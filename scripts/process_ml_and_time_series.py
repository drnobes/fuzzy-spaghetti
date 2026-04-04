#!/usr/bin/env python3
"""
Process ML_and_Time_Series folder: enrich metadata, generate .bibs, rename.

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


# ── All 13 papers with hand-extracted metadata (skip duplicate) ───────────

PAPERS = [
    {
        "original": "1810.01278.pdf",
        "rename": "Deep_Factor_Model-Kei_Nakagawa.pdf",
        "meta": {
            "title": "Deep Factor Model: Explaining Deep Learning Decisions for Forecasting Stock Returns with Layer-wise Relevance Propagation",
            "authors": [["Nakagawa", "Kei"], ["Uchida", "Takumi"], ["Aoshima", "Tomohisa"]],
            "date": "2018-10-01",
            "publisher": "arXiv",
            "institution": "Nomura Asset Management; Fujitsu; University of Tsukuba",
            "identifier": "arXiv:1810.01278",
            "abstract": "Construct a multifactor model using interpretable deep learning with layer-wise relevance propagation to decompose predicted returns.",
            "keywords": ["deep learning", "factor model", "LRP", "stock returns", "machine learning"],
            "doc_type": "article",
            "language": "en",
        },
    },
    {
        "original": "1810.02125.pdf",
        "rename": "ML_Recommendation_Swaptions_Strategies-Adriano_Koshiyama.pdf",
        "meta": {
            "title": "A Machine Learning-based Recommendation System for Swaptions Strategies",
            "authors": [["Koshiyama", "Adriano Soares"], ["Firoozye", "Nick"], ["Treleaven", "Philip"]],
            "date": "2018-10-05",
            "publisher": "arXiv",
            "institution": "University College London",
            "identifier": "arXiv:1810.02125",
            "abstract": "Trading recommendation system for Mid-Curve Calendar Spread swaption packages using lasso regression.",
            "keywords": ["swaptions", "trading recommendation", "machine learning", "MCCS", "lasso"],
            "doc_type": "article",
            "language": "en",
        },
    },
    {
        "original": "1903.04841.pdf",
        "rename": "Financial_Applications_Gaussian_Processes-Joan_Gonzalvez.pdf",
        "meta": {
            "title": "Financial Applications of Gaussian Processes and Bayesian Optimization",
            "authors": [["Gonzalvez", "Joan"], ["Lezmi", "Edmond"], ["Roncalli", "Thierry"], ["Xu", "Jiali"]],
            "date": "2019-02-01",
            "publisher": "arXiv",
            "institution": "Amundi Asset Management",
            "identifier": "arXiv:1903.04841",
            "abstract": "Explores Gaussian processes and Bayesian optimization for term structure modeling and trend-following strategy construction.",
            "keywords": ["Gaussian process", "Bayesian optimization", "machine learning", "term structure", "trend following"],
            "doc_type": "article",
            "language": "en",
        },
    },
    {
        "original": "2007.10462v1.pdf",
        "rename": "Deep_Local_Volatility-Marc_Chataigner.pdf",
        "meta": {
            "title": "Deep Local Volatility",
            "authors": [["Chataigner", "Marc"], ["Crepey", "Stephane"], ["Dixon", "Matthew"]],
            "date": "2020-07-22",
            "publisher": "arXiv",
            "institution": "University of Evry; Illinois Institute of Technology",
            "identifier": "arXiv:2007.10462",
            "abstract": "Deep learning approach for European option interpolation that jointly yields local volatility surfaces with no-arbitrage constraints via Dupire formula.",
            "keywords": ["deep learning", "local volatility", "option pricing", "no-arbitrage", "Dupire formula"],
            "doc_type": "article",
            "language": "en",
        },
    },
    {
        "original": "2106.03035.pdf",
        "rename": "Online_Trading_Forex_Transaction_Costs-Koya_Ishikawa.pdf",
        "meta": {
            "title": "Online Trading Models in the Forex Market Considering Transaction Costs",
            "authors": [["Ishikawa", "Koya"], ["Nakata", "Kazuhide"]],
            "date": "2021-06-08",
            "publisher": "arXiv",
            "institution": "Tokyo Institute of Technology",
            "identifier": "arXiv:2106.03035",
            "abstract": "Deep reinforcement learning trading agent for forex using online learning with transaction cost awareness.",
            "keywords": ["deep reinforcement learning", "forex", "online learning", "transaction costs", "trading"],
            "doc_type": "article",
            "language": "en",
        },
    },
    {
        "original": "2106.10024.pdf",
        "rename": "Robust_Deep_Hedging-Eva_Lutkebohmert.pdf",
        "meta": {
            "title": "Robust Deep Hedging",
            "authors": [["Lutkebohmert", "Eva"], ["Schmidt", "Thorsten"], ["Sester", "Julian"]],
            "date": "2021-06-21",
            "publisher": "arXiv",
            "institution": "University of Freiburg; NTU Singapore",
            "identifier": "arXiv:2106.10024",
            "abstract": "Deep hedging approach under parameter uncertainty for generalized affine processes, outperforming existing methods in volatile periods.",
            "keywords": ["deep hedging", "robust hedging", "Knightian uncertainty", "Kolmogorov equation", "deep learning"],
            "doc_type": "article",
            "language": "en",
        },
    },
    {
        "original": "Deep_Learning_A_Critical_Appraisal-Gary_Marcus.pdf",
        "rename": "Deep_Learning_Critical_Appraisal-Gary_Marcus.pdf",
        "meta": {
            "title": "Deep Learning: A Critical Appraisal",
            "authors": [["Marcus", "Gary"]],
            "date": "2018-01-02",
            "publisher": "arXiv",
            "institution": "New York University",
            "identifier": "arXiv:1801.00631",
            "abstract": "Presents ten concerns for deep learning and argues it must be supplemented by other techniques to reach artificial general intelligence.",
            "keywords": ["deep learning", "artificial general intelligence", "neural networks", "machine learning", "limitations"],
            "doc_type": "article",
            "language": "en",
        },
    },
    {
        "original": "JIS_FuzzyTradingSystem.pdf",
        "rename": "Intelligent_Trading_Fuzzy_Rules-Rodrigo_Naranjo.pdf",
        "meta": {
            "title": "An Intelligent Trading System with Fuzzy Rules and Fuzzy Capital Management",
            "authors": [["Naranjo", "Rodrigo"], ["Meco", "Albert"], ["Arroyo", "Javier"], ["Santos", "Matilde"]],
            "date": "2015-01-01",
            "publisher": "Wiley",
            "institution": "Universidad Complutense de Madrid",
            "identifier": "",
            "abstract": "Trading system applying fuzzy logic for both trading rules and capital management, with a new MACD-based indicator optimized by genetic algorithms.",
            "keywords": ["trading", "fuzzy logic", "decision making", "optimal-F", "capital management", "genetic algorithms"],
            "doc_type": "article",
            "language": "en",
        },
    },
    {
        "original": "Non_Stationary_Time_Series_Cointegration_And_Spurious_Regression-Heino_Bohn_Nielsen.pdf",
        "rename": "Non_Stationary_Time_Series_Cointegration-Heino_Nielsen.pdf",
        "meta": {
            "title": "Non-Stationary Time Series, Cointegration and Spurious Regression",
            "authors": [["Nielsen", "Heino Bohn"]],
            "date": "2005-09-01",
            "publisher": "",
            "institution": "University of Copenhagen",
            "identifier": "",
            "abstract": "Lecture notes on non-stationarity, cointegration, and spurious regression for econometrics.",
            "keywords": ["non-stationarity", "cointegration", "spurious regression", "unit roots", "error correction"],
            "doc_type": "misc",
            "language": "en",
        },
    },
    {
        "original": "SSRN-id3776322.pdf",
        "rename": "Valuing_Exotic_Options_Model_Risk-Jay_Cao.pdf",
        "meta": {
            "title": "Valuing Exotic Options and Estimating Model Risk",
            "authors": [["Cao", "Jay"], ["Chen", "Jacky"], ["Hull", "John"], ["Poulos", "Zissis"]],
            "date": "2021-03-01",
            "publisher": "SSRN",
            "institution": "Rotman School of Management, University of Toronto",
            "identifier": "SSRN:3776322",
            "abstract": "Volatility feature approach using neural networks to value exotic options from volatility surface inputs, outperforming model calibration approach.",
            "keywords": ["exotic options", "volatility surfaces", "neural networks", "model risk", "VFA"],
            "doc_type": "article",
            "language": "en",
        },
    },
    {
        "original": "SSRN-id3881993.pdf",
        "rename": "Jumping_Vol_Surface_Exotic_Pricing-Roman_Paolucci.pdf",
        "meta": {
            "title": "Jumping from Volatility Surface to Exotic Option Price",
            "authors": [["Paolucci", "Roman"]],
            "date": "2021-06-01",
            "publisher": "SSRN",
            "institution": "Bloomberg LP",
            "identifier": "SSRN:3881993",
            "abstract": "Variational autoencoders trained on market data generate training surfaces for neural network exotic option pricing, improving on model-generated surfaces.",
            "keywords": ["volatility surface", "exotic option pricing", "variational autoencoder", "neural networks", "VFA"],
            "doc_type": "article",
            "language": "en",
        },
    },
    {
        "original": "Ten_Things_We_Should_Know_About_Time_Series-Michael_McAleer.pdf",
        "rename": "Ten_Things_About_Time_Series-Michael_McAleer.pdf",
        "meta": {
            "title": "Ten Things We Should Know About Time Series",
            "authors": [["McAleer", "Michael"], ["Oxley", "Les"]],
            "date": "2010-06-01",
            "publisher": "",
            "institution": "Erasmus University Rotterdam; University of Canterbury",
            "identifier": "EI 2010-49",
            "abstract": "Highlights ten things we should know about time series including unit roots, VARFIMA, cointegration, volatility models, and forecasting.",
            "keywords": ["unit roots", "fractional integration", "long memory", "VARFIMA", "cointegration", "volatility", "forecasting"],
            "doc_type": "article",
            "language": "en",
        },
    },
    {
        "original": "Understanding_the_Basis_of_the_Kalman_Filter-Ramsey_Faragher.pdf",
        "rename": "Understanding_Kalman_Filter-Ramsey_Faragher.pdf",
        "meta": {
            "title": "Understanding the Basis of the Kalman Filter Via a Simple and Intuitive Derivation",
            "authors": [["Faragher", "Ramsey"]],
            "date": "2012-09-01",
            "publisher": "IEEE",
            "institution": "",
            "identifier": "10.1109/MSP.2012.2203621",
            "abstract": "Simple and intuitive derivation of the Kalman filter using the property that the product of two Gaussians is another Gaussian.",
            "keywords": ["Kalman filter", "state estimation", "Gaussian distribution", "data fusion", "Bayesian filtering"],
            "doc_type": "article",
            "language": "en",
        },
    },
]


def process_all():
    import tempfile

    folder = Path(os.path.expanduser("~/PycharmProjects/Papers/ML_and_Time_Series"))
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
    print(f"Processed {len(PAPERS)} papers in ML_and_Time_Series/")
    print(f"Run 'fz-ingest --vectors' to rebuild indices.")


if __name__ == "__main__":
    process_all()
