---
name: brainstorm
description: "Get a structured second opinion on a decision, a document, or something an agent just did, from an independent sub-agent or, when installed, from Codex or Grok reading the vault themselves. Use when the user says brainstorm, second opinion, audit this, review this, send to codex, ask grok, or all reviewers."
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent
---

# Brainstorm

A second mind on one thing. Not a committee. Not a product meeting.

**Mode: act** when they named the thing. **Ask once** if you cannot tell what to review.

## What to review

The file, decision, or output they pointed at. Read it. If it is a claim about the world, open the source before you argue.

## Who reviews

| Reviewer | When | What it is |
|---|---|---|
| Sub-agent | when your app can start one | A fresh copy of the model you are running on: a Claude sub-agent in Claude Code, a Codex sub-agent in Codex. Same family as you. Independent context, not an independent mind. |
| Codex | they said codex, or all reviewers | OpenAI's agent, run on their own ChatGPT sign-in. Reads the vault itself. |
| Grok | they said grok, or all reviewers | xAI's agent, run on their own xAI sign-in. Reads the vault itself. |

Run `command -v codex` and `command -v grok` to see what is installed.

- **They named an outside reviewer** (codex, grok, all reviewers): that is their yes to send it out. Use what they named, if installed. If it is not installed, say so and give them the setup guide: https://github.com/fukumushicha/autarkeia-plugin/blob/master/docs/second-opinion.md. Do not fake the run.
- **They asked for a second opinion without naming one:** use the sub-agent. At the close, say in one line which outside reviewers are installed (from another company than the model you are running on) and that naming one would get it. Do not send anything outside on your own.
- **The thing is about their health, another person, or anything they said was off the record:** even when they named an outside reviewer, confirm once before writing the packet, because that company will read it.
- Their yes covers what you put in the packet. The read-only flags stop changes, not reading: a reviewer may open other files in the vault. Say this once the first time they send something out.

## How

1. Run `date "+%Y-%m-%d"`. Pick a short name for the review. Choose the review folder once, and use it for everything below (packet, every reviewer's answer, retries, the result): `reviews` normally; `projects/<name>/reviews` when the thing belongs to a project whose rules keep its content inside it. Create it if missing. In the commands below it is written `<folder>`: put the folder's actual path in its place in every command you run, for example `projects/house-renovation/reviews`. Do not use a shell variable for it; each command runs in a fresh shell.
2. Write your own take first, privately: what is true, what is weak, what would change the decision. It does not go to the reviewer.
3. Write the packet to `<folder>/YYYY-MM-DD-<short-name>-packet.md`: the question in their words, the paths of the files to read, and any source you already fetched. Not your take.
4. Run each reviewer. One at a time is fine.
5. Synthesize. Where you and a reviewer clash, show both. Do not average them. Do not invent a third position nobody held. A reviewer who opened the file beats one who reasoned from the packet; check the file yourself before adopting either.
6. Save the result in `<folder>/YYYY-MM-DD-<short-name>.md`, with which reviewers actually answered.

### The prompt every reviewer gets

Put this at the top of the packet:

> You are an independent reviewer. You can read files but not change them. Read the files named below yourself; do not trust this packet's summary of them. Disagree where you can. List findings, most serious first, each with the file and the line or passage it rests on. End with your verdict in one paragraph.

### Sub-agent

Spawn **one** sub-agent with the packet only. Ask it to disagree where it can. If your runtime cannot start a sub-agent, say so and offer an outside reviewer instead; do not review it yourself and call that a second opinion.

When you are Codex, "send to codex" still runs the Codex command below: a separate Codex with a fresh context and the read-only sandbox. Say once that it is your own family, not an outside view. Grok is the outside view.

### Codex

From the vault folder. The prompt goes in through standard input; `-s read-only` is what stops it changing your vault.

```bash
codex exec -C "$PWD" --skip-git-repo-check -s read-only -o "<folder>/YYYY-MM-DD-<short-name>-codex.md" - < "<folder>/YYYY-MM-DD-<short-name>-packet.md"
```

### Grok

From the vault folder. `--sandbox read-only` is what stops it changing your vault. It can still write in its own working folders, listed below. Keep `--permission-mode bypassPermissions`: the stricter modes stop the review on its first file read instead of slowing it down. The sandbox, not the permission mode, does the protecting.

First check where the vault really is: run `pwd -P`, and `realpath` on each file named in the packet. If any of them is under `/tmp`, `/private/tmp`, `/var/tmp`, `/private/var/tmp`, `/var/folders`, `/private/var/folders` or `~/.grok`, stop: Grok's sandbox leaves those writable, so the review would not be read-only there. Say so and suggest moving the vault to an ordinary folder such as Documents.

```bash
grok --prompt-file "<folder>/YYYY-MM-DD-<short-name>-packet.md" --no-memory --disable-web-search --max-turns 40 --permission-mode bypassPermissions --sandbox read-only > "<folder>/YYYY-MM-DD-<short-name>-grok.md"
```

Grok sometimes stops on its first step. If that happens, run it once more into `...-grok-2.md`, keeping the first file.

### Is the answer complete?

Before you use a reviewer's answer, check: it finished normally (for Codex and Grok, the command exited with 0; for the sub-agent, it returned its answer); it says it read every file named in the packet and reports no failed reads; it ends with a verdict. If not, it is incomplete. Retry once into a new file (`-2`). If the second try is also incomplete, say the review did not finish, keep both files, and do not count that reviewer in the synthesis.

### When a reviewer fails

- Not signed in: tell them to run `codex` once (choose Sign in with ChatGPT) or `grok login`, in their own Terminal. Never handle their password.
- Out of usage: say so. That is their plan's limit, not a fault.
- Do not swap in a different reviewer without saying so.

## What not to do

- Do not send mail or publish.
- Do not treat agreement between reviewers as proof. Several models agreeing about one packet is one source.
- Never run a reviewer without its read-only flag.
- Do not expand into a new project.

Close with: the recommendation, what it would cost them in time or risk, and one question if a decision is still theirs.
