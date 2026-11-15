"""PreToolUse hook that blocks pull request creation until the current commit has passed the pre-pr standards review."""

import json
import re
import subprocess
import sys

REVIEW_MARKER = "coding-standards-reviewed"
GH_PR_CREATE = re.compile(r"\bgh\s+pr\s+create\b")
BLOCKED_EXIT_CODE = 2

BLOCK_MESSAGE = """\
Standards review required before creating a pull request.
Run the coding-standards:pre-pr skill on this branch first. Resolve its
findings (or get the user's decision on them), commit, then create the PR
again. The skill records the reviewed commit, which unblocks PR creation."""


def main() -> None:
    event = json.load(sys.stdin)
    if is_pr_creation(event) and not is_reviewed(event.get("cwd", ".")):
        block()


def is_pr_creation(event: dict) -> bool:
    return is_gh_pr_create(event) or is_mcp_pr_create(event)


def is_gh_pr_create(event: dict) -> bool:
    command = event.get("tool_input", {}).get("command", "")
    return event.get("tool_name") == "Bash" and bool(GH_PR_CREATE.search(join_line_continuations(command)))


def join_line_continuations(command: str) -> str:
    return command.replace("\\\n", "")


def is_mcp_pr_create(event: dict) -> bool:
    tool_name = event.get("tool_name", "")
    return tool_name.startswith("mcp__") and "create_pull_request" in tool_name


def is_reviewed(repo_dir: str) -> bool:
    head = git(repo_dir, "rev-parse", "HEAD")
    if head is None:
        return True
    return read_reviewed_commit(repo_dir) == head


def read_reviewed_commit(repo_dir: str) -> str | None:
    marker_path = git(repo_dir, "rev-parse", "--path-format=absolute", "--git-path", REVIEW_MARKER)
    try:
        with open(marker_path) as marker:
            return marker.read().strip()
    except (OSError, TypeError):
        return None


def git(repo_dir: str, *args: str) -> str | None:
    result = subprocess.run(["git", "-C", repo_dir, *args], capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else None


def block() -> None:
    print(BLOCK_MESSAGE, file=sys.stderr)
    sys.exit(BLOCKED_EXIT_CODE)


if __name__ == "__main__":
    main()
