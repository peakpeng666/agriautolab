"""Dubins 六字的解析真值与正演闭合（解析真值清单 1–5）。

5000 组随机位姿的全字闭合是 LRL 陷阱的唯一可靠哨兵：手工样例一个都没命中过它。
"""

import math

import numpy as np
import pytest

from agriautolab.contracts.errors import KinematicModelError
from agriautolab.contracts.geometry import Pose2D
from agriautolab.kinematics.dubins import dubins_endpoint, dubins_length, dubins_word, dubins_words


def _closure_error(start: Pose2D, goal: Pose2D, word, radius: float) -> float:
    end = dubins_endpoint(start, word, radius)
    yaw_error = (end.yaw_rad - goal.yaw_rad + math.pi) % (2.0 * math.pi) - math.pi
    return math.hypot(end.x - goal.x, end.y - goal.y) + abs(yaw_error)


def test_all_six_words_close_on_5000_random_poses() -> None:
    """真值 1：六字各自正演闭合，终点误差 < 1e-12。

    用 numpy Generator（种子显式注入）生成位姿，不用全局随机——
    任何随机都需可复现，这是仓库的确定性纪律。
    """
    rng = np.random.default_rng(20260821)
    worst = 0.0
    words_checked = 0
    names_seen = set()
    for _ in range(5000):
        start = Pose2D(
            x=float(rng.uniform(-50.0, 50.0)),
            y=float(rng.uniform(-50.0, 50.0)),
            yaw_rad=float(rng.uniform(-math.pi, math.pi)),
        )
        goal = Pose2D(
            x=float(rng.uniform(-50.0, 50.0)),
            y=float(rng.uniform(-50.0, 50.0)),
            yaw_rad=float(rng.uniform(-math.pi, math.pi)),
        )
        radius = float(rng.uniform(0.5, 20.0))
        for word in dubins_words(start, goal, radius):
            worst = max(worst, _closure_error(start, goal, word, radius))
            words_checked += 1
            names_seen.add(word.name)
    # CCC 字（RLR/LRL）只在两圆盘相交的参数域有效，平均每姿态约 4.5 个有效字
    assert words_checked >= 20000
    assert names_seen == {"LSL", "RSR", "LSR", "RSL", "RLR", "LRL"}
    assert worst < 1e-12, f"最大闭合误差 {worst:.3e}"


def test_antiparallel_truth_is_pi_plus_d_minus_2r() -> None:
    """真值 2：反平行 d=4, R=1 -> pi + d - 2R = 5.141593（两个 pi/2 弧 + 长 2 的直线）。"""
    length = dubins_length((0.0, 0.0, 0.0), (0.0, 4.0, math.pi), 1.0)
    assert length == pytest.approx(math.pi + 4.0 - 2.0 * 1.0, rel=1e-12)
    assert length == pytest.approx(5.141593, abs=5e-7)


def test_same_point_turnaround_truth_is_seven_pi_over_three() -> None:
    """真值 3：同点掉头 d=0, R=1, 航向差 pi -> 7pi/3 = 7.330383（CCC 字，三段 pi/3+5pi/3+pi/3）。

    LRL 与 RLR 在此位姿并列最优（互为镜像），长度同为 7pi/3；
    真值钉长度，字的选择由名字字典序破平（LRL），确定性不缺。
    """
    length = dubins_length((0.0, 0.0, 0.0), (0.0, 0.0, math.pi), 1.0)
    assert length == pytest.approx(7.0 * math.pi / 3.0, rel=1e-12)
    assert length == pytest.approx(7.330383, abs=5e-7)
    word = dubins_word(Pose2D(x=0.0, y=0.0, yaw_rad=0.0), Pose2D(x=0.0, y=0.0, yaw_rad=math.pi), 1.0)
    assert word.name in {"RLR", "LRL"}
    for actual, expected in zip(word.params, (math.pi / 3.0, 5.0 * math.pi / 3.0, math.pi / 3.0)):
        assert actual == pytest.approx(expected, rel=1e-12)


def test_straight_ahead_truth_is_d() -> None:
    """真值 4：正前方 d=10，同向 -> 10.0（LSL 退化成纯直线）。"""
    assert dubins_length((0.0, 0.0, 0.0), (10.0, 0.0, 0.0), 1.0) == pytest.approx(10.0, rel=1e-15)


def test_zero_radius_is_rejected_with_kinematic_model_error() -> None:
    """真值 5：R=0 交给 Dubins 需抛 KinematicModelError（契约既定裁决）。"""
    with pytest.raises(KinematicModelError):
        dubins_length((0.0, 0.0, 0.0), (5.0, 5.0, 1.0), 0.0)
    with pytest.raises(KinematicModelError):
        dubins_words(Pose2D(x=0.0, y=0.0, yaw_rad=0.0), Pose2D(x=5.0, y=5.0, yaw_rad=1.0), -1.0)


def test_shortest_word_never_exceeds_any_single_word() -> None:
    """min 的自洽性：最短 word 长度 <= 每个有效 word 的长度，且等于其中的最小值。"""
    rng = np.random.default_rng(777)
    for _ in range(200):
        start = Pose2D(x=float(rng.uniform(-30, 30)), y=float(rng.uniform(-30, 30)), yaw_rad=float(rng.uniform(-3, 3)))
        goal = Pose2D(x=float(rng.uniform(-30, 30)), y=float(rng.uniform(-30, 30)), yaw_rad=float(rng.uniform(-3, 3)))
        radius = float(rng.uniform(1.0, 10.0))
        words = dubins_words(start, goal, radius)
        best = dubins_word(start, goal, radius)
        assert best.length(radius) == min(word.length(radius) for word in words)
