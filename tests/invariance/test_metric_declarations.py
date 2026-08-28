"""变换断言由 MetricSpec 声明生成，而不是人工挑选不变性算例——新增指标忘了给算法会直接失败。"""

import math

import pytest
from shapely import LineString, box
from shapely.affinity import rotate as shp_rotate
from shapely.affinity import scale as shp_scale
from shapely.affinity import translate as shp_translate

from conftest import targets_from_geometry

from agriautolab.contracts.artifacts import PathArtifact, PathSegment
from agriautolab.contracts.enums import PathSegmentKind, ScaleBehavior
from agriautolab.contracts.geometry import LineStringSpec, Point
from agriautolab.pipeline.metrics.constraints import collision_area, outside_area
from agriautolab.pipeline.metrics.coverage import (
    coverage_stats, eta_l, headland_area_ratio, l_area, nonwork_normalized,
    path_length_breakdown, swath_count, turning_overhead_ratio,
)
from agriautolab.pipeline.metrics.path import (
    aol, cusp_count, headland_turn_count, median_clearance, min_clearance, path_length,
    row_crossings, total_heading_change, tortuosity, transit_length,
)
from agriautolab.pipeline.metrics.registry import METRIC_REGISTRY


def _transform_point(point: Point, *, theta: float, scale: float, tx: float, ty: float) -> Point:
    x = point.x * scale
    y = point.y * scale
    return Point(
        x=x * math.cos(theta) - y * math.sin(theta) + tx,
        y=x * math.sin(theta) + y * math.cos(theta) + ty,
    )


def _transform_points(points: tuple[Point, ...], *, theta: float, scale: float, tx: float, ty: float) -> tuple[Point, ...]:
    return tuple(_transform_point(point, theta=theta, scale=scale, tx=tx, ty=ty) for point in points)


def _transform_geometry(geometry, *, theta: float, scale: float, tx: float, ty: float):
    transformed = shp_scale(geometry, xfact=scale, yfact=scale, origin=(0.0, 0.0))
    transformed = shp_rotate(transformed, theta, origin=(0.0, 0.0), use_radians=True)
    return shp_translate(transformed, xoff=tx, yoff=ty)


def _path_artifact(theta: float, scale: float, tx: float, ty: float) -> PathArtifact:
    work = _transform_points((Point(x=0, y=3), Point(x=20, y=3)), theta=theta, scale=scale, tx=tx, ty=ty)
    turn = _transform_points((Point(x=20, y=3), Point(x=20, y=8)), theta=theta, scale=scale, tx=tx, ty=ty)
    return PathArtifact(segments=(
        PathSegment(segment_id="work", kind=PathSegmentKind.WORK,
                    line=LineStringSpec(geometry_id="work", points=work), signed_curvature_m_inv=0.0),
        PathSegment(segment_id="turn", kind=PathSegmentKind.TURN,
                    line=LineStringSpec(geometry_id="turn", points=turn), signed_curvature_m_inv=0.0),
    ))


