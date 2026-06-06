---
description: Run the_y_coding_standard governance audit. Dispatches three parallel sub-agents (security, audit, permissions) inspired by Microsoft's agent-governance-toolkit. Each runs deterministic scripts and inspects the repo. Aggregates findings into findings/YYYY-MM-DD-governance.md. Use before every release.
---

# /y-govern

You are running the_y_coding_standard governance audit. Goal: produce a findings file at `findings/YYYY-MM-DD-governance.md` covering five governance dimensions (security, policy, auditability, compliance, permissions).

## Pre-flight

1. Verify the working directory is a git repo. If not, abort with a helpful message.
2. Verify the canonical folder structure exists. If `findings/` is missing, create it.
3. Load the governance reference at `${CLAUDE_PLUGIN_ROOT}/skills/the-y-coding-standard/references/governance.md`. Use it as the policy catalog.
4. Identify the plugin install path. Scripts are at `${CLAUDE_PLUGIN_ROOT}/skills/the-y-coding-standard/scripts/`.

## Parse Args

Accept optional flags:
- `--quick`: skip slow dep scan (audit_deps.py).
- `--full` (default): run everything.

## Dispatch Three Sub-Agents in Parallel

Use the Agent tool with `subagent_type: general-purpose`. Dispatch all three in a single message so they run concurrently.

### Sub-agent A: Security

Prompt for the agent (self-contained, since the agent has no shared context):

"You are running the SECURITY portion of the_y_coding_standard governance audit on the repo at <PWD>.

Tasks:
1. Run `uv run ${CLAUDE_PLUGIN_ROOT}/skills/the-y-coding-standard/scripts/scan_secrets.py <PWD>` and capture JSON output.
2. Grep for common dangerous patterns across the codebase:
   - Python: `eval(`, `exec(`, `pickle.loads`, `yaml.load(` (without `safe_load`), `subprocess(...shell=True`, `verify=False`.
   - SQL string interpolation: regex `f\"SELECT.*\\{` or `\".*\" \\+ .*` near sql calls.
   - TLS-disabled HTTP: `rejectUnauthorized: false` (Node), `verify=False` (Python requests).
3. Inspect any `.env` files committed (should be only `.env.example`).
4. Check `package.json` / `pyproject.toml` for obviously suspicious deps.
5. Inspect `.github/workflows/*.yml` for secret exposure (env or secrets used on `pull_request_target`).

Return a JSON findings list. Severity P0 / P1 / P2 / P3. For each finding: file:line, message, severity, recommended fix.

Output format:
{
  \"dimension\": \"security\",
  \"findings\": [
    {\"file\": \"src/app.py\", \"line\": 42, \"message\": \"...\", \"severity\": \"P1\", \"fix\": \"...\"}
  ]
}"

### Sub-agent B: Audit (policy + auditability)

Prompt:

"You are running the AUDIT portion of the_y_coding_standard governance audit on the repo at <PWD>.

Tasks:
1. Run `uv run ${CLAUDE_PLUGIN_ROOT}/skills/the-y-coding-standard/scripts/check_agents_md.py <PWD>` and capture JSON output.
2. Verify canonical folders exist: `plans/`, `findings/`, `progress/`, `Docs/decisions/`, `.agents/skills/`.
3. Inspect recent git log (last 50 commits):
   - Any AI-assisted commits without `Co-Authored-By` line?
   - Any commits to main not via PR?
   - Any force-pushes (use reflog if available)?
4. Verify `Docs/decisions/` has at least one ADR.
5. Verify pre-commit hooks exist in `.husky/` or `.pre-commit-config.yaml`.
6. Verify `.github/workflows/ci.yml` exists and has lint + test gates.

Return a JSON findings list in the same format as the security agent.

Output format:
{
  \"dimension\": \"audit\",
  \"findings\": [...]
}"

### Sub-agent C: Permissions (deps + access)

Prompt:

"You are running the PERMISSIONS portion of the_y_coding_standard governance audit on the repo at <PWD>.

Tasks:
1. If --quick flag is NOT set, run `uv run ${CLAUDE_PLUGIN_ROOT}/skills/the-y-coding-standard/scripts/audit_deps.py <PWD>` and capture JSON output.
2. Inspect `.claude/settings.json` and `.claude/settings.local.json`:
   - Is there an allow + deny list?
   - Are destructive operations (rm -rf, git push --force, sudo) denied?
3. Inspect `.github/workflows/*.yml` for prod deploy gating:
   - Does prod deploy require `environment:` with required reviewers?
4. Check for permission matrix in `AGENTS.md`.
5. Check `.husky/pre-push` exists.

Return a JSON findings list.

Output format:
{
  \"dimension\": \"permissions\",
  \"findings\": [...]
}"

## Aggregate

After all three sub-agents return:
1. Combine findings into one list.
2. Deduplicate (same file, same line, same message).
3. Sort by severity P0 > P1 > P2 > P3.
4. Compute per-dimension status: PASS if no P0/P1 in that dimension, else FAIL.

## Write Report

Write `findings/YYYY-MM-DD-governance.md` with this structure:

```markdown
# Governance Audit

Date: YYYY-MM-DD
Branch: <branch>
Commit: <short-sha>
Mode: full | quick

## Summary

| Dimension | Status | Findings |
|---|---|---|
| Security | PASS / FAIL | N |
| Policy | PASS / FAIL | N |
| Auditability | PASS / FAIL | N |
| Compliance | PASS / FAIL | N |
| Permissions | PASS / FAIL | N |

## Critical Findings (block ship)
1. [P0] <file:line> - <message>. Fix: <fix>.

## High Findings (must fix before next release)
1. [P1] ...

## Medium / Low Findings (queue)
- [P2] ...
- [P3] ...

## Recommendations
1. <high-level action>

## Trend
<diff vs previous audit if findings/YYYY-MM-DD-governance.md exists from a prior date>
```

## Final Output

After writing the report:
1. Print the summary table to terminal.
2. Print critical and high findings inline.
3. Print the path to the full report.
4. If any P0 findings: explicitly say "BLOCK SHIP" and exit conceptually with failure status. Otherwise say "Governance: PASS" or "Governance: PASS with warnings".

## Rules
- No em dashes in any written content.
- No emojis.
- Direct Yash voice.
- Idempotent: running twice on the same commit produces the same report.
