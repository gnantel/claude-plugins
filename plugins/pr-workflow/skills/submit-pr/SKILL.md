---
name: submit-pr
description: Take the current branch from local review to a pull request that is ready for human review - run review-branch, create the PR linked to its leaf issue, run the Copilot review loop, file a removal issue for each new feature flag, and report what was raised, fixed and declined. Use when the user asks to submit, open or ship a PR, or when the pr-workflow hook blocks pull request creation.
argument-hint: "[base-branch] [--fix]"
---

# Submit PR

Orchestrator: it only decides and delegates. Each stage is its own skill.
If a review or PR creation stops, stop there and tell the user why. The
Copilot loop is the exception: however it ends, including a timeout or a
stop with a reason, go on to the report.

Arguments: `$ARGUMENTS`, passed on to `review-branch`.

## 1. Review the branch

If the branch is already pushed, note the remote tip first
(`git ls-remote origin <branch>`): it is the lease if the review rewrites
the branch. A repository with no `origin`, or a remote without the branch,
has nothing to verify: go on to the review. Otherwise fetch the tip and
check that it is an ancestor of local `HEAD`
(`git merge-base --is-ancestor <noted tip> HEAD`). If it isn't, another
session or a person pushed a commit that local `HEAD` lacks, and a rewrite
plus lease push would discard it: stop, say which commits the remote has
that local `HEAD` lacks, and ask the user to sync (rebase onto or merge the
remote branch) before anything is rewritten.

