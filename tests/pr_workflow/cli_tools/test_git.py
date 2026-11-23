"""Tests for the shared git wrapper against a throwaway repository."""

import subprocess
from pathlib import Path

import pytest

from cli_tools import git
from cli_tools.command import CommandFailed


@pytest.fixture
def checkout(tmp_path: Path) -> Path:
    subprocess.run(["git", "init", "-q", "-b", "main", str(tmp_path)], check=True)
    return tmp_path


def test_git_runs_in_the_given_directory(checkout: Path) -> None:
    assert Path(git.read("rev-parse", "--show-toplevel", cwd=checkout)).resolve() == checkout.resolve()


def test_read_strips_surrounding_whitespace_but_run_does_not(checkout: Path) -> None:
    assert git.run("rev-parse", "--is-inside-work-tree", cwd=checkout) == "true\n"
    assert git.read("rev-parse", "--is-inside-work-tree", cwd=checkout) == "true"


def test_a_failure_names_the_subcommand_and_carries_git_s_error_text(checkout: Path) -> None:
    with pytest.raises(CommandFailed, match="git cat-file failed: .*nonexistent") as failure:
        git.read("cat-file", "-t", "nonexistent", cwd=checkout)
    assert "nonexistent" in failure.value.stderr


def test_an_allowed_failure_yields_empty_output(checkout: Path) -> None:
    assert git.read("rev-parse", "--verify", "nonexistent", cwd=checkout, allow_failure=True) == ""


def test_a_missing_directory_is_a_failure(tmp_path: Path) -> None:
    with pytest.raises(CommandFailed):
        git.read("status", cwd=tmp_path / "missing")


def test_succeeds_reports_the_exit_status_as_a_boolean(checkout: Path) -> None:
    assert git.succeeds("rev-parse", "--git-dir", cwd=checkout)
    assert not git.succeeds("rev-parse", "--verify", "nonexistent", cwd=checkout)


def test_the_environment_is_passed_through(checkout: Path) -> None:
    environment = {"PATH": "/usr/bin:/bin", "GIT_AUTHOR_NAME": "Wrapper Test",
                   "GIT_AUTHOR_EMAIL": "wrapper@example.com"}
    assert git.read("var", "GIT_AUTHOR_IDENT", cwd=checkout, env=environment).startswith("Wrapper Test <")


def test_text_can_be_piped_to_git(checkout: Path) -> None:
    trailer = "Co-Authored-By: Someone <someone@example.com>"
    message = git.run("interpret-trailers", "--trailer", trailer, stdin="Subject\n", cwd=checkout)
    assert message.rstrip("\n").endswith(trailer)
