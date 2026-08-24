"""欧氏 TSP 的构造状态机与独立评价器。

求解与评价严格分离：构造器只产生闭合 tour，`evaluate_tsp_tour` 再从问题几何
独立复算总长度。无论启发式来自人工规则还是 LLM，都不能自报目标值。
"""

from __future__ import annotations

from dataclasses import dataclass

from agriautolab.contracts.routing import RoutingNode, TSPProblem
from agriautolab.optimization.routing import route_length_m


@dataclass(frozen=True)
class TSPState:
    """最近邻类构造器所需的最小状态。"""

    current_node_id: str
    unvisited_node_ids: tuple[str, ...]
    visit_order: tuple[str, ...]


@dataclass(frozen=True)
class TSPTour:
    """闭合 TSP 回路；起点在首尾各出现一次。"""

    node_ids: tuple[str, ...]


@dataclass(frozen=True)
class TSPEvaluation:
    """由独立 evaluator 复算的 TSP 指标。"""

    tour_length_m: float


class TSPConstructiveProblem:
    """把 `TSPProblem` 适配为逐节点选择的 constructive problem。"""

    def __init__(self, problem: TSPProblem) -> None:
        self.problem = problem
        self._nodes = {node.node_id: node for node in problem.nodes}

    def node(self, node_id: str) -> RoutingNode:
        return self._nodes[node_id]

    def initial_state(self) -> TSPState:
        unvisited = tuple(sorted(
            node_id for node_id in self._nodes if node_id != self.problem.start_node_id
        ))
        return TSPState(
            current_node_id=self.problem.start_node_id,
            unvisited_node_ids=unvisited,
            visit_order=(self.problem.start_node_id,),
        )

    def is_complete(self, state: TSPState) -> bool:
        return not state.unvisited_node_ids

    def feasible_actions(self, state: TSPState) -> tuple[str, ...]:
        # `initial_state` 已按 node_id 排序；后续只做稳定过滤，因此平局顺序可复现。
        return state.unvisited_node_ids

    def apply_action(self, state: TSPState, action: str) -> TSPState:
        if action not in state.unvisited_node_ids:
            raise ValueError(f"TSP 动作不是未访问节点：{action!r}")
        remaining = tuple(node_id for node_id in state.unvisited_node_ids if node_id != action)
        return TSPState(
            current_node_id=action,
            unvisited_node_ids=remaining,
            visit_order=state.visit_order + (action,),
        )

    def finalize(self, state: TSPState) -> TSPTour:
        if not self.is_complete(state):
            raise ValueError("TSP 尚未访问完全部节点，不能生成最终回路")
        return TSPTour(node_ids=state.visit_order + (self.problem.start_node_id,))


def evaluate_tsp_tour(problem: TSPProblem, tour: TSPTour) -> TSPEvaluation:
    """验证 Hamiltonian cycle 后独立复算欧氏总长度。"""
    expected_node_ids = {node.node_id for node in problem.nodes}
    if len(tour.node_ids) != len(problem.nodes) + 1:
        raise ValueError("TSP 回路长度必须等于节点数 + 1（闭合起点）")
    if tour.node_ids[0] != problem.start_node_id or tour.node_ids[-1] != problem.start_node_id:
        raise ValueError("TSP 回路必须从 start_node_id 出发并回到该节点")

    visited_once = tour.node_ids[:-1]
    if set(visited_once) != expected_node_ids or len(set(visited_once)) != len(problem.nodes):
        raise ValueError("TSP 回路必须且只能访问每个节点一次")

    nodes_by_id = {node.node_id: node for node in problem.nodes}
    return TSPEvaluation(tour_length_m=route_length_m(nodes_by_id, tour.node_ids))
