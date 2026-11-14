"""Commits and pushes one round of Copilot review fixes: folds them into the commits they fix while only bots have reviewed, and adds a new commit once a person has reviewed."""

import os
import subprocess
import sys

import github
import review_state


def push_round(number: int | None, round_number: int) -> dict:
    pull = github.pull_request(number)
    changed_files = changed_paths()
    if not changed_files:
        sys.exit("No changes to push: fix the threads first, or end the loop if every comment was declined.")
    mode = review_state.commit_mode(pull)
    if mode == "rewrite":
        mode = push_rewritten(changed_files, round_number)
    else:
        commit_new_round(changed_files, round_number)
        git("push", "--quiet")
    return {"mode": mode, "head": git("rev-parse", "HEAD"), "short": git("rev-parse", "--short", "HEAD")}


def changed_paths() -> list[str]:
    modified = git("diff", "--name-only", "HEAD").splitlines()
    untracked = git("ls-files", "--others", "--exclude-standard").splitlines()
    return [path for path in modified + untracked if path]


def push_rewritten(changed_files: list[str], round_number: int) -> str:
    base = git("merge-base", "HEAD", default_branch())
    unmatched = commit_fixups(changed_files, base)
    if unmatched:
        commit_new_round(unmatched, round_number)
    if autosquash(base):
        git("push", "--quiet", "--force-with-lease")
        return "rewrite"
    git("push", "--quiet")
    return "rewrite-failed-pushed-fixups"


def commit_fixups(changed_files: list[str], base: str) -> list[str]:
    unmatched = []
    for path in changed_files:
        target = git("log", "--format=%H", "-1", f"{base}..HEAD", "--", path)
        if target:
            git("add", "--", path)
            git("commit", "--quiet", f"--fixup={target}")
        else:
            unmatched.append(path)
    return unmatched


def autosquash(base: str) -> bool:
    environment = {**os.environ, "GIT_SEQUENCE_EDITOR": "true"}
    result = subprocess.run(["git", "rebase", "--quiet", "-i", "--autosquash", base],
                            capture_output=True, text=True, env=environment)
    if result.returncode == 0:
        return True
    git("rebase", "--abort", allow_failure=True)
    return False


def commit_new_round(paths: list[str], round_number: int) -> None:
    git("add", "--", *paths)
    git("commit", "--quiet", "-m", f"Address Copilot review (round {round_number})")


def default_branch() -> str:
    return git("symbolic-ref", "--short", "refs/remotes/origin/HEAD", allow_failure=True) or "origin/main"


def git(*arguments: str, allow_failure: bool = False) -> str:
    result = subprocess.run(["git", *arguments], capture_output=True, text=True)
    if result.returncode != 0 and not allow_failure:
        sys.exit(f"git {arguments[0]} failed: {result.stderr.strip()}")
    return result.stdout.strip() if result.returncode == 0 else ""
