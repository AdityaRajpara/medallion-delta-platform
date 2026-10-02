"""Filesystem helpers. JSONL keeps the local path dependency-free and portable."""
from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Iterable

def write_jsonl(path: Path, rows: Iterable[dict]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    # Write to a temp file then rename, so a crash never leaves a truncated output.
    tmp = path.with_name(path.name + ".tmp")
    count = 0
    with tmp.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, default=str) + "\n")
            count += 1
    os.replace(tmp, path)
    return count

def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]
