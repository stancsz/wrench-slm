import http.client
import json
import socket
import threading
import time
import unittest

from wrench_harness.opencode_request_boundary import (
    BoundaryError,
    CORRELATION_HEADER,
    CONTENT_TYPE_HEADER,
    FixtureResponse,
    MAX_RESPONSE_BYTES,
    LoweredRequest,
    LoopbackFixtureServer,
    RejectReason,
    RejectedRequest,
    RequestLeaseBoundary,
    ROUTE,
    StreamEnd,
)


class Clock:
    def __init__(self):
        self.now = 10.0

    def __call__(self):
        return self.now


def _request(nonce, *, route=ROUTE, headers=None, body=None):
    return LoweredRequest(
        "POST",
        route,
        tuple(
            headers
            if headers is not None
            else ((CORRELATION_HEADER, nonce), (CONTENT_TYPE_HEADER, "application/json"))
        ),
        body if body is not None else json.dumps(
            {
                "model": "wrench-offline-fixture",
                "messages": [{"role": "user", "content": "synthetic fixture request"}],
                "stream": True,
                "max_tokens": 4,
            },
            separators=(",", ":"),
        ).encode("utf-8"),
    )


def _boundary(clock=None, *, nonce="nonce-1", timeout=5):
    calls = []
    boundary = RequestLeaseBoundary(
        clock=clock or Clock(), nonce_factory=lambda: nonce, timeout_seconds=timeout
    )
    ticket = boundary.prepare("lease-1", lambda: calls.append("released"))
    return boundary, ticket, calls


def _recv_headers(sock):
    received = bytearray()
    while b"\r\n\r\n" not in received:
        byte = sock.recv(1)
        if not byte:
            break
        received.extend(byte)
        if len(received) > 16_384:
            raise AssertionError("bounded_response_headers_exceeded")
    return bytes(received)


