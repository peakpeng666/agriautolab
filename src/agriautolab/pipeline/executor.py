"""串起五个基线阶段。选择器与 LLM 相关逻辑一律不得进入规划代码路径。"""

from agriautolab.contracts.artifacts import PathArtifact
from agriautolab.contracts.problem import CoverageProblem
from agriautolab.contracts.vehicle import VehicleSpec
from agriautolab.pipeline.coverage_config import CoveragePipelineConfig
from agriautolab.algorithms.stages.decomposition import NoDecomposition
from agriautolab.algorithms.stages.headland import ConstantWidthHeadland
from agriautolab.algorithms.stages.path import DubinsPath
from agriautolab.algorithms.stages.route import SnakeRoute
from agriautolab.algorithms.stages.swath import LongestEdgeSwath


class CoveragePipeline:
    def __init__(self, config: CoveragePipelineConfig = CoveragePipelineConfig()) -> None:
        self.config = config
        expected = {
            "no_decomposition",
            "constant_width_headland",
            "longest_edge_swath",
            "snake_route",
            "dubins_path",
        }
        actual = {
            config.decomposition.algorithm_id,
            config.headland.algorithm_id,
            config.swath.algorithm_id,
            config.route.algorithm_id,
            config.path.algorithm_id,
        }
        if actual != expected:
            raise ValueError("阶段基线只允许第一条竖切的五个算法")

    def run(self, problem: CoverageProblem, robot: VehicleSpec) -> PathArtifact:
        cells = NoDecomposition().run(problem)
        headland = ConstantWidthHeadland(self.config.headland_width_m).run(cells)
        swaths = LongestEdgeSwath().run(headland, working_width_m=robot.working_width_m)
        route = SnakeRoute().run(swaths)
        return DubinsPath(self.config.dubins_sample_step_m).run(route, robot)
