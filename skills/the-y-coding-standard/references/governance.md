# Agent Governance

The agent governance reference for any repo where AI agents participate in development. Borrows the Microsoft agent-governance-toolkit pattern (security, policy enforcement, auditability, compliance, agent permissions) and adapts it to a Claude Code plugin.

This is the file loaded by the `/y-govern` slash command. Read it end to end before running an audit.

## Why Governance Matters

AI agents read, write, and execute. They also get tricked, prompt-injected, and behave unpredictably. Governance is the set of policies that bound what agents are allowed to do AND the audit trail proving they followed the rules.

Without governance:
- Secrets leak through commits or logs.
- Dependencies pull in compromised packages.
- Pipelines run untrusted code from PRs.
- An agent edits prod config and nobody notices for a week.
- Compliance auditors have nothing to review.

With governance:
- Every agent action is logged.
- Sensitive operations require named approval.
- Supply chain is verified at every install.
- Permission scopes are explicit and minimal.
- Audits produce verifiable findings.

Governance is not optional once an agent has write access. If you skip it you are accepting the blast radius of a compromised model.

## The Five Governance Dimensions

The framework mirrors the Microsoft agent-governance-toolkit categories:

1. Security. Agents cannot leak secrets, run untrusted code, or expand attack surface.
2. Policy enforcement. Agents follow defined rules (style, branching, deployment gates).
3. Auditability. Every action is logged, reviewable, and tied to a human or agent identity.
4. Compliance. The repo passes the policies it claims to follow (SOC2 lite, OWASP LLM Top 10, dependency posture).
5. Agent permissions. Explicit scopes for what each agent surface can do.

The `/y-govern` command runs all five dimensions in parallel using three subagents (security, audit, permissions) that collectively cover the five dimensions. Two subagents each shoulder one and a half dimensions so the fan-out stays at three.

## Subagent Dispatch Model

`/y-govern` does NOT register custom subagent types. It dispatches three parallel Agent calls with `subagent_type: general-purpose`. Each agent receives a focused inline prompt and a specific script to run. Parallel dispatch keeps the wall-clock under a minute on a normal repo.

The main agent waits for all three to return, aggregates the findings, deduplicates them, severity-sorts, and writes the report.

### Subagent A: Security

Covers dimension 1 (security) and partially dimension 4 (compliance: vulnerability posture).

Tasks:
- Run `scripts/scan_secrets.py` and report leaked secrets.
- Inspect `.env` files committed to the repo.
- Check `package.json` and `pyproject.toml` for known-malicious dependencies.
- Verify TLS settings in any HTTP client config (no `verify=False`, no `rejectUnauthorized: false`).
- Verify SQL queries are parameterized using a heuristic grep for string-concatenated SQL.
- Check for `eval`, `exec`, `pickle.loads`, `yaml.load` (without SafeLoader), and `subprocess(shell=True)` usage.
- Confirm no hardcoded credentials in test fixtures.

### Subagent B: Audit

Covers dimension 2 (policy) and dimension 3 (auditability).

Tasks:
- Verify `AGENTS.md` exists and matches the template.
- Verify the canonical folder structure (`plans/`, `findings/`, `progress/`, `skills/`).
- Run `scripts/check_agents_md.py` for completeness.
- Verify every shipped feature has a plan in `plans/`.
- Verify every closed bug has a finding in `findings/`.
- Verify `Docs/decisions/` ADRs exist for architecture decisions.
- Audit commit history for unsigned commits, force-pushes, and missing co-author lines on AI-assisted commits.
- Confirm pre-commit hooks are installed and enforced in CI.

### Subagent C: Permissions

Covers dimension 5 (agent permissions) and partially dimension 4 (compliance: access posture).

Tasks:
- Run `scripts/audit_deps.py` for dependency vulnerabilities (`npm audit`, `uv tree --outdated`, `pip-audit`).
- Inspect `.claude/settings.json` and `.claude/settings.local.json` for the allowed tool list.
- Verify destructive operations (`rm -rf`, `git push --force`, `DROP TABLE`, `kubectl delete`) require explicit human approval.
- Inspect `.github/workflows/` for secrets exposure on PR triggers, especially `pull_request_target` misuse.
- Verify deployment workflows have manual approval on prod.
- Check that CI runners have least-privilege scopes (no blanket `GITHUB_TOKEN: write-all`).
- Confirm the permission matrix in `AGENTS.md` matches the actual `.claude/settings.json`.

