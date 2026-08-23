#!/usr/bin/env python3
"""从已导入语料构建 F2C 对账请求清单（分层抽样，规则与种子写死进清单）。

参数与地块选择全部进 requests.json：两侧录制端只消费这份清单，
不引入任何一侧的隐式配置——同一清单、同一数字，才有对账意义。

抽样按 ReconciliationSamplingSpec 分层，不按 id 顺序，也不按等距抽：
等距抽样在这份语料上抽出的 12 块里只有 1 块含障碍，
而 235 块语料里有 33 块含障碍——于是 main_field_area 的 0.004% 主要来自无障碍情形，
而 RMA 裁决（F2C 扣障碍 + 扣障碍周围一圈 headland）恰恰是关于障碍的。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import shapely

from agriautolab.corpus.protocol import DEFAULT_RECONCILIATION_SAMPLING, ReconciliationSamplingSpec

DEFAULT_PARAMS = {
    "robot_width_m": 2.0,
    "working_width_m": 5.0,
    "min_turning_radius_m": 2.0,
    "headland_width_m": 5.0,
    "swath_angle_rad": 1.5707963267948966,
    # 路线阶段必须显式配对（路线配对规格）。写死 snake 那次的代价是
    # 两侧跑了不同路线、transit 差 −38.11%，被读成了「我方路径更短」。
    "route_algorithm": "boustrophedon",
}


def interior_ring_count(wkt: str) -> int:
    return len(shapely.from_wkt(wkt).interiors)


def stratified_sample(rows: list[dict], spec: ReconciliationSamplingSpec) -> list[dict]:
    """按内环数分三层抽样：多内环 -> 单内环 -> 无障碍，各层内用注入的 Generator 抽。

    返回顺序按 field_id 排序，让 request_id 稳定；随机只决定「抽谁」，不决定排序。
    """
    by_id = {row["field_id"]: row for row in rows}
    ring_counts = {field_id: interior_ring_count(row["wkt"]) for field_id, row in by_id.items()}
    multi = sorted(fid for fid, count in ring_counts.items() if count >= 2)
    single = sorted(fid for fid, count in ring_counts.items() if count == 1)
    plain = sorted(fid for fid, count in ring_counts.items() if count == 0)

    if len(multi) < spec.min_with_multiple_rings:
        raise SystemExit(f"语料只有 {len(multi)} 块含多内环，达不到下限 {spec.min_with_multiple_rings}")
    if len(multi) + len(single) < spec.min_with_obstacles:
        raise SystemExit(
            f"语料只有 {len(multi) + len(single)} 块含障碍，达不到下限 {spec.min_with_obstacles}"
        )

    rng = np.random.default_rng(spec.seed)

    def take(pool: list[str], count: int, chosen: set[str]) -> list[str]:
        available = [field_id for field_id in pool if field_id not in chosen]
        count = min(count, len(available))
        if count <= 0:
            return []
        picked = rng.choice(np.asarray(available, dtype=object), size=count, replace=False)
        return [str(item) for item in picked]

    chosen: set[str] = set()
    chosen.update(take(multi, spec.min_with_multiple_rings, chosen))
    chosen.update(take(single + multi, spec.min_with_obstacles - len(chosen), chosen))
    chosen.update(take(plain, spec.total - len(chosen), chosen))
    if len(chosen) < spec.total:
        raise SystemExit(f"语料不足：只凑出 {len(chosen)} 块，要求 {spec.total}")
    return [by_id[field_id] for field_id in sorted(chosen)]


def build_requests(corpus_dir: Path, spec: ReconciliationSamplingSpec, params: dict) -> list[dict]:
    rows = [
        json.loads(line)
        for line in (corpus_dir / "fields.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    picked = stratified_sample(rows, spec)
    return [
        # working_crs 逐地块随语料带出：F2B 语料按质心选局部 UTM，全语料不是同一个投影。
        # 两侧录制端都只消费这份清单，因此两侧声明的投影同源、可比。
        {
            "request_id": f"f2b_{index:03d}_{row['field_id']}",
            "field_id": row["field_id"],
            "field_wkt": row["wkt"],
            "working_crs": row["working_crs"],
            "interior_ring_count": interior_ring_count(row["wkt"]),
            **params,
        }
        for index, row in enumerate(picked)
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, required=True, help="export_corpus 输出目录")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--total", type=int, default=DEFAULT_RECONCILIATION_SAMPLING.total)
    parser.add_argument("--seed", type=int, default=DEFAULT_RECONCILIATION_SAMPLING.seed)
    args = parser.parse_args()
    spec = DEFAULT_RECONCILIATION_SAMPLING.model_copy(update={"total": args.total, "seed": args.seed})
    requests = build_requests(args.corpus, spec, DEFAULT_PARAMS)
    args.output.write_text(json.dumps({
        "params": DEFAULT_PARAMS,
        "sampling": spec.model_dump(mode="json"),
        "requests": requests,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    countries = sorted({item["field_id"][:2] for item in requests})
    with_obstacles = sum(1 for item in requests if item["interior_ring_count"] >= 1)
    with_multi = sum(1 for item in requests if item["interior_ring_count"] >= 2)
    print(f"requests: {len(requests)} 块（{', '.join(countries)}）-> {args.output}")
    print(f"  含障碍 {with_obstacles} 块，其中含多内环 {with_multi} 块；seed={spec.seed}")


if __name__ == "__main__":
    main()
