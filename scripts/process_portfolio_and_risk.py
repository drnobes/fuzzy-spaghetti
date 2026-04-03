#!/usr/bin/env python3
"""
Process Portfolio_and_Risk folder: enrich metadata, generate .bibs, rename.

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


# ── All 24 papers with hand-extracted metadata ─────────────────────────────

PAPERS = [
    {
        "original": "1701.01427.pdf",
        "rename": "Rational_Decision_Making_Biased_Coin-Victor_Haghani.pdf",
        "meta": {
            "title": "Rational Decision-Making Under Uncertainty: Observed Betting Patterns on a Biased Coin",
            "authors": [["Haghani", "Victor"], ["Dewey", "Richard"]],
            "date": "2017-01-04",
            "publisher": "",
            "institution": "Elm Partners",
            "identifier": "arXiv:1701.01427",
            "abstract": "Participants were given $25 to bet on a biased coin (60% heads) for 30 minutes, revealing even financially trained subjects fail to apply Kelly criterion.",
            "keywords": ["Kelly criterion", "betting", "decision making", "uncertainty", "behavioral finance"],
            "doc_type": "article",
            "language": "en",
        },
    },
    {
        "original": "2101.01006.pdf",
        "rename": "Design_Analysis_Momentum_Trading_Strategies-Richard_Martin.pdf",
        "meta": {
            "title": "Design and Analysis of Momentum Trading Strategies",
            "authors": [["Martin", "Richard J."]],
            "date": "2021-01-05",
            "publisher": "",
            "institution": "Imperial College London",
            "identifier": "arXiv:2101.01006",
            "abstract": "Complete description of skewness characteristics of linear and nonlinear momentum strategies, explaining why skewness is generally positive with a term structure.",
            "keywords": ["momentum", "trend following", "skewness", "EMA", "trading strategies", "CTA", "signal processing"],
            "doc_type": "article",
            "language": "en",
        },
    },
    {
        "original": "A_review_of_two_decades_of_correlations_hierarchies_networks_and_clustering-Gautier_Marti.pdf",
        "rename": "A_review_of_two_decades_of_correlations_hierarchies_networks_and_clustering-Gautier_Marti.pdf",
        "meta": {
            "title": "A Review of Two Decades of Correlations, Hierarchies, Networks and Clustering in Financial Markets",
            "authors": [["Marti", "Gautier"], ["Nielsen", "Frank"], ["Binkowski", "Mikolaj"], ["Donnat", "Philippe"]],
            "date": "2017-03-01",
            "publisher": "",
            "institution": "Hellebore Capital; Ecole Polytechnique; Imperial College London",
            "identifier": "arXiv:1703.00485",
            "abstract": "In-depth review of clustering financial time series and correlation networks, covering MST-based methodology and alternatives.",
            "keywords": ["financial time series", "cluster analysis", "correlation", "complex networks", "econophysics", "minimum spanning tree"],
            "doc_type": "article",
            "language": "en",
        },
    },
    {
        "original": "An_Introduction_To_Modern_Portfolio_Theory-Graeme_West.pdf",
        "rename": "An_Introduction_To_Modern_Portfolio_Theory-Graeme_West.pdf",
        "meta": {
            "title": "An Introduction to Modern Portfolio Theory: Markowitz, CAP-M, APT and Black-Litterman",
            "authors": [["West", "Graeme"]],
            "date": "2006-06-26",
            "publisher": "",
            "institution": "Financial Modelling Agency",
            "identifier": "",
            "abstract": "Introduction covering Markowitz, CAPM, APT, and Black-Litterman with derivations and practical considerations.",
            "keywords": ["Markowitz", "CAPM", "APT", "Black-Litterman", "portfolio theory", "efficient frontier", "mean-variance"],
            "doc_type": "techreport",
            "language": "en",
        },
    },
    {
        "original": "Black_Was_Right_Price_Is_Within_A_Factor_Of_2_Of_Value-J_Bouchaud.pdf",
        "rename": "Black_Was_Right_Price_Is_Within_A_Factor_Of_2_Of_Value-J_Bouchaud.pdf",
        "meta": {
            "title": "Black Was Right: Price Is Within a Factor of 2 of Value",
            "authors": [["Bouchaud", "Jean-Philippe"], ["Ciliberti", "Stefano"], ["Lemperiere", "Yves"], ["Majewski", "Adam"], ["Seager", "Philip"], ["Sin Ronia", "Kolbjorn"]],
            "date": "2017-11-15",
            "publisher": "",
            "institution": "Capital Fund Management",
            "identifier": "arXiv:1711.04717",
            "abstract": "Evidence that markets trend on medium term and mean-revert on long term, bolstering Fisher Black's factor of 2 intuition.",
            "keywords": ["trend following", "mean-reversion", "market efficiency", "Fisher Black", "behavioral biases", "autocorrelation"],
            "doc_type": "article",
            "language": "en",
        },
    },
    {
        "original": "Costly trading.pdf",
        "rename": "Costly_Trading-Michael_Isichenko.pdf",
        "meta": {
            "title": "Costly Trading",
            "authors": [["Isichenko", "Michael"]],
            "date": "2021-10-07",
            "publisher": "",
            "institution": "",
            "identifier": "arXiv:2110.15239",
            "abstract": "Revisits optimal execution with slippage costs, showing optimal no-trade zone width scales as square root of slippage cost.",
            "keywords": ["trading costs", "slippage", "optimal execution", "no-trade zone", "portfolio optimization", "transaction costs"],
            "doc_type": "article",
            "language": "en",
        },
    },
    {
        "original": "EndToReplicationFinal.pdf",
        "rename": "An_End_To_Replication-Patrick_Hagan.pdf",
        "meta": {
            "title": "An End to Replication",
            "authors": [["Hagan", "Patrick S."], ["Woodward", "Diana E."]],
            "date": "2008-01-01",
            "publisher": "",
            "institution": "Gorilla Science",
            "identifier": "",
            "abstract": "Uses SABR model for explicit expressions for quadratic swaps, calls, and puts, replacing traditional replication approach.",
            "keywords": ["SABR", "convexity corrections", "replication", "quadratic derivatives", "CMS", "swaptions", "volatility smile"],
            "doc_type": "article",
            "language": "en",
        },
    },
    {
        "original": "Kellys_Criterion_in_Portfolio_Optimization-Zachariah_Peterson.pdf",
        "rename": "Kellys_Criterion_in_Portfolio_Optimization-Zachariah_Peterson.pdf",
        "meta": {
            "title": "Kelly's Criterion in Portfolio Optimization: A Decoupled Problem",
            "authors": [["Peterson", "Zachariah"]],
            "date": "2017-07-31",
            "publisher": "",
            "institution": "Adams State University",
            "identifier": "doi:10.20944/preprints201707.0090.v1",
            "abstract": "Shows how Kelly's Criterion can be incorporated into portfolio optimization using differential evolution and Monte Carlo verification.",
            "keywords": ["Kelly criterion", "portfolio optimization", "differential evolution", "mean-variance", "geometric mean", "risk management"],
            "doc_type": "article",
            "language": "en",
        },
    },
    {
        "original": "Market_Risk_Analysis_V1-Carol_Alexander.pdf",
        "rename": "Market_Risk_Analysis_V1-Carol_Alexander.pdf",
        "meta": {
            "title": "Market Risk Analysis, Volume I: Quantitative Methods in Finance",
            "authors": [["Alexander", "Carol"]],
            "date": "2008-01-01",
            "publisher": "John Wiley & Sons",
            "institution": "",
            "identifier": "ISBN:978-0-470-99800-7",
            "abstract": "Volume I covering quantitative methods including probability, statistics, linear algebra, calculus, and numerical methods for financial risk analysis.",
            "keywords": ["quantitative methods", "finance", "statistics", "probability", "linear algebra", "risk analysis", "numerical methods"],
            "doc_type": "book",
            "language": "en",
        },
    },
    {
        "original": "Market_Risk_Analysis_V2-Carol_Alexander.pdf",
        "rename": "Market_Risk_Analysis_V2-Carol_Alexander.pdf",
        "meta": {
            "title": "Market Risk Analysis, Volume II: Practical Financial Econometrics",
            "authors": [["Alexander", "Carol"]],
            "date": "2008-01-01",
            "publisher": "John Wiley & Sons",
            "institution": "",
            "identifier": "ISBN:978-0-470-99801-4",
            "abstract": "Volume II covering financial econometrics including GARCH, volatility estimation, covariance matrices, and PCA.",
            "keywords": ["financial econometrics", "GARCH", "volatility", "time series", "covariance", "PCA", "risk modeling"],
            "doc_type": "book",
            "language": "en",
        },
    },
    {
        "original": "Market_Risk_Analysis_V3-Carol_Alexander.pdf",
        "rename": "Market_Risk_Analysis_V3-Carol_Alexander.pdf",
        "meta": {
            "title": "Market Risk Analysis, Volume III: Pricing, Hedging and Trading Financial Instruments",
            "authors": [["Alexander", "Carol"]],
            "date": "2008-01-01",
            "publisher": "John Wiley & Sons",
            "institution": "",
            "identifier": "ISBN:978-0-470-99802-1",
            "abstract": "Volume III covering pricing, hedging, and trading of bonds, futures, options, and swaps with emphasis on risk management.",
            "keywords": ["pricing", "hedging", "trading", "options", "bonds", "futures", "derivatives", "market risk"],
            "doc_type": "book",
            "language": "en",
        },
    },
    {
        "original": "Market_Risk_Analysis_V4-Carol_Alexander.pdf",
        "rename": "Market_Risk_Analysis_V4-Carol_Alexander.pdf",
        "meta": {
            "title": "Market Risk Analysis, Volume IV: Value-at-Risk Models",
            "authors": [["Alexander", "Carol"]],
            "date": "2008-01-01",
            "publisher": "John Wiley & Sons",
            "institution": "",
            "identifier": "ISBN:978-0-470-99788-8",
            "abstract": "Volume IV covering VaR models including historical simulation, Monte Carlo, parametric VaR, stress testing, and backtesting.",
            "keywords": ["Value-at-Risk", "VaR", "risk models", "Monte Carlo", "historical simulation", "stress testing", "backtesting"],
            "doc_type": "book",
            "language": "en",
        },
    },
    {
        "original": "Principal_Component_Analysis-Graeme_West.pdf",
        "rename": "Principal_Component_Analysis-Graeme_West.pdf",
        "meta": {
            "title": "Principal Component Analysis",
            "authors": [["West", "Graeme"]],
            "date": "2008-09-28",
            "publisher": "",
            "institution": "Financial Modelling Agency",
            "identifier": "",
            "abstract": "Mathematics of PCA including eigenvalue decomposition with applications to portfolio risk, scenario generation, and portfolio selection.",
            "keywords": ["PCA", "principal component analysis", "eigenvalue decomposition", "covariance matrix", "portfolio risk", "dimensionality reduction"],
            "doc_type": "techreport",
            "language": "en",
        },
    },
    {
        "original": "SSRN-id1879855.pdf",
        "rename": "Understanding_Asset_Correlations-Dominic_Burkhardt.pdf",
        "meta": {
            "title": "Understanding Asset Correlations",
            "authors": [["Burkhardt", "Dominic"], ["Hasseltoft", "Henrik"]],
            "date": "2012-01-01",
            "publisher": "Swiss Finance Institute",
            "institution": "University of Zurich",
            "identifier": "SSRN:1879855",
            "abstract": "Research examining the drivers and dynamics of asset correlations.",
            "keywords": ["asset correlations", "portfolio diversification", "correlation dynamics", "risk management", "covariance", "asset allocation"],
            "doc_type": "article",
            "language": "en",
        },
    },
    {
        "original": "SSRN-id2460551.pdf",
        "rename": "Deflated_Sharpe_Ratio-David_Bailey.pdf",
        "meta": {
            "title": "The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting and Non-Normality",
            "authors": [["Bailey", "David H."], ["Lopez de Prado", "Marcos"]],
            "date": "2014-07-31",
            "publisher": "Journal of Portfolio Management",
            "institution": "Lawrence Berkeley National Laboratory; Guggenheim Partners",
            "identifier": "SSRN:2460551",
            "abstract": "Introduces the Deflated Sharpe Ratio correcting for selection bias under multiple testing and non-normal returns.",
            "keywords": ["Sharpe ratio", "backtest overfitting", "selection bias", "non-normality", "multiple testing", "performance measurement"],
            "doc_type": "article",
            "language": "en",
        },
    },
    {
        "original": "SSRN-id2488552.pdf",
        "rename": "Rebalancing_Risk-Nick_Granger.pdf",
        "meta": {
            "title": "Rebalancing Risk",
            "authors": [["Granger", "Nick"], ["Greenig", "Doug"], ["Harvey", "Campbell R."], ["Rattray", "Sandy"], ["Zou", "David"]],
            "date": "2014-10-03",
            "publisher": "",
            "institution": "Man-AHL; Duke University; NBER",
            "identifier": "SSRN:2488552",
            "abstract": "Shows rebalancing to fixed weights induces negative convexity by magnifying drawdowns. A momentum overlay can reduce this risk.",
            "keywords": ["rebalancing", "portfolio construction", "negative convexity", "momentum overlay", "60-40 portfolio", "drawdowns"],
            "doc_type": "article",
            "language": "en",
        },
    },
    {
        "original": "SSRN-id2831926.pdf",
        "rename": "Trend_Following_Equity_Bond_Crisis_Alpha-Carl_Hamill.pdf",
        "meta": {
            "title": "Trend Following: Equity and Bond Crisis Alpha",
            "authors": [["Hamill", "Carl"], ["Rattray", "Sandy"], ["Van Hemert", "Otto"]],
            "date": "2016-08-30",
            "publisher": "",
            "institution": "Man AHL",
            "identifier": "SSRN:2831926",
            "abstract": "Studies time-series momentum finding consistent performance, positive skewness, and strong crisis alpha during worst drawdowns.",
            "keywords": ["trend following", "momentum", "crisis alpha", "skewness", "bonds", "equities", "commodities", "tail risk"],
            "doc_type": "article",
            "language": "en",
        },
    },
    {
        "original": "SSRN-id3175538.pdf",
        "rename": "Impact_Of_Volatility_Targeting-Campbell_Harvey.pdf",
        "meta": {
            "title": "The Impact of Volatility Targeting",
            "authors": [["Harvey", "Campbell R."], ["Hoyle", "Edward"], ["Korgaonkar", "Russell"], ["Rattray", "Sandy"], ["Sargaison", "Matthew"], ["Van Hemert", "Otto"]],
            "date": "2018-06-25",
            "publisher": "",
            "institution": "Duke University; Man Group",
            "identifier": "SSRN:3175538",
            "abstract": "Volatility-managed portfolios realize higher Sharpe ratios via the leverage effect while reducing extreme return likelihood.",
            "keywords": ["volatility targeting", "risk parity", "Sharpe ratio", "leverage effect", "asset allocation", "tail risk"],
            "doc_type": "article",
            "language": "en",
        },
    },
    {
        "original": "SSRN-id3330134.pdf",
        "rename": "Strategic_Rebalancing-Sandy_Rattray.pdf",
        "meta": {
            "title": "Strategic Rebalancing",
            "authors": [["Rattray", "Sandy"], ["Granger", "Nicolas"], ["Harvey", "Campbell R."], ["Van Hemert", "Otto"]],
            "date": "2019-12-19",
            "publisher": "",
            "institution": "Man Group; Duke University",
            "identifier": "SSRN:3330134",
            "abstract": "Proposes strategic rebalancing using trend-following signals to time rebalances, mitigating negative convexity without direct trend allocation.",
            "keywords": ["asset allocation", "smart rebalancing", "market timing", "momentum", "60-40 portfolio", "drawdown", "trend following"],
            "doc_type": "article",
            "language": "en",
        },
    },
    {
        "original": "SSRN-id3383173.pdf",
        "rename": "Best_Strategies_Worst_Times-Campbell_Harvey.pdf",
        "meta": {
            "title": "The Best of Strategies for the Worst of Times: Can Portfolios Be Crisis Proofed?",
            "authors": [["Harvey", "Campbell R."], ["Hoyle", "Edward"], ["Rattray", "Sandy"], ["Sargaison", "Matthew"], ["Taylor", "Dan"], ["Van Hemert", "Otto"]],
            "date": "2019-05-17",
            "publisher": "",
            "institution": "Duke University; Man Group",
            "identifier": "SSRN:3383173",
            "abstract": "Analyzes defensive strategies for equity drawdowns finding momentum and quality provide the best cost-reliability tradeoff.",
            "keywords": ["crisis hedge", "crisis alpha", "portfolio protection", "momentum", "quality factor", "drawdown", "safe-haven"],
            "doc_type": "article",
            "language": "en",
        },
    },
    {
        "original": "SSRN-id3657604.pdf",
        "rename": "Extreme_Stock_Market_Performers_Drawdowns-Hendrik_Bessembinder.pdf",
        "meta": {
            "title": "Extreme Stock Market Performers, Part I: Expect Some Drawdowns",
            "authors": [["Bessembinder", "Hendrik"]],
            "date": "2020-07-01",
            "publisher": "",
            "institution": "Arizona State University",
            "identifier": "SSRN:3657604",
            "abstract": "Documents that even the 100 most successful stocks per decade experienced average drawdowns of 32.5% within their best decade.",
            "keywords": ["drawdowns", "stock returns", "wealth creation", "equity performance", "long-term investing", "return distribution"],
            "doc_type": "article",
            "language": "en",
        },
    },
    {
        "original": "Supervisory_Guidance_on_Model_Risk_Management-Comptroller.pdf",
        "rename": "Supervisory_Guidance_on_Model_Risk_Management-Comptroller.pdf",
        "meta": {
            "title": "Supervisory Guidance on Model Risk Management",
            "authors": [["Board of Governors of the Federal Reserve System", ""], ["Office of the Comptroller of the Currency", ""]],
            "date": "2011-04-04",
            "publisher": "OCC / Federal Reserve",
            "institution": "Federal Reserve; OCC",
            "identifier": "OCC 2011-12",
            "abstract": "Comprehensive guidance for banks on model risk management covering development, implementation, validation, governance, and controls.",
            "keywords": ["model risk", "model validation", "banking regulation", "OCC", "Federal Reserve", "risk management", "governance"],
            "doc_type": "techreport",
            "language": "en",
        },
    },
    {
        "original": "barra_handbook_US.pdf",
        "rename": "Barra_US_Equity_Risk_Model_Handbook-Barra.pdf",
        "meta": {
            "title": "United States Equity Version 3 (E3) Risk Model Handbook",
            "authors": [["BARRA", ""]],
            "date": "1998-02-01",
            "publisher": "BARRA, Inc.",
            "institution": "BARRA, Inc.",
            "identifier": "",
            "abstract": "Technical handbook for the BARRA US Equity Risk Model Version 3, documenting multi-factor risk model methodology.",
            "keywords": ["BARRA", "risk model", "factor model", "US equities", "covariance estimation", "risk factors", "portfolio risk"],
            "doc_type": "techreport",
            "language": "en",
        },
    },
    {
        "original": "The_role_of_the_Model_Validation_Function-Alberto_Elices.pdf",
        "rename": "The_role_of_the_Model_Validation_Function-Alberto_Elices.pdf",
        "meta": {
            "title": "The Role of the Model Validation Function to Manage and Mitigate Model Risk",
            "authors": [["Elices", "Alberto"]],
            "date": "2012-11-02",
            "publisher": "",
            "institution": "Santander",
            "identifier": "arXiv:1211.0225",
            "abstract": "Describes model risk taxonomy, mitigation strategies, and the model validation function's role in risk controls.",
            "keywords": ["model risk", "model validation", "pricing models", "risk management", "fixed income", "calibration risk"],
            "doc_type": "article",
            "language": "en",
        },
    },
]


def process_all():
    import tempfile

    folder = Path(os.path.expanduser("~/PycharmProjects/Papers/Portfolio_and_Risk"))
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
    print(f"Processed {len(PAPERS)} papers in Portfolio_and_Risk/")
    print(f"Run 'fz-ingest --vectors' to rebuild indices.")


if __name__ == "__main__":
    process_all()
