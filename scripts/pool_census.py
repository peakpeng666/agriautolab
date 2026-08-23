#!/usr/bin/env python3
"""D2 普查：nominal / static-applicable / observed-OK 三层池，落盘 + Block D ledger。

用法（数据机）：
  python scripts/pool_census.py \
    --runs ~/agriautolab-data/out_v7/runs.parquet \
    --configs configs/corpus_13.json \
    --vehicles examples/corpus/vehicles.json \
    --cv evidence/v7/cv_assignment.json \
    --output evidence/block_d/pool_census.json \
    --ledger evidence/block_d/ledger.jsonl
"""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from collections import defaultdict
from pathlib import Path

from agriautolab.contracts.vehicle import VehicleSpec
from agriautolab.evidence.ledger import artifact_chain_entry
from agriautolab.pipeline.config import PipelineConfig
from agriautolab.selection.pools import census_from_runs


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
    holdout = set(json.loads((args.cv.parent / "holdout_seal.json").read_text(encoding="utf-8"))["field_ids"]) \
        if (args.cv.parent / "holdout_seal.json").exists() else None

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
        gap = [len(p.applicable - p.observed_ok) for p in rows]  # 静态适用但被拒 = 选择难度
        fields_doc.append({
            "field_id": field,
            "split": "holdout" if is_holdout else "train",
            "fold": None if is_holdout else fold_of.get(field),
            "n_instances": len(rows),
            "mean_ok": round(statistics.mean(ok_sizes), 4),
            "mean_applicable_minus_ok": round(statistics.mean(gap), 4),
            "zero_ok_instances": sum(1 for s in ok_sizes if s == 0),
        })

    train = [f for f in fields_doc if f["split"] == "train"]
    hold = [f for f in fields_doc if f["split"] == "holdout"]
    doc = {
        "study_id": "AGRIPLAN-PARETO-001",
        "stage": "D2-pool-census",
        "sources": {
            "runs_parquet_sha256": _sha256_file(args.runs),
            "configs_sha256": _sha256_file(args.configs),
            "vehicles_sha256": _sha256_file(args.vehicles),
            "cv_spec_hash": cv["spec_hash"],
        },
        "invariants": {
            "o_subset_a": True, "a_subset_n": True,
            "note": "census_from_runs 逐实例强制校验，违例当场抛错而非记录",
        },
        "nominal_size": census["nominal_size"],
        "applicable_by_vehicle": census["applicable_by_vehicle"],
        "n_instances": census["n_instances"],
        "fields": fields_doc,
        "summary": {
            "train_fields": len(train), "holdout_fields": len(hold),
            "train_mean_ok_per_instance": round(statistics.mean(f["mean_ok"] for f in train), 4),
            "holdout_mean_ok_per_instance": round(statistics.mean(f["mean_ok"] for f in hold), 4),
            "holdout_note": "holdout 的 O 层聚合仅描述性；建模消费在 H3 开留出集前禁止",
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    # Block D ledger 追加 index=1（继承 genesis 链）
    entries = [json.loads(line) for line in args.ledger.read_text(encoding="utf-8").splitlines() if line.strip()]
    previous = entries[-1]["entry_hash"]
    payload = {
        "artifact": "pool_census",
        "file_sha256": _sha256_file(args.output),
        "nominal_size": doc["nominal_size"],
        "applicable_by_vehicle": doc["applicable_by_vehicle"],
        "n_instances": doc["n_instances"],
        "cv_spec_hash": cv["spec_hash"],
    }
    entry = artifact_chain_entry(len(entries), previous, payload)
    with args.ledger.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
    print(f"census: fields={len(fields_doc)} instances={doc['n_instances']} "
          f"applicable={doc['applicable_by_vehicle']} ledger_index={entry['index']}")


if __name__ == "__main__":
    main()
