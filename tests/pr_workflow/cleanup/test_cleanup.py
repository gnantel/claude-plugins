"""Tests for removing merged local branches and their worktrees, and for what is kept and why."""

import subprocess
from pathlib import Path

from cleanup import Outcome, clean_branches
from conftest import FakePullRequests, add_worktree, git
from git_repository import GitRepository


def outcome_for(outcomes: list[Outcome], branch: str) -> Outcome:
    return next(outcome for outcome in outcomes if outcome.branch == branch)


def branches(directory: Path) -> list[str]:
    return git(directory, "branch", "--format=%(refname:short)").splitlines()


def test_a_merged_and_fully_pushed_branch_is_removed_with_its_clean_worktree(
        main_checkout: Path, repository: GitRepository, pull_requests: FakePullRequests) -> None:
    worktree = add_worktree(main_checkout, "7-done")
    pull_requests.merge("7-done", git(worktree, "rev-parse", "HEAD"))

    outcomes = clean_branches(repository, pull_requests, dry_run=False)

    assert outcome_for(outcomes, "7-done").action == "removed"
    assert not worktree.exists()
    assert branches(main_checkout) == ["main"]


def test_a_merged_branch_without_a_worktree_is_removed(
        main_checkout: Path, repository: GitRepository, pull_requests: FakePullRequests) -> None:
    git(main_checkout, "branch", "7-done")
    pull_requests.merge("7-done", git(main_checkout, "rev-parse", "7-done"))

    clean_branches(repository, pull_requests, dry_run=False)

    assert branches(main_checkout) == ["main"]


def test_a_branch_with_commits_after_the_pr_head_is_kept(
        main_checkout: Path, repository: GitRepository, pull_requests: FakePullRequests) -> None:
    worktree = add_worktree(main_checkout, "7-done")
    pull_requests.merge("7-done", git(worktree, "rev-parse", "HEAD"))
    git(worktree, "commit", "--allow-empty", "-m", "unpushed")

    outcomes = clean_branches(repository, pull_requests, dry_run=False)

    assert "unpushed commits" in outcome_for(outcomes, "7-done").detail
    assert worktree.exists()
    assert "7-done" in branches(main_checkout)


def test_a_worktree_with_a_modified_file_is_kept(
        main_checkout: Path, repository: GitRepository, pull_requests: FakePullRequests) -> None:
    (main_checkout / "notes.txt").write_text("v1")
    git(main_checkout, "add", "notes.txt")
    git(main_checkout, "commit", "-m", "notes")
    worktree = add_worktree(main_checkout, "7-done")
    pull_requests.merge("7-done", git(worktree, "rev-parse", "HEAD"))
    (worktree / "notes.txt").write_text("v2")

    outcomes = clean_branches(repository, pull_requests, dry_run=False)

    assert "uncommitted or untracked" in outcome_for(outcomes, "7-done").detail
    assert worktree.exists()
    assert "7-done" in branches(main_checkout)


def test_a_worktree_with_an_untracked_file_is_kept(
        main_checkout: Path, repository: GitRepository, pull_requests: FakePullRequests) -> None:
    worktree = add_worktree(main_checkout, "7-done")
    pull_requests.merge("7-done", git(worktree, "rev-parse", "HEAD"))
    (worktree / "scratch.txt").write_text("mine")

    outcomes = clean_branches(repository, pull_requests, dry_run=False)

    assert outcome_for(outcomes, "7-done").action == "skipped"
    assert (worktree / "scratch.txt").exists()


def test_a_branch_with_an_open_pr_is_kept(
        main_checkout: Path, repository: GitRepository, pull_requests: FakePullRequests) -> None:
    worktree = add_worktree(main_checkout, "7-wip")
    pull_requests.set_state("7-wip", "OPEN", git(worktree, "rev-parse", "HEAD"))

    outcomes = clean_branches(repository, pull_requests, dry_run=False)

    assert outcome_for(outcomes, "7-wip").detail == "PR #2 is open"
    assert worktree.exists()


