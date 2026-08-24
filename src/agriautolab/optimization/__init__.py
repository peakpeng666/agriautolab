"""组合优化公共内核。

这里定义与具体领域无关的构造式求解协议：问题状态、可行动作、启发式评分与确定性
构造循环。农业覆盖规划继续保留自己的强类型五阶段流水线；TSP/CVRP 作为标准组合
优化问题复用这一协议，为经典启发式与后续 LLM 自动算法设计提供共同方法学基线。
"""

from agriautolab.optimization.constructive import (
    ConstructionError,
    ConstructiveHeuristic,
    ConstructiveProblem,
    construct_solution,
)

__all__ = [
    "ConstructionError",
    "ConstructiveHeuristic",
    "ConstructiveProblem",
    "construct_solution",
]
