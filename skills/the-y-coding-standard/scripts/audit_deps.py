#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///
"""Aggregate dependency audit results across native package managers into one JSON output."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

TIMEOUT_SECONDS: int = 60

SEVERITY_MAP: dict[str, str] = {
    "critical": "P0", "high": "P1", "moderate": "P2", "medium": "P2",
    "low": "P3", "info": "P3", "unknown": "P3",
}


def normalize_severity(value: str | None) -> str:
    """Map a native severity string to our P0-P3 scale."""
    if not value:
        return "P3"
    return SEVERITY_MAP.get(value.strip().lower(), "P3")


def detect_managers(root: Path) -> list[str]:
    """Detect which package managers are present at the given root."""
    detected: list[str] = []
    if (root / "package.json").exists():
        if (root / "pnpm-lock.yaml").exists():
            detected.append("pnpm-audit")
        else:
            detected.append("npm-audit")
    if (root / "pyproject.toml").exists() or (root / "requirements.txt").exists():
        detected.append("pip-audit")
    if (root / "Cargo.toml").exists():
        detected.append("cargo-audit")
    if (root / "go.mod").exists():
        detected.append("govulncheck")
    return detected


def run_subprocess(cmd: list[str], cwd: Path) -> tuple[int, str, str]:
    """Run a subprocess returning (returncode, stdout, stderr)."""
    try:
        proc = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True,
                              timeout=TIMEOUT_SECONDS, check=False)
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired:
        return 124, "", f"timeout after {TIMEOUT_SECONDS}s"
    except FileNotFoundError as exc:
        return 127, "", str(exc)
    except OSError as exc:
        return 1, "", str(exc)


def _load_json(out: str, name: str) -> tuple[Any, str | None]:
    """Parse stdout as JSON; return (data, error)."""
    try:
        return json.loads(out), None
    except json.JSONDecodeError:
        return None, f"could not parse {name} JSON"


def run_npm_audit(root: Path, use_pnpm: bool = False) -> tuple[list[dict[str, Any]], str | None]:
    """Run npm or pnpm audit and parse JSON output into unified findings."""
    binary = "pnpm" if use_pnpm else "npm"
    if not shutil.which(binary):
        return [], f"{binary} not installed"
    code, out, err = run_subprocess([binary, "audit", "--json"], root)
    if not out:
        return [], err or f"{binary} produced no output (exit {code})"
    data, perr = _load_json(out, f"{binary} audit")
    if perr:
        return [], perr
    findings: list[dict[str, Any]] = []
    for pkg_name, info in (data.get("vulnerabilities") or {}).items():
        if not isinstance(info, dict):
            continue
        advisory_id, summary = "", ""
        for entry in info.get("via", []) or []:
            if isinstance(entry, dict):
                advisory_id = str(entry.get("url") or entry.get("source") or "")
                summary = str(entry.get("title") or "")
                break
        findings.append({"package": pkg_name, "version": str(info.get("range") or info.get("version") or ""),
                         "severity": normalize_severity(info.get("severity")), "advisory_id": advisory_id,
                         "summary": summary or f"{pkg_name} flagged by {binary} audit"})
    for _aid, adv in (data.get("advisories") or {}).items():
        if not isinstance(adv, dict):
            continue
        findings.append({"package": str(adv.get("module_name") or ""),
                         "version": str(adv.get("vulnerable_versions") or ""),
                         "severity": normalize_severity(adv.get("severity")),
                         "advisory_id": str(adv.get("url") or adv.get("id") or ""),
                         "summary": str(adv.get("title") or adv.get("overview") or "")})
    return findings, None


def run_pip_audit(root: Path) -> tuple[list[dict[str, Any]], str | None]:
    """Run pip-audit via uvx and parse JSON output."""
    if shutil.which("uvx"):
        cmd = ["uvx", "pip-audit", "-f", "json"]
    elif shutil.which("pip-audit"):
        cmd = ["pip-audit", "-f", "json"]
    else:
        return [], "neither uvx nor pip-audit installed"
    code, out, err = run_subprocess(cmd, root)
    if not out:
        return [], err or f"pip-audit produced no output (exit {code})"
    data, perr = _load_json(out, "pip-audit")
    if perr:
        return [], perr
    deps = data.get("dependencies") if isinstance(data, dict) else data
    findings: list[dict[str, Any]] = []
    for dep in deps or []:
        if not isinstance(dep, dict):
            continue
        pkg, version = str(dep.get("name") or ""), str(dep.get("version") or "")
        for v in dep.get("vulns") or []:
            if not isinstance(v, dict):
                continue
            findings.append({"package": pkg, "version": version,
                             "severity": normalize_severity(v.get("severity")),
                             "advisory_id": str(v.get("id") or ""),
                             "summary": str(v.get("description") or v.get("summary") or "")})
    return findings, None


def run_cargo_audit(root: Path) -> tuple[list[dict[str, Any]], str | None]:
    """Run cargo audit and parse JSON output."""
    if not shutil.which("cargo"):
        return [], "cargo not installed"
    code, out, err = run_subprocess(["cargo", "audit", "--json"], root)
    if not out:
        return [], err or f"cargo audit produced no output (exit {code})"
    data, perr = _load_json(out, "cargo audit")
    if perr:
        return [], perr
    findings: list[dict[str, Any]] = []
    for v in (data.get("vulnerabilities") or {}).get("list") or []:
        if not isinstance(v, dict):
            continue
        advisory = v.get("advisory") or {}
        package = v.get("package") or {}
        findings.append({"package": str(package.get("name") or ""),
                         "version": str(package.get("version") or ""),
                         "severity": normalize_severity(advisory.get("severity")),
                         "advisory_id": str(advisory.get("id") or ""),
                         "summary": str(advisory.get("title") or advisory.get("description") or "")})
    return findings, None


def run_govulncheck(root: Path) -> tuple[list[dict[str, Any]], str | None]:
    """Run govulncheck and parse newline-delimited JSON output."""
    if not shutil.which("govulncheck"):
        return [], "govulncheck not installed"
    code, out, err = run_subprocess(["govulncheck", "-json", "./..."], root)
    if not out:
        return [], err or f"govulncheck produced no output (exit {code})"
    findings: list[dict[str, Any]] = []
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        osv = entry.get("osv") or entry.get("OSV") if isinstance(entry, dict) else None
        if not isinstance(osv, dict):
            continue
        pkg_name = ""
        affected = osv.get("affected") or []
        if affected and isinstance(affected[0], dict):
            pkg = affected[0].get("package") or {}
            if isinstance(pkg, dict):
                pkg_name = str(pkg.get("name") or "")
        ds = osv.get("database_specific") if isinstance(osv.get("database_specific"), dict) else {}
        findings.append({"package": pkg_name, "version": "",
                         "severity": normalize_severity(ds.get("severity") if isinstance(ds, dict) else None),
                         "advisory_id": str(osv.get("id") or ""),
                         "summary": str(osv.get("summary") or osv.get("details") or "")})
    return findings, None


def main() -> int:
    """CLI entry: detect managers, run audits, aggregate, print JSON."""
    parser = argparse.ArgumentParser(description="Aggregate dependency audits.")
    parser.add_argument("path", nargs="?", default=".", help="Root path of the repo (default '.')")
    args = parser.parse_args()
    root = Path(args.path).resolve()
    if not root.exists():
        print(json.dumps({"error": f"path does not exist: {root}"}), file=sys.stderr)
        return 2

    detected = detect_managers(root)
    if not detected:
        print(json.dumps({"dimension": "permissions", "tool": "audit_deps", "scanners_run": [],
                          "scanners_skipped": [{"name": "all", "reason": "no recognized package manager files found"}],
                          "findings": []}, indent=2))
        return 0
    runners: dict[str, Any] = {
        "npm-audit": lambda r: run_npm_audit(r, use_pnpm=False),
        "pnpm-audit": lambda r: run_npm_audit(r, use_pnpm=True),
        "pip-audit": run_pip_audit, "cargo-audit": run_cargo_audit, "govulncheck": run_govulncheck,
    }
    scanners_run: list[str] = []
    scanners_skipped: list[dict[str, str]] = []
    all_findings: list[dict[str, Any]] = []
    failed = 0
    for name in detected:
        runner = runners.get(name)
        if runner is None:
            scanners_skipped.append({"name": name, "reason": "no runner defined"})
            continue
        try:
            findings, error = runner(root)
        except Exception as exc:
            scanners_skipped.append({"name": name, "reason": f"runner crashed: {exc}"})
            failed += 1
            continue
        if error and not findings:
            scanners_skipped.append({"name": name, "reason": error})
            failed += 1
            continue
        scanners_run.append(name)
        all_findings.extend(findings)
    print(json.dumps({"dimension": "permissions", "tool": "audit_deps", "scanners_run": scanners_run,
                      "scanners_skipped": scanners_skipped, "findings": all_findings}, indent=2))
    if not scanners_run and failed == len(detected):
        return 2
    return 1 if any(f.get("severity") in {"P0", "P1"} for f in all_findings) else 0


if __name__ == "__main__":
    sys.exit(main())
