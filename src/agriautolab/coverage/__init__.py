"""只暴露五阶段覆盖流水线。benchmark runner 与推荐逻辑禁止进入本包。"""

from agriautolab.coverage.pipeline import CoveragePipeline

__all__ = ["CoveragePipeline"]
