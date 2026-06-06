# CLAUDE.md

This file is read by Claude Code on session start. It points to `AGENTS.md` for the universal contract and adds Claude-specific overrides.

## Source of Truth

Read `AGENTS.md` first. It contains stack, workflow, branching, skill routing, governance, agent permissions, and constraints. Everything in this file is an addendum or Claude-specific override.

## Claude-specific Skill Routing

When the user says X, invoke the matching skill:

| User says | Skill |
|---|---|
| "scaffold this repo" | /y-init |
| "follow Yash standards" | the-y-coding-standard |
| "audit governance" | /y-govern |
| "review this PR" | /review |
| "plan a feature" | /plan-eng-review |
| "investigate this bug" | /investigate |
| "ship it" | /ship |
| "weekly retro" | /y-retro |

## Tool Permissions (Claude Code defaults)

These mirror `.claude/settings.json`. Override locally in `.claude/settings.local.json`.

Always allowed:

- Read, Write, Edit, Glob, Grep
- Bash: `pnpm`, `uv`, `npm`, `git status`, `git diff`, `git log`, `ls`, `find` (within repo)

Always denied without prompt:

- Bash: `rm -rf`, `git push --force`, `sudo`

Require prompt:

- Bash: `git push`, `git reset --hard`, `gh pr create`, `vercel deploy`

## Session Workflow

At session start:

1. Read `AGENTS.md`.
2. Check `plans/` for active plans on this branch.
3. Check `progress/` for the latest session journal.
4. If no active plan and no journal, ask the user what we're working on.

At session end (or `/ship`):

1. Append a `progress/YYYY-MM-DD-<session>.md` summarizing what shipped.
2. Update the active plan file's status if applicable.
3. Suggest `/y-retro` if significant work landed.

## Style

- No em dashes.
- No emojis in code.
- Markdown formatting in prose.
- Crisp Yash voice. Direct. No filler.

## Memory

Claude Code memory at `~/.claude/projects/<project-slug>/memory/` is for Claude-specific session preferences. Project-level decisions go in `Docs/decisions/` (ADRs), not memory.

## When in doubt

Defer to `AGENTS.md`. Then to the linked references in `the-y-coding-standard/references/`. Then ask the user.
