"""Reeds-Shepp 48 字全集的验证电池与解析真值 #17-#21。

8 个闭式基础式 x 三个对称变换（timeflip / reflect / backwards）的笛卡尔积，
逐词正演闭合。真值 #18（RS <= Dubins）与 #21（倒车罚极大时退化为 Dubins 解）
是一对：两条都过才说明这里确实多了一个自由度，而不是把 Dubins 换了个名字。
"""

import math

import numpy as np
import pytest

from agriautolab.contracts.errors import KinematicModelError
from agriautolab.contracts.geometry import Pose2D
from agriautolab.kinematics.dubins import dubins_length
from agriautolab.kinematics.reeds_shepp import (
    BASE_FORMULAS, ReverseCostModel, _rs_endpoint, reeds_shepp_cost, reeds_shepp_length,
    reeds_shepp_word, reeds_shepp_words,
)

GEOMETRIC = ReverseCostModel(reverse_length_multiplier=1.0, gear_shift_penalty_m=0.0)


def signed_form(word):
    """字的带符号形态，例如 ('L+','R-','S-','L-')。零长段不算——它不是一个字母。"""
    return tuple(
        letter + ("+" if value >= 0.0 else "-")
        for letter, value in zip(word.letters, word.params)
        if abs(value) > 1e-12
    )


def _poses(rng, count):
    for _ in range(count):
        yield (
            Pose2D(x=float(rng.uniform(-40, 40)), y=float(rng.uniform(-40, 40)),
                   yaw_rad=float(rng.uniform(-math.pi, math.pi))),
            Pose2D(x=float(rng.uniform(-40, 40)), y=float(rng.uniform(-40, 40)),
                   yaw_rad=float(rng.uniform(-math.pi, math.pi))),
            float(rng.uniform(1.0, 8.0)),
        )


def test_all_candidate_words_close_on_random_poses() -> None:
    rng = np.random.default_rng(20260821)
    worst = 0.0
    checked = 0
    with_reverse = 0
    for start, goal, radius in _poses(rng, 600):
        for word in reeds_shepp_words(start, goal, radius):
            end = _rs_endpoint(start, word, radius)
            error = math.hypot(end.x - goal.x, end.y - goal.y) + abs(
                (end.yaw_rad - goal.yaw_rad + math.pi) % (2 * math.pi) - math.pi
            )
            worst = max(worst, error)
            checked += 1
            with_reverse += word.has_reverse()
    assert worst < 1e-9, f"最大闭合误差 {worst:.3e}"
    assert checked > 3000
    assert with_reverse > checked // 4   # 倒车字确实在被使用，不是摆设


def test_never_exceeds_dubins() -> None:
    """前向-only 是 RS 可行子集：任何位姿上已实现字集的最短 <= Dubins 最短。"""
    rng = np.random.default_rng(777)
    for start, goal, radius in _poses(rng, 800):
        rs = reeds_shepp_length((start.x, start.y, start.yaw_rad), (goal.x, goal.y, goal.yaw_rad), radius)
        dub = dubins_length((start.x, start.y, start.yaw_rad), (goal.x, goal.y, goal.yaw_rad), radius)
        assert rs <= dub + 1e-9


def test_direction_symmetry_of_best_length() -> None:
    """时间反演对称：start->goal 与 goal->start 的最短值相同（0/4000 实测）。"""
    rng = np.random.default_rng(20260822)
    for start, goal, radius in _poses(rng, 500):
        forward = reeds_shepp_length((start.x, start.y, start.yaw_rad), (goal.x, goal.y, goal.yaw_rad), radius)
        backward = reeds_shepp_length((goal.x, goal.y, goal.yaw_rad), (start.x, start.y, start.yaw_rad), radius)
        assert forward == pytest.approx(backward, rel=1e-12, abs=1e-12)


def test_straight_ahead_truth_is_d() -> None:
    assert reeds_shepp_length((0.0, 0.0, 0.0), (10.0, 0.0, 0.0), 1.0) == pytest.approx(10.0, rel=1e-15)


def test_same_point_turnaround_truth_is_pi_times_radius() -> None:
    """同点换向 pi：RS 最短 = pi*R（尖点旋转），严格优于 Dubins 的 7pi/3。"""
    for radius in (1.0, 2.5):
        value = reeds_shepp_length((0.0, 0.0, 0.0), (0.0, 0.0, math.pi), radius)
        assert value == pytest.approx(math.pi * radius, rel=1e-12)
    assert reeds_shepp_length((0.0, 0.0, 0.0), (0.0, 0.0, math.pi), 1.0) < dubins_length(
        (0.0, 0.0, 0.0), (0.0, 0.0, math.pi), 1.0
    )


