"""TSPLIB / CVRPLIB 接入的真值测试。

每条都需在"错误实现"下失败——不是覆盖率测试。本文件钉住的核心是**可比性**：
接入标准实例的唯一价值是能与文献同表比较，而这只有在距离语义与文献一致时才成立。
"""

from __future__ import annotations

import math
import pathlib

import pytest

from agriautolab.algorithms.constructive.tsp import TSPNearestNeighborHeuristic
from agriautolab.contracts.errors import TSPLIBFormatError
from agriautolab.contracts.geometry import Point
from agriautolab.datasets.tsplib import (
    SUPPORTED_EDGE_WEIGHT_TYPES,
    load_tsplib_cvrp,
    load_tsplib_tsp,
    nint,
    optimality_gap,
    tsplib_distance,
    tsplib_tour_length,
    tsplib_tour_length_of,
)
from agriautolab.optimization.constructive import construct_solution
from agriautolab.optimization.routing import euclidean_node_distance_m, route_length_m
from agriautolab.optimization.tsp import TSPConstructiveProblem, evaluate_tsp_tour

# 手算方阵：边长 10，最优闭合回路 = 40（EUC_2D 下每边恰为整数 10）
SQUARE_TSP = """NAME : square4
COMMENT : hand-checkable square (Optimal value: 40)
TYPE : TSP
DIMENSION : 4
EDGE_WEIGHT_TYPE : EUC_2D
NODE_COORD_SECTION
1 0 0
2 0 10
3 10 10
4 10 0
EOF
"""

# 三角形：三条边的精确长度都不是整数，取整与否差别显著
TRIANGLE_TSP = """NAME : tri3
TYPE : TSP
DIMENSION : 3
EDGE_WEIGHT_TYPE : EUC_2D
NODE_COORD_SECTION
1 0 0
2 1 1
3 3 0
EOF
"""

TOY_CVRP = """NAME : toy-n5-k2
COMMENT : (hand made, No of trucks: 2, Optimal value: 100)
TYPE : CVRP
DIMENSION : 5
EDGE_WEIGHT_TYPE : EUC_2D
CAPACITY : 30
NODE_COORD_SECTION
 1 0 0
 2 10 0
 3 20 0
 4 0 10
 5 0 20
DEMAND_SECTION
1 0
2 10
3 10
4 10
5 10
DEPOT_SECTION
 1
 -1
EOF
"""


# ---------- 核心：距离语义需与 TSPLIB 一致 ----------

def test_nint_is_round_half_up_not_bankers() -> None:
    """TSPLIB 的 nint 是四舍五入 `(int)(x+0.5)`，不是 Python 的银行家舍入。

    【证伪力】用内建 `round()` 实现时 `round(0.5)==0`、`round(2.5)==2`，
    本测试的前两条断言直接变红。整数网格坐标下 `.5` 边界很常见，
    用错会让 tour 长度系统性偏低，与公开最优值的 gap 全部失真。
    """
    assert nint(0.5) == 1 and round(0.5) == 0
    assert nint(2.5) == 3 and round(2.5) == 2
    assert nint(1.5) == 2 == round(1.5)          # 奇数侧两者恰好一致
    assert nint(2.4999) == 2
    assert nint(7.0) == 7


def test_tsplib_distance_differs_from_exact_euclidean() -> None:
    """EUC_2D 是取整距离，与仓库的精确 `hypot` 不是同一个目标函数。

    【证伪力】若 `tsplib_distance` 直接返回 `math.hypot`，第二组断言变红。
    这条是整个模块存在的理由：公开最优值按取整距离算，混用即不可比。
    """
    euc = tsplib_distance("EUC_2D")
    a, b = Point(x=0.0, y=0.0), Point(x=1.0, y=1.0)
    assert euc(a, b) == 1.0                                   # nint(1.41421...) = 1
    assert euclidean_node_distance_m(
        _node("a", a), _node("b", b),
    ) == pytest.approx(math.sqrt(2.0))
    assert euc(a, b) != pytest.approx(math.sqrt(2.0))

    ceil = tsplib_distance("CEIL_2D")
    assert ceil(a, b) == 2.0                                  # ceil(1.41421...) = 2


def test_unsupported_edge_weight_types_are_rejected_by_name() -> None:
    """GEO / ATT / EXPLICIT 等需拒绝并点名，不能按欧氏静默降级。

    【证伪力】静默降级的实现会返回一个可用的距离函数，本测试的 raises 变红——
    而那种实现产出的数看着合理，实则与文献不可比。
    """
    for kind in ("GEO", "ATT", "EXPLICIT", "MAN_2D", "MAX_2D", "XRAY1"):
        with pytest.raises(TSPLIBFormatError, match="不支持的 EDGE_WEIGHT_TYPE"):
            tsplib_distance(kind)
    assert set(SUPPORTED_EDGE_WEIGHT_TYPES) == {"EUC_2D", "CEIL_2D"}

    geo_instance = SQUARE_TSP.replace("EUC_2D", "GEO")
    with pytest.raises(TSPLIBFormatError, match="不支持的 EDGE_WEIGHT_TYPE"):
        load_tsplib_tsp(geo_instance)


