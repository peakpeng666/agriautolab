"""CVRP Problem 只枚举硬约束可行动作，不隐藏 heuristic 策略。"""

from agriautolab.algorithms.constructive import CVRPNearestFeasibleCustomerHeuristic
from agriautolab.contracts.geometry import Point
from agriautolab.contracts.routing import CVRPCustomer, CVRPProblem, RoutingNode
from agriautolab.optimization import construct_solution
from agriautolab.optimization.cvrp import CVRPConstructiveProblem


def _node(node_id: str, x: float) -> RoutingNode:
    return RoutingNode(node_id=node_id, position=Point(x=x, y=0.0))


def _customer(node_id: str, x: float, demand: float) -> CVRPCustomer:
    return CVRPCustomer(node_id=node_id, position=Point(x=x, y=0.0), demand=demand)


def _problem() -> CVRPProblem:
    return CVRPProblem(
        problem_id="route-closure-boundary",
        depot=_node("D", 0.0),
        customers=(
            _customer("A", 1.0, 2.0),
            _customer("B", 2.0, 2.0),
        ),
        vehicle_capacity=10.0,
    )


def test_cvrp_problem_exposes_early_return_when_customer_still_fits() -> None:
    adapter = CVRPConstructiveProblem(_problem())
    state = adapter.apply_action(adapter.initial_state(), "A")

    # B 仍可装载，但提前回仓也满足所有硬约束；Problem 需同时暴露两者。
    assert adapter.feasible_actions(state) == ("B", "D")


def test_nearest_feasible_policy_not_problem_forces_fill_until_stuck() -> None:
    adapter = CVRPConstructiveProblem(_problem())
    solution = construct_solution(adapter, CVRPNearestFeasibleCustomerHeuristic(adapter))

    assert solution.routes == (("D", "A", "B", "D"),)


def test_alternative_heuristic_can_choose_early_return() -> None:
    adapter = CVRPConstructiveProblem(_problem())

    class EarlyReturnHeuristic:
        heuristic_id = "early-return-test"

        def score(self, state, action):
            if action == "D":
                return -1.0
            return 0.0 if action == "A" else 1.0

    solution = construct_solution(adapter, EarlyReturnHeuristic())
    assert solution.routes == (("D", "A", "D"), ("D", "B", "D"))
