"""Tests for the shared command runner: how failures, missing executables and a missing directory are reported."""

import sys

import pytest

from cli_tools.command import CommandFailed, run_command


def test_output_is_returned_unchanged() -> None:
    assert run_command(sys.executable, ("-c", "print('  hi  ')"), summary_words=0) == "  hi  \n"


def test_a_failing_command_reports_its_trimmed_error_text() -> None:
    with pytest.raises(CommandFailed) as failure:
        run_command(sys.executable, ("-c", "import sys; sys.stderr.write('boom\\n'); sys.exit(3)"), summary_words=0)
    assert failure.value.stderr == "boom"
    assert str(failure.value) == f"{sys.executable} failed: boom"


def test_the_summary_names_the_requested_number_of_arguments() -> None:
    with pytest.raises(CommandFailed) as failure:
        run_command(sys.executable, ("-c", "import sys; sys.exit(1)"), summary_words=1)
    assert failure.value.summary == f"{sys.executable} -c"


def test_a_missing_executable_is_reported_as_a_failure() -> None:
    with pytest.raises(CommandFailed, match="no-such-tool-anywhere failed"):
        run_command("no-such-tool-anywhere", (), summary_words=0)


def test_a_missing_directory_is_reported_as_a_failure(tmp_path) -> None:
    with pytest.raises(CommandFailed):
        run_command(sys.executable, ("-c", "pass"), summary_words=0, cwd=tmp_path / "missing")


def test_standard_input_reaches_the_command() -> None:
    output = run_command(sys.executable, ("-c", "import sys; print(sys.stdin.read().upper())"),
                         summary_words=0, stdin="abc")
    assert output == "ABC\n"


def test_an_environment_replaces_the_inherited_one() -> None:
    output = run_command(sys.executable, ("-c", "import os; print(os.environ.get('WRAPPER_TEST'))"),
                         summary_words=0, env={"WRAPPER_TEST": "set"})
    assert output == "set\n"
