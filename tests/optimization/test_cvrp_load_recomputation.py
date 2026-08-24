"""CVRP 构造容量使用精确二进制整数单位，不累计浮点误差或隐含容差。"""

import pytest

from agriautolab.algorithms.constructive import CVRPNearestFeasibleCustomerHeuristic
from agriautolab.contracts.geometry import Point
from agriautolab.contracts.routing import CVRPCustomer, CVRPProblem, RoutingNode
from agriautolab.optimization import construct_solution
from agriautolab.optimization.cvrp import (
    CVRPConstructiveProblem,
    CVRPSolution,
    evaluate_cvrp_solution,
)


def _depot() -> RoutingNode:
    return RoutingNode(node_id="D", position=Point(x=0.0, y=0.0))


def test_many_exact_binary_demands_fill_one_vehicle_without_drift() -> None:
    # 1/128 在 binary64 中精确可表示；128 项的精确总需求就是 1.0。
    demand = 1.0 / 128.0
    customers = tuple(
        CVRPCustomer(
            node_id=f"C{index:03d}",
            position=Point(x=float(index + 1), y=0.0),
            demand=demand,
        )
        for index in range(128)
    )
    problem = CVRPProblem(
        problem_id="exact-binary-fill",
        depot=_depot(),
        customers=customers,
        vehicle_capacity=1.0,
    )
    adapter = CVRPConstructiveProblem(problem)
    solution = construct_solution(adapter, CVRPNearestFeasibleCustomerHeuristic(adapter))

    assert len(solution.routes) == 1
    assert len(solution.routes[0][1:-1]) == 128
    assert evaluate_cvrp_solution(problem, solution).vehicle_count == 1


def test_decimal_intent_does_not_override_binary64_hard_capacity() -> None:
    customers = tuple(
        CVRPCustomer(
            node_id=f"C{index:03d}",
            position=Point(x=float(index + 1), y=0.0),
            demand=0.01,
        )
        for index in range(100)
    )
    problem = CVRPProblem(
        problem_id="hundred-hundredths-binary64",
        depot=_depot(),
        customers=customers,
        vehicle_capacity=1.0,
    )
    adapter = CVRPConstructiveProblem(problem)
    solution = construct_solution(adapter, CVRPNearestFeasibleCustomerHeuristic(adapter))

    # `0.01` 的 binary64 精确值乘 100 略大于 1.0；hard constraint 因此必须拆车。
    assert len(solution.routes) == 2

    overloaded = CVRPSolution(
        routes=(("D",) + tuple(customer.node_id for customer in customers) + ("D",),)
    )
    with pytest.raises(ValueError, match="超过车辆容量"):
        evaluate_cvrp_solution(problem, overloaded)
