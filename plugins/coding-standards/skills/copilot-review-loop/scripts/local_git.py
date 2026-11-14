"""Local git operations for the Copilot review loop: the current head, working tree state, the branch's own commits, and changed paths."""

import subprocess
import sys


def head() -> str:
    return git("rev-parse", "HEAD")


def is_dirty() -> bool:
    return bool(git("status", "--porcelain"))


def branch_base(base_branch: str) -> str:
    return git("merge-base", "HEAD", f"origin/{base_branch}")


def has_merge_commits(base: str) -> bool:
    return bool(git("rev-list", "--merges", f"{base}..HEAD"))


def last_branch_commit_touching(base: str, path: str) -> str:
    return git("log", "--format=%H", "-1", f"{base}..HEAD", "--", path)


def changed_paths() -> list[str]:
    modified = raw_git("diff", "-z", "--no-renames", "--name-only", "HEAD")
    untracked = raw_git("ls-files", "-z", "--others", "--exclude-standard")
    return [path for path in (modified + untracked).split("\0") if path]


def message_of(commit: str) -> str:
    return raw_git("log", "-1", "--format=%B", commit).rstrip("\n")


def subject_of(commit: str) -> str:
    return git("log", "-1", "--format=%s", commit)


def with_trailer(message: str, trailer: str) -> str:
    result = subprocess.run(["git", "interpret-trailers", "--if-exists", "addIfDifferent", "--trailer", trailer],
                            input=message + "\n", capture_output=True, text=True, check=True)
    return result.stdout.rstrip("\n")


def git(*arguments: str, allow_failure: bool = False) -> str:
    return raw_git(*arguments, allow_failure=allow_failure).strip()


def raw_git(*arguments: str, allow_failure: bool = False, environment: dict | None = None) -> str:
    result = subprocess.run(["git", *arguments], capture_output=True, text=True, env=environment)
    if result.returncode != 0 and not allow_failure:
        sys.exit(f"git {arguments[0]} failed: {result.stderr.strip()}")
    return result.stdout if result.returncode == 0 else ""


def succeeds(*arguments: str, environment: dict | None = None) -> bool:
    return subprocess.run(["git", *arguments], capture_output=True, text=True, env=environment).returncode == 0
