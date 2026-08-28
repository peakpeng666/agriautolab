"""Hard gate executed before the recommender holdout evaluation runs.

All frozen identity checks must precede joblib deserialization and holdout-runs
reads. This module performs byte-identity and positional-prefix verification
against the JSONL experiment log only; it runs no statistics.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from agriautolab.evaluation.records import sha256_file
from agriautolab.pipeline import jsonl_log


@dataclass(frozen=True)
class RecommenderPreflight:
    entries: tuple[dict, ...]
    cv: dict
    holdout: dict
    metadata: dict
    pool_hash: str
    selection_protocol_hash: str


def _load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected a JSON object: {path}")
    return value


def _read_verified_ledger(path: Path) -> tuple[dict, ...]:
    entries = jsonl_log.read_entries(path)
    jsonl_log.verify_entries(entries)
    return entries


def _require_artifact(entries: tuple[dict, ...], index: int, artifact: str) -> dict:
    if len(entries) <= index:
        raise ValueError(f"result ledger is missing index={index}")
    entry = entries[index]
    if entry.get("index") != index or entry.get("payload", {}).get("artifact") != artifact:
        raise ValueError(f"result ledger index={index} must be {artifact}")
    return entry


def _require_genesis(entries: tuple[dict, ...]) -> dict:
    if not entries:
        raise ValueError("result ledger is empty")
    entry = entries[0]
    if entry.get("index") != 0 or entry.get("payload", {}).get("event") != "cv_assignment_sealed":
        raise ValueError("result ledger index=0 must be cv_assignment_sealed")
    return entry


def _require_prefix_artifacts(entries: tuple[dict, ...]) -> tuple[dict, dict, dict, dict, dict]:
    genesis = _require_genesis(entries)
    pool_census = _require_artifact(entries, 1, "pool_census")
    selection_protocol = _require_artifact(entries, 2, "benchmark_cv_protocol")
    selection_cv = _require_artifact(entries, 3, "selection_cv_result")
    _require_artifact(entries, 4, "pareto_optimality_result")
    feature_effects = _require_artifact(entries, 5, "feature_effects_result")
    return genesis, pool_census, selection_protocol, selection_cv, feature_effects


def _reject_existing_recommender(entries: tuple[dict, ...]) -> None:
    if any(
        entry.get("payload", {}).get("artifact") == "recommender_eval_result"
        for entry in entries
    ):
        raise ValueError(
            "recommender evaluation is already sealed; holdout may not be re-executed. "
            "Only offline verification of the existing evidence is allowed."
        )


def ensure_recommender_holdout_unsealed(ledger_path: Path) -> None:
    """Read-only first gate: once the recommender result is sealed, no other input is touched."""
    entries = _read_verified_ledger(ledger_path)
    _require_prefix_artifacts(entries)
    _reject_existing_recommender(entries)


def verify_recommender_preflight(
    *,
    ledger_path: Path,
    runs_path: Path,
    configs_path: Path,
    vehicles_path: Path,
    cv_path: Path,
    holdout_path: Path,
    pool_census_path: Path,
    selection_protocol_path: Path,
    feature_effects_result_path: Path,
    model_path: Path,
    metadata_path: Path,
    protocol_bundle_hash: str,
    reject_if_recommender_sealed: bool,
) -> RecommenderPreflight:
    """Verify every frozen input of the recommender evaluation; return parsed safe metadata.

    With `reject_if_recommender_sealed=True`, refuse before reading any other input
    once the log already contains the recommender result. The CLI holdout mode also
    calls `ensure_recommender_holdout_unsealed` so protocol file hashes are never
    re-consumed after sealing.
    """
    entries = _read_verified_ledger(ledger_path)
    genesis, pool_census, selection_protocol, selection_cv, feature_effects = _require_prefix_artifacts(entries)
    if reject_if_recommender_sealed:
        _reject_existing_recommender(entries)

    if sha256_file(pool_census_path) != pool_census["payload"].get("file_sha256"):
        raise ValueError("pool census file does not match the byte binding at log index 1")
    if sha256_file(selection_protocol_path) != selection_protocol["payload"].get("file_sha256"):
        raise ValueError("selection protocol file does not match the byte binding at log index 2")
    if sha256_file(feature_effects_result_path) != feature_effects["payload"].get("result_file_sha256"):
        raise ValueError("feature-effects result file does not match the byte binding at log index 5")
    if protocol_bundle_hash != feature_effects["payload"].get("protocol_bundle_hash"):
        raise ValueError("protocol bundle hash does not match the sealed feature-effects identity")

    census = _load_json(pool_census_path)
    selection_protocol_doc = _load_json(selection_protocol_path)
    feature_effects_result = _load_json(feature_effects_result_path)

    sources = census.get("sources", {})
    expected_inputs = {
        "runs.parquet": (sha256_file(runs_path), sources.get("runs_parquet_sha256")),
        "standard_configs.json": (sha256_file(configs_path), sources.get("configs_sha256")),
        "vehicles.json": (sha256_file(vehicles_path), sources.get("vehicles_sha256")),
        "cv_assignment.json": (sha256_file(cv_path), genesis["payload"].get("cv_assignment_file_sha256")),
        "holdout_partition.json": (sha256_file(holdout_path), genesis["payload"].get("holdout_file_sha256")),
    }
    mismatched = {
        name: {"actual": actual, "expected": expected}
        for name, (actual, expected) in expected_inputs.items()
        if actual != expected
    }
    if mismatched:
        raise ValueError(f"frozen input byte drift: {mismatched}")

    # Model binary and metadata must be bound byte-for-byte before joblib.load.
    model_sha256 = sha256_file(model_path)
    metadata_sha256 = sha256_file(metadata_path)
    if model_sha256 != selection_cv["payload"].get("model_file_sha256"):
        raise ValueError("model bytes do not match the binding at log index 3")
    if metadata_sha256 != selection_cv["payload"].get("metadata_file_sha256"):
        raise ValueError("model metadata does not match the binding at log index 3")

    cv = _load_json(cv_path)
    holdout = _load_json(holdout_path)
    metadata = _load_json(metadata_path)

    if cv.get("spec_hash") != genesis["payload"].get("spec_hash"):
        raise ValueError("cv spec_hash does not match the genesis record")
    if holdout.get("seal_hash") != genesis["payload"].get("holdout_seal_hash"):
        raise ValueError("holdout seal_hash does not match the genesis record")

    if selection_protocol_doc.get("cv_spec_hash") != cv.get("spec_hash"):
        raise ValueError("selection protocol CV identity does not match the genesis record")
    if selection_protocol_doc.get("spec_hash") != selection_cv["payload"].get("protocol_hash"):
        raise ValueError("model protocol does not match the sealed selection protocol")
    if selection_protocol_doc.get("pool_hash") != selection_protocol["payload"].get("pool_hash"):
        raise ValueError("selection protocol pool_hash does not match the log")

    expected_metadata = {
        "protocol_hash": selection_protocol_doc.get("spec_hash"),
        "cv_spec_hash": cv.get("spec_hash"),
        "pool_hash": selection_protocol_doc.get("pool_hash"),
    }
    metadata_mismatch = {
        key: {"actual": metadata.get(key), "expected": expected}
        for key, expected in expected_metadata.items()
        if metadata.get(key) != expected
    }
    if metadata_mismatch:
        raise ValueError(f"recommender metadata identity mismatch: {metadata_mismatch}")

    predecessor_identity = feature_effects_result.get("identity", {})
    predecessor_expected = {
        "runs_parquet_sha256": expected_inputs["runs.parquet"][0],
        "configs_sha256": expected_inputs["standard_configs.json"][0],
        "vehicles_sha256": expected_inputs["vehicles.json"][0],
        "pool_hash": selection_protocol_doc.get("pool_hash"),
        "protocol_bundle_hash": protocol_bundle_hash,
    }
    predecessor_mismatch = {
        key: {"actual": predecessor_identity.get(key), "expected": expected}
        for key, expected in predecessor_expected.items()
        if predecessor_identity.get(key) != expected
    }
    if predecessor_mismatch:
        raise ValueError(f"feature-effects predecessor identity mismatch: {predecessor_mismatch}")

    holdout_fields = tuple(sorted(str(field_id) for field_id in holdout.get("field_ids", ())))
    training_fields = tuple(sorted(str(item["field_id"]) for item in cv.get("assignments", ())))
    if len(holdout_fields) != 70 or len(training_fields) != 165:
        raise ValueError("the frozen partition must be 70 holdout / 165 training fields")
    if set(holdout_fields) & set(training_fields):
        raise ValueError("holdout partition overlaps the training folds: sealed identity is corrupt")

    return RecommenderPreflight(
        entries=entries,
        cv=cv,
        holdout=holdout,
        metadata=metadata,
        pool_hash=str(selection_protocol_doc["pool_hash"]),
        selection_protocol_hash=str(selection_protocol_doc["spec_hash"]),
    )
