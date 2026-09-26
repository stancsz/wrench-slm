"""Small bounded-log helper checks for the supervised local screen."""
from __future__ import annotations

import io
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import run_local_config_review_draft_screen_01_with_deadline as wrapper


class LocalConfigReviewDraftScreenWrapperTests(unittest.TestCase):
    def test_log_pump_caps_file_and_signals_overflow(self):
        with tempfile.TemporaryDirectory(
            prefix="bounded-screen-log-test-",
            dir=r"C:\wrench-slm-data\artifacts\wrench-local-acceptability",
        ) as directory:
            path = Path(directory) / "stdout.log"
            overflow = threading.Event()
            error = threading.Event()
            with patch.object(wrapper, "MAX_LOG_BYTES", 8):
                wrapper._pump_bounded(io.BytesIO(b"0123456789abcdef"), path, overflow, error)
            self.assertEqual(path.read_bytes(), b"01234567")
            self.assertTrue(overflow.is_set())
            self.assertFalse(error.is_set())


if __name__ == "__main__":
    unittest.main()
