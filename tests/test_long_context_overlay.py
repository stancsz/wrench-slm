from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OVERLAY = ROOT / "runtime" / "freetoken_wrench_long_context" / "sitecustomize.py"


def test_overlay_is_valid_python_and_opt_in():
    source = OVERLAY.read_text(encoding="utf-8")
    ast.parse(source)
    assert 'WRENCH_LONG_CONTEXT_OVERLAY", "0"' in source
    assert "WRENCH_GLOBAL_FULL_LAYERS" in source
    assert "WRENCH_SWA_WINDOW" in source


def test_overlay_documents_native_input_boundary():
    readme = (OVERLAY.parent / "README.md").read_text(encoding="utf-8")
    assert "complete request payload" in readme
    assert "prompt_tokens" in readme
    assert "does not change the Safetensors weights" in readme

