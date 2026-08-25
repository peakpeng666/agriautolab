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
    """有障碍田上，烘焙的 rank 键集合必须与重放时真实产生的条带 id 集合**精确相等**。

    【证伪力】修复前烘焙走 BoustrophedonDecomposition、返回的 config 却声明
    no_decomposition。本例田上 BCD 产 10 条带、no_decomposition 产 7 条带。

    关键：两种分解的 id 都是顺序 `swath-NNNN`，10 个 id 是 7 个的**超集**，
    因此 RankedSwathOrderPlanner **不会**报「缺 rank 键」——它照跑不误，
    只是把 rank 套到几何上毫不相干的条带（Codex 警告的正是这一半）。
    所以断言必须直接比集合，不能只看 run_pipeline 是否抛异常，
    也不能只看 config_id 回填——那两种断言在缺陷下都会通过。
    """
    from agriautolab.algorithms.swath.principal_axis import PrincipalAxisSwathGenerator
    from agriautolab.algorithms.headland.uniform_headland import ConstantWidthHeadland
    from agriautolab.coverage.stages.decomposition import NoDecomposition

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
    baked_ids = {k.removeprefix("rank:") for k in config.params if k.startswith("rank:")}

    # 按 config 自己声明的 decomposition 重放上游，取真实条带 id
    assert config.decomposition == "no_decomposition"
    cells = NoDecomposition().run(problem)
    headland = ConstantWidthHeadland(config.params["headland_width_m"]).run(cells)
    mains = tuple(part for cell in headland.cells for part in cell.main_field)
    replayed = PrincipalAxisSwathGenerator().run(
        mains, working_width_m=VEHICLE.working_width_m, problem=problem,
    )
    replayed_ids = {s.swath_id for s in replayed.swaths}

    assert baked_ids == replayed_ids, (
        f"烘焙 rank 的条带集合与重放不一致：烘焙 {len(baked_ids)} 条、"
        f"重放 {len(replayed_ids)} 条；仅烘焙有={sorted(baked_ids - replayed_ids)}"
    )


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


# ---------- 复核第二轮：质心 / 不变性闸基线与比较口径 ----------

def _rect_problem(problem_id: str, exterior) -> CoverageProblem:
    return CoverageProblem(
        problem_id=problem_id,
        field=PolygonSpec(geometry_id="field", exterior=exterior),
    )


def test_field_centroid_is_encoding_independent() -> None:
    """同一矩形的两种等价编码必须烘焙出相同访问序。

    【证伪力】修复前用外环顶点算术平均当质心：闭合点被重复计数，插入共线冗余
    顶点又会再次改变结果。质心同时是 distance_norm 的初始出口与 projection_norm
    的原点，因此等价编码会得到不同 rank。60×40 矩形写成 (0,0)…(0,0) 时
    顶点平均给 (24,16)，真质心是 (30,20)。
    """
    plain = _rect_problem("plain", (
        Point(x=0.0, y=0.0), Point(x=60.0, y=0.0), Point(x=60.0, y=40.0),
        Point(x=0.0, y=40.0), Point(x=0.0, y=0.0),
    ))
    # 同一个矩形，但每条边中点插入共线冗余顶点——几何完全相同
    redundant = _rect_problem("redundant", (
        Point(x=0.0, y=0.0), Point(x=30.0, y=0.0), Point(x=60.0, y=0.0),
        Point(x=60.0, y=20.0), Point(x=60.0, y=40.0), Point(x=30.0, y=40.0),
        Point(x=0.0, y=40.0), Point(x=0.0, y=20.0), Point(x=0.0, y=0.0),
    ))
    slot = SLOTS["route_order"]
    function = slot.compile(
        "def next_swath_score(state, candidate):\n"
        "    return candidate['distance_norm'] + 0.5 * candidate['projection_norm']\n"
    )

    def ranks_of(problem):
        config = slot.build_config(function, problem, VEHICLE)
        return tuple(
            k.removeprefix("rank:") for k, _ in sorted(
                ((k, v) for k, v in config.params.items() if k.startswith("rank:")),
                key=lambda kv: (kv[1], kv[0]),
            )
        )

    assert ranks_of(plain) == ranks_of(redundant)


def test_invariance_gate_accepts_geometry_equivariant_candidate() -> None:
    """最近邻候选是几何等变的，不变性闸必须放行。

    【证伪力】修复前闸门比较**重新生成的 swath id**：旋转把 PCA 方向推过
    canonical_direction 的半平面边界时，_sweep.py 从地块另一侧开始分配顺序 id，
    同一条物理路线因此得到不同 id 排列，闸门把合法候选判为失败。
    现在改为把访问序映射成条带中心点、逆刚体变换回原坐标后逐点比较。
    """
    slot = SLOTS["route_order"]
    function = slot.compile(
        "def next_swath_score(state, candidate):\n"
        "    return candidate['distance_norm']\n"
    )
    problem = _rect_problem("invariance-ref", (
        Point(x=0.0, y=0.0), Point(x=90.0, y=0.0), Point(x=90.0, y=50.0),
        Point(x=0.0, y=50.0), Point(x=0.0, y=0.0),
    ))
    outcome = slot.invariance_check(function, problem, VEHICLE, np.random.default_rng(20260825))
    assert outcome.passed, outcome.detail


