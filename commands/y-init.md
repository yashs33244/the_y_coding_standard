---
description: Scaffold the_y_coding_standard agentic engineering stack into the current repo. Creates AGENTS.md, CLAUDE.md, the canonical folder tree (.claude/, .agents/, .conductor/, .cursor/, .devcontainer/, .github/, .husky/, Docs/, plans/, findings/, progress/), .gitignore, .editorconfig, and stub configs. Idempotent - safe to re-run.
---

# /y-init

You are scaffolding the_y_coding_standard agentic engineering stack into the current working directory.

## Pre-flight

1. Run `pwd` and confirm the working directory with the user via a single concise sentence. Format: "Scaffolding into: <pwd>. Confirm?". If they decline, stop.
2. Check if the directory is a git repo. If not, ask whether to `git init`.
3. Check for existing files. If `AGENTS.md`, `CLAUDE.md`, or any target dotfolder already exists, list them and ask whether to (a) skip those and continue or (b) abort. Never overwrite without consent.

## Detect Stack

Detect what's in the repo:
- `package.json` -> Node project (check for next, react, vue in dependencies).
- `pyproject.toml` / `requirements.txt` -> Python project.
- `Cargo.toml` -> Rust.
- `go.mod` -> Go.
- Empty directory -> greenfield.

Use the detection to inform the AGENTS.md stack section and the .husky pre-commit hook.

## Bootstrap Order

Create files in this exact order. Skip any the user said to keep.

1. `README.md` if missing: minimal stub with project name, setup, and a pointer to AGENTS.md.
2. `AGENTS.md` from the plugin template at `${CLAUDE_PLUGIN_ROOT}/skills/the-y-coding-standard/templates/AGENTS.md`. If `${CLAUDE_PLUGIN_ROOT}` is unset, fall back to the plugin install path you can detect from the slash command's location. Substitute project name into the TODO markers where you can detect it; leave others.
3. `CLAUDE.md` from the plugin template at `${CLAUDE_PLUGIN_ROOT}/skills/the-y-coding-standard/templates/CLAUDE.md`.
4. `.gitignore` covering: env files, node_modules, __pycache__, .venv, dist/build, .next, .DS_Store, .vscode/, .idea/, coverage, .claude/settings.local.json, .conductor-worktrees/.
5. `.editorconfig` (charset utf-8, lf, indent 2 spaces, 4 for Python).
6. Folder tree (empty + .gitkeep where needed):
   - `.claude/commands/`
   - `.claude/skills/`
   - `.claude/hooks/`
   - `.claude/settings.json` (minimal allow/deny set)
   - `.claude-plugin/` (empty + .gitkeep, only if user is shipping a plugin)
   - `.agents/skills/`
   - `.conductor/config.json` (with sensible defaults)
   - `.cursor/rules/01-style.md` (pointer to AGENTS.md)
   - `.devcontainer/devcontainer.json` (matched to detected stack)
   - `.devcontainer/Dockerfile` (matched to detected stack)
   - `.devcontainer/post-create.sh`
   - `.github/workflows/ci.yml` (matched to detected stack)
   - `.github/CODEOWNERS` (empty placeholder)
   - `.github/PULL_REQUEST_TEMPLATE.md`
   - `.husky/pre-commit` (matched to detected stack)
   - `.husky/commit-msg` (commitlint, only if Node)
   - `Docs/architecture.md` (stub with one ASCII diagram placeholder)
   - `Docs/decisions/.gitkeep`
   - `Docs/decisions/0001-template.md` (ADR template)
   - `Docs/runbooks/.gitkeep`
   - `plans/.gitkeep`
   - `findings/.gitkeep`
   - `progress/.gitkeep`
   - `tests/.gitkeep` if no tests directory exists

## .claude/settings.json content

Minimum:
```json
{
  "permissions": {
    "allow": [
      "Read", "Write", "Edit",
      "Bash(git status:*)", "Bash(git diff:*)", "Bash(git log:*)",
      "Bash(git add:*)", "Bash(git commit:*)",
      "Bash(pnpm:*)", "Bash(npm:*)", "Bash(uv:*)",
      "Bash(ls:*)", "Bash(cat:*)", "Bash(find:*)", "Bash(grep:*)"
    ],
    "deny": [
      "Bash(rm -rf:*)",
      "Bash(git push --force:*)",
      "Bash(sudo:*)"
    ]
  }
}
```

## .conductor/config.json content

```json
{
  "worktree_base": ".conductor-worktrees",
  "branch_prefix": "agent/",
  "default_agent": "claude",
  "max_parallel": 4
}
```

## .husky/pre-commit content

For Node:
```bash
#!/usr/bin/env sh
. "$(dirname -- "$0")/_/husky.sh"
pnpm exec lint-staged
pnpm exec tsc --noEmit
```

For Python:
```bash
#!/usr/bin/env sh
uv run ruff check --fix
uv run ruff format
uv run mypy src/ || true
```

For mixed: combine both, fail fast on either.

After writing the file, `chmod +x .husky/pre-commit` via Bash.

## .github/workflows/ci.yml content

Match the detected stack. For Node, use pnpm + node setup + lint + typecheck + test. For Python, use uv + ruff + mypy + pytest. For mixed, run both in parallel jobs.

Provide a baseline that the user can extend.

## .devcontainer/devcontainer.json

Match stack. Features: ghcr.io/devcontainers/features/git, node (lts) and/or python (latest), common-utils. Post-create runs install + husky install.

## Docs/decisions/0001-template.md

Provide the ADR template (Context, Decision, Consequences, Alternatives).

## Final Step

After all files are created:
1. Print a summary table of created files.
2. Suggest next steps: fill TODOs in AGENTS.md, install hook deps (`pnpm install` or `uv sync`), run `pnpm exec husky install` if Node.
3. Offer to run `/y-govern` immediately for a baseline audit.

## Rules
- Never overwrite existing files without explicit consent.
- All written content has no em dashes. Use hyphens or rewrite.
- No emojis.
- Idempotent: re-running `/y-init` after partial completion finishes the remaining files.
