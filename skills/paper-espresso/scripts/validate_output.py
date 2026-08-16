#!/usr/bin/env python3
"""Validate a digest's source, page count, log, density, and review renders."""

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
    issues = {"errors": [], "warnings": [], "overfull": []}
    if log_path is None:
        return issues
    if not log_path.is_file():
        issues["errors"].append(f"log not found: {log_path}")
        return issues
    for line in log_path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        lower = stripped.lower()
        if "overfull \\hbox" in lower or "overfull \\vbox" in lower:
            issues["overfull"].append(stripped)
        if stripped.startswith("!") or "fatal error" in lower:
            issues["errors"].append(stripped)
        if "undefined references" in lower or ("citation" in lower and "undefined" in lower):
            issues["warnings"].append(stripped)
    return issues


def inspect_source(
    tex_path: Path | None,
    *,
    expected_pages: int | None = None,
) -> dict[str, list[str]]:
    issues = {"errors": [], "warnings": []}
    if tex_path is None:
        return issues
    if not tex_path.is_file():
        issues["errors"].append(f"TeX source not found: {tex_path}")
        return issues

    source = tex_path.read_text(encoding="utf-8", errors="replace")
    placeholders = sorted(set(re.findall(r"PAPER_ESPRESSO_[A-Z0-9_]+", source)))
    if placeholders:
        issues["errors"].append(f"unresolved placeholders: {', '.join(placeholders)}")
    if re.search(r"(?:/tmp/|/private/(?:tmp|var/folders)/|paper-espresso-[\w.-]+)", source):
        issues["errors"].append("source contains a temporary-workspace reference")
    if re.search(r"\\(?:immediate\s*)?write18|\\ShellEscape", source, re.IGNORECASE):
        issues["errors"].append("source contains a shell-execution primitive")
    if re.search(r"\\(?:tiny|scriptsize)\b", source):
        issues["errors"].append("source uses text smaller than the readable-size policy")
    for match in re.finditer(r"\\fontsize\s*\{\s*([0-9]+(?:\.[0-9]+)?)", source):
        if float(match.group(1)) < 9.5:
            issues["errors"].append(
                f"source requests an explicit {match.group(1)} pt font below the 9.5 pt floor"
            )
    if re.search(r"\\resizebox\s*\{", source):
        issues["warnings"].append("resizebox can make text or equations unreadably small")
    if not re.search(r"\\usepackage(?:\[[^]]*\])?\{[^}]*microtype[^}]*\}", source):
        issues["warnings"].append("microtype is not enabled")
    explicit_page_size = re.search(
        r"\\documentclass\s*\[[^]]*(?:[ab]\d+paper|letterpaper|legalpaper|executivepaper)",
        source,
        re.IGNORECASE,
    ) or re.search(
        r"\\usepackage\s*\[[^]]*(?:[ab]\d+paper|letterpaper|legalpaper|executivepaper|paper\s*=|paperwidth\s*=)[^]]*\]\s*\{geometry\}"
        r"|\\geometry\s*\{[^}]*(?:paper\s*=|paperwidth\s*=)",
        source,
        re.IGNORECASE,
    )
    if not explicit_page_size:
        issues["errors"].append("source does not declare an explicit paper size")
    forced_layout = []
    if re.search(r"\\(?:columnbreak|balance|flushbottom)\b", source):
        forced_layout.append("manual column balancing")
    if re.search(r"\\usepackage(?:\[[^]]*\])?\{[^}]*(?:balance|flushend)[^}]*\}", source):
        forced_layout.append("a column-balancing package")
    if expected_pages == 1 and re.search(r"\\(?:newpage|clearpage)\b", source):
        forced_layout.append("a manual page/column break in a one-page digest")
    if forced_layout:
        issues["errors"].append(
            "source uses layout forcing that can conceal underfill: "
            + ", ".join(sorted(set(forced_layout)))
        )
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
    expected_pages: int,
    log: Path | None,
    render_dir: Path | None,
    *,
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
    source_issues = inspect_source(
        tex.expanduser().resolve() if tex else None,
        expected_pages=expected_pages,
    )
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
    if actual_pages != expected_pages:
        failures.append(f"expected {expected_pages} pages, found {actual_pages}")
    if log_issues["errors"]:
        failures.append("LaTeX log contains errors")
    if log_issues["warnings"]:
        failures.append("LaTeX log contains unresolved references or citations")
    if log_issues["overfull"]:
        failures.append("LaTeX log contains overfull boxes")
    if source_issues["errors"]:
        failures.append("TeX source violates the source policy")
    if layout and not layout["valid"]:
        failures.extend(layout["failures"])
    report = {
        "pdf": str(pdf_path),
        "expected_pages": expected_pages,
        "actual_pages": actual_pages,
        "log": log_issues,
        "source": source_issues,
        "layout": layout,
        "renders": renders,
        "valid": not failures,
        "failures": failures,
    }
    if failures:
        raise ValidationError(json.dumps(report, indent=2))
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--pages", type=int, required=True)
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
    if args.pages < 1:
        parser.error("--pages must be positive")
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
            args.pages,
            args.log,
            args.render_dir,
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
