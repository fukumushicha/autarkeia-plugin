"""Tests for genome_check. Fixtures are invented. No real genome is used."""

import contextlib
import gzip
import hashlib
import io
import json
import os
import pathlib
import re
import sys
import tempfile
import unittest
import zipfile
from datetime import date

TOOL_DIR = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_DIR))
import genome_check as gc

RESEARCH = (
    "**Research-grade and unconfirmed. Not for medical decisions.** "
    "This report compares a raw genome file with ClinVar, a public database of "
    "what genetic variants are known to mean. Raw consumer and research genome "
    "data contain errors, and a ClinVar classification is not a diagnosis. "
    "Nothing here has been confirmed by a clinical laboratory. ClinVar states "
    "that its data are not intended for direct diagnostic use or medical "
    "decision-making without review by a genetics professional."
)
CHIP = (
    "**This is a genotyping-chip file, not sequencing.** Chips read a fixed "
    "set of preselected positions and are unreliable for rare variants: in a "
    "2018 study, a clinical laboratory re-tested variants reported in consumer "
    "raw data and found that 40% were false positives (Tandy-Connor et al., "
    "*Genetics in Medicine* 2018, https://doi.org/10.1038/gim.2018.38). Treat "
    'every rare or "Pathogenic" call from this file as unverified. A position '
    "missing from the chip says nothing about that variant."
)
LEGEND = (
    "ClinVar rates its confidence in each classification from 0 to 4 stars: "
    "0 = no assertion criteria or no classification provided; "
    "1 = a single submitter, or submitters who disagree; "
    "2 = several submitters who agree; "
    "3 = reviewed by an expert panel; "
    "4 = a practice guideline. "
    "Hits with 0 or 1 star are marked LOW CONFIDENCE."
)
FORBIDDEN = re.compile(
    r"\b(should|recommend|consider|advise|daughter|son|children)\b",
    re.IGNORECASE,
)
REV2 = "criteria_provided,_multiple_submitters,_no_conflicts"
REV1 = "criteria_provided,_single_submitter"
REV3 = "reviewed_by_expert_panel"
REV4 = "practice_guideline"
REV0 = "no_assertion_criteria_provided"
EXACT_BLOCK = (
    "- **GENEA** \u2014 Pathogenic \u2014 \u2605\u2605\u2606\u2606 (2/4) "
    "criteria provided, multiple submitters, no conflicts\n"
    "  - Variant: 1:1000 C>T \u00b7 rs000000 \u00b7 "
    "ClinVar 12345 (https://www.ncbi.nlm.nih.gov/clinvar/variation/12345/)\n"
    "  - Genotype: 0/1 (heterozygous)\n"
    "  - Reads: depth 31, alt reads 14 of 31, GQ 99, filter PASS\n"
    "  - Condition: Example syndrome"
)


def run_main(argv):
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        code = gc.main(list(argv))
    return code, stdout.getvalue(), stderr.getvalue()


def snap(path: pathlib.Path):
    stat = path.stat()
    return stat.st_mtime_ns, path.read_bytes()


def header_body(markdown: str) -> str:
    start = markdown.index("<!-- header -->")
    end = markdown.index("<!-- /header -->")
    return markdown[start:end]


def outside_header(markdown: str) -> str:
    start = markdown.index("<!-- header -->")
    end = markdown.index("<!-- /header -->") + len("<!-- /header -->")
    return markdown[:start] + markdown[end:]


def genome_vcf(body, *, contig_length=249250621, contig_id="1", reference=None, samples=("SAMPLE",)):
    lines = ["##fileformat=VCFv4.2"]
    if reference:
        lines.append(f"##reference={reference}")
    if contig_length is not None:
        lines.append(f"##contig=<ID={contig_id},length={contig_length}>")
    header = "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO"
    if samples:
        header += "\tFORMAT\t" + "\t".join(samples)
    lines.append(header)
    lines.extend(body)
    return "\n".join(lines) + "\n"


def gline(chrom, pos, ref, alt, gt, *, qual=".", filt="PASS", info=".", fmt=None, sample=None, trailing=""):
    if fmt is None:
        fmt = "GT"
        sample_field = gt
    else:
        sample_field = gt if sample is None else sample
    line = f"{chrom}\t{pos}\t.\t{ref}\t{alt}\t{qual}\t{filt}\t{info}\t{fmt}\t{sample_field}"
    if trailing:
        line += "\t" + trailing
    return line


def cv(chrom, pos, ref, alt, *, vid=None, clnsig="Pathogenic", rev=REV2, gene="GENEA", condition="Example_syndrome", rs="000000"):
    vid = str(pos) if vid is None else str(vid)
    fields = [
        f"CLNSIG={clnsig}",
        f"CLNREVSTAT={rev}",
        f"GENEINFO={gene}:1",
        f"CLNDN={condition}",
    ]
    if rs is not None:
        fields.append(f"RS={rs}")
    fields.append("CLNVC=single_nucleotide_variant")
    fields.append("MC=SO:0001583|missense_variant")
    return f"{chrom}\t{pos}\t{vid}\t{ref}\t{alt}\t.\t.\t" + ";".join(fields)


def clinvar_vcf(records, *, build="GRCh37", filedate="20240115"):
    lines = [
        "##fileformat=VCFv4.2",
        f"##fileDate={filedate}",
        f"##reference={build}",
        "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO",
        *records,
    ]
    return "\n".join(lines) + "\n"


def chip_23(rows, build_line="# build 37"):
    lines = [
        "# This data file was generated by 23andMe",
        build_line,
        "# rsid\tchromosome\tposition\tgenotype",
        *rows,
    ]
    return "\n".join(lines) + "\n"


def chip_ancestry(rows):
    lines = [
        "# AncestryDNA raw data download",
        "# coordinates use human reference build 37.1",
        "rsid\tchromosome\tposition\tallele1\tallele2",
        *rows,
    ]
    return "\n".join(lines) + "\n"


def load_outputs(out: pathlib.Path):
    mds = sorted(path for path in out.glob("genome-check-*.md") if not path.name.endswith("-diff.md"))
    jsons = sorted(out.glob("genome-check-*.json"))
    diffs = sorted(out.glob("genome-check-*-diff.md"))
    if len(mds) != 1 or len(jsons) != 1:
        names = [path.name for path in out.iterdir()]
        raise AssertionError(f"expected one report and one json, found {names}")
    markdown = mds[0].read_text(encoding="utf-8")
    payload = json.loads(jsons[0].read_text(encoding="utf-8"))
    return payload, markdown, mds[0], jsons[0], diffs


def ids_of(payload, bucket):
    found = []
    for hit in payload[bucket]:
        found.extend(hit["clinvar_ids"])
    return found


class TempTest(unittest.TestCase):
    def temp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        return pathlib.Path(folder.name)

    def assert_report_contract(self, markdown, *, chip):
        self.assertEqual(gc.HEADER_RESEARCH, RESEARCH)
        self.assertEqual(gc.HEADER_CHIP, CHIP)
        self.assertEqual(gc.STAR_LEGEND, LEGEND)
        body = header_body(markdown)
        self.assertIn(RESEARCH, body)
        if chip:
            self.assertIn(CHIP, body)
        else:
            self.assertNotIn("genotyping-chip", markdown)
        self.assertIsNone(FORBIDDEN.search(outside_header(markdown)))
        self.assertIsNone(FORBIDDEN.search("The report contains no recommendations by design."))
        self.assertIsNotNone(FORBIDDEN.search("you should consider this"))
        self.assertIn(LEGEND, markdown)
        self.assertIn("https://www.ncbi.nlm.nih.gov/clinvar/docs/review_status/", markdown)
        if chip:
            self.assertIn(gc.METHOD_TEXT_CHIP, markdown)
            self.assertNotIn(
                "Exact match on chromosome, position, reference and alternate allele.",
                markdown,
            )
        else:
            self.assertIn(gc.METHOD_TEXT, markdown)
            self.assertNotIn("only single-letter ClinVar variants can be matched", markdown)
        self.assertIn("not evidence the person does not carry it", markdown)
        self.assertIn("somatic and oncogenicity classifications are ignored", markdown)
        self.assertIn("no recommendations by design", markdown)
        self.assertNotIn("expert reviewed", markdown.lower())

    def assert_diff_contract(self, markdown):
        self.assertIn(RESEARCH, header_body(markdown))
        self.assertIsNone(FORBIDDEN.search(outside_header(markdown)))
        self.assertIn("no recommendations by design", markdown)

    def run_local(self, genome_text, clinvar_text, extra=None, genome_name="genome.vcf"):
        root = self.temp()
        genome = root / genome_name
        clinvar = root / "clinvar.vcf"
        out = root / "out"
        genome.write_text(genome_text, encoding="utf-8")
        clinvar.write_text(clinvar_text, encoding="utf-8")
        before = snap(genome)
        argv = ["run", "--genome", str(genome), "--out-dir", str(out), "--clinvar", str(clinvar)]
        if extra:
            argv.extend(extra)
        code, stdout, stderr = run_main(argv)
        self.assertEqual(code, 0, stderr)
        self.assertEqual(stdout, "")
        self.assertEqual(snap(genome), before)
        payload, markdown, md_path, json_path, diffs = load_outputs(out)
        chip = "chip" in payload["metadata"]["file_type"].lower()
        self.assert_report_contract(markdown, chip=chip)
        counts = payload["metadata"]["counts"]
        star_total = sum(int(value) for value in counts["by_stars"].values())
        self.assertEqual(star_total, counts["hits"])
        self.assertEqual(int(counts["by_stars"]["0"]) + int(counts["by_stars"]["1"]), counts["low_confidence"])
        self.assertEqual(payload["tool"], "genome-check")
        self.assertEqual(payload["tool_version"], "0.2.0")
        self.assertEqual(payload["metadata"]["clinvar_source"], "local file provided")
        self.assertIsNone(payload["metadata"]["clinvar_url"])
        self.assertIsNone(payload["metadata"]["clinvar_download_time"])
        if not extra or "--previous" not in extra:
            self.assertNotIn("previous_lookup", payload)
        return {
            "payload": payload,
            "md": markdown,
            "out": out,
            "genome": genome,
            "clinvar": clinvar,
            "md_path": md_path,
            "json_path": json_path,
            "diffs": diffs,
            "root": root,
            "stderr": stderr,
        }


