---
name: improve
description: "Capture friction in this way of working and keep a propose-only list. Nothing is auto-applied. Use when the user says improve, this is annoying, capture friction, or improvement status."
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Improve

Notice what keeps going wrong. Propose. Do not silently change the system.

**Mode: act** for capture and status. **Ask** before changing any skill or contract.

## Capture

If they named a friction, append to `memory/ops/friction.md` (create if needed):

```
- **YYYY-MM-DD**: [what went wrong, in their words]. Surface: [distill/daily-debrief/email/other].
```

Confirm in one sentence.

## Status

Read `memory/ops/friction.md` and list the open items. If the file is missing, say there is no list yet.

## Harvest

If they said "run improve" or it is part of weekly debrief: read the last 14 daily logs and this file. Group repeats. Write a propose-only list to `memory/ops/improvement-proposals.md`:

```
- **[one line proposal]** -- because [friction]. Do not apply until they say yes.
```

Show the top few. Apply nothing.
