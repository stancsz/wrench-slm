import importlib.util
import sys
import types
from pathlib import Path


def _load_probe_module():
    path = Path("tools/probe_native_context.py")
    spec = importlib.util.spec_from_file_location("wrench_probe_native_context", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_probe_uses_unit_token_estimate_for_large_payload(monkeypatch, tmp_path):
    module = _load_probe_module()
    calls = []

    class FakeTokenizer:
        def __call__(self, text, *, add_special_tokens):
            calls.append(len(text))
            return types.SimpleNamespace(input_ids=[0] * 8)

    class FakeAutoTokenizer:
        @classmethod
        def from_pretrained(cls, path, *, local_files_only):
            return FakeTokenizer()

    monkeypatch.setitem(
        sys.modules,
        "transformers",
        types.SimpleNamespace(AutoTokenizer=FakeAutoTokenizer),
    )

    prompt, method, estimated = module._build_prompt(
        None,
        10000,
        tmp_path,
    )

    assert method == "local_tokenizer_unit_estimate"
    assert estimated == 8 * ((10000 - 128 + 7) // 8)
    assert len(prompt) > len(module.PROMPT_UNIT)
    assert calls == [len(module.PROMPT_UNIT)]