class TestWords(TempTest):
    def test_header_constants_match_the_fixed_text(self):
        self.assertEqual(gc.HEADER_RESEARCH, RESEARCH)
        self.assertEqual(gc.HEADER_CHIP, CHIP)
        self.assertEqual(gc.STAR_LEGEND, LEGEND)
        self.assertEqual(gc.CLINVAR_BASE_URL, "https://ftp.ncbi.nlm.nih.gov/pub/clinvar/")

    def test_chip_method_text_is_separate_from_sequencing(self):
        sentence = (
            "Chip files: only single-letter ClinVar variants can be matched; a hit means "
            "the chip called ClinVar's alternate letter at that position. The chip does not "
            "report the reference letter, so the reference allele is not checked."
        )
        self.assertIn(sentence, gc.METHOD_TEXT_CHIP)
        self.assertNotIn("only single-letter ClinVar variants can be matched", gc.METHOD_TEXT)
        self.assertTrue(
            gc.METHOD_TEXT.startswith(
                "Exact match on chromosome, position, reference and alternate allele."
            )
        )
        self.assertEqual(gc.method_text_for(False), gc.METHOD_TEXT)
        self.assertEqual(gc.method_text_for(True), gc.METHOD_TEXT_CHIP)


class TestClassify(TempTest):
    def decision(self, clnsig):
        return gc.classification_decision(clnsig, set(gc.DEFAULT_CLASSES))

    def test_base_terms_and_selection(self):
        cases = {
            "Pathogenic": (True, ["Pathogenic"], False),
            "Likely_pathogenic": (True, ["Likely_pathogenic"], False),
            "Pathogenic/Likely_pathogenic": (True, ["Pathogenic", "Likely_pathogenic"], False),
            "Pathogenic,_low_penetrance": (True, ["Pathogenic"], False),
            "Benign": (False, ["Benign"], False),
            "Uncertain_significance": (False, ["Uncertain_significance"], False),
            "Conflicting_classifications_of_pathogenicity": (
                False,
                ["Conflicting_classifications_of_pathogenicity"],
                True,
            ),
            "Conflicting_classifications_of_pathogenicity|risk_factor": (
                True,
                ["Conflicting_classifications_of_pathogenicity", "risk_factor"],
                True,
            ),
            "drug_response": (True, ["drug_response"], False),
            "protective": (True, ["protective"], False),
            "Conflicting_interpretations_of_pathogenicity": (
                False,
                ["Conflicting_interpretations_of_pathogenicity"],
                True,
            ),
            "Conflicting_interpretations_of_pathogenicity|protective": (
                True,
                ["Conflicting_interpretations_of_pathogenicity", "protective"],
                True,
            ),
        }
        for clnsig, (selected, terms, conflicting) in cases.items():
            with self.subTest(clnsig=clnsig):
                got = self.decision(clnsig)
                self.assertEqual(got["selected"], selected)
                self.assertEqual(got["terms"], terms)
                self.assertEqual(gc.base_terms(clnsig), terms)
                self.assertEqual(got["conflicting"], conflicting)
                if selected:
                    self.assertTrue(got["selected_terms"])
                    self.assertNotIn("Conflicting_classifications_of_pathogenicity", got["selected_terms"])
                    self.assertNotIn("Conflicting_interpretations_of_pathogenicity", got["selected_terms"])

    def test_low_penetrance_on_a_compound_value(self):
        self.assertEqual(
            gc.base_terms("Pathogenic/Likely_pathogenic,_low_penetrance"),
            ["Pathogenic", "Likely_pathogenic"],
        )


class TestStars(TempTest):
    def test_every_listed_review_status(self):
        expected = {
            "practice_guideline": (4, False, "practice guideline"),
            "reviewed_by_expert_panel": (3, False, "reviewed by expert panel"),
            "criteria_provided,_multiple_submitters,_no_conflicts": (
                2,
                False,
                "criteria provided, multiple submitters, no conflicts",
            ),
            "criteria_provided,_single_submitter": (1, False, "criteria provided, single submitter"),
            "criteria_provided,_conflicting_classifications": (
                1,
                False,
                "criteria provided, conflicting classifications",
            ),
            "criteria_provided,_conflicting_interpretations": (
                1,
                False,
                "criteria provided, conflicting interpretations",
            ),
            "no_assertion_criteria_provided": (0, False, "no assertion criteria provided"),
            "no_assertion_provided": (0, False, "no assertion provided"),
            "no_classification_provided": (0, False, "no classification provided"),
            "no_classification_for_the_single_variant": (
                0,
                False,
                "no classification for the single variant",
            ),
            "no_classifications_from_unflagged_records": (
                0,
                False,
                "no classifications from unflagged records",
            ),
            "no_interpretation_for_the_single_variant": (
                0,
                False,
                "no interpretation for the single variant",
            ),
            "": (0, False, ""),
            "not_a_real_status": (0, True, "not a real status"),
        }
        for raw, (stars, unrecognised, display) in expected.items():
            with self.subTest(raw=raw):
                got = gc.review_status_info(raw)
                self.assertEqual(got["stars"], stars)
                self.assertEqual(got["unrecognised"], unrecognised)
                self.assertEqual(got["display"], display)
                self.assertNotEqual(got["display"], "expert reviewed")

    def test_star_glyphs(self):
        self.assertEqual(gc.star_glyph(0), "\u2606\u2606\u2606\u2606")
        self.assertEqual(gc.star_glyph(1), "\u2605\u2606\u2606\u2606")
        self.assertEqual(gc.star_glyph(2), "\u2605\u2605\u2606\u2606")
        self.assertEqual(gc.star_glyph(3), "\u2605\u2605\u2605\u2606")
        self.assertEqual(gc.star_glyph(4), "\u2605\u2605\u2605\u2605")


class TestZygosityAndChrom(TempTest):
    def test_zygosity(self):
        self.assertEqual(gc.zygosity_for_gt([0, 1], 1), "heterozygous")
        self.assertEqual(gc.zygosity_for_gt([1, 1], 1), "homozygous")
        self.assertEqual(gc.zygosity_for_gt([1], 1), "hemizygous")
        self.assertEqual(gc.zygosity_for_gt([1, 2], 1), "compound with another allele")
        self.assertEqual(gc.zygosity_for_gt([0, 2], 2), "heterozygous")
        for genotype in ("1/.", "./1", "1|.", ".|1"):
            alleles = gc.parse_gt(genotype)
            self.assertEqual(gc.zygosity_for_gt(alleles, 1), gc.INCOMPLETE_ZYGOSITY)
        self.assertEqual(gc.zygosity_from_copies(1, 2), "heterozygous")
        self.assertEqual(gc.zygosity_from_copies(2, 2), "homozygous")
        self.assertEqual(gc.zygosity_from_copies(1, 1), "hemizygous")

    def test_chromosomes(self):
        self.assertEqual(gc.normalize_chrom("chr1"), "1")
        self.assertEqual(gc.normalize_chrom("1"), "1")
        self.assertEqual(gc.normalize_chrom("chrM"), "MT")
        self.assertEqual(gc.normalize_chrom("M"), "MT")
        self.assertEqual(gc.normalize_chrom("MT"), "MT")
        self.assertEqual(gc.normalize_chrom("chrMT"), "MT")
        self.assertEqual(gc.normalize_chrom("23"), "X")
        self.assertEqual(gc.normalize_chrom("24"), "Y")
        self.assertEqual(gc.normalize_chrom("25"), "X")
        self.assertEqual(gc.normalize_chrom("26"), "MT")
        self.assertEqual(gc.normalize_chrom("chrX"), "X")
        self.assertEqual(gc.normalize_chrom("x"), "X")

    def test_condition_text(self):
        self.assertEqual(gc.condition_display("Alpha_thing|Beta_thing"), "Alpha thing; Beta thing")
        self.assertEqual(gc.truncate_text("N" * 350), ("N" * 300) + "\u2026")
        self.assertEqual(gc.truncate_text("short"), "short")


class TestAreas(TempTest):
    def test_gene_table_and_keywords(self):
        self.assertEqual(gc.assign_area(["Pathogenic"], ["BRCA1"], "Example syndrome"), "Hereditary cancer")
        self.assertEqual(gc.assign_area(["Pathogenic"], ["TTN"], ""), "Heart rhythm and heart muscle")
        self.assertEqual(gc.assign_area(["Pathogenic"], ["LDLR"], ""), "Cholesterol and lipids")
        self.assertEqual(gc.assign_area(["Pathogenic"], ["HFE"], ""), "Iron")
        self.assertEqual(gc.assign_area(["Pathogenic"], ["CYP2D6"], ""), "Drug response")
        self.assertEqual(gc.assign_area(["Pathogenic"], ["C9orf72"], ""), "Brain and nerves")
        self.assertEqual(gc.assign_area(["Pathogenic"], ["HLA-A"], ""), "Drug response")
        self.assertEqual(gc.assign_area(["drug_response"], ["BRCA1"], "Example syndrome"), "Drug response")
        self.assertEqual(gc.assign_area(["Pathogenic"], ["GENEA"], "breast cancer"), "Cancer (other)")
        self.assertEqual(gc.assign_area(["Pathogenic"], ["GENEA"], "long qt syndrome"), "Heart (other)")
        self.assertEqual(gc.assign_area(["Pathogenic"], ["GENEA"], "kidney cancer"), "Cancer (other)")
        self.assertEqual(gc.assign_area(["protective"], ["GENEA"], "Example syndrome"), "Other")
        self.assertEqual(
            gc.assign_area(["Pathogenic"], ["BRCA1", "CYP2D6"], ""),
            "Hereditary cancer",
        )


