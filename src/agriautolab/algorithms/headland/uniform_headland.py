"""均匀地头：委托 coverage 阶段基线的 ConstantWidthHeadland 做内缩。

全仓库的减地头实现必须只有一份（曾删掉第二套 parallel path 实现的教训：
两份内偏置实现会在非凸地块的反曲顶点上分家，round/mitre 相差 0.4%~0.5%）。
分母一律走 resolve_coverage_targets，算法层不再自行减地头。
"""

from agriautolab.contracts.artifacts import CellsArtifact, HeadlandArtifact
from agriautolab.algorithms.stages import headland as _headland_stage


class ConstantWidthHeadland:
    algorithm_id = "uniform_headland"

    def __init__(self, width_m: float) -> None:
        if width_m <= 0.0:
            raise ValueError("地头宽度必须大于 0")
        self.width_m = width_m

    def run(self, cells: CellsArtifact) -> HeadlandArtifact:
        return _headland_stage.ConstantWidthHeadland(self.width_m).run(cells)


# legacy 别名：canonical 类名见 docs/NAMING.md。
UniformHeadland = ConstantWidthHeadland
