"""Commits and pushes one round of Copilot review fixes: folds them into the commits they fix while only bots have reviewed, and adds a new commit once a person has reviewed."""

import os
import sys

import github
import local_git
import review_state

CO_AUTHOR_TRAILER = "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"


def push_round(number: int | None, round_number: int) -> dict:
    pull = github.pull_request(number)
    if pull["from_fork"]:
        sys.exit("Pull requests from forks aren't supported: push-round pushes to origin, not the fork.")
    if local_git.head() != pull["head"]:
        sys.exit("Local HEAD differs from the PR head (someone pushed?). Run next-round again before pushing.")
    changed_files = local_git.changed_paths()
    if not changed_files:
        sys.exit("No changes to push: fix the threads first, or end the loop if every comment was declined.")
    mode = review_state.commit_mode(pull)
    if mode == "rewrite":
        mode = push_rewritten(pull, changed_files, round_number)
    else:
        commit_new_round(changed_files, round_number)
        local_git.git("push", "--quiet", "origin", f"HEAD:refs/heads/{pull['head_ref']}")
    return {"mode": mode, "head": local_git.head(), "short": local_git.git("rev-parse", "--short", "HEAD")}


def push_rewritten(pull: dict, changed_files: list[str], round_number: int) -> str:
    base = local_git.branch_base(pull["base"])
    unmatched = commit_fixups(changed_files, base)
    if unmatched:
        commit_new_round(unmatched, round_number)
    destination = f"refs/heads/{pull['head_ref']}"
    if autosquash(base):
        local_git.git("push", "--quiet", f"--force-with-lease={destination}:{pull['head']}",
                      "origin", f"HEAD:{destination}")
        return "rewrite"
    local_git.git("push", "--quiet", "origin", f"HEAD:{destination}")
    return "rewrite-failed-pushed-fixups"


def commit_fixups(changed_files: list[str], base: str) -> list[str]:
    unmatched = []
    for path in changed_files:
        target = local_git.last_branch_commit_touching(base, path)
        if target:
            local_git.git("add", "--", path, allow_failure=True)
            local_git.git("commit", "--quiet", "-m", amend_message(target), "--", path)
        else:
            unmatched.append(path)
    return unmatched


def amend_message(target: str) -> str:
    attributed = local_git.with_trailer(local_git.message_of(target), CO_AUTHOR_TRAILER)
    return f"amend! {local_git.subject_of(target)}\n\n{attributed}"


def autosquash(base: str) -> bool:
    environment = {**os.environ, "GIT_SEQUENCE_EDITOR": "true"}
    if local_git.succeeds("rebase", "--quiet", "-i", "--autosquash", base, environment=environment):
        return True
    local_git.git("rebase", "--abort", allow_failure=True)
    return False


def commit_new_round(paths: list[str], round_number: int) -> None:
    for path in paths:
        local_git.git("add", "--", path, allow_failure=True)
    message = f"Address Copilot review (round {round_number})\n\n{CO_AUTHOR_TRAILER}"
    local_git.git("commit", "--quiet", "-m", message, "--", *paths)
