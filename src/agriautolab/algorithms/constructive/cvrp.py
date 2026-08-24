"""CVRP 的人工构造式启发式基线。"""

from __future__ import annotations

from dataclasses import dataclass

from agriautolab.optimization.cvrp import CVRPConstructiveProblem, CVRPState
from agriautolab.optimization.routing import euclidean_node_distance_m


@dataclass(frozen=True)
class CVRPNearestFeasibleCustomerHeuristic:
    """最近可行客户，并在仍有可服务客户时推迟回仓。

    `CVRPConstructiveProblem` 会把“提前回仓”作为真实合法动作暴露出来；本基线才负责
    fill-until-stuck 策略。这样 Problem 只描述硬约束，route-closure 决策不会伪装成
    feasibility。回仓与客户评分均保持有限，公共 engine 不需要特殊 sentinel。
    """

    problem: CVRPConstructiveProblem
    heuristic_id: str = "cvrp_nearest_feasible_customer"

    def score(self, state: CVRPState, action: str) -> float:
        current = self.problem.node(state.current_node_id)
        depot_id = self.problem.problem.depot.node_id
        if action != depot_id:
            return euclidean_node_distance_m(current, self.problem.node(action))

        customer_actions = tuple(
            candidate
            for candidate in self.problem.feasible_actions(state)
            if candidate != depot_id
        )
        if not customer_actions:
            return euclidean_node_distance_m(current, self.problem.node(depot_id))

        # 回仓 action 固定排在客户之后。给它“当前可行客户中最远者”的有限分数，
        # 至少一个客户会取得不更大的分数；若恰好并列，稳定 action 顺序仍先选客户。
        return max(
            euclidean_node_distance_m(current, self.problem.node(customer_id))
            for customer_id in customer_actions
        )
