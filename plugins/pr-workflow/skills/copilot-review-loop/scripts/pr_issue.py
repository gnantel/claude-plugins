"""Gives the review loop the leaf issue a pull request implements: its body and
the comments from trusted authors, which bound what review comments are in scope."""

import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from cli_tools import gh
from cli_tools.command import CommandFailed

ISSUES_HELPER = Path(__file__).resolve().parents[2] / "issues" / "scripts" / "issues.py"
BRANCH_ISSUE_NUMBER = re.compile(r"(?:^|/)(\d+)-[^/]*$")


def pr_issue(pull: dict) -> dict:
    number = issue_number(pull)
    if isinstance(number, str):
        return {"error": number}
    issue = run_helper("show", str(number))
    if "error" in issue:
        return {"error": issue["error"]}
    if not issue["is_leaf"]:
        return {"error": f"Issue #{number} has sub-issues; a PR must close one leaf issue, not a parent."}
    return {
        "number": issue["number"],
        "title": issue["title"],
        "is_leaf": issue["is_leaf"],
        "body": issue["body"],
        "trusted_comments": [comment["body"] for comment in issue["comments"] if comment["trusted"]],
    }


def issue_number(pull: dict) -> int | str:
    current = current_pull(pull)
    if isinstance(current, str):
        return current
    references = current["closingIssuesReferences"]
    if len(references) > 1:
        return f"PR #{pull['number']} closes several issues; it must close exactly one leaf issue."
    if references and reference_repository(references[0]) != pull["repo"]:
        return f"PR #{pull['number']} closes an issue in another repository."
    if references:
        return references[0]["number"]
    return stacked_branch_issue(pull, current)


def current_pull(pull: dict) -> dict | str:
    try:
        return gh.read_json("pr", "view", str(pull["number"]), "--repo", pull["repo"],
                            "--json", "closingIssuesReferences,baseRefName,headRefName")
    except CommandFailed as failure:
        return f"Couldn't read PR #{pull['number']}'s issue: {failure.stderr}"


def stacked_branch_issue(pull: dict, current: dict) -> int | str:
    default = default_branch(pull["repo"])
    if default is None:
        return f"Couldn't read {pull['repo']}'s default branch, so PR #{pull['number']}'s issue can't be verified."
    branch_number = BRANCH_ISSUE_NUMBER.search(current["headRefName"])
    if current["baseRefName"] == default or branch_number is None:
        return f"PR #{pull['number']} doesn't close an issue: add `Closes #<n>` to its description."
    return int(branch_number.group(1))


def reference_repository(reference: dict) -> str:
    return f"{reference['repository']['owner']['login']}/{reference['repository']['name']}"


def default_branch(repo: str) -> str | None:
    repository = gh.read_json("repo", "view", repo, "--json", "defaultBranchRef", allow_failure=True)
    return repository["defaultBranchRef"]["name"] if repository else None


def run_helper(*arguments: str) -> dict:
    helper_run = subprocess.run([sys.executable, "-B", str(ISSUES_HELPER), *arguments],
                                capture_output=True, text=True)
    if helper_run.returncode != 0:
        return {"error": f"Couldn't read the PR's issue: {helper_run.stderr.strip()}"}
    try:
        return json.loads(helper_run.stdout)
    except ValueError:
        return {"error": "Couldn't read the PR's issue: the issues helper printed no JSON."}