## Aggregated Report

After all three subagents complete, `/y-govern` aggregates findings into a single report written to `findings/YYYY-MM-DD-governance.md`. Format:

```markdown
# Governance Audit

Date: YYYY-MM-DD
Branch: <branch>
Commit: <short-sha>

## Summary

| Dimension     | Status      | Findings |
|---------------|-------------|----------|
| Security      | PASS / FAIL | N        |
| Policy        | PASS / FAIL | N        |
| Auditability  | PASS / FAIL | N        |
| Compliance    | PASS / FAIL | N        |
| Permissions   | PASS / FAIL | N        |

## Critical Findings (block ship)
1. <P0 finding> at <file:line>

## High Findings (must fix before next release)
1. <P1 finding>

## Medium / Low Findings (queue)
- <P2/P3 finding>

## Recommendations
1. <action>

## Trend
<comparison to last audit if available>
```

Severity scale:
- P0 critical. Block ship. Secret in code, eval on untrusted input, prod token in a PR workflow.
- P1 high. Fix before next release. Missing pre-commit hook, unverified dependency, outdated lockfile.
- P2 medium. Queue. Missing ADR, missing finding for a closed bug.
- P3 low. Tracked but not blocking. Style drift in `AGENTS.md`.

## Policy Catalog

The audit checks the repo against this catalog. Add or remove policies per-project but keep the structure.

### Security policies
- No secrets in code. Any string matching common patterns (AWS keys, GitHub tokens, OpenAI keys, JWTs, private keys).
- No `.env` committed. Only `.env.example` with placeholder values.
- No TLS-disabled HTTP clients. `verify=True` in Python, `rejectUnauthorized: true` in Node.
- No `eval`, `exec`, `pickle`, or unsafe YAML on untrusted input.
- All SQL parameterized. No `f"SELECT ... {user_input}"`.
- Dependencies have no known criticals in the lockfile.
- No `subprocess(shell=True)` with user-controlled input.

### Policy enforcement
- `AGENTS.md` exists and follows the template.
- Every commit follows conventional commit format (`feat:`, `fix:`, `chore:`, etc.).
- Every PR has a passing CI run before merge.
- Pre-commit hooks block on lint, type, and test failures.
- Branch protection on `main` (no direct push, required reviews, required status checks).
- No force-push to protected branches.

### Auditability
- Every commit has an author.
- AI-assisted commits include a `Co-Authored-By` line for the model.
- Every deployed change is tied to a PR.
- Logs include request IDs, trace IDs, and agent session IDs.
- Skill invocations are logged in `progress/`.
- Every audit run leaves a dated file in `findings/`.

### Compliance
- Documented in `Docs/decisions/` for any architecture change.
- Dependency lockfiles checked in (`package-lock.json`, `uv.lock`, `pnpm-lock.yaml`).
- License compatibility scan passes.
- SBOM generated at release.
- Data handling matches the data classification doc.

### Agent permissions
- Each agent surface declares its tool allowlist in writing.
- Destructive tools (`Bash` with `rm`, force-push, prod-deploy) require explicit human approval at the harness level.
- Secret access scoped per surface, not granted globally.
- Production access gated by a named role, not blanket admin.

## Permission Matrix Template

Every repo with agent involvement publishes a permission matrix in `AGENTS.md` or `Docs/governance.md`. The audit checks that the matrix exists and matches reality.

```markdown
| Surface     | Read code | Write code  | Run tests | Deploy staging  | Deploy prod         | Access secrets     |
|-------------|-----------|-------------|-----------|-----------------|---------------------|--------------------|
| Claude Code | yes       | yes         | yes       | with approval   | NEVER               | dev only           |
| Cursor      | yes       | yes         | yes       | no              | NEVER               | dev only           |
| Codex CLI   | yes       | review-only | yes       | no              | NEVER               | none               |
| CI bot      | yes       | no          | yes       | yes             | with manual approval | scoped per workflow |
| Human dev   | yes       | yes         | yes       | yes             | with peer review    | scoped per role    |
```

If a surface is not in the matrix, the audit flags it. If a surface in the matrix has a permission the harness does not enforce, the audit flags it.

## How /y-govern Runs

