"""Tests for the PreToolUse hook that blocks pull request creation until the current commit has passed the branch review."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

HOOK = Path(__file__).parents[3] / "plugins" / "pr-workflow" / "hooks" / "require_branch_review.py"
BLOCKED = 2
ALLOWED = 0


@pytest.fixture
def repository(tmp_path: Path) -> Path:
    git(tmp_path, "init", "-q", "-b", "main")
    git(tmp_path, "commit", "-q", "--allow-empty", "-m", "Initial commit")
    return tmp_path


def git(directory: Path, *arguments: str) -> str:
    identity = ["-c", "user.name=Test", "-c", "user.email=test@example.com"]
    return subprocess.run(["git", "-C", str(directory), *identity, *arguments],
                          capture_output=True, text=True, check=True).stdout.strip()


def run_hook(tool_name: str, tool_input: dict, cwd: Path) -> int:
    event = json.dumps({"tool_name": tool_name, "tool_input": tool_input, "cwd": str(cwd)})
    return subprocess.run([sys.executable, "-B", str(HOOK)], input=event,
                          capture_output=True, text=True).returncode


def create_pr(cwd: Path) -> int:
    return run_hook("Bash", {"command": "gh pr create --title 'T' --body-file /tmp/body.md"}, cwd)


def record_review(directory: Path) -> None:
    marker = git(directory, "rev-parse", "--path-format=absolute", "--git-path", "pr-workflow-reviewed")
    Path(marker).write_text(git(directory, "rev-parse", "HEAD") + "\n")


def test_unrelated_commands_are_allowed(repository: Path) -> None:
    assert run_hook("Bash", {"command": "git status"}, repository) == ALLOWED


def test_pr_creation_is_blocked_without_a_review(repository: Path) -> None:
    assert create_pr(repository) == BLOCKED


def test_pr_creation_is_allowed_once_the_head_is_reviewed(repository: Path) -> None:
    record_review(repository)
    assert create_pr(repository) == ALLOWED


def test_a_new_commit_needs_a_new_review(repository: Path) -> None:
    record_review(repository)
    git(repository, "commit", "-q", "--allow-empty", "-m", "Another change")
    assert create_pr(repository) == BLOCKED


@pytest.mark.parametrize("command", [
    "gh \\\npr create --title T",
    "gh pr \\\ncreate --title T",
    "g\\\nh pr create --title T",
    "gh pr cre\\\nate --title T",
])
def test_pr_creation_split_by_line_continuations_is_blocked(repository: Path, command: str) -> None:
    assert run_hook("Bash", {"command": command}, repository) == BLOCKED


def test_mcp_pr_creation_is_blocked_without_a_review(repository: Path) -> None:
    assert run_hook("mcp__github__create_pull_request", {"title": "T"}, repository) == BLOCKED


def test_directories_outside_git_are_left_alone(tmp_path: Path) -> None:
    assert create_pr(tmp_path) == ALLOWED


def test_each_worktree_needs_its_own_review(repository: Path, tmp_path_factory: pytest.TempPathFactory) -> None:
    other_worktree = tmp_path_factory.mktemp("worktrees") / "other"
    git(repository, "worktree", "add", "-q", "-b", "other", str(other_worktree))
    record_review(repository)
    assert create_pr(other_worktree) == BLOCKED
