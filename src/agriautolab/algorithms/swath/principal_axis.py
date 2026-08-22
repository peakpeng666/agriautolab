"""主轴 swath：边界点协方差的最大特征向量方向（PCA 主轴）。"""

import math

import numpy as np

from agriautolab.algorithms.swath._sweep import canonical_direction, swaths_along_direction
from agriautolab.contracts.artifacts import SwathsArtifact
from agriautolab.contracts.geometry import PolygonSpec
from agriautolab.contracts.problem import CoverageProblem
from agriautolab.geometry.validate import polygon_from_spec


def principal_axis(polygon) -> tuple[float, float]:
    """多边形外环顶点的 PCA 主方向。

    协方差矩阵最小特征向量对应「顶点散布最薄」的方向；swath 沿散布最长的
    方向扫（最大特征向量），法向跨度才最小、条数最少。
    """
    coords = np.asarray(polygon.exterior.coords[:-1], dtype=float)
    centered = coords - coords.mean(axis=0)
    covariance = centered.T @ centered / len(coords)
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    principal = eigenvectors[:, int(np.argmax(eigenvalues))]
    return canonical_direction(float(principal[0]), float(principal[1]))


class PrincipalAxisSwath:
    algorithm_id = "principal_axis"

    def run(self, mains: tuple[PolygonSpec, ...], *, working_width_m: float, problem: CoverageProblem) -> SwathsArtifact:
        ux, uy = principal_axis(polygon_from_spec(mains[0]))
        return swaths_along_direction(mains, ux, uy, working_width_m=working_width_m)
