"""Predecessor-binding tests for the JSONL experiment log.

Each entry is bound to the previous entry's digest, so rewriting an earlier
payload invalidates every later entry. This matters because `commit_guarded`
reads the sealed digest from the very log an attacker may rewrite: a
self-consistent single-entry rewrite (recompute only that entry's own hash via
the public `entry()`) must be caught by `verify_entries` before the sealed-
artifact guard can be talked into overwriting sealed evidence.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from agriautolab.pipeline import jsonl_log


def _write_log(tmp_path: Path, payloads: tuple[dict, ...]) -> tuple[dict, ...]:
    log = tmp_path / "ledger.jsonl"
    for payload in payloads:
        jsonl_log.append_entry(log, payload)
    return jsonl_log.read_entries(log)


def test_rewritten_entry_with_recomputed_own_hash_is_rejected(tmp_path: Path):
    """The P1 attack: edit a payload, re-key that entry alone, keep the tail."""
    entries = list(_write_log(tmp_path, (
        {"artifact": "cv_assignment", "seed": 7},
        {"artifact": "pool_census", "nominal_size": 13},
        {"artifact": "selection_cv_result", "model_file_sha256": "a" * 64},
    )))
    forged = dict(entries[1]["payload"], nominal_size=99)
    entries[1] = jsonl_log.entry(1, forged)  # attacker recomputes only this entry's own digest
    with pytest.raises(ValueError, match="mismatch at index=1"):
        jsonl_log.verify_entries(tuple(entries))


def test_sealed_guard_cannot_be_bypassed_by_log_rewrite(tmp_path: Path):
    final = tmp_path / "sealed_result.json"
    log = tmp_path / "ledger.jsonl"
    jsonl_log.append_entry(log, {"event": "cv_assignment_sealed", "artifact": "cv_assignment"})
    jsonl_log.append_entry(log, {
        "artifact": "sealed_result",
        "file_sha256": hashlib.sha256(b"sealed evidence bytes").hexdigest(),
    })

    replacement = tmp_path / "replacement.json"
    replacement.write_bytes(b"rewritten evidence bytes")
    with pytest.raises(ValueError, match="sealed evidence"):
        jsonl_log.commit_guarded(replacement, final, log, "sealed_result", "file_sha256")
    assert not final.exists()

    entries = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
    forged_payload = dict(
        entries[1]["payload"],
        file_sha256=hashlib.sha256(b"rewritten evidence bytes").hexdigest(),
    )
    entries[1] = jsonl_log.entry(1, forged_payload)  # re-key the recorded seal, leave the tail alone
    log.write_text(
        "".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in entries),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="mismatch at index=1"):
        jsonl_log.commit_guarded(replacement, final, log, "sealed_result", "file_sha256")
    assert not final.exists()


def test_append_entry_keeps_the_log_verifiable(tmp_path: Path):
    log = tmp_path / "ledger.jsonl"
    for index, payload in enumerate((
        {"artifact": "manifest", "hash": "a" * 64},
        {"artifact": "run", "row": 1},
        {"artifact": "run", "row": 2},
    )):
        item = jsonl_log.append_entry(log, payload)
        assert item["index"] == index
    entries = jsonl_log.read_entries(log)
    assert len(entries) == 3
    assert entries[1]["prev_hash"] == entries[0]["entry_hash"]
    assert entries[2]["prev_hash"] == entries[1]["entry_hash"]
    jsonl_log.verify_entries(entries)


def test_genesis_entry_has_no_predecessor():
    genesis = jsonl_log.entry(0, {"event": "cv_assignment_sealed"})
    assert genesis["prev_hash"] is None
    jsonl_log.verify_entries((genesis,))


def test_editing_an_earlier_payload_invalidates_every_later_entry(tmp_path: Path):
    """Even a rewrite that keeps the predecessor binding must invalidate the tail."""
    entries = list(_write_log(tmp_path, (
        {"event": "cv_assignment_sealed", "artifact": "cv_assignment"},
        {"artifact": "pool_census", "nominal_size": 13},
        {"artifact": "selection_cv_result", "model_file_sha256": "b" * 64},
    )))
    entries[1] = jsonl_log.entry(1, dict(entries[1]["payload"], nominal_size=99), entries[0]["entry_hash"])
    with pytest.raises(ValueError, match="mismatch at index=2"):
        jsonl_log.verify_entries(tuple(entries))


def test_entry_after_derives_index_and_predecessor():
    genesis = jsonl_log.entry_after((), {"event": "cv_assignment_sealed"})
    assert genesis["index"] == 0
    assert genesis["prev_hash"] is None
    follower = jsonl_log.entry_after((genesis,), {"artifact": "pool_census"})
    assert follower["index"] == 1
    assert follower["prev_hash"] == genesis["entry_hash"]
    jsonl_log.verify_entries((genesis, follower))
