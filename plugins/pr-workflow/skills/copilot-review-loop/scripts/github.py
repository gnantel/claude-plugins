"""GitHub access for the Copilot review loop through the gh CLI: pull request state, reviews, review threads, and thread replies."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from cli_tools import gh

COPILOT_REST_LOGIN = "copilot-pull-request-reviewer[bot]"
COPILOT_GRAPHQL_LOGIN = "copilot-pull-request-reviewer"

COMMENT_FIELDS = "pageInfo { hasNextPage endCursor } nodes { author { login __typename } body url }"

THREADS_QUERY = """
query($owner: String!, $name: String!, $number: Int!, $after: String) {
  repository(owner: $owner, name: $name) {
    pullRequest(number: $number) {
      reviewThreads(first: 100, after: $after) {
        pageInfo { hasNextPage endCursor }
        nodes { id isResolved isOutdated path line comments(first: 100) { %s } }
      }
    }
  }
}
""" % COMMENT_FIELDS

THREAD_COMMENTS_QUERY = """
query($thread: ID!, $after: String) {
  node(id: $thread) {
    ... on PullRequestReviewThread { comments(first: 100, after: $after) { %s } }
  }
}
""" % COMMENT_FIELDS

REPLY_MUTATION = """
mutation($thread: ID!, $body: String!) {
  addPullRequestReviewThreadReply(input: {pullRequestReviewThreadId: $thread, body: $body}) {
    comment { url }
  }
}
"""

RESOLVE_MUTATION = """
mutation($thread: ID!) {
  resolveReviewThread(input: {threadId: $thread}) { thread { isResolved } }
}
"""


def pull_request(number: int | None) -> dict:
    selector = [] if number is None else [str(number)]
    pull = gh.read_json("pr", "view", *selector, "--json", "number,headRefOid,headRefName,baseRefName,isCrossRepository")
    repository = gh.read_json("repo", "view", "--json", "nameWithOwner")
    return {
        "repo": repository["nameWithOwner"],
        "number": pull["number"],
        "head": pull["headRefOid"],
        "head_ref": pull["headRefName"],
        "base": pull["baseRefName"],
        "from_fork": pull["isCrossRepository"],
    }


def current_head(repo: str, number: int) -> str:
    return gh.read_json("api", f"repos/{repo}/pulls/{number}")["head"]["sha"]


def reviews(repo: str, number: int) -> list[dict]:
    return gh.paginate(f"repos/{repo}/pulls/{number}/reviews")


def review_comment_count(repo: str, number: int, review_id: int) -> int:
    return len(gh.paginate(f"repos/{repo}/pulls/{number}/reviews/{review_id}/comments"))


def conversation_comments(repo: str, number: int) -> list[dict]:
    return gh.paginate(f"repos/{repo}/issues/{number}/comments")


def request_copilot_review(number: int) -> None:
    gh.run("pr", "edit", str(number), "--add-reviewer", "@copilot")


def review_threads(repo: str, number: int) -> list[dict]:
    threads, cursor = [], None
    while True:
        page = gh.graphql(THREADS_QUERY, owner=repo.split("/")[0], name=repo.split("/")[1],
                       number=number, after=cursor)["repository"]["pullRequest"]["reviewThreads"]
        threads.extend(page["nodes"])
        if not page["pageInfo"]["hasNextPage"]:
            return [with_all_comments(thread) for thread in threads]
        cursor = page["pageInfo"]["endCursor"]


def with_all_comments(thread: dict) -> dict:
    comments = thread["comments"]
    while comments["pageInfo"]["hasNextPage"]:
        page = gh.graphql(THREAD_COMMENTS_QUERY, thread=thread["id"],
                       after=comments["pageInfo"]["endCursor"])["node"]["comments"]
        comments = {"pageInfo": page["pageInfo"], "nodes": comments["nodes"] + page["nodes"]}
    return {**thread, "comments": comments}


def reply(thread_id: str, body: str) -> str:
    response = gh.graphql(REPLY_MUTATION, thread=thread_id, body=body)
    return response["addPullRequestReviewThreadReply"]["comment"]["url"]


def resolve(thread_id: str) -> bool:
    return gh.graphql(RESOLVE_MUTATION, thread=thread_id)["resolveReviewThread"]["thread"]["isResolved"]
