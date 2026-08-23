from __future__ import annotations

import hashlib
import json
from pathlib import Path

from agriautolab.contracts.vehicle import VehicleSpec
from agriautolab.corpus.protocol import CorpusProtocol
from agriautolab.evidence.hashing import content_hash
from agriautolab.evidence.ledger import verify_artifact_chain
from agriautolab.pareto.front import pool_hash
from agriautolab.pipeline.config import PipelineConfig


ROOT = Path(__file__).resolve().parents[2]
EXPECTED_H2_CODE_FILES = frozenset({
    "scripts/analyze_h2.py",
    "src/agriautolab/confirmatory/h2.py",
    "src/agriautolab/confirmatory/h1.py",
    "src/agriautolab/confirmatory/stats.py",
    "src/agriautolab/corpus/derived_status.py",
    "src/agriautolab/pareto/front.py",
})
EXPECTED_LEDGER_ARTIFACTS = (
    "cv_assignment_sealed",
    "pool_census",
    "selection_protocol_v1",
    "selection_cv_result",
    "h1_confirmatory_result",
    "h2_confirmatory_result",
)


def _json(relative: str):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def _sha256(relative: str) -> str:
    return hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()


def _protocol_source_sha256(source: str) -> str:
    if source != "AUDIT_NOTE.md#R1-1":
        return _sha256(source)
    text = (ROOT / "AUDIT_NOTE.md").read_text(encoding="utf-8")
    start = text.index("## R1-1")
    end = text.index("## R1-2", start)
    return hashlib.sha256(text[start:end].encode("utf-8")).hexdigest()


