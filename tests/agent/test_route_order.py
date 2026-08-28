"""route_order 槽位真值测试。

每条测试都需在「修复前的实现」下失败——不是覆盖率测试。对应
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


# ---------- 缺陷 1：state 需先投影 ----------

def test_state_dependent_candidate_survives_full_slot_path() -> None:
    """用 state 的候选需能走完 build_config，而不是被闸门淘汰。

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


# ---------- 缺陷 2：烘焙与重放需同一分解 ----------

def test_baked_ranks_match_replayed_swaths_on_obstacle_field() -> None:
    """有障碍田上，烘焙的 rank 键集合需与重放时真实产生的条带 id 集合**精确相等**。

    【证伪力】修复前烘焙走 BoustrophedonDecomposition、返回的 config 却声明
    no_decomposition。本例田上 BCD 产 10 条带、no_decomposition 产 7 条带。

    关键：两种分解的 id 都是顺序 `swath-NNNN`，10 个 id 是 7 个的**超集**，
    因此 RankedSwathOrderPlanner **不会**报「缺 rank 键」——它照跑不误，
    只是把 rank 套到几何上毫不相干的条带（Codex 警告的正是这一半）。
    所以断言需直接比集合，不能只看 run_pipeline 是否抛异常，
    也不能只看 config_id 回填——那两种断言在缺陷下都会通过。
    """
    from agriautolab.algorithms.swath.principal_axis import PrincipalAxisSwathGenerator
    from agriautolab.algorithms.headland.uniform_headland import ConstantWidthHeadland
    from agriautolab.algorithms.decomposition.boustrophedon_cells import BoustrophedonDecomposition

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

    # 按 config 自己声明的 decomposition 重放上游，取真实条带 id。
    # 需是**障碍感知**的分解：no_decomposition 只转发 problem.field、
    # 不带任何 interior，条带因此会横穿障碍（实测 interiors=0）。
    assert config.decomposition == "boustrophedon_cells"
    cells = BoustrophedonDecomposition().run(problem)
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


# ---------- 缺陷 4：投影需减质心（平移不变） ----------

def test_projection_is_translation_invariant() -> None:
    """整体平移后 axis_offset_norm 逐条带不变（质心随之平移）。

    【证伪力】修复前 axis_offset_norm 用绝对坐标投影，平移 (dx,dy) 会给所有条带
    加同一常数。纯按 projection 排序看不出来（同序），但与 distance_norm 混合
    加权的候选（route_mixed）次序会变——本测试同时钉住数值与混合候选次序。
    """
    base = _four_aligned_swaths()
    moved = _four_aligned_swaths(dx=37.0, dy=-19.0)
    p_base = _problem_for(base, centroid=(5.0, 1.5), normal=(0.0, 1.0))
    p_moved = _problem_for(moved, centroid=(5.0 + 37.0, 1.5 - 19.0), normal=(0.0, 1.0))

    proj_base = {a["swath_id"]: a["axis_offset_norm"] for a in p_base.feasible_actions(())}
    proj_moved = {a["swath_id"]: a["axis_offset_norm"] for a in p_moved.feasible_actions(())}
    for swath_id, value in proj_base.items():
        assert proj_moved[swath_id] == pytest.approx(value), f"{swath_id} 投影随平移漂移"

    mixed = lambda state, cand: 0.6 * cand["distance_norm"] + 0.4 * cand["axis_offset_norm"]
    assert _run(p_base, mixed) == _run(p_moved, mixed)


def test_nearest_neighbour_order_is_rigid_transform_invariant() -> None:
    """最近邻候选在刚体变换下访问序不变——质心与主轴法向需一同变换。

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
    """同一矩形的两种等价编码需烘焙出相同访问序。

    【证伪力】修复前用外环顶点算术平均当质心：闭合点被重复计数，插入共线冗余
    顶点又会再次改变结果。质心同时是 distance_norm 的初始出口与 axis_offset_norm
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
    _e1, centroid_plain, _n1 = slot._geometry_for(plain, VEHICLE)
    _e2, centroid_redundant, _n2 = slot._geometry_for(redundant, VEHICLE)

    # 真质心：60×40 矩形是 (30, 20)。顶点算术平均给 (24, 16)（5 点编码）
    # 或 (26.67, 17.78)（9 点编码）——两者都错，且互不相等。
    assert centroid_plain == pytest.approx((30.0, 20.0))
    assert centroid_redundant == pytest.approx((30.0, 20.0))
    assert centroid_plain == pytest.approx(centroid_redundant)


