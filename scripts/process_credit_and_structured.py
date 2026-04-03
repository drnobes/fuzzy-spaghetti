#!/usr/bin/env python3
"""
Process Credit_and_Structured folder: enrich metadata, generate .bibs, rename.

Follows the pdf-cleaner skill pipeline (steps 5-10):
- Metadata extracted by reading each PDF
- Enrich PDF with XMP + /Info metadata
- Generate companion .bib file
- Rename to library convention
- Move original to processed/
"""

import json
import os
import shutil
import sys
from pathlib import Path

# Add parent so we can import the ClaudeConfig scripts
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

CLOUD = Path(os.path.expanduser("~/PycharmProjects/ClaudeConfig_Cloud"))
sys.path.insert(0, str(CLOUD / "skills/pdf-cleaner/scripts"))

from enrich_metadata import enrich_pdf
from generate_bib import generate_bib


# ── All 6 papers with hand-extracted metadata ──────────────────────────────

PAPERS = [
    {
        "original": "A_CDS_Option_Miscellany-Richard_J_Martin.pdf",
        "rename": "A_CDS_Option_Miscellany-Richard_Martin.pdf",
        "meta": {
            "title": "A CDS Option Miscellany",
            "authors": [["Martin", "Richard J."]],
            "date": "2017-09-08",
            "publisher": "arXiv",
            "institution": "",
            "identifier": "arXiv:1201.0111v2",
            "abstract": "Detailed exposition of single-name CDS option types including options with upfront protection payment, recovery options and recovery swaps, plus a new formula for the index option, emphasizing the Black'76 framework.",
            "keywords": ["CDS options", "credit default swaps", "Black76", "index options", "recovery swaps", "credit derivatives"],
            "doc_type": "article",
            "language": "en",
        },
    },
    {
        "original": "A_Guide_To_The_Loan_Market-Standard_and_Poors.pdf",
        "rename": "A_Guide_To_The_Loan_Market-Standard_and_Poors.pdf",
        "meta": {
            "title": "A Guide to the Loan Market",
            "authors": [["Standard & Poor's", ""]],
            "date": "2009-09-01",
            "publisher": "Standard & Poor's",
            "institution": "Standard & Poor's Financial Services LLC",
            "identifier": "",
            "abstract": "Comprehensive guide to the syndicated loan market covering loan types, credit ratings, recovery ratings, and market structure.",
            "keywords": ["leveraged loans", "syndicated loans", "credit ratings", "bank loans", "recovery ratings", "loan market"],
            "doc_type": "techreport",
            "language": "en",
        },
    },
    {
        "original": "A_Mortgage_Product_Primer-Goldman_Sachs.pdf",
        "rename": "A_Mortgage_Product_Primer-Goldman_Sachs.pdf",
        "meta": {
            "title": "A Mortgage Product Primer",
            "authors": [["Goldman Sachs", ""]],
            "date": "2004-10-01",
            "publisher": "Goldman, Sachs & Co.",
            "institution": "Goldman Sachs",
            "identifier": "",
            "abstract": "Primer covering mortgage products including MBS, agency vs non-agency, collateral types, CMBS, ABS, CDOs/CLOs, and constant maturity mortgages.",
            "keywords": ["MBS", "mortgage-backed securities", "CMBS", "subprime", "CDO", "CLO", "ABS"],
            "doc_type": "techreport",
            "language": "en",
        },
    },
    {
        "original": "Teaching_Note_On_Convertable_Bonds-Zhi_Da.pdf",
        "rename": "Teaching_Note_On_Convertible_Bonds-Zhi_Da.pdf",
        "meta": {
            "title": "Teaching Note on Convertible Bonds",
            "authors": [["Da", "Zhi"], ["Jagannathan", "Ravi"]],
            "date": "2004-08-05",
            "publisher": "",
            "institution": "Kellogg School of Management, Northwestern University",
            "identifier": "",
            "abstract": "Teaching note explaining convertible bond features, market structure, and valuation for FINC 460.",
            "keywords": ["convertible bonds", "bond valuation", "conversion ratio", "callable bonds", "fixed income", "hybrid securities"],
            "doc_type": "misc",
            "language": "en",
        },
    },
    {
        "original": "The_Formula_That_Killed_Wall_Street-Donald_MacKenzie.pdf",
        "rename": "The_Formula_That_Killed_Wall_Street-Donald_MacKenzie.pdf",
        "meta": {
            "title": "The Formula That Killed Wall Street? The Gaussian Copula and the Material Cultures of Modelling",
            "authors": [["MacKenzie", "Donald"], ["Spears", "Taylor"]],
            "date": "2012-06-01",
            "publisher": "",
            "institution": "University of Edinburgh",
            "identifier": "",
            "abstract": "Oral-history account of the Gaussian copula model's role in the credit crisis, examining evaluation cultures and organizational coordination.",
            "keywords": ["Gaussian copula", "credit crisis", "CDO", "default correlation", "financial modelling", "sociology of finance"],
            "doc_type": "article",
            "language": "en",
        },
    },
    {
        "original": "The_US_Leveraged_Loan_Market_A_Primer-Glenn_Yago.pdf",
        "rename": "The_US_Leveraged_Loan_Market_A_Primer-Glenn_Yago.pdf",
        "meta": {
            "title": "The U.S. Leveraged Loan Market: A Primer",
            "authors": [["Yago", "Glenn"], ["McCarthy", "Donald"]],
            "date": "2004-10-01",
            "publisher": "Milken Institute",
            "institution": "Milken Institute",
            "identifier": "",
            "abstract": "Primer on the U.S. leveraged loan market covering market structure, participants, and the role of leveraged lending in capital allocation.",
            "keywords": ["leveraged loans", "syndicated lending", "credit markets", "bank debt", "loan pricing", "corporate finance"],
            "doc_type": "techreport",
            "language": "en",
        },
    },
]


