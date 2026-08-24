"""标准路由问题共享的米制几何计算。

问题契约保证输入坐标有限且单位为米；这里继续约束派生距离也必须有限。有限坐标的
差值或多段距离之和仍可能浮点溢出，因此不能只依赖输入 schema。
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence

from agriautolab.contracts.routing import RoutingNode


def euclidean_node_distance_m(left: RoutingNode, right: RoutingNode) -> float:
    """两个路由节点之间的二维欧氏距离，单位 m；不可表示时 fail closed。"""
    dx = left.position.x - right.position.x
    dy = left.position.y - right.position.y
    distance = math.hypot(dx, dy)
    if not math.isfinite(distance):
        raise ValueError(
            f"节点 {left.node_id!r} 与 {right.node_id!r} 的欧氏距离超出有限浮点表示范围"
        )
    return distance


def sum_distances_m(distances: Iterable[float]) -> float:
    """高精度累加有限距离；总量溢出时不返回 `inf` 污染下游目标。"""
    try:
        total = math.fsum(distances)
    except OverflowError as error:
        raise ValueError("距离总和超出有限浮点表示范围") from error
    if not math.isfinite(total):
        raise ValueError("距离总和不是有限数")
    return float(total)


def route_length_m(nodes_by_id: Mapping[str, RoutingNode], node_ids: Sequence[str]) -> float:
    """按给定节点序列独立复算折线路径长度，单位 m。"""
    return sum_distances_m(
        euclidean_node_distance_m(nodes_by_id[left], nodes_by_id[right])
        for left, right in zip(node_ids, node_ids[1:])
    )
