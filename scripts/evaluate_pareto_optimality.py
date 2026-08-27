#!/usr/bin/env python3
"""Evaluate the per-field Pareto front median and seal the result into the JSONL
experiment log at index 4 (after the selection_cv_result entry at index 3).

The result document carries the full byte identity (runs parquet, configs,
manifest, pool hash, analysis code) so replays are byte-deterministic. The
protocol bundle hash is inherited from the experiment log when present, or must
be supplied with --protocol-bundle-hash on a first run; the override is validated
against the known bundle identity recorded at the study-001-frozen tag, where the
preregistration sources it was originally computed from are archived.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
from pathlib import Path

from agriautolab.evaluation.records import seal_confirmatory_result, sha256_file
from agriautolab.evaluation.pareto_optimality import evaluate_pareto_optimality, field_estimates, load_front_instances
from agriautolab.pipeline.hashing import content_hash
from agriautolab.pipeline import jsonl_log
from agriautolab.pipeline.pareto.front import pool_hash
from agriautolab.pipeline.config import PipelineConfig

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_LEDGER_INDEX = 4
ARTIFACT = "pareto_optimality_result"
ANALYSIS_CODE_FILES = (
    "scripts/evaluate_pareto_optimality.py",
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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=Path, required=True)
    parser.add_argument("--configs", type=Path, default=ROOT / "configs" / "standard_configs.json")
    parser.add_argument("--manifest", type=Path, default=ROOT / "dataset_splits" / "manifest.json")
    parser.add_argument("--pool-census", type=Path, default=ROOT / "benchmarks/results/pool_census.json")
    parser.add_argument("--protocol", type=Path, default=ROOT / "benchmarks/results/benchmark_cv_protocol.json")
    parser.add_argument("--output", type=Path, default=ROOT / "benchmarks/results/pareto_optimality_result.json")
    parser.add_argument("--ledger", type=Path, default=ROOT / "benchmarks/results/benchmark_ledger.jsonl")
    parser.add_argument("--protocol-bundle-hash", type=str, default=None)
    args = parser.parse_args()

    entries = tuple(json.loads(line) for line in args.ledger.read_text(encoding="utf-8").splitlines() if line.strip())
    jsonl_log.verify_entries(entries)
    if len(entries) < 4 or entries[3]["payload"].get("artifact") != "selection_cv_result":
        raise ValueError("pareto front evaluation may only run or replay after the selection_cv_result entry at log index 3")
    if len(entries) >= 5 and entries[4]["payload"].get("artifact") != ARTIFACT:
        raise ValueError(f"log index 4 is occupied by an artifact other than {ARTIFACT}")

    protocol_bundle_hash = _protocol_bundle_hash_from_log(entries, args.protocol_bundle_hash)
    code_files, analysis_code_hash = _code_identity()
    runs_sha256 = sha256_file(args.runs)
    configs_sha256 = sha256_file(args.configs)
    manifest_sha256 = sha256_file(args.manifest)
    census = _load(args.pool_census)
    manifest = _load(args.manifest)
    selection_protocol = _load(args.protocol)
    if runs_sha256 != census["sources"]["runs_parquet_sha256"]:
        raise ValueError("runs.parquet does not match the data bytes bound by the pool census")
    if configs_sha256 != census["sources"]["configs_sha256"]:
        raise ValueError("standard configs do not match the config bytes bound by the pool census")
    if manifest_sha256 != entries[0]["payload"]["manifest_file_sha256"]:
        raise ValueError("manifest does not match the bytes bound at log index 0 (genesis)")

    config_items = json.loads(args.configs.read_text(encoding="utf-8"))
    configs = tuple(PipelineConfig(**{key: value for key, value in item.items() if key != "reason"}) for item in config_items)
    config_ids = tuple(config.config_id() for config in configs)
    actual_pool_hash = pool_hash(config_ids)
    if actual_pool_hash != selection_protocol["pool_hash"] or actual_pool_hash != entries[2]["payload"]["pool_hash"]:
        raise ValueError("nominal pool does not match the frozen pool in the selection protocol / log")

    expected_fields = tuple(sorted(str(field_id) for field_id in manifest["licenses"]))
    instances = load_front_instances(args.runs, config_ids)
    estimates = field_estimates(instances, expected_field_ids=expected_fields)
    if len(expected_fields) != 235 or len(instances) != 4700 or census["n_instances"] != 4700:
        raise ValueError("the dataset split must contain 235 fields / 4700 instances")
    if any(item.n_instances != 20 for item in estimates):
        raise ValueError("every field must have exactly 20 instances")

    analysis = evaluate_pareto_optimality(estimates)
    document = {
        "study_id": "AGRIPLAN-PARETO-001",
        "stage": "pareto-optimality-confirmatory",
        "hypothesis": "pareto_optimality",
        "scope": {
            "statistical_unit": "field_id",
            "field_universe": "all 235 license-cleared dataset-split fields from manifest.licenses",
            "model_consumption": False,
            "holdout_partition_used_for_modeling": False,
            "note": (
                "Pareto front-size analysis is a full-corpus test; no recommender/model artifact "
                "or holdout split membership is consumed."
            ),
        },
        "identity": {
            "runs_parquet_sha256": runs_sha256,
            "configs_sha256": configs_sha256,
            "manifest_sha256": manifest_sha256,
            "pool_hash": actual_pool_hash,
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
        hypothesis="pareto_optimality",
        expected_index=EXPECTED_LEDGER_INDEX,
        required_previous_artifact="selection_cv_result",
        result_path=args.output,
        ledger_path=args.ledger,
    )
    print(
        f"pareto_optimality: all_fields={analysis['n_all_fields']} "
        f"analyzable={analysis['n_analyzable_fields']} "
        f"zero_ok_fields={analysis['n_zero_ok_fields']} "
        f"median={analysis['primary_distribution']['median']} "
        f"p={analysis['wilcoxon']['pvalue']:.12g} ledger_index={entry['index']}"
    )


if __name__ == "__main__":
    main()
