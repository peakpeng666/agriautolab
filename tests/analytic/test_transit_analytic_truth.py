"""G-A.1：转移段的解析真值。判定我方那 50% 超额是不是实现 bug 的标尺。

背景（12 块 F2B 地实测）：swath_length_sum 只差 +0.169%，
path_length 差 -5.30%，transit 差 -38.1% —— 残差全在转移里。
没有解析标尺就只能比两个实现，比不出谁对。

π 的取用：Dubins 弧长是解析量（angle·R），与 buffer 圆角化无关，
按 geometry/discrete.py 已写明的既定约定用 math.pi，不用 PI_DISCRETE。
"""

import math

import pytest
from shapely import box

from agriautolab.algorithms.path.dubins_transit import DubinsTransit
from agriautolab.algorithms.route.boustrophedon_order import BoustrophedonOrder
from agriautolab.algorithms.swath.fixed_angle import FixedAngleSwath
from agriautolab.contracts.geometry import Pose2D
from agriautolab.contracts.problem import CoverageProblem
from agriautolab.contracts.vehicle import VehicleSpec
from agriautolab.geometry.validate import polygon_to_spec
from agriautolab.kinematics.dubins import dubins_length, dubins_word
from agriautolab.metrics.path import transit_breakdown


def pi_turn_analytic(radius: float, spacing: float) -> float:
    """相邻牛耕掉头的最短前进长度，d >= 2R。

    推导：左转 pi/2（弧长 pi·R/2，横移 R）-> 直行 d-2R -> 再左转 pi/2（横移 R），
    净航向改变 pi、净横移 2R + (d-2R) = d、净纵移 0，即 LSL 退化的 Pi 形掉头。
    """
    if spacing < 2.0 * radius:
        raise ValueError("d < 2R 属于鼓包区，本式不适用")
    return math.pi * radius + spacing - 2.0 * radius


# (R, d, 期望长度)。d >= 2R 的 Pi-turn 区。
# 规格里给 R=3.0/d=8.0 的字面量是 9.42477796076938，那等于 pi*3，即 d-2R=0 的情形；
# 与规格自己给的式子 pi·R + d − 2R 不符（该式在 R=3/d=8 上是 11.42477796076938，
# 解算器也给这个数）。这里按式子钉 11.4248，并补一行 R=3.0/d=6.0 —— 9.42477796076938
# 正是那组参数下的真值，规格那个数在它成立的地方照样被钉住。
PI_TURN_CASES = (
    (2.0, 5.0, 7.283185307179587),
    (3.0, 8.0, 11.42477796076938),
    (1.5, 4.0, 5.712388980384690),
    (3.0, 6.0, 9.42477796076938),
)


@pytest.mark.parametrize("radius,spacing,expected", PI_TURN_CASES)
def test_pi_turn_closed_form_matches_dubins_solver(radius: float, spacing: float, expected: float) -> None:
    """反平行、纯横移 d 的最短 Dubins 长度 == pi·R + d − 2R，rel=1e-9。"""
    assert pi_turn_analytic(radius, spacing) == pytest.approx(expected, rel=1e-9)
    solved = dubins_length((0.0, 0.0, 0.0), (0.0, spacing, math.pi), radius)
    assert solved == pytest.approx(expected, rel=1e-9)


@pytest.mark.parametrize("radius,spacing,expected", PI_TURN_CASES)
def test_boustrophedon_turn_on_rectangle_hits_the_analytic_minimum(
    radius: float, spacing: float, expected: float
) -> None:
    """矩形地块、无障碍、相邻牛耕：每次掉头的转移长度必须落在解析最短上。

    采样折线比真弧短：弦差每段约 theta^2/24（theta = step/R），
    step=0.25 时整体约 5e-4 —— 因此这里用 2e-3 的相对容差钉「等于解析值」，
    另有 test_sampled_turn_converges_to_analytic_as_step_shrinks 钉住
    这个差纯粹来自离散化。它不是 38% 那一级的量。
    """
    main = box(0.0, 0.0, 200.0, 4.0 * spacing)
    spec = polygon_to_spec(main, "main")
    problem = CoverageProblem(problem_id="rect", field=spec)
    swaths = FixedAngleSwath(0.0).run((spec,), working_width_m=spacing, problem=problem)
    route = BoustrophedonOrder().run(swaths)
    path = DubinsTransit(0.25).run(
        route, VehicleSpec(working_width_m=spacing, body_width_m=1.0, min_turning_radius_m=radius)
    )
    breakdown = transit_breakdown(path)

    assert len(swaths.swaths) == 4
    assert breakdown.turn_count == 3
    assert breakdown.entry_leg_m == 0.0
    assert breakdown.exit_leg_m == 0.0
    assert breakdown.inter_cell_m == 0.0
    assert breakdown.other_m == 0.0
    assert breakdown.mean_turn_m == pytest.approx(expected, rel=2e-3)
    # 采样只会让折线比弧短，绝不会更长。
    assert breakdown.mean_turn_m <= expected


