# Genome check: compare a genome file with ClinVar

This tool reads a genome file on your computer and writes a report of the places that match ClinVar. ClinVar is a public database of how genetic variants have been classified. The report quotes ClinVar's own label for each match, and ClinVar's own confidence score for that label (0 to 4 stars).

## What it never does

It never changes, renames, or moves your genome file. It only reads it.

It never sends your genome anywhere. The only thing it downloads is the public ClinVar file. If you already have that file, pass `--clinvar` and it does not use the network at all.

It never gives advice. It does not tell you what to do about a result, a medicine, a screening, or anyone in your family. It reports what ClinVar says, and how many stars ClinVar gives that record.

## What you need

Python 3.10 or newer. It is already on a Mac. Check with `python3 --version` if you want to be sure.

About 250 MB free if the tool downloads ClinVar. That file is large because it is the whole public database, not because of your genome. A run also writes two small report files.

No install. The tool is one file, `genome_check.py`, in this folder.

## Getting it

**Ask your agent to fetch it.** In Claude Code or Codex, in your vault, give this request:

> Download the genome check tool from https://github.com/fukumushicha/autarkeia-plugin/tree/master/tools/genome-check (the files `genome_check.py` and `README.md`) into `tools/genome-check/` in my health project. Read its README. Then run `detect` on my genome file and show me what it found before the full run. Do not move or change my genome file.

To do it by hand, open Terminal in the folder where you want the tool and paste:

```
curl -fLO https://raw.githubusercontent.com/fukumushicha/autarkeia-plugin/master/tools/genome-check/genome_check.py
curl -fLO https://raw.githubusercontent.com/fukumushicha/autarkeia-plugin/master/tools/genome-check/README.md
```

To update the tool later, fetch the same two files again. Each JSON report records the tool version that wrote it.

## Which file you have

A sequencing file is a VCF: a text file of variants from a sequencing machine. It may be plain text or gzip-compressed (the name often ends in `.vcf.gz`). The tool can usually tell whether the positions use GRCh37 or GRCh38, the two reference editions it knows. The reference edition is the version of the human reference the positions were counted on. If the file does not say, the tool stops and you add `--build GRCh37` or `--build GRCh38`.

