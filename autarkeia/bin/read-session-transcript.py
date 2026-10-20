#!/usr/bin/env python3
"""Read one local Codex or Claude transcript page. Read-only.

The output is a bounded page of original physical records. It is never a claim
that the original session survived intact: compaction, rotation, and a short
snapshot can all hide earlier or later talk. User text is a candidate, not
proof of who typed it.
"""

import argparse
import errno
import json
import os
from pathlib import Path
import re
import stat
import sys

DEFAULT_MAX_CHARS = 12000
MAX_MAX_CHARS = 50000
MAX_ITEMS = 200
MAX_WARNINGS = 100
READ_CHUNK = 65536

UUID_TEXT = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)
UUID_IN_NAME = re.compile(
    r"(?i)(?<![0-9a-f])[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}(?![0-9a-f])"
)

PARTIAL_CODES = {
    "truncated_record",
    "json_parse_error",
    "encoding_error",
    "unknown_record",
    "unknown_content_block",
    "mixed_provenance",
}
SPEECH_TYPES = {"text", "input_text", "output_text", "refusal", "output_refusal"}
REASONING_TYPES = {"reasoning", "thinking", "redacted_thinking", "reasoning_summary"}
ATTACHMENT_TYPES = {"image", "input_image", "input_file", "file", "image_url"}
TOOL_TYPES = {
    "function_call",
    "function_call_output",
    "custom_tool_call",
    "custom_tool_call_output",
    "local_shell_call",
    "local_shell_call_output",
    "web_search_call",
    "computer_call",
    "computer_call_output",
    "tool_call",
    "tool_use",
    "tool_result",
    "mcp_tool_call",
    "mcp_tool_call_output",
}
TOOL_OUTPUT_TYPES = {
    "function_call_output",
    "custom_tool_call_output",
    "local_shell_call_output",
    "computer_call_output",
    "mcp_tool_call_output",
    "tool_result",
}
MIRROR_EVENTS = {"user_message", "agent_message", "item_completed", "task_complete"}
TELEMETRY_EVENTS = {
    "token_count",
    "agent_reasoning",
    "agent_reasoning_raw_content",
    "agent_reasoning_delta",
    "exec_command_begin",
    "exec_command_end",
    "exec_command_output_delta",
    "exec_approval_request",
    "apply_patch_approval_request",
    "patch_apply_begin",
    "patch_apply_end",
    "mcp_tool_call_begin",
    "mcp_tool_call_end",
    "web_search_begin",
    "web_search_end",
    "session_configured",
    "thread_settings_applied",
    "plan_update",
    "shutdown_complete",
    "turn_aborted",
    "error",
    "warning",
    "item_started",
    "task_started",
    "context_window_update",
    "view_image_tool_call",
}
# Sampled Codex types that carry usage, world context, or settings. Not talk.
CODEX_CONTEXT_TELEMETRY = {"token_usage_record", "world_state", "thread_settings_applied"}
# Nonhuman Codex context that is not a person speaking and not an unknown gap.
CODEX_NONHUMAN_CONTEXT = {"inter_agent_communication_metadata", "agent_message"}
# Tool-definition payloads on a response item. Not dialogue, even when role is user.
CODEX_TOOL_DEFINITIONS = {"additional_tools"}
# Title, name, settings, transport, file-backup, and accounting fields only.
CLAUDE_METADATA = {
    "custom-title",
    "agent-name",
    "atis-latch",
    "bridge-session",
    "file-history-delta",
    "cost-state",
}
CLAUDE_TELEMETRY = {
    "progress",
    "file-history-snapshot",
    "queue-operation",
    "rate_limit_event",
    "permission-mode",
    "ai-title",
    "last-prompt",
} | CLAUDE_METADATA
# Kinds that are injected context, not a person typing. user.text is not in this set.
INJECTED_CONTEXT_KINDS = {
    "agents_md.instructions",
    "environments.environment_context",
    "additional_content.codex_apps_open_page",
}
# Named Claude attachment subtypes that are context or file material.
# A queued_command prompt is not in this set. Any other subtype may contain user input.
KNOWN_CONTEXT_ATTACHMENTS = {
    "edited_text_file",
    "compact_file_reference",
    "prompt_snapshot",
    "read_truncation_notice",
    "total_tokens_reminder",
    "environment",
    "instructions",
    "hook_success",
}
MAX_ATTACHMENT_SUBTYPE_KEYS = 24
MAX_QUEUE_ID_CHARS = 512
QUEUE_REMOVAL_OPS = {
    "remove",
    "removal",
    "removed",
    "dequeue",
    "dequeued",
    "pop",
    "delete",
    "drop",
}
QUEUE_ID_KEYS = ("source_uuid", "delivery_id")
OMISSION_KEYS = (
    "mirrored_events",
    "telemetry",
    "reasoning",
    "developer_or_system",
    "tool_evidence",
    "nonhuman_context",
    "attachments",
    "sidechain",
    "synthetic_or_meta",
    "unresolved_user_context",
    "compaction_summaries",
    "duplicate_ids",
    "unknown_records",
    "unknown_content_blocks",
)
BINARY_KEYS = {"data", "base64", "image_url", "encrypted_content"}
SUMMARY_KEYS = ("summary", "message", "content", "text")

DESCRIPTION = """
Read one local Codex or Claude session transcript and print one page of it as JSON.

This program is read-only. It does not write files, send messages, or run any text it finds.

Pass the runtime and the session id. The program looks for that exact session file, checks
that the id recorded in the file is the same id, and reads original records from the start
of the file. It does not pick the newest file. It does not search the words of other files.

User text is returned as kind user_message_candidate. That is not proof the person typed
those words. A later step has to check wrappers and quoted text. A Claude attachment of
type queued_command with command mode prompt is the same kind of candidate, labelled
claude_queued_command. Assistant text keeps the assistant role. Tool output is included
only with --include-tools, and each tool record is labeled tool evidence rather than as a
person speaking. Other attachment subtypes are not read as a person. An attachment subtype
this program does not handle makes coverage partial, because it may contain user input.

When one record's content kinds mix injected context with any other kind, the original
text and the original kind list are both kept and the item is marked mixed. Coverage is
partial. List position is not attribution: a later step must separate the words or hold
them. Do not treat that joined text as the person's.

coverage_status is retained_snapshot_only when this snapshot was read cleanly, or partial
when a record was cut off, badly formed, or not understood. It is never a promise that the
original session is complete. Records that are still physically in the file are kept,
including talk from before a compaction point. The compaction point itself is only a
boundary marker, with no summary text.
""".strip()

EPILOG = """
Pagination:
  --max-chars limits the text in one page (default 12000, maximum 50000). At most 200 items
  are returned on a page. A long record continues on the next page. Pass the printed
  next_cursor back as --cursor. Accepted text is split, not dropped.

Snapshot:
  --snapshot-bytes pins the end of the file. Later calls with the same number ignore
  anything appended after that byte. If the file is shorter than the pin, the read is
  refused. The default pin is the file size at the moment of the call.

Cursor JSON:
  {"line": 12, "text_offset": 0, "segment": 0}
  line is the physical line in the file, starting at 1. text_offset is the start of this
  slice inside that record. segment is 0 for the spoken text and 1 for tool evidence on
  that same line. segment may be left out; it then means 0.
""".strip()


class ReaderError(Exception):
    def __init__(self, code, message, details=None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}


