# The archive: originals, kept as they arrived

Memory is the summary. The archive is the evidence. A later, better model re-reads the originals and finds what today's missed, so an original is never edited, never summarised in place, and never deleted on the AI's initiative.

## Original or working?

- **Original** (goes to `archive/`): made by someone else and arrived as is. A bank or broker statement, a tax form, an invoice, a contract or anything signed, a letter with someone's letterhead, a scan, a photo of a document, a data export from a service, a medical report.
- **Working** (goes to `docs/`): written by the user or by an AI. Analysis, notes, drafts, summaries, transcripts they made, plans.

When unsure, treat it as an original.

## Layout

Organised the way a person looks for things: first the part of life, then the person or thing, then the kind of document. Eight areas, named exactly as below, with spaces and capitals (not slugs). None is created until a document for it arrives.

| Area | What goes there |
|---|---|
| `archive/Official documents/` | Each person by name: passports and IDs, residence and citizenship, visas, civil certificates |
| `archive/Money and tax/` | Banks and investments, tax by country, advisers, insurance, household bills |
| `archive/Health/` | Medical records by person; a portal export kept whole; shared insurance |
| `archive/Homes/` | One folder per property: title or lease, insurance, works |
| `archive/Travel/` | Trips by year and destination; tickets, bookings, travel insurance, entry forms |
| `archive/Companies and projects/` | One folder per company or project; legal, banking, board and work records stay together |
| `archive/Photos and memories/` | Albums and exports, family history, creative work |
| `archive/Archive records/` | What was imported when, and from where |

Inside an area: `<person or thing>/<document kind>/file`. For example `Official documents/Maria/Passport/`, `Money and tax/Banks and investments/First Bank/Statements/`, `Travel/Trips/2026 Lisbon/`.

## Filing rules

- A person's official records go under that person. Other people's documents stay under their own names; having a document never authorises using it.
- Company records stay with the company, property papers with the property, trip papers with the trip. General bank statements and tax returns stay in Money and tax.
- Keep familiar names. No empty folders made in advance. No Misc, Downloads or Desktop.
- A coherent export (a health portal, a social-media download, a mailbox) is kept whole in one folder, never split into the tree.
- The original keeps its name unless the name is empty or meaningless; then date and plain description, nothing clever. Never overwrite: if the destination name exists with a different hash, add the period or date to the new file's name (`statement-2026-09.pdf`) and keep both. After copying, verify the copy's hash matches the source.
- A document that belongs to a project whose `AGENTS.md` keeps its content inside goes to `projects/<name>/archive/` with the same layout and its own registers; the vault's daily log gets a pointer at most, and nothing at all if the project's rules forbid it. Read the project's rules before the first write.
- Each area has its own `register.md`: date filed, file path, what it is, who it concerns, hash (first 12 characters of SHA-256), and whether facts have been taken out of it into memory. Before filing, check the hash against every register; a duplicate copy is not filed twice, but extraction from the existing file goes ahead if asked, and its row is updated. A register made by an earlier version with other columns keeps them; the missing columns (hash, who it concerns, extracted) are appended at the end, hashes for existing rows are filled from the files, and every row follows that register's actual header order.
- A move inside the archive is: copy, verify the hash, update the register, repair any reference, then remove the source. Never a bare move.
- Nothing leaves the archive without the user's yes. A document about another person is not sent anywhere.

## Register row

```
| YYYY-MM-DD | Money and tax/Banks and investments/First Bank/Statements/2026-09.pdf | bank statement | Maria | a1b2c3d4e5f6 | extracted: yes |
```
