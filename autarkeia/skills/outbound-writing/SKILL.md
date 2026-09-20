---
name: outbound-writing
description: "Draft a message, post, or reply in the user's own words. Show it. Never send. Use when the user says draft, write a reply, what should I say, or proofread this."
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Outbound writing

Words that would go out in their name. You draft. They send, or they don't.

**Mode: ask.** Show the text. Do not send, post, or create a mail draft on their account.

## How

1. Ask who it is for, and what it must do, only if that is not already clear.
2. Match their language. If they wrote in Russian, draft in Russian. If they wrote in English, English.
3. Check the vault (`memory/facts.md`, `memory/decisions.md`) so the draft does not invent a fact.
4. Show the full text in chat. Short is good. Unexplained is not.
5. If they want a file, write it under `docs/drafts/` and still show it in chat.

## Never

- Send, post, or submit.
- Write as if they already signed off.
- Use someone else's voice (including the person who gave them this plugin).
- Add a pitch, a sign-off they do not use, or a meeting they did not ask for.
