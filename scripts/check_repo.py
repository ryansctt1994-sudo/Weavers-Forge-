#!/usr/bin/env python3
"""Repository readiness checks for Weaver Forge.

This script intentionally uses only the Python standard library so it can run
locally or in GitHub Actions without installing dependencies.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "README.md",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "ROADMAP.md",
    "PROJECT_PODS.md",
    "RECEIPT_TEMPLATE.md",
    "WITNESS_REVIEW_TEMPLATE.md",
    "WELCOME.md",
]

REQUIRED_README_PHRASES = [
    "Weaver Forge — Daily Commit Lab",
    "Build. Test. Commit. Receipt. Repeat.",
    "No commit. No claim. No receipt. No authority.",
    "https://discord.gg/2cQ22HPnK",
]

ALLOWED_TEMPLATE_PLACEHOLDERS = {
    "RECEIPT_TEMPLATE.md": [
        "(Short description)",
        "(Be precise)",
        "(Important)",
        "@handle",
        "YYYY-MM-DD",
    ],
    "WITNESS_REVIEW_TEMPLATE.md": [
        "(Link to receipt / PR / commit)",
        "@handle",
        "YYYY-MM-DD",
    ],
}

LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    sys.exit(1)


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        fail(f"{path.relative_to(ROOT)} is not valid UTF-8: {exc}")


def check_required_files() -> None:
    for relative in REQUIRED_FILES:
        path = ROOT / relative
        if not path.exists():
            fail(f"missing required file: {relative}")
        if not path.is_file():
            fail(f"required path is not a file: {relative}")
        if path.stat().st_size == 0:
            fail(f"required file is empty: {relative}")


def check_markdown_files() -> None:
    for path in sorted(ROOT.rglob("*.md")):
        text = read(path)
        relative = path.relative_to(ROOT).as_posix()
        if not text.endswith("\n"):
            fail(f"{relative} must end with a newline")
        if "link in announcements" in text.lower():
            fail(f"{relative} still contains the old Discord placeholder")
        if "TODO" in text:
            fail(f"{relative} contains TODO")


def check_readme_contract() -> None:
    readme = read(ROOT / "README.md")
    for phrase in REQUIRED_README_PHRASES:
        if phrase not in readme:
            fail(f"README.md missing required phrase: {phrase}")


def check_internal_links() -> None:
    for path in sorted(ROOT.rglob("*.md")):
        text = read(path)
        relative = path.relative_to(ROOT).as_posix()
        for match in LINK_RE.finditer(text):
            target = match.group(1).strip()
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            if target.startswith("/"):
                target_path = ROOT / target.lstrip("/")
            else:
                target_path = path.parent / target.split("#", 1)[0]
            if not target_path.exists():
                fail(f"{relative} has broken internal link: {target}")


def check_template_placeholders_are_scoped() -> None:
    for path in sorted(ROOT.rglob("*.md")):
        relative = path.relative_to(ROOT).as_posix()
        text = read(path)
        if relative in ALLOWED_TEMPLATE_PLACEHOLDERS:
            allowed = ALLOWED_TEMPLATE_PLACEHOLDERS[relative]
            scrubbed = text
            for placeholder in allowed:
                scrubbed = scrubbed.replace(placeholder, "")
            if "YYYY-MM-DD" in scrubbed or "@handle" in scrubbed:
                fail(f"{relative} has an unexpected placeholder")
        else:
            if "YYYY-MM-DD" in text or "@handle" in text:
                fail(f"{relative} contains template placeholder text outside a template")


def main() -> int:
    check_required_files()
    check_markdown_files()
    check_readme_contract()
    check_internal_links()
    check_template_placeholders_are_scoped()
    print("PASS: Weaver Forge repository readiness checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
