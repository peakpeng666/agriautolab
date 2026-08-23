"""D3-D4 协议与结果的 Block D 证据封存。"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from agriautolab.evidence.ledger import artifact_chain_entry, verify_artifact_chain
from agriautolab.selection.protocol import selection_protocol_hash, selection_protocol_payload


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_selection_protocol(*, cv_spec_hash: str, pool_hash: str, path: str | Path) -> dict:
    payload = selection_protocol_payload(cv_spec_hash=cv_spec_hash, pool_hash=pool_hash)
    document = dict(payload)
    document["spec_hash"] = selection_protocol_hash(cv_spec_hash=cv_spec_hash, pool_hash=pool_hash)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return document


def seal_selection_protocol(*, protocol_path: str | Path, ledger_path: str | Path) -> dict:
    """把 selection protocol 封为 Block D index=2；重复重放保持字节不变。"""
    protocol_file = Path(protocol_path)
    document = json.loads(protocol_file.read_text(encoding="utf-8"))
    expected_hash = selection_protocol_hash(
        cv_spec_hash=str(document["cv_spec_hash"]),
        pool_hash=str(document["pool_hash"]),
    )
    if document.get("spec_hash") != expected_hash:
        raise ValueError("selection protocol spec_hash 与代码规范不一致")

    ledger_file = Path(ledger_path)
    entries = tuple(
        json.loads(line)
        for line in ledger_file.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )
    verify_artifact_chain(entries)
    payload = {
        "artifact": "selection_protocol_v1",
        "file_sha256": _sha256_file(protocol_file),
        "spec_hash": expected_hash,
        "cv_spec_hash": document["cv_spec_hash"],
        "pool_hash": document["pool_hash"],
        "preference_grid_hash": document["preference_grid"]["hash"],
    }
    existing = [entry for entry in entries if entry["payload"].get("artifact") == "selection_protocol_v1"]
    if existing:
        if len(existing) != 1 or existing[0]["index"] != 2 or existing[0]["payload"] != payload:
            raise ValueError("已封存的 selection protocol 与当前重放冲突")
        return existing[0]
    if len(entries) != 2:
        raise ValueError("selection protocol 必须紧接 D1/D2，拒绝重排 Block D 历史")
    entry = artifact_chain_entry(2, entries[-1]["entry_hash"], payload)
    with ledger_file.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
    verify_artifact_chain(entries + (entry,))
    return entry


def seal_selection_cv_result(*, result_path: str | Path, ledger_path: str | Path, protocol_hash: str) -> dict:
    """真实训练侧 CV 跑完后封 index=3；协议 index=2 必须先存在。"""
    result_file = Path(result_path)
    ledger_file = Path(ledger_path)
    entries = tuple(
        json.loads(line)
        for line in ledger_file.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )
    verify_artifact_chain(entries)
    payload = {
        "artifact": "selection_cv_result",
        "file_sha256": _sha256_file(result_file),
        "protocol_hash": protocol_hash,
    }
    existing = [entry for entry in entries if entry["payload"].get("artifact") == "selection_cv_result"]
    if existing:
        if len(existing) != 1 or existing[0]["index"] != 3 or existing[0]["payload"] != payload:
            raise ValueError("已封存的 selection CV 结果与当前重放冲突")
        return existing[0]
    if len(entries) != 3 or entries[2]["payload"].get("artifact") != "selection_protocol_v1":
        raise ValueError("CV 结果只能在已封 selection protocol 之后追加")
    entry = artifact_chain_entry(3, entries[-1]["entry_hash"], payload)
    with ledger_file.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
    verify_artifact_chain(entries + (entry,))
    return entry