class TestDetect(TempTest):
    def detect(self, text, *, name="genome.txt", gzip_file=False, zip_members=None, extra=None):
        root = self.temp()
        path = root / name
        if zip_members is not None:
            with zipfile.ZipFile(path, "w") as archive:
                for member, contents in zip_members:
                    archive.writestr(member, contents)
        elif gzip_file:
            path.write_bytes(gzip.compress(text.encode("utf-8")))
        else:
            path.write_text(text, encoding="utf-8")
        argv = ["detect", "--genome", str(path)]
        if extra:
            argv.extend(extra)
        return run_main(argv)

    def test_vcf_builds_and_containers(self):
        code, out, err = self.detect(
            genome_vcf([], contig_length=249250621),
            name="genome.vcf",
        )
        self.assertEqual(code, 0, err)
        self.assertIn("File type: Sequencing VCF", out)
        self.assertIn("Reference build: GRCh37", out)
        self.assertIn("chromosome 1 contig length 249250621", out)
        self.assertIn("plain", out)

        code, out, err = self.detect(
            genome_vcf([], contig_length=248956422, contig_id="chr1"),
            name="genome.vcf",
        )
        self.assertEqual(code, 0, err)
        self.assertIn("Reference build: GRCh38", out)
        self.assertIn("248956422", out)

        code, out, err = self.detect(
            genome_vcf([], contig_length=None, reference="hg19"),
            name="text.vcf",
        )
        self.assertEqual(code, 0, err)
        self.assertIn("Reference build: GRCh37", out)
        self.assertIn("reference text", out)

        code, out, err = self.detect(
            genome_vcf([], contig_length=249250621, reference="GRCh38"),
            name="disagree.vcf",
        )
        self.assertEqual(code, 0, err)
        self.assertIn("Reference build: GRCh37", out)
        self.assertIn("disagreed", out)
        self.assertIn("contig length", out)
        self.assertIn("GRCh38", out)

        code, out, err = self.detect(
            genome_vcf([], contig_length=249250621, reference="hg18"),
            name="oldtext.vcf",
        )
        self.assertEqual(code, 0, err)
        self.assertIn("Reference build: GRCh37", out)
        self.assertIn("disagreed", out)

        code, out, err = self.detect(
            genome_vcf([], contig_length=249250621),
            name="genome.vcf.gz",
            gzip_file=True,
        )
        self.assertEqual(code, 0, err)
        self.assertIn("gzip", out)
        self.assertIn("Reference build: GRCh37", out)

    def test_chip_builds_zip_and_errors(self):
        code, out, err = self.detect(chip_23(["rs1\t1\t1000\tAA"]))
        self.assertEqual(code, 0, err)
        self.assertIn("File type: 23andMe chip", out)
        self.assertIn("Reference build: GRCh37", out)
        self.assertIn("header text", out)

        code, out, err = self.detect(chip_23(["rs1\t1\t1000\tAA"], build_line="# build 36"))
        self.assertEqual(code, 1)
        self.assertIn("36", err)

        code, out, err = self.detect(
            chip_23(["rs1\t1\t1000\tAA"], build_line="# build 36"),
            extra=["--build", "GRCh37"],
        )
        self.assertEqual(code, 0, err)
        self.assertIn("Reference build: GRCh37", out)
        self.assertIn("build given by user", out)

        code, out, err = self.detect(chip_ancestry(["rs1\t1\t1000\tA\tA"]))
        self.assertEqual(code, 0, err)
        self.assertIn("File type: AncestryDNA chip", out)
        self.assertIn("Reference build: GRCh37", out)
        self.assertIn("header text", out)

        code, out, err = self.detect(
            genome_vcf([], contig_length=100),
            name="unknown.vcf",
        )
        self.assertEqual(code, 1)
        self.assertIn("--build", err)

        code, out, err = self.detect(
            genome_vcf([], contig_length=249250621),
            name="forced.vcf",
            extra=["--build", "GRCh38"],
        )
        self.assertEqual(code, 0, err)
        self.assertIn("Reference build: GRCh38", out)
        self.assertIn("build given by user", out)

        text = chip_23(["rs1\t1\t1000\tAA"])
        code, out, err = self.detect(
            text,
            name="genome.zip",
            zip_members=[("notes.pdf", b"not a genome"), ("genome.txt", text)],
        )
        self.assertEqual(code, 0, err)
        self.assertIn("23andMe chip", out)
        self.assertIn("zip", out)
        self.assertIn("Reference build: GRCh37", out)

        code, out, err = self.detect(
            text,
            name="two.zip",
            zip_members=[("a.txt", text), ("b.txt", text)],
        )
        self.assertEqual(code, 1)
        self.assertIn("a.txt", err)
        self.assertIn("b.txt", err)

        code, out, err = self.detect("hello\nthis is not a genome\n", name="notes.txt")
        self.assertEqual(code, 1)
        self.assertIn("unrecognised genome file format", err)

    def test_detect_lists_samples(self):
        text = genome_vcf([], samples=("S1", "S2"))
        code, out, err = self.detect(text, name="multi.vcf")
        self.assertEqual(code, 0, err)
        self.assertIn("Samples: S1, S2", out)


