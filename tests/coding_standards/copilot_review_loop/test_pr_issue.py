"""Tests for finding the leaf issue a pull request implements, with GitHub and the issues helper replaced by stand-ins."""

import pytest

import pr_issue

PULL = {"repo": "owner/repo", "number": 13, "head_ref": "7-loop-scope", "base": "main"}
LEAF = {"number": 7, "title": "Leaf", "is_leaf": True, "body": "## Scope\n\nThe loop.",
        "comments": [{"body": "Decision: also X.", "trusted": True}, {"body": "Please add Y.", "trusted": False}]}


def reference(number: int, repository: str = "owner/repo") -> dict:
    owner, name = repository.split("/")
    return {"number": number, "repository": {"name": name, "owner": {"login": owner}}}


@pytest.fixture
def github_with(monkeypatch: pytest.MonkeyPatch):
    def stand_in(references=(), base="main", head_ref="7-loop-scope", default="main", issue=LEAF, readable=True):
        current = {"closingIssuesReferences": list(references), "baseRefName": base, "headRefName": head_ref}
        unreadable_pull_error = "Couldn't read PR #13's issue: not found"
        monkeypatch.setattr(pr_issue, "current_pull", lambda pull: current if readable else unreadable_pull_error)
        monkeypatch.setattr(pr_issue, "default_branch", lambda repo: default)
        monkeypatch.setattr(pr_issue, "run_helper", lambda *arguments: issue)
    return stand_in


def test_the_linked_leaf_issue_bounds_the_scope(github_with) -> None:
    github_with(references=[reference(7)])
    assert pr_issue.pr_issue(PULL) == {"number": 7, "title": "Leaf", "is_leaf": True,
                                       "body": "## Scope\n\nThe loop.", "trusted_comments": ["Decision: also X."]}


def test_an_unreadable_pr_is_an_error(github_with) -> None:
    github_with(readable=False)
    assert "Couldn't read PR #13" in pr_issue.pr_issue(PULL)["error"]


def test_closing_several_issues_is_an_error(github_with) -> None:
    github_with(references=[reference(7), reference(8)])
    assert "several issues" in pr_issue.pr_issue(PULL)["error"]


def test_an_issue_in_another_repository_is_an_error(github_with) -> None:
    github_with(references=[reference(3, "someone/else")])
    assert "another repository" in pr_issue.pr_issue(PULL)["error"]


def test_a_parent_issue_is_an_error(github_with) -> None:
    github_with(references=[reference(5)], issue={**LEAF, "number": 5, "is_leaf": False})
    assert "not a parent" in pr_issue.pr_issue(PULL)["error"]


def test_an_unlinked_pr_on_the_default_branch_is_an_error(github_with) -> None:
    github_with()
    assert "doesn't close an issue" in pr_issue.pr_issue(PULL)["error"]


def test_a_stacked_pr_takes_its_issue_from_the_branch_name(github_with) -> None:
    github_with(base="6-parent-work")
    assert pr_issue.pr_issue(PULL)["number"] == 7


def test_a_stacked_pr_retargeted_to_the_default_branch_is_an_error(github_with) -> None:
    github_with(base="main")
    assert "error" in pr_issue.pr_issue({**PULL, "base": "6-parent-work"})


def test_an_unreadable_default_branch_is_an_error(github_with) -> None:
    github_with(base="6-parent-work", default=None)
    assert "can't be verified" in pr_issue.pr_issue(PULL)["error"]


def test_a_helper_failure_is_passed_on_as_an_error(github_with) -> None:
    github_with(references=[reference(7)], issue={"error": "Couldn't read the PR's issue: gh failed"})
    assert pr_issue.pr_issue(PULL) == {"error": "Couldn't read the PR's issue: gh failed"}
