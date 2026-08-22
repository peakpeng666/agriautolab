"""只暴露算法元数据。推荐与排名逻辑不得进入本包——算法卡片描述能力，不描述优劣。"""

from agriautolab.algorithms.registry import AlgorithmRegistry

__all__ = ["AlgorithmRegistry"]
