# Changelog

User-visible changes to Autarkeia, newest first. Historical entries through 0.4.9 were reconstructed from published repository history. Dates are the version-introducing commit dates in their recorded timezone, not independently verified publication timestamps. Later changes made without a version bump are labelled separately. The published history starts at 0.3.0; no earlier releases are documented here.

## Repository updates — 2026-10-20

- Added an automated release check for matching versions, dated release notes, preservation of earlier release headings on version bumps, and changelog updates for shipped changes. The required GitHub check blocks merging when these checks fail. No plugin version change.

## 0.4.10 - 2026-10-20

- Skills no longer preapprove shell commands and file writes. Your app's permissions govern them; depending on your settings, you may see more approval prompts.
- Imported emails, documents and reviewer answers remain attributed evidence, not authority to run commands or change rules. Passwords, API keys and tokens are excluded from new memory and review packets; secret scans report filenames without printing matching values.
- Private-project routing now also covers processed mail and attachments, drafts, friction and reports. Projects that forbid even a pointer stay out of vault-level records; their reminder lines disappear from the overview, so deadlines and urgent items require checking that project’s own records.
- Grok reviews no longer accept outside material, including notes that quote or copy it. Read-only protection restricts writes; it does not confine reads or prove network isolation. Review paths handle spaces and apostrophes, and new reviews preserve existing files.
- The transcript reader marks mixed injected/user records as partial with uncertain attribution, rejects conflicting session identities and recovers after malformed record fields without silently treating the scan as complete.
- **Upgrade:** update the plugin and start a fresh session. Existing vault contracts are not overwritten. Run **health check** to review and approve the new **Source material and credentials** section and private-project wording; see [Older vaults](INSTALL.md#older-vaults). No new prerequisite beyond the reader's existing Python 3 requirement. These changes do not make AI instruction-following a security guarantee.

## Repository updates — 2026-10-20

- Added one human-step rule to the vault template: finish authorized preparation, give the user the exact remaining action, resume after their report, and confirm the outcome before recording completion. Approval boundaries are unchanged. Existing vaults need the rule added explicitly; INSTALL.md Updates provides the request, and the README links there. This template/documentation update leaves plugin version 0.4.9 unchanged.

## Repository updates — 2026-10-19

- Added this history and made changelog updates mandatory in the contributor release rules. This documentation-only update does not change the plugin version.

## 0.4.9 — 2026-10-19

- Daily debrief reads the selected day's records first, then asks only about gaps and corrections. A day with little recorded stays a short review; missing records are not treated as evidence that nothing happened.
- Reflection is optional and off by default. A one-off request does not become a permanent preference. Questions, including follow-ups, stay within the four-question limit.
- Proposed saved items distinguish log-only reflections from approved facts, decisions and tasks. Distill respects these choices instead of turning every intention into a task later.

## 0.4.8 — 2026-10-18

- Distill reads the exact current conversation's retained original messages in Claude Code and Codex, including retained history from before compaction. It checks later corrections and reports incomplete coverage when history is unavailable.
- **Upgrade note:** the bundled transcript reader requires Python 3. Disabled or missing local history limits recovery.
- **Removed:** checkpoint. Existing saved notes stay untouched; handover still provides a separate note for a fresh session.

Later updates without a version bump:

- 2026-10-18: added the optional genome-check tool for comparing a genome file with ClinVar. It is separate from the everyday skills; see [its guide](tools/genome-check/README.md) for setup, limitations and privacy considerations.
- 2026-10-19: expanded the skill descriptions and everyday-use guide to explain each skill's practical benefit.

## 0.4.7 — 2026-10-18

- Added one shared [installation guide](INSTALL.md) for agents and people, covering both apps, existing vaults, updates and verification.
- Separated the README overview from installation and first-session guidance. Users can give their agent an installation request, then follow [Getting started](docs/getting-started.md) for everyday use.

## 0.4.6 — 2026-10-15

- Added the Codex plugin and marketplace definitions. The same skills and vault template now serve Claude Code and Codex.

Later updates without a version bump, 2026-10-15:

- Corrected Claude-only commands and wording across skills and guides, clarified app-specific paths and existing-vault guidance, and added contributor rules to keep both app versions aligned.

## 0.4.5 — 2026-10-15

- Added the getting-started guide and the handover skill, which saves a continuation note for a fresh session.
- Extended librarian guidance for recordings and transcripts, and clarified backup and privacy expectations.

Later updates without a version bump, 2026-10-15:

- Documented automatic plugin updates and refreshed the description to “a living record of you, in files you own.”

## 0.4.4 — 2026-10-15

- Added operating guidance for evidence, corrections, attribution and staying within the user's request.
- Defined how newer facts supersede older ones while preserving history, how conflicting sources are weighed, and when an observation becomes an agreed task.
- Added an archive for incoming originals, separate from working documents, with registers and file hashes. Librarian preserves originals; health-check includes archive checks.

## 0.4.3 — 2026-10-14

- Added project-specific rules and memory routing, so a project can keep its own instructions and records without duplicating the whole vault contract.
- Updated distill, realign and health-check to respect project boundaries.

Later updates without a version bump, 2026-10-14:

- Explained the vault layout, older-vault handling and product purpose in the README. Added contributor rules requiring documentation to stay in step with user-visible changes.

## 0.4.2 — 2026-10-14

- Moved the vault's shared instructions into `AGENTS.md`, with `CLAUDE.md` referring to it, so different agents read one contract.
- Updated setup, distill and health-check for the shared instruction file.
- **Existing vaults:** updating the plugin does not automatically migrate your personal instruction files; preserve your custom rules and follow the existing-vault guidance in [Installation](INSTALL.md).

## 0.4.1 — 2026-10-09

- Documented installation directly from GitHub instead of requiring a local downloaded copy.

Later updates without a version bump:

- 2026-10-09: replaced the trusted-circle test framing with public-facing wording.
- 2026-10-11: extended brainstorm with read-only Codex and Grok second opinions and a setup guide; expanded the README's explanation of why the vault exists.

## 0.4.0 — 2026-09-23

- Added setup: the first session captures who the vault is for, priorities and one real job, then saves one real working cycle into memory.
- Setup asks one question at a time and can resume from recorded answers without building unused project structure.

## 0.3.0 — 2026-09-20

- First version present in published history: a Claude Code test with a personal vault template and twelve skills for saving session memory, daily and weekly reviews, checkpointing, document and email intake, realignment, diagnostics, second opinions, improvement proposals, writing drafts and sparring.
- Kept durable records in user-owned files, with local plugin installation instructions and a copy-the-skills fallback.
