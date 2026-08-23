from __future__ import annotations

import hashlib
import json
from pathlib import Path

from agriautolab.evidence.hashing import content_hash
from agriautolab.evidence.ledger import verify_artifact_chain
from agriautolab.pareto.front import pool_hash
from agriautolab.pipeline.config import PipelineConfig


ROOT = Path(__file__).resolve().parents[2]


def _json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def _sha256(relative: str) -> str:
    return hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()


def test_d5_result_is_bound_to_frozen_inputs_protocol_code_and_ledger() -> None:
    result_path = ROOT / "evidence/block_d/h1_result.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    entries = tuple(
        json.loads(line)
        for line in (ROOT / "evidence/block_d/ledger.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    )
    verify_artifact_chain(entries)
    assert len(entries) >= 5
    d1, d2, d3, _d4, d5 = entries[:5]
    assert d5["index"] == 4
    assert d5["payload"]["artifact"] == "h1_confirmatory_result"
    assert hashlib.sha256(result_path.read_bytes()).hexdigest() == d5["payload"]["result_file_sha256"]

    identity = result["identity"]
    census = _json("evidence/block_d/pool_census.json")
    protocol = _json("evidence/block_d/selection_protocol_v1.json")

    assert _sha256("evidence/block_d/pool_census.json") == d2["payload"]["file_sha256"]
    assert _sha256("evidence/block_d/selection_protocol_v1.json") == d3["payload"]["file_sha256"]
    assert identity["runs_parquet_sha256"] == census["sources"]["runs_parquet_sha256"]
    assert identity["runs_parquet_sha256"] == d5["payload"]["runs_parquet_sha256"]
    assert identity["configs_sha256"] == census["sources"]["configs_sha256"]
    assert identity["configs_sha256"] == _sha256("configs/corpus_13.json")
    assert identity["manifest_sha256"] == d1["payload"]["manifest_file_sha256"]
    assert identity["manifest_sha256"] == _sha256("evidence/v7/manifest.json")

    config_items = _json("configs/corpus_13.json")
    configs = tuple(
        PipelineConfig(**{key: value for key, value in item.items() if key != "reason"})
        for item in config_items
    )
    actual_pool_hash = pool_hash(config.config_id() for config in configs)
    assert actual_pool_hash == protocol["pool_hash"]
    assert actual_pool_hash == d3["payload"]["pool_hash"]
    assert actual_pool_hash == identity["pool_hash"]
    assert actual_pool_hash == d5["payload"]["pool_hash"]

    protocol_hashes = identity["protocol_sha256_by_source"]
    for source, expected_hash in protocol_hashes.items():
        if source == "AUDIT_NOTE.md#R1-1":
            text = (ROOT / "AUDIT_NOTE.md").read_text(encoding="utf-8")
            excerpt = text[text.index("## R1-1"):text.index("## R1-2", text.index("## R1-1"))]
            actual_hash = hashlib.sha256(excerpt.encode("utf-8")).hexdigest()
        else:
            actual_hash = _sha256(source)
        assert actual_hash == expected_hash
    actual_protocol_bundle_hash = content_hash({"sha256_by_source": protocol_hashes})
    assert actual_protocol_bundle_hash == identity["protocol_bundle_hash"]
    assert actual_protocol_bundle_hash == d5["payload"]["protocol_bundle_hash"]

    code_hashes = identity["analysis_code_sha256_by_path"]
    assert {path: _sha256(path) for path in code_hashes} == code_hashes
    actual_code_hash = content_hash({"sha256_by_path": code_hashes})
    assert actual_code_hash == identity["analysis_code_hash"]
    assert actual_code_hash == d5["payload"]["analysis_code_hash"]
