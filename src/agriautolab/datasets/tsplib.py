"""TSPLIB / CVRPLIB 标准实例接入。

TSP/CVRP 在本项目里是自动算法设计之前的**方法学验证参考问题**，不是第二条研究
主线。接入标准实例的唯一目的，是让本仓库的 constructive 结果能与文献同表比较——
而这件事只有在**距离语义与文献一致**时才成立。

## 为什么必须单独提供距离函数

TSPLIB 的 `EUC_2D` 距离**是取整的**：

    xd = x_i - x_j ; yd = y_i - y_j
    d_ij = nint( sqrt(xd*xd + yd*yd) )

而本仓库的 `optimization.routing.euclidean_node_distance_m` 是**精确 `math.hypot`**。
公开的最优值（`Optimal value:` / TSPLIB 官方最优解）全部按取整距离计算，因此：

**用精确欧氏距离算出来的 tour 长度不能与公开最优值比 gap。** 两者不是同一个目标
函数。本模块因此提供 `tsplib_distance()` 与 `tsplib_tour_length()`，与几何距离
明确分开；两条路径都保留，谁也不许冒充谁。

## nint 不是 round

TSPLIB 的 `nint(x)` 定义为 `(int)(x + 0.5)`——**四舍五入**。Python 内建 `round()`
是**银行家舍入**：`round(2.5) == 2`，而 `nint(2.5) == 3`。整数网格坐标下 `.5`
边界并不罕见，用错会系统性偏低。`test_nint_is_round_half_up_not_bankers` 钉住这一点。

同理，规范写的是 `sqrt(xd*xd + yd*yd)` 而不是 `hypot`。`hypot` 精度更高，但在
`.5` 边界上可能与规范舍到不同的整数。为了与文献逐位一致，这里照抄规范式。

## 实测佐证（berlin52，官方最优 tour，公开最优值 7542）

用 TSPLIB 官方 `berlin52.opt.tour` 在本模块下复算，三种口径分别是：

    逐边 nint（本模块 EUC_2D）  = 7542.0      ← 与公开最优值逐位相等
    精确欧氏浮点求和             = 7544.3659   ← 文献里常见的 "7544.36" 错误
    逐边向上取整（CEIL_2D）      = 7570.0      ← 文献里常见的 "7570" 错误

误用精确欧氏会把 gap 虚报 0.0314%。这三个数各自对应文献记录的一种典型错法，
可作为任何后续改动的回归锚点。真实实例不入仓（不猜第三方数据许可），
对应测试以 `AGRIAUTOLAB_TSPLIB_DIR` 环境变量 opt-in，默认跳过。

## 支持范围（fail-closed）

只接受 `EUC_2D` 与 `CEIL_2D`——它们是纯二维坐标、可无损映射到 `TSPProblem` /
`CVRPProblem` 的欧氏契约。`GEO` / `ATT` / `EXPLICIT` / `MAN_2D` / `MAX_2D` 等
**明确拒绝并点名**，而不是静默按欧氏处理：那会产出看着合理、其实与文献不可比的数。
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping

from agriautolab.contracts.errors import TSPLIBFormatError
from agriautolab.contracts.geometry import Point
from agriautolab.contracts.routing import CVRPCustomer, CVRPProblem, RoutingNode, TSPProblem

#: 可无损映射到本项目欧氏契约的边权类型。其余一律 fail-closed。
SUPPORTED_EDGE_WEIGHT_TYPES = ("EUC_2D", "CEIL_2D")

_KEYWORD_LINE = re.compile(r"^\s*([A-Z_]+)\s*:\s*(.*?)\s*$")
_SECTION_LINE = re.compile(r"^\s*([A-Z_]+_SECTION|EOF)\s*$")
_OPTIMUM = re.compile(r"Optimal\s+value\s*:\s*([0-9]+(?:\.[0-9]+)?)", re.IGNORECASE)
_TRUCKS = re.compile(r"No\s+of\s+trucks\s*:\s*([0-9]+)", re.IGNORECASE)


@dataclass(frozen=True)
class TSPLIBInstance:
    """随契约对象一同返回的实例元数据。

    `published_optimum` 与 `declared_vehicles` 只在文件**自己写明**时才有值：
    从文件名反推（例如 `A-n32-k5` 的 `k5`）是猜测，本模块不做。
    """

    name: str
    problem_type: str
    dimension: int
    edge_weight_type: str
    comment: str
    published_optimum: float | None = None
    declared_vehicles: int | None = None
    capacity: float | None = None

    def node_id(self, tsplib_index: int) -> str:
        """TSPLIB 的 1 基节点号 -> 本项目的稳定 node_id。"""
        return _node_id(tsplib_index, self.dimension)

    def tsplib_index(self, node_id: str) -> int:
        """反向映射，便于把结果写回 TSPLIB 口径。"""
        if not node_id.startswith("n"):
            raise TSPLIBFormatError(f"不是本模块生成的 node_id：{node_id!r}")
        return int(node_id[1:])


def _node_id(index: int, dimension: int) -> str:
    """零填充到维数宽度，使字典序与数值序一致。

    构造式问题按 `sorted(node_id)` 枚举可行动作以保证稳定顺序；若直接用 "1".."32"，
    字典序会得到 1,10,11,...,2,20——仍然确定，但与文献的节点顺序不一致，
    并列决胜时会产生无谓的差异。
    """
    width = max(1, len(str(dimension)))
    return f"n{index:0{width}d}"


def nint(value: float) -> int:
    """TSPLIB 的 `nint`：`(int)(x + 0.5)`，四舍五入。

    **不要用 `round()`**：内建 round 是银行家舍入，`round(2.5) == 2`，
    而 TSPLIB 要求 `nint(2.5) == 3`。
    """
    if not math.isfinite(value):
        raise TSPLIBFormatError(f"nint 的输入必须有限：{value!r}")
    return int(value + 0.5)


def tsplib_distance(edge_weight_type: str) -> Callable[[Point, Point], float]:
    """返回与 TSPLIB 规范逐位一致的距离函数。

    刻意不复用 `optimization.routing.euclidean_node_distance_m`：那条路径是精确
    `hypot`，与公开最优值不是同一个目标函数（见模块 docstring）。
    """
    kind = edge_weight_type.strip().upper()
    if kind not in SUPPORTED_EDGE_WEIGHT_TYPES:
        raise TSPLIBFormatError(
            f"不支持的 EDGE_WEIGHT_TYPE：{edge_weight_type!r}。"
            f"本模块只接受 {SUPPORTED_EDGE_WEIGHT_TYPES}——"
            "把其它类型按欧氏处理会产出与文献不可比的数，因此拒绝而不是静默降级"
        )

    def distance(left: Point, right: Point) -> float:
        dx = left.x - right.x
        dy = left.y - right.y
        # 照抄规范式 sqrt(xd*xd + yd*yd)；hypot 精度更高但可能在 .5 边界舍到另一侧
        raw = math.sqrt(dx * dx + dy * dy)
        return float(nint(raw)) if kind == "EUC_2D" else float(math.ceil(raw))

    return distance


def tsplib_tour_length(
    nodes_by_id: Mapping[str, RoutingNode],
    visit_order: tuple[str, ...],
    edge_weight_type: str,
    *,
    closed: bool = True,
) -> float:
    """按 TSPLIB 距离复算巡回长度；`closed` 表示回到起点。

    只接受**恰好一次覆盖全部节点**的访问序：少一个、多一个、或有重复都 fail-closed，
    否则"更短的 tour"可能只是漏访问了节点。
    """
    expected = set(nodes_by_id)
    if sorted(visit_order) != sorted(expected):
        raise TSPLIBFormatError(
            f"访问序必须是全部节点的精确置换：给了 {len(visit_order)} 个"
            f"（去重后 {len(set(visit_order))}），实例有 {len(expected)} 个"
        )
    distance = tsplib_distance(edge_weight_type)
    total = 0.0
    for left, right in zip(visit_order, visit_order[1:]):
        total += distance(nodes_by_id[left].position, nodes_by_id[right].position)
    if closed and len(visit_order) > 1:
        total += distance(nodes_by_id[visit_order[-1]].position, nodes_by_id[visit_order[0]].position)
    return total


def tsplib_tour_length_of(problem: TSPProblem, tour, edge_weight_type: str) -> float:
    """`TSPTour` 的便捷入口：它的 `node_ids` 首尾重复起点，这里剥掉再算闭合长度。

    直接把 `tour.node_ids` 传给 `tsplib_tour_length` 会因重复起点被判为非置换。
    提供这个入口是为了让"正确用法"比"错误用法"更顺手。

    **剥掉末位之前必须先校验回路本身**：`TSPTour` 是无校验的 dataclass，调用方
    完全可以构造一个"前 n 项是合法置换、末位是任意节点"的序列。若直接 `[:-1]`，
    那个非法末位会被静默丢掉，本函数照样算出一个看着合法的长度与 gap——而同一个
    回路在 `evaluate_tsp_tour` 那里会因"没回到 start_node_id"被拒。两条评估路径
    对同一份输入给出相反判断，是比算错更坏的失败模式。
    """
    expected_length = len(problem.nodes) + 1
    if len(tour.node_ids) != expected_length:
        raise TSPLIBFormatError(
            f"闭合回路长度必须是节点数+1={expected_length}，实际 {len(tour.node_ids)}"
        )
    if tour.node_ids[0] != problem.start_node_id or tour.node_ids[-1] != problem.start_node_id:
        raise TSPLIBFormatError(
            f"闭合回路必须从 {problem.start_node_id!r} 出发并回到该节点，"
            f"实际首尾为 {tour.node_ids[0]!r} / {tour.node_ids[-1]!r}"
        )
    nodes_by_id = {node.node_id: node for node in problem.nodes}
    # 前 n 项是否为全节点置换，由 tsplib_tour_length 统一 fail-closed
    return tsplib_tour_length(nodes_by_id, tuple(tour.node_ids[:-1]), edge_weight_type, closed=True)


def optimality_gap(value: float, optimum: float) -> float:
    """相对最优值的 gap，与文献口径一致：(value - optimum) / optimum。"""
    if not math.isfinite(value) or not math.isfinite(optimum):
        raise TSPLIBFormatError(f"gap 的输入必须有限：value={value!r} optimum={optimum!r}")
    if optimum <= 0.0:
        raise TSPLIBFormatError(f"最优值必须为正才能算相对 gap：{optimum!r}")
    return (value - optimum) / optimum


# ---------------- 解析 ----------------

def _read(source: str | Path) -> str:
    """接受路径或实例文本。

    区分方式：TSPLIB 文本必然含换行，而路径不会。不用 `Path(...).exists()` 直接
    试探任意字符串——过长或含 NUL 的文本会让 stat 抛 OSError/ValueError。
    """
    if isinstance(source, Path):
        return source.read_text(encoding="utf-8")
    text = str(source)
    if "\n" not in text and len(text) < 4096:
        try:
            candidate = Path(text)
            if candidate.exists():
                return candidate.read_text(encoding="utf-8")
        except (OSError, ValueError):
            pass
    return text


def _split_sections(text: str) -> tuple[dict[str, str], dict[str, list[str]]]:
    """把 TSPLIB 文本拆成 `KEY : VALUE` 与 `*_SECTION` 两部分。"""
    keywords: dict[str, str] = {}
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line.strip():
            continue
        section = _SECTION_LINE.match(line)
        if section:
            name = section.group(1)
            if name == "EOF":
                current = None
                continue
            current = name
            sections.setdefault(current, [])
            continue
        keyword = _KEYWORD_LINE.match(line)
        if keyword and current is None:
            keywords[keyword.group(1)] = keyword.group(2)
            continue
        if current is None:
            raise TSPLIBFormatError(f"位于任何 section 之外的数据行：{line!r}")
        sections[current].append(line.strip())
    return keywords, sections


def _require(keywords: Mapping[str, str], key: str) -> str:
    if key not in keywords:
        raise TSPLIBFormatError(f"缺少必需字段 {key}；已读到：{sorted(keywords)}")
    return keywords[key]


def _parse_metadata(keywords: Mapping[str, str], expected_type: str) -> TSPLIBInstance:
    problem_type = _require(keywords, "TYPE").upper()
    if problem_type != expected_type:
        raise TSPLIBFormatError(f"TYPE 是 {problem_type!r}，本入口只接受 {expected_type!r}")

    edge_weight_type = _require(keywords, "EDGE_WEIGHT_TYPE").upper()
    if edge_weight_type not in SUPPORTED_EDGE_WEIGHT_TYPES:
        raise TSPLIBFormatError(
            f"不支持的 EDGE_WEIGHT_TYPE：{edge_weight_type!r}。"
            f"本模块只接受 {SUPPORTED_EDGE_WEIGHT_TYPES}；"
            "GEO / ATT / EXPLICIT 等的距离语义与二维欧氏契约不同，"
            "静默按欧氏处理会产出与文献不可比的数"
        )

    try:
        dimension = int(_require(keywords, "DIMENSION"))
    except ValueError as error:
        raise TSPLIBFormatError(f"DIMENSION 不是整数：{keywords.get('DIMENSION')!r}") from error
    if dimension < 2:
        raise TSPLIBFormatError(f"DIMENSION 必须 >= 2：{dimension}")

    comment = keywords.get("COMMENT", "")
    optimum_match = _OPTIMUM.search(comment)
    trucks_match = _TRUCKS.search(comment)
    capacity = float(keywords["CAPACITY"]) if "CAPACITY" in keywords else None

    return TSPLIBInstance(
        name=keywords.get("NAME", "").strip(),
        problem_type=problem_type,
        dimension=dimension,
        edge_weight_type=edge_weight_type,
        comment=comment,
        published_optimum=float(optimum_match.group(1)) if optimum_match else None,
        declared_vehicles=int(trucks_match.group(1)) if trucks_match else None,
        capacity=capacity,
    )


def _parse_coords(lines: list[str], dimension: int) -> dict[int, Point]:
    coords: dict[int, Point] = {}
    for line in lines:
        parts = line.split()
        if len(parts) < 3:
            raise TSPLIBFormatError(f"NODE_COORD_SECTION 行需要 3 个字段：{line!r}")
        try:
            index = int(parts[0])
            x, y = float(parts[1]), float(parts[2])
        except ValueError as error:
            raise TSPLIBFormatError(f"NODE_COORD_SECTION 行无法解析：{line!r}") from error
        if index in coords:
            raise TSPLIBFormatError(f"NODE_COORD_SECTION 出现重复节点号 {index}")
        coords[index] = Point(x=x, y=y)
    if len(coords) != dimension:
        raise TSPLIBFormatError(
            f"NODE_COORD_SECTION 有 {len(coords)} 个节点，DIMENSION 声明 {dimension}——"
            "声明与数据不一致时不能猜哪个对"
        )
    return coords


def load_tsplib_tsp(source: str | Path) -> tuple[TSPProblem, TSPLIBInstance]:
    """读 TSPLIB `.tsp` 实例；起点固定为 TSPLIB 的 1 号节点。"""
    keywords, sections = _split_sections(_read(source))
    instance = _parse_metadata(keywords, "TSP")
    if "NODE_COORD_SECTION" not in sections:
        raise TSPLIBFormatError("缺少 NODE_COORD_SECTION；EXPLICIT 边权矩阵不在支持范围内")

    coords = _parse_coords(sections["NODE_COORD_SECTION"], instance.dimension)
    nodes = tuple(
        RoutingNode(node_id=_node_id(index, instance.dimension), position=coords[index])
        for index in sorted(coords)
    )
    problem = TSPProblem(
        problem_id=instance.name or "tsplib",
        nodes=nodes,
        start_node_id=_node_id(min(coords), instance.dimension),
    )
    return problem, instance


def load_tsplib_cvrp(
    source: str | Path,
    *,
    max_vehicles: int | None = None,
) -> tuple[CVRPProblem, TSPLIBInstance]:
    """读 CVRPLIB `.vrp` 实例。

    `max_vehicles` 显式给定时与 `COMMENT` 里的 `No of trucks` **必须一致**，
    不一致即 fail-closed——两个都写了却对不上，说明调用方与文件有分歧，
    这时静默采信任何一方都是错的。两者都没有则为 `None`（车辆数不设上限）。
    """
    keywords, sections = _split_sections(_read(source))
    instance = _parse_metadata(keywords, "CVRP")
    if instance.capacity is None:
        raise TSPLIBFormatError("CVRP 实例缺少 CAPACITY")
    for required in ("NODE_COORD_SECTION", "DEMAND_SECTION", "DEPOT_SECTION"):
        if required not in sections:
            raise TSPLIBFormatError(f"CVRP 实例缺少 {required}")

    coords = _parse_coords(sections["NODE_COORD_SECTION"], instance.dimension)

    demands: dict[int, float] = {}
    for line in sections["DEMAND_SECTION"]:
        parts = line.split()
        if len(parts) < 2:
            raise TSPLIBFormatError(f"DEMAND_SECTION 行需要 2 个字段：{line!r}")
        try:
            index, demand = int(parts[0]), float(parts[1])
        except ValueError as error:
            raise TSPLIBFormatError(f"DEMAND_SECTION 行无法解析：{line!r}") from error
        # 与 _parse_coords 同一纪律：重复行不能后者覆盖前者。全节点齐备时再多一行
        # 重复节点，节点集合比较照样通过，而容量约束已被悄悄改写。
        if index in demands:
            raise TSPLIBFormatError(f"DEMAND_SECTION 出现重复节点号 {index}")
        demands[index] = demand
    if sorted(demands) != sorted(coords):
        raise TSPLIBFormatError("DEMAND_SECTION 与 NODE_COORD_SECTION 的节点集合不一致")

    depot_indices = [
        int(token)
        for line in sections["DEPOT_SECTION"]
        for token in line.split()
        if token.strip("-").isdigit() and int(token) != -1
    ]
    if len(depot_indices) != 1:
        raise TSPLIBFormatError(
            f"本契约只支持单仓库；DEPOT_SECTION 给出 {len(depot_indices)} 个：{depot_indices}"
        )
    depot_index = depot_indices[0]
    if depot_index not in coords:
        raise TSPLIBFormatError(f"DEPOT_SECTION 指向不存在的节点 {depot_index}")
    if demands[depot_index] != 0.0:
        raise TSPLIBFormatError(
            f"仓库节点 {depot_index} 的 demand 是 {demands[depot_index]!r}，应为 0——"
            "非零说明该文件的仓库语义与本契约不同，不能当作普通客户处理"
        )

    if max_vehicles is not None and instance.declared_vehicles is not None:
        if max_vehicles != instance.declared_vehicles:
            raise TSPLIBFormatError(
                f"显式 max_vehicles={max_vehicles} 与 COMMENT 声明的 "
                f"No of trucks={instance.declared_vehicles} 不一致"
            )
    effective_vehicles = max_vehicles if max_vehicles is not None else instance.declared_vehicles

    problem = CVRPProblem(
        problem_id=instance.name or "cvrplib",
        depot=RoutingNode(
            node_id=_node_id(depot_index, instance.dimension), position=coords[depot_index],
        ),
        customers=tuple(
            CVRPCustomer(
                node_id=_node_id(index, instance.dimension),
                position=coords[index],
                demand=demands[index],
            )
            for index in sorted(coords)
            if index != depot_index
        ),
        vehicle_capacity=instance.capacity,
        max_vehicles=effective_vehicles,
    )
    return problem, instance
