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

1. **Shape.** These exist: the contract, `memory/facts.md`, `memory/decisions.md`, `memory/tasks.md`, `memory/daily/`, `inbox/`, `docs/`. Missing empty folders may be created. Contract, one of three cases: (a) `AGENTS.md` exists: it is the contract; `CLAUDE.md` should hold only the line `@AGENTS.md`, and anything more there is a finding (rules added there are invisible to Codex and Grok). (b) No `AGENTS.md`, and `CLAUDE.md` holds the whole contract: a vault made before v0.4.2, not broken; say it uses the older layout and offer the move (rename `CLAUDE.md` to `AGENTS.md`, new `CLAUDE.md` with `@AGENTS.md`); do it only after yes. (c) Neither: missing contract is a finding, not auto-created. Then, with a contract found, compare two passages with the plugin's `vault-template/AGENTS.md` (after a GitHub install it is at `~/.claude/plugins/marketplaces/autarkeia-plugin/vault-template/AGENTS.md`; otherwise look three folders above this skill's own folder, `<this skill's folder>/../../../vault-template/AGENTS.md`; if neither exists, say you could not compare the **Keep it safe** section and leave it as it is), each on its own: (i) the **Keep it safe** section, if it still offers `git init` as protection against a dead disk ("run `git init` here once and commit at the end of each week"); (ii) the example in quotation marks in the **Private projects** paragraph, only if it is the one older versions shipped: from the vault folder run exactly this, which reads the file itself and puts none of its text into the command: `python3 -c 'import re,hashlib;s=open("AGENTS.md").read();i=s.find("**Private projects.**");m=re.search(r"for example \"([^\"]*)\"",s[i:]) if i>=0 else None;print(hashlib.sha256(m.group(1).encode()).hexdigest()[:12] if m else "none")'`; the old one prints `d3a279ab69f2`. In a vault whose contract is still `CLAUDE.md` (case b), use `CLAUDE.md` in place of `AGENTS.md` in that command. Any other example is theirs: leave it. The current one is "house-renovation: two items saved in the project". Either one means a vault made before v0.4.5. Show the exact old and new text for each passage found, and replace only that text after yes; anything they added to those sections themselves stays.
2. **Projects.** For each folder in `projects/`: `memory/` holds `facts.md`, `decisions.md`, `tasks.md` (missing ones are a finding). If it has `AGENTS.md`, its `CLAUDE.md` holds only `@AGENTS.md`; a missing `CLAUDE.md` or anything more in it is a finding. A project without `AGENTS.md` is not a finding. If it has grown past a handful of entries, say in one line that it could have its own rules, and ask nothing more.
3. **Freshness.** Is there a daily log in the last 7 days? If the user has been using the vault and the newest log is older, say so.
4. **Tasks.** Open tasks with no date. Tasks older than 30 days still unchecked. Checked-off items still in `tasks.md`.
5. **Inbox.** Files sitting in `inbox/` more than 7 days.
6. **Secrets.** Search the vault (not `docs/` binaries) for lines that look like passwords, API keys, or tokens. Report paths, not the secrets.
7. **Hand edits to generated files.** If `NEXT-ACTIONS.md` exists and looks hand-written (no `Generated:` line), flag it.
8. **Archive.** For each `archive/*/register.md`: every listed file exists and its hash still matches (a mismatch means the file no longer matches its registered hash; the cause is unverified, so say exactly that, keep both, fix nothing). Files in an archive area with no register row. Originals sitting in `docs/` (statements, contracts, scans, exports from outside) that belong in `archive/`; offer the move, do it only after yes: copy, verify the hash, add the archive register row, change the `docs/register.md` row to point at the new path, repair any memory line that cites the old path, then remove the source.

Do not scan their whole disk. Stay in this folder.

Write a short report to `reviews/YYYY-MM-DD-health-check.md` and say the same in chat: what is fine, what is not, what you would fix if they say yes.

Dry run: they said "dry" — report only, no folder creates.
