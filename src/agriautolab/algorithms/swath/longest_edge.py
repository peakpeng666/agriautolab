"""最长边 swath：方向平行于多边形自身最长的那条外环边。

与 Block A 的 longest_edge_swath（MBR 最长边）不是同一个量：凸多边形上两者一致，
凹多边形上会给出不同方向。保留两个算法正是为了在池子里体现这个差异。"""

import math

from agriautolab.algorithms.swath._sweep import canonical_direction, swaths_along_direction
from agriautolab.contracts.artifacts import SwathsArtifact
from agriautolab.contracts.geometry import PolygonSpec
from agriautolab.contracts.problem import CoverageProblem
from agriautolab.geometry.validate import polygon_from_spec


def longest_edge_direction(polygon) -> tuple[float, float]:
    coords = list(polygon.exterior.coords)
    best = None
    for start, end in zip(coords, coords[1:] + coords[:1]):
        length = math.hypot(end[0] - start[0], end[1] - start[1])
        if best is None or length > best[0] + 1e-12:
            best = (length, end[0] - start[0], end[1] - start[1])
    return canonical_direction(best[1], best[2])


class LongestEdgeSwathDirection:
    algorithm_id = "longest_edge"

    def run(self, mains: tuple[PolygonSpec, ...], *, working_width_m: float, problem: CoverageProblem) -> SwathsArtifact:
        ux, uy = longest_edge_direction(polygon_from_spec(mains[0]))
        return swaths_along_direction(mains, ux, uy, working_width_m=working_width_m)