def process_all():
    import tempfile

    folder = Path(os.path.expanduser("~/PycharmProjects/Papers/Credit_and_Structured"))
    processed_dir = folder / "processed"
    processed_dir.mkdir(exist_ok=True)

    for i, paper in enumerate(PAPERS, 1):
        original = folder / paper["original"]
        if not original.exists():
            print(f"[{i}/{len(PAPERS)}] SKIP (not found): {paper['original']}")
            continue

        print(f"\n[{i}/{len(PAPERS)}] Processing: {paper['original']}")
        meta = paper["meta"]
        renamed = folder / paper["rename"]
        bib_path = renamed.with_suffix(".bib")

        try:
            # Step 1: Enrich PDF with XMP + /Info metadata
            print(f"  Enriching metadata...")
            tmp_enriched = tempfile.mktemp(suffix=".pdf")
            enrich_pdf(str(original), tmp_enriched, meta)

            # Step 2: Generate .bib file
            bib_content = generate_bib(meta, pdf_filename=paper["rename"])
            bib_path.write_text(bib_content + "\n")
            print(f"  → .bib: {bib_path.name}")

            # Step 3: Rename (move enriched to new name)
            shutil.move(tmp_enriched, str(renamed))
            print(f"  → Renamed: {paper['rename']}")

            # Step 4: Move original to processed/ (if name changed)
            if original.name != paper["rename"]:
                dest = processed_dir / original.name
                if not dest.exists():
                    shutil.move(str(original), str(dest))
                    print(f"  → Original moved to processed/")
                else:
                    original.unlink()
                    print(f"  → Original removed (already in processed/)")

        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()

        print()

    print(f"{'='*60}")
    print(f"Processed {len(PAPERS)} papers in Credit_and_Structured/")
    print(f"Run 'fz-ingest --vectors' to rebuild indices.")


if __name__ == "__main__":
    process_all()
