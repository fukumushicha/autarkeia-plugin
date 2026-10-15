---
name: email
description: "Process emails dropped in inbox/: extract facts, tasks, and decisions. Never send. Use when the user says process emails, email triage, or check the inbox."
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Email

Panning the inbox. Intake only. Never send.

**Mode: act** on files already in `inbox/`. **Ask** before any reply or outbound anything.

## Input

Only files in `inbox/` named `email-*.md` or that are clearly an email (From/Subject/body). If the folder is empty, say so and stop. Do not open Gmail. Do not hunt the rest of the machine.

## A task is rare

A task is something a named person is waiting for the user to do.

Not a task: newsletters, webinars, "register here", community digests, no-reply broadcasts, FYI. Those go to the daily log as observations.

A task is only:

- someone asked them by name to do a thing
- they promised someone a thing
- a receipt or appointment that requires them to act

If the verb you are about to write is attend, register, watch, join, or consider — it is probably not a task.

## Process each email

1. Read it.
2. Daily log first: who, subject, what matters.
3. Facts and decisions through **distill** routing.
4. Tasks only if they pass the gate above.
5. Move the file to `inbox/processed/` when done.

Attachments: do not pretend you extracted a PDF from a sentence in the email. Point **librarian** at the file.

Report: N processed, N tasks (who is waiting), N that were just FYI.