class State:
    def __init__(self):
        self.warnings = []
        self.warning_total = 0
        self.warnings_truncated = False
        self.partial = False
        self.omissions = {key: 0 for key in OMISSION_KEYS}
        self.seen = set()
        self.identity_ok = False
        self.conversational = 0
        self.missing_identity = False
        self.nodes = []
        self.node_ids = set()
        self.context_attachment_warned = False
        self.unhandled_attachment_warned = False
        self.attachment_overflow_warned = False
        self.attachment_subtypes = {}
        self.attachment_subtype_overflow = 0
        self.delivered_queue_ids = {key: set() for key in QUEUE_ID_KEYS}
        self.pending_enqueues = []

    def warn(self, code, message, line):
        if code in PARTIAL_CODES:
            self.partial = True
        self.warning_total += 1
        if len(self.warnings) < MAX_WARNINGS:
            self.warnings.append({"code": code, "line": line, "message": message})
        else:
            self.warnings_truncated = True

    def unknown_record(self, line, type_name):
        self.omissions["unknown_records"] += 1
        self.warn(
            "unknown_record",
            "Unrecognized record type %s on line %s was skipped." % (short_type(type_name), line),
            line,
        )

    def unknown_block(self, line, type_name):
        self.omissions["unknown_content_blocks"] += 1
        self.warn(
            "unknown_content_block",
            "Unrecognized content block type %s on line %s was skipped." % (short_type(type_name), line),
            line,
        )

    def attachment(self, line, type_name):
        self.omissions["attachments"] += 1
        self.warn(
            "attachment_omitted",
            "Omitted a binary attachment (%s) on line %s." % (short_type(type_name), line),
            line,
        )

    def coverage_gap(self, message, line):
        # missing_metadata alone does not mark the snapshot partial. A missing
        # message shape, role, text block, or content does: the page is a gap.
        self.partial = True
        self.warn("missing_metadata", message, line)

    def remember_attachment_subtype(self, type_name):
        # Count every omitted attachment. Keys are bounded so a hostile or
        # unknown subtype cannot grow the page without a visible overflow.
        self.omissions["attachments"] += 1
        key = short_type(type_name)
        if key in self.attachment_subtypes:
            self.attachment_subtypes[key] += 1
            return
        if len(self.attachment_subtypes) >= MAX_ATTACHMENT_SUBTYPE_KEYS:
            self.attachment_subtype_overflow += 1
            self.partial = True
            if not self.attachment_overflow_warned:
                self.attachment_overflow_warned = True
                self.warn(
                    "attachment_subtype_overflow",
                    "Some omitted attachment subtypes are not listed. "
                    "The overflow count is recorded. Unlisted subtypes were not read "
                    "and may contain user input.",
                    None,
                )
            return
        self.attachment_subtypes[key] = 1

    def note_known_context_attachment(self, line, type_name):
        self.remember_attachment_subtype(type_name)
        if self.context_attachment_warned:
            return
        self.context_attachment_warned = True
        self.warn(
            "context_attachment_omitted",
            "Omitted context and file attachments. Their subtype counts are recorded. "
            "Open them at the source when their content is needed.",
            line,
        )

    def note_unhandled_attachment(self, line, type_name):
        self.remember_attachment_subtype(type_name)
        self.partial = True
        if self.unhandled_attachment_warned:
            return
        self.unhandled_attachment_warned = True
        self.warn(
            "unhandled_attachment",
            "An unhandled attachment subtype was omitted. It may contain user input. "
            "It was not read as a message, and coverage is partial.",
            line,
        )

    def note_unresolved_user(self):
        # Meta text is not promoted from its wording. Human status stays unresolved.
        self.omissions["unresolved_user_context"] += 1
        self.partial = True

    def remember_queued_delivery(self, key, value):
        if key in self.delivered_queue_ids and value:
            self.delivered_queue_ids[key].add(value)

    def note_queue_operation(self, obj):
        # Queue records are transport. Text is not copied. An enqueue with no
        # matching delivery id is unresolved input, not proof the text was kept.
        if queue_operation_name(obj) in QUEUE_REMOVAL_OPS:
            return
        if not queue_has_text(obj):
            return
        self.pending_enqueues.append(queue_attribution_ids(obj))

    def finish_pending_enqueues(self):
        unresolved = 0
        for found in self.pending_enqueues:
            if queue_ids_match(found, self.delivered_queue_ids):
                continue
            unresolved += 1
        if not unresolved:
            return
        self.partial = True
        self.warn(
            "possible_pending_input",
            "Possible pending or unresolved queued input. %s text-bearing enqueue "
            "record(s) had no safe delivery attribution. Their text was not read as a "
            "person speaking, and this snapshot is not proof that every queued input was kept."
            % unresolved,
            None,
        )


def short_type(value):
    if not isinstance(value, str) or not value:
        return "unknown"
    cleaned = "".join(ch if ch.isprintable() else "?" for ch in value)
    return cleaned[:80]


def norm_uuid(value):
    if not isinstance(value, str) or not UUID_TEXT.fullmatch(value.strip()):
        return None
    return value.strip().lower()


def preview(value):
    if isinstance(value, str):
        return value[:120]
    return None


def mismatch(requested, recorded):
    raise ReaderError(
        "session_id_mismatch",
        "The recorded session id does not match the requested session id. "
        "Do not retry with another recorded id.",
        {"requested": requested, "recorded": preview(recorded)},
    )


def build_parser():
    parser = argparse.ArgumentParser(
        prog="read-session-transcript.py",
        description=DESCRIPTION,
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--runtime", choices=("codex", "claude"), required=True,
                        help="Which local transcript store to read. Required. It is not inferred from the environment.")
    parser.add_argument("--session-id",
                        help="Session UUID. For Codex only, CODEX_THREAD_ID is used when this is omitted.")
    parser.add_argument("--path", help="Read this JSONL file instead of searching the runtime home.")
    parser.add_argument("--home", help="Runtime data root. For tests or a non-default home. Paths may contain spaces.")
    parser.add_argument("--cursor", help="JSON object with line and text_offset from a previous next_cursor.")
    parser.add_argument("--max-chars", type=int, default=DEFAULT_MAX_CHARS,
                        help="Maximum text characters on this page. Default 12000. Maximum 50000.")
    parser.add_argument("--snapshot-bytes", type=int,
                        help="Read only the first N bytes. Default is the current file size.")
    parser.add_argument("--include-tools", action="store_true",
                        help="Include tool calls and tool results, labeled as tool evidence, never as a person.")
    return parser


def parse_session_id(value, source):
    session_id = norm_uuid(value)
    if session_id is None:
        raise ReaderError(
            "invalid_args",
            "%s must be a UUID, like 11111111-1111-4111-8111-111111111111." % source,
        )
    return session_id


def resolve_session_id(runtime, session_id, env):
    if session_id:
        return parse_session_id(session_id, "--session-id")
    if runtime == "codex":
        inherited = env.get("CODEX_THREAD_ID")
        if inherited:
            return parse_session_id(inherited, "CODEX_THREAD_ID")
    raise ReaderError(
        "invalid_args",
        "Pass --session-id. Codex may use CODEX_THREAD_ID when --runtime is codex. "
        "No other runtime is inferred from the environment.",
    )


