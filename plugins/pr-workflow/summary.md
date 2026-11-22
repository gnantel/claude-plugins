# Pull requests (summary)

Full rules: `standards/pull-requests.md` in the pr-workflow plugin.

- Every change starts from a leaf GitHub issue written before the work
  (scope, out of scope, done when); use the `issues` skill. Work needing
  several PRs is a parent issue split into sub-issues first.
- One PR closes exactly one leaf issue (`Closes #<n>`). In scope: the
  issue, fixes to its own changes within that scope, and minimal
  supporting changes.
- Anything else that comes up while a PR is open, including a new request
  from the user, becomes a new issue and its own branch and PR, unless the
  user explicitly says to include it. Never add it to the branch that
  happens to be checked out.
- Problems noticed in passing and follow-ups become issues. Scope decisions
  made in discussion go on the issue as a comment.
- Review locally with `review-branch` (it never creates a PR); use
  `submit-pr` to go from a reviewed branch to a PR ready for human review.
