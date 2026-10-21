"""Report metadata without importing packages or executing notebook cells."""
from __future__ import annotations

import argparse
from collections import Counter
from importlib import metadata
import json
from pathlib import Path
import os
import platform
import sys

PACKAGES = ("notebook", "jupyterlab", "jupyter-server", "nbclassic", "ipykernel",
            "ipywidgets", "rise", "jupyterlab-rise", "numpy", "torch", "d2l")


def notebook_summary(path: Path) -> dict:
    book = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(book, dict) or not isinstance(book.get("cells"), list):
        raise ValueError("not a notebook with a cells array")
    counts = Counter(cell.get("cell_type", "unknown") for cell in book["cells"])
    return {"nbformat": book.get("nbformat"), "cell_types": dict(counts),
            "kernelspec": book.get("metadata", {}).get("kernelspec", {}),
            "language_info": {"name": book.get("metadata", {}).get("language_info", {}).get("name")}}


def report(notebook: Path | None = None) -> dict:
    packages = {}
    for package in PACKAGES:
        try:
            packages[package] = metadata.version(package)
        except metadata.PackageNotFoundError:
            packages[package] = None
    result = {"python": platform.python_version(), "interpreter": sys.executable,
              "platform": platform.system(), "packages": packages,
              "pythonpath_is_set": bool(os.environ.get("PYTHONPATH")),
              "virtual_environment": sys.prefix != sys.base_prefix}
    if notebook:
        result["notebook"] = notebook_summary(notebook)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--notebook", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        data = json.dumps(report(args.notebook), ensure_ascii=False, indent=2) + "\n"
        if args.output:
            with args.output.open("x", encoding="utf-8") as output:
                output.write(data)
        else:
            print(data, end="")
    except (OSError, ValueError, TypeError) as error:
        parser.exit(1, f"ERROR: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
