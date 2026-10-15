---
name: daily-debrief
description: "End-of-day review: a few questions, then write what the user approved into the vault. Use when the user says daily debrief, close the day, evening check-in, or how did today go."
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Daily debrief

A short close. The user speaks. You write only what they approve.

**Mode: ask first.**

Confirm `memory/facts.md` exists. Run `date "+%Y-%m-%d"`. That is today unless they name another date.

Read today's daily log if it exists, and `memory/tasks.md`. Nothing else.

Ask **one question at a time**, in their language. Three is enough. Four is the maximum.

1. What happened today that you do not want to reconstruct tomorrow?
2. Did you decide something, or put a decision off?
3. What is still open that a future you should see?
4. Anything about this way of working that annoyed you today?

If question 4 gets a real answer, append it to `memory/ops/friction.md` the way **improve** does. Capture it. Propose nothing, change nothing.

If the log already answers one, skip it.

Then show a list: facts, decisions, tasks to add or mark done, items that stay only in today's log. Wait for yes or edits.

Write with the same files and format as **distill**. Put answers under `### Close of day` in that date's daily log.

One sentence to close: what was kept, and whether anything waits for tomorrow.