def parse_cursor(raw):
    if raw is None or raw == "":
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        raise ReaderError("invalid_cursor", "Cursor is not valid JSON.")
    if not isinstance(data, dict):
        raise ReaderError("invalid_cursor", "Cursor must be a JSON object with line and text_offset.")
    unknown = set(data) - {"line", "text_offset", "segment"}
    if unknown or "line" not in data or "text_offset" not in data:
        raise ReaderError("invalid_cursor", "Cursor must contain line and text_offset.")
    line = data["line"]
    offset = data["text_offset"]
    segment = data.get("segment", 0)
    if type(line) is not int or type(offset) is not int or type(segment) is not int:
        raise ReaderError("invalid_cursor", "Cursor line, text_offset, and segment must be integers.")
    if line < 1 or offset < 0 or segment < 0:
        raise ReaderError("invalid_cursor", "Cursor line must be 1 or more, and offsets must be 0 or more.")
    return {"line": line, "text_offset": offset, "segment": segment}


def default_home(runtime, env):
    if runtime == "codex":
        return env.get("CODEX_HOME") or str(Path.home() / ".codex")
    return env.get("CLAUDE_CONFIG_DIR") or str(Path.home() / ".claude")


def filename_has_uuid(name, session_id):
    return any(match.group(0).lower() == session_id for match in UUID_IN_NAME.finditer(name))


def walk_files(base):
    if base.is_symlink():
        raise ReaderError("unreadable", "Refusing to follow a symlink while searching.", {"path": str(base)})
    errors = []

    def onerror(err):
        errors.append(err)

    for dirpath, dirnames, filenames in os.walk(base, followlinks=False, onerror=onerror):
        kept = []
        for name in dirnames:
            child = Path(dirpath) / name
            if not child.is_symlink():
                kept.append(name)
        dirnames[:] = kept
        for name in filenames:
            path = Path(dirpath) / name
            if path.is_symlink():
                continue
            if path.suffix.lower() != ".jsonl":
                continue
            yield path
    if errors:
        raise ReaderError("unreadable", "Could not list the transcript directory.", {"path": str(base)})


def find_codex(root, session_id):
    matches = []
    for folder in ("sessions", "archived_sessions"):
        base = root / folder
        if not base.exists():
            continue
        if base.is_symlink() or not base.is_dir():
            raise ReaderError("unreadable", "The Codex transcript folder is not a directory.", {"path": str(base)})
        for path in walk_files(base):
            if filename_has_uuid(path.name, session_id):
                matches.append(path)
    return matches


def find_claude(root, session_id):
    projects = root / "projects"
    if not projects.exists():
        return []
    if projects.is_symlink() or not projects.is_dir():
        raise ReaderError("unreadable", "The Claude projects directory is not a directory.", {"path": str(projects)})
    target = session_id + ".jsonl"
    matches = []
    try:
        children = list(projects.iterdir())
    except OSError as exc:
        raise ReaderError("unreadable", "Could not list Claude projects.", {"reason": exc.strerror})
    for child in children:
        if child.is_symlink() or not child.is_dir() or child.name == "subagents":
            continue
        try:
            entries = list(child.iterdir())
        except OSError as exc:
            raise ReaderError("unreadable", "Could not list a Claude project directory.",
                              {"path": str(child), "reason": exc.strerror})
        for entry in entries:
            # Only projects/<dir>/<session-id>.jsonl. Do not descend into subagents.
            if entry.is_symlink() or not entry.is_file():
                continue
            if entry.name.lower() == target:
                matches.append(entry)
    return matches


def locate(runtime, session_id, path, home, env):
    if path:
        candidate = Path(path)
        if not candidate.is_absolute():
            candidate = Path.cwd() / candidate
        return os.path.abspath(candidate), None
    root = Path(home).expanduser() if home else Path(default_home(runtime, env)).expanduser()
    if not root.exists() or not root.is_dir():
        raise ReaderError(
            "not_found",
            "No transcript file matched this session id.",
            {"home": str(root), "runtime": runtime, "session_id": session_id},
        )
    matches = find_codex(root, session_id) if runtime == "codex" else find_claude(root, session_id)
    if not matches:
        raise ReaderError(
            "not_found",
            "No transcript file matched this session id.",
            {"home": str(root), "runtime": runtime, "session_id": session_id},
        )
    if len(matches) > 1:
        paths = sorted(os.path.abspath(str(item)) for item in matches)
        raise ReaderError(
            "multiple_candidates",
            "More than one transcript file matches this session id. "
            "Pass a host-supplied exact path with --path. "
            "No file was selected. Do not choose a file arbitrarily.",
            {"count": len(paths), "paths": paths},
        )
    return os.path.abspath(str(matches[0])), root


def open_transcript(path, snapshot_bytes):
    flags = os.O_RDONLY
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags | nofollow)
    except OSError as exc:
        if nofollow and exc.errno in (errno.ELOOP, errno.EMLINK):
            raise ReaderError("not_a_file", "Refusing to read a symlink.", {"path": path})
        raise ReaderError("unreadable", "Could not open the transcript.", {"path": path, "reason": exc.strerror})
    try:
        info = os.fstat(fd)
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
            raise ReaderError("not_a_file", "Transcript path is not a regular file.", {"path": path})
        if info.st_size < snapshot_bytes:
            raise ReaderError(
                "snapshot_shrink",
                "The transcript is shorter than snapshot-bytes, so this snapshot is no longer valid.",
                {"size": info.st_size, "snapshot_bytes": snapshot_bytes},
            )
        return fd, info.st_size
    except Exception:
        os.close(fd)
        raise


def iter_snapshot_lines(fd, snapshot_bytes, file_size):
    """Yield complete physical lines inside the snapshot, one line at a time.

    A snapshot that ends mid-line is a truncated record. It is not parsed.
    A file whose last line has no newline is complete when the snapshot reaches
    the real end of the file.
    """
    left = snapshot_bytes
    buf = bytearray()
    line_no = 0
    try:
        while left > 0:
            chunk = os.read(fd, min(READ_CHUNK, left))
            if not chunk:
                raise ReaderError(
                    "snapshot_shrink",
                    "The transcript shrank while it was being read.",
                    {"snapshot_bytes": snapshot_bytes},
                )
            left -= len(chunk)
            buf.extend(chunk)
            while True:
                nl = buf.find(b"\n")
                if nl < 0:
                    break
                raw = bytes(buf[:nl])
                del buf[:nl + 1]
                if raw.endswith(b"\r"):
                    raw = raw[:-1]
                line_no += 1
                if line_no == 1 and raw.startswith(b"\xef\xbb\xbf"):
                    raw = raw[3:]
                yield ("line", line_no, raw)
    except ReaderError:
        raise
    except OSError as exc:
        raise ReaderError("unreadable", "Could not read the transcript.", {"reason": exc.strerror})
    if buf:
        if file_size == snapshot_bytes:
            raw = bytes(buf)
            if raw.endswith(b"\r"):
                raw = raw[:-1]
            line_no += 1
            if line_no == 1 and raw.startswith(b"\xef\xbb\xbf"):
                raw = raw[3:]
            if raw:
                yield ("line", line_no, raw)
        else:
            yield ("truncated", line_no + 1, b"")
    del buf


def parse_line(raw, line_no, state):
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        state.warn("encoding_error", "Line %s is not valid UTF-8 and was skipped." % line_no, line_no)
        return None
    if not text.strip():
        return None
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        state.warn("json_parse_error", "Line %s is not valid JSON and was skipped." % line_no, line_no)
        return None
    if not isinstance(obj, dict):
        state.unknown_record(line_no, None)
        return None
    return obj


def check_identity(runtime, obj, requested, state):
    if runtime == "codex":
        check_identity_codex(obj, requested, state)
    else:
        check_identity_claude(obj, requested, state)


IDENTITY_KEYS = ("id", "session_id", "sessionId")


