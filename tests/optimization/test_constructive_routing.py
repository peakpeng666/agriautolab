"""TSP/CVRP 构造式求解的语义真值。

这些测试不只检查“能运行”或“同 seed 可重复”，而是固定解析小实例，要求构造顺序、
闭合路线、容量约束和独立复算目标都等于手算真值。
"""

import math

import pytest
from pydantic import ValidationError

from agriautolab.algorithms.constructive import (
    CVRPNearestFeasibleHeuristic,
    TSPNearestNeighborHeuristic,
)
from agriautolab.contracts.geometry import Point
from agriautolab.contracts.routing import CVRPCustomer, CVRPProblem, RoutingNode, TSPProblem
from agriautolab.optimization import construct_solution
from agriautolab.optimization.constructive import ConstructionError
from agriautolab.optimization.cvrp import CVRPConstructiveProblem, evaluate_cvrp_solution
from agriautolab.optimization.tsp import TSPConstructiveProblem, evaluate_tsp_tour


def node(node_id: str, x: float, y: float) -> RoutingNode:
    return RoutingNode(node_id=node_id, position=Point(x=x, y=y))


def customer(node_id: str, x: float, y: float, demand: float) -> CVRPCustomer:
    return CVRPCustomer(node_id=node_id, position=Point(x=x, y=y), demand=demand)


def test_tsp_nearest_neighbor_has_hand_computable_truth() -> None:
    problem = TSPProblem(
        problem_id="tsp-line",
        nodes=(node("A", 0.0, 0.0), node("B", 1.0, 0.0), node("C", 3.0, 0.0)),
        start_node_id="A",
    )
    adapter = TSPConstructiveProblem(problem)
    tour = construct_solution(adapter, TSPNearestNeighborHeuristic(adapter))

    assert tour.node_ids == ("A", "B", "C", "A")
    assert evaluate_tsp_tour(problem, tour).tour_length == pytest.approx(6.0)


def test_tsp_tie_break_follows_stable_action_order() -> None:
    problem = TSPProblem(
        problem_id="tsp-tie",
        nodes=(node("S", 0.0, 0.0), node("B", -1.0, 0.0), node("A", 1.0, 0.0)),
        start_node_id="S",
    )
    adapter = TSPConstructiveProblem(problem)
    tour = construct_solution(adapter, TSPNearestNeighborHeuristic(adapter))

    # A/B 与起点等距；feasible_actions 按 node_id 排序，所以平局必须稳定选 A。
    assert tour.node_ids[:3] == ("S", "A", "B")


def test_cvrp_nearest_feasible_respects_capacity_and_closes_routes() -> None:
    problem = CVRPProblem(
        problem_id="cvrp-line",
        depot=node("D", 0.0, 0.0),
        customers=(
            customer("A", 1.0, 0.0, 2.0),
            customer("B", 2.0, 0.0, 2.0),
            customer("C", 10.0, 0.0, 2.0),
        ),
        vehicle_capacity=4.0,
    )
    adapter = CVRPConstructiveProblem(problem)
    solution = construct_solution(adapter, CVRPNearestFeasibleHeuristic(adapter))

    assert solution.routes == (("D", "A", "B", "D"), ("D", "C", "D"))
    evaluation = evaluate_cvrp_solution(problem, solution)
    assert evaluation.vehicle_count == 2
    assert evaluation.total_distance == pytest.approx(24.0)


def test_cvrp_contract_rejects_customer_larger_than_vehicle_capacity() -> None:
    with pytest.raises(ValidationError, match="单车容量永远无法服务"):
        CVRPProblem(
            problem_id="oversized",
            depot=node("D", 0.0, 0.0),
            customers=(customer("A", 1.0, 0.0, 5.0),),
            vehicle_capacity=4.0,
        )


def test_cvrp_vehicle_limit_can_make_greedy_construction_infeasible() -> None:
    problem = CVRPProblem(
        problem_id="fleet-limit",
        depot=node("D", 0.0, 0.0),
        customers=(customer("A", 1.0, 0.0, 3.0), customer("B", 2.0, 0.0, 3.0)),
        vehicle_capacity=3.0,
        max_vehicles=1,
    )
    adapter = CVRPConstructiveProblem(problem)

    with pytest.raises(ValueError, match="超过 max_vehicles"):
        construct_solution(adapter, CVRPNearestFeasibleHeuristic(adapter))


def test_constructive_engine_rejects_non_finite_scores() -> None:
    problem = TSPProblem(
        problem_id="nan-score",
        nodes=(node("A", 0.0, 0.0), node("B", 1.0, 0.0)),
        start_node_id="A",
    )
    adapter = TSPConstructiveProblem(problem)

    class BadHeuristic:
        heuristic_id = "bad"

        def score(self, state, action):
            return math.nan

    with pytest.raises(ConstructionError, match="非有限分数"):
        construct_solution(adapter, BadHeuristic())
