"""参数化固定角 swath：方向直接由协议参数给出，覆盖 0 与 90 度两个正交基线。"""

import math

from agriautolab.algorithms.swath._sweep import swaths_along_direction
from agriautolab.contracts.geometry import PolygonSpec
from agriautolab.contracts.artifacts import SwathsArtifact
from agriautolab.contracts.problem import CoverageProblem


class FixedAngleSwath:
    algorithm_id = "fixed_angle"

    def __init__(self, angle_rad: float) -> None:
        self.angle_rad = angle_rad

    def run(self, mains: tuple[PolygonSpec, ...], *, working_width_m: float, problem: CoverageProblem) -> SwathsArtifact:
        return swaths_along_direction(
            mains, math.cos(self.angle_rad), math.sin(self.angle_rad), working_width_m=working_width_m
        )
