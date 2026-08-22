"""PI_DISCRETE 与两条已归档的 buffer 圆弧事故的解析对账。"""

import math

import pytest
from shapely import Polygon

from agriautolab.geometry.discrete import PI_DISCRETE
from agriautolab.geometry.footprint import QUAD_SEGS


def test_pi_discrete_matches_inscribed_polygon_formula() -> None:
    n = 4 * QUAD_SEGS
    assert PI_DISCRETE == pytest.approx(0.5 * n * math.sin(2.0 * math.pi / n), rel=1e-15)
    assert PI_DISCRETE == pytest.approx(3.1365484905469396, rel=1e-12)   # QUAD_SEGS=16, n=64
    assert PI_DISCRETE < math.pi


def test_reflex_corner_round_minus_mitre_is_w_squared_times_one_minus_pi_d_over_4() -> None:
    """AUDIT_NOTE 归档事故一：反曲角 round−mitre 差 = w^2(1 - pi_d/4) = 7.771064。

    连续 pi 会给 7.725666，与实测对不上——离散弧的面积必须用离散 pi。
    """
    w = 6.0
    notch = Polygon([(0, 0), (100, 0), (100, 50), (60, 50), (60, 20), (0, 20)])   # 缺口 60x30
    round_main = notch.buffer(-w, cap_style="round", join_style="round", quad_segs=QUAD_SEGS)
    mitre_main = notch.buffer(-w, cap_style="round", join_style="mitre", quad_segs=QUAD_SEGS)
    measured = round_main.area - mitre_main.area
    predicted = w * w * (1.0 - PI_DISCRETE / 4.0)
    assert measured == pytest.approx(predicted, rel=1e-9)
    assert measured == pytest.approx(7.771064, rel=1e-6)


def test_obstacle_annulus_false_positive_is_perimeter_w_plus_pi_d_w_squared() -> None:
    """AUDIT_NOTE 归档事故二：障碍环带假阳性 = 周长·w + pi_d·w^2 = 472.9157。"""
    w = 6.0
    field = Polygon([(0, 0), (100, 0), (100, 50), (0, 50)])
    obstacle = Polygon([(40, 20), (60, 20), (60, 30), (40, 30)])
    original = field.difference(obstacle)
    legit = field.buffer(-w, cap_style="round", join_style="round", quad_segs=QUAD_SEGS).difference(obstacle)
    verbatim = original.buffer(-w, cap_style="round", join_style="round", quad_segs=QUAD_SEGS)
    measured = legit.symmetric_difference(verbatim).area
    predicted = obstacle.length * w + PI_DISCRETE * w * w
    assert measured == pytest.approx(predicted, rel=1e-6)
    assert measured == pytest.approx(472.9157, rel=1e-5)