A chip file is the raw download from 23andMe or AncestryDNA. A zip is fine when it contains one text file. A chip reads a fixed list of positions chosen in advance. It is unreliable for rare variants. In a 2018 study, a clinical laboratory re-tested variants reported in consumer raw data and found that 40% were false positives (Tandy-Connor et al., *Genetics in Medicine* 2018, https://doi.org/10.1038/gim.2018.38). Treat every rare or "Pathogenic" call from a chip file as unverified. A position that is missing from the chip says nothing about that variant. A chip is matched differently from a sequencing file. The limits section says how.

The examples below use made-up paths. They are not real files and not real variants.

## The three commands

Open Terminal, go into this folder, and paste one of these. You can also call `genome_check.py` by its full path from any folder.

See what a file is, before a long run:

```
python3 genome_check.py detect --genome ~/genomes/my-genome.vcf.gz
```

Write the report. The first run downloads ClinVar into the same folder as the report. That download is the slow part.

```
python3 genome_check.py run --genome ~/genomes/my-genome.vcf.gz --out-dir ~/genomes/reports
```

Use a ClinVar file you already have, and do not download anything:

```
python3 genome_check.py run --genome ~/genomes/my-genome.vcf.gz --out-dir ~/genomes/reports --clinvar ~/genomes/clinvar_GRCh38_20240115.vcf.gz
```

Compare two saved JSON reports:

```
python3 genome_check.py diff ~/genomes/reports/earlier.json ~/genomes/reports/later.json --out ~/genomes/reports/what-changed.md
```

The diff lists matches that are new, matches that disappeared, and matches whose ClinVar label or star count changed. A match that disappeared says how that exact place is classified in the later ClinVar file. If the later run looked that place up and it is gone, the diff says it is no longer in this ClinVar release at this exact position and alleles. If the later run did not look that place up, the diff says the current classification was not looked up. When the earlier report recorded a ClinVar record number, the diff also says whether that record is now listed at another place, or is not in this release. One place can have more than one ClinVar record. Each record is compared, so a change in a second record is reported even when the first record is unchanged.

A run writes two files into the folder you name. One is a Markdown report, the one you read. The other is a JSON file, a structured copy of the same result, used the next month. The names look like `genome-check-2026-04-02-clinvar20260402.md` and the same name with `.json`. The first date is the day you ran it. The second date is the ClinVar release.

If you pass `--previous` and the JSON from last time, it also writes a third file, ending in `-diff.md`, describing what changed.

Other switches, when you need them:

- `--build GRCh37` or `--build GRCh38` if `detect` cannot tell the reference edition. This overrides the file. The report says the build was given by you.
- `--sample NAME` if a sequencing file has more than one person in it. Otherwise the first person in the file is used, and the report names them.
- `--classes` is a comma-separated list of ClinVar labels to keep. You can type a label with spaces or underscores, in any case. `Likely pathogenic`, `likely_pathogenic`, and `risk factor` are the same labels. The tool stores ClinVar's own spelling. The default is Pathogenic, Likely_pathogenic, risk_factor, drug_response, association, protective, and confers_sensitivity. An unknown label stops the run and lists the labels it accepts: Pathogenic, Likely_pathogenic, risk_factor, drug_response, association, protective, confers_sensitivity, Uncertain_significance, Likely_benign, Benign, Likely_risk_allele, Uncertain_risk_allele, Established_risk_allele, Affects, other, not_provided.
- `--clinvar-dir` chooses where a download is saved. The default is the report folder.

The tool will not overwrite a report, a diff, or a ClinVar file. A second run on the same day, with the same ClinVar release, stops and names the file that is already there. Move that report, or pick another folder. If a ClinVar file of that release is already saved, and it is the same file, the download is reused. Sameness is a checksum: a fingerprint of the file's bytes.

## How to read the report

The stars matter more than the label. ClinVar scores its confidence from 0 to 4. Four is a practice guideline. Three was reviewed by an expert panel. Two means several submitters who agree. One is a single submitter, or submitters who disagree. Zero means no assertion criteria, or no classification. Hits with 0 or 1 star are marked LOW CONFIDENCE in the report.

Pathogenic does not mean you will get the disease. It is a label in a database, attached to a variant, with a confidence score.

A sequencing file sometimes calls one allele and leaves the other blank, written `1/.` or `./1`. A vertical bar, as in `1|.`, means the same thing. That match is kept. The report marks the line INCOMPLETE CALL and does not call it heterozygous, because one allele was not called. If both alleles are blank (`./.`), that row is a no-call and not a match. If the only called allele is the reference letter and the other is blank (`0/.`), it is not a match either, and the summary still counts it under Incomplete calls.

A surprise can be an error in the file. A sequencing error can look like a pathogenic finding. Check a surprise against your real health record.

Nothing should change a screening, a medication, or a decision until a clinical laboratory has confirmed the variant and a genetics professional has seen the result.

## Keeping it current

Run it again about once a month. Point `--previous` at the JSON from the last run so the new folder contains a short diff as well as the new report.

```
python3 genome_check.py run --genome ~/genomes/my-genome.vcf.gz --out-dir ~/genomes/reports-may --previous ~/genomes/reports/genome-check-2026-04-02-clinvar20260402.json
```

ClinVar's monthly VCF comes out on the first Thursday of the month. The schedule is published at https://www.ncbi.nlm.nih.gov/clinvar/docs/maintenance_use/.

## Privacy

The script runs on your computer. It reads your genome file and does not upload it. The only download is the public ClinVar file from NCBI.

If you later ask an AI assistant to read the report, the matched variants in that report are processed by that AI's provider.

## Limits

A sequencing file is matched exactly: the same chromosome, the same position, the same reference letter, and the same alternate letter (the letter that differs). If the same variant is written differently in the two files, for example an insertion that is not lined up the same way, it is not reported.

Chip files: only single-letter ClinVar variants can be matched; a hit means the chip called ClinVar's alternate letter at that position. The chip does not report the reference letter, so the reference allele is not checked. Chip calls are read as the file wrote them, on the plus strand, which is the same DNA direction as the reference. The tool does not swap A with T or C with G.

A variant that is absent from your file is not evidence that you do not carry it. That is especially true for a chip, and for a sequencing file that lists only positions which differ from the reference.

Only GRCh37 and GRCh38 are read. An older build 36 file is refused.

Only ClinVar's germline classifications are used. Those are variants a person is born with, not changes found only in a tumour. Somatic classifications and oncogenicity classifications, which describe tumours, are ignored.

The report contains no recommendations, by design.
