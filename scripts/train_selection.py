#!/usr/bin/env python3
"""D3-D4：只消费冻结训练田，跑 10 折 CV 并拟合最终偏好条件推荐器。"""

from __future__ import annotations

import argparse
from dataclasses import asdict
import importlib.metadata
import json
from pathlib import Path

from agriautolab.contracts.vehicle import VehicleSpec
from agriautolab.pareto.front import pool_hash
from agriautolab.pipeline.config import PipelineConfig
from agriautolab.selection.evidence import seal_selection_cv_result
from agriautolab.selection.evaluation import load_selection_instances
from agriautolab.selection.experiment import run_frozen_grouped_cv
from agriautolab.selection.protocol import selection_protocol_hash
from agriautolab.selection.recommender import PreferenceConditionedRecommender


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=Path, required=True)
    parser.add_argument("--configs", type=Path, required=True)
    parser.add_argument("--vehicles", type=Path, required=True)
    parser.add_argument("--cv", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    args = parser.parse_args()

    cv = json.loads(args.cv.read_text(encoding="utf-8"))
    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    fold_of = {str(item["field_id"]): int(item["fold"]) for item in cv["assignments"]}
    training_fields = tuple(sorted(fold_of))
    if len(training_fields) != int(cv["n_training_fields"]):
        raise ValueError("cv_assignment 的训练田数量与 assignments 不一致")

    config_items = json.loads(args.configs.read_text(encoding="utf-8"))
    configs = tuple(PipelineConfig(**{key: value for key, value in item.items() if key != "reason"}) for item in config_items)
    vehicles = tuple(VehicleSpec.model_validate(item) for item in json.loads(args.vehicles.read_text(encoding="utf-8")))
    actual_pool_hash = pool_hash(config.config_id() for config in configs)
    if actual_pool_hash != protocol["pool_hash"]:
        raise ValueError("config pool 与已封 selection protocol 不一致")
    if cv["spec_hash"] != protocol["cv_spec_hash"]:
        raise ValueError("CV identity 与已封 selection protocol 不一致")
    expected_protocol_hash = selection_protocol_hash(cv_spec_hash=cv["spec_hash"], pool_hash=actual_pool_hash)
    if protocol["spec_hash"] != expected_protocol_hash:
        raise ValueError("selection protocol hash 不一致")

    # 关键纪律：loader 接到的只有 D1 training fields；holdout field_id 不进入扫描条件。
    instances = load_selection_instances(args.runs, training_fields, configs, vehicles)
    folds = run_frozen_grouped_cv(
        instances,
        fold_of,
        cv_spec_hash=cv["spec_hash"],
        pool_hash=actual_pool_hash,
    )
    fold_documents = [
        {
            "summary": fold.summary(),
            "fields": [asdict(field) for field in fold.fields],
        }
        for fold in folds
    ]
    result = {
        "study_id": "AGRIPLAN-PARETO-001",
        "stage": "D3-D4-training-cv",
        "protocol_hash": expected_protocol_hash,
        "cv_spec_hash": cv["spec_hash"],
        "pool_hash": actual_pool_hash,
        "environment": {
            "scikit_learn": importlib.metadata.version("scikit-learn"),
            "numpy": importlib.metadata.version("numpy"),
            "pyarrow": importlib.metadata.version("pyarrow"),
        },
        "n_training_fields": len(training_fields),
        "n_instances": len(instances),
        "n_zero_ok_instances": sum(not instance.analyzable for instance in instances),
        "n_fields_with_no_analyzable_instance": len({
            field_id
            for field_id in training_fields
            if not any(instance.field_id == field_id and instance.analyzable for instance in instances)
        }),
        "zero_ok_note": (
            "regret oracle is undefined when O_x is empty; these instances remain counted and are not silently excluded. "
            "This training-side CV is not the confirmatory H3 test."
        ),
        "folds": fold_documents,
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    result_path = args.output_dir / "selection_cv.json"
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    final_model = PreferenceConditionedRecommender(
        cv_spec_hash=cv["spec_hash"],
        pool_hash=actual_pool_hash,
    ).fit(instances)
    model_path = args.output_dir / "recommender.joblib"
    metadata_path = args.output_dir / "recommender_metadata.json"
    final_model.save(model_path, metadata_path)
    entry = seal_selection_cv_result(
        result_path=result_path,
        model_path=model_path,
        metadata_path=metadata_path,
        ledger_path=args.ledger,
        protocol_hash=expected_protocol_hash,
    )
    print(
        f"selection CV: fields={len(training_fields)} instances={len(instances)} "
        f"zero_ok={result['n_zero_ok_instances']} ledger_index={entry['index']}"
    )


if __name__ == "__main__":
    main()
