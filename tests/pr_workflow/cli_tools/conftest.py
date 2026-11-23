"""Fixtures for the shared wrapper tests: a stand-in gh executable on PATH that records its arguments and prints a canned reply."""

import json
import os
import stat
from pathlib import Path

import pytest

FAKE_GH = """#!/usr/bin/env python3
import json, os, sys
with open(os.environ["FAKE_GH_LOG"], "w") as log:
    json.dump({"arguments": sys.argv[1:], "cwd": os.getcwd()}, log)
sys.stderr.write(os.environ.get("FAKE_GH_STDERR", ""))
sys.stdout.write(os.environ.get("FAKE_GH_STDOUT", ""))
sys.exit(int(os.environ.get("FAKE_GH_EXIT", "0")))
"""


class FakeGh:
    def __init__(self, directory: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        self.log = directory / "gh-call.json"
        executable = directory / "gh"
        executable.write_text(FAKE_GH)
        executable.chmod(executable.stat().st_mode | stat.S_IEXEC)
        monkeypatch.setenv("PATH", f"{directory}{os.pathsep}{os.environ['PATH']}")
        monkeypatch.setenv("FAKE_GH_LOG", str(self.log))
        self.monkeypatch = monkeypatch

    def replies(self, stdout: str = "", stderr: str = "", exit_code: int = 0) -> None:
        self.monkeypatch.setenv("FAKE_GH_STDOUT", stdout)
        self.monkeypatch.setenv("FAKE_GH_STDERR", stderr)
        self.monkeypatch.setenv("FAKE_GH_EXIT", str(exit_code))

    def last_call(self) -> dict:
        return json.loads(self.log.read_text())


@pytest.fixture
def fake_gh(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> FakeGh:
    directory = tmp_path / "bin"
    directory.mkdir()
    return FakeGh(directory, monkeypatch)
