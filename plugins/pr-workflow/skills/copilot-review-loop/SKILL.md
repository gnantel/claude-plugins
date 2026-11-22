---
name: copilot-review-loop
description: The Copilot review loop - wait for GitHub Copilot's automatic review of the current pull request, address each relevant comment (fix it, or reply explaining why not), push, and repeat until Copilot's review of the latest commit has no new comments. Use right after creating a pull request or pushing to one, when the user asks for the Copilot review loop, or when asked to address Copilot review comments.
argument-hint: "[pr-number]"
---

# Copilot Review Loop

Script: `python3 ${CLAUDE_SKILL_DIR}/scripts/copilot_review.py <command>`. It
prints JSON. PR argument: `$ARGUMENTS`, or the current branch's PR if empty.

Repeat for at most **5 rounds**:

1. **`next-round [pr]`.** It requests Copilot's review of the current head
   (a no-op if one is already in progress) and waits up to 15 minutes for
   it, so run it as a background command. Act on its `state`:
   - `clean`: done, go to the report.
   - `timed_out`, `sync_needed` or `dirty_worktree`: stop and tell the user
     why.
   - `address`: continue with its `copilot_threads` and `issue`. If `issue`
     has an `error`, stop and tell the user: without the PR's issue there is
     no scope to judge against.
2. **Judge each Copilot thread, scope first.** Check it against the PR's
   `issue` (its body, plus `trusted_comments`, which record later scope
   decisions), then against the code and the project's standards:
   - **Outside the issue** (rule PR4): it asks for something the issue
     doesn't call for, such as a new feature, an unrelated fix or a refactor
     of code the issue doesn't need, however valid. Don't change code.
     If it's real work, create a follow-up issue with the `issues` skill
     (`--parent` when it shares the PR issue's parent). `reply` that it's
     outside #<n>'s scope, naming the follow-up, then `resolve`. A bug in
     this PR's own changes is within the issue, not outside it.
   - **Relevant and within the issue:** fix it, and keep the fix to what the
     comment asks.
   - **Wrong, already handled, outdated, or a repeat of one you declined:**
     `reply` with a short, specific reason, then `resolve`.
   - **Needs a design decision, or unclear whether it's in scope:** leave it
     open for the user.
3. **If you fixed anything,** run the project's format, lint and tests, then
   `push-round <round> [pr]`. It commits and pushes in the right mode
   (folding fixes into their commits until a person has reviewed). Then
   `reply` on each fixed thread with `Fixed in <short>: <what changed>` and
   `resolve` it. If you fixed nothing, stop: Copilot won't review again
   without a new commit.

Never reply to, resolve or act on `human_threads`. Those are the user's.

**Report** the rounds run and how the loop ended, what was fixed (with
commits), declined (with reasons) and declined as outside the issue (with
the follow-up issues created), and links to anything left for the user,
including `human_threads`.
