"""路径指标锁在能手推出答案的小算例上。"""

import math

import pytest

from agriautolab.contracts.geometry import Point
from agriautolab.metrics.path import aol, cusp_count, l0_zero_turn_radius, path_length, total_heading_change, tortuosity


def pts(*coords: tuple[float, float]) -> tuple[Point, ...]:
    return tuple(Point(x=x, y=y) for x, y in coords)


def test_345_path_length_and_tortuosity() -> None:
    path = pts((0, 0), (3, 0), (3, 4))
    assert path_length(path) == pytest.approx(7.0, abs=1e-12)
    assert tortuosity(path) == pytest.approx(1.4, abs=1e-12)


def test_closed_square_heading_change_has_only_three_internal_vertices() -> None:
    path = pts((0, 0), (10, 0), (10, 10), (0, 10), (0, 0))
    assert total_heading_change(path) == pytest.approx(3.0 * math.pi / 2.0, abs=1e-12)


def test_right_angle_heading_and_aol() -> None:
    path = pts((0, 0), (100, 0), (100, 50))
    assert total_heading_change(path) == pytest.approx(math.pi / 2.0, abs=1e-12)
    assert aol(path) == pytest.approx((math.pi / 2.0) / 150.0, abs=1e-12)


def test_out_and_back_has_one_cusp() -> None:
    assert cusp_count(pts((0, 0), (10, 0), (0, 0))) == 1


def test_l0_three_swaths() -> None:
    swaths = (
        pts((0, 0), (100, 0)),
        pts((100, 10), (0, 10)),
        pts((0, 20), (100, 20)),
    )
    assert l0_zero_turn_radius(swaths) == pytest.approx(320.0, abs=1e-12)
