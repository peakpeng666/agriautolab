"""CVRP capacity 是严格 hard constraint，不用 ULP 或绝对容差改写输入事实。"""

import math

import pytest
from pydantic import ValidationError

from agriautolab.contracts.geometry import Point
from agriautolab.contracts.routing import CVRPCustomer, CVRPProblem, RoutingNode


def _node(node_id: str) -> RoutingNode:
    return RoutingNode(node_id=node_id, position=Point(x=0.0, y=0.0))


def _customer(demand: float) -> CVRPCustomer:
    return CVRPCustomer(node_id="A", position=Point(x=1.0, y=0.0), demand=demand)


def test_single_customer_one_ulp_above_capacity_is_rejected() -> None:
    capacity = 1.0
    demand = math.nextafter(capacity, math.inf)
    assert demand > capacity

    with pytest.raises(ValidationError, match="单车容量永远无法服务"):
        CVRPProblem(
            problem_id="one-ulp-overload",
            depot=_node("D"),
            customers=(_customer(demand),),
            vehicle_capacity=capacity,
        )


def test_minimum_subnormal_capacity_does_not_gain_one_ulp_of_free_space() -> None:
    capacity = math.nextafter(0.0, math.inf)
    demand = math.nextafter(capacity, math.inf)
    assert demand == 2.0 * capacity

    with pytest.raises(ValidationError, match="单车容量永远无法服务"):
        CVRPProblem(
            problem_id="subnormal-two-x-overload",
            depot=_node("D"),
            customers=(_customer(demand),),
            vehicle_capacity=capacity,
        )


def test_exact_subnormal_equality_is_accepted() -> None:
    capacity = math.nextafter(0.0, math.inf)
    problem = CVRPProblem(
        problem_id="subnormal-exact-fit",
        depot=_node("D"),
        customers=(_customer(capacity),),
        vehicle_capacity=capacity,
    )
    assert problem.customers[0].demand == problem.vehicle_capacity
