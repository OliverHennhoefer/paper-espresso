#!/usr/bin/env python3
"""Measure PDF page utilization from Poppler grayscale renders."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

DEFAULT_MIN_USED_HEIGHT = 0.95
DEFAULT_MAX_BLANK_BAND = 0.08
DEFAULT_MIN_COLUMN_BALANCE = 0.80
DEFAULT_MAX_COLUMN_BOTTOM_BLANK = 0.05
BODY_TOP_RATIO = 0.05
BODY_BOTTOM_RATIO = 0.95
INK_THRESHOLD = 245


class LayoutError(RuntimeError):
    pass


def read_pgm(path: Path) -> tuple[int, int, bytes]:
    raw = path.read_bytes()
    index = 0

    def token() -> bytes:
        nonlocal index
        while index < len(raw):
            if raw[index] in b" \t\r\n":
                index += 1
                continue
            if raw[index] == ord("#"):
                newline = raw.find(b"\n", index)
                index = len(raw) if newline < 0 else newline + 1
                continue
            break
        start = index
        while index < len(raw) and raw[index] not in b" \t\r\n":
            index += 1
        if start == index:
            raise LayoutError(f"invalid PGM header: {path}")
        return raw[start:index]

    if token() != b"P5":
        raise LayoutError(f"expected binary PGM (P5): {path}")
    width = int(token())
    height = int(token())
    maximum = int(token())
    if maximum != 255:
        raise LayoutError(f"unsupported PGM maximum {maximum}: {path}")
    if raw[index:index + 2] == b"\r\n":
        index += 2
    elif index < len(raw) and raw[index] in b" \t\r\n":
        index += 1
    pixels = raw[index:index + width * height]
    if len(pixels) != width * height:
        raise LayoutError(f"truncated PGM pixel data: {path}")
    return width, height, pixels


def _largest_false_run(flags: list[bool]) -> tuple[int, int]:
    best_start = 0
    best_length = 0
    start: int | None = None
    for index, active in enumerate(flags + [True]):
        if not active and start is None:
            start = index
        elif active and start is not None:
            length = index - start
            if length > best_length:
                best_start, best_length = start, length
            start = None
    return best_start, best_length


def analyze_pixels(
    width: int,
    height: int,
    pixels: bytes,
    *,
    columns: int = 2,
    ink_threshold: int = INK_THRESHOLD,
) -> dict[str, Any]:
    if width < 10 or height < 10 or len(pixels) != width * height:
        raise LayoutError("invalid page raster")
    if columns not in (1, 2):
        raise LayoutError("only one- and two-column layouts are supported")

    x0, x1 = int(width * 0.06), int(width * 0.94)
    y0, y1 = int(height * BODY_TOP_RATIO), int(height * BODY_BOTTOM_RATIO)
    body_width = x1 - x0
    body_height = y1 - y0

    def ink_count(left: int, right: int, top: int, bottom: int) -> int:
        return sum(
            1
            for y in range(top, bottom)
            for value in pixels[y * width + left:y * width + right]
            if value < ink_threshold
        )

    row_threshold = max(2, int(body_width * 0.002))
    row_counts = [ink_count(x0, x1, y, y + 1) for y in range(y0, y1)]
    active_rows = [count >= row_threshold for count in row_counts]
    active_indexes = [index for index, active in enumerate(active_rows) if active]
    last_active = active_indexes[-1] if active_indexes else -1
    used_height = (last_active + 1) / body_height if active_indexes else 0.0
    blank_start, blank_length = _largest_false_run(active_rows)

    if columns == 1:
        column_ranges = [(x0, x1)]
    else:
        midpoint = (x0 + x1) // 2
        half_gutter = max(2, int(width * 0.012))
        column_ranges = [(x0, midpoint - half_gutter), (midpoint + half_gutter, x1)]

    column_metrics: list[dict[str, Any]] = []
    for left, right in column_ranges:
        threshold = max(1, int((right - left) * 0.002))
        counts = [ink_count(left, right, y, y + 1) for y in range(y0, y1)]
        active_indexes = [index for index, count in enumerate(counts) if count >= threshold]
        active_count = len(active_indexes)
        last_active = active_indexes[-1] if active_indexes else -1
        used_extent = (last_active + 1) / body_height if active_indexes else 0.0
        bottom_blank = 1.0 - used_extent
        column_metrics.append(
            {
                "ink_pixels": sum(counts),
                "active_rows": active_count,
                "active_row_ratio": round(active_count / body_height, 4),
                "last_active_y": y0 + last_active if active_indexes else None,
                "used_extent_ratio": round(used_extent, 4),
                "bottom_blank_height": body_height - last_active - 1,
                "bottom_blank_ratio": round(bottom_blank, 4),
            }
        )

    active_counts = [int(metric["active_rows"]) for metric in column_metrics]
    column_balance = 1.0
    if len(active_counts) > 1:
        maximum_active = max(active_counts)
        column_balance = min(active_counts) / maximum_active if maximum_active else 0.0

    total_ink = sum(row_counts)
    return {
        "width": width,
        "height": height,
        "body_crop": {"x0": x0, "x1": x1, "y0": y0, "y1": y1},
        "ink_ratio": round(total_ink / (body_width * body_height), 5),
        "active_row_ratio": round(sum(active_rows) / body_height, 4),
        "used_height_ratio": round(used_height, 4),
        "largest_blank_band": {
            "start_y": y0 + blank_start,
            "end_y": y0 + blank_start + blank_length,
            "height": blank_length,
            "ratio": round(blank_length / body_height, 4),
        },
        "columns": column_metrics,
        "column_balance": round(column_balance, 4),
    }


def layout_warnings(
    pages: list[dict[str, Any]],
    *,
    columns: int = 2,
    min_used_height: float = DEFAULT_MIN_USED_HEIGHT,
    max_blank_band: float = DEFAULT_MAX_BLANK_BAND,
    min_column_balance: float = DEFAULT_MIN_COLUMN_BALANCE,
    max_column_bottom_blank: float = DEFAULT_MAX_COLUMN_BOTTOM_BLANK,
) -> list[str]:
    warnings: list[str] = []
    for page_number, page in enumerate(pages, start=1):
        if page["used_height_ratio"] < min_used_height:
            warnings.append(
                f"page {page_number} uses only {page['used_height_ratio']:.1%} of body height"
            )
        blank_ratio = page["largest_blank_band"]["ratio"]
        if blank_ratio > max_blank_band:
            warnings.append(f"page {page_number} has a {blank_ratio:.1%} empty horizontal band")
        if columns > 1 and page["column_balance"] < min_column_balance:
            warnings.append(
                f"page {page_number} column balance is {page['column_balance']:.1%}"
            )
        for column_number, column in enumerate(page["columns"], start=1):
            bottom_blank = column["bottom_blank_ratio"]
            if bottom_blank > max_column_bottom_blank:
                warnings.append(
                    f"page {page_number} column {column_number} leaves "
                    f"{bottom_blank:.1%} of body height empty at the bottom"
                )
    return warnings


def layout_failures(
    pages: list[dict[str, Any]],
    **kwargs: Any,
) -> list[str]:
    """Backward-compatible alias for callers migrating to warning semantics."""
    return layout_warnings(pages, **kwargs)


def analyze_pdf(
    pdf: Path,
    *,
    columns: int = 2,
    min_used_height: float = DEFAULT_MIN_USED_HEIGHT,
    max_blank_band: float = DEFAULT_MAX_BLANK_BAND,
    min_column_balance: float = DEFAULT_MIN_COLUMN_BALANCE,
    max_column_bottom_blank: float = DEFAULT_MAX_COLUMN_BOTTOM_BLANK,
) -> dict[str, Any]:
    pdf_path = pdf.expanduser().resolve()
    if not pdf_path.is_file():
        raise LayoutError(f"PDF not found: {pdf_path}")
    executable = shutil.which("pdftoppm")
    if not executable:
        raise LayoutError("pdftoppm is required for layout-density analysis")

    with tempfile.TemporaryDirectory(prefix="paper-espresso-layout-") as directory:
        prefix = Path(directory) / "page"
        result = subprocess.run(
            [executable, "-gray", "-r", "72", str(pdf_path), str(prefix)],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            raise LayoutError(f"pdftoppm failed: {result.stderr.strip()}")
        pages = sorted(
            Path(directory).glob("page-*.pgm"),
            key=lambda path: int(re.search(r"(\d+)$", path.stem).group(1)),
        )
        if not pages:
            raise LayoutError("pdftoppm produced no page rasters")
        metrics = [analyze_pixels(*read_pgm(page), columns=columns) for page in pages]

    warnings = layout_warnings(
        metrics,
        columns=columns,
        min_used_height=min_used_height,
        max_blank_band=max_blank_band,
        min_column_balance=min_column_balance,
        max_column_bottom_blank=max_column_bottom_blank,
    )
    return {
        "thresholds": {
            "min_used_height": min_used_height,
            "max_blank_band": max_blank_band,
            "min_column_balance": min_column_balance,
            "max_column_bottom_blank": max_column_bottom_blank,
            "columns": columns,
        },
        "pages": metrics,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
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
    for name in (
        "min_used_height",
        "max_blank_band",
        "min_column_balance",
        "max_column_bottom_blank",
    ):
        if not 0 <= getattr(args, name) <= 1:
            parser.error(f"--{name.replace('_', '-')} must be between 0 and 1")
    try:
        report = analyze_pdf(
            args.pdf,
            columns=args.columns,
            min_used_height=args.min_used_height,
            max_blank_band=args.max_blank_band,
            min_column_balance=args.min_column_balance,
            max_column_bottom_blank=args.max_column_bottom_blank,
        )
    except (LayoutError, OSError, subprocess.SubprocessError, ValueError) as exc:
        parser.exit(2, f"error: {exc}\n")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
