"""Offline, fixture-only boundary for one prepared OpenCode request lease.

This module owns a loopback-only HTTP server for exercising immutable,
synthetic fixture response bytes. It has no HTTP client, upstream address, or
forwarding path. A lease stays owned until the bounded fixture stream and its
request writer stop and close.
"""

from __future__ import annotations

import json
import secrets
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from http.client import HTTPMessage
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable, Iterator
from urllib.parse import urlsplit


ROUTE = "/v1/chat/completions"
CORRELATION_HEADER = "x-wrench-request-nonce"
CONTENT_TYPE_HEADER = "content-type"
MAX_REQUEST_BYTES = 65_536
MAX_HEADER_BYTES = 8_192
MAX_HEADERS = 64
MAX_HTTP_LINE_BYTES = 4_096
MAX_MESSAGES = 64
MAX_MESSAGE_BYTES = 8_192
MAX_RESPONSE_CHUNK_BYTES = 16_384
MAX_RESPONSE_BYTES = 1_048_576
MAX_RESPONSE_CHUNKS = 128
MAX_IN_FLIGHT_LEASES = 128
MAX_REMEMBERED_NONCES = 4_096
DEFAULT_LEASE_TIMEOUT_SECONDS = 30.0
_BODY_KEYS = frozenset({"model", "messages", "stream", "max_tokens"})
_ROLES = frozenset({"system", "developer", "user", "assistant"})


class BoundaryError(ValueError):
    """Raised for invalid boundary configuration or stream use."""


class RejectReason(str, Enum):
    INVALID_REQUEST = "invalid_request"
    REQUEST_TOO_LARGE = "request_too_large"
    HEADERS_INVALID = "headers_invalid"
    CORRELATION_MISSING = "correlation_missing"
    CORRELATION_DUPLICATE = "correlation_duplicate"
    CORRELATION_UNKNOWN = "correlation_unknown"
    CORRELATION_STALE = "correlation_stale"
    LEASE_EXPIRED = "lease_expired"
    ROUTE_UNSUPPORTED = "route_unsupported"
    CONTENT_UNSUPPORTED = "content_unsupported"


@dataclass(frozen=True)
class LoweredRequest:
    """Only the bounded final request fields needed by this fixture gate."""

    method: str
    url: str
    headers: tuple[tuple[str, str], ...] = field(repr=False)
    body: bytes = field(repr=False)


@dataclass(frozen=True)
class RejectedRequest:
    reason: RejectReason


@dataclass(frozen=True)
class FixtureResponse:
    """Immutable, fully bounded fixture chunks; no responder code is invoked."""

    chunks: tuple[bytes, ...]

    def __post_init__(self) -> None:
        if type(self.chunks) is not tuple or len(self.chunks) > MAX_RESPONSE_CHUNKS:
            raise BoundaryError("fixture_chunks_invalid")
        total = 0
        for chunk in self.chunks:
            if type(chunk) is not bytes or len(chunk) > MAX_RESPONSE_CHUNK_BYTES:
                raise BoundaryError("fixture_chunk_invalid")
            total += len(chunk)
            if total > MAX_RESPONSE_BYTES:
                raise BoundaryError("fixture_response_too_large")


@dataclass(frozen=True)
class LeaseTicket:
    lease_id: str
    nonce: str = field(repr=False)


class StreamEnd(str, Enum):
    COMPLETE = "complete"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


def _valid_lease_id(value: object) -> bool:
    return (
        type(value) is str
        and 1 <= len(value) <= 128
        and all(ch.isalnum() or ch in "._:-" for ch in value)
    )


def _reject_duplicate_json_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate_json_key")
        result[key] = value
    return result