def identity_values(source):
    if not isinstance(source, dict):
        return []
    return [source[key] for key in IDENTITY_KEYS if key in source and source[key] is not None]


def same_requested_id(values, requested):
    # Every identity value in the record has to be the requested id.
    # One matching envelope must not hide a different value in the other.
    # A list or dict is not an id and is not copied into the error.
    if not values:
        return False
    disagreeing = None
    for value in values:
        norm = norm_uuid(value) if isinstance(value, str) else None
        if norm is None:
            mismatch(requested, value if isinstance(value, str) else None)
        if norm != requested and disagreeing is None:
            disagreeing = value
    if disagreeing is not None:
        mismatch(requested, disagreeing)
    return True


def check_identity_codex(obj, requested, state):
    if obj.get("type") == "session_meta":
        payload = obj.get("payload") if isinstance(obj.get("payload"), dict) else None
        values = identity_values(obj)
        if payload is not None:
            values.extend(identity_values(payload))
        if same_requested_id(values, requested):
            state.identity_ok = True
        return
    for source in (obj, obj.get("payload") if isinstance(obj.get("payload"), dict) else {}):
        if not isinstance(source, dict):
            continue
        for key in ("session_id", "sessionId"):
            if key in source and source[key] is not None:
                value = source[key]
                norm = norm_uuid(value) if isinstance(value, str) else None
                if norm != requested:
                    # A list or dict is not an id. Do not copy it into the error.
                    mismatch(requested, value if isinstance(value, str) else None)


def is_queued_command_record(obj):
    if obj.get("type") != "attachment":
        return False
    attachment = obj.get("attachment")
    return isinstance(attachment, dict) and attachment.get("type") == "queued_command"


def claude_record_is_conversational(obj):
    # A prompt-mode queued_command is conversational even when the file has no
    # ordinary user record. Sidechain and compaction stay out of that check.
    # A list or dict in the type field is not a record name.
    if obj.get("isSidechain") is True:
        return False
    record_type = obj.get("type")
    if not isinstance(record_type, str):
        return False
    if record_type in {"user", "assistant", "system"}:
        return True
    if obj.get("isCompactSummary") is True or record_type in {"summary", "compact_summary"}:
        return False
    return is_queued_command_record(obj)


def check_identity_claude(obj, requested, state):
    session_id = obj.get("sessionId")
    if claude_record_is_conversational(obj):
        state.conversational += 1
        norm = norm_uuid(session_id) if isinstance(session_id, str) else None
        if norm is None:
            state.missing_identity = True
            return
        if norm != requested:
            mismatch(requested, session_id if isinstance(session_id, str) else None)
        return
    if session_id is not None:
        norm = norm_uuid(session_id) if isinstance(session_id, str) else None
        if norm != requested:
            mismatch(requested, session_id if isinstance(session_id, str) else None)


def obj_line(obj):
    """Source line stored by read_page, or None when this object has none."""
    if not isinstance(obj, dict):
        return None
    line = obj.get("_line")
    if isinstance(line, bool) or not isinstance(line, int) or line < 1:
        return None
    return line


def note_parent(obj, line, state):
    if line is None:
        line = obj_line(obj)
    if obj.get("isSidechain") is True:
        return
    uid = obj.get("uuid")
    if not isinstance(uid, str) or not uid or uid in state.node_ids:
        return
    parent = obj.get("parentUuid")
    if parent is None or parent == "":
        parent = None
    elif not isinstance(parent, str):
        state.warn("missing_metadata", "Line %s has a parentUuid that is not text." % line, line)
        parent = None
    state.node_ids.add(uid)
    state.nodes.append((uid, parent, line))


def duplicate(runtime, obj, line, state):
    key = None
    if runtime == "claude":
        uid = obj.get("uuid")
        if isinstance(uid, str) and uid:
            key = "c:" + uid
    elif obj.get("type") == "response_item":
        payload = obj.get("payload") if isinstance(obj.get("payload"), dict) else {}
        item_id = payload.get("id")
        if isinstance(item_id, str) and item_id:
            key = "x:" + item_id
    if key is None:
        return False
    if key in state.seen:
        state.omissions["duplicate_ids"] += 1
        state.warn("duplicate_id", "Skipped a repeated record id on line %s." % line, line)
        return True
    state.seen.add(key)
    return False


def timestamp_of(obj):
    value = obj.get("timestamp")
    if isinstance(value, str) and value:
        return value
    payload = obj.get("payload")
    if isinstance(payload, dict):
        value = payload.get("timestamp")
        if isinstance(value, str) and value:
            return value
    return None


def meta_for(obj, line, item_id, parent_id):
    return {
        "line": line,
        "id": item_id if isinstance(item_id, str) and item_id else None,
        "parent_id": parent_id if isinstance(parent_id, str) and parent_id else None,
        "timestamp": timestamp_of(obj),
    }


def make_unit(meta, segment, role, kind, text, extra=None):
    unit = {
        "line": meta["line"],
        "segment": segment,
        "id": meta["id"],
        "parent_id": meta["parent_id"],
        "timestamp": meta["timestamp"],
        "role": role,
        "kind": kind,
        "text": text,
    }
    if extra:
        for key, value in extra.items():
            if value is not None:
                unit[key] = value
    return unit


def bounded_queue_id(value):
    if isinstance(value, str) and value and len(value) <= MAX_QUEUE_ID_CHARS:
        return value
    return None


def queue_operation_name(obj):
    value = obj.get("operation")
    if not isinstance(value, str):
        value = obj.get("op")
    if not isinstance(value, str):
        return ""
    return value.strip().lower()


def value_has_text(value):
    if isinstance(value, str):
        return value.strip() != ""
    if isinstance(value, dict):
        return any(value_has_text(inner) for inner in value.values())
    if isinstance(value, list):
        return any(value_has_text(inner) for inner in value)
    return False


def queue_has_text(obj):
    for key in ("content", "text", "prompt", "message", "body"):
        if key in obj and value_has_text(obj.get(key)):
            return True
    return False


def queue_attribution_sources(obj):
    sources = [obj]
    for key in ("attachment", "item", "payload", "queue", "content"):
        inner = obj.get(key)
        if isinstance(inner, dict):
            sources.append(inner)
    return sources


def queue_attribution_ids(obj):
    found = {}
    for source in queue_attribution_sources(obj):
        for key in QUEUE_ID_KEYS:
            if key in found:
                continue
            value = bounded_queue_id(source.get(key))
            if value:
                found[key] = value
    return found


def queue_ids_match(found, delivered):
    for key, value in found.items():
        if value in delivered.get(key, ()):
            return True
    return False


def queued_prompt_accepted(prompt):
    # A prompt is a nonempty string or a content-block list. Whitespace-only
    # strings stay a bad shape. An empty list is accepted here and reported
    # later as a content gap, not as a malformed command.
    if isinstance(prompt, str):
        return prompt.strip() != ""
    return isinstance(prompt, list)


def queued_origin(attachment):
    # Origin is the vendor attachment field. Absent origin stays compatible
    # with the string prompt probe. A supplied origin with no kind string is
    # unresolved, not human.
    if "origin" not in attachment:
        return "absent", None
    origin = attachment.get("origin")
    if not isinstance(origin, dict):
        return "malformed", None
    kind = origin.get("kind")
    if not isinstance(kind, str) or kind.strip() == "":
        return "malformed", None
    if kind != "human":
        return "nonhuman", kind
    return "human", kind


