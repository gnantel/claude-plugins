"""GitHub access for the Copilot review loop through the gh CLI: pull request state, reviews, review threads, and thread replies."""

import json
import subprocess
import sys

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
    pull = gh_json("pr", "view", *selector, "--json", "number,headRefOid,headRefName,baseRefName")
    repository = gh_json("repo", "view", "--json", "nameWithOwner,rebaseMergeAllowed")
    return {
        "repo": repository["nameWithOwner"],
        "number": pull["number"],
        "head": pull["headRefOid"],
        "head_ref": pull["headRefName"],
        "base": pull["baseRefName"],
        "rebase_merge_allowed": repository["rebaseMergeAllowed"],
    }


def current_head(repo: str, number: int) -> str:
    return gh_json("api", f"repos/{repo}/pulls/{number}")["head"]["sha"]


def reviews(repo: str, number: int) -> list[dict]:
    return paginated(f"repos/{repo}/pulls/{number}/reviews")


def review_comment_count(repo: str, number: int, review_id: int) -> int:
    return len(paginated(f"repos/{repo}/pulls/{number}/reviews/{review_id}/comments"))


def conversation_comments(repo: str, number: int) -> list[dict]:
    return paginated(f"repos/{repo}/issues/{number}/comments")


def request_copilot_review(number: int) -> None:
    gh_run("pr", "edit", str(number), "--add-reviewer", "@copilot")


def review_threads(repo: str, number: int) -> list[dict]:
    threads, cursor = [], None
    while True:
        page = graphql(THREADS_QUERY, owner=repo.split("/")[0], name=repo.split("/")[1],
                       number=number, after=cursor)["repository"]["pullRequest"]["reviewThreads"]
        threads.extend(page["nodes"])
        if not page["pageInfo"]["hasNextPage"]:
            return [with_all_comments(thread) for thread in threads]
        cursor = page["pageInfo"]["endCursor"]


def with_all_comments(thread: dict) -> dict:
    comments = thread["comments"]
    while comments["pageInfo"]["hasNextPage"]:
        page = graphql(THREAD_COMMENTS_QUERY, thread=thread["id"],
                       after=comments["pageInfo"]["endCursor"])["node"]["comments"]
        comments = {"pageInfo": page["pageInfo"], "nodes": comments["nodes"] + page["nodes"]}
    return {**thread, "comments": comments}


def reply(thread_id: str, body: str) -> str:
    response = graphql(REPLY_MUTATION, thread=thread_id, body=body)
    return response["addPullRequestReviewThreadReply"]["comment"]["url"]


def resolve(thread_id: str) -> bool:
    return graphql(RESOLVE_MUTATION, thread=thread_id)["resolveReviewThread"]["thread"]["isResolved"]


def paginated(path: str) -> list[dict]:
    return [item for page in gh_json("api", "--paginate", "--slurp", path) for item in page]


def graphql(query: str, **variables) -> dict:
    arguments = ["api", "graphql", "-f", f"query={query}"]
    for name, value in variables.items():
        if value is not None:
            arguments += ["-F" if isinstance(value, int) else "-f", f"{name}={value}"]
    return gh_json(*arguments)["data"]


def gh_json(*arguments: str):
    return json.loads(gh_run(*arguments))


def gh_run(*arguments: str) -> str:
    result = subprocess.run(["gh", *arguments], capture_output=True, text=True)
    if result.returncode != 0:
        sys.exit(f"gh {' '.join(arguments[:2])} failed: {result.stderr.strip()}")
    return result.stdout
