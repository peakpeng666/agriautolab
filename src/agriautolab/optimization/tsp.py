"""欧氏 TSP 的构造状态机与独立评价器。

求解过程与评价过程分离：构造器只产生闭合 tour，`evaluate_tsp_tour` 再从问题几何
独立复算总长度。这样后续无论启发式来自人工规则还是 LLM，都不能自报目标值。
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from agriautolab.contracts.routing import RoutingNode, TSPProblem


@dataclass(frozen=True)
class TSPState:
    current_node_id: str
    unvisited_node_ids: tuple[str, ...]
    visit_order: tuple[str, ...]


@dataclass(frozen=True)
class TSPTour:
    """闭合 TSP 回路；起点在首尾各出现一次。"""

    node_ids: tuple[str, ...]


@dataclass(frozen=True)
class TSPEvaluation:
    tour_length: float


def euclidean_distance(left: RoutingNode, right: RoutingNode) -> float:
    return math.hypot(left.position.x - right.position.x, left.position.y - right.position.y)


class TSPConstructiveProblem:
    """把 `TSPProblem` 适配为逐节点选择的 constructive problem。"""

    def __init__(self, problem: TSPProblem) -> None:
        self.problem = problem
        self._nodes = {node.node_id: node for node in problem.nodes}

    def node(self, node_id: str) -> RoutingNode:
        return self._nodes[node_id]

    def initial_state(self) -> TSPState:
        unvisited = tuple(sorted(node_id for node_id in self._nodes if node_id != self.problem.start_node_id))
        return TSPState(
            current_node_id=self.problem.start_node_id,
            unvisited_node_ids=unvisited,
            visit_order=(self.problem.start_node_id,),
        )

    def is_complete(self, state: TSPState) -> bool:
        return not state.unvisited_node_ids

    def feasible_actions(self, state: TSPState) -> tuple[str, ...]:
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
    """校验 Hamiltonian cycle 后独立复算欧氏总长度。"""
    expected = {node.node_id for node in problem.nodes}
    if len(tour.node_ids) != len(problem.nodes) + 1:
        raise ValueError("TSP 回路长度必须等于节点数 + 1（闭合起点）")
    if tour.node_ids[0] != problem.start_node_id or tour.node_ids[-1] != problem.start_node_id:
        raise ValueError("TSP 回路必须从 start_node_id 出发并回到该节点")
    if set(tour.node_ids[:-1]) != expected or len(set(tour.node_ids[:-1])) != len(problem.nodes):
        raise ValueError("TSP 回路必须且只能访问每个节点一次")

    nodes = {node.node_id: node for node in problem.nodes}
    total = sum(
        euclidean_distance(nodes[left], nodes[right])
        for left, right in zip(tour.node_ids, tour.node_ids[1:])
    )
    return TSPEvaluation(tour_length=float(total))
