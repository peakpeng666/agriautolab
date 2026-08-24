"""TSP/CVRP 构造式求解的语义真值。

这些测试不只检查“能运行”或“同 seed 可重复”，而是固定手算小实例，要求构造顺序、
闭合路线、容量约束和独立复算目标都符合明确真值；公共协议还必须拒绝非有限评分，
且不能偷偷要求领域动作实现比较运算。
"""

import math
from dataclasses import dataclass

import pytest
from pydantic import ValidationError

from agriautolab.algorithms.constructive import (
    CVRPNearestFeasibleCustomerHeuristic,
    TSPNearestNeighborHeuristic,
)
from agriautolab.contracts.geometry import Point
from agriautolab.contracts.routing import CVRPCustomer, CVRPProblem, RoutingNode, TSPProblem
from agriautolab.optimization import construct_solution
from agriautolab.optimization.constructive import ConstructionError
from agriautolab.optimization.cvrp import (
    CVRPConstructiveProblem,
    CVRPSolution,
    evaluate_cvrp_solution,
)
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
    assert evaluate_tsp_tour(problem, tour).tour_length_m == pytest.approx(6.0)


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


def test_tsp_contract_rejects_duplicate_node_identity() -> None:
    with pytest.raises(ValidationError, match="node_id 必须唯一"):
        TSPProblem(
            problem_id="duplicate-id",
            nodes=(node("A", 0.0, 0.0), node("A", 1.0, 0.0)),
            start_node_id="A",
        )


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
    solution = construct_solution(adapter, CVRPNearestFeasibleCustomerHeuristic(adapter))

    assert solution.routes == (("D", "A", "B", "D"), ("D", "C", "D"))
    evaluation = evaluate_cvrp_solution(problem, solution)
    assert evaluation.vehicle_count == 2
    assert evaluation.total_distance_m == pytest.approx(24.0)


def test_cvrp_decimal_exact_fit_survives_binary_roundoff() -> None:
    problem = CVRPProblem(
        problem_id="decimal-fit",
        depot=node("D", 0.0, 0.0),
        customers=(
            customer("A", 1.0, 0.0, 0.1),
            customer("B", 2.0, 0.0, 0.2),
        ),
        vehicle_capacity=0.3,
    )
    adapter = CVRPConstructiveProblem(problem)
    solution = construct_solution(adapter, CVRPNearestFeasibleCustomerHeuristic(adapter))

    assert solution.routes == (("D", "A", "B", "D"),)
    assert evaluate_cvrp_solution(problem, solution).vehicle_count == 1


def test_cvrp_subunit_capacity_does_not_gain_absolute_free_slack() -> None:
    problem = CVRPProblem(
        problem_id="subunit-capacity",
        depot=node("D", 0.0, 0.0),
        customers=(
            customer("A", 1.0, 0.0, 1e-15),
            customer("B", 2.0, 0.0, 1e-15),
        ),
        vehicle_capacity=1e-15,
    )
    adapter = CVRPConstructiveProblem(problem)
    solution = construct_solution(adapter, CVRPNearestFeasibleCustomerHeuristic(adapter))

    assert solution.routes == (("D", "A", "D"), ("D", "B", "D"))

    overloaded = CVRPSolution(routes=(("D", "A", "B", "D"),))
    with pytest.raises(ValueError, match="超过车辆容量"):
        evaluate_cvrp_solution(problem, overloaded)


def test_cvrp_contract_rejects_customer_larger_than_vehicle_capacity() -> None:
    with pytest.raises(ValidationError, match="单车容量永远无法服务"):
        CVRPProblem(
            problem_id="oversized",
            depot=node("D", 0.0, 0.0),
            customers=(customer("A", 1.0, 0.0, 5.0),),
            vehicle_capacity=4.0,
        )


def test_cvrp_contract_rejects_demand_above_total_fleet_capacity() -> None:
    with pytest.raises(ValidationError, match="总需求超过"):
        CVRPProblem(
            problem_id="insufficient-fleet",
            depot=node("D", 0.0, 0.0),
            customers=(customer("A", 1.0, 0.0, 4.0), customer("B", 2.0, 0.0, 4.0)),
            vehicle_capacity=5.0,
            max_vehicles=1,
        )


def test_cvrp_fleet_capacity_check_is_safe_when_finite_demands_would_overflow_sum() -> None:
    with pytest.raises(ValidationError, match="总需求超过"):
        CVRPProblem(
            problem_id="overflowing-fleet-sum",
            depot=node("D", 0.0, 0.0),
            customers=(
                customer("A", 1.0, 0.0, 9e307),
                customer("B", 2.0, 0.0, 9e307),
            ),
            vehicle_capacity=1e308,
            max_vehicles=1,
        )


def test_cvrp_evaluator_rejects_overloaded_route_even_when_demand_sum_would_overflow() -> None:
    problem = CVRPProblem(
        problem_id="overflowing-route-sum",
        depot=node("D", 0.0, 0.0),
        customers=(
            customer("A", 1.0, 0.0, 9e307),
            customer("B", 2.0, 0.0, 9e307),
        ),
        vehicle_capacity=1e308,
    )
    overloaded = CVRPSolution(routes=(("D", "A", "B", "D"),))

    with pytest.raises(ValueError, match="超过车辆容量"):
        evaluate_cvrp_solution(problem, overloaded)


def test_cvrp_fleet_limit_can_refute_a_greedy_order_even_when_problem_is_feasible() -> None:
    problem = CVRPProblem(
        problem_id="greedy-packing-trap",
        depot=node("D", 0.0, 0.0),
        customers=(
            customer("A", 1.0, 0.0, 4.0),
            customer("B", 2.0, 0.0, 4.0),
            customer("C", 100.0, 0.0, 6.0),
            customer("E", 101.0, 0.0, 6.0),
        ),
        vehicle_capacity=10.0,
        max_vehicles=2,
    )

    # 先给出显式可行解，证明失败来自 greedy 次序，而不是问题本身不可行。
    feasible = CVRPSolution(routes=(("D", "A", "C", "D"), ("D", "B", "E", "D")))
    assert evaluate_cvrp_solution(problem, feasible).vehicle_count == 2

    adapter = CVRPConstructiveProblem(problem)
    with pytest.raises(ConstructionError, match="第 3 辆车"):
        construct_solution(adapter, CVRPNearestFeasibleCustomerHeuristic(adapter))


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


def test_constructive_tie_break_does_not_require_action_ordering() -> None:
    @dataclass(frozen=True)
    class OpaqueAction:
        name: str

    class OneStepProblem:
        def initial_state(self):
            return None

        def is_complete(self, state):
            return state is not None

        def feasible_actions(self, state):
            return (OpaqueAction("first"), OpaqueAction("second"))

        def apply_action(self, state, action):
            return action.name

        def finalize(self, state):
            return state

    class EqualScoreHeuristic:
        heuristic_id = "equal-score"

        def score(self, state, action):
            return 0.0

    # OpaqueAction 未定义顺序比较；公共内核必须按动作枚举顺序稳定打破平局。
    assert construct_solution(OneStepProblem(), EqualScoreHeuristic()) == "first"
