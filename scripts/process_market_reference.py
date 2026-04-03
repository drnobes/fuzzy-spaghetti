#!/usr/bin/env python3
"""
Process Market_Reference folder: enrich metadata, generate .bibs, rename.

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


# ── All 5 papers with hand-extracted metadata ──────────────────────────────

PAPERS = [
    {
        "original": "JPM-The-Golden-Age-of-Quant.pdf",
        "rename": "Golden_Age_of_Quant-Eric_Sorensen.pdf",
        "meta": {
            "title": "The Golden Age of Quant",
            "authors": [["Sorensen", "Eric H."]],
            "date": "2019-11-01",
            "publisher": "The Journal of Portfolio Management",
            "institution": "PanAgora Asset Management",
            "identifier": "",
            "abstract": "Cover article for The Journal of Portfolio Management on the evolution and current state of quantitative investing.",
            "keywords": ["quantitative investing", "portfolio management", "asset management"],
            "doc_type": "article",
            "language": "en",
        },
    },
    {
        "original": "HP_12C_Users_Guide-HP.pdf",
        "rename": "HP_12C_Users_Guide-HP.pdf",
        "meta": {
            "title": "HP 12C Financial Calculator User's Guide",
            "authors": [],
            "date": "2004-08-01",
            "publisher": "Hewlett-Packard",
            "institution": "Hewlett-Packard Company",
            "identifier": "HP Part Number 0012C-90001",
            "abstract": "User's guide for the HP 12C financial calculator covering financial calculations including time value of money, bond pricing, and statistical functions.",
            "keywords": ["financial calculator", "HP 12C", "time value of money", "bond pricing"],
            "doc_type": "misc",
            "language": "en",
        },
    },
    {
        "original": "Fed_Funds_Futures_Reference_Guide-CBOT.pdf",
        "rename": "Fed_Funds_Futures_Reference_Guide-CBOT.pdf",
        "meta": {
            "title": "Reference Guide: CBOT Fed Funds Futures",
            "authors": [],
            "date": "2003-01-01",
            "publisher": "Chicago Board of Trade",
            "institution": "Chicago Board of Trade",
            "identifier": "",
            "abstract": "Reference guide for CBOT 30-Day Fed Funds futures covering contract pricing, final settlement, strip rates, and policy shift probability calculation.",
            "keywords": ["fed funds futures", "CBOT", "interest rate products", "monetary policy"],
            "doc_type": "techreport",
            "language": "en",
        },
    },
    {
        "original": "Futures_File_Format_Guide.pdf",
        "rename": "Global_Futures_File_Format-Tick_Data.pdf",
        "meta": {
            "title": "Global Futures Trade and Quote Data File Format Document",
            "authors": [],
            "date": "2010-01-01",
            "publisher": "Tick Data, LLC",
            "institution": "Tick Data, LLC",
            "identifier": "",
            "abstract": "File format specification for Tick Data's global futures trade and quote data covering exchanges worldwide.",
            "keywords": ["tick data", "futures", "file format", "trade data", "quote data"],
            "doc_type": "misc",
            "language": "en",
        },
    },
    {
        "original": "Daily_Settlement_file_layout-CME.pdf",
        "rename": "Daily_Settlement_File_Layout-CME.pdf",
        "meta": {
            "title": "Daily Settlement File Layout",
            "authors": [],
            "date": "2009-10-06",
            "publisher": "CME Group",
            "institution": "CME Group",
            "identifier": "",
            "abstract": "Specification for CME Group daily settlement file layout covering futures and options with 11 columns including price, volume, and open interest data.",
            "keywords": ["CME", "daily settlement", "futures", "options", "file layout"],
            "doc_type": "misc",
            "language": "en",
        },
    },
]


def process_all():
    import tempfile

    folder = Path(os.path.expanduser("~/PycharmProjects/Papers/Market_Reference"))
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
    print(f"Processed {len(PAPERS)} papers in Market_Reference/")
    print(f"Run 'fz-ingest --vectors' to rebuild indices.")


if __name__ == "__main__":
    process_all()
