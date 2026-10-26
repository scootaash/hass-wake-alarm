"""scripts/set_version.py, run against copies of the real repo files.

Using the real files means a reformatted manifest, banner or README example
fails here rather than in the release workflow (or worse, ships a release
whose manifest still names the old version: the card's cache-bust).
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "set_version.py"
FILES = [
    "custom_components/wake_alarm/manifest.json",
    "card/package.json",
    "card/package-lock.json",
    "card/src/wake-alarm-card.ts",
    "README.md",
    "CHANGELOG.md",
]


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    for rel in FILES:
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / rel, tmp_path / rel)
    # The real CHANGELOG usually carries an "## Unreleased" section between
    # releases; drop it so each test sets up exactly the sections it means to.
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text(
        re.sub(
            r"^## Unreleased[ \t]*\n.*?(?=^## )",
            "",
            changelog.read_text(encoding="utf-8"),
            count=1,
            flags=re.MULTILINE | re.DOTALL,
        ),
        encoding="utf-8",
    )
    return tmp_path


def _run(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args, "--root", str(repo)],
        capture_output=True,
        text=True,
    )


def _add_unreleased(repo: Path, body: str) -> None:
    path = repo / "CHANGELOG.md"
    text = path.read_text(encoding="utf-8")
    first = text.index("\n## ")
    path.write_text(
        text[:first] + f"\n## Unreleased\n\n{body}\n" + text[first:],
        encoding="utf-8",
    )


def test_sets_every_version(repo: Path) -> None:
    _add_unreleased(repo, "### Fixed\n\n- A thing.")
    notes = repo / "notes.md"

    result = _run(repo, "9.8.7", "--date", "2030-01-02", "--notes-out", str(notes))

    assert result.returncode == 0, result.stderr
    manifest = json.loads(
        (repo / "custom_components/wake_alarm/manifest.json").read_text()
    )
    assert manifest["version"] == "9.8.7"
    package = json.loads((repo / "card/package.json").read_text())
    assert package["version"] == "9.8.7"
    lock = json.loads((repo / "card/package-lock.json").read_text())
    assert lock["version"] == "9.8.7"
    assert lock["packages"][""]["version"] == "9.8.7"
    assert "WAKE-ALARM-CARD %c v9.8.7 " in (
        repo / "card/src/wake-alarm-card.ts"
    ).read_text()
    assert "/wake_alarm/wake-alarm-card.js?v=9.8.7" in (repo / "README.md").read_text()

    changelog = (repo / "CHANGELOG.md").read_text()
    assert "## Unreleased" not in changelog
    assert "\n## 9.8.7 — 2030-01-02\n" in changelog
    assert notes.read_text() == "### Fixed\n\n- A thing.\n"


def test_rerun_is_a_no_op_and_reuses_the_dated_section(repo: Path) -> None:
    _add_unreleased(repo, "- A thing.")
    assert _run(repo, "9.8.7", "--date", "2030-01-02").returncode == 0
    before = {rel: (repo / rel).read_bytes() for rel in FILES}
    notes = repo / "notes.md"

    result = _run(repo, "9.8.7", "--date", "2031-12-31", "--notes-out", str(notes))

    assert result.returncode == 0, result.stderr
    assert {rel: (repo / rel).read_bytes() for rel in FILES} == before
    assert notes.read_text() == "- A thing.\n"


def test_no_changelog_section_leaves_notes_empty(repo: Path) -> None:
    notes = repo / "notes.md"

    result = _run(repo, "9.8.7", "--notes-out", str(notes))

    assert result.returncode == 0, result.stderr
    assert notes.read_text() == ""


@pytest.mark.parametrize("bad", ["v1.2.3", "1.2", "1.2.3-beta.1", ""])
def test_rejects_malformed_versions(repo: Path, bad: str) -> None:
    before = {rel: (repo / rel).read_bytes() for rel in FILES}

    result = _run(repo, bad)

    assert result.returncode != 0
    assert {rel: (repo / rel).read_bytes() for rel in FILES} == before


def test_fails_loudly_if_the_banner_format_changes(repo: Path) -> None:
    card = repo / "card/src/wake-alarm-card.ts"
    card.write_text(card.read_text().replace("WAKE-ALARM-CARD", "WAKE ALARM"))

    result = _run(repo, "9.8.7")

    assert result.returncode != 0
    assert "wake-alarm-card.ts" in result.stderr
