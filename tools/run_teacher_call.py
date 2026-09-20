"""Execute one OpenAI-compatible teacher request in a killable process."""

from __future__ import annotations

import http.client
import json
import sys
import urllib.parse


def main() -> int:
    request = json.loads(sys.stdin.read())
    endpoint = str(request["endpoint"])
    parsed = urllib.parse.urlparse(endpoint)
    if parsed.scheme != "http" or not parsed.hostname:
        raise ValueError("teacher endpoint must be an HTTP URL")
    path = parsed.path or "/"
    if parsed.query:
        path += "?" + parsed.query
    body = json.dumps(
        {
            "model": request["model"],
            "messages": request["messages"],
            "temperature": 0,
            "max_tokens": int(request["max_tokens"]),
            "chat_template_kwargs": {"enable_thinking": False},
        },
        ensure_ascii=False,
    ).encode("utf-8")
    connection = http.client.HTTPConnection(parsed.hostname, parsed.port or 80, timeout=float(request["timeout"]))
    try:
        connection.request("POST", path, body=body, headers={"Content-Type": "application/json"})
        response = connection.getresponse()
        raw = response.read(512 * 1024 + 1)
        if len(raw) > 512 * 1024:
            raise ValueError("teacher response exceeds 512 KiB")
        if response.status >= 400:
            raise RuntimeError(f"teacher_http_{response.status}")
        payload = json.loads(raw.decode("utf-8"))
        sys.stdout.write(json.dumps({"ok": True, "payload": payload}, ensure_ascii=False))
    except BaseException as exc:
        sys.stdout.write(json.dumps({"ok": False, "error": type(exc).__name__}, ensure_ascii=False))
    finally:
        connection.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