def stamp_queued_units(units, extra):
    for unit in units:
        for key, value in extra.items():
            # Null origin_kind means the vendor left origin off. Keep that visible.
            if value is not None or key == "origin_kind":
                unit[key] = value
    return units


def queued_content_explained(state, before):
    attachments, tools, reasoning, unknown, warnings = before
    if state.omissions["attachments"] != attachments:
        return True
    if state.omissions["tool_evidence"] != tools:
        return True
    if state.omissions["reasoning"] != reasoning:
        return True
    if state.omissions["unknown_content_blocks"] != unknown:
        return True
    if state.warning_total != warnings:
        return True
    return False


def queued_command_provenance(obj, attachment, state, origin_kind):
    # The prompt is the candidate. rendered / renderedRole are not read.
    extra = {
        "source_kind": "claude_queued_command",
        "origin_kind": origin_kind,
    }
    for key in QUEUE_ID_KEYS:
        value = bounded_queue_id(attachment.get(key))
        if value is None:
            value = bounded_queue_id(obj.get(key))
        if value is None:
            continue
        extra[key] = value
        state.remember_queued_delivery(key, value)
    return extra


def warn_emitted(meta, state, runtime):
    if meta["timestamp"] is None:
        state.warn("missing_metadata", "Line %s has no timestamp." % meta["line"], meta["line"])
    if runtime == "claude" and meta["id"] is None:
        state.warn("missing_metadata", "Line %s has no uuid." % meta["line"], meta["line"])


def is_attachment(block):
    btype = block.get("type")
    if isinstance(btype, str) and btype in ATTACHMENT_TYPES:
        return True
    source = block.get("source")
    source_type = source.get("type") if isinstance(source, dict) else None
    if isinstance(source_type, str) and source_type in {"base64", "url"} and btype == "image":
        return True
    return False


def is_delegation(name):
    if not isinstance(name, str):
        return False
    lowered = name.lower()
    return "delegat" in lowered or "subagent" in lowered or "collab_agent" in lowered


def has_delegation_marker(payload):
    if not isinstance(payload, dict):
        return False
    if is_delegation(payload.get("type")):
        return True
    return any(payload.get(key) for key in ("agent_id", "subagent_id", "delegate_id", "from_agent"))


def suppressed_summary(obj):
    sources = [obj]
    payload = obj.get("payload")
    if isinstance(payload, dict):
        sources.append(payload)
    for source in sources:
        if "replacement_history" in source:
            return True
        for key in SUMMARY_KEYS:
            value = source.get(key)
            if isinstance(value, str) and value:
                return True
            if isinstance(value, (list, dict)) and value:
                return True
    return False


def is_boundary(runtime, obj):
    record_type = obj.get("type")
    if not isinstance(record_type, str):
        record_type = None
    if runtime == "codex":
        if record_type in {"compacted", "compaction"}:
            return True
        payload = obj.get("payload") if isinstance(obj.get("payload"), dict) else {}
        event_type = payload.get("type")
        if not isinstance(event_type, str):
            return False
        return record_type == "event_msg" and event_type in {"context_compacted", "compacted", "compaction"}
    if obj.get("subtype") == "compact_boundary":
        return True
    return record_type in {"compact_boundary", "compaction", "compacted"}


def boundary_units(obj, line, item_id, parent_id, state, runtime):
    meta = meta_for(obj, line, item_id, parent_id)
    if suppressed_summary(obj):
        state.omissions["compaction_summaries"] += 1
    # replacement_history is intentionally not walked. The bytes already in the
    # file, before and after this marker, are the records this page returns.
    warn_emitted(meta, state, runtime)
    return [make_unit(meta, 0, None, "compaction", "")]


def nonhuman_units(obj, line, item_id, parent_id, state, runtime):
    state.omissions["nonhuman_context"] += 1
    meta = meta_for(obj, line, item_id, parent_id)
    warn_emitted(meta, state, runtime)
    return [make_unit(meta, 0, "nonhuman", "nonhuman_context", "")]


def speech_piece(block):
    btype = block.get("type")
    if btype in {"refusal", "output_refusal"}:
        value = block.get("refusal")
        if isinstance(value, str):
            return value
        value = block.get("text")
        return value if isinstance(value, str) else None
    value = block.get("text")
    return value if isinstance(value, str) else None


def redact(value):
    if isinstance(value, dict):
        cleaned = {}
        for key, inner in value.items():
            if key in BINARY_KEYS or (key == "url" and isinstance(inner, str) and inner.startswith("data:")):
                cleaned[key] = "[attachment omitted]"
            else:
                cleaned[key] = redact(inner)
        return cleaned
    if isinstance(value, list):
        return [redact(inner) for inner in value]
    return value


def render_tool_body(value, state, line):
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, bool) or isinstance(value, (int, float)):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, list):
        parts = []
        for block in value:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and is_attachment(block):
                state.attachment(line, block.get("type"))
            elif isinstance(block, dict) and isinstance(block.get("type"), str) and block.get("type") in SPEECH_TYPES and isinstance(block.get("text"), str):
                parts.append(block["text"])
            else:
                try:
                    parts.append(json.dumps(redact(block), ensure_ascii=False, sort_keys=True))
                except TypeError:
                    parts.append("[unreadable]")
        return "\n".join(parts)
    if isinstance(value, dict):
        if is_attachment(value):
            state.attachment(line, value.get("type"))
            return "[attachment omitted]"
        if isinstance(value.get("type"), str) and value.get("type") in SPEECH_TYPES and isinstance(value.get("text"), str):
            return value["text"]
        try:
            return json.dumps(redact(value), ensure_ascii=False, sort_keys=True)
        except TypeError:
            return "[unreadable]"
    return "[unreadable]"


def format_tool_block(block, state, line):
    btype = short_type(block.get("type"))
    name = block.get("name") if isinstance(block.get("name"), str) else ""
    call_id = ""
    for key in ("call_id", "tool_use_id"):
        if isinstance(block.get(key), str) and block.get(key):
            call_id = block[key]
            break
    if not call_id and btype in TOOL_TYPES and isinstance(block.get("id"), str):
        call_id = block["id"]
    if btype in TOOL_OUTPUT_TYPES:
        body = block.get("output") if "output" in block else block.get("content")
        label = "[tool evidence] " + btype
        if call_id:
            label += " " + call_id
    else:
        if "arguments" in block:
            body = block.get("arguments")
        elif "input" in block:
            body = block.get("input")
        else:
            body = block.get("content")
        label = "[tool evidence] " + btype
        if name:
            label += " " + name
    return label + "\n" + render_tool_body(body, state, line)


def pack_units(speech, tools, role, kind, meta, state, include_tools):
    units = []
    if speech:
        units.append(make_unit(meta, 0, role, kind, "\n".join(speech)))
    if tools:
        if include_tools:
            segment = 1 if units else 0
            units.append(make_unit(meta, segment, "tool", "tool_evidence", "\n".join(tools)))
        else:
            state.omissions["tool_evidence"] += len(tools)
    return units


