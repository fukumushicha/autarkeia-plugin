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
- every `projects/*/memory/tasks.md` if those folders exist
- `inbox/` (count files only)

Write `NEXT-ACTIONS.md` from scratch (this file is generated):

```
# Open work
Generated: YYYY-MM-DD

## Now
- [open tasks that look current]

## Waiting
- [tasks waiting on someone else, if any]

## Inbox
- [N files waiting] or none
```

Do not put done tasks here. If a task in `tasks.md` is checked off, move it to `memory/tasks-archive.md` (create if needed) and remove it from `tasks.md`.

Lead the reply with the Now list, in plain language. One sentence on inbox if anything is waiting. Mention `/email` only if `inbox/` has `email-*.md` files.
