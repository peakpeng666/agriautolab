"""Recommender preflight: synthetic evidence chain proves identity gates precede holdout consumption."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agriautolab.evaluation.records import sha256_file
from agriautolab.evaluation.recommender_preflight import verify_recommender_preflight
from agriautolab.pipeline import jsonl_log


PROTOCOL_BUNDLE_HASH = "protocol-bundle"
POOL_HASH = "pool"
CV_SPEC_HASH = "cv-spec"
SELECTION_PROTOCOL_HASH = "selection-protocol"


def _write_json(path: Path, value: dict) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _append(entries: list[dict], payload: dict) -> None:
    entries.append(jsonl_log.entry_after(tuple(entries), payload))


def _fixture(tmp_path: Path) -> dict[str, Path]:
    runs = tmp_path / "runs.parquet"
    configs = tmp_path / "standard_configs.json"
    vehicles = tmp_path / "vehicles.json"
    cv = tmp_path / "cv_assignment.json"
    holdout = tmp_path / "holdout_partition.json"
    census = tmp_path / "pool_census.json"
    selection_protocol = tmp_path / "benchmark_cv_protocol.json"
    feature_effects_result = tmp_path / "feature_effects_result.json"
    model = tmp_path / "recommender.joblib"
    metadata = tmp_path / "recommender_metadata.json"
    ledger = tmp_path / "ledger.jsonl"

    runs.write_bytes(b"frozen-runs")
    configs.write_text("[]\n", encoding="utf-8")
    vehicles.write_text("[]\n", encoding="utf-8")
    model.write_bytes(b"frozen-model")

    _write_json(
        cv,
        {
            "spec_hash": CV_SPEC_HASH,
            "assignments": [
                {"field_id": f"train_{index}", "fold": index % 10}
                for index in range(165)
            ],
        },
    )
    _write_json(
        holdout,
        {
            "seal_hash": "holdout-seal",
            "field_ids": [f"holdout_{index}" for index in range(70)],
        },
    )
    _write_json(
        census,
        {
            "sources": {
                "runs_parquet_sha256": sha256_file(runs),
                "configs_sha256": sha256_file(configs),
                "vehicles_sha256": sha256_file(vehicles),
            }
        },
    )
    _write_json(
        selection_protocol,
        {
            "spec_hash": SELECTION_PROTOCOL_HASH,
            "cv_spec_hash": CV_SPEC_HASH,
            "pool_hash": POOL_HASH,
        },
    )
    _write_json(
        metadata,
        {
            "protocol_hash": SELECTION_PROTOCOL_HASH,
            "cv_spec_hash": CV_SPEC_HASH,
            "pool_hash": POOL_HASH,
        },
    )
    _write_json(
        feature_effects_result,
        {
            "hypothesis": "feature_effects",
            "identity": {
                "runs_parquet_sha256": sha256_file(runs),
                "configs_sha256": sha256_file(configs),
                "vehicles_sha256": sha256_file(vehicles),
                "pool_hash": POOL_HASH,
                "protocol_bundle_hash": PROTOCOL_BUNDLE_HASH,
            },
        },
    )

    entries: list[dict] = []
    _append(
        entries,
        {
            "event": "cv_assignment_sealed",
            "cv_assignment_file_sha256": sha256_file(cv),
            "holdout_file_sha256": sha256_file(holdout),
            "holdout_seal_hash": "holdout-seal",
            "spec_hash": CV_SPEC_HASH,
        },
    )
    _append(
        entries,
        {
            "artifact": "pool_census",
            "file_sha256": sha256_file(census),
        },
    )
    _append(
        entries,
        {
            "artifact": "benchmark_cv_protocol",
            "file_sha256": sha256_file(selection_protocol),
            "pool_hash": POOL_HASH,
            "cv_spec_hash": CV_SPEC_HASH,
        },
    )
    _append(
        entries,
        {
            "artifact": "selection_cv_result",
            "model_file_sha256": sha256_file(model),
            "metadata_file_sha256": sha256_file(metadata),
            "protocol_hash": SELECTION_PROTOCOL_HASH,
        },
    )
    _append(entries, {"artifact": "pareto_optimality_result"})
    _append(
        entries,
        {
            "artifact": "feature_effects_result",
            "result_file_sha256": sha256_file(feature_effects_result),
            "protocol_bundle_hash": PROTOCOL_BUNDLE_HASH,
            "runs_parquet_sha256": sha256_file(runs),
            "pool_hash": POOL_HASH,
        },
    )
    ledger.write_text(
        "".join(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n" for entry in entries),
        encoding="utf-8",
    )

    return {
        "runs_path": runs,
        "configs_path": configs,
        "vehicles_path": vehicles,
        "cv_path": cv,
        "holdout_path": holdout,
        "pool_census_path": census,
        "selection_protocol_path": selection_protocol,
        "feature_effects_result_path": feature_effects_result,
        "model_path": model,
        "metadata_path": metadata,
        "ledger_path": ledger,
    }


def _verify(paths: dict[str, Path], *, reject_if_recommender_sealed: bool = True):
    return verify_recommender_preflight(
        **paths,
        protocol_bundle_hash=PROTOCOL_BUNDLE_HASH,
        reject_if_recommender_sealed=reject_if_recommender_sealed,
    )


def test_preflight_accepts_fully_bound_synthetic_chain(tmp_path: Path) -> None:
    paths = _fixture(tmp_path)
    result = _verify(paths)
    assert result.pool_hash == POOL_HASH
    assert result.selection_protocol_hash == SELECTION_PROTOCOL_HASH
    assert len(result.holdout["field_ids"]) == 70
    assert len(result.cv["assignments"]) == 165


def test_existing_recommender_rejected_before_any_other_input_is_opened(tmp_path: Path) -> None:
    paths = _fixture(tmp_path)
    ledger = paths["ledger_path"]
    entries = [
        json.loads(line)
        for line in ledger.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    _append(entries, {"artifact": "recommender_eval_result"})
    ledger.write_text(
        "".join(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n" for entry in entries),
        encoding="utf-8",
    )

    # 如果实现错误地继续做输入检查，这两个缺失文件会先抛 FileNotFoundError。
    paths["runs_path"].unlink()
    paths["model_path"].unlink()
    with pytest.raises(ValueError, match="already sealed|sealed|re-executed"):
        _verify(paths)


def test_model_bytes_must_match_sealed_model_before_deserialization(tmp_path: Path) -> None:
    paths = _fixture(tmp_path)
    paths["model_path"].write_bytes(b"different-model")
    with pytest.raises(ValueError, match="model bytes|index 3"):
        _verify(paths)


def test_holdout_file_must_match_genesis(tmp_path: Path) -> None:
    paths = _fixture(tmp_path)
    holdout = json.loads(paths["holdout_path"].read_text(encoding="utf-8"))
    holdout["field_ids"][0] = "tampered"
    _write_json(paths["holdout_path"], holdout)
    with pytest.raises(ValueError, match="bytes.*drift|holdout"):
        _verify(paths)


def test_feature_effects_predecessor_must_share_data_and_protocol_identity(tmp_path: Path) -> None:
    paths = _fixture(tmp_path)
    h2 = json.loads(paths["feature_effects_result_path"].read_text(encoding="utf-8"))
    h2["identity"]["runs_parquet_sha256"] = "wrong"
    _write_json(paths["feature_effects_result_path"], h2)

    # 先把 ledger 对 feature-effects 文件的字节绑定同步到这个合成变体，才能命中更深层的
    # predecessor identity gate，而不是停在 result_file_sha256 外层守门。
    ledger = paths["ledger_path"]
    entries = [
        json.loads(line)
        for line in ledger.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    rebuilt: list[dict] = []
    for index, old in enumerate(entries):
        payload = dict(old["payload"])
        if index == 5:
            payload["result_file_sha256"] = sha256_file(paths["feature_effects_result_path"])
        _append(rebuilt, payload)
    ledger.write_text(
        "".join(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n" for entry in rebuilt),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="feature_effects|predecessor"):
        _verify(paths)
