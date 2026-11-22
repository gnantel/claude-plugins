"""Shared fixtures for the Copilot review loop tests: a scratch git repository with a bare remote, and a stand-in for the pull request GitHub would return."""

import subprocess
from pathlib import Path

import pytest

import github
import local_git


class ScratchRepository:
    def __init__(self, root: Path) -> None:
        self.remote = root / "remote.git"
        self.path = root / "work"

    def git(self, *arguments: str, cwd: Path | None = None) -> str:
        return subprocess.run(["git", "-C", str(cwd or self.path), *arguments],
                              capture_output=True, text=True, check=True).stdout.strip()

    def write(self, path: str, content: str) -> None:
        (self.path / path).write_text(content)

    def commit(self, message: str, **files: str) -> str:
        for path, content in files.items():
            self.write(path, content)
        self.git("add", "-A")
        self.git("commit", "-q", "-m", message)
        return self.git("rev-parse", "HEAD")

    def push(self, branch: str = "feature") -> None:
        self.git("push", "-q", "-u", "origin", branch)

    def remote_subjects(self, branch: str = "feature", base: str = "origin/main") -> list[str]:
        self.git("fetch", "-q")
        return self.git("log", "--format=%s", f"{base}..origin/{branch}").splitlines()

    def remote_file(self, path: str, branch: str = "feature") -> str:
        return self.git("show", f"origin/{branch}:{path}")

    def remote_message(self, subject: str, branch: str = "feature") -> str:
        commit = self.git("log", "--format=%H", f"--grep=^{subject}$", f"origin/{branch}")
        return self.git("log", "-1", "--format=%B", commit)


@pytest.fixture
def repository(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> ScratchRepository:
    scratch = ScratchRepository(tmp_path)
    subprocess.run(["git", "init", "-q", "--bare", str(scratch.remote)], check=True)
    subprocess.run(["git", "clone", "-q", str(scratch.remote), str(scratch.path)], check=True, capture_output=True)
    scratch.git("config", "user.name", "Author")
    scratch.git("config", "user.email", "author@example.com")
    scratch.commit("Base", **{"base.txt": "base"})
    scratch.git("push", "-q", "origin", "HEAD:main")
    scratch.git("remote", "set-head", "origin", "main")
    scratch.git("checkout", "-q", "-b", "feature")
    monkeypatch.chdir(scratch.path)
    return scratch


@pytest.fixture
def pull_request(monkeypatch: pytest.MonkeyPatch):
    def stand_in(**overrides) -> dict:
        pull = {"repo": "owner/repo", "number": 1, "head": local_git.head(), "head_ref": "feature",
                "base": "main", "from_fork": False, "rebase_merge_allowed": True, **overrides}
        monkeypatch.setattr(github, "pull_request", lambda number: pull)
        return pull
    return stand_in
