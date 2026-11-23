"""Local git operations for the Copilot review loop: the current head, working tree state, the branch's own commits, and changed paths."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from cli_tools import git as git_cli


def head() -> str:
    return git("rev-parse", "HEAD")


def is_dirty() -> bool:
    return bool(git("status", "--porcelain"))


def branch_base(base_branch: str) -> str:
    return git("merge-base", "HEAD", f"origin/{base_branch}")


def has_merge_commits(base: str) -> bool:
    return bool(git("rev-list", "--merges", f"{base}..HEAD"))


def sole_branch_commit(base: str) -> str:
    commits = git("rev-list", f"{base}..HEAD").split()
    return commits[0] if len(commits) == 1 else ""


def last_branch_commit_touching(base: str, path: str) -> str:
    return git("log", "--format=%H", "-1", f"{base}..HEAD", "--", path)


def is_inside_worktree(path: Path) -> bool:
    return Path(git("rev-parse", "--show-toplevel")) in path.resolve().parents


def is_rebasing() -> bool:
    return any(Path(git("rev-parse", "--git-path", name)).exists() for name in ("rebase-merge", "rebase-apply"))


def stopped_on_emptied_commit() -> bool:
    index_tree = git("write-tree", allow_failure=True)
    return is_rebasing() and bool(index_tree) and index_tree == git("rev-parse", "HEAD~1^{tree}", allow_failure=True)


def changed_paths() -> list[str]:
    modified = raw_git("diff", "-z", "--no-renames", "--name-only", "HEAD")
    untracked = raw_git("ls-files", "-z", "--others", "--exclude-standard")
    return [path for path in (modified + untracked).split("\0") if path]


def message_of(commit: str) -> str:
    return raw_git("log", "-1", "--format=%B", commit).rstrip("\n")


def subject_of(commit: str) -> str:
    return git("log", "-1", "--format=%s", commit)


def with_default_co_authors(message: str, co_authors: list[str]) -> str:
    if co_author_trailers(message):
        return message
    return with_trailers(message, co_authors)


def co_author_trailers(message: str) -> list[str]:
    parsed = git_cli.run("interpret-trailers", "--only-trailers", "--parse", stdin=message + "\n")
    return [line for line in parsed.splitlines() if line.lower().startswith("co-authored-by:")]


def with_trailers(message: str, trailers: list[str]) -> str:
    arguments = [argument for trailer in trailers for argument in ("--trailer", trailer)]
    return git_cli.run("interpret-trailers", "--if-exists", "addIfDifferent", *arguments,
                       stdin=message + "\n").rstrip("\n")


def git(*arguments: str, allow_failure: bool = False) -> str:
    return git_cli.read(*arguments, allow_failure=allow_failure)


def raw_git(*arguments: str, allow_failure: bool = False, environment: dict | None = None) -> str:
    return git_cli.run(*arguments, env=environment, allow_failure=allow_failure)


def succeeds(*arguments: str, environment: dict | None = None) -> bool:
    return git_cli.succeeds(*arguments, env=environment)
