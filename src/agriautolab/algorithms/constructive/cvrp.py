"""CVRP 的人工构造式启发式基线。"""

from __future__ import annotations

from dataclasses import dataclass

from agriautolab.optimization.cvrp import CVRPConstructiveProblem, CVRPState, euclidean_distance


@dataclass(frozen=True)
class CVRPNearestFeasibleHeuristic:
    """最近可行客户：容量允许时优先访问离当前位置最近的客户。

    返回仓库是状态机在当前车辆无法继续服务时强制提供的唯一动作；此时分数数值
    不参与比较，但仍返回当前位置到仓库的真实欧氏距离，保持语义一致。
    """

    problem: CVRPConstructiveProblem
    heuristic_id: str = "cvrp_nearest_feasible"

    def score(self, state: CVRPState, action: str) -> float:
        current = self.problem.node(state.current_node_id)
        candidate = self.problem.node(action)
        return euclidean_distance(current, candidate)
