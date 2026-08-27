"""Append-only JSONL experiment log.

The previous hash-chained ledger (prev_hash chain + verify_artifact_chain) was
removed in the flattening refactor. This module is its replacement: each line is
one JSON entry carrying an index, a payload, and a sha256 of that payload. The
per-line digest keeps append-only integrity checks possible (recompute and
compare) without a chain, and the "artifact" key inside payloads keeps the
sealed-artifact guard for overwrite protection.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from agriautolab.pipeline.hashing import content_hash


def entry(index: int, payload: dict) -> dict:
    """Build one log entry: index + payload + payload sha256 (no previous-hash)."""
    return {
        "index": index,
        "payload": payload,
        "entry_hash": content_hash({"index": index, "payload": payload}),
    }


def append_entry(path: str | Path, payload: dict) -> dict:
    """Append a single entry at the end of the JSONL file and return it.

    The index is derived from the current line count, so replays are
    positionally deterministic and cannot reorder history.
    """
    log = Path(path)
    log.parent.mkdir(parents=True, exist_ok=True)
    item = entry(len(read_entries(log)), payload)
    with log.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n")
    return item


def read_entries(path: str | Path) -> tuple[dict, ...]:
    """Read all lines as entries; a missing file is an empty log."""
    log = Path(path)
    if not log.exists():
        return ()
    return tuple(
        json.loads(line)
        for line in log.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )


def verify_entries(entries: tuple[dict, ...]) -> None:
    """Recompute each entry's digest and check the index sequence.

    A mismatch raises ValueError; the offending entry is reported by index.
    """
    for index, item in enumerate(entries):
        expected = entry(index, item.get("payload", {}))
        if item != expected:
            raise ValueError(f"experiment log entry mismatch at index={index}")


def sealed_sha_for(path: str | Path, artifact: str, key: str) -> str | None:
    """Return the recorded payload[key] for the first entry of `artifact`, if any."""
    for item in read_entries(path):
        payload = item.get("payload", {})
        if payload.get("artifact") == artifact and key in payload:
            return str(payload[key])
    return None


def commit_guarded(tmp: Path, final: Path, log_path: str | Path, artifact: str, key: str) -> None:
    """Commit tmp to final, honoring the sealed-artifact guard.

    Replaces the removed evidence/atomic.py: if the artifact has a sealed
    digest and the new bytes differ, refuse before touching final; identical
    bytes are an idempotent replace; unsealed artifacts get an atomic replace.
    """
    sealed = sealed_sha_for(log_path, artifact, key)
    actual = hashlib.sha256(tmp.read_bytes()).hexdigest()
    if sealed is not None and actual != sealed:
        raise ValueError(
            f"new artifact differs from sealed {artifact} ({key}={sealed[:16]}...): "
            "refusing to overwrite sealed evidence"
        )
    final.parent.mkdir(parents=True, exist_ok=True)
    os.replace(tmp, final)
