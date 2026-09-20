from tools.probe_explicit_patch_route import _cases
from tools.probe_explicit_patch_route import run


def test_explicit_patch_probe_covers_each_bounded_operation():
    cases = _cases()
    assert len(cases) == 20
    assert {case["operation"] for case in cases} == {
        "replace",
        "append",
        "prepend",
        "insert",
        "remove",
    }


def test_explicit_patch_probe_accepts_without_mutation(tmp_path):
    receipt = run(tmp_path / "receipt.json")
    assert receipt["status"] == "PASS_EXPLICIT_PATCH_MECHANICAL_ROUTE"
    assert receipt["accepted_count"] == 20
    assert receipt["workspace_unchanged_count"] == 20
