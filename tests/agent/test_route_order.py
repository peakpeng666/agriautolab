"""route_order 槽位真值测试。

每条测试都必须在「修复前的实现」下失败——不是覆盖率测试。对应
docs/OPTIMIZATION_FOUNDATIONS.md §4 的真值纪律。

本文件钉住的缺陷（PR #28 复核发现）：
  1. state 未投影：候选拿到原始 tuple 而非 {"visited_count", ...}
  2. 烘焙与重放分解不一致：BCD 烘焙 rank、no_decomposition 重放
  3. 端点不看行进方向：REVERSE 条带从 points[0] 出，不是 points[-1]
  4. 投影未减质心：绝对坐标投影在平移下整体偏移，混合加权候选次序会变
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from agriautolab.agent.evolve import evolve_pool
from agriautolab.agent.proposer import MockProposer
from agriautolab.agent.slots import SLOTS
from agriautolab.algorithms.route.constructive_order import (
    RouteOrderProblem, endpoints_of, entry_of, evaluate_route_order, exit_of, project_state,
)
from agriautolab.algorithms.route.ranked_swath_order import RankedSwathOrderPlanner
from agriautolab.contracts.artifacts import LineStringSpec, Swath, SwathsArtifact
from agriautolab.contracts.geometry import Point, PolygonSpec
from agriautolab.contracts.problem import CoverageProblem
from agriautolab.contracts.vehicle import VehicleSpec
from agriautolab.optimization.constructive import ConstructionError, construct_solution

from tests.agent.test_agent import base_pool, make_instance, make_protocol

VEHICLE = VehicleSpec(working_width_m=9.7, body_width_m=2.0, min_turning_radius_m=3.0)


def _four_aligned_swaths(dx: float = 0.0, dy: float = 0.0) -> SwathsArtifact:
    """4 条平行条带（沿 x 轴），中心线 (0,i)->(10,i)，可整体平移 (dx,dy)。"""
    return SwathsArtifact(swaths=tuple(
        Swath(
            swath_id=f"swath-{i:04d}",
            centerline=LineStringSpec(geometry_id=f"line-{i:04d}", points=(
                Point(x=0.0 + dx, y=float(i) + dy), Point(x=10.0 + dx, y=float(i) + dy),
            )),
            width_m=2.0,
        )
        for i in range(4)
    ))


def _irregular_swaths() -> SwathsArtifact:
    """不等间距条带 y=0/1/3/7：每步最优与次优间隔 ≥ 1.0，无精确并列。"""
    return SwathsArtifact(swaths=tuple(
        Swath(
            swath_id=f"swath-{index:04d}",
            centerline=LineStringSpec(geometry_id=f"line-{index:04d}", points=(
                Point(x=0.0, y=float(y)), Point(x=10.0, y=float(y)),
            )),
            width_m=2.0,
        )
        for index, y in enumerate((0, 1, 3, 7))
    ))


def _problem_for(swaths: SwathsArtifact, *, centroid, normal) -> RouteOrderProblem:
    return RouteOrderProblem(
        {s.swath_id: endpoints_of(s) for s in swaths.swaths},
        min_turning_radius_m=3.0,
        working_width_m=2.0,
        field_centroid=centroid,
        principal_normal=normal,
    )


def _run(problem: RouteOrderProblem, score_fn) -> tuple[str, ...]:
    """把裸评分函数接到公共 engine；state 按契约先投影。"""
    total = len(problem.all_swath_ids)

    class _H:
        heuristic_id = "candidate"

        def score(self, state, action) -> float:
            return float(score_fn(project_state(state, total_swath_count=total), action))

    return construct_solution(problem, _H())


# ---------- 缺陷 3：行进方向决定端点 ----------

def test_entry_exit_follow_visit_parity() -> None:
    """REVERSE 条带从 points[0] 出、points[-1] 进——与 RankedSwathOrderPlanner 同源。

    修复前 _swath_exit 恒取 points[-1]，本测试的 index=1 两条断言必失败。
    """
    ends = ((0.0, 5.0), (10.0, 5.0))
    assert entry_of(ends, 0) == (0.0, 5.0)    # FORWARD 进起点
    assert exit_of(ends, 0) == (10.0, 5.0)    # FORWARD 出终点
    assert entry_of(ends, 1) == (10.0, 5.0)   # REVERSE 进终点
    assert exit_of(ends, 1) == (0.0, 5.0)     # REVERSE 出起点


def test_nearest_neighbour_order_and_evaluator_hand_computation() -> None:
    """4 条带手算：访问序 + 独立 evaluator 复算的总转移距离。

    几何：4 条平行条带 (0,i)->(10,i)，i=0..3；起点 = 地块质心 (5, 1.5)。
    方向按访问序奇偶交替（偶 FORWARD 进 (0,i)、奇 REVERSE 进 (10,i)）。

    逐步手算（评分 = distance_norm，并列按 swath_id 稳定序取先枚举者）：
      idx0 从 (5,1.5)，FORWARD 进 (0,i)：
           i=1,2 同为 hypot(5,0.5) 最小 → 取 swath-0001；出 (10,1)
      idx1 从 (10,1)，REVERSE 进 (10,i)：
           i=0,2 同为 1.0 最小 → 取 swath-0000；出 (0,0)
      idx2 从 (0,0)，FORWARD 进 (0,i)：i=2 距 2.0 < i=3 距 3.0 → swath-0002；出 (10,2)
      idx3 从 (10,2)，REVERSE 进 (10,3)：距 1.0 → swath-0003
    访问序 = (0001, 0000, 0002, 0003)

    总转移 = hypot(5,0.5) + 1.0 + 2.0 + 1.0

    【证伪力】修复前端点不看奇偶（恒 (0,i) 进、(10,i) 出），总转移变成
    hypot(5,0.5) + hypot(10,1) + hypot(10,2) + hypot(10,1) ≈ 35.3，
    而本测试的期望值 ≈ 9.02。差 3.9 倍，不可能靠容差蒙混。
    """
    swaths = _four_aligned_swaths()
    problem = _problem_for(swaths, centroid=(5.0, 1.5), normal=(0.0, 1.0))

    order = _run(problem, lambda state, cand: cand["distance_norm"])
    assert order == ("swath-0001", "swath-0000", "swath-0002", "swath-0003")

    total = evaluate_route_order(swaths.swaths, order, (5.0, 1.5))
    expected = math.hypot(5.0, 0.5) + 1.0 + 2.0 + 1.0
    assert total == pytest.approx(expected)
    # 与「端点不看方向」的错误实现明确拉开距离
    parity_blind = (
        math.hypot(5.0, 0.5) + math.hypot(10.0, 1.0) + math.hypot(10.0, 2.0) + math.hypot(10.0, 1.0)
    )
    assert total < parity_blind / 3.0


# ---------- 缺陷 1：state 必须先投影 ----------

def test_state_dependent_candidate_survives_full_slot_path() -> None:
    """用 state 的候选必须能走完 build_config，而不是被闸门淘汰。

    【证伪力】修复前 _SandboxHeuristic 把原始 tuple[str, ...] 直接传给候选，
    `state["remaining_count"]` 抛 TypeError → ConstructionError → 该候选被
    validation 闸淘汰。修复前本测试必失败，且失败模式正是槽位静默退化成
    action-only（此前四个 mock 候选恰好都不用 state，所以老测试全绿）。
    """
    slot = SLOTS["route_order"]
    problem = CoverageProblem(
        problem_id="state-dependent",
        field=PolygonSpec(geometry_id="field", exterior=(
            Point(x=0.0, y=0.0), Point(x=80.0, y=0.0), Point(x=80.0, y=40.0),
            Point(x=0.0, y=40.0), Point(x=0.0, y=0.0),
        )),
    )
    source = (
        "def next_swath_score(state, candidate):\n"
        "    return candidate['distance_norm'] - 0.01 * state['remaining_count']\n"
    )
    function = slot.compile(source)
    config = slot.build_config(function, problem, VEHICLE)
    ranks = {k: v for k, v in config.params.items() if k.startswith("rank:")}
    assert ranks, "state 依赖候选未能烘焙出任何 rank"


def test_project_state_reports_visited_and_remaining() -> None:
    assert project_state((), total_swath_count=4) == {"visited_count": 0.0, "remaining_count": 4.0}
    assert project_state(("a", "b"), total_swath_count=4) == {
        "visited_count": 2.0, "remaining_count": 2.0,
    }


# ---------- 缺陷 2：烘焙与重放必须同一分解 ----------

def test_baked_ranks_match_replayed_swaths_on_obstacle_field() -> None:
    """有障碍田上，build_config 烘焙的 rank 键必须覆盖重放时真实产生的条带。

    【证伪力】修复前烘焙走 BoustrophedonDecomposition、返回的 config 却声明
    no_decomposition。BCD 在有障碍田上切出不同 cell 布局 → 重放条带数量/序号
    不同 → RankedSwathOrderPlanner 抛「缺 rank 键」。本测试直接跑 run_pipeline
    重放，修复前必失败。
    """
    from agriautolab.pipeline.run import run_pipeline

    problem = CoverageProblem(
        problem_id="obstacle-field",
        field=PolygonSpec(geometry_id="field", exterior=(
            Point(x=0.0, y=0.0), Point(x=120.0, y=0.0), Point(x=120.0, y=80.0),
            Point(x=0.0, y=80.0), Point(x=0.0, y=0.0),
        )),
        obstacles=(
            PolygonSpec(geometry_id="obs", exterior=(
                Point(x=50.0, y=30.0), Point(x=70.0, y=30.0), Point(x=70.0, y=50.0),
                Point(x=50.0, y=50.0), Point(x=50.0, y=30.0),
            )),
        ),
    )
    slot = SLOTS["route_order"]
    function = slot.compile(
        "def next_swath_score(state, candidate):\n"
        "    return candidate['distance_norm']\n"
    )
    config = slot.build_config(function, problem, VEHICLE)

    instance = make_instance()
    protocol = make_protocol(instance)
    # 重放：不得抛「缺 rank 键」
    result = run_pipeline(problem, VEHICLE, config, protocol)
    assert result.config_id == config.config_id()


# ---------- 缺陷 4：投影必须减质心（平移不变） ----------

def test_projection_is_translation_invariant() -> None:
    """整体平移后 projection_norm 逐条带不变（质心随之平移）。

    【证伪力】修复前 projection_norm 用绝对坐标投影，平移 (dx,dy) 会给所有条带
    加同一常数。纯按 projection 排序看不出来（同序），但与 distance_norm 混合
    加权的候选（route_mixed）次序会变——本测试同时钉住数值与混合候选次序。
    """
    base = _four_aligned_swaths()
    moved = _four_aligned_swaths(dx=37.0, dy=-19.0)
    p_base = _problem_for(base, centroid=(5.0, 1.5), normal=(0.0, 1.0))
    p_moved = _problem_for(moved, centroid=(5.0 + 37.0, 1.5 - 19.0), normal=(0.0, 1.0))

    proj_base = {a["swath_id"]: a["projection_norm"] for a in p_base.feasible_actions(())}
    proj_moved = {a["swath_id"]: a["projection_norm"] for a in p_moved.feasible_actions(())}
    for swath_id, value in proj_base.items():
        assert proj_moved[swath_id] == pytest.approx(value), f"{swath_id} 投影随平移漂移"

    mixed = lambda state, cand: 0.6 * cand["distance_norm"] + 0.4 * cand["projection_norm"]
    assert _run(p_base, mixed) == _run(p_moved, mixed)


def test_nearest_neighbour_order_is_rigid_transform_invariant() -> None:
    """最近邻候选在刚体变换下访问序不变——质心与主轴法向必须一同变换。

    distance_norm 是纯欧氏距离，本就刚体不变；此前测试之所以观察到"旋转后次序变"
    并改用恒定评分绕开，是因为旋转了条带却把 centroid/normal 钉死在原值
    （与 PR #30 的 "Co-rotate fixed-angle parameters" 同类错误）。

    几何刻意取不等间距 y=0/1/3/7，使每一步的最优都有明确间隔（最小间隔 1.0）。
    等间距几何会在某些步产生**精确并列**，此时刚体变换的浮点舍入会任意打破并列
    ——那是并列本身的性质，不是不变性缺陷，见
    test_exact_ties_are_broken_by_enumeration_order_not_geometry。
    """
    swaths = _irregular_swaths()
    centroid = (5.0, 2.6)
    normal = (0.0, 1.0)
    nearest = lambda state, cand: cand["distance_norm"]
    base_order = _run(_problem_for(swaths, centroid=centroid, normal=normal), nearest)

    rng = np.random.default_rng(0)
    for _ in range(8):
        theta = float(rng.uniform(-math.pi, math.pi))
        tx, ty = float(rng.uniform(-100.0, 100.0)), float(rng.uniform(-100.0, 100.0))
        cos_t, sin_t = math.cos(theta), math.sin(theta)

        def move(x: float, y: float) -> tuple[float, float]:
            return (tx + cos_t * x - sin_t * y, ty + sin_t * x + cos_t * y)

        moved = SwathsArtifact(swaths=tuple(
            Swath(
                swath_id=s.swath_id,
                centerline=LineStringSpec(
                    geometry_id=s.centerline.geometry_id,
                    points=tuple(Point(x=move(p.x, p.y)[0], y=move(p.x, p.y)[1])
                                 for p in s.centerline.points),
                ),
                width_m=s.width_m,
            )
            for s in swaths.swaths
        ))
        moved_centroid = move(*centroid)
        moved_normal = (cos_t * normal[0] - sin_t * normal[1], sin_t * normal[0] + cos_t * normal[1])
        order = _run(_problem_for(moved, centroid=moved_centroid, normal=moved_normal), nearest)
        assert order == base_order, f"旋转 {theta:.4f} rad 后访问序由 {base_order} 变 {order}"


def test_exact_ties_are_broken_by_enumeration_order_not_geometry() -> None:
    """等间距几何会产生精确并列；并列由稳定枚举序决胜，且刚体变换下不保证稳定。

    这条如实记录一个**数值性质而非缺陷**：等间距条带 y=0/1/2/3、质心在中线上时，
    第 1 步到 y=0 与 y=2 的距离精确相等（都是 1.0）。同一坐标系内并列由
    feasible_actions 的 swath_id 稳定序决胜（可复现）；但刚体变换会引入
    ~1e-16 的舍入，任意打破并列。

    对 invariance_check 闸的含义：候选若在**并列稠密**的几何上按距离评分，
    可能被闸门判为不变性失败。这是真实的、应当被记录的局限，不应通过
    放宽闸门容差来掩盖——放宽容差会让真正的不变性缺陷一起漏过。
    """
    swaths = _four_aligned_swaths()   # 等间距 y=0/1/2/3
    problem = _problem_for(swaths, centroid=(5.0, 1.5), normal=(0.0, 1.0))
    after_first = ("swath-0001",)
    actions = problem.feasible_actions(after_first)
    by_id = {a["swath_id"]: a["distance_norm"] for a in actions}
    assert by_id["swath-0000"] == by_id["swath-0002"], "本 fixture 应当产生精确并列"
    # 同坐标系内并列可复现：稳定枚举序取字典序在先者
    order = _run(problem, lambda state, cand: cand["distance_norm"])
    assert order[1] == "swath-0000"


# ---------- 协议契约 ----------

def test_nan_score_raises_construction_error() -> None:
    """NaN 评分 fail closed：验证农业 adapter 没有绕过公共 engine 的检查。"""
    problem = _problem_for(_four_aligned_swaths(), centroid=(5.0, 1.5), normal=(0.0, 1.0))

    class _NanHeuristic:
        heuristic_id = "nan"

        def score(self, state, action) -> float:
            return float("nan")

    with pytest.raises(ConstructionError, match="非有限"):
        construct_solution(problem, _NanHeuristic())


def test_apply_action_rejects_out_of_range() -> None:
    problem = _problem_for(_four_aligned_swaths(), centroid=(5.0, 1.5), normal=(0.0, 1.0))
    with pytest.raises(ValueError, match="拒绝越界"):
        problem.apply_action(("swath-0000",), {"swath_id": "swath-0000"})   # 已访问
    with pytest.raises(ValueError, match="拒绝越界"):
        problem.apply_action((), {"swath_id": "swath-9999"})                # 不存在
    with pytest.raises(ValueError, match="缺 swath_id"):
        problem.apply_action((), {"distance_norm": 1.0})                    # 非法动作


def test_missing_geometry_fails_closed() -> None:
    """几何必填：此前用 setattr 事后打补丁 + getattr 回退原点是 fail-open。"""
    with pytest.raises(ValueError, match="不能为空"):
        RouteOrderProblem({}, min_turning_radius_m=3.0, working_width_m=2.0,
                          field_centroid=(0.0, 0.0), principal_normal=(0.0, 1.0))


def test_evaluator_rejects_non_permutation() -> None:
    swaths = _four_aligned_swaths()
    with pytest.raises(ValueError, match="非置换"):
        evaluate_route_order(swaths.swaths, ("swath-0000", "swath-0001"), (0.0, 0.0))
    with pytest.raises(ValueError, match="非置换"):
        evaluate_route_order(
            swaths.swaths,
            ("swath-0000", "swath-0000", "swath-0002", "swath-0003"),
            (0.0, 0.0),
        )


def test_ranked_swath_order_fails_closed_on_missing_rank_key() -> None:
    planner = RankedSwathOrderPlanner()
    swaths = SwathsArtifact(swaths=tuple(
        Swath(
            swath_id=f"swath-{i:04d}",
            centerline=LineStringSpec(geometry_id=f"line-{i:04d}", points=(
                Point(x=0.0, y=float(i)), Point(x=10.0, y=float(i)),
            )),
            width_m=2.0,
        )
        for i in range(3)
    ))
    with pytest.raises(ValueError, match="缺 rank 键"):
        planner.run(swaths, ranks={"swath-0000": 0.0})


def test_route_mock_candidates_pass_full_gate_chain() -> None:
    """4 个 route mock 候选过完整闸链。"""
    instance = make_instance()
    protocol = make_protocol(instance)
    ledger, _kept = evolve_pool(
        base_pool(), (instance,),
        proposer=MockProposer(),
        protocol=protocol,
        rng=np.random.default_rng(0),
        rounds=3,
        slot="route_order",
    )
    assert len(ledger.records) == 3
    for record in ledger.records:
        assert record.slot_id == "route_order"
    ledger.verify()
    assert all(r.evaluations_used >= 2 for r in ledger.records)
