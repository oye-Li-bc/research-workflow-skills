"""Add missing slide boundaries without running or rewriting notebook cells."""
from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
import re


def mark_slides(book: dict, mode: str = "headings") -> dict:
    if not isinstance(book, dict) or not isinstance(book.get("cells"), list):
        raise ValueError("expected a notebook with a cells array")
    if mode not in {"headings", "cells"}:
        raise ValueError("unsupported mode")
    result = deepcopy(book)
    for cell in result["cells"]:
        metadata = cell.setdefault("metadata", {})
        slideshow = metadata.setdefault("slideshow", {})
        if "slide_type" in slideshow:
            continue
        source = cell.get("source", [])
        source = "".join(source) if isinstance(source, list) else source
        boundary = "-"
        if mode == "cells" and source.strip():
            boundary = "slide"
        elif cell.get("cell_type") == "markdown":
            heading = re.match(r"^\s*(#{1,2})\s+\S", source)
            if heading:
                boundary = "slide" if len(heading[1]) == 1 else "subslide"
        slideshow["slide_type"] = boundary
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--mode", choices=("headings", "cells"), default="headings")
    args = parser.parse_args()
    try:
        result = mark_slides(json.loads(args.input.read_text(encoding="utf-8-sig")), args.mode)
        with args.output.open("x", encoding="utf-8") as output:
            output.write(json.dumps(result, ensure_ascii=False, indent=1) + "\n")
    except (OSError, ValueError, TypeError) as error:
        parser.exit(1, f"ERROR: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
