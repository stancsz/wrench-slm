"""Regression checks for stale public summaries of the active objective."""
import pytest

from tools import check_token30_objective as objective_guard
from tools import check_token30_objective_docs as docs_guard


@pytest.fixture
def objective():
    return objective_guard.load_object(
        objective_guard.REPO / objective_guard.OBJECTIVE_PATH
    )[0]


def test_supporting_goal_cannot_create_its_own_work_queue(tmp_path):
    goal_root = tmp_path / "docs" / "goal"
    active = goal_root / "wrench-token30" / "GOAL.md"
    supporting = goal_root / "old-component" / "GOAL.md"
    active.parent.mkdir(parents=True)
    supporting.parent.mkdir(parents=True)
    active.write_text("# Active\n", encoding="utf-8")
    index = goal_root / "README.md"
    index.write_text(
        "This is a navigation index, not an execution queue. The active "
        "checkpoint is the only current work queue. Resume a goal only when "
        "the active checkpoint explicitly names it as an evidenced dependency.\n",
        encoding="utf-8",
    )
    supporting.write_text("# Old component\n\nNext action: do more work.\n", encoding="utf-8")
    with pytest.raises(ValueError, match="supporting-only authority notice"):
        docs_guard.check_goal_authority(tmp_path)

    supporting.write_text(
        "# Old component\n\n> Supporting record only. Follow the active goal. "
        "This next-step text has no authority unless the active checkpoint "
        "names it as a dependency.\n",
        encoding="utf-8",
    )
    docs_guard.check_goal_authority(tmp_path)


def test_active_checkpoint_rejects_completed_preparation_directive(tmp_path):
    goal = tmp_path / "docs/goal/wrench-token30/GOAL.md"
    goal.parent.mkdir(parents=True)
    prefix = (
        "## Current checkpoint\n\n"
        "**Unmet criterion:** reach the target.\n\n"
        "**Next action / owner / check:** complete the next check with at least "
        "30% reduction.\n"
    )
    goal.write_text(prefix, encoding="utf-8")
    docs_guard.check_current_checkpoint(tmp_path)

    goal.write_text(
        prefix + "The repository agent freezes a new paired comparison contract.\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="completed preparation directive"):
        docs_guard.check_current_checkpoint(tmp_path)


def test_active_checkpoint_allows_only_one_next_action(tmp_path):
    goal = tmp_path / "docs/goal/wrench-token30/GOAL.md"
    goal.parent.mkdir(parents=True)
    goal.write_text(
        "## Current checkpoint\n\n"
        "**Unmet criterion:** reach the target.\n\n"
        "**Next action / owner / check:** complete the next check with at least "
        "30% reduction.\n\n"
        "**Next action / owner / check:** another task.\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="exactly one next action"):
        docs_guard.check_current_checkpoint(tmp_path)


@pytest.mark.parametrize("obsolete", docs_guard.OBSOLETE_OBJECTIVE_COPY)
def test_public_copy_rejects_parked_or_superseded_objective_language(
    tmp_path, objective, obsolete
):
    for name in docs_guard.PUBLIC_OBJECTIVE_PAGES:
        page = tmp_path / name
        page.parent.mkdir(parents=True, exist_ok=True)
        page.write_text("30% Qwen objective is unachieved.", encoding="utf-8")
    story = tmp_path / "site/pages/model-story.html"
    story.write_text(
        f"30% Qwen objective is unachieved. {obsolete}", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="obsolete target"):
        docs_guard.check_public_objective_copy(tmp_path, objective)


def test_public_copy_rejects_a_parked_model_as_the_current_starting_point(
    tmp_path, objective
):
    for name in docs_guard.PUBLIC_OBJECTIVE_PAGES:
        page = tmp_path / name
        page.parent.mkdir(parents=True, exist_ok=True)
        page.write_text("30% Qwen objective is unachieved.", encoding="utf-8")
    story = tmp_path / "site/pages/model-story.html"
    story.write_text(
        "30% Qwen objective is unachieved. Start with Qwen3.6.",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="obsolete target"):
        docs_guard.check_public_objective_copy(tmp_path, objective)
