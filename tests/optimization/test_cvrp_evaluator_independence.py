"""CVRP evaluator 必须以独立计算路径复核 hard capacity。"""

import pytest

import agriautolab.optimization.cvrp as cvrp_module
from agriautolab.contracts.geometry import Point
from agriautolab.contracts.routing import CVRPCustomer, CVRPProblem, RoutingNode
from agriautolab.optimization.cvrp import CVRPSolution, evaluate_cvrp_solution


def _node(node_id: str, x: float) -> RoutingNode:
    return RoutingNode(node_id=node_id, position=Point(x=x, y=0.0))


def _customer(node_id: str, x: float, demand: float) -> CVRPCustomer:
    return CVRPCustomer(node_id=node_id, position=Point(x=x, y=0.0), demand=demand)


def test_evaluator_rejects_overload_even_if_constructor_capacity_helper_is_broken(monkeypatch) -> None:
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

    # 故意破坏 constructor 的逐项剩余容量 helper：若 evaluator 复用同一路径，
    # 这个补丁会把 1.2 倍超载伪装成可行。独立 evaluator 必须仍由 0.6+0.6 的
    # 无量纲复算拒绝该路线。
    monkeypatch.setattr(cvrp_module, "_remaining_capacity_after", lambda demand, available: 0.0)

    with pytest.raises(ValueError, match="超过车辆容量"):
        evaluate_cvrp_solution(problem, overloaded)