class TestMatchVcf(TempTest):
    def test_genotypes_filters_and_chromosomes(self):
        genome = genome_vcf(
            [
                gline("chr1", 1000, "C", "T", "0/1", qual="99", info="DP=10", fmt="GT:DP:GQ:AD", sample="0/1:31:99:17,14"),
                gline("1", 2000, "A", "G", "1/1"),
                gline("Y", 3000, "C", "T", "1"),
                gline("1", 4000, "A", "C,T", "0/2", qual="40", fmt="GT:AD", sample="0/2:5,1,9"),
                gline("1", 5000, "A", "C,T", "1/2"),
                gline("1", 6000, "G", "A", "0/0"),
                gline("1", 7000, "G", "A", "./."),
                gline("1", 8000, "G", "A", "0/1", filt="LowQual"),
                gline("chrM", 9000, "A", "G", "0/1"),
                gline("1", 10000, "C", "T", "0/1", fmt="GT:FT", sample="0/1:q20"),
                gline("1", 11000, "C", "T", "0/1"),
            ]
        )
        clinvar = clinvar_vcf(
            [
                cv("1", 1000, "C", "T"),
                cv("1", 2000, "A", "G"),
                cv("Y", 3000, "C", "T"),
                cv("1", 4000, "A", "T", vid="4002"),
                cv("1", 5000, "A", "C", vid="5001"),
                cv("1", 5000, "A", "T", vid="5002"),
                cv("1", 6000, "G", "A"),
                cv("1", 7000, "G", "A"),
                cv("1", 8000, "G", "A"),
                cv("MT", 9000, "A", "G"),
                cv("1", 10000, "C", "T"),
                cv("1", 11000, "C", "T", gene="BRCA1"),
            ]
        )
        result = self.run_local(genome, clinvar)
        payload = result["payload"]
        hits = [(hit["chrom"], hit["pos"], hit["alt"]) for hit in payload["hits"]]
        self.assertEqual(
            hits,
            [
                ("1", 1000, "T"),
                ("1", 2000, "G"),
                ("1", 4000, "T"),
                ("1", 5000, "C"),
                ("1", 5000, "T"),
                ("1", 11000, "T"),
                ("Y", 3000, "T"),
                ("MT", 9000, "G"),
            ],
        )
        by_key = {(hit["chrom"], hit["pos"], hit["alt"]): hit for hit in payload["hits"]}
        first = by_key[("1", 1000, "T")]
        self.assertEqual(first["zygosity"], "heterozygous")
        self.assertEqual(first["genotype"], "0/1")
        self.assertEqual(first["depth"], 31)
        self.assertEqual(first["alt_reads"], 14)
        self.assertEqual(first["total_reads"], 31)
        self.assertEqual(first["gq"], 99)
        self.assertEqual(first["qual"], 99)
        self.assertEqual(first["filter"], "PASS")
        self.assertEqual(first["area"], "Other")
        self.assertEqual(by_key[("1", 2000, "G")]["zygosity"], "homozygous")
        self.assertEqual(by_key[("Y", 3000, "T")]["zygosity"], "hemizygous")
        second_alt = by_key[("1", 4000, "T")]
        self.assertEqual(second_alt["genotype"], "0/2")
        self.assertEqual(second_alt["zygosity"], "heterozygous")
        self.assertEqual(second_alt["alt_reads"], 9)
        self.assertEqual(second_alt["total_reads"], 15)
        self.assertNotIn(("1", 4000, "C"), by_key)
        self.assertEqual(by_key[("1", 5000, "C")]["zygosity"], "compound with another allele")
        self.assertEqual(by_key[("1", 5000, "T")]["zygosity"], "compound with another allele")
        self.assertEqual(by_key[("1", 11000, "T")]["gene"], "BRCA1")
        self.assertEqual(by_key[("1", 11000, "T")]["area"], "Hereditary cancer")
        seen = ids_of(payload, "hits") + ids_of(payload, "filtered_matches")
        self.assertNotIn("6000", seen)
        self.assertNotIn("7000", seen)
        filtered = {(hit["pos"], hit["filter"]) for hit in payload["filtered_matches"]}
        self.assertEqual(filtered, {(8000, "LowQual"), (10000, "FT=q20")})
        counts = payload["metadata"]["counts"]
        self.assertEqual(counts["genome_records_scanned"], 11)
        self.assertEqual(counts["no_calls"], 1)
        self.assertEqual(counts["incomplete_calls"], 0)
        self.assertEqual(counts["hits"], 8)
        self.assertEqual(counts["filtered_matches"], 2)
        self.assertEqual(counts["skipped_indels"], 0)
        self.assertEqual(counts["allele_mismatches"], 0)
        self.assertIn("## Matches that failed the sequencer's quality filter (2)", result["md"])
        self.assertIn("LowQual", result["md"])
        self.assertEqual(payload["metadata"]["sample"], "SAMPLE")
        self.assertIn("SAMPLE (first sample in the file)", result["md"])

    def test_sample_choice(self):
        genome = genome_vcf(
            [gline("1", 1000, "C", "T", "0/0", trailing="0/1")],
            samples=("S1", "S2"),
        )
        clinvar = clinvar_vcf([cv("1", 1000, "C", "T")])
        default = self.run_local(genome, clinvar)
        self.assertEqual(default["payload"]["hits"], [])
        self.assertEqual(default["payload"]["metadata"]["sample"], "S1")
        chosen = self.run_local(genome, clinvar, extra=["--sample", "S2"])
        self.assertEqual(len(chosen["payload"]["hits"]), 1)
        self.assertEqual(chosen["payload"]["hits"][0]["genotype"], "0/1")
        self.assertIn("S2 (named with --sample)", chosen["md"])
        root = self.temp()
        path = root / "multi.vcf"
        path.write_text(genome, encoding="utf-8")
        clin = root / "clinvar.vcf"
        clin.write_text(clinvar, encoding="utf-8")
        code, _out, err = run_main(
            ["run", "--genome", str(path), "--out-dir", str(root / "out"), "--clinvar", str(clin), "--sample", "NOPE"]
        )
        self.assertEqual(code, 1)
        self.assertIn("NOPE", err)
        self.assertIn("S1", err)
        self.assertIn("S2", err)

    def test_partly_missing_genotypes_stay_hits_but_are_not_heterozygous(self):
        genotypes = ["1/.", "./1", "1|.", ".|1", "0/.", "./.", "0/1"]
        genome = genome_vcf(
            [gline("1", 1000 + index * 1000, "C", "T", gt) for index, gt in enumerate(genotypes)]
        )
        clinvar = clinvar_vcf(
            [cv("1", 1000 + index * 1000, "C", "T", vid=str(1000 + index * 1000)) for index in range(len(genotypes))]
        )
        result = self.run_local(genome, clinvar)
        by_gt = {hit["genotype"]: hit for hit in result["payload"]["hits"]}
        self.assertEqual(set(by_gt), {"1/.", "./1", "1|.", ".|1", "0/1"})
        for genotype in ("1/.", "./1", "1|.", ".|1"):
            self.assertEqual(by_gt[genotype]["zygosity"], "unknown (one allele not called)")
            self.assertTrue(by_gt[genotype]["incomplete_call"])
            self.assertIn(
                f"Genotype: {genotype} (unknown (one allele not called))",
                result["md"],
            )
        self.assertEqual(by_gt["0/1"]["zygosity"], "heterozygous")
        self.assertFalse(by_gt["0/1"]["incomplete_call"])
        self.assertIn("Genotype: 0/1 (heterozygous)", result["md"])
        flag_lines = [line for line in result["md"].splitlines() if "INCOMPLETE CALL" in line]
        self.assertEqual(len(flag_lines), 4)
        for line in flag_lines:
            self.assertTrue(line.startswith("- **"))
            self.assertIn("\u2014 INCOMPLETE CALL", line)
        counts = result["payload"]["metadata"]["counts"]
        self.assertEqual(counts["hits"], 5)
        self.assertEqual(counts["no_calls"], 1)
        self.assertEqual(counts["incomplete_calls"], 5)
        self.assertIn("- Incomplete calls: 5", result["md"])
        self.assertNotIn("Genotype: 0/.", result["md"])
        self.assertNotIn("Genotype: ./.", result["md"])


class TestClasses(TempTest):
    def test_selection_is_applied_to_a_real_run(self):
        rows = [
            (1000, "Pathogenic", "GENEA", "1000"),
            (2000, "Likely_pathogenic", "GENEA", "2000"),
            (3000, "Pathogenic/Likely_pathogenic", "GENEA", "3000"),
            (4000, "Pathogenic,_low_penetrance", "GENEA", "4000"),
            (5000, "Benign", "GENEA", "5000"),
            (6000, "Uncertain_significance", "GENEA", "6000"),
            (7000, "Conflicting_classifications_of_pathogenicity", "GENEA", "7000"),
            (8000, "Conflicting_classifications_of_pathogenicity|risk_factor", "GENEA", "8000"),
            (9000, "drug_response", "BRCA1", "9000"),
            (10000, "protective", "GENEA", "10000"),
        ]
        genome = genome_vcf([gline("1", pos, "C", "T", "0/1") for pos, _sig, _gene, _vid in rows])
        clinvar = clinvar_vcf(
            [cv("1", pos, "C", "T", clnsig=sig, gene=gene, vid=vid) for pos, sig, gene, vid in rows]
        )
        result = self.run_local(genome, clinvar)
        found = {hit["pos"]: hit for hit in result["payload"]["hits"]}
        self.assertEqual(set(found), {1000, 2000, 3000, 4000, 8000, 9000, 10000})
        self.assertEqual(found[3000]["base_classes"], ["Pathogenic", "Likely_pathogenic"])
        self.assertEqual(found[4000]["base_classes"], ["Pathogenic"])
        self.assertEqual(found[4000]["classification"], "Pathogenic,_low_penetrance")
        self.assertTrue(found[8000]["conflicting"])
        self.assertIn("risk_factor", found[8000]["base_classes"])
        self.assertIn("CONFLICTING SUBMISSIONS", result["md"])
        self.assertEqual(found[9000]["area"], "Drug response")
        self.assertEqual(found[9000]["gene"], "BRCA1")
        self.assertEqual(found[10000]["area"], "Other")
        counts = result["payload"]["metadata"]["counts"]["by_class"]
        self.assertEqual(counts["Pathogenic"], 3)
        self.assertEqual(counts["Likely_pathogenic"], 2)
        self.assertEqual(counts["risk_factor"], 1)
        self.assertEqual(counts["drug_response"], 1)
        self.assertEqual(counts["protective"], 1)
        self.assertEqual(counts["association"], 0)
        self.assertNotIn("Benign", counts)

    def test_classes_flag_limits_the_run(self):
        genome = genome_vcf(
            [
                gline("1", 1000, "C", "T", "0/1"),
                gline("1", 2000, "C", "T", "0/1"),
            ]
        )
        clinvar = clinvar_vcf(
            [
                cv("1", 1000, "C", "T", clnsig="Pathogenic"),
                cv("1", 2000, "C", "T", clnsig="drug_response"),
            ]
        )
        result = self.run_local(genome, clinvar, extra=["--classes", "Pathogenic"])
        self.assertEqual([hit["pos"] for hit in result["payload"]["hits"]], [1000])
        self.assertEqual(result["payload"]["metadata"]["selected_classes"], ["Pathogenic"])

    def test_display_labels_map_to_clinvar_terms(self):
        labels = {
            "Pathogenic": "Pathogenic",
            "pathogenic": "Pathogenic",
            "Likely pathogenic": "Likely_pathogenic",
            "likely_pathogenic": "Likely_pathogenic",
            "risk factor": "risk_factor",
            "drug response": "drug_response",
            "association": "association",
            "protective": "protective",
            "confers sensitivity": "confers_sensitivity",
            "Uncertain significance": "Uncertain_significance",
            "Likely benign": "Likely_benign",
            "Benign": "Benign",
            "Likely risk allele": "Likely_risk_allele",
            "Uncertain risk allele": "Uncertain_risk_allele",
            "Established risk allele": "Established_risk_allele",
            "Affects": "Affects",
            "other": "other",
            "not provided": "not_provided",
        }
        for label, canonical in labels.items():
            with self.subTest(label=label):
                self.assertEqual(gc.parse_classes(label), [canonical])
        self.assertEqual(
            gc.parse_classes("Likely pathogenic, likely_pathogenic, risk factor"),
            ["Likely_pathogenic", "risk_factor"],
        )
        genome = genome_vcf(
            [
                gline("1", 1000, "C", "T", "0/1"),
                gline("1", 2000, "C", "T", "0/1"),
                gline("1", 3000, "C", "T", "0/1"),
            ]
        )
        clinvar = clinvar_vcf(
            [
                cv("1", 1000, "C", "T", clnsig="Pathogenic"),
                cv("1", 2000, "C", "T", clnsig="Likely_pathogenic"),
                cv("1", 3000, "C", "T", clnsig="risk_factor"),
            ]
        )
        result = self.run_local(
            genome,
            clinvar,
            extra=["--classes", "Likely pathogenic, risk factor"],
        )
        self.assertEqual([hit["pos"] for hit in result["payload"]["hits"]], [2000, 3000])
        self.assertEqual(
            result["payload"]["metadata"]["selected_classes"],
            ["Likely_pathogenic", "risk_factor"],
        )

    def test_unknown_class_is_rejected(self):
        with self.assertRaises(gc.GenomeCheckError) as caught:
            gc.parse_classes("Pathogenic, made_up")
        message = str(caught.exception)
        self.assertIn("made_up", message)
        for term in gc.ACCEPTED_CLASSES:
            self.assertIn(term, message)
        root = self.temp()
        genome = root / "genome.vcf"
        genome.write_text(genome_vcf([gline("1", 1000, "C", "T", "0/1")]), encoding="utf-8")
        code, _stdout, err = run_main(
            [
                "run",
                "--genome",
                str(genome),
                "--out-dir",
                str(root / "out"),
                "--classes",
                "not_a_class",
            ]
        )
        self.assertEqual(code, 1)
        self.assertIn("not_a_class", err)
        self.assertIn("Likely_pathogenic", err)
        self.assertIn("not_provided", err)
        self.assertIn("Established_risk_allele", err)
        self.assertFalse((root / "out").exists())


