"""CVRP evaluator 需以独立计算路径复核 hard capacity。"""

import pytest

from agriautolab.contracts.geometry import Point
from agriautolab.contracts.routing import CVRPCustomer, CVRPProblem, RoutingNode
from agriautolab.optimization.cvrp import (
    CVRPConstructiveProblem,
    CVRPSolution,
    evaluate_cvrp_solution,
)


def _node(node_id: str, x: float) -> RoutingNode:
    return RoutingNode(node_id=node_id, position=Point(x=x, y=0.0))


def _customer(node_id: str, x: float, demand: float) -> CVRPCustomer:
    return CVRPCustomer(node_id=node_id, position=Point(x=x, y=0.0), demand=demand)


def test_evaluator_rejects_overload_even_if_constructor_capacity_path_is_broken(monkeypatch) -> None:
    problem = CVRPProblem(
        problem_id="independent-capacity-recheck",
        depot=_node("D", 0.0),
        customers=(
            _customer("A", 1.0, 0.6),
            _customer("B", 2.0, 0.6),
        ),
        vehicle_capacity=1.0,
    )
    overloaded = CVRPSolution(routes=(("D", "A", "B", "D"),))

    # 故意破坏 constructor 的可行性函数：即使构造器会错误放行任意客户，evaluator
    # 仍需用自己的 Fraction 精确路线求和拒绝 1.2 倍超载。
    monkeypatch.setattr(
        CVRPConstructiveProblem,
        "_customer_fits",
        lambda self, state, customer_id: True,
    )

    with pytest.raises(ValueError, match="超过车辆容量"):
        evaluate_cvrp_solution(problem, overloaded)
