# Project Scaffold Reference

The set of dotfolders and config files every Yash project gets. Each folder has one job. Skip none.

## The Folder Set

| Folder | Job |
|---|---|
| `.claude/` | Claude Code project config: commands, skills, settings, hooks |
| `.claude-plugin/` | When shipping a Claude Code plugin from this repo: plugin.json + marketplace.json |
| `.agents/skills/` | Skills usable by any agent surface (Claude, Cursor, Codex) |
| `.conductor/` | Conductor parallel-workspace config |
| `.cursor/` | Cursor rules and prompts |
| `.devcontainer/` | Dockerized dev env, reproducible across machines |
| `.github/` | Workflows, issue templates, PR templates, CODEOWNERS |
| `.husky/` | Git hooks (pre-commit, commit-msg, pre-push) |
| `Docs/` | Human-facing documentation |
| `plans/`, `findings/`, `progress/` | The agentic stack folders (see agentic-stack.md) |
| `tests/` | Real project tests |

## `.claude/`

Structure:
```
.claude/
  commands/                 # slash commands for this repo
    deploy.md
    review.md
  skills/                   # symlinks or full skills installed for the repo
  settings.json             # shared team settings (checked in)
  settings.local.json       # per-developer overrides (gitignored)
  hooks/                    # bash hooks fired on tool events
    on-stop.sh
```

settings.json minimum:
```json
{
  "permissions": {
    "allow": [
      "Bash(pnpm:*)",
      "Bash(uv:*)",
      "Bash(git status:*)",
      "Bash(git diff:*)",
      "Bash(git log:*)"
    ],
    "deny": [
      "Bash(rm -rf:*)",
      "Bash(git push --force:*)"
    ]
  }
}
```

settings.local.json is gitignored. Used for per-dev token-bearing configs.

## `.claude-plugin/`

Only present in repos that ship a plugin to the Claude Code marketplace.

```
.claude-plugin/
  plugin.json
  marketplace.json
```

plugin.json declares: name, description, version, author, license, skills[], commands[].
marketplace.json declares: name, owner, metadata, plugins[].

See `templates/` in this skill for working examples.

## `.agents/skills/`

Agent-surface-agnostic skills used by anyone in the team. Structure:

```
.agents/skills/<skill-name>/
  SKILL.md
  scripts/
  tests/
  references/
```

Differs from `.claude/skills/` in that `.agents/skills/` is portable across Cursor, Codex, etc. `.claude/skills/` may include Claude-Code-specific features.

## `.conductor/`

Conductor lets you run parallel agents in isolated worktrees.

```
.conductor/
  config.json               # worktree base path, branch naming, default agent
  prompts/                  # reusable agent prompt templates
```

config.json example:
```json
{
  "worktree_base": ".conductor-worktrees",
  "branch_prefix": "agent/",
  "default_agent": "claude",
  "max_parallel": 4
}
```

## `.cursor/`

Cursor rules and prompts.

```
.cursor/
  rules                     # legacy single-file rules
  rules/                    # newer multi-file rules (cursor 0.45+)
    01-style.md
    02-architecture.md
    03-testing.md
```

Cursor reads `.cursor/rules/*.md` in lexical order. Use numeric prefixes.

Minimum content:
- Style baseline matching this repo's standards.
- Reference AGENTS.md as the source of truth.
- Cursor-specific behavior overrides.

## `.devcontainer/`

Reproducible dev env via Docker + VS Code devcontainer spec.

```
.devcontainer/
  devcontainer.json
  Dockerfile
  docker-compose.yml        # if multi-service
  post-create.sh            # provisioning script
```

devcontainer.json minimum:
```json
{
  "name": "the-y-project",
  "build": { "dockerfile": "Dockerfile" },
  "features": {
    "ghcr.io/devcontainers/features/git:1": {},
    "ghcr.io/devcontainers/features/node:1": { "version": "lts" },
    "ghcr.io/devcontainers/features/python:1": { "version": "3.13" }
  },
  "postCreateCommand": "bash .devcontainer/post-create.sh",
  "customizations": {
    "vscode": {
      "extensions": [
        "ms-python.python",
        "charliermarsh.ruff",
        "dbaeumer.vscode-eslint",
        "esbenp.prettier-vscode"
      ]
    }
  }
}
```

post-create.sh installs deps, hooks, sets up env.

## `.github/`

