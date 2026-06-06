---
description: Sprint Loop step 07. Trigger when the user says "ship it", "open the PR", "ship", "land this", "deploy this", "release this", "create PR", "merge ready", or any variant asking to push code out the door. This is the "Ship." step. Verifies the plan is ready-to-ship, the review has no open P0/P1, the QA report is PASS or PASS WITH CONCERNS, runs governance, generates the PR title and body in conventional commit format, pushes the branch, opens the PR with gh, prints the PR URL, updates the plan status to shipped, and appends a one-line entry to the session journal. Run AFTER /y-review and /y-qa. No exceptions.
---

## /y-ship

The "Ship." step. Step 07 of the Sprint Loop. /y-review said the code is right. /y-qa said the code works. /y-ship gets it out the door. This is not the place for new decisions. Every choice should already be made. This command runs the gates one more time, builds a clean PR, pushes, opens it, and tells you the URL. If any gate fails, it stops and tells you why.

## Pre-flight

This is the strictest pre-flight in the loop. Do not skip any check.

### 1. Branch check

Run `git branch --show-current`. If the branch is `main`, `master`, `trunk`, or `develop`, abort hard. Ship from feature branches only.

### 2. Working tree check

Run `git status --porcelain`. If output is non-empty, ask the user: "Working tree is dirty. Commit WIP first, or abort?" If commit, generate a sensible commit message and commit. If abort, stop.

### 3. Active plan check

Look in `plans/` for the active plan file. Read its frontmatter or header. Verify `status: ready-to-ship`. If status is anything else, abort and tell the user which step they skipped.

### 4. Review check

Look for `findings/YYYY-MM-DD-review.md` for today (or the most recent one tied to this branch). Parse the recommendation line. If recommendation is HOLD, abort. If there are any open P0 or P1 in the report, abort and list them. The user must run `/y-review` again after fixes.

### 5. QA check

Look for `findings/YYYY-MM-DD-qa.md` for today. Parse the verdict. If verdict is FAIL, abort. PASS or PASS WITH CONCERNS proceeds.

### 6. Date and folder check

Confirm today's date for filenames. Confirm `progress/` exists; create if missing.

## Workflow

### 1. Run governance

Invoke `/y-govern` as the final pre-flight gate. Wait for its output. If it reports any P0, abort and surface the P0 list. Do not ship around governance failures.

Load the right reference for context if governance flags stack-specific issues:

- Python: `references/python.md`.
- React / Next.js: `references/react-nextjs.md`.
- OOP issues: `references/oop.md`.
- Scaffold drift: `references/project-scaffold.md`.

### 2. Generate the PR title

Format: conventional commit. One of:

- `feat: <short description>` for new user-facing features.
- `fix: <short description>` for bug fixes.
- `refactor: <short description>` for internal cleanups.
- `chore: <short description>` for tooling, deps, config.
- `docs: <short description>` for docs-only.
- `test: <short description>` for tests-only.

Keep the title under 70 characters. Use the plan's title as the source of truth. Strip the file prefix.

### 3. Generate the PR body

Use this template:

```
## Plan
plans/<plan-file>.md

## Summary
<2-3 bullets pulled from the plan's scope section>

## Changes
<bullet list of meaningful file groups, not every file>

## Test plan
- [ ] <unit tests pass> (link findings/<date>-qa.md)
- [ ] <integration tests pass>
- [ ] <manual flow 1>
- [ ] <manual flow 2>

## Screenshots
<inline any from findings/screenshots/ for this branch>

## Review
findings/<date>-review.md - recommendation: SHIP

## QA
findings/<date>-qa.md - verdict: PASS | PASS WITH CONCERNS

## Governance
<one line from /y-govern output>

## Out of scope
<bullet list from the plan's out-of-scope section, so reviewers know what NOT to ask about>
```

Do not include emojis. Do not use the em dash character.

### 4. Push the branch

Run `git push -u origin <branch>` if the upstream is not set. Otherwise `git push`. Capture the output. If push fails (rejected, non-fast-forward, hook error), surface the error and stop. Do not force-push.

### 5. Open the PR

Run `gh pr create --title "<title>" --body "<body>"`. Pass the body via HEREDOC so formatting survives.

Capture the PR URL from the gh output. If `gh pr create` fails because a PR already exists, run `gh pr view --json url` and use that URL instead. If the existing PR body is stale, ask the user before overwriting.

### 6. Print the PR URL

One line, very visible:

```
PR opened: <url>
```

### 7. Update the plan status

Edit the active plan file. Change `status: ready-to-ship` to `status: shipped`. Add a line under the header:

```
Shipped: YYYY-MM-DD
PR: <url>
```

### 8. Append to the session journal

Find or create `progress/YYYY-MM-DD-<session>.md`. Append one line:

```
- <time> shipped <plan title> - <pr url>
```

If no session file exists for today, create one with a minimal header.

## Output

- Updated plan with `status: shipped` and PR link.
- New PR on the remote.
- Console output with the PR URL.
- One-line append to `progress/YYYY-MM-DD-<session>.md`.

## Hand-off

- The PR now belongs to whoever reviews it on the remote (Yash, codex, a human reviewer).
- After merge + deploy, hand off to `/y-retro` at the end of the week.

## Rules

- Eat the dog food. This command file itself must obey the_y_coding_standard.
- Never ship from main. Ever.
- Never skip governance. The whole point is the final gate.
- Never force-push to open a PR. Resolve conflicts the slow way.
- Never use the em dash character. Use a hyphen or rewrite.
- Never invent test plan items. Pull from the QA report.
- Never paste raw stack traces into the PR body. Link the QA report instead.
- Always update the plan status. Future-you needs to know what shipped.
- Always print the PR URL last. That is the artifact the user is waiting for.
