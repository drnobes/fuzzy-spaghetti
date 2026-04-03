#!/usr/bin/env python3
"""
Process Macro_and_Economics folder: enrich metadata, generate .bibs, rename.

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


# ── All 8 papers with hand-extracted metadata ──────────────────────────────

PAPERS = [
    {
        "original": "1-s2.0-S1057521915001477-main.pdf",
        "rename": "Lost_Century_Three_Theories_Banking-Richard_Werner.pdf",
        "meta": {
            "title": "A lost century in economics: Three theories of banking and the conclusive evidence",
            "authors": [["Werner", "Richard A."]],
            "date": "2015-09-08",
            "publisher": "Elsevier",
            "institution": "University of Southampton",
            "identifier": "doi:10.1016/j.irfa.2015.08.014",
            "abstract": "Reviews three theories of banking: financial intermediation, fractional reserve, and credit creation. Presents empirical evidence that individual banks create money when granting loans.",
            "keywords": ["bank credit", "credit creation", "money creation", "financial intermediation", "fractional reserve banking"],
            "doc_type": "article",
            "language": "en",
        },
    },
    {
        "original": "Functional_Finance_And_The_Federal_Debt-Abba_Lerner.pdf",
        "rename": "Functional_Finance_And_The_Federal_Debt-Abba_Lerner.pdf",
        "meta": {
            "title": "Functional Finance and the Federal Debt",
            "authors": [["Lerner", "Abba P."]],
            "date": "1943-02-01",
            "publisher": "Social Research",
            "institution": "",
            "identifier": "",
            "abstract": "Argues government fiscal policy should be judged by its economic results (Functional Finance), not traditional doctrines about sound finance.",
            "keywords": ["functional finance", "fiscal policy", "federal debt", "government spending", "money creation"],
            "doc_type": "article",
            "language": "en",
        },
    },
    {
        "original": "WP-Trouble.pdf",
        "rename": "Trouble_With_Macroeconomics-Paul_Romer.pdf",
        "meta": {
            "title": "The Trouble With Macroeconomics",
            "authors": [["Romer", "Paul"]],
            "date": "2016-09-14",
            "publisher": "",
            "institution": "Stern School of Business, NYU",
            "identifier": "",
            "abstract": "Argues macroeconomics has regressed over three decades, with opaque identification, dismissal of empirical facts, and deference to authority displacing scientific objectivity.",
            "keywords": ["macroeconomics", "identification", "DSGE", "monetary policy", "scientific methodology"],
            "doc_type": "article",
            "language": "en",
        },
    },
    {
        "original": "money_notes_24.pdf",
        "rename": "Global_Money_Notes_24_Sagittarius-Zoltan_Pozsar.pdf",
        "meta": {
            "title": "Global Money Notes #24: Sagittarius A*",
            "authors": [["Pozsar", "Zoltan"]],
            "date": "2019-08-21",
            "publisher": "Credit Suisse",
            "institution": "Credit Suisse",
            "identifier": "",
            "abstract": "Analyzes the foreign RRP facility as a black hole at the center of global dollar funding markets, driven by yield curve inversion.",
            "keywords": ["foreign RRP", "yield curve inversion", "reserves", "dollar funding", "Fed", "central banks"],
            "doc_type": "techreport",
            "language": "en",
        },
    },
    {
        "original": "JPM_Scary_stories_to_tel_2020-06-29_3414293.pdf",
        "rename": "Scary_Stories_COVID_Market_Panic-Joshua_Younger.pdf",
        "meta": {
            "title": "Scary stories to tell in the dark: How COVID-19 nearly took down one of the safest trades",
            "authors": [["Younger", "Joshua"], ["St John", "Henry"], ["Aggarwal", "Sejal"]],
            "date": "2020-06-29",
            "publisher": "J.P. Morgan",
            "institution": "J.P. Morgan Securities LLC",
            "identifier": "JPM-3414293",
            "abstract": "First draft of financial history examining the March 2020 COVID market panic, how post-2008 regulations substituted a liquidity crisis for a credit crisis, and the Fed's response.",
            "keywords": ["COVID-19", "liquidity crisis", "Treasury market", "cash futures basis", "Fed intervention", "bank regulation"],
            "doc_type": "techreport",
            "language": "en",
        },
    },
    {
        "original": "JPM_I_love_it_when_a_pla_2019-02-01_2901973.pdf",
        "rename": "SOFR_Derivatives_Progress_Report-Joshua_Younger.pdf",
        "meta": {
            "title": "I love it when a plan comes together: A SOFR derivatives progress report",
            "authors": [["Younger", "Joshua"], ["Salem", "Munier"], ["St John", "Henry"]],
            "date": "2019-02-01",
            "publisher": "J.P. Morgan",
            "institution": "J.P. Morgan Securities LLC",
            "identifier": "JPM-2901973",
            "abstract": "Progress report on SOFR derivatives market development. Activity in SOFR futures and FRNs continues to build with improving OTC derivatives liquidity.",
            "keywords": ["SOFR", "LIBOR transition", "interest rate derivatives", "swap curve", "FF/SOFR basis"],
            "doc_type": "techreport",
            "language": "en",
        },
    },
    {
        "original": "global-money-dispatch.pdf",
        "rename": "Global_Money_Dispatch_CB_Deposits-Zoltan_Pozsar.pdf",
        "meta": {
            "title": "Global Money Dispatch: Central Bank Deposits",
            "authors": [["Pozsar", "Zoltan"]],
            "date": "2020-10-08",
            "publisher": "Credit Suisse",
            "institution": "Credit Suisse",
            "identifier": "",
            "abstract": "Examines the central bank-to-bank deposit market (~$400B), analyzing how major FX reserve managers are the biggest depositors at G-SIBs and important participants in dollar funding markets.",
            "keywords": ["central bank deposits", "G-SIBs", "FX reserves", "LCR", "dollar funding"],
            "doc_type": "techreport",
            "language": "en",
        },
    },
    {
        "original": "Limits_To_Growth_Revisited-Vaclav_Smil.pdf",
        "rename": "Limits_To_Growth_Revisited-Vaclav_Smil.pdf",
        "meta": {
            "title": "Limits to Growth Revisited: A Review Essay",
            "authors": [["Smil", "Vaclav"]],
            "date": "2005-03-01",
            "publisher": "Population and Development Review",
            "institution": "",
            "identifier": "",
            "abstract": "Critical review of Limits to Growth: The 30-Year Update, arguing the original mixed truisms with arbitrary assumptions and the update added nothing of value.",
            "keywords": ["Limits to Growth", "Club of Rome", "system dynamics", "environmental modeling", "population", "resources"],
            "doc_type": "article",
            "language": "en",
        },
    },
]


def process_all():
    import tempfile

    folder = Path(os.path.expanduser("~/PycharmProjects/Papers/Macro_and_Economics"))
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
    print(f"Processed {len(PAPERS)} papers in Macro_and_Economics/")
    print(f"Run 'fz-ingest --vectors' to rebuild indices.")


if __name__ == "__main__":
    process_all()
