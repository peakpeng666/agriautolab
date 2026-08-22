"""均匀地头：委托 Block A 的 ConstantWidthHeadland 做内缩。

全仓库的减地头实现必须只有一份（Block A G-1.4 删掉第二套 parallel path 的教训：
两份内偏置实现会在非凸地块的反曲顶点上分家，round/mitre 相差 0.4%~0.5%）。
分母一律走 resolve_coverage_targets，算法层不再自行减地头。
"""

from agriautolab.contracts.artifacts import CellsArtifact, HeadlandArtifact
from agriautolab.coverage.stages.headland import ConstantWidthHeadland


class UniformHeadland:
    algorithm_id = "uniform_headland"

    def __init__(self, width_m: float) -> None:
        if width_m <= 0.0:
            raise ValueError("地头宽度必须大于 0")
        self.width_m = width_m

    def run(self, cells: CellsArtifact) -> HeadlandArtifact:
        return ConstantWidthHeadland(self.width_m).run(cells)
