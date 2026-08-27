"""对抗式复核子代理：任务是推翻候选，不是给它背书。

默认输出 refuted=True；只有跑完一组具体探针、每条都给出结果，
才允许 refuted=False——「我认为没问题」不构成复核。

为什么这条复核链有效而「多跑几个模型投票」无效：ICLR 2024 已有结论，
无外部反馈的自我修正会让结果变差。本项目的每一步复核都有外部反馈
（解析真值、回归基线、独立复算的重算结果），reviewer 拿到的探针输出
就是这种反馈——它不是在表达意见，是在读取测量。
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Protocol


from agriautolab.agent.gates import HeuristicFn
from agriautolab.agent.proposer import ProposalCandidate


@dataclass(frozen=True)
class ReviewVerdict:
    refuted: bool
    reasons: tuple[str, ...]
    # hard=True 的否决不可被投票翻案（正确性类检查）；advisory 检查仍走多数。
    hard: bool = False


class AdversarialReviewer(Protocol):
    def review(self, candidate: ProposalCandidate, function: HeuristicFn) -> ReviewVerdict:
        ...


class CorrectnessReviewer:
    """维度一：正确性。探针 = 一组特征向量（正常、全零、缺键、极值）。"""

    PROBES: tuple[dict[str, float], ...] = (
        {"elongation": 1.0, "row_angle_vs_principal": 0.5, "turning_ratio": 0.3},
        {},
        {"elongation": 0.0, "row_angle_vs_principal": 0.0},
        {"elongation": 50.0, "row_angle_vs_principal": math.pi / 2.0, "turning_ratio": 10.0},
    )

    def review(self, candidate: ProposalCandidate, function: HeuristicFn) -> ReviewVerdict:
        for index, probe in enumerate(self.PROBES):
            try:
                value = function(probe)
            except Exception as error:  # noqa: BLE001 -- 探针失败就是反例本身，必须记录而不是上抛
                return ReviewVerdict(True, (f"探针 {index}（{probe}）抛出 {type(error).__name__}: {error}",), hard=True)
            if not isinstance(value, (int, float)) or not math.isfinite(float(value)):
                return ReviewVerdict(True, (f"探针 {index} 返回非有限数：{value!r}",), hard=True)
            if abs(float(value)) > math.pi / 2.0 + 1e-12:
                return ReviewVerdict(True, (f"探针 {index} 越界：{float(value)!r}",), hard=True)
        return ReviewVerdict(False, tuple(
            f"探针 {index} 通过（返回 {function(probe)!r}）" for index, probe in enumerate(self.PROBES)
        ))


class DegenerateCaseReviewer:
    """维度二：退化情形。空特征表、单 swath 地块（特征几乎全零）必须给出有限偏移。

    空前沿 / 单点前沿属于 Pareto 层的退化（evaluate_front 已显式处理），
    这里复核的是候选在退化实例上的行为，两个维度互补。
    """

    def review(self, candidate: ProposalCandidate, function: HeuristicFn) -> ReviewVerdict:
        # 退化一：什么特征都没有（特征提取失败或字段缺失的下游形态）
        try:
            value = function({})
        except Exception as error:  # noqa: BLE001 -- 反例记录
            return ReviewVerdict(True, (f"空特征表抛出 {type(error).__name__}: {error}",))
        if not math.isfinite(float(value)) or abs(float(value)) > math.pi / 2.0 + 1e-12:
            return ReviewVerdict(True, (f"空特征表返回 {value!r}",))
        # 退化二：正方形地块（elongation=1，无冲突），偏移应仍在界内
        value = function({"elongation": 1.0, "obstacle_count": 0.0, "row_angle_vs_principal": 0.0})
        if not math.isfinite(float(value)) or abs(float(value)) > math.pi / 2.0 + 1e-12:
            return ReviewVerdict(True, (f"退化方形地块返回 {value!r}",))
        return ReviewVerdict(False, (
            f"空特征表 -> {float(function({}))!r}（有限且界内）",
            f"方形地块 -> {float(value)!r}（有限且界内）",
        ))


# 不变性复核不在此列：对 area_m2/obstacle_count 的扰动检查与 proposer prompt
# （把这些特征列为可用输入）自相矛盾，会错杀合法的专家启发式；真正的问题对称性
# （几何刚体变换下行为不变）由 gates.invariance_gate 承担。
#
# 这两个 reviewer 内嵌 swath 值域假设（单参 features dict 调用 +
# |v|≤π/2 hard 否决）；新槽位【必须自带 reviewer 集】，不得照抄 SWATH_REVIEWERS。
SWATH_REVIEWERS: tuple[AdversarialReviewer, ...] = (
    CorrectnessReviewer(),
    DegenerateCaseReviewer(),
)
# 兼容别名：单槽位时代的公开名 `DEFAULT_REVIEWERS`。新代码请用 SWATH_REVIEWERS
# 或更明确的 `<slot>_REVIEWERS` 命名。
DEFAULT_REVIEWERS = SWATH_REVIEWERS


class RouteOrderCorrectnessReviewer:
    """route_order 槽位专属复核器：探针 = 典型 (state, candidate) 对。

    与 SWATH_REVIEWERS 的区别：双参调用、(state, candidate) 形态；
    **不设 |v|≤π/2 界**——离散序贯决策的分数无自然标量界。
    hard 否决仅用于「抛异常」与「非有限」两类正确性问题。
    """

    PROBES: tuple[tuple[dict[str, float], dict[str, float]], ...] = (
        ({"visited_count": 0.0, "remaining_count": 4.0}, {"distance_norm": 1.0, "axis_offset_norm": 0.5}),
        ({"visited_count": 1.0, "remaining_count": 3.0}, {"distance_norm": 0.0, "axis_offset_norm": 0.0}),
        ({"visited_count": 3.0, "remaining_count": 1.0}, {"distance_norm": 2.5, "axis_offset_norm": 0.3}),
    )

    def review(self, candidate: ProposalCandidate, function: HeuristicFn) -> ReviewVerdict:
        """逐探针调用一次并**记住返回值**，成功理由由记下的值拼装。

        # Two invariants:

        1. 每个探针传**新副本**——沙箱不禁止候选改写入参，共用常量会让先跑的候选
           把后面的探针掏空，「候选能否通过」于是取决于提议顺序。
        2. 成功理由**不再二次调用候选**。此前 return 里又跑了一遍：一个在第一遍
           成功、第二遍抛 KeyError（例如自己 pop 掉某键）的候选，会在这个
           **无保护**的格式化调用里把异常抛出复核器之外，穿透 evolve_pool
           并在写账本记录之前终止实验。
        """
        values: list[float] = []
        for index, (state_template, action_template) in enumerate(self.PROBES):
            state, action = dict(state_template), dict(action_template)
            try:
                value = function(state, action)
                coerced = float(value)
            except Exception as error:  # noqa: BLE001 -- 探针失败是反例本身
                return ReviewVerdict(
                    True, (f"探针 {index} 抛出 {type(error).__name__}: {error}",), hard=True,
                )
            if not isinstance(value, (int, float)) or not math.isfinite(coerced):
                return ReviewVerdict(
                    True, (f"探针 {index} 返回非有限数：{value!r}",), hard=True,
                )
            values.append(coerced)
        return ReviewVerdict(False, tuple(
            f"探针 {index} 通过（返回 {value!r}）" for index, value in enumerate(values)
        ))


# route_order 槽位专属复核器集：不复用 SWATH_REVIEWERS（其内嵌 |v|≤π/2 界
# 不适用于双参 (state, candidate) 评分；硬要复用会在所有离散评分上误杀）。
ROUTE_REVIEWERS: tuple[AdversarialReviewer, ...] = (RouteOrderCorrectnessReviewer(),)


def majority_refuted(verdicts: tuple[ReviewVerdict, ...]) -> bool:
    """多数否决即淘汰。平票（偶数复核器）按否决处理——保守侧。"""
    refuted = sum(1 for verdict in verdicts if verdict.refuted)
    return refuted * 2 >= len(verdicts)


def final_refuted(verdicts: tuple[ReviewVerdict, ...]) -> bool:
    """终判：任何 hard 否决直接淘汰（不被多数翻案），其余按多数。"""
    if any(verdict.refuted and verdict.hard for verdict in verdicts):
        return True
    return majority_refuted(verdicts)
