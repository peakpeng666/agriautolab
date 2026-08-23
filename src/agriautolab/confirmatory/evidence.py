"""D5/D6 结果证据的只追加封存。"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from agriautolab.evidence.ledger import artifact_chain_entry, verify_artifact_chain


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
    """按指定序位封存结果；既有条目只能逐字幂等重放。"""
    normalized = hypothesis.upper()
    artifact = f"{normalized.lower()}_confirmatory_result"
    result_file = Path(result_path)
    document = json.loads(result_file.read_text(encoding="utf-8"))
    if document.get("hypothesis") != normalized:
        raise ValueError("结果文件 hypothesis 与封存请求不一致")
    identity = document.get("identity", {})
    required = ("analysis_code_hash", "protocol_bundle_hash", "runs_parquet_sha256", "pool_hash")
    missing = [key for key in required if not identity.get(key)]
    if missing:
        raise ValueError(f"结果文件缺少封存身份：{missing}")

    payload = {
        "artifact": artifact,
        "hypothesis": normalized,
        "result_file_sha256": sha256_file(result_file),
        "analysis_code_hash": identity["analysis_code_hash"],
        "protocol_bundle_hash": identity["protocol_bundle_hash"],
        "runs_parquet_sha256": identity["runs_parquet_sha256"],
        "pool_hash": identity["pool_hash"],
    }
    ledger_file = Path(ledger_path)
    entries = tuple(
        json.loads(line)
        for line in ledger_file.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )
    verify_artifact_chain(entries)
    existing = [entry for entry in entries if entry["payload"].get("artifact") == artifact]
    if existing:
        if len(existing) != 1 or existing[0]["index"] != expected_index or existing[0]["payload"] != payload:
            raise ValueError(f"已封存的 {normalized} 结果与当前重放冲突")
        return existing[0]
    if len(entries) != expected_index:
        raise ValueError(f"{normalized} 必须封为 index={expected_index}，当前 ledger 长度={len(entries)}")
    if not entries or entries[-1]["payload"].get("artifact") != required_previous_artifact:
        raise ValueError(f"{normalized} 前序必须是 {required_previous_artifact}")
    entry = artifact_chain_entry(expected_index, entries[-1]["entry_hash"], payload)
    with ledger_file.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
    verify_artifact_chain(entries + (entry,))
    return entry

