"""行对齐 swath：扫掠方向对齐作物行。

这是唯一用到 CoverageProblem 语义（而不只是几何）的 swath 算法；
problem.row_structure 为 None 时需在入口拒绝——静默退化成别的方向，
会让 row_crossings 目标悄悄变成常数 0，恰是分母漂移那类错误的目标空间版本。
"""

import math

from agriautolab.algorithms.swath._sweep import swaths_along_direction
from agriautolab.contracts.artifacts import SwathsArtifact
from agriautolab.contracts.geometry import PolygonSpec
from agriautolab.contracts.problem import CoverageProblem


class RowAlignedSwathGenerator:
    algorithm_id = "row_aligned"

    def run(self, mains: tuple[PolygonSpec, ...], *, working_width_m: float, problem: CoverageProblem) -> SwathsArtifact:
        row_structure = problem.row_structure
        if row_structure is None:
            raise ValueError("row_aligned 需要 problem.row_structure；没有行结构的地块请显式选择其他 swath 算法")
        return swaths_along_direction(
            mains,
            math.cos(row_structure.direction_rad),
            math.sin(row_structure.direction_rad),
            working_width_m=working_width_m,
        )


# legacy 别名：canonical 类名见 docs/NAMING.md。
RowAlignedSwath = RowAlignedSwathGenerator
