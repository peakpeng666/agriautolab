"""RouteOrderProblem：把"条带访问序选择"适配到公共 ConstructiveProblem 协议。

领域 adapter（放农业侧 / src/agriautolab/algorithms/route/）的反方向是
架构错误：optimization/ 不得 import 农业（见 docs/ARCHITECTURE.md 的
依赖纪律）。本模块 import 公共协议 src/agriautolab/optimization/constructive.py，
由它单向流到 heuristics；不反向。

状态 / 动作 / 投影映射口径：
  StateT = tuple[str, ...]        # 已访问 swath_id 序列
  ActionT = str                    # 下一个要访问的 swath_id
  SolutionT = tuple[str, ...]      # 完整访问序列（swath_id 元组）
  initial = ()
  feasible_actions(state) = 未访问 swath_id 按 swath_id 稳定排序的 tuple
  apply_action(state, action) = state + (action,)（action 必须 ∈ feasible）
  finalize(state) = state
  方向约定：第 i 个访问（0 基）偶数 FORWARD、奇数 REVERSE，沿用
  BoustrophedonRoutePlanner 的 index%2 交替纪律（boustrophedon_order.py:32）。

投影函数（领域对象 -> Mapping[str, float]，只用旋转不变键）：
  state -> visited_count, remaining_count
  candidate -> distance_norm（出口→条带入口距离/min_turning_radius）、
               projection_norm（条带中心在主轴法向的投影/working_width）

独立 evaluator evaluate_route_order(swaths, visit_order, start_position)：
  不复用构造过程的任何累计值；从 swath 中心线端点几何独立复算总转移距离。
  访问序必须严格是 swaths 全体 swath_id 的置换，否则 ValueError（fail-closed）。
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from agriautolab.optimization.constructive import (
    ConstructiveProblem, ConstructionError,
)


@dataclass(frozen=True)
class _HeuristicShim:
    """把沙箱里的 next_turn_score(state, candidate) 包成 ConstructiveHeuristic。

    heuristic_id="candidate"：独立 evaluator 不看 id，但记日志有用。
    """

    heuristic_id: str = "candidate"

    def score(self, state: Mapping[str, float], action: Mapping[str, float]) -> float:
        # 实际评分由 slot.build_config 注入的源码函数在沙箱里执行；
        # shim 仅作为公共 engine 的占位——本路径实际走的是 construct_solution
        # 调 _finite_score(heuristic, ...) 时本类的 score() 被调到的版本。
        raise ConstructionError(
            "RouteOrderProblem 必须通过 construct_solution 注入实际的沙箱评分函数；"
            "本 shim 仅供 construct_solution 内部使用，不应被直接调用"
        )


def _projection_from_visit_index(visit_index: int) -> str:
    """第 i 个访问（0 基）偶数 FORWARD、奇数 REVERSE——与 boustrophedon_order 同源。"""
    return "FORWARD" if visit_index % 2 == 0 else "REVERSE"


def _swath_entry(swath_centerline_points) -> tuple[float, float]:
    """取条带中心线起点的 x, y 作为入口。"""
    p0 = swath_centerline_points[0]
    return (float(p0.x), float(p0.y))


def _swath_exit(swath_centerline_points) -> tuple[float, float]:
    """取条带中心线终点的 x, y 作为出口。"""
    p1 = swath_centerline_points[-1]
    return (float(p1.x), float(p1.y))


class RouteOrderProblem(ConstructiveProblem[tuple[str, ...], dict, tuple[str, ...]]):
    """条带访问序的构造式问题。

    ActionT = dict：候选动作包含 swath_id + 旋转不变键（distance_norm /
    projection_norm），候选评分函数 next_turn_score(state, candidate) 直接
    拿到这个 dict。apply_action 校验 dict["swath_id"] ∈ feasible。

    字段：
      all_swath_ids: 全体 swath_id 元组（顺序由调用方保证稳定）
      min_turning_radius_m: 用于 distance_norm 归一
      working_width_m: 用于 projection_norm 归一
      field_centroid: 初始"出口位置"=地块质心（写在 docstring 起点）
      principal_normal: 地块主轴法向单位向量（nx, ny），用于 projection_norm
        （主轴法向随刚体变换协变，投影值不变——这是旋转不变键的关键）
    """

    def __init__(
        self,
        all_swath_ids: Sequence[str],
        *,
        min_turning_radius_m: float,
        working_width_m: float,
        field_centroid: tuple[float, float],
        principal_normal: tuple[float, float],
    ) -> None:
        if not all_swath_ids:
            raise ValueError("all_swath_ids 不能为空")
        if min_turning_radius_m <= 0.0:
            raise ValueError("min_turning_radius_m 必须 > 0")
        if working_width_m <= 0.0:
            raise ValueError("working_width_m 必须 > 0")
        nx, ny = principal_normal
        norm = math.hypot(nx, ny)
        if norm == 0.0:
            raise ValueError("principal_normal 不能为零向量")
        # 归一保证投影值与单位无关
        self._all_swath_ids = tuple(all_swath_ids)
        self._min_turning_radius_m = float(min_turning_radius_m)
        self._working_width_m = float(working_width_m)
        self._field_centroid = (float(field_centroid[0]), float(field_centroid[1]))
        self._principal_normal = (nx / norm, ny / norm)

    # -- ConstructiveProblem 五方法 --

    def initial_state(self) -> tuple[str, ...]:
        return ()

    def is_complete(self, state: tuple[str, ...]) -> bool:
        return len(state) == len(self._all_swath_ids)

    def feasible_actions(self, state: tuple[str, ...]) -> tuple[dict, ...]:
        """返回候选 dict 列表：每个 dict 含 swath_id + 旋转不变键。

        出口位置：初始为 field_centroid；之后随 apply_action 推到当前 swath
        终点（由 update_exit 显式推进）。距离归一用 min_turning_radius_m。
        """
        visited = set(state)
        exit_pos = self._current_exit(state)
        entry_positions = getattr(self, "_entry_positions", {})
        centers = getattr(self, "_centers", {})
        actions: list[dict] = []
        for swath_id in self._all_swath_ids:
            if swath_id in visited:
                continue
            entry = entry_positions.get(swath_id, (0.0, 0.0))
            center = centers.get(swath_id, (0.0, 0.0))
            actions.append(project_candidate(
                candidate_swath_id=swath_id,
                exit_position=exit_pos,
                swath_entry_position=entry,
                swath_center_position=center,
                min_turning_radius_m=self._min_turning_radius_m,
                working_width_m=self._working_width_m,
                principal_normal=self._principal_normal,
            ))
        return tuple(actions)

    def _current_exit(self, state: tuple[str, ...]) -> tuple[float, float]:
        """当前"出口"位置：state 为空 → field_centroid；否则最后访问 swath 的终点。"""
        if not state:
            return self._field_centroid
        # 由 build_config 注入 _exit_positions dict；测试/裸用时回退到 centroid
        positions = getattr(self, "_exit_positions", None)
        if positions and state[-1] in positions:
            return positions[state[-1]]
        return self._field_centroid

    def apply_action(self, state: tuple[str, ...], action: dict) -> tuple[str, ...]:
        feasible = self.feasible_actions(state)
        if action not in feasible:
            raise ValueError(
                f"apply_action 拒绝越界：action={action!r} 不在 feasible_actions"
                f"({feasible!r})"
            )
        return state + (action["swath_id"],)

    def finalize(self, state: tuple[str, ...]) -> tuple[str, ...]:
        return state


# ---- 投影：领域对象 -> 旋转不变键的 Mapping ----

def project_state(
    state: tuple[str, ...],
    *,
    total_swath_count: int,
) -> dict[str, float]:
    """状态投影：已访问 / 未访问计数（无量纲，旋转平移缩放全不变）。"""
    return {
        "visited_count": float(len(state)),
        "remaining_count": float(total_swath_count - len(state)),
    }


def project_candidate(
    *,
    candidate_swath_id: str,
    exit_position: tuple[float, float],
    swath_entry_position: tuple[float, float],
    swath_center_position: tuple[float, float],
    min_turning_radius_m: float,
    working_width_m: float,
    principal_normal: tuple[float, float],
) -> dict[str, float]:
    """候选投影：distance_norm + projection_norm（都旋转不变）+ swath_id。

    distance_norm = 出口到条带入口欧氏距离 / min_turning_radius_m
    projection_norm = 条带中心在主轴法向上的投影 / working_width_m
    """
    dx = swath_entry_position[0] - exit_position[0]
    dy = swath_entry_position[1] - exit_position[1]
    distance = math.hypot(dx, dy)
    nx, ny = principal_normal
    proj = ((swath_center_position[0] - 0.0) * nx + (swath_center_position[1] - 0.0) * ny)
    return {
        "swath_id": candidate_swath_id,
        "distance_norm": distance / min_turning_radius_m,
        "projection_norm": proj / working_width_m,
    }


# ---- 独立 evaluator：复算总转移距离（不复用构造过程） ----

def evaluate_route_order(
    swaths: Sequence,
    visit_order: Sequence[str],
    start_position: tuple[float, float],
) -> float:
    """独立复算总转移距离。

    纪律：先断言 visit_order 是 swaths 全体 swath_id 的**精确置换**；
    再从 swath 中心线端点几何独立复算总距离；**不复用**构造过程的任何
    累计值（构造过程只累计 visited set，不累计距离——见 RouteOrderProblem
    apply_action）。

    返回总转移距离（米）。
    """
    all_ids = tuple(swath.swath_id for swath in swaths)
    if set(visit_order) != set(all_ids):
        raise ValueError(
            f"evaluate_route_order 拒绝非置换访问序："
            f"visit_order={tuple(visit_order)!r} vs all_swath_ids={all_ids!r}"
        )
    if not swaths:
        return 0.0
    by_id = {swath.swath_id: swath for swath in swaths}
    current = (float(start_position[0]), float(start_position[1]))
    total = 0.0
    for swath_id in visit_order:
        entry = _swath_entry(by_id[swath_id].centerline.points)
        dx = entry[0] - current[0]
        dy = entry[1] - current[1]
        total += math.hypot(dx, dy)
        current = _swath_exit(by_id[swath_id].centerline.points)
    return total
