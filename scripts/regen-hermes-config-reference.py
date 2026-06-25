#!/usr/bin/env python3
"""
regen-hermes-config-reference.py

Regenerate the sanitized Hermes config.yaml reference snapshot tracked by chezmoi.

It reads the LIVE ~/.hermes/config.yaml, replaces every real secret value with a
chezmoi-style {{ env "VAR" }} placeholder, runs a leak scan to guarantee no
plaintext secret survives, and writes the result to:

    <chezmoi-source>/.hermes-reference/config.yaml.sanitized

The live config is never modified. Secrets are never printed to stdout.

Usage:
    ./scripts/regen-hermes-config-reference.py            # write the snapshot
    ./scripts/regen-hermes-config-reference.py --check    # dry run: report only, exit 1 if it would change
    ./scripts/regen-hermes-config-reference.py --stdout    # print sanitized output to stdout (still leak-scanned)

Exit codes:
    0  success (or --check found no drift)
    1  --check found drift, OR a leak was detected (snapshot NOT written)
    2  input/config problem (missing files, etc.)
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

HOME = Path.home()
LIVE_CONFIG = HOME / ".hermes" / "config.yaml"

# Patterns that identify a line carrying a real secret, mapped to the env var
# name the placeholder should reference. Order matters only for readability.
#
# Each rule: (compiled regex matching the *stripped* line, env_var_name)
# The regex must capture nothing; we rebuild the line preserving indentation.
SECRET_RULES = [
    # LiteLLM / model api_key:  "api_key: sk-...."   -> LM_API_KEY
    (re.compile(r"^api_key:\s*sk-\S+"), "api_key", "LM_API_KEY"),
    # Jira token
    (re.compile(r"^JIRA_API_TOKEN:\s*\S+"), "JIRA_API_TOKEN", "JIRA_API_TOKEN"),
    # Confluence token
    (re.compile(r"^CONFLUENCE_API_TOKEN:\s*\S+"), "CONFLUENCE_API_TOKEN", "CONFLUENCE_API_TOKEN"),
]

# Final safety net: if any of these appear in the output, we refuse to write.
LEAK_PATTERNS = re.compile(r"sk-[A-Za-z0-9]{12,}|ATATT[A-Za-z0-9]{12,}|BWS_[A-Za-z0-9]{12,}")


def chezmoi_source_path() -> Path:
    try:
        out = subprocess.run(
            ["chezmoi", "source-path"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        return Path(out)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        sys.stderr.write(f"error: could not determine chezmoi source path: {e}\n")
        sys.exit(2)


def sanitize(raw: str) -> tuple[str, list[tuple[int, str]]]:
    """Return (sanitized_text, replacements). replacements = [(lineno, key), ...]."""
    lines = raw.split("\n")
    replacements: list[tuple[int, str]] = []
    for i, ln in enumerate(lines):
        stripped = ln.strip()
        if not stripped:
            continue
        indent = ln[: len(ln) - len(ln.lstrip())]
        for rule, key, var in SECRET_RULES:
            if rule.match(stripped):
                lines[i] = f'{indent}{key}: {{{{ env "{var}" }}}}'
                replacements.append((i + 1, f"{key} -> {var}"))
                break
    return "\n".join(lines), replacements


def main() -> int:
    ap = argparse.ArgumentParser(description="Regenerate sanitized Hermes config reference.")
    ap.add_argument("--check", action="store_true",
                    help="Dry run: report what would change, exit 1 on drift. Do not write.")
    ap.add_argument("--stdout", action="store_true",
                    help="Print sanitized output to stdout instead of writing the file.")
    args = ap.parse_args()

    if not LIVE_CONFIG.is_file():
        sys.stderr.write(f"error: live config not found: {LIVE_CONFIG}\n")
        return 2

    raw = LIVE_CONFIG.read_text()
    sanitized, replacements = sanitize(raw)

    # Leak scan — the hard gate. Never write/emit if a secret survived.
    leaks = LEAK_PATTERNS.findall(sanitized)
    if leaks:
        sys.stderr.write(
            "REFUSING: leak scan found "
            f"{len(leaks)} secret-looking token(s) still in the sanitized output.\n"
            "A new secret pattern likely appeared in config.yaml that this script\n"
            "doesn't know how to redact. Update SECRET_RULES, then re-run.\n"
        )
        return 1

    dest = chezmoi_source_path() / ".hermes-reference" / "config.yaml.sanitized"

    if args.stdout:
        sys.stdout.write(sanitized)
        if not sanitized.endswith("\n"):
            sys.stdout.write("\n")
        _report(replacements, dest, wrote=False)
        return 0

    existing = dest.read_text() if dest.is_file() else None
    would_change = existing != sanitized

    if args.check:
        if would_change:
            print(f"DRIFT: {dest} is out of date — run without --check to update.")
            _report(replacements, dest, wrote=False)
            return 1
        print(f"OK: {dest} is up to date ({len(replacements)} secret(s) redacted).")
        return 0

    if not would_change:
        print(f"No change: {dest} already current ({len(replacements)} secret(s) redacted).")
        return 0

    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(sanitized)
    _report(replacements, dest, wrote=True)
    return 0


def _report(replacements: list[tuple[int, str]], dest: Path, wrote: bool) -> None:
    verb = "Wrote" if wrote else "Would write"
    print(f"\n{verb} sanitized reference -> {dest}")
    print(f"Secrets redacted: {len(replacements)}")
    for lineno, what in replacements:
        print(f"  L{lineno}: {what}")
    print("Leak scan: clean (0 plaintext secrets)")


if __name__ == "__main__":
    sys.exit(main())
