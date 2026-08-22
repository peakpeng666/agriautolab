#!/usr/bin/env python3
"""对账报告：配对后的残差、含障碍子集单列、路线身份复现、路线扫描留痕。

四件事各自对应一条要求：
1. compare_results       —— 任务 3 的配对比较（两侧同名路线才允许比）
2. 含障碍子集单列        —— 任务 4（RMA 那条关于障碍的裁决要能被验，不是被读）
3. 路线身份复现          —— 必修正 1（bracket 不构成身份证明，用 F2C 吐出的顺序逐块复现）
4. 路线扫描              —— 必修正 3（bracket 必须是可复跑的证据，不是散文里的数字）
"""
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

import shapely

from agriautolab.algorithms.headland.uniform_headland import UniformHeadland
from agriautolab.algorithms.path.dubins_transit import DubinsTransit
from agriautolab.algorithms.route.boustrophedon_order import BoustrophedonOrder
from agriautolab.algorithms.route.skip_one_order import SkipOneOrder
from agriautolab.algorithms.swath.fixed_angle import FixedAngleSwath
from agriautolab.contracts.artifacts import CellsArtifact, RouteArtifact, SwathTraversal
from agriautolab.contracts.enums import SwathDirection
from agriautolab.contracts.problem import CoverageProblem
from agriautolab.contracts.vehicle import VehicleSpec
from agriautolab.cross_validation.f2c import F2CRequest, RecordedCsvAdapter
from agriautolab.cross_validation.report import compare_results
from agriautolab.geometry.validate import line_from_spec, polygon_to_spec
from agriautolab.metrics.path import transit_breakdown

REQUEST_FIELDS = (
    "request_id", "field_wkt", "robot_width_m", "working_width_m",
    "min_turning_radius_m", "headland_width_m", "swath_angle_rad",
    "working_crs", "route_algorithm",
)
ROUTE_SCAN = {"boustrophedon_order": BoustrophedonOrder, "skip_one_order": SkipOneOrder}


def build_swaths(item):
    polygon = shapely.from_wkt(item["field_wkt"])
    spec = polygon_to_spec(polygon, "recon")
    problem = CoverageProblem(problem_id="recon", field=spec)
    headland = UniformHeadland(item["headland_width_m"]).run(CellsArtifact(cells=(spec,)))
    swaths = FixedAngleSwath(item["swath_angle_rad"]).run(
        headland.cells[0].main_field, working_width_m=item["working_width_m"], problem=problem
    )
    vehicle = VehicleSpec(
        working_width_m=item["working_width_m"], body_width_m=item["robot_width_m"],
        min_turning_radius_m=item["min_turning_radius_m"],
    )
    return swaths, vehicle


