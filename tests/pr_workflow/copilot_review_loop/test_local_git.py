"""Tests for the local git operations behind the Copilot review loop, run against a scratch repository."""

import local_git

TRAILER = "Co-Authored-By: Claude <noreply@anthropic.com>"


def test_changed_paths_include_modified_staged_and_untracked_files(repository) -> None:
    repository.commit("Add files", **{"modified.py": "a", "staged.py": "b"})
    repository.write("modified.py", "a changed")
    repository.write("staged.py", "b changed")
    repository.git("add", "staged.py")
    repository.write("new.py", "c")
    assert sorted(local_git.changed_paths()) == ["modified.py", "new.py", "staged.py"]


def test_changed_paths_keep_unusual_file_names_intact(repository) -> None:
    repository.write("ünï code name.py", "x")
    assert local_git.changed_paths() == ["ünï code name.py"]


def test_changed_paths_report_both_sides_of_a_staged_rename(repository) -> None:
    repository.commit("Add old", **{"old.py": "content"})
    repository.git("mv", "old.py", "new.py")
    assert sorted(local_git.changed_paths()) == ["new.py", "old.py"]


def test_a_clean_tree_is_not_dirty(repository) -> None:
    assert not local_git.is_dirty()


def test_an_untracked_file_makes_the_tree_dirty(repository) -> None:
    repository.write("stray.txt", "x")
    assert local_git.is_dirty()


def test_branch_base_is_the_merge_base_with_the_named_branch(repository) -> None:
    main_commit = repository.git("rev-parse", "origin/main")
    repository.commit("Feature work", **{"a.py": "a"})
    assert local_git.branch_base("main") == main_commit


def test_merge_commits_on_the_branch_are_detected(repository) -> None:
    base = local_git.branch_base("main")
    repository.git("checkout", "-q", "-b", "side")
    repository.commit("Side work", **{"side.py": "s"})
    repository.git("checkout", "-q", "feature")
    repository.git("merge", "-q", "--no-ff", "-m", "Merge side", "side")
    assert local_git.has_merge_commits(base)


def test_a_linear_branch_has_no_merge_commits(repository) -> None:
    repository.commit("Feature work", **{"a.py": "a"})
    assert not local_git.has_merge_commits(local_git.branch_base("main"))


def test_the_last_branch_commit_touching_a_file_is_found(repository) -> None:
    repository.commit("Add a", **{"a.py": "a"})
    touching_a = repository.commit("Change a", **{"a.py": "a2"})
    repository.commit("Add b", **{"b.py": "b"})
    assert local_git.last_branch_commit_touching(local_git.branch_base("main"), "a.py") == touching_a


def test_files_only_on_the_base_branch_have_no_branch_commit(repository) -> None:
    repository.commit("Add a", **{"a.py": "a"})
    assert local_git.last_branch_commit_touching(local_git.branch_base("main"), "base.txt") == ""


def test_a_trailer_is_added_after_the_body(repository) -> None:
    assert local_git.with_trailer("Subject\n\nBody text.", TRAILER) == f"Subject\n\nBody text.\n\n{TRAILER}"


def test_an_existing_trailer_is_not_duplicated(repository) -> None:
    message = f"Subject\n\n{TRAILER}"
    assert local_git.with_trailer(message, TRAILER) == message
