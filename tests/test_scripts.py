from __future__ import annotations

import importlib.util
import io
import json
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "paper-espresso" / "scripts"
ASSETS = ROOT / "skills" / "paper-espresso" / "assets"


def load_module(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


arxiv = load_module("arxiv")
build_corpus = load_module("build_corpus")
temp_workspace = load_module("temp_workspace")
analyze_layout = load_module("analyze_layout")
validate_output = load_module("validate_output")
compile_tex = load_module("compile_tex")


class ArxivTests(unittest.TestCase):
    def test_parse_current_and_legacy_ids(self):
        self.assertEqual(arxiv.parse_arxiv_id("https://arxiv.org/pdf/1706.03762.pdf"), "1706.03762")
        self.assertEqual(arxiv.parse_arxiv_id("arXiv:hep-th/9901001v2"), "hep-th/9901001v2")

    def test_repairs_common_utf8_mojibake(self):
        self.assertEqual(arxiv.repair_mojibake("âspikinessâ"), "“spikiness”")

    def test_safe_tar_extraction(self):
        buffer = io.BytesIO()
        payload = b"\\documentclass{article}"
        with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
            info = tarfile.TarInfo("paper/main.tex")
            info.size = len(payload)
            archive.addfile(info, io.BytesIO(payload))
        with tempfile.TemporaryDirectory() as directory:
            extracted = arxiv.safe_extract_source(buffer.getvalue(), Path(directory))
            self.assertEqual(extracted, ["paper/main.tex"])
            self.assertEqual((Path(directory) / "paper" / "main.tex").read_bytes(), payload)

    def test_rejects_archive_traversal(self):
        buffer = io.BytesIO()
        with tarfile.open(fileobj=buffer, mode="w") as archive:
            info = tarfile.TarInfo("../escape.tex")
            info.size = 1
            archive.addfile(info, io.BytesIO(b"x"))
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(arxiv.ArxivError):
                arxiv.safe_extract_source(buffer.getvalue(), Path(directory))


class CorpusTests(unittest.TestCase):
    def test_flattens_local_inputs_without_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "main.tex").write_text(
                "\\documentclass{article}\n\\begin{document}\n\\input{section}\n\\end{document}\n",
                encoding="utf-8",
            )
            (root / "section.tex").write_text("Core result. % remove me\n", encoding="utf-8")
            corpus, included = build_corpus.flatten_tex(root, root / "main.tex")
            self.assertIn("Core result.", corpus)
            self.assertNotIn("remove me", corpus)
            self.assertEqual(included, ["main.tex", "section.tex"])

    def test_build_writes_inventory_and_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            source = workspace / "input" / "source"
            source.mkdir(parents=True)
            (source / "main.tex").write_text("\\documentclass{article}\n\\begin{document}x\\end{document}", encoding="utf-8")
            (source / "appendix-fragment.tex").write_text("extra evidence", encoding="utf-8")
            figures = source / "figures"
            figures.mkdir()
            (figures / "mechanism.PNG").write_bytes(b"not-a-real-image")
            manifest = {
                "paper": {"title": "Test", "arxiv_id": "0000.00000"},
                "acquisition": {"kind": "source", "path": "input/source"},
            }
            (workspace / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            inventory = build_corpus.build(workspace)
            self.assertEqual(inventory["main"], "main.tex")
            self.assertEqual(inventory["unreferenced"], ["appendix-fragment.tex"])
            self.assertEqual(inventory["figure_files"], ["figures/mechanism.PNG"])
            self.assertTrue((workspace / "analysis" / "corpus.txt").is_file())
            self.assertIn("extra evidence", (workspace / "analysis" / "corpus.txt").read_text(encoding="utf-8"))


class WorkspaceAndValidationTests(unittest.TestCase):
    def test_marked_workspace_cleanup(self):
        workspace = temp_workspace.create_workspace()
        self.assertTrue(workspace.is_dir())
        temp_workspace.cleanup_workspace(workspace)
        self.assertFalse(workspace.exists())

    def test_log_inspection(self):
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "digest.log"
            log.write_text("Overfull \\hbox (2.0pt too wide)\nLaTeX Warning: There were undefined references.\n", encoding="utf-8")
            issues = validate_output.inspect_log(log)
            self.assertEqual(len(issues["overfull"]), 1)
            self.assertEqual(len(issues["warnings"]), 1)

    def test_source_inspection_rejects_placeholders_temp_paths_and_tiny_text(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "digest.tex"
            source.write_text(
                r"\usepackage{microtype,annotate-equations}"
                "\nPAPER_ESPRESSO_TITLE /tmp/input.tex "
                r"\tiny hidden",
                encoding="utf-8",
            )
            issues = validate_output.inspect_source(source)
            self.assertEqual(len(issues["errors"]), 3)


class TemplateTests(unittest.TestCase):
    def test_digest_template_is_content_neutral(self):
        source = (ASSETS / "digest.tex").read_text(encoding="utf-8")
        self.assertIn("PAPER_ESPRESSO_BODY", source)
        self.assertIn(r"\newcommand{\pehead}", source)
        self.assertIn(r"\usepackage{wrapfig}", source)
        self.assertNotIn(r"\usepackage{annotate-equations}", source)
        self.assertNotIn(r"\section{", source)
        fixed_placeholders = (
            "PAPER_ESPRESSO_PROBLEM",
            "PAPER_ESPRESSO_CONTRIBUTION",
            "PAPER_ESPRESSO_METHOD",
            "PAPER_ESPRESSO_ASSUMPTIONS",
            "PAPER_ESPRESSO_OBJECTIVE",
            "PAPER_ESPRESSO_SIGNAL",
            "PAPER_ESPRESSO_CONSTRAINT",
            "PAPER_ESPRESSO_SYMBOLS",
            "PAPER_ESPRESSO_INTUITION",
            "PAPER_ESPRESSO_RESULTS",
            "PAPER_ESPRESSO_LIMITATIONS",
            "PAPER_ESPRESSO_RELATED",
        )
        for placeholder in fixed_placeholders:
            with self.subTest(placeholder=placeholder):
                self.assertNotIn(placeholder, source)


class LayoutTests(unittest.TestCase):
    @staticmethod
    def raster(*, balanced: bool) -> tuple[int, int, bytes]:
        width, height = 200, 300
        pixels = bytearray([255]) * (width * height)
        column_ranges = [(15, 92), (108, 185)] if balanced else [(15, 92)]
        final_y = 270 if balanced else 135
        for y in range(20, final_y, 11):
            for row in range(y, min(y + 3, height)):
                for left, right in column_ranges:
                    pixels[row * width + left:row * width + right] = bytes([40]) * (right - left)
        return width, height, bytes(pixels)

    def test_dense_balanced_raster_meets_default_targets(self):
        metrics = analyze_layout.analyze_pixels(*self.raster(balanced=True), columns=2)
        self.assertGreaterEqual(metrics["used_height_ratio"], analyze_layout.DEFAULT_MIN_USED_HEIGHT)
        self.assertLessEqual(
            metrics["largest_blank_band"]["ratio"], analyze_layout.DEFAULT_MAX_BLANK_BAND
        )
        self.assertGreaterEqual(
            metrics["column_balance"], analyze_layout.DEFAULT_MIN_COLUMN_BALANCE
        )

    def test_sparse_one_sided_raster_is_detected(self):
        metrics = analyze_layout.analyze_pixels(*self.raster(balanced=False), columns=2)
        self.assertLess(metrics["used_height_ratio"], analyze_layout.DEFAULT_MIN_USED_HEIGHT)
        self.assertLess(metrics["column_balance"], analyze_layout.DEFAULT_MIN_COLUMN_BALANCE)


class CompileTests(unittest.TestCase):
    def test_tectonic_is_untrusted_and_uses_vendored_assets(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "digest.tex"
            output = root / "output"
            source.write_text("\\documentclass{article}", encoding="utf-8")

            def fake_run(command, **kwargs):
                self.assertIn("--untrusted", command)
                self.assertIn("--keep-logs", command)
                self.assertIn("paper-espresso/assets", kwargs["env"]["TEXINPUTS"])
                output.mkdir(exist_ok=True)
                (output / "digest.pdf").write_bytes(b"%PDF-1.5")
                return SimpleNamespace(returncode=0, stdout="ok")

            with mock.patch.object(compile_tex, "select_engine", return_value="/tools/tectonic"):
                with mock.patch.object(compile_tex.subprocess, "run", side_effect=fake_run):
                    report = compile_tex.compile_tex(source, output)
            self.assertEqual(report["passes"], 1)

    def test_tex_engines_disable_shell_escape(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "digest.tex"
            output = root / "output"
            source.write_text("\\documentclass{article}", encoding="utf-8")
            commands = []

            def fake_run(command, **_kwargs):
                commands.append(command)
                output.mkdir(exist_ok=True)
                (output / "digest.pdf").write_bytes(b"%PDF-1.5")
                return SimpleNamespace(returncode=0, stdout="ok")

            with mock.patch.object(compile_tex, "select_engine", return_value="/tools/pdflatex"):
                with mock.patch.object(compile_tex.subprocess, "run", side_effect=fake_run):
                    report = compile_tex.compile_tex(source, output)
            self.assertEqual(report["passes"], 2)
            self.assertTrue(all("-no-shell-escape" in command for command in commands))


if __name__ == "__main__":
    unittest.main()
