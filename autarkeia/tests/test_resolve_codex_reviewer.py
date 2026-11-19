"""Exercise the resolver's CLI and Codex JSONL handshake without contacting OpenAI."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


RESOLVER = Path(__file__).resolve().parents[1] / "bin" / "resolve-codex-reviewer.py"


def model(name, *, hidden=False):
    return {"id": name, "model": name, "hidden": hidden}


def page(names, cursor=None):
    return {"data": names, "nextCursor": cursor}


class ResolveCodexReviewerTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="autarkeia reviewer ")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.workspace = self.root / "Review Project"
        self.workspace.mkdir()
        codex = self.root / "codex"
        codex.write_text(
            "#!" + sys.executable + "\n" + """
import json
import os
import sys

assert sys.argv[1:] == ["app-server", "--stdio"]
assert os.getcwd() == os.environ["TEST_REVIEW_WORKSPACE"]

def read():
    return json.loads(sys.stdin.readline())

def write(message):
    print(json.dumps(message), flush=True)

init = read()
assert init["method"] == "initialize"
write({"id": init["id"], "result": {}})
assert read() == {"method": "initialized"}
cursor = None
for response in json.loads(os.environ["TEST_MODEL_PAGES"]):
    request = read()
    assert request["method"] == "model/list"
    assert request["params"].get("cursor") == cursor
    assert request["params"]["includeHidden"] is False
    if "error" in response:
        write({"id": request["id"], **response})
        break
    write({"method": "account/updated", "params": {}})
    write({"id": request["id"], "result": response})
    cursor = response.get("nextCursor")
"""
        )
        codex.chmod(0o700)

    def resolve(self, family, pages):
        return subprocess.run(
            [sys.executable, str(RESOLVER), family],
            cwd=self.workspace,
            env={
                **os.environ,
                "PATH": f"{self.root}{os.pathsep}{os.environ['PATH']}",
                "TEST_REVIEW_WORKSPACE": str(self.workspace),
                "TEST_MODEL_PAGES": json.dumps(pages),
            },
            capture_output=True,
            text=True,
            timeout=5,
        )

    def test_selects_latest_exact_visible_family_across_pages(self):
        result = self.resolve("astra", [
            page([model("gpt-12.9-astra"), model("gpt-13.2-sol")], "long/opaque:cursor"),
            page([model("gpt-12.10-astra"), model("gpt-13.0-astra", hidden=True),
                  model("gpt-14.1-astra-preview"), model("spoof-gpt-15.1-astra")]),
        ])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "gpt-12.10-astra\n")

    def test_sol_can_have_a_newer_major_or_patch_version(self):
        result = self.resolve("sol", [
            page([model("gpt-9.99-sol"), model("gpt-10.1-sol"),
                  model("gpt-10.1.2-sol"), model("gpt-99.0-astra")]),
        ])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "gpt-10.1.2-sol\n")

    def test_picker_catalog_can_omit_hidden_field(self):
        result = self.resolve("astra", [
            page([{"model": "gpt-10.1-astra"}]),
        ])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "gpt-10.1-astra\n")

    def test_no_match_in_account_never_falls_back(self):
        result = self.resolve("astra", [
            page([model("gpt-12.1-sol"), model("gpt-12.1-astra", hidden=True)]),
        ])
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertIn("no visible Astra model", result.stderr)

    def test_rpc_failure_discards_selection_from_earlier_page(self):
        result = self.resolve("astra", [
            page([model("gpt-12.1-astra")], "next"),
            {"error": {"code": -32600, "message": "test error"}},
        ])
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertIn("model/list", result.stderr)
        self.assertIn("-32600", result.stderr)

    def test_repeated_cursor_fails_without_returning_partial_selection(self):
        result = self.resolve("astra", [
            page([model("gpt-12.1-astra")], "loop"),
            page([], "loop"),
        ])
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertIn("repeated cursor", result.stderr)

    def test_malformed_page_fails_without_returning_partial_selection(self):
        result = self.resolve("astra", [
            page([model("gpt-12.1-astra")], "next"),
            {"data": "not a model list", "nextCursor": None},
        ])
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertIn("invalid model/list page", result.stderr)


if __name__ == "__main__":
    unittest.main()
