---
description: Sprint Loop step 06. Trigger when the user says "QA this", "test this", "does it work", "run QA", "verify the change", "smoke test", "end to end check", "report bugs", "QA pass", or any variant asking to validate that the code actually works. This is the "Does it work?" gate. Runs unit + integration tests, walks the golden path, hits at least one error path and one boundary case per user flow, captures screenshots on UI changes. Produces findings/YYYY-MM-DD-qa.md with PASS / FAIL / PASS WITH CONCERNS at the top. Run this AFTER /y-review and BEFORE /y-ship. No exceptions.
---

## /y-qa

The "Does it work?" gate. Step 06 of the Sprint Loop. /y-review told us the code looks right on paper. /y-qa tells us the code actually runs. Tests pass. The golden path works. The obvious error paths do not crash. The obvious boundaries do not explode. The output is `findings/YYYY-MM-DD-qa.md` with a top-line verdict and the evidence behind it.

## Pre-flight

Before running QA, confirm:

1. We are in a git repo. If not, abort.
2. There is an active plan in `plans/`. Read it to know what user flows we are validating.
3. There is a recent `findings/YYYY-MM-DD-review.md`. If not, suggest running `/y-review` first. If the user insists on skipping, log this as a concern in the QA report.
4. Today's date is known. Use it to name the findings file.
5. The `findings/` folder exists. If not, create it.

Ask the user once: "QA on current branch, recent commit, or a specified PR number?" Default to current branch.

## Workflow

### 1. Identify the change scope

Capture:

- Current branch name.
- Recent commit messages: `git log --oneline -10`.
- Files changed since branching from main: `git diff --name-only main...HEAD`.

Read the active plan and extract the user-facing flows we promised. These are the flows we will walk through.

### 2. Detect test runners

Look for config in this order:

- `package.json` scripts and devDependencies. Look for `vitest`, `jest`, `playwright`, `cypress`, `test`.
- `pyproject.toml` or `pytest.ini` or `tox.ini`. Look for `pytest`.
- `Cargo.toml`. Look for `cargo test`.
- `go.mod`. Look for `go test`.

If no test runner is configured, write a P1 finding in the QA report: "No test runner detected. Set one up before next sprint." Continue with manual checks only.

Load the right reference for context:

- Python tests: `references/python.md`.
- React / Next.js tests: `references/react-nextjs.md`.

### 3. Run unit + integration tests

Run the detected test command. Capture full output, including:

- Total tests run.
- Passed / failed / skipped.
- Stack traces for failures.
- Time taken.

If tests fail, that does not automatically fail QA. Read the failures. If they are in code the diff did not touch, log as "pre-existing failure" and note it. If they are in code the diff touched, that is a hard FAIL.

### 4. Start a dev server if applicable

If the project has:

- `next dev`, `vite`, `npm run dev`: start it on a free port.
- `uvicorn`, `fastapi dev`, `flask run`: start it.
- `python manage.py runserver`: start it.

Run in background. Capture the URL. If the server fails to start, that is a P0 finding.

If the project does not have a runnable dev server (library, CLI), skip this step.

### 5. Walk every user flow in the plan

For each flow the plan promised:

**Happy path.** Do the thing the user does. Confirm the expected outcome. Record what happened.

**At least one error path.** Submit invalid input. Send a network error. Click cancel. Confirm the error is handled. No silent failures. No raw stack traces in the UI. No 500s.

**At least one boundary case.** Empty input. Maximum input. Very slow network. Very fast successive clicks. Confirm the system holds up.

For each path, write one line in the report:

```
- [PASS|FAIL] flow-name - happy - what happened
- [PASS|FAIL] flow-name - error - what happened
- [PASS|FAIL] flow-name - boundary - what happened
```

### 6. Screenshots for UI changes

If the diff touched any UI file (`.tsx`, `.jsx`, `.html`, `.css`):

- Take a screenshot of the affected screen after the change.
- If a baseline exists (previous screenshot in `findings/screenshots/`), compare. Note any unexpected visual diff.
- Save new screenshots under `findings/screenshots/YYYY-MM-DD-<flow>.png`.

If no headless browser is available, ask the user to attach screenshots manually and note this in the report.

### 7. Edge cases worth checking on every QA run

- Reload the page mid-action. Does state survive?
- Open the feature in a second tab. Does it conflict?
- Use the back button. Does it crash?
- Disable JavaScript (if applicable). Does the page degrade?
- Slow 3G throttling. Does loading state show?

These do not have to all pass. Note which ones were checked.

### 8. Write the report

Create `findings/YYYY-MM-DD-qa.md`:

```
# QA YYYY-MM-DD

Verdict: PASS | FAIL | PASS WITH CONCERNS

Plan: plans/<plan-file>.md
Branch: <branch-name>
Files changed: <count>

## Test run
Command: <test command>
Total: <N>
Passed: <N>
Failed: <N>
Skipped: <N>
Time: <seconds>

Failures:
- <test name> - <one line>

## User flows
- [PASS|FAIL] flow - happy - notes
- [PASS|FAIL] flow - error - notes
- [PASS|FAIL] flow - boundary - notes

## Screenshots
- findings/screenshots/<file>.png - <what it shows>

## Bugs found
- [P?] file:line - bug - repro steps - expected vs actual

## Edge cases checked
- reload mid-action: <result>
- second tab: <result>
- back button: <result>

## Concerns
<anything that PASSed but felt off>
```

Verdict rules:

- **FAIL** if any happy path failed, any test in changed code failed, dev server failed to start, or there are P0 bugs.
- **PASS WITH CONCERNS** if happy paths passed but error/boundary cases failed or P1 bugs exist.
- **PASS** otherwise.

### 9. Print the one-screen summary

After writing the file:

- Verdict at the top.
- Test counts.
- One-line per flow.
- Top bugs (P0 first).
- Path to the report.

## Output

`findings/YYYY-MM-DD-qa.md` with the full QA report and evidence.

## Hand-off

- If verdict is PASS or PASS WITH CONCERNS: hand off to `/y-ship`.
- If verdict is FAIL: hand off back to `/y-build` with the bug list.

## Rules

- Eat the dog food. This command file itself must obey the_y_coding_standard.
- Never skip user flows because they feel obvious. Walk every one.
- Never report PASS if any happy path is broken. PASS WITH CONCERNS is for nice-to-have failures only.
- Never use the em dash character. Use a hyphen or rewrite.
- Always save screenshots for UI changes if a browser is available.
- Always write the report file, even on PASS. Future-you needs the audit trail.