1. Parse args. Optional `--quick` skips the slow dependency scan. Default is `--full`.
2. Dispatch three parallel Agent calls (security, audit, permissions) with inline prompts.
3. Each subagent loads the relevant sections of this file plus runs its assigned script.
4. Each subagent returns a structured findings list (JSON-like markdown).
5. Main agent aggregates, deduplicates, severity-sorts.
6. Writes `findings/YYYY-MM-DD-governance.md`.
7. Prints the summary table to the terminal.
8. Exits with status code 0 if no P0 findings, else 1.

The whole run should finish under 60 seconds for a normal repo, 3 minutes for a large monorepo with deep dependency trees.

## Scripts

The plugin ships three deterministic scripts in `scripts/`. All Python (uv-runnable). Python is the right choice because most projects in scope already have Python on the path or can use `uvx`.

| Script                 | Purpose                                              | How invoked                              |
|------------------------|------------------------------------------------------|------------------------------------------|
| `scan_secrets.py`      | Regex + entropy scan for leaked secrets              | `uv run scripts/scan_secrets.py [path]`  |
| `audit_deps.py`        | Wrap npm audit / pip-audit / uv tree --outdated      | `uv run scripts/audit_deps.py`           |
| `check_agents_md.py`   | Verify AGENTS.md exists and contains required sections | `uv run scripts/check_agents_md.py`     |

Script contract:
- Exit 0 plus JSON to stdout on success.
- Exit non-zero plus JSON to stdout on findings.
- All errors go to stderr.

Subagents parse the JSON and incorporate it into their report. Scripts must be idempotent and safe to run in any directory.

### scan_secrets.py
Walks the working tree, skips `.git`, `node_modules`, `.venv`, `dist`, and `build`. Matches common secret patterns (AWS access key, GitHub token, OpenAI key, generic high-entropy 32+ char strings). Returns a list of `{file, line, kind, snippet}` objects.

### audit_deps.py
Detects `package.json`, `pyproject.toml`, or `requirements.txt`. Runs the matching auditor. Parses output into a unified `{package, version, severity, advisory}` shape. Returns the list.

### check_agents_md.py
Loads `AGENTS.md` from the repo root. Verifies the required sections exist: project overview, permission matrix, command catalog, agent identity, and audit history. Returns `{missing_sections, warnings}`.

## Cross-Reference

This governance reference cites:
- Microsoft agent-governance-toolkit for the five-dimension framework.
- Microsoft AI-Engineering-Coach for the coach-mode review pattern at each workflow stage.
- OWASP LLM Top 10 for security policy seeds.
- SLSA framework for supply chain verification levels.

Names only. The URLs live in the project README, not here.

## What Governance Does NOT Do

- Replace pen tests.
- Replace SAST or DAST.
- Replace SOC2 or ISO certification.
- Substitute for a real security team.

It is the baseline that catches the obvious failures before they ship. If the audit is green and the repo still gets breached, the failure mode was outside the baseline. Treat the audit as the floor, not the ceiling.

## Running the First Audit

On a fresh repo:

1. Install the plugin and run `/y-init` to scaffold `AGENTS.md`, `plans/`, `findings/`, `progress/`.
2. Fill in the permission matrix manually. The audit cannot infer intent.
3. Run `/y-govern --full`. Expect findings on the first pass. That is the point.
4. Triage P0 immediately, P1 before the next release, P2 and P3 into the backlog.
5. Re-run after fixes. Compare to the previous audit using the `## Trend` section.

A repo passes when the audit returns zero P0 findings, fewer than three P1 findings, and the trend is flat or improving across two consecutive runs.

## Audit Cadence

- On every PR. The CI integration runs `/y-govern --quick` and posts findings as a comment.
- Weekly. A scheduled `/y-govern --full` run produces a dated report.
- Before every release. A blocking `/y-govern --full` plus a manual review of the permissions matrix.
- After any incident. A targeted audit on the affected surface.

The findings directory becomes the audit trail. Auditors read the dated files, not the live state.

## Inline Subagent Prompts

Each subagent receives an inline prompt at dispatch time. The prompts are short, deterministic, and reference this file by path. The main agent does not write the prompt from scratch each run. It uses these templates.

### Security subagent prompt

```
You are the security auditor for /y-govern.
Read references/governance.md sections "Subagent A: Security" and "Policy Catalog > Security policies".
Run scripts/scan_secrets.py on the repo root.
Grep for eval, exec, pickle.loads, yaml.load, subprocess(shell=True).
Grep for verify=False and rejectUnauthorized: false.
Return findings as a JSON array with shape:
[{severity: P0|P1|P2|P3, dimension: security, finding: string, file: string, line: number|null, fix: string}]
Do not write any files. Do not modify the repo.
```

