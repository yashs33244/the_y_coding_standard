# AGENTS.md

The contract for any agent working in the_y_coding_standard repo.

## Project Overview

the_y_coding_standard is a Claude Code plugin by Yash Singh. It encodes hard-opinionated coding standards for Python and React/Next.js, ships an AGENTS.md template, and runs a parallel-agent governance audit.

## Stack

- Plugin format: Claude Code skill + commands + scripts
- Scripts: Python 3.13+ via `uv run --script` (PEP 723 inline metadata)
- Distribution: GitHub + Claude Code marketplace

## Repository Layout

```
the_y_coding_standard/
  README.md                 # human-facing overview
  AGENTS.md                 # this file
  CHANGELOG.md
  CONTRIBUTING.md
  LICENSE
  .claude-plugin/
    plugin.json             # plugin manifest
    marketplace.json        # marketplace manifest
  skills/
    the-y-coding-standard/
      SKILL.md              # skill entry, aggressive triggers
      references/
        python.md
        react-nextjs.md
        agentic-stack.md
        governance.md
        project-scaffold.md
      templates/
        AGENTS.md           # drop-in for downstream repos
        CLAUDE.md           # drop-in for downstream repos
      scripts/
        scan_secrets.py
        audit_deps.py
        check_agents_md.py
      evals/
        triggers.md         # manual trigger test cases
  commands/
    y-init.md               # /y-init scaffolds a repo
    y-govern.md             # /y-govern runs the audit
```

## Workflow

Issue -> Plan -> Implement -> Test -> Review -> Ship.

1. Plan: `plans/YYYY-MM-DD-<feature>.md`.
2. Test: trigger eval cases in `skills/the-y-coding-standard/evals/triggers.md`.
3. Review: run `/y-govern` on this repo.
4. Ship: tag and release per `CONTRIBUTING.md`.

## Branching

- `main`: protected. PR required.
- `feat/<slug>`, `fix/<slug>`, `chore/<slug>`, `docs/<slug>`.

## Coding Standards

The plugin eats its own dog food. Follow `skills/the-y-coding-standard/references/`.

Hard rules:
- No em dashes in any file.
- No emojis.
- Python scripts: type hints, ruff clean.
- Markdown: clear headings, table-heavy.

## Governance

Run `/y-govern` before every release.

## Agent Permissions

| Surface | Read | Write | Run scripts | Push to main |
|---|---|---|---|---|
| Claude Code | yes | yes | yes | never |
| Codex | yes | review-only | no | never |
| CI bot | yes | no | yes | only via PR merge |
| Human dev | yes | yes | yes | only via PR |

## Constraints

Agents MUST NOT:
- Push directly to main.
- Bump version without a CHANGELOG entry.
- Add a new command without updating plugin.json AND marketplace.json AND evals/triggers.md.
- Add a new reference file without updating SKILL.md's Reference Index table.

## Filing Rules

| Information | Lives in |
|---|---|
| Feature plans | `plans/` (create on demand) |
| Investigation outputs | `findings/` (create on demand) |
| Session journals | `progress/` (create on demand) |
| Architecture decisions | `Docs/decisions/` (create on demand) |
| Reusable patterns for downstream repos | `skills/the-y-coding-standard/references/` |
| Governance scripts | `skills/the-y-coding-standard/scripts/` |
| Slash commands | `commands/` |

## Ownership

- Owner: Yash Singh
- Repo: https://github.com/yashs33244/the_y_coding_standard
- License: MIT

## Last reviewed

2026-06-07
