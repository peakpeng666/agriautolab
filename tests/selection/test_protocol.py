"""D3-D4 协议先于结果封存的证据测试。"""

import hashlib
import json
from pathlib import Path

import pytest

from agriautolab.evidence.ledger import artifact_chain_entry, verify_artifact_chain
from agriautolab.selection.evidence import seal_selection_protocol, write_selection_protocol
from agriautolab.selection.protocol import (
    RECOMMENDER_PARAMS,
    SELECTION_FEATURE_IDS,
    ZERO_OK_POLICY,
    selection_protocol_hash,
    selection_protocol_payload,
)


def _ledger_with_d1_d2(path: Path) -> None:
    first = artifact_chain_entry(0, "0" * 64, {"event": "cv_assignment_sealed"})
    second = artifact_chain_entry(1, first["entry_hash"], {"artifact": "pool_census"})
    path.write_text(
        json.dumps(first, sort_keys=True) + "\n" + json.dumps(second, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def test_protocol_freezes_features_preferences_baselines_and_model():
    payload = selection_protocol_payload(cv_spec_hash="a" * 64, pool_hash="b" * 64)
    assert payload["feature_ids"] == list(SELECTION_FEATURE_IDS)
    assert len(payload["feature_ids"]) == 12
    assert payload["preference_grid"]["n_points"] == 22
    assert payload["baselines"]["primary"] == "random_applicable_exact_mean_over_A_x"
    assert payload["baselines"]["oracle_sampling"] is False
    assert payload["loss"]["zero_ok_policy"] == ZERO_OK_POLICY
    assert payload["recommender"]["hyperparameter_search"] is False
    assert payload["recommender"]["params"] == RECOMMENDER_PARAMS
    assert selection_protocol_hash(cv_spec_hash="a" * 64, pool_hash="b" * 64) == selection_protocol_hash(
        cv_spec_hash="a" * 64, pool_hash="b" * 64
    )


def test_selection_protocol_sealing_is_index_two_and_idempotent(tmp_path: Path):
    protocol = tmp_path / "protocol.json"
    ledger = tmp_path / "ledger.jsonl"
    _ledger_with_d1_d2(ledger)
    write_selection_protocol(cv_spec_hash="c" * 64, pool_hash="d" * 64, path=protocol)

    first = seal_selection_protocol(protocol_path=protocol, ledger_path=ledger)
    bytes_after_first = ledger.read_bytes()
    second = seal_selection_protocol(protocol_path=protocol, ledger_path=ledger)
    assert first == second
    assert first["index"] == 2
    assert ledger.read_bytes() == bytes_after_first
    entries = tuple(json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines())
    verify_artifact_chain(entries)
    assert len(entries) == 3


def test_selection_protocol_refuses_code_document_drift(tmp_path: Path):
    protocol = tmp_path / "protocol.json"
    ledger = tmp_path / "ledger.jsonl"
    _ledger_with_d1_d2(ledger)
    document = write_selection_protocol(cv_spec_hash="e" * 64, pool_hash="f" * 64, path=protocol)
    document["feature_ids"][0] = "tampered"
    protocol.write_text(json.dumps(document, sort_keys=True), encoding="utf-8")
    with pytest.raises(ValueError, match="spec_hash"):
        seal_selection_protocol(protocol_path=protocol, ledger_path=ledger)


def test_committed_selection_protocol_replays_exactly_and_is_ledger_index_two():
    root = Path(__file__).resolve().parents[2]
    protocol_path = root / "evidence" / "block_d" / "selection_protocol_v1.json"
    ledger_path = root / "evidence" / "block_d" / "ledger.jsonl"
    document = json.loads(protocol_path.read_text(encoding="utf-8"))
    expected = selection_protocol_payload(
        cv_spec_hash=document["cv_spec_hash"],
        pool_hash=document["pool_hash"],
    )
    expected["spec_hash"] = selection_protocol_hash(
        cv_spec_hash=document["cv_spec_hash"],
        pool_hash=document["pool_hash"],
    )
    assert document == expected

    entries = tuple(json.loads(line) for line in ledger_path.read_text(encoding="utf-8").splitlines())
    verify_artifact_chain(entries)
    assert len(entries) == 3
    entry = entries[2]
    assert entry["index"] == 2
    assert entry["payload"]["artifact"] == "selection_protocol_v1"
    assert entry["payload"]["spec_hash"] == document["spec_hash"]
    assert entry["payload"]["file_sha256"] == hashlib.sha256(protocol_path.read_bytes()).hexdigest()