def test_antiparallel_matches_dubins_no_gain() -> None:
    """反平行 d=4, R=1：最优就是前向 LSL（pi+2），RS 无增益——如实现给出了更短值反而可疑。"""
    assert reeds_shepp_length((0.0, 0.0, 0.0), (0.0, 4.0, math.pi), 1.0) == pytest.approx(math.pi + 2.0, rel=1e-12)


def test_reverse_beats_dubins_on_near_antiparallel_corridor() -> None:
    """近反平行窄走廊：倒车三点掉头应显著短于 Dubins（mean gain 实测 ~1 m）。"""
    rng = np.random.default_rng(31)
    gains = []
    for _ in range(100):
        goal = (float(rng.uniform(-2.0, 2.0)), float(rng.uniform(2.0, 6.0)), math.pi)
        radius = float(rng.uniform(1.0, 3.0))
        gains.append(dubins_length((0, 0, 0), goal, radius) - reeds_shepp_length((0, 0, 0), goal, radius))
    assert max(gains) > 0.5   # 存在显著增益场景（实测 max ~5.8 m）


def test_zero_radius_is_rejected() -> None:
    with pytest.raises(KinematicModelError):
        reeds_shepp_length((0.0, 0.0, 0.0), (5.0, 5.0, 1.0), 0.0)
    with pytest.raises(KinematicModelError):
        reeds_shepp_words(Pose2D(x=0.0, y=0.0, yaw_rad=0.0), Pose2D(x=5.0, y=5.0, yaw_rad=1.0), -1.0)


def test_reverse_cost_model_arithmetic_and_selection() -> None:
    model = ReverseCostModel(reverse_length_multiplier=2.0, gear_shift_penalty_m=0.0)
    word = reeds_shepp_word(
        Pose2D(x=0.0, y=0.0, yaw_rad=0.0), Pose2D(x=0.0, y=0.0, yaw_rad=math.pi), 1.0,
        cost_model=model,
    )
    forward = sum(v for v in word.params if v >= 0.0)
    backward = sum(-v for v in word.params if v < 0.0)
    assert model.cost(word, 1.0) == pytest.approx(forward + 2.0 * backward, rel=1e-15)
    with pytest.raises(ValueError):
        ReverseCostModel(reverse_length_multiplier=0.5, gear_shift_penalty_m=0.0)
    with pytest.raises(ValueError):
        ReverseCostModel(reverse_length_multiplier=1.0, gear_shift_penalty_m=-1.0)


def test_gear_shift_penalty_is_not_expressible_by_the_length_multiplier() -> None:
    """两个参数不冗余：换挡罚是固定成本，乘子怎么调都表达不出来。"""
    word = reeds_shepp_word(
        Pose2D(x=0.0, y=0.0, yaw_rad=0.0), Pose2D(x=0.0, y=0.0, yaw_rad=math.pi), 1.0,
        cost_model=GEOMETRIC,
    )
    assert word.gear_shift_count() >= 1
    without = ReverseCostModel(reverse_length_multiplier=1.0, gear_shift_penalty_m=0.0)
    with_penalty = ReverseCostModel(reverse_length_multiplier=1.0, gear_shift_penalty_m=3.0)
    delta = with_penalty.cost(word, 1.0) - without.cost(word, 1.0)
    assert delta == pytest.approx(3.0 * word.gear_shift_count(), rel=1e-15)


def test_truth_17_generator_reaches_the_full_48_word_set() -> None:
    """真值 #17：8 个基础式 x 2^3 对称变换，随机位姿上必须命中 48 个不同带符号字形。

    这是「48 字」这个可数事实的落点。旧断言钉的是候选个数 > 15000，
    那是过量生成的产物：去重后同样位姿只有 3841 个候选，而字形恰好 48 个。
    """
    rng = np.random.default_rng(20260821)
    forms = set()
    for start, goal, radius in _poses(rng, 5000):
        for word in reeds_shepp_words(start, goal, radius):
            forms.add(signed_form(word))
    assert len(BASE_FORMULAS) == 8
    assert len(forms) == 48, f"命中 {len(forms)} 个字形，应为 48"


def test_truth_21_huge_reverse_penalty_degenerates_to_the_dubins_solution() -> None:
    """真值 #21：倒车罚极大时最优解必须退化为纯前进解，长度等于 Dubins。

    与真值 #18（RS <= Dubins）成对：#18 说 RS 不会更差，#21 说这个「更好」
    确实来自倒车这个新自由度——把倒车罚到极大，好处就该消失得干干净净。
    只过 #18 不过 #21，说明可能只是把 Dubins 换了个名字。
    """
    prohibitive = ReverseCostModel(reverse_length_multiplier=1.0e9, gear_shift_penalty_m=1.0e9)
    rng = np.random.default_rng(4242)
    for start, goal, radius in _poses(rng, 300):
        p0 = (start.x, start.y, start.yaw_rad)
        p1 = (goal.x, goal.y, goal.yaw_rad)
        best = reeds_shepp_word(start, goal, radius, cost_model=prohibitive)
        assert not best.has_reverse(), f"倒车罚 1e9 仍选了倒车字 {best.name}"
        assert best.geometric_length(radius) == pytest.approx(
            dubins_length(p0, p1, radius), rel=1e-9
        )


