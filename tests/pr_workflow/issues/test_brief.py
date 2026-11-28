"""Tests for the child-session brief: every fixed part is present and the parts the planning session fills in are marked."""

import pytest

import issues
from cli_tools import gh

FIXED_PARTS = [
    "gh issue view 19 --comments",
    "git fetch origin",
    "latest `origin/<default>`",
    "`coding-standards` skill",
    "One PR, closing #19 only",
    "becomes a new issue",
    "no changelog wording",
    "no counts of growing lists",
    "git commit --amend",
    "Verify Done when for real",
    "pr-workflow:submit-pr",
    "`Closes #19`",
    "whether Copilot reviewed the final head",
    "Record the review only with `review-branch` step 7",
    "on its own, before the command that creates the PR",
    "Never write the marker any other way. Never merge.",
    "Ask the user only when a decision is genuinely theirs",
]


@pytest.fixture
def brief() -> str:
    template = issues.BRIEF_TEMPLATE.read_text()
    return issues.render_brief(template, 19, "Delegation brief", "owner/repo")


@pytest.mark.parametrize("fixed_part", FIXED_PARTS)
def test_the_brief_contains_every_fixed_part(brief: str, fixed_part: str) -> None:
    assert fixed_part in brief


def test_the_brief_names_the_issue_and_repository(brief: str) -> None:
    assert "Implement GitHub issue #19 in `owner/repo`: Delegation brief." in brief


@pytest.mark.parametrize("varying_part", ["Area", "Verify Done when by", "Sibling sessions", "Version bumps", "Extra context"])
def test_each_varying_part_is_marked_for_the_planning_session(brief: str, varying_part: str) -> None:
    line = next(line for line in brief.splitlines() if line.startswith(f"- {varying_part}:"))
    assert "<<FILL:" in line


def test_a_title_with_braces_is_kept_as_written() -> None:
    rendered = issues.render_brief("{title}", 1, "Support {braces}", "owner/repo")
    assert rendered == "Support {braces}"


def test_the_brief_command_prints_the_rendered_brief_as_plain_text(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    requests = []

    def fake_gh_json(*arguments: str):
        requests.append(arguments)
        return {"number": 19, "title": "Delegation brief"}

    monkeypatch.setattr(gh, "read_json", fake_gh_json)
    monkeypatch.setattr(issues, "repository", lambda: "owner/repo")
    monkeypatch.setattr("sys.argv", ["issues.py", "brief", "19"])

    issues.main()

    assert requests == [("issue", "view", "19", "--json", "number,title")]
    assert capsys.readouterr().out.startswith("Implement GitHub issue #19 in `owner/repo`: Delegation brief.\n")
