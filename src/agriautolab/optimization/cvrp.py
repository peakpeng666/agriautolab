"""欧氏 CVRP 的构造状态机与独立评价器。

容量、客户覆盖、回仓合法性与车队上限由问题状态机维护；heuristic 只在当前合法动作
之间决定策略。离开仓库后，提前回仓本身可以是合法动作，不能被 Problem adapter 以
“还有客户装得下”为由隐藏；但若回仓必然要求超过 `max_vehicles` 的下一辆车，它就
不是可行动作。最终 evaluator 以独立计算路径重新检查客户覆盖、容量、车辆数与总距离，
不采信构造器自报指标，也不重放 constructor 的逐项减法状态机。
"""

from __future__ import annotations

import math
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

    constructor 不累加绝对 route demand：多个有限需求的和仍可能上溢为 `inf`。
    比较只容忍 `contracts.numerics` 规定的少量 binary64 舍入步长，不使用固定绝对
    容差；`available == 0` 时任何正需求都必须拒绝。
    """
    if not not_greater_than_with_roundoff(demand, available):
        return None
    remaining = available - demand
    return 0.0 if remaining < 0.0 else remaining


def _capacity_allows(demand: float, available: float) -> bool:
    return _remaining_capacity_after(demand, available) is not None


class CVRPConstructiveProblem:
    """把 `CVRPProblem` 适配为逐客户/回仓选择的 constructive problem。"""

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

    def _can_open_following_route(self, state: CVRPState) -> bool:
        """当前路线闭合后，是否还有车辆可继续服务未完成客户。"""
        if self.problem.max_vehicles is None:
            return True
        current_vehicle_number = len(state.completed_routes) + 1
        return current_vehicle_number < self.problem.max_vehicles

    def feasible_actions(self, state: CVRPState) -> tuple[str, ...]:
        """枚举当前硬约束下可执行动作；不在 Problem 层嵌入 route-closure 策略。"""
        depot_id = self.problem.depot.node_id
        if not state.unserved_customer_ids:
            return () if state.current_node_id == depot_id else (depot_id,)

        feasible_customers = tuple(
            customer_id
            for customer_id in state.unserved_customer_ids
            if _capacity_allows(self._customers[customer_id].demand, state.remaining_capacity)
        )
        if state.current_node_id == depot_id:
            # 仓库不能原地“回仓”形成空路线；schema 保证至少有一个客户可由满载车辆服务。
            return feasible_customers

        # 客户动作保持 node_id 稳定顺序，回仓固定放最后。提前回仓是否值得由 heuristic
        # 决定；若已没有下一辆车，则回仓会留下未服务客户，因此不属于当前可行动作。
        if self._can_open_following_route(state):
            return feasible_customers + (depot_id,)
        return feasible_customers

    def apply_action(self, state: CVRPState, action: str) -> CVRPState:
        depot_id = self.problem.depot.node_id
        if action not in self.feasible_actions(state):
            raise ValueError(f"CVRP 动作当前不可行：{action!r}")

        if action == depot_id:
            completed_routes = state.completed_routes + (state.current_route + (depot_id,),)
            if state.unserved_customer_ids:
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


def _normalized_route_demand(
    problem: CVRPProblem,
    customer_ids: tuple[str, ...],
    customers_by_id: dict[str, CVRPCustomer],
) -> float:
    """用独立于 constructor 状态更新的无量纲路径复算路线容量占用。"""
    try:
        normalized = math.fsum(
            customers_by_id[customer_id].demand / problem.vehicle_capacity
            for customer_id in customer_ids
        )
    except OverflowError as error:  # 极端有限输入仍不允许把 inf 送进硬约束判断
        raise ValueError("CVRP 路线归一化需求超出有限浮点表示范围") from error
    if not math.isfinite(normalized):
        raise ValueError("CVRP 路线归一化需求不是有限数")
    return normalized


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

        # evaluator 不复用 constructor 的逐项剩余容量状态机；它独立计算整条路线的
        # 无量纲容量占用，只共享“最多容忍若干 ULP”的判定政策。
        normalized_demand = _normalized_route_demand(problem, customer_ids, customers_by_id)
        if not not_greater_than_with_roundoff(normalized_demand, 1.0):
            raise ValueError(f"CVRP 路线 {route_index} 超过车辆容量")

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
