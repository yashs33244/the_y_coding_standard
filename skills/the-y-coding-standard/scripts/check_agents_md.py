#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///
"""Verify AGENTS.md exists at a repo root and contains all required sections."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REQUIRED_SECTIONS: list[tuple[str, list[str]]] = [
    ("Project Overview", ["project overview", "overview"]),
    ("Stack", ["stack"]),
    ("Quickstart", ["quickstart", "setup", "getting started"]),
    ("Repository Layout", ["repository layout", "layout", "structure"]),
    ("Workflow", ["workflow"]),
    ("Coding Standards", ["coding standards"]),
    ("Governance", ["governance"]),
    ("Agent Permissions", ["agent permissions", "permissions"]),
    ("Constraints", ["constraints"]),
    ("Filing Rules", ["filing rules"]),
    ("Ownership", ["ownership", "owner", "contact"]),
]

OPTIONAL_SECTIONS: list[tuple[str, list[str]]] = [
    ("Skill Routing", ["skill routing"]),
]

H2_RE: re.Pattern[str] = re.compile(r"^\s{0,3}##\s+(.+?)\s*$", re.MULTILINE)
TODO_RE: re.Pattern[str] = re.compile(r"\bTODO\b", re.IGNORECASE)
STANDARD_REF_RE: re.Pattern[str] = re.compile(r"the[-_]y[-_]coding[-_]standard", re.IGNORECASE)


def find_agents_md(root: Path) -> Path | None:
    """Return path to AGENTS.md at root or None if absent."""
    candidate = root / "AGENTS.md"
    if candidate.is_file():
        return candidate
    return None


def parse_sections(content: str) -> list[str]:
    """Extract all H2 section headers from the markdown content."""
    return [m.group(1).strip() for m in H2_RE.finditer(content)]


def normalize(name: str) -> str:
    """Lowercase and trim a section name for comparison."""
    return name.strip().lower()


def check_required(present_sections: list[str]) -> tuple[list[str], list[str], list[str]]:
    """Return (present_required_canonical, missing_required, missing_optional)."""
    present_norm = {normalize(s) for s in present_sections}
    present_required: list[str] = []
    missing_required: list[str] = []
    missing_optional: list[str] = []
    for canonical, aliases in REQUIRED_SECTIONS:
        if any(alias in present_norm for alias in aliases):
            present_required.append(canonical)
        else:
            missing_required.append(canonical)
    for canonical, aliases in OPTIONAL_SECTIONS:
        if any(alias in present_norm for alias in aliases):
            present_required.append(canonical)
        else:
            missing_optional.append(canonical)
    return present_required, missing_required, missing_optional


def count_todos(content: str) -> int:
    """Count unresolved TODO markers in the content."""
    return len(TODO_RE.findall(content))


def main() -> int:
    """CLI entry: locate AGENTS.md, validate structure, print JSON."""
    parser = argparse.ArgumentParser(description="Validate AGENTS.md governance contract.")
    parser.add_argument("path", nargs="?", default=".", help="Repo root path (default '.')")
    args = parser.parse_args()
    root = Path(args.path).resolve()
    if not root.exists():
        print(json.dumps({"error": f"path does not exist: {root}"}), file=sys.stderr)
        return 2

    agents = find_agents_md(root)
    if agents is None:
        output = {
            "dimension": "audit",
            "tool": "check_agents_md",
            "file": "AGENTS.md",
            "exists": False,
            "sections_present": [],
            "sections_missing": [c for c, _ in REQUIRED_SECTIONS],
            "todos_unresolved": 0,
            "findings": [{
                "severity": "P1",
                "kind": "missing_file",
                "message": "AGENTS.md not found at repo root",
            }],
        }
        print(json.dumps(output, indent=2))
        return 1

    try:
        content = agents.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        print(json.dumps({"error": f"could not read AGENTS.md: {exc}"}), file=sys.stderr)
        return 2

    sections_present = parse_sections(content)
    present_canonical, missing_required, missing_optional = check_required(sections_present)
    todos = count_todos(content)
    has_standard_ref = bool(STANDARD_REF_RE.search(content))

    findings: list[dict[str, str]] = []
    for missing in missing_required:
        findings.append({
            "severity": "P1",
            "kind": "missing_section",
            "message": f"Required section missing: {missing}",
        })
    for missing in missing_optional:
        findings.append({
            "severity": "P2",
            "kind": "missing_optional_section",
            "message": f"Optional section missing: {missing}",
        })
    if todos > 0:
        for _ in range(todos):
            findings.append({
                "severity": "P3",
                "kind": "unresolved_todo",
                "message": "Unresolved TODO marker in AGENTS.md",
            })
    if not has_standard_ref:
        findings.append({
            "severity": "P2",
            "kind": "missing_standard_reference",
            "message": "AGENTS.md does not reference the-y-coding-standard",
        })

    output = {
        "dimension": "audit",
        "tool": "check_agents_md",
        "file": str(agents.relative_to(root)) if agents.is_relative_to(root) else str(agents),
        "exists": True,
        "sections_present": present_canonical,
        "sections_missing": missing_required + missing_optional,
        "todos_unresolved": todos,
        "findings": findings,
    }
    print(json.dumps(output, indent=2))

    high_sev = any(f.get("severity") in {"P0", "P1"} for f in findings)
    return 1 if high_sev else 0


if __name__ == "__main__":
    sys.exit(main())
