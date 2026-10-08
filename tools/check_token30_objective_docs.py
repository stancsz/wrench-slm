"""Check that public documentation reflects the active token30 objective."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from tools import check_token30_objective as objective_guard


PUBLIC_OBJECTIVE_PAGES = (
    "site/pages/index.html",
    "site/pages/experiment-v2.html",
    "site/pages/evidence.html",
    "site/pages/roadmap.html",
    "site/pages/model-story.html",
    "site/pages/zh/index.html",
    "site/pages/zh/experiment-v2.html",
    "site/pages/zh/evidence.html",
    "site/pages/zh/roadmap.html",
    "site/pages/zh/model-story.html",
)

OBSOLETE_OBJECTIVE_COPY = (
    "there is no fixed local/frontier percentage",
    "不设固定的本地/强模型调用比例",
    "next milestone: less than 2 gb",
    "下一站：不到 2 gb",
    "start with qwen3.6",
    "从现成的 qwen3.6 出发",
    "the useful score is the total cost",
    "最后要算的是同一件事成功做完的总账",
)

SUPPORTING_GOAL_MARKERS = (
    "Supporting record only.",
    "active goal",
    "no authority",
    "checkpoint",
    "dependency",
)

STALE_CHECKPOINT_DIRECTIVES = (
    "the repository agent freezes a new paired comparison contract",
)


def check_goal_authority(repo: Path) -> None:
    """Keep stale component-goal next steps from becoming an implicit queue."""
    index = (repo / "docs/goal/README.md").read_text(encoding="utf-8")
    objective_guard.require(
        "navigation index, not an execution queue" in index,
        "goal index must stay navigation-only",
    )
    objective_guard.require(
        "only current work queue" in index,
        "active checkpoint must be the only current work queue",
    )
    objective_guard.require(
        "explicitly names it as an evidenced dependency" in index,
        "restarting a supporting goal needs an explicit active-checkpoint dependency",
    )

    active = (repo / "docs/goal/wrench-token30/GOAL.md").resolve()
    for path in sorted((repo / "docs/goal").glob("*/GOAL.md")):
        if path.resolve() == active:
            continue
        text = path.read_text(encoding="utf-8")
        for marker in SUPPORTING_GOAL_MARKERS:
            objective_guard.require(
                marker in text,
                f"non-active goal lacks supporting-only authority notice: {path.relative_to(repo)}",
            )


def check_current_checkpoint(repo: Path) -> None:
    """Require one live unmet criterion and reject the completed preparation step."""
    text = (repo / "docs/goal/wrench-token30/GOAL.md").read_text(encoding="utf-8")
    marker = "## Current checkpoint"
    objective_guard.require(text.count(marker) == 1,
                            "active goal must have exactly one current checkpoint")
    checkpoint = text.split(marker, 1)[1]
    unmet = "**Unmet criterion:**"
    next_action = "**Next action / owner / check:**"
    objective_guard.require(checkpoint.count(unmet) == 1,
                            "active checkpoint must state one unmet criterion")
    objective_guard.require(checkpoint.count(next_action) == 1,
                            "active checkpoint must have exactly one next action")
    lowered = checkpoint.lower()
    objective_guard.require(
        not any(directive in lowered for directive in STALE_CHECKPOINT_DIRECTIVES),
        "active checkpoint repeats a completed preparation directive",
    )
    objective_guard.require("at least 30% reduction" in lowered,
                            "active checkpoint must preserve the 30% success check")


def check_public_objective_copy(repo, objective: dict) -> None:
    """Keep the public summary aligned with the metric and local model."""
    target = f"{objective['target_reduction']:.0%}"
    for name in PUBLIC_OBJECTIVE_PAGES:
        text = (repo / name).read_text(encoding="utf-8")
        objective_guard.require(
            target in text and "Qwen" in text,
            f"public objective copy missing {target} target or Qwen: {name}",
        )
        lowered = text.lower()
        objective_guard.require(
            not any(phrase in lowered for phrase in OBSOLETE_OBJECTIVE_COPY),
            f"public copy revives an obsolete target: {name}",
        )


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=str(REPO), help="repository root (defaults to this checkout)")
    args = parser.parse_args(argv)
    try:
        objective, _ = objective_guard.load_object(
            objective_guard.REPO / objective_guard.OBJECTIVE_PATH
        )
        objective_guard.validate_objective(objective)
        objective_guard.check_documentation(Path(args.repo), objective)
        check_goal_authority(Path(args.repo))
        check_current_checkpoint(Path(args.repo))
        check_public_objective_copy(Path(args.repo), objective)
        print(json.dumps({
            "status": "PUBLIC_OBJECTIVE_COPY_ALIGNED",
            "objective_id": objective_guard.OBJECTIVE_ID,
            "pages_checked": len(PUBLIC_OBJECTIVE_PAGES),
        }))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "OBJECTIVE_COPY_DRIFT", "reason": str(exc)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
