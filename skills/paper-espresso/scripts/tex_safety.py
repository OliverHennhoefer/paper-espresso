#!/usr/bin/env python3
"""Preflight generated Paper Espresso LaTeX before compilation."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

TEMPLATE_PATH = Path(__file__).resolve().parents[1] / "assets" / "digest.tex"
PAPER_SIZES = {
    "a4paper",
    "a5paper",
    "b5paper",
    "executivepaper",
    "legalpaper",
    "letterpaper",
}
ASSET_SUFFIXES = {".eps", ".jpeg", ".jpg", ".pdf", ".png"}
PLACEHOLDER_RE = re.compile(r"PAPER_ESPRESSO_[A-Z0-9_]+")
INCLUDE_GRAPHICS_RE = re.compile(
    r"\\includegraphics(?:\s*\[[^]]*\])?\s*\{([^}]+)\}", re.IGNORECASE
)
FORBIDDEN_BODY_RE = re.compile(
    r"\\(?:"
    r"addbibresource|bibliography|catcode|csname|def|directlua|edef|everyjob|font|include|"
    r"includeonly|input|latelua|let|lstinputlisting|luadirect|newread|newwrite|openin|openout|"
    r"pdf(?:annot|filedump|mdfivesum|obj|refobj|startlink|xform|ximage)|read|readline|"
    r"requirepackage|scantokens|special|usepackage|write(?:18)?|xetexpdffile|xetexpicfile|"
    r"immediate|shellexcape|@@input"
    r")\b",
    re.IGNORECASE,
)
LAYOUT_FORCING_RE = re.compile(
    r"\\(?:balance|clearpage|columnbreak|flushbottom|newpage)\b"
    r"|\\usepackage(?:\[[^]]*\])?\{[^}]*(?:balance|flushend)[^}]*\}",
    re.IGNORECASE,
)
UNSAFE_HREF_RE = re.compile(r"\\href\s*\{\s*(?!https?://)[^}]+\}", re.IGNORECASE)


class TexSafetyError(RuntimeError):
    pass


def _inside(root: Path, candidate: Path) -> bool:
    resolved_root = root.resolve()
    resolved = candidate.resolve()
    return resolved == resolved_root or resolved_root in resolved.parents


def _document_parts(source: str) -> tuple[str, str]:
    marker = r"\begin{document}"
    if source.count(marker) != 1 or source.count(r"\end{document}") != 1:
        raise TexSafetyError("source must contain exactly one document environment")
    preamble, body = source.split(marker, 1)
    body, trailing = body.split(r"\end{document}", 1)
    if trailing.strip():
        raise TexSafetyError("source contains content after the document environment")
    return preamble, body


def _verify_trusted_preamble(source_preamble: str, template_path: Path) -> str:
    template = template_path.read_text(encoding="utf-8")
    template_preamble, _ = _document_parts(template)
    class_match = re.search(r"\\documentclass\s*\[([^]]+)\]\s*\{article\}", source_preamble)
    if not class_match:
        raise TexSafetyError("source does not use the trusted article document class")
    options = {part.strip().lower() for part in class_match.group(1).split(",")}
    sizes = options & PAPER_SIZES
    if len(sizes) != 1:
        raise TexSafetyError("source must declare exactly one supported paper size")
    paper_size = next(iter(sizes))
    expected = template_preamble.replace("PAPER_ESPRESSO_PAPER_SIZE", paper_size)
    if source_preamble != expected:
        raise TexSafetyError("source preamble differs from the trusted Paper Espresso template")
    return paper_size


def _resolve_assets(source_path: Path, assets: Iterable[Path] | None) -> dict[str, Path]:
    if assets is None:
        return {}
    root = source_path.parent.resolve()
    approved: dict[str, Path] = {}
    for raw in assets:
        path = raw.expanduser().resolve()
        if not path.is_file() or not _inside(root, path):
            raise TexSafetyError(f"asset must be a file inside the source directory: {raw}")
        if path.suffix.lower() not in ASSET_SUFFIXES:
            raise TexSafetyError(f"unsupported asset type: {path.suffix or '<none>'}")
        relative = path.relative_to(root).as_posix()
        approved[relative] = path
        approved[str(Path(relative).with_suffix(""))] = path
    return approved


def inspect_source(
    tex_path: Path,
    *,
    assets: Iterable[Path] | None = None,
    require_declared_assets: bool = False,
    template_path: Path = TEMPLATE_PATH,
) -> dict[str, object]:
    path = tex_path.expanduser().resolve()
    issues: dict[str, object] = {
        "errors": [],
        "warnings": [],
        "paper_size": None,
        "assets": [],
    }
    errors = issues["errors"]
    warnings = issues["warnings"]
    assert isinstance(errors, list) and isinstance(warnings, list)
    if path.suffix.lower() != ".tex" or not path.is_file():
        errors.append(f"TeX source not found: {path}")
        return issues

    source = path.read_text(encoding="utf-8", errors="replace")
    placeholders = sorted(set(PLACEHOLDER_RE.findall(source)))
    if placeholders:
        errors.append(f"unresolved placeholders: {', '.join(placeholders)}")

    try:
        preamble, body = _document_parts(source)
        issues["paper_size"] = _verify_trusted_preamble(preamble, template_path)
    except (OSError, TexSafetyError) as exc:
        errors.append(str(exc))
        body = source

    if FORBIDDEN_BODY_RE.search(body):
        errors.append("document body contains a prohibited TeX I/O or macro primitive")
    if re.search(r"\\begin\s*\{filecontents\*?\}", body, re.IGNORECASE):
        errors.append("document body contains a prohibited file-writing environment")
    if LAYOUT_FORCING_RE.search(source):
        errors.append("source uses prohibited manual page or column forcing")
    if UNSAFE_HREF_RE.search(body):
        errors.append("document body contains a non-HTTP(S) hyperlink target")
    if re.search(r"(?:^|[\s{])/(?![/\\])|(?:^|[/{])\.\.(?:/|[}\\])", body, re.MULTILINE):
        errors.append("document body contains an absolute or parent-relative path")
    if re.search(r"\\(?:tiny|scriptsize)\b", body):
        errors.append("document body uses text below the readable-size policy")
    for match in re.finditer(r"\\fontsize\s*\{\s*([0-9]+(?:\.[0-9]+)?)", body):
        if float(match.group(1)) < 9.5:
            errors.append(f"document body requests {match.group(1)} pt text below the 9.5 pt floor")
    if re.search(r"\\resizebox\s*\{", body):
        warnings.append("resizebox can make text or equations unreadably small")

    try:
        approved = _resolve_assets(path, assets)
    except TexSafetyError as exc:
        errors.append(str(exc))
        approved = {}

    referenced: dict[str, Path] = {}
    for match in INCLUDE_GRAPHICS_RE.finditer(body):
        raw = match.group(1).strip()
        candidate = Path(raw)
        if candidate.is_absolute() or ".." in candidate.parts:
            errors.append(f"unsafe figure path: {raw}")
            continue
        if require_declared_assets:
            asset = approved.get(candidate.as_posix())
            if asset is None:
                errors.append(f"figure was not declared with --asset: {raw}")
                continue
        else:
            direct = (path.parent / candidate).resolve()
            candidates = [direct] if direct.suffix else [direct.with_suffix(suffix) for suffix in ASSET_SUFFIXES]
            asset = next((item for item in candidates if item.is_file() and _inside(path.parent, item)), None)
            if asset is None:
                errors.append(f"referenced figure is missing or outside the source directory: {raw}")
                continue
        referenced[asset.relative_to(path.parent.resolve()).as_posix()] = asset

    if require_declared_assets:
        declared_paths = {item.relative_to(path.parent.resolve()).as_posix() for item in set(approved.values())}
        unused = sorted(declared_paths - set(referenced))
        if unused:
            errors.append(f"declared assets are not referenced: {', '.join(unused)}")
    issues["assets"] = sorted(referenced)
    return issues


def require_safe_source(
    tex_path: Path,
    *,
    assets: Iterable[Path] = (),
    template_path: Path = TEMPLATE_PATH,
) -> dict[str, object]:
    report = inspect_source(
        tex_path,
        assets=assets,
        require_declared_assets=True,
        template_path=template_path,
    )
    if report["errors"]:
        raise TexSafetyError("; ".join(str(item) for item in report["errors"]))
    return report
