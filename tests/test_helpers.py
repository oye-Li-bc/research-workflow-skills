from copy import deepcopy
import gzip
import importlib.util
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def module(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


arxiv = module("fetch_source", "skills/arxiv-source/scripts/fetch_source.py")
slides = module("mark_slides", "skills/notebook-slides/scripts/mark_slides.py")
environment = module("env_report", "skills/jupyter-environment/scripts/env_report.py")
links = module("check_links", "skills/obsidian-research-notes/scripts/check_links.py")
skillctl = module("skillctl", "tools/skillctl.py")


def tar_bytes(items):
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode="w") as output:
        for name, content in items:
            member = tarfile.TarInfo(name)
            if content in (tarfile.SYMTYPE, tarfile.LNKTYPE, tarfile.CHRTYPE):
                member.type = content
                member.linkname = "../../outside"
                output.addfile(member)
            else:
                member.size = len(content)
                output.addfile(member, io.BytesIO(content))
    return stream.getvalue()


class ArxivTests(unittest.TestCase):
    def test_modern_url_and_version(self):
        self.assertEqual(arxiv.arxiv_id("https://arxiv.org/pdf/2509.07996v4.pdf"), "2509.07996v4")

    def test_legacy_id(self):
        self.assertEqual(arxiv.arxiv_id("hep-th/9901001v2"), "hep-th/9901001v2")

    def test_rejects_unrelated_and_malicious_urls(self):
        for value in ["https://arxiv.org.evil.example/abs/2509.07996", "../../secret", "https://arxiv.org@evil.example/abs/2509.07996"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                arxiv.arxiv_id(value)

    def test_extract_nested_tex_and_manifest_hash(self):
        payload = gzip.compress(tar_bytes([("paper/main.tex", b"\\documentclass{article}"), ("paper/figures/a.dat", b"figure")]))
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "source"
            result = arxiv.unpack_payload(payload, target)
            self.assertEqual(result["kind"], "tex")
            self.assertEqual(result["tex_files"], ["paper/main.tex"])
            self.assertEqual((target / "paper/figures/a.dat").read_bytes(), b"figure")
            self.assertEqual(json.loads((target / "manifest.json").read_text()), result)

    def test_pdf_only_is_explicit(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "source"
            result = arxiv.unpack_payload(b"%PDF-1.4\nfixture", target)
            self.assertEqual(result["kind"], "pdf")
            self.assertFalse(result["tex_files"])

    def test_single_gzip_tex(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = arxiv.unpack_payload(gzip.compress(b"\\documentclass{article}"), Path(temporary) / "source")
            self.assertEqual(result["tex_files"], ["paper.tex"])

    def test_rejects_paths_links_devices_and_aliases(self):
        for items in [[("../outside.tex", b"x")], [("/absolute.tex", b"x")],
                      [("a\\b.tex", b"x")], [("C:/bad.tex", b"x")], [("NUL.tex", b"x")],
                      [("link.tex", tarfile.SYMTYPE)], [("link.tex", tarfile.LNKTYPE)],
                      [("device", tarfile.CHRTYPE)], [("a.tex", b"x"), ("A.tex", b"y")]]:
            with self.subTest(items=items), tempfile.TemporaryDirectory() as temporary:
                target = Path(temporary) / "source"
                with self.assertRaises(ValueError):
                    arxiv.unpack_payload(tar_bytes(items), target)
                self.assertFalse(target.exists())
                self.assertFalse((Path(temporary) / "outside.tex").exists())

    def test_rejects_download_and_expansion_limits(self):
        with tempfile.TemporaryDirectory() as temporary:
            with patch.object(arxiv, "MAX_DOWNLOAD", 10), self.assertRaises(ValueError):
                arxiv.unpack_payload(b"x" * 11, Path(temporary) / "download")
            with patch.object(arxiv, "MAX_EXPANDED", 100), self.assertRaises(ValueError):
                arxiv.unpack_payload(gzip.compress(b"x" * 101), Path(temporary) / "expanded")

    def test_failure_preserves_existing_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "source"
            target.mkdir()
            (target / "user.tex").write_text("keep")
            with self.assertRaises(ValueError):
                arxiv.unpack_payload(b"\\documentclass{article}", target)
            self.assertEqual((target / "user.tex").read_text(), "keep")

    def test_html_error_is_not_tex(self):
        with tempfile.TemporaryDirectory() as temporary, self.assertRaises(ValueError):
            arxiv.unpack_payload(b"<html>rate limited</html>", Path(temporary) / "source")

    def test_archive_cannot_replace_generated_manifest(self):
        with tempfile.TemporaryDirectory() as temporary, self.assertRaises(ValueError):
            arxiv.unpack_payload(tar_bytes([("main.tex", b"x"), ("manifest.json", b"bad")]), Path(temporary) / "source")


class NotebookTests(unittest.TestCase):
    def setUp(self):
        self.book = {"nbformat": 4, "metadata": {"kernelspec": {"name": "fixture-kernel"}}, "cells": [
            {"cell_type": "markdown", "source": ["# First"], "metadata": {}},
            {"cell_type": "code", "source": ["raise RuntimeError('do not execute')"], "metadata": {"custom": 42}, "execution_count": 9, "outputs": [{"output_type": "stream", "text": "keep"}]},
            {"cell_type": "markdown", "source": "## Detail", "metadata": {}},
            {"cell_type": "markdown", "source": "# Manual notes", "metadata": {"slideshow": {"slide_type": "notes"}}}]}

    def test_preserves_source_outputs_and_input_object(self):
        original = deepcopy(self.book)
        changed = slides.mark_slides(self.book)
        self.assertEqual(self.book, original)
        self.assertEqual(changed["metadata"], original["metadata"])
        for before, after in zip(original["cells"], changed["cells"]):
            for key in set(before) - {"metadata"}:
                self.assertEqual(after[key], before[key])
        self.assertEqual(changed["cells"][1]["metadata"]["custom"], 42)

    def test_boundaries_and_manual_override(self):
        changed = slides.mark_slides(self.book)
        self.assertEqual([cell["metadata"]["slideshow"]["slide_type"] for cell in changed["cells"]], ["slide", "-", "subslide", "notes"])

    def test_idempotent(self):
        changed = slides.mark_slides(self.book)
        self.assertEqual(slides.mark_slides(changed), changed)

    def test_cell_mode_does_not_override_notes(self):
        changed = slides.mark_slides(self.book, "cells")
        self.assertEqual(changed["cells"][1]["metadata"]["slideshow"]["slide_type"], "slide")
        self.assertEqual(changed["cells"][3]["metadata"]["slideshow"]["slide_type"], "notes")

    def test_environment_summary_does_not_read_cell_text(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "book.ipynb"
            path.write_text(json.dumps(self.book))
            summary = environment.notebook_summary(path)
            self.assertEqual(summary["cell_types"], {"markdown": 3, "code": 1})
            self.assertNotIn("RuntimeError", json.dumps(summary))
            self.assertEqual(summary["kernelspec"]["name"], "fixture-kernel")

    def test_package_metadata_does_not_import_ml_packages(self):
        with patch.object(environment.metadata, "version", side_effect=environment.metadata.PackageNotFoundError):
            result = environment.report()
            self.assertTrue(all(value is None for value in result["packages"].values()))


class WikiTests(unittest.TestCase):
    def make_vault(self, root):
        (root / "papers").mkdir()
        (root / "papers/Method.md").write_text("method", encoding="utf-8")
        (root / "figure.png").write_bytes(b"fixture")

    def test_aliases_escaped_table_aliases_embeds_and_anchors(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.make_vault(root)
            (root / "Index.md").write_text("[[papers/Method|Method]]\n| [[Method\\|label]] |\n![[figure.png]]\n[[Method#Details]]\n[[#Local]]", encoding="utf-8")
            result = links.check_links(root)
            self.assertEqual(result["checked_links"], 4)
            self.assertEqual(result["errors"], [])

    def test_missing_and_ambiguous(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.make_vault(root)
            (root / "Method.md").write_text("duplicate")
            (root / "Index.md").write_text("[[Method]] [[Missing]] [[papers/Method]]")
            errors = links.check_links(root)["errors"]
            self.assertEqual({error["reason"] for error in errors}, {"ambiguous", "missing"})
            self.assertEqual(len(errors), 2)

    def test_code_examples_are_ignored(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "Example.md").write_text("```md\n[[Missing]]\n```\n`[[Missing2]]`\n\\[[Escaped]]")
            self.assertEqual(links.check_links(root)["checked_links"], 0)

    def test_relative_target(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.make_vault(root)
            (root / "papers/Other.md").write_text("[[./Method]] [[../figure.png]]")
            self.assertEqual(links.check_links(root)["errors"], [])

    def test_does_not_edit_vault(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "Index.md").write_text("[[Missing]]")
            before = {p.name: p.read_bytes() for p in root.iterdir()}
            links.check_links(root)
            self.assertEqual(before, {p.name: p.read_bytes() for p in root.iterdir()})


class LibraryTests(unittest.TestCase):
    def test_library_validates(self):
        self.assertEqual(skillctl.validate(), [])

    def test_install_copies_complete_independent_skill(self):
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "skills"
            names = skillctl.install(destination, ["arxiv-source"])
            self.assertEqual(names, ["arxiv-source"])
            self.assertTrue((destination / "arxiv-source/scripts/fetch_source.py").is_file())
            self.assertEqual(skillctl.frontmatter(destination / "arxiv-source/SKILL.md")["name"], "arxiv-source")

    def test_install_refuses_overwrite_and_unknown_skill(self):
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary)
            (destination / "arxiv-source").mkdir()
            (destination / "arxiv-source/SKILL.md").write_text("user version")
            with self.assertRaises(ValueError):
                skillctl.install(destination, ["arxiv-source"])
            self.assertEqual((destination / "arxiv-source/SKILL.md").read_text(), "user version")
            with self.assertRaises(ValueError):
                skillctl.install(destination, ["does-not-exist"])

    def test_dry_run_has_no_side_effect(self):
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "absent"
            skillctl.install(destination, ["arxiv-source"], dry_run=True)
            self.assertFalse(destination.exists())

    def test_build_reproducible_and_excludes_reports(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            archive = skillctl.build(output)
            first = archive.read_bytes()
            self.assertEqual(first, skillctl.build(output).read_bytes())
            import zipfile
            with zipfile.ZipFile(archive) as bundle:
                self.assertFalse(any("__pycache__" in name or "/.git/" in name or "/reports/" in name for name in bundle.namelist()))
                self.assertEqual(len([name for name in bundle.namelist() if name.endswith("/SKILL.md")]), 7)


if __name__ == "__main__":
    unittest.main()
