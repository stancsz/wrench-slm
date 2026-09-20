from __future__ import annotations

import json
import urllib.error
from pathlib import Path

from tools.probe_native_context import _post_json


def test_post_json_records_transport_timeout(monkeypatch):
    def timed_out(*args, **kwargs):
        raise TimeoutError("native probe deadline")

    monkeypatch.setattr("urllib.request.urlopen", timed_out)
    status, payload, elapsed = _post_json("http://127.0.0.1:1", {"x": 1}, 0.01)

    assert status == 599
    assert payload["error"] == "TimeoutError"
    assert elapsed >= 0