Run `pr-workflow:review-branch` with the arguments. Continue once it has
recorded the review for the current commit. If it stopped (no leaf issue, a
PR linked to a different issue, findings the user hasn't settled), stop too.
Keep its outcome: findings raised, fixed and declined.

## 2. Create the PR

The branch has exactly one commit on its base at this point (stage 1
squashes it if needed), with a message that describes the whole change and
ends with `Closes #<n>`. Stacked branches deliberately split into several
commits are the exception.

Push the branch (with `git push --force-with-lease=<branch>:<noted tip>` if
stage 1 rewrote commits that were already pushed and no person has been
involved; a plain push for a new branch or additive commits) and create the PR with `Closes #<n>` for its issue in the
description. Its `--base` is a branch name: the base branch argument if one
was given, the branch it stacks on, or otherwise the default branch. Never
the merge-base commit that `review-branch` diffs against. If the branch already has a
PR, reuse it. Write the description to a file and pass it with `--body-file`.

Confirm the link with `gh pr view --json closingIssuesReferences`: exactly
that one issue. Fix the description with `gh pr edit` if it doesn't match.

A stacked PR (based on another feature branch, not the default branch) is
the exception: GitHub ignores closing keywords there, so the link stays
empty. Its issue comes from the branch name (`<issue-id>-<description>`).
Confirm the link once the PR is retargeted to the default branch.

## 3. Run the Copilot loop

Note the head commit (`git rev-parse HEAD`) as the pre-loop head. Run
`pr-workflow:copilot-review-loop` on the PR. Keep its report: rounds,
fixes, declined comments, follow-up issues, how it ended (including why it
stopped, if it did) and anything left for the user.

## 4. Re-review what the loop pushed

Compare the pre-loop head with the current head (`git rev-parse HEAD`). If they are
equal, the loop added no commits: skip this stage and say so in the report.

If they differ, note the PR's head SHA (`gh pr view --json headRefOid`) as
the lease. It must equal local `HEAD`: if it doesn't, a commit was pushed
that the local branch lacks (or the push didn't land), so stop, report
both SHAs and ask the user to sync instead of reviewing and rewriting.
Otherwise run `pr-workflow:review-branch` again on the new head, with
the same arguments. Its findings are handled as in stage 1: fixed
(while only bots have reviewed, amended into the single commit and pushed
with `git push --force-with-lease=<branch>:<noted SHA>`, never the amended local head; once a person has
reviewed or commented, new commits pushed normally), or declined by the
user. If the loop left the commit message
out of date, update it in the same amend. Keep its outcome as its own
stage, separate from stage 1. If it stopped on findings the user hasn't
settled, stop and tell the user.

## 5. Make the PR mergeable

Run `git fetch origin`, then `gh pr view --json mergeable,mergeStateStatus`.
If GitHub reports `MERGEABLE` and the PR is not stacked on a parent whose PR
was squash-merged, skip this stage and say so in the report. A stacked PR
whose parent was squash-merged goes through the steps below even when
`MERGEABLE`, since it is judged against an obsolete base.
GitHub may report `UNKNOWN` while it computes; ask again every 10 seconds
for up to 2 minutes. If it is still `UNKNOWN`, don't call the PR ready:
report that mergeability is unknown.

If the PR conflicts with its base, or is stacked on a squash-merged parent:

1. Stop and ask the user before rewriting anything if a person has reviewed
   the PR, started a review thread or commented on it. Only a PR no human
   has been involved in is rebased unasked.
2. Verify that the PR is not from a fork (`gh pr view --json
   isCrossRepository`) and that local `HEAD` equals its `headRefOid`; if
   either fails, stop and tell the user. Note that SHA as the lease.
3. Rebase the branch onto the latest base and resolve the conflicts. A
   stacked PR whose parent was squash-merged uses
   `git rebase --onto origin/<default> <parent's old tip>`, so the parent's
   original commits are dropped; then retarget the PR to the default
   branch and confirm its closing-issue link as in stage 2. Stop and ask
   the user only when a conflict can't be resolved without a judgement call on the
   code's intent.
4. Rebasing keeps the single commit. Run the project's tests, then push to the PR's head branch with a lease
   bound to the verified SHA:
   `git push --force-with-lease=<branch>:<sha> origin HEAD:<branch>`.
5. Run stage 1 again on the new head, with `origin/<default>` (or the PR's
   base branch, fetched) as its base argument instead of any local branch
   name, and fix as in stage 4: amend into the single commit with a lease push only
   while no person has reviewed, otherwise add commits. Then run stage 3 again on the PR
   as usual (it takes no base argument) and stage 4 with the same base
   argument as stage 1.

Repeat this stage until GitHub reports `MERGEABLE`. Keep what the rebase and
the repeated stages produced as their own outcome, separate from the earlier
ones.

## 6. File flag removal issues

Do this whenever you are about to report on the PR, however stages 3 to 5
ended, so it covers the final head. The rules and the issue's format are in
PR7 of `${CLAUDE_PLUGIN_ROOT}/standards/pull-requests.md`: read it first.

1. **Find the added flags.** First check that local `HEAD` equals the PR's
   head (`gh pr view --json headRefOid`). If it doesn't, the local diff
   isn't the PR's: file nothing, report that the flag check didn't run and
   don't call the PR ready. Otherwise read the diff the PR adds:
   `git diff <merge-base> HEAD`, where the merge base is
   `git merge-base HEAD origin/<the PR's base branch>`, so a stacked PR
   doesn't count its parent's flags. For each flag key the diff newly
   evaluates, search the merge base (`git grep -F <key> <merge-base>`) and
   keep the keys PR7 says the branch adds. The project's
   `.claude/operational.md`, if present, names its flag wrapper. If there
   are none, create no issue or label, say in the report that the branch
   adds no flag, and skip the rest of this stage.
2. **Reuse what exists**, so a repeated run files nothing twice:
   `gh issue list --label flag-removal --state open --limit 1000 --json number,body`.
   An open issue is this PR's removal issue for a flag only if its `Flag:`
   line is exactly the key and its `Pull request:` line is this PR. Don't
   reuse or change one that names the same key for another PR: name it in
   the report, for the user to settle.
3. **File the missing ones.** Make sure the label exists: if
   `gh label list --search flag-removal --json name` doesn't list
   `flag-removal`, run
   `gh label create flag-removal --description "Remove a feature flag"`.
   For each flag without an issue, write the PR7 body to a file and run
   `python3 ${CLAUDE_PLUGIN_ROOT}/skills/issues/scripts/issues.py create --title "Remove feature flag <key>" --body-file <path> --label flag-removal`,
   with no `--parent`.
4. **Link them from the PR.** Save the current description's text
   (`gh pr view --json body --jq .body`) to a file, add the missing
   `Flag removal: #<n> (<key>)` lines, keeping the rest as it is, and run
   `gh pr edit --body-file <path>`. Then confirm with
   `gh pr view --json closingIssuesReferences` that the PR still closes only
   its own issue (a stacked PR still closes none).

If a step fails, go on to the report and say which flags have no linked
removal issue.

## 7. Report

Check that the branch is still one commit on its base. Run the loop's `status` command (`copilot_review.py status`) on the PR
for the final head. State that the PR is ready for human review, with its
link, only if it reports `ready` (Copilot reviewed the final head, no
threads open), which also covers commits that stages 4 and 5 pushed after
the loop, the flag check ran, and every flag the branch adds has a removal
issue linked from the PR description. Otherwise say so explicitly (which
head is unreviewed, how many threads are open, whether the flag check ran,
which flags have no linked removal issue) and don't call it ready. If the
loop stopped early, say why. Cover:

- **Commit:** that the PR reaches human review as one commit, or why it
  doesn't.
- **Local review:** findings raised, fixed and declined.
- **Copilot:** comments raised, fixed (with commits), declined (with
  reasons) and declined as outside the issue (with the follow-up issues).
- **Re-review after Copilot:** findings raised, fixed (with commits) and
  declined on the commits the loop added, or that the loop added none.
- **Rebase:** that the PR was already mergeable, or what conflicted, how it
  was resolved and what the review steps raised on the rebased head.
- **Flag removal:** each flag the branch adds with its removal issue, and
  any open removal issue for the same key from another PR, or that it adds
  none.
- **Left for the user:** open threads, including any from people.
