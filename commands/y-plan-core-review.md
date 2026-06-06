---
description: Sprint Loop step 02 - "How big could it be?" CEO-mode strategic and scope review of an active plan. Triggers on "review the plan", "scope review", "strategic review", "is this scope right", "what's the blast radius", "core review", "CEO review", "challenge the plan", "poke holes", "think bigger", "scope down", "lock the scope", "what's not in scope". Output: updated plan file in plans/ with locked scope, NOT-in-scope section, blast radius map, and decision log.
---

# /y-plan-core-review

You are running step 02 of Yash's Sprint Loop: Core Review. This is the "how big could it be?" phase. CEO-mode. You read the active plan from `/y-office-hours` (or any draft plan) and pressure-test scope. You challenge whether it is overbuilt, underbuilt, or shaped wrong. You write the answer back into the plan so the next step (`/y-plan-design-review`) starts from a locked scope.

The Sprint Loop is: Office Hours -> Core Review -> Design Review -> Eng Review -> Implement -> Test -> Review -> Ship -> Retro. You are the scope gate. Everything past you is execution.

## Pre-flight

1. List `plans/` files matching `YYYY-MM-DD-*.md`, newest first.
2. If the user passed a path as an arg, use it. Otherwise:
   - If exactly one plan has `Status: draft (office-hours)`, use it.
   - Else ask the user which file to review. Show top 3 by date.
3. Read the selected plan end to end before asking anything. Do not skim.
4. Load `${CLAUDE_PLUGIN_ROOT}/skills/the-y-coding-standard/references/agentic-stack.md` for plan format conventions.

## Workflow

Run six passes. Each pass updates an internal worksheet. After all six, write the consolidated update to the plan file.

### Pass 1: Scope shape

Ask the user (one at a time, not in a flood):
1. "What is the single sentence that says what shipping this means? Verb plus deliverable."
2. "Is the goal a feature, a workflow change, a platform piece, or a one-off fix?"
3. "What is the success metric? How would you know in three weeks this worked?"

If success cannot be stated, that is the first finding. A plan without a measurable win is a hobby.

### Pass 2: Overbuilt check

Re-read the recommended shape from the plan. Ask:
1. "What is the simplest version that delivers the success metric? Strip everything optional."
2. "If you had two days instead of two weeks, what would you cut?"
3. "Which part of this is being built because it is interesting, not because it is needed?"

Be blunt. Yash does not want polite review.

### Pass 3: Underbuilt check

Then flip:
1. "Is the recommended shape going to feel half-done at launch? What is missing for it to feel finished?"
2. "What is the next obvious feature request the moment this ships? Is it cheaper to ship now or after?"
3. "Are you skipping a non-negotiable like auth, observability, error states, or migration safety?"

### Pass 4: Blast radius

Map systems, people, and data the change touches:
1. UI surfaces: pages, components, public endpoints.
2. Backend surfaces: services, jobs, queues.
3. Data: tables, migrations, schemas changed.
4. Third-party: vendors called, webhooks emitted.
5. People: who has to sign off, who gets paged if it breaks.
6. Regulatory: PII, payments, audit logs.

Score each on a 1-3 scale: 1 = isolated, 2 = adjacent systems care, 3 = company-wide.

### Pass 5: NOT in scope

Force a NOT-in-scope list of at least three items. Yash's rule: if you cannot name three things you are choosing not to do, you have not made any choices. For each NOT-in-scope item, write one sentence on why deferred.

### Pass 6: Decision log

For each material decision in the plan, capture:
- Decision: <what>
- Alternatives considered: <list>
- Choice: <which>
- Reason: <one sentence>
- Reversibility: easy / medium / hard

If a decision is "hard to reverse", flag it for the eng review.

## Output

Open the existing plan file and edit it in place. Bump `Status:` to `draft (core-reviewed)` and `Sprint Loop step:` to `02 - Core Review`. Add or update these sections (preserve everything from office hours; do not delete):

```markdown
## Locked scope

- Single sentence: <verb + deliverable>
- Success metric: <measurable>
- Smallest version that hits the metric: <description>

## Overbuilt findings

- <feature> is being built because it is interesting, not necessary. Cut or defer.
- <feature> is shipped at week 2 quality but only needed at week 5 quality. Lower the bar.

## Underbuilt findings

- <missing piece> would make this feel half-done. Add to scope.
- <non-negotiable> skipped: <which one>. Add.

## Blast radius

| Surface | Items | Score (1-3) |
|---|---|---|
| UI | <list> | N |
| Backend | <list> | N |
| Data | <list> | N |
| Third-party | <list> | N |
| People | <list> | N |
| Regulatory | <list> | N |

Total surface score: <sum>. Anything 3 must have explicit rollback in eng review.

## NOT in scope

- <item>: <why deferred>
- <item>: <why deferred>
- <item>: <why deferred>

## Decision log

| Decision | Choice | Alternatives | Reason | Reversible |
|---|---|---|---|---|
| <what> | <pick> | <list> | <one line> | easy / med / hard |

## Open questions remaining

- <question> (resolve in: design-review | eng-review)
```

After editing the plan, append a one-line entry to a `## Review log` section at the bottom (create it if missing):

```
- YYYY-MM-DD core-review by <user>: scope locked, blast radius scored, N items moved to NOT-in-scope.
```

## Hand-off

After the file is updated:
1. Print the plan file path.
2. Print a 3-line summary: locked scope sentence, surface score total, count of NOT-in-scope items.
3. If the plan has any UI / UX surface (UI score > 0): suggest `/y-plan-design-review plans/<file>.md`.
4. Else: suggest `/y-plan-eng-review plans/<file>.md`.
5. Do NOT start coding.

## Rules

- No em dashes anywhere. Use hyphens or rewrite.
- No emojis.
- Yash voice: direct, opinionated, no hedge words.
- If the plan fails Pass 1 (no success metric), stop and tell the user to go back to `/y-office-hours`. Do not lock scope on a fuzzy goal.
- Preserve all office-hours content. This command edits, not rewrites.
- Idempotent: re-running on the same plan updates the review log entry and refreshes findings without duplicating sections.
- Reference: `references/agentic-stack.md` for plan format. The plan file is the source of truth, not chat memory.
