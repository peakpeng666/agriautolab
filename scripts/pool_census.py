#!/usr/bin/env python3
"""池普查：nominal / static-applicable / observed-OK 三层池，落盘 + 基准结果账本。

用法（数据机）：
  python scripts/pool_census.py \
    --runs ~/agriautolab-data/out_v7/runs.parquet \
    --configs configs/standard_configs.json \
    --vehicles examples/corpus/vehicles.json \
    --cv dataset_splits/cv_assignment.json \
    --output benchmarks/results/pool_census.json \
    --ledger benchmarks/results/benchmark_ledger.jsonl
"""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from collections import defaultdict
from pathlib import Path

from agriautolab.contracts.vehicle import VehicleSpec
from agriautolab.pipeline.config import PipelineConfig
from agriautolab.pipeline import jsonl_log
from agriautolab.selection.pools import census_from_runs, seal_pool_census_ledger


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=Path, required=True)
    parser.add_argument("--configs", type=Path, required=True)
    parser.add_argument("--vehicles", type=Path, required=True)
    parser.add_argument("--cv", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    args = parser.parse_args()

    items = json.loads(args.configs.read_text(encoding="utf-8"))
    configs = tuple(PipelineConfig(**{k: v for k, v in it.items() if k != "reason"}) for it in items)
    vehicles = tuple(VehicleSpec.model_validate(v) for v in json.loads(args.vehicles.read_text(encoding="utf-8")))
    cv = json.loads(args.cv.read_text(encoding="utf-8"))
    fold_of = {e["field_id"]: e["fold"] for e in cv["assignments"]}
    holdout_path = args.cv.parent / "holdout_seal.json"
    holdout = set(json.loads(holdout_path.read_text(encoding="utf-8"))["field_ids"]) if holdout_path.exists() else None

    census = census_from_runs(args.runs, configs, vehicles)
    instances = census.pop("instances")

    by_field: dict[str, list] = defaultdict(list)
    for pools in instances:
        by_field[pools.field_id].append(pools)

    fields_doc = []
    for field in sorted(by_field):
        rows = by_field[field]
        is_holdout = holdout is not None and field in holdout
        ok_sizes = [len(p.observed_ok) for p in rows]
        gap = [len(p.applicable - p.observed_ok) for p in rows]
        fields_doc.append({
            "field_id": field,
            "split": "holdout" if is_holdout else "train",
            "fold": None if is_holdout else fold_of.get(field),
            "n_instances": len(rows),
            "mean_ok": round(statistics.mean(ok_sizes), 4),
            "mean_applicable_minus_ok": round(statistics.mean(gap), 4),
            "zero_ok_instances": sum(1 for size in ok_sizes if size == 0),
        })

    train = [field for field in fields_doc if field["split"] == "train"]
    hold = [field for field in fields_doc if field["split"] == "holdout"]
    doc = {
        "study_id": "AGRIPLAN-PARETO-001",
        "stage": "pool-census",
        "sources": {
            "runs_parquet_sha256": _sha256_file(args.runs),
            "configs_sha256": _sha256_file(args.configs),
            "vehicles_sha256": _sha256_file(args.vehicles),
            "cv_spec_hash": cv["spec_hash"],
        },
        "invariants": {
            "o_subset_a": True,
            "a_subset_n": True,
            "note": "census_from_runs 逐实例强制校验，违例当场抛错而非记录",
        },
        "nominal_size": census["nominal_size"],
        "applicable_by_vehicle": census["applicable_by_vehicle"],
        "n_instances": census["n_instances"],
        "fields": fields_doc,
        "summary": {
            "train_fields": len(train),
            "holdout_fields": len(hold),
            "train_mean_ok_per_instance": round(statistics.mean(field["mean_ok"] for field in train), 4),
            "holdout_mean_ok_per_instance": round(statistics.mean(field["mean_ok"] for field in hold), 4),
            "holdout_note": "holdout 的 O 层聚合仅描述性；建模消费在 recommender 评估开留出集前不得",
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    tmp = args.output.with_name(args.output.name + ".tmp")
    tmp.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    jsonl_log.replace_unless_sealed(tmp, args.output, args.ledger, "pool_census", "file_sha256")

    payload = {
        "artifact": "pool_census",
        "file_sha256": _sha256_file(args.output),
        "nominal_size": doc["nominal_size"],
        "applicable_by_vehicle": doc["applicable_by_vehicle"],
        "n_instances": doc["n_instances"],
        "cv_spec_hash": cv["spec_hash"],
    }
    entry = seal_pool_census_ledger(payload, args.ledger)
    print(
        f"census: fields={len(fields_doc)} instances={doc['n_instances']} "
        f"applicable={doc['applicable_by_vehicle']} ledger_index={entry['index']}"
    )


if __name__ == "__main__":
    main()
