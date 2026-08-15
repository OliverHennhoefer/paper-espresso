#!/usr/bin/env python3
"""Resolve and safely acquire arXiv papers using only the Python standard library."""

from __future__ import annotations

import argparse
import gzip
import io
import json
import re
import shutil
import tarfile
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path, PurePosixPath
from typing import Any

API_URL = "https://export.arxiv.org/api/query"
ARXIV_URL = "https://arxiv.org"
USER_AGENT = "paper-espresso/0.1 (research-paper retrieval)"
MAX_DOWNLOAD = 100 * 1024 * 1024
MAX_EXTRACTED = 250 * 1024 * 1024
MAX_MEMBERS = 5000
MATCH_THRESHOLD = 0.86
ATOM = "{http://www.w3.org/2005/Atom}"
ARXIV = "{http://arxiv.org/schemas/atom}"
ID_RE = re.compile(r"(?:arxiv:)?((?:\d{4}\.\d{4,5}|[a-z-]+(?:\.[A-Z]{2})?/\d{7})(?:v\d+)?)", re.I)


class ArxivError(RuntimeError):
    pass


@dataclass
class Paper:
    arxiv_id: str
    title: str
    authors: list[str]
    abstract: str
    published: str | None
    updated: str | None
    primary_category: str | None
    license: str | None
    abs_url: str
    pdf_url: str
    source_url: str
    match_score: float = 1.0