```
.github/
  CODEOWNERS
  ISSUE_TEMPLATE/
    bug.yml
    feature.yml
  PULL_REQUEST_TEMPLATE.md
  workflows/
    ci.yml                  # lint + type + test on every PR
    deploy.yml              # deploy on main merge
    security.yml            # weekly dep scan
    governance.yml          # weekly /y-govern run
  dependabot.yml
```

CODEOWNERS minimum:
```
* @yashs33244
.github/ @yashs33244
Docs/ @yashs33244
```

ci.yml essential gates (any language):
- Lint
- Type check
- Test with coverage threshold
- Build artifact (when applicable)

Branch protection on main:
- Require PR
- Require status checks (ci must pass)
- Require linear history
- No force-push

## `.husky/`

Pre-commit hooks. Stop bad commits at the source.

```
.husky/
  pre-commit                # lint-staged, type check
  commit-msg                # conventional commit format check
  pre-push                  # full test suite
```

pre-commit example (JS/TS project):
```bash
#!/usr/bin/env sh
. "$(dirname -- "$0")/_/husky.sh"

pnpm exec lint-staged
pnpm exec tsc --noEmit
```

pre-commit example (Python project):
```bash
#!/usr/bin/env sh
uv run ruff check --fix
uv run ruff format
uv run mypy src/
```

commit-msg uses commitlint:
```bash
#!/usr/bin/env sh
. "$(dirname -- "$0")/_/husky.sh"
pnpm exec commitlint --edit $1
```

commitlint.config.cjs:
```js
module.exports = { extends: ['@commitlint/config-conventional'] }
```

Conventional commit prefixes: feat, fix, chore, docs, refactor, test, perf, ci, build, revert.

## `Docs/`

Human-facing docs. Document everything.

```
Docs/
  README.md                 # docs index
  architecture.md           # system overview + ASCII diagrams
  decisions/                # ADRs
    0001-use-fluid-compute.md
    0002-postgres-over-mongo.md
  runbooks/
    deploy.md
    incident-response.md
    db-migration.md
  api/                      # generated or hand-written API docs
  setup.md                  # onboarding for new devs
  testing.md                # how to run + write tests
```

ADR format (Architecture Decision Record):
```markdown
# 0001: Use Fluid Compute over Edge Functions

Date: YYYY-MM-DD
Status: accepted

## Context
<problem space>

## Decision
<what we decided>

## Consequences
<positive + negative>

## Alternatives considered
- <alt> -> why not
```

## Bootstrap Order (which folders to create first)

When `/y-init` runs, create in this order:

1. `README.md` (stub)
2. `AGENTS.md` (from template)
3. `CLAUDE.md` (from template)
4. `.github/workflows/ci.yml`
5. `.husky/pre-commit`
6. `.devcontainer/devcontainer.json`
7. `.claude/settings.json`
8. `.cursor/rules/01-style.md`
9. `.conductor/config.json`
10. `Docs/architecture.md`, `Docs/decisions/`, `Docs/runbooks/`
11. `plans/`, `findings/`, `progress/`, `.agents/skills/`
12. `.gitignore` (with the right exclusions)
13. `tests/`

## .gitignore Essentials

```
# env
.env
.env.local
.env.*.local

# deps
node_modules/
__pycache__/
.venv/
venv/

# build
dist/
build/
.next/
.turbo/

# editor
.DS_Store
.vscode/
.idea/

# coverage
coverage/
.coverage
htmlcov/

# claude / agents
.claude/settings.local.json
.conductor-worktrees/
```

## .editorconfig

```
root = true

[*]
charset = utf-8
end_of_line = lf
indent_style = space
indent_size = 2
insert_final_newline = true
trim_trailing_whitespace = true

[*.py]
indent_size = 4

[Makefile]
indent_style = tab
```

## Per-Language Lockfile Rules

| Stack | Lockfile (check in) |
|---|---|
| Node (pnpm) | pnpm-lock.yaml |
| Node (npm) | package-lock.json |
| Node (yarn) | yarn.lock |
| Python (uv) | uv.lock |
| Python (poetry) | poetry.lock |
| Rust | Cargo.lock |
| Go | go.sum |

Never gitignore a lockfile in a deployed project.

## Folder Counts

Count file types as a sanity check on completeness. After `/y-init` on a fresh repo, expect:
- 1 AGENTS.md
- 1 CLAUDE.md
- 1 .gitignore
- 1 .editorconfig
- At least 1 file each in: .github/, .husky/, .devcontainer/, .claude/, .cursor/, .conductor/, Docs/
- Empty (with .gitkeep) folders for: plans/, findings/, progress/, .agents/skills/
