"""Removes local branches whose pull request merged, and their clean worktrees, skipping anything that could lose work."""

import argparse
import subprocess
from dataclasses import dataclass
from pathlib import Path

from git_repository import GitRepository, Worktree
from pull_requests import GitHubPullRequests, PullRequest

REMOVED = "removed"
WOULD_REMOVE = "would remove"
SKIPPED = "skipped"


@dataclass(frozen=True)
class Outcome:
    branch: str
    action: str
    detail: str = ""


def main() -> None:
    arguments = parse_arguments()
    repository = GitRepository(Path.cwd())
    repository.fetch_prune()
    outcomes = clean_branches(repository, GitHubPullRequests(Path.cwd()), arguments.dry_run)
    print(report(outcomes))


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Only report what would be removed.")
    return parser.parse_args()


def clean_branches(repository: GitRepository, pull_requests, dry_run: bool) -> list[Outcome]:
    default_branch = pull_requests.default_branch()
    checkouts = checkouts_by_branch(repository)
    return [clean_branch(branch, checkouts.get(branch, []), repository, pull_requests, dry_run)
            for branch in repository.local_branches() if branch != default_branch]


def checkouts_by_branch(repository: GitRepository) -> dict[str, list[Worktree]]:
    checkouts: dict[str, list[Worktree]] = {}
    for worktree in repository.worktrees():
        if worktree.branch:
            checkouts.setdefault(worktree.branch, []).append(worktree)
    return checkouts


def clean_branch(branch: str, checkouts: list[Worktree], repository: GitRepository,
                 pull_requests, dry_run: bool) -> Outcome:
    if len(checkouts) > 1:
        return Outcome(branch, SKIPPED, "checked out in several worktrees")
    worktree = checkouts[0] if checkouts else None
    try:
        checked_head = repository.branch_head(branch)
        reason = reason_to_keep(branch, checked_head, worktree, repository, pull_requests)
    except subprocess.CalledProcessError as failure:
        return Outcome(branch, SKIPPED, f"check failed: {failure.stderr.strip()}")
    if reason:
        return Outcome(branch, SKIPPED, reason)
    if dry_run:
        return Outcome(branch, WOULD_REMOVE, worktree_detail(worktree))
    return remove_branch_and_worktree(branch, checked_head, worktree, repository)


def reason_to_keep(branch: str, checked_head: str, worktree: Worktree | None,
                   repository: GitRepository, pull_requests) -> str | None:
    return (worktree_in_use_reason(worktree, repository)
            or pull_request_reason(branch, checked_head, pull_requests)
            or dirty_reason(worktree, repository))


def worktree_in_use_reason(worktree: Worktree | None, repository: GitRepository) -> str | None:
    if worktree is None:
        return None
    if worktree.path == repository.current_worktree():
        return "current worktree"
    if worktree.path == repository.main_worktree():
        return "checked out in the main worktree"
    if worktree.locked:
        return f"worktree {worktree.path} is locked"
    return None


def pull_request_reason(branch: str, checked_head: str, pull_requests) -> str | None:
    branch_pull_requests = pull_requests.for_branch(branch)
    open_pull = next((pull for pull in branch_pull_requests if pull.state == "OPEN"), None)
    if open_pull:
        return f"PR #{open_pull.number} is open"
    last_merged = latest_merged(branch_pull_requests)
    if last_merged is None:
        return closed_or_missing_reason(branch_pull_requests)
    return unpushed_commits_reason(checked_head, last_merged)


def latest_merged(branch_pull_requests: list[PullRequest]) -> PullRequest | None:
    merged = [pull for pull in branch_pull_requests if pull.state == "MERGED"]
    return max(merged, key=lambda pull: pull.merged_at or "", default=None)


def closed_or_missing_reason(branch_pull_requests: list[PullRequest]) -> str:
    if branch_pull_requests:
        return f"PR #{branch_pull_requests[0].number} was closed without merging"
    return "no pull request found"


def unpushed_commits_reason(checked_head: str, last_merged: PullRequest) -> str | None:
    if checked_head == last_merged.head:
        return None
    return f"local head differs from PR #{last_merged.number}'s final head (unpushed commits)"


def dirty_reason(worktree: Worktree | None, repository: GitRepository) -> str | None:
    if worktree and not repository.is_clean(worktree.path):
        return f"worktree {worktree.path} has uncommitted or untracked changes"
    return None


def worktree_detail(worktree: Worktree | None) -> str:
    return f"with worktree {worktree.path}" if worktree else ""


def remove_branch_and_worktree(branch: str, checked_head: str, worktree: Worktree | None,
                               repository: GitRepository) -> Outcome:
    try:
        if worktree:
            repository.remove_worktree(worktree.path)
    except subprocess.CalledProcessError as failure:
        return Outcome(branch, SKIPPED, f"git failed: {failure.stderr.strip()}")
    try:
        repository.delete_branch_at(branch, checked_head)
    except subprocess.CalledProcessError as failure:
        return Outcome(branch, SKIPPED, f"git failed: {failure.stderr.strip()}{removed_worktree_note(worktree)}")
    return Outcome(branch, REMOVED, worktree_detail(worktree))


def removed_worktree_note(worktree: Worktree | None) -> str:
    return f" (worktree {worktree.path} was already removed)" if worktree else ""


def report(outcomes: list[Outcome]) -> str:
    if not outcomes:
        return "No local branches other than the default branch."
    return "\n".join(describe(outcome) for outcome in outcomes)


def describe(outcome: Outcome) -> str:
    summary = f"{outcome.action} {outcome.branch}"
    if not outcome.detail:
        return summary
    return f"{summary}{detail_separator(outcome)}{outcome.detail}"


def detail_separator(outcome: Outcome) -> str:
    return ": " if outcome.action == SKIPPED else " "


if __name__ == "__main__":
    main()
