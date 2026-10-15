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

Decide first: **whose is it?** If it belongs to a project in `projects/`, read that project's `AGENTS.md` if it has one; a project whose rules keep its content inside gets the copy, the register row and the log line inside `projects/<name>/` (its own `archive/` or `docs/`), and the vault's daily log a pointer at most. Then: **original or working?** An original was made by someone else and arrived as is (a statement, a contract, a scan, an export, a medical report); it goes to `archive/`. A working document was written by the user or an AI; it goes to `docs/`. When unsure, original. Layout and rules: the plugin file `references/archive.md`.

Propose a table: what it is, original or working, where it would go (the archive area and folder, or `docs/`), what facts/decisions/tasks to take out. Wait for yes.

After yes:

1. Compute the hash (first 12 characters of SHA-256) and check every `archive/*/register.md` and `docs/register.md` (and the project's, if it is a project's). A register from an earlier version has other columns: keep them, append the missing ones (`Hash`, `Concerns`, `Extracted`) at the end of the header, fill the hashes for existing rows from the files, and write every row in the order of that register's actual header. A duplicate is not copied again: point at the existing row, then continue with any extraction they approved and update that row.
2. An original: copy into `archive/<area>/<person or thing>/<kind>/`, with the area named exactly as in `references/archive.md`, creating only those folders. A working document: copy into `docs/`. Keep the file's name unless it is empty or meaningless. Never overwrite: if that name exists there with a different hash, add the period or date to the new name and keep both. Verify the copy's hash matches the source. Do not delete the source unless they ask. Do not rename into a clever scheme.
3. Add a row to that area's `archive/<area>/register.md` or to `docs/register.md` (create it with the columns date, path, what it is, who it concerns, hash, extracted); in an existing register, follow its actual header order.
4. Write approved memory the same way `/distill` does, then mark the row extracted.
5. Daily log: one line that it was filed, and where.

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
