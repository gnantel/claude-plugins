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

## 5. Report

State that the PR is ready for human review, with its link, or why the
Copilot loop stopped before that. Cover:

- **Local review:** findings raised, fixed and declined.
- **Copilot:** comments raised, fixed (with commits), declined (with
  reasons) and declined as outside the issue (with the follow-up issues).
- **Re-review after Copilot:** findings raised, fixed (with commits) and
  declined on the commits the loop added, or that the loop added none.
- **Left for the user:** open threads, including any from people.
