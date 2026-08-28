#!/usr/bin/env python3
"""Evaluate the preference-conditioned recommender on the one-shot holdout and
seal the result into the JSONL experiment log at index 6 (after the
feature_effects_result entry at index 5).

--fields train is a training-side sanity pass only (writes nothing, seals
nothing); --fields holdout may run exactly once while the log has no
recommender_eval_result. All protocol, input and model byte identities must
pass before model deserialization and holdout-runs reads.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
from pathlib import Path

from agriautolab.evaluation.records import seal_confirmatory_result, sha256_file
from agriautolab.evaluation.recommender_eval import evaluate_recommender
from agriautolab.evaluation.recommender_preflight import (
    ensure_recommender_holdout_unsealed,
    verify_recommender_preflight,
)
from agriautolab.contracts.vehicle import VehicleSpec
from agriautolab.pipeline.hashing import content_hash
from agriautolab.pipeline.config import PipelineConfig
from agriautolab.selection.evaluation import load_selection_instances

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_LEDGER_INDEX = 6
REQUIRED_PREVIOUS_ARTIFACT = "feature_effects_result"
ANALYSIS_CODE_FILES = (
    "scripts/evaluate_recommender.py",
    "src/agriautolab/evaluation/recommender_eval.py",
    "src/agriautolab/evaluation/recommender_preflight.py",
    "src/agriautolab/selection/evaluation.py",
    "src/agriautolab/selection/experiment.py",
    "src/agriautolab/selection/recommender.py",
    "src/agriautolab/selection/pools.py",
    "src/agriautolab/pipeline/pareto/preference_grid.py",
    "src/agriautolab/pipeline/corpus/derived_status.py",
    "src/agriautolab/pipeline/pareto/front.py",
)


def _protocol_bundle_hash_from_log(entries: tuple[dict, ...], override: str | None) -> str:
    if override:
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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=Path, required=True)
    parser.add_argument("--configs", type=Path, default=ROOT / "configs" / "standard_configs.json")
    parser.add_argument("--vehicles", type=Path, default=ROOT / "examples" / "corpus" / "vehicles.json")
    parser.add_argument("--cv", type=Path, default=ROOT / "dataset_splits" / "cv_assignment.json")
    parser.add_argument("--holdout", type=Path, default=ROOT / "dataset_splits" / "holdout_partition.json")
    parser.add_argument("--pool-census", type=Path, default=ROOT / "benchmarks/results/pool_census.json")
    parser.add_argument(
        "--selection-protocol",
        type=Path,
        default=ROOT / "benchmarks/results/benchmark_cv_protocol.json",
    )
    parser.add_argument(
        "--feature-effects-result",
        type=Path,
        default=ROOT / "benchmarks/results/feature_effects_result.json",
    )
    parser.add_argument("--model-dir", type=Path, default=Path.home() / "agriautolab-data" / "d4")
    parser.add_argument("--output", type=Path, default=ROOT / "benchmarks/results/recommender_eval_result.json")
    parser.add_argument("--ledger", type=Path, default=ROOT / "benchmarks/results/benchmark_ledger.jsonl")
    parser.add_argument("--fields", choices=("train", "holdout"), default="holdout")
    parser.add_argument("--protocol-bundle-hash", type=str, default=None)
    args = parser.parse_args()

    # The holdout-mode first action reads only the log: once the recommender result is
    # sealed, no other recommender input may be touched.
    if args.fields == "holdout":
        ensure_recommender_holdout_unsealed(args.ledger)

    if importlib.metadata.version("scikit-learn") != "1.7.2":
        raise ValueError("recommender evaluation requires scikit-learn==1.7.2 (the sealed model's version)")

    entries = tuple(
        json.loads(line)
        for line in args.ledger.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )
    protocol_bundle_hash = _protocol_bundle_hash_from_log(entries, args.protocol_bundle_hash)
    code_files, analysis_code_hash = _code_identity()
    model_path = args.model_dir / "recommender.joblib"
    metadata_path = args.model_dir / "recommender_metadata.json"
    preflight = verify_recommender_preflight(
        ledger_path=args.ledger,
        runs_path=args.runs,
        configs_path=args.configs,
        vehicles_path=args.vehicles,
        cv_path=args.cv,
        holdout_path=args.holdout,
        pool_census_path=args.pool_census,
        selection_protocol_path=args.selection_protocol,
        feature_effects_result_path=args.feature_effects_result,
        model_path=model_path,
        metadata_path=metadata_path,
        protocol_bundle_hash=protocol_bundle_hash,
        reject_if_recommender_sealed=args.fields == "holdout",
    )

    items = json.loads(args.configs.read_text(encoding="utf-8"))
    configs = tuple(PipelineConfig(**{k: v for k, v in it.items() if k != "reason"}) for it in items)
    vehicles = tuple(
        VehicleSpec.model_validate(v)
        for v in json.loads(args.vehicles.read_text(encoding="utf-8"))
    )

    # Deserialization is only allowed after the model binary passed the exact-SHA gate.
    import joblib

    recommender = joblib.load(model_path)
    loaded_identity = {
        "protocol_hash": getattr(recommender, "protocol_hash", None),
        "cv_spec_hash": getattr(recommender, "cv_spec_hash", None),
        "pool_hash": getattr(recommender, "pool_hash", None),
    }
    expected_loaded_identity = {
        "protocol_hash": preflight.selection_protocol_hash,
        "cv_spec_hash": preflight.cv["spec_hash"],
        "pool_hash": preflight.pool_hash,
    }
    if loaded_identity != expected_loaded_identity:
        raise ValueError(
            f"model object identity disagrees with the verified metadata: "
            f"actual={loaded_identity}, expected={expected_loaded_identity}"
        )

    holdout_fields = sorted(preflight.holdout["field_ids"])
    training_fields = sorted(e["field_id"] for e in preflight.cv["assignments"])
    field_ids = training_fields if args.fields == "train" else holdout_fields

    # Data reads happen only after every identity gate and the model self-check.
    target_instances = load_selection_instances(args.runs, field_ids, configs, vehicles)
    training_instances = (
        target_instances
        if args.fields == "train"
        else load_selection_instances(args.runs, training_fields, configs, vehicles)
    )
    analysis = evaluate_recommender(recommender, training_instances, target_instances)

    if args.fields == "train":
        track = analysis["track_70"]
        print(
            f"[sanity|train] fields={analysis['n_analyzable_fields']} "
            f"rec={track['mean_recommender_loss']:.5f} "
            f"rand_app={track['mean_random_applicable_loss']:.5f} "
            f"mean_D={track['mean_D']:.5f} sbs={analysis['sbs_config_id'][:12]}"
        )
        return

    document = {
        "hypothesis": "recommender_eval",
        "stage": "recommender-eval-confirmatory",
        "study_id": "AGRIPLAN-PARETO-001",
        "analysis": analysis,
        "identity": {
            "analysis_code_sha256_by_path": code_files,
            "analysis_code_hash": analysis_code_hash,
            "protocol_bundle_hash": protocol_bundle_hash,
            "runs_parquet_sha256": sha256_file(args.runs),
            "configs_sha256": sha256_file(args.configs),
            "vehicles_sha256": sha256_file(args.vehicles),
            "model_file_sha256": sha256_file(model_path),
            "metadata_file_sha256": sha256_file(metadata_path),
            "cv_spec_hash": preflight.cv["spec_hash"],
            "holdout_seal_hash": preflight.holdout.get("seal_hash"),
            "pool_hash": recommender.pool_hash,
        },
        "environment": {
            "scikit_learn": importlib.metadata.version("scikit-learn"),
            "numpy": importlib.metadata.version("numpy"),
            "python": __import__("sys").version.split()[0],
        },
        "scope": {
            "field_universe": "70 sealed holdout fields; dual-track 70/68 excluding the 2 debug-probe fields",
            "model_consumption": "final-fit recommender (in-sample on training, one-shot on holdout)",
            "statistical_unit": "field",
        },
    }
    _immutable_write(args.output, document)
    seal_confirmatory_result(
        hypothesis="recommender_eval",
        expected_index=EXPECTED_LEDGER_INDEX,
        required_previous_artifact=REQUIRED_PREVIOUS_ARTIFACT,
        result_path=args.output,
        ledger_path=args.ledger,
    )
    track = analysis["track_70"]
    print(
        f"recommender_eval sealed (index={EXPECTED_LEDGER_INDEX}): fields={track['n_fields']} "
        f"mean_D={track['mean_D']:.5f} p={track['permutation']['pvalue']:.4e} "
        f"failure_triggered={analysis['failure_thresholds']['any_triggered']}"
    )


if __name__ == "__main__":
    main()