class TestMatchChip(TempTest):
    def test_23andme(self):
        genome = chip_23(
            [
                "rs1\t1\t1000\tAG",
                "rs2\t1\t2000\tAA",
                "rs3\tX\t3000\tA",
                "rs4\t1\t4000\t--",
                "rs5\t1\t5000\tII",
                "rs6\t1\t5100\tDD",
                "rs7\t1\t5200\tDI",
                "rs8\t1\t7000\tGG",
                "rs9\t1\t8000\tAA",
            ]
        )
        clinvar = clinvar_vcf(
            [
                cv("1", 1000, "C", "G"),
                cv("1", 2000, "C", "A"),
                cv("X", 3000, "C", "A"),
                cv("1", 4000, "C", "T"),
                cv("1", 7000, "A", "T"),
                cv("1", 8000, "A", "AT"),
            ]
        )
        result = self.run_local(genome, clinvar, genome_name="chip.txt")
        by_pos = {hit["pos"]: hit for hit in result["payload"]["hits"]}
        self.assertEqual(set(by_pos), {1000, 2000, 3000})
        self.assertEqual(by_pos[1000]["zygosity"], "heterozygous")
        self.assertEqual(by_pos[1000]["genotype"], "AG")
        self.assertEqual(by_pos[2000]["zygosity"], "homozygous")
        self.assertEqual(by_pos[3000]["zygosity"], "hemizygous")
        self.assertEqual(by_pos[3000]["chrom"], "X")
        self.assertIsNone(by_pos[1000]["depth"])
        self.assertIsNone(by_pos[1000]["filter"])
        counts = result["payload"]["metadata"]["counts"]
        self.assertEqual(counts["genome_records_scanned"], 9)
        self.assertEqual(counts["no_calls"], 1)
        self.assertEqual(counts["incomplete_calls"], 0)
        self.assertEqual(counts["skipped_indels"], 3)
        self.assertEqual(counts["allele_mismatches"], 1)
        self.assertEqual(counts["hits"], 3)
        self.assertIn("\u2013", result["md"])
        self.assertIn("none (chip file, no sample name)", result["md"])
        self.assertIn(CHIP, header_body(result["md"]))

    def test_ancestry_chromosome_codes(self):
        genome = chip_ancestry(
            [
                "rsX\t23\t1000\tA\tG",
                "rsP\t25\t1500\tT\tT",
                "rsM\t26\t2000\tA\tA",
                "rs0\t1\t3000\t0\t0",
                "rsI\t1\t4000\tI\tI",
            ]
        )
        clinvar = clinvar_vcf(
            [
                cv("X", 1000, "C", "G"),
                cv("X", 1500, "C", "T"),
                cv("MT", 2000, "G", "A"),
                cv("1", 3000, "C", "T"),
            ]
        )
        result = self.run_local(genome, clinvar, genome_name="ancestry.txt")
        found = {(hit["chrom"], hit["pos"], hit["zygosity"]) for hit in result["payload"]["hits"]}
        self.assertEqual(
            found,
            {("X", 1000, "heterozygous"), ("X", 1500, "homozygous"), ("MT", 2000, "homozygous")},
        )
        counts = result["payload"]["metadata"]["counts"]
        self.assertEqual(counts["no_calls"], 1)
        self.assertEqual(counts["incomplete_calls"], 0)
        self.assertEqual(counts["skipped_indels"], 1)
        self.assertEqual(counts["allele_mismatches"], 0)
        self.assertEqual(counts["genome_records_scanned"], 5)
        self.assertIn(CHIP, result["md"])


class TestReport(TempTest):
    def test_exact_block_header_and_forbidden_words(self):
        genome = genome_vcf(
            [gline("chr1", 1000, "C", "T", "0/1", qual="99", info="DP=10", fmt="GT:DP:GQ:AD", sample="0/1:31:99:17,14")]
        )
        clinvar = clinvar_vcf([cv("1", 1000, "C", "T", vid="12345", rs="000000", condition="Example_syndrome")])
        result = self.run_local(genome, clinvar)
        self.assertEqual(result["md"].count(EXACT_BLOCK), 1)
        self.assertIn("## Other (1)", result["md"])
        self.assertIn("## Matches that failed the sequencer's quality filter (0)", result["md"])
        # The star legend must contain this phrase. The 2-star hit must not.
        self.assertIn("marked LOW CONFIDENCE", result["md"])
        for line in result["md"].splitlines():
            if line.startswith("- **"):
                self.assertNotIn("LOW CONFIDENCE", line)
        self.assertNotIn("genotyping-chip", result["md"])

    def test_star_lines_and_low_confidence(self):
        specs = [
            (1000, "GENEA", REV4),
            (2000, "GENEB", REV3),
            (3000, "GENEC", REV2),
            (4000, "GENED", REV1),
            (5000, "GENEE", REV0),
            (6000, "GENEF", "not_a_real_status"),
        ]
        genome = genome_vcf([gline("1", pos, "C", "T", "0/1") for pos, _gene, _rev in specs])
        clinvar = clinvar_vcf(
            [cv("1", pos, "C", "T", gene=gene, rev=rev) for pos, gene, rev in specs]
        )
        result = self.run_local(genome, clinvar)
        markdown = result["md"]
        self.assertIn("\u2605\u2605\u2605\u2605 (4/4) practice guideline", markdown)
        self.assertIn("\u2605\u2605\u2605\u2606 (3/4) reviewed by expert panel", markdown)
        self.assertIn(
            "\u2605\u2605\u2606\u2606 (2/4) criteria provided, multiple submitters, no conflicts",
            markdown,
        )
        self.assertIn("\u2605\u2606\u2606\u2606 (1/4) criteria provided, single submitter", markdown)
        self.assertIn("\u2606\u2606\u2606\u2606 (0/4) no assertion criteria provided", markdown)
        self.assertIn("\u2606\u2606\u2606\u2606 (0/4) not a real status", markdown)
        for line in markdown.splitlines():
            if not line.startswith("- **"):
                continue
            if "(4/4)" in line or "(3/4)" in line or "(2/4)" in line:
                self.assertNotIn("LOW CONFIDENCE", line)
            if "(1/4)" in line or "(0/4)" in line:
                self.assertIn("LOW CONFIDENCE", line)
        # Three low-confidence hit lines, plus the same words once in the star legend.
        self.assertEqual(markdown.count("LOW CONFIDENCE"), 4)
        flags = {hit["pos"]: hit["review_status_unrecognised"] for hit in result["payload"]["hits"]}
        self.assertEqual(flags, {1000: False, 2000: False, 3000: False, 4000: False, 5000: False, 6000: True})
        self.assertEqual(result["payload"]["metadata"]["counts"]["low_confidence"], 3)
        self.assertEqual(result["payload"]["metadata"]["counts"]["by_stars"]["0"], 2)

    def test_long_condition_is_cut_in_the_report_only(self):
        genome = genome_vcf([gline("1", 1000, "C", "T", "0/1")])
        clinvar = clinvar_vcf([cv("1", 1000, "C", "T", condition="N" * 350)])
        result = self.run_local(genome, clinvar)
        self.assertIn(("N" * 300) + "\u2026", result["md"])
        self.assertNotIn("N" * 301, result["md"])
        self.assertEqual(len(result["payload"]["hits"][0]["condition"]), 350)