# ---------- 解析 ----------

def test_square_instance_parses_with_hand_checked_geometry() -> None:
    problem, instance = load_tsplib_tsp(SQUARE_TSP)

    assert instance.name == "square4"
    assert instance.dimension == 4
    assert instance.edge_weight_type == "EUC_2D"
    assert instance.published_optimum == 40.0

    assert [node.node_id for node in problem.nodes] == ["n1", "n2", "n3", "n4"]
    assert problem.start_node_id == "n1"
    assert problem.nodes[0].position == Point(x=0.0, y=0.0)
    assert problem.nodes[2].position == Point(x=10.0, y=10.0)

    # 手算：沿方阵四边一圈，每边 EUC_2D 恰为 10
    order = ("n1", "n2", "n3", "n4")
    nodes_by_id = {node.node_id: node for node in problem.nodes}
    assert tsplib_tour_length(nodes_by_id, order, "EUC_2D") == 40.0
    assert optimality_gap(40.0, instance.published_optimum) == 0.0


def test_node_ids_sort_numerically_via_zero_padding() -> None:
    """节点号零填充到维数宽度，使字典序与数值序一致。

    【证伪力】直接用 "1".."12" 时 `sorted` 给出 1,10,11,12,2,...——构造式问题
    按 node_id 排序枚举可行动作，顺序与文献不一致会在并列决胜处产生无谓差异。
    """
    body = "\n".join(f"{i} {i} 0" for i in range(1, 13))
    text = (
        "NAME : wide12\nTYPE : TSP\nDIMENSION : 12\nEDGE_WEIGHT_TYPE : EUC_2D\n"
        f"NODE_COORD_SECTION\n{body}\nEOF\n"
    )
    problem, instance = load_tsplib_tsp(text)
    ids = [node.node_id for node in problem.nodes]
    assert ids == sorted(ids)
    assert ids[0] == "n01" and ids[-1] == "n12"
    assert instance.tsplib_index("n07") == 7
    assert instance.node_id(7) == "n07"


def test_dimension_mismatch_fails_closed() -> None:
    """声明的 DIMENSION 与实际节点数不符时不能猜哪个对。"""
    text = SQUARE_TSP.replace("DIMENSION : 4", "DIMENSION : 5")
    with pytest.raises(TSPLIBFormatError, match="DIMENSION 声明"):
        load_tsplib_tsp(text)


def test_missing_coord_section_names_the_explicit_case() -> None:
    text = SQUARE_TSP.split("NODE_COORD_SECTION")[0] + "EOF\n"
    with pytest.raises(TSPLIBFormatError, match="NODE_COORD_SECTION"):
        load_tsplib_tsp(text)


def test_duplicate_node_index_is_rejected() -> None:
    text = SQUARE_TSP.replace("4 10 0", "3 10 0")
    with pytest.raises(TSPLIBFormatError, match="重复节点号"):
        load_tsplib_tsp(text)


def test_wrong_type_is_rejected() -> None:
    with pytest.raises(TSPLIBFormatError, match="只接受"):
        load_tsplib_cvrp(SQUARE_TSP)
    with pytest.raises(TSPLIBFormatError, match="只接受"):
        load_tsplib_tsp(TOY_CVRP)


# ---------- CVRP ----------

def test_cvrp_instance_separates_depot_from_customers() -> None:
    problem, instance = load_tsplib_cvrp(TOY_CVRP)

    assert instance.name == "toy-n5-k2"
    assert instance.capacity == 30.0
    assert instance.declared_vehicles == 2
    assert instance.published_optimum == 100.0

    assert problem.depot.node_id == "n1"
    assert problem.depot.position == Point(x=0.0, y=0.0)
    assert [c.node_id for c in problem.customers] == ["n2", "n3", "n4", "n5"]
    assert all(c.demand == 10.0 for c in problem.customers)
    assert problem.vehicle_capacity == 30.0
    assert problem.max_vehicles == 2


def test_cvrp_depot_with_nonzero_demand_fails_closed() -> None:
    """仓库 demand 非零说明该文件的仓库语义与本契约不同，不能当普通客户处理。

    【证伪力】若把仓库也塞进 customers，`CVRPCustomer.demand` 的 `gt=0` 会让
    demand=0 的仓库直接被 pydantic 拒；而 demand 非零的仓库反而会**静默通过**，
    变成一个多出来的客户——这正是本测试要挡住的形态。
    """
    text = TOY_CVRP.replace("\n1 0\n2 10", "\n1 7\n2 10")
    assert text != TOY_CVRP, "测试数据替换未生效"
    with pytest.raises(TSPLIBFormatError, match="仓库节点"):
        load_tsplib_cvrp(text)


