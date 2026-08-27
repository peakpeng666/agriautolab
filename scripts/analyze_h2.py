#!/usr/bin/env python3
"""D6：按修正案 04/05 执行 H2，并封存 Block D ledger index=5。"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path

from agriautolab.evaluation.evidence import seal_confirmatory_result, sha256_file
from agriautolab.evaluation.h2 import analyze_h2, field_effects, load_offset_front_instances
from agriautolab.contracts.vehicle import VehicleSpec
from agriautolab.pipeline.corpus.protocol import CorpusProtocol
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
    "scripts/analyze_h2.py",
    "src/agriautolab/confirmatory/h2.py",
    "src/agriautolab/confirmatory/h1.py",
    "src/agriautolab/confirmatory/stats.py",
    "src/agriautolab/corpus/derived_status.py",
    "src/agriautolab/pareto/front.py",
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _amendment_01_hash() -> str:
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


def _validate_predecessor(entries: tuple[dict, ...], h1_result: Path) -> dict:
    if len(entries) < 5 or entries[4]["payload"].get("artifact") != "h1_confirmatory_result":
        raise ValueError("D6 只能在合法 D5/H1 index=4 之后执行/重放")
    if len(entries) >= 6 and entries[5]["payload"].get("artifact") != "h2_confirmatory_result":
        raise ValueError("Block D index=5 已被非 H2 产物占用")
    if sha256_file(h1_result) != entries[4]["payload"].get("result_file_sha256"):
        raise ValueError("H1 结果文件与 ledger index=4 绑定字节不一致")
    h1_document = _load(h1_result)
    if h1_document.get("hypothesis") != "H1":
        raise ValueError("index=4 前序结果不是 H1")
    return h1_document


def _validate_h1_field_reconciliation(h1_document: dict, estimates) -> None:
    h1_rows = h1_document.get("analysis", {}).get("fields")
    if not isinstance(h1_rows, list):
        raise ValueError("H1 结果缺少 analysis.fields 字段级证据")
    h1_by_field: dict[str, dict] = {}
    for row in h1_rows:
        field_id = str(row.get("field_id"))
        if field_id in h1_by_field:
            raise ValueError(f"H1 结果含重复 field_id：{field_id}")
        h1_by_field[field_id] = row
    h2_by_field = {item.field_id: item for item in estimates}
    if set(h1_by_field) != set(h2_by_field):
        raise ValueError("H1/H2 field universe 不一致")
    mismatches: dict[str, dict] = {}
    for field_id, h2_row in h2_by_field.items():
        h1_row = h1_by_field[field_id]
        expected = (
            h1_row.get("n_instances"),
            h1_row.get("n_defined_front_instances"),
            h1_row.get("median_defined_front_size"),
        )
        actual = (
            h2_row.n_instances,
            h2_row.n_defined_front_instances,
            h2_row.median_defined_front_size,
        )
        if actual != expected:
            mismatches[field_id] = {"h1": expected, "h2": actual}
    if mismatches:
        sample = dict(list(sorted(mismatches.items()))[:5])
        raise ValueError(f"H2 重算前沿与已封 H1 字段级证据漂移：{sample}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=Path, required=True)
    parser.add_argument("--configs", type=Path, default=ROOT / "configs" / "corpus_13.json")
    parser.add_argument("--vehicles", type=Path, default=ROOT / "examples" / "corpus" / "vehicles.json")
    parser.add_argument(
        "--corpus-protocol",
        type=Path,
        default=ROOT / "examples" / "corpus" / "corpus_protocol.json",
    )
    parser.add_argument("--manifest", type=Path, default=ROOT / "evidence" / "v7" / "manifest.json")
    parser.add_argument("--pool-census", type=Path, default=ROOT / "evidence" / "block_d" / "pool_census.json")
    parser.add_argument(
        "--selection-protocol",
        type=Path,
        default=ROOT / "evidence" / "block_d" / "selection_protocol_v1.json",
    )
    parser.add_argument("--h1-result", type=Path, default=ROOT / "evidence" / "block_d" / "h1_result.json")
    parser.add_argument("--output", type=Path, default=ROOT / "evidence" / "block_d" / "h2_result.json")
    parser.add_argument("--ledger", type=Path, default=ROOT / "evidence" / "block_d" / "ledger.jsonl")
    args = parser.parse_args()

    entries = tuple(
        json.loads(line)
        for line in args.ledger.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )
    jsonl_log.verify_entries(entries)
    h1_document = _validate_predecessor(entries, args.h1_result)

    protocol_sources, protocol_bundle_hash = _verified_protocol_identity()
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
        raise ValueError("Block D index=1 必须是 D2 pool_census")
    if pool_census_sha256 != entries[1]["payload"].get("file_sha256"):
        raise ValueError("D2 pool census 文件与 ledger index=1 绑定字节不一致")
    if entries[2]["payload"].get("artifact") != "selection_protocol_v1":
        raise ValueError("Block D index=2 必须是 D3 selection_protocol_v1")
    if selection_protocol_sha256 != entries[2]["payload"].get("file_sha256"):
        raise ValueError("D3 selection protocol 文件与 ledger index=2 绑定字节不一致")
    if runs_sha256 != census["sources"]["runs_parquet_sha256"]:
        raise ValueError("runs.parquet 与 D2 pool census 绑定的数据字节不一致")
    if configs_sha256 != census["sources"]["configs_sha256"]:
        raise ValueError("corpus_13.json 与 D2 pool census 绑定的配置字节不一致")
    if vehicles_sha256 != census["sources"]["vehicles_sha256"]:
        raise ValueError("vehicles.json 与 D2 pool census 绑定的机具字节不一致")
    if manifest_sha256 != entries[0]["payload"]["manifest_file_sha256"]:
        raise ValueError("manifest 与 D1 genesis 绑定的字节不一致")

    corpus_protocol = CorpusProtocol.model_validate(_load(args.corpus_protocol))
    if corpus_protocol.spec_hash() != manifest["protocol_hash"]:
        raise ValueError("corpus_protocol.json 与 v7 manifest 的冻结 protocol_hash 不一致")
    if corpus_protocol.row_direction_mode.value != "principal_axis":
        raise ValueError("H2 只允许冻结 principal_axis 场景处理")
    if list(corpus_protocol.row_offsets_rad) != manifest["row_offsets_rad"]:
        raise ValueError("manifest row_offsets_rad 与正式 corpus protocol 不一致")
    if list(corpus_protocol.row_spacings_m) != manifest["row_spacings_m"]:
        raise ValueError("manifest row_spacings_m 与正式 corpus protocol 不一致")

    vehicle_items = _load(args.vehicles)
    vehicles = tuple(VehicleSpec(**item) for item in vehicle_items)
    actual_vehicles_hash = content_hash(tuple(vehicle.model_dump(mode="json") for vehicle in vehicles))
    if actual_vehicles_hash != corpus_protocol.vehicles_hash or len(vehicles) != 2:
        raise ValueError("H2 机具设计必须与冻结 corpus protocol 的 2 台机具一致")

    config_items = _load(args.configs)
    configs = tuple(
        PipelineConfig(**{key: value for key, value in item.items() if key != "reason"})
        for item in config_items
    )
    config_ids = tuple(config.config_id() for config in configs)
    actual_pool_hash = pool_hash(config_ids)
    if actual_pool_hash != selection_protocol["pool_hash"] or actual_pool_hash != entries[2]["payload"]["pool_hash"]:
        raise ValueError("H2 nominal pool 与 D3/ledger 冻结池不一致")

    h1_identity = h1_document.get("identity", {})
    expected_h1_identity = {
        "runs_parquet_sha256": runs_sha256,
        "configs_sha256": configs_sha256,
        "manifest_sha256": manifest_sha256,
        "pool_hash": actual_pool_hash,
        "protocol_bundle_hash": protocol_bundle_hash,
    }
    mismatched_h1 = {
        key: (h1_identity.get(key), expected)
        for key, expected in expected_h1_identity.items()
        if h1_identity.get(key) != expected
    }
    if mismatched_h1:
        raise ValueError(f"H1 前序与 H2 数据/协议身份不一致：{mismatched_h1}")

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
        raise ValueError("v7 H2 全语料维度必须是 235 fields / 4700 instances")
    if any(item.n_instances != 20 or len(item.offset_bins) != 5 for item in estimates):
        raise ValueError("v7 H2 每田必须恰好 20 instances / 5 offset bins")
    _validate_h1_field_reconciliation(h1_document, estimates)

    analysis = analyze_h2(estimates)
    document = {
        "study_id": "AGRIPLAN-PARETO-001",
        "stage": "D6-H2-confirmatory",
        "hypothesis": "H2",
        "scope": {
            "statistical_unit": "field_id",
            "field_universe": "all 235 license-cleared v7 fields from manifest.licenses",
            "model_consumption": False,
            "holdout_partition_membership_consumed": False,
            "note": (
                "H2 is a full-corpus controlled within-field scenario-factor test; no recommender/model artifact, "
                "CV assignment, holdout seal, or holdout split membership is consumed."
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
            "h1_result_sha256": sha256_file(args.h1_result),
            "h1_ledger_entry_hash": entries[4]["entry_hash"],
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
        hypothesis="H2",
        expected_index=5,
        required_previous_artifact="h1_confirmatory_result",
        result_path=args.output,
        ledger_path=args.ledger,
    )
    print(
        f"H2: all_fields={analysis['n_all_fields']} analyzable={analysis['n_analyzable_fields']} "
        f"n3/n4/n5={analysis['n_3_bins']}/{analysis['n_4_bins']}/{analysis['n_5_bins']} "
        f"median_rho={analysis['primary_rho_distribution']['median']:.12g} "
        f"p={analysis['wilcoxon']['pvalue']:.12g} ledger_index={entry['index']}"
    )


if __name__ == "__main__":
    main()
