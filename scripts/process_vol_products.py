#!/usr/bin/env python3
"""
Process Vol_Products folder: enrich metadata, generate .bibs, rename.

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


# ── All 7 papers with hand-extracted metadata ──────────────────────────────

PAPERS = [
    {
        "original": "A_Market_Model_For_VIX_Futures-Alexander_Badran.pdf",
        "rename": "A_Market_Model_For_VIX_Futures-Alexander_Badran.pdf",
        "meta": {
            "title": "A Market Model for VIX Futures",
            "authors": [["Badran", "Alexander"], ["Goldys", "Beniamin"]],
            "date": "2015-04-03",
            "publisher": "arXiv",
            "institution": "",
            "identifier": "arXiv:1504.00428v1",
            "abstract": "A new modelling approach that directly prescribes dynamics to the term structure of VIX futures, deriving necessary conditions for no arbitrage analogous to HJM drift restrictions.",
            "keywords": ["VIX", "VIX futures", "VIX options", "market model", "HJM", "stochastic volatility"],
            "doc_type": "article",
            "language": "en",
        },
    },
    {
        "original": "Robust_Replication_of_Volatility_Derivatives-Peter_Carr.pdf",
        "rename": "Robust_Replication_of_Volatility_Derivatives-Peter_Carr.pdf",
        "meta": {
            "title": "Robust Replication of Volatility Derivatives",
            "authors": [["Carr", "Peter"], ["Lee", "Roger"]],
            "date": "2009-05-31",
            "publisher": "",
            "institution": "Bloomberg LP / Courant Institute; University of Chicago",
            "identifier": "",
            "abstract": "Nonparametric trading strategies to replicate volatility derivatives using the underlying asset and vanilla options, with formulas for volatility swaps and variance options.",
            "keywords": ["volatility derivatives", "variance swaps", "robust replication", "nonparametric pricing"],
            "doc_type": "article",
            "language": "en",
        },
    },
    {
        "original": "SSRN-id3723837.pdf",
        "rename": "VIX_Futures_Term_Structure_Expectations-Ivan_Asensio.pdf",
        "meta": {
            "title": "VIX Futures Term Structure and Expectations Hypothesis",
            "authors": [["Asensio", "Ivan Oscar"]],
            "date": "2019-04-01",
            "publisher": "SSRN",
            "institution": "University of San Francisco",
            "identifier": "SSRN:3723837",
            "abstract": "Tests expectations hypothesis on the VIX futures term structure, finding the slope predicts direction but not magnitude of short-end evolution. Spread trades deliver Sharpe ratios comparable to volatility-writing strategies.",
            "keywords": ["VIX futures", "term structure", "expectations hypothesis", "volatility trading", "ETN"],
            "doc_type": "article",
            "language": "en",
        },
    },
    {
        "original": "SSRN-id3871384.pdf",
        "rename": "Option_Implied_Spreads_And_Risk_Premia-Christopher_Culp.pdf",
        "meta": {
            "title": "Option-Implied Spreads and Option Risk Premia",
            "authors": [["Culp", "Christopher L."], ["Gandhi", "Mihir"], ["Nozawa", "Yoshio"], ["Veronesi", "Pietro"]],
            "date": "2021-06-11",
            "publisher": "SSRN",
            "institution": "Johns Hopkins; University of Chicago; HKUST",
            "identifier": "SSRN:3871384",
            "abstract": "Proposes implied spreads and normalized implied spreads as measures to characterize option prices, analyzing their countercyclical behavior and return predictability.",
            "keywords": ["implied spreads", "option risk premia", "put options", "tail risk", "stochastic volatility"],
            "doc_type": "article",
            "language": "en",
        },
    },
    {
        "original": "SSRN-id3930703.pdf",
        "rename": "Volatility_Uncertainty_Disasters_VIX_Contango-Gurdip_Bakshi.pdf",
        "meta": {
            "title": "Volatility Uncertainty, Disasters, and VIX Futures Contango",
            "authors": [["Bakshi", "Gurdip"], ["Crosby", "John"], ["Gao", "Xiaohui"], ["Xue", "Jinming"]],
            "date": "2021-10-25",
            "publisher": "SSRN",
            "institution": "Temple University; University of Maryland; SMU",
            "identifier": "SSRN:3930703",
            "abstract": "Explains VIX futures contango and backwardation via stochastic orders of volatility uncertainty and disaster probability dynamics.",
            "keywords": ["volatility uncertainty", "VIX futures curve", "stochastic orders", "contango", "backwardation"],
            "doc_type": "article",
            "language": "en",
        },
    },
    {
        "original": "Vix_WhitePaper-CBOE.pdf",
        "rename": "Vix_WhitePaper-CBOE.pdf",
        "meta": {
            "title": "The CBOE Volatility Index - VIX",
            "authors": [],
            "date": "2009-01-01",
            "publisher": "CBOE",
            "institution": "Chicago Board Options Exchange",
            "identifier": "",
            "abstract": "White paper on VIX methodology: estimates expected 30-day volatility by averaging weighted prices of SPX puts and calls over a wide range of strike prices.",
            "keywords": ["VIX", "volatility index", "CBOE", "S&P 500", "implied volatility"],
            "doc_type": "techreport",
            "language": "en",
        },
    },
    {
        "original": "Volatility_Derivatives_Practical_Notes-Fabien_Le_Floch.pdf",
        "rename": "Volatility_Derivatives_Practical_Notes-Fabien_Le_Floch.pdf",
        "meta": {
            "title": "Volatility Derivatives Practical Notes",
            "authors": [["Le Floc'h", "Fabien"]],
            "date": "2015-03-10",
            "publisher": "SSRN",
            "institution": "Calypso Technology, Paris",
            "identifier": "SSRN:2620166",
            "abstract": "Practical notes on pricing volatility derivatives with the Carr-Lee methodology, with attention to oscillatory integrands and Filon quadrature.",
            "keywords": ["volatility derivatives", "Carr-Lee", "Filon quadrature", "oscillatory integrand", "variance swaps"],
            "doc_type": "article",
            "language": "en",
        },
    },
]


def process_all():
    import tempfile

    folder = Path(os.path.expanduser("~/PycharmProjects/Papers/Vol_Products"))
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
    print(f"Processed {len(PAPERS)} papers in Vol_Products/")
    print(f"Run 'fz-ingest --vectors' to rebuild indices.")


if __name__ == "__main__":
    process_all()
