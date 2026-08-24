"""标准路由 evaluator 的浮点边界真值。"""

import pytest

from agriautolab.contracts.geometry import Point
from agriautolab.contracts.routing import RoutingNode, TSPProblem
from agriautolab.optimization.tsp import TSPTour, evaluate_tsp_tour


def node(node_id: str, x: float, y: float = 0.0) -> RoutingNode:
    return RoutingNode(node_id=node_id, position=Point(x=x, y=y))


def test_tsp_evaluator_rejects_edge_distance_overflow_from_finite_coordinates() -> None:
    problem = TSPProblem(
        problem_id="edge-overflow",
        nodes=(node("A", 1e308), node("B", -1e308)),
        start_node_id="A",
    )

    with pytest.raises(ValueError, match="欧氏距离超出"):
        evaluate_tsp_tour(problem, TSPTour(node_ids=("A", "B", "A")))


def test_tsp_evaluator_rejects_route_sum_overflow_from_finite_edges() -> None:
    problem = TSPProblem(
        problem_id="route-sum-overflow",
        nodes=(node("A", 0.0), node("B", 1e308), node("C", 0.0)),
        start_node_id="A",
    )

    # 每条边都可有限表示，但 1e308 + 1e308 的总长度超出 binary64 范围。
    with pytest.raises(ValueError, match="距离总和超出"):
        evaluate_tsp_tour(problem, TSPTour(node_ids=("A", "B", "C", "A")))
