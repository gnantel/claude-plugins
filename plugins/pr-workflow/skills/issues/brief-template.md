Implement GitHub issue #{number} in `{repository}`: {title}.

The issue is the spec and its Done when is the bar. Lines marked `<<FILL: ...>>` are for the planning session to fill in before the session starts; delete a line that does not apply.

COMMON RULES
- Read issue #{number} in full, including its comments: they hold scope decisions (`gh issue view {number} --comments`).
- Run `git fetch origin` first and base your branch on the latest `origin/<default>` in your own worktree.
- Load the `coding-standards` skill before writing code.
- One PR, closing #{number} only. Anything out of scope becomes a new issue (use the `issues` skill), never part of this branch.
- Docs describe what is true now: no changelog wording, and no counts of growing lists (reviewers, skills, rules) or version numbers.
- Keep exactly one commit on the branch: amend every later fix into it with `git commit --amend`, including `review-branch` fixes, and update the message when a fix changes what the commit does. If you end up with several, squash them into one curated commit before the review is recorded.
- Verify Done when for real, not by reading the code.
- Ship with `pr-workflow:submit-pr`: local review, PR with `Closes #{number}`, Copilot loop, re-review, conflict check and rebase. Report whether Copilot reviewed the final head and how many threads are open.
- Never write the review marker by hand. Never merge.
- Ask the user only when a decision is genuinely theirs.

THIS ISSUE
- Area: <<FILL: the files or area this issue touches>>
- Verify Done when by: <<FILL: the commands to run and what they must show>>
- Sibling sessions: <<FILL: sessions running in parallel and the files to stay out of, or "none running">>
- Version bumps: <<FILL: "skip, one follow-up bumps the whole batch", or "bump as usual">>
- Extra context: <<FILL: name translations for issues written before a reorganisation, the threat model, known tooling problems, or delete>>
