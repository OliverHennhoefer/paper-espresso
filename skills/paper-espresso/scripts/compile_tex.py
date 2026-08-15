#!/usr/bin/env python3
"""Compile a generated LaTeX digest with shell escape disabled."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path


class CompileError(RuntimeError):
    pass


def select_engine(requested: str) -> str:
    choices = [requested] if requested != "auto" else ["pdflatex", "lualatex", "xelatex", "tectonic"]
    for choice in choices:
        executable = shutil.which(choice)
        if executable:
            return executable
    raise CompileError(f"LaTeX engine not found (requested: {requested})")


def compile_tex(source: Path, output_dir: Path, engine: str = "auto") -> dict[str, str | int]:
    tex_path = source.expanduser().resolve()
    if tex_path.suffix.lower() != ".tex" or not tex_path.is_file():
        raise CompileError(f"generated .tex source not found: {tex_path}")
    destination = output_dir.expanduser().resolve()
    destination.mkdir(parents=True, exist_ok=True)
    executable = select_engine(engine)
    assets_dir = Path(__file__).resolve().parent.parent / "assets"
    environment = os.environ.copy()
    environment["TEXINPUTS"] = os.pathsep.join(
        [str(tex_path.parent), str(assets_dir), environment.get("TEXINPUTS", "")]
    )
    is_tectonic = Path(executable).name == "tectonic"
    command = (
        [
            executable,
            "-X",
            "compile",
            "--outdir",
            str(destination),
            "--outfmt",
            "pdf",
            "--print",
            "--untrusted",
            "--keep-logs",
            tex_path.name,
        ]
        if is_tectonic
        else [
            executable,
            "-no-shell-escape",
            "-interaction=nonstopmode",
            "-halt-on-error",
            "-file-line-error",
            f"-output-directory={destination}",
            tex_path.name,
        ]
    )
    last_output = ""
    passes = 1 if is_tectonic else 2
    for _ in range(passes):
        result = subprocess.run(
            command,
            cwd=tex_path.parent,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=180,
            env=environment,
        )
        last_output = result.stdout
        if result.returncode != 0:
            tail = "\n".join(last_output.splitlines()[-40:])
            raise CompileError(f"LaTeX compilation failed:\n{tail}")
    pdf_path = destination / f"{tex_path.stem}.pdf"
    if not pdf_path.is_file():
        raise CompileError(f"compiler did not create expected PDF: {pdf_path}")
    return {"engine": Path(executable).name, "passes": passes, "pdf": str(pdf_path)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--engine", choices=["auto", "pdflatex", "lualatex", "xelatex", "tectonic"], default="auto")
    args = parser.parse_args()
    try:
        result = compile_tex(args.source, args.output_dir, args.engine)
    except (CompileError, OSError, subprocess.SubprocessError) as exc:
        parser.exit(2, f"error: {exc}\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
