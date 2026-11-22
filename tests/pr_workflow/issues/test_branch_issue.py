"""Tests for finding an issue from a branch name: an optional path prefix, then the issue number at the start of the last segment."""

import pytest

import issues


def found_issue_number(monkeypatch: pytest.MonkeyPatch, branch: str) -> int | None:
    monkeypatch.setattr(issues, "git", lambda *arguments: branch)
    monkeypatch.setattr(issues, "issue", lambda number: {"number": number})
    return issues.issue_from_branch_name(stacked=False).get("number")


@pytest.mark.parametrize("branch", ["22-review-branch-submit-pr", "claude/22-review-branch-submit-pr-247cb5", "feature/22-x"])
def test_the_issue_number_starts_the_last_segment(monkeypatch: pytest.MonkeyPatch, branch: str) -> None:
    assert found_issue_number(monkeypatch, branch) == 22


@pytest.mark.parametrize("branch", ["main", "claude/fix-the-thing", "22/fix", "feature/22-x/other", "fix-22-thing"])
def test_a_last_segment_without_a_leading_issue_number_has_no_issue(monkeypatch: pytest.MonkeyPatch, branch: str) -> None:
    assert found_issue_number(monkeypatch, branch) is None
