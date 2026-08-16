#!/usr/bin/env python3
"""Preflight and compile a generated Paper Espresso digest in isolation."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Iterable

from tex_safety import TexSafetyError, require_safe_source


class CompileError(RuntimeError):
    pass


def select_engine(requested: str) -> str:
    choices = [requested] if requested != "auto" else ["tectonic", "pdflatex", "lualatex", "xelatex"]
    for choice in choices:
        executable = shutil.which(choice)
        if executable:
            return executable
    raise CompileError(f"LaTeX engine not found (requested: {requested})")


def _remove_stale_outputs(destination: Path, stem: str) -> None:
    for suffix in (".aux", ".fls", ".log", ".out", ".pdf", ".synctex.gz"):
        stale = destination / f"{stem}{suffix}"
        if stale.is_file():
            stale.unlink()


def _audit_recorder(recorder: Path, staging_root: Path) -> None:
    if not recorder.is_file():
        raise CompileError("classic TeX engine did not produce the required .fls recorder file")
    root = staging_root.resolve()
    for line in recorder.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.startswith("OUTPUT "):
            continue
        raw = line.removeprefix("OUTPUT ").strip()
        path = Path(raw)
        resolved = path.resolve() if path.is_absolute() else (recorder.parent / path).resolve()
        if resolved != root and root not in resolved.parents:
            raise CompileError(f"TeX wrote outside the isolated staging directory: {raw}")


def compile_tex(
    source: Path,
    output_dir: Path,
    engine: str = "auto",
    *,
    assets: Iterable[Path] = (),
) -> dict[str, object]:
    tex_path = source.expanduser().resolve()
    asset_paths = [item.expanduser().resolve() for item in assets]
    try:
        preflight = require_safe_source(tex_path, assets=asset_paths)
    except TexSafetyError as exc:
        raise CompileError(f"LaTeX preflight failed: {exc}") from exc

    destination = output_dir.expanduser().resolve()
    destination.mkdir(parents=True, exist_ok=True)
    _remove_stale_outputs(destination, tex_path.stem)
    executable = select_engine(engine)
    is_tectonic = Path(executable).name == "tectonic"

    with tempfile.TemporaryDirectory(prefix="paper-espresso-compile-") as directory:
        staging_root = Path(directory).resolve()
        source_dir = staging_root / "source"
        build_dir = staging_root / "build"
        source_dir.mkdir()
        build_dir.mkdir()
        staged_tex = source_dir / tex_path.name
        shutil.copy2(tex_path, staged_tex)
        for asset in asset_paths:
            relative = asset.relative_to(tex_path.parent)
            target = source_dir / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(asset, target)

        command = (
            [
                executable,
                "-X",
                "compile",
                "--outdir",
                str(build_dir),
                "--outfmt",
                "pdf",
                "--print",
                "--untrusted",
                "--keep-logs",
                staged_tex.name,
            ]
            if is_tectonic
            else [
                executable,
                "-no-shell-escape",
                "-interaction=nonstopmode",
                "-halt-on-error",
                "-file-line-error",
                "-recorder",
                f"-output-directory={build_dir}",
                staged_tex.name,
            ]
        )
        environment = os.environ.copy()
        environment.update({"openin_any": "p", "openout_any": "p", "TEXMFOUTPUT": str(build_dir)})
        passes = 1 if is_tectonic else 2
        last_output = ""
        for _ in range(passes):
            result = subprocess.run(
                command,
                cwd=source_dir,
                env=environment,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=180,
            )
            last_output = result.stdout
            if result.returncode != 0:
                tail = "\n".join(last_output.splitlines()[-40:])
                raise CompileError(f"LaTeX compilation failed:\n{tail}")

        pdf_path = build_dir / f"{tex_path.stem}.pdf"
        if not pdf_path.is_file():
            raise CompileError(f"compiler did not create expected PDF: {pdf_path}")
        if not is_tectonic:
            _audit_recorder(build_dir / f"{tex_path.stem}.fls", staging_root)

        final_pdf = destination / pdf_path.name
        shutil.copy2(pdf_path, final_pdf)
        log_path = build_dir / f"{tex_path.stem}.log"
        if log_path.is_file():
            shutil.copy2(log_path, destination / log_path.name)

    return {
        "engine": Path(executable).name,
        "passes": passes,
        "pdf": str(final_pdf),
        "preflight": preflight,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--asset", type=Path, action="append", default=[])
    parser.add_argument(
        "--engine",
        choices=["auto", "pdflatex", "lualatex", "xelatex", "tectonic"],
        default="auto",
    )
    args = parser.parse_args()
    try:
        result = compile_tex(args.source, args.output_dir, args.engine, assets=args.asset)
    except (CompileError, OSError, subprocess.SubprocessError) as exc:
        parser.exit(2, f"error: {exc}\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