def test_multi_depot_is_rejected() -> None:
    text = TOY_CVRP.replace(" 1\n -1", " 1\n 2\n -1")
    with pytest.raises(TSPLIBFormatError, match="单仓库"):
        load_tsplib_cvrp(text)


def test_explicit_vehicle_count_must_agree_with_comment() -> None:
    """显式 max_vehicles 与 COMMENT 声明冲突时，静默采信任何一方都是错的。"""
    with pytest.raises(TSPLIBFormatError, match="不一致"):
        load_tsplib_cvrp(TOY_CVRP, max_vehicles=3)
    problem, _ = load_tsplib_cvrp(TOY_CVRP, max_vehicles=2)
    assert problem.max_vehicles == 2


def test_vehicle_count_is_not_inferred_from_the_name() -> None:
    """文件名里的 `k5` 是约定不是声明；没有 COMMENT 就是 None，不猜。"""
    text = TOY_CVRP.replace("COMMENT : (hand made, No of trucks: 2, Optimal value: 100)\n", "")
    problem, instance = load_tsplib_cvrp(text)
    assert instance.declared_vehicles is None
    assert instance.published_optimum is None
    assert problem.max_vehicles is None


def test_demand_and_coord_node_sets_must_match() -> None:
    text = TOY_CVRP.replace("\n5 10\nDEPOT_SECTION", "\n6 10\nDEPOT_SECTION")
    assert text != TOY_CVRP, "测试数据替换未生效"
    with pytest.raises(TSPLIBFormatError, match="节点集合不一致"):
        load_tsplib_cvrp(text)


# ---------- 端到端：与文献口径的 gap ----------

def test_nearest_neighbour_tour_is_scored_under_tsplib_semantics() -> None:
    """跑通「标准实例 → 公共 constructive 协议 → TSPLIB 口径长度 → gap」。

    三角形实例上两种口径明确分开：
      精确欧氏 = sqrt(2) + sqrt(5) + 3 ≈ 6.6503
      TSPLIB   = nint(1.4142) + nint(2.2361) + nint(3) = 1 + 2 + 3 = 6
    【证伪力】若把 evaluator 的精确长度当作可与文献比较的值，两者相差 10%，
    任何 gap 都会被这条系统性偏差污染。
    """
    problem, instance = load_tsplib_tsp(TRIANGLE_TSP)
    constructive = TSPConstructiveProblem(problem)
    tour = construct_solution(constructive, TSPNearestNeighborHeuristic(problem=constructive))

    assert tour.node_ids[0] == tour.node_ids[-1] == "n1"
    assert set(tour.node_ids[:-1]) == {"n1", "n2", "n3"}

    exact = evaluate_tsp_tour(problem, tour).tour_length_m
    assert exact == pytest.approx(math.sqrt(2.0) + math.sqrt(5.0) + 3.0)

    tsplib_value = tsplib_tour_length_of(problem, tour, instance.edge_weight_type)
    assert tsplib_value == 6.0
    assert tsplib_value != pytest.approx(exact)


def test_tour_length_rejects_non_permutation() -> None:
    """漏访问或重复访问都需拒绝——否则"更短的 tour"可能只是没走完。"""
    problem, _ = load_tsplib_tsp(SQUARE_TSP)
    nodes_by_id = {node.node_id: node for node in problem.nodes}
    with pytest.raises(TSPLIBFormatError, match="精确置换"):
        tsplib_tour_length(nodes_by_id, ("n1", "n2", "n3"), "EUC_2D")
    with pytest.raises(TSPLIBFormatError, match="精确置换"):
        tsplib_tour_length(nodes_by_id, ("n1", "n2", "n3", "n3"), "EUC_2D")
    # TSPTour.node_ids 首尾重复起点，直接传入同样应被拒（正确用法见 tsplib_tour_length_of）
    with pytest.raises(TSPLIBFormatError, match="精确置换"):
        tsplib_tour_length(nodes_by_id, ("n1", "n2", "n3", "n4", "n1"), "EUC_2D")


