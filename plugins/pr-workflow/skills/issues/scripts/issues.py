"""Command-line helper for issue-first work: shows an issue with all its comments and sub-issues, finds the issue a branch implements, creates issues, links sub-issues, and renders the brief for a child session. Requires gh 2.104 or later for sub-issue support."""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

BRANCH_ISSUE_NUMBER = re.compile(r"(?:^|/)(\d+)-[^/]*$")
TRUSTED_ASSOCIATIONS = {"OWNER", "MEMBER", "COLLABORATOR"}
BRIEF_TEMPLATE = Path(__file__).resolve().parent.parent / "brief-template.md"
ISSUE_FIELDS = "number,title,state,url,body,parent,subIssues"


def main() -> None:
    args = parse_arguments()
    output = args.command(args)
    print(output if isinstance(output, str) else json.dumps(output, indent=2))


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(required=True)
    show = commands.add_parser("show", help="Show an issue, all its comments, its parent and sub-issues.")
    show.add_argument("number", type=int)
    show.set_defaults(command=lambda args: issue(args.number))
    branch = commands.add_parser("for-branch", help="Find the issue the current branch implements.")
    branch.set_defaults(command=lambda args: issue_for_branch())
    create = commands.add_parser("create", help="Create an issue, optionally as a sub-issue.")
    create.add_argument("--title", required=True)
    create.add_argument("--body-file", required=True)
    create.add_argument("--parent", type=int, help="Parent issue number.")
    create.add_argument("--label", action="append", default=[])
    create.set_defaults(command=lambda args: create_issue(args.title, args.body_file, args.parent, args.label))
    link = commands.add_parser("link", help="Make an existing issue a sub-issue of another.")
    link.add_argument("parent", type=int)
    link.add_argument("child", type=int)
    link.set_defaults(command=lambda args: link_sub_issue(args.parent, args.child))
    brief = commands.add_parser("brief", help="Print the brief for a child session implementing an issue.")
    brief.add_argument("number", type=int)
    brief.set_defaults(command=lambda args: brief_for_issue(args.number))
    return parser.parse_args()


def issue(number: int) -> dict:
    found = gh_json("issue", "view", str(number), "--json", ISSUE_FIELDS)
    sub_issues = [{"number": sub["number"], "title": sub["title"], "state": sub["state"]}
                  for sub in (found.get("subIssues") or {}).get("nodes", [])]
    return {
        "number": found["number"],
        "title": found["title"],
        "state": found["state"],
        "url": found["url"],
        "is_leaf": not sub_issues,
        "parent": (found.get("parent") or {}).get("number"),
        "sub_issues": sub_issues,
        "body": found["body"],
        "comments": all_comments(number),
    }


def all_comments(number: int) -> list[dict]:
    pages = gh_json("api", "--paginate", "--slurp", f"repos/{repository()}/issues/{number}/comments")
    return [{"author": (comment.get("user") or {}).get("login"),
             "trusted": comment.get("author_association") in TRUSTED_ASSOCIATIONS,
             "body": comment["body"]}
            for page in pages for comment in page]


def issue_for_branch() -> dict:
    pull = gh_json("pr", "view", "--json", "closingIssuesReferences,baseRefName", allow_failure=True)
    references = (pull or {}).get("closingIssuesReferences", [])
    if len(references) > 1:
        return {"error": "The PR closes several issues; it must close exactly one leaf issue."}
    if references and reference_repository(references[0]) != repository():
        return {"error": f"The PR closes an issue in another repository ({reference_repository(references[0])})."}
    if references:
        return issue(references[0]["number"])
    return issue_from_branch_name(stacked=is_stacked(pull))


def issue_from_branch_name(stacked: bool) -> dict:
    branch_number = BRANCH_ISSUE_NUMBER.search(git("branch", "--show-current"))
    if branch_number is None:
        return {"error": "No issue found: the branch has no PR closing an issue, and the last segment of its name doesn't start with one."}
    found = issue(int(branch_number.group(1)))
    return {**found, "stacked": True} if stacked else found


def is_stacked(pull: dict | None) -> bool:
    return bool(pull) and pull.get("baseRefName") != default_branch()


def reference_repository(reference: dict) -> str:
    return f"{reference['repository']['owner']['login']}/{reference['repository']['name']}"


def create_issue(title: str, body_file: str, parent: int | None, labels: list[str]) -> dict:
    arguments = ["issue", "create", "--title", title, "--body-file", body_file]
    if parent is not None:
        arguments += ["--parent", str(parent)]
    for label in labels:
        arguments += ["--label", label]
    url = gh(*arguments).strip()
    return {"number": int(url.rsplit("/", 1)[1]), "url": url, "parent": parent}


def link_sub_issue(parent: int, child: int) -> dict:
    gh("issue", "edit", str(parent), "--add-sub-issue", str(child))
    return {"parent": parent, "child": child}


def brief_for_issue(number: int) -> str:
    issue_summary = gh_json("issue", "view", str(number), "--json", "number,title")
    return render_brief(BRIEF_TEMPLATE.read_text(), issue_summary["number"], issue_summary["title"], repository())


def render_brief(template: str, number: int, title: str, repository_name: str) -> str:
    return template.format(number=number, title=title, repository=repository_name)


def repository() -> str:
    return gh_json("repo", "view", "--json", "nameWithOwner")["nameWithOwner"]


def default_branch() -> str:
    return gh_json("repo", "view", "--json", "defaultBranchRef")["defaultBranchRef"]["name"]


def gh_json(*arguments: str, allow_failure: bool = False):
    output = gh(*arguments, allow_failure=allow_failure)
    return json.loads(output) if output else None


def gh(*arguments: str, allow_failure: bool = False) -> str:
    result = subprocess.run(["gh", *arguments], capture_output=True, text=True)
    if result.returncode != 0:
        if allow_failure:
            return ""
        sys.exit(f"gh {' '.join(arguments[:2])} failed: {result.stderr.strip()}")
    return result.stdout


def git(*arguments: str) -> str:
    return subprocess.run(["git", *arguments], capture_output=True, text=True).stdout.strip()


if __name__ == "__main__":
    main()
