"""Looks up a repository's default branch and the pull requests of a branch through the GitHub CLI."""

import json
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from cli_tools import gh as gh_cli


@dataclass(frozen=True)
class PullRequest:
    number: int
    state: str
    head: str
    merged_at: str | None


class GitHubPullRequests:
    def __init__(self, directory: Path) -> None:
        self.directory = directory

    def default_branch(self) -> str:
        return self.gh("repo", "view", "--json", "defaultBranchRef", "--jq", ".defaultBranchRef.name")

    def for_branch(self, branch: str) -> list[PullRequest]:
        json_fields = "number,state,headRefOid,mergedAt"
        listing = self.gh("pr", "list", "--head", branch, "--state", "all", "--limit", "100", "--json", json_fields)
        return [PullRequest(pull["number"], pull["state"], pull["headRefOid"], pull["mergedAt"])
                for pull in json.loads(listing)]

    def gh(self, *arguments: str) -> str:
        return gh_cli.read(*arguments, cwd=self.directory)