def content_units(content, role, kind, meta, state, include_tools):
    speech = []
    tools = []
    if isinstance(content, str):
        speech.append(content)
    elif isinstance(content, list):
        for block in content:
            if isinstance(block, str):
                speech.append(block)
                continue
            if not isinstance(block, dict):
                state.unknown_block(meta["line"], None)
                continue
            btype = block.get("type")
            # A list or dict is not a block type. Skip that block and keep going.
            if isinstance(btype, (list, dict)):
                state.unknown_block(meta["line"], None)
                continue
            if btype in SPEECH_TYPES:
                piece = speech_piece(block)
                if not isinstance(piece, str) or piece == "":
                    state.coverage_gap("Line %s has a text block with no text." % meta["line"], meta["line"])
                else:
                    speech.append(piece)
            elif is_attachment(block):
                state.attachment(meta["line"], btype)
            elif btype in TOOL_TYPES:
                tools.append(format_tool_block(block, state, meta["line"]))
            elif btype in REASONING_TYPES:
                state.omissions["reasoning"] += 1
            else:
                state.unknown_block(meta["line"], btype)
    elif content is None:
        state.coverage_gap("Line %s has no message content." % meta["line"], meta["line"])
    else:
        state.unknown_block(meta["line"], None)
    return pack_units(speech, tools, role, kind, meta, state, include_tools)


def units_for(runtime, obj, line, state, include_tools):
    if is_boundary(runtime, obj):
        item_id = obj.get("uuid") if runtime == "claude" else None
        parent = obj.get("parentUuid") if runtime == "claude" else None
        return boundary_units(obj, line, item_id, parent, state, runtime)
    if runtime == "claude":
        return units_for_claude(obj, line, state, include_tools)
    return units_for_codex(obj, line, state, include_tools)


def units_for_codex(obj, line, state, include_tools):
    record_type = obj.get("type")
    if isinstance(record_type, (list, dict)):
        state.unknown_record(line, None)
        return []
    payload = obj.get("payload") if isinstance(obj.get("payload"), dict) else None
    if record_type == "session_meta":
        return []
    if record_type == "turn_context" or record_type in CODEX_CONTEXT_TELEMETRY:
        state.omissions["telemetry"] += 1
        return []
    if record_type in CODEX_NONHUMAN_CONTEXT:
        kinds = content_item_kinds_of(payload) if isinstance(payload, dict) else None
        return with_kinds(nonhuman_units(obj, line, None, None, state, "codex"), kinds)
    if record_type == "event_msg":
        if payload is None:
            state.unknown_record(line, record_type)
            return []
        return units_for_event(obj, payload, line, state, "codex")
    if record_type == "response_item":
        if payload is None:
            state.unknown_record(line, record_type)
            return []
        return units_for_response(obj, payload, line, state, include_tools)
    if record_type == "replacement_history":
        state.omissions["compaction_summaries"] += 1
        return []
    state.unknown_record(line, record_type)
    return []


def units_for_event(obj, payload, line, state, runtime):
    event_type = payload.get("type")
    if isinstance(event_type, (list, dict)):
        state.unknown_record(line, None)
        return []
    if has_delegation_marker(payload):
        return nonhuman_units(obj, line, payload.get("id"), None, state, runtime)
    if event_type in MIRROR_EVENTS:
        state.omissions["mirrored_events"] += 1
        return []
    if event_type == "inter_agent_communication_metadata":
        return with_kinds(
            nonhuman_units(obj, line, payload.get("id"), None, state, runtime),
            content_item_kinds_of(payload),
        )
    if event_type in REASONING_TYPES:
        state.omissions["reasoning"] += 1
        return []
    if event_type in TELEMETRY_EVENTS or event_type in CODEX_CONTEXT_TELEMETRY:
        state.omissions["telemetry"] += 1
        return []
    state.unknown_record(line, event_type if isinstance(event_type, str) else "event_msg")
    return []


def content_item_kinds_of(payload):
    box = payload.get("internal_chat_message_metadata_passthrough")
    if not isinstance(box, dict) or "content_item_kinds" not in box:
        return None
    kinds = box.get("content_item_kinds")
    if not isinstance(kinds, list):
        return None
    return list(kinds)


def classify_kinds(kinds):
    # Kinds label the whole record. They are not a parallel list of content blocks,
    # so a kind's position must not be read as the block at that position.
    if not kinds:
        return None
    injected = False
    other = False
    for kind in kinds:
        if isinstance(kind, str) and kind in INJECTED_CONTEXT_KINDS:
            injected = True
        else:
            other = True
    if injected and other:
        return "mixed"
    if injected:
        return "injected"
    return None


def with_kinds(units, kinds):
    if kinds is None:
        return units
    for unit in units:
        unit["content_item_kinds"] = kinds
    return units


def units_for_response(obj, payload, line, state, include_tools):
    payload_type = payload.get("type")
    if isinstance(payload_type, (list, dict)):
        state.unknown_record(line, None)
        return []
    item_id = payload.get("id") if isinstance(payload.get("id"), str) else None
    if payload_type in CODEX_CONTEXT_TELEMETRY:
        state.omissions["telemetry"] += 1
        return []
    if payload_type in CODEX_NONHUMAN_CONTEXT or is_delegation(payload_type):
        return with_kinds(
            nonhuman_units(obj, line, item_id, None, state, "codex"),
            content_item_kinds_of(payload),
        )
    if payload_type == "message":
        role = payload.get("role")
        kinds = content_item_kinds_of(payload)
        kind_class = classify_kinds(kinds)
        # Every kind is known injected context: do not extract that text as a person.
        if kind_class == "injected":
            return with_kinds(nonhuman_units(obj, line, item_id, None, state, "codex"), kinds)
        if isinstance(role, (list, dict)):
            state.coverage_gap("Line %s has a message role that is not text." % line, line)
            return []
        if role in {"developer", "system"}:
            state.omissions["developer_or_system"] += 1
            return []
        if role not in {"user", "assistant"}:
            return with_kinds(nonhuman_units(obj, line, item_id, None, state, "codex"), kinds)
        kind = "user_message_candidate" if role == "user" else "assistant_message"
        meta = meta_for(obj, line, item_id, None)
        units = content_units(payload.get("content"), role, kind, meta, state, include_tools)
        if kind_class == "mixed":
            # Keep every block's text. Do not zip kinds onto blocks by index.
            for unit in units:
                unit["provenance"] = "mixed"
            state.warn(
                "mixed_provenance",
                "Line %s mixes injected context with other content kinds. Original text "
                "and kinds are kept. Which words are the person's is uncertain, and list "
                "position is not proof. Hold this attribution." % line,
                line,
            )
        if units:
            warn_emitted(meta, state, "codex")
        return with_kinds(units, kinds)
    if payload_type in REASONING_TYPES:
        state.omissions["reasoning"] += 1
        return []
    if payload_type in TOOL_TYPES:
        meta = meta_for(obj, line, item_id, None)
        if include_tools:
            units = [make_unit(meta, 0, "tool", "tool_evidence", format_tool_block(payload, state, line))]
            warn_emitted(meta, state, "codex")
            return units
        state.omissions["tool_evidence"] += 1
        return []
    if payload_type in CODEX_TOOL_DEFINITIONS:
        # Definitions sit beside a turn. Do not print them, and do not read role as a speaker.
        return with_kinds(
            nonhuman_units(obj, line, item_id, None, state, "codex"),
            content_item_kinds_of(payload),
        )
    state.unknown_record(line, payload_type if isinstance(payload_type, str) else "response_item")
    return []


def only_tool_content(obj):
    message = obj.get("message")
    if not isinstance(message, dict):
        return False
    content = message.get("content")
    if not isinstance(content, list) or not content:
        return False
    for block in content:
        if not isinstance(block, dict):
            return False
        btype = block.get("type")
        if not isinstance(btype, str) or btype not in TOOL_TYPES:
            return False
    return True


