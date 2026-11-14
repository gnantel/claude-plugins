"""Works out where a pull request stands in the Copilot review loop: waits for Copilot's review of the current head, then reports whether the loop is done, blocked, or has threads to address and how to commit the fixes."""

import time

import github
import local_git

POLL_SECONDS = 30
DECISIVE_REVIEW_STATES = {"APPROVED", "CHANGES_REQUESTED", "DISMISSED"}


def next_round(number: int | None, timeout: int) -> dict:
    pull = github.pull_request(number)
    review, head = wait_for_review_of_current_head(pull, timeout)
    if review is None:
        return {"state": "timed_out", "head": head}
    if local_git.head() != head:
        return {"state": "sync_needed", "head": head, "local_head": local_git.head()}
    if local_git.is_dirty():
        return {"state": "dirty_worktree", "head": head}
    return review_outcome(pull, review, head)


def wait_for_review_of_current_head(pull: dict, timeout: int) -> tuple[dict | None, str]:
    head = github.current_head(pull["repo"], pull["number"])
    if copilot_review_of(pull, head) is None:
        github.request_copilot_review(pull["number"])
    return poll_for_review(pull, timeout)


def poll_for_review(pull: dict, timeout: int) -> tuple[dict | None, str]:
    deadline = time.monotonic() + timeout
    while True:
        head = github.current_head(pull["repo"], pull["number"])
        review = copilot_review_of(pull, head)
        if review is not None or time.monotonic() >= deadline:
            return review, head
        time.sleep(POLL_SECONDS)


def copilot_review_of(pull: dict, head: str) -> dict | None:
    matching = [review for review in github.reviews(pull["repo"], pull["number"])
                if review["user"]["login"] == github.COPILOT_REST_LOGIN and review["commit_id"] == head]
    return matching[-1] if matching else None


def review_outcome(pull: dict, review: dict, head: str) -> dict:
    threads = [thread for thread in github.review_threads(pull["repo"], pull["number"])
               if not thread["isResolved"]]
    copilot_threads = [describe(thread) for thread in threads if is_started_by_copilot(thread)]
    new_comments = github.review_comment_count(pull["repo"], pull["number"], review["id"])
    outcome = {
        "head": head,
        "review_url": review["html_url"],
        "human_threads": [thread_url(thread) for thread in threads if is_started_by_person(thread)],
    }
    if new_comments == 0 and not copilot_threads:
        return {"state": "clean", **outcome}
    return {"state": "address", "commit_mode": commit_mode(pull), "copilot_threads": copilot_threads, **outcome}


def commit_mode(pull: dict) -> str:
    if not pull["rebase_merge_allowed"] or local_git.has_merge_commits(local_git.branch_base(pull["base"])):
        return "new-commit"
    return "new-commit" if human_reviewed(pull["repo"], pull["number"]) else "rewrite"


def human_reviewed(repo: str, number: int) -> bool:
    return (
        any(is_decisive_or_written_by_person(review) for review in github.reviews(repo, number))
        or any(is_started_by_person(thread) for thread in github.review_threads(repo, number))
        or any(comment["user"]["type"] == "User" for comment in github.conversation_comments(repo, number))
    )


def is_decisive_or_written_by_person(review: dict) -> bool:
    by_person = review["user"]["type"] == "User"
    return by_person and (review["state"] in DECISIVE_REVIEW_STATES or bool(review["body"].strip()))


def is_started_by_copilot(thread: dict) -> bool:
    return first_author(thread).get("login") == github.COPILOT_GRAPHQL_LOGIN


def is_started_by_person(thread: dict) -> bool:
    return first_author(thread).get("__typename") == "User"


def first_author(thread: dict) -> dict:
    comments = thread["comments"]["nodes"]
    return (comments[0].get("author") or {}) if comments else {}


def describe(thread: dict) -> dict:
    return {
        "id": thread["id"],
        "path": thread["path"],
        "line": thread["line"],
        "outdated": thread["isOutdated"],
        "url": thread_url(thread),
        "comments": [{"author": (comment.get("author") or {}).get("login"), "body": comment["body"]}
                     for comment in thread["comments"]["nodes"]],
    }


def thread_url(thread: dict) -> str | None:
    comments = thread["comments"]["nodes"]
    return comments[0]["url"] if comments else None