def test_d6_result_is_bound_to_every_predecessor_input_protocol_code_and_pratt_rule() -> None:
    result_path = ROOT / "evidence/block_d/h2_result.json"
    h1_path = ROOT / "evidence/block_d/h1_result.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    h1_result = json.loads(h1_path.read_text(encoding="utf-8"))
    entries = tuple(
        json.loads(line)
        for line in (ROOT / "evidence/block_d/ledger.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    )

    # D6 is the exact sixth append-only entry; deletion, insertion, reordering, or
    # payload mutation must fail the generic chain recomputation before identities.
    verify_artifact_chain(entries)
    assert len(entries) == 6
    assert tuple(entry["index"] for entry in entries) == tuple(range(6))
    d1, d2, d3, d4, d5, d6 = entries
    actual_artifacts = (
        d1["payload"]["event"],
        *(entry["payload"]["artifact"] for entry in entries[1:]),
    )
    assert actual_artifacts == EXPECTED_LEDGER_ARTIFACTS
    assert d6["previous_hash"] == d5["entry_hash"]

    assert result["study_id"] == "AGRIPLAN-PARETO-001"
    assert result["hypothesis"] == "H2"
    assert result["stage"] == "D6-H2-confirmatory"
    result_sha256 = hashlib.sha256(result_path.read_bytes()).hexdigest()
    assert result_sha256 == d6["payload"]["result_file_sha256"]

    identity = result["identity"]
    h1_identity = h1_result["identity"]
    census = _json("evidence/block_d/pool_census.json")
    selection_protocol = _json("evidence/block_d/selection_protocol_v1.json")
    manifest = _json("evidence/v7/manifest.json")

    # H1 is the byte-identical and chain-identical immediate predecessor.  The
    # shared dataset/protocol/pool identities cannot silently change between D5/D6.
    h1_sha256 = hashlib.sha256(h1_path.read_bytes()).hexdigest()
    assert h1_sha256 == d5["payload"]["result_file_sha256"]
    assert h1_sha256 == identity["h1_result_sha256"]
    assert d5["entry_hash"] == identity["h1_ledger_entry_hash"]
    for key in ("runs_parquet_sha256", "pool_hash", "protocol_bundle_hash"):
        assert identity[key] == h1_identity[key]
        assert identity[key] == d5["payload"][key]

    # D1 manifest and its corpus identity remain the sole full-field-universe
    # source.  H2 must not substitute a CV/holdout-derived field list.
    manifest_sha256 = _sha256("evidence/v7/manifest.json")
    assert manifest_sha256 == d1["payload"]["manifest_file_sha256"]
    assert manifest_sha256 == identity["manifest_sha256"]
    assert manifest_sha256 == h1_identity["manifest_sha256"]
    assert manifest["corpus_hash"] == d1["payload"]["corpus_hash"]

    # D2/D3 are bound as complete files, not merely selected fields copied from
    # them.  This catches otherwise-valid JSON edits outside the consumed keys.
    census_sha256 = _sha256("evidence/block_d/pool_census.json")
    selection_protocol_sha256 = _sha256("evidence/block_d/selection_protocol_v1.json")
    assert census_sha256 == d2["payload"]["file_sha256"]
    assert census_sha256 == identity["pool_census_sha256"]
    assert selection_protocol_sha256 == d3["payload"]["file_sha256"]
    assert selection_protocol_sha256 == identity["selection_protocol_sha256"]

    # runs.parquet itself stays on the data machine; its frozen byte identity is
    # independently joined through D2, H1, and the two ledger result entries.
    runs_sha256 = census["sources"]["runs_parquet_sha256"]
    assert runs_sha256 == identity["runs_parquet_sha256"]
    assert runs_sha256 == h1_identity["runs_parquet_sha256"]
    assert runs_sha256 == d5["payload"]["runs_parquet_sha256"]
    assert runs_sha256 == d6["payload"]["runs_parquet_sha256"]

    configs_sha256 = _sha256("configs/corpus_13.json")
    vehicles_sha256 = _sha256("examples/corpus/vehicles.json")
    corpus_protocol_sha256 = _sha256("examples/corpus/corpus_protocol.json")
    assert configs_sha256 == census["sources"]["configs_sha256"]
    assert configs_sha256 == identity["configs_sha256"]
    assert vehicles_sha256 == census["sources"]["vehicles_sha256"]
    assert vehicles_sha256 == identity["vehicles_sha256"]
    assert corpus_protocol_sha256 == identity["corpus_protocol_sha256"]

    corpus_protocol = CorpusProtocol.model_validate(_json("examples/corpus/corpus_protocol.json"))
    assert corpus_protocol.spec_hash() == manifest["protocol_hash"]
    assert corpus_protocol.spec_hash() == identity["corpus_protocol_hash"]
    vehicles = tuple(VehicleSpec(**item) for item in _json("examples/corpus/vehicles.json"))
    actual_vehicles_hash = content_hash(tuple(vehicle.model_dump(mode="json") for vehicle in vehicles))
    assert len(vehicles) == 2
    assert actual_vehicles_hash == corpus_protocol.vehicles_hash

    config_items = _json("configs/corpus_13.json")
    configs = tuple(
        PipelineConfig(**{key: value for key, value in item.items() if key != "reason"})
        for item in config_items
    )
    actual_pool_hash = pool_hash(config.config_id() for config in configs)
    assert actual_pool_hash == selection_protocol["pool_hash"]
    assert actual_pool_hash == d3["payload"]["pool_hash"]
    assert actual_pool_hash == identity["pool_hash"]
    assert actual_pool_hash == d6["payload"]["pool_hash"]
    assert d4["payload"]["protocol_hash"] == selection_protocol["spec_hash"]

    protocol_hashes = identity["protocol_sha256_by_source"]
    assert {
        source: _protocol_source_sha256(source)
        for source in protocol_hashes
    } == protocol_hashes
    actual_protocol_bundle_hash = content_hash({"sha256_by_source": protocol_hashes})
    assert actual_protocol_bundle_hash == identity["protocol_bundle_hash"]
    assert actual_protocol_bundle_hash == d5["payload"]["protocol_bundle_hash"]
    assert actual_protocol_bundle_hash == d6["payload"]["protocol_bundle_hash"]

    code_hashes = identity["analysis_code_sha256_by_path"]
    assert frozenset(code_hashes) == EXPECTED_H2_CODE_FILES
    assert {path: _sha256(path) for path in code_hashes} == code_hashes
    actual_code_hash = content_hash({"sha256_by_path": code_hashes})
    assert actual_code_hash == identity["analysis_code_hash"]
    assert actual_code_hash == d6["payload"]["analysis_code_hash"]

    primary = result["analysis"]["wilcoxon"]
    full_five = result["analysis"]["full_5_bin_sensitivity"]
    assert full_five["status"] == "secondary_sensitivity__not_in_holm_family"
    assert primary["zero_method"] == "pratt"
    assert full_five["wilcoxon"]["zero_method"] == "pratt"
    for test in (primary, full_five["wilcoxon"]):
        assert test["alternative"] == "greater"
        assert test["null_value"] == 0.0
        assert test["method"] == "approx"
        assert test["n_zero_differences"] > 0

