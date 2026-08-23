#!/usr/bin/env python3
"""从 runs.parquet + manifest.json 独立重算单实例三目标 Pareto 前沿并手写 SVG。"""

from __future__ import annotations

import argparse
import csv
import html
import json
from pathlib import Path

from agriautolab.corpus.derived_status import derive_status
from agriautolab.pareto.front import ObjectiveVector, pareto_front, pool_hash


def _project(x: float, y: float, z: float) -> tuple[float, float]:
    # 固定等轴投影；只用于显示，CSV 保留未经投影的原始目标值。
    return 110.0 + 500.0 * x + 120.0 * z, 500.0 - 360.0 * y - 90.0 * z


def generate(runs_path: Path, manifest_path: Path, output_svg: Path, output_csv: Path, instance_id: str | None) -> None:
    try:
        import pyarrow.parquet as pq
    except ImportError as error:
        raise RuntimeError("生成论文图需要项目声明的 pyarrow>=16") from error
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows = pq.read_table(runs_path).to_pylist()

    def is_ok(row) -> bool:
        # 分析层统一状态入口：validator 事实优先于运行时归并
        return derive_status(str(row["runstatus"]), row.get("failure_reason")) == "ok"

    valid_instances = sorted({str(row["instance_id"]) for row in rows if is_ok(row)})
    if not valid_instances:
        raise ValueError("runs.parquet 中没有 OK 实例")
    selected = instance_id or valid_instances[0]
    selected_rows = [row for row in rows if str(row["instance_id"]) == selected and is_ok(row)]
    if not selected_rows:
        raise ValueError(f"instance_id={selected!r} 没有 OK 运行")
    points = {
        str(row["config_id"]): ObjectiveVector(float(row["path_length"]), float(row["headland_turns"]), float(row["row_crossings"]))
        for row in selected_rows
    }
    front = pareto_front(points)
    # 归一化用该实例的解析参考点（parquet 的 ref_* 列），协议模板参考点
    # 只是占位（basis 自述 placeholder），用作图归一化会系统性失真。
    ref_row = selected_rows[0]
    try:
        reference = (
            float(ref_row["ref_path_length"]),
            float(ref_row["ref_headland_turns"]),
            float(ref_row["ref_row_crossings"]),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("runs.parquet 缺少逐实例参考点列 ref_*（用带参考点列的语料重新生成）") from error

    with output_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["instance_id", "config_id", "path_length", "headland_turns", "row_crossings", "is_pareto"])
        for config_id in sorted(points):
            vector = points[config_id]
            writer.writerow([selected, config_id, *vector.as_tuple(), config_id in front])

    def norm(value: float, ref: float) -> float:
        return max(0.0, min(value / ref, 1.0)) if ref > 0.0 else 0.0

    circles = []
    projected_front = []
    for config_id in sorted(points):
        vector = points[config_id]
        x, y = _project(norm(vector.path_length, reference[0]), norm(vector.headland_turns, reference[1]), norm(vector.row_crossings, reference[2]))
        circles.append(
            f'<circle cx="{x:.3f}" cy="{y:.3f}" r="{6 if config_id in front else 4}" '
            f'fill="none" stroke="black"><title>{html.escape(config_id)}</title></circle>'
        )
        if config_id in front:
            projected_front.append((x, y, config_id))
    projected_front.sort(key=lambda item: item[0])
    polyline = " ".join(f"{x:.3f},{y:.3f}" for x, y, _ in projected_front)
    annotations = [
        f"instance_id={selected}",
        f"pool_hash={manifest.get('pool_hash', pool_hash(points.keys()))}",
        f"n_instances={len(valid_instances)}",
        f"reference={reference}",
        f"protocol_hash={manifest['protocol_hash']}",
    ]
    svg = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="900" height="620" viewBox="0 0 900 620">',
        '<rect x="0" y="0" width="900" height="620" fill="white"/>',
        '<line x1="110" y1="500" x2="610" y2="500" stroke="black"/><text x="620" y="505">path_length / ref</text>',
        '<line x1="110" y1="500" x2="110" y2="140" stroke="black"/><text x="20" y="135">headland_turns / ref</text>',
        '<line x1="110" y1="500" x2="230" y2="410" stroke="black"/><text x="235" y="410">row_crossings / ref</text>',
    ]
    if len(projected_front) >= 2:
        svg.append(f'<polyline points="{polyline}" fill="none" stroke="black" stroke-dasharray="5,4"/>')
    svg.extend(circles)
    for index, text in enumerate(annotations):
        svg.append(f'<text x="520" y="{40 + 24*index}">{html.escape(text)}</text>')
    svg.append('</svg>')
    output_svg.write_text("\n".join(svg) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--svg", type=Path, default=Path("figure_front.svg"))
    parser.add_argument("--csv", type=Path, default=Path("figure_front_data.csv"))
    parser.add_argument("--instance-id")
    args = parser.parse_args()
    generate(args.runs, args.manifest, args.svg, args.csv, args.instance_id)


if __name__ == "__main__":
    main()
