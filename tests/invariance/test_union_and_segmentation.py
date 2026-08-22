"""回归两次真实故障：并集在特定旋转角丢块，以及分段密度凭空制造指标差异。"""

import math

import pytest
from shapely import box
from shapely.affinity import rotate, scale

from agriautolab.contracts.geometry import Point
from agriautolab.geometry.robust import robust_union
from agriautolab.metrics.path import aol, path_length, total_heading_change, tortuosity


def test_known_theta_1_9_scale_3_union_keeps_all_disjoint_pieces() -> None:
    pieces = tuple(box(0.0, i * 12.0, 100.0, i * 12.0 + 10.0) for i in range(5))
    transformed = tuple(
        rotate(scale(piece, xfact=3.0, yfact=3.0, origin=(0.0, 0.0)), 1.9, origin=(0.0, 0.0), use_radians=True)
        for piece in pieces
    )
    result = robust_union(transformed, scale_hint=300.0)
    assert result.area == pytest.approx(sum(piece.area for piece in transformed), rel=1e-9)


def test_coarse_vs_76_segment_same_physical_path() -> None:
    coarse = (Point(x=0, y=0), Point(x=100, y=0), Point(x=100, y=50))
    fine_points = [Point(x=100.0 * i / 38.0, y=0.0) for i in range(39)]
    fine_points.extend(Point(x=100.0, y=50.0 * i / 38.0) for i in range(1, 39))
    fine = tuple(fine_points)
    assert len(fine) - 1 == 76
    for metric in (path_length, total_heading_change, aol, tortuosity):
        assert metric(fine) == pytest.approx(metric(coarse), rel=1e-12, abs=1e-12)
    assert total_heading_change(fine) == pytest.approx(math.pi / 2.0, rel=1e-12)