def test_sampled_turn_converges_to_analytic_as_step_shrinks() -> None:
    """步长减半，弦差降到约四分之一：证明那 5e-4 是离散化，不是几何错。"""
    radius, spacing = 2.0, 5.0
    analytic = pi_turn_analytic(radius, spacing)
    main = box(0.0, 0.0, 200.0, 4.0 * spacing)
    spec = polygon_to_spec(main, "main")
    problem = CoverageProblem(problem_id="rect", field=spec)
    swaths = FixedAngleSwath(0.0).run((spec,), working_width_m=spacing, problem=problem)
    route = BoustrophedonOrder().run(swaths)
    vehicle = VehicleSpec(working_width_m=spacing, body_width_m=1.0, min_turning_radius_m=radius)

    deficits = []
    for step in (0.4, 0.2, 0.1):
        path = DubinsTransit(step).run(route, vehicle)
        deficits.append(analytic - transit_breakdown(path).mean_turn_m)
    assert all(deficit > 0.0 for deficit in deficits)
    for coarse, fine in zip(deficits, deficits[1:]):
        assert fine == pytest.approx(coarse / 4.0, rel=0.1)


# d < 2R 的鼓包区：钉 length/R，字只断言落在并列最优集合里。
# d/R=2.0 是边界，LSL（pi/2 + 0 + pi/2）与 LRL 同为 pi·R，并列；
# 现有实现按 (长度, 字名) 字典序破平，得到 LRL。真值钉长度，不钉破平结果。
BULGE_CASES = (
    (0.0, 7.330382858376184, {"LRL", "RLR"}),
    (1.0, 6.032529644843455, {"RLR"}),
    (2.0, 3.141592653589793, {"LSL", "LRL"}),
)


@pytest.mark.parametrize("ratio,expected_over_radius,words", BULGE_CASES)
def test_bulge_region_lengths_are_pinned(ratio: float, expected_over_radius: float, words: set[str]) -> None:
    """d < 2R：直线段塌缩，最短解走 CCC 字；这三点把整个鼓包区钉住。

    规格给 d/R=1.0 的参考值是 6.032484，实测是 6.032529644843455（相对差 7.6e-6）。
    规格原话是「实测钉住即可」，故按实测钉。
    """
    radius = 1.0
    goal = (0.0, ratio * radius, math.pi)
    assert dubins_length((0.0, 0.0, 0.0), goal, radius) / radius == pytest.approx(
        expected_over_radius, rel=1e-9
    )
    word = dubins_word(
        Pose2D(x=0.0, y=0.0, yaw_rad=0.0),
        Pose2D(x=0.0, y=ratio * radius, yaw_rad=math.pi),
        radius,
    )
    assert word.name in words


def test_bulge_and_pi_turn_agree_at_the_d_equals_2r_boundary() -> None:
    """两个区在 d=2R 处必须接上：pi·R + d − 2R 在此退化为 pi·R。"""
    radius = 2.0
    assert pi_turn_analytic(radius, 2.0 * radius) == pytest.approx(math.pi * radius, rel=1e-15)
    assert dubins_length((0.0, 0.0, 0.0), (0.0, 2.0 * radius, math.pi), radius) == pytest.approx(
        math.pi * radius, rel=1e-12
    )


def test_pi_turn_formula_refuses_the_bulge_region() -> None:
    """作用域有效性：d < 2R 时本式不成立，必须拒绝求值而不是给一个偏小的数。"""
    with pytest.raises(ValueError):
        pi_turn_analytic(2.0, 3.9)
