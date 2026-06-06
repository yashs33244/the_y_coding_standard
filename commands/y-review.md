---
description: Sprint Loop step 05. Trigger when the user says "review this PR", "review the diff", "review my code", "audit this change", "did we build it", "code review", "Yash review", "review against the plan", "P0 P1 P2", or any variant asking for a code review. This is the "Did we build it?" gate. Reviews the diff against the locked plan AND against the_y_coding_standard. Produces findings/YYYY-MM-DD-review.md with P0/P1/P2/P3 labeled findings and a ship/hold recommendation. Run this BEFORE /y-qa and BEFORE /y-ship. No exceptions.
---

## /y-review

The "Did we build it?" gate. Step 05 of the Sprint Loop. After /y-build finishes you stop and ask: does the code on disk actually match the locked plan, and does it meet the_y_coding_standard? This command answers both. Plan compliance first, standards second, OOP third, tests fourth. Every finding gets a severity label and a file:line pointer. The output is a written report at `findings/YYYY-MM-DD-review.md` and a one-screen summary with a ship/hold recommendation.

## Pre-flight

Before reviewing, confirm:

1. We are in a git repo. If not, abort and tell the user to initialize one.
2. There is an active plan in `plans/`. If none, ask the user which plan this code implements. If they say "no plan", that is itself a P0 finding (we shipped without a plan).
3. Today's date is known. Use it to name the findings file.
4. The `findings/` folder exists. If not, create it.

Ask the user once: "Reviewing uncommitted changes, current branch vs main, or a specific path?" Default to current branch vs main if the user does not answer.

## Workflow

### 1. Identify the diff scope

Run one of:

- `git diff` for uncommitted changes.
- `git diff main...HEAD` for current branch vs main.
- `git diff <ref>...HEAD -- <path>` for a scoped path.

Capture the file list. If the diff is empty, stop and report "Nothing to review."

### 2. Locate the active plan

Look in `plans/` for the most recent plan file or the one the user pointed to. Read it. Extract:

- The stated scope (what we said we would build).
- The acceptance criteria (how we said we would know it works).
- The out-of-scope list (what we said we would NOT touch).

If the plan is missing or status is not `ready-to-ship` or `in-progress`, flag this in the report.

### 3. Load the right reference

Based on the files in the diff:

- Any `.py` files: read `references/python.md`.
- Any `.tsx`, `.jsx`, `.ts`, `.js` in a React/Next.js project: read `references/react-nextjs.md`.
- Any class definitions touched: read `references/oop.md`.
- Folder structure changes (new top-level dirs, moved modules): read `references/project-scaffold.md`.

Load all that apply. Do not skip this step.

### 4. Review in four passes

**Pass 1: Plan compliance.**

For each item in the plan's scope, find the code that implements it. For each item in the diff, find the plan line that asked for it. Any code that is not in the plan is scope creep. Any plan item with no code is incomplete. Both are findings.

**Pass 2: Standards compliance.**

Run through the_y_coding_standard checklist on every changed file:

- File size under 400 lines. Anything over is a P1.
- Enums, constants, and types live in their own files. Inline magic strings are P2.
- Every external call (network, disk, subprocess, db) has explicit error handling. Missing is P1.
- No em dash unicode character (U+2014). Any hit is a P2 (auto-fixable).
- Configuration is centralized. Hardcoded URLs, ports, secrets are P0.
- Imports are sorted and grouped. Inconsistent is P3.

**Pass 3: OOP review (only if classes were touched).**

Apply `references/oop.md`:

- Single Responsibility: one class, one reason to change. Violations are P1.
- Open/Closed: extension over modification. Violations are P2.
- Liskov: subclasses substitute base classes cleanly. Violations are P1.
- Interface segregation: no fat interfaces. Violations are P2.
- Dependency inversion: depend on abstractions. Violations are P1.
- Composition over inheritance. New inheritance chains are P2.
- Inheritance depth at most two. Depth three or more is P0.
- Law of Demeter: do not reach through objects. Violations are P2.

**Pass 4: Tests.**

For every new code path, find the test that covers it. For every branch (if/else, try/except, switch), find at least one test per branch. Missing test for a happy path is P1. Missing test for an error branch is P1. Missing test for a boundary is P2. No tests added when production code was added is P0.

### 5. Label and locate every finding

Every finding gets:

- A severity: P0 (block ship), P1 (must-fix before merge), P2 (should-fix this sprint), P3 (nice-to-have).
- A file path and line number.
- A one-sentence statement of the problem.
- A one-sentence statement of the fix.

No vague findings. No "code could be cleaner" entries. Either it is a concrete thing or it does not go in the report.

### 6. Write the report

Create `findings/YYYY-MM-DD-review.md` with this structure:

```
# Review YYYY-MM-DD

Plan: plans/<plan-file>.md
Diff scope: <what was reviewed>
Files changed: <count>
Lines changed: <+N / -M>

## Recommendation
SHIP | HOLD

## Summary
P0: <count>
P1: <count>
P2: <count>
P3: <count>

## Pass 1: Plan compliance
- [P?] file:line - problem - fix

## Pass 2: Standards compliance
- [P?] file:line - problem - fix

## Pass 3: OOP review
- [P?] file:line - problem - fix

## Pass 4: Tests
- [P?] file:line - problem - fix

## Notes
<any context the next reader needs>
```

Recommendation is HOLD if any P0 or P1 exist. Otherwise SHIP.

### 7. Print the one-screen summary

After writing the file, print to stdout:

- Counts per severity.
- Top 3 findings by severity (P0 first).
- The recommendation.
- The path to the full report.

## Output

`findings/YYYY-MM-DD-review.md` with the full four-pass report.

## Hand-off

- If recommendation is SHIP: hand off to `/y-qa`.
- If recommendation is HOLD: hand off back to `/y-build` with the fix list.

## Rules

- Eat the dog food. This command file itself must obey the_y_coding_standard.
- Never invent findings to look thorough. Empty sections are fine.
- Never skip the plan-compliance pass. It is the most important one.
- Never use the em dash character. Use a hyphen or rewrite.
- Always include file:line for every finding.
- Always write the report file, even if there are zero findings. A clean review is still a record.