def test_a_branch_whose_pr_closed_without_merging_is_kept_and_reported(
        main_checkout: Path, repository: GitRepository, pull_requests: FakePullRequests) -> None:
    git(main_checkout, "branch", "7-dropped")
    pull_requests.set_state("7-dropped", "CLOSED", git(main_checkout, "rev-parse", "7-dropped"))

    outcomes = clean_branches(repository, pull_requests, dry_run=False)

    assert outcome_for(outcomes, "7-dropped").detail == "PR #2 was closed without merging"
    assert "7-dropped" in branches(main_checkout)


def test_a_branch_without_a_pr_is_kept(
        main_checkout: Path, repository: GitRepository, pull_requests: FakePullRequests) -> None:
    git(main_checkout, "branch", "7-idea")

    outcomes = clean_branches(repository, pull_requests, dry_run=False)

    assert outcome_for(outcomes, "7-idea").detail == "no pull request found"


def test_the_current_worktree_and_its_branch_are_kept_even_when_merged(
        main_checkout: Path, pull_requests: FakePullRequests) -> None:
    worktree = add_worktree(main_checkout, "7-done")
    pull_requests.merge("7-done", git(worktree, "rev-parse", "HEAD"))

    outcomes = clean_branches(GitRepository(worktree), pull_requests, dry_run=False)

    assert outcome_for(outcomes, "7-done").detail == "current worktree"
    assert worktree.exists()
    assert "7-done" in branches(main_checkout)


def test_a_branch_checked_out_in_the_main_worktree_is_kept(
        main_checkout: Path, pull_requests: FakePullRequests) -> None:
    git(main_checkout, "checkout", "-b", "7-done")
    pull_requests.merge("7-done", git(main_checkout, "rev-parse", "HEAD"))
    other_worktree = add_worktree(main_checkout, "8-other")

    outcomes = clean_branches(GitRepository(other_worktree), pull_requests, dry_run=False)

    assert outcome_for(outcomes, "7-done").detail == "checked out in the main worktree"


def test_a_dry_run_reports_what_would_be_removed_and_removes_nothing(
        main_checkout: Path, repository: GitRepository, pull_requests: FakePullRequests) -> None:
    worktree = add_worktree(main_checkout, "7-done")
    pull_requests.merge("7-done", git(worktree, "rev-parse", "HEAD"))

    outcomes = clean_branches(repository, pull_requests, dry_run=True)

    assert outcome_for(outcomes, "7-done").action == "would remove"
    assert worktree.exists()
    assert "7-done" in branches(main_checkout)


def test_the_default_branch_is_never_listed(
        repository: GitRepository, pull_requests: FakePullRequests) -> None:
    assert clean_branches(repository, pull_requests, dry_run=False) == []


def test_a_commit_made_after_the_check_keeps_the_branch(
        main_checkout: Path, repository: GitRepository, pull_requests: FakePullRequests) -> None:
    git(main_checkout, "branch", "7-done")
    pull_requests.merge("7-done", git(main_checkout, "rev-parse", "7-done"))
    delete_branch_at = repository.delete_branch_at

    def delete_after_new_commit(branch: str, head: str) -> None:
        git(main_checkout, "commit", "--allow-empty", "-m", "late")
        git(main_checkout, "branch", "-f", branch, "HEAD")
        delete_branch_at(branch, head)

    repository.delete_branch_at = delete_after_new_commit

    outcomes = clean_branches(repository, pull_requests, dry_run=False)

    assert outcome_for(outcomes, "7-done").action == "skipped"
    assert "7-done" in branches(main_checkout)


