"""Read-only wikilink target checks. No plugins and no vault modifications."""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import re

EXCLUDED = {".obsidian", ".git", ".trash", "node_modules"}


def prose(text: str) -> str:
    lines = []
    fence = None
    for line in text.splitlines():
        marker = re.match(r"^\s*(`{3,}|~{3,})", line)
        if marker:
            if fence is None:
                fence = marker[1][0]
            elif marker[1][0] == fence:
                fence = None
            continue
        if fence is None:
            lines.append(re.sub(r"`+[^`]*`+", "", line))
    return "\n".join(lines)


def check_links(vault: Path) -> dict:
    vault = vault.resolve(strict=True)
    if not vault.is_dir():
        raise ValueError("vault must be a directory")
    files = [p for p in vault.rglob("*") if p.is_file() and not p.is_symlink()
             and not (set(p.relative_to(vault).parts) & EXCLUDED)
             and p.resolve().is_relative_to(vault)]
    index = defaultdict(set)
    for path in files:
        relative = path.relative_to(vault).as_posix()
        variants = {relative}
        if path.suffix.casefold() == ".md":
            variants.add(relative[:-3])
        for variant in variants:
            parts = variant.split("/")
            for start in range(len(parts)):
                index["/".join(parts[start:]).casefold()].add(relative)
    errors = []
    checked = 0
    notes = [p for p in files if p.suffix.casefold() == ".md"]
    for path in notes:
        for match in re.finditer(r"(?<!\\)\[\[([^\]\n]+)\]\]", prose(path.read_text(encoding="utf-8-sig"))):
            target = re.split(r"\\?\|", match[1], maxsplit=1)[0].split("#", 1)[0].strip()
            if not target or "://" in target:
                continue
            checked += 1
            # Explicit note-relative paths are resolved against the source note.
            if target.startswith(("./", "../")):
                candidate = path.parent / target
                possible = [candidate, candidate.with_suffix(".md")] if not candidate.suffix else [candidate]
                candidates = {p.relative_to(vault).as_posix() for p in files if
                              any(p == q.resolve() and q.resolve().is_relative_to(vault) for q in possible)}
            else:
                candidates = index.get(target.removeprefix("/").casefold(), set())
            if len(candidates) != 1:
                errors.append({"note": path.relative_to(vault).as_posix(), "target": target,
                               "reason": "missing" if not candidates else "ambiguous",
                               "candidates": sorted(candidates)})
    return {"notes": len(notes), "checked_links": checked, "errors": errors,
            "scope": "file targets only; heading and block anchors are not checked"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vault", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = check_links(args.vault)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return int(bool(result["errors"]))
    except (OSError, ValueError) as error:
        parser.exit(2, f"ERROR: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
