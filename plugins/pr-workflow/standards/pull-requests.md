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
- **Each leaf is reviewable in one sitting**, judged by the lines a
  reviewer has to read; mechanical changes (moves, renames, generated
  files) count for little. A leaf that looks too big is split before work
  starts.
- **Sub-issues record their dependencies** in a `## Depends on` section and
  are split so that as many as possible are independent.
- **An issue whose code guards, validates or hardens something states its
  threat model**: what it defends against and what it deliberately does
  not. Review judges the change against it.
- **Branch from the freshly fetched `origin/<default>`**, in its own
  worktree, named `<issue-id>-<description>` (`6-issue-linked-prs`).
- **The description of the PR includes `Closes #<n>`** for its one leaf
  issue.

## PR3. New work becomes a new issue

When out-of-scope work comes up (a new request from the user, a problem
noticed in passing, a follow-up), open a new issue for it, as a sub-issue
when it belongs to a larger goal. Don't add it to the branch that happens
to be checked out, unless the user explicitly asks for that.

- If the new work depends on an open PR, say so in its issue. Waiting for
  that PR to merge is the default; stacking is the exception, for a long
  dependent chain when review is slow. To stack, base the new PR explicitly
  on the open PR's branch and say so in its description. GitHub ignores `Closes #<n>` on a
  stacked PR until it targets the default branch, so its issue is found
  from the `<issue-id>-` branch name.
- Decisions that change what an issue should contain are recorded on the
  issue as a comment, so the issue stays the true record of the scope.

## PR4. Review comments don't widen the scope

A review comment asking for something outside the issue is answered with a
reply suggesting a follow-up issue, not implemented in this PR. The user can
override that.

## PR5. Conflicts are resolved by rebasing, before human review

A PR is reported ready for human review only once GitHub reports it
`MERGEABLE`. If its base moved on and it conflicts, rebase the branch onto
the latest base, run the tests, push with a lease bound to the PR's verified
head SHA, and review the new head again. PRs are squash-merged, so rewriting
the branch loses nothing.

Rebase unasked only when no person has reviewed, commented on or started a
thread on the PR; otherwise ask the user first, since rewriting reviewed
history is theirs to allow.

A stacked PR whose parent was squash-merged uses
`git rebase --onto origin/<default> <parent's old tip>`, which drops the
parent's original commits, and is then retargeted to the default branch.

## PR6. A PR reaches human review as one commit

The branch has one commit on its base when the PR is opened, with a message
that describes the whole change and ends with `Closes #<n>`, so it reads as
one change and rebases cleanly.

- **Amend by default.** Every later fix goes into that commit with
  `git commit --amend`: the session's own corrections, `review-branch`
  fixes and the Copilot loop's fixes. If a fix changes what the commit does,
  update the message.
- **Squash as a backstop.** Just before the review is recorded, a branch
  with more than one commit on its base is squashed into one. The review
  marker records HEAD, so it is recorded after the last amend and never
  rewritten by hand.
- **Replies don't cite hashes.** The commit is rewritten, so thread replies
  say what changed.
- **Once a person has reviewed, fixes are new commits.** Rewriting reviewed
  history is theirs to allow (PR5).
- **Exception:** a stacked branch deliberately split into several commits
  keeps them.

## PR7. Every new feature flag has a removal issue

A feature flag is temporary, so the PR that adds one is not reported ready
for human review until an issue to remove it exists and the PR description
links it. Each flag a PR adds has its own removal issue, which names that
PR.

**A branch adds a flag** when its diff makes code evaluate a flag key that
nothing evaluates on its base. Code evaluates a flag through the
OpenFeature API, the project's wrapper around it (typically while building
the request's flag snapshot) or a flag SDK. The key may be a literal or a
constant. These add no flag: another use of a flag the base already
evaluates (including moved code), a configuration setting, and a flag that
only tests evaluate.

**Removal time.** A flag is removed once it has been fully on for the time
the project's `.claude/operational.md` gives with its flag setup, for
example `Remove a flag once it has been fully on for 30 days.` If the
project gives none, the time is 14 days.

**Issue.** Its label is `flag-removal`, its title is
`Remove feature flag <flag key>`, and it is never a sub-issue: as one, it
would make the feature's issue a parent while its PR is open (PR1), or
hold the feature's parent goal open until the removal. Its body:

```markdown
## Flag removal

- Flag: checkout-new-pricing
- Removal condition: fully on for 14 days
- Reached 100%: pending
- Pull request: #12
- Feature issue: #6

## Rollout plan

1% → 10% → 50% → 100%

## Scope

Remove the `checkout-new-pricing` flag and the old path it gates, keeping
the new behaviour. Start once the removal condition is met.

## Out of scope

Changing the new behaviour.

## Done when

Nothing in the code or its configuration refers to `checkout-new-pricing`
or runs the old path.
```

- **The `Flag removal` fields are read by automation.** Keep the heading,
  the field names, their order and one `- <name>: <value>` line per field,
  with no backticks, links or notes in a value.
- `Flag` is the key exactly as the code evaluates it.
- `Removal condition` is `fully on for <n> days`.
- `Reached 100%` is `pending` until the flag is fully on, then that date as
  `YYYY-MM-DD`. The removal time counts from it.
- `Pull request` and `Feature issue` are `#<number>`.
- The rollout plan is the one the feature's issue or the project states,
  and `1% → 10% → 50% → 100%` when neither does.

**Link.** The PR description has one line per flag,
`Flag removal: #<n> (<flag key>)`. It never puts a closing keyword
(`Closes`, `Fixes`, `Resolves`) before a removal issue: the PR closes only
its own issue (PR1).
