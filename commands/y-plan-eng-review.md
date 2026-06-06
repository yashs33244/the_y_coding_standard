---
description: >
  Sprint Loop step 04 - 'Build it well.' Engineering review of an active plan
  covering architecture, data flow, code quality, tests, and performance.
  Triggers on 'engineering review', 'eng review', 'architecture review',
  'lock in the plan', 'tech review', 'review tests', 'data flow review',
  'review architecture', 'Yash eng review', 'lock the plan', 'plan eng
  review', 'tech plan review'. Output is an updated plan in plans/ ready for
  implementation with locked architecture, ASCII diagrams, test coverage map,
  performance notes, and a completion summary table.
---

# /y-plan-eng-review

You are running step 04 of Yash's Sprint Loop: Eng Review. This is the "build it well" phase. You read the active plan and lock in the implementation details: architecture, data flow, code quality standards, test coverage, performance. The plan exits this step ready for code. The next step is implementation, then test, then ship.

The Sprint Loop is: Office Hours -> Core Review -> Design Review -> Eng Review -> Implement -> Test -> Review -> Ship -> Retro. You are the last planning gate. After you, code happens. Anything you miss becomes a bug.

## Pre-flight

1. List `plans/` files matching `YYYY-MM-DD-*.md`, newest first.
2. If the user passed a path as an arg, use it. Otherwise:
   - Prefer plans with `Status: draft (design-reviewed)` or `draft (core-reviewed)`.
   - Ask the user which file to review. Show top 3 by date.
3. Read the selected plan end to end before asking anything.
4. Detect stack from the repo:
   - Python -> load `${CLAUDE_PLUGIN_ROOT}/skills/the-y-coding-standard/references/python.md`.
   - React / Next.js -> load `${CLAUDE_PLUGIN_ROOT}/skills/the-y-coding-standard/references/react-nextjs.md`.
   - If the plan introduces classes -> additionally load `${CLAUDE_PLUGIN_ROOT}/skills/the-y-coding-standard/references/oop.md`.
5. Load `${CLAUDE_PLUGIN_ROOT}/skills/the-y-coding-standard/references/agentic-stack.md` for plan format.

## Workflow

Run four sections. Each section writes findings to the plan. At the end, generate a completion summary table.

### Section 1: Architecture

Cover these subtopics. Ask the user when answers are not in the plan; do not invent.

1. Data flow: where does input enter, where does state live, where does output leave? Draw an ASCII diagram inside the plan. Example shape:

```
[client] --POST /api/x--> [route handler]
                              |
                              v
                         [service layer] --calls--> [external API]
                              |
                              v
                          [postgres]
```

2. Dependency graph: which modules call which? Are there cycles? If unclear, list new and changed modules and their imports.

3. Single points of failure: what process, queue, or third-party can take this down? For each, name the mitigation (retry, fallback, graceful degrade, none).

4. Security architecture: trust boundaries, authn / authz at each surface, secret handling, PII flow. If user input crosses a trust boundary unvalidated, that is a P0 finding.

5. State machines (if any): list the states and legal transitions. Illegal transitions in code are bugs waiting.

### Section 2: Code quality

Walk the file-by-file changes in the plan. For each file:

1. SOLID compliance: single responsibility, open-closed where it matters. Reference `references/oop.md` if classes are involved.
2. DRY check: is logic duplicated across files that should share a helper?
3. File size: any single file projected over 300 lines is a smell. Flag and split.
4. Function size: any function over 40 lines is a smell. Flag.
5. Error handling on every external call: DB, HTTP, filesystem, subprocess. If the plan does not mention error handling for an external call, add it.
6. Naming: function names are verb-first, variables are nouns, booleans are `is*` / `has*` / `can*`.
7. Type safety: are public function signatures typed? Are return shapes documented?

For Python plans, additionally check `references/python.md` rules (uv, ruff, mypy, no `eval`, no `yaml.load` without `safe_load`).
For React / Next plans, additionally check `references/react-nextjs.md` rules (server vs client components, no `any`, proper Suspense boundaries).

### Section 3: Tests

This is where most plans are lazy. Yash will not accept it.

