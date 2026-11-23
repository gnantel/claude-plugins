"""Runs one external command and reports every failure the same way: as a CommandFailed carrying the tool's own error text."""

import subprocess
from pathlib import Path


class CommandFailed(Exception):
    def __init__(self, summary: str, stderr: str) -> None:
        super().__init__(f"{summary} failed: {stderr}")
        self.summary = summary
        self.stderr = stderr


def run_command(executable: str, arguments: tuple[str, ...], *, summary_words: int, cwd: Path | str | None = None,
                env: dict[str, str] | None = None, stdin: str | None = None) -> str:
    summary = " ".join([executable, *arguments[:summary_words]])
    try:
        completed = subprocess.run([executable, *arguments], cwd=cwd, env=env, input=stdin,
                                   capture_output=True, text=True)
    except OSError as failure:
        raise CommandFailed(summary, str(failure)) from failure
    if completed.returncode != 0:
        raise CommandFailed(summary, completed.stderr.strip())
    return completed.stdout
