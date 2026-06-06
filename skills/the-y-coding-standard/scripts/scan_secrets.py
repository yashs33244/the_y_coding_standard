#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///
"""Regex and entropy scanner for leaked secrets across a repository tree."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

SKIP_DIRS: set[str] = {
    "node_modules",
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "dist",
    "build",
    ".next",
    "coverage",
    ".turbo",
    ".cache",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}

SKIP_EXTS: set[str] = {
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".webp", ".svg",
    ".pdf", ".zip", ".tar", ".gz", ".bz2", ".7z", ".rar",
    ".mp3", ".mp4", ".mov", ".avi", ".wav", ".webm",
    ".woff", ".woff2", ".ttf", ".otf", ".eot",
    ".pyc", ".pyo", ".class", ".jar", ".so", ".dll", ".dylib", ".exe",
    ".lock", ".log",
    ".min.js", ".min.css",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
}

LOCKFILES: set[str] = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "bun.lockb",
    "Cargo.lock", "Pipfile.lock", "poetry.lock", "uv.lock", "go.sum",
}

FIXTURE_HINTS: tuple[str, ...] = ("fixtures", "mock", "sample", "example", "test_data", "testdata")

MAX_FILE_SIZE: int = 1024 * 1024
IGNORE_MARKER: str = "scan-secrets: ignore"

PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("aws_access_key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("aws_secret_key", re.compile(r"(?i)aws.{0,20}[\"'](?:[A-Za-z0-9/+=]{40})[\"']")),
    ("generic_api_key", re.compile(r"(?i)(api[_-]?key|secret[_-]?key|access[_-]?token)[\"'\s]*[:=][\"'\s]*[A-Za-z0-9_\-]{16,}")),
    ("github_token", re.compile(r"gh[pousr]_[A-Za-z0-9]{36,}")),
    ("slack_token", re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}")),
    ("anthropic_key", re.compile(r"sk-ant-[A-Za-z0-9_-]{40,}")),
    ("openai_key_legacy", re.compile(r"sk-[A-Za-z0-9]{32,}")),
    ("openai_key_proj", re.compile(r"sk-proj-[A-Za-z0-9_-]{40,}")),
    ("private_key", re.compile(r"-----BEGIN (RSA |EC |DSA |OPENSSH |)PRIVATE KEY-----")),
    ("jwt", re.compile(r"eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}")),
]

HIGH_ENTROPY_TOKEN: re.Pattern[str] = re.compile(r"[A-Za-z0-9_\-+/=]{32,}")


def shannon_entropy(s: str) -> float:
    """Return Shannon entropy in bits per character for the given string."""
    if not s:
        return 0.0
    counts = Counter(s)
    length = len(s)
    return -sum((c / length) * math.log2(c / length) for c in counts.values())


def redact(match: str) -> str:
    """Return a redacted preview of a matched secret keeping first and last 4 chars."""
    trimmed = match.strip()
    if len(trimmed) <= 12:
        return "REDACTED"
    prefix = trimmed[:4]
    suffix = trimmed[-4:]
    preview = f"{prefix}...REDACTED...{suffix}"
    return preview[:60]


def should_skip_path(path: Path, root: Path) -> bool:
    """Return True if path is in an ignored directory."""
    try:
        rel = path.relative_to(root)
    except ValueError:
        rel = path
    return any(part in SKIP_DIRS for part in rel.parts)


def should_skip_file(path: Path) -> bool:
    """Return True if a file should be skipped based on name, extension, or size."""
    name = path.name
    if name in LOCKFILES:
        return True
    suffixes = "".join(path.suffixes).lower()
    if any(suffixes.endswith(ext) for ext in SKIP_EXTS):
        return True
    if path.suffix.lower() in SKIP_EXTS:
        return True
    lower_path = str(path).lower()
    if any(hint in lower_path for hint in FIXTURE_HINTS):
        return True
    try:
        if path.stat().st_size > MAX_FILE_SIZE:
            return True
    except OSError:
        return True
    return False


def is_binary(path: Path) -> bool:
    """Return True if a file appears to be binary (null bytes in first 8KB)."""
    try:
        with path.open("rb") as fh:
            chunk = fh.read(8192)
        return b"\x00" in chunk
    except OSError:
        return True


def scan_file(path: Path) -> list[dict[str, object]]:
    """Scan a single file for known secret patterns and high-entropy tokens."""
    findings: list[dict[str, object]] = []
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as fh:
            for lineno, line in enumerate(fh, start=1):
                if IGNORE_MARKER in line:
                    continue
                stripped = line.rstrip("\n")
                seen_spans: list[tuple[int, int]] = []
                for name, pattern in PATTERNS:
                    for m in pattern.finditer(stripped):
                        seen_spans.append(m.span())
                        findings.append({
                            "file": str(path),
                            "line": lineno,
                            "pattern": name,
                            "severity": "P1",
                            "preview": redact(m.group(0)),
                        })
                for m in HIGH_ENTROPY_TOKEN.finditer(stripped):
                    span = m.span()
                    if any(s[0] <= span[0] < s[1] or s[0] < span[1] <= s[1] for s in seen_spans):
                        continue
                    token = m.group(0)
                    if len(set(token)) < 16:
                        continue
                    if shannon_entropy(token) <= 4.5:
                        continue
                    findings.append({
                        "file": str(path),
                        "line": lineno,
                        "pattern": "high_entropy",
                        "severity": "P2",
                        "preview": redact(token),
                    })
    except OSError as exc:
        print(json.dumps({"error": f"read failed for {path}: {exc}"}), file=sys.stderr)
    return findings


def scan_path(root: Path) -> tuple[int, list[dict[str, object]]]:
    """Walk root and scan every eligible file. Return (scanned_count, findings)."""
    scanned = 0
    findings: list[dict[str, object]] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if should_skip_path(path, root):
            continue
        if should_skip_file(path):
            continue
        if is_binary(path):
            continue
        scanned += 1
        findings.extend(scan_file(path))
    return scanned, findings


def main() -> int:
    """CLI entry: parse args, scan, print JSON, return exit code."""
    parser = argparse.ArgumentParser(description="Scan a tree for leaked secrets.")
    parser.add_argument("path", nargs="?", default=".", help="Root path to scan (default '.')")
    args = parser.parse_args()
    root = Path(args.path).resolve()
    if not root.exists():
        print(json.dumps({"error": f"path does not exist: {root}"}), file=sys.stderr)
        return 2
    try:
        scanned, findings = scan_path(root)
    except Exception as exc:
        print(json.dumps({"error": f"scan failed: {exc}"}), file=sys.stderr)
        return 2
    output = {
        "dimension": "security",
        "tool": "scan_secrets",
        "scanned_files": scanned,
        "findings": findings,
    }
    print(json.dumps(output, indent=2))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