class RequestBoundaryTests(unittest.TestCase):
    def test_loopback_server_uses_ephemeral_loopback_and_fixture_only(self):
        released = []
        boundary = RequestLeaseBoundary(nonce_factory=lambda: "loopback-nonce")
        ticket = boundary.prepare("loopback-lease", lambda: released.append(True))
        fixture = FixtureResponse((b"data: synthetic-one\n\n", b"data: synthetic-two\n\n"))

        with LoopbackFixtureServer(boundary, fixture) as server:
            host, port = server.address
            self.assertEqual(host, "127.0.0.1")
            self.assertNotEqual(port, 4000)
            connection = http.client.HTTPConnection(host, port, timeout=3)
            body = json.dumps({
                "model": "wrench-offline-fixture",
                "messages": [{"role": "user", "content": "synthetic local fixture"}],
                "stream": True,
                "max_tokens": 2,
            }).encode()
            connection.request(
                "POST",
                ROUTE,
                body=body,
                headers={CORRELATION_HEADER: ticket.nonce, "Content-Type": "application/json"},
            )
            response = connection.getresponse()
            self.assertEqual(response.status, 200)
            self.assertEqual(response.getheader("Content-Type"), "text/event-stream")
            self.assertEqual(response.read(), b"data: synthetic-one\n\ndata: synthetic-two\n\n")
            connection.close()
        self.assertEqual(released, [True])

    def test_loopback_oversized_body_releases_correlated_lease_without_reading_it(self):
        released = []
        boundary = RequestLeaseBoundary(nonce_factory=lambda: "oversized-loopback-nonce")
        ticket = boundary.prepare("oversized-loopback-lease", lambda: released.append(True))
        with LoopbackFixtureServer(boundary, FixtureResponse(())) as server:
            host, port = server.address
            connection = http.client.HTTPConnection(host, port, timeout=3)
            body = b"x" * 65_537
            connection.request(
                "POST", ROUTE, body=body, headers={CORRELATION_HEADER: ticket.nonce}
            )
            response = connection.getresponse()
            self.assertEqual(response.status, 413)
            self.assertIn(b"request_too_large", response.read())
            connection.close()
        self.assertEqual(released, [True])

    def test_raw_aggregate_header_cap_rejects_and_releases_known_lease(self):
        released = []
        boundary = RequestLeaseBoundary(nonce_factory=lambda: "aggregate-header-nonce")
        ticket = boundary.prepare("aggregate-header-lease", lambda: released.append(True))
        with LoopbackFixtureServer(boundary, FixtureResponse(())) as server:
            sock = socket.create_connection(server.address, timeout=3)
            sock.sendall(
                (
                    f"POST {ROUTE} HTTP/1.1\r\n"
                    f"Host: 127.0.0.1:{server.address[1]}\r\n"
                    f"{CORRELATION_HEADER}: {ticket.nonce}\r\n"
                    "Content-Length: 0\r\n"
                    f"X-One: {'a' * 3000}\r\n"
                    f"X-Two: {'b' * 3000}\r\n"
                    f"X-Three: {'c' * 3000}\r\n"
                    "Connection: close\r\n\r\n"
                ).encode("ascii")
            )
            response = _recv_headers(sock)
            sock.close()
            self.assertIn(b"431", response.split(b"\r\n", 1)[0])
        self.assertEqual(released, [True])

    def test_transfer_encoding_and_duplicate_lengths_are_rejected(self):
        scenarios = (
            ("transfer", "Transfer-Encoding: chunked\r\nContent-Length: 0\r\n"),
            ("duplicate-length", "Content-Length: 0\r\nContent-Length: 0\r\n"),
        )
        for name, framing in scenarios:
            with self.subTest(name=name):
                released = []
                boundary = RequestLeaseBoundary(nonce_factory=lambda: f"framing-{name}")
                ticket = boundary.prepare(f"framing-{name}-lease", lambda: released.append(True))
                with LoopbackFixtureServer(boundary, FixtureResponse(())) as server:
                    sock = socket.create_connection(server.address, timeout=3)
                    wire = (
                        f"POST {ROUTE} HTTP/1.1\r\n"
                        f"Host: 127.0.0.1:{server.address[1]}\r\n"
                        f"{CORRELATION_HEADER}: {ticket.nonce}\r\n"
                        + framing
                        + "Connection: close\r\n\r\n"
                    )
                    sock.sendall(wire.encode("ascii"))
                    response = _recv_headers(sock)
                    sock.close()
                    self.assertIn(b"400", response.split(b"\r\n", 1)[0])
                self.assertEqual(released, [True])

    def test_raw_overlong_header_and_excess_count_are_capped_before_body_read(self):
        scenarios = (
            ("overlong", lambda nonce, port: f"{CORRELATION_HEADER}: {nonce}\r\nX-Long: {'z' * 5000}\r\n"),
            ("count", lambda nonce, port: f"{CORRELATION_HEADER}: {nonce}\r\n" + "".join(f"X-{index}: v\r\n" for index in range(64))),
        )
        for name, headers in scenarios:
            with self.subTest(name=name):
                released = []
                boundary = RequestLeaseBoundary(
                    nonce_factory=lambda: f"parser-{name}-nonce", timeout_seconds=0.05
                )
                ticket = boundary.prepare(f"parser-{name}-lease", lambda: released.append(True))
                with LoopbackFixtureServer(boundary, FixtureResponse(())) as server:
                    sock = socket.create_connection(server.address, timeout=3)
                    wire = (
                        f"POST {ROUTE} HTTP/1.1\r\n"
                        f"Host: 127.0.0.1:{server.address[1]}\r\n"
                        + headers(ticket.nonce, server.address[1])
                        + "Content-Length: 0\r\n\r\n"
                    )
                    sock.sendall(wire.encode("ascii"))
                    response = _recv_headers(sock)
                    sock.close()
                    self.assertIn(b"431", response.split(b"\r\n", 1)[0])
                    self.assertTrue(_wait_until_released(released, timeout=1.0))
                self.assertEqual(released, [True])

    def test_real_loopback_disconnect_releases_after_request_writer_stops(self):
        released = []
        release_event = threading.Event()

        def release():
            released.append(True)
            release_event.set()

        boundary = RequestLeaseBoundary(nonce_factory=lambda: "disconnect-nonce")
        ticket = boundary.prepare("disconnect-lease", release)
        fixture = FixtureResponse((b"x" * 16_384,) * 64)
        with LoopbackFixtureServer(boundary, fixture) as server:
            sock = socket.create_connection(server.address, timeout=3)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024)
            body = json.dumps({
                "model": "wrench-offline-fixture",
                "messages": [{"role": "user", "content": "disconnect fixture"}],
                "stream": True,
            }).encode()
            sock.sendall(
                (
                    f"POST {ROUTE} HTTP/1.1\r\n"
                    f"Host: 127.0.0.1:{server.address[1]}\r\n"
                    f"{CORRELATION_HEADER}: {ticket.nonce}\r\n"
                    "Content-Type: application/json\r\n"
                    f"Content-Length: {len(body)}\r\n"
                    "Connection: close\r\n\r\n"
                ).encode("ascii") + body
            )
            response_headers = _recv_headers(sock)
            self.assertIn(b"200", response_headers.split(b"\r\n", 1)[0])
            self.assertEqual(released, [])
            self.assertIn(ticket.nonce, boundary._active)
            sock.shutdown(socket.SHUT_RDWR)
            sock.close()
            self.assertTrue(release_event.wait(3.0))
            self.assertNotIn(ticket.nonce, boundary._active)
        self.assertEqual(released, [True])

    def test_loopback_active_timeout_marks_cancel_without_early_release(self):
        released = []
        release_event = threading.Event()

        def release():
            released.append(True)
            release_event.set()

        boundary = RequestLeaseBoundary(
            nonce_factory=lambda: "loopback-timeout-nonce", timeout_seconds=0.5
        )
        ticket = boundary.prepare("loopback-timeout-lease", release)
        fixture = FixtureResponse((b"y" * 16_384,) * 64)
        with LoopbackFixtureServer(boundary, fixture) as server:
            sock = socket.create_connection(server.address, timeout=3)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024)
            body = json.dumps({
                "model": "wrench-offline-fixture",
                "messages": [{"role": "user", "content": "timeout fixture"}],
                "stream": True,
            }).encode()
            sock.sendall(
                (
                    f"POST {ROUTE} HTTP/1.1\r\n"
                    f"Host: 127.0.0.1:{server.address[1]}\r\n"
                    f"{CORRELATION_HEADER}: {ticket.nonce}\r\n"
                    "Content-Type: application/json\r\n"
                    f"Content-Length: {len(body)}\r\n"
                    "Connection: close\r\n\r\n"
                ).encode("ascii") + body
            )
            response_headers = _recv_headers(sock)
            self.assertIn(b"200", response_headers.split(b"\r\n", 1)[0])

            deadline = time.monotonic() + 3.0
            timed_out_while_active = False
            while time.monotonic() < deadline:
                with boundary._lock:
                    active_lease = boundary._active.get(ticket.nonce)
                    timed_out_while_active = bool(
                        active_lease is not None and active_lease.timeout_requested
                    )
                if timed_out_while_active:
                    break
                time.sleep(0.01)
            self.assertTrue(timed_out_while_active)
            self.assertEqual(released, [])
            self.assertIn(ticket.nonce, boundary._active)

            # The tiny receive window keeps the 1 MiB writer in flight until
            # disconnect. Its timeout flag alone must not release the lease.
            sock.shutdown(socket.SHUT_RDWR)
            sock.close()
            self.assertTrue(release_event.wait(3.0))
            self.assertNotIn(ticket.nonce, boundary._active)
        self.assertEqual(released, [True])

    def test_one_nonce_binds_one_immutable_bounded_stream_and_releases_at_eof(self):
        boundary, ticket, released = _boundary()
        fixture = FixtureResponse((b"data: one\n\n", b"data: two\n\n"))
        stream = boundary.dispatch(_request(ticket.nonce), fixture)
        self.assertNotIsInstance(stream, RejectedRequest)
        self.assertEqual(list(stream), [b"data: one\n\n", b"data: two\n\n"])
        self.assertEqual(stream.end, StreamEnd.COMPLETE)
        self.assertEqual(released, ["released"])
        self.assertEqual(
            boundary.dispatch(_request(ticket.nonce), fixture),
            RejectedRequest(RejectReason.CORRELATION_STALE),
        )

    def test_direct_api_requires_exactly_one_supported_json_media_type(self):
        cases = (
            (((CORRELATION_HEADER, "nonce-1"),), RejectReason.CONTENT_UNSUPPORTED),
            (
                ((CORRELATION_HEADER, "nonce-1"), (CONTENT_TYPE_HEADER, "application/json"), (CONTENT_TYPE_HEADER, "application/json")),
                RejectReason.CONTENT_UNSUPPORTED,
            ),
            (
                ((CORRELATION_HEADER, "nonce-1"), (CONTENT_TYPE_HEADER, "text/plain")),
                RejectReason.CONTENT_UNSUPPORTED,
            ),
            (
                ((CORRELATION_HEADER, "nonce-1"), (CONTENT_TYPE_HEADER, "application/json; charset=latin-1")),
                RejectReason.CONTENT_UNSUPPORTED,
            ),
            (
                ((CORRELATION_HEADER, "nonce-1"), (CONTENT_TYPE_HEADER, "application/json; boundary=x")),
                RejectReason.CONTENT_UNSUPPORTED,
            ),
        )
        for headers, expected in cases:
            with self.subTest(headers=headers):
                boundary, ticket, released = _boundary()
                request = _request(ticket.nonce, headers=headers)
                self.assertEqual(boundary.dispatch(request, FixtureResponse(())), RejectedRequest(expected))
                self.assertEqual(released, ["released"])

        for content_type in ("Application/Json", "application/json; charset=UTF-8"):
            with self.subTest(content_type=content_type):
                boundary, ticket, released = _boundary()
                request = _request(
                    ticket.nonce,
                    headers=((CORRELATION_HEADER, ticket.nonce), (CONTENT_TYPE_HEADER, content_type)),
                )
                stream = boundary.dispatch(request, FixtureResponse(()))
                self.assertNotIsInstance(stream, RejectedRequest)
                self.assertEqual(list(stream), [])
                self.assertEqual(released, ["released"])

    def test_loopback_requires_json_media_type_and_releases_correlated_lease(self):
        scenarios = (
            ("missing", ()),
            ("duplicate", ("Content-Type: application/json\r\n", "Content-Type: application/json\r\n")),
            ("plain", ("Content-Type: text/plain\r\n",)),
            ("parameter", ("Content-Type: application/json; boundary=x\r\n",)),
        )
        body = json.dumps({
            "model": "wrench-offline-fixture",
            "messages": [{"role": "user", "content": "synthetic media-type case"}],
            "stream": True,
        }).encode()
        for name, media_headers in scenarios:
            with self.subTest(name=name):
                released = []
                boundary = RequestLeaseBoundary(nonce_factory=lambda: f"media-{name}-nonce")
                ticket = boundary.prepare(f"media-{name}-lease", lambda: released.append(True))
                with LoopbackFixtureServer(boundary, FixtureResponse(())) as server:
                    sock = socket.create_connection(server.address, timeout=3)
                    media = "".join(media_headers)
                    sock.sendall(
                        (
                            f"POST {ROUTE} HTTP/1.1\r\n"
                            f"Host: 127.0.0.1:{server.address[1]}\r\n"
                            f"{CORRELATION_HEADER}: {ticket.nonce}\r\n"
                            + media
                            + f"Content-Length: {len(body)}\r\nConnection: close\r\n\r\n"
                        ).encode("ascii") + body
                    )
                    response = _recv_headers(sock)
                    sock.close()
                    self.assertIn(b"400", response.split(b"\r\n", 1)[0])
                self.assertEqual(released, [True])

    def test_missing_unknown_and_duplicate_correlation_fail_closed(self):
        cases = (
            ((), RejectReason.CORRELATION_MISSING),
            (((CORRELATION_HEADER, "unknown"),), RejectReason.CORRELATION_UNKNOWN),
            (
                ((CORRELATION_HEADER, "nonce-1"), (CORRELATION_HEADER, "nonce-1")),
                RejectReason.CORRELATION_DUPLICATE,
            ),
        )
        for headers, expected in cases:
            with self.subTest(expected=expected):
                boundary, ticket, released = _boundary()
                result = boundary.dispatch(
                    _request(ticket.nonce, headers=headers), FixtureResponse(())
                )
                self.assertEqual(result, RejectedRequest(expected))
                if expected is RejectReason.CORRELATION_DUPLICATE:
                    self.assertEqual(released, ["released"])
                else:
                    self.assertEqual(released, [])

    def test_unsupported_route_and_content_consume_and_release(self):
        cases = (
            (_request("nonce-1", route="/v1/other"), RejectReason.ROUTE_UNSUPPORTED),
            (
                _request("nonce-1", body=b'{"model":"elsewhere","messages":[],"stream":true}'),
                RejectReason.CONTENT_UNSUPPORTED,
            ),
        )
        for request, expected in cases:
            with self.subTest(expected=expected):
                boundary, _, released = _boundary()
                self.assertEqual(
                    boundary.dispatch(request, FixtureResponse(())),
                    RejectedRequest(expected),
                )
                self.assertEqual(released, ["released"])

    def test_duplicate_json_keys_and_non_text_messages_are_rejected(self):
        boundary, ticket, released = _boundary()
        body = b'{"model":"wrench-offline-fixture","model":"wrench-offline-fixture","messages":[],"stream":true}'
        result = boundary.dispatch(
            _request(ticket.nonce, body=body), FixtureResponse(())
        )
        self.assertEqual(result, RejectedRequest(RejectReason.CONTENT_UNSUPPORTED))
        self.assertEqual(released, ["released"])

        boundary, ticket, released = _boundary()
        body = json.dumps({
            "model": "wrench-offline-fixture",
            "messages": [{"role": [], "content": "fixture"}],
            "stream": True,
        }).encode()
        self.assertEqual(
            boundary.dispatch(_request(ticket.nonce, body=body), FixtureResponse(())),
            RejectedRequest(RejectReason.CONTENT_UNSUPPORTED),
        )
        self.assertEqual(released, ["released"])

    def test_fixture_response_is_immutable_and_prevalidated(self):
        with self.assertRaisesRegex(BoundaryError, "fixture_chunk_invalid"):
            FixtureResponse((b"valid", object()))
        with self.assertRaisesRegex(BoundaryError, "fixture_chunks_invalid"):
            FixtureResponse((b"x",) * 129)
        with self.assertRaisesRegex(BoundaryError, "fixture_response_too_large"):
            FixtureResponse((b"x" * 16_384,) * 65)

    def test_active_timeout_marks_cancellation_but_releases_only_after_stream_close(self):
        clock = Clock()
        boundary, ticket, released = _boundary(clock, timeout=0.05)
        stream = boundary.dispatch(_request(ticket.nonce), FixtureResponse((b"pending",)))
        time.sleep(0.1)
        self.assertEqual(released, [])
        self.assertIsNone(stream.end)
        self.assertIn(ticket.nonce, boundary._active)
        self.assertEqual(boundary.expire(), 0)
        stream.close()
        self.assertEqual(stream.end, StreamEnd.TIMEOUT)
        self.assertNotIn(ticket.nonce, boundary._active)
        self.assertEqual(released, ["released"])
        boundary.expire()
        self.assertEqual(released, ["released"])

    def test_pending_timeout_releases_without_request(self):
        clock = Clock()
        boundary, ticket, released = _boundary(clock)
        clock.now += 5
        self.assertEqual(boundary.expire(), 1)
        self.assertEqual(released, ["released"])
        self.assertEqual(
            boundary.dispatch(_request(ticket.nonce), FixtureResponse(())),
            RejectedRequest(RejectReason.CORRELATION_STALE),
        )

    def test_headers_and_body_are_byte_bounded(self):
        boundary, ticket, released = _boundary()
        headers = ((CORRELATION_HEADER, ticket.nonce), ("x-extra", "x" * 9000))
        self.assertEqual(
            boundary.dispatch(_request(ticket.nonce, headers=headers), FixtureResponse(())),
            RejectedRequest(RejectReason.HEADERS_INVALID),
        )
        self.assertEqual(released, ["released"])

        boundary, ticket, released = _boundary()
        self.assertEqual(
            boundary.dispatch(_request(ticket.nonce, body=b" " * 65_537), FixtureResponse(())),
            RejectedRequest(RejectReason.REQUEST_TOO_LARGE),
        )
        self.assertEqual(released, ["released"])


def _wait_until_released(released, timeout):
    deadline = time.monotonic() + timeout
    while not released and time.monotonic() < deadline:
        time.sleep(0.01)
    return bool(released)


if __name__ == "__main__":
    unittest.main()
