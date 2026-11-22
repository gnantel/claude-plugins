# Pull Request Standards

Rules for how work is split into issues and pull requests. Each rule has an
ID so reviews can cite it. The `issues` skill has the helper for creating,
showing and linking issues.

## PR1. One pull request, one leaf issue

Every PR implements and closes exactly one **leaf issue**: an issue with no
sub-issues. The issue is the PR's scope, written before the work, so the
diff can be checked against something the diff didn't shape.

**In scope:**
- Changes that serve the issue.
- Fixes to this PR's own changes within the issue's scope, whether a
  review found them or not.
- The minimum supporting changes the issue needs: a version bump,
  documentation of what this PR changes, a test for it.

**Out of scope:**
- New features, rules or requests that come up while the PR is open, even
  from the user, even when small and even when the branch is already
  checked out.
- Refactoring, renaming or cleaning up code the issue does not need
  ("while I'm here").
- Fixing unrelated bugs noticed in passing.
- Reformatting untouched code.

## PR2. Every change starts from an issue

Before writing code, find the change's issue or create one from the user's
request. Its body states:

```markdown
## Scope

Add the Spring Boot conventions plugin (rules SB1–SB6 and its reviewer).

## Out of scope

The Copilot review loop and G11 (separate issues).

## Done when

The plugin, its rules and reviewer exist, and the reviewer passes a sample
Spring repository.
```

- **Work that needs several PRs is a parent issue.** Split it into
  sub-issues, one per PR, before starting. Only leaves get PRs. Nesting
  depth is the hierarchy: a parent for the goal, leaves for the units of
  work.
- **Branch from the default branch**, named `<issue-id>-<description>`
  (`6-issue-linked-prs`).
- **The description of the PR includes `Closes #<n>`** for its one leaf
  issue.

## PR3. New work becomes a new issue

When out-of-scope work comes up (a new request from the user, a problem
noticed in passing, a follow-up), open a new issue for it, as a sub-issue
when it belongs to a larger goal. Don't add it to the branch that happens
to be checked out, unless the user explicitly asks for that.

- If the new work depends on an open PR, say so in its issue. Either wait
  for that PR to merge, or stack the new PR explicitly on the open PR's
  branch and say so in its description. GitHub ignores `Closes #<n>` on a
  stacked PR until it targets the default branch, so its issue is found
  from the `<issue-id>-` branch name.
- Decisions that change what an issue should contain are recorded on the
  issue as a comment, so the issue stays the true record of the scope.

## PR4. Review comments don't widen the scope

A review comment asking for something outside the issue is answered with a
reply suggesting a follow-up issue, not implemented in this PR. The user can
override that.
