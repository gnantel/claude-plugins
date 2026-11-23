"""Tests for the shared gh wrapper, with a stand-in gh executable on PATH."""

import json

import pytest

from cli_tools import gh
from cli_tools.command import CommandFailed


def test_read_returns_trimmed_output_and_run_returns_it_raw(fake_gh) -> None:
    fake_gh.replies(stdout="main\n")
    assert gh.run("repo", "view") == "main\n"
    assert gh.read("repo", "view") == "main"


def test_gh_runs_in_the_given_directory(fake_gh, tmp_path) -> None:
    fake_gh.replies()
    gh.run("repo", "view", cwd=tmp_path)
    assert fake_gh.last_call()["cwd"] == str(tmp_path.resolve())


def test_json_output_is_parsed(fake_gh) -> None:
    fake_gh.replies(stdout='{"number": 7}')
    assert gh.read_json("pr", "view") == {"number": 7}


def test_a_failure_names_the_first_two_arguments_and_carries_gh_s_error_text(fake_gh) -> None:
    fake_gh.replies(stderr="not found\n", exit_code=1)
    with pytest.raises(CommandFailed, match="gh pr view failed: not found") as failure:
        gh.read_json("pr", "view", "7")
    assert failure.value.stderr == "not found"


def test_an_allowed_failure_yields_no_json(fake_gh) -> None:
    fake_gh.replies(stderr="no PR", exit_code=1)
    assert gh.read_json("pr", "view", allow_failure=True) is None


def test_graphql_sends_the_query_and_typed_variables_and_returns_the_data(fake_gh) -> None:
    fake_gh.replies(stdout='{"data": {"ok": true}}')
    assert gh.graphql("query { x }", owner="octo", number=5, after=None) == {"ok": True}
    assert fake_gh.last_call()["arguments"] == ["api", "graphql", "-f", "query=query { x }",
                                                "-f", "owner=octo", "-F", "number=5"]


def test_paginated_pages_are_flattened_into_one_list(fake_gh) -> None:
    fake_gh.replies(stdout=json.dumps([[{"id": 1}, {"id": 2}], [{"id": 3}]]))
    assert gh.paginate("repos/o/r/pulls/1/reviews") == [{"id": 1}, {"id": 2}, {"id": 3}]
    assert fake_gh.last_call()["arguments"] == ["api", "--paginate", "--slurp", "repos/o/r/pulls/1/reviews"]
