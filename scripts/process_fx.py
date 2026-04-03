#!/usr/bin/env python3
"""
Process FX folder: enrich metadata, generate .bibs, rename.

Follows the pdf-cleaner skill pipeline (steps 5-10):
- Metadata extracted by reading each PDF
- Enrich PDF with XMP + /Info metadata
- Generate companion .bib file
- Rename to library convention
- Move original to processed/

Note: "Guide to cad ba market 2.pdf" is skipped (duplicate).
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


# ── All 7 papers with hand-extracted metadata ──────────────────────────────
# Note: "Guide to cad ba market 2.pdf" excluded (duplicate of "Guide to cad ba market.pdf")

PAPERS = [
    {
        "original": "Foreign_Exchange_Trading_Manual-Lehman_Brothers.pdf",
        "rename": "Foreign_Exchange_Trading_Manual-Lehman_Brothers.pdf",
        "meta": {
            "title": "Foreign Exchange Training Manual",
            "authors": [],
            "date": "2008-01-01",
            "publisher": "Lehman Brothers",
            "institution": "Lehman Brothers",
            "identifier": "",
            "abstract": "Internal training manual covering FX spot, forwards, exchange rate quotation conventions, cross rates, bid-offer mechanics, and trading conventions.",
            "keywords": ["foreign exchange", "FX spot", "FX forwards", "cross rates", "trading conventions", "market making"],
            "doc_type": "misc",
            "language": "en",
        },
    },
    {
        "original": "JPM_Cross_currency_basis_2018-10-04_2791563.pdf",
        "rename": "Cross_Currency_Basis_4Q18_Outlook-Fabio_Bassi.pdf",
        "meta": {
            "title": "Cross Currency Basis 4Q18 Outlook",
            "authors": [["Bassi", "Fabio"], ["Younger", "Joshua"]],
            "date": "2018-10-04",
            "publisher": "J.P. Morgan",
            "institution": "J.P. Morgan Securities",
            "identifier": "JPM-2791563",
            "abstract": "Short term factors support wider front end FX OIS basis with steepening bias from light reverse Yankee issuance.",
            "keywords": ["cross-currency basis", "FX OIS", "FRA/OIS", "Libor", "funding", "basis swap"],
            "doc_type": "techreport",
            "language": "en",
        },
    },
    {
        "original": "BAML-GLOBAL_FX_WEEKLY-20170324.pdf",
        "rename": "Global_FX_Weekly_Q1_Insights-BAML.pdf",
        "meta": {
            "title": "Global FX Weekly: Q1 Insights for Q2",
            "authors": [["Vamvakidis", "Athanasios"], ["Piron", "Claudio"], ["Kyriacou", "Myria"]],
            "date": "2017-03-24",
            "publisher": "Bank of America Merrill Lynch",
            "institution": "Bank of America Merrill Lynch",
            "identifier": "",
            "abstract": "Weekly FX strategy report covering G10 and EM positioning, factor analysis, regional views, and technical analysis.",
            "keywords": ["FX strategy", "G10", "emerging markets", "positioning", "Brexit", "central banks"],
            "doc_type": "techreport",
            "language": "en",
        },
    },
    {
        "original": "SSRN-id3906716.pdf",
        "rename": "Dynamic_Currency_Hedging_Ambiguity-Pawel_Polak.pdf",
        "meta": {
            "title": "Dynamic Currency Hedging with Ambiguity",
            "authors": [["Polak", "Pawel"], ["Ulrych", "Urban"]],
            "date": "2021-08-01",
            "publisher": "Swiss Finance Institute",
            "institution": "Stony Brook University; University of Zurich",
            "identifier": "SSRN:3906716",
            "abstract": "Develops an ambiguity-adjusted dynamic currency hedging strategy using filtered historical simulation and non-Gaussian returns.",
            "keywords": ["currency hedging", "ambiguity", "filtered historical simulation", "expected shortfall", "currency risk"],
            "doc_type": "article",
            "language": "en",
        },
    },
    {
        "original": "Guide to cad ba market.pdf",
        "rename": "Primer_Canadian_Bankers_Acceptance_Market-Kaetlynd_McRae.pdf",
        "meta": {
            "title": "A Primer on the Canadian Bankers' Acceptance Market",
            "authors": [["McRae", "Kaetlynd"], ["Auger", "Danny"]],
            "date": "2018-06-01",
            "publisher": "Bank of Canada",
            "institution": "Bank of Canada",
            "identifier": "Staff Discussion Paper 2018-6",
            "abstract": "Discusses how the bankers' acceptance market in Canada is organized and its link to CDOR.",
            "keywords": ["bankers acceptance", "CDOR", "Canadian money market", "financial institutions", "market structure"],
            "doc_type": "techreport",
            "language": "en",
        },
    },
    {
        "original": "The_Foreign_Exchange_Market-ACI.pdf",
        "rename": "The_Foreign_Exchange_Market-ACI.pdf",
        "meta": {
            "title": "The Foreign Exchange Market",
            "authors": [],
            "date": "2001-01-01",
            "publisher": "ACI",
            "institution": "ACI - The Financial Markets Association",
            "identifier": "",
            "abstract": "Chapter on FX market fundamentals from the ACI Dealing Certificate guide, covering spot rates, quotation conventions, settlement, forwards, and swaps.",
            "keywords": ["foreign exchange", "FX spot", "exchange rates", "ACI dealing certificate", "FX forwards", "FX swaps"],
            "doc_type": "misc",
            "language": "en",
        },
    },
    {
        "original": "JPM_Funding_markets_dive_2018-12-03_2852139.pdf",
        "rename": "Funding_Markets_Diverge_Yellow_Wood-Joshua_Younger.pdf",
        "meta": {
            "title": "Funding Markets Diverge in a Yellow Wood",
            "authors": [["Younger", "Joshua"], ["Roever", "Alex"], ["Ho", "Teresa C"]],
            "date": "2018-12-03",
            "publisher": "J.P. Morgan",
            "institution": "J.P. Morgan Securities LLC",
            "identifier": "JPM-2852139",
            "abstract": "FX and unsecured short-term funding markets have diverged as year-end turn narrowed while FRA/OIS remained wide.",
            "keywords": ["funding markets", "FX-OIS basis", "FRA/OIS", "G-SIB", "year-end turn"],
            "doc_type": "techreport",
            "language": "en",
        },
    },
]


def process_all():
    import tempfile

    folder = Path(os.path.expanduser("~/PycharmProjects/Papers/FX"))
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
    print(f"Processed {len(PAPERS)} papers in FX/")
    print(f"Run 'fz-ingest --vectors' to rebuild indices.")


if __name__ == "__main__":
    process_all()
