#!/usr/bin/env python3
"""Validate hard output constraints and report layout diagnostics."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from analyze_layout import (
    DEFAULT_MAX_COLUMN_BOTTOM_BLANK,
    DEFAULT_MAX_BLANK_BAND,
    DEFAULT_MIN_COLUMN_BALANCE,
    DEFAULT_MIN_USED_HEIGHT,
    LayoutError,
    analyze_pdf,
)
from tex_safety import inspect_source


class ValidationError(RuntimeError):
    pass


def page_count(pdf: Path) -> int:
    executable = shutil.which("pdfinfo")
    if not executable:
        raise ValidationError("pdfinfo is required to verify page count")
    result = subprocess.run(
        [executable, str(pdf)],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        raise ValidationError(f"pdfinfo failed: {result.stderr.strip()}")
    match = re.search(r"^Pages:\s+(\d+)\s*$", result.stdout, re.MULTILINE)
    if not match:
        raise ValidationError("pdfinfo did not report a page count")
    return int(match.group(1))


def inspect_log(log_path: Path | None) -> dict[str, list[str]]:
    issues = {
        "errors": [],
        "unresolved": [],
        "missing_glyphs": [],
        "material_overfull": [],
        "warnings": [],
    }
    if log_path is None:
        return issues
    if not log_path.is_file():
        issues["errors"].append(f"log not found: {log_path}")
        return issues
    for line in log_path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        lower = stripped.lower()
        if stripped.startswith("!") or "fatal error" in lower:
            issues["errors"].append(stripped)
        if "undefined references" in lower or ("citation" in lower and "undefined" in lower):
            issues["unresolved"].append(stripped)
        if "missing character" in lower or "missing glyph" in lower or "glyph not found" in lower:
            issues["missing_glyphs"].append(stripped)
        if "overfull \\hbox" in lower or "overfull \\vbox" in lower:
            amount = re.search(r"\(([0-9]+(?:\.[0-9]+)?)pt too (?:wide|high)\)", lower)
            if amount is None or float(amount.group(1)) > 1.0:
                issues["material_overfull"].append(stripped)
            else:
                issues["warnings"].append(stripped)
    return issues


def render(pdf: Path, render_dir: Path) -> list[str]:
    executable = shutil.which("pdftoppm")
    if not executable:
        raise ValidationError("pdftoppm is required for visual review renders")
    destination = render_dir.expanduser().resolve()
    destination.mkdir(parents=True, exist_ok=True)
    for stale_render in destination.glob("page-*.png"):
        stale_render.unlink()
    prefix = destination / "page"
    result = subprocess.run(
        [executable, "-png", "-r", "144", str(pdf), str(prefix)],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        raise ValidationError(f"pdftoppm failed: {result.stderr.strip()}")
    return [str(path) for path in sorted(destination.glob("page-*.png"))]


def validate(
    pdf: Path,
    max_pages: int,
    log: Path | None,
    render_dir: Path | None,
    *,
    exact_pages: int | None = None,
    tex: Path | None = None,
    density: bool = True,
    columns: int = 2,
    min_used_height: float = DEFAULT_MIN_USED_HEIGHT,
    max_blank_band: float = DEFAULT_MAX_BLANK_BAND,
    min_column_balance: float = DEFAULT_MIN_COLUMN_BALANCE,
    max_column_bottom_blank: float = DEFAULT_MAX_COLUMN_BOTTOM_BLANK,
) -> dict[str, Any]:
    pdf_path = pdf.expanduser().resolve()
    if not pdf_path.is_file():
        raise ValidationError(f"PDF not found: {pdf_path}")
    actual_pages = page_count(pdf_path)
    log_issues = inspect_log(log.expanduser().resolve() if log else None)
    source_issues = inspect_source(tex.expanduser().resolve()) if tex else {
        "errors": [],
        "warnings": [],
        "paper_size": None,
        "assets": [],
    }
    layout = (
        analyze_pdf(
            pdf_path,
            columns=columns,
            min_used_height=min_used_height,
            max_blank_band=max_blank_band,
            min_column_balance=min_column_balance,
            max_column_bottom_blank=max_column_bottom_blank,
        )
        if density
        else None
    )
    renders = render(pdf_path, render_dir) if render_dir else []

    failures: list[str] = []
    warnings = list(source_issues["warnings"]) + list(log_issues["warnings"])
    if actual_pages > max_pages:
        failures.append(f"maximum is {max_pages} pages, found {actual_pages}")
    if exact_pages is not None and actual_pages != exact_pages:
        failures.append(f"expected exactly {exact_pages} pages, found {actual_pages}")
    if log_issues["errors"]:
        failures.append("LaTeX log contains errors")
    if log_issues["unresolved"]:
        failures.append("LaTeX log contains unresolved references or citations")
    if log_issues["missing_glyphs"]:
        failures.append("LaTeX log contains missing characters or glyphs")
    if log_issues["material_overfull"]:
        failures.append("LaTeX log contains materially overfull boxes")
    if source_issues["errors"]:
        failures.append("TeX source violates the source policy")
    if layout:
        warnings.extend(layout["warnings"])

    report = {
        "pdf": str(pdf_path),
        "max_pages": max_pages,
        "exact_pages": exact_pages,
        "actual_pages": actual_pages,
        "log": log_issues,
        "source": source_issues,
        "layout": layout,
        "renders": renders,
        "warnings": warnings,
        "valid": not failures,
        "failures": failures,
    }
    if failures:
        raise ValidationError(json.dumps(report, indent=2))
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--max-pages", type=int, required=True)
    parser.add_argument("--exact-pages", type=int)
    parser.add_argument("--log", type=Path)
    parser.add_argument("--tex", type=Path)
    parser.add_argument("--render-dir", type=Path)
    parser.add_argument("--skip-density", action="store_true")
    parser.add_argument("--columns", type=int, choices=[1, 2], default=2)
    parser.add_argument("--min-used-height", type=float, default=DEFAULT_MIN_USED_HEIGHT)
    parser.add_argument("--max-blank-band", type=float, default=DEFAULT_MAX_BLANK_BAND)
    parser.add_argument("--min-column-balance", type=float, default=DEFAULT_MIN_COLUMN_BALANCE)
    parser.add_argument(
        "--max-column-bottom-blank",
        type=float,
        default=DEFAULT_MAX_COLUMN_BOTTOM_BLANK,
    )
    args = parser.parse_args()
    if args.max_pages < 1:
        parser.error("--max-pages must be positive")
    if args.exact_pages is not None and not 1 <= args.exact_pages <= args.max_pages:
        parser.error("--exact-pages must be positive and no greater than --max-pages")
    for name in (
        "min_used_height",
        "max_blank_band",
        "min_column_balance",
        "max_column_bottom_blank",
    ):
        if not 0 <= getattr(args, name) <= 1:
            parser.error(f"--{name.replace('_', '-')} must be between 0 and 1")
    try:
        report = validate(
            args.pdf,
            args.max_pages,
            args.log,
            args.render_dir,
            exact_pages=args.exact_pages,
            tex=args.tex,
            density=not args.skip_density,
            columns=args.columns,
            min_used_height=args.min_used_height,
            max_blank_band=args.max_blank_band,
            min_column_balance=args.min_column_balance,
            max_column_bottom_blank=args.max_column_bottom_blank,
        )
    except (LayoutError, ValidationError, OSError, subprocess.SubprocessError) as exc:
        parser.exit(2, f"error: {exc}\n")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
