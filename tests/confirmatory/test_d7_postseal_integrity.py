"""D7.1：既有 H3 封存不可回写，修正只能作为后继证据追加。"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from agriautolab.evidence.ledger import verify_artifact_chain


ROOT = Path(__file__).resolve().parents[2]
ORIGINAL_H3_RESULT_SHA256 = "3dbc41ea35640c3b430e882af1acb7bb74360120203b554c594ad92ddbf6b6f0"
ORIGINAL_H3_ENTRY_HASH = "8f85746404481c5e18c444861be14626b11ac38456ff9eb1482df266e3ffd17a"
CORRIGENDUM_ENTRY_HASH = "c278bec5af643c81a372ec116deb7cfe2766bcd3fd0793abb74fcddee653c40c"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_h3_postseal_corrigendum_is_append_only_and_primary_inference_is_unchanged() -> None:
    h3_path = ROOT / "evidence/block_d/h3_result.json"
    corrigendum_path = ROOT / "evidence/block_d/h3_corrigendum.json"
    ledger_path = ROOT / "evidence/block_d/ledger.jsonl"

    entries = tuple(
        json.loads(line)
        for line in ledger_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )
    verify_artifact_chain(entries)
    assert len(entries) >= 8
    assert tuple(entry["index"] for entry in entries) == tuple(range(len(entries)))

    # index 0..6 是历史事实；D7.1 只能追加，不能“修漂亮”原封存。
    h3_entry = entries[6]
    assert h3_entry["payload"]["artifact"] == "h3_confirmatory_result"
    assert h3_entry["entry_hash"] == ORIGINAL_H3_ENTRY_HASH
    assert h3_entry["payload"]["result_file_sha256"] == ORIGINAL_H3_RESULT_SHA256
    assert _sha256(h3_path) == ORIGINAL_H3_RESULT_SHA256

    correction_entry = entries[7]
    assert correction_entry["payload"]["artifact"] == "h3_postseal_corrigendum"
    assert correction_entry["previous_hash"] == ORIGINAL_H3_ENTRY_HASH
    assert correction_entry["entry_hash"] == CORRIGENDUM_ENTRY_HASH
    assert correction_entry["payload"]["original_h3_entry_hash"] == ORIGINAL_H3_ENTRY_HASH
    assert correction_entry["payload"]["original_h3_result_sha256"] == ORIGINAL_H3_RESULT_SHA256
    assert correction_entry["payload"]["corrigendum_file_sha256"] == _sha256(corrigendum_path)
    assert correction_entry["payload"]["primary_inference_changed"] is False

    original = json.loads(h3_path.read_text(encoding="utf-8"))
    corrigendum = json.loads(corrigendum_path.read_text(encoding="utf-8"))
    assert corrigendum["original_seal"]["ledger_index"] == 6
    assert corrigendum["status"]["one_shot_execution_claim_valid"] is False
    assert corrigendum["status"]["h3_primary_inference_changed"] is False
    assert corrigendum["status"]["h3_result_file_mutated"] is False
    assert corrigendum["status"]["ledger_entries_0_through_6_mutated"] is False

    original_track = original["analysis"]["track_70"]
    primary = corrigendum["primary_inference"]
    assert original_track["mean_D"] == primary["mean_D"]
    assert original_track["mean_recommender_loss"] == primary["mean_recommender_loss"]
    assert original_track["mean_random_applicable_loss"] == primary["mean_random_applicable_loss"]
    assert original_track["permutation"]["pvalue"] == primary["permutation_pvalue"]
    assert primary["h3_supported"] is False
    assert primary["criterion_1_triggered"] is True
    assert primary["criterion_2_triggered"] is False

    median_finding = next(
        finding
        for finding in corrigendum["findings"]
        if finding["id"] == "D7.1-P2-01"
    )
    assert median_finding["corrected_value"] is None
    assert median_finding["affected_original_values"]["track_70.median_D"] == original_track["median_D"]
