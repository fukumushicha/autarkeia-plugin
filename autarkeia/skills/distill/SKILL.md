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

Read `CLAUDE.md` in this folder. Routing lives there and in the plugin file `references/layers.md`.

Run `date "+%Y-%m-%d"` and `date "+%H:%M"`. Do not guess the date.

## Capture

Scan this conversation for facts, decisions, constraints, tasks, and observations worth keeping. Skip small talk and recap.

If nothing is worth saving, say so and stop.

## Write

Everything goes to `memory/daily/YYYY-MM-DD.md` first (create if needed; add at the end) under `### Session (HH:MM)`.

Then also:

| Kind | File |
|---|---|
| Fact or constraint | `memory/facts.md` (newest at top) |
| Decision | `memory/decisions.md` (newest at top) |
| Task | `memory/tasks.md` as `- [ ] **title** -- one line. *(added: YYYY-MM-DD)*` |
| Observation | daily log only |

If `projects/<name>/memory/` exists and the item is clearly that project, write there instead of the vault facts/decisions/tasks, and leave a one-line pointer in the daily log.

Before each append, re-read the live insertion point. If the same claim is already there, skip it. Never replace a whole memory file.

If the new text **corrects** something already written, do not stack a second version underneath. Mark the old line `updated YYYY-MM-DD:` with the new sentence, so the file says which one is current. Strike the old wording only if they told you it was wrong.

After writes, re-read the daily tail and confirm the new `### Session` heading. Tell the user in one sentence what you saved. No file paths unless they ask.
