"""欧氏 CVRP 的构造状态机与独立评价器。

容量约束由问题状态机维护，启发式只能给当前可服务客户排序；当当前车辆已无法
继续服务任何客户时，状态机强制返回仓库并开启下一条路线。最终评价器重新检查
客户覆盖、容量、车辆数与总距离，不采信构造器自报指标。
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from agriautolab.contracts.routing import CVRPCustomer, CVRPProblem, RoutingNode


@dataclass(frozen=True)
class CVRPState:
    current_node_id: str
    remaining_capacity: float
    unserved_customer_ids: tuple[str, ...]
    current_route: tuple[str, ...]
    completed_routes: tuple[tuple[str, ...], ...]


@dataclass(frozen=True)
class CVRPSolution:
    routes: tuple[tuple[str, ...], ...]


@dataclass(frozen=True)
class CVRPEvaluation:
    total_distance: float
    vehicle_count: int


def euclidean_distance(left: RoutingNode, right: RoutingNode) -> float:
    return math.hypot(left.position.x - right.position.x, left.position.y - right.position.y)


class CVRPConstructiveProblem:
    """把 `CVRPProblem` 适配为逐客户选择的 constructive problem。"""

    def __init__(self, problem: CVRPProblem) -> None:
        self.problem = problem
        self._customers = {customer.node_id: customer for customer in problem.customers}

    def node(self, node_id: str) -> RoutingNode:
        if node_id == self.problem.depot.node_id:
            return self.problem.depot
        return self._customers[node_id]

    def customer(self, node_id: str) -> CVRPCustomer:
        return self._customers[node_id]

    def initial_state(self) -> CVRPState:
        return CVRPState(
            current_node_id=self.problem.depot.node_id,
            remaining_capacity=self.problem.vehicle_capacity,
            unserved_customer_ids=tuple(sorted(self._customers)),
            current_route=(self.problem.depot.node_id,),
            completed_routes=(),
        )

    def is_complete(self, state: CVRPState) -> bool:
        return not state.unserved_customer_ids and state.current_node_id == self.problem.depot.node_id

    def feasible_actions(self, state: CVRPState) -> tuple[str, ...]:
        if not state.unserved_customer_ids:
            if state.current_node_id == self.problem.depot.node_id:
                return ()
            return (self.problem.depot.node_id,)

        feasible_customers = tuple(
            customer_id
            for customer_id in state.unserved_customer_ids
            if self._customers[customer_id].demand <= state.remaining_capacity + 1e-12
        )
        if feasible_customers:
            return feasible_customers

        if state.current_node_id == self.problem.depot.node_id:
            return ()
        return (self.problem.depot.node_id,)

    def apply_action(self, state: CVRPState, action: str) -> CVRPState:
        depot_id = self.problem.depot.node_id
        if action not in self.feasible_actions(state):
            raise ValueError(f"CVRP 动作当前不可行：{action!r}")

        if action == depot_id:
            closed_route = state.current_route + (depot_id,)
            completed = state.completed_routes + (closed_route,)
            if state.unserved_customer_ids:
                used_vehicles = len(completed) + 1
                if self.problem.max_vehicles is not None and used_vehicles > self.problem.max_vehicles:
                    raise ValueError(
                        f"CVRP 需要开启第 {used_vehicles} 辆车，超过 max_vehicles={self.problem.max_vehicles}"
                    )
                return CVRPState(
                    current_node_id=depot_id,
                    remaining_capacity=self.problem.vehicle_capacity,
                    unserved_customer_ids=state.unserved_customer_ids,
                    current_route=(depot_id,),
                    completed_routes=completed,
                )
            return CVRPState(
                current_node_id=depot_id,
                remaining_capacity=self.problem.vehicle_capacity,
                unserved_customer_ids=(),
                current_route=(depot_id,),
                completed_routes=completed,
            )

        customer = self._customers[action]
        remaining = tuple(customer_id for customer_id in state.unserved_customer_ids if customer_id != action)
        return CVRPState(
            current_node_id=action,
            remaining_capacity=state.remaining_capacity - customer.demand,
            unserved_customer_ids=remaining,
            current_route=state.current_route + (action,),
            completed_routes=state.completed_routes,
        )

    def finalize(self, state: CVRPState) -> CVRPSolution:
        if not self.is_complete(state):
            raise ValueError("CVRP 尚未形成完整闭合路线集")
        return CVRPSolution(routes=state.completed_routes)


def evaluate_cvrp_solution(problem: CVRPProblem, solution: CVRPSolution) -> CVRPEvaluation:
    """独立校验 CVRP 可行性并复算总欧氏距离。"""
    depot_id = problem.depot.node_id
    customers = {customer.node_id: customer for customer in problem.customers}
    nodes: dict[str, RoutingNode] = {depot_id: problem.depot, **customers}

    if not solution.routes:
        raise ValueError("CVRP 解至少需要一条路线")
    if problem.max_vehicles is not None and len(solution.routes) > problem.max_vehicles:
        raise ValueError("CVRP 解使用车辆数超过 max_vehicles")

    visited: list[str] = []
    total_distance = 0.0
    for route_index, route in enumerate(solution.routes):
        if len(route) < 3 or route[0] != depot_id or route[-1] != depot_id:
            raise ValueError(f"CVRP 路线 {route_index} 必须从仓库出发并回仓")
        customer_ids = route[1:-1]
        if any(node_id not in customers for node_id in customer_ids):
            raise ValueError(f"CVRP 路线 {route_index} 含未知客户或中途仓库")
        demand = sum(customers[node_id].demand for node_id in customer_ids)
        if demand > problem.vehicle_capacity + 1e-12:
            raise ValueError(f"CVRP 路线 {route_index} 超过车辆容量")
        visited.extend(customer_ids)
        total_distance += sum(
            euclidean_distance(nodes[left], nodes[right])
            for left, right in zip(route, route[1:])
        )

    expected = {customer.node_id for customer in problem.customers}
    if set(visited) != expected or len(visited) != len(expected):
        raise ValueError("CVRP 解必须且只能服务每个客户一次")

    return CVRPEvaluation(total_distance=float(total_distance), vehicle_count=len(solution.routes))
