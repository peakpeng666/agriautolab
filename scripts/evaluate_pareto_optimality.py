#!/usr/bin/env python3
"""D5：按修正案 03/05 正式执行 H1，并封存 Block D ledger index=4。"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
from pathlib import Path

from agriautolab.evaluation.records import seal_confirmatory_result, sha256_file
from agriautolab.evaluation.pareto_optimality import analyze_h1, field_estimates, load_front_instances
from agriautolab.pipeline.hashing import content_hash
from agriautolab.pipeline import jsonl_log
from agriautolab.pipeline.pareto.front import pool_hash
from agriautolab.pipeline.config import PipelineConfig

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_PROTOCOL_SHA256 = {
    "prereg/AGRIPLAN-PARETO-001.yaml": "8d1326de651ed91cce66ed01fc24a7a527064fe9ec7c1cedd83793e7c23f6a80",
    "prereg/AGRIPLAN-PARETO-001.amendment-02.md": "f0416911d7c0a22d0fe39afad472f564154fd2d0e2daf313c9b31437f3511323",
    "prereg/AGRIPLAN-PARETO-001.amendment-03.md": "f0b0d42dadd3cc9287e032f9f3981244a82e8ecbc26f5fb7ca7e810f529a80c3",
    "prereg/AGRIPLAN-PARETO-001.amendment-04.md": "f4c16b78c48f34f33b5f42b6a595fdde8c9aaffa3626463025bd5f69a495a860",
    "prereg/AGRIPLAN-PARETO-001.amendment-05.md": "97f4f2328bfe25d53711dc97c0e46d81471deb1315cf20b15c85f874244cbf87",
}
EXPECTED_AMENDMENT_01_EXCERPT_SHA256 = "162f28a32db646335019f9900130177d2c4aa3e8079188d9db71e9b74d6b5efb"
ANALYSIS_CODE_FILES = (
    "scripts/evaluate_pareto_optimality.py",
    "src/agriautolab/evaluation/pareto_optimality.py",
    "src/agriautolab/evaluation/stats.py",
    "src/agriautolab/pipeline/corpus/derived_status.py",
    "src/agriautolab/pipeline/pareto/front.py",
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _amendment_01_hash() -> str:
    import hashlib

    text = (ROOT / "AUDIT_NOTE.md").read_text(encoding="utf-8")
    start = text.index("## R1-1")
    end = text.index("## R1-2", start)
    return hashlib.sha256(text[start:end].encode("utf-8")).hexdigest()


def _verified_protocol_identity() -> tuple[dict[str, str], str]:
    actual = {relative: sha256_file(ROOT / relative) for relative in EXPECTED_PROTOCOL_SHA256}
    if actual != EXPECTED_PROTOCOL_SHA256:
        raise ValueError(f"冻结预注册/修正案字节漂移：expected={EXPECTED_PROTOCOL_SHA256}, actual={actual}")
    amendment_01 = _amendment_01_hash()
    if amendment_01 != EXPECTED_AMENDMENT_01_EXCERPT_SHA256:
        raise ValueError("AUDIT_NOTE R1-1 修正案 01 字节漂移")
    sources = {"AUDIT_NOTE.md#R1-1": amendment_01, **actual}
    return sources, content_hash({"sha256_by_source": sources})


def _code_identity() -> tuple[dict[str, str], str]:
    files = {relative: sha256_file(ROOT / relative) for relative in ANALYSIS_CODE_FILES}
    return files, content_hash({"sha256_by_path": files})


def _immutable_write(path: Path, document: dict) -> None:
    encoded = (json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    if path.exists():
        if path.read_bytes() != encoded:
            raise ValueError(f"拒绝覆盖既有不同结果：{path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encoded)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=Path, required=True)
    parser.add_argument("--configs", type=Path, default=ROOT / "configs" / "corpus_13.json")
    parser.add_argument("--manifest", type=Path, default=ROOT / "evidence" / "v7" / "manifest.json")
    parser.add_argument("--pool-census", type=Path, default=ROOT / "benchmarks/results/pool_census.json")
    parser.add_argument("--protocol", type=Path, default=ROOT / "benchmarks/results/benchmark_cv_protocol.json")
    parser.add_argument("--output", type=Path, default=ROOT / "benchmarks/results/pareto_optimality_result.json")
    parser.add_argument("--ledger", type=Path, default=ROOT / "benchmarks/results/benchmark_ledger.jsonl")
    args = parser.parse_args()

    entries = tuple(json.loads(line) for line in args.ledger.read_text(encoding="utf-8").splitlines() if line.strip())
    jsonl_log.verify_entries(entries)
    if len(entries) < 4 or entries[3]["payload"].get("artifact") != "selection_cv_result":
        raise ValueError("D5 只能在合法 D4 index=3 之后执行/重放")
    if len(entries) >= 5 and entries[4]["payload"].get("artifact") != "h1_confirmatory_result":
        raise ValueError("Block D index=4 已被非 H1 产物占用")

    protocol_sources, protocol_bundle_hash = _verified_protocol_identity()
    code_files, analysis_code_hash = _code_identity()
    runs_sha256 = sha256_file(args.runs)
    configs_sha256 = sha256_file(args.configs)
    manifest_sha256 = sha256_file(args.manifest)
    census = _load(args.pool_census)
    manifest = _load(args.manifest)
    selection_protocol = _load(args.protocol)
    if runs_sha256 != census["sources"]["runs_parquet_sha256"]:
        raise ValueError("runs.parquet 与 D2 pool census 绑定的数据字节不一致")
    if configs_sha256 != census["sources"]["configs_sha256"]:
        raise ValueError("corpus_13.json 与 D2 pool census 绑定的配置字节不一致")
    if manifest_sha256 != entries[0]["payload"]["manifest_file_sha256"]:
        raise ValueError("manifest 与 D1 genesis 绑定的字节不一致")

    config_items = json.loads(args.configs.read_text(encoding="utf-8"))
    configs = tuple(PipelineConfig(**{key: value for key, value in item.items() if key != "reason"}) for item in config_items)
    config_ids = tuple(config.config_id() for config in configs)
    actual_pool_hash = pool_hash(config_ids)
    if actual_pool_hash != selection_protocol["pool_hash"] or actual_pool_hash != entries[2]["payload"]["pool_hash"]:
        raise ValueError("H1 nominal pool 与 D3/ledger 冻结池不一致")

    expected_fields = tuple(sorted(str(field_id) for field_id in manifest["licenses"]))
    instances = load_front_instances(args.runs, config_ids)
    estimates = field_estimates(instances, expected_field_ids=expected_fields)
    if len(expected_fields) != 235 or len(instances) != 4700 or census["n_instances"] != 4700:
        raise ValueError("v7 H1 全语料维度必须是 235 fields / 4700 instances")
    if any(item.n_instances != 20 for item in estimates):
        raise ValueError("v7 H1 每田必须恰好 20 instances")

    analysis = analyze_h1(estimates)
    document = {
        "study_id": "AGRIPLAN-PARETO-001",
        "stage": "D5-H1-confirmatory",
        "hypothesis": "H1",
        "scope": {
            "statistical_unit": "field_id",
            "field_universe": "all 235 license-cleared v7 fields from manifest.licenses",
            "model_consumption": False,
            "holdout_partition_used_for_modeling": False,
            "note": "H1 is a full-corpus front-size test; no recommender/model artifact or holdout split membership is consumed.",
        },
        "identity": {
            "runs_parquet_sha256": runs_sha256,
            "configs_sha256": configs_sha256,
            "manifest_sha256": manifest_sha256,
            "pool_hash": actual_pool_hash,
            "analysis_code_sha256_by_path": code_files,
            "analysis_code_hash": analysis_code_hash,
            "protocol_sha256_by_source": protocol_sources,
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
        hypothesis="H1",
        expected_index=4,
        required_previous_artifact="selection_cv_result",
        result_path=args.output,
        ledger_path=args.ledger,
    )
    print(
        f"H1: all_fields={analysis['n_all_fields']} analyzable={analysis['n_analyzable_fields']} "
        f"zero_ok_fields={analysis['n_zero_ok_fields']} median={analysis['primary_distribution']['median']} "
        f"p={analysis['wilcoxon']['pvalue']:.12g} ledger_index={entry['index']}"
    )


if __name__ == "__main__":
    main()