def test_invariance_gate_accepts_geometry_equivariant_candidate_on_asymmetric_field() -> None:
    """最近邻候选是几何等变的，不变性闸需在**非对称**田上也放行。

    【证伪力】闸门若把刚体变换施加在**地块**上再重跑上游，测的就是
    PrincipalAxisSwathGenerator 的等变性而不是候选的不变性。实测该生成器不等变
    （见 test_swath_generator_is_not_rigid_equivariant_when_field_rotates）。

    田形需非对称才有证伪力：90×50 矩形上，"余量换端 + id 从另一侧编号 +
    法向翻转"构成镜像对称，逐 id 的不变键恰好抵消，漂移只有 ~1e-14，
    地块口径也能蒙混过关。改用梯形后实测地块口径漂移 3.1（容差 1e-9）。
    L 形更极端：24 次随机变换里有 10 次连条带集合都不同。
    """
    slot = SLOTS["route_order"]
    function = slot.compile(
        "def next_swath_score(state, candidate):\n"
        "    return candidate['distance_norm']\n"
    )
    trapezoid = _rect_problem("invariance-trapezoid", (
        Point(x=0.0, y=0.0), Point(x=120.0, y=0.0), Point(x=95.0, y=60.0),
        Point(x=10.0, y=60.0), Point(x=0.0, y=0.0),
    ))
    outcome = slot.invariance_check(function, trapezoid, VEHICLE, np.random.default_rng(7))
    assert outcome.passed, outcome.detail


def test_invariance_gate_baseline_is_the_untransformed_geometry() -> None:
    """基线需来自未变换的原几何，而不是第一个随机变换的结果。

    【证伪力】修复前 base_order 取第一次循环的结果，闸门从不与原始坐标下的路线
    比较——只在原坐标触发分支的候选可以让原始路线与八个扰动路线全都不同却过闸。
    这里统计 _order_for 的调用次数：修复后应为 1（基线）+ 8（扰动）= 9 次，
    且第一次传入的需是未变换端点（与 _geometry_for 的输出逐点相等）。
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
    assert seen[0] == untransformed, "第一次取分需用未变换的几何做基线"


def test_invariance_gate_rejects_non_invariant_candidate() -> None:
    """使用绝对坐标的候选需被不变性闸拒绝。

    候选通过 axis_offset_norm 间接读到几何，但真正的非不变量要靠"闸门能否分辨"
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


# ---------- 复核第三轮：闸门忠实度与候选可见面 ----------

def test_candidate_runtime_failure_is_a_rejection_not_a_crash() -> None:
    """候选在契约探针上抛任意异常 → SandboxViolation，而不是掀翻整个实验。

    【证伪力】修复前 compile 只捕 TypeError，别的异常会穿透 compile 与
    contract_gate，**在写任何账本记录之前终止 evolve_pool**。探针的
    axis_offset_norm 恰为 0.0，所以 1.0 / candidate[...] 抛 ZeroDivisionError。
    """
    from agriautolab.agent.sandbox import SandboxViolation

    slot = SLOTS["route_order"]
    with pytest.raises(SandboxViolation, match="ZeroDivisionError"):
        slot.compile(
            "def next_swath_score(state, candidate):\n"
            "    return 1.0 / candidate['axis_offset_norm']\n"
        )


def test_candidate_cannot_see_swath_id() -> None:
    """候选只能看到契约承诺的两个键；swath_id 需被剥掉。

    【证伪力】修复前评分包装器把完整动作字典（含 swath_id）交给候选，
    于是 `float(candidate['swath_id'][-1])` 能过掉不带该键的探针、也能过
    不变性闸（合成变换刻意保留 id），却完全按上游生成器的坐标序号排序。
    """
    from agriautolab.algorithms.route.constructive_order import (
        CANDIDATE_FEATURE_KEYS, candidate_features,
    )

    action = {"swath_id": "swath-0007", "distance_norm": 1.5, "axis_offset_norm": 0.25}
    features = candidate_features(action)
    assert set(features) == set(CANDIDATE_FEATURE_KEYS)
    assert "swath_id" not in features

    # 端到端：按 swath_id 排序的候选在**契约探针**上就拿不到该键 → KeyError，
    # 经修复后的 compile 统一转成 SandboxViolation，候选在第一道闸即被淘汰。
    from agriautolab.agent.sandbox import SandboxViolation

    slot = SLOTS["route_order"]
    with pytest.raises(SandboxViolation, match="KeyError"):
        slot.compile(
            "def next_swath_score(state, candidate):\n"
            "    return float(candidate['swath_id'][-1])\n"
        )


