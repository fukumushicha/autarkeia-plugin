---
name: realign
description: "Rebuild the picture of open work from the vault files. Use when the user says realign, sync, sync projects, or what is open."
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Realign

Bring the files back into one picture.

**Mode: act.** Rebuild `NEXT-ACTIONS.md`. Do not invent work.

Confirm the vault. Run `date "+%Y-%m-%d"`.

Read:

- `memory/tasks.md`
- `PRIORITIES.md` if it exists
- today's daily log if it exists
- every `projects/*/memory/tasks.md` if those folders exist, after that project's `AGENTS.md` if it has one
- `inbox/` (count files only)

Write `NEXT-ACTIONS.md` from scratch (this file is generated):

```
# Open work
Generated: YYYY-MM-DD

## Now
- [open tasks that look current; a project's task starts with the project name in brackets, and any due date stays in the line]

## Waiting
- [tasks waiting on someone else, if any]

## Inbox
- [N files waiting] or none
```

A project whose rules keep its content inside it gets one line instead of its tasks: `[name] N open tasks, next due YYYY-MM-DD`, or `[name] has open work` if its rules forbid even the date. A project's due date matters most here: it is how a session that never opens the project still sees the deadline.

Do not put done tasks here. If a task in `memory/tasks.md` is checked off, move it to `memory/tasks-archive.md` (create if needed) and remove it from `tasks.md`. A checked-off project task moves to that project's own `memory/tasks-archive.md`.

Lead the reply with the Now list, in plain language. One sentence on inbox if anything is waiting. Mention `/email` only if `inbox/` has `email-*.md` files.