def _valid_chat_request(request: LoweredRequest) -> RejectReason | None:
    if type(request) is not LoweredRequest:
        return RejectReason.INVALID_REQUEST
    if type(request.method) is not str or request.method != "POST":
        return RejectReason.ROUTE_UNSUPPORTED
    if type(request.url) is not str or len(request.url.encode("utf-8", "ignore")) > 512:
        return RejectReason.ROUTE_UNSUPPORTED
    try:
        url = urlsplit(request.url)
        if (
            url.scheme != ""
            or url.netloc != ""
            or url.path != ROUTE
            or url.query
            or url.fragment
            or url.username is not None
            or url.password is not None
        ):
            return RejectReason.ROUTE_UNSUPPORTED
    except (TypeError, ValueError):
        return RejectReason.ROUTE_UNSUPPORTED
    if type(request.body) is not bytes:
        return RejectReason.INVALID_REQUEST
    if len(request.body) > MAX_REQUEST_BYTES:
        return RejectReason.REQUEST_TOO_LARGE
    if type(request.headers) is not tuple or len(request.headers) > MAX_HEADERS:
        return RejectReason.HEADERS_INVALID
    total_header_bytes = 0
    for pair in request.headers:
        if (
            type(pair) is not tuple or len(pair) != 2
            or type(pair[0]) is not str or type(pair[1]) is not str
        ):
            return RejectReason.HEADERS_INVALID
        try:
            total_header_bytes += len(pair[0].encode("ascii")) + len(pair[1].encode("ascii"))
        except UnicodeEncodeError:
            return RejectReason.HEADERS_INVALID
        if "\r" in pair[0] or "\n" in pair[0] or "\r" in pair[1] or "\n" in pair[1]:
            return RejectReason.HEADERS_INVALID
    if total_header_bytes > MAX_HEADER_BYTES:
        return RejectReason.HEADERS_INVALID
    content_types = [
        value for name, value in request.headers
        if name.lower() == CONTENT_TYPE_HEADER
    ]
    if len(content_types) != 1:
        return RejectReason.CONTENT_UNSUPPORTED
    media_type = content_types[0].split(";")
    if media_type[0].strip().lower() != "application/json" or len(media_type) > 2:
        return RejectReason.CONTENT_UNSUPPORTED
    if len(media_type) == 2:
        parameter = media_type[1].strip().split("=", 1)
        if (
            len(parameter) != 2
            or parameter[0].strip().lower() != "charset"
            or parameter[1].strip().lower() != "utf-8"
        ):
            return RejectReason.CONTENT_UNSUPPORTED
    if len(request.body) == 0:
        return RejectReason.CONTENT_UNSUPPORTED
    try:
        body = json.loads(
            request.body.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_json_keys,
            parse_constant=lambda _value: (_ for _ in ()).throw(ValueError("invalid_number")),
        )
    except (UnicodeDecodeError, TypeError, ValueError, RecursionError):
        return RejectReason.CONTENT_UNSUPPORTED
    if type(body) is not dict or set(body) - _BODY_KEYS:
        return RejectReason.CONTENT_UNSUPPORTED
    if (
        body.get("model") != "wrench-offline-fixture"
        or type(body.get("model")) is not str
        or body.get("stream") is not True
        or type(body.get("messages")) is not list
        or not 1 <= len(body["messages"]) <= MAX_MESSAGES
    ):
        return RejectReason.CONTENT_UNSUPPORTED
    if "max_tokens" in body and (
        type(body["max_tokens"]) is not int or not 1 <= body["max_tokens"] <= 8192
    ):
        return RejectReason.CONTENT_UNSUPPORTED
    for message in body["messages"]:
        if (
            type(message) is not dict
            or set(message) != {"role", "content"}
            or type(message.get("role")) is not str
            or message.get("role") not in _ROLES
            or type(message.get("content")) is not str
        ):
            return RejectReason.CONTENT_UNSUPPORTED
        try:
            if not message["content"] or len(message["content"].encode("utf-8")) > MAX_MESSAGE_BYTES:
                return RejectReason.CONTENT_UNSUPPORTED
        except UnicodeEncodeError:
            return RejectReason.CONTENT_UNSUPPORTED
    return None


