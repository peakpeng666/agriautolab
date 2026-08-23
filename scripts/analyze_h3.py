#!/usr/bin/env python3
"""D7：按修正案 03/04/05 正式执行 H3（留出集一次性消费）并封存 index=6。

--fields train 仅作管道 sanity（不写结果、不封存）；--fields holdout 是
唯一正式模式：一次性读取 70 块留出田，写 h3_result.json 并封存账本。
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
from pathlib import Path

from agriautolab.confirmatory.evidence import seal_confirmatory_result, sha256_file
from agriautolab.confirmatory.h3 import analyze_h3
from agriautolab.contracts.vehicle import VehicleSpec
from agriautolab.evidence.hashing import content_hash
from agriautolab.evidence.ledger import verify_artifact_chain
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
ANALYSIS_CODE_FILES = (
    "scripts/analyze_h3.py",
    "src/agriautolab/confirmatory/h3.py",
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
        raise ValueError(f"冻结预注册/修正案字节漂移：{actual}")
    import hashlib

    text = (ROOT / "AUDIT_NOTE.md").read_text(encoding="utf-8")
    start = text.index("## R1-1")
    end = text.index("## R1-2", start)
    amendment_01 = hashlib.sha256(text[start:end].encode("utf-8")).hexdigest()
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
    parser.add_argument("--model-dir", type=Path, default=Path.home() / "agriautolab-data" / "d4")
    parser.add_argument("--output", type=Path, default=ROOT / "evidence" / "block_d" / "h3_result.json")
    parser.add_argument("--ledger", type=Path, default=ROOT / "evidence" / "block_d" / "ledger.jsonl")
    parser.add_argument("--fields", choices=("train", "holdout"), default="holdout")
    args = parser.parse_args()

    if importlib.metadata.version("scikit-learn") != "1.7.2":
        raise ValueError("H3 执行环境必须 scikit-learn==1.7.2（与封存模型一致）")

    cv = json.loads(args.cv.read_text(encoding="utf-8"))
    holdout = json.loads(args.holdout.read_text(encoding="utf-8"))
    holdout_fields = sorted(holdout["field_ids"])
    training_fields = sorted(e["field_id"] for e in cv["assignments"])
    if set(holdout_fields) & set(training_fields):
        raise ValueError("留出集与训练折重叠：封存身份已坏")

    entries = tuple(json.loads(line) for line in args.ledger.read_text(encoding="utf-8").splitlines() if line.strip())
    verify_artifact_chain(entries)
    artifacts = [entry["payload"].get("artifact") for entry in entries]
    if REQUIRED_PREVIOUS_ARTIFACT not in artifacts:
        raise ValueError("H3 只能在合法 D6（h2_confirmatory_result）之后执行")
    if "h3_confirmatory_result" in artifacts and args.fields == "holdout":
        pass  # 幂等重放由 sealer 逐字节校验

    items = json.loads(args.configs.read_text(encoding="utf-8"))
    configs = tuple(PipelineConfig(**{k: v for k, v in it.items() if k != "reason"}) for it in items)
    vehicles = tuple(VehicleSpec.model_validate(v) for v in json.loads(args.vehicles.read_text(encoding="utf-8")))

    import joblib

    model_path = args.model_dir / "recommender.joblib"
    recommender = joblib.load(model_path)
    metadata = json.loads((args.model_dir / "recommender_metadata.json").read_text(encoding="utf-8"))
    if metadata.get("cv_spec_hash") != cv["spec_hash"]:
        raise ValueError("模型绑定 的 CV 身份与当前折表不一致")

    field_ids = training_fields if args.fields == "train" else holdout_fields
    target_instances = load_selection_instances(args.runs, field_ids, configs, vehicles)
    training_instances = (target_instances if args.fields == "train"
                          else load_selection_instances(args.runs, training_fields, configs, vehicles))

    analysis = analyze_h3(recommender, training_instances, target_instances)

    if args.fields == "train":
        track = analysis["track_70"]
        print(f"[sanity|train] fields={analysis['n_analyzable_fields']} "
              f"rec={track['mean_recommender_loss']:.5f} rand_app={track['mean_random_applicable_loss']:.5f} "
              f"mean_D={track['mean_D']:.5f} sbs={analysis['sbs_config_id'][:12]}")
        return

    protocol_sources, protocol_bundle_hash = _verified_protocol_identity()
    code_files, analysis_code_hash = _code_identity()
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
            "metadata_file_sha256": sha256_file(args.model_dir / "recommender_metadata.json"),
            "cv_spec_hash": cv["spec_hash"],
            "holdout_seal_hash": holdout.get("seal_hash"),
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
    print(f"H3 sealed (index={EXPECTED_LEDGER_INDEX}): fields={track['n_fields']} "
          f"mean_D={track['mean_D']:.5f} p={track['permutation']['pvalue']:.4e} "
          f"failure_triggered={analysis['preregistered_failure_checks']['any_triggered']}")


if __name__ == "__main__":
    main()
