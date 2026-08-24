"""构造式启发式的最小公共协议。

构造式求解器只负责四件事：读取当前状态、枚举可行动作、用启发式给动作评分、
执行最优动作。可行性由问题对象定义，启发式不能绕过约束；目标函数也不塞进
启发式协议里，而由各问题的独立 evaluator 复算。

这个边界刻意保持很窄：TSP、CVRP 与农业路线规划可以共享同一构造范式，
但不强迫它们共享状态类型、动作类型或解类型。
"""

from __future__ import annotations

from typing import Generic, Protocol, TypeVar

StateT = TypeVar("StateT")
ActionT = TypeVar("ActionT")
SolutionT = TypeVar("SolutionT")


class ConstructiveProblem(Protocol[StateT, ActionT, SolutionT]):
    """能被逐步构造的优化问题。

    `feasible_actions` 是唯一可行动作来源；constructive engine 不接受启发式直接
    返回动作，因此容量、已访问集合等硬约束始终由问题契约掌控。
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
    """构造过程与问题契约发生矛盾。"""


def construct_solution(
    problem: ConstructiveProblem[StateT, ActionT, SolutionT],
    heuristic: ConstructiveHeuristic[StateT, ActionT],
) -> SolutionT:
    """按 `(score, action)` 的稳定顺序重复选择最优可行动作直到完成。

    动作必须可排序，这使同分候选有确定性 tie-break。若某问题的动作天然不可排序，
    应在领域层包装成带稳定身份的动作，而不是让公共内核偷偷依赖容器遍历顺序。
    """
    state = problem.initial_state()
    while not problem.is_complete(state):
        actions = problem.feasible_actions(state)
        if not actions:
            raise ConstructionError("问题尚未完成，但不存在可行动作")
        scored = []
        for action in actions:
            value = float(heuristic.score(state, action))
            if value != value or value in (float("inf"), float("-inf")):
                raise ConstructionError(
                    f"启发式 {heuristic.heuristic_id!r} 对动作 {action!r} 返回非有限分数 {value!r}"
                )
            scored.append((value, action))
        _, selected = min(scored)
        state = problem.apply_action(state, selected)
    return problem.finalize(state)