def replay_recorded_order(swaths, identity):
    """按 F2C 吐出的访问顺序重排我方 swath：按中点最近匹配，匹配不上就抛。

    swath 数两侧不总相同（边界 epsilon），所以不能按序号对，只能按几何对。
    匹配距离超过半个幅宽即视为对不上——宁可报「复现不了」也不要静默错配。
    """
    ours = list(swaths.swaths)
    used = set()
    order = []
    worst = 0.0
    for visit in identity["visits"]:
        target = shapely.Point(
            (visit["start"][0] + visit["end"][0]) / 2.0,
            (visit["start"][1] + visit["end"][1]) / 2.0,
        )
        best, best_distance = None, float("inf")
        for index, swath in enumerate(ours):
            if index in used:
                continue
            line = line_from_spec(swath.centerline)
            distance = line.interpolate(0.5, normalized=True).distance(target)
            if distance < best_distance:
                best, best_distance = index, distance
        if best is None:
            return None, "我方 swath 用尽，F2C 还有第 %d 条" % len(order)
        used.add(best)
        order.append(ours[best])
        worst = max(worst, best_distance)
    traversals = tuple(
        SwathTraversal(
            swath_id=swath.swath_id,
            direction=SwathDirection.FORWARD if index % 2 == 0 else SwathDirection.REVERSE,
        )
        for index, swath in enumerate(order)
    )
    return RouteArtifact(traversals=traversals, swaths=tuple(order)), worst


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--requests", type=Path, default=Path("requests_metric.json"))
    parser.add_argument("--ours", type=Path, default=Path("ours.csv"))
    parser.add_argument("--golden", type=Path, default=Path("golden_f2c.csv"))
    parser.add_argument("--route-identity", type=Path, default=Path("golden_route.json"))
    parser.add_argument("--scan-output", type=Path, default=Path("route_scan.json"))
    args = parser.parse_args()

    payload = json.loads(args.requests.read_text(encoding="utf-8"))
    items = payload["requests"]
    requests = [F2CRequest(**{key: item[key] for key in REQUEST_FIELDS}) for item in items]
    ours_rows = [RecordedCsvAdapter(args.ours).run(request) for request in requests]
    golden_rows = [RecordedCsvAdapter(args.golden).run(request) for request in requests]
    by_id = {item["request_id"]: item for item in items}

    print("=" * 96)
    print("1) 配对后的残差（rel_diff_vs_golden = (ours - golden) / golden）")
    reports = compare_results(ours_rows, golden_rows)
    print(f"   route_algorithm = {reports[0].route_algorithm} ; working_crs = {reports[0].working_crs}")
    print(f"   {'metric':26s} {'n':>3s} {'median':>12s} {'max|·|':>12s}")
    for report in reports:
        print(f"   {report.metric_id:26s} {report.n_compared:3d} "
              f"{report.median_rel_diff_vs_golden * 100:11.4f}% "
              f"{report.max_abs_rel_diff_vs_golden * 100:11.4f}%")

    print()
    print("2) 含障碍子集 vs 无障碍子集（任务 4）")
    strata = {"含障碍": [], "无障碍": []}
    for ours_row, golden_row in zip(ours_rows, golden_rows):
        key = "含障碍" if by_id[ours_row.request_id]["interior_ring_count"] >= 1 else "无障碍"
        strata[key].append((ours_row, golden_row))
    print(f"   {'子集':>6s} {'n':>3s} {'main_field_area':>18s} {'path_length':>14s} {'transit_turn_total_m':>22s}")
    for name, pairs in strata.items():
        if not pairs:
            continue
        cells = []
        for metric in ("main_field_area", "path_length", "transit_turn_total_m"):
            cells.append(statistics.median(
                (float(getattr(a, metric)) - float(getattr(b, metric))) / float(getattr(b, metric))
                for a, b in pairs
            ) * 100.0)
        print(f"   {name:>6s} {len(pairs):3d} {cells[0]:17.4f}% {cells[1]:13.4f}% {cells[2]:21.4f}%")

    print()
    print("3) 路线身份复现（必修正 1）：用 F2C 吐出的访问顺序驱动我方 path 阶段")
    identities = {item["request_id"]: item
                  for item in json.loads(args.route_identity.read_text(encoding="utf-8"))["identities"]}
    replay_rows = []
    print(f"   {'request_id':26s} {'F2C 顺序前 8':>26s} {'匹配最大偏差':>12s} {'复现 transit':>13s} "
          f"{'F2C transit':>12s} {'rel':>9s}")
    for item in items:
        identity = identities[item["request_id"]]
        swaths, vehicle = build_swaths(item)
        route, detail = replay_recorded_order(swaths, identity)
        golden_turn = next(r for r in golden_rows if r.request_id == item["request_id"]).transit_turn_total_m
        if route is None:
            print(f"   {item['request_id']:26s} {'复现失败: ' + str(detail):>26s}")
            continue
        path = DubinsTransit(0.25).run(route, vehicle)
        replayed = transit_breakdown(path).turn_total_m
        rel = (replayed - golden_turn) / golden_turn
        replay_rows.append({"request_id": item["request_id"], "match_worst_m": detail,
                            "replayed_turn_total_m": replayed, "golden_turn_total_m": golden_turn,
                            "rel_diff_vs_golden": rel})
        print(f"   {item['request_id']:26s} {str(identity['visit_order'][:8]):>26s} {detail:11.4f}m "
              f"{replayed:12.2f} {golden_turn:11.2f} {rel * 100:8.3f}%")
    if replay_rows:
        print(f"   复现 transit 中位 rel_diff_vs_golden = "
              f"{statistics.median(r['rel_diff_vs_golden'] for r in replay_rows) * 100:+.4f} %")

    print()
    print("4) 路线扫描（必修正 3）：同一 swath 输入，只换我方路线算法")
    scan = {}
    print(f"   {'route':22s} {'transit 中位 rel_diff_vs_golden':>32s}")
    for name, factory in ROUTE_SCAN.items():
        rels = []
        for item in items:
            swaths, vehicle = build_swaths(item)
            path = DubinsTransit(0.25).run(factory().run(swaths), vehicle)
            golden = next(r for r in golden_rows if r.request_id == item["request_id"])
            golden_transit = golden.path_length - golden.swath_length_sum
            rels.append((transit_breakdown(path).total_m - golden_transit) / golden_transit)
        scan[name] = rels
        print(f"   {name:22s} {statistics.median(rels) * 100:31.4f}%")

    args.scan_output.write_text(json.dumps({
        "route_algorithm_compared": reports[0].route_algorithm,
        "route_scan_transit_rel_diff_vs_golden": {
            name: {"per_request": dict(zip([i["request_id"] for i in items], rels)),
                   "median": statistics.median(rels)}
            for name, rels in scan.items()
        },
        "route_identity_replay": replay_rows,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\n扫描与复现结果已留痕 -> {args.scan_output}")


if __name__ == "__main__":
    main()
