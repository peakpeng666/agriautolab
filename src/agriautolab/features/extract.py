"""实例特征提取：农业几何难度量，全部解析、确定性、带提取耗时。

耗时与数值一起返回（ASlib 的 feature_costs）：若提取一个特征比跑满整个
算法池还慢，推荐器就没有存在意义——这个数必须能被读者看到，
而不是埋在实现里。
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field

from shapely.geometry.base import BaseGeometry

from agriautolab.algorithms.swath.min_width import min_width_direction, swath_count_at_direction
from agriautolab.algorithms.swath.principal_axis import principal_axis
from agriautolab.contracts.problem import CoverageProblem
from agriautolab.contracts.vehicle import VehicleSpec
from agriautolab.geometry.robust import robust_union
from agriautolab.geometry.validate import polygon_from_spec, validate_obstacles_within_field


@dataclass(frozen=True)
class InstanceFeatures:
    values: dict[str, float]
    elapsed_s: dict[str, float] = field(default_factory=dict)


def _ring_orientation(ring) -> float:
    """标准 shoelace 定向：CCW 为 +1。洞环按惯例为 CW，但不依赖惯例，按实测定向。"""
    coords = list(ring.coords)
    signed = sum(
        coords[i][0] * coords[i + 1][1] - coords[i + 1][0] * coords[i][1]
        for i in range(len(coords) - 1)
    )
    return 1.0 if signed > 0.0 else -1.0


def reflex_vertex_count(polygon) -> int:
    """自由空间边界上内角 > pi 的顶点数（外环与洞环分开判向）。

    外环：与环方向相反的转角是反曲；洞环（障碍角点）恰好相反——
    障碍的凸角在自由空间里是 270 度反曲角。判据用环自身的带号面积定向，
    不依赖 shapely 的存储朝向。
    """
    count = 0
    rings = [(polygon.exterior, True)] + [(ring, False) for ring in polygon.interiors]
    for ring, is_exterior in rings:
        orientation = _ring_orientation(ring)
        coords = list(ring.coords)[:-1]
        for index in range(len(coords)):
            prev_point = coords[index - 1]
            current = coords[index]
            nxt = coords[(index + 1) % len(coords)]
            cross = (current[0] - prev_point[0]) * (nxt[1] - current[1]) - \
                    (current[1] - prev_point[1]) * (nxt[0] - current[0])
            product = cross * orientation
            if (is_exterior and product < 0.0) or (not is_exterior and product > 0.0):
                count += 1
    return count


def _components(free: BaseGeometry):
    if free.geom_type == "Polygon":
        return (free,)
    return tuple(part for part in free.geoms if part.geom_type == "Polygon" and not part.is_empty)


def extract_instance_features(problem: CoverageProblem, vehicle: VehicleSpec, *, clock=time.perf_counter) -> InstanceFeatures:
    """提取 10 个实例特征与各自耗时。row_structure 为 None 时 row_angle_vs_principal 缺席。"""
    field = polygon_from_spec(problem.field)
    obstacle_items = tuple(
        (spec.geometry_id, polygon_from_spec(spec))
        for spec in sorted(problem.obstacles, key=lambda item: item.geometry_id)
    )
    validate_obstacles_within_field(field, obstacle_items)
    scale_hint = max(field.bounds[2] - field.bounds[0], field.bounds[3] - field.bounds[1], 1.0)
    obstacle_union = robust_union(tuple(item[1] for item in obstacle_items), scale_hint=scale_hint)
    free = field.difference(obstacle_union)
    components = _components(free)
    hull_area = free.convex_hull.area

    values: dict[str, float] = {}
    elapsed: dict[str, float] = {}

    def record(name: str, compute) -> None:
        started = clock()
        values[name] = compute()
        elapsed[name] = clock() - started

    record("area_m2", lambda: free.area)
    record("perimeter_area_ratio", lambda: free.length / math.sqrt(free.area))
    record("convexity_deficiency", lambda: 1.0 - free.area / hull_area)
    record("elongation", lambda: _elongation(free))
    record("reflex_vertex_count", lambda: float(sum(reflex_vertex_count(c) for c in components)))
    record("obstacle_count", lambda: float(len(problem.obstacles)))
    record("obstacle_area_ratio", lambda: obstacle_union.area / field.area)
    if problem.row_structure is not None:
        record("row_angle_vs_principal", lambda: _row_angle_vs_principal(free, problem.row_structure.direction_rad))
        # 行距可见性（2026-08-21 可辨识性缺口整改）：row_crossings 与 1/spacing 成比例、
        # 最优配置随行距移动，而旧特征集对 spacing 完全盲——仅差行距的两个实例特征相同、
        # 标签可能不同，推荐器学到的是欠定映射。
        record("crossing_density", lambda: math.sqrt(free.area) / problem.row_structure.spacing_m)
        record("spacing_to_width_ratio", lambda: problem.row_structure.spacing_m / vehicle.working_width_m)
    record("turning_ratio", lambda: vehicle.min_turning_radius_m / vehicle.working_width_m)
    record("swath_count_at_minwidth", lambda: float(sum(
        swath_count_at_direction(c, *min_width_direction(c), vehicle.working_width_m) for c in components
    )))
    return InstanceFeatures(values=values, elapsed_s=elapsed)


def _elongation(free: BaseGeometry) -> float:
    rectangle = free.minimum_rotated_rectangle
    coords = list(rectangle.exterior.coords)
    edge_lengths = [
        math.hypot(end[0] - start[0], end[1] - start[1])
        for start, end in zip(coords, coords[1:] + coords[:1])
    ]
    # 带洞几何的 MBR 顶点可能出现重复点，零长边必须剔除（长宽比除以 0 没有意义）
    positive = [length for length in edge_lengths if length > 1e-12]
    if not positive:
        return 1.0
    return max(positive) / min(positive)


def _row_angle_vs_principal(free: BaseGeometry, direction_rad: float) -> float:
    """行方向与 PCA 主轴的夹角，折到 [0, pi/2]。

    最重要的一个特征：它量化「顺行」与「顺形状」的冲突程度——
    实测目标空间的第二维（crossings）正是从这个冲突里长出来的。
    """
    principal = principal_axis(free if free.geom_type == "Polygon" else free.convex_hull)
    principal_angle = math.atan2(principal[1], principal[0])
    delta = abs(direction_rad - principal_angle) % math.pi
    return min(delta, math.pi - delta)
