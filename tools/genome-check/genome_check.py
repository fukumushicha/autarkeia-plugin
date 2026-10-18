#!/usr/bin/env python3
"""Compare a genome file with ClinVar on this computer.

The genome file is only read. The report says what ClinVar records and how
many stars ClinVar gives that record. It does not give advice.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
import zipfile
import zlib
from datetime import date, datetime, timezone

TOOL_NAME = "genome-check"
TOOL_VERSION = "0.2.0"

# NCBI's public ClinVar VCF. Tests point this at a file:// directory.
CLINVAR_BASE_URL = "https://ftp.ncbi.nlm.nih.gov/pub/clinvar/"

DEFAULT_CLASSES = [
    "Pathogenic",
    "Likely_pathogenic",
    "risk_factor",
    "drug_response",
    "association",
    "protective",
    "confers_sensitivity",
]

# Every base term --classes accepts. The spelling here is ClinVar's own.
ACCEPTED_CLASSES = [
    "Pathogenic",
    "Likely_pathogenic",
    "risk_factor",
    "drug_response",
    "association",
    "protective",
    "confers_sensitivity",
    "Uncertain_significance",
    "Likely_benign",
    "Benign",
    "Likely_risk_allele",
    "Uncertain_risk_allele",
    "Established_risk_allele",
    "Affects",
    "other",
    "not_provided",
]

HEADER_RESEARCH = (
    "**Research-grade and unconfirmed. Not for medical decisions.** "
    "This report compares a raw genome file with ClinVar, a public database of "
    "what genetic variants are known to mean. Raw consumer and research genome "
    "data contain errors, and a ClinVar classification is not a diagnosis. "
    "Nothing here has been confirmed by a clinical laboratory. ClinVar states "
    "that its data are not intended for direct diagnostic use or medical "
    "decision-making without review by a genetics professional."
)

HEADER_CHIP = (
    "**This is a genotyping-chip file, not sequencing.** Chips read a fixed "
    "set of preselected positions and are unreliable for rare variants: in a "
    "2018 study, a clinical laboratory re-tested variants reported in consumer "
    "raw data and found that 40% were false positives (Tandy-Connor et al., "
    "*Genetics in Medicine* 2018, https://doi.org/10.1038/gim.2018.38). Treat "
    'every rare or "Pathogenic" call from this file as unverified. A position '
    "missing from the chip says nothing about that variant."
)

STAR_LEGEND = (
    "ClinVar rates its confidence in each classification from 0 to 4 stars: "
    "0 = no assertion criteria or no classification provided; "
    "1 = a single submitter, or submitters who disagree; "
    "2 = several submitters who agree; "
    "3 = reviewed by an expert panel; "
    "4 = a practice guideline. "
    "Hits with 0 or 1 star are marked LOW CONFIDENCE."
)
STAR_LEGEND_URL = "https://www.ncbi.nlm.nih.gov/clinvar/docs/review_status/"

METHOD_TEXT = (
    "Exact match on chromosome, position, reference and alternate allele. "
    "Variants written differently in the two files (for example indels not "
    "left-aligned) are not matched. A variant absent from the genome file is "
    "not evidence the person does not carry it, especially for chip files and "
    "for VCFs that list only variant sites. ClinVar germline classifications "
    "only; somatic and oncogenicity classifications are ignored. The report "
    "contains no recommendations by design."
)

# Chip files do not carry the reference allele, so they do not use METHOD_TEXT.
METHOD_TEXT_CHIP = (
    "Chip files: only single-letter ClinVar variants can be matched; a hit means "
    "the chip called ClinVar's alternate letter at that position. The chip does not "
    "report the reference letter, so the reference allele is not checked. "
    "Variants written differently in the two files (for example indels not "
    "left-aligned) are not matched. A variant absent from the genome file is "
    "not evidence the person does not carry it, especially for chip files and "
    "for VCFs that list only variant sites. ClinVar germline classifications "
    "only; somatic and oncogenicity classifications are ignored. The report "
    "contains no recommendations by design."
)

INCOMPLETE_ZYGOSITY = "unknown (one allele not called)"

# Contig length of chromosome 1 decides the build when it is one of these,
# and it wins when the header text names a different build.
CHR1_LENGTH_TO_BUILD = {
    249250621: "GRCh37",
    248956422: "GRCh38",
}

CONFLICT_MARKERS = (
    "Conflicting_classifications_of_pathogenicity",
    "Conflicting_interpretations_of_pathogenicity",
)

# Exact ClinVar CLNREVSTAT values. Anything else is 0 stars and is flagged.
REVIEW_STARS = {
    "practice_guideline": 4,
    "reviewed_by_expert_panel": 3,
    "criteria_provided,_multiple_submitters,_no_conflicts": 2,
    "criteria_provided,_single_submitter": 1,
    "criteria_provided,_conflicting_classifications": 1,
    "criteria_provided,_conflicting_interpretations": 1,
    "no_assertion_criteria_provided": 0,
    "no_assertion_provided": 0,
    "no_classification_provided": 0,
    "no_classification_for_the_single_variant": 0,
    "no_classifications_from_unflagged_records": 0,
    "no_interpretation_for_the_single_variant": 0,
    "": 0,
}

CLASS_RANK = {
    "Pathogenic": 0,
    "Likely pathogenic": 1,
    "risk factor": 2,
    "drug response": 3,
    "association": 4,
    "confers sensitivity": 5,
    "protective": 6,
}

# First area in this list wins when a gene is looked up.
AREA_TABLE = [
    (
        "Hereditary cancer",
        """
        BRCA1 BRCA2 PALB2 ATM CHEK2 BARD1 RAD51C RAD51D MLH1 MSH2 MSH6 PMS2
        EPCAM APC MUTYH STK11 SMAD4 BMPR1A PTEN TP53 CDH1 VHL RET MEN1 NF1 NF2
        BAP1 BLM BRIP1 FH FLCN HOXB13 MITF MAX NTHL1 POLD1 POLE PRKAR1A PTCH1
        SDHA SDHB SDHC SDHD SDHAF2 SUFU TMEM127 TSC1 TSC2 WT1 RB1 DICER1
        """,
    ),
    (
        "Heart rhythm and heart muscle",
        """
        ACTC1 MYBPC3 MYH7 MYL2 MYL3 PRKAG2 TNNI3 TNNT2 TPM1 BAG3 DES FLNC LMNA
        RBM20 TNNC1 TTN DSC2 DSG2 DSP JUP PKP2 TMEM43 CASQ2 RYR2 TRDN CALM1
        CALM2 CALM3 KCNH2 KCNQ1 SCN5A KCNE1 KCNE2 ANK2 KCNJ2 PITX2 ZFHX3 KCNN3
        SHOX2 KCNA5 GJA5 MYL4 NPPA
        """,
    ),
    (
        "Aorta and connective tissue",
        """
        ACTA2 COL3A1 FBN1 MYH11 SMAD3 TGFB2 TGFBR1 TGFBR2 FBN2 EFEMP2 MFAP5
        PRKG1 LOX FOXE3 COL1A1 COL1A2 COL5A1 COL5A2 COL2A1 COL11A1
        """,
    ),
    (
        "Cholesterol and lipids",
        """
        LDLR APOB PCSK9 LDLRAP1 ABCG5 ABCG8 STAP1 LIPA APOE LPA LPL APOA5 APOC3
        """,
    ),
    (
        "Diabetes and metabolism",
        """
        HNF1A HNF4A HNF1B GCK ABCC8 KCNJ11 INS PDX1 WFS1 PAX4 NEUROD1 BLK KLF11
        CEL
        """,
    ),
    ("Iron", "HFE HJV HAMP TFR2 SLC40A1 FTL FTH1 TF"),
    ("Blood clotting", "F2 F5 PROC PROS1 SERPINC1 F11 F13A1 F7"),
    (
        "Brain and nerves",
        """
        APP PSEN1 PSEN2 MAPT GRN C9orf72 SNCA LRRK2 PARK7 PINK1 PRKN GBA GBA1
        HTT ATXN1 ATXN2 ATXN3 ATXN7 TBP SOD1 TARDBP FUS VCP
        """,
    ),
    (
        "Drug response",
        """
        CYP2D6 CYP2C19 CYP2C9 CYP3A4 CYP3A5 CYP1A2 CYP2B6 CYP4F2 CYP2A6 TPMT
        NUDT15 DPYD UGT1A1 G6PD VKORC1 SLCO1B1 ABCB1 ABCG2 HLA-A HLA-B IFNL3
        IFNL4 NAT2 RYR1 CACNA1S
        """,
    ),
    ("Kidney", "PKD1 PKD2 PKHD1 COL4A3 COL4A4 COL4A5 UMOD MUC1"),
    (
        "Eyes and hearing",
        "GJB2 MYO7A USH2A ABCA4 RPE65 RHO RPGR RP1 BEST1 PRPH2 CHM",
    ),
    ("Liver", "SERPINA1 ATP7B PNPLA3 TM6SF2 MBOAT7"),
    ("Inflammation and immune", "MEFV TNFRSF1A NLRP3 MVK PSTPIP1"),
]

CONDITION_RULES = [
    (
        "Cancer (other)",
        ["cancer", "tumor", "neoplasm", "carcinoma", "leukemia", "lymphoma", "melanoma"],
    ),
    (
        "Heart (other)",
        ["cardi", "arrhythm", "qt syndrome", "brugada", "fibrillation"],
    ),
    (
        "Metabolism (other)",
        ["diabet", "insulin", "glucose", "obesity", "lipid", "cholesterol"],
    ),
    (
        "Brain and nerves (other)",
        ["alzheim", "parkinson", "huntington", "ataxia", "sclerosis", "dementia"],
    ),
    ("Kidney (other)", ["kidney", "renal", "polycystic"]),
    ("Eyes and hearing (other)", ["deaf", "hearing", "vision", "blind", "retin"]),
]

GENE_AREA: dict[str, str] = {}
AREA_ORDER: dict[str, int] = {}
for _i, (_area, _genes) in enumerate(AREA_TABLE):
    AREA_ORDER[_area] = _i
    for _gene in _genes.split():
        # C9orf72 is the one mixed-case symbol. Lookup is case-insensitive.
        GENE_AREA.setdefault(_gene.upper(), _area)

REPORT_AREA_ORDER = [area for area, _genes in AREA_TABLE] + [
    "Cancer (other)",
    "Heart (other)",
    "Metabolism (other)",
    "Brain and nerves (other)",
    "Kidney (other)",
    "Eyes and hearing (other)",
    "Other",
]

EM = "\u2014"
MID = "\u00b7"
EN = "\u2013"
ELLIPSIS = "\u2026"
STAR_ON = "\u2605"
STAR_OFF = "\u2606"

LOW_PENETRANCE_SUFFIX = ",_low_penetrance"
PARTIAL_PREFIX = ".genome-check-partial-"


class GenomeCheckError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def progress(message: str) -> None:
    print(message, file=sys.stderr)


def _remove(path: str) -> None:
    try:
        os.remove(path)
    except FileNotFoundError:
        pass
    except OSError:
        pass


def paths_equal(a: str, b: str) -> bool:
    return os.path.normcase(os.path.realpath(a)) == os.path.normcase(os.path.realpath(b))


def variant_key(chrom: str, pos: int, ref: str, alt: str) -> str:
    return f"{chrom}:{pos}:{ref}:{alt}"


def normalize_chrom(chrom: str) -> str:
    text = chrom.strip()
    if text.lower().startswith("chr"):
        text = text[3:]
    upper = text.upper()
    if upper == "M":
        return "MT"
    if text == "23":
        return "X"
    if text == "24":
        return "Y"
    if text == "25":
        return "X"
    if text == "26":
        return "MT"
    if upper in ("X", "Y", "MT"):
        return upper
    return text


def chrom_sort_key(chrom: str) -> tuple:
    if chrom.isdigit():
        return (0, int(chrom), "")
    special = {"X": 23, "Y": 24, "MT": 25}
    if chrom in special:
        return (1, special[chrom], chrom)
    return (2, 999, chrom)


def hit_sort_tuple(hit: dict) -> tuple:
    return (
        chrom_sort_key(str(hit["chrom"])),
        int(hit["pos"]),
        str(hit["ref"]),
        str(hit["alt"]),
    )


def star_glyph(stars: int) -> str:
    n = max(0, min(4, int(stars)))
    return STAR_ON * n + STAR_OFF * (4 - n)


def class_display(token: str) -> str:
    return token.replace("_", " ")


def clnsig_display(raw: str) -> str:
    return raw.replace("_", " ")


def class_rank(terms: list[str]) -> int:
    ranks = []
    for term in terms:
        rank = CLASS_RANK.get(class_display(term))
        if rank is not None:
            ranks.append(rank)
    return min(ranks) if ranks else 99


def condition_display(clndn: str) -> str:
    if not clndn or clndn == ".":
        return ""
    text = urllib.parse.unquote(clndn).replace("_", " ").replace("|", "; ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def truncate_text(text: str, limit: int = 300) -> str:
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + ELLIPSIS


def base_terms(clnsig: str) -> list[str]:
    """Split a CLNSIG value into base terms.

    Split on '|' and then on '/'. A trailing ',_low_penetrance' is removed
    from the base term. The original string is kept separately for display.
    """
    if not clnsig or clnsig == ".":
        return []
    terms: list[str] = []
    for piece in clnsig.split("|"):
        piece = piece.strip()
        if piece.endswith(LOW_PENETRANCE_SUFFIX):
            piece = piece[: -len(LOW_PENETRANCE_SUFFIX)]
        for sub in piece.split("/"):
            sub = sub.strip()
            if sub.endswith(LOW_PENETRANCE_SUFFIX):
                sub = sub[: -len(LOW_PENETRANCE_SUFFIX)]
            if sub and sub not in terms:
                terms.append(sub)
    return terms


def is_conflicting_clnsig(clnsig: str) -> bool:
    return any(marker in clnsig for marker in CONFLICT_MARKERS)


def classification_decision(clnsig: str, selected: set[str]) -> dict:
    terms = base_terms(clnsig)
    conflicting = is_conflicting_clnsig(clnsig)
    # A conflicting record is kept only when some other component is selected.
    selected_terms = [term for term in terms if term in selected]
    return {
        "terms": terms,
        "selected_terms": selected_terms,
        "selected": bool(selected_terms),
        "conflicting": conflicting,
    }


def review_status_info(raw: str | None) -> dict:
    if raw is None or raw == ".":
        raw = ""
    else:
        raw = raw.strip()
    if raw in REVIEW_STARS:
        stars = REVIEW_STARS[raw]
        unrecognised = False
    else:
        stars = 0
        unrecognised = True
    return {
        "raw": raw,
        "stars": stars,
        "unrecognised": unrecognised,
        "display": review_status_display(raw),
    }


def review_status_display(raw: str) -> str:
    """Underscores become spaces. A leading comma-space is removed.

    The words are ClinVar's own. They are not rewritten.
    """
    text = raw.replace("_", " ").strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"^,\s*", "", text)
    return text.strip()


def assign_area(terms: list[str], genes: list[str], condition: str) -> str:
    # A drug_response classification outranks the gene table.
    if "drug_response" in terms:
        return "Drug response"
    found: list[str] = []
    for gene in genes:
        area = GENE_AREA.get(gene.upper())
        if area and area not in found:
            found.append(area)
    if found:
        return min(found, key=lambda area: AREA_ORDER[area])
    text = condition_display(condition).lower()
    for area, keys in CONDITION_RULES:
        if any(key in text for key in keys):
            return area
    return "Other"


def parse_gt(gt: str) -> list[int | None]:
    alleles: list[int | None] = []
    for part in re.split(r"[/|]", gt):
        if part in ("", "."):
            alleles.append(None)
        else:
            try:
                alleles.append(int(part))
            except ValueError:
                alleles.append(None)
    return alleles


def zygosity_for_gt(alleles: list[int | None], allele_index: int) -> str:
    """Zygosity of one allele index inside a VCF genotype.

    1/2 is compound, because the other allele is a different alternate.
    0/1 is heterozygous. 1/1 is homozygous. A single '1' is hemizygous.
    1/. and the other one-missing forms stay hits, but the zygosity is unknown.
    """
    copies = sum(1 for allele in alleles if allele == allele_index)
    ploidy = len(alleles)
    # A partly missing genotype is not heterozygous: one allele was not called.
    if copies >= 1 and any(allele is None for allele in alleles):
        return INCOMPLETE_ZYGOSITY
    other_alt = any(
        allele not in (None, 0, allele_index) for allele in alleles
    )
    if other_alt and copies >= 1:
        return "compound with another allele"
    if copies == 1 and ploidy == 1:
        return "hemizygous"
    if copies == ploidy and ploidy >= 2:
        return "homozygous"
    if copies == 1 and ploidy == 2:
        return "heterozygous"
    return "compound with another allele"


def zygosity_from_copies(copies: int, ploidy: int) -> str:
    if copies == 1 and ploidy == 1:
        return "hemizygous"
    if copies == ploidy and ploidy >= 2:
        return "homozygous"
    if copies == 1 and ploidy == 2:
        return "heterozygous"
    return "compound with another allele"


def text_build_label(text: str) -> str | None:
    """Return GRCh37, GRCh38, NCBI36, 'ambiguous', or None."""
    low = text.lower()
    found: set[str] = set()
    if re.search(r"\bgrch38\b", low) or re.search(r"\bhg38\b", low):
        found.add("GRCh38")
    if re.search(r"\bbuild[\s_-]*38\b", low):
        found.add("GRCh38")
    if (
        re.search(r"\bgrch37\b", low)
        or re.search(r"\bhg19\b", low)
        or re.search(r"\bhs37d5\b", low)
        or re.search(r"\bb37\b", low)
        or re.search(r"\bbuild[\s_-]*37\b", low)
    ):
        found.add("GRCh37")
    if (
        re.search(r"\bncbi36\b", low)
        or re.search(r"\bhg18\b", low)
        or re.search(r"\bb36\b", low)
        or re.search(r"\bbuild[\s_-]*36\b", low)
    ):
        found.add("NCBI36")
    modern = found & {"GRCh37", "GRCh38"}
    if len(modern) > 1:
        return "ambiguous"
    if len(modern) == 1:
        return next(iter(modern))
    if "NCBI36" in found:
        return "NCBI36"
    return None


def decide_build(
    *,
    contig_length: int | None,
    text_label: str | None,
    kind: str,
    override: str | None,
) -> tuple[str, str]:
    if override:
        if override not in ("GRCh37", "GRCh38"):
            raise GenomeCheckError("The --build value must be GRCh37 or GRCh38.")
        return override, "build given by user"
    contig_build = CHR1_LENGTH_TO_BUILD.get(contig_length) if contig_length else None
    if text_label == "ambiguous":
        if contig_build:
            return contig_build, (
                f"chromosome 1 contig length {contig_length} ({contig_build}) "
                "disagreed with the reference text (it names both GRCh37 and "
                "GRCh38); the contig length was used"
            )
        raise GenomeCheckError(
            "The file names both GRCh37 and GRCh38, so the build is not clear. "
            "Run again with --build GRCh37 or --build GRCh38."
        )
    if contig_build and text_label in ("GRCh37", "GRCh38", "NCBI36") and text_label != contig_build:
        shown = "build 36" if text_label == "NCBI36" else text_label
        return contig_build, (
            f"chromosome 1 contig length {contig_length} ({contig_build}) "
            f"disagreed with the reference text ({shown}); the contig length was used"
        )
    if contig_build:
        return contig_build, f"chromosome 1 contig length {contig_length}"
    if text_label == "NCBI36":
        raise GenomeCheckError(
            "This file uses reference build 36 (NCBI36 / hg18). "
            "This tool does not support that build. It reads GRCh37 and GRCh38 only."
        )
    if text_label in ("GRCh37", "GRCh38"):
        noun = "reference text" if kind == "vcf" else "header text"
        return text_label, f"{noun} ({text_label})"
    raise GenomeCheckError(
        "Could not tell whether this genome uses GRCh37 or GRCh38. "
        "Run again with --build GRCh37 or --build GRCh38."
    )


def parse_contig_fields(line: str) -> dict[str, str]:
    match = re.match(r"##contig=<(.+)>$", line.strip())
    if not match:
        return {}
    fields: dict[str, str] = {}
    for key, val in re.findall(r'([A-Za-z_][A-Za-z0-9_]*)=("[^"]*"|[^,>]*)', match.group(1)):
        fields[key] = val.strip().strip('"')
    return fields


def header_build_evidence(header_lines: list[str]) -> tuple[int | None, str]:
    length: int | None = None
    bits: list[str] = []
    for line in header_lines:
        if line.startswith("##reference=") or line.startswith("##assembly="):
            bits.append(line.split("=", 1)[1])
        if not line.startswith("##contig=<"):
            continue
        fields = parse_contig_fields(line)
        if fields.get("ID") not in ("1", "chr1"):
            continue
        if "assembly" in fields:
            bits.append(fields["assembly"])
        if length is None and "length" in fields:
            try:
                length = int(fields["length"])
            except ValueError:
                length = None
    return length, "\n".join(bits)


def parse_info(info: str) -> dict[str, str]:
    if not info or info == ".":
        return {}
    parsed: dict[str, str] = {}
    for part in info.split(";"):
        if not part:
            continue
        if "=" in part:
            key, value = part.split("=", 1)
            parsed[key] = urllib.parse.unquote(value)
        else:
            parsed[part] = "True"
    return parsed


def parse_format(fmt: str, sample: str) -> dict[str, str]:
    if not fmt or fmt == ".":
        return {}
    keys = fmt.split(":")
    values = sample.split(":") if sample else []
    return {key: (values[i] if i < len(values) else "") for i, key in enumerate(keys)}


def parse_number(value: str | None):
    if value is None:
        return None
    text = str(value).strip()
    if text in ("", "."):
        return None
    if re.fullmatch(r"-?\d+", text):
        return int(text)
    try:
        return float(text)
    except ValueError:
        return None


def parse_genes(geneinfo: str) -> list[str]:
    if not geneinfo or geneinfo == ".":
        return []
    genes: list[str] = []
    for part in geneinfo.split("|"):
        symbol = part.split(":")[0].strip()
        if symbol and symbol not in genes:
            genes.append(symbol)
    return genes


def parse_rs(rs_field: str) -> list[str]:
    if not rs_field or rs_field == ".":
        return []
    found: list[str] = []
    for part in re.split(r"[|,]", rs_field):
        token = part.strip()
        if not token or token == ".":
            continue
        if token.lower().startswith("rs"):
            norm = "rs" + token[2:]
        else:
            norm = "rs" + token
        if norm not in found:
            found.append(norm)
    return found


def parse_ids(id_field: str) -> list[str]:
    if not id_field or id_field == ".":
        return []
    return [part for part in id_field.split(";") if part and part != "."]


def parse_mc(mc_field: str) -> list[str]:
    if not mc_field or mc_field == ".":
        return []
    names: list[str] = []
    for part in mc_field.split(","):
        name = part.split("|", 1)[1].strip() if "|" in part else part.strip()
        if name and name not in names:
            names.append(name.replace("_", " "))
    return names


def clinvar_variation_url(vid: str) -> str | None:
    if vid.isdigit():
        return f"https://www.ncbi.nlm.nih.gov/clinvar/variation/{vid}/"
    return None


def file_md5(path: str) -> str:
    digest = hashlib.md5()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_md5_text(text: str) -> str:
    match = re.search(r"\b([0-9a-fA-F]{32})\b", text)
    if not match:
        raise GenomeCheckError("The ClinVar md5 sidecar does not contain an md5 hash.")
    return match.group(1).lower()


def compact_filedate(raw: str) -> str:
    digits = re.sub(r"\D", "", raw or "")
    if len(digits) == 8:
        return digits
    raise GenomeCheckError(
        "The ClinVar file has no usable ##fileDate header, so the release cannot be named."
    )


def display_filedate(compact: str) -> str:
    if len(compact) == 8 and compact.isdigit():
        return f"{compact[0:4]}-{compact[4:6]}-{compact[6:8]}"
    return compact


def read_vcf_header_lines(path: str) -> list[str]:
    lines: list[str] = []
    with open_text(path) as handle:
        for line in handle:
            line = line.rstrip("\r\n")
            if line.startswith("\ufeff"):
                line = line[1:]
            if not line:
                continue
            if line.startswith("#"):
                lines.append(line)
                continue
            break
    return lines


def filedate_from_header(header_lines: list[str]) -> str:
    for line in header_lines:
        if line.startswith("##fileDate="):
            return compact_filedate(line.split("=", 1)[1].strip())
    raise GenomeCheckError(
        "The ClinVar file has no ##fileDate header, so the release cannot be named."
    )


def assert_clinvar_reference(header_lines: list[str], genome_build: str) -> None:
    ref_lines = [line for line in header_lines if line.startswith("##reference=")]
    if not ref_lines:
        raise GenomeCheckError(
            "ClinVar file has no ##reference header, so it cannot be checked "
            f"against the genome build {genome_build}."
        )
    label = text_build_label("\n".join(ref_lines))
    if label == genome_build:
        return
    shown = label if label in ("GRCh37", "GRCh38") else "unrecognised"
    raise GenomeCheckError(
        f"ClinVar ##reference build ({shown}) does not match the genome build ({genome_build})."
    )


def clinvar_vcf_url(base_url: str, build: str) -> str:
    return base_url.rstrip("/") + f"/vcf_{build}/clinvar.vcf.gz"


def _stream_url(url: str, dest: str) -> str:
    digest = hashlib.md5()
    try:
        with urllib.request.urlopen(url) as response, open(dest, "wb") as out:
            while True:
                chunk = response.read(1 << 20)
                if not chunk:
                    break
                digest.update(chunk)
                out.write(chunk)
    except Exception:
        _remove(dest)
        raise
    return digest.hexdigest()


def _already_here(final: str) -> GenomeCheckError:
    return GenomeCheckError(
        f"A ClinVar file is already here, so it was not overwritten: {final}"
    )


def _copy_exclusive(tmp: str, final: str) -> None:
    """Copy tmp to a new file. Exclusive create refuses an existing final."""
    try:
        dest = open(final, "xb")
    except FileExistsError as exc:
        _remove(tmp)
        raise _already_here(final) from exc
    try:
        with dest, open(tmp, "rb") as source:
            while True:
                chunk = source.read(1 << 20)
                if not chunk:
                    break
                dest.write(chunk)
    except Exception:
        _remove(final)
        raise
    _remove(tmp)


def _publish_new(tmp: str, final: str) -> None:
    """Put tmp at final. Never replace a file that is already there.

    os.rename replaces on Unix, so a failed os.link falls back to an
    exclusive copy instead.
    """
    if os.path.lexists(final):
        raise _already_here(final)
    try:
        os.link(tmp, final)
    except FileExistsError as exc:
        raise _already_here(final) from exc
    except OSError:
        _copy_exclusive(tmp, final)
        return
    os.remove(tmp)


def acquire_clinvar(
    *,
    build: str,
    dest_dir: str,
    base_url: str,
    genome_path: str,
) -> dict:
    os.makedirs(dest_dir, exist_ok=True)
    vcf_url = clinvar_vcf_url(base_url, build)
    md5_url = vcf_url + ".md5"
    token = f"{os.getpid()}-{uuid.uuid4().hex}"
    tmp_vcf = os.path.join(dest_dir, f"{PARTIAL_PREFIX}{token}.vcf.gz")
    tmp_md5 = tmp_vcf + ".md5"
    progress(f"Downloading ClinVar for {build}.")
    try:
        try:
            actual = _stream_url(vcf_url, tmp_vcf)
            _stream_url(md5_url, tmp_md5)
        except (urllib.error.URLError, OSError) as exc:
            raise GenomeCheckError(f"Could not download ClinVar from {vcf_url}: {exc}") from exc
        with open(tmp_md5, "r", encoding="utf-8", errors="replace") as handle:
            sidecar_text = handle.read()
        try:
            expected = parse_md5_text(sidecar_text)
        except GenomeCheckError:
            _remove(tmp_vcf)
            _remove(tmp_md5)
            raise
        if actual != expected:
            _remove(tmp_vcf)
            _remove(tmp_md5)
            raise GenomeCheckError(
                "ClinVar download failed the md5 check. The temporary file was deleted. "
                f"Expected {expected}, got {actual}."
            )
        header = read_vcf_header_lines(tmp_vcf)
        release = filedate_from_header(header)
        final = os.path.join(dest_dir, f"clinvar_{build}_{release}.vcf.gz")
        final_md5 = final + ".md5"
        if paths_equal(final, genome_path) or paths_equal(final_md5, genome_path):
            raise GenomeCheckError(
                f"Refusing to write a ClinVar file onto the genome file: {genome_path}"
            )
        if os.path.lexists(final) or os.path.lexists(final_md5):
            if not (os.path.isfile(final) and os.path.isfile(final_md5)):
                raise GenomeCheckError(
                    "A ClinVar file is already here but its md5 sidecar is missing, "
                    f"so it was not overwritten: {final}"
                )
            existing_hash = file_md5(final)
            try:
                sidecar_hash = parse_md5_text(open(final_md5, "r", encoding="utf-8", errors="replace").read())
            except GenomeCheckError as exc:
                raise GenomeCheckError(
                    f"A ClinVar file is already here and its md5 sidecar cannot be read: {final_md5}"
                ) from exc
            if existing_hash == actual == sidecar_hash == expected:
                progress(f"Reusing the ClinVar file already on disk: {os.path.basename(final)}")
                return {
                    "clinvar_release_raw": release,
                    "clinvar_release": display_filedate(release),
                    "clinvar_file": os.path.basename(final),
                    "clinvar_source": vcf_url,
                    "clinvar_url": vcf_url,
                    "clinvar_md5": existing_hash,
                    "clinvar_path": os.path.abspath(final),
                    "clinvar_download_time": _utc_now(),
                    "clinvar_reused": True,
                    "local_provided": False,
                }
            raise GenomeCheckError(
                "A ClinVar file is already here with a different md5, "
                f"so it was not overwritten: {final}"
            )
        _publish_new(tmp_vcf, final)
        _publish_new(tmp_md5, final_md5)
        progress(f"Saved ClinVar as {os.path.basename(final)}.")
        return {
            "clinvar_release_raw": release,
            "clinvar_release": display_filedate(release),
            "clinvar_file": os.path.basename(final),
            "clinvar_source": vcf_url,
            "clinvar_url": vcf_url,
            "clinvar_md5": actual,
            "clinvar_path": os.path.abspath(final),
            "clinvar_download_time": _utc_now(),
            "clinvar_reused": False,
            "local_provided": False,
        }
    finally:
        _remove(tmp_vcf)
        _remove(tmp_md5)


def describe_local_clinvar(path: str, genome_build: str) -> dict:
    if not os.path.isfile(path):
        raise GenomeCheckError(f"ClinVar file not found: {path}")
    header = read_vcf_header_lines(path)
    if not header or not header[0].startswith("##fileformat=VCF"):
        raise GenomeCheckError(f"The ClinVar file is not a VCF: {path}")
    assert_clinvar_reference(header, genome_build)
    release = filedate_from_header(header)
    return {
        "clinvar_release_raw": release,
        "clinvar_release": display_filedate(release),
        "clinvar_file": os.path.basename(path),
        "clinvar_source": "local file provided",
        "clinvar_url": None,
        "clinvar_md5": file_md5(path),
        "clinvar_path": os.path.abspath(path),
        "clinvar_download_time": None,
        "clinvar_reused": False,
        "local_provided": True,
    }


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def open_text(path: str):
    """Open a plain, gzip, or single-txt zip file as text. Read-only."""
    return _TextFile(path)


class _TextFile:
    def __init__(self, path: str) -> None:
        self.path = path
        self._raw = None
        self._gz = None
        self._zip = None
        self._text = None

    def __enter__(self):
        raw = open(self.path, "rb")
        self._raw = raw
        try:
            magic = raw.read(4)
            raw.seek(0)
            if magic[:2] == b"\x1f\x8b":
                self._gz = gzip.GzipFile(fileobj=raw)
                self._text = io.TextIOWrapper(
                    self._gz, encoding="utf-8-sig", errors="replace", newline=None
                )
                return self._text
            if magic[:2] == b"PK":
                raw.close()
                self._raw = None
                self._zip = zipfile.ZipFile(self.path, "r")
                names = _zip_txt_names(self._zip)
                if len(names) != 1:
                    self._zip.close()
                    self._zip = None
                    if not names:
                        raise GenomeCheckError(
                            "unrecognised genome file format: the zip file has no .txt file"
                        )
                    listed = ", ".join(names)
                    raise GenomeCheckError(
                        "The zip file has more than one .txt file: " + listed
                    )
                self._text = io.TextIOWrapper(
                    self._zip.open(names[0], "r"),
                    encoding="utf-8-sig",
                    errors="replace",
                    newline=None,
                )
                return self._text
            self._text = io.TextIOWrapper(
                raw, encoding="utf-8-sig", errors="replace", newline=None
            )
            return self._text
        except GenomeCheckError:
            self.close()
            raise
        except (OSError, gzip.BadGzipFile, zipfile.BadZipFile) as exc:
            self.close()
            raise GenomeCheckError(f"Could not read {self.path}: {exc}") from exc

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def close(self) -> None:
        if self._text is not None:
            try:
                self._text.close()
            except Exception:
                pass
            self._text = None
        if self._zip is not None:
            try:
                self._zip.close()
            except Exception:
                pass
            self._zip = None
        if self._raw is not None:
            try:
                self._raw.close()
            except Exception:
                pass
            self._raw = None


def _zip_txt_names(archive: zipfile.ZipFile) -> list[str]:
    names = []
    for name in archive.namelist():
        if name.endswith("/"):
            continue
        if name.lower().endswith(".txt"):
            names.append(name)
    return names


class GenomeReader:
    """Read a genome file once. The file is never opened for writing."""

    def __init__(self, path: str) -> None:
        self.path = path
        self.container = "plain"
        self._ctx = None
        self._text = None
        self._first_data: str | None = None
        self.kind = ""
        self.meta: dict = {}

    def __enter__(self):
        self._ctx = open_text(self.path)
        self._text = self._ctx.__enter__()
        self.container = _container_of(self.path)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._ctx is not None:
            self._ctx.__exit__(exc_type, exc, tb)
            self._ctx = None
            self._text = None

    def _next_line(self) -> str | None:
        if self._text is None:
            return None
        try:
            line = self._text.readline()
        except (OSError, EOFError, gzip.BadGzipFile, zlib.error) as exc:
            raise GenomeCheckError(f"Could not read {self.path}: {exc}") from exc
        if line == "":
            return None
        return line.rstrip("\r\n")

    def _next_content(self) -> str | None:
        while True:
            line = self._next_line()
            if line is None:
                return None
            if line.strip() == "":
                continue
            return line

    def inspect(self, build_override: str | None = None) -> dict:
        first = self._next_content()
        if first is None:
            raise GenomeCheckError("unrecognised genome file format: the file is empty")
        if first.startswith("##fileformat=VCF"):
            self.kind = "vcf"
            self.meta = self._inspect_vcf(first, build_override)
        else:
            self.meta = self._inspect_chip(first, build_override)
        self.meta["container"] = self.container
        self.meta["path"] = self.path
        self.meta["basename"] = os.path.basename(self.path)
        return self.meta

    def _inspect_vcf(self, first: str, build_override: str | None) -> dict:
        header = [first]
        while True:
            line = self._next_line()
            if line is None:
                break
            if line.strip() == "":
                continue
            if line.startswith("#"):
                header.append(line)
                continue
            self._first_data = line
            break
        chrom_line = next((line for line in header if line.startswith("#CHROM")), None)
        samples: list[str] = []
        if chrom_line:
            columns = chrom_line.split("\t")
            if len(columns) >= 10:
                samples = columns[9:]
        length, text = header_build_evidence(header)
        label = text_build_label(text)
        build, reason = decide_build(
            contig_length=length,
            text_label=label,
            kind="vcf",
            override=build_override,
        )
        version = "VCF"
        match = re.match(r"##fileformat=(VCFv[0-9.]+)", first)
        if match:
            version = match.group(1)
        return {
            "kind": "vcf",
            "file_type": "Sequencing VCF",
            "format": f"{version}, {self.container}",
            "samples": samples,
            "build": build,
            "build_decision": reason,
            "is_chip": False,
        }

    def _inspect_chip(self, first: str, build_override: str | None) -> dict:
        # The column names are sometimes a comment (`# rsid\tchromosome\t...`).
        comments: list[str] = []
        column_line = None
        line: str | None = first
        while line is not None:
            if _is_chip_header_line(line):
                column_line = line
                break
            if line.startswith("#"):
                comments.append(line)
                line = self._next_content()
                continue
            raise GenomeCheckError("unrecognised genome file format")
        if column_line is None:
            raise GenomeCheckError("unrecognised genome file format")
        columns = _chip_columns(column_line)
        blob = "\n".join(comments + [column_line])
        low = blob.lower()
        mentions_23 = "23andme" in low
        mentions_ancestry = "ancestrydna" in low
        is_23 = columns == ["rsid", "chromosome", "position", "genotype"]
        is_ancestry = columns == ["rsid", "chromosome", "position", "allele1", "allele2"]
        if mentions_23 and is_23:
            kind = "23andme"
            file_type = "23andMe chip"
        elif mentions_ancestry and is_ancestry:
            kind = "ancestry"
            file_type = "AncestryDNA chip"
        elif mentions_23 or mentions_ancestry or is_23 or is_ancestry:
            raise GenomeCheckError(
                "unrecognised genome file format: the header and the column names do not agree"
            )
        else:
            raise GenomeCheckError("unrecognised genome file format")
        self.kind = kind
        label = text_build_label(blob)
        build, reason = decide_build(
            contig_length=None,
            text_label=label,
            kind=kind,
            override=build_override,
        )
        return {
            "kind": kind,
            "file_type": file_type,
            "format": f"tab-separated, {self.container}",
            "samples": [],
            "build": build,
            "build_decision": reason,
            "is_chip": True,
        }

    def data_lines(self):
        if self._first_data is not None:
            yield self._first_data
            self._first_data = None
        while True:
            line = self._next_line()
            if line is None:
                return
            if line.strip() == "" or line.startswith("#"):
                continue
            yield line


def _container_of(path: str) -> str:
    with open(path, "rb") as handle:
        magic = handle.read(4)
    if magic[:2] == b"\x1f\x8b":
        return "gzip"
    if magic[:2] == b"PK":
        return "zip"
    return "plain"


def _chip_columns(line: str) -> list[str]:
    raw = line.strip()
    if raw.startswith("#"):
        raw = raw[1:].strip()
    return [part.strip().lower() for part in raw.split("\t")]


def _is_chip_header_line(line: str) -> bool:
    columns = _chip_columns(line)
    return columns in (
        ["rsid", "chromosome", "position", "genotype"],
        ["rsid", "chromosome", "position", "allele1", "allele2"],
    )


def inspect_genome(path: str, build_override: str | None = None) -> dict:
    if not os.path.isfile(path):
        raise GenomeCheckError(f"Genome file not found: {path}")
    with GenomeReader(path) as reader:
        return reader.inspect(build_override)


def format_detect(info: dict) -> str:
    samples = ", ".join(info["samples"]) if info["samples"] else "none"
    lines = [
        f"File type: {info['file_type']}",
        f"Format: {info['format']}",
        f"Reference build: {info['build']}",
        f"Build decided by: {info['build_decision']}",
        f"Samples: {samples}",
    ]
    return "\n".join(lines) + "\n"


def _class_key(token: str) -> str:
    return re.sub(r"[\s_]+", "_", token.strip().lower()).strip("_")


def canonical_class(token: str) -> str:
    """Map a class label to ClinVar's spelling.

    Spaces or underscores, and any case, are accepted. An unknown label errors
    and lists the accepted terms.
    """
    key = _class_key(token)
    for term in ACCEPTED_CLASSES:
        if _class_key(term) == key:
            return term
    accepted = ", ".join(ACCEPTED_CLASSES)
    raise GenomeCheckError(
        f"Unknown classification {token!r}. Accepted terms: {accepted}."
    )


def parse_classes(text: str | None) -> list[str]:
    if text is None:
        return [canonical_class(term) for term in DEFAULT_CLASSES]
    items = []
    for part in text.split(","):
        part = part.strip()
        if not part:
            continue
        canonical = canonical_class(part)
        if canonical not in items:
            items.append(canonical)
    if not items:
        raise GenomeCheckError(
            "The --classes list is empty. Name at least one ClinVar classification."
        )
    return items


def choose_sample(samples: list[str], requested: str | None) -> tuple[str, int, str]:
    if not samples:
        raise GenomeCheckError(
            "This VCF has no sample column, so there is no genotype to read."
        )
    if requested is None:
        return samples[0], 0, "first sample in the file"
    if requested not in samples:
        names = ", ".join(samples)
        raise GenomeCheckError(
            f"Sample {requested} is not in this VCF. The samples are: {names}."
        )
    return requested, samples.index(requested), "named with --sample"


def _record_sort_key(record: dict) -> tuple:
    vid = record["clinvar_ids"][0] if record["clinvar_ids"] else ""
    return (-record["stars"], class_rank(record["selected_terms"] or record["terms"]), vid)


def _better_lookup(candidate: dict, current: dict | None) -> bool:
    if current is None:
        return True
    return _record_sort_key(candidate) < _record_sort_key(current)


def index_clinvar(
    path: str,
    selected: set[str],
    previous_keys: set[str],
    ids_by_key: dict[str, list[str]] | None = None,
) -> tuple[dict, dict, dict]:
    """Stream ClinVar once.

    Selected records are indexed for matching. Every key from a previous run
    is recorded, including keys this release does not have. Variation IDs from
    those hits are indexed even when the class would not be selected, so a
    dropped hit can say where the record went.
    """
    if ids_by_key is None:
        ids_by_key = {}
    wanted_ids = {vid for vids in ids_by_key.values() for vid in vids}
    by_key: dict[tuple, list[dict]] = {}
    by_pos: dict[tuple, list[tuple]] = {}
    lookup_rank: dict[str, dict] = {}
    id_rank: dict[str, dict] = {}
    id_index: dict[str, dict] = {}
    progress("Reading ClinVar.")
    header_done = False
    with open_text(path) as handle:
        for raw_line in handle:
            line = raw_line.rstrip("\r\n")
            if not line or line.startswith("#"):
                header_done = line.startswith("#CHROM") or header_done
                continue
            parsed = _parse_clinvar_line(line, selected)
            if parsed is None:
                continue
            key = parsed["key"]
            key_text = parsed["key_text"]
            if key_text in previous_keys and _better_lookup(parsed, lookup_rank.get(key_text)):
                lookup_rank[key_text] = parsed
            for vid in parsed["clinvar_ids"]:
                if vid in wanted_ids and _better_lookup(parsed, id_rank.get(vid)):
                    id_rank[vid] = parsed
                    id_index[vid] = {
                        "found": True,
                        "chrom": parsed["chrom"],
                        "pos": parsed["pos"],
                        "ref": parsed["ref"],
                        "alt": parsed["alt"],
                        "clnsig": parsed["classification"],
                        "stars": parsed["stars"],
                    }
            if not parsed["selected"]:
                continue
            by_key.setdefault(key, []).append(parsed)
            if parsed["snv"]:
                bucket = by_pos.setdefault((parsed["chrom"], parsed["pos"]), [])
                if key not in bucket:
                    bucket.append(key)
    for records in by_key.values():
        records.sort(key=_record_sort_key)
    lookup: dict[str, dict] = {}
    for key_text in previous_keys:
        parsed = lookup_rank.get(key_text)
        if parsed is None:
            entry: dict = {"looked_up": True, "found": False}
        else:
            entry = {
                "looked_up": True,
                "found": True,
                "clnsig": parsed["classification"],
                "clnrevstat": parsed["review_status_raw"],
                "stars": parsed["stars"],
            }
        id_map: dict[str, dict] = {}
        for vid in ids_by_key.get(key_text, []):
            id_map[vid] = id_index.get(vid) or {"found": False}
        entry["ids"] = id_map
        lookup[key_text] = entry
    return by_key, by_pos, lookup


def _parse_clinvar_line(line: str, selected: set[str]) -> dict | None:
    columns = line.split("\t")
    if len(columns) < 8:
        raise GenomeCheckError("A ClinVar data line has fewer than 8 columns.")
    chrom_raw, pos_raw, vid, ref, alt, _qual, _filt, info_raw = columns[:8]
    if alt in ("*", ".") or alt.startswith("<"):
        return None
    try:
        pos = int(pos_raw)
    except ValueError as exc:
        raise GenomeCheckError(f"ClinVar has a position that is not a number: {pos_raw}") from exc
    ref_n = ref.upper()
    alt_n = alt.upper()
    chrom = normalize_chrom(chrom_raw)
    info = parse_info(info_raw)
    clnsig = info.get("CLNSIG", "")
    decision = classification_decision(clnsig, selected)
    review = review_status_info(info.get("CLNREVSTAT", ""))
    genes = parse_genes(info.get("GENEINFO", ""))
    rsids = parse_rs(info.get("RS", ""))
    record = {
        "key": (chrom, pos, ref_n, alt_n),
        "key_text": variant_key(chrom, pos, ref_n, alt_n),
        "chrom": chrom,
        "pos": pos,
        "ref": ref_n,
        "alt": alt_n,
        "snv": len(ref_n) == 1 and len(alt_n) == 1,
        "clinvar_ids": parse_ids(vid),
        "classification": clnsig,
        "classification_display": clnsig_display(clnsig) if clnsig else "",
        "terms": decision["terms"],
        "selected_terms": decision["selected_terms"],
        "selected": decision["selected"],
        "conflicting": decision["conflicting"],
        "review_status_raw": review["raw"],
        "review_status": review["display"],
        "stars": review["stars"],
        "low_confidence": review["stars"] <= 1,
        "review_status_unrecognised": review["unrecognised"],
        "gene": genes[0] if genes else "no gene",
        "genes": genes,
        "rsids": rsids,
        "condition": condition_display(info.get("CLNDN", "")),
        "variant_type": info.get("CLNVC", "") or "",
        "consequences": parse_mc(info.get("MC", "")),
    }
    return record


def _empty_counts() -> dict:
    return {
        "genome_records_scanned": 0,
        "no_calls": 0,
        "incomplete_calls": 0,
        "skipped_indels": 0,
        "filtered_matches": 0,
        "allele_mismatches": 0,
    }


def match_genome(
    reader: GenomeReader,
    by_key: dict,
    by_pos: dict,
    *,
    sample_index: int | None,
) -> tuple[list[dict], list[dict], dict]:
    progress("Matching the genome to ClinVar.")
    counts = _empty_counts()
    hits: list[dict] = []
    filtered: list[dict] = []
    if reader.kind == "vcf":
        _match_vcf(reader, by_key, sample_index if sample_index is not None else 0, hits, filtered, counts)
    else:
        _match_chip(reader, by_key, by_pos, hits, filtered, counts)
    return hits, filtered, counts


def _match_vcf(reader, by_key, sample_index, hits, filtered, counts) -> None:
    for line in reader.data_lines():
        counts["genome_records_scanned"] += 1
        columns = line.split("\t")
        if len(columns) < 8:
            raise GenomeCheckError("A genome VCF line has fewer than 8 columns.")
        chrom = normalize_chrom(columns[0])
        try:
            pos = int(columns[1])
        except ValueError as exc:
            raise GenomeCheckError(f"A genome VCF position is not a number: {columns[1]}") from exc
        ref = columns[3].upper()
        alt_field = columns[4]
        qual = columns[5]
        filt = columns[6] if columns[6] else "."
        info = parse_info(columns[7])
        fmt: dict[str, str] = {}
        gt = ""
        if len(columns) >= 10:
            sample_cell = columns[9 + sample_index] if 9 + sample_index < len(columns) else ""
            fmt = parse_format(columns[8], sample_cell)
            gt = fmt.get("GT", "")
        elif len(columns) == 9:
            fmt = parse_format(columns[8], "")
            gt = fmt.get("GT", "")
        alleles = parse_gt(gt) if gt else []
        if not gt or not alleles or all(allele is None for allele in alleles):
            counts["no_calls"] += 1
            continue
        # One allele called, one not: keep going, and count it either way.
        # 0/. is not a hit. 1/. can be. ./. was already counted as a no-call.
        if any(allele is None for allele in alleles):
            counts["incomplete_calls"] += 1
        alts = alt_field.split(",")
        for index, alt in enumerate(alts, start=1):
            if alt in ("*", ".") or alt.startswith("<"):
                continue
            alt_n = alt.upper()
            if alleles.count(index) < 1:
                continue
            key = (chrom, pos, ref, alt_n)
            records = by_key.get(key)
            if not records:
                continue
            observation = _vcf_observation(
                gt=gt,
                alleles=alleles,
                allele_index=index,
                qual=qual,
                filt=filt,
                info=info,
                fmt=fmt,
            )
            hit = _assemble_hit(records, observation)
            if observation["filter_failed"]:
                filtered.append(hit)
            else:
                hits.append(hit)
    counts["filtered_matches"] = len(filtered)


def _vcf_observation(*, gt, alleles, allele_index, qual, filt, info, fmt) -> dict:
    ft = fmt.get("FT")
    if ft == "":
        ft = None
    filt_bad = filt not in ("PASS", ".")
    ft_bad = ft is not None and ft not in ("PASS", ".")
    filter_value = filt if filt else "."
    if filt_bad or ft_bad:
        parts = []
        if filt_bad:
            parts.append(filt)
        if ft_bad:
            parts.append(f"FT={ft}")
        filter_value = ";".join(parts)
    depth = parse_number(fmt.get("DP"))
    if depth is None:
        depth = parse_number(info.get("DP"))
    gq = parse_number(fmt.get("GQ"))
    alt_reads = None
    total_reads = None
    ad = fmt.get("AD")
    if ad:
        numbers = [parse_number(part) for part in ad.split(",")]
        if numbers and all(number is not None for number in numbers):
            total_reads = sum(numbers)
            if allele_index < len(numbers):
                alt_reads = numbers[allele_index]
    return {
        "genotype": gt,
        "zygosity": zygosity_for_gt(alleles, allele_index),
        "incomplete_call": any(allele is None for allele in alleles),
        "depth": depth,
        "alt_reads": alt_reads,
        "total_reads": total_reads,
        "gq": gq,
        "qual": parse_number(qual),
        "filter": filter_value,
        "filter_failed": filt_bad or ft_bad,
    }


def _match_chip(reader, by_key, by_pos, hits, filtered, counts) -> None:
    ancestry = reader.kind == "ancestry"
    for line in reader.data_lines():
        counts["genome_records_scanned"] += 1
        columns = line.split("\t")
        needed = 5 if ancestry else 4
        if len(columns) < needed:
            raise GenomeCheckError("A chip data line does not have the expected columns.")
        chrom = normalize_chrom(columns[1])
        try:
            pos = int(columns[2])
        except ValueError as exc:
            raise GenomeCheckError(f"A chip position is not a number: {columns[2]}") from exc
        call = _parse_chip_call(columns, ancestry)
        if call["nocall"]:
            counts["no_calls"] += 1
            continue
        if call["indel"]:
            counts["skipped_indels"] += 1
            continue
        bases = call["bases"]
        keys = by_pos.get((chrom, pos), [])
        records_at_pos = [record for key in keys for record in by_key.get(key, [])]
        if records_at_pos and not any(_chip_consistent(bases, record) for record in records_at_pos):
            counts["allele_mismatches"] += 1
        seen = set()
        for key in keys:
            if key in seen:
                continue
            seen.add(key)
            records = by_key.get(key, [])
            if not records:
                continue
            alt = records[0]["alt"]
            copies = sum(1 for base in bases if base == alt)
            if copies < 1:
                continue
            observation = {
                "genotype": call["genotype"],
                "zygosity": zygosity_from_copies(copies, len(bases)),
                "incomplete_call": False,
                "depth": None,
                "alt_reads": None,
                "total_reads": None,
                "gq": None,
                "qual": None,
                "filter": None,
                "filter_failed": False,
            }
            hits.append(_assemble_hit(records, observation))
    counts["filtered_matches"] = len(filtered)


def _chip_consistent(bases: list[str], record: dict) -> bool:
    allowed = {record["ref"], record["alt"]}
    return any(base in allowed for base in bases)


def _parse_chip_call(columns: list[str], ancestry: bool) -> dict:
    if ancestry:
        allele1 = columns[3].strip().upper()
        allele2 = columns[4].strip().upper()
        genotype = allele1 + allele2
        tokens = [allele1, allele2]
        if any(token in ("0", "-", "--", "N", "NN") for token in tokens):
            return {"nocall": True, "indel": False, "bases": [], "genotype": genotype}
        if any(token in ("I", "D") for token in tokens):
            return {"nocall": False, "indel": True, "bases": [], "genotype": genotype}
        if all(token in ("A", "C", "G", "T") for token in tokens):
            return {"nocall": False, "indel": False, "bases": tokens, "genotype": genotype}
        return {"nocall": True, "indel": False, "bases": [], "genotype": genotype}
    genotype = columns[3].strip().upper()
    if genotype in ("--", "-", "0", "00", "N", "NN"):
        return {"nocall": True, "indel": False, "bases": [], "genotype": genotype}
    letters = list(genotype)
    if any(letter in ("I", "D") for letter in letters):
        return {"nocall": False, "indel": True, "bases": [], "genotype": genotype}
    if letters and all(letter in ("A", "C", "G", "T") for letter in letters):
        return {"nocall": False, "indel": False, "bases": letters, "genotype": genotype}
    return {"nocall": True, "indel": False, "bases": [], "genotype": genotype}


def _assemble_hit(records: list[dict], observation: dict) -> dict:
    ordered = sorted(records, key=_record_sort_key)
    primary = ordered[0]
    genes: list[str] = []
    for record in ordered:
        for gene in record["genes"]:
            if gene not in genes:
                genes.append(gene)
    terms: list[str] = []
    for record in ordered:
        for term in record["terms"]:
            if term not in terms:
                terms.append(term)
    conditions: list[str] = []
    for record in ordered:
        if record["condition"] and record["condition"] not in conditions:
            conditions.append(record["condition"])
    rsids: list[str] = []
    ids: list[str] = []
    for record in ordered:
        for rsid in record["rsids"]:
            if rsid not in rsids:
                rsids.append(rsid)
        for vid in record["clinvar_ids"]:
            if vid not in ids:
                ids.append(vid)
    condition = "; ".join(conditions)
    area = assign_area(terms, genes, condition)
    clinvar_records = [_public_record(record) for record in ordered]
    return {
        "chrom": primary["chrom"],
        "pos": primary["pos"],
        "ref": primary["ref"],
        "alt": primary["alt"],
        "gene": primary["gene"],
        "genes": genes,
        "rsid": ", ".join(rsids) if rsids else None,
        "clinvar_ids": ids,
        "classification": primary["classification"],
        "classification_display": primary["classification_display"],
        "base_classes": list(primary["terms"]),
        "review_status": primary["review_status"],
        "review_status_raw": primary["review_status_raw"],
        "stars": primary["stars"],
        "low_confidence": primary["stars"] <= 1,
        "conflicting": primary["conflicting"],
        "review_status_unrecognised": primary["review_status_unrecognised"],
        "condition": condition,
        "area": area,
        "genotype": observation["genotype"],
        "zygosity": observation["zygosity"],
        "incomplete_call": bool(observation.get("incomplete_call")),
        "depth": observation["depth"],
        "alt_reads": observation["alt_reads"],
        "total_reads": observation["total_reads"],
        "gq": observation["gq"],
        "qual": observation["qual"],
        "filter": observation["filter"],
        "variant_type": primary["variant_type"],
        "consequences": list(primary["consequences"]),
        "clinvar_records": clinvar_records,
        "_selected_terms_union": [term for term in terms if term in _selected_from(ordered)],
    }


def _selected_from(records: list[dict]) -> set[str]:
    found = set()
    for record in records:
        found.update(record["selected_terms"])
    return found


def _public_record(record: dict) -> dict:
    return {
        "clinvar_ids": list(record["clinvar_ids"]),
        "classification": record["classification"],
        "classification_display": record["classification_display"],
        "base_classes": list(record["terms"]),
        "review_status": record["review_status"],
        "review_status_raw": record["review_status_raw"],
        "stars": record["stars"],
        "low_confidence": record["stars"] <= 1,
        "conflicting": record["conflicting"],
        "review_status_unrecognised": record["review_status_unrecognised"],
        "condition": record["condition"],
        "gene": record["gene"],
        "genes": list(record["genes"]),
        "rsid": ", ".join(record["rsids"]) if record["rsids"] else None,
        "variant_type": record["variant_type"],
        "consequences": list(record["consequences"]),
    }


def _summary_counts(hits: list[dict], filtered: list[dict], counts: dict, selected: list[str]) -> dict:
    by_stars = {str(star): 0 for star in range(5)}
    by_class = {token: 0 for token in selected}
    low = 0
    for hit in hits:
        by_stars[str(int(hit["stars"]))] += 1
        if hit["stars"] <= 1:
            low += 1
        for term in hit.get("_selected_terms_union") or []:
            if term in by_class:
                by_class[term] += 1
    return {
        "hits": len(hits),
        "by_stars": by_stars,
        "by_class": by_class,
        "low_confidence": low,
        "genome_records_scanned": counts["genome_records_scanned"],
        "no_calls": counts["no_calls"],
        "incomplete_calls": counts.get("incomplete_calls", 0),
        "skipped_indels": counts["skipped_indels"],
        "filtered_matches": len(filtered),
        "allele_mismatches": counts["allele_mismatches"],
    }


def _strip_private(hit: dict) -> dict:
    return {key: value for key, value in hit.items() if not key.startswith("_")}


def _dash(value) -> str:
    if value is None or value == "":
        return EN
    return str(value)


def _flag_suffix(record: dict) -> str:
    parts = []
    if record.get("low_confidence") or int(record.get("stars", 0)) <= 1:
        parts.append("LOW CONFIDENCE")
    if record.get("conflicting"):
        parts.append("CONFLICTING SUBMISSIONS")
    return "".join(f" {EM} {part}" for part in parts)


def _classification_lines(hit: dict) -> list[str]:
    lines = []
    records = hit.get("clinvar_records") or [_public_record_from_hit(hit)]
    for index, record in enumerate(records):
        glyph = star_glyph(int(record["stars"]))
        review = record.get("review_status") or ""
        display = record.get("classification_display") or class_display(record.get("classification", ""))
        flags = _flag_suffix(record)
        if index == 0 and hit.get("incomplete_call"):
            flags += f" {EM} INCOMPLETE CALL"
        if index == 0:
            lines.append(
                f"- **{hit['gene']}** {EM} {display} {EM} {glyph} "
                f"({record['stars']}/4) {review}{flags}".rstrip()
            )
        else:
            lines.append(
                f"  - {display} {EM} {glyph} ({record['stars']}/4) {review}{flags}".rstrip()
            )
    return lines


def _public_record_from_hit(hit: dict) -> dict:
    return hit


def _variant_line(hit: dict) -> str:
    rs_text = hit["rsid"] if hit.get("rsid") else "no rs number"
    id_bits = []
    for vid in hit.get("clinvar_ids") or []:
        url = clinvar_variation_url(vid)
        if url:
            id_bits.append(f"ClinVar {vid} ({url})")
        else:
            id_bits.append(f"ClinVar {vid}")
    id_text = "; ".join(id_bits) if id_bits else "ClinVar id not recorded"
    return (
        f"  - Variant: {hit['chrom']}:{hit['pos']} {hit['ref']}>{hit['alt']} "
        f"{MID} {rs_text} {MID} {id_text}"
    )


def _hit_block(hit: dict) -> str:
    lines = _classification_lines(hit)
    lines.append(_variant_line(hit))
    lines.append(f"  - Genotype: {hit['genotype']} ({hit['zygosity']})")
    lines.append(
        "  - Reads: "
        f"depth {_dash(hit.get('depth'))}, "
        f"alt reads {_dash(hit.get('alt_reads'))} of {_dash(hit.get('total_reads'))}, "
        f"GQ {_dash(hit.get('gq'))}, "
        f"filter {_dash(hit.get('filter'))}"
    )
    condition = truncate_text(hit.get("condition") or "")
    if not condition:
        condition = "not recorded"
    lines.append(f"  - Condition: {condition}")
    return "\n".join(lines)


def _report_sort_key(hit: dict) -> tuple:
    terms = hit.get("_selected_terms_union") or hit.get("base_classes") or []
    return (-int(hit["stars"]), class_rank(terms), str(hit["gene"]).upper(), hit_sort_tuple(hit))


def _cell(value: str) -> str:
    return str(value).replace("|", "/").replace("\n", " ")


def render_header(is_chip: bool) -> str:
    parts = ["<!-- header -->", "", HEADER_RESEARCH, ""]
    if is_chip:
        parts.extend([HEADER_CHIP, ""])
    parts.append("<!-- /header -->")
    return "\n".join(parts)


def render_report(payload: dict) -> str:
    meta = payload["metadata"]
    counts = meta["counts"]
    is_chip = "chip" in meta.get("file_type", "").lower()
    lines = [render_header(is_chip), "", "# Genome check", ""]
    sample = meta.get("sample_label") or meta.get("sample") or "none"
    rows = [
        ("Genome file", meta.get("genome_file", "")),
        ("File type", meta.get("file_type", "")),
        ("Format", meta.get("format", "")),
        ("Sample used", sample),
        ("Reference build", meta.get("build", "")),
        ("How the build was decided", meta.get("build_decision", "")),
        ("ClinVar release", meta.get("clinvar_release", "")),
        ("ClinVar file", meta.get("clinvar_file", "")),
        ("ClinVar source", meta.get("clinvar_source", "")),
        ("Run date", meta.get("run_date", "")),
        ("Selected classes", ", ".join(meta.get("selected_classes") or [])),
    ]
    lines.append("| | |")
    lines.append("| --- | --- |")
    for label, value in rows:
        lines.append(f"| {_cell(label)} | {_cell(value)} |")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Hits: {counts['hits']}")
    star_bits = ", ".join(f"{star} stars {counts['by_stars'][str(star)]}" for star in range(4, -1, -1))
    lines.append(f"- By stars: {star_bits}")
    class_bits = ", ".join(
        f"{class_display(token)} {counts['by_class'].get(token, 0)}"
        for token in meta.get("selected_classes") or []
    )
    lines.append(f"- By class: {class_bits}")
    lines.append(f"- Low confidence (0 or 1 star): {counts['low_confidence']}")
    lines.append(f"- Genome records scanned: {counts['genome_records_scanned']}")
    lines.append(f"- No-calls: {counts['no_calls']}")
    lines.append(f"- Incomplete calls: {counts.get('incomplete_calls', 0)}")
    lines.append(f"- Skipped indel codes: {counts['skipped_indels']}")
    lines.append(f"- Filtered matches: {counts['filtered_matches']}")
    lines.append(f"- Chip allele mismatches: {counts['allele_mismatches']}")
    lines.append("")
    lines.append("## Stars")
    lines.append("")
    lines.append(STAR_LEGEND)
    lines.append("")
    lines.append(f"Source: {STAR_LEGEND_URL}")
    lines.append("")
    grouped: dict[str, list[dict]] = {}
    for hit in payload["hits"]:
        grouped.setdefault(hit["area"], []).append(hit)
    for area in REPORT_AREA_ORDER:
        group = grouped.get(area)
        if not group:
            continue
        group = sorted(group, key=_report_sort_key)
        lines.append(f"## {area} ({len(group)})")
        lines.append("")
        for hit in group:
            lines.append(_hit_block(hit))
            lines.append("")
    extra_areas = [area for area in grouped if area not in REPORT_AREA_ORDER]
    for area in sorted(extra_areas):
        group = sorted(grouped[area], key=_report_sort_key)
        lines.append(f"## {area} ({len(group)})")
        lines.append("")
        for hit in group:
            lines.append(_hit_block(hit))
            lines.append("")
    filtered = sorted(payload.get("filtered_matches") or [], key=_report_sort_key)
    lines.append(
        f"## Matches that failed the sequencer's quality filter ({len(filtered)})"
    )
    lines.append("")
    if not filtered:
        lines.append("None.")
        lines.append("")
    else:
        for hit in filtered:
            lines.append(_hit_block(hit))
            lines.append("")
    lines.append("## Method and limits")
    lines.append("")
    lines.append(method_text_for(is_chip))
    lines.append("")
    return "\n".join(lines)


def method_text_for(is_chip: bool) -> str:
    if is_chip:
        return METHOD_TEXT_CHIP
    return METHOD_TEXT


def render_diff(old: dict, new: dict) -> str:
    old_meta = old.get("metadata") or {}
    new_meta = new.get("metadata") or {}
    old_hits = {_hit_key(hit): hit for hit in old.get("hits") or []}
    new_hits = {_hit_key(hit): hit for hit in new.get("hits") or []}
    lookup = new.get("previous_lookup", None)
    if lookup is not None and not isinstance(lookup, dict):
        lookup = None
    new_keys = [key for key in new_hits if key not in old_hits]
    dropped_keys = [key for key in old_hits if key not in new_hits]
    shared = [key for key in new_hits if key in old_hits]
    reclassified = []
    star_changes = []
    added_records = []
    removed_records = []
    for key in shared:
        events = _record_events(old_hits[key], new_hits[key], key)
        reclassified.extend(events["reclassified"])
        star_changes.extend(events["star_changes"])
        added_records.extend(events["added"])
        removed_records.extend(events["removed"])
    other_changes = []
    for key in shared:
        changes = []
        if str(old_hits[key].get("genotype", "")) != str(new_hits[key].get("genotype", "")):
            changes.append(
                "genotype "
                f"{old_hits[key].get('genotype')} ({old_hits[key].get('zygosity')}) "
                f"{_arrow()} {new_hits[key].get('genotype')} ({new_hits[key].get('zygosity')})"
            )
        if str(old_hits[key].get("area", "")) != str(new_hits[key].get("area", "")):
            changes.append(
                f"area {old_hits[key].get('area')} {_arrow()} {new_hits[key].get('area')}"
            )
        if str(old_hits[key].get("zygosity", "")) != str(new_hits[key].get("zygosity", "")) and not any(
            item.startswith("genotype ") for item in changes
        ):
            changes.append(
                "zygosity "
                f"{old_hits[key].get('zygosity')} {_arrow()} {new_hits[key].get('zygosity')}"
            )
        if changes:
            other_changes.append((key, changes))
    def _event_sort(item: tuple) -> tuple:
        return (_key_sort(item[0]), str(item[1]))

    new_keys.sort(key=_key_sort)
    dropped_keys.sort(key=_key_sort)
    reclassified.sort(key=_event_sort)
    star_changes.sort(key=_event_sort)
    added_records.sort(key=_event_sort)
    removed_records.sort(key=_event_sort)
    other_changes.sort(key=lambda item: _key_sort(item[0]))
    is_chip = "chip" in str(old_meta.get("file_type", "")).lower() or "chip" in str(
        new_meta.get("file_type", "")
    ).lower()
    lines = [render_header(is_chip), "", "# What changed between two ClinVar runs", ""]
    lines.append("| | Earlier | Later |")
    lines.append("| --- | --- | --- |")
    lines.append(
        "| Genome file | "
        f"{_cell(old_meta.get('genome_file', 'unknown'))} | "
        f"{_cell(new_meta.get('genome_file', 'unknown'))} |"
    )
    lines.append(
        "| Run date | "
        f"{_cell(old_meta.get('run_date', 'unknown'))} | "
        f"{_cell(new_meta.get('run_date', 'unknown'))} |"
    )
    lines.append(
        "| ClinVar release | "
        f"{_cell(old_meta.get('clinvar_release', 'unknown'))} | "
        f"{_cell(new_meta.get('clinvar_release', 'unknown'))} |"
    )
    lines.append("")
    old_name = str(old_meta.get("genome_file", ""))
    new_name = str(new_meta.get("genome_file", ""))
    if old_name and new_name and old_name != new_name:
        lines.append(f"Warning: the genome file names differ ({old_name} and {new_name}).")
        lines.append("")
    lines.append("## Counts")
    lines.append("")
    lines.append(f"- New hits: {len(new_keys)}")
    lines.append(f"- Dropped hits: {len(dropped_keys)}")
    lines.append(f"- Reclassified: {len(reclassified)}")
    lines.append(f"- Review-status changes: {len(star_changes)}")
    lines.append(f"- ClinVar records added: {len(added_records)}")
    lines.append(f"- ClinVar records removed: {len(removed_records)}")
    lines.append(f"- Genotype or area changes: {len(other_changes)}")
    lines.append("")
    lines.append(f"## New hits ({len(new_keys)})")
    lines.append("")
    if not new_keys:
        lines.append("None.")
        lines.append("")
    for key in new_keys:
        hit = new_hits[key]
        lines.append(
            f"- **{hit.get('gene', 'no gene')}** {EM} {hit.get('classification_display') or hit.get('classification')} "
            f"{EM} {star_glyph(int(hit.get('stars', 0)))} ({hit.get('stars')}/4) {EM} {_key_text(key)}"
        )
    if new_keys:
        lines.append("")
    lines.append(f"## Dropped hits ({len(dropped_keys)})")
    lines.append("")
    if not dropped_keys:
        lines.append("None.")
        lines.append("")
    for key in dropped_keys:
        hit = old_hits[key]
        text = _key_text(key)
        was = hit.get("classification_display") or hit.get("classification") or ""
        tail = _dropped_tail(lookup, text)
        lines.append(
            f"- **{hit.get('gene', 'no gene')}** {EM} {text} {EM} was {was}, {hit.get('stars')}/4. {tail}"
        )
        lines.extend(_dropped_id_lines(lookup, text, _hit_variation_ids(hit)))
    if dropped_keys:
        lines.append("")
    lines.append(f"## Reclassified ({len(reclassified)})")
    lines.append("")
    if not reclassified:
        lines.append("None.")
        lines.append("")
    for key, vid, gene, before, after in reclassified:
        lines.append(
            f"- **{gene}** {EM} {_key_text(key)} {EM} {_vid_phrase(vid)}"
            f"{before} {_arrow()} {after}"
        )
    if reclassified:
        lines.append("")
    lines.append(f"## Review-status changes ({len(star_changes)})")
    lines.append("")
    if not star_changes:
        lines.append("None.")
        lines.append("")
    for key, vid, gene, before, after in star_changes:
        lines.append(
            f"- **{gene}** {EM} {_key_text(key)} {EM} {_vid_phrase(vid)}"
            f"{_stars_of(before)}/4 {_arrow()} {_stars_of(after)}/4"
        )
        lines.append(f"  - Earlier: {before.get('review_status', '')}")
        lines.append(f"  - Later: {after.get('review_status', '')}")
    if star_changes:
        lines.append("")
    lines.append(f"## ClinVar records added ({len(added_records)})")
    lines.append("")
    if not added_records:
        lines.append("None.")
        lines.append("")
    for key, vid, gene, record in added_records:
        lines.append(_record_presence_line(gene, key, vid, record))
    if added_records:
        lines.append("")
    lines.append(f"## ClinVar records removed ({len(removed_records)})")
    lines.append("")
    if not removed_records:
        lines.append("None.")
        lines.append("")
    for key, vid, gene, record in removed_records:
        lines.append(_record_presence_line(gene, key, vid, record))
    if removed_records:
        lines.append("")
    lines.append(f"## Genotype or area changes ({len(other_changes)})")
    lines.append("")
    if not other_changes:
        lines.append("None.")
        lines.append("")
    for key, changes in other_changes:
        hit = new_hits[key]
        detail = "; ".join(changes)
        lines.append(f"- **{hit.get('gene', 'no gene')}** {EM} {_key_text(key)} {EM} {detail}")
        lines.append("  - Flag: genotype or area differs for the same variant key.")
    if other_changes:
        lines.append("")
    lines.append("## Method and limits")
    lines.append("")
    lines.append(method_text_for(is_chip))
    lines.append("")
    return "\n".join(lines)


def _arrow() -> str:
    return "\u2192"


def _hit_key(hit: dict) -> tuple:
    chrom = normalize_chrom(str(hit.get("chrom", "")))
    return (chrom, int(hit["pos"]), str(hit.get("ref", "")).upper(), str(hit.get("alt", "")).upper())


def _key_text(key: tuple) -> str:
    chrom, pos, ref, alt = key
    return variant_key(chrom, pos, ref, alt)


def _key_sort(key: tuple) -> tuple:
    chrom, pos, ref, alt = key
    return (chrom_sort_key(chrom), pos, ref, alt)


def _id_list(value) -> list[str]:
    if value is None or value == "":
        return []
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list):
        return []
    found: list[str] = []
    for item in value:
        text = str(item).strip()
        if text and text != "." and text not in found:
            found.append(text)
    return found


def _stars_of(record: dict) -> int:
    try:
        return int(record.get("stars"))
    except (TypeError, ValueError):
        return 0


def _class_of(record: dict) -> str:
    value = record.get("classification")
    if value is None:
        return ""
    return str(value)


def _records_for_diff(hit: dict) -> tuple[dict[str, dict], list[dict]]:
    """Variation-id map, plus records that have no id.

    A hit with no clinvar_records is one virtual record, so an older JSON
    file still diffs on its top-level classification and stars.
    """
    records = hit.get("clinvar_records")
    if not isinstance(records, list) or not records:
        ids = _id_list(hit.get("clinvar_ids"))
        virtual = {
            "clinvar_ids": ids,
            "classification": hit.get("classification", ""),
            "stars": hit.get("stars", 0),
            "review_status": hit.get("review_status", ""),
        }
        if ids:
            return {ids[0]: virtual}, []
        return {"": virtual}, []
    by_id: dict[str, dict] = {}
    anonymous: list[dict] = []
    for record in records:
        if not isinstance(record, dict):
            continue
        ids = _id_list(record.get("clinvar_ids"))
        if not ids:
            anonymous.append(record)
            continue
        by_id.setdefault(ids[0], record)
    return by_id, anonymous


def _vid_phrase(vid: str) -> str:
    if vid and not str(vid).startswith("#"):
        return f"ClinVar {vid} {EM} "
    return ""


def _record_presence_line(gene: str, key: tuple, vid: str, record: dict) -> str:
    if vid and not str(vid).startswith("#"):
        label = f"ClinVar {vid}"
    else:
        label = "ClinVar id not recorded"
    return (
        f"- **{gene}** {EM} {_key_text(key)} {EM} {label} {EM} "
        f"{_class_of(record)} ({_stars_of(record)}/4)"
    )


def _record_events(old_hit: dict, new_hit: dict, key: tuple) -> dict:
    """Compare every ClinVar record on one key, by variation id."""
    old_by, old_anon = _records_for_diff(old_hit)
    new_by, new_anon = _records_for_diff(new_hit)
    gene_new = new_hit.get("gene", "no gene")
    gene_old = old_hit.get("gene", "no gene")
    reclassified = []
    star_changes = []
    added = []
    removed = []
    for vid in sorted(set(old_by) | set(new_by)):
        if vid not in old_by:
            added.append((key, vid, gene_new, new_by[vid]))
        elif vid not in new_by:
            removed.append((key, vid, gene_old, old_by[vid]))
        else:
            before = old_by[vid]
            after = new_by[vid]
            if _class_of(before) != _class_of(after):
                reclassified.append((key, vid, gene_new, _class_of(before), _class_of(after)))
            if _stars_of(before) != _stars_of(after):
                star_changes.append((key, vid, gene_new, before, after))
    shared_n = min(len(old_anon), len(new_anon))
    for index in range(shared_n):
        before = old_anon[index]
        after = new_anon[index]
        vid = f"#{index}"
        if _class_of(before) != _class_of(after):
            reclassified.append((key, vid, gene_new, _class_of(before), _class_of(after)))
        if _stars_of(before) != _stars_of(after):
            star_changes.append((key, vid, gene_new, before, after))
    for index in range(shared_n, len(old_anon)):
        removed.append((key, f"#{index}", gene_old, old_anon[index]))
    for index in range(shared_n, len(new_anon)):
        added.append((key, f"#{index}", gene_new, new_anon[index]))
    return {
        "reclassified": reclassified,
        "star_changes": star_changes,
        "added": added,
        "removed": removed,
    }


def _dropped_tail(lookup: dict | None, key_text: str) -> str:
    if not isinstance(lookup, dict) or key_text not in lookup:
        return "current classification not looked up"
    info = lookup.get(key_text)
    if not isinstance(info, dict):
        return "current classification not looked up"
    # Only an explicit miss may say the variant left this ClinVar release.
    if info.get("looked_up") is True and info.get("found") is False:
        return "no longer in this ClinVar release at this exact position and alleles"
    if info.get("found") is True or "clnsig" in info:
        raw = str(info.get("clnsig", ""))
        display = clnsig_display(raw) if raw else ""
        stars = info.get("stars", 0)
        return f"now classified: {display}, {stars}/4"
    return "current classification not looked up"


def _hit_variation_ids(hit: dict) -> list[str]:
    """Variation ids carried by one hit, in report order.

    Every id on every clinvar_records entry. When that list is missing or
    empty, the hit's own clinvar_ids are used, matching an older report and
    the ids previous_lookup recorded for it.
    """
    records = hit.get("clinvar_records")
    sources = records if isinstance(records, list) and records else [hit]
    found: list[str] = []
    for source in sources:
        if not isinstance(source, dict):
            continue
        for vid in _id_list(source.get("clinvar_ids")):
            if vid not in found:
                found.append(vid)
    return found


def _dropped_id_lines(
    lookup: dict | None, key_text: str, variation_ids: list[str]
) -> list[str]:
    """Where the dropped hit's own variation ids sit in this ClinVar release.

    A line is printed only for an id the dropped hit carries, and only when
    this report saved evidence for that id under previous_lookup. An id with
    no saved evidence is omitted, and an id the hit does not carry is never
    mentioned. Also omitted when the lookup has no per-id data, including a
    plain diff of two JSON files that never recorded it.
    """
    if not variation_ids:
        return []
    if not isinstance(lookup, dict) or key_text not in lookup:
        return []
    info = lookup.get(key_text)
    if not isinstance(info, dict) or "ids" not in info:
        return []
    saved = info.get("ids")
    if not isinstance(saved, dict):
        return []
    lines = []
    for vid in variation_ids:
        if vid not in saved:
            continue
        detail = saved[vid]
        if not isinstance(detail, dict):
            detail = {}
        if detail.get("found"):
            raw = str(detail.get("clnsig", ""))
            display = clnsig_display(raw) if raw else ""
            lines.append(
                "  - ClinVar record "
                f"{vid} now listed at {detail.get('chrom')}:{detail.get('pos')} "
                f"{detail.get('ref')}>{detail.get('alt')}, "
                f"classified {display}, {detail.get('stars', 0)}/4"
            )
        else:
            lines.append(
                f"  - ClinVar record {vid} is not in this release "
                "(removed, merged or withdrawn by ClinVar)"
            )
    return lines


def load_json(path: str) -> dict:
    if not os.path.isfile(path):
        raise GenomeCheckError(f"JSON file not found: {path}")
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:
        raise GenomeCheckError(f"Previous report is not readable JSON: {path}") from exc
    if not isinstance(data, dict):
        raise GenomeCheckError(f"Previous report is not a JSON object: {path}")
    return data


def previous_interest(payload: dict) -> tuple[set[str], dict[str, list[str]]]:
    """Keys to look up, and the variation ids that belong to each key."""
    if "hits" not in payload:
        raise GenomeCheckError("Previous report JSON has no hits list.")
    keys: set[str] = set()
    ids_by_key: dict[str, list[str]] = {}
    for bucket in ("hits", "filtered_matches"):
        for hit in payload.get(bucket) or []:
            try:
                chrom, pos, ref, alt = _hit_key(hit)
            except (KeyError, TypeError, ValueError) as exc:
                raise GenomeCheckError(
                    "A hit in the previous report is missing chrom, pos, ref, or alt."
                ) from exc
            key = variant_key(chrom, pos, ref, alt)
            keys.add(key)
            found = ids_by_key.setdefault(key, [])
            records = hit.get("clinvar_records")
            sources = records if isinstance(records, list) and records else [hit]
            for source in sources:
                if not isinstance(source, dict):
                    continue
                for vid in _id_list(source.get("clinvar_ids")):
                    if vid not in found:
                        found.append(vid)
    return keys, ids_by_key


def previous_keys_from(payload: dict) -> set[str]:
    keys, _ids = previous_interest(payload)
    return keys


def write_exclusive(path: str, data: str) -> None:
    if os.path.lexists(path):
        raise GenomeCheckError(
            f"Output file already exists: {path}. This tool never overwrites."
        )
    encoded = data.encode("utf-8")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    try:
        descriptor = os.open(path, flags, 0o644)
    except FileExistsError as exc:
        raise GenomeCheckError(
            f"Output file already exists: {path}. This tool never overwrites."
        ) from exc
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(encoded)


def output_paths(out_dir: str, run_date: str, release_raw: str) -> tuple[str, str, str]:
    stem = f"genome-check-{run_date}-clinvar{release_raw}"
    return (
        os.path.join(out_dir, stem + ".md"),
        os.path.join(out_dir, stem + ".json"),
        os.path.join(out_dir, stem + "-diff.md"),
    )


def refuse_genome_collision(paths: list[str], genome_path: str) -> None:
    for path in paths:
        if paths_equal(path, genome_path):
            raise GenomeCheckError(f"Refusing to write over the genome file: {genome_path}")


def build_payload(
    *,
    genome_meta: dict,
    sample_name: str | None,
    sample_note: str,
    clinvar_meta: dict,
    selected: list[str],
    hits: list[dict],
    filtered: list[dict],
    counts: dict,
    run_date: str,
    previous_lookup: dict | None,
) -> dict:
    summary = _summary_counts(hits, filtered, counts, selected)
    public_hits = [_strip_private(hit) for hit in sorted(hits, key=hit_sort_tuple)]
    public_filtered = [_strip_private(hit) for hit in sorted(filtered, key=hit_sort_tuple)]
    if sample_name:
        sample_label = f"{sample_name} ({sample_note})"
    else:
        sample_name = "none"
        sample_label = "none (chip file, no sample name)"
    metadata = {
        "genome_file": genome_meta["basename"],
        "file_type": genome_meta["file_type"],
        "format": genome_meta["format"],
        "sample": sample_name,
        "sample_label": sample_label,
        "samples": list(genome_meta.get("samples") or []),
        "build": genome_meta["build"],
        "build_decision": genome_meta["build_decision"],
        "clinvar_release": clinvar_meta["clinvar_release"],
        "clinvar_release_raw": clinvar_meta["clinvar_release_raw"],
        "clinvar_file": clinvar_meta["clinvar_file"],
        "clinvar_source": clinvar_meta["clinvar_source"],
        "clinvar_url": clinvar_meta["clinvar_url"],
        "clinvar_md5": clinvar_meta["clinvar_md5"],
        "clinvar_path": clinvar_meta["clinvar_path"],
        "clinvar_download_time": clinvar_meta["clinvar_download_time"],
        "clinvar_reused": clinvar_meta["clinvar_reused"],
        "run_date": run_date,
        "selected_classes": list(selected),
        "counts": summary,
    }
    payload = {
        "tool": TOOL_NAME,
        "tool_version": TOOL_VERSION,
        "metadata": metadata,
        "hits": public_hits,
        "filtered_matches": public_filtered,
    }
    if previous_lookup is not None:
        payload["previous_lookup"] = previous_lookup
    return payload


def run_check(
    *,
    genome: str,
    out_dir: str,
    clinvar: str | None = None,
    clinvar_dir: str | None = None,
    build: str | None = None,
    sample: str | None = None,
    previous: str | None = None,
    classes: str | None = None,
    clinvar_base_url: str = CLINVAR_BASE_URL,
    run_date: str | None = None,
) -> dict:
    if not os.path.isfile(genome):
        raise GenomeCheckError(f"Genome file not found: {genome}")
    if paths_equal(out_dir, genome):
        raise GenomeCheckError(f"Refusing to write over the genome file: {genome}")
    selected = parse_classes(classes)
    selected_set = set(selected)
    run_date = run_date or date.today().isoformat()
    previous_payload = None
    previous_key_set: set[str] = set()
    ids_by_key: dict[str, list[str]] = {}
    if previous:
        previous_payload = load_json(previous)
        previous_key_set, ids_by_key = previous_interest(previous_payload)
    with GenomeReader(genome) as reader:
        genome_meta = reader.inspect(build)
        if reader.kind == "vcf":
            sample_name, sample_index, sample_note = choose_sample(genome_meta["samples"], sample)
        else:
            if sample:
                raise GenomeCheckError("A chip file has no sample column, so --sample does not apply.")
            sample_name, sample_index, sample_note = None, None, ""
        if clinvar:
            progress("Using the local ClinVar file.")
            clinvar_meta = describe_local_clinvar(clinvar, genome_meta["build"])
        else:
            dest = clinvar_dir or out_dir
            if paths_equal(dest, genome):
                raise GenomeCheckError(f"Refusing to write over the genome file: {genome}")
            clinvar_meta = acquire_clinvar(
                build=genome_meta["build"],
                dest_dir=dest,
                base_url=clinvar_base_url,
                genome_path=genome,
            )
            clinvar = clinvar_meta["clinvar_path"]
            header = read_vcf_header_lines(clinvar)
            assert_clinvar_reference(header, genome_meta["build"])
        md_path, json_path, diff_path = output_paths(
            out_dir, run_date, clinvar_meta["clinvar_release_raw"]
        )
        planned = [md_path, json_path]
        if previous_payload is not None:
            planned.append(diff_path)
        refuse_genome_collision(planned, genome)
        existing = [path for path in planned if os.path.lexists(path)]
        if existing:
            names = ", ".join(existing)
            raise GenomeCheckError(
                f"Output file already exists: {names}. This tool never overwrites."
            )
        if not os.path.isdir(out_dir):
            os.makedirs(out_dir, exist_ok=True)
        by_key, by_pos, lookup = index_clinvar(
            clinvar, selected_set, previous_key_set, ids_by_key
        )
        hits, filtered, counts = match_genome(
            reader, by_key, by_pos, sample_index=sample_index
        )
    payload = build_payload(
        genome_meta=genome_meta,
        sample_name=sample_name,
        sample_note=sample_note,
        clinvar_meta=clinvar_meta,
        selected=selected,
        hits=hits,
        filtered=filtered,
        counts=counts,
        run_date=run_date,
        previous_lookup=lookup if previous_payload is not None else None,
    )
    report = render_report(payload)
    write_exclusive(md_path, report)
    write_exclusive(json_path, json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    progress(f"Wrote {os.path.basename(md_path)}")
    progress(f"Wrote {os.path.basename(json_path)}")
    if previous_payload is not None:
        diff_text = render_diff(previous_payload, payload)
        write_exclusive(diff_path, diff_text)
        progress(f"Wrote {os.path.basename(diff_path)}")
    return {"markdown": md_path, "json": json_path, "diff": diff_path if previous_payload is not None else None}


def run_diff(old_path: str, new_path: str, out_path: str) -> str:
    if paths_equal(out_path, old_path) or paths_equal(out_path, new_path):
        raise GenomeCheckError(f"Refusing to write the diff onto an input file: {out_path}")
    old = load_json(old_path)
    new = load_json(new_path)
    text = render_diff(old, new)
    parent = os.path.dirname(os.path.abspath(out_path))
    if parent and not os.path.isdir(parent):
        os.makedirs(parent, exist_ok=True)
    write_exclusive(out_path, text)
    progress(f"Wrote {os.path.basename(out_path)}")
    return out_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="genome_check.py",
        description="Compare a genome file with ClinVar on this computer.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    detect = sub.add_parser("detect", help="Say what a genome file is, and which reference build it uses.")
    detect.add_argument("--genome", required=True, help="Path to the genome file.")
    detect.add_argument("--build", choices=["GRCh37", "GRCh38"], help="Use this build instead of detecting one.")

    run = sub.add_parser("run", help="Write a Markdown report and a JSON file.")
    run.add_argument("--genome", required=True, help="Path to the genome file. It is only read.")
    run.add_argument("--out-dir", required=True, help="Folder for the report. Existing files there are left as they are.")
    run.add_argument("--clinvar", help="A ClinVar VCF or VCF.gz already on this computer. Nothing is downloaded.")
    run.add_argument("--clinvar-dir", help="Folder for a downloaded ClinVar file. Defaults to --out-dir.")
    run.add_argument("--build", choices=["GRCh37", "GRCh38"], help="Use this build instead of detecting one.")
    run.add_argument("--sample", help="Sample column, when the VCF has more than one.")
    run.add_argument("--previous", help="JSON from an earlier run, used to describe what changed.")
    run.add_argument(
        "--classes",
        help=(
            "Comma-separated ClinVar terms to keep. Spaces or underscores, any case. "
            "An unknown term stops the run and lists the accepted terms."
        ),
    )
    run.add_argument("--clinvar-base-url", default=CLINVAR_BASE_URL, help=argparse.SUPPRESS)

    diff = sub.add_parser("diff", help="Compare two JSON reports and write a Markdown file.")
    diff.add_argument("old_json", help="JSON from the earlier run.")
    diff.add_argument("new_json", help="JSON from the later run.")
    diff.add_argument("--out", required=True, help="Markdown file to write. It must not already exist.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "detect":
            info = inspect_genome(args.genome, args.build)
            sys.stdout.write(format_detect(info))
            return 0
        if args.command == "run":
            run_check(
                genome=args.genome,
                out_dir=args.out_dir,
                clinvar=args.clinvar,
                clinvar_dir=args.clinvar_dir,
                build=args.build,
                sample=args.sample,
                previous=args.previous,
                classes=args.classes,
                clinvar_base_url=args.clinvar_base_url,
            )
            return 0
        if args.command == "diff":
            run_diff(args.old_json, args.new_json, args.out)
            return 0
    except GenomeCheckError as exc:
        print(exc.message, file=sys.stderr)
        return 1
    return 2


if __name__ == "__main__":
    sys.exit(main())