class RequestLeaseBoundary:
    """One-shot nonce correlation and bounded local fixture stream ownership."""

    def __init__(
        self,
        *,
        clock: Callable[[], float] = time.monotonic,
        nonce_factory: Callable[[], str] = lambda: secrets.token_urlsafe(24),
        timeout_seconds: float = DEFAULT_LEASE_TIMEOUT_SECONDS,
    ) -> None:
        if type(timeout_seconds) not in (int, float) or timeout_seconds <= 0:
            raise BoundaryError("timeout_invalid")
        self._clock = clock
        self._nonce_factory = nonce_factory
        self._timeout = float(timeout_seconds)
        self._lock = threading.RLock()
        self._pending: dict[str, _Lease] = {}
        self._active: dict[str, _Lease] = {}
        self._used_nonces: set[str] = set()
        self._used_nonce_order: deque[str] = deque()

    def prepare(self, lease_id: str, release: Callable[[], object]) -> LeaseTicket:
        """Register one caller-owned prepared lease and return its one-use nonce."""
        if not _valid_lease_id(lease_id) or not callable(release):
            raise BoundaryError("lease_invalid")
        with self._lock:
            if any(lease.lease_id == lease_id for lease in (*self._pending.values(), *self._active.values())):
                raise BoundaryError("lease_id_in_use")
            if len(self._pending) + len(self._active) >= MAX_IN_FLIGHT_LEASES:
                raise BoundaryError("lease_capacity_reached")
            nonce = self._nonce_factory()
            if type(nonce) is not str or not nonce or len(nonce) > 128 or nonce in self._pending or nonce in self._used_nonces:
                raise BoundaryError("nonce_invalid_or_reused")
            lease = _Lease(lease_id=lease_id, nonce=nonce, release=release, deadline=self._clock() + self._timeout)
            self._pending[nonce] = lease
            lease.timer = threading.Timer(self._timeout, self._timeout_lease, args=(lease,))
            lease.timer.daemon = True
            lease.timer.start()
            return LeaseTicket(lease_id, nonce)

    def dispatch(
        self,
        request: LoweredRequest,
        fixture_response: FixtureResponse,
        *,
        defer_completion: bool = False,
    ) -> "FixtureResponseStream | RejectedRequest":
        """Validate a lowered request and connect it to immutable fixture bytes."""
        if type(fixture_response) is not FixtureResponse:
            return RejectedRequest(RejectReason.INVALID_REQUEST)
        reason, nonce_values = self._correlations(request)
        if reason is not None:
            self._expire_due()
            if reason is RejectReason.CORRELATION_DUPLICATE:
                self._consume_ambiguous(nonce_values)
            return RejectedRequest(reason)
        nonce = nonce_values[0]
        with self._lock:
            self._expire_due_locked()
            lease = self._pending.get(nonce)
            if lease is None:
                reason = RejectReason.CORRELATION_STALE if nonce in self._used_nonces else RejectReason.CORRELATION_UNKNOWN
                return RejectedRequest(reason)
            # Consume before inspecting content. An attempted correlation can never be replayed.
            del self._pending[nonce]
            self._remember_used_nonce(nonce)
            lease.consumed = True
            self._active[nonce] = lease
        invalid = _valid_chat_request(request)
        if invalid is not None:
            self._finish(lease, StreamEnd.FAILED)
            return RejectedRequest(invalid)
        return FixtureResponseStream(
            self,
            lease,
            iter(fixture_response.chunks),
            defer_completion=defer_completion,
        )

    def expire(self) -> int:
        """Release overdue pending leases and request cancellation for active ones."""
        with self._lock:
            return self._expire_due_locked()

    def _correlations(self, request: object) -> tuple[RejectReason | None, list[str]]:
        if (
            type(request) is not LoweredRequest
            or type(request.headers) is not tuple
            or len(request.headers) > MAX_HEADERS
        ):
            return RejectReason.INVALID_REQUEST, []
        values: list[str] = []
        for pair in request.headers:
            if type(pair) is tuple and len(pair) == 2 and type(pair[0]) is str and pair[0].lower() == CORRELATION_HEADER:
                if type(pair[1]) is not str:
                    return RejectReason.HEADERS_INVALID, values
                values.append(pair[1])
        if not values:
            return RejectReason.CORRELATION_MISSING, []
        if len(values) != 1:
            return RejectReason.CORRELATION_DUPLICATE, values
        if not values[0] or len(values[0]) > 128:
            return RejectReason.CORRELATION_UNKNOWN, values
        return None, values

    def _consume_ambiguous(self, values: list[str]) -> None:
        releases: list[_Lease] = []
        with self._lock:
            for nonce in set(values):
                lease = self._pending.pop(nonce, None)
                if lease is not None:
                    self._remember_used_nonce(nonce)
                    lease.consumed = True
                    releases.append(lease)
        for lease in releases:
            self._finish(lease, StreamEnd.FAILED)

    def _expire_due(self) -> int:
        with self._lock:
            return self._expire_due_locked()

    def _expire_due_locked(self) -> int:
        now = self._clock()
        expired_pending = [lease for lease in self._pending.values() if now >= lease.deadline]
        expired_active = [
            lease for lease in self._active.values()
            if now >= lease.deadline and not lease.timeout_requested
        ]
        for lease in expired_pending:
            self._pending.pop(lease.nonce, None)
            self._remember_used_nonce(lease.nonce)
            lease.ended = StreamEnd.TIMEOUT
        for lease in expired_active:
            # The worker owns the iterator and socket writer. Mark cancellation,
            # but leave the active lease pinned until that worker closes them.
            lease.timeout_requested = True
        for lease in expired_pending:
            lease.release_once()
        return len(expired_pending) + len(expired_active)

    def _timeout_lease(self, lease: "_Lease") -> None:
        with self._lock:
            if lease.ended is not None:
                return
            if self._pending.pop(lease.nonce, None) is not None:
                lease.ended = StreamEnd.TIMEOUT
                self._remember_used_nonce(lease.nonce)
                lease.release_once()
            elif self._active.get(lease.nonce) is lease:
                lease.timeout_requested = True

    def _finish(self, lease: "_Lease", end: StreamEnd) -> None:
        with self._lock:
            if lease.ended is not None:
                return
            if lease.timeout_requested or self._clock() >= lease.deadline:
                end = StreamEnd.TIMEOUT
            lease.ended = end
            self._pending.pop(lease.nonce, None)
            self._active.pop(lease.nonce, None)
            lease.release_once()

    def _remember_used_nonce(self, nonce: str) -> None:
        if nonce in self._used_nonces:
            return
        self._used_nonces.add(nonce)
        self._used_nonce_order.append(nonce)
        if len(self._used_nonce_order) > MAX_REMEMBERED_NONCES:
            self._used_nonces.discard(self._used_nonce_order.popleft())


