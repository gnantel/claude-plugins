"""Runs the git commands that branch and worktree cleanup needs against one repository."""

import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from cli_tools import git as git_cli


BRANCH_PREFIX = "refs/heads/"


@dataclass(frozen=True)
class Worktree:
    path: Path
    branch: str | None
    locked: bool = False


class GitRepository:
    def __init__(self, directory: Path) -> None:
        self.directory = directory

    def fetch_prune(self) -> None:
        self.git("fetch", "--prune", "origin")

    def local_branches(self) -> list[str]:
        references = self.git("for-each-ref", "--format=%(refname)", "refs/heads/")
        return [reference.removeprefix(BRANCH_PREFIX) for reference in references.splitlines()]

    def branch_head(self, branch: str) -> str:
        return self.git("rev-parse", f"{BRANCH_PREFIX}{branch}")

    def current_worktree(self) -> Path:
        return Path(self.git("rev-parse", "--show-toplevel")).resolve()

    def worktrees(self) -> list[Worktree]:
        listing = self.git("worktree", "list", "--porcelain", "-z")
        return [parse_worktree(block) for block in listing.split("\0\0") if block.strip("\0")]

    def main_worktree(self) -> Path:
        return self.worktrees()[0].path

    def is_clean(self, worktree: Path) -> bool:
        return not self.git("-C", str(worktree), "status", "--porcelain", "--untracked-files=all")

    def remove_worktree(self, worktree: Path) -> None:
        self.git("worktree", "remove", str(worktree))

    def delete_branch_at(self, branch: str, head: str) -> None:
        self.git("update-ref", "-d", f"{BRANCH_PREFIX}{branch}", head)

    def git(self, *arguments: str) -> str:
        return git_cli.run(*arguments, cwd=self.directory).removesuffix("\n")


def parse_worktree(block: str) -> Worktree:
    fields = block.strip("\0").split("\0")
    values = dict(field.split(" ", 1) for field in fields if " " in field)
    branch = values.get("branch")
    return Worktree(Path(values["worktree"]).resolve(),
                    branch.removeprefix(BRANCH_PREFIX) if branch else None,
                    locked=any(field == "locked" or field.startswith("locked ") for field in fields))