def test_invariance_tolerance_scales_with_score_magnitude() -> None:
    """量级放大 1e9 的等价候选仍须过闸（正数缩放不改变 argmin）。

    【证伪力】修复前用绝对容差 1e-9，`1e9 * distance_norm` 的 ~1e-14 刚体残差
    被放大到 ~1e-5，数学上完全不变的启发式被误拒。
    """
    slot = SLOTS["route_order"]
    trapezoid = _rect_problem("tolerance-scale", (
        Point(x=0.0, y=0.0), Point(x=120.0, y=0.0), Point(x=95.0, y=60.0),
        Point(x=10.0, y=60.0), Point(x=0.0, y=0.0),
    ))
    scaled = slot.compile(
        "def next_swath_score(state, candidate):\n"
        "    return 1e9 * candidate['distance_norm']\n"
    )
    outcome = slot.invariance_check(scaled, trapezoid, VEHICLE, np.random.default_rng(7))
    assert outcome.passed, outcome.detail


def test_gate_reproduces_canonical_axis_orientation() -> None:
    """闸门需复现 canonical_direction 的符号规范化，否则有符号特征会漏网。

    【证伪力】真实构建的法向来自 principal_axis，而后者 return 的就是
    canonical_direction(...)（强制 ux>0）。闸门若只把基线法向旋转（R·n）而不
    重新规范化，就永远走不到符号翻转那一支——一个依赖有符号投影的候选在闸门里
    看着不变，在真实构建里优先方向却整体反转。

    本测试直接断言：对同一批条带，把主轴旋转过半平面边界后，
    _geometry_for 给出的法向与朴素旋转的结果**方向相反**。
    """
    from agriautolab.algorithms.swath._sweep import canonical_direction

    # 单位主轴接近 +x；旋转 ~180° 会把它推过 ux>0 边界
    norm = math.hypot(1.0, 0.05)
    axis = (1.0 / norm, 0.05 / norm)
    theta = math.pi * 0.98
    cos_t, sin_t = math.cos(theta), math.sin(theta)
    naive = (cos_t * axis[0] - sin_t * axis[1], sin_t * axis[0] + cos_t * axis[1])
    canonical = canonical_direction(*naive)
    # 朴素旋转落在左半平面，规范化把它翻回右半平面 → 两者反号
    assert naive[0] < 0.0
    assert canonical[0] > 0.0
    assert canonical[0] == pytest.approx(-naive[0])
    assert canonical[1] == pytest.approx(-naive[1])
    # 由此导出的法向也整体反号——正是有符号投影不成立的原因
    assert (-canonical[1], canonical[0]) == pytest.approx((naive[1], -naive[0]))