def test_truth_21_and_18_together_prove_a_real_extra_degree_of_freedom() -> None:
    """同点掉头：几何代价下 RS 严格短于 Dubins，倒车罚极大时又恰好回到 Dubins。"""
    p0, p1, radius = (0.0, 0.0, 0.0), (0.0, 0.0, math.pi), 1.0
    dubins = dubins_length(p0, p1, radius)
    assert reeds_shepp_cost(p0, p1, radius, cost_model=GEOMETRIC) < dubins
    prohibitive = ReverseCostModel(reverse_length_multiplier=1.0e9, gear_shift_penalty_m=1.0e9)
    best = reeds_shepp_word(
        Pose2D(x=0.0, y=0.0, yaw_rad=0.0), Pose2D(x=0.0, y=0.0, yaw_rad=math.pi), radius,
        cost_model=prohibitive,
    )
    assert best.geometric_length(radius) == pytest.approx(dubins, rel=1e-9)


def test_no_headland_plus_reeds_shepp_is_feasible_where_dubins_is_not() -> None:
    """加 Reeds-Shepp 的全部理由：headland=0 的矩形上它可行，而前向-only Dubins 不可行。

    无地头时掉头向界外鼓出最多 2R，outside_area 必然拒绝前向解——
    掉头空间正是地头存在的理由。倒车能力把掉头收进场内，这个组合才成立。
    """
    from agriautolab.contracts.enums import CoverageTarget, RunStatus
    from agriautolab.contracts.geometry import Point, PolygonSpec
    from agriautolab.contracts.problem import CoverageProblem
    from agriautolab.contracts.protocol import BenchmarkProtocol, ReverseCostSpec
    from agriautolab.contracts.vehicle import VehicleSpec
    from agriautolab.pipeline.pareto.hypervolume import analytic_reference
    from agriautolab.pipeline.config import PipelineConfig
    from agriautolab.pipeline.run import run_pipeline

    field = PolygonSpec(geometry_id="field", exterior=(
        Point(x=0.0, y=0.0), Point(x=200.0, y=0.0), Point(x=200.0, y=100.0),
        Point(x=0.0, y=100.0), Point(x=0.0, y=0.0),
    ))
    problem = CoverageProblem(problem_id="rs-no-headland", field=field)
    reversible = VehicleSpec(
        working_width_m=10.0, body_width_m=2.0, min_turning_radius_m=3.0, can_reverse=True,
    )
    protocol = BenchmarkProtocol(
        protocol_id="rs", coverage_target=CoverageTarget.ORIGINAL_FIELD, coverage_threshold=0.0,
        hypervolume_reference=analytic_reference(problem, reversible),
        reverse_cost=ReverseCostSpec(reverse_length_multiplier=1.0, gear_shift_penalty_m=0.0),
    )

    def config(path_algorithm: str) -> PipelineConfig:
        return PipelineConfig(
            "no_decomposition", "no_headland", "fixed_angle", "boustrophedon_order",
            path_algorithm, {"angle_rad": 0.0},
        )

    rs = run_pipeline(problem, reversible, config("reeds_shepp_transit"), protocol)
    assert rs.validation.status is RunStatus.OK
    assert rs.objectives is not None
    assert math.isfinite(rs.validation.metric("path_length"))

    forward_only = reversible.model_copy(update={"can_reverse": False})
    dubins = run_pipeline(problem, forward_only, config("dubins_transit"), protocol)
    assert dubins.validation.status is RunStatus.CONSTRAINT_VIOLATION
    assert dubins.validation.failure_reason == "validator_rejected:outside_area"


def test_reeds_shepp_stage_refuses_a_vehicle_that_cannot_reverse() -> None:
    """RS 的意义全在倒车；给不可倒车机具静默跑前向词等于伪装成「用了 RS」。"""
    from agriautolab.algorithms.path.reeds_shepp_transit import ReedsSheppTransit
    from agriautolab.contracts.artifacts import RouteArtifact
    from agriautolab.contracts.vehicle import VehicleSpec

    stage = ReedsSheppTransit(0.25, cost_model=GEOMETRIC)
    forward_only = VehicleSpec(
        working_width_m=10.0, body_width_m=2.0, min_turning_radius_m=3.0, can_reverse=False,
    )
    with pytest.raises(KinematicModelError, match="can_reverse"):
        stage.run(RouteArtifact(traversals=(), swaths=()), forward_only)
