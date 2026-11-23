---
name: submit-pr
description: Take the current branch from local review to a pull request that is ready for human review - run review-branch, create the PR linked to its leaf issue, run the Copilot review loop, and report what was raised, fixed and declined. Use when the user asks to submit, open or ship a PR, or when the pr-workflow hook blocks pull request creation.
argument-hint: "[base-branch] [--fix]"
---

# Submit PR

Orchestrator: it only decides and delegates. Each stage is its own skill.
If a review or PR creation stops, stop there and tell the user why. The
Copilot loop is the exception: however it ends, including a timeout or a
stop with a reason, go on to the report.

Arguments: `$ARGUMENTS`, passed on to `review-branch`.

## 1. Review the branch

Run `pr-workflow:review-branch` with the arguments. Continue once it has
recorded the review for the current commit. If it stopped (no leaf issue, a
PR linked to a different issue, findings the user hasn't settled), stop too.
Keep its outcome: findings raised, fixed and declined.

## 2. Create the PR

Push the branch and create the PR with `Closes #<n>` for its issue in the
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

If they differ, run `pr-workflow:review-branch` again on the new head,
with the same arguments. Its findings are handled as in stage 1: fixed,
committed and pushed, or declined by the user. Keep its outcome as its own
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
4. Run the project's tests, then push to the PR's head branch with a lease
   bound to the verified SHA:
   `git push --force-with-lease=<branch>:<sha> origin HEAD:<branch>`.
5. Run stage 1 again on the new head, with `origin/<default>` (or the PR's
   base branch, fetched) as its base argument instead of any local branch
   name, and push any commits it produces. Then run stage 3 again on the PR
   as usual (it takes no base argument) and stage 4 with the same base
   argument as stage 1.

Repeat this stage until GitHub reports `MERGEABLE`. Keep what the rebase and
the repeated stages produced as their own outcome, separate from the earlier
ones.

## 6. Report

Run the loop's `status` command (`copilot_review.py status`) on the PR
for the final head. State that the PR is ready for human review, with its
link, only if it reports `ready` (Copilot reviewed the final head, no
threads open), which also covers commits that stages 4 and 5 pushed after
the loop. Otherwise say so explicitly (which head is unreviewed, how many threads are
open) and don't call it ready. If the loop stopped early, say why. Cover:

- **Local review:** findings raised, fixed and declined.
- **Copilot:** comments raised, fixed (with commits), declined (with
  reasons) and declined as outside the issue (with the follow-up issues).
- **Re-review after Copilot:** findings raised, fixed (with commits) and
  declined on the commits the loop added, or that the loop added none.
- **Rebase:** that the PR was already mergeable, or what conflicted, how it
  was resolved and what the review steps raised on the rebased head.
- **Left for the user:** open threads, including any from people.
