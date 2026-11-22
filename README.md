# claude-plugins

My personal Claude Code plugin marketplace (`personal`).

| Plugin | What it does | Enable |
|---|---|---|
| [coding-standards](plugins/coding-standards) | Coding style rules and style reviewers | Globally |
| [pr-workflow](plugins/pr-workflow) | Issues, `/pre-pr` review, scope reviewer, PR hook, Copilot loop | Globally |
| [operational-readiness](plugins/operational-readiness) | Metrics, structured logging and resilience reviewers | Per project (services) |
| [spring-boot](plugins/spring-boot) | Spring Boot conventions and reviewer | Per project (Spring Boot) |

## Install

In Claude Code, from GitHub:

```
/plugin marketplace add gnantel/claude-plugins
/plugin install coding-standards@personal
/plugin install pr-workflow@personal
```

or from the local checkout, which is handier while editing the rules:

```
/plugin marketplace add ~/work/claude-plugins
```

Add the summaries to `~/.claude/CLAUDE.md`:

```
@~/work/claude-plugins/plugins/coding-standards/summary.md
@~/work/claude-plugins/plugins/pr-workflow/summary.md
```

Enable the per-project plugins (only the ones that apply) by adding to its
`.claude/settings.json`:

```json
{
  "enabledPlugins": {
    "operational-readiness@personal": true,
    "spring-boot@personal": true
  }
}
```

and describing that project's tools in `.claude/operational.md` (metrics
library and naming, logging library and required fields, resilience library
and default policies).

## How reviews work

`/pr-workflow:pre-pr` runs every enabled agent named `*-reviewer`, from
any plugin, in parallel. A review plugin provides:

- agents named `<name>-reviewer`, each checking a narrow set of rule IDs,
  reading its rules from `${CLAUDE_PLUGIN_ROOT}/skills/<plugin>/standards/`
  and returning findings in the shared format, and
- a skill with the same name as the plugin, holding those rules in
  `standards/` and loading them before Claude writes code.

Adding a review plugin that follows this shape extends `/pre-pr` with no
other changes. When Claude creates a PR, the pr-workflow hook blocks
it until the current commit has passed `/pre-pr`.

## Changing rules

Edit the plugin's `standards/` files, bump its `version` in
`.claude-plugin/plugin.json`, then run `/plugin marketplace update personal`.
Rules that reviews keep flagging should become lint or ast-grep checks in the
project template instead.

## Tests and evals

- **Unit tests** cover the deterministic code (the PR-review hook and the
  Copilot review loop's scripts): `just test`. They're fast and free, so run
  them on every change.
- **Evals** check that the skills and reviewers behave as intended, with
  and without the plugin: `just eval <plugin>` (for example
  `just eval coding-standards`). Each case in a plugin's `evals/` folder
  builds a scratch repository with a planted violation of one rule, next to
  a look-alike the rules allow, and graders check the review. Run them when
  a skill or reviewer changes. Each case makes an agent run with and
  without the plugin (one run per case), plus Sonnet grading of each answer. Every run prints its cost, and `--max-cost-usd`
  sets a ceiling.

The evals grant `git`, `gh` and `python3` inside the eval sandbox, which on
Ubuntu needs `bubblewrap` and `socat` installed and an AppArmor profile for
`bwrap` (see [sandboxing](https://code.claude.com/docs/en/sandboxing)).
Results are written to each plugin's `evals/results/`, which git ignores.
