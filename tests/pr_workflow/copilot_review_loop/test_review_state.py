"""Tests for working out where a pull request stands in the Copilot review loop, with GitHub and local git replaced by stand-ins."""

import pytest

import github
import local_git
import pr_issue
import review_state

PULL = {"repo": "owner/repo", "number": 1, "head": "abc", "head_ref": "1-x", "base": "main",
        "from_fork": False, "rebase_merge_allowed": True}
PERSON = {"type": "User", "login": "author"}
BOT = {"type": "Bot", "login": github.COPILOT_REST_LOGIN}


def review(user: dict, state: str = "COMMENTED", body: str = "", commit: str = "abc") -> dict:
    return {"id": 7, "user": user, "state": state, "body": body, "commit_id": commit, "html_url": "url"}


def thread(started_by: str, typename: str, resolved: bool = False) -> dict:
    author = {"login": started_by, "__typename": typename}
    return {"id": "T", "isResolved": resolved, "isOutdated": False, "path": "a.py", "line": 1,
            "comments": {"nodes": [{"author": author, "body": "comment", "url": "thread-url"}]}}


COPILOT_THREAD = thread(github.COPILOT_GRAPHQL_LOGIN, "Bot")
PERSON_THREAD = thread("author", "User")


@pytest.fixture
def github_with(monkeypatch: pytest.MonkeyPatch):
    def stand_in(reviews=(), threads=(), conversation=()) -> None:
        monkeypatch.setattr(github, "reviews", lambda repo, number: list(reviews))
        monkeypatch.setattr(github, "review_threads", lambda repo, number: list(threads))
        monkeypatch.setattr(github, "conversation_comments", lambda repo, number: list(conversation))
    return stand_in


@pytest.mark.parametrize("reviews, threads, conversation, expected", [
    ([review(PERSON)], [], [], False),
    ([review(PERSON, state="APPROVED")], [], [], True),
    ([review(PERSON, state="CHANGES_REQUESTED")], [], [], True),
    ([review(PERSON, state="DISMISSED")], [], [], True),
    ([review(PERSON, body="Looks good overall.")], [], [], True),
    ([review(BOT, body="Copilot summary")], [], [], False),
    ([], [PERSON_THREAD], [], True),
    ([], [COPILOT_THREAD], [], False),
    ([], [], [{"user": {"type": "User"}}], True),
], ids=["loop reply", "approval", "changes requested", "dismissed approval", "written review",
        "bot review", "thread started by a person", "copilot thread", "conversation comment"])
def test_human_review_detection(github_with, reviews, threads, conversation, expected) -> None:
    github_with(reviews, threads, conversation)
    assert review_state.human_reviewed("owner/repo", 1) is expected


@pytest.fixture
def branch_with(monkeypatch: pytest.MonkeyPatch):
    def stand_in(merge_commits: bool = False, human: bool = False) -> None:
        monkeypatch.setattr(local_git, "branch_base", lambda base: "base")
        monkeypatch.setattr(local_git, "has_merge_commits", lambda base: merge_commits)
        monkeypatch.setattr(review_state, "human_reviewed", lambda repo, number: human)
    return stand_in


def test_bot_reviews_only_allow_rewriting(branch_with) -> None:
    branch_with()
    assert review_state.commit_mode(PULL) == "rewrite"


def test_a_human_review_means_new_commits(branch_with) -> None:
    branch_with(human=True)
    assert review_state.commit_mode(PULL) == "new-commit"


def test_merge_commits_on_the_branch_mean_new_commits(branch_with) -> None:
    branch_with(merge_commits=True)
    assert review_state.commit_mode(PULL) == "new-commit"


def test_repositories_without_rebase_merges_get_new_commits(branch_with) -> None:
    branch_with()
    assert review_state.commit_mode({**PULL, "rebase_merge_allowed": False}) == "new-commit"


@pytest.fixture
def round_with(monkeypatch: pytest.MonkeyPatch, github_with):
    requests = []

    def stand_in(reviews=(), threads=(), new_comments=0, local_head="abc", dirty=False) -> list:
        github_with(reviews, threads)
        monkeypatch.setattr(github, "pull_request", lambda number: PULL)
        monkeypatch.setattr(github, "current_head", lambda repo, number: "abc")
        monkeypatch.setattr(github, "request_copilot_review", lambda number: requests.append(number))
        monkeypatch.setattr(github, "review_comment_count", lambda repo, number, review_id: new_comments)
        monkeypatch.setattr(local_git, "head", lambda: local_head)
        monkeypatch.setattr(local_git, "is_dirty", lambda: dirty)
        monkeypatch.setattr(review_state, "commit_mode", lambda pull: "rewrite")
        monkeypatch.setattr(pr_issue, "pr_issue", lambda pull: {"number": 1, "title": "Issue"})
        monkeypatch.setattr(review_state.time, "sleep", lambda seconds: None)
        return requests
    return stand_in


def test_a_round_with_no_review_times_out_after_requesting_one(round_with) -> None:
    requests = round_with()
    assert review_state.next_round(1, timeout=0)["state"] == "timed_out"
    assert requests == [1]


def test_an_existing_review_is_not_requested_again(round_with) -> None:
    requests = round_with(reviews=[review(BOT)])
    review_state.next_round(1, timeout=0)
    assert requests == []


def test_a_stale_local_head_needs_syncing(round_with) -> None:
    round_with(reviews=[review(BOT)], local_head="old")
    assert review_state.next_round(1, timeout=0)["state"] == "sync_needed"


def test_a_dirty_tree_stops_the_round(round_with) -> None:
    round_with(reviews=[review(BOT)], dirty=True)
    assert review_state.next_round(1, timeout=0)["state"] == "dirty_worktree"


def test_a_review_without_comments_is_clean(round_with) -> None:
    round_with(reviews=[review(BOT)], threads=[PERSON_THREAD])
    outcome = review_state.next_round(1, timeout=0)
    assert outcome["state"] == "clean"
    assert outcome["human_threads"] == ["thread-url"]


def test_open_copilot_threads_are_addressed_with_the_issue_and_mode(round_with) -> None:
    round_with(reviews=[review(BOT)], threads=[COPILOT_THREAD, thread(github.COPILOT_GRAPHQL_LOGIN, "Bot", resolved=True)],
               new_comments=1)
    outcome = review_state.next_round(1, timeout=0)
    assert outcome["state"] == "address"
    assert outcome["commit_mode"] == "rewrite"
    assert outcome["issue"] == {"number": 1, "title": "Issue"}
    assert [open_thread["id"] for open_thread in outcome["copilot_threads"]] == ["T"]


def test_a_reviewed_head_with_no_open_threads_is_ready(round_with) -> None:
    round_with(reviews=[review(BOT)], threads=[thread(github.COPILOT_GRAPHQL_LOGIN, "Bot", resolved=True)])
    assert review_state.head_status(1) == {"head": "abc", "head_reviewed": True, "open_threads": 0, "ready": True}


def test_a_head_pushed_after_the_last_review_is_not_ready(round_with) -> None:
    round_with(reviews=[review(BOT, commit="older")])
    status = review_state.head_status(1)
    assert status["head_reviewed"] is False
    assert status["ready"] is False


def test_open_threads_of_any_author_block_readiness(round_with) -> None:
    round_with(reviews=[review(BOT)], threads=[COPILOT_THREAD, PERSON_THREAD])
    status = review_state.head_status(1)
    assert status["open_threads"] == 2
    assert status["ready"] is False
