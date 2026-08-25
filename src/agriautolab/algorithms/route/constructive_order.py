"""RouteOrderProblem：把「条带访问序选择」适配到公共 ConstructiveProblem 协议。

领域 adapter 放农业侧（`src/agriautolab/algorithms/route/`），反方向是架构错误：
`optimization/` 不得 import 农业 `pipeline/`（见 docs/ARCHITECTURE.md 依赖纪律）。
本模块单向 import 公共协议 `src/agriautolab/optimization/constructive.py`。

状态 / 动作 / 投影口径：
  StateT    = tuple[str, ...]   已访问 swath_id 序列
  ActionT   = dict              候选条带的 swath_id + 旋转平移不变键
  SolutionT = tuple[str, ...]   完整访问序列
  feasible_actions(state) = 未访问条带按 swath_id 稳定排序（协议硬要求）
  apply_action(state, action)  action 必须 ∈ feasible，否则 ValueError（fail-closed）

**行进方向与端点（关键）**：第 i 个访问（0 基）偶数 FORWARD、奇数 REVERSE，
与 `RankedSwathOrderPlanner` 及 `BoustrophedonRoutePlanner` 同源。因此：
  FORWARD 从 centerline.points[0] 进、points[-1] 出；
  REVERSE 从 centerline.points[-1] 进、points[0] 出。
入口/出口必须按访问序奇偶取端点——否则候选评的转移几何与路线实际走的不是同一条，
`distance_norm` 会从错误的一端量起。

投影键（都必须旋转+平移不变）：
  distance_norm   = 上一条带出口 → 本条带入口 的欧氏距离 / min_turning_radius_m
  projection_norm = （条带中心 − 地块质心）在主轴法向上的投影 / working_width_m
                    减去质心是平移不变的前提：不减则整体平移会给所有投影加同一常数，
                    纯排序看似不变，但与 distance_norm 混合加权的候选会改变次序。
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

from agriautolab.optimization.constructive import ConstructiveProblem

# (start_xy, end_xy)：条带中心线两端，几何原样，不预设行进方向
SwathEndpoints = tuple[tuple[float, float], tuple[float, float]]


def endpoints_of(swath) -> SwathEndpoints:
    """从 swath 的中心线取两端端点，不预设方向。"""
    points = swath.centerline.points
    first, last = points[0], points[-1]
    return ((float(first.x), float(first.y)), (float(last.x), float(last.y)))


def is_forward(visit_index: int) -> bool:
    """第 i 个访问（0 基）偶数 FORWARD、奇数 REVERSE——与 route planner 同源。"""
    return visit_index % 2 == 0


def entry_of(endpoints: SwathEndpoints, visit_index: int) -> tuple[float, float]:
    """按访问序奇偶取入口端点。"""
    start, end = endpoints
    return start if is_forward(visit_index) else end


def exit_of(endpoints: SwathEndpoints, visit_index: int) -> tuple[float, float]:
    """按访问序奇偶取出口端点。REVERSE 从 points[0] 出，不是 points[-1]。"""
    start, end = endpoints
    return end if is_forward(visit_index) else start


def center_of(endpoints: SwathEndpoints) -> tuple[float, float]:
    """条带中心 = 两端中点。"""
    (x0, y0), (x1, y1) = endpoints
    return ((x0 + x1) / 2.0, (y0 + y1) / 2.0)


def project_state(state: tuple[str, ...], *, total_swath_count: int) -> dict[str, float]:
    """状态投影：已访问 / 未访问计数（无量纲，刚体变换与缩放全不变）。

    候选契约函数 `next_swath_score(state, candidate)` 拿到的 state **必须**是本函数
    的输出，而不是原始 `tuple[str, ...]`——否则任何使用 `state.get(...)` 的候选都会
    在构造期抛异常并被闸门淘汰，槽位静默退化成 action-only 启发式。
    """
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
    field_centroid: tuple[float, float],
    min_turning_radius_m: float,
    working_width_m: float,
    principal_normal: tuple[float, float],
) -> dict[str, float]:
    """候选投影：swath_id + distance_norm + projection_norm（后两者刚体变换不变）。"""
    dx = swath_entry_position[0] - exit_position[0]
    dy = swath_entry_position[1] - exit_position[1]
    distance = math.hypot(dx, dy)
    nx, ny = principal_normal
    # 先减地块质心再投影：平移不变的前提（见模块 docstring）
    cx = swath_center_position[0] - field_centroid[0]
    cy = swath_center_position[1] - field_centroid[1]
    return {
        "swath_id": candidate_swath_id,
        "distance_norm": distance / min_turning_radius_m,
        "projection_norm": (cx * nx + cy * ny) / working_width_m,
    }


class RouteOrderProblem(ConstructiveProblem[tuple[str, ...], dict, tuple[str, ...]]):
    """条带访问序的构造式问题。

    几何由构造函数**必填**注入（`swath_endpoints`）。此前用 `setattr` 事后打补丁 +
    `getattr(..., {})` 回退到原点是 fail-open：几何缺失时所有 distance_norm 都从
    (0,0) 量起，候选照跑不误却在优化一个不存在的几何。现在缺几何直接 ValueError。
    """

    def __init__(
        self,
        swath_endpoints: Mapping[str, SwathEndpoints],
        *,
        min_turning_radius_m: float,
        working_width_m: float,
        field_centroid: tuple[float, float],
        principal_normal: tuple[float, float],
    ) -> None:
        if not swath_endpoints:
            raise ValueError("swath_endpoints 不能为空")
        if min_turning_radius_m <= 0.0:
            raise ValueError("min_turning_radius_m 必须 > 0")
        if working_width_m <= 0.0:
            raise ValueError("working_width_m 必须 > 0")
        nx, ny = principal_normal
        norm = math.hypot(nx, ny)
        if norm == 0.0:
            raise ValueError("principal_normal 不能为零向量")

        self._endpoints = dict(swath_endpoints)
        # 稳定顺序：swath_id 字典序。公共 engine 用枚举顺序处理评分并列。
        self._all_swath_ids = tuple(sorted(self._endpoints))
        self._min_turning_radius_m = float(min_turning_radius_m)
        self._working_width_m = float(working_width_m)
        self._field_centroid = (float(field_centroid[0]), float(field_centroid[1]))
        self._principal_normal = (nx / norm, ny / norm)

    @property
    def all_swath_ids(self) -> tuple[str, ...]:
        return self._all_swath_ids

    # -- ConstructiveProblem 五方法 --

    def initial_state(self) -> tuple[str, ...]:
        return ()

    def is_complete(self, state: tuple[str, ...]) -> bool:
        return len(state) == len(self._all_swath_ids)

    def _current_exit(self, state: tuple[str, ...]) -> tuple[float, float]:
        """当前出口：state 为空 → 地块质心；否则上一条带按**其访问序奇偶**的出口端点。"""
        if not state:
            return self._field_centroid
        last_index = len(state) - 1
        return exit_of(self._endpoints[state[last_index]], last_index)

    def feasible_actions(self, state: tuple[str, ...]) -> tuple[dict, ...]:
        visited = set(state)
        exit_pos = self._current_exit(state)
        next_index = len(state)   # 下一条带的访问序号，决定它的进入端点
        return tuple(
            project_candidate(
                candidate_swath_id=swath_id,
                exit_position=exit_pos,
                swath_entry_position=entry_of(self._endpoints[swath_id], next_index),
                swath_center_position=center_of(self._endpoints[swath_id]),
                field_centroid=self._field_centroid,
                min_turning_radius_m=self._min_turning_radius_m,
                working_width_m=self._working_width_m,
                principal_normal=self._principal_normal,
            )
            for swath_id in self._all_swath_ids
            if swath_id not in visited
        )

    def apply_action(self, state: tuple[str, ...], action: dict) -> tuple[str, ...]:
        """按 swath_id 校验动作可行性。

        比 swath_id 而非整个 dict：动作字典含浮点投影值，逐字段相等比较会被
        重算噪声影响；身份判定只应看 swath_id。
        """
        if not isinstance(action, Mapping) or "swath_id" not in action:
            raise ValueError(f"apply_action 拒绝非法动作（缺 swath_id）：{action!r}")
        swath_id = action["swath_id"]
        feasible_ids = tuple(item["swath_id"] for item in self.feasible_actions(state))
        if swath_id not in feasible_ids:
            raise ValueError(
                f"apply_action 拒绝越界：swath_id={swath_id!r} 不在当前可行集 {feasible_ids!r}"
            )
        return state + (swath_id,)

    def finalize(self, state: tuple[str, ...]) -> tuple[str, ...]:
        if not self.is_complete(state):
            raise ValueError("访问序尚未覆盖全部条带，不能 finalize")
        return state


def evaluate_route_order(
    swaths: Sequence,
    visit_order: Sequence[str],
    start_position: tuple[float, float],
) -> float:
    """独立复算总转移距离（米）。

    纪律（对照 optimization/cvrp.py 的 `_exact_route_demand`）：先断言 visit_order 是
    全体 swath_id 的**精确置换**，再从条带端点几何独立复算；**不复用**构造过程的任何
    累计值或投影缓存。端点按访问序奇偶取，与 `RankedSwathOrderPlanner` 的
    FORWARD/REVERSE 交替一致——否则复算的是一条路线，实际走的是另一条。
    """
    all_ids = tuple(swath.swath_id for swath in swaths)
    order = tuple(visit_order)
    if sorted(order) != sorted(all_ids):
        raise ValueError(
            f"evaluate_route_order 拒绝非置换访问序：visit_order={order!r} vs all_swath_ids={all_ids!r}"
        )
    if not all_ids:
        return 0.0

    endpoints = {swath.swath_id: endpoints_of(swath) for swath in swaths}
    current = (float(start_position[0]), float(start_position[1]))
    total = 0.0
    for visit_index, swath_id in enumerate(order):
        ends = endpoints[swath_id]
        entry = entry_of(ends, visit_index)
        total += math.hypot(entry[0] - current[0], entry[1] - current[1])
        current = exit_of(ends, visit_index)
    return total
