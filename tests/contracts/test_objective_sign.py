"""最大化目标必须在 objective 内部翻成最小化代价，优化器一侧不允许出现方向分支。"""

from agriautolab.contracts.artifacts import CellsArtifact
from agriautolab.contracts.enums import CoverageStage, ObjectiveRole
from agriautolab.pipeline.objectives import Artifact, Objective


class MaxObjective(Objective):
    objective_id = "max-test"
    stage = CoverageStage.DECOMPOSITION
    role = ObjectiveRole.SEARCH_OBJECTIVE

    def raw_cost(self, artifact: Artifact) -> float:
        return 3.5

    def is_minimizing(self) -> bool:
        return False


def test_max_objective_sign_flips() -> None:
    assert MaxObjective().cost(CellsArtifact(cells=())) == -3.5
