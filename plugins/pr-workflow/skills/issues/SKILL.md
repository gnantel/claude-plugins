---
name: issues
description: Issue-first work - every change starts from a leaf GitHub issue written before the work, and each pull request closes exactly one leaf issue. Use before starting any change (find or open its issue, split it into sub-issues if it needs several PRs), when new work comes up while a PR is open, and when recording follow-ups or scope decisions.
---

# Issues

Helper: `python3 ${CLAUDE_SKILL_DIR}/scripts/issues.py <command>` (prints JSON,
needs gh 2.104 or later for sub-issues):

| Command | Does |
|---|---|
| `show <n>` | The issue's body, comments (each marked `trusted` when written by the repository's owner, a member or a collaborator), state, parent, sub-issues and `is_leaf` |
| `for-branch` | The issue the current branch implements: its PR's closing issue (refused if it's in another repository), or the `<issue-id>-` branch name, marked `stacked` when the PR isn't based on the default branch |
| `create --title <t> --body-file <path> [--parent <n>] [--label <l>]` | Creates an issue, as a sub-issue if `--parent` is given |
| `link <parent> <child>` | Makes an existing issue a sub-issue |
| `brief <n>` | Prints the brief for a child session implementing the issue: the fixed rules filled in with the issue number, title and repository, and the parts that vary marked `<<FILL: ...>>` (plain text, not JSON) |

## Before starting a change

1. Find its issue, or create one from the user's request **before** writing
   code. The body has `## Scope` (the purpose, one or two sentences), `## Out
   of scope` (related work left for other issues) and `## Done when`.
2. If it needs more than one PR, it is a parent: split it into sub-issues,
   one per PR, and work on a leaf. Only leaves get PRs. See "Sizing and
   splitting".
3. Work in a git worktree of its own, on a branch named
   `<issue-id>-<description>` (for example `6-issue-linked-prs`), cut from
   the freshly fetched remote default branch: `git fetch origin`, then
   `git worktree add -b <branch> <path> origin/<default>`. Right after the
   fetch, run `pr-workflow:cleanup` to remove local branches and worktrees
   whose PRs merged; it never touches the current worktree or its branch.
   Never cut from a
   local default branch that may be stale. When the change deliberately
   stacks on an open PR (rule PR3), cut from that PR's freshly fetched
   branch (`origin/<parent-branch>`) instead.
4. If the session is already in a worktree, run `git fetch origin` (then
   `pr-workflow:cleanup`) and check
   that the branch contains its base, `origin/<default>` or the parent
   branch it stacks on
   (`git merge-base --is-ancestor origin/<base> HEAD`). If it doesn't and
   the branch has no commits of its own yet, recut it from that base.

## Sizing and splitting

- **A leaf is reviewable in one sitting.** It is one coherent change, judged
  by the lines a reviewer has to read. Mechanical changes (moves, renames,
  generated files) count for little: a 39-file rename can be easy to
  review. If a leaf looks too big, split it before work starts. There is no
  line limit.
- **Order sub-issues by dependency.** Each sub-issue body has a `## Depends
  on` section naming the sub-issues it needs merged first (`None` when it
  needs nothing). Prefer splits where as many sub-issues as possible are
  independent, so they run in parallel, each cut from the latest default
  branch.
- **A dependent sub-issue waits for its dependency to merge.** Stacking a PR
  on an open PR (rule PR3) is the exception, for a long dependent chain
  when review is slow.
- **State a threat model when the code guards, validates or hardens
  something.** Under `## Scope`, say what it defends against and what it
  deliberately does not. A hook that stops Claude forgetting a review is a
  guard rail, not a security boundary. Reviewers then judge the change
  against that, instead of arguing edge cases the issue ruled out.

## While working

- **New work that comes up** (a new request, a problem noticed in passing)
  becomes a new issue, with `--parent` when it belongs to a larger goal. It
  does not go into the current branch unless the user explicitly says so.
- **Scope decisions made during discussion** go on the issue as a comment,
  so the issue stays the true record of what the PR should contain.
- **Follow-ups** are new issues, not notes in a PR description.

## Opening the PR

The description includes `Closes #<n>` for exactly one leaf issue.

## Delegating to child sessions

A planning session writes leaf issues, then starts one child session per
issue, usually on a cheaper model. The child starts with a fresh context, so
its brief is the strongest lever for getting it to follow the rules.

1. Run `brief <n>` for the issue. The fixed rules (read the issue and its
   comments, fetch and branch from `origin/<default>`, load
   `coding-standards`, one PR per leaf issue, docs describe what is true,
   one commit amended in place, verify Done when for real, ship with
   `pr-workflow:submit-pr`, record the review only with `review-branch` step
   7, never merge, ask only for the user's decisions) live in
   `brief-template.md` next to this file.
   Edit the template to change them for every brief. If the issue isn't on
   GitHub, fill in `{number}`, `{title}` and `{repository}` in the template
   by hand.
2. Replace each `<<FILL: ...>>` line, or delete it when it doesn't apply:
   the files or area, how to verify Done when for this issue, sibling
   sessions and the files to stay out of, whether to skip version bumps
   while a batch runs, and extra context (name translations for issues
   written before a reorganisation, the threat model, known tooling
   problems). Fill in only what the request or the issue states. A part
   nobody has decided, such as the version-bump policy, stays marked and is
   put to the user, never guessed.
3. Start the child session with the finished brief.

Running several child sessions at once:

- Each needs its own worktree. Starting them from a session opened on a
  folder that isn't a git repository (such as `~/work`) makes them share
  one checkout.
- Group issues so that no two running sessions touch the same files, and
  order the rest by dependency (see "Sizing and splitting").
- Keep only a few sessions running at once, to stay within usage limits.
