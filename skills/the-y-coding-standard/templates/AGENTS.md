# AGENTS.md

<!-- TODO: Replace placeholders marked with TODO. Delete this line when done. -->

This file is the universal agent contract for this repository. Every agent surface (Claude Code, Cursor, Codex, Manus, Conductor, CI bots) reads this file first when entering the repo. It defines the stack, workflow, branching, skill routing, governance, permissions, and constraints that every contributor (human or agent) must follow.

## Project Overview

<!-- TODO: 2-3 sentence project description. What it does, who uses it, why it exists. -->

## Stack

<!-- TODO: Fill in the actual stack -->

- Language: <e.g., Python 3.13 / TypeScript 5.x>
- Framework: <e.g., FastAPI 0.115 / Next.js 15 App Router>
- Database: <e.g., Postgres 16 via Neon>
- Cache / Queue: <e.g., Redis via Upstash / Inngest>
- Deploy target: <e.g., Vercel Fluid Compute>
- AI: <e.g., Vercel AI SDK v6, Anthropic Claude>
- Observability: <e.g., Sentry, OpenTelemetry, Vercel Analytics>

## Quickstart

```bash
# clone
git clone <repo-url>
cd <repo>

# install deps
<TODO: pnpm install OR uv sync OR poetry install>

# env setup
cp .env.example .env
# TODO: fill in DATABASE_URL, ANTHROPIC_API_KEY, etc.

# db (if applicable)
<TODO: pnpm db:migrate OR uv run alembic upgrade head>

# run
<TODO: pnpm dev OR uv run python -m app>

# test
<TODO: pnpm test OR uv run pytest>

# lint + typecheck
<TODO: pnpm lint && pnpm typecheck OR uv run ruff check && uv run pyright>
```

## Repository Layout

```
.
├── AGENTS.md                  # this file. Universal agent contract.
├── CLAUDE.md                  # Claude Code overrides. Points here.
├── README.md                  # human-facing project intro.
├── .agents/
│   └── skills/                # project-local agent skills.
├── .claude/
│   ├── settings.json          # Claude Code tool permissions.
│   └── settings.local.json    # local override (gitignored).
├── .github/
│   └── workflows/             # CI: lint, type, test, deploy.
├── Docs/
│   ├── decisions/             # ADRs. One file per architectural decision.
│   └── runbooks/              # operational playbooks (incident, rollback, etc).
├── findings/                  # outputs from /y-govern, /investigate, audits.
├── plans/                     # feature plans. One file per feature.
├── progress/                  # session journals. Append-only.
├── src/ or app/               # source code.
├── tests/                     # unit, integration, e2e.
└── scripts/                   # one-off scripts. Idempotent where possible.
```

One-line per folder:

- `.agents/skills/`: project-local skills that override or extend plugin skills.
- `.claude/`: Claude Code settings. Tool allowlist and per-project hooks.
- `.github/workflows/`: CI pipelines. Lint, type, test, deploy gates.
- `Docs/decisions/`: ADRs. Permanent record of architectural choices.
- `Docs/runbooks/`: operational playbooks for incident response and rollback.
- `findings/`: governance reports, security audits, investigation outputs.
- `plans/`: pre-implementation feature plans. Reviewed before coding.
- `progress/`: session journals appended at end of every working session.
- `src/`: application source.
- `tests/`: test suites. Mirrors `src/` structure.
- `scripts/`: utility scripts. Should be idempotent.

## Workflow

The canonical loop. Every change goes through it:

Issue -> Plan -> Implement -> Test -> Review -> Ship -> Retro

1. **Issue**: tracked in <TODO: GitHub Issues / Linear>. One issue per unit of work.
2. **Plan**: write `plans/YYYY-MM-DD-<feature>.md`. Run `/plan-eng-review` before coding.
3. **Implement**: TDD where reasonable. Small commits. WIP commits allowed inside a branch.
4. **Test**: unit + integration + e2e. Coverage threshold defined in `ci.yml`.
5. **Review**: `/y-review` or external reviewer. No self-merge.
6. **Ship**: `/y-ship` opens the PR. Merge gated on green CI + reviewer approval.
7. **Retro**: `/y-retro` weekly or after every significant ship.

