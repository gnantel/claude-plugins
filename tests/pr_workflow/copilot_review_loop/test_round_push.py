"""Tests for committing and pushing a round of Copilot review fixes, run against a scratch repository with a bare remote."""

import pytest

import local_git
import review_state
import round_push
from cli_tools.command import CommandFailed


@pytest.fixture
def rewrite_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(review_state, "commit_mode", lambda pull: "rewrite")


@pytest.fixture
def new_commit_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(review_state, "commit_mode", lambda pull: "new-commit")


def push_round_for_pull_request(pull_request, **overrides) -> dict:
    pull_request(**overrides)
    return round_push.push_round(1, 3)


def test_rewrite_folds_a_fix_into_the_commit_that_introduced_the_file(repository, pull_request, rewrite_mode) -> None:
    repository.commit("Add parser", **{"parser.py": "v1"})
    repository.commit("Add cli", **{"cli.py": "v1"})
    repository.push()
    repository.write("parser.py", "v1 fixed")
    assert push_round_for_pull_request(pull_request)["mode"] == "rewrite"
    assert repository.remote_subjects() == ["Add cli", "Add parser"]
    assert repository.remote_file("parser.py") == "v1 fixed"


def test_rewrite_adds_attribution_to_the_commit_a_fix_is_folded_into(repository, pull_request, rewrite_mode) -> None:
    repository.commit("Add parser\n\nParses the input.", **{"parser.py": "v1"})
    repository.push()
    repository.write("parser.py", "v1 fixed")
    push_round_for_pull_request(pull_request)
    message = repository.remote_message("Add parser")
    assert "Parses the input." in message
    assert message.count(round_push.CO_AUTHOR_TRAILER) == 1


def test_rewrite_puts_a_new_file_in_a_round_commit_on_a_multi_commit_branch(repository, pull_request, rewrite_mode) -> None:
    repository.commit("Add cli", **{"cli.py": "v1"})
    repository.commit("Add parser", **{"parser.py": "v1"})
    repository.push()
    repository.write("helper.py", "new")
    push_round_for_pull_request(pull_request)
    assert repository.remote_subjects() == ["Address Copilot review (round 3)", "Add parser", "Add cli"]
    assert round_push.CO_AUTHOR_TRAILER in repository.remote_message(r"Address Copilot review (round 3)")


def test_rewrite_folds_a_new_file_into_the_single_commit(repository, pull_request, rewrite_mode) -> None:
    repository.commit("Add parser", **{"parser.py": "v1"})
    repository.push()
    repository.write("helper.py", "new")
    push_round_for_pull_request(pull_request)
    assert repository.remote_subjects() == ["Add parser"]
    assert repository.remote_file("helper.py") == "new"


def test_rewrite_replaces_the_message_of_the_single_commit(repository, pull_request, rewrite_mode) -> None:
    repository.commit("Add parser", **{"parser.py": "v1"})
    repository.push()
    repository.write("parser.py", "v1 fixed")
    pull_request()
    round_push.push_round(1, 3, "Add parser and its validation\n\nCloses #5")
    assert repository.remote_subjects() == ["Add parser and its validation"]
    message = repository.remote_message("Add parser and its validation")
    assert "Closes #5" in message
    assert message.count(round_push.CO_AUTHOR_TRAILER) == 1


def test_rewrite_folds_each_staged_file_into_its_own_commit(repository, pull_request, rewrite_mode) -> None:
    repository.commit("Add a", **{"a.py": "a"})
    repository.commit("Add b", **{"b.py": "b"})
    repository.push()
    repository.write("a.py", "a fixed")
    repository.write("b.py", "b fixed")
    repository.git("add", "-A")
    push_round_for_pull_request(pull_request)
    assert repository.remote_subjects() == ["Add b", "Add a"]
    assert repository.git("show", "--format=", "--name-only", "origin/feature~1") == "a.py"


def test_rewrite_handles_a_staged_rename(repository, pull_request, rewrite_mode) -> None:
    repository.commit("Add old", **{"old.py": "content"})
    repository.push()
    repository.git("mv", "old.py", "new.py")
    push_round_for_pull_request(pull_request)
    assert repository.git("ls-tree", "--name-only", "origin/feature").splitlines() == ["base.txt", "new.py"]
    assert not local_git.is_dirty()


def test_rewrite_folds_a_restored_file(repository, pull_request, rewrite_mode) -> None:
    repository.commit("Add keep", **{"keep.py": "k"})
    repository.git("rm", "-q", "keep.py")
    repository.git("commit", "-q", "-m", "Remove keep")
    repository.push()
    repository.write("keep.py", "restored")
    push_round_for_pull_request(pull_request)
    assert repository.remote_file("keep.py") == "restored"
    assert repository.remote_subjects() == ["Remove keep", "Add keep"]


