"""Append-only sealing of evaluation result records into the JSONL experiment log."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from agriautolab.pipeline import jsonl_log


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def seal_confirmatory_result(
    *,
    hypothesis: str,
    expected_index: int,
    required_previous_artifact: str,
    result_path: str | Path,
    ledger_path: str | Path,
) -> dict:
    """Seal a result at a fixed log index; existing entries may only replay byte-for-byte.

    `hypothesis` is the evaluation slug (e.g. "pareto_optimality"); the artifact
    name is ``<slug>_result``. Replays must reproduce the exact payload.
    """
    artifact = f"{hypothesis}_result"
    result_file = Path(result_path)
    document = json.loads(result_file.read_text(encoding="utf-8"))
    if document.get("hypothesis") != hypothesis:
        raise ValueError(f"result document hypothesis != {hypothesis}")
    identity = document.get("identity", {})
    required = ("analysis_code_hash", "protocol_bundle_hash", "runs_parquet_sha256", "pool_hash")
    missing = [key for key in required if not identity.get(key)]
    if missing:
        raise ValueError(f"result document is missing sealing identity keys: {missing}")

    payload = {
        "artifact": artifact,
        "hypothesis": hypothesis,
        "result_file_sha256": sha256_file(result_file),
        "analysis_code_hash": identity["analysis_code_hash"],
        "protocol_bundle_hash": identity["protocol_bundle_hash"],
        "runs_parquet_sha256": identity["runs_parquet_sha256"],
        "pool_hash": identity["pool_hash"],
    }
    ledger_file = Path(ledger_path)
    entries = jsonl_log.read_entries(ledger_file)
    jsonl_log.verify_entries(entries)
    existing = [entry for entry in entries if entry["payload"].get("artifact") == artifact]
    if existing:
        if len(existing) != 1 or existing[0]["index"] != expected_index or existing[0]["payload"] != payload:
            raise ValueError(f"sealed {hypothesis} result conflicts with the current replay")
        return existing[0]
    if len(entries) != expected_index:
        raise ValueError(
            f"evaluation record missing at log index {expected_index} "
            f"(current log length {len(entries)})"
        )
    if not entries or entries[-1]["payload"].get("artifact") != required_previous_artifact:
        raise ValueError(f"{hypothesis} requires {required_previous_artifact} as its predecessor")
    entry = jsonl_log.entry_after(entries, payload)
    with ledger_file.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
    jsonl_log.verify_entries(entries + (entry,))
    return entry