## Branching

- `main`: protected. PR required. Linear history. Auto-deploy to prod after manual approval.
- `feat/<short-slug>`: feature branches.
- `fix/<short-slug>`: bug fixes.
- `chore/<short-slug>`: non-functional changes (deps, docs, refactors).
- `hotfix/<short-slug>`: emergency prod fixes. PR + 1 reviewer minimum.

Commit format: [Conventional Commits](https://www.conventionalcommits.org/). Enforced by `.husky/commit-msg`.

Example: `feat(auth): add Google OAuth provider`.

## Skill Routing

When the user says X, invoke skill Y. Customize this table for the project.

| User says | Invoke |
|---|---|
| "scaffold this repo" | /y-init |
| "audit governance" | /y-govern |
| "follow standards" | the-y-coding-standard |
| "review this PR" | /review |
| "plan a feature" | /plan-eng-review |
| "ship it" | /ship |
| "investigate this bug" | /investigate |
| "weekly retro" | /y-retro |

## Coding Standards

Follow `the-y-coding-standard` plugin (https://github.com/yashs33244/the_y_coding_standard).

Hard rules:

- 400 line file limit (frontend) / 300 lines preferred (backend).
- Enums, constants, types in separate files.
- Centralized config. Never read `process.env` outside `lib/config.ts`.
- Middleware for cross-cutting concerns (auth, logging, validation).
- Server Components by default in Next.js. Client only where necessary.
- `useReducer` over `useState` when state has 3+ related fields.
- `pydantic` at boundaries, `dataclass` internally (Python).
- Error handling on every external call.
- No em dashes anywhere.
- No emojis in code.

## Governance

Run `/y-govern` before every release. It dispatches three parallel sub-agents (security, audit, permissions) and writes a report to `findings/YYYY-MM-DD-governance.md`.

Required policies:

- No secrets in code. Use `.env.example` for templates and a secret manager for prod.
- Pre-commit hooks enforce lint + type + tests.
- Branch protection on `main`.
- AI-assisted commits include `Co-Authored-By` line.
- Destructive operations require explicit human approval.
- All ADRs reviewed by at least one human before merge.

See `the-y-coding-standard/references/governance.md` for the full policy catalog.

## Agent Permissions

| Surface | Read code | Write code | Run tests | Deploy staging | Deploy prod | Access secrets |
|---|---|---|---|---|---|---|
| Claude Code | yes | yes | yes | with approval | NEVER | dev only |
| Cursor | yes | yes | yes | no | NEVER | dev only |
| Codex CLI | yes | review-only | yes | no | NEVER | none |
| Manus | yes | with approval | yes | no | NEVER | none |
| Conductor | yes | yes | yes | with approval | NEVER | dev only |
| CI bot | yes | no | yes | yes | with manual approval | scoped per workflow |

## Constraints

Agents MUST NOT, without explicit human approval per action:

- Push to remote (`git push`, `git push --force`).
- Run `rm -rf` outside the workspace.
- Run prod migrations.
- Deploy to prod.
- Rotate or read prod secrets.
- Delete branches.
- Force-push to any branch.
- Disable CI checks or branch protection.
- Merge their own PRs.
- Commit `.env`, credentials, or any file matching `*secret*` / `*key*`.

## Filing Rules (where information lives)

| Information | Lives in |
|---|---|
| Architecture decisions | `Docs/decisions/` (ADRs) |
| Feature plans | `plans/` |
| Investigation outputs | `findings/` |
| Session journals | `progress/` |
| Runbooks | `Docs/runbooks/` |
| Skills | `.agents/skills/` |
| Standards | `AGENTS.md` (this file) + linked references |
| Secrets | secret manager only. Never in repo. |

## Ownership

<!-- TODO: Fill in -->

- Owner: <name>
- Slack / Discord: <handle or channel>
- Oncall: <rotation link>
- Escalation: <name + contact>

## Last reviewed

<!-- TODO: date of last update (YYYY-MM-DD) -->
