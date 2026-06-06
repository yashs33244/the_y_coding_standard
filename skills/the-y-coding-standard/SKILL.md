---
name: the-y-coding-standard
description: >
  MUST USE whenever the user starts a new project, scaffolds a repo, creates a
  new feature, module, service, or package, or creates any `.py`, `.ts`, `.tsx`,
  `.js`, `.jsx`, or `.sql` file. MUST USE when the user mentions Next.js,
  FastAPI, Django, Flask, React, Python, TypeScript, Postgres, Prisma, Drizzle,
  SQLAlchemy, App Router, Server Components, or AI SDK. MUST USE when the user
  says "best practices", "production ready", "structure this properly", "make
  this modular", "follow standards", "set up project", "scaffold", "init repo",
  "bootstrap", "lay this out", "organize this code", "split this file", "review
  this code", "audit this", "is this clean", "SOLID", "OOP", "object-oriented",
  "design pattern", "inheritance", "composition", "polymorphism", "encapsulation",
  "abstraction", "SRP", "OCP", "LSP", "ISP", "DIP", "DRY", "KISS", "YAGNI",
  "Law of Demeter", "dependency injection", or "should I extend or compose".
  MUST USE before generating
  boilerplate, before suggesting a folder layout, before writing the first
  module of any new repo, and before any refactor that touches file structure.
  This is Yash Singh's personal opinionated standard - apply silently while
  coding, do not lecture the user about the rules. Triggers on agent-governance,
  AGENTS.md, plans/findings/progress/skills folders, .claude, .conductor,
  .cursor, .devcontainer, .husky, and any request to "make this an agentic
  repo". If in doubt, load this skill - the cost of missing it is wrong defaults
  that the user will reject.
---

# the_y_coding_standard

Yash Singh's opinionated standards for Python and React/Next.js development, the agentic engineering stack (AGENTS.md + folder layout), and agent governance. Hard-opinionated for v1. Personal-style, no diplomacy. This skill encodes the defaults Yash expects on every project he touches - apply them silently while writing code, surface them only when reviewing or auditing.

## Workflow

- For new code: identify the stack, load the matching reference(s) from `references/`, apply silently while writing. Don't lecture the user about the rules; just follow them.
- For audits/refactors: read code thoroughly, load the matching reference(s), produce a structured audit (what violates, why it matters, what to change).
- For project scaffolding: run the `/y-init` command or apply `references/agentic-stack.md` and `references/project-scaffold.md`.
- For agent-governance audits: run `/y-govern`.

## Reference Index (load only what's relevant)

| Context | Reference |
|---|---|
| Python (any framework: FastAPI, Django, Flask, scripts) | `references/python.md` |
| React / Next.js / frontend | `references/react-nextjs.md` |
| Object-oriented design: SOLID, OOP pillars, clean-code principles, relationship types (any class-heavy code) | `references/oop.md` |
| AGENTS.md, folder structure for agent-driven repos, plans/findings/progress/skills | `references/agentic-stack.md` |
| Agent governance, security, audit, permissions | `references/governance.md` |
| Project scaffolding: .claude, .conductor, .cursor, .devcontainer, .husky, .github, Docs/ | `references/project-scaffold.md` |

Load a reference only when its context actually applies. Do not load all six at once. If the user is writing a React component, load `react-nextjs.md` and stop. If the diff is class-heavy or the user asks about SOLID, load `oop.md` alongside the stack reference.

## Universal Rules (override language defaults on conflict)

### File length

- HARD LIMIT: 400 lines per file. If a file approaches 400 lines, split it. Frontend industry standard.
- Components: 400 lines max (matches React community guidance).
- Backend services / classes: 300 lines preferred, 400 hard cap.
- One file = one responsibility you can describe in one sentence.

### Modularity rules

- Enums go in their own file(s): `enums.py` / `enums.ts`.
- Constants go in their own file(s): `constants.py` / `constants.ts`.
- Types/interfaces go in `types.py` / `types.ts`.
- No mixing of enums, constants, business logic, and types in a single file.

### Naming

- Self-documenting names. `getUserByEmail` beats `getUser2`. `fetchActiveSubscriptions` beats `getSubs`.
- No abbreviations except `id`, `url`, `http`, `db`, `ctx`, `api`, `ui`.
- Booleans: prefix with `is`, `has`, `can`, `should`, `did`.

### Design principles

- SOLID. DRY (abstract on the 3rd occurrence). KISS. Separation of concerns.
- Centralized config. Environment values come from one place (`config.py` / `lib/config.ts`).
- Middleware for cross-cutting concerns. Don't repeat validation, auth, logging inline in every handler.
- Error handling is non-negotiable. Every external call (HTTP, DB, filesystem, LLM) has explicit error paths. No silent swallows.

### Comments

- Comments explain WHY, not WHAT. Code names explain WHAT.
- No commented-out code in commits. Delete it.
- Document non-obvious invariants and external constraints.

### Folder organization

- Organize by feature/domain, not by type. `users/` not `models/`.
- Small projects (under 5 features) may use flat type-based layout.

## How this skill behaves

- When triggered by new code: silently apply the rules, never lecture.
- When triggered by review: produce a structured audit, file by file.
- When the user says `/y-init`: scaffold the agentic stack into the current repo.
- When the user says `/y-govern`: run the parallel governance pass.

## Python version policy

This skill REQUIRES the latest stable Python release. Before writing Python code or scaffolding a Python project, use the WebSearch tool to look up the current latest stable Python release (e.g., search "latest stable Python release"). Use that version in `pyproject.toml`, `.python-version`, and `README.md`. Do not hardcode a version in this skill; always look it up at runtime.

## React/Next.js posture

- Always App Router (Next.js 14+).
- Server Components by default; mark client only when needed.
- Prefer `useReducer` over multiple `useState` calls when state shape grows (more than 3 related useState entries is a smell).
- Latest React/Next.js hooks. Use `useActionState`, `useOptimistic`, `useFormStatus` where they apply.
- Vercel-native patterns: AI SDK v6 default for AI features, AI Gateway for multi-provider, Server Actions for mutations.

## Yash's non-negotiables

- No em dashes anywhere. Use a regular hyphen or rewrite.
- No emojis in code, comments, or files unless explicitly requested.
- Document everything. `Docs/` folder per project.
- `AGENTS.md` is the contract. Every new repo gets one. See `templates/AGENTS.md`.
- Pre-commit hooks via Husky on every JS/TS project. Pre-commit via `pre-commit` (Python) on every Python project.
