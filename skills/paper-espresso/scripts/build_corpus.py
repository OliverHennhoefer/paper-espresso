#!/usr/bin/env python3
"""Build a non-executing text corpus from acquired TeX or PDF input."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

INCLUDE_RE = re.compile(r"\\(?:input|include)\s*\{([^}]+)\}")
COMMENT_RE = re.compile(r"(?<!\\)%.*")
MAX_CORPUS_BYTES = 30 * 1024 * 1024
FIGURE_SUFFIXES = {
    ".eps",
    ".jpeg",
    ".jpg",
    ".pdf",
    ".png",
    ".svg",
    ".tif",
    ".tiff",
    ".webp",
}


class CorpusError(RuntimeError):
    pass


def _safe_child(root: Path, candidate: Path) -> Path:
    resolved_root = root.resolve()
    resolved = candidate.resolve()
    if resolved != resolved_root and resolved_root not in resolved.parents:
        raise CorpusError(f"include escapes source root: {candidate}")
    return resolved


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def choose_main(tex_files: list[Path]) -> Path:
    if not tex_files:
        raise CorpusError("no TeX files found")

    def score(path: Path) -> tuple[int, int, str]:
        text = _read_text(path)[:250_000]
        value = 0
        value += 100 if "\\documentclass" in text else 0
        value += 50 if "\\begin{document}" in text else 0
        value += 20 if path.name.lower() in {"main.tex", "paper.tex", "manuscript.tex", "ms.tex"} else 0
        return value, -len(path.parts), path.as_posix()

    return max(tex_files, key=score)


def flatten_tex(root: Path, main: Path) -> tuple[str, list[str]]:
    root = root.resolve()
    main = main.resolve()
    visited: set[Path] = set()
    included: list[str] = []

    def expand(path: Path, depth: int = 0) -> str:
        if depth > 40:
            raise CorpusError("TeX include depth exceeds 40")
        resolved = _safe_child(root, path)
        if resolved in visited:
            return f"\n% [Paper Espresso: skipped repeated include {resolved.relative_to(root)}]\n"
        if not resolved.is_file():
            return f"\n% [Paper Espresso: missing include {resolved.relative_to(root)}]\n"
        visited.add(resolved)
        relative = resolved.relative_to(root).as_posix()
        included.append(relative)
        text = _read_text(resolved)
        lines = [COMMENT_RE.sub("", line) for line in text.splitlines()]
        text = "\n".join(lines)

        def replace(match: re.Match[str]) -> str:
            raw = match.group(1).strip()
            include = resolved.parent / raw
            if include.suffix == "":
                include = include.with_suffix(".tex")
            return expand(include, depth + 1)

        expanded = INCLUDE_RE.sub(replace, text)
        return f"\n% ===== FILE: {relative} =====\n{expanded}\n% ===== END FILE: {relative} =====\n"

    corpus = expand(main)
    if len(corpus.encode("utf-8")) > MAX_CORPUS_BYTES:
        raise CorpusError("flattened TeX corpus exceeds size limit")
    return corpus, included


def extract_pdf(pdf_path: Path) -> str:
    executable = shutil.which("pdftotext")
    if not executable:
        raise CorpusError("pdftotext is required for PDF fallback extraction")
    result = subprocess.run(
        [executable, "-layout", str(pdf_path), "-"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        raise CorpusError(f"pdftotext failed: {result.stderr.strip()}")
    pages = result.stdout.split("\f")
    if pages and not pages[-1].strip():
        pages.pop()
    if not pages:
        raise CorpusError("pdftotext produced no page content")
    return "\n\n".join(
        f"===== PDF PAGE {number} =====\n{page.rstrip()}"
        for number, page in enumerate(pages, start=1)
    ) + "\n"


def build(work_dir: Path) -> dict[str, Any]:
    workspace = work_dir.expanduser().resolve()
    manifest_path = workspace / "manifest.json"
    if not manifest_path.is_file():
        raise CorpusError(f"manifest missing: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    acquisition = manifest["acquisition"]
    analysis_dir = workspace / "analysis"
    analysis_dir.mkdir(exist_ok=True)

    if acquisition["kind"] == "source":
        source_root = _safe_child(workspace, workspace / acquisition["path"])
        tex_files = sorted(path for path in source_root.rglob("*.tex") if path.is_file())
        main = choose_main(tex_files)
        corpus, included = flatten_tex(source_root, main)
        unreferenced = [
            path.relative_to(source_root).as_posix()
            for path in tex_files
            if path.relative_to(source_root).as_posix() not in included
        ]
        bib_files = sorted(path for path in source_root.rglob("*.bib") if path.is_file())
        figure_files = sorted(
            path
            for path in source_root.rglob("*")
            if path.is_file() and path.suffix.lower() in FIGURE_SUFFIXES
        )
        inventory = {
            "kind": "source",
            "main": main.relative_to(source_root).as_posix(),
            "included": included,
            "unreferenced": unreferenced,
            "tex_files": [path.relative_to(source_root).as_posix() for path in tex_files],
            "bib_files": [path.relative_to(source_root).as_posix() for path in bib_files],
            "figure_files": [path.relative_to(source_root).as_posix() for path in figure_files],
        }
    elif acquisition["kind"] == "pdf":
        pdf_path = _safe_child(workspace, workspace / acquisition["path"])
        corpus = extract_pdf(pdf_path)
        inventory = {"kind": "pdf", "pdf": pdf_path.relative_to(workspace).as_posix()}
    else:
        raise CorpusError(f"unsupported acquisition kind: {acquisition['kind']}")

    header = {
        key: manifest["paper"].get(key)
        for key in ("arxiv_id", "title", "authors", "abstract", "published", "updated", "abs_url", "license")
    }
    corpus_text = "PAPER METADATA\n" + json.dumps(header, indent=2) + "\n\nPAPER CONTENT\n" + corpus
    if len(corpus_text.encode("utf-8")) > MAX_CORPUS_BYTES:
        raise CorpusError("corpus exceeds size limit")
    (analysis_dir / "corpus.txt").write_text(corpus_text, encoding="utf-8")
    (analysis_dir / "inventory.json").write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")
    return inventory


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("work_dir", type=Path)
    args = parser.parse_args()
    try:
        inventory = build(args.work_dir)
    except (CorpusError, OSError, KeyError, json.JSONDecodeError) as exc:
        parser.exit(2, f"error: {exc}\n")
    print(json.dumps(inventory, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
