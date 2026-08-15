#!/usr/bin/env python3
"""Create and remove marked Paper Espresso temporary workspaces."""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
import uuid
from pathlib import Path

MARKER = ".paper-espresso-workspace"
PREFIX = "paper-espresso-"


def create_workspace() -> Path:
    workspace = Path(tempfile.mkdtemp(prefix=PREFIX)).resolve()
    marker = {"format": 1, "token": str(uuid.uuid4())}
    (workspace / MARKER).write_text(json.dumps(marker) + "\n", encoding="utf-8")
    return workspace


def validate_workspace(path: Path) -> Path:
    workspace = path.expanduser().resolve()
    temp_root = Path(tempfile.gettempdir()).resolve()
    if workspace.parent != temp_root or not workspace.name.startswith(PREFIX):
        raise ValueError(f"refusing non-Paper-Espresso temp path: {workspace}")
    marker_path = workspace / MARKER
    if not marker_path.is_file():
        raise ValueError(f"workspace marker missing: {marker_path}")
    marker = json.loads(marker_path.read_text(encoding="utf-8"))
    if marker.get("format") != 1 or not marker.get("token"):
        raise ValueError("workspace marker is invalid")
    return workspace


def cleanup_workspace(path: Path) -> None:
    workspace = validate_workspace(path)
    shutil.rmtree(workspace)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("create", help="create a marked workspace")
    cleanup = subparsers.add_parser("cleanup", help="remove a marked workspace")
    cleanup.add_argument("path", type=Path)
    args = parser.parse_args()

    if args.command == "create":
        print(create_workspace())
    else:
        cleanup_workspace(args.path)
        print(f"removed {args.path.expanduser().resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