class TestDownload(TempTest):
    def clinvar_site(self, text, *, bad_md5=False):
        root = self.temp()
        folder = root / "vcf_GRCh37"
        folder.mkdir()
        raw = gzip.compress(text.encode("utf-8"))
        (folder / "clinvar.vcf.gz").write_bytes(raw)
        digest = "0" * 32 if bad_md5 else hashlib.md5(raw).hexdigest()
        (folder / "clinvar.vcf.gz.md5").write_text(digest + "\n", encoding="utf-8")
        return root, raw, hashlib.md5(raw).hexdigest()

    def test_file_url_success_mismatch_reuse_and_conflict(self):
        text = clinvar_vcf([cv("1", 1000, "C", "T")])
        genome = genome_vcf([gline("1", 1000, "C", "T", "0/1")])
        site, raw, digest = self.clinvar_site(text)
        work = self.temp()
        genome_path = work / "genome.vcf"
        genome_path.write_text(genome, encoding="utf-8")
        before = snap(genome_path)
        out = work / "out"
        clinvar_dir = work / "clinvar"
        code, _stdout, err = run_main(
            [
                "run",
                "--genome",
                str(genome_path),
                "--out-dir",
                str(out),
                "--clinvar-dir",
                str(clinvar_dir),
                "--clinvar-base-url",
                site.as_uri() + "/",
            ]
        )
        self.assertEqual(code, 0, err)
        self.assertEqual(snap(genome_path), before)
        final = clinvar_dir / "clinvar_GRCh37_20240115.vcf.gz"
        self.assertTrue(final.is_file())
        self.assertTrue((clinvar_dir / "clinvar_GRCh37_20240115.vcf.gz.md5").is_file())
        self.assertEqual(list(clinvar_dir.glob(".genome-check-partial-*")), [])
        payload, markdown, md_path, _json_path, _diffs = load_outputs(out)
        self.assertEqual(payload["metadata"]["clinvar_md5"], digest)
        self.assertEqual(payload["metadata"]["clinvar_release"], "2024-01-15")
        self.assertTrue(payload["metadata"]["clinvar_source"].startswith("file:"))
        self.assertTrue(payload["metadata"]["clinvar_download_time"].endswith("Z"))
        self.assertEqual(md_path.name, f"genome-check-{date.today().isoformat()}-clinvar20240115.md")
        self.assertEqual(len(payload["hits"]), 1)
        self.assert_report_contract(markdown, chip=False)

        bad_site, _raw, _digest = self.clinvar_site(text, bad_md5=True)
        bad_dir = work / "bad"
        before_bad = snap(genome_path)
        code, _stdout, err = run_main(
            [
                "run",
                "--genome",
                str(genome_path),
                "--out-dir",
                str(work / "bad-out"),
                "--clinvar-dir",
                str(bad_dir),
                "--clinvar-base-url",
                bad_site.as_uri() + "/",
            ]
        )
        self.assertEqual(code, 1)
        self.assertIn("md5", err.lower())
        self.assertEqual(snap(genome_path), before_bad)
        self.assertEqual(list(bad_dir.glob(".genome-check-partial-*")), [])
        self.assertEqual(list(bad_dir.glob("clinvar_*")), [])

        reuse_dir = work / "reuse"
        reuse_dir.mkdir()
        seeded = reuse_dir / "clinvar_GRCh37_20240115.vcf.gz"
        seeded.write_bytes(raw)
        sidecar = reuse_dir / "clinvar_GRCh37_20240115.vcf.gz.md5"
        sidecar.write_text(digest + "\n", encoding="utf-8")
        os.utime(seeded, (1_700_000_000, 1_700_000_000))
        os.utime(sidecar, (1_700_000_000, 1_700_000_000))
        seeded_snap = snap(seeded)
        sidecar_snap = snap(sidecar)
        code, _stdout, err = run_main(
            [
                "run",
                "--genome",
                str(genome_path),
                "--out-dir",
                str(work / "reuse-out"),
                "--clinvar-dir",
                str(reuse_dir),
                "--clinvar-base-url",
                site.as_uri() + "/",
            ]
        )
        self.assertEqual(code, 0, err)
        self.assertEqual(snap(seeded), seeded_snap)
        self.assertEqual(snap(sidecar), sidecar_snap)
        self.assertEqual(list(reuse_dir.glob(".genome-check-partial-*")), [])
        reused, _md, _md_path, _json_path, _diffs = load_outputs(work / "reuse-out")
        self.assertTrue(reused["metadata"]["clinvar_reused"])
        self.assertEqual(reused["metadata"]["clinvar_md5"], digest)

        clash_dir = work / "clash"
        clash_dir.mkdir()
        other = clash_dir / "clinvar_GRCh37_20240115.vcf.gz"
        other_bytes = b"not-the-download"
        other.write_bytes(other_bytes)
        other_md5 = clash_dir / "clinvar_GRCh37_20240115.vcf.gz.md5"
        other_md5.write_text(hashlib.md5(other_bytes).hexdigest() + "\n", encoding="utf-8")
        os.utime(other, (1_700_000_000, 1_700_000_000))
        other_snap = snap(other)
        code, _stdout, err = run_main(
            [
                "run",
                "--genome",
                str(genome_path),
                "--out-dir",
                str(work / "clash-out"),
                "--clinvar-dir",
                str(clash_dir),
                "--clinvar-base-url",
                site.as_uri() + "/",
            ]
        )
        self.assertEqual(code, 1)
        self.assertIn("md5", err.lower())
        self.assertEqual(snap(other), other_snap)
        self.assertEqual(list(clash_dir.glob(".genome-check-partial-*")), [])
        self.assertFalse((work / "clash-out").exists())

    def test_local_clinvar_build_must_match(self):
        root = self.temp()
        genome = root / "genome.vcf"
        clinvar = root / "clinvar.vcf"
        genome.write_text(genome_vcf([gline("1", 1000, "C", "T", "0/1")]), encoding="utf-8")
        clinvar.write_text(clinvar_vcf([cv("1", 1000, "C", "T")], build="GRCh38"), encoding="utf-8")
        before = snap(genome)
        out = root / "out"
        code, _stdout, err = run_main(
            ["run", "--genome", str(genome), "--out-dir", str(out), "--clinvar", str(clinvar)]
        )
        self.assertEqual(code, 1)
        self.assertIn("GRCh38", err)
        self.assertIn("GRCh37", err)
        self.assertEqual(snap(genome), before)
        self.assertFalse(out.exists())

    def test_link_failure_copies_without_replacing(self):
        root = self.temp()
        real_link = gc.os.link
        real_rename = gc.os.rename
        real_lexists = gc.os.path.lexists

        def boom(*_args, **_kwargs):
            raise OSError("cross-device link")

        def rename_bomb(*_args, **_kwargs):
            raise AssertionError("os.rename must not be used to publish ClinVar")

        gc.os.link = boom
        gc.os.rename = rename_bomb
        try:
            tmp = root / "partial.vcf.gz"
            final = root / "clinvar_GRCh37_20240115.vcf.gz"
            payload = b"clinvar-bytes-v1"
            tmp.write_bytes(payload)
            gc._publish_new(str(tmp), str(final))
            self.assertFalse(tmp.exists())
            self.assertEqual(final.read_bytes(), payload)

            tmp_existing = root / "partial-existing.vcf.gz"
            final_existing = root / "already.vcf.gz"
            tmp_existing.write_bytes(b"new-bytes")
            final_existing.write_bytes(b"old-bytes")
            with self.assertRaises(gc.GenomeCheckError) as caught:
                gc._publish_new(str(tmp_existing), str(final_existing))
            self.assertIn("already here", str(caught.exception))
            self.assertEqual(final_existing.read_bytes(), b"old-bytes")

            calls = {"n": 0}

            def hide_first(path):
                calls["n"] += 1
                if calls["n"] == 1:
                    return False
                return real_lexists(path)

            gc.os.path.lexists = hide_first
            tmp_race = root / "partial-race.vcf.gz"
            final_race = root / "race.vcf.gz"
            tmp_race.write_bytes(b"race-bytes")
            final_race.write_bytes(b"kept-bytes")
            with self.assertRaises(gc.GenomeCheckError) as caught_race:
                gc._publish_new(str(tmp_race), str(final_race))
            self.assertIn("already here", str(caught_race.exception))
            self.assertEqual(final_race.read_bytes(), b"kept-bytes")
            self.assertFalse(tmp_race.exists())
        finally:
            gc.os.link = real_link
            gc.os.rename = real_rename
            gc.os.path.lexists = real_lexists


class TestNeverOverwrite(TempTest):
    def test_second_run_and_genome_path_collision(self):
        root = self.temp()
        genome = root / "genome.vcf"
        clinvar = root / "clinvar.vcf"
        genome.write_text(genome_vcf([gline("1", 1000, "C", "T", "0/1")]), encoding="utf-8")
        clinvar.write_text(clinvar_vcf([cv("1", 1000, "C", "T")]), encoding="utf-8")
        out = root / "out"
        code, _stdout, err = run_main(
            ["run", "--genome", str(genome), "--out-dir", str(out), "--clinvar", str(clinvar)]
        )
        self.assertEqual(code, 0, err)
        _payload, _markdown, _md_path, json_path, _diffs = load_outputs(out)
        original = json_path.read_bytes()
        before = snap(genome)
        code, _stdout, err = run_main(
            ["run", "--genome", str(genome), "--out-dir", str(out), "--clinvar", str(clinvar)]
        )
        self.assertEqual(code, 1)
        self.assertIn(json_path.name, err)
        self.assertIn("never overwrites", err)
        self.assertEqual(json_path.read_bytes(), original)
        self.assertEqual(snap(genome), before)

        clash = self.temp()
        today = date.today().isoformat()
        clash_out = clash / "out"
        clash_out.mkdir()
        named = clash_out / f"genome-check-{today}-clinvar20240115.md"
        named.write_text(genome_vcf([gline("1", 1000, "C", "T", "0/1")]), encoding="utf-8")
        clin = clash / "clinvar.vcf"
        clin.write_text(clinvar_vcf([cv("1", 1000, "C", "T")]), encoding="utf-8")
        before_named = snap(named)
        code, _stdout, err = run_main(
            ["run", "--genome", str(named), "--out-dir", str(clash_out), "--clinvar", str(clin)]
        )
        self.assertEqual(code, 1)
        self.assertIn("genome", err.lower())
        self.assertEqual(snap(named), before_named)
        self.assertFalse((clash_out / f"genome-check-{today}-clinvar20240115.json").exists())

        code, _stdout, err = run_main(
            ["run", "--genome", str(named), "--out-dir", str(named), "--clinvar", str(clin)]
        )
        self.assertEqual(code, 1)
        self.assertIn("genome", err.lower())
        self.assertEqual(snap(named), before_named)


