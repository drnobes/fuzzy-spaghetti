#!/usr/bin/env python3
"""
Process Vol_Surface_and_SABR folder: enrich metadata, generate .bibs, rename.

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


# ── All 41 papers with hand-extracted metadata ──────────────────────────────

PAPERS = [
    {
        "original": "1810.04868.pdf",
        "rename": "Lifting_The_Heston_Model-Eduardo_Abi_Jaber.pdf",
        "meta": {
            "title": "Lifting the Heston Model",
            "authors": [["Abi Jaber", "Eduardo"]],
            "date": "2018-10-12",
            "publisher": "arXiv",
            "institution": "AXA Investment Managers / Université Paris-Dauphine",
            "identifier": "arXiv:1810.04868",
            "abstract": "How to reconcile the classical Heston model with its rough counterpart? We introduce a lifted version of the Heston model with n multi-factors, sharing the same Brownian motion but mean reverting at different speeds. Our model nests as extreme cases the classical Heston model (when n=1), and the rough Heston model (when n goes to infinity). We show that the lifted model enjoys the best of both worlds: Markovianity and satisfactory fits of implied volatility smiles for short maturities with very few parameters.",
            "keywords": ["stochastic volatility", "implied volatility", "affine Volterra processes", "Riccati equations", "rough Heston", "lifted Heston"],
            "doc_type": "article",
            "language": "en",
        },
    },
    {
        "original": "1903.05747.pdf",
        "rename": "Fractional_And_Mixed_Fractional_CEV_Model-Axel_Araneda.pdf",
        "meta": {
            "title": "The Fractional and Mixed-Fractional CEV Model",
            "authors": [["Araneda", "Axel A."]],
            "date": "2019-03-15",
            "publisher": "arXiv",
            "institution": "Frankfurt Institute for Advanced Studies",
            "identifier": "arXiv:1903.05747",
            "abstract": "The continuous observation of the financial markets has identified some stylized facts which challenge the conventional assumptions, promoting the born of new approaches. The European Call price is derived in a compact and explicit way, in terms of the non-central-chi-squared distribution and the M-Whittaker function.",
            "keywords": ["CEV model", "fractional Brownian motion", "mixed-fractional", "option pricing", "long range dependence"],
            "doc_type": "article",
            "language": "en",
        },
    },
    {
        "original": "A_Note_ontheEquivalencebetweentheNormalandtheLognormalImpliedVolatility-Cyril_Grunspan.pdf",
        "rename": "Equivalence_Normal_Lognormal_Implied_Vol-Cyril_Grunspan.pdf",
        "meta": {
            "title": "A Note on the Equivalence between the Normal and the Lognormal Implied Volatility: A Model Free Approach",
            "authors": [["Grunspan", "Cyril"]],
            "date": "2011-12-09",
            "publisher": "arXiv",
            "institution": "ESILV, Department of Financial Engineering",
            "abstract": "First, we show that implied normal volatility is intimately linked with the incomplete Gamma function. Then, we deduce an expansion on implied normal volatility in terms of the time-value of a European call option.",
            "keywords": ["implied volatility", "normal volatility", "lognormal volatility", "Bachelier", "Black-Scholes"],
            "doc_type": "article",
            "language": "en",
        },
    },
    {
        "original": "Adjusters_Turning_Good_Prices_Into_Great_Prices_Wilmott-Patrick_Hagan.pdf",
        "rename": "Adjusters_Turning_Good_Prices_Into_Great_Prices-Patrick_Hagan.pdf",
        "meta": {
            "title": "Adjusters: Turning Good Prices into Great Prices",
            "authors": [["Hagan", "Patrick S."]],
            "date": "2003-01-01",
            "publisher": "Wilmott Magazine",
            "abstract": "We need to price and trade an exotic derivative, but because of limitations in our pricing systems, we cannot calibrate on the natural set of hedging instruments. Instead we have to calibrate to a different set of instruments, which leads to calibration errors. Adjusters correct for these errors systematically.",
            "keywords": ["exotic derivatives", "calibration", "vega risk", "swaptions", "volatility cube", "adjusters"],
            "doc_type": "article",
            "series": "Wilmott Magazine",
            "language": "en",
        },
    },
    {
        "original": "Alpha Heston model .pdf",
        "rename": "Alpha_Heston_Stochastic_Volatility_Model-Ying_Jiao.pdf",
        "meta": {
            "title": "The Alpha-Heston Stochastic Volatility Model",
            "authors": [["Jiao", "Ying"], ["Ma", "Chunhua"], ["Scotti", "Simone"], ["Zhou", "Chao"]],
            "date": "2018-12-06",
            "publisher": "arXiv",
            "abstract": "We introduce an affine extension of the Heston model where the instantaneous variance process contains a jump part driven by alpha-stable processes with alpha in (1,2]. In this framework, we examine the implied volatility and its asymptotic behaviors for both asset and variance options. Furthermore, we examine the jump clustering phenomenon observed on the variance market.",
            "keywords": ["stochastic volatility", "alpha-stable processes", "Heston model", "jump clustering", "variance options", "implied volatility"],
            "doc_type": "article",
            "language": "en",
        },
    },
    {
        "original": "An_Arbitrage_Free_Method_For_Smile_Extrapolation-Shalom_Benaim.pdf",
        "rename": "Arbitrage_Free_Smile_Extrapolation-Shalom_Benaim.pdf",
        "meta": {
            "title": "An Arbitrage-Free Method for Smile Extrapolation",
            "authors": [["Benaim", "Shalom"], ["Dodgson", "Matthew"], ["Kainth", "Dherminder"]],
            "date": "2008-01-01",
            "publisher": "Royal Bank of Scotland",
            "institution": "Royal Bank of Scotland",
            "abstract": "A robust method for pricing options at strikes where there is not an observed price is a vital tool for the pricing, hedging, and risk management of derivatives. We propose a method which works well for extrapolation across strikes, avoiding the breakdown of simple interpolation schemes at extreme strikes.",
            "keywords": ["smile extrapolation", "arbitrage-free", "implied volatility", "option pricing", "tail behavior"],
            "doc_type": "techreport",
            "language": "en",
        },
    },
    {
        "original": "Arbitrage_Free_Constructoin_Of_The_Swaption_Cube-Simon_Johnson.pdf",
        "rename": "Arbitrage_Free_Construction_Swaption_Cube-Simon_Johnson.pdf",
        "meta": {
            "title": "Arbitrage-Free Construction of the Swaption Cube",
            "authors": [["Johnson", "Simon"], ["Nonas", "Bereshad"]],
            "date": "2009-01-05",
            "publisher": "Commerzbank",
            "institution": "Commerzbank Corporates and Markets",
            "abstract": "In this paper we look at two areas in the interest rate options market where arbitrage could be hiding. We derive a no-arbitrage condition for swaption prices with complementary expiry dates and tenors within the swaption cube. We also propose an alternative European option approximation for the SABR dynamics that reduces the possibility of arbitrage.",
            "keywords": ["swaption cube", "arbitrage-free", "SABR", "interest rate options", "no-arbitrage condition"],
            "doc_type": "techreport",
            "language": "en",
        },
    },
    {
        "original": "Arbitrage_Free_Sabr_Draft-Patrick_Hagan.pdf",
        "rename": "Arbitrage_Free_SABR-Patrick_Hagan.pdf",
        "meta": {
            "title": "Arbitrage Free SABR",
            "authors": [["Hagan", "Patrick S."], ["Kumar", "Deep"]],
            "date": "2014-01-01",
            "publisher": "Working Paper",
            "institution": "AVM Ltd",
            "abstract": "Smile risk is often managed using the explicit implied vol formulas developed for the SABR model. These asymptotic formulas are not exact, and this can lead to arbitrage for low strike options. Here we provide an alternate method for pricing options under the SABR model: We use asymptotic techniques to reduce the SABR model from two dimensions to one dimension, leading to an effective one dimensional forward equation.",
            "keywords": ["SABR", "arbitrage-free", "implied volatility", "asymptotic expansion", "forward equation", "low strike"],
            "doc_type": "techreport",
            "language": "en",
        },
    },
    {
        "original": "Bartletts_delta_in_the_SABR_model-Patrick_Hagan.pdf",
        "rename": "Bartletts_Delta_In_The_SABR_Model-Patrick_Hagan.pdf",
        "meta": {
            "title": "Bartlett's Delta in the SABR Model",
            "authors": [["Hagan", "Patrick S."], ["Lesniewski", "Andrew"]],
            "date": "2017-04-12",
            "publisher": "Working Paper",
            "institution": "AVM L.P. / Baruch College",
            "abstract": "We refine the analysis of hedging strategies for options under the SABR model. In particular, we provide a theoretical justification of the empirical observation that the modified delta (Bartlett's delta) provides a superior hedge compared to the standard Black delta.",
            "keywords": ["SABR", "delta hedging", "Bartlett's delta", "Greeks", "stochastic volatility"],
            "doc_type": "techreport",
            "language": "en",
        },
    },
    {
        "original": "Calibration_Of_a_Four_Factor_Hybrid_LSV-Andrei-Cozma.pdf",
        "rename": "Four_Factor_Hybrid_LSV_Calibration-Andrei_Cozma.pdf",
        "meta": {
            "title": "Calibration of a Four-Factor Hybrid Local-Stochastic Volatility Model with a New Control Variate Particle Method",
            "authors": [["Cozma", "Andrei"], ["Mariapragassam", "Matthieu"], ["Reisinger", "Christoph"]],
            "date": "2018-01-01",
            "publisher": "Working Paper",
            "institution": "University of Oxford",
            "abstract": "We propose a novel and generic calibration technique for four-factor foreign-exchange hybrid local-stochastic volatility models with stochastic short rates. We build upon the particle method introduced by Guyon and Labordere and combine it with new variance reduction techniques.",
            "keywords": ["local-stochastic volatility", "calibration", "particle method", "FX options", "hybrid model", "stochastic rates"],
            "doc_type": "article",
            "language": "en",
        },
    },
    {
        "original": "Calibration_of_the_SABR_Model_in_Illiquid_Markets-Graeme_West.pdf",
        "rename": "SABR_Calibration_Illiquid_Markets-Graeme_West.pdf",
        "meta": {
            "title": "Calibration of the SABR Model in Illiquid Markets",
            "authors": [["West", "Graeme"]],
            "date": "2005-12-01",
            "publisher": "Applied Mathematical Finance",
            "institution": "Financial Modelling Agency / University of the Witwatersrand",
            "abstract": "Recently the SABR model has been developed to manage the option smile which is observed in derivatives markets. Typically, calibration of such models is straightforward when liquid option prices are available across a range of strikes. We address the problem of calibrating in illiquid markets.",
            "keywords": ["SABR", "calibration", "illiquid markets", "implied volatility", "smile"],
            "doc_type": "article",
            "series": "Applied Mathematical Finance",
            "page_range": "371-385",
            "language": "en",
        },
    },
    {
        "original": "Classes_of_Elementary_Function_Solutions_to_the_CEV_Model-Evangelos_Melas.pdf",
        "rename": "Elementary_Function_Solutions_CEV_Model-Evangelos_Melas.pdf",
        "meta": {
            "title": "Classes of Elementary Function Solutions to the CEV Model. I.",
            "authors": [["Melas", "Evangelos"]],
            "date": "2018-04-19",
            "publisher": "arXiv",
            "institution": "University of Athens, Department of Economics",
            "abstract": "Cox introduced the constant elasticity of variance (CEV) model in 1975, in order to capture the inverse relationship between stock price and volatility. We derive classes of elementary function solutions to the CEV model.",
            "keywords": ["CEV model", "constant elasticity of variance", "option pricing", "elementary functions"],
            "doc_type": "article",
            "language": "en",
        },
    },
    {
        "original": "Convexity_Conundrums_Draft-Patrick_Hagan.pdf",
        "rename": "Convexity_Conundrums_CMS_Pricing-Patrick_Hagan.pdf",
        "meta": {
            "title": "Convexity Conundrums: Pricing CMS Swaps, Caps, and Floors",
            "authors": [["Hagan", "Patrick S."]],
            "date": "2003-01-01",
            "publisher": "Gorilla Science",
            "abstract": "Here we focus on a single class of deals, the constant maturity swaps, caps, and floors. We develop a framework that leads to the standard methodology for pricing these deals, and then use this framework to systematically improve the pricing.",
            "keywords": ["CMS", "convexity adjustment", "constant maturity swap", "caps", "floors", "replication"],
            "doc_type": "techreport",
            "language": "en",
        },
    },
    {
        "original": "Fast_And_Accurate_Basis_Point_Vol-Fabien_LeFloch.pdf",
        "rename": "Fast_Accurate_Basis_Point_Volatility-Fabien_Le_Floch.pdf",
        "meta": {
            "title": "Fast and Accurate Analytic Basis Point Volatility",
            "authors": [["Le Floc'h", "Fabien"]],
            "date": "2016-06-17",
            "publisher": "Calypso Technology",
            "institution": "Calypso Technology",
            "abstract": "This paper describes a fast analytic formula to obtain the basis point volatility for a given option price under the Bachelier normal model with near machine accuracy. It handles near-the-money as well as very far out-of-the-money options and low volatilities.",
            "keywords": ["implied volatility", "basis point vol", "Bachelier", "normal model", "analytic formula"],
            "doc_type": "article",
            "language": "en",
        },
    },
    {
        "original": "Fine_Tune_Your_Smile-Jan_Obloj.pdf",
        "rename": "Fine_Tune_Your_Smile_SABR_Correction-Jan_Obloj.pdf",
        "meta": {
            "title": "Fine-Tune Your Smile: Correction to Hagan et al",
            "authors": [["Obloj", "Jan"]],
            "date": "2008-03-18",
            "publisher": "arXiv",
            "institution": "Imperial College London",
            "abstract": "Using results derived in Berestycki et al. we correct the celebrated formulae of Hagan et al. We derive explicitly the correct zero order term in the expansion of the implied volatility in time to maturity. The new term is consistent as beta approaches 1. Furthermore, numerical simulations show that it reduces or eliminates known pathologies of the earlier formulae.",
            "keywords": ["SABR", "implied volatility", "asymptotic expansion", "correction", "smile"],
            "doc_type": "article",
            "language": "en",
        },
    },
    {
        "original": "Fitting_The_Smile-Pierre_Gauthier.pdf",
        "rename": "Fitting_The_Smile_Smart_Parameters-Pierre_Gauthier.pdf",
        "meta": {
            "title": "Fitting the Smile: Smart Parameters for SABR and Heston",
            "authors": [["Gauthier", "Pierre"], ["Rivaille", "Pierre-Yves H."]],
            "date": "2009-10-30",
            "publisher": "Pricing Partners",
            "institution": "Pricing Partners",
            "abstract": "In this paper we revisit the problem of calibrating stochastic volatility models. By finding smart initial parameters, we improve robustness of Levenberg-Marquardt. Applying this technique to the SABR and Heston models reduces calibration time by more than 90% compared to global optimization.",
            "keywords": ["SABR", "Heston", "calibration", "smart parameters", "Levenberg-Marquardt", "stochastic volatility"],
            "doc_type": "techreport",
            "language": "en",
        },
    },
    {
        "original": "Implied_Volatility_Smile_Dyanmics_In_The_Presence_Of_Jumps-M_Magris.pdf",
        "rename": "Implied_Vol_Smile_Dynamics_With_Jumps-Martin_Magris.pdf",
        "meta": {
            "title": "Implied Volatility Smile Dynamics in the Presence of Jumps",
            "authors": [["Magris", "M."], ["Barholm", "P."], ["Kanniainen", "J."]],
            "date": "2017-01-01",
            "publisher": "Working Paper",
            "institution": "Tampere University of Technology",
            "abstract": "The main purpose of this work is to examine the behavior of the implied volatility smiles around jumps, contributing to the literature with a high-frequency analysis of the smile dynamics based on intra-day option data from SPX S&P500 index options.",
            "keywords": ["implied volatility", "smile dynamics", "jumps", "high-frequency", "SPX options", "intraday"],
            "doc_type": "article",
            "language": "en",
        },
    },
    {
        "original": "Know_Your_Weapon_P1-Espen_Haug.pdf",
        "rename": "Know_Your_Weapon_Part_1-Espen_Haug.pdf",
        "meta": {
            "title": "Know Your Weapon, Part 1",
            "authors": [["Haug", "Espen Gaarder"]],
            "date": "2003-01-01",
            "publisher": "Wilmott Magazine",
            "abstract": "Trading options is War! For an option trader a pricing or hedging formula is just like a weapon. A review of option pricing models, their practical use and limitations for derivatives traders.",
            "keywords": ["option pricing", "Black-Scholes", "trading", "hedging", "derivatives"],
            "doc_type": "article",
            "series": "Wilmott Magazine",
            "language": "en",
        },
    },
    # Derman lecture series — E4718 Spring 2008, Columbia University
    {
        "original": "Lecture_1_Introduction_To_The_Smile.pdf",
        "rename": "Derman_Lecture_01_Introduction_To_The_Smile-Emanuel_Derman.pdf",
        "meta": {
            "title": "Lecture 1: Introduction to the Smile; The Principles of Valuation",
            "authors": [["Derman", "Emanuel"]],
            "date": "2008-01-28",
            "publisher": "Columbia University",
            "institution": "Columbia University",
            "series": "E4718 Spring 2008: The Smile",
            "keywords": ["volatility smile", "option pricing", "valuation principles"],
            "doc_type": "techreport",
            "language": "en",
        },
    },
    {
        "original": "Lecture_2_Dynamic_Replication.pdf",
        "rename": "Derman_Lecture_02_Dynamic_Replication-Emanuel_Derman.pdf",
        "meta": {
            "title": "Lecture 2: Dynamic Replication: Realities and Myths of Options Pricing",
            "authors": [["Derman", "Emanuel"]],
            "date": "2008-02-01",
            "publisher": "Columbia University",
            "institution": "Columbia University",
            "series": "E4718 Spring 2008: The Smile",
            "keywords": ["dynamic replication", "options pricing", "hedging"],
            "doc_type": "techreport",
            "language": "en",
        },
    },
    {
        "original": "Lecture_3_Transactions_Costs.pdf",
        "rename": "Derman_Lecture_03_Transactions_Costs_And_Smile-Emanuel_Derman.pdf",
        "meta": {
            "title": "Lecture 3: Transactions Costs; The Smile: Constraints, Problems, Models",
            "authors": [["Derman", "Emanuel"]],
            "date": "2008-02-01",
            "publisher": "Columbia University",
            "institution": "Columbia University",
            "series": "E4718 Spring 2008: The Smile",
            "keywords": ["transaction costs", "volatility smile", "constraints"],
            "doc_type": "techreport",
            "language": "en",
        },
    },
    {
        "original": "Lecture_4_More_On_The_Smile.pdf",
        "rename": "Derman_Lecture_04_More_On_The_Smile-Emanuel_Derman.pdf",
        "meta": {
            "title": "Lecture 4: More on The Smile: Arbitrage Bounds, Valuation Problems, Models",
            "authors": [["Derman", "Emanuel"]],
            "date": "2008-03-01",
            "publisher": "Columbia University",
            "institution": "Columbia University",
            "series": "E4718 Spring 2008: The Smile",
            "keywords": ["volatility smile", "arbitrage bounds", "valuation"],
            "doc_type": "techreport",
            "language": "en",
        },
    },
    {
        "original": "Lecture_5_Static_Hedging.pdf",
        "rename": "Derman_Lecture_05_Static_Hedging-Emanuel_Derman.pdf",
        "meta": {
            "title": "Lecture 5: Static Hedging and Implied Distributions",
            "authors": [["Derman", "Emanuel"]],
            "date": "2008-03-01",
            "publisher": "Columbia University",
            "institution": "Columbia University",
            "series": "E4718 Spring 2008: The Smile",
            "keywords": ["static hedging", "implied distributions", "risk-neutral density"],
            "doc_type": "techreport",
            "language": "en",
        },
    },
    {
        "original": "Lecture_6_Extending_Black_Scholes.pdf",
        "rename": "Derman_Lecture_06_Extending_Black_Scholes-Emanuel_Derman.pdf",
        "meta": {
            "title": "Lecture 6: Extending Black-Scholes; Local Volatility Models",
            "authors": [["Derman", "Emanuel"]],
            "date": "2008-03-01",
            "publisher": "Columbia University",
            "institution": "Columbia University",
            "series": "E4718 Spring 2008: The Smile",
            "keywords": ["Black-Scholes", "local volatility", "Dupire", "implied tree"],
            "doc_type": "techreport",
            "language": "en",
        },
    },
    {
        "original": "Lecture_7_Local_Vol_Continued.pdf",
        "rename": "Derman_Lecture_07_Local_Vol_Continued-Emanuel_Derman.pdf",
        "meta": {
            "title": "Lecture 7: Local Volatility Continued",
            "authors": [["Derman", "Emanuel"]],
            "date": "2008-03-27",
            "publisher": "Columbia University",
            "institution": "Columbia University",
            "series": "E4718 Spring 2008: The Smile",
            "keywords": ["local volatility", "Dupire", "calibration"],
            "doc_type": "techreport",
            "language": "en",
        },
    },
    {
        "original": "Lecture_8_Local_Volatility_Implications.pdf",
        "rename": "Derman_Lecture_08_Local_Vol_Implications-Emanuel_Derman.pdf",
        "meta": {
            "title": "Lecture 8: Local Volatility Models: Implications",
            "authors": [["Derman", "Emanuel"]],
            "date": "2008-04-01",
            "publisher": "Columbia University",
            "institution": "Columbia University",
            "series": "E4718 Spring 2008: The Smile",
            "keywords": ["local volatility", "implications", "practical calibration"],
            "doc_type": "techreport",
            "language": "en",
        },
    },
    {
        "original": "Lecture_9_Patterns_Of_Volatility_Change.pdf",
        "rename": "Derman_Lecture_09_Patterns_Of_Volatility_Change-Emanuel_Derman.pdf",
        "meta": {
            "title": "Lecture 9: Patterns of Volatility Change",
            "authors": [["Derman", "Emanuel"]],
            "date": "2008-04-01",
            "publisher": "Columbia University",
            "institution": "Columbia University",
            "series": "E4718 Spring 2008: The Smile",
            "keywords": ["volatility regimes", "implied volatility", "index volatility"],
            "doc_type": "techreport",
            "language": "en",
        },
    },
    {
        "original": "Lecture_10_Stochastic_Vol_Models.pdf",
        "rename": "Derman_Lecture_10_Stochastic_Vol_Models-Emanuel_Derman.pdf",
        "meta": {
            "title": "Lecture 10: Stochastic Volatility Models",
            "authors": [["Derman", "Emanuel"]],
            "date": "2008-04-24",
            "publisher": "Columbia University",
            "institution": "Columbia University",
            "series": "E4718 Spring 2008: The Smile",
            "keywords": ["stochastic volatility", "Heston", "mean reversion"],
            "doc_type": "techreport",
            "language": "en",
        },
    },
    {
        "original": "Lecture_11_More_Stochastic_Vol_Models.pdf",
        "rename": "Derman_Lecture_11_More_Stochastic_Vol_Models-Emanuel_Derman.pdf",
        "meta": {
            "title": "Lecture 11: Stochastic Volatility Models Continued",
            "authors": [["Derman", "Emanuel"]],
            "date": "2008-05-01",
            "publisher": "Columbia University",
            "institution": "Columbia University",
            "series": "E4718 Spring 2008: The Smile",
            "keywords": ["stochastic volatility", "SABR", "mixing models"],
            "doc_type": "techreport",
            "language": "en",
        },
    },
    {
        "original": "Lecture_12_Jump_Diffusions.pdf",
        "rename": "Derman_Lecture_12_Jump_Diffusion_Models-Emanuel_Derman.pdf",
        "meta": {
            "title": "Lecture 12: Jump Diffusion Models of the Smile",
            "authors": [["Derman", "Emanuel"]],
            "date": "2008-05-31",
            "publisher": "Columbia University",
            "institution": "Columbia University",
            "series": "E4718 Spring 2008: The Smile",
            "keywords": ["jump diffusion", "Merton model", "volatility smile", "Poisson process"],
            "doc_type": "techreport",
            "language": "en",
        },
    },
    {
        "original": "Libor_Market_Model_with_SABR_style_stochastic_volatility-Patrick_Hagan.pdf",
        "rename": "LIBOR_Market_Model_SABR_Stochastic_Vol-Patrick_Hagan.pdf",
        "meta": {
            "title": "LIBOR Market Model with SABR Style Stochastic Volatility",
            "authors": [["Hagan", "Patrick"], ["Lesniewski", "Andrew"]],
            "date": "2008-04-30",
            "publisher": "Working Paper",
            "institution": "JP Morgan Chase / Ellington Management Group",
            "abstract": "We develop a LIBOR market model with SABR style stochastic volatility for each forward rate. The model provides a consistent framework for pricing and hedging interest rate derivatives with smile.",
            "keywords": ["LIBOR market model", "SABR", "stochastic volatility", "interest rate derivatives", "smile"],
            "doc_type": "techreport",
            "language": "en",
        },
    },
    {
        "original": "Managing_Smile_Risk_Wilmott-Patrick_Hagan.pdf",
        "rename": "Managing_Smile_Risk_SABR-Patrick_Hagan.pdf",
        "meta": {
            "title": "Managing Smile Risk",
            "authors": [["Hagan", "Patrick S."], ["Kumar", "Deep"], ["Lesniewski", "Andrew S."], ["Woodward", "Diana E."]],
            "date": "2002-01-01",
            "publisher": "Wilmott Magazine",
            "abstract": "Market smiles and skews are usually managed by using local volatility models a la Dupire. We discover that the dynamics of the market smile predicted by local volatility become degenerate as the expiry is increased. We introduce the SABR model and apply it to USD interest rate options, finding good agreement between theoretical and observed smiles.",
            "keywords": ["SABR", "smile risk", "stochastic volatility", "local volatility", "dynamic hedging", "volga", "vanna"],
            "doc_type": "article",
            "series": "Wilmott Magazine",
            "language": "en",
        },
    },
    {
        "original": "Paul_Wilmott_on_Quantitative_Finance-Paul_Wilmott.pdf",
        "rename": "Paul_Wilmott_On_Quantitative_Finance-Paul_Wilmott.pdf",
        "meta": {
            "title": "Paul Wilmott on Quantitative Finance",
            "authors": [["Wilmott", "Paul"]],
            "date": "2006-01-01",
            "publisher": "John Wiley & Sons",
            "abstract": "Comprehensive textbook covering quantitative finance including derivatives pricing, risk management, stochastic calculus, and numerical methods.",
            "keywords": ["quantitative finance", "derivatives", "Black-Scholes", "stochastic calculus", "risk management"],
            "doc_type": "book",
            "language": "en",
        },
    },
    {
        "original": "Rough_Volatility_Evidence_From_Option_Prices-Giulia_Livieri.pdf",
        "rename": "Rough_Volatility_Evidence_From_Option_Prices-Giulia_Livieri.pdf",
        "meta": {
            "title": "Rough Volatility: Evidence from Option Prices",
            "authors": [["Livieri", "Giulia"], ["Mouti", "Saad"], ["Pallavicini", "Andrea"], ["Rosenbaum", "Mathieu"]],
            "date": "2017-02-09",
            "publisher": "Working Paper",
            "institution": "Scuola Normale Superiore / Ecole Polytechnique / Imperial College London",
            "abstract": "It has been recently shown that spot volatilities can be very well modeled by rough stochastic volatility type dynamics. In such models, the volatility process is driven by a fractional Brownian motion with Hurst parameter less than 1/2.",
            "keywords": ["rough volatility", "fractional Brownian motion", "Hurst parameter", "option pricing", "implied volatility"],
            "doc_type": "article",
            "language": "en",
        },
    },
    {
        "original": "SSRN-id1493294.pdf",
        "rename": "Smile_Dynamics-Lorenzo_Bergomi.pdf",
        "meta": {
            "title": "Smile Dynamics",
            "authors": [["Bergomi", "Lorenzo"]],
            "date": "2004-04-01",
            "publisher": "SSRN",
            "institution": "Société Générale",
            "identifier": "SSRN:1493294",
            "abstract": "Traditionally smile models have been assessed according to how well they fit market option prices across strikes and maturities. However, the pricing of most of the recent exotic structures, such as reverse cliquets or Napoleons, is more dependent on the assumptions made for the future dynamics of implied vols than on today's vanilla option prices.",
            "keywords": ["smile dynamics", "stochastic volatility", "local volatility", "exotic options", "implied volatility dynamics"],
            "doc_type": "article",
            "language": "en",
        },
    },
    {
        "original": "SSRN-id2692048.pdf",
        "rename": "Implementation_Of_The_ZABR_Model-Peter_Caspers.pdf",
        "meta": {
            "title": "Implementation of the ZABR Model",
            "authors": [["Caspers", "Peter"]],
            "date": "2013-09-07",
            "publisher": "SSRN",
            "identifier": "SSRN:2692048",
            "abstract": "This is mainly a repeat of the ZABR paper inserting some more intermediate steps in the calculations and a test of the numerical examples in the original paper against our own implementation.",
            "keywords": ["ZABR", "SABR", "local volatility", "stochastic volatility", "implementation"],
            "doc_type": "techreport",
            "language": "en",
        },
    },
    {
        "original": "SSRN-id898701.pdf",
        "rename": "Stochastic_Volatility_For_Real-Jesper_Andreasen.pdf",
        "meta": {
            "title": "Stochastic Volatility for Real",
            "authors": [["Andreasen", "Jesper"]],
            "date": "2006-03-01",
            "publisher": "SSRN",
            "institution": "Bank of America",
            "identifier": "SSRN:898701",
            "abstract": "A practical approach to stochastic volatility modeling for derivatives pricing and risk management.",
            "keywords": ["stochastic volatility", "calibration", "option pricing", "practical implementation"],
            "doc_type": "article",
            "language": "en",
        },
    },
    {
        "original": "The Best of Wilmott Vol 2.pdf",
        "rename": "Best_Of_Wilmott_Volume_2-Paul_Wilmott.pdf",
        "meta": {
            "title": "The Best of Wilmott, Volume 2",
            "authors": [["Wilmott", "Paul"]],
            "date": "2005-01-01",
            "publisher": "John Wiley & Sons",
            "abstract": "A collection of the best articles from Wilmott magazine covering quantitative finance, derivatives, and risk management.",
            "keywords": ["quantitative finance", "derivatives", "Wilmott magazine", "collected papers"],
            "doc_type": "book",
            "language": "en",
        },
    },
    {
        "original": "The_Implied_Volatility_of_Forward_Start_Options-Elisa_Alos.pdf",
        "rename": "Implied_Volatility_Forward_Start_Options-Elisa_Alos.pdf",
        "meta": {
            "title": "The Implied Volatility of Forward-Start Options: ATM Short-Time Level, Skew and Curvature",
            "authors": [["Alos", "Elisa"], ["Jacquier", "Antoine"], ["Leon", "Jorge A."]],
            "date": "2017-10-30",
            "publisher": "arXiv",
            "institution": "Universitat Pompeu Fabra / Imperial College London / CINVESTAV-IPN",
            "abstract": "We study the implied volatility of forward-start options, deriving ATM short-time level, skew and curvature in terms of the model parameters.",
            "keywords": ["forward-start options", "implied volatility", "ATM skew", "curvature", "stochastic volatility"],
            "doc_type": "article",
            "language": "en",
        },
    },
    {
        "original": "Vanna volga normal vols.pdf",
        "rename": "Vanna_Volga_Method_Normal_Volatilities-Volodymyr_Perederiy.pdf",
        "meta": {
            "title": "Vanna-Volga Method for Normal Volatilities",
            "authors": [["Perederiy", "Volodymyr"]],
            "date": "2018-10-01",
            "publisher": "Working Paper",
            "abstract": "Vanna-volga is a popular method for interpolation/extrapolation of volatility smiles. The technique is widely used in the FX markets context, due to its ability to consistently construct the entire lognormal smile using only three lognormal market quotes. However, the derivation of vanna-volga method itself is free of distributional assumptions. We extend it to normal volatilities.",
            "keywords": ["vanna-volga", "normal volatility", "FX options", "smile interpolation", "Bachelier"],
            "doc_type": "article",
            "language": "en",
        },
    },
    {
        "original": "zwp-008-RobustNoArbSSVI.pdf",
        "rename": "Robust_Calibration_Arbitrage_Free_SSVI-Zeliade.pdf",
        "meta": {
            "title": "Robust Calibration and Arbitrage-Free Interpolation of SSVI Slices",
            "authors": [["Zeliade Systems", ""]],
            "date": "2018-04-11",
            "publisher": "Zeliade Systems",
            "institution": "Zeliade Systems",
            "abstract": "We propose a robust calibration procedure and an arbitrage-free interpolation method for SSVI (Surface Stochastic Volatility Inspired) slices.",
            "keywords": ["SSVI", "SVI", "arbitrage-free", "calibration", "implied volatility surface", "interpolation"],
            "doc_type": "techreport",
            "language": "en",
        },
    },
]


def process_all():
    folder = Path(os.path.expanduser("~/PycharmProjects/Papers/Vol_Surface_and_SABR"))
    processed_dir = Path(os.path.expanduser("~/PycharmProjects/Papers/processed"))
    processed_dir.mkdir(exist_ok=True)

    # Load progress
    progress_path = folder / "_batch_progress.json"
    progress = json.loads(progress_path.read_text()) if progress_path.exists() else {}

    for i, paper in enumerate(PAPERS, 1):
        original = folder / paper["original"]
        if not original.exists():
            print(f"[{i}/{len(PAPERS)}] SKIP (not found): {paper['original']}")
            continue

        renamed = folder / paper["rename"]
        bib_path = renamed.with_suffix(".bib")

        # Skip if already done (bib exists for the renamed file)
        if bib_path.exists() and renamed.exists():
            print(f"[{i}/{len(PAPERS)}] SKIP (done): {paper['rename']}")
            continue

        print(f"[{i}/{len(PAPERS)}] Processing: {paper['original']}")
        meta = paper["meta"]

        # Step 6: Enrich metadata
        try:
            import tempfile
            tmp_enriched = tempfile.mktemp(suffix=".pdf")
            enrich_pdf(str(original), tmp_enriched, meta)

            # Step 7: Generate .bib
            bib_content = generate_bib(meta, pdf_filename=paper["rename"])
            bib_path.write_text(bib_content + "\n")
            print(f"  → .bib: {bib_path.name}")

            # Step 8: Rename (move enriched to new name)
            shutil.move(tmp_enriched, str(renamed))
            print(f"  → Renamed: {paper['rename']}")

            # Step 10: Move original to processed/
            if original.name != paper["rename"]:
                dest = processed_dir / original.name
                if not dest.exists():
                    shutil.move(str(original), str(dest))
                    print(f"  → Original moved to processed/")
                else:
                    original.unlink()
                    print(f"  → Original removed (already in processed/)")
            else:
                # Same name — original was overwritten by enriched version
                pass

        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()

        print()

    # Clean up progress file
    if progress_path.exists():
        progress_path.unlink()

    print("Done!")


if __name__ == "__main__":
    process_all()
