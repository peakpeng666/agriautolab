"""三维超体积：参考点锁死在协议里，精确计算，不用蒙特卡洛。

参考点是覆盖率分母问题的同构物：浮动的参考点 = 浮动的分母。
若参考点取自「观测到的最差值」，换一个算法池，同一前沿的超体积就变了，
跨池不可比——Dolan-Moré 性能剖面在 solver 集合变化下不稳定是同一个病。
所以 HypervolumeReference 由 BenchmarkProtocol 必填声明（进入 spec_hash），
由解析上界导出（见 analytic_reference），绝不从观测数据取。
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Mapping

from agriautolab.contracts.problem import CoverageProblem
from agriautolab.contracts.protocol import HypervolumeReference
from agriautolab.contracts.vehicle import VehicleSpec
from agriautolab.geometry.robust import robust_union
from agriautolab.geometry.validate import polygon_from_spec, validate_obstacles_within_field
from agriautolab.pareto.front import ConfigId, ObjectiveVector, pareto_front, pool_hash

_Box = tuple[float, float, float, float, float, float]


def _boxes(points: Mapping[ConfigId, ObjectiveVector], reference: HypervolumeReference) -> tuple[_Box, ...]:
    """每个前沿点张成一个 [p, reference] 的闭箱（最小化：参考点是「最差角」）。"""
    return tuple(
        (vector.path_length, reference.path_length,
         vector.headland_turns, reference.headland_turns,
         vector.row_crossings, reference.row_crossings)
        for vector in points.values()
    )


def beyond_reference(points: Mapping[ConfigId, ObjectiveVector], *, reference: HypervolumeReference) -> frozenset[ConfigId]:
    """任一目标达到或超过参考点的解：超体积贡献记 0 且必须显式标记，不许静默截断。"""
    return frozenset(
        config_id
        for config_id, vector in points.items()
        if vector.path_length >= reference.path_length
        or vector.headland_turns >= reference.headland_turns
        or vector.row_crossings >= reference.row_crossings
    )


def _union_area_2d(rectangles: tuple[tuple[float, float, float, float], ...]) -> float:
    """矩形并集面积：y 坐标压缩 + 每 y 带内 z 区间求并。"""
    ys = sorted({y for rect in rectangles for y in (rect[0], rect[1])})
    area = 0.0
    for y_low, y_high in zip(ys, ys[1:]):
        y_mid = (y_low + y_high) / 2.0
        intervals = sorted(
            (rect[2], rect[3]) for rect in rectangles if rect[0] <= y_mid <= rect[1]
        )
        covered = 0.0
        current_low, current_high = None, None
        for low, high in intervals:
            if current_high is None or low > current_high:
                if current_high is not None:
                    covered += current_high - current_low
                current_low, current_high = low, high
            else:
                current_high = max(current_high, high)
        if current_high is not None:
            covered += current_high - current_low
        area += (y_high - y_low) * covered
    return area


def hypervolume(points: Mapping[ConfigId, ObjectiveVector], *, reference: HypervolumeReference) -> float:
    """前沿相对参考点的精确超体积（三目标，全部最小化）。

    越过参考点的解贡献 0（箱退化为空）；调用方必须同时记录
    beyond_reference 的标记集，否则就是静默截断。
    x 扫掠 + 2D 压缩求并，对前沿规模（<= 池大小）精确且确定性。
    """
    boxes = tuple(
        box for box in _boxes(points, reference)
        if box[0] < box[1] and box[2] < box[3] and box[4] < box[5]
    )
    if not boxes:
        return 0.0
    xs = sorted({x for box in boxes for x in (box[0], box[1])})
    volume = 0.0
    for x_low, x_high in zip(xs, xs[1:]):
        x_mid = (x_low + x_high) / 2.0
        slab = tuple(
            (box[2], box[3], box[4], box[5]) for box in boxes if box[0] <= x_mid <= box[1]
        )
        volume += (x_high - x_low) * _union_area_2d(slab)
    return volume


@dataclass(frozen=True)
class FrontEvaluation:
    """一次前沿评估的全部可对账量：前沿成员、超体积、越界标记、池身份。"""

    pool_hash: str
    front: frozenset[ConfigId]
    hypervolume: float
    beyond_reference: frozenset[ConfigId]

    def __post_init__(self) -> None:
        if not self.beyond_reference.isdisjoint(self.front):
            raise ValueError("越过参考点的解不能同时在前沿里：先剔除再评估")


def evaluate_front(
    points: Mapping[ConfigId, ObjectiveVector],
    *,
    reference: HypervolumeReference,
    rtol: float = 1e-12,
) -> FrontEvaluation:
    """前沿评估的统一入口：越界解先剔除（并留下标记），再算前沿与超体积。"""
    beyond = beyond_reference(points, reference=reference)
    admissible = {key: value for key, value in points.items() if key not in beyond}
    return FrontEvaluation(
        pool_hash=pool_hash(points.keys()),
        front=pareto_front(admissible, rtol=rtol) if admissible else frozenset(),
        hypervolume=hypervolume(admissible, reference=reference) if admissible else 0.0,
        beyond_reference=beyond,
    )


def _components(free):
    if free.geom_type == "Polygon":
        return (free,)
    return tuple(part for part in free.geoms if part.geom_type == "Polygon" and not part.is_empty)


def analytic_reference(problem: CoverageProblem, vehicle: VehicleSpec) -> HypervolumeReference:
    """由问题与机具解析推导的参考点上界，basis 记录公式，随协议进入哈希。

    - path_length 上界 = 2·(可作业区面积/幅宽) + n^2·(地块直径 + pi·R)：
      第一项是作业里程的两倍余量，第二项假设每段之间都发生一次
      「跨整个地块直径再加半圆掉头」的最坏转移（n 段最多 n^2 个有序对）。
    - headland_turns 上界 = n：每段最多一次进入，转移数不超过段数。
    - row_crossings 上界 = path_length 上界 / 行距（全程垂直于行的穿行密度）；
      无行结构时该维恒为 0，上界取 1（保持三维体积非退化）。
    上界只要求「解析、稳定、支配一切可行解」，不追求紧——紧的参考点
    只会让超体积对数值噪声更敏感。
    """
    from agriautolab.algorithms.swath.min_width import min_width_direction, swath_count_at_direction

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

    swath_count = sum(
        swath_count_at_direction(component, *min_width_direction(component), vehicle.working_width_m)
        for component in components
    )
    hull_points = list(free.convex_hull.exterior.coords)
    diameter = max(
        math.dist(p, q) for i, p in enumerate(hull_points) for q in hull_points[i + 1:]
    )
    radius = max(vehicle.min_turning_radius_m, 0.0)
    path_cap = 2.0 * free.area / vehicle.working_width_m + (swath_count * swath_count) * (diameter + math.pi * radius)
    turns_cap = float(max(swath_count, 1))
    if problem.row_structure is None:
        crossings_cap = 1.0
        crossings_basis = "no_rows(=1)"
    else:
        crossings_cap = path_cap / problem.row_structure.spacing_m
        crossings_basis = "path_cap/spacing"

    return HypervolumeReference(
        path_length=path_cap,
        headland_turns=turns_cap,
        row_crossings=crossings_cap,
        basis=(
            "analytic: path=2A/w+n^2(D+piR) "
            f"(A={free.area!r}, w={vehicle.working_width_m!r}, n={swath_count}, D={diameter!r}, R={radius!r}); "
            f"turns=n; crossings={crossings_basis}"
        ),
    )
