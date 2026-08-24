"""算法实现包；顶层命名空间只暴露元数据注册表，具体算法从子模块显式导入。"""

from agriautolab.algorithms.registry import AlgorithmRegistry

__all__ = ["AlgorithmRegistry"]
