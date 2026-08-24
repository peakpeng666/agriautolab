"""组合优化公共内核。

这一层只定义与具体领域无关的构造式求解协议：问题状态、可行动作、
启发式评分与确定性构造循环。农业覆盖规划仍保留自己的强类型五阶段流水线；
TSP/CVRP 作为标准组合优化问题复用这里的协议，用于经典启发式与后续 LLM
自动算法设计的共同基线。
"""

from agriautolab.optimization.constructive import (
    ConstructiveHeuristic,
    ConstructiveProblem,
    construct_solution,
)

__all__ = [
    "ConstructiveHeuristic",
    "ConstructiveProblem",
    "construct_solution",
]
