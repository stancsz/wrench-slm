#!/usr/bin/env python3
"""Reject every request sent through the package's external proxy guard.

The portable Claude Code launcher points HTTP proxy variables at this local
listener while bypassing the Wrench loopback endpoint. This makes an isolated
smoke run fail closed instead of silently reaching a first-party provider.
"""

from __future__ import annotations

import argparse
import socketserver


class _RejectHandler(socketserver.BaseRequestHandler):
    def handle(self) -> None:
        try:
            self.request.recv(4096)
            body = b"Wrench portable package blocks external traffic.\n"
            response = (
                b"HTTP/1.1 403 Forbidden\r\n"
                b"Content-Type: text/plain; charset=utf-8\r\n"
                + f"Content-Length: {len(body)}\r\n".encode("ascii")
                + b"Connection: close\r\n\r\n"
                + body
            )
            self.request.sendall(response)
        except OSError:
            pass


class _ThreadingRejectServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def main() -> int:
    parser = argparse.ArgumentParser(description="Reject non-loopback proxy traffic")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, required=True)
    args = parser.parse_args()
    with _ThreadingRejectServer((args.host, args.port), _RejectHandler) as server:
        server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