def queued_command_units(obj, attachment, line, state):
    mode = attachment.get("commandMode")
    prompt = attachment.get("prompt")
    # Non-prompt command modes are not speech. A bad shape is a visible gap.
    if mode != "prompt" or not queued_prompt_accepted(prompt):
        state.remember_attachment_subtype("queued_command")
        state.partial = True
        state.warn(
            "queued_command_shape",
            "Line %s has a queued_command attachment that is malformed or not a prompt. "
            "It was not read as a person speaking, and coverage is partial." % line,
            line,
        )
        return []
    status, origin_kind = queued_origin(attachment)
    if status == "malformed":
        state.note_unresolved_user()
        return []
    parent = obj.get("parentUuid") if isinstance(obj.get("parentUuid"), str) else None
    item_id = obj.get("uuid")
    meta = meta_for(obj, line, item_id, parent)
    extra = queued_command_provenance(obj, attachment, state, origin_kind)
    if status == "nonhuman":
        # An explicit non-human kind is context, not a person, even when the
        # prompt text is ordinary words.
        units = nonhuman_units(obj, line, item_id, parent, state, "claude")
        return stamp_queued_units(units, extra)
    before = (
        state.omissions["attachments"],
        state.omissions["tool_evidence"],
        state.omissions["reasoning"],
        state.omissions["unknown_content_blocks"],
        state.warning_total,
    )
    # Ordinary block decoder: images stay omissions, and tools are not speech.
    units = content_units(prompt, "user", "user_message_candidate", meta, state, False)
    stamp_queued_units(units, extra)
    if not units and not queued_content_explained(state, before):
        state.coverage_gap(
            "Line %s has a queued_command prompt with no readable text." % line,
            line,
        )
    if units:
        warn_emitted(meta, state, "claude")
    return units


def units_for_attachment(obj, line, state):
    attachment = obj.get("attachment")
    if not isinstance(attachment, dict):
        state.note_unhandled_attachment(line, None)
        return []
    atype = attachment.get("type")
    # Meta is suppressed before any prompt is taken from the attachment.
    if obj.get("isMeta") is True and atype == "queued_command":
        state.note_unresolved_user()
        state.remember_attachment_subtype(atype)
        return []
    if atype == "queued_command":
        return queued_command_units(obj, attachment, line, state)
    if isinstance(atype, str) and atype in KNOWN_CONTEXT_ATTACHMENTS:
        state.note_known_context_attachment(line, atype)
        return []
    state.note_unhandled_attachment(line, atype)
    return []


def unresolved_meta_user(obj):
    if obj.get("type") == "user":
        return True
    message = obj.get("message")
    return isinstance(message, dict) and message.get("role") == "user"


def units_for_claude(obj, line, state, include_tools):
    # Sidechain, compaction, and meta are decided before attachment text is read.
    if obj.get("isSidechain") is True:
        state.omissions["sidechain"] += 1
        return []
    record_type = obj.get("type")
    if isinstance(record_type, (list, dict)):
        state.unknown_record(line, None)
        return []
    if obj.get("isCompactSummary") is True or record_type in {"summary", "compact_summary"}:
        state.omissions["synthetic_or_meta"] += 1
        return []
    if obj.get("type") == "attachment":
        return units_for_attachment(obj, line, state)
    if obj.get("type") == "queue-operation":
        state.note_queue_operation(obj)
        state.omissions["telemetry"] += 1
        return []
    # A meta record is not promoted from English wording inside a wrapper.
    # A tool result can also be marked meta; that one stays tool evidence.
    # A summary was already suppressed above and is not a new fact.
    if obj.get("isMeta") is True and not only_tool_content(obj):
        if unresolved_meta_user(obj):
            state.note_unresolved_user()
            return []
        state.omissions["synthetic_or_meta"] += 1
        return []
    if record_type == "system":
        state.omissions["developer_or_system"] += 1
        return []
    if record_type in CLAUDE_TELEMETRY:
        state.omissions["telemetry"] += 1
        return []
    if record_type not in {"user", "assistant"}:
        state.unknown_record(line, record_type)
        return []
    message = obj.get("message")
    meta = meta_for(obj, line, obj.get("uuid"), obj.get("parentUuid") if isinstance(obj.get("parentUuid"), str) else None)
    if not isinstance(message, dict):
        state.coverage_gap("Line %s has no message object." % line, line)
        return []
    role = message.get("role")
    # A missing role, an unsupported role, or a recognized role that disagrees
    # with the envelope is a coverage gap. Neither field becomes a human candidate.
    # A list or dict is a bad role, not a person, and it must not raise.
    if isinstance(role, (list, dict)):
        state.coverage_gap("Line %s has a message role that is not text." % line, line)
        return []
    if role not in {"user", "assistant"}:
        state.coverage_gap("Line %s has an unsupported or missing message role." % line, line)
        return []
    if role != record_type:
        state.coverage_gap("Line %s has a message role that conflicts with the record type." % line, line)
        return []
    kind = "assistant_message" if role == "assistant" else "user_message_candidate"
    units = content_units(message.get("content") if "content" in message else None, role, kind, meta, state, include_tools)
    if units:
        warn_emitted(meta, state, "claude")
    return units


def finish_identity(runtime, state):
    if runtime == "codex":
        if not state.identity_ok:
            raise ReaderError("missing_session_id", "The transcript has no recorded session id.")
        return
    if state.conversational == 0 or state.missing_identity:
        message = "The transcript has no recorded session id."
        if state.conversational and state.missing_identity:
            message = "A conversational record has no session id."
        raise ReaderError("missing_session_id", message)


def parent_warnings(state):
    parents = {}
    children = {}
    known = set()
    line_of = {}
    for uid, parent, line in state.nodes:
        known.add(uid)
        parents[uid] = parent
        line_of[uid] = line
        if parent:
            children.setdefault(parent, []).append(line)
    for parent, lines in children.items():
        if len(lines) > 1:
            state.warn(
                "ambiguous_branch",
                "Parent %s has %s child records in this snapshot. This is possible fork or "
                "parallel record linkage, not proof of a branch. Verify the source before "
                "conflicting candidates are routed. No branch was chosen; records stay in file order."
                % (parent[:80], len(lines)),
                lines[1],
            )
    missing = set()
    for uid, parent, line in state.nodes:
        if parent and parent not in known and parent not in missing:
            missing.add(parent)
            state.warn(
                "missing_parent",
                "Parent %s does not appear in this snapshot. The record was still included." % parent[:80],
                line,
            )
    has_cycle, cycle_line = parent_cycle(parents, line_of)
    if has_cycle:
        state.warn(
            "parent_cycle",
            "The parent chain contains a cycle. No branch was chosen; records stay in file order.",
            cycle_line,
        )


def parent_cycle(parents, line_of=None):
    """Return (has_cycle, source_line).

    The walk is iterative. A reversed parent chain can be longer than the
    interpreter recursion limit, and the records are not ordered parent-first.
    """
    if line_of is None:
        line_of = {}
    color = {}
    for start in parents:
        if color.get(start, 0) != 0:
            continue
        stack = [start]
        while stack:
            uid = stack[-1]
            state_color = color.get(uid, 0)
            if state_color == 0:
                color[uid] = 1
                parent = parents.get(uid)
                if parent not in parents:
                    color[uid] = 2
                    stack.pop()
                    continue
                parent_color = color.get(parent, 0)
                if parent_color == 1:
                    line = line_of.get(uid)
                    if not isinstance(line, int) or isinstance(line, bool):
                        line = line_of.get(parent)
                    if not isinstance(line, int) or isinstance(line, bool):
                        line = None
                    return True, line
                if parent_color == 0:
                    stack.append(parent)
                    continue
                color[uid] = 2
                stack.pop()
                continue
            if state_color == 1:
                color[uid] = 2
                stack.pop()
                continue
            stack.pop()
    return False, None


