"""可行性与指标全部由最终路径几何重算，不采信规划器自报值。"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict
from shapely.geometry import GeometryCollection

from agriautolab.contracts.artifacts import HeadlandArtifact, PathArtifact
from agriautolab.contracts.enums import RunStatus
from agriautolab.contracts.problem import CoverageProblem
from agriautolab.contracts.vehicle import VehicleSpec
from agriautolab.geometry.kernel import FieldGeometry
from agriautolab.geometry.robust import robust_union
from agriautolab.geometry.validate import line_from_spec, polygon_from_spec
from agriautolab.pipeline.metrics.constraints import collision_area, max_abs_declared_curvature, outside_area
from agriautolab.pipeline.metrics.coverage import (
    coverage_stats, eta_l, l_area, nonwork_normalized, path_length_breakdown,
    path_work_lines, resolve_coverage_targets, swath_count, turning_overhead_ratio,
)
from agriautolab.pipeline.metrics.path import (
    aol, cusp_count, headland_turn_count, path_length, row_crossings,
    total_heading_change, tortuosity, transit_length,
)

if TYPE_CHECKING:
    from agriautolab.contracts.protocol import BenchmarkProtocol


class MetricValue(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    metric_id: str
    value: float


class ValidationResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    status: RunStatus
    failure_reason: str | None = None
    metrics: tuple[MetricValue, ...] = ()

    def metric(self, metric_id: str) -> float:
        for item in self.metrics:
            if item.metric_id == metric_id:
                return item.value
        raise KeyError(metric_id)


def _flatten_path(path: PathArtifact) -> tuple:
    if not path.segments:
        return ()
    points = list(path.segments[0].line.points)
    for segment in path.segments[1:]:
        points.extend(segment.line.points[1:])
    return tuple(points)


class PathValidator:
    def validate(
        self,
        problem: CoverageProblem,
        robot: VehicleSpec,
        path: PathArtifact,
        protocol: BenchmarkProtocol,
        *,
        headland: HeadlandArtifact | None = None,
        headland_width_m: float | None = None,
    ) -> ValidationResult:
        """headland 传的是地头阶段的产物，不是任意几何：分母只能来自阶段输出，或者 None 表示没跑地头。

        产物本身不携带宽度，所以传了 headland 就需同时传 headland_width_m，
        否则分母 provenance 缺少地头配置、事后无法对账。
        """
        if not path.segments:
            return ValidationResult(status=RunStatus.INFEASIBLE, failure_reason="validator_rejected:empty_path")

        for previous, current in zip(path.segments, path.segments[1:]):
            if previous.line.points[-1] != current.line.points[0]:
                return ValidationResult(
                    status=RunStatus.CONSTRAINT_VIOLATION,
                    failure_reason="validator_rejected:discontinuous_endpoints",
                )

        field_geometry = FieldGeometry.from_problem(problem, robot)
        scale_hint = max(
            field_geometry.field.bounds[2] - field_geometry.field.bounds[0],
            field_geometry.field.bounds[3] - field_geometry.field.bounds[1],
            1.0,
        )
        obstacles = tuple(
            polygon_from_spec(spec)
            for spec in sorted(problem.obstacles, key=lambda item: item.geometry_id)
        )
        obstacle_union = robust_union(obstacles, scale_hint=scale_hint) if obstacles else GeometryCollection()

        # 校验逐段执行，避免整条路径并集把局部碰撞的位置证据抹掉。
        for segment in path.segments:
            segment_path = PathArtifact(segments=(segment,))
            if collision_area(segment_path, obstacle_union, body_width_m=robot.body_width_m, scale_hint=scale_hint) > protocol.area_epsilon_m2:
                return ValidationResult(status=RunStatus.COLLISION, failure_reason="validator_rejected:collision")

        # 可原地转向的车没有曲率上界；这里需先分支，否则 1/0 会把校验器本身炸掉。
        curvature_limit = math.inf if robot.can_turn_in_place else 1.0 / robot.min_turning_radius_m
        if max_abs_declared_curvature(path) > curvature_limit * (1.0 + 1e-12):
            return ValidationResult(
                status=RunStatus.INFEASIBLE_KINEMATICS,
                failure_reason="validator_rejected:curvature_limit",
            )

        # 倒车段只属于可倒车机具：Reeds-Shepp 路径含 reversing 段，纯前向车辆
        # （can_reverse=False）开着它物理上不成立，需在门口拒绝而不是假装可行。
        if any(segment.reversing for segment in path.segments) and not robot.can_reverse:
            return ValidationResult(
                status=RunStatus.INFEASIBLE_KINEMATICS,
                failure_reason="validator_rejected:reverse_without_gear",
            )

        outside = outside_area(path, field_geometry.field, body_width_m=robot.body_width_m, scale_hint=scale_hint)
        if outside > protocol.area_epsilon_m2:
            return ValidationResult(
                status=RunStatus.CONSTRAINT_VIOLATION,
                failure_reason="validator_rejected:outside_area",
            )

        forbidden = tuple(
            polygon_from_spec(spec)
            for spec in sorted(problem.forbidden_crossing_zones, key=lambda item: item.geometry_id)
        )
        if forbidden:
            forbidden_union = robust_union(forbidden, scale_hint=scale_hint)
            for segment in path.segments:
                if line_from_spec(segment.line).crosses(forbidden_union):
                    return ValidationResult(
                        status=RunStatus.CONSTRAINT_VIOLATION,
                        failure_reason="validator_rejected:forbidden_crossing",
                    )

        work_lines = path_work_lines(path)
        targets = resolve_coverage_targets(
            problem,
            headland,
            target=protocol.coverage_target,
            headland_width_m=headland_width_m,
        )
        stats = coverage_stats(work_lines, working_width_m=robot.working_width_m, targets=targets)
        # 硬门槛只认对原田的覆盖率。用主田做门槛的话，把地头开宽就能无损通过：
        # 地头 18 米时对主田是 1.0000，对原田只有 0.1792。
        if stats.coverage_ratio_field + 1e-12 < protocol.coverage_threshold:
            return ValidationResult(
                status=RunStatus.CONSTRAINT_VIOLATION,
                failure_reason="validator_rejected:coverage_threshold",
            )

        points = _flatten_path(path)
        work_area_m2 = targets.original_field.area
        metrics = (
            MetricValue(metric_id="coverage_ratio_field", value=stats.coverage_ratio_field),
            MetricValue(metric_id="coverage_ratio_main", value=stats.coverage_ratio_main),
            MetricValue(metric_id="overlap_ratio", value=stats.overlap_ratio),
            MetricValue(
                metric_id="nonwork_normalized",
                value=nonwork_normalized(path, working_width_m=robot.working_width_m, work_area_m2=work_area_m2),
            ),
            MetricValue(metric_id="outside_area", value=outside),
            MetricValue(metric_id="collision_area", value=0.0),
            MetricValue(metric_id="L_R", value=path_length_breakdown(path).total_m),
            MetricValue(metric_id="L_area", value=l_area(path, working_width_m=robot.working_width_m, work_area_m2=work_area_m2)),
            MetricValue(metric_id="eta_L", value=eta_l(path)),
            MetricValue(metric_id="turning_overhead_ratio", value=turning_overhead_ratio(path)),
            MetricValue(metric_id="swath_count", value=float(swath_count(path))),
            MetricValue(metric_id="path_length", value=path_length(points)),
            MetricValue(metric_id="transit_length", value=transit_length(path)),
            MetricValue(metric_id="headland_turn_count", value=float(headland_turn_count(path))),
            MetricValue(metric_id="row_crossings", value=row_crossings(path, problem.row_structure)),
            MetricValue(metric_id="total_heading_change", value=total_heading_change(points)),
            MetricValue(metric_id="aol", value=aol(points)),
            MetricValue(metric_id="tortuosity", value=tortuosity(points)),
            MetricValue(metric_id="cusp_count", value=float(cusp_count(points))),
        )
        if not all(math.isfinite(item.value) for item in metrics if item.metric_id != "tortuosity"):
            return ValidationResult(status=RunStatus.NUMERICAL_ERROR, failure_reason="validator_rejected:nonfinite_metric")
        return ValidationResult(status=RunStatus.OK, metrics=metrics)
