# Agentic Engineering Stack

The reference layout for any repo where AI agents (Claude Code, Cursor, Codex, Manus, etc.) participate in development. Treats agents as first-class team members with named files, contracts, and audit trails.

If you cannot point at the file where an agent recorded what it did, the agent did not do work. It hallucinated work. The whole stack below exists to make agent activity legible and reviewable.

## Mental Model

The repo IS the org chart. Each folder is a department. Each `SKILL.md` is an employee with a defined capability. `AGENTS.md` is the company handbook every agent reads first.

Borrowed terminology (treat as inspiration, not literal mapping):

| Agent term | Org term | What it does |
|---|---|---|
| Skills | Employees | Each one has a capability |
| The resolver | Org chart | Routes who handles what |
| Filing rules | Internal process | Where information lives |
| Check-resolvable | Audit & compliance | Can the system do what it claims? |
| Trigger evals | Performance reviews | Does the right team respond? |

Internalize this: when you scaffold a repo, you are not creating folders. You are hiring a team and writing their job descriptions.

## The Canonical Tree

```
repo/
  AGENTS.md                # the contract every agent reads first
  CLAUDE.md                # Claude Code specific instructions, links to AGENTS.md
  README.md                # human-facing project overview
  .agents/
    skills/
      <skill-name>/
        SKILL.md
        tests/
  plans/                   # implementation plans (one .md per feature)
    YYYY-MM-DD-<feature>.md
  findings/                # investigation outputs, audits, diagnostics
    YYYY-MM-DD-<topic>.md
  progress/                # session journals, what happened when
    YYYY-MM-DD-<session>.md
  skills/                  # team-installable Claude Code skills
    <skill-name>/SKILL.md
  tests/                   # actual project tests
  Docs/                    # human documentation
    architecture.md
    decisions/             # ADRs
      0001-use-fluid-compute.md
    runbooks/
  .claude/                 # Claude Code specific config
    commands/
    skills/
    settings.json
  .claude-plugin/          # if shipping a plugin
    plugin.json
    marketplace.json
  .conductor/              # Conductor workspace config (parallel agents)
  .cursor/                 # Cursor rules and prompts
  .devcontainer/           # Dockerized dev env
  .github/                 # workflows, issue templates
  .husky/                  # pre-commit hooks
```

Two skills folders is intentional. `.agents/skills/` is project-internal: skills only this repo needs. `skills/` is team-installable: skills meant to be shipped as a plugin or symlinked into `~/.claude/skills/`. Keep the boundary clean.

## AGENTS.md Contract

Every repo with agent involvement must have an `AGENTS.md` at root. It is the single source of truth for agents. Format below. A drop-in template lives at `templates/AGENTS.md` in this plugin.

Required sections:

1. Project overview (2-3 sentences).
2. Stack (languages, frameworks, key services).
3. Build / run / test commands (concrete: `pnpm dev`, `uv run pytest`).
4. Repository layout (the tree above, annotated).
5. Branching and commit conventions.
6. Workflow: Issue -> Plan -> Implement -> Test -> Review -> Ship.
7. Skill routing rules ("when user asks X, invoke skill Y").
8. Governance (link to `/y-govern`, list which scripts run).
9. Constraints (what agents may NOT do without human approval: prod deploys, force-push, destructive SQL).
10. Contact / ownership.

If a section is missing, an agent will guess. Guessing is how production goes down.

## Workflow: Issue -> Plan -> Implement -> Test -> Review -> Ship

This is the canonical loop. Popularized by Claude Code and Manus-style workflows.

```
Issue
  v
Plan          -> plans/YYYY-MM-DD-<feature>.md
  v
Implement     -> code + tests + WIP commits
  v
Test          -> unit + integration + e2e
  v
Review        -> /y-review or external reviewer
  v
Ship          -> /y-ship (PR, deploy)
  v
Retro         -> progress/YYYY-MM-DD-retro.md
```

Each stage produces a named artifact in the repo. No invisible work. If a stage produced nothing on disk, treat it as not done and rerun it.