class LoopbackFixtureServer:
    """Short-lived 127.0.0.1 HTTP server for exercising the offline boundary.

    It binds an OS-assigned ephemeral port. Requests terminate in the immutable
    fixture response; this server has no upstream address or forwarding code.
    """

    def __init__(
        self,
        boundary: RequestLeaseBoundary,
        fixture_response: FixtureResponse,
    ) -> None:
        if type(boundary) is not RequestLeaseBoundary or type(fixture_response) is not FixtureResponse:
            raise BoundaryError("loopback_server_configuration_invalid")
        owner = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def setup(self) -> None:
                # Apply read and write timeouts before BaseHTTPRequestHandler
                # begins parsing the request line or headers.
                self.request.settimeout(5.0)
                super().setup()

            def handle_one_request(self) -> None:
                try:
                    self.raw_requestline = self.rfile.readline(MAX_HTTP_LINE_BYTES + 1)
                    if len(self.raw_requestline) > MAX_HTTP_LINE_BYTES:
                        self.send_error(414)
                        self.close_connection = True
                        return
                    if not self.raw_requestline:
                        self.close_connection = True
                        return
                    if not self.parse_request():
                        return
                    method_name = "do_" + self.command
                    if not hasattr(self, method_name):
                        self.send_error(501)
                        return
                    getattr(self, method_name)()
                    self.wfile.flush()
                except (TimeoutError, OSError):
                    # No request body or lease exists until parsing completes.
                    self.close_connection = True

            def parse_request(self) -> bool:
                """Parse only bounded raw lines before constructing HTTPMessage."""
                self.requestline = self.raw_requestline.decode("iso-8859-1").rstrip("\r\n")
                fields = self.requestline.split(" ")
                if (
                    len(fields) != 3
                    or not fields[0]
                    or not fields[1]
                    or fields[2] not in {"HTTP/1.0", "HTTP/1.1"}
                ):
                    self.close_connection = True
                    self._send_rejection(400, RejectReason.INVALID_REQUEST.value)
                    return False
                self.command, self.path, self.request_version = fields
                self.close_connection = self.request_version != "HTTP/1.1"
                partial_headers: list[tuple[str, str]] = []
                raw_total = 0
                while True:
                    try:
                        line = self.rfile.readline(MAX_HTTP_LINE_BYTES + 1)
                    except (TimeoutError, OSError):
                        self._consume_raw_headers(self.path, partial_headers)
                        self.close_connection = True
                        return False
                    if not line:
                        self._consume_raw_headers(self.path, partial_headers)
                        self.close_connection = True
                        self._send_rejection(400, RejectReason.INVALID_REQUEST.value)
                        return False
                    if len(line) > MAX_HTTP_LINE_BYTES:
                        self._consume_raw_headers(self.path, partial_headers)
                        self.close_connection = True
                        self._send_rejection(431, RejectReason.HEADERS_INVALID.value)
                        return False
                    raw_total += len(line)
                    if raw_total > MAX_HEADER_BYTES:
                        self._consume_raw_headers(self.path, partial_headers)
                        self.close_connection = True
                        self._send_rejection(431, RejectReason.HEADERS_INVALID.value)
                        return False
                    if line == b"\r\n":
                        break
                    if not line.endswith(b"\r\n") or len(partial_headers) >= MAX_HEADERS:
                        self._consume_raw_headers(self.path, partial_headers)
                        self.close_connection = True
                        self._send_rejection(431, RejectReason.HEADERS_INVALID.value)
                        return False
                    try:
                        text = line[:-2].decode("iso-8859-1")
                    except UnicodeDecodeError:
                        self._consume_raw_headers(self.path, partial_headers)
                        self.close_connection = True
                        self._send_rejection(400, RejectReason.HEADERS_INVALID.value)
                        return False
                    if not text or text[0] in " \t" or ":" not in text:
                        self._consume_raw_headers(self.path, partial_headers)
                        self.close_connection = True
                        self._send_rejection(400, RejectReason.HEADERS_INVALID.value)
                        return False
                    name, value = text.split(":", 1)
                    if (
                        not name.isascii()
                        or not name
                        or any(not (char.isalnum() or char in "!#$%&'*+-.^_`|~") for char in name)
                        or any((ord(char) < 32 and char != "\t") or ord(char) == 127 for char in value)
                    ):
                        self._consume_raw_headers(self.path, partial_headers)
                        self.close_connection = True
                        self._send_rejection(400, RejectReason.HEADERS_INVALID.value)
                        return False
                    partial_headers.append((name, value.strip(" \t")))
                self.headers = HTTPMessage()
                for name, value in partial_headers:
                    self.headers.add_header(name, value)
                if self.headers.get("Connection", "").lower() == "close":
                    self.close_connection = True
                return True

            def log_message(self, _format: str, *args: object) -> None:
                # BaseHTTPRequestHandler logs request metadata to stderr.
                return

            def send_error(self, code: int, message: str | None = None, explain: str | None = None) -> None:
                try:
                    self._consume_rejected_attempt()
                except Exception:
                    pass
                status = 405 if code == 501 else 400
                reason = (
                    RejectReason.ROUTE_UNSUPPORTED.value
                    if status == 405
                    else RejectReason.INVALID_REQUEST.value
                )
                if code == 414:
                    status = 414
                elif code == 431:
                    status = 431
                self._send_rejection(status, reason)

            def _send_rejection(self, status: int, reason: str) -> None:
                payload = json.dumps({"error": reason}, separators=(",", ":")).encode("ascii")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.send_header("Connection", "close")
                self.end_headers()
                self.wfile.write(payload)
                self.close_connection = True

            def _consume_rejected_attempt(self) -> None:
                # Consume and release any uniquely identified lease even when
                # HTTP framing fails before its body can be safely read.
                try:
                    self._consume_raw_headers(
                        self.path[:512],
                        tuple((name, value) for name, value in self.headers.raw_items()),
                    )
                except Exception:
                    return

            def _consume_raw_headers(self, path: str, headers: object) -> None:
                if type(headers) is not tuple and type(headers) is not list:
                    return
                lowered = LoweredRequest("POST", path[:512], tuple(headers), b"")
                owner._boundary.dispatch(lowered, owner._fixture_response)

            def do_POST(self) -> None:
                if self.path != ROUTE:
                    self._consume_rejected_attempt()
                    self._send_rejection(404, RejectReason.ROUTE_UNSUPPORTED.value)
                    return
                if self.headers.get_all("Transfer-Encoding"):
                    self._consume_rejected_attempt()
                    self._send_rejection(400, RejectReason.HEADERS_INVALID.value)
                    return
                length_values = self.headers.get_all("Content-Length") or []
                if len(length_values) != 1:
                    self._consume_rejected_attempt()
                    self._send_rejection(400, RejectReason.HEADERS_INVALID.value)
                    return
                try:
                    length = int(length_values[0], 10)
                except (TypeError, ValueError):
                    self._consume_rejected_attempt()
                    self._send_rejection(400, RejectReason.HEADERS_INVALID.value)
                    return
                if length < 0:
                    self._consume_rejected_attempt()
                    self._send_rejection(400, RejectReason.HEADERS_INVALID.value)
                    return
                if length > MAX_REQUEST_BYTES:
                    self._consume_rejected_attempt()
                    self._send_rejection(413, RejectReason.REQUEST_TOO_LARGE.value)
                    return
                if len(self.headers) > MAX_HEADERS:
                    self._consume_rejected_attempt()
                    self._send_rejection(400, RejectReason.HEADERS_INVALID.value)
                    return
                header_bytes = 0
                try:
                    for name, value in self.headers.raw_items():
                        header_bytes += len(name.encode("latin-1")) + len(value.encode("latin-1"))
                except (UnicodeEncodeError, AttributeError):
                    header_bytes = MAX_HEADER_BYTES + 1
                if header_bytes > MAX_HEADER_BYTES:
                    self._consume_rejected_attempt()
                    self._send_rejection(431, RejectReason.HEADERS_INVALID.value)
                    return
                try:
                    body = self.rfile.read(length)
                except (OSError, TimeoutError):
                    self._consume_rejected_attempt()
                    self._send_rejection(400, RejectReason.INVALID_REQUEST.value)
                    return
                if len(body) != length:
                    self._consume_rejected_attempt()
                    self._send_rejection(400, RejectReason.INVALID_REQUEST.value)
                    return
                lowered = LoweredRequest(
                    "POST",
                    self.path,
                    tuple((name, value) for name, value in self.headers.raw_items()),
                    body,
                )
                try:
                    outcome = owner._boundary.dispatch(
                        lowered, owner._fixture_response, defer_completion=True
                    )
                except Exception:
                    self._send_rejection(502, "fixture_failed")
                    return
                if isinstance(outcome, RejectedRequest):
                    status = 413 if outcome.reason is RejectReason.REQUEST_TOO_LARGE else 400
                    self._send_rejection(status, outcome.reason.value)
                    return
                try:
                    self.send_response(200)
                    self.send_header("Content-Type", "text/event-stream")
                    self.send_header("Cache-Control", "no-cache")
                    self.send_header("Transfer-Encoding", "chunked")
                    self.send_header("Connection", "close")
                    self.end_headers()
                    for chunk in outcome:
                        self.wfile.write(f"{len(chunk):X}\r\n".encode("ascii"))
                        self.wfile.write(chunk)
                        self.wfile.write(b"\r\n")
                        self.wfile.flush()
                    self.wfile.write(b"0\r\n\r\n")
                    outcome.close(StreamEnd.COMPLETE)
                except (BrokenPipeError, ConnectionResetError, OSError):
                    outcome.close(StreamEnd.CANCELLED)
                except (BoundaryError, TimeoutError):
                    outcome.close(StreamEnd.FAILED)
                finally:
                    outcome.close(StreamEnd.CANCELLED)
                    self.close_connection = True

            def do_GET(self) -> None:
                self._consume_rejected_attempt()
                self._send_rejection(405, RejectReason.ROUTE_UNSUPPORTED.value)

        class Server(ThreadingHTTPServer):
            daemon_threads = True
            allow_reuse_address = False

            def __init__(self, server_address: tuple[str, int], handler_class: type[BaseHTTPRequestHandler]) -> None:
                self._request_slots = threading.BoundedSemaphore(MAX_IN_FLIGHT_LEASES)
                super().__init__(server_address, handler_class)

            def process_request(self, request: object, client_address: object) -> None:
                if not self._request_slots.acquire(blocking=False):
                    self.shutdown_request(request)
                    return
                try:
                    super().process_request(request, client_address)
                except BaseException:
                    self._request_slots.release()
                    raise

            def process_request_thread(self, request: object, client_address: object) -> None:
                try:
                    super().process_request_thread(request, client_address)
                finally:
                    self._request_slots.release()

            def handle_error(self, request: object, client_address: object) -> None:
                # Do not emit request-associated data to process logs.
                return

        self._boundary = boundary
        self._fixture_response = fixture_response
        self._server = Server(("127.0.0.1", 0), Handler)
        self._thread: threading.Thread | None = None
        self._closed = False

    @property
    def address(self) -> tuple[str, int]:
        host, port = self._server.server_address[:2]
        return str(host), int(port)

    def __enter__(self) -> "LoopbackFixtureServer":
        if self._closed or self._thread is not None:
            raise BoundaryError("loopback_server_already_started")
        self._thread = threading.Thread(
            target=lambda: self._server.serve_forever(poll_interval=0.05),
            name="wrench-offline-fixture",
            daemon=True,
        )
        self._thread.start()
        return self

    def close(self) -> None:
        if self._closed:
            return
        if self._thread is None:
            self._server.server_close()
            self._closed = True
            return
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=2.0)
        if self._thread.is_alive():
            raise BoundaryError("loopback_server_shutdown_timeout")
        self._thread = None
        self._closed = True

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.close()


