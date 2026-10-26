#!/usr/bin/env python3
"""Set the release version everywhere the repo records it.

Run by .github/workflows/release.yml; also safe to run by hand.

The manifest version matters most: it's the version Home Assistant reports,
and the card is served as /wake_alarm/wake-alarm-card.js?v=<version>, so it is
also the browser cache-bust for the card. A release whose manifest still names
the previous version leaves browsers on the cached old card. The card package,
the card's console banner and the README's YAML example are kept in step.

Usage:
    python scripts/set_version.py X.Y.Z [--notes-out FILE] [--date YYYY-MM-DD]

A "## Unreleased" CHANGELOG heading becomes "## X.Y.Z — <date>". With
--notes-out, that version's CHANGELOG section is written to FILE for use as
release notes (FILE is left empty if there is no such section).

Doesn't rebuild the card bundle: run `npm run build` in card/ afterwards.
Exits non-zero if a version string it must update isn't found, so a format
change can't silently ship a stale version.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")

MANIFEST = Path("custom_components/wake_alarm/manifest.json")
PACKAGE = Path("card/package.json")
PACKAGE_LOCK = Path("card/package-lock.json")
CARD_SOURCE = Path("card/src/wake-alarm-card.ts")
README = Path("README.md")
CHANGELOG = Path("CHANGELOG.md")


def _replace(
    root: Path, rel: Path, pattern: str, repl: str, *, exactly_one: bool
) -> None:
    path = root / rel
    text = path.read_text(encoding="utf-8")
    new, count = re.subn(pattern, repl, text, flags=re.MULTILINE)
    if exactly_one and count != 1:
        raise SystemExit(
            f"{rel}: expected exactly one match for {pattern!r}, found {count}"
        )
    if count == 0:
        print(f"warning: {rel}: no match for {pattern!r}; left unchanged",
              file=sys.stderr)
    path.write_text(new, encoding="utf-8")


def _set_json(root: Path, rel: Path, version: str) -> None:
    path = root / rel
    data = json.loads(path.read_text(encoding="utf-8"))
    data["version"] = version
    # package-lock.json repeats the root package's version here.
    root_package = data.get("packages", {}).get("")
    if root_package is not None:
        root_package["version"] = version
    # npm's own format, so an unchanged file round-trips byte for byte.
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def _changelog(root: Path, version: str, date: str) -> str:
    """Date an Unreleased section; return this version's section body."""
    path = root / CHANGELOG
    text = path.read_text(encoding="utf-8")
    text = re.sub(
        r"^## Unreleased[ \t]*$",
        f"## {version} — {date}",
        text,
        count=1,
        flags=re.MULTILINE,
    )
    path.write_text(text, encoding="utf-8")
    match = re.search(
        rf"^## {re.escape(version)}\b[^\n]*\n(.*?)(?=^## |\Z)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    return match.group(1).strip() + "\n" if match else ""


def set_version(root: Path, version: str, date: str) -> str:
    """Write ``version`` into every file; return the release notes."""
    _replace(root, MANIFEST, r'("version":\s*")[^"]*(")', rf"\g<1>{version}\g<2>",
             exactly_one=True)
    _set_json(root, PACKAGE, version)
    _set_json(root, PACKAGE_LOCK, version)
    _replace(root, CARD_SOURCE, r"(WAKE-ALARM-CARD %c v)[0-9][^\s\"'`]*",
             rf"\g<1>{version}", exactly_one=True)
    _replace(root, README, r"(/wake_alarm/wake-alarm-card\.js\?v=)[0-9][^\s\"'`]*",
             rf"\g<1>{version}", exactly_one=False)
    return _changelog(root, version, date)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("version", help="X.Y.Z, no leading v")
    parser.add_argument("--notes-out", type=Path,
                        help="write this version's CHANGELOG section here")
    parser.add_argument("--date", default=dt.date.today().isoformat(),
                        help="date for a newly dated CHANGELOG heading")
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parent.parent,
                        help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    if not VERSION_RE.match(args.version):
        parser.error(f"version must look like 1.2.3, got {args.version!r}")

    notes = set_version(args.root, args.version, args.date)
    if args.notes_out is not None:
        args.notes_out.write_text(notes, encoding="utf-8")
    print(f"set version {args.version}"
          + ("" if notes else " (no CHANGELOG section for it)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
