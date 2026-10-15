---
name: checkpoint
description: "Save working state so the session can continue later. Use when the user says checkpoint, save state, save progress, or before a long burst of work."
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Checkpoint

Mark the trail. This is not **distill**.

**Mode: act.** No approval.

Confirm the vault. Run `date "+%Y-%m-%d"` and `date "+%H:%M"`.

Append to today's daily log:

```
### Checkpoint (HH:MM)

**Context**: [one sentence]
**Decisions**: [bullets or none]
**Files touched**: [names, or none]
**Open**: [bullets or none]
**Next**: [bullets]
```

If the work was in a project whose rules keep its content inside it, write the checkpoint in that project's terms only as a pointer here ("worked on house-renovation"), nothing private. Keep it under 20 lines. Re-read the tail after writing. Say: checkpoint saved.
