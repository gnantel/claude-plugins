"""Fixtures for cleanup tests: a throwaway git repository and a fake pull request lookup."""

import subprocess
from pathlib import Path

import pytest

from git_repository import GitRepository
from pull_requests import PullRequest


def git(directory: Path, *arguments: str) -> str:
    identity = ["-c", "user.name=Test", "-c", "user.email=test@example.com"]
    completed = subprocess.run(["git", "-C", str(directory), *identity, *arguments],
                               capture_output=True, text=True, check=True)
    return completed.stdout.strip()


class FakePullRequests:
    def __init__(self) -> None:
        self.by_branch: dict[str, list[PullRequest]] = {}

    def default_branch(self) -> str:
        return "main"

    def for_branch(self, branch: str) -> list[PullRequest]:
        return self.by_branch.get(branch, [])

    def merge(self, branch: str, head: str) -> None:
        self.by_branch[branch] = [PullRequest(1, "MERGED", head, "2026-01-01T00:00:00Z")]

    def set_state(self, branch: str, state: str, head: str = "") -> None:
        self.by_branch[branch] = [PullRequest(2, state, head, None)]


@pytest.fixture
def main_checkout(tmp_path: Path) -> Path:
    checkout = tmp_path / "main-checkout"
    checkout.mkdir()
    git(checkout, "init", "-b", "main")
    git(checkout, "commit", "--allow-empty", "-m", "first")
    return checkout


@pytest.fixture
def repository(main_checkout: Path) -> GitRepository:
    return GitRepository(main_checkout)


@pytest.fixture
def pull_requests() -> FakePullRequests:
    return FakePullRequests()


def add_worktree(main_checkout: Path, branch: str) -> Path:
    worktree = main_checkout.parent / branch
    git(main_checkout, "worktree", "add", "-b", branch, str(worktree))
    return worktree
