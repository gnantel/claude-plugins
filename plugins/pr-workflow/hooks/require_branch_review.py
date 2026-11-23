"""PreToolUse hook that blocks pull request creation until the current commit has passed the branch review.

It is a guard rail against forgetting the review, not a security boundary: contrived commands are out of scope."""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cli_tools import git as git_cli
from cli_tools.command import CommandFailed

REVIEW_MARKER = "pr-workflow-reviewed"
COMMAND_START = r"(?:^|[;&|()`\n]|\{(?=\s))\s*(?:(?:then|do|else|elif|if|while|until|!)\s+)*"
COMMAND_PREFIXES = r"(?:(?:command|env|exec|sudo|time|nohup|--|\"\"|-[uCS]\s+\S+|-(?![vV]\b)\w+)\s+|\w+=\S*\s+|\d*[<>]{1,2}&?\s*\S+\s+)*"
GH_PR_CREATE = re.compile(COMMAND_START + COMMAND_PREFIXES + r"gh\s+pr\s+create\b")
HEREDOC = r"(?<!<)<<(?!<)(?P<dash>-)?\s*(?P<quote>[\"']?)(?P<delimiter>[^\s'\"<>|&;()]+)(?P=quote)(?P<tail>[^\n]*)\n(?P<body>.*?)^(?(dash)\t*)(?P=delimiter)$"
SINGLE_QUOTED = r"'[^']*'"
DOUBLE_QUOTED = r"(?P<double>\"(?:\\.|\$\([^)]*\)|[^\"\\])*\")"
ESCAPED_CHARACTER = r"\\."
COMMENT = r"(?<![^\s;&|(])#[^\n]*"
LITERALS = re.compile("|".join([HEREDOC, COMMENT, SINGLE_QUOTED, DOUBLE_QUOTED, ESCAPED_CHARACTER]), re.DOTALL | re.MULTILINE)
SUBSTITUTION = re.compile(r"(?<!\\)\$\(([^)]*)\)|`([^`]*)`")
BLOCKED_EXIT_CODE = 2

BLOCK_MESSAGE = """\
Branch review required before creating a pull request.
Run the pr-workflow:review-branch skill on this branch first (or
pr-workflow:submit-pr, which runs it and then creates the PR). Resolve the
findings (or get the user's decision on them) and commit. The review
records the reviewed commit, which unblocks PR creation."""


def main() -> None:
    event = json.load(sys.stdin)
    if is_pr_creation(event) and not is_reviewed(event.get("cwd", ".")):
        block()


def is_pr_creation(event: dict) -> bool:
    return is_gh_pr_create(event) or is_mcp_pr_create(event)


def is_gh_pr_create(event: dict) -> bool:
    command = event.get("tool_input", {}).get("command", "")
    return event.get("tool_name") == "Bash" and bool(GH_PR_CREATE.search(executable_text(command)))


def executable_text(command: str) -> str:
    return strip_literals(join_line_continuations(command))


def join_line_continuations(command: str) -> str:
    return command.replace("\\\n", "")


def strip_literals(command: str) -> str:
    stripped = LITERALS.sub(keep_executable_part, command)
    return command if stripped == command else strip_literals(stripped)


def keep_executable_part(literal: re.Match) -> str:
    if literal["delimiter"]:
        return "\n" + ("" if literal["quote"] else substitutions_as_commands(literal["body"])) + "\n" + literal["tail"]
    if literal["double"]:
        return '""' + substitutions_as_commands(literal["double"])
    return '""'


def substitutions_as_commands(text: str) -> str:
    commands = [dollar_form or backtick_form for dollar_form, backtick_form in SUBSTITUTION.findall(text)]
    return "".join(f";{command};" for command in commands)


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
    try:
        return git_cli.read(*args, cwd=repo_dir)
    except CommandFailed:
        return None


def block() -> None:
    print(BLOCK_MESSAGE, file=sys.stderr)
    sys.exit(BLOCKED_EXIT_CODE)


if __name__ == "__main__":
    main()
