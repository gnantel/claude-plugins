---
name: copilot-review-loop
description: The Copilot review loop - wait for GitHub Copilot's automatic review of the current pull request, address each relevant comment (fix it, or reply explaining why not), push, and repeat until Copilot's review of the latest commit has no new comments. Use right after creating a pull request or pushing to one, when the user asks for the Copilot review loop, or when asked to address Copilot review comments.
argument-hint: "[pr-number]"
---

# Copilot Review Loop

Repeat review rounds with GitHub Copilot until its review of the PR's latest
commit has no new comments.

Arguments: `$ARGUMENTS`

The helper script is `${CLAUDE_SKILL_DIR}/scripts/copilot_review.py`
(`python3 <script> <command> ...`; run it with `--help` for details):

| Command | Does |
|---|---|
| `wait <owner/repo> <pr> <sha>` | Waits up to 15 minutes for Copilot's review of that commit; prints `new_comments`. Exit code 3 on timeout |
| `threads <owner/repo> <pr>` | Lists unresolved review threads, with `from_copilot` and `outdated` flags |
| `reply <thread-id> <body>` | Replies on a thread |
| `resolve <thread-id>` | Resolves a thread |
| `human-reviewed <owner/repo> <pr>` | Reports whether a person has reviewed the PR: an approval or change request, a review with a written summary, a thread a person started, or a top-level PR comment. Replies inside Copilot's threads don't count, even though they are posted under the user's account |

## 1. Set up

- PR: the argument if given, otherwise the current branch's PR
  (`gh pr view --json number,headRefOid,url`). Repository:
  `gh repo view --json nameWithOwner`.
- Make sure local `HEAD` is pushed and equals the PR's `headRefOid`.
- Rounds so far: 0. **Stop after 5 rounds** and report to the user, since a
  review that keeps producing comments needs a human decision.

## 2. Wait for Copilot's review of the head commit

Run `wait` for the head SHA. It polls for up to 15 minutes, so run it as a
background command if your environment supports that (you are notified when
it exits); otherwise run it in the foreground with a timeout of at least
16 minutes.

When it exits, re-read the PR's `headRefOid` before doing anything else. If
the head changed during the wait (someone else pushed):

1. Bring the local branch up to date with `git pull --ff-only`, so local
   `HEAD` equals `headRefOid` again. If that fails (local commits that are
   not on the PR), stop and ask the user to synchronize the branch. Never
   force-push over commits you haven't seen.
2. Go back to the start of this step with the new head: a review of the old
   commit says nothing about the current one.

If it times out, Copilot probably isn't set to review new pushes. Request a
review with `gh pr edit <pr> --add-reviewer @copilot` and wait once more. If
that also times out, stop and tell the user.

## 3. Decide whether you're done

Run `threads`. Consider only threads with `from_copilot: true`.

- If Copilot's review of the head commit has `new_comments: 0` and no
  Copilot thread is unresolved, the loop is done. Go to step 6.
- Threads started by people (`from_copilot: false`) are the user's own
  review. Never reply to, resolve or act on them in this loop. List them in
  the final report instead.

## 4. Address each open Copilot thread

For each one, read the code it points at and judge it on its merits,
against the project's standards (the `coding-standards` skill and any other
enabled standards):

- **Relevant:** fix it. Keep the fix to what the comment is about, and
  follow the standards in the fix itself.
- **Not relevant** (wrong, already handled, contradicts the standards, or
  out of scope for this PR): don't change code. Reply with a short, specific
  reason, then resolve it.
- **Outdated** (`outdated: true`): check whether it still applies to the
  current code. If not, reply that the code it referred to has changed, and
  resolve it.
- **Unsure, or it needs a design decision:** leave it unresolved and add it
  to the list for the user. Don't guess.
- **A repeat of a comment you already declined:** reply pointing to the
  earlier reply, and resolve it. Don't flip-flop.

## 5. Push the round

If you made fixes, run the project's format, lint and test commands (`just
fmt`, `just lint`, `just test` if a justfile exists; otherwise the project's
own tooling). Then choose how to commit:

- **Rewrite history** while no person has reviewed the PR yet
  (`human-reviewed` reports `false`) and the repository allows rebase merges
  (`gh repo view --json rebaseMergeAllowed`), since only then do the branch's
  commits reach the default branch as they are:
  1. Commit each fix as a fixup of the branch commit that introduced the code
     it changes: `git commit --fixup=<sha>`, finding the commit with
     `git log --format=%h -1 <base>..HEAD -- <file>`.
  2. Fold them in without an editor:
     `GIT_SEQUENCE_EDITOR=true git rebase -i --autosquash <base>`.
  3. Push with `git push --force-with-lease`.
  4. If the rebase hits a conflict, run `git rebase --abort`. That restores
     the branch with this round's fixup commits still on it, so push them as
     they are with a normal `git push` (no force needed).
- **New commits only** once a person has reviewed (`human-reviewed` reports
  `true`), or whenever the repository doesn't allow rebase merges (squash or
  merge commits make the branch's history irrelevant on the default branch):
  commit with a message like `Address Copilot review (round <n>)` and push
  normally. **Never
  force-push after a human review**, because it breaks "changes since your
  last review" for them.

Check `human-reviewed` again every round: the user may review at any time.

After pushing, reply on each fixed thread with `Fixed in <short-sha>:`
(the new head commit) plus one line on what changed, then resolve it.
- If nothing changed in this round (every comment was declined, or left for
  the user), the loop is done. Copilot doesn't re-review without a new
  commit. Go to step 6.
- Otherwise increment the round count and go back to step 2 with the new
  head SHA.

## 6. Report

Summarize for the user:

- Rounds run, and how the loop ended (clean review, nothing left to change,
  round limit, or timeout).
- Per round: comments fixed (with commits) and comments declined (with the
  reason).
- Copilot comments left for the user to decide, with links.
- Open threads from people, with links. These are waiting on the user.
