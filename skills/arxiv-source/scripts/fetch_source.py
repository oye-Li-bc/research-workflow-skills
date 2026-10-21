"""Bounded arXiv downloader/extractor. Standard library only; never compiles TeX."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import tarfile
import tempfile
from urllib.parse import unquote, urlparse
from urllib.request import Request, urlopen

MAX_DOWNLOAD = 50 * 1024 * 1024
MAX_EXPANDED = 200 * 1024 * 1024
MAX_MEMBERS = 5000
ID_PATTERN = re.compile(r"(?:\d{4}\.\d{4,5}|[a-z][a-z.-]*(?:\.[A-Z]{2})?/\d{7})(?:v[1-9]\d*)?\Z")


def arxiv_id(value: str) -> str:
    value = value.strip()
    if "://" in value:
        parsed = urlparse(value)
        if parsed.scheme != "https" or parsed.netloc not in {"arxiv.org", "export.arxiv.org", "www.arxiv.org"}:
            raise ValueError("expected an https arxiv.org URL or a bare arXiv ID")
        value = unquote(parsed.path).removeprefix("/")
        prefix, sep, value = value.partition("/")
        if not sep or prefix not in {"abs", "pdf", "e-print", "src"}:
            raise ValueError("unsupported arXiv URL path")
        value = value.removesuffix(".pdf")
    if not ID_PATTERN.fullmatch(value):
        raise ValueError("invalid arXiv ID")
    return value


def member_path(name: str) -> Path:
    raw = PurePosixPath(name)
    if not name or raw.is_absolute() or "\\" in name or ":" in name or ".." in raw.parts:
        raise ValueError("unsafe archive path")
    if any(part.endswith((".", " ")) or part.split(".")[0].upper() in
           {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}
           for part in raw.parts):
        raise ValueError("nonportable archive path")
    return Path(*raw.parts)


def unpack_payload(payload: bytes, destination: Path) -> dict:
    destination = Path(destination)
    if len(payload) > MAX_DOWNLOAD:
        raise ValueError("download exceeds size limit")
    if destination.exists() or destination.is_symlink():
        raise ValueError("destination already exists; choose a new directory")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".arxiv-", dir=destination.parent) as temporary:
        root = Path(temporary) / "payload"
        root.mkdir()
        data = payload
        if data.startswith(b"\x1f\x8b"):
            with gzip.GzipFile(fileobj=io.BytesIO(data)) as stream:
                data = stream.read(MAX_EXPANDED + 1)
            if len(data) > MAX_EXPANDED:
                raise ValueError("gzip expansion exceeds size limit")
        if data.startswith(b"%PDF-"):
            (root / "paper.pdf").write_bytes(data)
            kind = "pdf"
        else:
            try:
                archive = tarfile.open(fileobj=io.BytesIO(data), mode="r:")
            except tarfile.ReadError:
                text = data.decode("utf-8-sig")
                if "\\documentclass" not in text and "\\begin{document}" not in text:
                    raise ValueError("response is neither PDF, TeX, nor a source tar archive")
                (root / "paper.tex").write_text(text, encoding="utf-8")
            else:
                with archive:
                    seen: set[str] = set()
                    total = 0
                    for count, member in enumerate(archive, start=1):
                        if count > MAX_MEMBERS:
                            raise ValueError("too many archive members")
                        relative = member_path(member.name)
                        if relative.as_posix().casefold() == "manifest.json":
                            raise ValueError("archive uses reserved manifest filename")
                        if not member.isdir() and not member.isfile():
                            raise ValueError("archive links and special files are unsupported")
                        key = relative.as_posix().casefold()
                        if key in seen:
                            raise ValueError("duplicate archive destination")
                        seen.add(key)
                        total += member.size
                        if total > MAX_EXPANDED or member.size < 0:
                            raise ValueError("archive expansion exceeds size limit")
                        target = root / relative
                        if member.isdir():
                            target.mkdir(parents=True, exist_ok=True)
                        else:
                            target.parent.mkdir(parents=True, exist_ok=True)
                            source = archive.extractfile(member)
                            if source is None:
                                raise ValueError("unreadable archive member")
                            with source, target.open("xb") as output:
                                shutil.copyfileobj(source, output)
            kind = "tex"
            if not list(root.rglob("*.tex")):
                raise ValueError("source payload contains no .tex file")
        files = [{"path": p.relative_to(root).as_posix(),
                  "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
                 for p in sorted(root.rglob("*")) if p.is_file()]
        manifest = {"kind": kind, "response_sha256": hashlib.sha256(payload).hexdigest(),
                    "files": files, "tex_files": [f["path"] for f in files if f["path"].endswith(".tex")]}
        (root / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        # The temporary directory is on the same filesystem; never merge trees.
        root.rename(destination)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paper", help="arXiv ID or https URL")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--archive", type=Path, help="saved payload; disables network access")
    args = parser.parse_args()
    try:
        paper = arxiv_id(args.paper)
        if args.archive:
            with args.archive.open("rb") as source:
                payload = source.read(MAX_DOWNLOAD + 1)
        else:
            request = Request("https://arxiv.org/e-print/" + paper,
                              headers={"User-Agent": "research-workflow-skills/0.1 (source retrieval)"})
            with urlopen(request, timeout=30) as response:
                payload = response.read(MAX_DOWNLOAD + 1)
        destination = args.output / ("arxiv-" + paper.replace("/", "-"))
        manifest = unpack_payload(payload, destination)
        print(json.dumps({"directory": str(destination), **manifest}, ensure_ascii=False))
    except (OSError, ValueError, tarfile.TarError, EOFError) as error:
        parser.exit(1, f"ERROR: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
