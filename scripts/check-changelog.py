#!/usr/bin/env python3
"""Validate Autarkeia release versions and changelog notes.

The repository root defaults to the parent of this script, not the current
working directory. Pass ``--base-ref`` to compare a git revision. Git is
invoked with an argument list only; ref text is never sent through a shell.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

EM_DASH = "\u2014"
VERSION_TEXT = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
README_TITLE = re.compile(
    r"^# Autarkeia v(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$"
)
VERSION_HEADING = re.compile(
    rf"^## (?P<ver>(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)) {EM_DASH} "
    rf"(?P<date>\d{{4}}-\d{{2}}-\d{{2}})$"
)
REPO_HEADING = re.compile(
    rf"^## Repository updates {EM_DASH} (?P<date>\d{{4}}-\d{{2}}-\d{{2}})$"
)
FENCE_OPEN = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
BULLET = re.compile(r"^[ \t]*(?:[-*+]|\d+[.)])[ \t]+(.*\S)[ \t]*$")
SEPARATOR = re.compile(r"^[ \t]*([-*_])\1{2,}[ \t]*$")
SUBHEADING = re.compile(r"^#{1,6}[ \t]+\S")
# A base ref is one git revision argument, never an option or a shell snippet.
REF_TEXT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/@^{}~-]*$")
PLACEHOLDER_COMPACT = {"todo", "tbd", "placeholder", "comingsoon"}

MARKETPLACE = ".claude-plugin/marketplace.json"
CLAUDE_PLUGIN = "autarkeia/.claude-plugin/plugin.json"
CODEX_PLUGIN = "autarkeia/.codex-plugin/plugin.json"
README = "README.md"
CHANGELOG = "CHANGELOG.md"
# Only these trees can ship without a plugin bump, and only with a changelog diff.
DISTRIBUTABLE = ("autarkeia", "vault-template", "tools")

METADATA_LABEL = f"{MARKETPLACE} metadata.version"
ENTRY_LABEL = f"{MARKETPLACE} plugin autarkeia version"
CLAUDE_LABEL = f"{CLAUDE_PLUGIN} version"
CODEX_LABEL = f"{CODEX_PLUGIN} version"


class GitFailure(Exception):
    """A git invocation failed. The message is safe to show as a validation error."""


@dataclass
class Section:
    version: tuple[int, int, int]
    line: int
    substantive: int = 0
    placeholder: int = 0
    separators: int = 0
    subheadings: int = 0
    prose: int = 0
    comments: int = 0
    fences: int = 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate Autarkeia versions and changelog notes."
    )
    parser.add_argument(
        "--root",
        default=None,
        help="Repository root. Defaults to the parent of this script, not the current directory.",
    )
    parser.add_argument(
        "--base-ref",
        default=None,
        help="Git revision to compare. A version change must be strictly greater and add release notes.",
    )
    args = parser.parse_args(argv)
    if args.root is None:
        root = Path(__file__).resolve().parent.parent
    else:
        root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        return _emit([f"root {root} is not a directory"])

    errors, canonical = _collect_versions(root)
    readme, readme_error = _read_text(root / README, README)
    if readme_error:
        errors.append(readme_error)
    elif readme is not None:
        errors.extend(_check_readme(readme, canonical))

    changelog, changelog_error = _read_text(root / CHANGELOG, CHANGELOG)
    if changelog_error:
        errors.append(changelog_error)
    elif changelog is not None:
        errors.extend(_check_changelog(changelog, canonical))

    if args.base_ref is not None:
        errors.extend(_check_base(root, args.base_ref, canonical))
    return _emit(errors)


def _emit(errors: list[str]) -> int:
    if not errors:
        return 0
    for error in errors:
        print(f"error: {error}", file=sys.stderr)
    return 1


def _collect_versions(
    root: Path,
) -> tuple[list[str], tuple[int, int, int] | None]:
    errors: list[str] = []
    found: list[tuple[str, tuple[int, int, int]]] = []

    payload, load_error = _load_json(root / MARKETPLACE, MARKETPLACE)
    if load_error:
        errors.append(load_error)
    elif not isinstance(payload, dict):
        errors.append(f"{MARKETPLACE}: must be a JSON object, got {_json_type(payload)}")
    else:
        metadata = payload.get("metadata")
        if not isinstance(metadata, dict):
            errors.append(
                f"{MARKETPLACE}: metadata must be a JSON object, got {_json_type(metadata)}"
            )
        else:
            _add_version(
                errors,
                found,
                METADATA_LABEL,
                metadata.get("version"),
                missing="version" not in metadata,
            )
        if "plugins" not in payload:
            errors.append(f"{MARKETPLACE}: missing plugins list")
        else:
            entry = _autarkeia_entry(errors, payload["plugins"], MARKETPLACE)
            if entry is not None:
                _add_version(
                    errors,
                    found,
                    ENTRY_LABEL,
                    entry.get("version"),
                    missing="version" not in entry,
                )

    for path, label in ((CLAUDE_PLUGIN, CLAUDE_LABEL), (CODEX_PLUGIN, CODEX_LABEL)):
        payload, load_error = _load_json(root / path, path)
        if load_error:
            errors.append(load_error)
            continue
        if not isinstance(payload, dict):
            errors.append(f"{path}: must be a JSON object, got {_json_type(payload)}")
            continue
        _check_plugin_name(errors, payload, path)
        _add_version(
            errors,
            found,
            label,
            payload.get("version"),
            missing="version" not in payload,
        )

    canonical: tuple[int, int, int] | None = None
    if len(found) == 4:
        values = {version for _, version in found}
        if len(values) == 1:
            canonical = found[0][1]
        else:
            detail = "; ".join(f"{label} is {_fmt(version)}" for label, version in found)
            errors.append(f"versions differ: {detail}")
    elif len({version for _, version in found}) > 1:
        detail = "; ".join(f"{label} is {_fmt(version)}" for label, version in found)
        errors.append(f"versions differ: {detail}")
    return errors, canonical


def _autarkeia_entry(errors: list[str], plugins: object, display: str) -> dict | None:
    if not isinstance(plugins, list):
        errors.append(f"{display}: plugins must be a list, got {_json_type(plugins)}")
        return None
    matches: list[dict] = []
    for index, entry in enumerate(plugins):
        if not isinstance(entry, dict):
            errors.append(f"{display}: plugins[{index}] is not an object")
            continue
        if "name" not in entry:
            errors.append(f"{display}: plugins[{index}] is missing name")
            continue
        name = entry["name"]
        if not isinstance(name, str):
            errors.append(
                f"{display}: plugins[{index}] name is not a string ({_json_type(name)})"
            )
            continue
        if name == "autarkeia":
            matches.append(entry)
    if len(matches) != 1:
        errors.append(
            f'{display}: expected exactly one plugin named "autarkeia", found {len(matches)}'
        )
        return None
    return matches[0]


def _check_plugin_name(errors: list[str], payload: dict, display: str) -> None:
    if "name" not in payload:
        errors.append(f"{display}: missing name")
        return
    name = payload["name"]
    if not isinstance(name, str):
        errors.append(f"{display}: name is not a string ({_json_type(name)})")
        return
    if name != "autarkeia":
        errors.append(f'{display}: name is {name!r}, expected "autarkeia"')


def _add_version(
    errors: list[str],
    found: list[tuple[str, tuple[int, int, int]]],
    label: str,
    value: object,
    *,
    missing: bool,
) -> None:
    if missing:
        errors.append(f"{label}: missing")
        return
    if isinstance(value, bool) or not isinstance(value, str):
        errors.append(f"{label}: must be a string, got {_json_type(value)}")
        return
    parsed = _parse_version(value)
    if parsed is None:
        errors.append(f"{label}: {value!r} must be numeric X.Y.Z without leading zeros")
        return
    found.append((label, parsed))


def _check_readme(text: str, canonical: tuple[int, int, int] | None) -> list[str]:
    first = ""
    for line in text.splitlines():
        if line.strip() == "":
            continue
        first = line.rstrip()
        break
    if first == "":
        return ['README.md: missing first title, expected "# Autarkeia vX.Y.Z"']
    match = README_TITLE.fullmatch(first)
    if match is None:
        return [f"README.md: first title is {first!r}, expected \"# Autarkeia vX.Y.Z\""]
    found = (int(match.group(1)), int(match.group(2)), int(match.group(3)))
    if canonical is not None and found != canonical:
        return [
            f"README.md: first title is '# Autarkeia v{_fmt(found)}', "
            f"expected '# Autarkeia v{_fmt(canonical)}'"
        ]
    return []


def _check_changelog(text: str, canonical: tuple[int, int, int] | None) -> list[str]:
    parser = _ChangelogParser()
    parser.parse(text)
    errors = list(parser.errors)
    seen: dict[tuple[int, int, int], int] = {}
    for section in parser.sections:
        previous = seen.get(section.version)
        if previous is None:
            seen[section.version] = section.line
            continue
        errors.append(
            f"{CHANGELOG}:{section.line}: duplicate version heading {_fmt(section.version)} "
            f"(first at line {previous})"
        )
    if canonical is None:
        return errors
    matched = [section for section in parser.sections if section.version == canonical]
    if not parser.sections or parser.sections[0].version != canonical:
        if parser.sections:
            errors.append(
                f"{CHANGELOG}:{parser.sections[0].line}: top version is "
                f"{_fmt(parser.sections[0].version)}, but current version {_fmt(canonical)} "
                "must be the first version heading"
            )
        if not matched:
            errors.append(f"{CHANGELOG}: missing notes for version {_fmt(canonical)}")
    for section in matched:
        problem = _substance_problem(section)
        if problem:
            errors.append(
                f"{CHANGELOG}:{section.line}: version {_fmt(section.version)} notes are {problem}"
            )
    return errors


class _ChangelogParser:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.sections: list[Section] = []
        self.current: Section | None = None
        self.in_comment = False
        self.in_fence = False
        self.fence_char = ""
        self.fence_len = 0

    def parse(self, text: str) -> None:
        for lineno, raw in enumerate(text.splitlines(), 1):
            self._line(lineno, raw)

    def _line(self, lineno: int, raw: str) -> None:
        if self.in_fence:
            if _fence_close(raw, self.fence_char, self.fence_len):
                self.in_fence = False
            self._touch("fence")
            return
        if self.in_comment:
            visible, self.in_comment, _saw = _strip_comments(raw, True)
            if self.in_comment or visible.strip() == "":
                self._touch("comment")
                return
            opened = _fence_open(visible)
            if opened is not None:
                self.fence_char, self.fence_len = opened
                self.in_fence = True
                self._touch("fence")
                return
            self._classify(lineno, visible.rstrip(), saw_comment=True)
            return

        opened = _fence_open(raw)
        if opened is not None:
            self.fence_char, self.fence_len = opened
            self.in_fence = True
            self._touch("fence")
            return
        visible, self.in_comment, saw_comment = _strip_comments(raw, False)
        if visible.strip() == "":
            self._touch("comment" if saw_comment else "blank")
            return
        opened = _fence_open(visible)
        if opened is not None:
            self.fence_char, self.fence_len = opened
            self.in_fence = True
            self._touch("fence")
            return
        self._classify(lineno, visible.rstrip(), saw_comment=saw_comment)

    def _classify(self, lineno: int, line: str, *, saw_comment: bool) -> None:
        version_match = VERSION_HEADING.fullmatch(line)
        if version_match is not None:
            parsed = _parse_version(version_match.group("ver"))
            day = version_match.group("date")
            if parsed is None or not _real_date(day):
                self.errors.append(
                    f"{CHANGELOG}:{lineno}: invalid calendar date {day} in release heading"
                )
            if parsed is not None:
                self.current = Section(parsed, lineno)
                self.sections.append(self.current)
            else:
                self.current = None
            return
        repo_match = REPO_HEADING.fullmatch(line)
        if repo_match is not None:
            day = repo_match.group("date")
            if not _real_date(day):
                self.errors.append(
                    f"{CHANGELOG}:{lineno}: invalid calendar date {day} "
                    "in repository updates heading"
                )
            # Explicit repository-update headings are not release headings.
            self.current = None
            return
        if _is_level2_heading(line) and "Repository updates" in line:
            self.errors.append(
                f"{CHANGELOG}:{lineno}: malformed repository updates heading {_clip(line)!r}"
            )
            self.current = None
            return
        if _is_level2_heading(line):
            self.errors.append(
                f"{CHANGELOG}:{lineno}: malformed release heading {_clip(line)!r}"
            )
            self.current = None
            return
        if self.current is None:
            return
        if saw_comment and line.strip() == "":
            self.current.comments += 1
            return
        separator = SEPARATOR.fullmatch(line)
        if separator is not None:
            self.current.separators += 1
            return
        bullet = BULLET.fullmatch(line)
        if bullet is not None:
            if _substantive_text(bullet.group(1)):
                self.current.substantive += 1
            else:
                self.current.placeholder += 1
            return
        if SUBHEADING.match(line):
            self.current.subheadings += 1
            return
        if _substantive_text(line):
            self.current.prose += 1
        else:
            self.current.placeholder += 1

    def _touch(self, kind: str) -> None:
        section = self.current
        if section is None or kind == "blank":
            return
        if kind == "comment":
            section.comments += 1
        elif kind == "fence":
            section.fences += 1


def _substance_problem(section: Section) -> str | None:
    if section.substantive:
        return None
    visible = section.placeholder or section.separators or section.subheadings or section.prose
    if not visible:
        labels: list[str] = []
        if section.comments:
            labels.append("comments-only")
        if section.fences:
            labels.append("code-fence-only")
        if not labels:
            return "empty"
        return " and ".join(labels)
    if section.placeholder and not (section.separators or section.subheadings or section.prose):
        return "placeholder-only (TODO, TBD, coming soon, or placeholder)"
    if section.subheadings and not (section.placeholder or section.separators or section.prose):
        return "heading-only"
    if section.separators and not (section.placeholder or section.subheadings or section.prose):
        return "separator-only"
    return "missing a substantive bullet"


def _is_level2_heading(line: str) -> bool:
    # ``###`` is a deeper heading and must not be read as a release heading.
    return line.startswith("##") and not line.startswith("###")


def _substantive_text(body: str) -> bool:
    text = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r" \1 ", body)
    text = re.sub(r"[*_`~]+", " ", text)
    words = re.sub(r"[^\w]+", " ", text, flags=re.UNICODE).lower().strip()
    if not words:
        return False
    compact = "".join(ch for ch in words if ch.isalnum())
    if compact in PLACEHOLDER_COMPACT:
        return False
    reduced = re.sub(r"\bcoming\s+soon\b", " ", words)
    reduced = re.sub(r"\b(?:todo|tbd|placeholder)\b", " ", reduced)
    return bool(reduced.strip())


def _strip_comments(line: str, in_comment: bool) -> tuple[str, bool, bool]:
    saw = in_comment
    pieces: list[str] = []
    index = 0
    while index < len(line):
        if in_comment:
            end = line.find("-->", index)
            if end == -1:
                return "".join(pieces), True, True
            in_comment = False
            index = end + 3
            continue
        start = line.find("<!--", index)
        if start == -1:
            pieces.append(line[index:])
            break
        saw = True
        pieces.append(line[index:start])
        in_comment = True
        index = start + 4
    return "".join(pieces), in_comment, saw


def _fence_open(line: str) -> tuple[str, int] | None:
    match = FENCE_OPEN.fullmatch(line.rstrip())
    if match is None:
        # An info string keeps the line from being only the marker.
        match = FENCE_OPEN.match(line)
        if match is None:
            return None
        rest = match.group(2)
        if rest.startswith("`"):
            return None
    marker = match.group(1)
    return marker[0], len(marker)


def _fence_close(line: str, char: str, length: int) -> bool:
    pattern = rf"^ {{0,3}}{re.escape(char)}{{{length},}}[ \t]*$"
    return re.fullmatch(pattern, line) is not None


def _check_base(
    root: Path,
    ref: str,
    canonical: tuple[int, int, int] | None,
) -> list[str]:
    if REF_TEXT.fullmatch(ref) is None:
        return [f"invalid base ref {ref!r}"]
    try:
        raw = _git_show(root, ref, CLAUDE_PLUGIN)
    except GitFailure as exc:
        return [f"base ref {ref!r} could not be read: {exc}"]
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        return [
            f"base Claude version in {CLAUDE_PLUGIN} at {ref} is invalid JSON "
            f"({exc.msg} at line {exc.lineno})"
        ]
    if not isinstance(payload, dict) or isinstance(payload.get("version"), bool) or not isinstance(
        payload.get("version"), str
    ):
        return [
            f"base Claude version in {CLAUDE_PLUGIN} at {ref} is missing or not a string"
        ]
    base = _parse_version(payload["version"])
    if base is None:
        return [
            f"base Claude version {payload['version']!r} in {CLAUDE_PLUGIN} at {ref} "
            "must be numeric X.Y.Z without leading zeros"
        ]
    if canonical is None:
        return []
    if canonical == base:
        return _check_unbumped_distribution(root, ref)
    if canonical < base:
        return [
            f"version {_fmt(canonical)} is lower than base Claude version {_fmt(base)}; "
            "a changed version must be strictly greater"
        ]
    try:
        base_log = _git_show(root, ref, CHANGELOG)
    except GitFailure as exc:
        return [f"base {CHANGELOG} at {ref} could not be read: {exc}"]
    base_parser = _ChangelogParser()
    base_parser.parse(base_log)
    if any(section.version == canonical for section in base_parser.sections):
        return [
            f"{CHANGELOG}: version {_fmt(canonical)} already has a section in the base changelog; "
            "the current version section must be newly added"
        ]
    return []


def _check_unbumped_distribution(root: Path, ref: str) -> list[str]:
    """Same plugin version: distributable edits need a changelog diff, docs do not."""
    try:
        changed = _git_diff_names(root, ref, DISTRIBUTABLE)
    except GitFailure as exc:
        return [f"could not compare distributable paths to base {ref}: {exc}"]
    if not changed:
        return []
    try:
        notes = _git_diff_names(root, ref, (CHANGELOG,))
    except GitFailure as exc:
        return [f"could not compare {CHANGELOG} to base {ref}: {exc}"]
    if notes:
        return []
    listed = ", ".join(changed)
    return [
        "distributable files changed without a version bump, "
        f"but {CHANGELOG} does not differ from base {ref}: {listed}"
    ]


def _git_show(root: Path, ref: str, path: str) -> str:
    # ``git show <rev>:<path>`` reads one blob. The rev and path share one argv slot
    # so a caller cannot add further git options or commands.
    completed = _run_git(root, ["show", f"{ref}:{path}"])
    return completed.stdout


def _git_diff_names(root: Path, ref: str, paths: tuple[str, ...]) -> list[str]:
    # ``git diff <rev> -- paths`` is the working tree versus that revision, so staged
    # and unstaged edits both show. Pathspecs keep the diff inside the named trees.
    completed = _run_git(
        root,
        ["diff", "--name-only", ref, "--", *paths],
    )
    return [line for line in completed.stdout.splitlines() if line.strip()]


def _run_git(root: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    command = ["git", "--no-pager", "-C", str(root), *args]
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=60,
            shell=False,
            check=False,
        )
    except FileNotFoundError:
        raise GitFailure("git is not available") from None
    except subprocess.TimeoutExpired:
        raise GitFailure("git timed out") from None
    except OSError as exc:
        raise GitFailure(f"could not run git ({exc.strerror or exc})") from None
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip().splitlines()
        summary = detail[0] if detail else f"git exited {completed.returncode}"
        raise GitFailure(summary)
    return completed


def _load_json(path: Path, display: str) -> tuple[object | None, str | None]:
    text, error = _read_text(path, display)
    if error or text is None:
        return None, error or f"{display}: cannot read"
    try:
        return json.loads(text), None
    except json.JSONDecodeError as exc:
        return None, f"{display}: invalid JSON ({exc.msg} at line {exc.lineno})"


def _read_text(path: Path, display: str) -> tuple[str | None, str | None]:
    try:
        return path.read_text(encoding="utf-8"), None
    except FileNotFoundError:
        return None, f"{display}: file not found"
    except UnicodeDecodeError as exc:
        return None, f"{display}: not valid UTF-8 ({exc.reason})"
    except OSError as exc:
        return None, f"{display}: cannot read ({exc.strerror or exc})"


def _parse_version(value: str) -> tuple[int, int, int] | None:
    match = VERSION_TEXT.fullmatch(value)
    if match is None:
        return None
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def _real_date(value: str) -> bool:
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def _fmt(version: tuple[int, int, int]) -> str:
    return f"{version[0]}.{version[1]}.{version[2]}"


def _json_type(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, str):
        return "string"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, list):
        return "list"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def _clip(text: str) -> str:
    if len(text) <= 120:
        return text
    return text[:117] + "..."


if __name__ == "__main__":
    sys.exit(main())
