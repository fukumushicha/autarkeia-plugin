---
name: brainstorm
description: "Get a structured second opinion on a decision, a document, or something an agent just did. Use when the user says brainstorm, second opinion, audit this, or review this."
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent
---

# Brainstorm

A second mind on one thing. Not a committee. Not a product meeting.

**Mode: act** when they named the thing. **Ask once** if you cannot tell what to review.

## What to review

The file, decision, or output they pointed at. Read it. If it is code or a claim about the world, open the live file or source before you argue.

## How

1. Write your own take first, privately: what is true, what is weak, what would change the decision.
2. Spawn **one** independent subagent with the artifact only — not your take. Ask it to disagree where it can.
3. Synthesize. Where you and the subagent clash, show both. Do not average them. Do not invent a third position nobody held.
4. Save the packet in `reviews/YYYY-MM-DD-<short-name>.md`.

If they asked for another product (ChatGPT, Codex, Grok), do not fake that run. Give them a short prompt they can paste there, and wait for what comes back.

## What not to do

- Do not send mail or publish.
- Do not treat agreement between you and your subagent as proof.
- Do not expand into a new project.

Close with: the recommendation, what it would cost them in time or risk, and one question if a decision is still theirs.
