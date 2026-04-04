#!/usr/bin/env python3
"""
Process Non_Finance folder: enrich metadata, generate .bibs, rename.

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


# ── All 6 papers with hand-extracted metadata (skip Paul Klee Notebooks) ──

PAPERS = [
    {
        "original": "Leaves_Of_Grass-Walt_Whitman.pdf",
        "rename": "Leaves_Of_Grass-Walt_Whitman.pdf",
        "meta": {
            "title": "Leaves of Grass",
            "authors": [["Whitman", "Walt"]],
            "date": "2007-01-01",
            "publisher": "Pennsylvania State University Electronic Classics",
            "institution": "Pennsylvania State University",
            "identifier": "",
            "abstract": "Complete collection of Walt Whitman's poetry.",
            "keywords": ["poetry", "American literature", "Walt Whitman"],
            "doc_type": "book",
            "language": "en",
        },
    },
    {
        "original": "Not_Zen-Unknown.pdf",
        "rename": "Not_Zen-ewk.pdf",
        "meta": {
            "title": "Not Zen",
            "authors": [["ewk", ""]],
            "date": "2014-01-01",
            "publisher": "",
            "institution": "",
            "identifier": "",
            "abstract": "Essays and commentary on Zen Buddhism.",
            "keywords": ["Zen", "Buddhism", "Dharma", "philosophy"],
            "doc_type": "book",
            "language": "en",
        },
    },
    {
        "original": "Poor Charlie's Almanack by Charles T. Munger.pdf",
        "rename": "Poor_Charlies_Almanack-Charles_Munger.pdf",
        "meta": {
            "title": "Poor Charlie's Almanack: The Wit and Wisdom of Charles T. Munger",
            "authors": [["Munger", "Charles T."]],
            "date": "2005-01-01",
            "publisher": "The Donning Company Publishers",
            "institution": "",
            "identifier": "ISBN 978-1-57864-501-5",
            "abstract": "Collection of speeches, talks, and wisdom from Berkshire Hathaway Vice Chairman Charlie Munger on investing, decision-making, and mental models.",
            "keywords": ["investing", "decision making", "mental models", "Berkshire Hathaway", "value investing"],
            "doc_type": "book",
            "language": "en",
        },
    },
    {
        "original": "The_Wind_In_The_Willows-Kenneth_Grahame.pdf",
        "rename": "The_Wind_In_The_Willows-Kenneth_Grahame.pdf",
        "meta": {
            "title": "The Wind in the Willows",
            "authors": [["Grahame", "Kenneth"]],
            "date": "1908-01-01",
            "publisher": "",
            "institution": "",
            "identifier": "",
            "abstract": "Classic English children's novel following the adventures of Mole, Rat, Badger, and Toad.",
            "keywords": ["children's literature", "English literature", "animals", "classic fiction"],
            "doc_type": "book",
            "language": "en",
        },
    },
    {
        "original": "las_vidas_del_gato.pdf",
        "rename": "Why_Cats_Have_Nine_Lives-Jared_Diamond.pdf",
        "meta": {
            "title": "Why Cats Have Nine Lives",
            "authors": [["Diamond", "Jared M."]],
            "date": "1988-04-14",
            "publisher": "Nature",
            "institution": "University of California Medical School, Los Angeles",
            "identifier": "Nature Vol. 332, pp. 586-587",
            "abstract": "Analysis of why cats survive falls that are lethal to humans, examining data from 132 cats injured by falls in New York City.",
            "keywords": ["animal behaviour", "falling cats", "terminal velocity", "biomechanics", "physics"],
            "doc_type": "article",
            "language": "en",
        },
    },
    {
        "original": "rms-essays.pdf",
        "rename": "Free_Software_Free_Society-Richard_Stallman.pdf",
        "meta": {
            "title": "Free Software, Free Society: Selected Essays of Richard M. Stallman",
            "authors": [["Stallman", "Richard M."]],
            "date": "2002-01-01",
            "publisher": "GNU Press",
            "institution": "Free Software Foundation",
            "identifier": "ISBN 1-882114-98-1",
            "abstract": "Selected essays on free software philosophy, copyleft, GNU project, and software freedom.",
            "keywords": ["free software", "open source", "GNU", "software freedom", "copyleft", "GPL"],
            "doc_type": "book",
            "language": "en",
        },
    },
]


def process_all():
    import tempfile

    folder = Path(os.path.expanduser("~/PycharmProjects/Papers/Non_Finance"))
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
    print(f"Processed {len(PAPERS)} papers in Non_Finance/")
    print(f"Run 'fz-ingest --vectors' to rebuild indices.")


if __name__ == "__main__":
    process_all()
