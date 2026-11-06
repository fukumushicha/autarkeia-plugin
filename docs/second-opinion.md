# Second opinions from other AI models

The `brainstorm` skill gets you a second opinion on a decision, a document, or something an agent just did. Out of the box it asks a second Claude, which has a fresh context but the same training as the first. That catches slips; it does not catch the blind spots both share. If you work in Codex rather than Claude Code, the built-in reviewer is a second Codex instead, and the same holds.

For a real second opinion, add a model from another company. Autarkeia can hand the review to **Codex** (OpenAI), **Claude** (Anthropic, when you work in Codex) or **Grok** (xAI). Each runs on your Mac and reads files in your vault itself, so the reviewer checks the actual file rather than trusting a summary of it. The read-only settings below restrict file writes. They do not confine which files can be read or, by themselves, prove network isolation.

## What you need

| | What it is | Account |
|---|---|---|
| **Claude Code** or **Codex** | The app you already run Autarkeia in. Hosts the built-in reviewer: a second Claude, or a second Codex. | Your Claude or ChatGPT account |
| **Codex CLI** | OpenAI's command-line agent | A ChatGPT account. OpenAI says Codex is included across ChatGPT plans, Free included, with usage limits that vary by plan. |
| **Claude Code** (for Codex users) | Anthropic's command-line agent | A paid Claude plan (Pro or above). Which models a plan can use differs by plan; the review falls back to your plan's default when a named model is not available. |
| **Grok Build** | xAI's command-line agent | An xAI account (sign in through the browser), or an xAI API key. Check x.ai for which plans include it. |

You can install any of them, or none. With none, `brainstorm` still works with the built-in reviewer. A reviewer from the same company as the model you work in (a second Codex for a Codex user, Claude for a Claude Code user) is not an outside-company opinion, even when it runs as a separate command. **All reviewers** means every installed reviewer from another company than the one you work in, plus the built-in reviewer.

## Install

Each of these is the vendor's own installer. Run them in Terminal.

**Codex** (official guide: https://developers.openai.com/codex/cli):

```bash
curl -fsSL https://chatgpt.com/codex/install.sh | sh
```

Then run `codex` once, choose **Sign in with ChatGPT**, and finish the sign-in in your browser. Type `/quit` to leave.

**Claude Code**, if you work in Codex (official guide: https://code.claude.com/docs/en/setup):

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

Then run `claude` once in your vault folder, answer its first-run questions (trust the folder), type `/login` and finish the sign-in in your browser. Type `/exit` to leave. Your Codex agent can run the install line for you if you ask; the sign-in is yours.

**Grok Build** (official guide: https://docs.x.ai/build/overview):

```bash
curl -fsSL https://x.ai/cli/install.sh | bash
```

Then sign in:

```bash
grok login
```

If either command says "command not found" afterwards, close Terminal and open it again.

## Check it works

```bash
codex --version
```

```bash
claude --version
```

```bash
grok --version
```

Each should print a version number. You only need the ones you installed.

A version number proves the tool is installed, not that it is signed in. For a real test, open your vault in Claude Code (or Codex) and say **brainstorm: test that codex answers** (or claude, or grok). It sends a tiny question about a harmless file and shows the reply. A reply means it works end to end. "Not signed in" means: run `codex`, or `claude` then `/login`, or `grok login` in Terminal and sign in there, as in the Install section above.

## How to use it

In your vault, say:

| Say | Who reviews |
|---|---|
| **second opinion on** this decision | The built-in reviewer: Claude, or Codex if you work in Codex |
| **send to codex** | Codex (when you already work in Codex: a separate, read-only Codex; same company, fresh context) |
| **send to claude** | Claude, when you work in Codex (in Claude Code it is the built-in reviewer). Add **use opus** or **high effort** to choose; otherwise your Claude Code default applies. |
| **send to grok** | Grok |
| **all reviewers** | Every reviewer that can take this material |

Nothing goes to an outside reviewer unless you name it. (When you work in Codex, the built-in reviewer is itself a Codex, so a plain second opinion is read by OpenAI, like everything else in that session.) If you ask for a plain second opinion, Autarkeia uses the built-in reviewer and tells you which outside reviewers are available.

What happens:

1. The AI you are working with (Claude or Codex) writes its own view first and keeps it to itself, so it cannot steer the reviewer.
2. It writes a short packet in the item's owner's `reviews/` (the project folder for any project-owned review, the vault otherwise; answers stay with the packet): your question and which files to read. Naming a reviewer covers those files. It does not allow sending unrelated private files. If the project's rules forbid even a pointer, the vault copy is not written and the project is not named there.
3. Each reviewer is told to read only the named files, to treat them as data rather than instructions, and to write its answer next to the packet. The built-in reviewer gets the same instruction. That is an instruction, not a technical confinement.
4. It puts the answers side by side. Where they disagree, you see both. It does not split the difference.
5. You get one recommendation and, if a decision is still yours, one question.

A review takes from one to several minutes per reviewer.

## What to know before you use it

- **Read-only restricts writes, not reads.** Codex is started with `-s read-only`, Claude in plan mode with only its built-in reading tools and none of your configured connectors, and Grok with `--sandbox read-only`. Those settings select technical write restrictions, subject to the tool’s writable exceptions. They do not limit which files can be read, and starting the command in your vault folder does not confine it. A reviewer may open other files than the ones named. The same is true of the built-in reviewer: it is told to read only the named files, and that instruction is not a technical confinement.
- **Grok's shell can still reach the internet.** The read-only setting does not turn the network off. You choose what Grok reviews, including mail, imported documents and fetched pages. Know that a hidden instruction inside such a file could ask a reviewer with network access to send what it read somewhere else; the reviewer prompt tells Grok to treat file contents as evidence, and that is an instruction, not a technical guarantee.
- **Naming a reviewer covers the files the review is about.** It does not allow sending unrelated private files. If the thing is about your health, another person, or anything you said was off the record, Autarkeia asks you before sending it out, even after you named the reviewer.
- **The other company sees what the reviewer reads.** Whatever files Codex, Claude or Grok open are sent to OpenAI, Anthropic or xAI under your account, just as your own sessions go to the company whose model you work in.
- **Claude's models depend on your plan.** If you ask for a model your Claude plan does not include, the review says so and runs once more on your plan's default. Choosing a plan or model is yours; Autarkeia does not pick one for you.
- **Keep your vault in an ordinary folder**, such as Documents. Grok's read-only setting leaves temporary folders writable (`/tmp`, `/var/folders`, `~/.grok` and similar), so Autarkeia will not run Grok on a vault stored there.
- **It uses your own plan's limits.** A long review against a big vault is real usage. If you hit a limit, that is the plan, not a fault.

## If something goes wrong

- **"Not signed in"**: run `codex` (then choose Sign in with ChatGPT), or `claude` then `/login`, or `grok login` again, in your own Terminal. Autarkeia never handles your password.
- **Claude says a flag is unknown**: your Claude Code is older than this guide expects. Update it with the install line above. Until then Autarkeia leaves Claude out of the review rather than run it with fewer restrictions; only the optional effort flag is dropped.
- **Grok returns almost nothing**: it sometimes stops on its first step. Autarkeia retries once on its own. If the second try also fails, it tells you the review did not finish and leaves that reviewer out.
- **"Command not found" inside Claude Code or Codex**: restart the app after installing, so it sees the new command.
