"""构造式启发式的最小公共协议。

构造式求解器只负责四件事：读取当前状态、枚举可行动作、用启发式给动作评分、
执行最优动作。可行性由问题对象定义，启发式不能绕过约束；目标函数也不塞进
启发式协议里，而由各问题的独立 evaluator 复算。

这个边界刻意保持很窄：TSP、CVRP 与农业路线规划可以共享同一构造范式，
但不强迫它们共享状态类型、动作类型或解类型。
"""

from __future__ import annotations

import math
from typing import Protocol, TypeVar

StateT = TypeVar("StateT")
ActionT = TypeVar("ActionT")
SolutionT = TypeVar("SolutionT")


class ConstructiveProblem(Protocol[StateT, ActionT, SolutionT]):
    """能被逐步构造的优化问题。

    `feasible_actions` 是唯一可行动作来源；constructive engine 不接受启发式直接
    返回动作，因此容量、已访问集合等硬约束始终由问题契约掌控。

    `feasible_actions` 还必须返回稳定顺序。公共内核用该顺序处理评分并列，避免要求
    任意 `ActionT` 自身实现比较运算，也避免依赖 set/dict 的偶然遍历顺序。
    """

    def initial_state(self) -> StateT:
        ...

    def is_complete(self, state: StateT) -> bool:
        ...

    def feasible_actions(self, state: StateT) -> tuple[ActionT, ...]:
        ...

    def apply_action(self, state: StateT, action: ActionT) -> StateT:
        ...

    def finalize(self, state: StateT) -> SolutionT:
        ...


class ConstructiveHeuristic(Protocol[StateT, ActionT]):
    """给可行动作打分；分数越小优先级越高。

    启发式只参与排序，不负责检查可行性，也不直接修改状态。这个函数槽位既能承载
    人工规则，也能承载后续由 LLM/EoH 生成的受限候选代码。
    """

    heuristic_id: str

    def score(self, state: StateT, action: ActionT) -> float:
        ...


class ConstructionError(RuntimeError):
    """构造过程或启发式运行违反公共契约。"""


def _finite_score(
    heuristic: ConstructiveHeuristic[StateT, ActionT],
    state: StateT,
    action: ActionT,
) -> float:
    """执行评分并收敛为有限 float；候选异常不能穿透公共 engine 边界。"""
    try:
        raw_value = heuristic.score(state, action)
    except Exception as error:  # noqa: BLE001 -- 插件边界；原异常通过 chaining 保留
        raise ConstructionError(
            f"启发式 {heuristic.heuristic_id!r} 对动作 {action!r} 评分时抛出异常"
        ) from error

    try:
        value = float(raw_value)
    except Exception as error:  # noqa: BLE001 -- 自定义 __float__ 同样属于插件边界
        raise ConstructionError(
            f"启发式 {heuristic.heuristic_id!r} 对动作 {action!r} 返回不可用评分"
        ) from error
    if not math.isfinite(value):
        raise ConstructionError(
            f"启发式 {heuristic.heuristic_id!r} 对动作 {action!r} 返回非有限分数 {value!r}"
        )
    return value


def construct_solution(
    problem: ConstructiveProblem[StateT, ActionT, SolutionT],
    heuristic: ConstructiveHeuristic[StateT, ActionT],
) -> SolutionT:
    """反复选择最低分可行动作直到解完整；评分并列时保留动作枚举顺序。"""
    state = problem.initial_state()
    while not problem.is_complete(state):
        actions = problem.feasible_actions(state)
        if not actions:
            raise ConstructionError("问题尚未完成，但不存在可行动作")

        best_index = -1
        best_score = math.inf
        for index, action in enumerate(actions):
            value = _finite_score(heuristic, state, action)
            if value < best_score:
                best_index = index
                best_score = value

        if best_index < 0:
            raise ConstructionError("可行动作非空，但没有得到可选择动作")
        state = problem.apply_action(state, actions[best_index])
    return problem.finalize(state)
