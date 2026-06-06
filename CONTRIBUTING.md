# Contributing to the_y_coding_standard

The plugin eats its own dog food: every PR must pass `/y-govern` before merge.

## Workflow

1. Open or claim an issue.
2. Write a plan in `plans/YYYY-MM-DD-<feature>.md`.
3. Implement on a `feat/<slug>` or `fix/<slug>` branch.
4. Add tests where applicable (eval cases in `skills/the-y-coding-standard/evals/triggers.md`).
5. Run `/y-govern` locally. Fix any P0/P1 findings.
6. Open the PR. Reference the plan file.

## Code style

The plugin is mostly markdown plus three small Python scripts. Rules:

- No em dashes (`-`). Use a regular hyphen or rewrite the sentence.
- No emojis in any file.
- Python scripts: `ruff` clean, type hints, stdlib only (or PEP 723 inline metadata).
- Markdown: clear headings, no walls of prose, table-heavy where appropriate.

## Adding a new reference file

1. Create `skills/the-y-coding-standard/references/<topic>.md`.
2. Add a row to the Reference Index table in `SKILL.md`.
3. Add at least one trigger case to `evals/triggers.md`.

## Adding a new command

1. Create `commands/y-<name>.md` with YAML frontmatter and a clear body prompt.
2. Add it to the `commands[]` array in `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`.
3. Add at least one trigger case to `evals/triggers.md`.

## Adding a new governance script

1. Create `skills/the-y-coding-standard/scripts/<name>.py` with PEP 723 inline metadata.
2. Make it `chmod +x` if it has a shebang.
3. Reference it from `commands/y-govern.md` in the relevant sub-agent prompt.
4. Document its JSON output shape in the script docstring.

## Versioning

We follow SemVer.

- Patch: typo fixes, doc clarifications, non-breaking script changes.
- Minor: new reference file, new command, new script, new policy.
- Major: changes to skill name, manifest schema, or backward-incompatible command behavior.

## Releasing

1. Update `version` in `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`.
2. Move `[Unreleased]` items in `CHANGELOG.md` under a new version + today's date.
3. Tag: `git tag v0.x.y && git push --tags`.
4. Cut a GitHub release pointing at the tag.

## License

MIT. See `LICENSE`.
