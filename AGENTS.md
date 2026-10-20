# Working on this repository

These rules are for anyone changing the plugin itself: people and AI agents (Claude, Codex, Grok). They are not part of the plugin and are not installed with it.

## Keep each document responsible for one job

Every change a user could notice updates the user documentation **in the same commit**. That covers a skill's behaviour or wording a user sees, a command, the vault template, the install steps, the version, and anything in `tools/`.

- `README.md`: purpose, capabilities, supported apps, cost, version and the agent-led entry point. Keep installation commands out of it.
- `INSTALL.md`: the single shared installation procedure for agents and people; prerequisites, fresh installs, existing vaults, verification, updates, migrations and troubleshooting.
- `docs/getting-started.md`: first personal setup and everyday use after installation, for both apps; label app-specific controls explicitly.
- `docs/second-opinion.md` when `brainstorm` or the outside reviewers change.
- A tool's own README (for example `tools/email-stager/README.md`) when that tool changes.

Update the relevant document in the same commit. Touch the README when its overview, links or version change. A commit that changes `autarkeia/`, `vault-template/`, `tools/` or `docs/` without touching `README.md` says why in its message, on a line of its own: `README: unchanged (<reason>; updated guide: <path or not applicable>)`.

Before pushing, read the README and affected guides against what the change does, and check their links. Documentation that describes old behaviour is a bug, the same as broken code.

## One plugin, two apps: Claude Code and Codex

The skills, references and vault template exist once and serve both apps. Only the install files are separate. Keep the two in step on every change:

1. **The version is in four places, always the same number:** `.claude-plugin/marketplace.json` (twice: `metadata.version` and the plugin's `version`), `autarkeia/.claude-plugin/plugin.json`, `autarkeia/.codex-plugin/plugin.json`; plus the README title. A version left behind in one file means that app's users never see the update. Check before pushing: `grep -rn '"version"' .claude-plugin autarkeia/.claude-plugin autarkeia/.codex-plugin`.
2. **Skill wording works in both apps.** Name skills in plain words (**distill**, the distill skill), never as slash commands (`/distill`). A path that differs between the apps gives both (`~/.claude/plugins/marketplaces/autarkeia-plugin/...` and `~/.codex/.tmp/marketplaces/autarkeia-plugin/...`). Say "Claude Code or Codex", or "the app", where either can host. Claude-only steps (`/plugin`, `/autarkeia:distill`, `.claude/` fallback) are fine only where the text says they are for Claude.
3. **One procedure, two app paths.** Check any installation or update change in `INSTALL.md` against both app paths in the same commit. Keep personal setup in `docs/getting-started.md`, shared by both apps. Do not duplicate installation commands there or in the README.

Before publishing a release, install it once in each app from the pushed branch or a local path: `claude plugin validate .`, and in Codex a scratch `CODEX_HOME` with `codex plugin marketplace add <path>` and `codex plugin add autarkeia@autarkeia-plugin`, then confirm `codex debug prompt-input` lists every skill.

## Every release has a changelog entry

Updating `CHANGELOG.md` is mandatory for every future plugin release. A release is not ready to merge or publish without its entry. The `Release changelog` GitHub check validates the release on every pull request to `master` and every push to it. The check must pass before merging; do not bypass or remove it to publish a release.

- Add or finalize the entry in the same commit that changes the version. Use `## X.Y.Z — YYYY-MM-DD`, newest version first, with the exact version shared by the manifests and README. Verify the date from the clock when preparing the release; correct it if publication moves to another date.
- Explain the user-visible changes and their practical effect. Call out removals, breaking changes, new prerequisites and any action existing users must take. Record only changes included in the release, never planned work or unverified outcomes.
- Keep notable changes published without a plugin version bump as separately dated follow-ups under the current version, or as a clearly labelled repository-only update. Do not retroactively imply they were included in the original release. A documentation-only change does not require a version bump solely for the changelog.
- Before merge or publication, the author and reviewer compare the entry with the changes since the previous version, check version/date consistency and upgrade guidance, and confirm the README still links to the changelog. Missing or stale notes block release completion, just like missing required documentation.

Run the checks locally before pushing:

```sh
python3 scripts/check-changelog.py --base-ref origin/master
python3 -m unittest discover -s scripts -p 'test_*.py'
```

The automated check requires matching versions in all four manifest fields and the README title, a matching newest dated changelog section with a substantive bullet, and a new section when the version increases while preserving every prior release heading. A numeric version displayed in the marketplace description must match too. Changes under `autarkeia/`, `vault-template/`, or `tools/` without a version increase still require a changelog change. It rejects malformed or placeholder-only current release notes. Reviewers remain responsible for the accuracy and completeness of the prose; repository administrators can deliberately change protection settings.

Edits to the validator, its tests, or `.github/workflows/` change the gate itself and require explicit reviewer attention: each pull request runs its proposed copy of these files.