def normalize_title(value: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", value.lower()).split())


def repair_mojibake(value: str) -> str:
    if not any(marker in value for marker in ("â", "Ã", "Â")):
        return value
    try:
        repaired = value.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return value
    original_markers = sum(value.count(marker) for marker in ("â", "Ã", "Â"))
    repaired_markers = sum(repaired.count(marker) for marker in ("â", "Ã", "Â"))
    return repaired if repaired_markers < original_markers else value


def parse_arxiv_id(value: str) -> str | None:
    decoded = urllib.parse.unquote(value).strip()
    match = ID_RE.search(decoded)
    return match.group(1) if match else None


def _download(url: str, *, max_bytes: int = MAX_DOWNLOAD, timeout: int = 30) -> bytes:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept-Encoding": "identity"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        length = response.headers.get("Content-Length")
        if length and int(length) > max_bytes:
            raise ArxivError(f"download exceeds {max_bytes} bytes: {url}")
        chunks: list[bytes] = []
        received = 0
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            received += len(chunk)
            if received > max_bytes:
                raise ArxivError(f"download exceeds {max_bytes} bytes: {url}")
            chunks.append(chunk)
        return b"".join(chunks)


def _entry_to_paper(entry: ET.Element, requested_title: str | None) -> Paper:
    entry_url = (entry.findtext(f"{ATOM}id") or "").strip()
    arxiv_id = entry_url.rstrip("/").rsplit("/", 1)[-1]
    title = repair_mojibake(" ".join((entry.findtext(f"{ATOM}title") or "").split()))
    authors = [
        repair_mojibake(" ".join((node.findtext(f"{ATOM}name") or "").split()))
        for node in entry.findall(f"{ATOM}author")
    ]
    category_node = entry.find(f"{ARXIV}primary_category")
    license_text = entry.findtext(f"{ARXIV}license")
    score = 1.0
    if requested_title:
        score = SequenceMatcher(None, normalize_title(requested_title), normalize_title(title)).ratio()
    return Paper(
        arxiv_id=arxiv_id,
        title=title,
        authors=authors,
        abstract=repair_mojibake(" ".join((entry.findtext(f"{ATOM}summary") or "").split())),
        published=entry.findtext(f"{ATOM}published"),
        updated=entry.findtext(f"{ATOM}updated"),
        primary_category=category_node.get("term") if category_node is not None else None,
        license=license_text.strip() if license_text else None,
        abs_url=f"{ARXIV_URL}/abs/{arxiv_id}",
        pdf_url=f"{ARXIV_URL}/pdf/{arxiv_id}",
        source_url=f"{ARXIV_URL}/e-print/{arxiv_id}",
        match_score=round(score, 4),
    )


def resolve(query: str, *, max_results: int = 8) -> dict[str, Any]:
    arxiv_id = parse_arxiv_id(query)
    params: dict[str, str | int]
    requested_title: str | None
    if arxiv_id:
        params = {"id_list": arxiv_id, "max_results": 1}
        requested_title = None
    else:
        requested_title = query
        params = {"search_query": f'ti:"{query}"', "start": 0, "max_results": max_results}
    url = f"{API_URL}?{urllib.parse.urlencode(params)}"
    try:
        root = ET.fromstring(_download(url, max_bytes=5 * 1024 * 1024))
    except (ET.ParseError, OSError, urllib.error.URLError) as exc:
        raise ArxivError(f"arXiv metadata lookup failed: {exc}") from exc
    papers = [_entry_to_paper(entry, requested_title) for entry in root.findall(f"{ATOM}entry")]
    if not papers:
        raise ArxivError(f"no arXiv paper found for: {query}")
    papers.sort(key=lambda paper: paper.match_score, reverse=True)
    best = papers[0]
    return {
        "paper": asdict(best),
        "needs_confirmation": requested_title is not None and best.match_score < MATCH_THRESHOLD,
        "candidates": [asdict(paper) for paper in papers[:5]],
    }


def _safe_member_name(name: str) -> Path:
    if "\\" in name:
        raise ArxivError(f"unsafe archive path: {name}")
    pure = PurePosixPath(name)
    if pure.is_absolute() or ".." in pure.parts:
        raise ArxivError(f"unsafe archive path: {name}")
    cleaned = [part for part in pure.parts if part not in ("", ".")]
    if not cleaned:
        raise ArxivError(f"empty archive path: {name}")
    return Path(*cleaned)


def safe_extract_source(data: bytes, destination: Path) -> list[str]:
    destination.mkdir(parents=True, exist_ok=True)
    try:
        archive = tarfile.open(fileobj=io.BytesIO(data), mode="r:*")
    except tarfile.ReadError:
        raw = data
        if data.startswith(b"\x1f\x8b"):
            try:
                raw = gzip.decompress(data)
            except OSError as exc:
                raise ArxivError(f"invalid gzip source: {exc}") from exc
        if b"\\documentclass" not in raw[:2_000_000] and b"\\begin{" not in raw[:2_000_000]:
            raise ArxivError("source response is neither a safe archive nor recognizable TeX")
        (destination / "main.tex").write_bytes(raw)
        return ["main.tex"]

    extracted: list[str] = []
    total_size = 0
    with archive:
        members = archive.getmembers()
        if len(members) > MAX_MEMBERS:
            raise ArxivError(f"source archive has too many members: {len(members)}")
        for member in members:
            relative = _safe_member_name(member.name)
            if member.issym() or member.islnk() or member.isdev() or member.isfifo():
                raise ArxivError(f"unsupported archive member: {member.name}")
            total_size += max(member.size, 0)
            if total_size > MAX_EXTRACTED:
                raise ArxivError("source archive exceeds extracted-size limit")
            target = destination / relative
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            if not member.isfile():
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            source = archive.extractfile(member)
            if source is None:
                raise ArxivError(f"could not read archive member: {member.name}")
            with source, target.open("wb") as output:
                shutil.copyfileobj(source, output, length=1024 * 1024)
            extracted.append(relative.as_posix())
    if not extracted:
        raise ArxivError("source archive contained no regular files")
    return sorted(extracted)


def _prepare_workspace(work_dir: Path) -> Path:
    workspace = work_dir.expanduser().resolve()
    marker = workspace / ".paper-espresso-workspace"
    if not workspace.is_dir() or not marker.is_file():
        raise ArxivError("work directory must be created by temp_workspace.py")
    allowed = {marker.name}
    unexpected = [path.name for path in workspace.iterdir() if path.name not in allowed]
    if unexpected:
        raise ArxivError(f"work directory is not empty: {', '.join(sorted(unexpected))}")
    return workspace


def fetch(query: str, work_dir: Path, *, accept_best_match: bool = False, pdf_only: bool = False) -> dict[str, Any]:
    resolution = resolve(query)
    if resolution["needs_confirmation"] and not accept_best_match:
        candidate_lines = [
            f"{item['arxiv_id']}: {item['title']} ({item['match_score']:.2f})"
            for item in resolution["candidates"]
        ]
        raise ArxivError("ambiguous title match; verify one of:\n" + "\n".join(candidate_lines))
    paper = resolution["paper"]
    workspace = _prepare_workspace(work_dir)
    input_dir = workspace / "input"
    errors: list[str] = []
    acquisition: dict[str, Any] | None = None

    if not pdf_only:
        try:
            source_data = _download(paper["source_url"])
            source_dir = input_dir / "source"
            files = safe_extract_source(source_data, source_dir)
            acquisition = {"kind": "source", "path": "input/source", "files": files}
        except (ArxivError, OSError, urllib.error.URLError) as exc:
            errors.append(f"source: {exc}")

    if acquisition is None:
        try:
            pdf_data = _download(paper["pdf_url"])
            if not pdf_data.startswith(b"%PDF-"):
                raise ArxivError("PDF endpoint did not return a PDF")
            input_dir.mkdir(parents=True, exist_ok=True)
            pdf_path = input_dir / "paper.pdf"
            pdf_path.write_bytes(pdf_data)
            acquisition = {"kind": "pdf", "path": "input/paper.pdf", "files": ["paper.pdf"]}
        except (ArxivError, OSError, urllib.error.URLError) as exc:
            errors.append(f"pdf: {exc}")
            raise ArxivError("paper acquisition failed: " + "; ".join(errors)) from exc

    manifest = {
        "format": 1,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "paper": paper,
        "acquisition": acquisition,
        "fallback_errors": errors,
    }
    (workspace / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    resolve_parser = subparsers.add_parser("resolve", help="resolve a title, ID, or URL")
    resolve_parser.add_argument("query")
    fetch_parser = subparsers.add_parser("fetch", help="resolve and acquire a paper")
    fetch_parser.add_argument("query")
    fetch_parser.add_argument("--work-dir", required=True, type=Path)
    fetch_parser.add_argument("--accept-best-match", action="store_true")
    fetch_parser.add_argument("--pdf-only", action="store_true")
    args = parser.parse_args()

    try:
        result = resolve(args.query) if args.command == "resolve" else fetch(
            args.query,
            args.work_dir,
            accept_best_match=args.accept_best_match,
            pdf_only=args.pdf_only,
        )
    except ArxivError as exc:
        parser.exit(2, f"error: {exc}\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
