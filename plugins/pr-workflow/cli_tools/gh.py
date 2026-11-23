"""Runs the GitHub CLI and returns its output as text or JSON, including GraphQL with variables and paginated REST lists."""

import json
from pathlib import Path

from cli_tools.command import CommandFailed, run_command

SUMMARY_WORDS = 2


def run(*arguments: str, cwd: Path | str | None = None, allow_failure: bool = False) -> str:
    try:
        return run_command("gh", arguments, summary_words=SUMMARY_WORDS, cwd=cwd)
    except CommandFailed:
        if allow_failure:
            return ""
        raise


def read(*arguments: str, cwd: Path | str | None = None) -> str:
    return run(*arguments, cwd=cwd).strip()


def read_json(*arguments: str, cwd: Path | str | None = None, allow_failure: bool = False):
    output = run(*arguments, cwd=cwd, allow_failure=allow_failure)
    return json.loads(output) if output else None


def graphql(query: str, **variables) -> dict:
    arguments = ["api", "graphql", "-f", f"query={query}"]
    for name, value in variables.items():
        if value is not None:
            arguments += ["-F" if isinstance(value, int) else "-f", f"{name}={value}"]
    return read_json(*arguments)["data"]


def paginate(path: str) -> list[dict]:
    return [item for page in read_json("api", "--paginate", "--slurp", path) for item in page]
