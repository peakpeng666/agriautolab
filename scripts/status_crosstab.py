#!/usr/bin/env python3
"""config × 机具 × derived_status 交叉表 + 有效池分布（H1 前置，v7 复核 §六）。

验证器具名拒绝若在配置之间分布高度不均，前沿实际是在「事实上更小的池」上
算出来的——这张表把每个配置-机具组合的 ok / 具名拒绝 / 配对 NA 占比摆到
明面上，并报有效池的完整分布（不只中位：均值 6.63 vs 中位 10 的重低尾
必须可见）与零 ok 实例计数。

状态一律取 derived_status（validator 事实优先于运行时归并）。
用法：
  python scripts/status_crosstab.py --runs out_v7/runs.parquet \
      --configs configs/corpus_13.json --out evidence/v7/
"""

from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path

from agriautolab.corpus.derived_status import derive_status, status_diff_counts
from agriautolab.pipeline.config import PipelineConfig


def _config_names(configs_path: Path) -> dict[str, str]:
    items = json.loads(configs_path.read_text(encoding="utf-8"))
    names: dict[str, str] = {}
    for item in items:
        config = PipelineConfig(**{k: v for k, v in item.items() if k != "reason"})
        parts = [config.decomposition, config.headland, config.swath, config.route, config.path]
        label = "+".join(parts)
        params = item.get("params", {})
        width = params.get("headland_width_m")
        if width is not None:
            label += f"@{width}m"
        angle = params.get("angle_rad")
        if angle is not None:
            label += f"/a={angle:.4f}"
        names[config.config_id()] = label
    return names


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=Path, required=True)
    parser.add_argument("--configs", type=Path, default=Path(__file__).resolve().parents[1] / "configs" / "corpus_13.json")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    import pyarrow.parquet as pq

    names = _config_names(args.configs)
    cells: dict[tuple[str, int], Counter] = defaultdict(Counter)
    ok_per_instance: Counter = Counter()
    instances: set[str] = set()
    diffs: Counter = Counter()
    n_rows = 0
    for batch in pq.ParquetFile(args.runs).iter_batches(
        batch_size=16384, columns=["config_id", "vehicle_index", "instance_id", "runstatus", "failure_reason"],
    ):
        for cid, vid, iid, raw, reason in zip(
            batch.column(0).to_pylist(), batch.column(1).to_pylist(), batch.column(2).to_pylist(),
            batch.column(3).to_pylist(), batch.column(4).to_pylist(),
        ):
            n_rows += 1
            derived = derive_status(str(raw), reason)
            cells[(cid, vid)][derived] += 1
            instances.add(str(iid))
            if derived == "ok":
                ok_per_instance[str(iid)] += 1
            if derived != str(raw):
                diffs[f"{raw}->{derived}"] += 1

    table: list[dict] = []
    for (cid, vid), counts in sorted(cells.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        total = sum(counts.values())
        ok = counts.get("ok", 0)
        named_reject = total - ok - counts.get("not_applicable", 0)
        table.append({
            "config": names.get(cid, cid[:12]), "config_id": cid, "vehicle_index": vid,
            "rows": total, "ok": ok, "ok_share": round(ok / total, 4),
            "named_rejections": named_reject, "named_rejection_share": round(named_reject / total, 4),
            "not_applicable": counts.get("not_applicable", 0),
            "by_derived_status": dict(counts),
            "factually_out_of_pool": named_reject / total >= 0.8,
        })

    pool_sizes = sorted(ok_per_instance.get(iid, 0) for iid in instances)
    positive = [v for v in pool_sizes if v >= 1]
    quartile = lambda q: pool_sizes[min(len(pool_sizes) - 1, int(q * (len(pool_sizes) - 1)))]
    pool_stats = {
        "n_instances": len(instances),
        "zero_ok": sum(1 for v in pool_sizes if v == 0),
        "degenerate_le1": sum(1 for v in pool_sizes if v <= 1),
        "min": pool_sizes[0], "q1": quartile(0.25), "median": statistics.median(pool_sizes),
        "median_over_positive": statistics.median(positive),
        "median_note": "median=全实例口径（含零 ok，低尾可见）；median_over_positive=仅 ≥1 ok 实例（与 manifest 口径一致）",
        "q3": quartile(0.75), "max": pool_sizes[-1],
        "mean": round(statistics.mean(pool_sizes), 4),
        "histogram": {str(k): v for k, v in Counter(pool_sizes).most_common()},
        "mean_vs_median_note": "均值<中位=重低尾（零/小 ok 实例拖尾），只报中位会盖住尾巴",
    }

    result = {
        "runs": str(args.runs), "n_rows": n_rows,
        "derived_vs_runstatus_diff_counts": dict(diffs),
        "crosstab": table,
        "effective_pool_distribution": pool_stats,
        "factually_out_of_pool_combos": [r["config"] + f"@v{r['vehicle_index']}" for r in table if r["factually_out_of_pool"]],
    }
    (args.out / "status_crosstab.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8",
    )

    lines = [
        "# config × 机具 × derived_status 交叉表（H1 前置）", "",
        f"行数 {n_rows}；derived_status 分歧：{dict(diffs) or '无'}", "",
        "| 配置 | 机具 | 行数 | ok | ok% | 具名拒绝% | NA | 事实上出池(≥80%拒) |",
        "|---|---:|---:|---:|---:|---:|---:|:--:|",
    ]
    for r in table:
        lines.append(
            f"| {r['config']} | v{r['vehicle_index']} | {r['rows']} | {r['ok']} | "
            f"{r['ok_share']:.1%} | {r['named_rejection_share']:.1%} | {r['not_applicable']} | "
            f"{'**是**' if r['factually_out_of_pool'] else ''} |"
        )
    lines += ["", "## 有效池分布（实例数 = {n}）".format(n=pool_stats["n_instances"]), ""]
    lines.append(f"零 ok {pool_stats['zero_ok']}；≤1 {pool_stats['degenerate_le1']}；"
                 f"min {pool_stats['min']} / Q1 {pool_stats['q1']} / 中位(全实例) {pool_stats['median']} / "
                 f"中位(仅≥1ok，manifest 口径) {pool_stats['median_over_positive']} / "
                 f"Q3 {pool_stats['q3']} / max {pool_stats['max']}；**均值 {pool_stats['mean']}**")
    lines.append("直方图（池大小:实例数）：" + ", ".join(
        f"{k}:{v}" for k, v in sorted(pool_stats["histogram"].items(), key=lambda kv: int(kv[0]))))
    (args.out / "status_crosstab.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {args.out / 'status_crosstab.json'} and .md; rows={n_rows}, diffs={dict(diffs)}")


if __name__ == "__main__":
    main()