def test_gate_uses_canonicalised_normal_for_boundary_crossing_rotations() -> None:
    """闸门喂给候选的法向需是**规范化后**的，与真实构建一致。

    【证伪力】直接断言闸门内部实际使用的法向。修复前它是朴素旋转 R·n；
    当旋转把主轴推过 canonical_direction 的 ux>0 边界时，真实构建拿到的是
    −R·n。本测试用同一串 rng 复算两种期望值，断言：
      (a) 闸门用的与**规范化**期望逐点相等；
      (b) 八次里**至少有一次**两种期望不同——否则本测试没有区分力。

    注意：现在暴露给候选的 axis_offset_norm 取了绝对值，符号翻转对候选评分
    不可观测，因此不能靠「某候选被拒」来证伪。闸门保持忠实是为了将来任何
    符号敏感的特征——这一条需由本测试直接钉住。
    """
    from agriautolab.algorithms.swath._sweep import canonical_direction

    slot = SLOTS["route_order"]
    problem = _rect_problem("canonical-normal", (
        Point(x=0.0, y=0.0), Point(x=90.0, y=0.0), Point(x=90.0, y=50.0),
        Point(x=0.0, y=50.0), Point(x=0.0, y=0.0),
    ))
    function = slot.compile(
        "def next_swath_score(state, candidate):\n"
        "    return candidate['distance_norm']\n"
    )
    _endpoints, _centroid, base_axis = slot._geometry_for(problem, VEHICLE)

    seen_normals = []
    original = type(slot)._scores_along

    def recording(self, fn, endpoints, order, *, vehicle, centroid, normal):
        seen_normals.append(normal)
        return original(self, fn, endpoints, order, vehicle=vehicle, centroid=centroid, normal=normal)

    type(slot)._scores_along = recording
    try:
        slot.invariance_check(function, problem, VEHICLE, np.random.default_rng(11))
    finally:
        type(slot)._scores_along = original

    # 用同一串 rng 复算八组变换的两种法向期望
    rng = np.random.default_rng(11)
    canonical_expected, naive_expected = [], []
    for _ in range(8):
        theta = float(rng.uniform(-math.pi, math.pi))
        rng.uniform(-100.0, 100.0)
        rng.uniform(-100.0, 100.0)
        cos_t, sin_t = math.cos(theta), math.sin(theta)
        rotated_axis = (cos_t * base_axis[0] - sin_t * base_axis[1],
                        sin_t * base_axis[0] + cos_t * base_axis[1])
        cx, cy = canonical_direction(*rotated_axis)
        canonical_expected.append((-cy, cx))
        naive_expected.append((-rotated_axis[1], rotated_axis[0]))

    assert len(seen_normals) == 9, f"应为 1 次基线 + 8 次扰动，实测 {len(seen_normals)}"
    for index, (got, want) in enumerate(zip(seen_normals[1:], canonical_expected)):
        assert got == pytest.approx(want), f"第 {index} 次变换的法向未经规范化"

    differing = sum(
        1 for c, n in zip(canonical_expected, naive_expected)
        if c != pytest.approx(n)
    )
    assert differing > 0, "本 seed 下没有任何旋转跨过半平面边界，测试失去区分力"


def test_all_route_mock_candidates_pass_the_faithful_gate() -> None:
    """四个出货 mock 候选在**忠实**闸门下都需过。

    加入 canonical_direction 后，原先用**有符号** projection_norm 的两个候选
    （route_projection_order / route_mixed）立刻在梯形与矩形田上双双失败，
    漂移达 2.5–3.6（容许 ~1e-9）——这证明有符号投影根本不是不变量。
    修法是让特征本身变成不变量（axis_offset_norm 取绝对值），
    而不是放松闸门。本测试钉住修法之后四个候选全部通过。
    """
    from agriautolab.agent.proposer import MOCK_CANDIDATES_BY_SLOT

    slot = SLOTS["route_order"]
    trapezoid = _rect_problem("mock-gate", (
        Point(x=0.0, y=0.0), Point(x=120.0, y=0.0), Point(x=95.0, y=60.0),
        Point(x=10.0, y=60.0), Point(x=0.0, y=0.0),
    ))
    for candidate in MOCK_CANDIDATES_BY_SLOT["route_order"]:
        function = slot.compile(candidate.source_code)
        for seed in (0, 7, 20260825):
            outcome = slot.invariance_check(function, trapezoid, VEHICLE, np.random.default_rng(seed))
            assert outcome.passed, f"{candidate.algorithm_id} seed={seed}: {outcome.detail}"


