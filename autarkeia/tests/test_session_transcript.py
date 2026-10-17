import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.dont_write_bytecode = True
SCRIPT = Path(__file__).resolve().parents[1] / "bin" / "read-session-transcript.py"
spec = importlib.util.spec_from_file_location("read_session_transcript", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

SID = "11111111-1111-4111-8111-111111111111"
SID2 = "22222222-2222-4222-8222-222222222222"
OTHER = "33333333-3333-4333-8333-333333333333"


def dump(records):
    return "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records).encode("utf-8")


def meta(sid=SID):
    return {
        "timestamp": "2026-08-01T00:00:00Z",
        "type": "session_meta",
        "payload": {"id": sid, "cwd": "/tmp/not-a-selector"},
    }


def user(text, item_id=None, timestamp="2026-08-01T00:00:01Z", content=None):
    payload = {
        "type": "message",
        "role": "user",
        "content": content if content is not None else [{"type": "input_text", "text": text}],
    }
    if item_id is not None:
        payload["id"] = item_id
    record = {"type": "response_item", "payload": payload}
    if timestamp is not None:
        record["timestamp"] = timestamp
    return record


def assistant(text, item_id="msg_a", content=None):
    payload = {
        "type": "message",
        "role": "assistant",
        "id": item_id,
        "content": content if content is not None else [{"type": "output_text", "text": text}],
    }
    return {"timestamp": "2026-08-01T00:00:02Z", "type": "response_item", "payload": payload}


def cuser(text, uid, parent=None, content=None, sid=SID, **flags):
    record = {
        "type": "user",
        "uuid": uid,
        "parentUuid": parent,
        "sessionId": sid,
        "timestamp": "2026-08-01T00:00:01Z",
        "message": {"role": "user", "content": content if content is not None else text},
    }
    record.update(flags)
    return record


def cassistant(text, uid, parent=None, message_id="msg_a", content=None, sid=SID):
    if content is None:
        content = [{"type": "text", "text": text}]
    return {
        "type": "assistant",
        "uuid": uid,
        "parentUuid": parent,
        "sessionId": sid,
        "timestamp": "2026-08-01T00:00:02Z",
        "message": {"role": "assistant", "id": message_id, "content": content},
    }


def write_jsonl(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(dump(records))
    return path


def codex_path(root, records, sid=SID, name=None):
    folder = root / "sessions" / "2026" / "08" / "01"
    path = folder / (name or ("rollout-2026-08-01T00-00-00-%s.jsonl" % sid))
    return write_jsonl(path, records)


def claude_path(root, records, sid=SID, project="My Project"):
    return write_jsonl(root / "projects" / project / ("%s.jsonl" % sid), records)


class TranscriptReaderTests(unittest.TestCase):
    def invoke(self, args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = mod.main(list(args))
        stdout, stderr = out.getvalue(), err.getvalue()
        if code == 0:
            self.assertEqual(stderr, "")
            page = json.loads(stdout)
            self.assert_contract(page, self.max_chars(args))
            return code, page, stdout, stderr
        self.assertEqual(code, 2, stdout + stderr)
        self.assertEqual(stdout, "")
        try:
            payload = json.loads(stderr)
        except json.JSONDecodeError:
            self.fail(stderr)
        self.assertIn("code", payload["error"])
        return code, payload, stdout, stderr

    def max_chars(self, args):
        if "--max-chars" in args:
            return int(args[args.index("--max-chars") + 1])
        return 12000

    def assert_contract(self, page, max_chars):
        for key in ("source", "runtime", "session_id", "snapshot_bytes", "coverage_status",
                    "warnings", "items", "next_cursor", "done"):
            self.assertIn(key, page)
        self.assertIn(page["runtime"], ("codex", "claude"))
        self.assertEqual(page["session_id"], mod.norm_uuid(page["session_id"]))
        self.assertIn(page["coverage_status"], ("retained_snapshot_only", "partial"))
        self.assertNotIn("full", page["coverage_status"])
        self.assertNotIn("complete", page["coverage_status"])
        self.assertIsInstance(page["snapshot_bytes"], int)
        self.assertIsInstance(page["warnings"], list)
        self.assertLessEqual(len(page["items"]), mod.MAX_ITEMS)
        self.assertLessEqual(sum(len(item["text"]) for item in page["items"]), max_chars)
        self.assertEqual(page["done"], page["next_cursor"] is None)
        if page["next_cursor"] is not None:
            self.assertGreaterEqual(page["next_cursor"]["line"], 1)
            self.assertGreaterEqual(page["next_cursor"]["text_offset"], 0)
            self.assertIsInstance(page["next_cursor"]["segment"], int)
        for key in mod.OMISSION_KEYS:
            self.assertIsInstance(page["omissions"][key], int)
        for item in page["items"]:
            for key in ("line", "id", "parent_id", "timestamp", "role", "kind", "text",
                        "text_offset", "continued", "segment"):
                self.assertIn(key, item)
            self.assertGreaterEqual(item["line"], 1)
            self.assertNotEqual(item["role"], "human")
            self.assertNotIn("verified", item["kind"])
            if item["kind"] == "user_message_candidate":
                self.assertEqual(item["role"], "user")
            if item["kind"] == "assistant_message":
                self.assertEqual(item["role"], "assistant")
            if item["kind"] == "tool_evidence":
                self.assertEqual(item["role"], "tool")
                # A nearly full page can start a tool record with fewer characters
                # than the label. The slice is still the start of that label.
                # Later slices keep the original characters and do not repeat it.
                if item["text_offset"] == 0 and item["text"]:
                    marker = "[tool evidence]"
                    self.assertTrue(item["text"].startswith(marker) or marker.startswith(item["text"]))
            if item["kind"] == "compaction":
                self.assertIsNone(item["role"])
                self.assertEqual(item["text"], "")
            if item["kind"] == "nonhuman_context":
                self.assertEqual(item["role"], "nonhuman")
                self.assertEqual(item["text"], "")

    def walk(self, args):
        pages = []
        code, page, stdout, stderr = self.invoke(args)
        self.assertEqual(code, 0, stderr)
        pages.append(page)
        seen = []
        while not page["done"]:
            cursor = json.dumps(page["next_cursor"])
            self.assertNotIn(cursor, seen)
            seen.append(cursor)
            if len(seen) > 30:
                self.fail("pagination did not finish")
            code, page, stdout, stderr = self.invoke(self.with_pin(args, page))
            self.assertEqual(code, 0, stderr)
            pages.append(page)
        return pages

    def with_pin(self, args, page):
        cleaned = []
        skip = False
        for arg in args:
            if skip:
                skip = False
                continue
            if arg in ("--cursor", "--snapshot-bytes"):
                skip = True
                continue
            cleaned.append(arg)
        cleaned.extend(["--snapshot-bytes", str(page["snapshot_bytes"]),
                        "--cursor", json.dumps(page["next_cursor"])])
        return cleaned

    def joined(self, pages):
        groups = []
        for page in pages:
            for item in page["items"]:
                key = (item["line"], item["segment"], item["kind"])
                if groups and groups[-1][0] == key:
                    groups[-1][1].append(item)
                else:
                    groups.append((key, [item]))
        texts = []
        for _key, parts in groups:
            built = ""
            for index, part in enumerate(parts):
                self.assertEqual(part["text_offset"], len(built))
                built += part["text"]
                self.assertEqual(part["continued"], index != len(parts) - 1)
            texts.append((parts[0]["kind"], parts[0]["role"], built))
        return texts

    def file_bytes(self, root):
        return {str(path.relative_to(root)): path.read_bytes()
                for path in root.rglob("*") if path.is_file()}

    def test_help_is_plain(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            with self.assertRaises(SystemExit) as caught:
                mod.main(["--help"])
        self.assertEqual(caught.exception.code, 0)
        text = buf.getvalue().lower()
        for phrase in ("read-only", "does not write", "user_message_candidate", "not proof",
                       "snapshot", "cursor", "complete", "compaction", "tool evidence"):
            self.assertIn(phrase, text)

    def test_codex_basic_page_is_read_only_and_keeps_roles(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "home"
            path = codex_path(root, [
                meta(),
                user("hello"),
                assistant("ignored", content=[{"type": "output_text", "text": "foo"},
                                              {"type": "output_text", "text": "bar"}]),
            ])
            before = path.read_bytes()
            mtime = path.stat().st_mtime_ns
            names = self.file_bytes(root)
            code, page, _out, _err = self.invoke(["--runtime", "codex", "--home", str(root),
                                                  "--session-id", SID.upper()])
            self.assertEqual(code, 0)
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(path.stat().st_mtime_ns, mtime)
            self.assertEqual(self.file_bytes(root), names)
            self.assertEqual(page["source"], os.path.abspath(str(path)))
            self.assertEqual(page["session_id"], SID)
            self.assertEqual(page["snapshot_bytes"], path.stat().st_size)
            self.assertEqual(page["coverage_status"], "retained_snapshot_only")
            self.assertEqual(page["warnings"], [])
            self.assertTrue(all(value == 0 for value in page["omissions"].values()))
            self.assertEqual([(item["line"], item["role"], item["kind"], item["text"], item["id"], item["parent_id"])
                              for item in page["items"]], [
                (2, "user", "user_message_candidate", "hello", None, None),
                (3, "assistant", "assistant_message", "foo\nbar", "msg_a", None),
            ])

    def test_last_line_without_newline_crlf_and_bom_still_read(self):
        records = [meta(), user("plain")]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bare = codex_path(root / "bare", records)
            bare.write_bytes(bare.read_bytes().rstrip(b"\n"))
            crlf = codex_path(root / "crlf", records)
            crlf.write_bytes(crlf.read_bytes().replace(b"\n", b"\r\n"))
            bom = codex_path(root / "bom", records)
            bom.write_bytes(b"\xef\xbb\xbf" + bom.read_bytes())
            for home in (root / "bare", root / "crlf", root / "bom"):
                code, page, _out, _err = self.invoke(["--runtime", "codex", "--home", str(home), "--session-id", SID])
                self.assertEqual(code, 0)
                self.assertEqual([item["text"] for item in page["items"]], ["plain"])
                self.assertEqual(page["coverage_status"], "retained_snapshot_only")
                self.assertNotIn("truncated_record", [warning["code"] for warning in page["warnings"]])

    def test_compaction_keeps_originals_and_drops_summaries(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            codex_path(root, [
                meta(),
                user("ORIGINAL_A"),
                {"timestamp": "2026-08-01T00:00:03Z", "type": "compacted", "payload": {
                    "summary": "SUMMARY_BODY",
                    "replacement_history": [user("REPLACEMENT_SENTINEL")],
                }},
                user("ORIGINAL_B"),
                {"timestamp": "2026-08-01T00:00:04Z", "type": "compacted", "payload": {"summary": "SUMMARY_BODY_2"}},
                user("ORIGINAL_C"),
            ])
            code, page, out, err = self.invoke(["--runtime", "codex", "--home", str(root), "--session-id", SID])
            self.assertEqual(code, 0)
            self.assertEqual([(item["kind"], item["text"]) for item in page["items"]], [
                ("user_message_candidate", "ORIGINAL_A"),
                ("compaction", ""),
                ("user_message_candidate", "ORIGINAL_B"),
                ("compaction", ""),
                ("user_message_candidate", "ORIGINAL_C"),
            ])
            self.assertEqual(page["coverage_status"], "retained_snapshot_only")
            self.assertGreaterEqual(page["omissions"]["compaction_summaries"], 2)
            for secret in ("SUMMARY_BODY", "SUMMARY_BODY_2", "REPLACEMENT_SENTINEL"):
                self.assertNotIn(secret, out + err)

    def test_claude_originals_survive_multiple_boundaries(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            claude_path(root, [
                cuser("ORIGINAL_A", "a", None),
                cuser("SUMMARY_SENTINEL", "s", "a", isCompactSummary=True, isMeta=True),
                {"type": "system", "subtype": "compact_boundary", "uuid": "b1", "parentUuid": "s",
                 "sessionId": SID, "timestamp": "2026-08-01T00:00:03Z", "isMeta": True,
                 "content": "BOUNDARY_BODY"},
                cuser("ORIGINAL_B", "b", "b1"),
                {"type": "system", "subtype": "compact_boundary", "uuid": "b2", "parentUuid": "b",
                 "sessionId": SID, "timestamp": "2026-08-01T00:00:04Z", "content": "BOUNDARY_BODY_2"},
                cuser("ORIGINAL_C", "c", "b2"),
                {"type": "progress", "sessionId": SID, "uuid": "p", "timestamp": "2026-08-01T00:00:05Z",
                 "data": "PROGRESS_SENTINEL"},
                {"type": "file-history-snapshot", "sessionId": SID, "uuid": "f",
                 "timestamp": "2026-08-01T00:00:06Z", "snapshot": "FILE_HISTORY_SENTINEL"},
            ])
            code, page, out, err = self.invoke(["--runtime", "claude", "--home", str(root), "--session-id", SID])
            self.assertEqual(code, 0)
            self.assertEqual([(item["kind"], item["text"], item["parent_id"]) for item in page["items"]], [
                ("user_message_candidate", "ORIGINAL_A", None),
                ("compaction", "", "s"),
                ("user_message_candidate", "ORIGINAL_B", "b1"),
                ("compaction", "", "b"),
                ("user_message_candidate", "ORIGINAL_C", "b2"),
            ])
            self.assertEqual(page["coverage_status"], "retained_snapshot_only")
            self.assertNotIn("ambiguous_branch", [warning["code"] for warning in page["warnings"]])
            for secret in ("SUMMARY_SENTINEL", "BOUNDARY_BODY", "BOUNDARY_BODY_2",
                           "PROGRESS_SENTINEL", "FILE_HISTORY_SENTINEL"):
                self.assertNotIn(secret, out + err)

    def test_mirrors_are_not_duplicated(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            codex_path(root, [
                meta(),
                user("CANONICAL_USER"),
                {"timestamp": "2026-08-01T00:00:02Z", "type": "event_msg",
                 "payload": {"type": "user_message", "message": "MIRROR_ONLY"}},
                assistant("CANONICAL_ASSISTANT"),
                {"timestamp": "2026-08-01T00:00:03Z", "type": "event_msg",
                 "payload": {"type": "agent_message", "message": "MIRROR_ASSISTANT"}},
                {"timestamp": "2026-08-01T00:00:04Z", "type": "event_msg",
                 "payload": {"type": "task_complete", "last_agent_message": "LAST_ONLY"}},
                {"timestamp": "2026-08-01T00:00:05Z", "type": "event_msg",
                 "payload": {"type": "item_completed", "item": "ITEM_COPY"}},
            ])
            code, page, out, err = self.invoke(["--runtime", "codex", "--home", str(root), "--session-id", SID])
            self.assertEqual(code, 0)
            self.assertEqual([item["text"] for item in page["items"]], ["CANONICAL_USER", "CANONICAL_ASSISTANT"])
            self.assertGreaterEqual(page["omissions"]["mirrored_events"], 4)
            for secret in ("MIRROR_ONLY", "MIRROR_ASSISTANT", "LAST_ONLY", "ITEM_COPY"):
                self.assertNotIn(secret, out + err)

    def test_repeated_text_correction_order_and_id_dedup(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            codex_path(root, [
                meta(),
                user("yes"),
                user("yes"),
                user("the date is Monday"),
                user("correction: the date is Tuesday"),
                user("first wording", item_id="msg_same"),
                user("second wording", item_id="msg_same"),
            ])
            code, page, _out, _err = self.invoke(["--runtime", "codex", "--home", str(root), "--session-id", SID])
            self.assertEqual(code, 0)
            self.assertEqual([item["text"] for item in page["items"]], [
                "yes", "yes", "the date is Monday", "correction: the date is Tuesday", "first wording",
            ])
            self.assertEqual(page["omissions"]["duplicate_ids"], 1)

    def test_claude_dedup_uses_uuid_not_shared_message_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            claude_path(root, [
                cassistant("part one", "u1", message_id="msg_shared"),
                cassistant("part two", "u2", parent="u1", message_id="msg_shared"),
                cassistant("duplicate uuid", "u1", parent="u2", message_id="msg_other"),
            ])
            code, page, out, err = self.invoke(["--runtime", "claude", "--home", str(root), "--session-id", SID])
            self.assertEqual(code, 0)
            self.assertEqual([item["text"] for item in page["items"]], ["part one", "part two"])
            self.assertNotIn("duplicate uuid", out + err)
            self.assertEqual(page["omissions"]["duplicate_ids"], 1)

    def test_nonhuman_records_are_not_speech(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            codex_path(root, [
                meta(),
                user("KEEP_USER"),
                {"timestamp": "2026-08-01T00:00:02Z", "type": "response_item", "payload": {
                    "type": "message", "role": "developer",
                    "content": [{"type": "input_text", "text": "DEVELOPER_SECRET"}],
                }},
                {"timestamp": "2026-08-01T00:00:03Z", "type": "response_item", "payload": {
                    "type": "reasoning", "summary": [{"text": "REASONING_SECRET"}],
                    "encrypted_content": "REASONING_SECRET",
                }},
                {"timestamp": "2026-08-01T00:00:04Z", "type": "response_item", "payload": {
                    "type": "function_call_output", "call_id": "call_1", "output": "SECRET_TOOL_OUTPUT",
                }},
                {"timestamp": "2026-08-01T00:00:05Z", "type": "event_msg", "payload": {
                    "type": "agent_message", "agent_id": "agent-1", "message": "DELEGATED_BODY",
                }},
                {"timestamp": "2026-08-01T00:00:06Z", "type": "event_msg",
                 "payload": {"type": "token_count", "info": "TELEMETRY_SENTINEL"}},
                {"timestamp": "2026-08-01T00:00:07Z", "type": "turn_context",
                 "payload": {"cwd": "TELEMETRY_CWD_SENTINEL"}},
            ])
            hidden = ["--runtime", "codex", "--home", str(root), "--session-id", SID]
            code, page, out, err = self.invoke(hidden)
            self.assertEqual(code, 0)
            self.assertEqual([item["text"] for item in page["items"] if item["kind"] != "nonhuman_context"], ["KEEP_USER"])
            self.assertTrue(any(item["kind"] == "nonhuman_context" and item["text"] == "" for item in page["items"]))
            self.assertGreaterEqual(page["omissions"]["tool_evidence"], 1)
            self.assertGreaterEqual(page["omissions"]["developer_or_system"], 1)
            self.assertGreaterEqual(page["omissions"]["reasoning"], 1)
            self.assertGreaterEqual(page["omissions"]["nonhuman_context"], 1)
            self.assertEqual(page["coverage_status"], "retained_snapshot_only")
            for secret in ("DEVELOPER_SECRET", "REASONING_SECRET", "SECRET_TOOL_OUTPUT",
                           "DELEGATED_BODY", "TELEMETRY_SENTINEL", "TELEMETRY_CWD_SENTINEL"):
                self.assertNotIn(secret, out + err)
            code, shown, out, err = self.invoke(hidden + ["--include-tools"])
            self.assertEqual(code, 0)
            tool_items = [item for item in shown["items"] if item["kind"] == "tool_evidence"]
            self.assertEqual(len(tool_items), 1)
            self.assertIn("SECRET_TOOL_OUTPUT", tool_items[0]["text"])
            self.assertEqual(tool_items[0]["role"], "tool")
            self.assertNotIn("DEVELOPER_SECRET", out + err)
            self.assertNotIn("DELEGATED_BODY", out + err)

    def test_claude_tool_results_are_not_human(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            claude_path(root, [
                cuser("PERSON_SAID", "u1"),
                cuser("ignored", "u2", "u1", isMeta=True, content=[
                    {"type": "tool_result", "tool_use_id": "toolu_1", "content": "SECRET_TOOL_RESULT"},
                ]),
                cassistant("ASSISTANT_SAID", "a1", "u2", content=[
                    {"type": "text", "text": "ASSISTANT_SAID"},
                    {"type": "thinking", "thinking": "THINKING_SECRET"},
                    {"type": "tool_use", "id": "toolu_2", "name": "Read", "input": {"path": "SECRET_PATH"}},
                ]),
                cuser("META_SENTINEL", "m1", "a1", isMeta=True),
                cuser("SIDECHAIN_SENTINEL", "s1", "a1", isSidechain=True),
            ])
            args = ["--runtime", "claude", "--home", str(root), "--session-id", SID]
            code, page, out, err = self.invoke(args)
            self.assertEqual(code, 0)
            self.assertEqual([(item["kind"], item["text"]) for item in page["items"]], [
                ("user_message_candidate", "PERSON_SAID"),
                ("assistant_message", "ASSISTANT_SAID"),
            ])
            for secret in ("SECRET_TOOL_RESULT", "SECRET_PATH", "THINKING_SECRET",
                           "META_SENTINEL", "SIDECHAIN_SENTINEL"):
                self.assertNotIn(secret, out + err)
            self.assertGreaterEqual(page["omissions"]["tool_evidence"], 1)
            self.assertGreaterEqual(page["omissions"]["sidechain"], 1)
            code, shown, out, _err = self.invoke(args + ["--include-tools"])
            self.assertEqual(code, 0)
            self.assertEqual([item["role"] for item in shown["items"]], ["user", "tool", "assistant", "tool"])
            self.assertIn("SECRET_TOOL_RESULT", shown["items"][1]["text"])
            self.assertIn("SECRET_PATH", shown["items"][3]["text"])
            self.assertNotIn("THINKING_SECRET", out)
            self.assertNotIn("META_SENTINEL", out)
            self.assertNotIn("SIDECHAIN_SENTINEL", out)
            self.assertNotEqual(shown["items"][1]["role"], "user")

    def test_unknown_attachment_and_missing_timestamp_are_explicit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            codex_path(root, [
                meta(),
                user("KEEP_BEFORE"),
                {"type": "mystery", "timestamp": "2026-08-01T00:00:02Z", "secret": "UNKNOWN_SENTINEL"},
                user("caption", content=[
                    {"type": "input_image", "image_url": "data:image/png;base64,AAAASECRETBASE64"},
                    {"type": "input_text", "text": "caption"},
                    {"type": "widget", "text": "WIDGET_SECRET"},
                ]),
                user("no stamp", timestamp=None),
            ])
            code, page, out, err = self.invoke(["--runtime", "codex", "--home", str(root), "--session-id", SID])
            self.assertEqual(code, 0)
            self.assertEqual(page["coverage_status"], "partial")
            self.assertEqual([item["text"] for item in page["items"]], ["KEEP_BEFORE", "caption", "no stamp"])
            self.assertIsNone(page["items"][-1]["timestamp"])
            codes = [warning["code"] for warning in page["warnings"]]
            self.assertIn("unknown_record", codes)
            self.assertIn("unknown_content_block", codes)
            self.assertIn("attachment_omitted", codes)
            self.assertIn("missing_metadata", codes)
            for secret in ("UNKNOWN_SENTINEL", "AAAASECRETBASE64", "WIDGET_SECRET"):
                self.assertNotIn(secret, out + err)
            self.assertTrue(page["done"])

    def test_malformed_truncated_and_invalid_utf8_are_partial(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = codex_path(root, [meta(), user("KEEP_BEFORE"), user("KEEP_AFTER")])
            raw = path.read_bytes()
            first, rest = raw.split(b"\n", 1)
            second, third = rest.split(b"\n", 1)
            path.write_bytes(first + b"\n" + second + b"\n" + b'{"text": "BAD_JSON_SENTINEL"\n' + b"\xff\xfe\n" + third)
            code, page, out, err = self.invoke(["--runtime", "codex", "--home", str(root), "--session-id", SID])
            self.assertEqual(code, 0)
            self.assertEqual(page["coverage_status"], "partial")
            self.assertEqual([item["text"] for item in page["items"]], ["KEEP_BEFORE", "KEEP_AFTER"])
            codes = [warning["code"] for warning in page["warnings"]]
            self.assertIn("json_parse_error", codes)
            self.assertIn("encoding_error", codes)
            self.assertNotIn("BAD_JSON_SENTINEL", out + err)

            prefix = dump([meta(), user("KEEP")])
            last = json.dumps(user("AFTER_SENTINEL_AND_MORE_TEXT"), ensure_ascii=False).encode("utf-8")
            blob = prefix + last + b"\n"
            cut = blob.find(b"AFTER_SENTINEL_AND_MORE_TEXT") + len(b"AFTER_SENTINEL")
            self.assertLess(cut, len(blob))
            self.assertNotIn(b"\n", blob[len(prefix):cut])
            path.write_bytes(blob)
            code, page, out, err = self.invoke(["--runtime", "codex", "--home", str(root), "--session-id", SID,
                                                "--snapshot-bytes", str(cut)])
            self.assertEqual(code, 0)
            self.assertEqual([item["text"] for item in page["items"]], ["KEEP"])
            self.assertEqual(page["coverage_status"], "partial")
            self.assertIn("truncated_record", [warning["code"] for warning in page["warnings"]])
            self.assertNotIn("AFTER_SENTINEL", out + err)
            self.assertTrue(page["done"])

    def test_snapshot_stays_stable_when_the_file_grows_and_refuses_shrink(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = codex_path(root, [meta(), user("FIRST")])
            code, page, _out, _err = self.invoke(["--runtime", "codex", "--home", str(root), "--session-id", SID])
            self.assertEqual(code, 0)
            pinned = page["snapshot_bytes"]
            original = path.read_bytes()
            with path.open("ab") as handle:
                handle.write(dump([user("APPENDED_LATER")]))
            self.assertGreater(path.stat().st_size, pinned)
            code, again, out, err = self.invoke(["--runtime", "codex", "--home", str(root), "--session-id", SID,
                                                 "--snapshot-bytes", str(pinned)])
            self.assertEqual(code, 0)
            self.assertEqual(again["items"], page["items"])
            self.assertNotIn("APPENDED_LATER", out + err)
            code, grown, _out, _err = self.invoke(["--runtime", "codex", "--home", str(root), "--session-id", SID])
            self.assertEqual(code, 0)
            self.assertIn("APPENDED_LATER", [item["text"] for item in grown["items"]])

            exact = len(original)
            # original ended at a record boundary; pinning it excludes the append and is not a cut record.
            self.assertEqual(again["coverage_status"], "retained_snapshot_only")
            self.assertNotIn("truncated_record", [warning["code"] for warning in again["warnings"]])
            self.assertEqual(exact, pinned)

            code, payload, out, err = self.invoke(["--runtime", "codex", "--home", str(root), "--session-id", SID,
                                                   "--snapshot-bytes", str(path.stat().st_size + 5)])
            self.assertEqual(payload["error"]["code"], "snapshot_shrink")
            shrunk = original
            path.write_bytes(shrunk[:20])
            after = path.read_bytes()
            code, payload, out, err = self.invoke(["--runtime", "codex", "--home", str(root), "--session-id", SID,
                                                   "--snapshot-bytes", str(pinned)])
            self.assertEqual(payload["error"]["code"], "snapshot_shrink")
            self.assertEqual(path.read_bytes(), after)
            self.assertNotIn("FIRST", out + err)

    def test_long_text_continues_without_loss(self):
        phrase = "настройка"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            codex_path(root, [meta(), user(phrase), user("end")])
            pages = self.walk(["--runtime", "codex", "--home", str(root), "--session-id", SID, "--max-chars", "4"])
            for page in pages:
                self.assertLessEqual(sum(len(item["text"]) for item in page["items"]), 4)
                self.assertEqual(page["coverage_status"], "retained_snapshot_only")
            self.assertEqual([(kind, text) for kind, _role, text in self.joined(pages)], [
                ("user_message_candidate", phrase),
                ("user_message_candidate", "end"),
            ])

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            codex_path(root, [meta(), user("x" * 12001)])
            pages = self.walk(["--runtime", "codex", "--home", str(root), "--session-id", SID])
            self.assertEqual("".join(item["text"] for page in pages for item in page["items"]), "x" * 12001)
            self.assertEqual(len(pages[0]["items"][0]["text"]), 12000)
            self.assertTrue(pages[0]["items"][0]["continued"])
            self.assertFalse(pages[-1]["items"][-1]["continued"])

    def test_tool_pages_match_the_unsplit_text(self):
        speech = "S" * 50
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            claude_path(root, [
                cassistant(speech, "a1", content=[
                    {"type": "text", "text": speech},
                    {"type": "tool_use", "id": "toolu_1", "name": "Read", "input": {"path": "SECRET_PATH"}},
                ]),
            ])
            base = ["--runtime", "claude", "--home", str(root), "--session-id", SID,
                    "--include-tools", "--max-chars", "50000"]
            full = self.joined(self.walk(base))
            # 25 divides the 50-character speech, so the tool text starts on a fresh page.
            small = self.joined(self.walk(["--runtime", "claude", "--home", str(root), "--session-id", SID,
                                           "--include-tools", "--max-chars", "25"]))
            self.assertEqual(small, full)
            # 30 leaves 10 characters on the page after the speech. The tool label is
            # longer than that, so the first fragment is only a prefix of the label.
            tight_pages = self.walk(["--runtime", "claude", "--home", str(root), "--session-id", SID,
                                     "--include-tools", "--max-chars", "30"])
            tight = self.joined(tight_pages)
            self.assertEqual(tight, full)
            self.assertEqual(full[0][2], speech)
            self.assertEqual(full[1][0], "tool_evidence")
            self.assertIn("SECRET_PATH", full[1][2])
            self.assertNotIn("SECRET_PATH", full[0][2])
            marker = "[tool evidence]"
            tool_parts = [item for page in tight_pages for item in page["items"]
                          if item["kind"] == "tool_evidence"]
            self.assertGreaterEqual(len(tool_parts), 2)
            self.assertEqual(tool_parts[0]["text_offset"], 0)
            self.assertLess(len(tool_parts[0]["text"]), len(marker))
            self.assertTrue(marker.startswith(tool_parts[0]["text"]))
            rebuilt = "".join(part["text"] for part in tool_parts)
            self.assertEqual(rebuilt, full[1][2])
            self.assertEqual(rebuilt.count(marker), 1)
            self.assertGreater(tool_parts[1]["text_offset"], 0)
            self.assertFalse(tool_parts[1]["text"].startswith(marker))

    def test_invalid_cursor_and_out_of_range(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            codex_path(root, [meta(), user("short")])
            base = ["--runtime", "codex", "--home", str(root), "--session-id", SID]
            invalid = [
                "not-json",
                "[]",
                "{}",
                '{"line": 1}',
                '{"text_offset": 0}',
                '{"line": 0, "text_offset": 0}',
                '{"line": 1, "text_offset": -1}',
                '{"line": true, "text_offset": 0}',
                '{"line": "1", "text_offset": 0}',
                '{"line": 1, "text_offset": 0, "extra": 1}',
            ]
            for raw in invalid:
                code, payload, _out, _err = self.invoke(base + ["--cursor", raw])
                self.assertEqual(payload["error"]["code"], "invalid_cursor")
            code, page, _out, _err = self.invoke(base)
            line = page["items"][0]["line"]
            for raw in (
                '{"line": %s, "text_offset": 0}' % line,
                json.dumps({"line": 99999, "text_offset": 0}),
                json.dumps({"line": line, "text_offset": len("short")}),
                json.dumps({"line": line, "text_offset": 999, "segment": 0}),
                json.dumps({"line": line, "text_offset": 0, "segment": 5}),
            ):
                if raw == '{"line": %s, "text_offset": 0}' % line:
                    code, ok, _out, _err = self.invoke(base + ["--cursor", raw])
                    self.assertEqual(code, 0)
                    self.assertEqual(ok["items"][0]["text"], "short")
                    continue
                code, payload, _out, _err = self.invoke(base + ["--cursor", raw])
                self.assertEqual(payload["error"]["code"], "cursor_out_of_range")
            code, payload, _out, _err = self.invoke(base + ["--max-chars", "0"])
            self.assertEqual(payload["error"]["code"], "invalid_args")
            code, payload, _out, _err = self.invoke(base + ["--max-chars", "50001"])
            self.assertEqual(payload["error"]["code"], "invalid_args")
            code, page, _out, _err = self.invoke(base + ["--max-chars", "50000"])
            self.assertEqual(code, 0)
            self.assertEqual(page["items"][0]["text"], "short")

    def test_identity_mismatch_multiple_and_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "codex"
            path = codex_path(root, [meta(SID2), user("LEAK_MISMATCH")])
            before = path.read_bytes()
            code, payload, out, err = self.invoke(["--runtime", "codex", "--home", str(root), "--session-id", SID])
            self.assertEqual(payload["error"]["code"], "session_id_mismatch")
            self.assertNotIn("LEAK_MISMATCH", out + err)
            self.assertEqual(path.read_bytes(), before)

            missing_root = Path(tmp) / "missing"
            codex_path(missing_root, [user("LEAK_MISSING")])
            code, payload, out, err = self.invoke(["--runtime", "codex", "--home", str(missing_root), "--session-id", SID])
            self.assertEqual(payload["error"]["code"], "missing_session_id")
            self.assertNotIn("LEAK_MISSING", out + err)

            disagree = Path(tmp) / "disagree"
            codex_path(disagree, [{
                "timestamp": "2026-08-01T00:00:00Z",
                "type": "session_meta",
                "payload": {"id": SID, "session_id": SID2},
            }, user("LEAK_DISAGREE")])
            code, payload, out, err = self.invoke(["--runtime", "codex", "--home", str(disagree), "--session-id", SID])
            self.assertEqual(payload["error"]["code"], "session_id_mismatch")
            self.assertNotIn("LEAK_DISAGREE", out + err)

            session_field = Path(tmp) / "field"
            codex_path(session_field, [{
                "timestamp": "2026-08-01T00:00:00Z",
                "type": "session_meta",
                "payload": {"session_id": SID.upper()},
            }, user("FROM_SESSION_FIELD")])
            code, page, _out, _err = self.invoke(["--runtime", "codex", "--home", str(session_field), "--session-id", SID])
            self.assertEqual(code, 0)
            self.assertEqual(page["items"][0]["text"], "FROM_SESSION_FIELD")
            self.assertEqual(page["session_id"], SID)

            both = Path(tmp) / "both"
            codex_path(both, [meta(), user("BODY_SESSIONS")])
            archived = both / "archived_sessions"
            write_jsonl(archived / ("%s.jsonl" % SID), [meta(), user("BODY_ARCHIVED")])
            code, payload, out, err = self.invoke(["--runtime", "codex", "--home", str(both), "--session-id", SID])
            self.assertEqual(payload["error"]["code"], "multiple_candidates")
            self.assertEqual(payload["error"]["details"]["count"], 2)
            self.assertNotIn("BODY_SESSIONS", out + err)
            self.assertNotIn("BODY_ARCHIVED", out + err)

            only_archived = Path(tmp) / "archived-only"
            write_jsonl(only_archived / "archived_sessions" / ("%s.jsonl" % SID), [meta(), user("ARCHIVED_ONLY")])
            code, page, _out, _err = self.invoke(["--runtime", "codex", "--home", str(only_archived), "--session-id", SID])
            self.assertEqual(code, 0)
            self.assertEqual(page["items"][0]["text"], "ARCHIVED_ONLY")

            claude_root = Path(tmp) / "claude"
            bare = dict(cuser("LEAK_CLAUDE_MISSING", "u1"))
            del bare["sessionId"]
            write_jsonl(claude_root / "projects" / "proj" / ("%s.jsonl" % SID), [bare])
            code, payload, out, err = self.invoke(["--runtime", "claude", "--home", str(claude_root), "--session-id", SID])
            self.assertEqual(payload["error"]["code"], "missing_session_id")
            self.assertNotIn("LEAK_CLAUDE_MISSING", out + err)

            wrong = Path(tmp) / "claude-wrong"
            claude_path(wrong, [cuser("LEAK_WRONG", "u1", sid=SID2), cuser("ALSO", "u2", "u1")])
            code, payload, out, err = self.invoke(["--runtime", "claude", "--home", str(wrong), "--session-id", SID])
            self.assertEqual(payload["error"]["code"], "session_id_mismatch")
            self.assertNotIn("LEAK_WRONG", out + err)

    def test_discovery_uses_the_exact_filename_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            real = codex_path(root, [meta(), user("EXACT_FILE")])
            write_jsonl(real.parent / "notes.jsonl", [meta(), user("DECOY_CONTENT")])
            write_jsonl(root / "sessions" / SID / "notes.jsonl", [meta(), user("DIR_SENTINEL")])
            write_jsonl(root / "sessions" / "2026" / "09" / "02" / ("rollout-2026-09-02T00-00-00-%s.jsonl" % OTHER),
                        [meta(OTHER), user("NEWER_OTHER")])
            write_jsonl(real.parent / ("rollout-2026-08-01T00-00-00-%saa.jsonl" % SID), [meta(), user("EXTRA_HEX")])
            code, page, out, err = self.invoke(["--runtime", "codex", "--home", str(root), "--session-id", SID])
            self.assertEqual(code, 0)
            self.assertEqual(page["source"], os.path.abspath(str(real)))
            self.assertEqual([item["text"] for item in page["items"]], ["EXACT_FILE"])
            for secret in ("DECOY_CONTENT", "DIR_SENTINEL", "NEWER_OTHER", "EXTRA_HEX"):
                self.assertNotIn(secret, out + err)

            absent = Path(tmp) / "absent"
            write_jsonl(absent / "sessions" / "2026" / "08" / "01" / "notes.jsonl", [meta(), user("DECOY_CONTENT")])
            write_jsonl(absent / "sessions" / "2026" / "09" / "02" / ("rollout-2026-09-02T00-00-00-%s.jsonl" % OTHER),
                        [meta(OTHER), user("NEWER_OTHER")])
            code, payload, out, err = self.invoke(["--runtime", "codex", "--home", str(absent), "--session-id", SID])
            self.assertEqual(payload["error"]["code"], "not_found")
            self.assertNotIn("DECOY_CONTENT", out + err)
            self.assertNotIn("NEWER_OTHER", out + err)

            projects = Path(tmp) / "projects-home"
            claude_path(projects, [cuser("CHILD_TEXT", "child")], sid=SID, project="demo")
            write_jsonl(projects / "projects" / "demo" / ("%s.jsonl" % SID2), [cuser("PARENT_TEXT", "parent", sid=SID2)])
            write_jsonl(projects / "projects" / "demo" / "subagents" / ("%s.jsonl" % SID),
                        [cuser("SUBAGENT_TEXT", "sub")])
            nested = projects / "projects" / "demo" / SID / "subagents"
            write_jsonl(nested / "agent.jsonl", [cuser("NESTED_SUBAGENT", "n1")])
            code, page, out, err = self.invoke(["--runtime", "claude", "--home", str(projects), "--session-id", SID])
            self.assertEqual(code, 0)
            self.assertEqual(page["items"][0]["text"], "CHILD_TEXT")
            for secret in ("PARENT_TEXT", "SUBAGENT_TEXT", "NESTED_SUBAGENT"):
                self.assertNotIn(secret, out + err)

            only_sub = Path(tmp) / "only-sub"
            write_jsonl(only_sub / "projects" / "demo" / "subagents" / ("%s.jsonl" % SID),
                        [cuser("SUBAGENT_TEXT", "sub")])
            write_jsonl(only_sub / "projects" / ("%s.jsonl" % SID), [cuser("TOO_SHALLOW", "x")])
            code, payload, out, err = self.invoke(["--runtime", "claude", "--home", str(only_sub), "--session-id", SID])
            self.assertEqual(payload["error"]["code"], "not_found")
            self.assertNotIn("SUBAGENT_TEXT", out + err)
            self.assertNotIn("TOO_SHALLOW", out + err)

            multi = Path(tmp) / "multi-claude"
            claude_path(multi, [cuser("ONE_BODY", "a")], project="alpha")
            claude_path(multi, [cuser("TWO_BODY", "b")], project="beta")
            code, payload, out, err = self.invoke(["--runtime", "claude", "--home", str(multi), "--session-id", SID])
            self.assertEqual(payload["error"]["code"], "multiple_candidates")
            self.assertNotIn("ONE_BODY", out + err)
            self.assertNotIn("TWO_BODY", out + err)

    def test_custom_homes_spaces_env_and_explicit_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "My Codex Home"
            codex_path(home, [meta(), user("SPACED_HOME")])
            code, page, _out, _err = self.invoke(["--runtime", "codex", "--home", str(home), "--session-id", SID])
            self.assertEqual(code, 0)
            self.assertEqual(page["items"][0]["text"], "SPACED_HOME")
            self.assertIn("My Codex Home", page["source"])

            claude_home = Path(tmp) / "Claude Config"
            claude_path(claude_home, [cuser("CLAUDE_SPACED", "u1")], project="Project Dir")
            with mock.patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": str(claude_home),
                                              "CODEX_THREAD_ID": SID, "CLAUDE_SESSION_ID": SID}):
                code, page, _out, _err = self.invoke(["--runtime", "claude", "--session-id", SID])
                self.assertEqual(code, 0)
                self.assertEqual(page["items"][0]["text"], "CLAUDE_SPACED")
                code, payload, out, err = self.invoke(["--runtime", "claude"])
                self.assertEqual(payload["error"]["code"], "invalid_args")
                self.assertNotIn("CLAUDE_SPACED", out + err)

            empty = Path(tmp) / "empty home"
            empty.mkdir()
            write_jsonl(empty / "sessions" / ("%s.jsonl" % SID), [meta(), user("ENV_HOME_DECOY")])
            with mock.patch.dict(os.environ, {"CODEX_HOME": str(empty), "CODEX_THREAD_ID": SID}):
                code, page, out, err = self.invoke(["--runtime", "codex", "--home", str(home)])
                self.assertEqual(code, 0)
                self.assertEqual(page["items"][0]["text"], "SPACED_HOME")
                self.assertNotIn("ENV_HOME_DECOY", out + err)
                code, page, _out, _err = self.invoke(["--runtime", "codex"])
                self.assertEqual(code, 0)
                self.assertEqual(page["items"][0]["text"], "ENV_HOME_DECOY")

            with mock.patch.dict(os.environ, {"CODEX_HOME": str(home)}, clear=False):
                os.environ.pop("CODEX_THREAD_ID", None)
                code, payload, _out, _err = self.invoke(["--runtime", "codex"])
                self.assertEqual(payload["error"]["code"], "invalid_args")

            explicit = Path(tmp) / "My Transcripts" / "notes.jsonl"
            write_jsonl(explicit, [meta(), user("EXPLICIT_PATH")])
            code, page, out, err = self.invoke(["--runtime", "codex", "--session-id", SID, "--path", str(explicit),
                                                "--home", str(empty)])
            self.assertEqual(code, 0)
            self.assertEqual(page["source"], os.path.abspath(str(explicit)))
            self.assertEqual(page["items"][0]["text"], "EXPLICIT_PATH")
            self.assertNotIn("ENV_HOME_DECOY", out + err)

            link_target = Path(tmp) / "target.jsonl"
            write_jsonl(link_target, [meta(), user("LINK_TARGET")])
            link = Path(tmp) / "link.jsonl"
            link.symlink_to(link_target)
            code, payload, out, err = self.invoke(["--runtime", "codex", "--session-id", SID, "--path", str(link)])
            self.assertEqual(payload["error"]["code"], "not_a_file")
            self.assertNotIn("LINK_TARGET", out + err)
            folder = Path(tmp) / "a-directory"
            folder.mkdir()
            code, payload, _out, _err = self.invoke(["--runtime", "codex", "--session-id", SID, "--path", str(folder)])
            self.assertEqual(payload["error"]["code"], "not_a_file")

    def test_ambiguous_branch_and_parent_cycle_keep_every_record(self):
        self.assertEqual(mod.obj_line({"_line": 4}), 4)
        self.assertIsNone(mod.obj_line({}))
        self.assertIsNone(mod.obj_line({"_line": None}))
        self.assertIsNone(mod.obj_line({"_line": True}))
        self.assertIsNone(mod.obj_line("nope"))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "branch"
            claude_path(root, [
                cuser("root", "a", None),
                cuser("left", "b", "a"),
                cuser("right", "c", "a"),
                cuser("orphan", "d", "missing-parent-uuid"),
            ])
            code, page, _out, _err = self.invoke(["--runtime", "claude", "--home", str(root), "--session-id", SID])
            self.assertEqual(code, 0)
            self.assertEqual([item["text"] for item in page["items"]], ["root", "left", "right", "orphan"])
            self.assertEqual([item["parent_id"] for item in page["items"]], [None, "a", "a", "missing-parent-uuid"])
            codes = [warning["code"] for warning in page["warnings"]]
            self.assertIn("ambiguous_branch", codes)
            self.assertIn("missing_parent", codes)
            self.assertEqual(page["coverage_status"], "retained_snapshot_only")
            branch = next(warning for warning in page["warnings"] if warning["code"] == "ambiguous_branch")
            self.assertEqual(branch["line"], 3)
            wording = branch["message"].lower()
            self.assertIn("possible fork", wording)
            self.assertIn("parallel", wording)
            self.assertIn("verify the source", wording)
            self.assertIn("conflicting candidates", wording)
            missing = next(warning for warning in page["warnings"] if warning["code"] == "missing_parent")
            self.assertEqual(missing["line"], 4)

            cycled = Path(tmp) / "cycle"
            claude_path(cycled, [cuser("CYCLE_A", "a", "b"), cuser("CYCLE_B", "b", "a")])
            code, page, _out, _err = self.invoke(["--runtime", "claude", "--home", str(cycled), "--session-id", SID])
            self.assertEqual(code, 0)
            self.assertEqual([item["text"] for item in page["items"]], ["CYCLE_A", "CYCLE_B"])
            cycle = next(warning for warning in page["warnings"] if warning["code"] == "parent_cycle")
            self.assertIn(cycle["line"], (1, 2))

    def test_pasted_text_is_not_executed(self):
        payload = 'os.system("echo PWND")'
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            codex_path(root, [meta(), user(payload)])
            code, page, _out, _err = self.invoke(["--runtime", "codex", "--home", str(root), "--session-id", SID])
            self.assertEqual(code, 0)
            self.assertEqual(page["items"][0]["text"], payload)
            self.assertEqual(page["items"][0]["kind"], "user_message_candidate")

    def test_known_telemetry_and_metadata_are_not_unknown_gaps(self):
        codex_secrets = (
            "TOKEN_USAGE_SECRET", "WORLD_STATE_SECRET", "SETTINGS_SECRET",
            "INTER_AGENT_SECRET", "AGENT_MESSAGE_SECRET",
        )
        codex_records = [
            meta(),
            user("KEEP_TELEMETRY"),
            {"timestamp": "2026-08-01T00:00:08Z", "type": "token_usage_record",
             "payload": {"text": "TOKEN_USAGE_SECRET"}},
            {"timestamp": "2026-08-01T00:00:08Z", "type": "world_state",
             "payload": {"text": "WORLD_STATE_SECRET"}},
            {"timestamp": "2026-08-01T00:00:08Z", "type": "event_msg",
             "payload": {"type": "thread_settings_applied", "text": "SETTINGS_SECRET"}},
            {"timestamp": "2026-08-01T00:00:08Z", "type": "inter_agent_communication_metadata",
             "payload": {"text": "INTER_AGENT_SECRET"}},
            {"timestamp": "2026-08-01T00:00:09Z", "type": "response_item", "payload": {
                "type": "agent_message", "id": "agent-msg-1",
                "content": [{"type": "input_text", "text": "AGENT_MESSAGE_SECRET"}],
            }},
        ]
        claude_meta = [
            ("custom-title", "TITLE_SECRET"),
            ("agent-name", "NAME_SECRET"),
            ("atis-latch", "LATCH_SECRET"),
            ("bridge-session", "BRIDGE_SECRET"),
            ("file-history-delta", "DELTA_SECRET"),
            ("cost-state", "COST_SECRET"),
        ]
        claude_records = [cuser("KEEP_META", "u1")]
        for name, secret in claude_meta:
            claude_records.append({
                "type": name, "sessionId": SID, "timestamp": "2026-08-01T00:00:03Z",
                "title": secret, "name": secret, "settings": secret,
            })
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            codex_path(root / "codex", codex_records)
            code, page, out, err = self.invoke(["--runtime", "codex", "--home", str(root / "codex"),
                                                "--session-id", SID])
            self.assertEqual(code, 0)
            self.assertEqual(page["coverage_status"], "retained_snapshot_only")
            self.assertEqual(page["omissions"]["telemetry"], 3)
            self.assertEqual(page["omissions"]["nonhuman_context"], 2)
            self.assertEqual(page["omissions"]["unknown_records"], 0)
            self.assertEqual([item["text"] for item in page["items"] if item["kind"] != "nonhuman_context"],
                             ["KEEP_TELEMETRY"])
            self.assertEqual(sum(item["kind"] == "nonhuman_context" for item in page["items"]), 2)
            self.assertNotIn("unknown_record", [warning["code"] for warning in page["warnings"]])
            for secret in codex_secrets:
                self.assertNotIn(secret, out + err)

            codex_path(root / "codex-gap", codex_records + [
                {"type": "mystery_gap", "timestamp": "2026-08-01T00:00:10Z", "secret": "STILL_UNKNOWN_SECRET"},
            ])
            code, page, out, err = self.invoke(["--runtime", "codex", "--home", str(root / "codex-gap"),
                                                "--session-id", SID])
            self.assertEqual(code, 0)
            self.assertEqual(page["coverage_status"], "partial")
            self.assertEqual(page["omissions"]["unknown_records"], 1)
            self.assertEqual(page["omissions"]["telemetry"], 3)
            self.assertNotIn("STILL_UNKNOWN_SECRET", out + err)

            claude_path(root / "claude", claude_records)
            code, page, out, err = self.invoke(["--runtime", "claude", "--home", str(root / "claude"),
                                                "--session-id", SID])
            self.assertEqual(code, 0)
            self.assertEqual(page["coverage_status"], "retained_snapshot_only")
            self.assertEqual(page["omissions"]["telemetry"], 6)
            self.assertEqual(page["omissions"]["unknown_records"], 0)
            self.assertEqual([item["text"] for item in page["items"]], ["KEEP_META"])
            self.assertNotIn("unknown_record", [warning["code"] for warning in page["warnings"]])
            for _name, secret in claude_meta:
                self.assertNotIn(secret, out + err)

            claude_path(root / "claude-gap", claude_records + [{
                "type": "not-a-real-claude-record", "sessionId": SID,
                "timestamp": "2026-08-01T00:00:04Z", "body": "CLAUDE_UNKNOWN_SECRET",
            }])
            code, page, out, err = self.invoke(["--runtime", "claude", "--home", str(root / "claude-gap"),
                                                "--session-id", SID])
            self.assertEqual(code, 0)
            self.assertEqual(page["coverage_status"], "partial")
            self.assertEqual(page["omissions"]["unknown_records"], 1)
            self.assertEqual(page["omissions"]["telemetry"], 6)
            self.assertNotIn("CLAUDE_UNKNOWN_SECRET", out + err)

    def test_claude_attachments_are_not_human_messages(self):
        inner = [
            ("edited_text_file", "ATTACH_EDIT_SECRET"),
            ("compact_file_reference", "ATTACH_COMPACT_SECRET"),
            ("prompt_snapshot", "ATTACH_PROMPT_SECRET"),
            ("read_truncation_notice", "ATTACH_TRUNC_SECRET"),
            ("total_tokens_reminder", "ATTACH_TOKEN_SECRET"),
            ("environment", "ATTACH_ENV_SECRET"),
            ("instructions", "ATTACH_INSTR_SECRET"),
            ("hook_success", "ATTACH_HOOK_SECRET"),
            ("custom_context_blob", "ATTACH_CUSTOM_SECRET"),
        ]
        records = [cuser("KEEP_PERSON", "person")]
        for index, (kind, secret) in enumerate(inner):
            records.append({
                "type": "attachment",
                "uuid": "att-%s" % index,
                "sessionId": SID,
                "timestamp": "2026-08-01T00:00:04Z",
                "renderedRole": "user",
                "attachment": {"type": kind, "text": secret, "content": secret},
            })
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            claude_path(root, records)
            code, page, out, err = self.invoke(["--runtime", "claude", "--home", str(root), "--session-id", SID])
            self.assertEqual(code, 0)
            self.assertEqual(page["coverage_status"], "retained_snapshot_only")
            self.assertEqual([(item["role"], item["kind"], item["text"]) for item in page["items"]], [
                ("user", "user_message_candidate", "KEEP_PERSON"),
            ])
            self.assertEqual(page["omissions"]["attachments"], len(inner))
            self.assertEqual(page["omissions"]["telemetry"], 0)
            self.assertEqual(page["omissions"]["unknown_records"], 0)
            notes = [warning for warning in page["warnings"] if warning["code"] == "context_attachment_omitted"]
            self.assertEqual(len(notes), 1)
            self.assertEqual(notes[0]["line"], 2)
            message = notes[0]["message"].lower()
            self.assertIn("not human", message)
            self.assertIn("source", message)
            for _kind, secret in inner:
                self.assertNotIn(secret, out + err)

    def test_content_item_kinds_mark_injected_context(self):
        def kinds_user(content, kinds, item_id):
            record = user("unused", item_id=item_id, content=content)
            record["payload"]["internal_chat_message_metadata_passthrough"] = {
                "content_item_kinds": kinds,
            }
            return record

        injected_kinds = [
            "agents_md.instructions",
            "environments.environment_context",
            "additional_content.codex_apps_open_page",
        ]
        records = [meta()]
        secrets = []
        for kind in injected_kinds:
            secret = kind.upper() + "_SECRET"
            secrets.append(secret)
            records.append(kinds_user(
                [{"type": "input_text", "text": secret}], [kind], "k-" + kind,
            ))
        records.append(kinds_user(
            [{"type": "input_text", "text": "ALL_THREE_SECRET"}], list(injected_kinds), "k-all",
        ))
        secrets.append("ALL_THREE_SECRET")
        records.append(kinds_user([
            {"type": "input_text", "text": "INSTR_BLOCK"},
            {"type": "input_text", "text": "GENUINE_USER_SENTENCE"},
        ], ["agents_md.instructions", "user.text"], "k-mixed"))
        records.append(kinds_user(
            [{"type": "input_text", "text": "UNKNOWN_MIX_TEXT"}],
            ["agents_md.instructions", "mystery.kind"],
            "k-unknown",
        ))
        records.append(kinds_user(
            [{"type": "input_text", "text": "PLAIN_USER_TEXT"}], ["user.text"], "k-plain",
        ))
        records.append(kinds_user(
            [{"type": "input_text", "text": "EMPTY_KINDS_USER"}], [], "k-empty",
        ))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            codex_path(root, records)
            code, page, out, err = self.invoke(["--runtime", "codex", "--home", str(root), "--session-id", SID])
            self.assertEqual(code, 0)
            self.assertEqual(page["coverage_status"], "retained_snapshot_only")
            self.assertEqual(page["omissions"]["unknown_records"], 0)
            by_id = {item["id"]: item for item in page["items"]}
            for kind in injected_kinds:
                item = by_id["k-" + kind]
                self.assertEqual(item["kind"], "nonhuman_context")
                self.assertEqual(item["text"], "")
                self.assertEqual(item["content_item_kinds"], [kind])
            all_three = by_id["k-all"]
            self.assertEqual(all_three["kind"], "nonhuman_context")
            self.assertEqual(all_three["text"], "")
            self.assertEqual(all_three["content_item_kinds"], injected_kinds)
            mixed = by_id["k-mixed"]
            self.assertEqual(mixed["kind"], "user_message_candidate")
            self.assertEqual(mixed["role"], "user")
            self.assertIn("GENUINE_USER_SENTENCE", mixed["text"])
            self.assertEqual(mixed["content_item_kinds"], ["agents_md.instructions", "user.text"])
            unknown = by_id["k-unknown"]
            self.assertEqual(unknown["kind"], "user_message_candidate")
            self.assertEqual(unknown["text"], "UNKNOWN_MIX_TEXT")
            self.assertEqual(unknown["content_item_kinds"], ["agents_md.instructions", "mystery.kind"])
            plain = by_id["k-plain"]
            self.assertEqual(plain["kind"], "user_message_candidate")
            self.assertEqual(plain["text"], "PLAIN_USER_TEXT")
            self.assertEqual(plain["content_item_kinds"], ["user.text"])
            empty = by_id["k-empty"]
            self.assertEqual(empty["kind"], "user_message_candidate")
            self.assertEqual(empty["text"], "EMPTY_KINDS_USER")
            self.assertEqual(empty["content_item_kinds"], [])
            for secret in secrets:
                self.assertNotIn(secret, out + err)

    def test_missing_message_shape_role_and_text_are_partial(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            codex_path(root / "codex", [
                meta(),
                user("KEEP_BEFORE"),
                user("ignored", content=[
                    {"type": "input_text", "note": "EMPTY_BLOCK_SECRET"},
                    {"type": "input_text", "text": ""},
                ]),
                {"timestamp": "2026-08-01T00:00:03Z", "type": "response_item", "payload": {
                    "type": "message", "role": "user", "id": "bare", "note": "MISSING_CONTENT_SECRET",
                }},
                assistant("KEEP_AFTER", content=[
                    {"type": "output_text", "note": "ASSIST_EMPTY_SECRET"},
                    {"type": "output_text", "text": "KEEP_AFTER"},
                ]),
            ])
            code, page, out, err = self.invoke(["--runtime", "codex", "--home", str(root / "codex"),
                                                "--session-id", SID])
            self.assertEqual(code, 0)
            self.assertEqual(page["coverage_status"], "partial")
            self.assertEqual([item["text"] for item in page["items"]], ["KEEP_BEFORE", "KEEP_AFTER"])
            self.assertIn("missing_metadata", [warning["code"] for warning in page["warnings"]])
            for secret in ("EMPTY_BLOCK_SECRET", "MISSING_CONTENT_SECRET", "ASSIST_EMPTY_SECRET"):
                self.assertNotIn(secret, out + err)

            codex_path(root / "empty-only", [meta(), user("ignored", content=[{"type": "input_text"}])])
            code, page, out, err = self.invoke(["--runtime", "codex", "--home", str(root / "empty-only"),
                                                "--session-id", SID])
            self.assertEqual(code, 0)
            self.assertEqual(page["items"], [])
            self.assertEqual(page["coverage_status"], "partial")

            claude_path(root / "claude", [
                cuser("KEEP_C", "u1"),
                cuser("ignored", "u2", "u1", content=[{"type": "text", "note": "CLAUDE_EMPTY_SECRET"}]),
                {"type": "user", "uuid": "u3", "parentUuid": "u2", "sessionId": SID,
                 "timestamp": "2026-08-01T00:00:03Z",
                 "message": {"role": "user", "note": "CLAUDE_MISSING_CONTENT_SECRET"}},
                cassistant("KEEP_C2", "a1", "u3", content=[
                    {"type": "text"},
                    {"type": "text", "text": "KEEP_C2"},
                ]),
            ])
            code, page, out, err = self.invoke(["--runtime", "claude", "--home", str(root / "claude"),
                                                "--session-id", SID])
            self.assertEqual(code, 0)
            self.assertEqual(page["coverage_status"], "partial")
            self.assertEqual([item["text"] for item in page["items"]], ["KEEP_C", "KEEP_C2"])
            self.assertIn("missing_metadata", [warning["code"] for warning in page["warnings"]])
            self.assertNotIn("CLAUDE_EMPTY_SECRET", out + err)
            self.assertNotIn("CLAUDE_MISSING_CONTENT_SECRET", out + err)

            claude_path(root / "claude-empty", [cuser("ignored", "u1", content=[{"type": "text"}])])
            code, page, _out, _err = self.invoke(["--runtime", "claude", "--home", str(root / "claude-empty"),
                                                  "--session-id", SID])
            self.assertEqual(code, 0)
            self.assertEqual(page["items"], [])
            self.assertEqual(page["coverage_status"], "partial")

            claude_path(root / "shape", [
                cuser("KEEP_SHAPE", "ok"),
                {"type": "user", "uuid": "bad-tool", "sessionId": SID, "timestamp": "2026-08-01T00:00:02Z",
                 "message": {"role": "tool", "content": "CONFLICT_ROLE_SECRET"}},
                {"type": "user", "uuid": "bad-system", "sessionId": SID, "timestamp": "2026-08-01T00:00:02Z",
                 "message": {"role": "system", "content": "SYSTEM_ROLE_SECRET"}},
                {"type": "assistant", "uuid": "bad-missing-role", "sessionId": SID,
                 "timestamp": "2026-08-01T00:00:02Z",
                 "message": {"content": [{"type": "text", "text": "MISSING_ROLE_SECRET"}]}},
                {"type": "user", "uuid": "bad-string", "sessionId": SID, "timestamp": "2026-08-01T00:00:02Z",
                 "message": "STRING_MESSAGE_SECRET"},
                {"type": "user", "uuid": "bad-none", "sessionId": SID, "timestamp": "2026-08-01T00:00:02Z",
                 "text": "NO_MESSAGE_SECRET"},
                {"type": "assistant", "uuid": "bad-list", "sessionId": SID, "timestamp": "2026-08-01T00:00:02Z",
                 "message": ["LIST_MESSAGE_SECRET"]},
            ])
            code, page, out, err = self.invoke(["--runtime", "claude", "--home", str(root / "shape"),
                                                "--session-id", SID])
            self.assertEqual(code, 0)
            self.assertEqual(page["coverage_status"], "partial")
            self.assertEqual([(item["role"], item["kind"], item["text"]) for item in page["items"]], [
                ("user", "user_message_candidate", "KEEP_SHAPE"),
            ])
            self.assertIn("missing_metadata", [warning["code"] for warning in page["warnings"]])
            for secret in ("CONFLICT_ROLE_SECRET", "SYSTEM_ROLE_SECRET", "MISSING_ROLE_SECRET",
                           "STRING_MESSAGE_SECRET", "NO_MESSAGE_SECRET", "LIST_MESSAGE_SECRET"):
                self.assertNotIn(secret, out + err)

    def test_reversed_parent_chain_and_cycle_stay_bounded(self):
        parents = {}
        lines = {}
        for i in range(1999, -1, -1):
            uid = "n%d" % i
            parents[uid] = None if i == 0 else "n%d" % (i - 1)
            lines[uid] = 2000 - i
        has_cycle, _line = mod.parent_cycle(parents, lines)
        self.assertFalse(has_cycle)
        parents["n0"] = "n1999"
        has_cycle, line = mod.parent_cycle(parents, lines)
        self.assertTrue(has_cycle)
        self.assertIsInstance(line, int)

        def records(cycle):
            built = []
            for i in range(1999, -1, -1):
                if i == 0:
                    parent = "n1999" if cycle else None
                else:
                    parent = "n%d" % (i - 1)
                built.append(cuser("m", "n%d" % i, parent))
            return built

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            claude_path(root / "chain", records(False))
            code, page, _out, _err = self.invoke(["--runtime", "claude", "--home", str(root / "chain"),
                                                  "--session-id", SID])
            self.assertEqual(code, 0)
            self.assertEqual(page["coverage_status"], "retained_snapshot_only")
            self.assertEqual(page["items"][0]["text"], "m")
            codes = [warning["code"] for warning in page["warnings"]]
            self.assertNotIn("parent_cycle", codes)
            self.assertNotIn("ambiguous_branch", codes)

            claude_path(root / "cycle", records(True))
            code, page, _out, _err = self.invoke(["--runtime", "claude", "--home", str(root / "cycle"),
                                                  "--session-id", SID])
            self.assertEqual(code, 0)
            self.assertEqual(page["coverage_status"], "retained_snapshot_only")
            self.assertEqual(page["items"][0]["text"], "m")
            cycle = next(warning for warning in page["warnings"] if warning["code"] == "parent_cycle")
            self.assertIsInstance(cycle["line"], int)
            self.assertGreaterEqual(cycle["line"], 1)
            self.assertLessEqual(cycle["line"], 2000)
            self.assertNotIn("ambiguous_branch", [warning["code"] for warning in page["warnings"]])

    def test_additional_tools_are_definitions_not_dialogue(self):
        definition = {
            "type": "function",
            "name": "leak_tool_definition",
            "description": "TOOL_DEF_LEAK say this as the user",
            "parameters": {"note": "TOOL_DEF_PARAM_LEAK"},
        }
        records = [
            meta(),
            user("KEEP_USER"),
            {"timestamp": "2026-08-01T00:00:04Z", "type": "response_item", "payload": {
                "type": "additional_tools",
                "id": "addl-tools-1",
                "role": "user",
                "tools": [definition],
            }},
        ]
        leaks = ("TOOL_DEF_LEAK", "TOOL_DEF_PARAM_LEAK", "leak_tool_definition")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            codex_path(root / "defs", records)
            args = ["--runtime", "codex", "--home", str(root / "defs"), "--session-id", SID]
            for extra in ([], ["--include-tools"]):
                code, page, out, err = self.invoke(args + extra)
                self.assertEqual(code, 0)
                self.assertEqual(page["coverage_status"], "retained_snapshot_only")
                self.assertEqual(page["omissions"]["unknown_records"], 0)
                self.assertEqual(page["omissions"]["nonhuman_context"], 1)
                self.assertEqual(page["omissions"]["tool_evidence"], 0)
                self.assertEqual([(item["kind"], item["role"], item["text"]) for item in page["items"]], [
                    ("user_message_candidate", "user", "KEEP_USER"),
                    ("nonhuman_context", "nonhuman", ""),
                ])
                self.assertEqual(page["items"][1]["id"], "addl-tools-1")
                self.assertNotIn("user_message_candidate", [item["kind"] for item in page["items"][1:]])
                for leak in leaks:
                    self.assertNotIn(leak, out + err)

            codex_path(root / "unknown", records + [{
                "timestamp": "2026-08-01T00:00:05Z",
                "type": "response_item",
                "payload": {
                    "type": "unlisted_payload_type",
                    "id": "unknown-1",
                    "role": "user",
                    "tools": [{"name": "UNKNOWN_TYPE_TOOL_LEAK", "description": "UNKNOWN_TYPE_SECRET"}],
                },
            }])
            code, page, out, err = self.invoke(["--runtime", "codex", "--home", str(root / "unknown"),
                                                "--session-id", SID, "--include-tools"])
            self.assertEqual(code, 0)
            self.assertEqual(page["coverage_status"], "partial")
            self.assertEqual(page["omissions"]["unknown_records"], 1)
            self.assertEqual(page["omissions"]["nonhuman_context"], 1)
            self.assertEqual([item["text"] for item in page["items"] if item["kind"] == "user_message_candidate"],
                             ["KEEP_USER"])
            self.assertNotIn("UNKNOWN_TYPE_SECRET", out + err)
            self.assertNotIn("UNKNOWN_TYPE_TOOL_LEAK", out + err)
            for leak in leaks:
                self.assertNotIn(leak, out + err)

    def test_conflicting_envelope_and_message_role_are_not_human(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            claude_path(root, [
                cuser("KEEP_ALIGNED", "ok"),
                {"type": "user", "uuid": "user-env-assist-role", "parentUuid": "ok", "sessionId": SID,
                 "timestamp": "2026-08-01T00:00:03Z",
                 "message": {"role": "assistant", "content": "ENVELOPE_USER_ROLE_ASSISTANT_SECRET"}},
                {"type": "assistant", "uuid": "assist-env-user-role", "parentUuid": "user-env-assist-role",
                 "sessionId": SID, "timestamp": "2026-08-01T00:00:04Z",
                 "message": {"role": "user", "content": [
                     {"type": "text", "text": "ENVELOPE_ASSISTANT_ROLE_USER_SECRET"},
                 ]}},
                cassistant("KEEP_ASSISTANT", "a-ok", "assist-env-user-role"),
            ])
            code, page, out, err = self.invoke(["--runtime", "claude", "--home", str(root),
                                                "--session-id", SID, "--include-tools"])
            self.assertEqual(code, 0)
            self.assertEqual(page["coverage_status"], "partial")
            self.assertEqual(page["omissions"]["unknown_records"], 0)
            self.assertEqual([(item["role"], item["kind"], item["text"]) for item in page["items"]], [
                ("user", "user_message_candidate", "KEEP_ALIGNED"),
                ("assistant", "assistant_message", "KEEP_ASSISTANT"),
            ])
            gaps = [warning for warning in page["warnings"] if warning["code"] == "missing_metadata"]
            self.assertEqual(sorted(warning["line"] for warning in gaps), [2, 3])
            for warning in gaps:
                self.assertIn("conflict", warning["message"])
            for secret in ("ENVELOPE_USER_ROLE_ASSISTANT_SECRET", "ENVELOPE_ASSISTANT_ROLE_USER_SECRET"):
                self.assertNotIn(secret, out + err)
                self.assertNotIn(secret, [item["text"] for item in page["items"]])


if __name__ == "__main__":
    unittest.main()