class TestDiff(TempTest):
    def wrap(self, hits, *, genome, release, run_date, lookup=None, include_lookup=False):
        payload = {
            "tool": "genome-check",
            "tool_version": "0.1.0",
            "metadata": {
                "genome_file": genome,
                "file_type": "Sequencing VCF",
                "clinvar_release": release,
                "run_date": run_date,
            },
            "hits": hits,
            "filtered_matches": [],
        }
        if include_lookup:
            payload["previous_lookup"] = {} if lookup is None else lookup
        return payload

    def hit(self, **kwargs):
        base = {
            "chrom": "1",
            "pos": 1000,
            "ref": "C",
            "alt": "T",
            "gene": "GENEA",
            "classification": "Pathogenic",
            "classification_display": "Pathogenic",
            "stars": 2,
            "review_status": "criteria provided, multiple submitters, no conflicts",
            "genotype": "0/1",
            "zygosity": "heterozygous",
            "area": "Other",
        }
        base.update(kwargs)
        return base

    def test_diff_sections(self):
        old = self.wrap(
            [
                self.hit(pos=1000, gene="GENEA"),
                self.hit(pos=3000, ref="G", alt="T", gene="GENEC"),
                self.hit(pos=4000, ref="A", alt="G", gene="GENED"),
                self.hit(
                    pos=5000,
                    ref="A",
                    alt="C",
                    gene="GENEE",
                    stars=1,
                    review_status="criteria provided, single submitter",
                ),
                self.hit(pos=6000, ref="G", alt="A", gene="GENEF", genotype="0/1", area="Other"),
                self.hit(pos=7000, ref="C", alt="A", gene="GENEG"),
            ],
            genome="earlier.vcf",
            release="2024-01-15",
            run_date="2026-01-02",
        )
        new = self.wrap(
            [
                self.hit(pos=2000, ref="A", alt="G", gene="GENEB"),
                self.hit(pos=4000, ref="A", alt="G", gene="GENED", classification="Likely_pathogenic", classification_display="Likely pathogenic"),
                self.hit(pos=5000, ref="A", alt="C", gene="GENEE", stars=2, review_status="criteria provided, multiple submitters, no conflicts"),
                self.hit(pos=6000, ref="G", alt="A", gene="GENEF", genotype="1/1", zygosity="homozygous", area="Hereditary cancer"),
                self.hit(pos=7000, ref="C", alt="A", gene="GENEG"),
            ],
            genome="later.vcf",
            release="2024-02-15",
            run_date="2026-02-02",
            include_lookup=True,
            lookup={"1:1000:C:T": {"clnsig": "Benign", "clnrevstat": REV1, "stars": 1}},
        )
        root = self.temp()
        old_path = root / "old.json"
        new_path = root / "new.json"
        out = root / "changes.md"
        old_path.write_text(json.dumps(old), encoding="utf-8")
        new_path.write_text(json.dumps(new), encoding="utf-8")
        code, _stdout, err = run_main(["diff", str(old_path), str(new_path), "--out", str(out)])
        self.assertEqual(code, 0, err)
        markdown = out.read_text(encoding="utf-8")
        self.assert_diff_contract(markdown)
        self.assertIn("now classified: Benign, 1/4", markdown)
        self.assertIn("current classification not looked up", markdown)
        self.assertNotIn("no longer in this ClinVar release", markdown)
        self.assertNotIn("now listed at", markdown)
        self.assertNotIn("is not in this release", markdown)
        self.assertIn("GENEB", markdown)
        self.assertIn("Pathogenic \u2192 Likely_pathogenic", markdown)
        self.assertIn("1/4 \u2192 2/4", markdown)
        self.assertIn("criteria provided, single submitter", markdown)
        self.assertIn("criteria provided, multiple submitters, no conflicts", markdown)
        self.assertIn("Flag: genotype or area differs for the same variant key.", markdown)
        self.assertIn("genome file names differ (earlier.vcf and later.vcf)", markdown)
        self.assertIn("- New hits: 1", markdown)
        self.assertIn("- Dropped hits: 2", markdown)
        self.assertIn("- Reclassified: 1", markdown)
        self.assertIn("- Review-status changes: 1", markdown)
        self.assertIn("- Genotype or area changes: 1", markdown)
        self.assertIn("2024-01-15", markdown)
        self.assertIn("2024-02-15", markdown)

        bare_old = self.wrap([self.hit()], genome="same.vcf", release="2024-01-15", run_date="2026-01-02")
        bare_new = self.wrap([], genome="same.vcf", release="2024-02-15", run_date="2026-02-02")
        bare_out = root / "bare.md"
        (root / "bare-old.json").write_text(json.dumps(bare_old), encoding="utf-8")
        (root / "bare-new.json").write_text(json.dumps(bare_new), encoding="utf-8")
        code, _stdout, err = run_main(
            ["diff", str(root / "bare-old.json"), str(root / "bare-new.json"), "--out", str(bare_out)]
        )
        self.assertEqual(code, 0, err)
        bare = bare_out.read_text(encoding="utf-8")
        self.assertIn("current classification not looked up", bare)
        self.assertNotIn("now listed at", bare)
        self.assertNotIn("is not in this release", bare)
        self.assertNotIn("genome file names differ", bare)
        self.assert_diff_contract(bare)

        code, _stdout, err = run_main(
            ["diff", str(old_path), str(new_path), "--out", str(out)]
        )
        self.assertEqual(code, 1)
        self.assertIn("never overwrites", err)
        self.assertIn("now classified: Benign, 1/4", out.read_text(encoding="utf-8"))

    def test_run_previous_writes_a_diff(self):
        genome = genome_vcf(
            [
                gline("1", 1000, "C", "T", "0/1"),
                gline("1", 2000, "A", "G", "0/1"),
                gline("1", 3000, "G", "T", "0/1"),
            ]
        )
        old_clinvar = clinvar_vcf(
            [
                cv("1", 1000, "C", "T", gene="GENEA", clnsig="Pathogenic"),
                cv("1", 3000, "G", "T", gene="GENEC", clnsig="Pathogenic"),
            ],
            filedate="20240115",
        )
        new_clinvar = clinvar_vcf(
            [
                cv("1", 1000, "C", "T", gene="GENEA", clnsig="Benign", rev=REV1),
                cv("1", 2000, "A", "G", gene="GENEB", clnsig="Pathogenic"),
            ],
            filedate="20240215",
        )
        first = self.run_local(genome, old_clinvar)
        self.assertEqual(sorted(hit["gene"] for hit in first["payload"]["hits"]), ["GENEA", "GENEC"])
        root = first["root"]
        second_out = root / "out2"
        second_clinvar = root / "clinvar-new.vcf"
        second_clinvar.write_text(new_clinvar, encoding="utf-8")
        before = snap(first["genome"])
        code, _stdout, err = run_main(
            [
                "run",
                "--genome",
                str(first["genome"]),
                "--out-dir",
                str(second_out),
                "--clinvar",
                str(second_clinvar),
                "--previous",
                str(first["json_path"]),
            ]
        )
        self.assertEqual(code, 0, err)
        self.assertEqual(snap(first["genome"]), before)
        payload, _markdown, _md_path, _json_path, diffs = load_outputs(second_out)
        self.assertEqual([hit["gene"] for hit in payload["hits"]], ["GENEB"])
        looked = payload["previous_lookup"]["1:1000:C:T"]
        self.assertTrue(looked["looked_up"])
        self.assertTrue(looked["found"])
        self.assertEqual(looked["clnsig"], "Benign")
        self.assertEqual(looked["stars"], 1)
        missing = payload["previous_lookup"]["1:3000:G:T"]
        self.assertEqual(missing["looked_up"], True)
        self.assertEqual(missing["found"], False)
        self.assertNotIn("clnsig", missing)
        self.assertEqual(len(diffs), 1)
        self.assertTrue(diffs[0].name.endswith("-diff.md"))
        self.assertIn("20240215", diffs[0].name)
        diff = diffs[0].read_text(encoding="utf-8")
        self.assert_diff_contract(diff)
        self.assertIn("now classified: Benign, 1/4", diff)
        self.assertIn("no longer in this ClinVar release at this exact position and alleles", diff)
        self.assertIn("GENEB", diff)
        self.assertNotIn("genome file names differ", diff)
        self.assertNotIn("genotyping-chip", diff)

    def _section(self, markdown: str, heading: str) -> str:
        start = markdown.index(heading)
        rest = markdown[start + len(heading):]
        nxt = rest.find("\n## ")
        return rest if nxt < 0 else rest[:nxt]

    def test_secondary_clinvar_records_are_compared(self):
        genome = genome_vcf([gline("1", 1000, "C", "T", "0/1")])
        old_cv = clinvar_vcf(
            [
                cv("1", 1000, "C", "T", vid="111", clnsig="Pathogenic", rev=REV3, gene="GENEA"),
                cv("1", 1000, "C", "T", vid="222", clnsig="risk_factor", rev=REV1, gene="GENEA"),
            ],
            filedate="20240115",
        )
        new_cv = clinvar_vcf(
            [
                cv("1", 1000, "C", "T", vid="111", clnsig="Pathogenic", rev=REV3, gene="GENEA"),
                cv("1", 1000, "C", "T", vid="222", clnsig="Likely_pathogenic", rev=REV2, gene="GENEA"),
            ],
            filedate="20240215",
        )
        old = self.run_local(genome, old_cv)
        new = self.run_local(genome, new_cv)
        self.assertEqual(old["payload"]["hits"][0]["classification"], "Pathogenic")
        self.assertEqual(new["payload"]["hits"][0]["classification"], "Pathogenic")
        self.assertEqual(old["payload"]["hits"][0]["stars"], 3)
        self.assertEqual(new["payload"]["hits"][0]["stars"], 3)
        out = self.temp() / "secondary.md"
        code, _stdout, err = run_main(
            ["diff", str(old["json_path"]), str(new["json_path"]), "--out", str(out)]
        )
        self.assertEqual(code, 0, err)
        text = out.read_text(encoding="utf-8")
        self.assert_diff_contract(text)
        self.assertIn("- Reclassified: 1", text)
        self.assertIn("- Review-status changes: 1", text)
        self.assertIn("- ClinVar records added: 0", text)
        self.assertIn("- ClinVar records removed: 0", text)
        reclass = self._section(text, "## Reclassified")
        stars = self._section(text, "## Review-status changes")
        self.assertIn("222", reclass)
        self.assertNotIn("111", reclass)
        self.assertIn("risk_factor \u2192 Likely_pathogenic", reclass)
        self.assertEqual(reclass.count("\u2192"), 1)
        self.assertIn("222", stars)
        self.assertNotIn("111", stars)
        self.assertIn("1/4 \u2192 2/4", stars)
        self.assertIn("criteria provided, single submitter", stars)
        self.assertIn("criteria provided, multiple submitters, no conflicts", stars)

    def test_added_and_removed_clinvar_records(self):
        genome = genome_vcf([gline("1", 1000, "C", "T", "0/1")])
        old_cv = clinvar_vcf(
            [
                cv("1", 1000, "C", "T", vid="111", clnsig="Pathogenic", rev=REV3),
                cv("1", 1000, "C", "T", vid="333", clnsig="risk_factor", rev=REV1),
            ],
            filedate="20240115",
        )
        new_cv = clinvar_vcf(
            [
                cv("1", 1000, "C", "T", vid="111", clnsig="Pathogenic", rev=REV3),
                cv("1", 1000, "C", "T", vid="444", clnsig="association", rev=REV2),
            ],
            filedate="20240215",
        )
        old = self.run_local(genome, old_cv)
        new = self.run_local(genome, new_cv)
        out = self.temp() / "records.md"
        code, _stdout, err = run_main(
            ["diff", str(old["json_path"]), str(new["json_path"]), "--out", str(out)]
        )
        self.assertEqual(code, 0, err)
        text = out.read_text(encoding="utf-8")
        self.assertIn("- Reclassified: 0", text)
        self.assertIn("- Review-status changes: 0", text)
        self.assertIn("- ClinVar records added: 1", text)
        self.assertIn("- ClinVar records removed: 1", text)
        added = self._section(text, "## ClinVar records added")
        removed = self._section(text, "## ClinVar records removed")
        self.assertIn("ClinVar 444", added)
        self.assertIn("association", added)
        self.assertIn("ClinVar 333", removed)
        self.assertIn("risk_factor", removed)
        self.assertNotIn("111", added)
        self.assertNotIn("111", removed)

    def test_not_looked_up_when_the_previous_run_lacked_the_key(self):
        genome = genome_vcf(
            [
                gline("1", 1000, "C", "T", "0/1"),
                gline("1", 3000, "G", "A", "0/1"),
            ]
        )
        report_a = self.run_local(
            genome,
            clinvar_vcf(
                [
                    cv("1", 1000, "C", "T", vid="1000"),
                    cv("1", 3000, "G", "A", vid="3000"),
                ],
                filedate="20240115",
            ),
        )
        report_b = self.run_local(
            genome,
            clinvar_vcf([cv("1", 1000, "C", "T", vid="1000")], filedate="20240215"),
        )
        report_c = self.run_local(
            genome,
            clinvar_vcf([cv("1", 4000, "A", "C", vid="4000")], filedate="20240315"),
            extra=["--previous", str(report_b["json_path"])],
        )
        self.assertEqual(set(report_c["payload"]["previous_lookup"]), {"1:1000:C:T"})
        self.assertTrue(report_c["payload"]["previous_lookup"]["1:1000:C:T"]["looked_up"])
        self.assertFalse(report_c["payload"]["previous_lookup"]["1:1000:C:T"]["found"])
        self.assertNotIn("1:3000:G:A", report_c["payload"]["previous_lookup"])
        out = self.temp() / "a-vs-c.md"
        code, _stdout, err = run_main(
            ["diff", str(report_a["json_path"]), str(report_c["json_path"]), "--out", str(out)]
        )
        self.assertEqual(code, 0, err)
        text = out.read_text(encoding="utf-8")
        self.assert_diff_contract(text)
        matched = [line for line in text.splitlines() if "1:3000:G:A" in line]
        self.assertTrue(matched)
        for line in matched:
            self.assertIn("not looked up", line)
            self.assertNotIn("no longer in this ClinVar release", line)
        self.assertIn(
            "no longer in this ClinVar release at this exact position and alleles",
            text,
        )

    def test_dropped_hit_explains_each_variation_id(self):
        genome = genome_vcf(
            [
                gline("1", 1000, "C", "T", "0/1"),
                gline("1", 2000, "A", "G", "0/1"),
            ]
        )
        old_cv = clinvar_vcf(
            [
                cv("1", 1000, "C", "T", vid="111", clnsig="Pathogenic", gene="GENEA"),
                cv("1", 2000, "A", "G", vid="222", clnsig="Pathogenic", gene="GENEB"),
            ],
            filedate="20240115",
        )
        new_cv = clinvar_vcf(
            [cv("1", 9000, "C", "T", vid="111", clnsig="Benign", rev=REV1, gene="GENEA")],
            filedate="20240215",
        )
        first = self.run_local(genome, old_cv)
        second = self.run_local(genome, new_cv, extra=["--previous", str(first["json_path"])])
        lookup = second["payload"]["previous_lookup"]
        moved = lookup["1:1000:C:T"]
        gone = lookup["1:2000:A:G"]
        self.assertTrue(moved["looked_up"])
        self.assertFalse(moved["found"])
        self.assertEqual(
            moved["ids"]["111"],
            {
                "found": True,
                "chrom": "1",
                "pos": 9000,
                "ref": "C",
                "alt": "T",
                "clnsig": "Benign",
                "stars": 1,
            },
        )
        self.assertTrue(gone["looked_up"])
        self.assertFalse(gone["found"])
        self.assertEqual(gone["ids"]["222"], {"found": False})
        diff = second["diffs"][0].read_text(encoding="utf-8")
        self.assert_diff_contract(diff)
        self.assertIn(
            "ClinVar record 111 now listed at 1:9000 C>T, classified Benign, 1/4",
            diff,
        )
        self.assertIn(
            "ClinVar record 222 is not in this release (removed, merged or withdrawn by ClinVar)",
            diff,
        )
        self.assertIn("no longer in this ClinVar release at this exact position and alleles", diff)

        plain_new = json.loads(second["json_path"].read_text(encoding="utf-8"))
        for entry in plain_new["previous_lookup"].values():
            entry.pop("ids", None)
        root = self.temp()
        old_path = root / "old.json"
        new_path = root / "new.json"
        plain_out = root / "plain.md"
        old_path.write_text(first["json_path"].read_text(encoding="utf-8"), encoding="utf-8")
        new_path.write_text(json.dumps(plain_new), encoding="utf-8")
        code, _stdout, err = run_main(
            ["diff", str(old_path), str(new_path), "--out", str(plain_out)]
        )
        self.assertEqual(code, 0, err)
        plain = plain_out.read_text(encoding="utf-8")
        self.assertNotIn("now listed at", plain)
        self.assertNotIn("is not in this release", plain)
        self.assertIn("no longer in this ClinVar release at this exact position and alleles", plain)

    def test_diff_explains_only_ids_from_the_dropped_hit(self):
        genome = genome_vcf([gline("1", 1000, "C", "T", "0/1")])
        report_a = self.run_local(
            genome,
            clinvar_vcf(
                [cv("1", 1000, "C", "T", vid="111", clnsig="Pathogenic", gene="GENEA")],
                filedate="20240115",
            ),
        )
        report_b = self.run_local(
            genome,
            clinvar_vcf(
                [cv("1", 1000, "C", "T", vid="222", clnsig="Pathogenic", gene="GENEA")],
                filedate="20240215",
            ),
        )
        report_c = self.run_local(
            genome,
            clinvar_vcf(
                [cv("1", 9000, "C", "T", vid="222", clnsig="Benign", rev=REV1, gene="GENEA")],
                filedate="20240315",
            ),
            extra=["--previous", str(report_b["json_path"])],
        )
        hit_a = report_a["payload"]["hits"][0]
        hit_b = report_b["payload"]["hits"][0]
        self.assertEqual(hit_a["clinvar_records"][0]["clinvar_ids"], ["111"])
        self.assertEqual(hit_b["clinvar_records"][0]["clinvar_ids"], ["222"])
        saved = report_c["payload"]["previous_lookup"]["1:1000:C:T"]["ids"]
        self.assertEqual(set(saved), {"222"})
        self.assertTrue(saved["222"]["found"])

        wrong = self.temp() / "a-vs-c.md"
        code, _stdout, err = run_main(
            ["diff", str(report_a["json_path"]), str(report_c["json_path"]), "--out", str(wrong)]
        )
        self.assertEqual(code, 0, err)
        text = wrong.read_text(encoding="utf-8")
        self.assert_diff_contract(text)
        self.assertNotIn("222", text)
        self.assertNotIn("111", text)
        self.assertNotIn("now listed at", text)
        self.assertNotIn("is not in this release", text)
        self.assertIn(
            "no longer in this ClinVar release at this exact position and alleles",
            text,
        )

        right = self.temp() / "b-vs-c.md"
        code, _stdout, err = run_main(
            ["diff", str(report_b["json_path"]), str(report_c["json_path"]), "--out", str(right)]
        )
        self.assertEqual(code, 0, err)
        positive = right.read_text(encoding="utf-8")
        self.assert_diff_contract(positive)
        self.assertIn(
            "ClinVar record 222 now listed at 1:9000 C>T, classified Benign, 1/4",
            positive,
        )
        self.assertNotIn("111", positive)


if __name__ == "__main__":
    unittest.main()
