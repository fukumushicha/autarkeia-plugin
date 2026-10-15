---
name: distill
description: "Extract and route session memory into the vault so the next session is not amnesia. Use when the user says distill, save, extract memory, end session, or wrap up."
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Distill

Write what changed. The chat is not the memory.

**Mode: act** for ordinary facts, decisions, and tasks from this session.

**Ask** before writing anything about another person, anything they flagged as off the record, and anything that would leave this vault. Their own life is the ordinary case — write it. Do not ask permission every time; it teaches them to stop reading what you ask.

**If this is about a body — health, a result, a medication — these hold:**

- You are a research analyst, not a doctor. Everything is an observation to take to a medical professional, never something to act on because you said it.
- Before saying anything about a supplement, compound or medication, check it against what they already take, at the source. Never invent a severity grade the source did not give.
- Anything urgent goes at the top of the reply, and into the log, and comes back at the start of each session until they say it is handled.
- Never reinterpret a doctor's note. Put it next to the data, name any difference plainly, and leave it.
- Never edit a document that arrived. The original stays as it came.

Longer version, if the plugin's `references/health.md` is reachable: read it.


## Before writing

Confirm `memory/facts.md` exists. If not, stop: open the vault folder in Claude Code.

**The contract** is `AGENTS.md`. Only if there is no `AGENTS.md` and `CLAUDE.md` holds more than the line `@AGENTS.md` (a vault made before v0.4.2), the contract is that `CLAUDE.md`; do not move or rename it.

Read the contract. Routing lives there and in the plugin file `references/layers.md`.

Run `date "+%Y-%m-%d"` and `date "+%H:%M"`. Do not guess the date.

## Capture

Scan this conversation for facts, decisions, constraints, tasks, and observations worth keeping. Skip small talk and recap.

If nothing is worth saving, say so and stop.

## Write

First decide where each item belongs. An item that belongs to a project whose `AGENTS.md` keeps its content inside goes only into the project's files; the daily log gets a pointer at most ("house-renovation: two items saved in the project"), or nothing if the rules forbid even that.

Everything else goes to `memory/daily/YYYY-MM-DD.md` first (create if needed; add at the end) under `### Session (HH:MM)`.

Then also:

| Kind | File |
|---|---|
| Fact or constraint | `memory/facts.md` (newest at top) |
| Decision | `memory/decisions.md` (newest at top) |
| Task | `memory/tasks.md` as `- [ ] **title** -- one line. *(added: YYYY-MM-DD)*` |
| Observation | daily log only |

If `projects/<name>/memory/` exists and the item is clearly that project, read `projects/<name>/AGENTS.md` first if it exists and follow it, then write there instead of the vault facts/decisions/tasks, and leave a one-line pointer in the daily log (the content itself too, if the project's rules allow it).

A new rule for a project (who may see it, what never leaves it, how to talk about it, what to watch) goes into that project's `AGENTS.md`, not into its facts. It is a change to the project's rules: show it, write after yes. If the project has no `AGENTS.md` yet, create it with a `CLAUDE.md` next to it that holds only `@AGENTS.md`.

Before each append, re-read the live insertion point. If the same claim is already there, skip it. Never replace a whole memory file.

If the new text **changes** something already written: same topic and newer, mark the old line `superseded YYYY-MM-DD:` with the new sentence, so the file says which one is current; a different aspect of the same topic is not a change, both stay; a contradiction you cannot settle from a source is written as neither, noted in the daily log, and asked. Never delete the old line. Full rules, and what wins between a project's entry and the vault's: `references/layers.md`.

A task line holds current state only: what it is, the next step, a pointer to the history if there is one. A status change replaces the old status. Done items move to `memory/tasks-archive.md` now.

An action they agreed to or asked for that could not be finished is not left as a note: it becomes a task with a next step and, when known, a date, or the daily log says it was dropped. Something merely noticed stays an observation; do not invent an owner or a deadline for it.

After writes, re-read the daily tail and confirm the new `### Session` heading. Tell the user in one sentence what you saved. No file paths unless they ask.