def test_invariance_gate_baseline_is_the_untransformed_geometry() -> None:
    """基线必须来自未变换的原几何，而不是第一个随机变换的结果。

    【证伪力】修复前 base_order 取第一次循环的结果，闸门从不与原始坐标下的路线
    比较——只在原坐标触发分支的候选可以让原始路线与八个扰动路线全都不同却过闸。
    这里统计 _order_for 的调用次数：修复后应为 1（基线）+ 8（扰动）= 9 次，
    且第一次传入的必须是未变换端点（与 _geometry_for 的输出逐点相等）。
    """
    slot = SLOTS["route_order"]
    function = slot.compile(
        "def next_swath_score(state, candidate):\n"
        "    return candidate['distance_norm']\n"
    )
    problem = _rect_problem("baseline-ref", (
        Point(x=0.0, y=0.0), Point(x=90.0, y=0.0), Point(x=90.0, y=50.0),
        Point(x=0.0, y=50.0), Point(x=0.0, y=0.0),
    ))
    untransformed, _c, _n = slot._geometry_for(problem, VEHICLE)

    seen = []
    original = type(slot)._scores_along

    def recording(self, fn, endpoints, order, **kwargs):
        seen.append(endpoints)
        return original(self, fn, endpoints, order, **kwargs)

    type(slot)._scores_along = recording
    try:
        outcome = slot.invariance_check(function, problem, VEHICLE, np.random.default_rng(0))
    finally:
        type(slot)._scores_along = original

    assert outcome.passed, outcome.detail
    assert len(seen) == 9, f"应为 1 次基线 + 8 次扰动，实测 {len(seen)}"
    assert seen[0] == untransformed, "第一次取分必须用未变换的几何做基线"


def test_invariance_gate_rejects_non_invariant_candidate() -> None:
    """使用绝对坐标的候选必须被不变性闸拒绝。

    候选通过 projection_norm 间接读到几何，但真正的非不变量要靠"闸门能否分辨"
    来验证。这里用一个**故意不减质心**的等效构造：候选把 distance_norm 与
    一个随平移改变的量混合——通过 state 无法做到，因此改用可行动作集合之外的
    路径：直接断言闸门对"评分随变换漂移"的响应。
    """
    slot = SLOTS["route_order"]
    problem = _rect_problem("reject-ref", (
        Point(x=0.0, y=0.0), Point(x=90.0, y=0.0), Point(x=90.0, y=50.0),
        Point(x=0.0, y=50.0), Point(x=0.0, y=0.0),
    ))

    class _DriftingFn:
        """每次调用返回略有不同的分数——模拟非不变特征。"""

        def __init__(self) -> None:
            self.calls = 0

        def __call__(self, state, candidate) -> float:
            self.calls += 1
            return candidate["distance_norm"] + self.calls * 1e-3

    outcome = slot.invariance_check(_DriftingFn(), problem, VEHICLE, np.random.default_rng(0))
    assert not outcome.passed
    assert "评分漂移" in outcome.detail


def test_swath_generator_is_not_rigid_equivariant_when_field_rotates() -> None:
    """记录上游性质：旋转**地块**会改变条带的实际位置，不只是 id 重新编号。

    这是不变性闸把刚体变换施加在**条带几何**而非地块上的原因。若照初版旋转地块
    再重跑上游，闸门测的是 PrincipalAxisSwathGenerator 的等变性而不是候选的
    不变性，几何等变的合法候选会被误拒。

    本测试断言这个上游非等变性**确实存在**——它是一条已知局限，不是本槽位的缺陷。
    若将来上游改成等变的，本测试会变红，提示可以简化闸门。
    """
    from shapely.affinity import rotate as shp_rotate, translate as shp_translate

    from agriautolab.geometry.validate import polygon_from_spec, polygon_to_spec

    slot = SLOTS["route_order"]
    problem = _rect_problem("upstream-equivariance", (
        Point(x=0.0, y=0.0), Point(x=90.0, y=0.0), Point(x=90.0, y=50.0),
        Point(x=0.0, y=50.0), Point(x=0.0, y=0.0),
    ))
    base_endpoints, _c, _n = slot._geometry_for(problem, VEHICLE)

    theta, tx, ty = 1.5857, 0.0, 0.0
    cos_t, sin_t = math.cos(theta), math.sin(theta)
    rotated = problem.model_copy(update={
        "field": polygon_to_spec(
            shp_translate(
                shp_rotate(polygon_from_spec(problem.field), theta, origin=(0.0, 0.0), use_radians=True),
                tx, ty,
            ),
            problem.field.geometry_id,
        ),
    })
    moved_endpoints, _c2, _n2 = slot._geometry_for(rotated, VEHICLE)

    def unmove(point):
        px, py = point[0] - tx, point[1] - ty
        return (cos_t * px + sin_t * py, -sin_t * px + cos_t * py)

    def center_set(endpoints):
        return sorted(
            round(sum(c) / 2.0, 3)
            for c in (
                (start[1], end[1]) for start, end in endpoints.values()
            )
        )

    base_ys = center_set(base_endpoints)
    moved_ys = sorted(
        round((unmove(start)[1] + unmove(end)[1]) / 2.0, 3)
        for start, end in moved_endpoints.values()
    )
    assert base_ys != moved_ys, (
        "上游若已变为刚体等变，不变性闸可以简化为直接旋转地块；"
        f"实测 base={base_ys} moved={moved_ys}"
    )


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
