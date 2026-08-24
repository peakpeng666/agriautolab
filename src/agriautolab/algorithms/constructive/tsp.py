"""TSP 的人工构造式启发式基线。"""

from __future__ import annotations

from dataclasses import dataclass

from agriautolab.optimization.routing import euclidean_node_distance_m
from agriautolab.optimization.tsp import TSPConstructiveProblem, TSPState


@dataclass(frozen=True)
class TSPNearestNeighborHeuristic:
    """最近邻：优先访问离当前节点最近的未访问节点。"""

    problem: TSPConstructiveProblem
    heuristic_id: str = "tsp_nearest_neighbor"

    def score(self, state: TSPState, action: str) -> float:
        current = self.problem.node(state.current_node_id)
        candidate = self.problem.node(action)
        return euclidean_node_distance_m(current, candidate)
