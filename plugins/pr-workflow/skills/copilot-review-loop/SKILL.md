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
2. **Judge each Copilot thread, scope first, then value.** Check it
   against the PR's `issue` (its body, plus `trusted_comments`, which record
   later scope decisions), then against the code and the project's
   standards:
   - **Outside the issue** (rule PR4): it asks for something the issue
     doesn't call for, such as a new feature, an unrelated fix or a refactor
     of code the issue doesn't need, however valid. Don't change code.
     If it's real work, create a follow-up issue with the `issues` skill
     (`--parent` when it shares the PR issue's parent). `reply` that it's
     outside #<n>'s scope, naming the follow-up, then `resolve`. A bug in
     this PR's own changes is within the issue, not outside it.
   - **Relevant and within the issue:** fix it, and keep the fix to what the
     comment asks.
   - **Low value:** a speculative edge case, hardening beyond the threat
     model the issue or the code's header states (a guard rail is not a
     security boundary), or a style preference that conflicts with the
     standards. `reply` with a short reason, then `resolve`.
   - **Wrong, already handled, outdated, or a repeat of one you declined:**
     `reply` with a short, specific reason, then `resolve`.
   - **Needs a design decision, or unclear whether it's in scope:** leave it
     open for the user.
3. **If you fixed anything,** run the project's format, lint and tests, then
   `push-round <round> [pr]`. It commits and pushes in the right mode
   (folding fixes into the branch's single commit until a person has
   reviewed; new commits afterwards). If a fix changes what the commit does,
   write the updated message to a file outside the working tree (push-round
   refuses one inside it) and pass `--message-file <file>`. The
   commit is rewritten, so its hash won't last: `reply` on each fixed thread
   with `Fixed: <what changed>`, with no hash, and `resolve` it. If you fixed nothing, stop: Copilot won't review again
   without a new commit. This includes a round whose comments are all
   declined: end the loop there.

**Final round.** Copilot reviews every push automatically. After the push
of round 5's fixes, run `next-round` once more to wait for the review of
that head. In it fix only correctness bugs; decline everything else with a
reason. A fix pushed there makes the head unreviewed again: don't start
another round, report it.

Before the report, resolve what you declined, then run `status [pr]`. It
returns at once with `head_reviewed`, `open_threads` and `ready`.

Never reply to, resolve or act on `human_threads`. Those are the user's.

**Report** whether Copilot reviewed the final head (`head_reviewed`; if
not, which head) and how many threads are open. Then the rounds run and how the loop ended, what was fixed (with
what changed in each), declined (with reasons) and declined as outside the issue (with
the follow-up issues created), and links to anything left for the user,
including `human_threads`.