## The Three Folders: plans/, findings/, progress/

These three folders are the backbone of agent-legible work. Skip them and you are building in the dark.

### plans/

Forward-looking documents. One per feature or refactor. Filename: `YYYY-MM-DD-<slug>.md`.

Minimum sections:
- Problem statement
- Constraints
- Approach (with ASCII diagrams)
- Test plan
- Rollout / migration
- NOT in scope

The "NOT in scope" section is non-negotiable. Most agent overreach happens because no one wrote down what was off-limits.

### findings/

Investigation outputs. Filename: `YYYY-MM-DD-<topic>.md`.

Use for: bug investigations, performance audits, architectural reviews, dependency audits, security scans.

Sections:
- Trigger (why we looked)
- Method (how we investigated)
- Findings (numbered list)
- Recommendations
- Open questions

A finding without a method section is a guess. Always record how you investigated, not just what you found.

### progress/

Session journals. Filename: `YYYY-MM-DD-<session-name>.md`.

Use for: what happened today, what's next, blockers, what we learned. Append-only history.

Sections:
- What shipped
- What's in progress
- Blockers
- Decisions made
- Tomorrow

Progress files are the cheapest way to make handoffs (human-to-agent, agent-to-agent, future-self-to-current-self) actually work.

## Skills as Reusable Capabilities

A "skill" is a `SKILL.md` file plus optional scripts/tests/templates. It encodes a capability the team uses repeatedly.

Structure:
```
.agents/skills/<skill-name>/
  SKILL.md                 # contract: name, triggers, rules
  scripts/                 # deterministic code (no LLM for what code can do)
  tests/                   # unit + integration + LLM evals
  references/              # reference docs the skill loads
```

Skill creation checklist (the Skillify 10-item promotion checklist):

1. SKILL.md present with frontmatter (name, description, triggers).
2. Deterministic code in scripts/ (do not ask an LLM to do what code can do).
3. Unit tests.
4. Integration tests against live endpoints.
5. LLM evals for quality and correctness.
6. Resolver trigger entry in AGENTS.md.
7. Resolver eval verifying the trigger actually routes.
8. Check-resolvable: DRY audit (does this duplicate an existing skill?).
9. E2E smoke test.
10. Brain filing rules: where related context goes.

If a skill cannot pass items 1-5, it is a prompt, not a skill. Keep it in your notes, not in the repo.

## Brain Filing Rules

Where each kind of information lives in the repo:

| Information | Lives in |
|---|---|
| Why we built X | `Docs/decisions/` (ADRs) |
| How a feature works | `Docs/architecture.md` or feature README |
| Step-by-step ops | `Docs/runbooks/` |
| Plan for a future change | `plans/` |
| Result of an investigation | `findings/` |
| What happened in a session | `progress/` |
| Reusable capability | `.agents/skills/` |
| Project standards | `AGENTS.md` + linked references |
| Per-agent overrides | `CLAUDE.md`, `.cursor/rules`, `.conductor/config.json` |

When in doubt, file it. A misfiled note is recoverable. An unwritten note is gone.

## The Resolver Pattern

The resolver is the routing logic that decides which skill responds to a user request. In Claude Code, this is the `description` field on each skill plus the AGENTS.md routing table.

Resolver design:
- Each skill has clear, non-overlapping triggers.
- AGENTS.md has an explicit routing table for common phrases.
- When triggers overlap, write a check-resolvable test that probes the ambiguity.

Example AGENTS.md routing table block:

```markdown
## Skill Routing

| User says | Invoke |
|---|---|
| "review this PR" | /y-review |
| "ship it" | /y-ship |
| "scaffold the repo" | /y-init |
| "audit agent permissions" | /y-govern |
| "start a new feature" | /y-office-hours (external) |
```

Treat resolver collisions like merge conflicts: stop and resolve before continuing. Two skills firing on the same trigger is a bug, not a feature.

## Multi-Agent Surfaces (when to use each)

