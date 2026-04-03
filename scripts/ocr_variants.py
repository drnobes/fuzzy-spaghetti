#!/usr/bin/env python3
"""
Run multiple OCR parameter variants on Neftci to compare quality.
Outputs to Numerical_Methods/ocr_test/ for visual inspection.

Key finding: the scan is rotated 90° clockwise, so --rotate-pages is essential.
"""

import os
import time
from pathlib import Path

import ocrmypdf
import pdfplumber


INPUT = Path(os.path.expanduser(
    "~/PycharmProjects/Papers/Numerical_Methods/"
    "Introduction_Mathematics_Financial_Derivatives-Salih_Neftci.pdf"
))
OUT_DIR = INPUT.parent / "ocr_test"
# Test on pages 21-25 (content pages with text + math, confirmed non-blank)
TEST_PAGES = "21-25"

VARIANTS = {
    "rotate_only": {
        # Auto-rotate + baseline — should fix the garbled text
        "force_ocr": True,
        "optimize": 0,
        "rotate_pages": True,
    },
    "rotate_oversample_300": {
        # Auto-rotate + 300 DPI
        "force_ocr": True,
        "optimize": 0,
        "rotate_pages": True,
        "oversample": 300,
    },
    "rotate_clean_300": {
        # Auto-rotate + clean + deskew + 300 DPI
        "force_ocr": True,
        "optimize": 0,
        "rotate_pages": True,
        "oversample": 300,
        "deskew": True,
        "clean": True,
    },
    "rotate_clean_400": {
        # Auto-rotate + clean + deskew + 400 DPI — max quality
        "force_ocr": True,
        "optimize": 0,
        "rotate_pages": True,
        "oversample": 400,
        "deskew": True,
        "clean": True,
    },
}


def run_variant(name, opts):
    """Run one OCR variant and return quality metrics."""
    output = OUT_DIR / f"neftci_{name}.pdf"
    sidecar = OUT_DIR / f"neftci_{name}.txt"

    t0 = time.perf_counter()
    result = ocrmypdf.ocr(
        str(INPUT),
        str(output),
        language=["eng"],
        pages=TEST_PAGES,
        jobs=2,
        progress_bar=False,
        sidecar=str(sidecar),
        **opts,
    )
    elapsed = time.perf_counter() - t0

    # Read the sidecar text (raw OCR output, independent of pdfplumber)
    sidecar_text = sidecar.read_text(errors="replace") if sidecar.exists() else ""

    # Also extract via pdfplumber for comparison
    pages_text = []
    total_chars = 0
    with pdfplumber.open(output) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            pages_text.append(text)
            total_chars += len(text)

    # Quality heuristic: ratio of recognizable words (3+ alpha chars)
    all_text = sidecar_text
    words = all_text.split()
    real_words = sum(1 for w in words if len(w) >= 3 and w.isalpha())
    word_quality = real_words / len(words) if words else 0

    return {
        "name": name,
        "exit_code": result.name,
        "elapsed": round(elapsed, 1),
        "total_chars": len(sidecar_text),
        "pdfplumber_chars": total_chars,
        "total_words": len(words),
        "real_words": real_words,
        "word_quality_pct": round(word_quality * 100, 1),
        "sidecar_sample": sidecar_text[:800],
        "pdfplumber_sample": pages_text[0][:800] if pages_text else "",
        "output": str(output),
        "sidecar_path": str(sidecar),
    }


def main():
    OUT_DIR.mkdir(exist_ok=True)
    print(f"Input: {INPUT}")
    print(f"Test pages: {TEST_PAGES}")
    print(f"Output dir: {OUT_DIR}")
    print(f"Running {len(VARIANTS)} variants...\n")

    results = []
    for name, opts in VARIANTS.items():
        print(f"  [{name}] running...")
        r = run_variant(name, opts)
        results.append(r)
        print(f"  [{name}] {r['elapsed']}s, {r['total_chars']} chars (sidecar), "
              f"{r['pdfplumber_chars']} chars (pdfplumber), "
              f"{r['word_quality_pct']}% real words")

    # Summary table
    print(f"\n{'='*85}")
    print(f"{'Variant':<25} {'Time':>5} {'Sidecar':>8} {'Plumber':>8} "
          f"{'Words':>6} {'Real%':>6}")
    print("-" * 85)
    for r in sorted(results, key=lambda x: -x["word_quality_pct"]):
        print(f"{r['name']:<25} {r['elapsed']:>5} {r['total_chars']:>8} "
              f"{r['pdfplumber_chars']:>8} {r['total_words']:>6} "
              f"{r['word_quality_pct']:>5}%")

    # Show best variant's sidecar sample
    best = max(results, key=lambda x: x["word_quality_pct"])
    print(f"\n{'='*85}")
    print(f"BEST: {best['name']} ({best['word_quality_pct']}% real words)")
    print(f"Sidecar text sample:\n")
    print(best["sidecar_sample"])
    print(f"\n{'='*85}")
    print(f"pdfplumber text sample:\n")
    print(best["pdfplumber_sample"])

    print(f"\nOutput files in: {OUT_DIR}")
    print("  PDFs:     neftci_<variant>.pdf  (open to check text selection)")
    print("  Sidecar:  neftci_<variant>.txt  (raw OCR text)")


if __name__ == "__main__":
    main()
