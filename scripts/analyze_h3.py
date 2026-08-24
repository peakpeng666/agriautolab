#!/usr/bin/env python3
"""D7：按修正案 03/04/05 执行 H3；已封存后禁止再次消费 holdout。

--fields train 仅作训练侧管道 sanity（不写结果、不封存）；--fields holdout
仅允许在 ledger 尚无 H3 时执行一次。所有协议、输入与 D4 模型字节身份必须在
模型反序列化及 holdout runs 读取之前通过。
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
from pathlib import Path

from agriautolab.confirmatory.evidence import seal_confirmatory_result, sha256_file
from agriautolab.confirmatory.h3 import analyze_h3
from agriautolab.confirmatory.h3_preflight import verify_h3_preflight
from agriautolab.contracts.vehicle import VehicleSpec
from agriautolab.evidence.hashing import content_hash
from agriautolab.pipeline.config import PipelineConfig
from agriautolab.selection.evaluation import load_selection_instances

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
    "scripts/analyze_h3.py",
    "src/agriautolab/confirmatory/h3.py",
    "src/agriautolab/confirmatory/h3_preflight.py",
    "src/agriautolab/selection/evaluation.py",
    "src/agriautolab/selection/experiment.py",
    "src/agriautolab/selection/recommender.py",
    "src/agriautolab/selection/pools.py",
    "src/agriautolab/pareto/preference_grid.py",
    "src/agriautolab/corpus/derived_status.py",
    "src/agriautolab/pareto/front.py",
)
EXPECTED_LEDGER_INDEX = 6
REQUIRED_PREVIOUS_ARTIFACT = "h2_confirmatory_result"


def _verified_protocol_identity() -> tuple[dict[str, str], str]:
    actual = {relative: sha256_file(ROOT / relative) for relative in EXPECTED_PROTOCOL_SHA256}
    if actual != EXPECTED_PROTOCOL_SHA256:
        raise ValueError(f"冻结预注册/修正案字节漂移：expected={EXPECTED_PROTOCOL_SHA256}, actual={actual}")

    import hashlib

    text = (ROOT / "AUDIT_NOTE.md").read_text(encoding="utf-8")
    start = text.index("## R1-1")
    end = text.index("## R1-2", start)
    amendment_01 = hashlib.sha256(text[start:end].encode("utf-8")).hexdigest()
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
    parser.add_argument("--vehicles", type=Path, default=ROOT / "examples" / "corpus" / "vehicles.json")
    parser.add_argument("--cv", type=Path, default=ROOT / "evidence" / "v7" / "cv_assignment.json")
    parser.add_argument("--holdout", type=Path, default=ROOT / "evidence" / "v7" / "holdout_seal.json")
    parser.add_argument("--pool-census", type=Path, default=ROOT / "evidence" / "block_d" / "pool_census.json")
    parser.add_argument(
        "--selection-protocol",
        type=Path,
        default=ROOT / "evidence" / "block_d" / "selection_protocol_v1.json",
    )
    parser.add_argument("--h2-result", type=Path, default=ROOT / "evidence" / "block_d" / "h2_result.json")
    parser.add_argument("--model-dir", type=Path, default=Path.home() / "agriautolab-data" / "d4")
    parser.add_argument("--output", type=Path, default=ROOT / "evidence" / "block_d" / "h3_result.json")
    parser.add_argument("--ledger", type=Path, default=ROOT / "evidence" / "block_d" / "ledger.jsonl")
    parser.add_argument("--fields", choices=("train", "holdout"), default="holdout")
    args = parser.parse_args()

    if importlib.metadata.version("scikit-learn") != "1.7.2":
        raise ValueError("H3 执行环境必须 scikit-learn==1.7.2（与封存模型一致）")

    # 先验硬门：必须在 joblib.load 和任何 holdout runs 读取之前完成。
    protocol_sources, protocol_bundle_hash = _verified_protocol_identity()
    code_files, analysis_code_hash = _code_identity()
    model_path = args.model_dir / "recommender.joblib"
    metadata_path = args.model_dir / "recommender_metadata.json"
    preflight = verify_h3_preflight(
        ledger_path=args.ledger,
        runs_path=args.runs,
        configs_path=args.configs,
        vehicles_path=args.vehicles,
        cv_path=args.cv,
        holdout_path=args.holdout,
        pool_census_path=args.pool_census,
        selection_protocol_path=args.selection_protocol,
        h2_result_path=args.h2_result,
        model_path=model_path,
        metadata_path=metadata_path,
        protocol_bundle_hash=protocol_bundle_hash,
        reject_if_h3_sealed=args.fields == "holdout",
    )

    items = json.loads(args.configs.read_text(encoding="utf-8"))
    configs = tuple(PipelineConfig(**{k: v for k, v in it.items() if k != "reason"}) for it in items)
    vehicles = tuple(
        VehicleSpec.model_validate(v)
        for v in json.loads(args.vehicles.read_text(encoding="utf-8"))
    )

    # 二进制已通过 D4 exact-SHA gate，随后才允许反序列化。
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
            f"D4 模型对象身份与已验证 metadata 不一致："
            f"actual={loaded_identity}, expected={expected_loaded_identity}"
        )

    holdout_fields = sorted(preflight.holdout["field_ids"])
    training_fields = sorted(e["field_id"] for e in preflight.cv["assignments"])
    field_ids = training_fields if args.fields == "train" else holdout_fields

    # 数据读取在全部身份门和模型对象自检之后才发生。
    target_instances = load_selection_instances(args.runs, field_ids, configs, vehicles)
    training_instances = (
        target_instances
        if args.fields == "train"
        else load_selection_instances(args.runs, training_fields, configs, vehicles)
    )
    analysis = analyze_h3(recommender, training_instances, target_instances)

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
        "hypothesis": "H3",
        "stage": "D7-H3-confirmatory",
        "study_id": "AGRIPLAN-PARETO-001",
        "analysis": analysis,
        "identity": {
            "analysis_code_sha256_by_path": code_files,
            "analysis_code_hash": analysis_code_hash,
            "protocol_sha256_by_source": protocol_sources,
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
            "field_universe": "70 sealed holdout fields; dual-track 70/68 per amendment 05",
            "model_consumption": "final-fit recommender from D4 (in-sample on training, one-shot on holdout)",
            "statistical_unit": "field",
        },
    }
    _immutable_write(args.output, document)
    seal_confirmatory_result(
        hypothesis="H3",
        expected_index=EXPECTED_LEDGER_INDEX,
        required_previous_artifact=REQUIRED_PREVIOUS_ARTIFACT,
        result_path=args.output,
        ledger_path=args.ledger,
    )
    track = analysis["track_70"]
    print(
        f"H3 sealed (index={EXPECTED_LEDGER_INDEX}): fields={track['n_fields']} "
        f"mean_D={track['mean_D']:.5f} p={track['permutation']['pvalue']:.4e} "
        f"failure_triggered={analysis['preregistered_failure_checks']['any_triggered']}"
    )


if __name__ == "__main__":
    main()
