"""不切分的分解基线：唯一的 cell 就是原始地块，用作其余分解算法的对照组。"""

from agriautolab.contracts.artifacts import CellsArtifact
from agriautolab.contracts.problem import CoverageProblem


class NoDecomposition:
    algorithm_id = "no_decomposition"

    def run(self, problem: CoverageProblem) -> CellsArtifact:
        return CellsArtifact(cells=(problem.field,))
