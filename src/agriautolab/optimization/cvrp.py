"""欧氏 CVRP 的构造状态机与独立评价器。

容量约束由问题状态机维护，启发式只能给当前可服务客户排序；当前车辆无法继续
服务时，状态机强制回仓并开启下一条路线。最终 evaluator 重新检查客户覆盖、容量、
车辆数与总距离，不采信构造器自报指标。
"""

from __future__ import annotations

from dataclasses import dataclass

from agriautolab.contracts.numerics import not_greater_than_with_roundoff
from agriautolab.contracts.routing import CVRPCustomer, CVRPProblem, RoutingNode
from agriautolab.optimization.constructive import ConstructionError
from agriautolab.optimization.routing import route_length_m, sum_distances_m


@dataclass(frozen=True)
class CVRPState:
    """逐客户构造所需的容量与路线状态。"""

    current_node_id: str
    remaining_capacity: float
    unserved_customer_ids: tuple[str, ...]
    current_route: tuple[str, ...]
    completed_routes: tuple[tuple[str, ...], ...]


@dataclass(frozen=True)
class CVRPSolution:
    """闭合车辆路线集合；每条路线首尾均为仓库。"""

    routes: tuple[tuple[str, ...], ...]


@dataclass(frozen=True)
class CVRPEvaluation:
    """由独立 evaluator 复算的 CVRP 指标。"""

    total_distance_m: float
    vehicle_count: int


def _remaining_capacity_after(demand: float, available: float) -> float | None:
    """若当前容量容得下需求，返回扣减后的剩余容量；否则返回 None。

    不累加绝对 route demand：多个有限需求的和仍可能上溢为 `inf`。比较只容忍
    `contracts.numerics` 规定的少量 binary64 舍入步长，不使用固定绝对容差；
    `available == 0` 时任何正需求都必须拒绝。
    """
    if not not_greater_than_with_roundoff(demand, available):
        return None
    remaining = available - demand
    return 0.0 if remaining < 0.0 else remaining


def _capacity_allows(demand: float, available: float) -> bool:
    return _remaining_capacity_after(demand, available) is not None


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
        depot_id = self.problem.depot.node_id
        if not state.unserved_customer_ids:
            return () if state.current_node_id == depot_id else (depot_id,)

        feasible_customers = tuple(
            customer_id
            for customer_id in state.unserved_customer_ids
            if _capacity_allows(self._customers[customer_id].demand, state.remaining_capacity)
        )
        if feasible_customers:
            # unserved_customer_ids 始终保持 node_id 排序；评分并列因此有稳定 tie-break。
            return feasible_customers

        return () if state.current_node_id == depot_id else (depot_id,)

    def apply_action(self, state: CVRPState, action: str) -> CVRPState:
        depot_id = self.problem.depot.node_id
        if action not in self.feasible_actions(state):
            raise ValueError(f"CVRP 动作当前不可行：{action!r}")

        if action == depot_id:
            closed_route = state.current_route + (depot_id,)
            completed_routes = state.completed_routes + (closed_route,)
            if state.unserved_customer_ids:
                next_vehicle_number = len(completed_routes) + 1
                if (
                    self.problem.max_vehicles is not None
                    and next_vehicle_number > self.problem.max_vehicles
                ):
                    raise ConstructionError(
                        f"当前构造需要第 {next_vehicle_number} 辆车，"
                        f"超过 max_vehicles={self.problem.max_vehicles}"
                    )
                return CVRPState(
                    current_node_id=depot_id,
                    remaining_capacity=self.problem.vehicle_capacity,
                    unserved_customer_ids=state.unserved_customer_ids,
                    current_route=(depot_id,),
                    completed_routes=completed_routes,
                )
            return CVRPState(
                current_node_id=depot_id,
                remaining_capacity=self.problem.vehicle_capacity,
                unserved_customer_ids=(),
                current_route=(depot_id,),
                completed_routes=completed_routes,
            )

        customer = self._customers[action]
        remaining_capacity = _remaining_capacity_after(customer.demand, state.remaining_capacity)
        if remaining_capacity is None:  # pragma: no cover -- feasible_actions 已做同一检查
            raise ConstructionError(f"客户 {action!r} 超过当前剩余容量")
        remaining_customers = tuple(
            customer_id for customer_id in state.unserved_customer_ids if customer_id != action
        )
        return CVRPState(
            current_node_id=action,
            remaining_capacity=remaining_capacity,
            unserved_customer_ids=remaining_customers,
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
    customers_by_id = {customer.node_id: customer for customer in problem.customers}
    nodes_by_id: dict[str, RoutingNode] = {depot_id: problem.depot, **customers_by_id}

    if not solution.routes:
        raise ValueError("CVRP 解至少需要一条路线")
    if problem.max_vehicles is not None and len(solution.routes) > problem.max_vehicles:
        raise ValueError("CVRP 解使用车辆数超过 max_vehicles")

    visited_customer_ids: list[str] = []
    route_lengths_m: list[float] = []
    for route_index, route in enumerate(solution.routes):
        if len(route) < 3 or route[0] != depot_id or route[-1] != depot_id:
            raise ValueError(f"CVRP 路线 {route_index} 必须从仓库出发并回仓")

        customer_ids = route[1:-1]
        if any(node_id not in customers_by_id for node_id in customer_ids):
            raise ValueError(f"CVRP 路线 {route_index} 含未知客户或中途仓库")

        remaining_capacity = problem.vehicle_capacity
        for customer_id in customer_ids:
            next_remaining = _remaining_capacity_after(
                customers_by_id[customer_id].demand, remaining_capacity
            )
            if next_remaining is None:
                raise ValueError(f"CVRP 路线 {route_index} 超过车辆容量")
            remaining_capacity = next_remaining

        visited_customer_ids.extend(customer_ids)
        route_lengths_m.append(route_length_m(nodes_by_id, route))

    expected_customer_ids = {customer.node_id for customer in problem.customers}
    if (
        set(visited_customer_ids) != expected_customer_ids
        or len(visited_customer_ids) != len(expected_customer_ids)
    ):
        raise ValueError("CVRP 解必须且只能服务每个客户一次")

    return CVRPEvaluation(
        total_distance_m=sum_distances_m(route_lengths_m),
        vehicle_count=len(solution.routes),
    )