| Surface | Use for |
|---|---|
| Claude Code (terminal/IDE) | Interactive coding, long sessions, complex multi-step |
| Cursor | In-IDE pair programming, quick edits |
| Codex CLI | Independent code review, adversarial second opinion |
| Manus | Browser-based autonomous tasks |
| Conductor | Parallel agent orchestration in worktrees |

Each surface reads `AGENTS.md` first. Surface-specific overrides go in the respective dotfolder. Do not duplicate stack-wide rules across `.cursor/rules` and `CLAUDE.md`. Link both back to `AGENTS.md` and override only what is genuinely surface-specific (keybindings, IDE behavior, agent autonomy limits).

## Microsoft AI Engineering Coach Inspiration

Patterns to borrow:
- Coach role for plan critique BEFORE implementation.
- Quality gates at each workflow stage.
- Explicit handoff contracts between stages.
- Measurable success criteria per plan.

The "coach before code" pattern is the single biggest win. Most agent failure modes are upstream of code: bad plan, missing constraint, unmeasured success criteria. Catch them in `plans/` review, not in PR review.

## Plan File Template (for plans/)

Every plan file has:

```markdown
# Plan: <feature-name>

Date: YYYY-MM-DD
Author: <name>
Status: draft | active | shipped | archived

## Problem
<2-3 sentences>

## Constraints
- <constraint>
- <constraint>

## Approach
<prose + ASCII diagrams>

## File-by-file changes
- `path/to/file.ts`: <what changes>

## Tests
- Unit: <list>
- Integration: <list>
- E2E: <list>

## Rollout
- Feature flag: <name or N/A>
- Migration: <steps or N/A>
- Rollback: <plan>

## NOT in scope
- <deferred item>: <why>

## Open questions
- <question>
```

A plan without a "file-by-file changes" section is wishful thinking. Force yourself to enumerate the files. If you cannot, the design is not concrete enough.

## Finding File Template (for findings/)

```markdown
# Finding: <topic>

Date: YYYY-MM-DD
Trigger: <what prompted this>
Method: <how we investigated>

## Findings
1. <finding> - severity, file:line
2. <finding>

## Recommendations
1. <action>

## Open questions
- <question>
```

Findings cite file:line. Vague findings get ignored. Specific findings get fixed.

## Progress File Template (for progress/)

```markdown
# Session: YYYY-MM-DD

## What shipped
- <thing>

## In progress
- <thing>

## Blockers
- <thing>

## Decisions
- <decision> -> <rationale>

## Tomorrow
- <next>
```

Write the progress file at session end. Five minutes of journaling saves an hour of "where was I" the next day.

## Where /y-init scaffolds

When the user runs `/y-init`, this skill writes the canonical tree above (empty folders + stub files where useful + AGENTS.md + CLAUDE.md from the templates folder).

What `/y-init` guarantees:
- `AGENTS.md` exists and has all 10 required sections (with TODOs where the user must fill in).
- `CLAUDE.md` exists and points at `AGENTS.md` as the source of truth.
- `plans/`, `findings/`, `progress/` exist with `.gitkeep` and a `README.md` explaining filing rules.
- `Docs/decisions/` has `0000-record-architecture-decisions.md` (the meta-ADR).
- `.agents/skills/` exists and is empty (no defaults, no fluff).
- A pre-commit hook stub is added if `.husky/` is present.

What `/y-init` does NOT do:
- Install dependencies.
- Pick your framework.
- Write your stack section. That is your job. The scaffolder cannot read your mind.

## Operating Principles

A few rules that hold across every section above:

1. Named files beat conversation. If it is not on disk, it did not happen.
2. Plans before code. Plans review before plans implementation. Skip the order, ship the bug.
3. Skills must be deterministic where possible. Push logic into scripts. Reserve the LLM for judgment calls.
4. Every agent action is auditable through `plans/`, `findings/`, `progress/`, and commits. If you cannot trace it, you cannot trust it.
5. Two surfaces, one source of truth: `AGENTS.md` is canon. Everything else links to it.

The goal of the stack is simple: make agent work as legible as human work, so the team (humans and agents) can review, audit, and improve it.
