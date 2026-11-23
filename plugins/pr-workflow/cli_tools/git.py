"""Runs git in a given directory and returns its output; failures raise CommandFailed unless the caller allows them."""

from pathlib import Path

from cli_tools.command import CommandFailed, run_command

SUMMARY_WORDS = 1


def run(*arguments: str, cwd: Path | str | None = None, env: dict[str, str] | None = None,
        stdin: str | None = None, allow_failure: bool = False) -> str:
    try:
        return run_command("git", arguments, summary_words=SUMMARY_WORDS, cwd=cwd, env=env, stdin=stdin)
    except CommandFailed:
        if allow_failure:
            return ""
        raise


def read(*arguments: str, cwd: Path | str | None = None, env: dict[str, str] | None = None,
         allow_failure: bool = False) -> str:
    return run(*arguments, cwd=cwd, env=env, allow_failure=allow_failure).strip()


def succeeds(*arguments: str, cwd: Path | str | None = None, env: dict[str, str] | None = None) -> bool:
    try:
        run_command("git", arguments, summary_words=SUMMARY_WORDS, cwd=cwd, env=env)
    except CommandFailed:
        return False
    return True
