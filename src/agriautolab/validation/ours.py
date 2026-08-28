"""我方对账复算：与 F2C 公共链路同语义的四个共有量。

语义假设（对账的目的就是检验它们，先显式声明再被数据裁决）：
- 链路对应关系：F2C HG_Const_gen ↔ uniform_headland（同一减地头实现），
  SG_BruteForce(angle) ↔ fixed_angle，RP_Snake ↔ boustrophedon_order，
  PP_DubinsCurves ↔ dubins_transit。
- main_field_area 取「地块 − 地头环带」的面积（假设 A）。F2C 侧 headland.area()
  的真实语义（主田面积还是环带面积、是否扣障碍）由 golden 比对裁决——
  compute_ours_detail 同时给出环带面积与地块面积，供假设 B 对账用，
  对齐口径需在查看残差之后确定。
"""

from __future__ import annotations

import shapely

from agriautolab.algorithms.headland.uniform_headland import UniformHeadland
from agriautolab.algorithms.path.dubins_transit import DubinsTransit
from agriautolab.algorithms.route.boustrophedon_order import BoustrophedonOrder
from agriautolab.algorithms.swath.fixed_angle import FixedAngleSwath
from agriautolab.contracts.artifacts import CellsArtifact
from agriautolab.contracts.problem import CoverageProblem
from agriautolab.contracts.vehicle import VehicleSpec
from agriautolab.validation.f2c import F2CRequest, F2CResult, RouteAlgorithmMismatchError
from agriautolab.geometry.robust import robust_union
from agriautolab.geometry.validate import line_from_spec, polygon_from_spec, polygon_to_spec
from agriautolab.pipeline.metrics.path import transit_breakdown


# 协议声明的路线算法名 -> 我方实现。只放语义确实相同的。
#
# 刻意不收 "snake"：我方 skip_one_order 的奇数轮是升序（0,2,4,…,1,3,5,…），
# F2C RP_Snake 的奇数轮是降序回扫（0,2,4,…,20,19,17,…,3,1）——同轮内多一次长回跳，
# 不是同一条路线。按名字硬配上去，等于把上一轮那个 −38.11% 换了个地方重犯。
OURS_ROUTE_ALGORITHMS = {
    "boustrophedon": BoustrophedonOrder,
}


def _route_for(route_algorithm: str):
    factory = OURS_ROUTE_ALGORITHMS.get(route_algorithm)
    if factory is None:
        raise RouteAlgorithmMismatchError(
            f"我方没有 route_algorithm={route_algorithm!r} 的对应实现；"
            f"可用：{sorted(OURS_ROUTE_ALGORITHMS)}。"
            "不得以名字相近的实现顶替：skip_one_order 与 F2C RP_Snake 的回扫方向不同。"
        )
    return factory()


def compute_ours_detail(request: F2CRequest) -> dict[str, float]:
    """返回全部候选口径的量，供比对脚本裁决语义假设。"""
    polygon = shapely.from_wkt(request.field_wkt)
    if polygon.geom_type != "Polygon":
        raise ValueError("对账复算当前只接受单 Polygon WKT")
    field_spec = polygon_to_spec(polygon, "f2c-cross-check")
    problem = CoverageProblem(problem_id="f2c-cross-check", field=field_spec)
    vehicle = VehicleSpec(
        working_width_m=request.working_width_m,
        body_width_m=request.robot_width_m,
        min_turning_radius_m=request.min_turning_radius_m,
    )
    cells = CellsArtifact(cells=(field_spec,))
    headland = UniformHeadland(request.headland_width_m).run(cells)
    main_parts = tuple(polygon_from_spec(part) for part in headland.cells[0].main_field)
    scale = max(polygon.bounds[2] - polygon.bounds[0], polygon.bounds[3] - polygon.bounds[1], 1.0)
    main = robust_union(main_parts, scale_hint=scale)

    swaths = FixedAngleSwath(request.swath_angle_rad).run(
        headland.cells[0].main_field, working_width_m=request.working_width_m, problem=problem
    )
    route = _route_for(request.route_algorithm).run(swaths)
    path = DubinsTransit(0.25).run(route, vehicle)

    # 转移五项分解：只有总数查不出超额出在哪一项（G-A.2）。
    # 这里是单 cell 对账链路，cell_of_work_index 传 None 即事实陈述。
    breakdown = transit_breakdown(path, cell_of_work_index=None)
    return {
        "path_length": sum(line_from_spec(segment.line).length for segment in path.segments),
        "swath_count": float(len(swaths.swaths)),
        "swath_length_sum": sum(line_from_spec(swath.centerline).length for swath in swaths.swaths),
        "main_field_area": main.area,
        "field_area": polygon.area,
        "headland_ring_area": polygon.area - main.area,
        "transit_entry_leg_m": breakdown.entry_leg_m,
        "transit_turn_total_m": breakdown.turn_total_m,
        "transit_turn_count": float(breakdown.turn_count),
        "transit_inter_cell_m": breakdown.inter_cell_m,
        "transit_exit_leg_m": breakdown.exit_leg_m,
        "transit_other_m": breakdown.other_m,
        "transit_mean_turn_m": breakdown.mean_turn_m,
        "transit_inter_cell_count": float(breakdown.inter_cell_count),
    }


def compute_ours(request: F2CRequest) -> F2CResult:
    detail = compute_ours_detail(request)
    return F2CResult(
        request_id=request.request_id,
        path_length=detail["path_length"],
        swath_count=detail["swath_count"],
        swath_length_sum=detail["swath_length_sum"],
        main_field_area=detail["main_field_area"],
        transit_entry_leg_m=detail["transit_entry_leg_m"],
        transit_turn_total_m=detail["transit_turn_total_m"],
        transit_turn_count=detail["transit_turn_count"],
        transit_inter_cell_m=detail["transit_inter_cell_m"],
        transit_exit_leg_m=detail["transit_exit_leg_m"],
        transit_other_m=detail["transit_other_m"],
        # 我方复算全程在请求给的坐标里做，不再投影——如实回报同一个 CRS 与实际用的路线算法。
        working_crs=request.working_crs,
        route_algorithm=request.route_algorithm,
    )
