"""所有田块域在这里一次性导出，指标就没有机会把不同域的分子和分母凑到一起。

主田与地头环带不在这里算：全仓库唯一的减地头路径是
metrics.coverage.resolve_coverage_targets。确实需要地头环带几何时，
从 CoverageTargets 派生 original_field.difference(main_field)，不要再算第二遍——
两份独立的内偏置实现在非凸地块上会分家（反曲顶点的圆角化程度不同，
round 与 mitre 在 100x50 缺 40x30 角的 L 形上相差约 0.4%，而矩形上完全一致）。
"""

from __future__ import annotations

from dataclasses import dataclass

from shapely.geometry.base import BaseGeometry

from agriautolab.contracts.problem import CoverageProblem
from agriautolab.contracts.vehicle import VehicleSpec
from agriautolab.geometry.footprint import QUAD_SEGS
from agriautolab.geometry.robust import robust_union
from agriautolab.geometry.validate import polygon_from_spec, validate_obstacles_within_field


@dataclass(frozen=True)
class FieldGeometry:
    field: BaseGeometry
    raw_free: BaseGeometry
    center_free: BaseGeometry
    reachable: BaseGeometry

    @classmethod
    def from_problem(cls, problem: CoverageProblem, robot: VehicleSpec) -> "FieldGeometry":
        field = polygon_from_spec(problem.field)
        obstacle_items = tuple(
            (spec.geometry_id, polygon_from_spec(spec))
            for spec in sorted(problem.obstacles, key=lambda item: item.geometry_id)
        )
        validate_obstacles_within_field(field, obstacle_items)
        scale_hint = max(field.bounds[2] - field.bounds[0], field.bounds[3] - field.bounds[1], 1.0)
        obstacle_union = robust_union(tuple(item[1] for item in obstacle_items), scale_hint=scale_hint)
        raw_free = field.difference(obstacle_union)
        center_free = raw_free.buffer(
            -robot.body_width_m / 2.0,
            cap_style="round",
            join_style="round",
            quad_segs=QUAD_SEGS,
        )
        return cls(
            field=field,
            raw_free=raw_free,
            center_free=center_free,
            reachable=center_free,
        )
