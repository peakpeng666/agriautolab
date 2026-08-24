"""标准路由问题共享的米制几何计算。

问题契约保证坐标系单位为米；这里集中实现边长与路线长度，避免 TSP/CVRP 各自
复制一份距离公式后逐渐产生语义漂移。
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

from agriautolab.contracts.routing import RoutingNode


def euclidean_node_distance_m(left: RoutingNode, right: RoutingNode) -> float:
    """两个路由节点之间的二维欧氏距离，单位 m。"""
    return math.hypot(left.position.x - right.position.x, left.position.y - right.position.y)


def route_length_m(nodes_by_id: Mapping[str, RoutingNode], node_ids: Sequence[str]) -> float:
    """按给定节点序列独立复算折线路径长度，单位 m。"""
    return float(sum(
        euclidean_node_distance_m(nodes_by_id[left], nodes_by_id[right])
        for left, right in zip(node_ids, node_ids[1:])
    ))
