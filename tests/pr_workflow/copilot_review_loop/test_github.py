"""Tests for the GitHub access behind the Copilot review loop: paging through review threads and their comments, with the gh CLI replaced by stand-ins."""

import pytest

import github
from cli_tools import gh


def comment_page(bodies: list[str], next_cursor: str | None = None) -> dict:
    return {"pageInfo": {"hasNextPage": next_cursor is not None, "endCursor": next_cursor},
            "nodes": [{"author": {"login": "copilot-pull-request-reviewer"}, "body": body, "url": "u"} for body in bodies]}


def thread_page(threads: list[dict], next_cursor: str | None = None) -> dict:
    return {"repository": {"pullRequest": {"reviewThreads": {
        "pageInfo": {"hasNextPage": next_cursor is not None, "endCursor": next_cursor}, "nodes": threads}}}}


def test_review_threads_follow_every_page(monkeypatch: pytest.MonkeyPatch) -> None:
    pages = {None: thread_page([{"id": "A", "comments": comment_page(["a"])}], next_cursor="page-2"),
             "page-2": thread_page([{"id": "B", "comments": comment_page(["b"])}])}
    monkeypatch.setattr(gh, "graphql", lambda query, **variables: pages[variables.get("after")])
    assert [thread["id"] for thread in github.review_threads("owner/repo", 1)] == ["A", "B"]


def test_a_long_thread_has_all_its_comments(monkeypatch: pytest.MonkeyPatch) -> None:
    later_pages = {"c1": comment_page(["second"], next_cursor="c2"), "c2": comment_page(["third"])}
    monkeypatch.setattr(gh, "graphql",
                        lambda query, **variables: {"node": {"comments": later_pages[variables["after"]]}})
    thread = {"id": "T", "comments": comment_page(["first"], next_cursor="c1")}
    assert [comment["body"] for comment in github.with_all_comments(thread)["comments"]["nodes"]] == [
        "first", "second", "third"]


def test_paginated_rest_results_are_flattened(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gh, "read_json", lambda *arguments: [[{"id": 1}, {"id": 2}], [{"id": 3}]])
    assert [item["id"] for item in gh.paginate("repos/owner/repo/pulls/1/reviews")] == [1, 2, 3]


def test_review_comments_are_counted_across_pages(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gh, "read_json", lambda *arguments: [[{"id": n} for n in range(30)], [{"id": 30}]])
    assert github.review_comment_count("owner/repo", 1, 99) == 31
