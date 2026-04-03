#!/usr/bin/env python3
"""
Process Programming folder: enrich metadata, generate .bibs, rename.

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


# ── All 14 papers with hand-extracted metadata ─────────────────────────────

PAPERS = [
    {
        "original": "A_Flex_Engine_In_Less_Than_101_Lines-Ingo_Fahrner.pdf",
        "rename": "A_Flex_Engine_In_Less_Than_101_Lines-Ingo_Fahrner.pdf",
        "meta": {
            "title": "A Flex Engine In Less Than 101 Lines",
            "authors": [["Fahrner", "Ingo"], ["Fehnl", "Thomas"]],
            "date": "2008-01-01",
            "publisher": "Wilmott Magazine",
            "institution": "LBBW Quantitative Research",
            "identifier": "",
            "abstract": "Framework for building a flexible payoff language and linking it to the pricing kernel in very short code with good performance.",
            "keywords": ["flexible payoff language", "exotic products", "pricing kernel", "derivatives"],
            "doc_type": "article",
            "language": "en",
        },
    },
    {
        "original": "An_Introduction_To_Programming_In_Emacs_Lisp-GNU.pdf",
        "rename": "An_Introduction_To_Programming_In_Emacs_Lisp-Robert_Chassell.pdf",
        "meta": {
            "title": "An Introduction to Programming in Emacs Lisp",
            "authors": [["Chassell", "Robert J."]],
            "date": "2009-10-28",
            "publisher": "GNU Press",
            "institution": "Free Software Foundation",
            "identifier": "ISBN 1-882114-43-4",
            "abstract": "An introduction to programming in Emacs Lisp for people who are not programmers.",
            "keywords": ["Emacs", "Lisp", "programming", "GNU", "text editor"],
            "doc_type": "book",
            "language": "en",
        },
    },
    {
        "original": "Dive_Into_Python-Mark_Pilgrim.pdf",
        "rename": "Dive_Into_Python-Mark_Pilgrim.pdf",
        "meta": {
            "title": "Dive Into Python",
            "authors": [["Pilgrim", "Mark"]],
            "date": "2004-01-01",
            "publisher": "",
            "institution": "",
            "identifier": "",
            "abstract": "Comprehensive Python tutorial covering datatypes, introspection, objects, exceptions, regular expressions, HTML/XML processing.",
            "keywords": ["Python", "programming", "tutorial", "introspection", "regular expressions"],
            "doc_type": "book",
            "language": "en",
        },
    },
    {
        "original": "Matplotlib Notes.pdf",
        "rename": "Introductory_Notes_Matplotlib-Mark_Graph.pdf",
        "meta": {
            "title": "Introductory Notes: Matplotlib",
            "authors": [["Graph", "Mark"]],
            "date": "2017-05-19",
            "publisher": "",
            "institution": "",
            "identifier": "",
            "abstract": "Draft reference notes covering matplotlib's pyplot API, Figure and Axes classes, line plots, and programmatic plotting.",
            "keywords": ["matplotlib", "Python", "visualization", "plotting", "data science"],
            "doc_type": "misc",
            "language": "en",
        },
    },
    {
        "original": "Notes_On_Structured_Programming-Edsger_Dijkstra.pdf",
        "rename": "Notes_On_Structured_Programming-Edsger_Dijkstra.pdf",
        "meta": {
            "title": "Notes on Structured Programming",
            "authors": [["Dijkstra", "Edsger W."]],
            "date": "1970-01-01",
            "publisher": "",
            "institution": "Technological University Eindhoven",
            "identifier": "EWD 249",
            "abstract": "Notes on composition of large programs, treating problems of size and scale in programming and intellectual manageability of software.",
            "keywords": ["structured programming", "software engineering", "program correctness", "Dijkstra"],
            "doc_type": "techreport",
            "language": "en",
        },
    },
    {
        "original": "Programming_From_The_Ground_Up-Jonathan_Bartlett.pdf",
        "rename": "Programming_From_The_Ground_Up-Jonathan_Bartlett.pdf",
        "meta": {
            "title": "Programming from the Ground Up",
            "authors": [["Bartlett", "Jonathan"]],
            "date": "2003-01-01",
            "publisher": "Bartlett Publishing",
            "institution": "",
            "identifier": "",
            "abstract": "Introductory book on x86 assembly language programming on Linux.",
            "keywords": ["assembly language", "x86", "Linux", "programming", "systems programming"],
            "doc_type": "book",
            "language": "en",
        },
    },
    {
        "original": "The_Art_of_Assembly-Unknown.pdf",
        "rename": "The_Art_of_Assembly_Language-Randall_Hyde.pdf",
        "meta": {
            "title": "The Art of Assembly Language",
            "authors": [["Hyde", "Randall"]],
            "date": "2003-01-01",
            "publisher": "",
            "institution": "",
            "identifier": "",
            "abstract": "Comprehensive textbook on assembly language covering data representation, boolean algebra, 80x86 instruction set, procedures, floating point, strings, interrupts, and hardware interfaces.",
            "keywords": ["assembly language", "80x86", "MASM", "PC architecture", "systems programming", "low-level programming"],
            "doc_type": "book",
            "language": "en",
        },
    },
    {
        "original": "The_Craft_of_Text_Editing_In_EMACS-Craig_Finseth.pdf",
        "rename": "The_Craft_of_Text_Editing-Craig_Finseth.pdf",
        "meta": {
            "title": "The Craft of Text Editing, or, A Cookbook for an Emacs",
            "authors": [["Finseth", "Craig A."]],
            "date": "1999-01-01",
            "publisher": "",
            "institution": "",
            "identifier": "",
            "abstract": "Guide to implementing text editors covering buffer data structures, display management, user interface design, and implementation languages.",
            "keywords": ["text editor", "Emacs", "buffer gap", "display management", "user interface", "software design"],
            "doc_type": "book",
            "language": "en",
        },
    },
    {
        "original": "The_Origin_Of_the_Stored_Program-Allan_Bromley.pdf",
        "rename": "The_Origin_Of_The_Stored_Program_Concept-Allan_Bromley.pdf",
        "meta": {
            "title": "The Origin of the Stored Program Concept",
            "authors": [["Bromley", "Allan G."]],
            "date": "1985-11-15",
            "publisher": "University of Sydney",
            "institution": "University of Sydney",
            "identifier": "Technical Report 274",
            "abstract": "Examines the stored program concept, finding it divisible into distinct sub-concepts attributable to separate inventors, not the work of one person.",
            "keywords": ["stored program concept", "computer history", "von Neumann", "ENIAC", "computing pioneers"],
            "doc_type": "techreport",
            "language": "en",
        },
    },
    {
        "original": "Think_Python-Allen_Downey.pdf",
        "rename": "Think_Python-Allen_Downey.pdf",
        "meta": {
            "title": "Think Python: An Introduction to Software Design",
            "authors": [["Downey", "Allen"]],
            "date": "2008-06-01",
            "publisher": "Green Tea Press",
            "institution": "",
            "identifier": "",
            "abstract": "Introduction to software design using Python, evolved from How to Think Like a Computer Scientist.",
            "keywords": ["Python", "programming", "software design", "computer science", "introductory"],
            "doc_type": "book",
            "language": "en",
        },
    },
    {
        "original": "Thinking_Forth-Leo_Brodie.pdf",
        "rename": "Thinking_Forth-Leo_Brodie.pdf",
        "meta": {
            "title": "Thinking Forth: A Language and Philosophy for Solving Problems",
            "authors": [["Brodie", "Leo"]],
            "date": "2004-01-01",
            "publisher": "",
            "institution": "",
            "identifier": "ISBN 0-9764587-0-5",
            "abstract": "Book on the Forth programming language and its philosophy for problem solving, including interviews with Charles H. Moore.",
            "keywords": ["Forth", "programming language", "problem solving", "philosophy", "Charles Moore"],
            "doc_type": "book",
            "language": "en",
        },
    },
    {
        "original": "Unix_Building_A_Development_Environment_From_Scratch-Warren_Toomey.pdf",
        "rename": "Unix_Building_A_Development_Environment_From_Scratch-Warren_Toomey.pdf",
        "meta": {
            "title": "Unix: Building a Development Environment from Scratch",
            "authors": [["Toomey", "Warren"]],
            "date": "2016-01-01",
            "publisher": "",
            "institution": "The Unix Heritage Society",
            "identifier": "",
            "abstract": "Examines the creation of Unix on the PDP-7 after AT&T's departure from Multics and the 2016 restoration of PDP-7 Unix from source.",
            "keywords": ["Unix", "PDP-7", "operating systems", "Multics", "Ken Thompson", "computer history"],
            "doc_type": "inproceedings",
            "language": "en",
        },
    },
    {
        "original": "Windows_Assembly_Programming_Tutorial-Jeff_Huang.pdf",
        "rename": "Windows_Assembly_Programming_Tutorial-Jeff_Huang.pdf",
        "meta": {
            "title": "Windows Assembly Programming Tutorial",
            "authors": [["Huang", "Jeff"]],
            "date": "2003-12-10",
            "publisher": "",
            "institution": "University of Illinois at Urbana-Champaign",
            "identifier": "",
            "abstract": "Tutorial on Windows assembly programming covering MASM32, CPU registers, instruction set, Windows API, string manipulation, and GUI controls.",
            "keywords": ["assembly language", "Windows", "MASM32", "x86", "Windows API", "tutorial"],
            "doc_type": "misc",
            "language": "en",
        },
    },
    {
        "original": "iverson.pdf",
        "rename": "Notation_As_A_Tool_Of_Thought-Kenneth_Iverson.pdf",
        "meta": {
            "title": "Notation as a Tool of Thought",
            "authors": [["Iverson", "Kenneth E."]],
            "date": "1979-10-29",
            "publisher": "ACM",
            "institution": "IBM Thomas J. Watson Research Center",
            "identifier": "",
            "abstract": "1979 ACM Turing Award Lecture on combining executability and universality of programming languages with advantages of mathematical notation, resulting in APL.",
            "keywords": ["APL", "notation", "programming languages", "mathematical notation", "Turing Award", "array programming"],
            "doc_type": "inproceedings",
            "language": "en",
        },
    },
]


def process_all():
    import tempfile

    folder = Path(os.path.expanduser("~/PycharmProjects/Papers/Programming"))
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
    print(f"Processed {len(PAPERS)} papers in Programming/")
    print(f"Run 'fz-ingest --vectors' to rebuild indices.")


if __name__ == "__main__":
    process_all()
