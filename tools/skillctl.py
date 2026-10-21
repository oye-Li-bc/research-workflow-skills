"""Validate, inspect, install, and package this skill library. Standard library only."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile
from urllib.parse import unquote
import zipfile

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {".git", "__pycache__", ".venv", "dist", "reports"}


def entries(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*") if p.is_file() and
                  not (set(p.relative_to(root).parts) & EXCLUDED) and p.suffix != ".pyc")


def catalog(root: Path = ROOT) -> dict:
    return json.loads((root / "catalog.json").read_text(encoding="utf-8"))


def frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8-sig")
    match = re.match(r"\A---\n(.*?)\n---(?:\n|$)", text, re.S)
    if not match:
        raise ValueError(f"missing frontmatter: {path.name}")
    result = {}
    for line in match[1].splitlines():
        key, sep, value = line.partition(":")
        if not sep or key not in {"name", "description", "license"} or key in result:
            raise ValueError("expected unique name/description/license scalar fields")
        value = value.strip()
        result[key] = json.loads(value) if value.startswith('"') else value
    return result


def validate(root: Path = ROOT) -> list[str]:
    errors = []
    data = catalog(root)
    if data.get("schema_version") != 1 or data.get("version") != (root / "VERSION").read_text().strip():
        errors.append("catalog schema/version mismatch")
    known = set()
    for skill in data["skills"]:
        name = skill["id"]
        path = root / skill["path"]
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name) or len(name) > 64:
            errors.append(f"invalid skill id: {name}")
        if name in known or skill["path"] != "skills/" + name:
            errors.append(f"duplicate id or unexpected path: {name}")
        known.add(name)
        try:
            meta = frontmatter(path / "SKILL.md")
            if meta.get("name") != name or meta.get("license") != "MIT" or not isinstance(meta.get("description"), str) or not meta.get("description"):
                errors.append(f"frontmatter mismatch: {name}")
            if isinstance(meta.get("description"), str) and len(meta["description"]) > 1024:
                errors.append(f"description too long: {name}")
        except (OSError, ValueError) as error:
            errors.append(f"{name}: {error}")
    actual = {p.parent.name for p in (root / "skills").glob("*/SKILL.md")}
    if known != actual:
        errors.append("catalog and skill directories differ")
    for path in root.rglob("*"):
        if path.is_symlink() and not (set(path.relative_to(root).parts) & EXCLUDED):
            errors.append(f"symlink is not distributable: {path.relative_to(root)}")
    # All textual files remain local to the package, without followed symlinks.
    for path in entries(root):
        if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
            errors.append(f"symlink/outside file: {path.relative_to(root)}")
            continue
        if path.suffix in {".md", ".py", ".json", ".yml", ".yaml", ".txt"}:
            text = path.read_text(encoding="utf-8")
            if re.search(r"(?:ghp_[A-Za-z0-9]{30,}|sk-[A-Za-z0-9]{30,}|-----BEGIN [A-Z ]*PRIVATE KEY-----)", text):
                errors.append(f"possible embedded credential: {path.relative_to(root)}")
            if re.search(r"[A-Z]:[\\/](?:Users|Documents)[\\/](?!Public\b)[^\s<>`]+", text):
                errors.append(f"machine-specific personal path: {path.relative_to(root)}")
            if path.suffix == ".py":
                try:
                    ast.parse(text, filename=str(path.relative_to(root)))
                except SyntaxError as error:
                    errors.append(f"Python syntax: {error}")
            if path.suffix == ".md":
                for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", text):
                    target = target.split("#", 1)[0].strip("<>")
                    if not target or "://" in target or target.startswith("mailto:"):
                        continue
                    resolved = (path.parent / unquote(target)).resolve()
                    if not resolved.is_relative_to(root.resolve()) or not resolved.exists():
                        errors.append(f"missing local reference: {path.relative_to(root)} -> {target}")
    cases = json.loads((root / "evals/cases.json").read_text(encoding="utf-8"))["cases"]
    ids = [case["id"] for case in cases]
    if len(ids) != len(set(ids)):
        errors.append("duplicate evaluation case id")
    for name in known:
        if {case["kind"] for case in cases if case["skill"] == name} != {"positive", "boundary"}:
            errors.append(f"missing evaluation coverage: {name}")
    return errors


def install(destination: Path, names: list[str], *, root: Path = ROOT, dry_run: bool = False) -> list[str]:
    errors = validate(root)
    if errors:
        raise ValueError("library validation failed: " + "; ".join(errors))
    available = {item["id"]: root / item["path"] for item in catalog(root)["skills"]}
    names = names or list(available)
    if len(names) != len(set(names)) or set(names) - available.keys():
        raise ValueError("duplicate or unknown skill selection")
    destination = destination.resolve()
    sources = [available[name].resolve() for name in names]
    if destination == root.resolve() or destination.is_relative_to((root / "skills").resolve()):
        raise ValueError("destination cannot be the source library")
    for name in names:
        target = destination / name
        if target.exists() or target.is_symlink():
            raise ValueError(f"destination skill already exists: {name}")
    if not dry_run:
        destination.mkdir(parents=True, exist_ok=True)
        # Stage complete folders first. Each move refuses an existing nonempty target.
        with tempfile.TemporaryDirectory(prefix=".skill-install-", dir=destination) as temporary:
            stage = Path(temporary)
            for name, source in zip(names, sources):
                shutil.copytree(source, stage / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            for name in names:
                (stage / name).rename(destination / name)
    return names


def build(output: Path, *, root: Path = ROOT) -> Path:
    errors = validate(root)
    if errors:
        raise ValueError("library validation failed: " + "; ".join(errors))
    output = output.resolve()
    if output.is_relative_to(root.resolve()) and output != (root / "dist").resolve():
        raise ValueError("inside the library, build output must be dist/")
    files = entries(root)
    version = catalog(root)["version"]
    output.mkdir(parents=True, exist_ok=True)
    archive = output / f"research-workflow-skills-v{version}.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for path in files:
            info = zipfile.ZipInfo("research-workflow-skills/" + path.relative_to(root).as_posix(), (2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            bundle.writestr(info, path.read_bytes())
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    (output / "SHA256SUMS").write_text(f"{digest}  {archive.name}\n", encoding="utf-8")
    return archive


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("validate")
    commands.add_parser("catalog")
    installation = commands.add_parser("install")
    installation.add_argument("--destination", type=Path, required=True)
    installation.add_argument("--skill", action="append", default=[])
    installation.add_argument("--dry-run", action="store_true")
    package = commands.add_parser("build")
    package.add_argument("--output", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    try:
        if args.command == "validate":
            errors = validate()
            print(json.dumps({"skills": len(catalog()["skills"]), "errors": errors}, ensure_ascii=False, indent=2))
            return int(bool(errors))
        if args.command == "catalog":
            print(json.dumps(catalog(), ensure_ascii=False, indent=2))
        elif args.command == "install":
            installed = install(args.destination, args.skill, dry_run=args.dry_run)
            print(json.dumps({"skills": installed, "dry_run": args.dry_run}, ensure_ascii=False))
        elif args.command == "build":
            print(build(args.output))
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, f"ERROR: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
