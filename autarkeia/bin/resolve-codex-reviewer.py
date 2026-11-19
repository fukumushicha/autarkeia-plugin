#!/usr/bin/env python3
"""Print the latest visible Codex model in the requested reviewer family."""

import argparse
import json
import os
from queue import Empty, Queue
import re
import shutil
import subprocess
import sys
from threading import Thread


TIME_LIMIT_SECONDS = 30
MAX_PAGES = 64
MAX_MESSAGE_BYTES = 1024 * 1024


class CatalogError(Exception):
    """The server did not provide a complete, usable catalog."""


class CatalogClient:
    def __init__(self, server):
        self.input = server.stdin.fileno()
        self.output = server.stdout.fileno()
        self.buffer = bytearray()
        self.request_id = 0

    def send(self, message):
        pending = memoryview((json.dumps(message) + "\n").encode())
        while pending:
            pending = pending[os.write(self.input, pending):]

    def read_message(self):
        while True:
            newline = self.buffer.find(b"\n")
            if newline >= 0:
                line = self.buffer[:newline]
                del self.buffer[:newline + 1]
                message = json.loads(line)
                if not isinstance(message, dict):
                    raise CatalogError("invalid Codex app server message")
                return message

            space = MAX_MESSAGE_BYTES - len(self.buffer)
            if not space:
                raise CatalogError("Codex app server message is too large")
            chunk = os.read(self.output, min(space, 65536))
            if not chunk:
                raise CatalogError("Codex app server closed before answering")
            self.buffer.extend(chunk)

    def request(self, method, params):
        self.request_id += 1
        self.send({"id": self.request_id, "method": method, "params": params})
        while True:
            reply = self.read_message()
            if reply.get("id") != self.request_id or "method" in reply:
                continue
            if "error" in reply:
                error = reply["error"]
                code = error.get("code") if isinstance(error, dict) else None
                detail = f" (code {code})" if type(code) is int else ""
                raise CatalogError(f"Codex rejected {method}{detail}")
            if not isinstance(reply.get("result"), dict):
                raise CatalogError(f"invalid Codex response to {method}")
            return reply["result"]


def resolve_model(client, family):
    client.request("initialize", {
        "clientInfo": {"name": "autarkeia_brainstorm", "version": "1"},
    })
    client.send({"method": "initialized"})

    pattern = re.compile(rf"gpt-([0-9]+(?:\.[0-9]+)*)-{family}")
    candidates = []
    cursors = set()
    params = {"includeHidden": False, "limit": 50}
    for _ in range(MAX_PAGES):
        page = client.request("model/list", params)
        models = page.get("data")
        cursor = page.get("nextCursor")
        if (not isinstance(models, list) or "nextCursor" not in page
                or (cursor is not None and not isinstance(cursor, str))):
            raise CatalogError("invalid model/list page")
        for entry in models:
            if (not isinstance(entry, dict) or not isinstance(entry.get("model"), str)
                    or not isinstance(entry.get("hidden", False), bool)):
                raise CatalogError("invalid model/list entry")
            model = entry["model"]
            match = pattern.fullmatch(model)
            if match and not entry.get("hidden", False):
                version = tuple(map(int, match[1].split(".")))
                candidates.append((version, model))
        if cursor is None:
            if not candidates:
                raise CatalogError(f"no visible {family.title()} model in the Codex catalog")
            return max(candidates)[1]
        if cursor in cursors:
            raise CatalogError("Codex model/list returned a repeated cursor")
        cursors.add(cursor)
        params["cursor"] = cursor
    raise CatalogError("Codex model/list exceeded the page limit")


def query_catalog(family):
    executable = shutil.which("codex")
    if executable is None:
        raise CatalogError("Could not find the Codex CLI on PATH.")
    outcome = Queue()

    with subprocess.Popen(
        [executable, "app-server", "--stdio"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        bufsize=0,
    ) as server:
        # Blocking pipe I/O also works on Windows. The caller reaps the server
        # on timeout, even if the server never returns a complete line.
        def lookup():
            try:
                outcome.put(resolve_model(CatalogClient(server), family))
            except (CatalogError, OSError, ValueError, RecursionError) as error:
                outcome.put(error)

        worker = Thread(target=lookup, daemon=True)
        worker.start()
        try:
            result = outcome.get(timeout=TIME_LIMIT_SECONDS)
        except Empty:
            raise CatalogError("Codex app server timed out") from None
        finally:
            server.kill()

    if isinstance(result, Exception):
        raise result
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("family", choices=("astra", "sol"))
    args = parser.parse_args()

    try:
        model = query_catalog(args.family)
    except CatalogError as error:
        print(error, file=sys.stderr)
        return 1
    except (OSError, ValueError, RecursionError):
        print("Could not read the Codex model catalog.", file=sys.stderr)
        return 1

    print(model)
    return 0


if __name__ == "__main__":
    sys.exit(main())
