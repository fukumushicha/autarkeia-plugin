---
name: health-check
description: "Check that the vault is still a working system: files exist, work is not rotting, nothing secret slipped in. Use when the user says health check, system health, audit memory, or check the vault."
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Health check

Is this still a system, or a pile of files?

**Mode: act** for the report. **Ask** before fixing anything that is not a missing empty folder.

Confirm the vault. Run `date "+%Y-%m-%d"`.

Check, in order:

1. **Shape.** These exist: `CLAUDE.md`, `memory/facts.md`, `memory/decisions.md`, `memory/tasks.md`, `memory/daily/`, `inbox/`, `docs/`. Missing empty folders may be created. Missing contract (`CLAUDE.md`) is a finding, not auto-created.
2. **Freshness.** Is there a daily log in the last 7 days? If the user has been using the vault and the newest log is older, say so.
3. **Tasks.** Open tasks with no date. Tasks older than 30 days still unchecked. Checked-off items still in `tasks.md`.
4. **Inbox.** Files sitting in `inbox/` more than 7 days.
5. **Secrets.** Search the vault (not `docs/` binaries) for lines that look like passwords, API keys, or tokens. Report paths, not the secrets.
6. **Hand edits to generated files.** If `NEXT-ACTIONS.md` exists and looks hand-written (no `Generated:` line), flag it.

Do not scan their whole disk. Stay in this folder.

Write a short report to `reviews/YYYY-MM-DD-health-check.md` and say the same in chat: what is fine, what is not, what you would fix if they say yes.

Dry run: they said "dry" — report only, no folder creates.
