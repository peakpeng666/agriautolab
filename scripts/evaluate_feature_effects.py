#!/usr/bin/env python3
"""Evaluate within-field row-angle offset treatment effects and seal the result
into the JSONL experiment log at index 5 (after the pareto_optimality_result
entry at index 4).

All frozen byte identities are verified before any analysis; the protocol
bundle hash is inherited from the experiment log when present, or must be
supplied with --protocol-bundle-hash on a first run.
"""

from __future__ import annotations

import argparse

import importlib.metadata
import json
from pathlib import Path

from agriautolab.evaluation.records import seal_confirmatory_result, sha256_file
from agriautolab.evaluation.feature_effects import evaluate_feature_effects, field_effects, load_offset_front_instances
from agriautolab.contracts.vehicle import VehicleSpec
from agriautolab.pipeline.corpus.protocol import CorpusProtocol
from agriautolab.pipeline.hashing import content_hash
from agriautolab.pipeline import jsonl_log
from agriautolab.pipeline.pareto.front import pool_hash
from agriautolab.pipeline.config import PipelineConfig

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_LEDGER_INDEX = 5
ARTIFACT = "feature_effects_result"
PREDECESSOR_ARTIFACT = "pareto_optimality_result"
ANALYSIS_CODE_FILES = (
    "scripts/evaluate_feature_effects.py",
    "src/agriautolab/evaluation/feature_effects.py",
    "src/agriautolab/evaluation/pareto_optimality.py",
    "src/agriautolab/evaluation/stats.py",
    "src/agriautolab/pipeline/corpus/derived_status.py",
    "src/agriautolab/pipeline/pareto/front.py",
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


# Known identity of the study-001 preregistration protocol bundle: content_hash over
# the sha256_by_source of the preregistration sources archived at the study-001-frozen
# tag, where the sealed result payloads and ledger entries record the same value. A
# --protocol-bundle-hash override must match it before any result seals or replays.
KNOWN_PROTOCOL_BUNDLE_HASH = "5d7b4d66ae02702faec68d3d32a83cd687fb426c72a22ea771e7d07306482bc4"


def _protocol_bundle_hash_from_log(entries: tuple[dict, ...], override: str | None) -> str:
    if override:
        if override != KNOWN_PROTOCOL_BUNDLE_HASH:
            raise ValueError(
                "--protocol-bundle-hash does not match the preregistration bundle identity "
                f"archived at the study-001-frozen tag ({override[:16]}...); refusing to seal "
                "an unverified protocol identity"
            )
        return override
    for entry in entries:
        value = entry.get("payload", {}).get("protocol_bundle_hash")
        if value:
            return str(value)
    raise ValueError(
        "protocol bundle hash is not in the experiment log and --protocol-bundle-hash was not supplied; "
        "the preregistration sources live at the study-001-frozen tag"
    )


def _code_identity() -> tuple[dict[str, str], str]:
    files = {relative: sha256_file(ROOT / relative) for relative in ANALYSIS_CODE_FILES}
    return files, content_hash({"sha256_by_path": files})


def _immutable_write(path: Path, document: dict) -> None:
    encoded = (json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    if path.exists():
        if path.read_bytes() != encoded:
            raise ValueError(f"refusing to overwrite an existing, different result: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encoded)


def _validate_predecessor(entries: tuple[dict, ...], pareto_result: Path) -> dict:
    if len(entries) < 5 or entries[4]["payload"].get("artifact") != PREDECESSOR_ARTIFACT:
        raise ValueError("feature-effects evaluation may only run or replay after the pareto_optimality_result entry at log index 4")
    if len(entries) >= 6 and entries[5]["payload"].get("artifact") != ARTIFACT:
        raise ValueError(f"log index 5 is occupied by an artifact other than {ARTIFACT}")
    if sha256_file(pareto_result) != entries[4]["payload"].get("result_file_sha256"):
        raise ValueError("pareto front result file does not match the byte binding at log index 4")
    pareto_document = _load(pareto_result)
    if pareto_document.get("hypothesis") != "pareto_optimality":
        raise ValueError("the predecessor at log index 4 is not the pareto_optimality result")
    return pareto_document


def _validate_field_reconciliation(pareto_document: dict, estimates) -> None:
    pareto_rows = pareto_document.get("analysis", {}).get("fields")
    if not isinstance(pareto_rows, list):
        raise ValueError("pareto result is missing the field-level analysis.fields evidence")
    pareto_by_field: dict[str, dict] = {}
    for row in pareto_rows:
        field_id = str(row.get("field_id"))
        if field_id in pareto_by_field:
            raise ValueError(f"pareto result contains a duplicate field_id: {field_id}")
        pareto_by_field[field_id] = row
    effects_by_field = {item.field_id: item for item in estimates}
    if set(pareto_by_field) != set(effects_by_field):
        raise ValueError("pareto / feature-effects field universes disagree")
    mismatches: dict[str, dict] = {}
    for field_id, effects_row in effects_by_field.items():
        pareto_row = pareto_by_field[field_id]
        expected = (
            pareto_row.get("n_instances"),
            pareto_row.get("n_front_instances"),
            pareto_row.get("median_front_size"),
        )
        actual = (
            effects_row.n_instances,
            effects_row.n_front_instances,
            effects_row.median_front_size,
        )
        if actual != expected:
            mismatches[field_id] = {"pareto": expected, "effects": actual}
    if mismatches:
        sample = dict(list(sorted(mismatches.items()))[:5])
        raise ValueError(f"recomputed fronts drift from the sealed pareto field evidence: {sample}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=Path, required=True)
    parser.add_argument("--configs", type=Path, default=ROOT / "configs" / "standard_configs.json")
    parser.add_argument("--vehicles", type=Path, default=ROOT / "examples" / "corpus" / "vehicles.json")
    parser.add_argument(
        "--corpus-protocol",
        type=Path,
        default=ROOT / "examples" / "corpus" / "corpus_protocol.json",
    )
    parser.add_argument("--manifest", type=Path, default=ROOT / "dataset_splits" / "manifest.json")
    parser.add_argument("--pool-census", type=Path, default=ROOT / "benchmarks/results/pool_census.json")
    parser.add_argument(
        "--selection-protocol",
        type=Path,
        default=ROOT / "benchmarks/results/benchmark_cv_protocol.json",
    )
    parser.add_argument("--pareto-result", type=Path, default=ROOT / "benchmarks/results/pareto_optimality_result.json")
    parser.add_argument("--output", type=Path, default=ROOT / "benchmarks/results/feature_effects_result.json")
    parser.add_argument("--ledger", type=Path, default=ROOT / "benchmarks/results/benchmark_ledger.jsonl")
    parser.add_argument("--protocol-bundle-hash", type=str, default=None)
    args = parser.parse_args()

    entries = tuple(
        json.loads(line)
        for line in args.ledger.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )
    jsonl_log.verify_entries(entries)
    pareto_document = _validate_predecessor(entries, args.pareto_result)

    protocol_bundle_hash = _protocol_bundle_hash_from_log(entries, args.protocol_bundle_hash)
    code_files, analysis_code_hash = _code_identity()
    runs_sha256 = sha256_file(args.runs)
    configs_sha256 = sha256_file(args.configs)
    vehicles_sha256 = sha256_file(args.vehicles)
    corpus_protocol_sha256 = sha256_file(args.corpus_protocol)
    manifest_sha256 = sha256_file(args.manifest)

    census = _load(args.pool_census)
    manifest = _load(args.manifest)
    selection_protocol = _load(args.selection_protocol)
    pool_census_sha256 = sha256_file(args.pool_census)
    selection_protocol_sha256 = sha256_file(args.selection_protocol)
    if entries[1]["payload"].get("artifact") != "pool_census":
        raise ValueError("log index 1 must be the pool_census artifact")
    if pool_census_sha256 != entries[1]["payload"].get("file_sha256"):
        raise ValueError("pool census file does not match the byte binding at log index 1")
    if entries[2]["payload"].get("artifact") != "benchmark_cv_protocol":
        raise ValueError("log index 2 must be the benchmark_cv_protocol artifact")
    if selection_protocol_sha256 != entries[2]["payload"].get("file_sha256"):
        raise ValueError("selection protocol file does not match the byte binding at log index 2")
    if runs_sha256 != census["sources"]["runs_parquet_sha256"]:
        raise ValueError("runs.parquet does not match the data bytes bound by the pool census")
    if configs_sha256 != census["sources"]["configs_sha256"]:
        raise ValueError("standard configs do not match the config bytes bound by the pool census")
    if vehicles_sha256 != census["sources"]["vehicles_sha256"]:
        raise ValueError("vehicles.json does not match the vehicle bytes bound by the pool census")
    if manifest_sha256 != entries[0]["payload"]["manifest_file_sha256"]:
        raise ValueError("manifest does not match the bytes bound at log index 0 (genesis)")

    corpus_protocol = CorpusProtocol.model_validate(_load(args.corpus_protocol))
    if corpus_protocol.spec_hash() != manifest["protocol_hash"]:
        raise ValueError("corpus_protocol.json does not match the frozen protocol hash in the manifest")
    if corpus_protocol.row_direction_mode.value != "principal_axis":
        raise ValueError("only the frozen principal_axis scenario may be processed")
    if list(corpus_protocol.row_offsets_rad) != manifest["row_offsets_rad"]:
        raise ValueError("manifest row_offsets_rad does not match the corpus protocol")
    if list(corpus_protocol.row_spacings_m) != manifest["row_spacings_m"]:
        raise ValueError("manifest row_spacings_m does not match the corpus protocol")

    vehicle_items = _load(args.vehicles)
    vehicles = tuple(VehicleSpec(**item) for item in vehicle_items)
    actual_vehicles_hash = content_hash(tuple(vehicle.model_dump(mode="json") for vehicle in vehicles))
    if actual_vehicles_hash != corpus_protocol.vehicles_hash or len(vehicles) != 2:
        raise ValueError("the vehicle design must match the 2 vehicles frozen in the corpus protocol")

    config_items = _load(args.configs)
    configs = tuple(
        PipelineConfig(**{key: value for key, value in item.items() if key != "reason"})
        for item in config_items
    )
    config_ids = tuple(config.config_id() for config in configs)
    actual_pool_hash = pool_hash(config_ids)
    if actual_pool_hash != selection_protocol["pool_hash"] or actual_pool_hash != entries[2]["payload"]["pool_hash"]:
        raise ValueError("nominal pool does not match the frozen pool in the selection protocol / log")

    pareto_identity = pareto_document.get("identity", {})
    expected_pareto_identity = {
        "runs_parquet_sha256": runs_sha256,
        "configs_sha256": configs_sha256,
        "manifest_sha256": manifest_sha256,
        "pool_hash": actual_pool_hash,
        "protocol_bundle_hash": protocol_bundle_hash,
    }
    mismatched_pareto = {
        key: (pareto_identity.get(key), expected)
        for key, expected in expected_pareto_identity.items()
        if pareto_identity.get(key) != expected
    }
    if mismatched_pareto:
        raise ValueError(f"pareto predecessor identity disagrees with the feature-effects inputs: {mismatched_pareto}")

    expected_fields = tuple(sorted(str(field_id) for field_id in manifest["licenses"]))
    instances = load_offset_front_instances(args.runs, config_ids)
    estimates = field_effects(
        instances,
        expected_offsets_rad=corpus_protocol.row_offsets_rad,
        expected_spacings_m=corpus_protocol.row_spacings_m,
        expected_vehicle_indices=range(len(vehicles)),
        expected_field_ids=expected_fields,
    )
    if len(expected_fields) != 235 or len(instances) != 4700 or census["n_instances"] != 4700:
        raise ValueError("the dataset split must contain 235 fields / 4700 instances")
    if any(item.n_instances != 20 or len(item.offset_bins) != 5 for item in estimates):
        raise ValueError("every field must have exactly 20 instances / 5 offset bins")
    _validate_field_reconciliation(pareto_document, estimates)

    analysis = evaluate_feature_effects(estimates)
    document = {
        "study_id": "AGRIPLAN-PARETO-001",
        "stage": "feature-effects-confirmatory",
        "hypothesis": "feature_effects",
        "scope": {
            "statistical_unit": "field_id",
            "field_universe": "all 235 license-cleared dataset-split fields from manifest.licenses",
            "model_consumption": False,
            "holdout_partition_membership_consumed": False,
            "note": (
                "Feature-effects analysis is a full-corpus controlled within-field scenario-factor test; "
                "no recommender/model artifact, CV assignment, holdout partition, or holdout split membership is consumed."
            ),
        },
        "identity": {
            "runs_parquet_sha256": runs_sha256,
            "configs_sha256": configs_sha256,
            "vehicles_sha256": vehicles_sha256,
            "corpus_protocol_sha256": corpus_protocol_sha256,
            "corpus_protocol_hash": corpus_protocol.spec_hash(),
            "manifest_sha256": manifest_sha256,
            "pool_census_sha256": pool_census_sha256,
            "selection_protocol_sha256": selection_protocol_sha256,
            "pool_hash": actual_pool_hash,
            "pareto_result_sha256": sha256_file(args.pareto_result),
            "pareto_ledger_entry_hash": entries[4]["entry_hash"],
            "analysis_code_sha256_by_path": code_files,
            "analysis_code_hash": analysis_code_hash,
            "protocol_bundle_hash": protocol_bundle_hash,
        },
        "environment": {
            "numpy": importlib.metadata.version("numpy"),
            "pyarrow": importlib.metadata.version("pyarrow"),
            "scipy": importlib.metadata.version("scipy"),
        },
        "analysis": analysis,
    }
    _immutable_write(args.output, document)
    entry = seal_confirmatory_result(
        hypothesis="feature_effects",
        expected_index=EXPECTED_LEDGER_INDEX,
        required_previous_artifact=PREDECESSOR_ARTIFACT,
        result_path=args.output,
        ledger_path=args.ledger,
    )
    print(
        f"feature_effects: all_fields={analysis['n_all_fields']} "
        f"analyzable={analysis['n_analyzable_fields']} "
        f"n3/n4/n5={analysis['n_3_bins']}/{analysis['n_4_bins']}/{analysis['n_5_bins']} "
        f"median_rho={analysis['primary_rho_distribution']['median']:.12g} "
        f"p={analysis['wilcoxon']['pvalue']:.12g} ledger_index={entry['index']}"
    )


if __name__ == "__main__":
    main()
