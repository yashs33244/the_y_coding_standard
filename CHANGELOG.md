# Changelog

All notable changes to the_y_coding_standard plugin will be documented in this file.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-06-07

### Added
- Initial release.
- `the-y-coding-standard` skill with aggressive auto-trigger on new projects, new features, and `.py/.ts/.tsx/.js` file creation.
- Six reference files: python.md, react-nextjs.md, oop.md, agentic-stack.md, governance.md, project-scaffold.md.
- Full Sprint Loop slash commands: `/y-office-hours`, `/y-plan-core-review`, `/y-plan-design-review`, `/y-plan-eng-review`, `/y-review`, `/y-qa`, `/y-ship`, `/y-retro`.
- `/y-init` command that scaffolds the agentic engineering stack into a target repo (AGENTS.md, CLAUDE.md, .claude, .agents, .conductor, .cursor, .devcontainer, .github, .husky, Docs, plans, findings, progress).
- `/y-govern` command that dispatches three parallel sub-agents (security, audit, permissions) inspired by Microsoft's agent-governance-toolkit.
- Three governance scripts: scan_secrets.py, audit_deps.py, check_agents_md.py.
- AGENTS.md and CLAUDE.md drop-in templates.
- Trigger eval matrix at evals/triggers.md (27 cases covering all command and reference triggers).
- Marketplace manifest for `/plugin marketplace add yashs33244/the_y_coding_standard`.
