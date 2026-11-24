"""Commits and pushes one round of Copilot review fixes: amends them into the branch's single commit while only bots have reviewed, and adds a new commit once a person has reviewed."""

import os
import sys

import github
import local_git
import review_state


def push_round(number: int | None, round_number: int, single_commit_message: str | None = None) -> dict:
    pull = pull_verified_for_push(number)
    changed_files = changed_paths_or_exit()
    mode = review_state.commit_mode(pull)
    co_authors = local_git.co_author_trailers(local_git.message_of("HEAD"))
    if mode == "rewrite":
        mode = push_rewritten(pull, changed_files, round_number, single_commit_message, co_authors)
    else:
        push_new_round(pull, changed_files, round_number, co_authors)
    return {"mode": mode, "head": local_git.head(), "short": local_git.git("rev-parse", "--short", "HEAD")}


def pull_verified_for_push(number: int | None) -> dict:
    pull = github.pull_request(number)
    if pull["from_fork"]:
        sys.exit("Pull requests from forks aren't supported: push-round pushes to origin, not the fork.")
    if local_git.head() != pull["head"]:
        sys.exit("Local HEAD differs from the PR head (someone pushed?). Run next-round again before pushing.")
    return pull


def changed_paths_or_exit() -> list[str]:
    changed_files = local_git.changed_paths()
    if not changed_files:
        sys.exit("No changes to push: fix the threads first, or end the loop if every comment was declined.")
    return changed_files


def push_rewritten(pull: dict, changed_files: list[str], round_number: int, single_commit_message: str | None,
                   co_authors: list[str]) -> str:
    base = local_git.branch_base(pull["base"])
    unmatched = commit_fixups(changed_files, base)
    if unmatched:
        commit_new_round(unmatched, round_number, co_authors)
    destination = f"refs/heads/{pull['head_ref']}"
    if autosquash(base):
        replace_message(base, single_commit_message, co_authors)
        force_push_with_lease(destination, pull["head"])
        return "rewrite"
    push_head(destination)
    return "rewrite-failed-pushed-fixups"


def commit_fixups(changed_files: list[str], base: str) -> list[str]:
    unmatched = []
    sole_commit = local_git.sole_branch_commit(base)
    for path in changed_files:
        target = sole_commit or local_git.last_branch_commit_touching(base, path)
        if target:
            local_git.git("add", "--", path, allow_failure=True)
            local_git.git("commit", "--quiet", "-m", amend_message(target), "--", path)
        else:
            unmatched.append(path)
    return unmatched


def amend_message(target: str) -> str:
    return f"amend! {local_git.subject_of(target)}\n\n{local_git.message_of(target)}"


def commit_new_round(paths: list[str], round_number: int, co_authors: list[str]) -> None:
    for path in paths:
        local_git.git("add", "--", path, allow_failure=True)
    attributed = local_git.with_default_co_authors(f"Address Copilot review (round {round_number})", co_authors)
    local_git.git("commit", "--quiet", "-m", attributed, "--", *paths)


def autosquash(base: str) -> bool:
    environment = {**os.environ, "GIT_SEQUENCE_EDITOR": "true", "GIT_EDITOR": "true"}
    succeeded = local_git.succeeds("rebase", "--quiet", "-i", "--autosquash", base, environment=environment)
    while not succeeded and local_git.stopped_on_emptied_commit():
        local_git.git("reset", "--soft", "HEAD~1")
        succeeded = local_git.succeeds("rebase", "--continue", environment=environment)
    if not succeeded:
        local_git.git("rebase", "--abort", allow_failure=True)
    return succeeded


def replace_message(base: str, single_commit_message: str | None, co_authors: list[str]) -> None:
    if single_commit_message and local_git.sole_branch_commit(base):
        attributed = local_git.with_default_co_authors(single_commit_message, co_authors)
        local_git.git("commit", "--quiet", "--amend", "-m", attributed)


def force_push_with_lease(destination: str, expected_head: str) -> None:
    local_git.git("push", "--quiet", f"--force-with-lease={destination}:{expected_head}",
                  "origin", f"HEAD:{destination}")


def push_head(destination: str) -> None:
    local_git.git("push", "--quiet", "origin", f"HEAD:{destination}")


def push_new_round(pull: dict, changed_files: list[str], round_number: int, co_authors: list[str]) -> None:
    commit_new_round(changed_files, round_number, co_authors)
    push_head(f"refs/heads/{pull['head_ref']}")