def test_tie_at_the_selected_minimum_is_rejected() -> None:
    """最优分并列即拒——真正被 swath_id 决定的是**选中哪一条**，不是全体是否同分。

    【证伪力】此前的检查只拒「每一步所有动作都同分」。但 `axis_offset_norm` 取绝对
    值后，关于主轴对称的两条条带**系统性同分**，而其余条带分数不同——这类候选能过
    旧检查，可实际选中哪一条仍由 `feasible_actions` 的 swath_id 枚举序决定，
    且该序在扫掠方向翻转时反转空间对应。判定需落在**被选中的那一步的最小值**上。
    """
    slot = SLOTS["route_order"]
    trapezoid = _rect_problem("tie-at-min", (
        Point(x=0.0, y=0.0), Point(x=120.0, y=0.0), Point(x=95.0, y=60.0),
        Point(x=10.0, y=60.0), Point(x=0.0, y=0.0),
    ))
    # 关键锚点：**只在最优处并列、别处不并列**。量化距离制造这种形态——
    # 旧的「全体同分才拒」检查会放行它，新的「最优分并列即拒」抓得住。
    # 实测该候选在 90×50 / 120×80 / 梯形三块田上都是这个形态。
    quantised = slot.compile(
        "def next_swath_score(state, candidate):\n"
        "    return float(int(candidate['distance_norm']))\n"
    )
    outcome = slot.invariance_check(quantised, trapezoid, VEHICLE, np.random.default_rng(0))
    assert not outcome.passed
    assert "最优分并列" in outcome.detail

    # 恒定候选（全体同分）当然也要拒
    constant = slot.compile(
        "def next_swath_score(state, candidate):\n"
        "    return 0.0\n"
    )
    assert not slot.invariance_check(constant, trapezoid, VEHICLE, np.random.default_rng(0)).passed

    # 分数各不相同的候选不受影响
    distinct = slot.compile(
        "def next_swath_score(state, candidate):\n"
        "    return candidate['distance_norm']\n"
    )
    outcome2 = slot.invariance_check(distinct, trapezoid, VEHICLE, np.random.default_rng(0))
    assert outcome2.passed, outcome2.detail


def test_scored_state_is_recreated_for_every_action() -> None:
    """闸门取分时每个动作都要拿新的投影状态，与真实构造路径一致。

    【证伪力】此前 `_scores_along` 每步只造一次投影 dict 并在该步所有动作间共用，
    而真实构造路径逐次调用 `project_state`。于是一个自增 `state["visited_count"]`
    并返回它的候选，在真实路径上产生全并列、在闸门里却产生递增分数——它因此
    绕过并列拒绝、通过不变性比较，而实际部署的路线仍完全由 swath_id 决定。
    """
    slot = SLOTS["route_order"]
    trapezoid = _rect_problem("fresh-state", (
        Point(x=0.0, y=0.0), Point(x=120.0, y=0.0), Point(x=95.0, y=60.0),
        Point(x=10.0, y=60.0), Point(x=0.0, y=0.0),
    ))
    mutating = slot.compile(
        "def next_swath_score(state, candidate):\n"
        "    state['visited_count'] = state['visited_count'] + 1.0\n"
        "    return state['visited_count']\n"
    )
    endpoints, centroid, axis = slot._geometry_for(trapezoid, VEHICLE)
    normal = slot._normal_of(axis)
    order = slot._order_for(mutating, endpoints, vehicle=VEHICLE, centroid=centroid, normal=normal)
    scores = slot._scores_along(mutating, endpoints, order,
                                vehicle=VEHICLE, centroid=centroid, normal=normal)
    first = scores[0]
    assert len(first) > 1
    assert len(set(first.values())) == 1, (
        f"共用投影 dict 会让分数递增；实测 {first}"
    )
    # 因此该候选应当被并列拒绝抓到，而不是蒙混过关
    outcome = slot.invariance_check(mutating, trapezoid, VEHICLE, np.random.default_rng(0))
    assert not outcome.passed
    assert "最优分并列" in outcome.detail


def test_reviewer_does_not_invoke_the_candidate_twice() -> None:
    """复核器拼装成功理由时不得二次调用候选。

    【证伪力】此前成功分支在 return 里又跑了一遍探针。一个第一遍成功、第二遍抛
    KeyError 的候选（例如自己 pop 掉某键）会在那个**无保护**的格式化调用里把异常
    抛出复核器之外，穿透 evolve_pool 并在写账本记录之前终止实验。
    """
    from agriautolab.agent.proposer import ProposalCandidate
    from agriautolab.agent.reviewer import ROUTE_REVIEWERS

    calls = {"n": 0}

    def flaky(state, candidate):
        calls["n"] += 1
        if calls["n"] > 3:                    # 前三次（三个探针）成功，之后炸
            raise KeyError("distance_norm")
        return candidate["distance_norm"]

    verdict = ROUTE_REVIEWERS[0].review(
        ProposalCandidate(algorithm_id="flaky", source_code="", description=""), flaky,
    )
    assert not verdict.refuted, verdict.reasons
    assert calls["n"] == 3, f"候选应恰好被调用 3 次（每探针一次），实测 {calls['n']}"


