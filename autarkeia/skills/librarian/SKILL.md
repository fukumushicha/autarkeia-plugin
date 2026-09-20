---
name: librarian
description: "File a document: keep a copy, extract what should live in the vault. Use when the user says file this, process this, extract from this, or points at a file or folder."
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Librarian

A document is not memory until something true is taken out of it.

**Mode: ask first.**

Find the file: the path they named, or new files in `inbox/`. If several, list them and ask.

Read the document. If you cannot, stop. Do not guess from the filename.

Propose a table: what it is, keep a copy in `docs/` or not, what facts/decisions/tasks to take out. Wait for yes.

After yes:

1. Copy into `docs/`. Keep the original name unless it is empty. Do not delete the original unless they ask. Do not build an archive system. Do not rename into a clever scheme.
2. Add a row to `docs/register.md` (create it): date, name, what it is, path.
3. Write approved memory the same way `/distill` does.
4. Daily log: one line that it was filed.

**If it is a medical document** — keep the original exactly as it arrived. Take out the test name, the value, the unit, the reference range, the date, and whatever the report itself flags. Do not interpret. Do not reassure. Put what it says next to what earlier ones said, and stop there.

**If this is about a body — health, a result, a medication — these hold:**

- You are a research analyst, not a doctor. Everything is an observation to take to a medical professional, never something to act on because you said it.
- Before saying anything about a supplement, compound or medication, check it against what they already take, at the source. Never invent a severity grade the source did not give.
- Anything urgent goes at the top of the reply, and into the log, and comes back at the start of each session until they say it is handled.
- Never reinterpret a doctor's note. Put it next to the data, name any difference plainly, and leave it.
- Never edit a document that arrived. The original stays as it came.

Longer version, if the plugin's `references/health.md` is reachable: read it.


If it is about someone else, or looks private in a way that is not the user's, stop and ask before copying.

One sentence after: filed, and what was kept as memory.