def test_a_failed_branch_deletion_reports_the_worktree_already_removed(
        main_checkout: Path, repository: GitRepository, pull_requests: FakePullRequests) -> None:
    worktree = add_worktree(main_checkout, "7-done")
    pull_requests.merge("7-done", git(worktree, "rev-parse", "HEAD"))
    delete_branch_at = repository.delete_branch_at

    def delete_after_new_commit(branch: str, head: str) -> None:
        git(main_checkout, "commit", "--allow-empty", "-m", "late")
        git(main_checkout, "branch", "-f", branch, "main")
        delete_branch_at(branch, head)

    repository.delete_branch_at = delete_after_new_commit

    outcomes = clean_branches(repository, pull_requests, dry_run=False)

    assert f"worktree {worktree.resolve()} was already removed" in outcome_for(outcomes, "7-done").detail


def test_a_failing_lookup_skips_the_branch_and_the_rest_are_still_cleaned(
        main_checkout: Path, repository: GitRepository, pull_requests: FakePullRequests) -> None:
    git(main_checkout, "branch", "7-broken")
    git(main_checkout, "branch", "8-done")
    pull_requests.merge("8-done", git(main_checkout, "rev-parse", "8-done"))
    for_branch = pull_requests.for_branch

    def failing_for_one(branch: str):
        if branch == "7-broken":
            raise subprocess.CalledProcessError(1, "gh", stderr="boom")
        return for_branch(branch)

    pull_requests.for_branch = failing_for_one

    outcomes = clean_branches(repository, pull_requests, dry_run=False)

    assert outcome_for(outcomes, "7-broken").detail == "check failed: boom"
    assert outcome_for(outcomes, "8-done").action == "removed"


def test_a_branch_sharing_its_name_with_a_tag_is_cleaned(
        main_checkout: Path, repository: GitRepository, pull_requests: FakePullRequests) -> None:
    git(main_checkout, "branch", "7-done")
    git(main_checkout, "tag", "7-done")
    pull_requests.merge("7-done", git(main_checkout, "rev-parse", "refs/heads/7-done"))

    clean_branches(repository, pull_requests, dry_run=False)

    assert branches(main_checkout) == ["main"]


def test_a_worktree_path_with_non_ascii_characters_is_cleaned(
        main_checkout: Path, repository: GitRepository, pull_requests: FakePullRequests) -> None:
    worktree = main_checkout.parent / "tréma"
    git(main_checkout, "worktree", "add", "-b", "7-done", str(worktree))
    pull_requests.merge("7-done", git(worktree, "rev-parse", "HEAD"))

    clean_branches(repository, pull_requests, dry_run=False)

    assert not worktree.exists()


def test_a_branch_checked_out_in_several_worktrees_is_kept(
        main_checkout: Path, repository: GitRepository, pull_requests: FakePullRequests) -> None:
    first = add_worktree(main_checkout, "7-done")
    second = main_checkout.parent / "second"
    git(main_checkout, "worktree", "add", "--force", str(second), "7-done")
    pull_requests.merge("7-done", git(first, "rev-parse", "HEAD"))

    outcomes = clean_branches(repository, pull_requests, dry_run=False)

    assert outcome_for(outcomes, "7-done").detail == "checked out in several worktrees"
    assert first.exists() and second.exists()


def test_a_locked_worktree_is_kept_in_a_dry_run_too(
        main_checkout: Path, repository: GitRepository, pull_requests: FakePullRequests) -> None:
    worktree = add_worktree(main_checkout, "7-done")
    pull_requests.merge("7-done", git(worktree, "rev-parse", "HEAD"))
    git(main_checkout, "worktree", "lock", str(worktree))

    outcomes = clean_branches(repository, pull_requests, dry_run=True)

    assert outcome_for(outcomes, "7-done").action == "skipped"
    assert "is locked" in outcome_for(outcomes, "7-done").detail


def test_the_current_worktree_is_kept_when_its_path_ends_with_a_space(
        main_checkout: Path, pull_requests: FakePullRequests) -> None:
    worktree = main_checkout.parent / "spaced "
    git(main_checkout, "worktree", "add", "-b", "7-done", str(worktree))
    pull_requests.merge("7-done", git(worktree, "rev-parse", "HEAD"))

    outcomes = clean_branches(GitRepository(worktree), pull_requests, dry_run=True)

    assert outcome_for(outcomes, "7-done").detail == "current worktree"