### Audit subagent prompt

```
You are the policy and auditability checker for /y-govern.
Read references/governance.md sections "Subagent B: Audit", "Policy Catalog > Policy enforcement", and "Policy Catalog > Auditability".
Run scripts/check_agents_md.py.
Verify plans/, findings/, progress/, and skills/ directories exist.
Walk git log for the last 100 commits and flag missing Co-Authored-By on AI-assisted commits, force-pushes, and unsigned commits.
Return findings as a JSON array with the shape defined in the main prompt.
Do not write any files. Do not modify the repo.
```

### Permissions subagent prompt

```
You are the permissions and access auditor for /y-govern.
Read references/governance.md sections "Subagent C: Permissions", "Policy Catalog > Agent permissions", and "Permission Matrix Template".
Run scripts/audit_deps.py.
Read .claude/settings.json and .claude/settings.local.json.
Read all files under .github/workflows/.
Compare the declared permission matrix in AGENTS.md against the actual settings.
Return findings as a JSON array with the shape defined in the main prompt.
Do not write any files. Do not modify the repo.
```

The main agent collects the three arrays, deduplicates by `(dimension, file, line, finding)`, sorts by severity, and writes the report.

## Failure Modes the Audit Catches

Real examples the audit has caught on shipped repos:

- A `.env.production` file committed to a public mirror. P0. Found by `scan_secrets.py`.
- A GitHub Action with `pull_request_target` plus `actions/checkout` pinned to the PR head. Remote code execution on the runner with secrets exposed. P0. Found by the permissions subagent.
- A FastAPI route building SQL via f-string interpolation of a query parameter. P0. Found by the security subagent grep.
- An ADR-free migration from PostgreSQL to SQLite. P2. Found by the audit subagent.
- A `.claude/settings.local.json` granting `Bash(*)` with no allowlist. P1. Found by the permissions subagent.
- An OpenAI key in a Jupyter notebook output cell. P0. Found by `scan_secrets.py` scanning `.ipynb` JSON.

Each of these would have shipped without the audit. None of them required deep analysis. They required the audit to actually run on a schedule.

## Integrating with CI

A minimal GitHub Actions integration:

```yaml
name: governance
on: pull_request
jobs:
  audit:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: astral-sh/setup-uv@v3
      - run: uv run scripts/scan_secrets.py
      - run: uv run scripts/check_agents_md.py
      - run: uv run scripts/audit_deps.py
```

The Claude Code slash command and the CI workflow run the same scripts. The slash command adds the LLM-driven reasoning on top of the script output. The CI run gives you a fast, deterministic gate on every PR.

## Failure Recovery

If `/y-govern` fails midway:

1. Check `findings/` for a partial report. It may have one or two subagent sections completed.
2. Re-run with `--full` to overwrite. The report file is a single output, not an append.
3. If a script crashes, run it standalone via `uv run scripts/<script>.py` to see the stderr.
4. If a subagent times out, the main agent reports it as a P1 finding ("audit incomplete: <dimension>") and the report is marked partial in the summary table.

Partial audits are still useful. Two out of three dimensions green is better than no audit at all. But a partial audit cannot be used to justify a release.

## Customization

Projects extend this baseline by adding to the policy catalog. Do not weaken the baseline. To extend:

1. Add a new policy to the relevant section of the catalog.
2. Add a check to the relevant script (or write a new script and register it in the table above).
3. Update the inline subagent prompt to include the new check.
4. Document the extension in `Docs/governance.md` with a short rationale.

If a policy needs to be disabled for a specific repo, document why in `AGENTS.md` under a `## Governance Exceptions` section. The audit still runs the check but tags the finding as `accepted: true` and downgrades it. Exceptions expire after 90 days unless renewed.

## Identity and Attribution

Every action attributed to an agent must include the agent surface name (Claude Code, Cursor, Codex CLI) and the model version. The `Co-Authored-By` line in commits is the canonical attribution. Logs reference an agent session ID that maps back to the same identity. If an action cannot be attributed to a named human or named agent, the audit flags it as P1.

This matters because when something goes wrong you need to know which surface produced the change. "An AI did it" is not an answer. "Claude Code session abc123 on Opus 4.7 produced this commit, signed off by yash@example.com" is.

