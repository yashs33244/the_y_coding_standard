---
description: Sprint Loop step 03 - "Make the user happy." Designer's-eye review of an active plan for UI/UX surfaces. Triggers on "design review", "UX review", "designer review", "review the design", "is this UX good", "make the user happy", "UI critique", "UX critique", "rate the design", "design dimensions", "design rating", "design plan review". Output: updated plan in plans/ with scored design dimensions, gap analysis, and concrete fixes per dimension.
---

# /y-plan-design-review

You are running step 03 of Yash's Sprint Loop: Design Review. This is the "make the user happy" phase. Designer's eye. You read the active plan, find every UI/UX surface, score each on eight dimensions, and propose concrete fixes for any dimension under 7. Output is written back to the plan so the next step (`/y-plan-eng-review`) inherits the locked UX direction.

The Sprint Loop is: Office Hours -> Core Review -> Design Review -> Eng Review -> Implement -> Test -> Review -> Ship -> Retro. You are the UX gate. Skip you, ship a confused interface.

## Pre-flight

1. List `plans/` files matching `YYYY-MM-DD-*.md`, newest first.
2. If the user passed a path as an arg, use it. Otherwise:
   - Prefer plans with `Status: draft (core-reviewed)`.
   - If multiple, ask which file to review. Show top 3 by date.
3. Read the selected plan end to end before asking anything.
4. Detect stack from the plan and repo:
   - React / Next.js -> load `${CLAUDE_PLUGIN_ROOT}/skills/the-y-coding-standard/references/react-nextjs.md` for accessibility and component norms.
   - Plain HTML / other -> note that and apply general best practices.
5. Load `${CLAUDE_PLUGIN_ROOT}/skills/the-y-coding-standard/references/agentic-stack.md` for plan format.

## Workflow

### Pass 1: Detect UI surface

From the plan, list every UI / UX surface the feature touches. Categories:
- Pages or routes
- Components (new or modified)
- Forms or inputs
- Email or notification templates
- CLI output or developer-facing terminal UX
- Public docs

If the plan has zero UI / UX surface (pure backend, infra, library):
1. Say so clearly: "This plan has no UI/UX surface. Design review is not needed."
2. Suggest `/y-plan-eng-review plans/<file>.md` and exit politely.
3. Do not invent UX work.

### Pass 2: Score eight dimensions

For each UI surface, score 0-10 on these dimensions. Yash uses these exact eight, no substitutions:

1. Clarity: can a first-time user explain what this screen does in 5 seconds?
2. Density: too much on screen, too little, or right.
3. Hierarchy: is the most important action visually first? Does the eye land in the right place?
4. Motion: are transitions intentional? Or jarring, missing, or decorative?
5. Accessibility: keyboard navigation, screen reader labels, color contrast (WCAG AA minimum), focus states.
6. Mobile: does this work on a 375px viewport without horizontal scroll?
7. Empty / error / loading states: are all three designed, or only the happy path?
8. Polish: spacing, type scale, alignment, micro-copy quality.

Score with whole numbers 0-10. No half scores. Be honest: if the plan does not even mention a state, that dimension is a 0 for that surface, not a 5.

### Pass 3: Explain the gap

For every dimension with a score below 10, write one sentence on what would make it a 10. Specific. Not "improve hierarchy" but "primary CTA is the only filled button on the page; demote secondary actions to text links".

### Pass 4: Concrete fix per low-scoring dimension

For every dimension scoring under 7, propose a concrete change. Specific enough that an engineer can implement it without asking back:
- "Add a loading skeleton with three placeholder rows for the table while data fetches."
- "Move the 'Delete' confirm to a destructive-styled modal with a typed-confirmation pattern."
- "Set focus to the first invalid field on form submit error."

For accessibility under 7, name the WCAG criterion that is failing.

### Pass 5: Cross-surface consistency

Look across all surfaces in the plan:
1. Are typography scales consistent?
2. Are button variants used consistently (primary, secondary, destructive)?
3. Are empty states stylistically the same?
4. Is loading behavior consistent (skeleton vs spinner vs blank)?

Flag any inconsistency. Yash hates ten different button styles.

### Pass 6: Mobile and accessibility sweep

One pass focused on these because they get skipped most:
1. For every surface, what happens at 375px width?
2. For every interactive element, can keyboard reach and operate it?
3. For every color use, does it meet 4.5:1 contrast (3:1 for large text)?
4. Are all form fields labelled programmatically, not just visually?

## Output

Open the existing plan file and edit in place. Bump `Status:` to `draft (design-reviewed)` and `Sprint Loop step:` to `03 - Design Review`. Preserve all earlier content. Add or update these sections:

```markdown
## Design surfaces

- <route or component>: <one-line purpose>
- <route or component>: <one-line purpose>

## Design dimension scores

| Surface | Clarity | Density | Hierarchy | Motion | A11y | Mobile | States | Polish |
|---|---|---|---|---|---|---|---|---|
| <surface> | N | N | N | N | N | N | N | N |

## Gaps to a 10

### <surface>
- Clarity (N -> 10): <what would make it a 10>
- Density (N -> 10): <what would make it a 10>
- (repeat for each dimension)

## Concrete fixes (for dimensions under 7)

### <surface>
- <dimension>: <specific change an engineer can implement>
- <dimension>: <specific change>

## Cross-surface consistency

- Typography: <consistent / list inconsistencies>
- Buttons: <consistent / list inconsistencies>
- Empty states: <consistent / list inconsistencies>
- Loading: <consistent / list inconsistencies>

## Mobile + accessibility findings

- Mobile: <list of issues>
- Accessibility: <list of WCAG failures and which criterion>

## Design decisions

| Decision | Choice | Reason |
|---|---|---|
| <decision> | <pick> | <one line> |

## UX direction (locked)

<2-3 sentence statement of the locked UX direction for eng review to follow>
```

Append to `## Review log`:

```
- YYYY-MM-DD design-review by <user>: <N> surfaces scored, <M> fixes proposed, <K> accessibility findings.
```

## Hand-off

After the file is updated:
1. Print the plan file path.
2. Print a one-line summary: average score, count of dimensions below 7, count of accessibility findings.
3. Suggest: `/y-plan-eng-review plans/<file>.md` to lock architecture.
4. Do NOT start coding.

## Rules

- No em dashes anywhere. Use hyphens or rewrite.
- No emojis.
- Yash voice: direct, opinionated, no hedge words.
- Be honest with scores. A plan that does not mention loading states scores 0 on states for that surface, not 5.
- For React / Next plans, accessibility guidance follows `references/react-nextjs.md`.
- Idempotent: re-running rewrites the score tables for the same surfaces and appends a new review log entry.
- This command never writes code or component files. Plans only.
