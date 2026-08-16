from __future__ import annotations

import gzip
import importlib.util
import io
import json
import sys
import tarfile
import tempfile
import tomllib
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "paper-espresso"
SCRIPTS = SKILL / "scripts"
ASSETS = SKILL / "assets"


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
tex_safety = load_module("tex_safety")
validate_output = load_module("validate_output")
compile_tex = load_module("compile_tex")


def safe_digest(path: Path, body: str = r"\pehead{Bottom line} A faithful test digest.") -> Path:
    source = (ASSETS / "digest.tex").read_text(encoding="utf-8")
    source = source.replace("PAPER_ESPRESSO_PAPER_SIZE", "letterpaper")
    source = source.replace(
        "PAPER_ESPRESSO_TITLE_LINE",
        r"\href{https://arxiv.org/abs/0000.00000}{Test Paper}",
    )
    source = source.replace("PAPER_ESPRESSO_IDENTITY", "Test, 2026")
    source = source.replace("PAPER_ESPRESSO_BODY", body)
    path.write_text(source, encoding="utf-8")
    return path


def atom_feed(*titles: str) -> bytes:
    entries = []
    for index, title in enumerate(titles, start=1):
        entries.append(
            f"""
            <entry>
              <id>https://arxiv.org/abs/2601.0000{index}</id>
              <title>{title}</title>
              <summary>Abstract</summary>
              <published>2026-01-01T00:00:00Z</published>
              <updated>2026-01-01T00:00:00Z</updated>
              <author><name>Author</name></author>
            </entry>
            """
        )
    return (
        '<feed xmlns="http://www.w3.org/2005/Atom" '
        'xmlns:arxiv="http://arxiv.org/schemas/atom">'
        + "".join(entries)
        + "</feed>"
    ).encode()


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

    def test_rejects_archive_traversal(self):
        buffer = io.BytesIO()
        with tarfile.open(fileobj=buffer, mode="w") as archive:
            info = tarfile.TarInfo("../escape.tex")
            info.size = 1
            archive.addfile(info, io.BytesIO(b"x"))
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(arxiv.ArxivError):
                arxiv.safe_extract_source(buffer.getvalue(), Path(directory))

    def test_bounds_raw_gzip_expansion(self):
        payload = gzip.compress(b"\\documentclass{article}" + b"x" * 2048)
        with tempfile.TemporaryDirectory() as directory:
            with mock.patch.object(arxiv, "MAX_EXTRACTED", 128):
                with self.assertRaisesRegex(arxiv.ArxivError, "extracted-size limit"):
                    arxiv.safe_extract_source(payload, Path(directory))

    def test_rejects_non_arxiv_remote_url(self):
        with self.assertRaisesRegex(arxiv.ArxivError, "must be arXiv"):
            arxiv.resolve("https://publisher.example/paper.pdf")

    def test_close_title_candidates_require_confirmation(self):
        feed = atom_feed("Learning Dense Models", "Learning Dense Model")
        with mock.patch.object(arxiv, "_download", return_value=feed):
            result = arxiv.resolve("Learning Dense Modelling")
        self.assertTrue(result["needs_confirmation"])

    def test_unique_exact_title_is_accepted(self):
        feed = atom_feed("Learning Dense Models", "Learning Sparse Models")
        with mock.patch.object(arxiv, "_download", return_value=feed):
            result = arxiv.resolve("Learning Dense Models")
        self.assertFalse(result["needs_confirmation"])
        self.assertEqual(result["paper"]["title"], "Learning Dense Models")

    def test_imports_local_pdf_into_marked_workspace(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paper = root / "local-paper.pdf"
            paper.write_bytes(b"%PDF-1.5\nlocal")
            workspace = root / "workspace"
            workspace.mkdir()
            (workspace / ".paper-espresso-workspace").write_text("paper-espresso\n", encoding="utf-8")
            manifest = arxiv.fetch(str(paper), workspace)
            self.assertEqual(manifest["acquisition"]["kind"], "pdf")
            self.assertEqual(manifest["local_source_name"], "local-paper.pdf")
            self.assertEqual((workspace / "input" / "paper.pdf").read_bytes(), paper.read_bytes())

    def test_missing_local_pdf_fails_without_title_lookup(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = root / "workspace"
            workspace.mkdir()
            (workspace / ".paper-espresso-workspace").write_text("paper-espresso\n", encoding="utf-8")
            with mock.patch.object(arxiv, "resolve") as resolve:
                with self.assertRaisesRegex(arxiv.ArxivError, "local PDF not found"):
                    arxiv.fetch(str(root / "missing.pdf"), workspace)
            resolve.assert_not_called()


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

    def test_inventory_keeps_unreferenced_material_out_of_main_corpus(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            source = workspace / "input" / "source"
            source.mkdir(parents=True)
            (source / "main.tex").write_text(
                "\\documentclass{article}\n\\begin{document}Core claim.\\end{document}",
                encoding="utf-8",
            )
            (source / "response-letter.tex").write_text("CORPUS NOISE", encoding="utf-8")
            (source / "references.bib").write_text("BIBLIOGRAPHY NOISE", encoding="utf-8")
            figures = source / "figures"
            figures.mkdir()
            (figures / "mechanism.PNG").write_bytes(b"image")
            manifest = {
                "paper": {"title": "Test", "arxiv_id": "0000.00000"},
                "acquisition": {"kind": "source", "path": "input/source"},
            }
            (workspace / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            inventory = build_corpus.build(workspace)
            corpus = (workspace / "analysis" / "corpus.txt").read_text(encoding="utf-8")
            self.assertIn("Core claim", corpus)
            self.assertNotIn("CORPUS NOISE", corpus)
            self.assertNotIn("BIBLIOGRAPHY NOISE", corpus)
            self.assertEqual(inventory["unreferenced"], ["response-letter.tex"])
            self.assertEqual(inventory["bib_files"], ["references.bib"])
            self.assertEqual(inventory["figure_files"], ["figures/mechanism.PNG"])

    def test_pdf_extraction_adds_page_markers(self):
        result = SimpleNamespace(returncode=0, stdout="first\fsecond\f", stderr="")
        with mock.patch.object(build_corpus.shutil, "which", return_value="/tools/pdftotext"):
            with mock.patch.object(build_corpus.subprocess, "run", return_value=result):
                text = build_corpus.extract_pdf(Path("paper.pdf"))
        self.assertIn("===== PDF PAGE 1 =====\nfirst", text)
        self.assertIn("===== PDF PAGE 2 =====\nsecond", text)


class WorkspaceAndLayoutTests(unittest.TestCase):
    def test_marked_workspace_cleanup(self):
        workspace = temp_workspace.create_workspace()
        self.assertTrue(workspace.is_dir())
        temp_workspace.cleanup_workspace(workspace)
        self.assertFalse(workspace.exists())

    @staticmethod
    def raster(*, balanced: bool, final_y: int = 286) -> tuple[int, int, bytes]:
        width, height = 200, 300
        pixels = bytearray([255]) * (width * height)
        ranges = [(15, 92), (108, 185)] if balanced else [(15, 92)]
        for y in range(20, final_y, 11):
            for row in range(y, min(y + 3, height)):
                for left, right in ranges:
                    pixels[row * width + left:row * width + right] = bytes([40]) * (right - left)
        return width, height, bytes(pixels)

    def test_underfill_is_reported_as_a_warning(self):
        metrics = analyze_layout.analyze_pixels(*self.raster(balanced=True, final_y=220), columns=2)
        warnings = analyze_layout.layout_warnings([metrics], columns=2)
        self.assertTrue(any("leaves" in warning for warning in warnings))

    def test_dense_balanced_raster_has_no_warnings(self):
        metrics = analyze_layout.analyze_pixels(*self.raster(balanced=True), columns=2)
        self.assertEqual(analyze_layout.layout_warnings([metrics], columns=2), [])


class TexSafetyAndCompileTests(unittest.TestCase):
    def test_trusted_template_passes_preflight(self):
        with tempfile.TemporaryDirectory() as directory:
            source = safe_digest(Path(directory) / "digest.tex")
            report = tex_safety.require_safe_source(source)
        self.assertEqual(report["paper_size"], "letterpaper")

    def test_modified_preamble_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            source = safe_digest(Path(directory) / "digest.tex")
            source.write_text(source.read_text().replace("0.55in", "0.25in"), encoding="utf-8")
            report = tex_safety.inspect_source(source)
        self.assertTrue(any("preamble differs" in item for item in report["errors"]))

    def test_body_file_io_is_rejected_before_compilation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = safe_digest(root / "digest.tex", r"\input{/etc/passwd}")
            with mock.patch.object(compile_tex, "select_engine") as select_engine:
                with self.assertRaisesRegex(compile_tex.CompileError, "preflight failed"):
                    compile_tex.compile_tex(source, root / "output")
            select_engine.assert_not_called()

    def test_engine_specific_file_and_code_primitives_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for primitive in (r"\directlua{io.open('/etc/passwd')}", r"\XeTeXpicfile '/tmp/x'"):
                source = safe_digest(root / "digest.tex", primitive)
                report = tex_safety.inspect_source(source)
                self.assertTrue(report["errors"], primitive)

    def test_figure_must_be_explicitly_declared(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            figure = root / "figure.png"
            figure.write_bytes(b"png")
            source = safe_digest(root / "digest.tex", r"\includegraphics{figure.png}")
            report = tex_safety.inspect_source(source, assets=[], require_declared_assets=True)
            self.assertTrue(any("--asset" in item for item in report["errors"]))
            accepted = tex_safety.require_safe_source(source, assets=[figure])
            self.assertEqual(accepted["assets"], ["figure.png"])

    def test_classic_engine_compiles_in_isolation_and_replaces_stale_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = safe_digest(root / "digest.tex")
            output = root / "output"
            output.mkdir()
            (output / "digest.pdf").write_bytes(b"stale")
            calls = []

            def fake_run(command, **kwargs):
                calls.append((command, kwargs))
                self.assertNotEqual(Path(kwargs["cwd"]), source.parent)
                self.assertEqual(kwargs["env"]["openin_any"], "p")
                build = Path(next(item for item in command if item.startswith("-output-directory=")).split("=", 1)[1])
                build.mkdir(exist_ok=True)
                (build / "digest.pdf").write_bytes(b"%PDF-new")
                (build / "digest.log").write_text("ok\n", encoding="utf-8")
                (build / "digest.fls").write_text(
                    f"OUTPUT {build / 'digest.pdf'}\nOUTPUT {build / 'digest.log'}\n",
                    encoding="utf-8",
                )
                return SimpleNamespace(returncode=0, stdout="ok")

            with mock.patch.object(compile_tex, "select_engine", return_value="/tools/pdflatex"):
                with mock.patch.object(compile_tex.subprocess, "run", side_effect=fake_run):
                    report = compile_tex.compile_tex(source, output)
            self.assertEqual(len(calls), 2)
            self.assertEqual((output / "digest.pdf").read_bytes(), b"%PDF-new")
            self.assertEqual(report["preflight"]["paper_size"], "letterpaper")

    def test_tectonic_uses_untrusted_mode(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = safe_digest(root / "digest.tex")

            def fake_run(command, **_kwargs):
                self.assertIn("--untrusted", command)
                build = Path(command[command.index("--outdir") + 1])
                (build / "digest.pdf").write_bytes(b"%PDF")
                (build / "digest.log").write_text("ok\n", encoding="utf-8")
                return SimpleNamespace(returncode=0, stdout="ok")

            with mock.patch.object(compile_tex, "select_engine", return_value="/tools/tectonic"):
                with mock.patch.object(compile_tex.subprocess, "run", side_effect=fake_run):
                    report = compile_tex.compile_tex(source, root / "output")
            self.assertEqual(report["passes"], 1)


class ValidationTests(unittest.TestCase):
    def test_log_distinguishes_material_overflow_and_missing_glyphs(self):
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "digest.log"
            log.write_text(
                "Overfull \\hbox (0.4pt too wide)\n"
                "Overfull \\hbox (2.0pt too wide)\n"
                "Missing character: There is no Ω in font.\n",
                encoding="utf-8",
            )
            issues = validate_output.inspect_log(log)
        self.assertEqual(len(issues["warnings"]), 1)
        self.assertEqual(len(issues["material_overfull"]), 1)
        self.assertEqual(len(issues["missing_glyphs"]), 1)

    def test_underfill_does_not_invalidate_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pdf = root / "digest.pdf"
            pdf.write_bytes(b"%PDF")
            source = safe_digest(root / "digest.tex")
            layout = {"warnings": ["page 1 is underfilled"], "pages": [], "thresholds": {}}
            with mock.patch.object(validate_output, "page_count", return_value=1):
                with mock.patch.object(validate_output, "analyze_pdf", return_value=layout):
                    report = validate_output.validate(pdf, 1, None, None, tex=source)
        self.assertTrue(report["valid"])
        self.assertIn("page 1 is underfilled", report["warnings"])

    def test_exact_page_count_is_optional_and_enforced_when_requested(self):
        with tempfile.TemporaryDirectory() as directory:
            pdf = Path(directory) / "digest.pdf"
            pdf.write_bytes(b"%PDF")
            with mock.patch.object(validate_output, "page_count", return_value=1):
                with self.assertRaisesRegex(validate_output.ValidationError, "expected exactly 2"):
                    validate_output.validate(pdf, 2, None, None, exact_pages=2, density=False)

    def test_maximum_page_count_is_hard(self):
        with tempfile.TemporaryDirectory() as directory:
            pdf = Path(directory) / "digest.pdf"
            pdf.write_bytes(b"%PDF")
            with mock.patch.object(validate_output, "page_count", return_value=2):
                with self.assertRaisesRegex(validate_output.ValidationError, "maximum is 1"):
                    validate_output.validate(pdf, 1, None, None, density=False)


class ContractTests(unittest.TestCase):
    def test_template_is_content_neutral_and_structured(self):
        source = (ASSETS / "digest.tex").read_text(encoding="utf-8")
        self.assertIn("PAPER_ESPRESSO_BODY", source)
        self.assertIn("PAPER_ESPRESSO_PAPER_SIZE", source)
        self.assertIn("PAPER_ESPRESSO_TITLE_LINE", source)
        self.assertIn(r"\newcommand{\pehead}", source)
        self.assertIn(r"\newcommand{\pemathmark}", source)
        self.assertNotIn(r"\section{", source)
        self.assertNotIn("PAPER_ESPRESSO_AUTHORS", source)

    def test_skill_uses_progressive_disclosure_and_learning_mandate(self):
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("smallest faithful learning artifact", skill)
        self.assertIn("visible semantic guideposts", skill)
        self.assertIn("Do not add recall questions", skill)
        self.assertNotIn("content-contract.md", skill)
        self.assertLess(len(skill.encode("utf-8")), 10_000)

    def test_canonical_example_passes_source_preflight(self):
        source = ROOT / "attention-is-all-you-need-espresso.tex"
        report = tex_safety.inspect_source(source)
        self.assertEqual(report["errors"], [])
        self.assertEqual(report["paper_size"], "letterpaper")
        self.assertGreaterEqual(source.read_text(encoding="utf-8").count(r"\pehead{"), 3)
        self.assertLessEqual(source.read_text(encoding="utf-8").count(r"\pehead{"), 5)

    def test_benchmark_is_small_diverse_and_non_recall(self):
        cases = json.loads((ROOT / "evals" / "cases.json").read_text(encoding="utf-8"))
        self.assertEqual(cases["format"], 1)
        self.assertEqual(len(cases["cases"]), 3)
        self.assertEqual(len({case["arxiv_id"] for case in cases["cases"]}), 3)
        self.assertEqual(len({case["archetype"] for case in cases["cases"]}), 3)
        rubric = (ROOT / "evals" / "README.md").read_text(encoding="utf-8")
        self.assertIn("Keep the artifact open", rubric)
        self.assertIn("No delayed-recall", rubric)
        self.assertNotIn("quiz", rubric.lower())

    def test_metadata_versions_and_outcome_match(self):
        manifest = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        self.assertEqual(manifest["version"], project["project"]["version"])
        self.assertEqual(manifest["version"], "0.4.0")
        self.assertIn("learning artifact", manifest["description"])
        self.assertIn("$paper-espresso", (SKILL / "agents" / "openai.yaml").read_text())


if __name__ == "__main__":
    unittest.main()
