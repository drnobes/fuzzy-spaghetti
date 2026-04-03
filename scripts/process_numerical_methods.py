#!/usr/bin/env python3
"""
Process Numerical_Methods folder: enrich metadata, generate .bibs, rename.

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
        "original": "An_Introduction_to_the_Mathematics_of_Financial_Derivatives-Salih-Neftci.pdf",
        "rename": "Introduction_Mathematics_Financial_Derivatives-Salih_Neftci.pdf",
        "meta": {
            "title": "An Introduction to the Mathematics of Financial Derivatives",
            "authors": [["Neftci", "Salih N."]],
            "date": "2000-01-01",
            "publisher": "Academic Press",
            "institution": "",
            "identifier": "ISBN 0-12-515392-9",
            "abstract": "A comprehensive textbook covering the mathematical foundations of financial derivatives pricing, including calculus in deterministic and stochastic environments, probability theory, martingales, differentiation and integration in stochastic environments, the Wiener process, Ito's lemma, Black-Scholes PDE, and numerical methods for pricing.",
            "keywords": ["financial derivatives", "stochastic calculus", "Ito's lemma", "Black-Scholes", "martingales", "Wiener process", "option pricing", "numerical methods"],
            "doc_type": "book",
            "language": "en",
        },
    },
    {
        "original": "Better_Approximations_to_Cumulative_Normal_Functions-Graeme_West.pdf",
        "rename": "Better_Approximations_to_Cumulative_Normal_Functions-Graeme_West.pdf",
        "meta": {
            "title": "Better Approximations to Cumulative Normal Functions",
            "authors": [["West", "Graeme"]],
            "date": "2004-12-08",
            "publisher": "",
            "institution": "",
            "identifier": "",
            "abstract": "Compares numerical approximations to the cumulative normal distribution function, including the Abramowitz & Stegun polynomial, Hart's rational function, and Excel's NORMSDIST. Shows the Hart algorithm achieves double precision accuracy throughout the real line, and discusses implications for bivariate and multivariate cumulative normals, inverse normal computation via Moro transform, and Newton/Halley refinement methods.",
            "keywords": ["cumulative normal", "numerical approximation", "Hart algorithm", "Abramowitz Stegun", "bivariate normal", "Moro transform", "option pricing"],
            "doc_type": "article",
            "language": "en",
        },
    },
    {
        "original": "Chebyshev_Methods_for_Ultra_Efficient_Risk_Calculations-Mariano_Laris.pdf",
        "rename": "Chebyshev_Methods_Ultra_Efficient_Risk_Calculations-Mariano_Zeron_Medina_Laris.pdf",
        "meta": {
            "title": "Chebyshev Methods for Ultra-efficient Risk Calculations: Spectral Decomposition Applications in Risk Management",
            "authors": [["Zeron Medina Laris", "Mariano"], ["Ruiz", "Ignacio"]],
            "date": "2018-04-01",
            "publisher": "",
            "institution": "MoCaX Intelligence, London",
            "identifier": "",
            "abstract": "Shows how Chebyshev interpolation techniques can reduce the computational effort of risk calculations by orders of magnitude. Pricing functions are approximated via Chebyshev interpolants that show exponential convergence, enabling ultra-efficient revaluation for XVAs, IMM on exotics, XVA sensitivities, Initial Margin Simulations, IMA-FRTB, and AAD.",
            "keywords": ["Chebyshev interpolation", "spectral decomposition", "risk management", "XVA", "FRTB", "IMM", "initial margin", "AAD", "numerical methods"],
            "doc_type": "article",
            "language": "en",
        },
    },
    {
        "original": "Fast_Monte_Carlo_Valuation_Of_American_Options-Yves-Hilpisch.pdf",
        "rename": "Fast_Monte_Carlo_American_Options-Yves_Hilpisch.pdf",
        "meta": {
            "title": "Fast Monte Carlo Valuation of American Options under Stochastic Volatility and Interest Rates",
            "authors": [["Hilpisch", "Yves J."]],
            "date": "2011-08-01",
            "publisher": "",
            "institution": "Visixion GmbH",
            "identifier": "",
            "abstract": "Analyzes the valuation of American options by Monte Carlo simulation in the presence of stochastic volatility and interest rates. Demonstrates that a Python implementation of the Least-Squares Monte Carlo (LSM) algorithm with control variates takes less than one second per American option valuation, matching accuracy consistent with typical bid-ask spreads and tick sizes.",
            "keywords": ["American options", "Monte Carlo", "least-squares Monte Carlo", "LSM", "stochastic volatility", "Heston model", "CIR", "control variates", "Python"],
            "doc_type": "article",
            "language": "en",
        },
    },
    {
        "original": "Kenneth_Geddes_Wilson-Andreas_Kronfeld.pdf",
        "rename": "Kenneth_Geddes_Wilson-Andreas_Kronfeld.pdf",
        "meta": {
            "title": "Kenneth Geddes Wilson",
            "authors": [["Kronfeld", "Andreas S."]],
            "date": "2013-12-24",
            "publisher": "Proceedings of Science",
            "institution": "Fermi National Accelerator Laboratory",
            "identifier": "arXiv:1312.6861",
            "abstract": "A retrospective on Kenneth Wilson's contributions to theoretical physics — the operator product expansion, renormalization group, critical phenomena, lattice gauge theory, and the Kondo problem — with personal reminiscences from the author's time as a graduate student at Cornell in the 1980s.",
            "keywords": ["Kenneth Wilson", "renormalization group", "lattice gauge theory", "critical phenomena", "Kondo problem", "operator product expansion", "Nobel Prize"],
            "doc_type": "inproceedings",
            "language": "en",
        },
    },
    {
        "original": "Roll_Models-Tadashi_Tokieda.pdf",
        "rename": "Roll_Models-Tadashi_Tokieda.pdf",
        "meta": {
            "title": "Roll Models",
            "authors": [["Tokieda", "Tadashi"]],
            "date": "2013-03-01",
            "publisher": "American Mathematical Monthly",
            "institution": "Trinity Hall, Cambridge",
            "identifier": "doi:10.4169/amer.math.monthly.120.03.265",
            "abstract": "A case study of applied mathematics for beginning students via problems of rolling. Points out diverse surprising phenomena — from cylinders on pulled sheets to oloids and developable surfaces — modeling them and testing the limits of these models. Demonstrates that rolling tightly coordinates different modes of motion and is more exactly solvable than meets the eye.",
            "keywords": ["rolling", "applied mathematics", "rigid body dynamics", "angular momentum", "contact mechanics", "oloid", "developable surfaces"],
            "doc_type": "article",
            "language": "en",
        },
    },
    {
        "original": "Stochastic_Calculus_Review-Robert_Kohn.pdf",
        "rename": "Stochastic_Calculus_Review-Robert_Kohn.pdf",
        "meta": {
            "title": "PDE for Finance Notes — Stochastic Calculus Review",
            "authors": [["Kohn", "Robert V."]],
            "date": "2003-01-01",
            "publisher": "",
            "institution": "Courant Institute of Mathematical Sciences, NYU",
            "identifier": "NYU G63.2706",
            "abstract": "Lecture notes reviewing basic stochastic calculus for the NYU course PDE for Finance. Covers Brownian motion, filtrations and conditional expectations, martingales, Ito's formula, stochastic differential equations, the Feynman-Kac formula, and the Black-Scholes equation. Designed as prerequisite review material.",
            "keywords": ["stochastic calculus", "Brownian motion", "Ito's formula", "martingales", "Feynman-Kac", "Black-Scholes", "SDE", "PDE for finance"],
            "doc_type": "misc",
            "language": "en",
        },
    },
]


def process_all():
    import tempfile

    folder = Path(os.path.expanduser("~/PycharmProjects/Papers/Numerical_Methods"))
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
    print(f"Processed {len(PAPERS)} papers in Numerical_Methods/")
    print(f"Run 'fz-ingest --vectors' to rebuild indices.")


if __name__ == "__main__":
    process_all()
