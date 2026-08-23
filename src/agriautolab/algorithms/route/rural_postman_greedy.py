"""贪心 Rural Postman 排序：作业段排序按弧路径问题建模，不是 TSP。

见 管梅谷 (1962)，中国邮递员问题（Chinese Postman Problem）的弧变量版
Rural Postman Problem（RPP）：作业段是**必经弧**（有起点航向与终点航向），
转移段是可选弧，目标是总转移代价最小。

为什么这个区分重要：TSP 建模把作业段缩成一个质心点，同时丢掉两个自由度——
段有方向（沿 +u 进入和沿 -u 进入的转移代价不同），且两端都能作为入口。
Dubins 转移代价对入口选择敏感（反平行进入与顺行进入可差 pi 倍弧长），
丢掉它是系统性高估。这里实现确定性的 O(n^2) 贪心：从当前位姿出发，
在所有未访问段的两个入口位姿里选 Dubins 转移最短者；平局按 (swath_id, 入口端序)
破平。贪心不给最优 RPP，只给可行且确定的排序——Block B 的主张在 Pareto 结构，
不在单个排序的最优性。
"""

from __future__ import annotations

import math

from agriautolab.contracts.artifacts import RouteArtifact, SwathTraversal, SwathsArtifact
from agriautolab.contracts.enums import SwathDirection
from agriautolab.kinematics.dubins import dubins_length


def _heading(points) -> float:
    return math.atan2(points[-1].y - points[0].y, points[-1].x - points[0].x)


def _entry_poses(swath):
    """两个入口位姿：(起点, FORWARD) 与 (终点, REVERSE)。出口位姿随之确定。"""
    points = swath.centerline.points
    heading = _heading(points)
    return (
        ((points[0].x, points[0].y, heading), SwathDirection.FORWARD,
         (points[-1].x, points[-1].y, heading)),
        ((points[-1].x, points[-1].y, heading + math.pi), SwathDirection.REVERSE,
         (points[0].x, points[0].y, heading + math.pi)),
    )


class GreedyRuralPostmanRoutePlanner:
    algorithm_id = "rural_postman_greedy"

    def run(self, artifact: SwathsArtifact, *, min_turning_radius_m: float) -> RouteArtifact:
        if min_turning_radius_m <= 0.0:
            raise ValueError(f"rural_postman_greedy 需要正的转弯半径，实际 {min_turning_radius_m!r}")
        swaths = tuple(sorted(artifact.swaths, key=lambda swath: swath.swath_id))
        entries = {swath.swath_id: _entry_poses(swath) for swath in swaths}
        remaining = [swath.swath_id for swath in swaths]
        traversals: list[SwathTraversal] = []
        current_pose = None
        while remaining:
            best = None
            for swath_id in remaining:
                for entry_index, (entry_pose, direction, _) in enumerate(entries[swath_id]):
                    if current_pose is None:
                        cost, key = 0.0, (swath_id, entry_index)
                    else:
                        cost = dubins_length(current_pose, entry_pose, min_turning_radius_m)
                        key = (cost, swath_id, entry_index)
                    if best is None or key < best[0]:
                        best = (key, swath_id, entry_index)
            _, swath_id, entry_index = best
            _, direction, exit_pose = entries[swath_id][entry_index]
            traversals.append(SwathTraversal(swath_id=swath_id, direction=direction))
            remaining.remove(swath_id)
            current_pose = exit_pose
        return RouteArtifact(traversals=tuple(traversals), swaths=swaths)


# legacy 别名：canonical 类名见 docs/NAMING.md。
RuralPostmanGreedy = GreedyRuralPostmanRoutePlanner