def summary_warnings(state):
    synthetic = state.omissions["synthetic_or_meta"]
    if synthetic:
        state.warn(
            "synthetic_omitted",
            "Skipped %s meta or synthetic summary records. Their text is not included." % synthetic,
            None,
        )
    unresolved = state.omissions["unresolved_user_context"]
    if unresolved:
        state.warn(
            "possible_omitted_user_context",
            "Possible omitted user context. %s meta record(s) have unresolved original-human "
            "status. Their text was not promoted, and coverage is partial. "
            "Summaries stay suppressed and are not new facts." % unresolved,
            None,
        )
    sidechain = state.omissions["sidechain"]
    if sidechain:
        state.warn(
            "sidechain_omitted",
            "Skipped %s sidechain records. Their text is not included." % sidechain,
            None,
        )
    nonhuman = state.omissions["nonhuman_context"]
    if nonhuman:
        state.warn(
            "nonhuman_context",
            "Omitted the text of %s delegation or other nonhuman records. They are not treated as a person speaking."
            % nonhuman,
            None,
        )


def cursor_key(cursor):
    if cursor is None:
        return None
    return (cursor["line"], cursor["segment"])


def bad_text_offset(text, offset):
    if offset < 0:
        return True
    if text == "":
        return offset != 0
    return offset >= len(text)


def emit_unit(unit, offset, items, used, max_chars):
    if len(items) >= MAX_ITEMS:
        return False, used, offset
    text = unit["text"]
    if text == "":
        if used >= max_chars and items:
            return False, used, 0
        items.append(item_dict(unit, "", 0, False))
        return True, used, 0
    room = max_chars - used
    if room <= 0:
        return False, used, offset
    piece = text[offset:offset + room]
    new_offset = offset + len(piece)
    continued = new_offset < len(text)
    items.append(item_dict(unit, piece, offset, continued))
    used += len(piece)
    if continued:
        return False, used, new_offset
    return True, used, new_offset


def item_dict(unit, text, offset, continued):
    item = {
        "line": unit["line"],
        "id": unit["id"],
        "parent_id": unit["parent_id"],
        "timestamp": unit["timestamp"],
        "role": unit["role"],
        "kind": unit["kind"],
        "text": text,
        "text_offset": offset,
        "continued": continued,
        "segment": unit["segment"],
    }
    for key in ("content_item_kinds", "provenance", "source_kind", "origin_kind", "source_uuid", "delivery_id"):
        if key in unit:
            item[key] = unit[key]
    return item


def consider_unit(unit, cursor, flags, items, used, max_chars):
    key = (unit["line"], unit["segment"])
    target = cursor_key(cursor)
    if target is not None and key < target:
        return used, False
    if target is not None and not flags["satisfied"] and key > target:
        flags["failed"] = True
        return used, True
    offset = 0
    if target is not None and key == target:
        flags["satisfied"] = True
        offset = cursor["text_offset"]
        if bad_text_offset(unit["text"], offset):
            flags["bad_offset"] = True
            return used, True
    accepted, used, next_offset = emit_unit(unit, offset, items, used, max_chars)
    if not accepted:
        flags["stop"] = {"line": unit["line"], "text_offset": next_offset if unit["text"] else 0, "segment": unit["segment"]}
        return used, True
    if unit["text"] and next_offset < len(unit["text"]):
        flags["stop"] = {"line": unit["line"], "text_offset": next_offset, "segment": unit["segment"]}
        return used, True
    return used, False


def read_page(path, runtime, session_id, snapshot_bytes, cursor, max_chars, include_tools):
    state = State()
    items = []
    used = 0
    flags = {"satisfied": cursor is None, "failed": False, "bad_offset": False, "stop": None}
    stop_emitting = False
    fd, file_size = open_transcript(path, snapshot_bytes)
    try:
        for kind, line_no, raw in iter_snapshot_lines(fd, snapshot_bytes, file_size):
            if kind == "truncated":
                state.warn(
                    "truncated_record",
                    "The snapshot ends in the middle of a record. That trailing text was not read.",
                    line_no,
                )
                continue
            obj = parse_line(raw, line_no, state)
            del raw
            if obj is None:
                continue
            obj["_line"] = line_no
            line = obj_line(obj)
            check_identity(runtime, obj, session_id, state)
            if runtime == "claude" and claude_record_is_conversational(obj):
                note_parent(obj, line, state)
            if duplicate(runtime, obj, line, state):
                continue
            units = units_for(runtime, obj, line, state, include_tools)
            obj.clear()
            if stop_emitting:
                continue
            for unit in units:
                used, stop_emitting = consider_unit(unit, cursor, flags, items, used, max_chars)
                if stop_emitting:
                    break
    finally:
        os.close(fd)
    finish_identity(runtime, state)
    if flags["bad_offset"] or flags["failed"] or (cursor is not None and not flags["satisfied"]):
        raise ReaderError("cursor_out_of_range", "Cursor does not point at text inside this snapshot.")
    if runtime == "claude":
        parent_warnings(state)
    summary_warnings(state)
    state.finish_pending_enqueues()
    done = flags["stop"] is None
    return {
        "source": path,
        "runtime": runtime,
        "session_id": session_id,
        "snapshot_bytes": snapshot_bytes,
        "coverage_status": "partial" if state.partial else "retained_snapshot_only",
        "warnings": state.warnings,
        "warnings_truncated": state.warnings_truncated,
        "omissions": state.omissions,
        "attachment_subtype_omissions": state.attachment_subtypes,
        "attachment_subtype_overflow": state.attachment_subtype_overflow,
        "items": items,
        "next_cursor": None if done else flags["stop"],
        "done": done,
    }


def execute(args, env=None):
    env = os.environ if env is None else env
    if type(args.max_chars) is not int or not 1 <= args.max_chars <= MAX_MAX_CHARS:
        raise ReaderError("invalid_args", "max-chars must be an integer from 1 to 50000.")
    if args.snapshot_bytes is not None and (type(args.snapshot_bytes) is not int or args.snapshot_bytes < 0):
        raise ReaderError("invalid_args", "snapshot-bytes must be an integer of 0 or more.")
    session_id = resolve_session_id(args.runtime, args.session_id, env)
    cursor = parse_cursor(args.cursor)
    path, _root = locate(args.runtime, session_id, args.path, args.home, env)
    if args.snapshot_bytes is None:
        try:
            info = os.lstat(path)
        except OSError as exc:
            raise ReaderError("unreadable", "Could not stat the transcript.", {"path": path, "reason": exc.strerror})
        if stat.S_ISLNK(info.st_mode):
            raise ReaderError("not_a_file", "Refusing to read a symlink.", {"path": path})
        if not stat.S_ISREG(info.st_mode):
            raise ReaderError("not_a_file", "Transcript path is not a regular file.", {"path": path})
        snapshot_bytes = info.st_size
    else:
        snapshot_bytes = args.snapshot_bytes
    return read_page(path, args.runtime, session_id, snapshot_bytes, cursor, args.max_chars, args.include_tools)


def write_error(exc):
    payload = {"error": {"code": exc.code, "message": exc.message, "details": exc.details}}
    sys.stderr.write(json.dumps(payload, ensure_ascii=False) + "\n")


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    try:
        page = execute(args)
    except ReaderError as exc:
        write_error(exc)
        return 2
    sys.stdout.write(json.dumps(page, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
