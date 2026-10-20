#!/usr/bin/env python3
"""Contract tests for scripts/check-changelog.py.

Fixtures are temporary directories. Git cases build a temporary repository.
Cleanup is unittest teardown. The checker is executed as a process so the
tests follow the CLI contract rather than its helpers.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "check-changelog.py"
REPO = SCRIPT.parent.parent
EM = "\u2014"

NOTE = "- Shipped a user-visible change with a practical effect.\n"
OLDER = "- Previous user-visible change stayed available.\n"
REPO_NOTE = "- Recorded a documentation follow-up without a plugin version bump.\n"
_UNSET = object()


def repo_heading(day: str = "2026-10-19") -> str:
    return f"## Repository updates {EM} {day}"


def version_heading(version: str, day: str = "2026-10-19") -> str:
    return f"## {version} {EM} {day}"


def changelog_text(
    sections: list[tuple[str, str, str]],
    *,
    repo: bool = True,
    repo_day: str = "2026-10-19",
    repo_body: str = REPO_NOTE,
) -> str:
    parts = ["# Changelog\n", "\n", "User-visible changes, newest first.\n"]
    if repo:
        parts.extend(["\n", repo_heading(repo_day), "\n", "\n", repo_body])
        if not repo_body.endswith("\n"):
            parts.append("\n")
    for version, day, body in sections:
        parts.extend(["\n", version_heading(version, day), "\n", "\n", body])
        if body and not body.endswith("\n"):
            parts.append("\n")
    return "".join(parts)


def standard_changelog(version: str = "0.4.9", day: str = "2026-10-19", notes: str = NOTE) -> str:
    sections = [(version, day, notes)]
    if version != "0.4.8":
        sections.append(("0.4.8", "2026-10-18", OLDER))
    return changelog_text(sections)


class ReleaseNoteContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def write_tree(
        self,
        version: str = "0.4.9",
        *,
        metadata_version: str | None = None,
        entry_version: str | None = None,
        claude_version: str | None = None,
        codex_version: str | None = None,
        claude_name: object = "autarkeia",
        codex_name: object = "autarkeia",
        plugins: object = _UNSET,
        readme_version: str | None = None,
        changelog: str | None = None,
        marketplace_raw: str | None = None,
        claude_raw: str | None = None,
        codex_raw: str | None = None,
        readme: str | None = None,
    ) -> None:
        metadata_version = version if metadata_version is None else metadata_version
        entry_version = version if entry_version is None else entry_version
        claude_version = version if claude_version is None else claude_version
        codex_version = version if codex_version is None else codex_version
        readme_version = version if readme_version is None else readme_version
        if plugins is _UNSET:
            # A decoy at index 0 must not be read as the autarkeia plugin.
            plugins = [
                {"name": "other-plugin", "version": "9.9.9"},
                {"name": "autarkeia", "source": "./autarkeia", "version": entry_version},
            ]
        if marketplace_raw is None:
            marketplace = {
                "name": "autarkeia-plugin",
                "metadata": {"description": "Autarkeia", "version": metadata_version},
                "plugins": plugins,
            }
            self._put(f"{MARKETPLACE}", json.dumps(marketplace, indent=2) + "\n")
        else:
            self._put(MARKETPLACE, marketplace_raw)
        if claude_raw is None:
            self._put(
                CLAUDE_PLUGIN,
                json.dumps({"name": claude_name, "version": claude_version}, indent=2) + "\n",
            )
        else:
            self._put(CLAUDE_PLUGIN, claude_raw)
        if codex_raw is None:
            self._put(
                CODEX_PLUGIN,
                json.dumps({"name": codex_name, "version": codex_version}, indent=2) + "\n",
            )
        else:
            self._put(CODEX_PLUGIN, codex_raw)
        if readme is None:
            readme = f"# Autarkeia v{readme_version}\n\nA living record.\n"
        self._put("README.md", readme)
        self._put("CHANGELOG.md", standard_changelog(version) if changelog is None else changelog)
        self._put("autarkeia/skills/note.txt", "base\n")
        self._put("vault-template/note.txt", "base\n")
        self._put("tools/note.txt", "base\n")
        self._put("docs/getting-started.md", "Guide.\n")

    def _put(self, relative: str, text: str) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def run_check(self, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--root", str(self.root), *args],
            cwd=cwd or REPO,
            capture_output=True,
            text=True,
            shell=False,
            check=False,
        )

    def assert_ok(self, proc: subprocess.CompletedProcess[str]) -> None:
        blob = proc.stdout + proc.stderr
        self.assertEqual(proc.returncode, 0, blob)
        self.assertNotIn("Traceback", blob)

    def assert_fails(self, proc: subprocess.CompletedProcess[str], *needles: str) -> None:
        blob = proc.stdout + proc.stderr
        self.assertNotEqual(proc.returncode, 0, blob)
        self.assertNotIn("Traceback", blob)
        for needle in needles:
            self.assertIn(needle, blob)

    def commit(self) -> str:
        _git(self.root, "init")
        _git(self.root, "add", "-A")
        _git(
            self.root,
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.com",
            "-c",
            "commit.gpgsign=false",
            "-c",
            "core.hooksPath=/dev/null",
            "commit",
            "--no-verify",
            "-m",
            "base",
        )
        return _git(self.root, "rev-parse", "HEAD").strip()

    def test_baseline_repository_updates_pass_from_script_parent_not_cwd(self) -> None:
        # Empty cwd would fail if the checker used the working directory as the root.
        proc = subprocess.run(
            [sys.executable, str(SCRIPT)],
            cwd=self.root,
            capture_output=True,
            text=True,
            shell=False,
            check=False,
        )
        self.assert_ok(proc)

    def test_synthetic_repository_updates_heading_is_not_a_version(self) -> None:
        self.write_tree()
        self.assert_ok(self.run_check())

    def test_release_date_need_not_be_today(self) -> None:
        self.write_tree(
            changelog=changelog_text(
                [("0.4.9", "2024-02-29", NOTE), ("0.4.8", "2024-02-28", OLDER)]
            )
        )
        self.assert_ok(self.run_check())

    def test_plugin_is_found_by_name_not_index(self) -> None:
        self.write_tree(
            plugins=[
                {"name": "other-plugin", "version": "1.2.3"},
                {"name": "autarkeia", "version": "0.4.9"},
            ]
        )
        self.assert_ok(self.run_check())

    def test_substantive_bullet_allows_a_placeholder_sibling_and_the_word_todo(self) -> None:
        notes = (
            "- TODO\n"
            "- Documented the TODO list behaviour for contributors.\n"
        )
        self.write_tree(changelog=standard_changelog(notes=notes))
        self.assert_ok(self.run_check())

    def test_empty_historical_section_does_not_fail_the_current_release(self) -> None:
        self.write_tree(
            changelog=changelog_text(
                [("0.4.9", "2026-10-19", NOTE), ("0.4.8", "2026-10-18", "\n")]
            )
        )
        self.assert_ok(self.run_check())

    def test_each_version_site_mismatch(self) -> None:
        cases = {
            "metadata": {"metadata_version": "0.4.8"},
            "plugin-entry": {"entry_version": "0.4.8"},
            "claude": {"claude_version": "0.4.8"},
            "codex": {"codex_version": "0.4.8"},
        }
        labels = {
            "metadata": "metadata.version is 0.4.8",
            "plugin-entry": "plugin autarkeia version is 0.4.8",
            "claude": "autarkeia/.claude-plugin/plugin.json version is 0.4.8",
            "codex": "autarkeia/.codex-plugin/plugin.json version is 0.4.8",
        }
        for name, kwargs in cases.items():
            with self.subTest(site=name):
                self.write_tree(**kwargs)
                self.assert_fails(self.run_check(), "versions differ", labels[name])

    def test_leading_zero_version_is_rejected(self) -> None:
        self.write_tree(metadata_version="0.04.9")
        self.assert_fails(self.run_check(), "without leading zeros", "0.04.9")

    def test_missing_json_files(self) -> None:
        for relative in (MARKETPLACE, CLAUDE_PLUGIN, CODEX_PLUGIN):
            with self.subTest(path=relative):
                self.write_tree()
                (self.root / relative).unlink()
                self.assert_fails(self.run_check(), relative, "file not found")

    def test_malformed_json_has_no_traceback(self) -> None:
        self.write_tree(marketplace_raw="{not json\n")
        self.assert_fails(self.run_check(), MARKETPLACE, "invalid JSON")

    def test_name_wrong(self) -> None:
        self.write_tree(claude_name="other-plugin")
        self.assert_fails(self.run_check(), CLAUDE_PLUGIN, "other-plugin", "autarkeia")

    def test_name_wrong_type(self) -> None:
        self.write_tree(codex_raw='{"name": 12, "version": "0.4.9"}\n')
        self.assert_fails(self.run_check(), CODEX_PLUGIN, "name is not a string")

    def test_version_wrong_type(self) -> None:
        self.write_tree(claude_raw='{"name": "autarkeia", "version": 0.4}\n')
        self.assert_fails(self.run_check(), "must be a string", "number")

    def test_plugins_list_malformed(self) -> None:
        cases = {
            "object": {"name": "autarkeia", "version": "0.4.9"},
            "string-entry": ["autarkeia"],
            "two-autarkeia": [
                {"name": "autarkeia", "version": "0.4.9"},
                {"name": "autarkeia", "version": "0.4.9"},
            ],
            "none-named": [{"name": "other-plugin", "version": "0.4.9"}],
            "null": None,
        }
        for name, plugins in cases.items():
            with self.subTest(shape=name):
                self.write_tree(plugins=plugins)
                proc = self.run_check()
                if name in {"object", "null"}:
                    self.assert_fails(proc, "plugins must be a list")
                elif name == "string-entry":
                    self.assert_fails(proc, "not an object")
                else:
                    self.assert_fails(proc, "exactly one plugin named", "autarkeia")

    def test_invalid_calendar_dates(self) -> None:
        for day in ("2026-02-31", "2026-02-29", "2026-13-01"):
            with self.subTest(day=day):
                self.write_tree(
                    changelog=changelog_text([("0.4.9", day, NOTE), ("0.4.8", "2026-10-18", OLDER)])
                )
                self.assert_fails(self.run_check(), "invalid calendar date", day)

    def test_malformed_release_headings(self) -> None:
        bad = [
            f"## 0.4.9 - 2026-10-19",
            f"## 0.4.9 \u2013 2026-10-19",
            f"## v0.4.9 {EM} 2026-10-19",
            f"## 0.4.09 {EM} 2026-10-19",
            "## 0.4.9",
            f"## 0.4.9 {EM} 19-10-2026",
        ]
        for heading in bad:
            with self.subTest(heading=heading):
                body = (
                    "# Changelog\n\n"
                    + repo_heading()
                    + "\n\n"
                    + REPO_NOTE
                    + "\n"
                    + heading
                    + "\n\n"
                    + NOTE
                    + "\n"
                    + version_heading("0.4.8", "2026-10-18")
                    + "\n\n"
                    + OLDER
                )
                self.write_tree(changelog=body)
                self.assert_fails(self.run_check(), "malformed release heading")

    def test_duplicate_current_version(self) -> None:
        self.write_tree(
            changelog=changelog_text(
                [
                    ("0.4.9", "2026-10-19", NOTE),
                    ("0.4.9", "2026-10-20", "- Repeated the same version heading.\n"),
                ]
            )
        )
        self.assert_fails(self.run_check(), "duplicate version heading 0.4.9")

    def test_missing_current_notes(self) -> None:
        self.write_tree(
            changelog=changelog_text([("0.4.8", "2026-10-18", OLDER)])
        )
        self.assert_fails(self.run_check(), "missing notes for version 0.4.9")

    def test_empty_current_notes(self) -> None:
        self.write_tree(
            changelog=changelog_text(
                [("0.4.9", "2026-10-19", "\n"), ("0.4.8", "2026-10-18", OLDER)]
            )
        )
        self.assert_fails(self.run_check(), "notes are empty")

    def test_comment_only_notes_ignore_hidden_headings(self) -> None:
        hidden = (
            "<!--\n"
            f"{version_heading('9.9.9', '2020-01-01')}\n"
            "- Commented bullet must not count\n"
            "-->\n"
        )
        self.write_tree(
            changelog=changelog_text(
                [("0.4.9", "2026-10-19", hidden), ("0.4.8", "2026-10-18", OLDER)]
            )
        )
        proc = self.run_check()
        self.assert_fails(proc, "comments-only")
        self.assertNotIn("9.9.9", proc.stdout + proc.stderr)

    def test_fence_only_notes_ignore_hidden_headings(self) -> None:
        hidden = (
            "```markdown\n"
            f"{version_heading('9.9.9', '2020-01-01')}\n"
            "- Fenced bullet must not count\n"
            "```\n"
        )
        self.write_tree(
            changelog=changelog_text(
                [("0.4.9", "2026-10-19", hidden), ("0.4.8", "2026-10-18", OLDER)]
            )
        )
        proc = self.run_check()
        self.assert_fails(proc, "code-fence-only")
        self.assertNotIn("9.9.9", proc.stdout + proc.stderr)

    def test_hidden_fakes_do_not_reject_a_real_bullet(self) -> None:
        body = (
            "<!--\n"
            f"{version_heading('9.9.9', '2020-01-01')}\n"
            "- hidden\n"
            "-->\n"
            "```\n"
            f"{version_heading('8.8.8', '2020-01-02')}\n"
            "- also hidden\n"
            "```\n"
            "- Visible note that ships in this release.\n"
        )
        self.write_tree(
            changelog=changelog_text(
                [("0.4.9", "2026-10-19", body), ("0.4.8", "2026-10-18", OLDER)]
            )
        )
        self.assert_ok(self.run_check())

    def test_placeholder_only_notes(self) -> None:
        for bullet in ("- TODO", "- TBD", "- coming soon", "- placeholder", "- **TODO**"):
            with self.subTest(bullet=bullet):
                self.write_tree(
                    changelog=standard_changelog(notes=bullet + "\n")
                )
                self.assert_fails(self.run_check(), "placeholder-only")

    def test_heading_only_notes(self) -> None:
        self.write_tree(changelog=standard_changelog(notes="### Details\n"))
        self.assert_fails(self.run_check(), "heading-only")

    def test_separator_only_notes(self) -> None:
        self.write_tree(changelog=standard_changelog(notes="---\n"))
        self.assert_fails(self.run_check(), "separator-only")

    def test_paragraph_without_bullet_fails(self) -> None:
        self.write_tree(
            changelog=standard_changelog(notes="Users can install the plugin from GitHub.\n")
        )
        self.assert_fails(self.run_check(), "substantive bullet")

    def test_stale_top_version(self) -> None:
        self.write_tree(
            changelog=changelog_text(
                [
                    ("0.4.8", "2026-10-18", OLDER),
                    ("0.4.9", "2026-10-19", NOTE),
                ]
            )
        )
        proc = self.run_check()
        self.assert_fails(proc, "top version is 0.4.8", "0.4.9")
        self.assertNotIn("malformed", proc.stdout + proc.stderr)

    def test_readme_drift(self) -> None:
        self.write_tree(readme="# Autarkeia v0.4.8\n\nOverview.\n")
        self.assert_fails(self.run_check(), "README.md", "0.4.8", "0.4.9")

    def test_readme_title_must_match_the_pattern(self) -> None:
        self.write_tree(readme="# Autarkeia 0.4.9\n")
        self.assert_fails(self.run_check(), "README.md", "first title")

    def test_valid_numeric_version_bump(self) -> None:
        self.write_tree()
        base = self.commit()
        self.write_tree(
            "0.4.10",
            changelog=changelog_text(
                [
                    ("0.4.10", "2020-05-05", "- Raised the patch version and recorded the release.\n"),
                    ("0.4.9", "2026-10-19", NOTE),
                ]
            ),
        )
        self.assert_ok(self.run_check("--base-ref", base))

    def test_bump_lacking_new_notes_fails(self) -> None:
        self.write_tree()
        base = self.commit()
        # Manifests move to 0.4.10 and the changelog text stays on 0.4.9.
        self.write_tree("0.4.10", changelog=standard_changelog("0.4.9"))
        self.assert_fails(self.run_check("--base-ref", base), "0.4.10", "missing notes")

    def test_bump_reusing_a_base_section_fails(self) -> None:
        prepared = changelog_text(
            [
                ("0.4.10", "2026-10-20", "- Notes written before the version changed.\n"),
                ("0.4.9", "2026-10-19", NOTE),
            ]
        )
        self.write_tree(changelog=prepared)
        base = self.commit()
        self.write_tree("0.4.10", changelog=prepared)
        self.assert_fails(
            self.run_check("--base-ref", base),
            "already has a section",
            "newly added",
        )

    def test_downgrade_fails(self) -> None:
        self.write_tree(
            "0.4.10",
            changelog=changelog_text(
                [("0.4.10", "2026-10-20", "- Base release notes.\n")]
            ),
        )
        base = self.commit()
        self.write_tree(
            "0.4.9",
            changelog=changelog_text([("0.4.9", "2026-10-19", NOTE)]),
        )
        self.assert_fails(self.run_check("--base-ref", base), "strictly greater", "0.4.9", "0.4.10")

    def test_invalid_base_ref_fails_closed(self) -> None:
        self.write_tree()
        self.commit()
        missing = "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef"
        proc = self.run_check("--base-ref", missing)
        self.assert_fails(proc, missing, "could not be read")

    def test_base_ref_is_not_executed_as_an_option_or_shell(self) -> None:
        self.write_tree()
        self.commit()
        for ref in ("--version", "HEAD;echo injected", ""):
            with self.subTest(ref=ref):
                proc = self.run_check("--base-ref=" + ref)
                self.assert_fails(proc, "invalid base ref")

    def test_no_bump_documentation_update_passes(self) -> None:
        self.write_tree()
        base = self.commit()
        readme = (self.root / "README.md").read_text(encoding="utf-8")
        (self.root / "README.md").write_text(readme + "\nMore overview.\n", encoding="utf-8")
        guide = self.root / "docs" / "getting-started.md"
        guide.write_text(guide.read_text(encoding="utf-8") + "Another step.\n", encoding="utf-8")
        self.assert_ok(self.run_check("--base-ref", base))

    def test_clean_tree_matches_base(self) -> None:
        self.write_tree()
        base = self.commit()
        self.assert_ok(self.run_check("--base-ref", base))

    def test_version_mismatch_fails_even_when_diff_is_empty(self) -> None:
        self.write_tree(metadata_version="0.4.8")
        base = self.commit()
        self.assert_fails(self.run_check("--base-ref", base), "versions differ", "0.4.8")

    def wipe(self) -> None:
        for child in list(self.root.iterdir()):
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()

    def test_distributed_changes_without_changelog_fail(self) -> None:
        for relative in ("autarkeia/skills/note.txt", "vault-template/note.txt", "tools/note.txt"):
            with self.subTest(path=relative):
                self.wipe()
                self.write_tree()
                base = self.commit()
                target = self.root / relative
                target.write_text("changed\n", encoding="utf-8")
                self.assert_fails(
                    self.run_check("--base-ref", base),
                    "without a version bump",
                    "CHANGELOG.md",
                    relative,
                )

    def test_staged_distributed_change_without_changelog_fails(self) -> None:
        self.write_tree()
        base = self.commit()
        target = self.root / "tools" / "note.txt"
        target.write_text("staged change\n", encoding="utf-8")
        _git(self.root, "add", "tools/note.txt")
        self.assert_fails(
            self.run_check("--base-ref", base),
            "without a version bump",
            "tools/note.txt",
        )

    def test_distributed_change_with_changelog_notes_passes(self) -> None:
        self.write_tree()
        base = self.commit()
        for relative in ("autarkeia/skills/note.txt", "vault-template/note.txt", "tools/note.txt"):
            (self.root / relative).write_text("changed\n", encoding="utf-8")
        log = (self.root / "CHANGELOG.md").read_text(encoding="utf-8")
        log = log.replace(
            REPO_NOTE,
            REPO_NOTE + "- Noted a follow-up shipped without a plugin version bump.\n",
            1,
        )
        (self.root / "CHANGELOG.md").write_text(log, encoding="utf-8")
        self.assert_ok(self.run_check("--base-ref", base))

    def test_non_repo_base_ref_fails_closed(self) -> None:
        self.write_tree()
        self.assert_fails(self.run_check("--base-ref", "HEAD"), "HEAD", "could not be read")


MARKETPLACE = ".claude-plugin/marketplace.json"
CLAUDE_PLUGIN = "autarkeia/.claude-plugin/plugin.json"
CODEX_PLUGIN = "autarkeia/.codex-plugin/plugin.json"


def _git(root: Path, *args: str) -> str:
    env = os.environ.copy()
    env["GIT_AUTHOR_NAME"] = "Test"
    env["GIT_AUTHOR_EMAIL"] = "test@example.com"
    env["GIT_COMMITTER_NAME"] = "Test"
    env["GIT_COMMITTER_EMAIL"] = "test@example.com"
    proc = subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        env=env,
        shell=False,
        check=False,
    )
    if proc.returncode != 0:
        raise AssertionError(proc.stderr or proc.stdout or f"git exited {proc.returncode}")
    return proc.stdout


if __name__ == "__main__":
    unittest.main()
