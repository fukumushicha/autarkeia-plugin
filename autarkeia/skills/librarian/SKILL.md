---
name: librarian
description: "File a document or a recording: keep a copy, extract what should live in the vault. Use when the user says file this, process this, extract from this, transcribe this, or points at a file, a folder, or an audio recording such as a voice memo."
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Librarian

A document is not memory until something true is taken out of it.

**Mode: ask first.**

Find the file: the path they named, or new files in `inbox/`. If several, list them and ask.

A recording (audio: a voice memo, a call, an appointment) cannot be read directly: follow **If it is a recording** further down instead of the read-and-propose steps here; its filing uses the same numbered steps below.

Read the document. If you cannot, stop. Do not guess from the filename.

Decide first: **whose is it?** If it belongs to a project in `projects/`, read that project's `AGENTS.md` if it has one; a project whose rules keep its content inside gets the copy, the register row and the log line inside `projects/<name>/` (its own `archive/` or `docs/`), and the vault's daily log a pointer at most. Then: **original or working?** An original was made by someone else and arrived as is (a statement, a contract, a scan, an export, a medical report); it goes to `archive/`. A working document was written by the user or an AI; it goes to `docs/`. When unsure, original. Layout and rules: the plugin file `references/archive.md`.

Propose a table: what it is, original or working, where it would go (the archive area and folder, or `docs/`), what facts/decisions/tasks to take out. Wait for yes.

After yes:

1. Compute the hash (first 12 characters of SHA-256) and check every `archive/*/register.md` and `docs/register.md` (and the project's, if it is a project's). A register from an earlier version has other columns: keep them, append the missing ones (`Hash`, `Concerns`, `Extracted`) at the end of the header, fill the hashes for existing rows from the files, and write every row in the order of that register's actual header. A duplicate is not copied again: point at the existing row, then continue with any extraction they approved and update that row.
2. An original: copy into `archive/<area>/<person or thing>/<kind>/`, with the area named exactly as in `references/archive.md`, creating only those folders. A working document: copy into `docs/`. Keep the file's name unless it is empty or meaningless. Never overwrite: if that name exists there with a different hash, add the period or date to the new name and keep both. Verify the copy's hash matches the source. Do not delete the source unless they ask. Do not rename into a clever scheme.
3. Add a row to that area's `archive/<area>/register.md` or to `docs/register.md` (create it with the columns date, path, what it is, who it concerns, hash, extracted); in an existing register, follow its actual header order.
4. Write approved memory the same way **distill** does, then mark the row extracted.
5. Daily log: one line that it was filed, and where.

**If it is a medical document** — keep the original exactly as it arrived. Take out the test name, the value, the unit, the reference range, the date, and whatever the report itself flags. Do not interpret. Do not reassure. Put what it says next to what earlier ones said, and stop there.

**If this is about a body — health, a result, a medication — these hold:**

- You are a research analyst, not a doctor. Everything is an observation to take to a medical professional, never something to act on because you said it.
- Before saying anything about a supplement, compound or medication, check it against what they already take, at the source. Never invent a severity grade the source did not give.
- Anything urgent goes at the top of the reply, and into the log, and comes back at the start of each session until they say it is handled.
- Never reinterpret a doctor's note. Put it next to the data, name any difference plainly, and leave it.
- Never edit a document that arrived. The original stays as it came.

Longer version, if the plugin's `references/health.md` is reachable: read it.


**If it is a recording** (a voice memo, a call, an appointment):

1. Decide whose it is, as above (a project whose rules keep its content inside gets everything inside `projects/<name>/`).
2. First proposal, before any transcript exists: where the audio goes (an original: the area by what it is about, a doctor's visit under Health and the person), and how it will be transcribed. Check for a local transcription tool (`command -v whisper`, `command -v whisper-cli`, `command -v mlx_whisper`). If one is there, propose using it on this computer; a long recording takes a while and closing the laptop stops it; do not guess how long. If none is there and no transcript exists, say so: file the audio if they want, and stop there. Do not install anything, and never send the audio to an online transcription service without their yes. Wait for yes.
3. After yes: file the audio like any original (hash, register row, copy check). Then the transcript:
   - **A transcript that arrived with it** (from a clinic, an app, another person) is a received original: file it unchanged in the archive like any original, with the register row naming the recording it belongs to. Do not add a header to it.
   - **A transcript made here** is a working document: `docs/` (or the project's `docs/`), named after the recording, with a first line pointing at the audio's archive path and the tool that made it; its register row names the same.
4. Read the transcript. Second proposal: the specific facts, decisions and tasks to take out, as for any document. Wait for yes.
5. Extraction after yes: keep who said what (doctor, patient, someone else) and keep what was unclear marked as unclear. A name, dose, value or date taken from a recording points at the transcript and the place in it; never promote a misheard word into a fact. A doctor's recording is a doctor's note: the body rules above hold.

Say once: the transcript is read by the AI you work with, so it is sent to that company like any file it reads. Transcribing locally keeps the audio on this computer; it does not keep the transcript there.

If it is about someone else, or looks private in a way that is not the user's, stop and ask before copying.

One sentence after: filed, and what was kept as memory.
