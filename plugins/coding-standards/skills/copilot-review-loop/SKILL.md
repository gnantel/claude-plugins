---
name: copilot-review-loop
description: The Copilot review loop - wait for GitHub Copilot's automatic review of the current pull request, address each relevant comment (fix it, or reply explaining why not), push, and repeat until Copilot's review of the latest commit has no new comments. Use right after creating a pull request or pushing to one, when the user asks for the Copilot review loop, or when asked to address Copilot review comments.
argument-hint: "[pr-number]"
---

# Copilot Review Loop

Script: `python3 ${CLAUDE_SKILL_DIR}/scripts/copilot_review.py <command>`. It
prints JSON. PR argument: `$ARGUMENTS`, or the current branch's PR if empty.

Repeat for at most **5 rounds**:

1. **`next-round [pr]`.** It can wait up to 30 minutes, so run it as a
   background command. Act on its `state`:
   - `clean`: done, go to the report.
   - `timed_out`, `sync_needed` or `dirty_worktree`: stop and tell the user
     why.
   - `address`: continue with its `copilot_threads`.
2. **Judge each Copilot thread** against the code and the project's standards:
   - Relevant and within this PR's scope: fix it, and keep the fix to what
     the comment asks.
   - Wrong, already handled, outdated, out of scope, or a repeat of one you
     declined: `reply` with a short, specific reason, then `resolve`.
   - Needs a design decision: leave it open for the user.
3. **If you fixed anything,** run the project's format, lint and tests, then
   `push-round <round> [pr]`. It commits and pushes in the right mode
   (folding fixes into their commits until a person has reviewed). Then
   `reply` on each fixed thread with `Fixed in <short>: <what changed>` and
   `resolve` it. If you fixed nothing, stop: Copilot won't review again
   without a new commit.

Never reply to, resolve or act on `human_threads`. Those are the user's.

**Report** the rounds run and how the loop ended, what was fixed (with
commits) and declined (with reasons), and links to anything left for the
user, including `human_threads`.
