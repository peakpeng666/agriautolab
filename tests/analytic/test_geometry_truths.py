"""几何原语钉在能手算的解析面积上，而不是看图觉得对。"""

import math

import pytest
from shapely import LineString, Point, box

from agriautolab.geometry.footprint import QUAD_SEGS
from agriautolab.metrics.coverage import coverage_stats


def test_five_width10_swaths_cover_rectangle_exactly(coverage_targets) -> None:
    field = box(0.0, 0.0, 100.0, 50.0)
    lines = tuple(LineString([(0.0, y), (100.0, y)]) for y in (5.0, 15.0, 25.0, 35.0, 45.0))
    stats = coverage_stats(lines, working_width_m=10.0, targets=coverage_targets(field))
    assert stats.coverage_ratio_field == pytest.approx(1.0, abs=1e-9)
    assert stats.overlap_ratio == pytest.approx(0.0, abs=1e-9)
    assert stats.missed_ratio == pytest.approx(0.0, abs=1e-9)


def test_width12_clamped_final_swath_has_overlap_point2(coverage_targets) -> None:
    field = box(0.0, 0.0, 100.0, 50.0)
    lines = tuple(LineString([(0.0, y), (100.0, y)]) for y in (6.0, 18.0, 30.0, 42.0, 44.0))
    stats = coverage_stats(lines, working_width_m=12.0, targets=coverage_targets(field))
    assert stats.coverage_ratio_field == pytest.approx(1.0, abs=1e-9)
    assert stats.overlap_area_m2 == pytest.approx(1000.0, abs=1e-9)
    assert stats.overlap_ratio == pytest.approx(0.2, abs=1e-9)


@pytest.mark.parametrize("radius", [0.5, 1.0, 3.0, 10.0])
def test_circle_buffer_matches_inscribed_polygon(radius: float) -> None:
    disk = Point(0.0, 0.0).buffer(radius, quad_segs=QUAD_SEGS, cap_style="round", join_style="round")
    n = 4 * QUAD_SEGS
    expected = 0.5 * n * radius * radius * math.sin(2.0 * math.pi / n)
    assert disk.area == pytest.approx(expected, rel=1e-12)


@pytest.mark.parametrize("width,height,radius", [(100.0, 50.0, 2.0), (20.0, 10.0, 1.0), (7.0, 5.0, 0.5)])
def test_erode_then_dilate_rectangle_area(width: float, height: float, radius: float) -> None:
    rectangle = box(0.0, 0.0, width, height)
    eroded = rectangle.buffer(-radius, quad_segs=QUAD_SEGS, cap_style="round", join_style="round")
    restored = eroded.buffer(radius, quad_segs=QUAD_SEGS, cap_style="round", join_style="round")
    n = 4 * QUAD_SEGS
    pi_discrete = 0.5 * n * math.sin(2.0 * math.pi / n)
    expected = width * height - radius * radius * (4.0 - pi_discrete)
    assert restored.area == pytest.approx(expected, rel=1e-12)


def test_primary_metric_algebra_identity_on_saturated_width12_case(coverage_targets) -> None:
    from agriautolab.contracts.artifacts import PathArtifact, PathSegment
    from agriautolab.contracts.enums import PathSegmentKind
    from agriautolab.contracts.geometry import LineStringSpec, Point as ContractPoint
    from agriautolab.metrics.coverage import eta_l, l_area

    field = box(0.0, 0.0, 100.0, 50.0)
    ys = (6.0, 18.0, 30.0, 42.0, 44.0)
    lines = tuple(LineString([(0.0, y), (100.0, y)]) for y in ys)
    stats = coverage_stats(lines, working_width_m=12.0, targets=coverage_targets(field))
    path = PathArtifact(segments=tuple(
        PathSegment(
            segment_id=f"w{i}",
            kind=PathSegmentKind.WORK,
            line=LineStringSpec(
                geometry_id=f"w{i}",
                points=(ContractPoint(x=0.0, y=y), ContractPoint(x=100.0, y=y)),
            ),
        )
        for i, y in enumerate(ys)
    ))
    lhs = l_area(path, working_width_m=12.0, work_area_m2=field.area) * (1.0 - eta_l(path))
    assert lhs == pytest.approx(1.0 + stats.overlap_ratio, rel=1e-12)
