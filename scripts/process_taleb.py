#!/usr/bin/env python3
"""
Process Taleb folder: enrich metadata, generate .bibs, rename.

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


# ── All 5 papers with hand-extracted metadata ────────────────────────────

PAPERS = [
    {
        "original": "Dynamic_Hedging-Nassim_Taleb.pdf",
        "rename": "Dynamic_Hedging-Nassim_Taleb.pdf",
        "meta": {
            "title": "Dynamic Hedging: Managing Vanilla and Exotic Options",
            "authors": [["Taleb", "Nassim"]],
            "date": "1997-01-01",
            "publisher": "John Wiley & Sons",
            "institution": "",
            "identifier": "",
            "abstract": "Comprehensive treatment of dynamic hedging for vanilla and exotic options from a practitioner perspective.",
            "keywords": ["options", "dynamic hedging", "risk management", "exotic options", "vanilla options", "Greeks"],
            "doc_type": "book",
            "language": "en",
        },
    },
    {
        "original": "Silent_Risk-Nassim_Taleb.pdf",
        "rename": "Silent_Risk-Nassim_Taleb.pdf",
        "meta": {
            "title": "Silent Risk: Lectures on Probability, Vol. 1",
            "authors": [["Taleb", "Nassim Nicholas"]],
            "date": "2015-01-01",
            "publisher": "DesCartes Publishing",
            "institution": "",
            "identifier": "",
            "abstract": "Mathematical parallel version of the Incerto with derivations, theorems, and heuristics on probability and risk.",
            "keywords": ["probability", "risk", "fat tails", "Incerto", "statistics", "uncertainty"],
            "doc_type": "book",
            "language": "en",
        },
    },
    {
        "original": "A_Map_and_Simple_Heuristic_to_Detect_Fragility-Nassim_Taleb.pdf",
        "rename": "Map_Heuristic_Fragility_Antifragility-Nassim_Taleb.pdf",
        "meta": {
            "title": "A Map and Simple Heuristic to Detect Fragility, Antifragility, and Model Error",
            "authors": [["Taleb", "Nassim Nicholas"]],
            "date": "2010-06-04",
            "publisher": "",
            "institution": "NYU Polytechnic Institute",
            "identifier": "SSRN 1864633",
            "abstract": "Defines fragility and antifragility as sensitivity to second-order effects and proposes a model-free heuristic for detection.",
            "keywords": ["fragility", "antifragility", "model error", "convexity", "nonlinearity", "heuristic", "tail risk"],
            "doc_type": "article",
            "language": "en",
        },
    },
    {
        "original": "How_We_Tend_To_Overestimate_Powerlaw_Tail_Exponents-Nassim_Taleb.pdf",
        "rename": "Overestimate_Powerlaw_Tail_Exponents-Nassim_Taleb.pdf",
        "meta": {
            "title": "How We Tend To Overestimate Powerlaw Tail Exponents",
            "authors": [["Taleb", "Nassim Nicholas"]],
            "date": "2012-10-01",
            "publisher": "",
            "institution": "NYU Polytechnic Institute",
            "identifier": "",
            "abstract": "Shows that with metaprobabilities, asymptotic tail exponent corresponds to the lowest possible regardless of probability, explaining chronic underestimation of tail contributions.",
            "keywords": ["power laws", "tail exponents", "metaprobability", "fat tails", "Black Swan", "estimation error"],
            "doc_type": "article",
            "language": "en",
        },
    },
    {
        "original": "Cook.1998.HowComplexSystemsFailRevG.pdf",
        "rename": "How_Complex_Systems_Fail-Richard_Cook.pdf",
        "meta": {
            "title": "How Complex Systems Fail",
            "authors": [["Cook", "Richard I."]],
            "date": "1998-01-01",
            "publisher": "",
            "institution": "University of Chicago",
            "identifier": "",
            "abstract": "Short treatise on the nature of failure in complex systems, how failure is evaluated and attributed to proximate cause, with implications for patient safety.",
            "keywords": ["complex systems", "failure", "patient safety", "catastrophe", "system safety"],
            "doc_type": "techreport",
            "language": "en",
        },
    },
]


def process_all():
    import tempfile

    folder = Path(os.path.expanduser("~/PycharmProjects/Papers/Taleb"))
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
    print(f"Processed {len(PAPERS)} papers in Taleb/")
    print(f"Run 'fz-ingest --vectors' to rebuild indices.")


if __name__ == "__main__":
    process_all()
