"""Command-line entry point for the Copilot review loop: next-round reports where the pull request stands, status says whether its head is reviewed with no open threads, push-round commits and pushes fixes, and reply and resolve answer review threads."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import github
import local_git
import review_state
import round_push
from cli_tools.command import CommandFailed

DEFAULT_TIMEOUT_SECONDS = 900


def main() -> None:
    args = parse_arguments()
    try:
        print(json.dumps(args.command(args), indent=2))
    except CommandFailed as failure:
        sys.exit(str(failure))


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(required=True)
    add_next_round_command(commands)
    add_status_command(commands)
    add_push_round_command(commands)
    add_thread_commands(commands)
    return parser.parse_args()


def add_next_round_command(commands) -> None:
    command = commands.add_parser("next-round", help="Wait for Copilot's review of the PR head and report the state.")
    command.add_argument("pr", nargs="?", type=int, help="PR number (default: the current branch's PR).")
    command.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SECONDS,
                         help="Seconds to wait for Copilot's review after requesting it.")
    command.set_defaults(command=lambda args: review_state.next_round(args.pr, args.timeout))


def add_status_command(commands) -> None:
    command = commands.add_parser("status", help="Report at once whether Copilot reviewed the PR head and how many threads are open.")
    command.add_argument("pr", nargs="?", type=int, help="PR number (default: the current branch's PR).")
    command.set_defaults(command=lambda args: review_state.head_status(args.pr))


def add_push_round_command(commands) -> None:
    command = commands.add_parser("push-round", help="Commit and push this round's fixes in the right mode.")
    command.add_argument("round", type=int, help="Round number, used in the commit message.")
    command.add_argument("pr", nargs="?", type=int, help="PR number (default: the current branch's PR).")
    command.add_argument("--message-file", type=Path, help="New message for the branch's single commit, when a fix changes what it does.")
    command.set_defaults(command=lambda args: round_push.push_round(args.pr, args.round, read_message_file(args.message_file)))


def read_message_file(path: Path | None) -> str | None:
    if path and local_git.is_inside_worktree(path):
        sys.exit("--message-file must be outside the working tree, or push-round would commit it.")
    return path.read_text().strip() if path else None


def add_thread_commands(commands) -> None:
    reply = commands.add_parser("reply", help="Reply to a review thread.")
    reply.add_argument("thread", help="Review thread node ID.")
    reply.add_argument("body", help="Reply text (Markdown).")
    reply.set_defaults(command=lambda args: {"url": github.reply(args.thread, args.body)})
    resolve = commands.add_parser("resolve", help="Resolve a review thread.")
    resolve.add_argument("thread", help="Review thread node ID.")
    resolve.set_defaults(command=lambda args: {"resolved": github.resolve(args.thread)})


if __name__ == "__main__":
    main()