def test_tour_length_of_validates_the_closed_tour_before_stripping() -> None:
    """剥掉末位之前需先校验回路，否则非法末位会被静默丢掉。

    【证伪力】`TSPTour` 是无校验 dataclass。构造"前 n 项是合法置换、末位是任意
    节点"的序列时，直接 `[:-1]` 的实现会算出一个看着合法的长度与 gap，
    而同一份输入在 `evaluate_tsp_tour` 那里会被拒——两条评估路径对同一个回路
    给出相反判断，比算错更坏。
    """
    from agriautolab.optimization.tsp import TSPTour

    problem, instance = load_tsplib_tsp(SQUARE_TSP)

    # 前 4 项是合法置换，末位却不是起点
    bogus = TSPTour(node_ids=("n1", "n2", "n3", "n4", "n3"))
    with pytest.raises(TSPLIBFormatError, match="出发并回到"):
        tsplib_tour_length_of(problem, bogus, instance.edge_weight_type)
    with pytest.raises(ValueError):                      # evaluator 同样拒绝
        evaluate_tsp_tour(problem, bogus)

    # 长度不对
    with pytest.raises(TSPLIBFormatError, match="节点数\\+1"):
        tsplib_tour_length_of(problem, TSPTour(node_ids=("n1", "n2", "n1")), instance.edge_weight_type)

    # 长度与首尾都对，但中间有重复 → 由置换检查兜住
    with pytest.raises(TSPLIBFormatError, match="精确置换"):
        tsplib_tour_length_of(
            problem, TSPTour(node_ids=("n1", "n2", "n2", "n4", "n1")), instance.edge_weight_type,
        )

    assert tsplib_tour_length_of(
        problem, TSPTour(node_ids=("n1", "n2", "n3", "n4", "n1")), instance.edge_weight_type,
    ) == 40.0


def test_duplicate_demand_row_is_rejected() -> None:
    """DEMAND_SECTION 的重复行不能后者覆盖前者——与 _parse_coords 同一纪律。

    【证伪力】全部节点齐备后再追加一行重复节点（拼接或手改实例的典型形态），
    节点集合比较照样通过，而该客户的 demand 已被悄悄改写，容量约束与路由结果
    随之改变却不报任何格式错误。
    """
    text = TOY_CVRP.replace("\n5 10\nDEPOT_SECTION", "\n5 10\n2 29\nDEPOT_SECTION")
    assert text != TOY_CVRP, "测试数据替换未生效"
    with pytest.raises(TSPLIBFormatError, match="重复节点号"):
        load_tsplib_cvrp(text)


def test_optimality_gap_rejects_degenerate_optimum() -> None:
    assert optimality_gap(44.0, 40.0) == pytest.approx(0.1)
    for bad in (0.0, -1.0):
        with pytest.raises(TSPLIBFormatError, match="must be positive"):
            optimality_gap(40.0, bad)


def _node(node_id: str, position: Point):
    from agriautolab.contracts.routing import RoutingNode

    return RoutingNode(node_id=node_id, position=position)


# ---------- 真实实例（opt-in，默认跳过） ----------

def _tsplib_dir():
    import os

    raw = os.environ.get("AGRIAUTOLAB_TSPLIB_DIR")
    return pathlib.Path(raw) if raw else None


@pytest.mark.skipif(
    _tsplib_dir() is None or not (_tsplib_dir() / "berlin52.tsp").exists(),
    reason="需要真实 TSPLIB 文件；设 AGRIAUTOLAB_TSPLIB_DIR 指向含 berlin52.tsp/.opt.tour 的目录",
)
def test_berlin52_optimal_tour_reproduces_the_published_optimum() -> None:
    """官方最优 tour 在本模块下需复算出**恰好** 7542。

    这是距离语义唯一的决定性验证：三种口径各自对应文献里的一种典型错法——

        逐边 nint（正确）      = 7542
        精确欧氏浮点求和        ≈ 7544.37   （最常见的错法）
        逐边向上取整           = 7570       （另一种错法）

    真实实例不入仓（不猜第三方数据许可），因此本测试 opt-in。
    参考获取方式见 PR 说明；三个数值本身已记入模块 docstring 作为回归锚点。
    """
    directory = _tsplib_dir()
    problem, instance = load_tsplib_tsp(directory / "berlin52.tsp")
    assert instance.name == "berlin52"
    assert instance.dimension == 52
    assert instance.edge_weight_type == "EUC_2D"

    tokens = (directory / "berlin52.opt.tour").read_text(encoding="utf-8").splitlines()
    order, started = [], False
    for line in tokens:
        token = line.strip()
        if token == "TOUR_SECTION":
            started = True
            continue
        if started and token and token not in ("-1", "EOF"):
            order.append(instance.node_id(int(token)))
        elif started and token in ("-1", "EOF"):
            break
    assert len(order) == 52

    nodes_by_id = {node.node_id: node for node in problem.nodes}
    assert tsplib_tour_length(nodes_by_id, tuple(order), "EUC_2D") == 7542.0

    closed = tuple(order) + (order[0],)
    exact = route_length_m(nodes_by_id, closed)
    assert exact == pytest.approx(7544.3659, abs=1e-3)
    assert optimality_gap(exact, 7542.0) == pytest.approx(3.14e-4, rel=0.05)
