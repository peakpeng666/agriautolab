"""最小宽度 swath：扫描角使地块在 swath 法向上的跨度最小，等价于最小化作业段条数。

旋转卡壳定理的多边形版本：多边形（及其凸包）的最小宽度必在凸包某条边的方向上取得，
因此只需枚举凸包边方向，不必连续搜索。这一条同时是特征
swath_count_at_minwidth 的定义来源。
"""

import math

from agriautolab.algorithms.swath._sweep import canonical_direction, swaths_along_direction
from agriautolab.contracts.artifacts import SwathsArtifact
from agriautolab.contracts.geometry import PolygonSpec
from agriautolab.contracts.problem import CoverageProblem
from agriautolab.geometry.validate import polygon_from_spec


def min_width_direction(polygon) -> tuple[float, float]:
    """返回使法向跨度最小的扫掠方向（沿该方向扫，条数最少）。"""
    hull = polygon.convex_hull
    coords = list(hull.exterior.coords)
    ux, uy = 1.0, 0.0
    best_span = math.inf
    for start, end in zip(coords, coords[1:] + coords[:1]):
        dx, dy = end[0] - start[0], end[1] - start[1]
        length = math.hypot(dx, dy)
        if length == 0.0:
            continue
        candidate_ux, candidate_uy = canonical_direction(dx / length, dy / length)
        nx, ny = -candidate_uy, candidate_ux
        span = max(x * nx + y * ny for x, y in coords) - min(x * nx + y * ny for x, y in coords)
        if span < best_span - 1e-12:
            best_span = span
            ux, uy = candidate_ux, candidate_uy
    return ux, uy


def swath_count_at_direction(polygon, ux: float, uy: float, working_width_m: float) -> int:
    """给定方向下的作业段条数（条数 = ceil(法向跨度 / 幅宽)，与 _sweep 一致）。"""
    nx, ny = -uy, ux
    coords = list(polygon.exterior.coords)
    span = max(x * nx + y * ny for x, y in coords) - min(x * nx + y * ny for x, y in coords)
    return max(1, math.ceil(span / working_width_m))


class MinimumWidthSwathGenerator:
    algorithm_id = "min_width"

    def run(self, mains: tuple[PolygonSpec, ...], *, working_width_m: float, problem: CoverageProblem) -> SwathsArtifact:
        ux, uy = min_width_direction(polygon_from_spec(mains[0]))
        return swaths_along_direction(mains, ux, uy, working_width_m=working_width_m)


# legacy 别名：canonical 类名见 docs/NAMING.md。
MinWidthSwath = MinimumWidthSwathGenerator