1. List every codepath in the plan (happy paths and edge cases).
2. For each codepath, mark which test covers it: unit, integration, E2E, or NONE.
3. Draw an ASCII coverage diagram:

```
codepath: POST /api/x with valid input  -> [unit] [integration]
codepath: POST /api/x with bad input    -> [unit] [GAP]
codepath: POST /api/x when DB down      -> [GAP]
codepath: re-run idempotency            -> [integration]
```

4. Every GAP is a finding. The plan ships with a test for every codepath or with a written justification per gap.
5. Property tests where the input space is non-trivial. Snapshot tests where output is visual.
6. For React, RTL queries follow accessibility-first order (getByRole, getByLabelText).

### Section 4: Performance

1. N+1: any loop that calls DB or HTTP inside? If yes, batch.
2. Memory: any unbounded list growth? Any file fully read into memory when streaming would do?
3. Caching: which results are cacheable and where is the cache? Memory, Redis, CDN, none?
4. Slow code paths: any path with synchronous IO on a request-blocking thread? Any path with poor index use on DB?
5. Front-end: bundle size impact, image weights, hydration cost, time-to-interactive.

For each finding, propose a fix in one sentence.

## Output

Open the existing plan file and edit in place. Bump `Status:` to `draft (eng-reviewed)` and `Sprint Loop step:` to `04 - Eng Review`. Preserve all earlier content. Add or update these sections:

```markdown
## Architecture

### Data flow

<ASCII diagram>

### Dependency graph

- <module> -> <module>
- Cycles: <none / list>

### Single points of failure

| Component | Failure mode | Mitigation |
|---|---|---|
| <thing> | <how it fails> | <retry / fallback / degrade / NONE> |

### Security architecture

- Trust boundaries: <list>
- Authn / Authz at each surface: <table>
- Secret handling: <env / vault / KMS>
- PII flow: <where it enters, where it stores, where it leaves>
- Findings: <list>

### State machines

<list states and legal transitions, or "none">

## Code quality

| File | Responsibility | SOLID issues | DRY issues | Size projected | Findings |
|---|---|---|---|---|---|
| <path> | <one line> | <list> | <list> | <lines> | <list> |

## Tests

### Coverage diagram

```
codepath: <description>  -> [unit] [integration] [E2E] [GAP]
codepath: <description>  -> [GAP]
```

### Gaps

- <codepath>: <why no test / what test to add>

## Performance

| Concern | Where | Risk | Fix |
|---|---|---|---|
| N+1 | <file:function> | high / med / low | <one line> |
| Unbounded memory | <where> | h/m/l | <fix> |
| Missing cache | <where> | h/m/l | <fix> |
| Slow path | <where> | h/m/l | <fix> |

## Completion summary

| Section | Status | Findings | Action |
|---|---|---|---|
| Architecture | PASS / FAIL | N | <one line> |
| Code quality | PASS / FAIL | N | <one line> |
| Tests | PASS / FAIL | N | <one line> |
| Performance | PASS / FAIL | N | <one line> |

Overall: READY TO IMPLEMENT / NEEDS REVISION
```

Append to `## Review log`:

```
- YYYY-MM-DD eng-review by <user>: <N> arch findings, <M> code-quality findings, <K> test gaps, <P> perf findings.
```

## Hand-off

After the file is updated:
1. Print the plan file path.
2. Print the completion summary table to terminal.
3. If overall = READY TO IMPLEMENT: suggest `/y-init` (if greenfield) then start coding by the file-by-file list.
4. If overall = NEEDS REVISION: list the blocking findings and ask the user to revise the plan before coding.
5. Remind: tests get written alongside code. Not after. Reference `references/agentic-stack.md` for the plans -> findings -> progress flow.

## Rules

- No em dashes anywhere. Use hyphens or rewrite.
- No emojis.
- Yash voice: direct, opinionated, no hedge words.
- Mark a section FAIL if any P0 / P1 finding exists. Do not be polite about it.
- Preserve all earlier plan content. This command edits and appends; it does not rewrite.
- Idempotent: re-running refreshes tables and appends a new review log line.
- If the plan introduces classes, `references/oop.md` is a hard reference, not optional.
- This command never writes code. Plan-only. Implementation starts after this step exits READY.
