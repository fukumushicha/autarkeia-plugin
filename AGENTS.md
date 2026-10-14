# Working on this repository

These rules are for anyone changing the plugin itself: people and AI agents (Claude, Codex, Grok). They are not part of the plugin and are not installed with it.

## The README is the user manual, and it is updated with every change

Every change a user could notice updates the user documentation **in the same commit**. That covers a skill's behaviour or wording a user sees, a command, the vault template, the install steps, the version, and anything in `tools/`.

- `README.md` always: the skills table, setup, how to use it, "What is in your vault", and the version in the title.
- `docs/second-opinion.md` when `brainstorm` or the outside reviewers change.
- A tool's own README (for example `tools/email-stager/README.md`) when that tool changes.

A commit that changes `autarkeia/`, `vault-template/`, `tools/` or `docs/` without touching `README.md` says why in its message, on a line of its own: `README: no user-visible change (<reason>)`.

Before pushing, read the README top to bottom once against what the change does. A README that describes the old behaviour is a bug, the same as broken code.
