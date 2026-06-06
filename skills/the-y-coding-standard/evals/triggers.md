# Trigger Evals

Manual evals for verifying that the `the-y-coding-standard` skill fires on the expected prompts and stays quiet on the wrong ones. Each row is a test case.

## Format

| # | User says | Expected behavior |
|---|---|---|
| 1 | "Start a new Next.js project" | the-y-coding-standard fires, references/react-nextjs.md and references/project-scaffold.md load |
| 2 | "Set up a Python FastAPI service" | the-y-coding-standard fires, references/python.md loads |
| 3 | "Review this Python file" | the-y-coding-standard fires, references/python.md loads |
| 4 | "Scaffold the repo" | /y-init triggers |
| 5 | "Audit governance" | /y-govern triggers |
| 6 | "Run the governance pass" | /y-govern triggers |
| 7 | "Make this code production ready" | the-y-coding-standard fires |
| 8 | "Apply best practices to this PR" | the-y-coding-standard fires |
| 9 | "Structure this module properly" | the-y-coding-standard fires |
| 10 | "Make this modular" | the-y-coding-standard fires |
| 11 | "What's the weather" | the-y-coding-standard does NOT fire |
| 12 | "Write me a poem" | the-y-coding-standard does NOT fire |
| 13 | "Set up an AGENTS.md template" | the-y-coding-standard fires (loads agentic-stack.md) |
| 14 | "Add a pre-commit hook" | the-y-coding-standard fires (loads project-scaffold.md) |
| 15 | "Check for leaked secrets" | /y-govern fires |
| 16 | "Audit npm dependencies" | /y-govern fires |
| 17 | "Create a useReducer-based form" | the-y-coding-standard fires (loads react-nextjs.md) |
| 18 | "Set up uv and conda for a Python project" | the-y-coding-standard fires (loads python.md) |
| 19 | "Add a Husky pre-commit" | the-y-coding-standard fires (loads project-scaffold.md) |
| 20 | "Add ADRs to this repo" | the-y-coding-standard fires (loads project-scaffold.md and agentic-stack.md) |
| 21 | "Is this class SRP-compliant" | the-y-coding-standard fires (loads oop.md) |
| 22 | "Should I extend or compose here" | the-y-coding-standard fires (loads oop.md) |
| 23 | "Review this for SOLID violations" | the-y-coding-standard fires (loads oop.md) |
| 24 | "Refactor this inheritance hierarchy" | the-y-coding-standard fires (loads oop.md) |
| 25 | "Apply dependency injection here" | the-y-coding-standard fires (loads oop.md) |
| 26 | "Design a polymorphic discount engine" | the-y-coding-standard fires (loads oop.md) |
| 27 | "Check Law of Demeter on this method chain" | the-y-coding-standard fires (loads oop.md) |
| 28 | "Build a Node CLI" | the-y-coding-standard fires (loads javascript-typescript.md) |
| 29 | "Write a TypeScript library" | the-y-coding-standard fires (loads javascript-typescript.md) |
| 30 | "Set up a Spring Boot service" | the-y-coding-standard fires (loads java-spring.md and oop.md) |
| 31 | "Add a REST controller in Java" | the-y-coding-standard fires (loads java-spring.md and oop.md) |
| 32 | "Write a C++ class for vector ops" | the-y-coding-standard fires (loads cpp.md and oop.md) |
| 33 | "Set up CMake for this project" | the-y-coding-standard fires (loads cpp.md) |
| 34 | "Design a users table in Postgres" | the-y-coding-standard fires (loads database-postgres.md) |
| 35 | "Write a Drizzle migration" | the-y-coding-standard fires (loads database-postgres.md) |
| 36 | "Add an index to speed up this query" | the-y-coding-standard fires (loads database-postgres.md) |
| 37 | "Set up pgvector for embeddings" | the-y-coding-standard fires (loads database-postgres.md) |

## How to run manually

For each row, start a fresh Claude Code session with the plugin installed, type the user prompt, and observe whether the expected skill/command activates and which reference files (if any) are loaded.

## How to run with automation

(Future) Use `evals` runner that simulates each prompt and verifies the SKILL.md is loaded into context and the right references are referenced. v1: manual only.

## Pass criteria

- 100% of POSITIVE cases (rows where skill should fire) trigger the skill.
- 100% of NEGATIVE cases (rows where skill should NOT fire) leave the skill quiet.
- Reference file loading happens lazily (only for the matched topic).
