"""CVRP 构造容量必须从路线重算，不能累计减法漂移。"""

from agriautolab.algorithms.constructive import CVRPNearestFeasibleCustomerHeuristic
from agriautolab.contracts.geometry import Point
from agriautolab.contracts.routing import CVRPCustomer, CVRPProblem, RoutingNode
from agriautolab.optimization import construct_solution
from agriautolab.optimization.cvrp import CVRPConstructiveProblem, evaluate_cvrp_solution


def test_hundred_decimal_demands_exactly_fill_one_vehicle() -> None:
    depot = RoutingNode(node_id="D", position=Point(x=0.0, y=0.0))
    customers = tuple(
        CVRPCustomer(
            node_id=f"C{index:03d}",
            position=Point(x=float(index + 1), y=0.0),
            demand=0.01,
        )
        for index in range(100)
    )
    problem = CVRPProblem(
        problem_id="hundred-hundredths",
        depot=depot,
        customers=customers,
        vehicle_capacity=1.0,
    )
    adapter = CVRPConstructiveProblem(problem)
    solution = construct_solution(adapter, CVRPNearestFeasibleCustomerHeuristic(adapter))

    # 连续做 `remaining -= 0.01` 会在最后一个客户前漂到约
    # 0.009999999999999247，并错误拆成第二辆车。fsum 路线重算必须保持数学真值。
    assert len(solution.routes) == 1
    assert solution.routes[0][0] == "D"
    assert solution.routes[0][-1] == "D"
    assert len(solution.routes[0][1:-1]) == 100
    assert evaluate_cvrp_solution(problem, solution).vehicle_count == 1