def test_rewrite_leaves_the_parent_branch_of_a_stacked_pr_alone(repository, pull_request, rewrite_mode) -> None:
    parent_commit = repository.commit("Parent change", **{"parent.py": "p"})
    repository.push("feature")
    repository.git("checkout", "-q", "-b", "child")
    repository.commit("Child change", **{"child.py": "c"})
    repository.push("child")
    repository.write("parent.py", "p fixed")
    push_round_for_pull_request(pull_request, base="feature", head_ref="child")
    assert repository.remote_subjects("child", "origin/feature") == ["Child change"]
    assert repository.git("rev-parse", "origin/child~1") == parent_commit


def test_a_failed_rebase_pushes_the_unfolded_fixups(repository, pull_request, rewrite_mode, monkeypatch) -> None:
    repository.commit("Add parser", **{"parser.py": "v1"})
    repository.push()
    repository.write("parser.py", "v1 fixed")
    monkeypatch.setattr(local_git, "succeeds", lambda *arguments, **options: False)
    assert push_round_for_pull_request(pull_request)["mode"] == "rewrite-failed-pushed-fixups"
    assert repository.remote_subjects() == ["amend! Add parser", "Add parser"]


def test_new_commit_mode_adds_an_attributed_round_commit(repository, pull_request, new_commit_mode) -> None:
    repository.commit("Add parser", **{"parser.py": "v1"})
    repository.push()
    repository.write("parser.py", "v1 fixed")
    assert push_round_for_pull_request(pull_request)["mode"] == "new-commit"
    assert repository.remote_subjects() == ["Address Copilot review (round 3)", "Add parser"]
    assert round_push.CO_AUTHOR_TRAILER in repository.remote_message(r"Address Copilot review (round 3)")


def test_the_force_push_is_refused_when_someone_else_pushed(repository, pull_request, rewrite_mode) -> None:
    repository.commit("Add parser", **{"parser.py": "v1"})
    repository.push()
    pull = pull_request()
    other_clone = repository.path.parent / "other"
    repository.git("clone", "-q", "-b", "feature", str(repository.remote), str(other_clone), cwd=repository.path.parent)
    repository.git("-c", "user.name=Other", "-c", "user.email=o@example.com", "commit", "-q", "--allow-empty",
                   "-m", "Someone else's commit", cwd=other_clone)
    repository.git("push", "-q", cwd=other_clone)
    repository.git("fetch", "-q")
    repository.write("parser.py", "v1 fixed")
    with pytest.raises(CommandFailed):
        round_push.push_round(pull["number"], 3)
    assert "Someone else's commit" in repository.remote_subjects()


def test_pull_requests_from_forks_are_refused(repository, pull_request, rewrite_mode) -> None:
    repository.write("a.py", "a")
    with pytest.raises(SystemExit, match="forks"):
        push_round_for_pull_request(pull_request, from_fork=True)


def test_a_local_head_that_differs_from_the_pr_is_refused(repository, pull_request, rewrite_mode) -> None:
    repository.write("a.py", "a")
    with pytest.raises(SystemExit, match="differs from the PR head"):
        push_round_for_pull_request(pull_request, head="0" * 40)


def test_nothing_to_push_is_refused(repository, pull_request, rewrite_mode) -> None:
    with pytest.raises(SystemExit, match="No changes to push"):
        push_round_for_pull_request(pull_request)


def test_rewrite_drops_a_commit_that_a_deleting_fix_empties(repository, pull_request, rewrite_mode) -> None:
    repository.commit("Add scratch", **{"scratch.py": "temporary"})
    repository.commit("Add parser", **{"parser.py": "v1"})
    repository.push()
    repository.git("rm", "-q", "scratch.py")
    assert push_round_for_pull_request(pull_request)["mode"] == "rewrite"
    assert repository.remote_subjects() == ["Add parser"]
    assert not local_git.is_dirty()


def test_rewrite_drops_an_emptied_commit_and_still_folds_other_fixes(repository, pull_request, rewrite_mode) -> None:
    repository.commit("Add scratch", **{"scratch.py": "temporary"})
    repository.commit("Add parser", **{"parser.py": "v1"})
    repository.push()
    repository.git("rm", "-q", "scratch.py")
    repository.write("parser.py", "v1 fixed")
    assert push_round_for_pull_request(pull_request)["mode"] == "rewrite"
    assert repository.remote_subjects() == ["Add parser"]
    assert repository.remote_file("parser.py") == "v1 fixed"