def test_reviewer_probes_are_fresh_per_call() -> None:
    """复核器的探针也需传副本，否则先跑的候选会污染后面的。"""
    from agriautolab.agent.proposer import ProposalCandidate
    from agriautolab.agent.reviewer import ROUTE_REVIEWERS, RouteOrderCorrectnessReviewer

    def poisoner(state, candidate):
        candidate.pop("distance_norm", None)
        return 0.0

    ROUTE_REVIEWERS[0].review(
        ProposalCandidate(algorithm_id="p", source_code="", description=""), poisoner,
    )
    for _state, action in RouteOrderCorrectnessReviewer.PROBES:
        assert "distance_norm" in action, "复核器探针常量被候选改写了"


def test_probe_inputs_are_fresh_per_call() -> None:
    """候选改写入参不能污染后续候选。

    【证伪力】沙箱不不得候选改写 dict 入参。此前探针直接传类级常量，
    `candidate.pop("distance_norm")` 会永久掏空它，之后所有正常使用该键的候选都
    在探针上抛 KeyError 被拒——「候选能否通过」取决于它在提议序列里排第几。
    """
    slot = SLOTS["route_order"]
    poisoner = slot.compile(
        "def next_swath_score(state, candidate):\n"
        "    candidate.pop('distance_norm', None)\n"
        "    state.pop('remaining_count', None)\n"
        "    return 0.0\n"
    )
    slot.probe_value(poisoner, _rect_problem("poison", (
        Point(x=0.0, y=0.0), Point(x=60.0, y=0.0), Point(x=60.0, y=40.0),
        Point(x=0.0, y=40.0), Point(x=0.0, y=0.0),
    )), VEHICLE)

    # 模板未被改写：正常候选照常拿到两个键
    normal = slot.compile(
        "def next_swath_score(state, candidate):\n"
        "    return candidate['distance_norm'] + state['remaining_count']\n"
    )
    state, candidate = type(slot)._probe_inputs()
    assert set(candidate) == {"distance_norm", "axis_offset_norm"}
    assert "remaining_count" in state
    assert math.isfinite(normal(state, candidate))


def test_overflow_during_score_coercion_is_a_rejection() -> None:
    """float(score) 溢出需转成拒绝，而不是穿透闸门终止实验。

    【证伪力】此前 `float(value)` 在保护块之外：候选返回 `10 ** 10000` 时两次函数
    调用都成功，却在转换处抛 OverflowError；而 contract_gate 只捕
    SandboxViolation / ValueError / TypeError，异常仍会终止 evolve_pool。
    """
    slot = SLOTS["route_order"]
    huge = slot.compile(
        "def next_swath_score(state, candidate):\n"
        "    return 10 ** 10000\n"
    )
    with pytest.raises(ValueError, match="OverflowError"):
        slot.probe_value(huge, _rect_problem("overflow", (
            Point(x=0.0, y=0.0), Point(x=60.0, y=0.0), Point(x=60.0, y=40.0),
            Point(x=0.0, y=40.0), Point(x=0.0, y=0.0),
        )), VEHICLE)


def test_per_instance_failure_does_not_abort_the_run() -> None:
    """候选在探针实例外的某个实例上抛异常 → 该实例记 None，账本照记，实验不崩。

    【证伪力】四道闸只跑单个探针实例；此前 _candidate_points 是无保护列表推导，
    后续实例的异常会穿过 evolve_pool 并在写账本记录**之前**终止整个实验。
    """
    from agriautolab.agent.evolve import _candidate_points

    slot = SLOTS["route_order"]
    function = slot.compile(
        "def next_swath_score(state, candidate):\n"
        "    return candidate['distance_norm']\n"
    )
    instance = make_instance()
    protocol = make_protocol(instance)
    calls = {"n": 0}

    def exploding_run(*args, **kwargs):
        calls["n"] += 1
        raise RuntimeError("第二个实例上炸了")

    points = _candidate_points(function, (instance,), protocol, slot, run=exploding_run)
    assert points == [None], "失败实例应记 None 而不是抛出"
    assert calls["n"] == 1


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
