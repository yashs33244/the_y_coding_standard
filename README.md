# the_y_coding_standard

An opinionated coding-standards plugin for Claude Code. Hard rules for Python and React/Next.js. Drop-in AGENTS.md template. Parallel governance audit inspired by Microsoft's agent-governance-toolkit.

## Install

```bash
# add the marketplace
/plugin marketplace add yashs33244/the_y_coding_standard

# install the plugin
/plugin install the-y-coding-standard
```

## What you get

| Surface | What it does |
|---|---|
| `the-y-coding-standard` skill | Aggressive auto-trigger on new code, new features, and standards-related prompts. Loads the right reference file per stack. |
| `/y-init` command | Scaffolds the agentic engineering stack into the current repo: AGENTS.md, CLAUDE.md, .claude/, .agents/, .conductor/, .cursor/, .devcontainer/, .github/, .husky/, Docs/, plans/, findings/, progress/. |
| `/y-govern` command | Dispatches three parallel sub-agents (security, audit, permissions) inspired by Microsoft's agent-governance-toolkit. Writes a findings report. |

## Reference Files

Loaded by the skill on demand:

- `references/python.md`: Python version policy (latest stable, looked up at runtime), uv + Poetry, conda envs, modularity rules (separate enums.py / constants.py / types.py), pydantic boundaries, error handling, 20+ common pitfalls.
- `references/react-nextjs.md`: Next.js App Router 14+, Server Components default, 400-line component cap, useReducer over useState explosion, centralized config, middleware patterns, Vercel AI SDK v6 defaults.
- `references/agentic-stack.md`: AGENTS.md format, the canonical folder tree, plans/findings/progress/ semantics, the Skillify 10-item promotion checklist.
- `references/governance.md`: The five governance dimensions, parallel sub-agent dispatch model, policy catalog, permission matrix template.
- `references/project-scaffold.md`: Every dotfolder Yash uses (.claude, .conductor, .cursor, .devcontainer, .github, .husky, Docs), what each one does, canonical config inside.

## Quickstart

```bash
# in any repo
/y-init           # scaffolds the agentic stack
/y-govern         # runs the parallel governance audit
```

## Standards Highlights

Python:
- Latest stable Python at scaffolding time (looked up via WebSearch).
- `uv` default, Poetry fallback, conda for env management.
- Each enums / constants / types / exceptions in its own file.
- Pydantic at API boundaries, dataclass internally.
- Error handling on every external call.
- `ruff` for lint + format. `mypy --strict`. `pytest` with 90% coverage gate.

React / Next.js:
- App Router 14+, never `pages/`.
- Server Components default, push client components to leaves.
- 400-line component hard cap.
- `useReducer` when state has 3+ related fields.
- Centralized config via `lib/config.ts` with `zod` schema.
- Middleware for cross-cutting concerns.
- Vercel AI SDK v6 by default for AI features.

Agentic Stack:
- AGENTS.md is the universal agent contract.
- plans/ for forward-looking docs, findings/ for investigations, progress/ for journals.
- Issue -> Plan -> Implement -> Test -> Review -> Ship -> Retro loop.

Governance:
- Run `/y-govern` before every release.
- Five dimensions: security, policy enforcement, auditability, compliance, agent permissions.
- Three parallel sub-agents (security, audit, permissions) inspired by Microsoft agent-governance-toolkit.
- Findings written to `findings/YYYY-MM-DD-governance.md`.

## Compatibility

- Claude Code (current).
- Python 3.13+ required for `/y-govern` scripts (uses `uv run` for the inline metadata).
- Node 20+ recommended for Next.js scaffolding.

## License

MIT.

## Inspirations

- Anthropic Claude Code skill format
- Vercel Labs agent-skills (https://github.com/vercel-labs/agent-skills)
- Microsoft agent-governance-toolkit (https://github.com/microsoft/agent-governance-toolkit)
- Microsoft AI-Engineering-Coach (https://github.com/microsoft/AI-Engineering-Coach)
- Skillify checklist pattern (Stanford agentic-workflows talk)

## Contributing

Open a PR. Run `/y-govern` first.

## Author

https://github.com/yashs33244
