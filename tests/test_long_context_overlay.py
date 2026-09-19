from pathlib import Path


def _load_overlay_source():
    source = Path("runtime/freetoken_wrench_long_context/sitecustomize.py").read_text(encoding="utf-8")
    namespace = {}
    exec(compile(source, "sitecustomize.py", "exec"), namespace)
    return namespace


def test_long_context_overlay_allows_zero_global_full_layers():
    namespace = _load_overlay_source()
    resolve = namespace["_resolve_global_ids"]
    assert resolve((3, 7, 11), "none") == ()
    assert resolve((3, 7, 11), "off") == ()
    assert resolve((3, 7, 11), "7,99") == (7,)
    assert resolve((3, 7, 11), "") == (11,)
