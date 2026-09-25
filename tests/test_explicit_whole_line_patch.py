import difflib
import json

import pytest

from wrench_harness.worker import WrenchWorker


@pytest.mark.parametrize(
    ("source", "marker", "expected"),
    [
        (b"head=true\nold.mode=quiet\ntail=true\n", "old.mode=quiet", b"head=true\ntail=true\n"),
        (b"first=1\nlast=remove\n", "last=remove", b"first=1\n"),
        (b"only=entry\n", "only=entry", b""),
    ],
)
def test_explicit_whole_line_removal_proposes_exact_unapplied_patch(
    tmp_path, source, marker, expected
):
    relative = "settings/local.conf"
    target = tmp_path / relative
    target.parent.mkdir(parents=True)
    target.write_bytes(source)
    prompt = (
        f"Draft a review-only patch: remove the entire line containing `{marker}` "
        f"from {relative} and do not apply it."
    )

    result = WrenchWorker(tokenizer=None, model=None, allowed_root=tmp_path).propose(
        [{"role": "user", "content": prompt}]
    )

    proposal = json.loads(result["raw_model_output"])
    assert result["status"] == "accepted"
    assert result["action"] == "patch_draft"
    assert result["mechanical_fast_path"] is True
    assert proposal["files"] == [relative]
    assert proposal["review_only"] is True
    assert target.read_bytes() == source
    expected_diff = "".join(
        difflib.unified_diff(
            source.decode("utf-8").splitlines(keepends=True),
            expected.decode("utf-8").splitlines(keepends=True),
            fromfile=f"a/{relative}",
            tofile=f"b/{relative}",
            n=3,
        )
    )
    assert proposal["diff"] == expected_diff


@pytest.mark.parametrize(
    ("source", "marker"),
    [
        (b"mode=old\nmode=old\n", "mode=old"),
        (b"mode=current\n", "mode=absent"),
    ],
)
def test_explicit_whole_line_removal_abstains_when_target_line_is_not_unique(
    tmp_path, source, marker
):
    relative = "settings/local.conf"
    target = tmp_path / relative
    target.parent.mkdir(parents=True)
    target.write_bytes(source)
    prompt = (
        f"Draft a review-only patch: remove the entire line containing `{marker}` "
        f"from {relative} and do not apply it."
    )

    result = WrenchWorker(tokenizer=None, model=None, allowed_root=tmp_path).propose(
        [{"role": "user", "content": prompt}]
    )

    assert result["status"] == "abstain"
    assert result["action"] is None
    assert result["fallback_reason"] == "patch_target_not_unique"
    assert result["mechanical_fast_path"] is True
    assert target.read_bytes() == source
