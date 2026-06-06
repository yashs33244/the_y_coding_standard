---
description: Sprint Loop step 08. Trigger when the user says "retro", "retrospective", "weekly retro", "post-mortem", "what did we ship", "reflect on the week", "retro time", "Yash retro", or any variant asking to look back at recent work. This is the "Reflect." step. Pulls commit history, plans activity, findings activity, and progress journals over a period (default 7 days), categorizes work into Shipped / In flight / Blocked / Learned, calls out Praise and Growth, captures any new Decisions, and writes progress/YYYY-MM-DD-retro.md. Run weekly or after any big ship. No exceptions.
---

## /y-retro

The "Reflect." step. Step 08 of the Sprint Loop. The other steps move forward. This one looks back. What did we ship, what is still in flight, what got stuck, what surprised us. The point is not a feel-good ritual. The point is to notice patterns of friction before they become permanent. Output is `progress/YYYY-MM-DD-retro.md` with concrete entries that future-you can grep through.

## Pre-flight

1. We are in a git repo. If not, abort.
2. Today's date is known. Use it to name the retro file.
3. `progress/` exists. If not, create it.
4. `plans/` and `findings/` exist. If not, log that as a finding (no Sprint Loop discipline this period).

Ask the user once: "Retro window: since last retro, last 7 days, last 14 days, or custom range?" Default to since last retro, fall back to 7 days if no prior retro file exists.

## Workflow

### 1. Determine the period

Find the most recent prior retro file in `progress/`. Use its date as the start. If none, use 7 days ago.

Capture:

- Start date.
- End date (today).
- Day count.

### 2. Pull commit history

Run `git log --since=<start> --pretty=format:'%h %s' --no-merges`.

Capture every commit. Group by:

- Conventional commit type: feat, fix, refactor, chore, docs, test.
- Day.

Count totals per type. Note the busiest day.

If you have multiple branches, also run `git log --since=<start> --all --pretty=format:'%h %an %s'` to see contributor breakdown.

### 3. Pull plans activity

List files in `plans/` modified during the period. For each:

- Read its status frontmatter.
- Categorize: created this period, shipped this period, abandoned this period, still in flight.

A plan that went from non-existent to `status: shipped` in one period is a healthy sprint signal. A plan that has been `in-progress` for three retros is a problem.

### 4. Pull findings activity

List files in `findings/` modified during the period:

- Governance findings: count P0/P1/P2/P3 across all `*-govern.md`.
- Review findings: count P0/P1/P2/P3 across all `*-review.md`.
- QA findings: count PASS / FAIL / PASS WITH CONCERNS across all `*-qa.md`.

Note repeat offenders: if the same standard violation shows up in three reviews this period, that is a growth area.

### 5. Pull progress journals

Skim every `progress/YYYY-MM-DD-*.md` from the period. Pull out:

- One-line shipped entries.
- Any "learned" or "note to self" lines.
- Any "blocked on X" lines.

### 6. Load references for context

If the period included a lot of Python work, skim `references/python.md` to see which standards came up. Same for `references/react-nextjs.md`, `references/oop.md`, `references/project-scaffold.md`. Use these to interpret the findings: a P1 about file size hits differently than a P1 about error handling.

### 7. Categorize the work

Build four lists:

**Shipped.** Features that merged AND deployed in the period. Source: plans with `status: shipped` and progress journals with shipped lines.

**In flight.** Open plans, open PRs, branches with recent commits but no ship. Source: `plans/` with `status: in-progress` and `git branch --no-merged main`.

**Blocked.** Anything explicitly marked blocked in plans or journals. Anything that did not move at all during the period. Anything called out in a finding as "waiting on X".

**Learned.** Surprises, gotchas, "did not know that", "next time we should". Pull from progress journals and findings.

### 8. Praise

Two or three concrete wins. Specific. Not "good week", but "shipped X in two days, P0 count down from 4 to 0". If there is nothing to praise, write "Quiet week. No notable wins or losses." Do not invent.

### 9. Growth

Repeated patterns of friction. Examples:

- "Same SOLID violation flagged in three reviews. Read references/oop.md before next class refactor."
- "QA caught error path bugs in two PRs. Build the error path during /y-build, not after."
- "Plans took two days each to lock in. Try smaller scopes."

Be honest. This is for future-you, not for an audience.

### 10. Decisions

Any new technical or process decision made this period that deserves a record. Examples:

- "Adopted vitest over jest for new packages."
- "Decided all classes get a fromJSON factory."
- "Decided no PR ships without a /y-qa report."

If any decision is worth keeping, suggest writing it to `Docs/decisions/YYYY-MM-DD-<slug>.md`. Do not write it automatically; surface the suggestion.

### 11. Next

One-paragraph forward look. What are we shipping next period? What are we stopping?

### 12. Write the retro

Create `progress/YYYY-MM-DD-retro.md`:

```
# Retro YYYY-MM-DD

## Period
Start: YYYY-MM-DD
End: YYYY-MM-DD
Days: N

## Commit stats
feat: N
fix: N
refactor: N
chore: N
docs: N
test: N
Total: N

## Shipped
- <plan title> - <pr url or commit>
- ...

## In flight
- <plan title> - status - last touched
- ...

## Blocked
- <thing> - reason
- ...

## Learned
- <one line>
- ...

## Praise
- <concrete win>
- ...

## Growth
- <pattern of friction> - <action item>
- ...

## Decisions
- <decision> - <suggested home: Docs/decisions/...>
- ...

## Next
<one paragraph forward look>
```

### 13. Print the one-screen summary

After writing the file:

- Period line.
- Commit total and busiest type.
- Shipped count.
- In flight count.
- Blocked count.
- Top praise.
- Top growth.
- Path to the full retro.

## Output

`progress/YYYY-MM-DD-retro.md` with the structured weekly retrospective.

## Hand-off

- If decisions were captured: hand off to writing `Docs/decisions/` entries.
- Otherwise: the loop starts over at `/y-grill` for the next sprint.

## Rules

- Eat the dog food. This command file itself must obey the_y_coding_standard.
- Never invent wins. A quiet week is a quiet week.
- Never make Growth a personal attack. It is about the system, not the person.
- Never use the em dash character. Use a hyphen or rewrite.
- Always include concrete file paths and PR URLs. The retro is searchable history.
- Always write the file. A skipped retro is a lost data point.
