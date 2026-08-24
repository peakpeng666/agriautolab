"""CVRP schema 与运行时必须共享同一 hard-capacity roundoff 语义。"""

import math

import pytest
from pydantic import ValidationError

from agriautolab.contracts.geometry import Point
from agriautolab.contracts.routing import CVRPCustomer, CVRPProblem, RoutingNode


def _node(node_id: str) -> RoutingNode:
    return RoutingNode(node_id=node_id, position=Point(x=0.0, y=0.0))


def _customer(demand: float) -> CVRPCustomer:
    return CVRPCustomer(node_id="A", position=Point(x=1.0, y=0.0), demand=demand)


def _next_float(value: float, steps: int) -> float:
    for _ in range(steps):
        value = math.nextafter(value, math.inf)
    return value


def test_cvrp_schema_accepts_single_customer_within_roundoff_budget() -> None:
    capacity = 1.0
    problem = CVRPProblem(
        problem_id="single-customer-roundoff",
        depot=_node("D"),
        customers=(_customer(_next_float(capacity, 1)),),
        vehicle_capacity=capacity,
    )
    assert problem.customers[0].demand > problem.vehicle_capacity


def test_cvrp_schema_rejects_single_customer_beyond_roundoff_budget() -> None:
    capacity = 1.0
    with pytest.raises(ValidationError, match="单车容量永远无法服务"):
        CVRPProblem(
            problem_id="single-customer-material-overflow",
            depot=_node("D"),
            customers=(_customer(_next_float(capacity, 9)),),
            vehicle_capacity=capacity,
        )
