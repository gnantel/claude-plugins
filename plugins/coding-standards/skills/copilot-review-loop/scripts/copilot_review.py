"""Command-line helper for the Copilot review loop: waits for Copilot's review of a pull request's head commit, lists its open threads, and replies to or resolves them through the gh CLI."""

import argparse
import json
import subprocess
import sys
import time

COPILOT_REST_LOGIN = "copilot-pull-request-reviewer[bot]"
COPILOT_GRAPHQL_LOGIN = "copilot-pull-request-reviewer"
POLL_SECONDS = 30
TIMED_OUT_EXIT_CODE = 3

THREADS_QUERY = """
query($owner: String!, $name: String!, $number: Int!, $after: String) {
  repository(owner: $owner, name: $name) {
    pullRequest(number: $number) {
      reviewThreads(first: 100, after: $after) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id isResolved isOutdated path line
          comments(first: 20) { nodes { author { login } body url } }
        }
      }
    }
  }
}
"""

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


def main() -> None:
    args = parse_arguments()
    args.command(args)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(required=True)
    add_wait_command(commands)
    add_threads_command(commands)
    add_reply_command(commands)
    add_resolve_command(commands)
    return parser.parse_args()


def add_wait_command(commands) -> None:
    wait = commands.add_parser("wait", help="Wait for Copilot's review of a commit.")
    add_pull_request_arguments(wait)
    wait.add_argument("commit", help="Full SHA of the PR head commit to wait for.")
    wait.add_argument("--timeout", type=int, default=900, help="Seconds to wait (default 900).")
    wait.set_defaults(command=wait_for_review)


def add_threads_command(commands) -> None:
    threads = commands.add_parser("threads", help="List unresolved review threads.")
    add_pull_request_arguments(threads)
    threads.set_defaults(command=print_open_threads)


def add_reply_command(commands) -> None:
    reply = commands.add_parser("reply", help="Reply to a review thread.")
    reply.add_argument("thread", help="Review thread node ID.")
    reply.add_argument("body", help="Reply text (Markdown).")
    reply.set_defaults(command=reply_to_thread)


def add_resolve_command(commands) -> None:
    resolve = commands.add_parser("resolve", help="Resolve a review thread.")
    resolve.add_argument("thread", help="Review thread node ID.")
    resolve.set_defaults(command=resolve_thread)


def add_pull_request_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("repo", help="Repository as owner/name.")
    parser.add_argument("number", type=int, help="Pull request number.")


def wait_for_review(args: argparse.Namespace) -> None:
    deadline = time.monotonic() + args.timeout
    while time.monotonic() < deadline:
        review = find_copilot_review(args.repo, args.number, args.commit)
        if review is not None:
            print_json(summarize_review(args.repo, args.number, review))
            return
        time.sleep(POLL_SECONDS)
    print_json({"status": "timed_out", "commit": args.commit})
    sys.exit(TIMED_OUT_EXIT_CODE)


def find_copilot_review(repo: str, number: int, commit: str) -> dict | None:
    reviews = gh_json("api", "--paginate", "--slurp", f"repos/{repo}/pulls/{number}/reviews")
    matching = [review for page in reviews for review in page if is_copilot_review_of(review, commit)]
    return matching[-1] if matching else None


def is_copilot_review_of(review: dict, commit: str) -> bool:
    return review["user"]["login"] == COPILOT_REST_LOGIN and review["commit_id"] == commit


def summarize_review(repo: str, number: int, review: dict) -> dict:
    comments = gh_json("api", f"repos/{repo}/pulls/{number}/reviews/{review['id']}/comments")
    return {
        "status": "reviewed",
        "review_id": review["id"],
        "commit": review["commit_id"],
        "new_comments": len(comments),
        "url": review["html_url"],
    }


def print_open_threads(args: argparse.Namespace) -> None:
    threads = fetch_threads(args.repo, args.number)
    print_json([describe_thread(thread) for thread in threads if not thread["isResolved"]])


def fetch_threads(repo: str, number: int) -> list[dict]:
    threads, cursor = [], None
    while True:
        page = fetch_thread_page(repo, number, cursor)
        threads.extend(page["nodes"])
        if not page["pageInfo"]["hasNextPage"]:
            return threads
        cursor = page["pageInfo"]["endCursor"]


def fetch_thread_page(repo: str, number: int, cursor: str | None) -> dict:
    owner, name = repo.split("/")
    arguments = ["api", "graphql", "-f", f"query={THREADS_QUERY}",
                 "-f", f"owner={owner}", "-f", f"name={name}", "-F", f"number={number}"]
    if cursor is not None:
        arguments += ["-f", f"after={cursor}"]
    response = gh_json(*arguments)
    return response["data"]["repository"]["pullRequest"]["reviewThreads"]


def describe_thread(thread: dict) -> dict:
    comments = thread["comments"]["nodes"]
    return {
        "id": thread["id"],
        "from_copilot": is_started_by_copilot(comments),
        "outdated": thread["isOutdated"],
        "path": thread["path"],
        "line": thread["line"],
        "comments": [{"author": login_of(comment), "body": comment["body"]} for comment in comments],
        "url": comments[0]["url"] if comments else None,
    }


def is_started_by_copilot(comments: list[dict]) -> bool:
    return bool(comments) and login_of(comments[0]) == COPILOT_GRAPHQL_LOGIN


def login_of(comment: dict) -> str | None:
    author = comment.get("author")
    return author["login"] if author else None


def reply_to_thread(args: argparse.Namespace) -> None:
    response = gh_json("api", "graphql", "-f", f"query={REPLY_MUTATION}",
                       "-f", f"thread={args.thread}", "-f", f"body={args.body}")
    print_json(response["data"]["addPullRequestReviewThreadReply"]["comment"])


def resolve_thread(args: argparse.Namespace) -> None:
    response = gh_json("api", "graphql", "-f", f"query={RESOLVE_MUTATION}", "-f", f"thread={args.thread}")
    print_json(response["data"]["resolveReviewThread"]["thread"])


def gh_json(*args: str):
    result = subprocess.run(["gh", *args], capture_output=True, text=True)
    if result.returncode != 0:
        sys.exit(f"gh {' '.join(args[:2])} failed: {result.stderr.strip()}")
    return json.loads(result.stdout)


def print_json(value) -> None:
    print(json.dumps(value, indent=2))


if __name__ == "__main__":
    main()
