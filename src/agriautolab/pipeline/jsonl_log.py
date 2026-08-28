"""Append-only JSONL experiment log.

Each line carries an index, a payload, a digest of both, and the previous
entry's digest. The prev-hash link binds the ordered history: editing an
earlier payload invalidates every later entry, which is what
`replace_unless_sealed`'s sealed-artifact check relies on. The "artifact" key
inside payloads keeps the sealed-artifact guard for overwrite protection.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from agriautolab.pipeline.hashing import content_hash


def build_entry(index: int, payload: dict, prev_hash: str | None = None) -> dict:
    """Build one log entry: index + payload + previous entry digest.

    `prev_hash` binds this entry to the one before it (None at index 0), so
    editing an earlier payload invalidates every later entry. Without it, a
    rewritten history verifies clean and the sealed-artifact guard in
    `replace_unless_sealed` can be defeated by editing the log it reads from.
    """
    return {
        "index": index,
        "payload": payload,
        "prev_hash": prev_hash,
        "entry_hash": content_hash({"index": index, "payload": payload, "prev_hash": prev_hash}),
    }


def build_next_entry(entries: tuple[dict, ...], payload: dict) -> dict:
    """Build the next entry for an existing log: index and prev_hash both derived."""
    return build_entry(len(entries), payload, entries[-1]["entry_hash"] if entries else None)


def append_entry(path: str | Path, payload: dict) -> dict:
    """Append a single entry at the end of the JSONL file and return it.

    Index and prev_hash are derived from the current tail, so replays are
    positionally deterministic and cannot reorder history.
    """
    log = Path(path)
    log.parent.mkdir(parents=True, exist_ok=True)
    item = build_next_entry(read_entries(log), payload)
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
    """Recompute each entry's digest and check the index sequence and prev-hash chain.

    A mismatch raises ValueError; the offending entry is reported by index.
    """
    prev_hash = None
    for index, item in enumerate(entries):
        if item != build_entry(index, item.get("payload", {}), prev_hash):
            raise ValueError(f"experiment log entry mismatch at index={index}")
        prev_hash = item["entry_hash"]


def read_sealed_sha256(path: str | Path, artifact: str, key: str) -> str | None:
    """Return the recorded payload[key] for the first entry of `artifact`, if any.

    The log is chain-verified before any value is read: the sealed-artifact
    guard must only trust a log whose ordered history is intact, never one
    whose entries were rewritten and re-keyed in place.
    """
    entries = read_entries(path)
    verify_entries(entries)
    for item in entries:
        payload = item.get("payload", {})
        if payload.get("artifact") == artifact and key in payload:
            return str(payload[key])
    return None


def replace_unless_sealed(tmp: Path, final: Path, log_path: str | Path, artifact: str, key: str) -> None:
    """Replace tmp onto final, honoring the sealed-artifact guard.

    If the artifact has a sealed digest and the new bytes differ, refuse
    before touching final; identical bytes are an idempotent replace; unsealed
    artifacts get an atomic replace. The log is chain-verified before the
    sealed digest is consulted.
    """
    sealed = read_sealed_sha256(log_path, artifact, key)
    actual = hashlib.sha256(tmp.read_bytes()).hexdigest()
    if sealed is not None and actual != sealed:
        raise ValueError(
            f"new artifact differs from sealed {artifact} ({key}={sealed[:16]}...): "
            "refusing to overwrite sealed evidence"
        )
    final.parent.mkdir(parents=True, exist_ok=True)
    os.replace(tmp, final)
