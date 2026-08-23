"""Dubins 转移 path 阶段：委托 coverage 阶段基线的 DubinsPath 采样实现。

长度与转移代价的解析来源是 kinematics/dubins.py（六字闭式解 + 正演闭合测试），
路径采样沿用被既有测试约束的基线实现——采样器只有一份，
就像减地头只有一份。
"""

from agriautolab.contracts.artifacts import PathArtifact, RouteArtifact
from agriautolab.contracts.vehicle import VehicleSpec
from agriautolab.coverage.stages.path import DubinsPath


class DubinsPathPlanner:
    algorithm_id = "dubins_transit"

    def __init__(self, sample_step_m: float = 0.25) -> None:
        if sample_step_m <= 0.0:
            raise ValueError("采样步长必须大于 0")
        self.sample_step_m = sample_step_m

    def run(self, route: RouteArtifact, robot: VehicleSpec) -> PathArtifact:
        return DubinsPath(self.sample_step_m).run(route, robot)


# legacy 别名：canonical 类名见 docs/NAMING.md。
DubinsTransit = DubinsPathPlanner