def _evaluate(metric_id: str, *, theta: float = 0.0, scale: float = 1.0, tx: float = 0.0, ty: float = 0.0) -> float:
    """按注册表里的 metric_id 求值。新增指标需在这里给出算法，否则最后一行会直接失败。"""
    base_points = (
        Point(x=0.0, y=0.0),
        Point(x=4.0, y=0.0),
        Point(x=4.0, y=3.0),
        Point(x=10.0, y=3.0),
    )
    points = _transform_points(base_points, theta=theta, scale=scale, tx=tx, ty=ty)
    path_functions = {
        "path_length": path_length,
        "total_heading_change": total_heading_change,
        "aol": aol,
        "tortuosity": tortuosity,
        "cusp_count": lambda value: float(cusp_count(value)),
    }
    if metric_id in path_functions:
        return path_functions[metric_id](points)

    field_region = _transform_geometry(box(0.0, 0.0, 20.0, 10.0), theta=theta, scale=scale, tx=tx, ty=ty)
    lines = tuple(
        _transform_geometry(LineString([(0.0, y), (20.0, y)]), theta=theta, scale=scale, tx=tx, ty=ty)
        for y in (3.0, 7.0)
    )
    if metric_id in {"coverage_ratio_field", "coverage_ratio_main", "overlap_ratio"}:
        # 没跑地头阶段，主田即原田；两个比值在这里需给出同一个数，
        # 否则说明分母解析器在无地头时凭空造出了第二个域。
        stats = coverage_stats(lines, working_width_m=6.0 * scale, targets=targets_from_geometry(field_region))
        if metric_id == "coverage_ratio_field":
            return stats.coverage_ratio_field
        if metric_id == "coverage_ratio_main":
            return stats.coverage_ratio_main
        return stats.overlap_ratio

    if metric_id in {"nonwork_normalized", "L_R", "L_area", "eta_L", "turning_overhead_ratio", "swath_count",
                     "transit_length", "headland_turn_count", "row_crossings"}:
        artifact = _path_artifact(theta, scale, tx, ty)
        if metric_id == "nonwork_normalized":
            return nonwork_normalized(artifact, working_width_m=6.0 * scale, work_area_m2=field_region.area)
        if metric_id == "L_R":
            return path_length_breakdown(artifact).total_m
        if metric_id == "L_area":
            return l_area(artifact, working_width_m=6.0 * scale, work_area_m2=field_region.area)
        if metric_id == "eta_L":
            return eta_l(artifact)
        if metric_id == "turning_overhead_ratio":
            return turning_overhead_ratio(artifact)
        if metric_id == "transit_length":
            return transit_length(artifact)
        if metric_id == "headland_turn_count":
            return float(headland_turn_count(artifact))
        if metric_id == "row_crossings":
            # 本夹具的 problem 不带行结构：无行可穿，恒为 0；非零情形由 row_structure 契约测试覆盖
            return row_crossings(artifact, None)
        return float(swath_count(artifact))

    if metric_id == "headland_area_ratio":
        main = _transform_geometry(box(2.0, 2.0, 18.0, 8.0), theta=theta, scale=scale, tx=tx, ty=ty)
        headland = field_region.difference(main)
        return headland_area_ratio(main, headland)

    single_line = _transform_points((Point(x=0, y=0), Point(x=20, y=0)), theta=theta, scale=scale, tx=tx, ty=ty)
    artifact = PathArtifact(segments=(PathSegment(
        segment_id="body",
        kind=PathSegmentKind.TRANSIT,
        line=LineStringSpec(geometry_id="body", points=single_line),
        signed_curvature_m_inv=0.0,
    ),))
    scale_hint = 20.0 * scale
    if metric_id == "outside_area":
        return outside_area(artifact, field_region, body_width_m=2.0 * scale, scale_hint=scale_hint)
    if metric_id == "collision_area":
        obstacle = _transform_geometry(box(8.0, -2.0, 12.0, 2.0), theta=theta, scale=scale, tx=tx, ty=ty)
        return collision_area(artifact, obstacle, body_width_m=2.0 * scale, scale_hint=scale_hint)
    if metric_id in {"min_clearance", "median_clearance"}:
        obstacle = _transform_geometry(box(5.0, 8.0, 8.0, 12.0), theta=theta, scale=scale, tx=tx, ty=ty)
        if metric_id == "min_clearance":
            return min_clearance(points, obstacle)
        return median_clearance(points, obstacle, sample_step=0.25 * scale)
    raise AssertionError(f"测试未覆盖注册指标 {metric_id}")


_ROTATION_CASES = (0.0, 0.3, math.pi / 4.0, 1.9, math.pi, 5.5)


@pytest.mark.parametrize("metric_id", tuple(METRIC_REGISTRY))
@pytest.mark.parametrize("theta", _ROTATION_CASES)
def test_rotation_invariance_generated_from_registry(metric_id: str, theta: float) -> None:
    spec = METRIC_REGISTRY[metric_id]
    if not spec.rotation_invariant:
        pytest.skip("MetricSpec 未声明旋转不变")
    baseline = _evaluate(metric_id)
    transformed = _evaluate(metric_id, theta=theta, tx=13.7, ty=-9.2)
    assert transformed == pytest.approx(baseline, rel=1e-9, abs=1e-12)


@pytest.mark.parametrize("metric_id", tuple(METRIC_REGISTRY))
@pytest.mark.parametrize("scale", (0.2, 0.7, 3.0, 11.0))
def test_scale_behavior_generated_from_registry(metric_id: str, scale: float) -> None:
    spec = METRIC_REGISTRY[metric_id]
    if spec.scale_behavior is ScaleBehavior.UNDEFINED:
        pytest.skip("MetricSpec 未声明尺度规律")
    baseline = _evaluate(metric_id)
    transformed = _evaluate(metric_id, scale=scale)
    factors = {
        ScaleBehavior.INVARIANT: 1.0,
        ScaleBehavior.LINEAR: scale,
        ScaleBehavior.QUADRATIC: scale * scale,
        ScaleBehavior.INVERSE_LINEAR: 1.0 / scale,
    }
    assert transformed == pytest.approx(baseline * factors[spec.scale_behavior], rel=1e-9, abs=1e-12)
