#!/usr/bin/env python3
"""顺序运行真实语料；正式模式要求显式 13 配置，self-check 不触碰网络。"""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from shapely.geometry import Polygon

from agriautolab.contracts.protocol import (
    BenchmarkProtocol,
    HypervolumeReference,
    ReverseCostSpec,
)
from agriautolab.contracts.vehicle import VehicleSpec
from agriautolab.evidence.hashing import content_hash
from agriautolab.corpus.protocol import CorpusProtocol
from agriautolab.corpus.runner import CodeVersion, CorpusRunner, discover_code_version
from agriautolab.datasets.fields2benchmark import DatasetLicense, FieldRecord, load_exported_corpus
from agriautolab.pipeline.config import PipelineConfig


def _self_check() -> None:
    record = FieldRecord(
        field_id="synthetic",
        geometry=Polygon([(0, 0), (60, 0), (60, 30), (0, 30), (0, 0)]),
        source="self-check",
        license=DatasetLicense.CC0_1_0,
        source_crs="EPSG:28992",
        working_crs="EPSG:28992",
    )
    vehicle = VehicleSpec(working_width_m=5.0, body_width_m=2.0, min_turning_radius_m=2.0)
    benchmark = BenchmarkProtocol(
        protocol_id="self-check",
        coverage_target="original_field",
        coverage_threshold=0.0,
        hypervolume_reference=HypervolumeReference(
            path_length=1e6, headland_turns=1e5, row_crossings=1e6,
            basis="corpus-template-placeholder; 超体积参考点的正典来源是逐实例 analytic_reference，"
                  "随 runs.parquet 的 ref_* 列落盘，协议模板里的这一份不参与任何前沿计算",
        ),
        # self-check 取几何中性倒车代价（乘子 1.0、换挡罚 0.0）；正式运行由协议文件给。
        reverse_cost=ReverseCostSpec(reverse_length_multiplier=1.0, gear_shift_penalty_m=0.0),
    )
    corpus = CorpusProtocol(
        protocol_id="self-check-corpus",
        benchmark_protocol_hash=benchmark.spec_hash(),
        row_offsets_rad=(0.0,),
        row_spacings_m=(3.0,),
        cv_folds=2,
        vehicles_hash=content_hash(tuple(v.model_dump(mode="json") for v in (vehicle,))),
    )
    config = PipelineConfig(
        decomposition="no_decomposition",
        headland="uniform_headland",
        swath="fixed_angle",
        route="boustrophedon_order",
        path="dubins_transit",
        params={"headland_width_m": 5.0, "angle_rad": 0.0},
    )
    with tempfile.TemporaryDirectory() as temp:
        result = CorpusRunner().run(
            (record,), (vehicle,), (config,), benchmark, corpus,
            output_dir=temp,
            code_version=CodeVersion("SELF_CHECK", True, "0" * 64),
            stop_after=1,
        )
        assert result == {"interrupted": True, "n_new": 1}
        assert len((Path(temp) / "checkpoint.jsonl").read_text(encoding="utf-8").splitlines()) == 1
    print("self-check: ok")


def _load_configs(path: Path) -> tuple[PipelineConfig, ...]:
    """读取冻结的 13 配置清单；每个条目必须带 reason，理由与配置同文件同审计。"""
    import hashlib

    items = json.loads(path.read_text(encoding="utf-8"))
    if len(items) != 13:
        raise ValueError(f"正式协议名义配置池锁定为 13；当前 JSON 给了 {len(items)}。Block C 不擅自发明第 13 个配置。")
    configs = []
    for index, item in enumerate(items):
        reason = item.pop("reason", None)
        if not str(reason).strip():
            raise ValueError(f"配置 #{index} 缺少 reason：每个进池的配置必须写明存在的理由，不许凑数")
        configs.append(PipelineConfig(**item))
    print(f"configs file sha256: {hashlib.sha256(path.read_bytes()).hexdigest()}")
    return tuple(configs)


def _seal_holdout(records, output_dir: Path, *, fraction: float, seed: int) -> None:
    """跑之前先封存留出集，按 field_id 分组。

    顺序不能反：跑完再封存，等于看过结果之后再决定留出谁。
    已存在封存文件则只对账不重封——「重新封存」就是换留出集（HoldoutVault 的既定语义）。
    """
    from agriautolab.evidence.holdout import HoldoutVault, field_level_holdout

    field_ids = tuple(record.field_id for record in records)
    holdout = field_level_holdout(field_ids, fraction=fraction, seed=seed)
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    seal_path = root / "holdout_seal.json"
    vault = HoldoutVault()
    seal = vault.seal_holdout(holdout, seed=seed)
    if seal_path.exists():
        existing = json.loads(seal_path.read_text(encoding="utf-8"))
        if existing["seal_hash"] != seal.seal_hash:
            raise SystemExit(
                f"留出集与已有封存不一致：{seal_path} 记的是 {existing['seal_hash'][:12]}，"
                f"本次算出 {seal.seal_hash[:12]}。实验中途换留出集是预注册要防的那件事"
            )
        print(f"holdout: 已封存 {len(holdout)}/{len(set(field_ids))} 块（对账通过）")
        return
    seal_path.write_text(json.dumps({
        "field_ids": list(seal.problem_ids),
        "seed": seal.seed,
        "fraction": fraction,
        "seal_hash": seal.seal_hash,
        "grouping": "field_id",
        "note": "按 field_id 分组，与 C-R1 的折分组一致；按实例封存 = 同地块跨集 = 泄漏",
    }, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"holdout: 封存 {len(holdout)}/{len(set(field_ids))} 块 "
          f"(fraction={fraction}, seed={seed}) -> {seal_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path)
    parser.add_argument("--configs", type=Path, default=Path(__file__).resolve().parents[1] / "configs" / "corpus_13.json")
    parser.add_argument("--vehicles", type=Path)
    parser.add_argument("--benchmark-protocol", type=Path)
    parser.add_argument("--corpus-protocol", type=Path)
    parser.add_argument("--output", type=Path)
    # 任务 10：必须先封存再跑。预注册参数 field 级 30%、seed 20260821。
    parser.add_argument("--holdout-fraction", type=float, default=0.3)
    parser.add_argument("--holdout-seed", type=int, default=20260821)
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    if args.self_check:
        _self_check()
        return
    required = (args.corpus, args.vehicles, args.benchmark_protocol, args.corpus_protocol, args.output)
    if any(value is None for value in required):
        parser.error("正式运行必须给 corpus/vehicles/benchmark-protocol/corpus-protocol/output")
    records = load_exported_corpus(args.corpus)
    _seal_holdout(records, args.output, fraction=args.holdout_fraction, seed=args.holdout_seed)
    configs = _load_configs(args.configs)
    vehicles = tuple(VehicleSpec.model_validate(item) for item in json.loads(args.vehicles.read_text(encoding="utf-8")))
    benchmark = BenchmarkProtocol.model_validate_json(args.benchmark_protocol.read_text(encoding="utf-8"))
    corpus_protocol = CorpusProtocol.model_validate_json(args.corpus_protocol.read_text(encoding="utf-8"))
    root = Path(__file__).resolve().parents[1]
    import hashlib

    manifest = CorpusRunner().run(
        records, vehicles, configs, benchmark, corpus_protocol,
        output_dir=args.output,
        code_version=discover_code_version(root),
        pool_file_sha256=hashlib.sha256(args.configs.read_bytes()).hexdigest(),
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