@dataclass
class _Lease:
    lease_id: str
    nonce: str = field(repr=False)
    release: Callable[[], object] = field(repr=False)
    deadline: float
    consumed: bool = False
    ended: StreamEnd | None = None
    timeout_requested: bool = False
    _released: bool = False
    timer: threading.Timer | None = field(default=None, repr=False)

    def release_once(self) -> None:
        if not self._released:
            self._released = True
            if self.timer is not None:
                self.timer.cancel()
            self.release()


class FixtureResponseStream(Iterator[bytes]):
    """Bounded fixture chunks that release the associated lease on every end."""

    def __init__(
        self,
        boundary: RequestLeaseBoundary,
        lease: _Lease,
        chunks: Iterator[bytes],
        *,
        defer_completion: bool = False,
    ) -> None:
        self._boundary = boundary
        self._lease = lease
        self._chunks = chunks
        self._total = 0
        self.end: StreamEnd | None = None
        self._finished = False
        self._defer_completion = defer_completion

    def __iter__(self) -> "FixtureResponseStream":
        return self

    def __next__(self) -> bytes:
        if self.end is not None:
            raise StopIteration
        if self._lease.timeout_requested or self._boundary._clock() >= self._lease.deadline:
            self.close(StreamEnd.TIMEOUT)
            raise TimeoutError("fixture_stream_timeout")
        try:
            chunk = next(self._chunks)
        except StopIteration:
            self._close_iterator()
            self.end = StreamEnd.COMPLETE
            if not self._defer_completion:
                self._finished = True
                self._boundary._finish(self._lease, StreamEnd.COMPLETE)
            raise
        except BaseException:
            self.close(StreamEnd.FAILED)
            raise
        if self._lease.timeout_requested or self._boundary._clock() >= self._lease.deadline:
            self.close(StreamEnd.TIMEOUT)
            raise TimeoutError("fixture_stream_timeout")
        if type(chunk) is not bytes or len(chunk) > MAX_RESPONSE_CHUNK_BYTES:
            self.close(StreamEnd.FAILED)
            raise BoundaryError("fixture_chunk_invalid")
        self._total += len(chunk)
        if self._total > MAX_RESPONSE_BYTES:
            self.close(StreamEnd.FAILED)
            raise BoundaryError("fixture_response_too_large")
        return chunk

    def close(self, end: StreamEnd = StreamEnd.CANCELLED) -> None:
        if self._finished:
            return
        if self._lease.timeout_requested or self._boundary._clock() >= self._lease.deadline:
            end = StreamEnd.TIMEOUT
        self._close_iterator()
        self.end = end
        self._finished = True
        self._boundary._finish(self._lease, end)

    def _close_iterator(self) -> None:
        close = getattr(self._chunks, "close", None)
        if callable(close):
            close()

    def __enter__(self) -> "FixtureResponseStream":
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.close(StreamEnd.FAILED if exc_type else StreamEnd.CANCELLED)


__all__ = [
    "CORRELATION_HEADER",
    "CONTENT_TYPE_HEADER",
    "DEFAULT_LEASE_TIMEOUT_SECONDS",
    "FixtureResponseStream",
    "FixtureResponse",
    "MAX_HTTP_LINE_BYTES",
    "LoweredRequest",
    "MAX_REQUEST_BYTES",
    "MAX_RESPONSE_BYTES",
    "MAX_IN_FLIGHT_LEASES",
    "RejectReason",
    "RejectedRequest",
    "RequestLeaseBoundary",
    "ROUTE",
    "StreamEnd",
    "LeaseTicket",
    "LoopbackFixtureServer",
]
