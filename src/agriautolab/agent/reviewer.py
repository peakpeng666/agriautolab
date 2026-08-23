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

import numpy as np

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


class InvarianceReviewer:
    """维度三：不变性。特征是旋转不变的，候选输出必须同样不变。"""

    def review(self, candidate: ProposalCandidate, function: HeuristicFn) -> ReviewVerdict:
        rng = np.random.default_rng(20260821)
        base = {"elongation": 2.3, "row_angle_vs_principal": 0.6, "turning_ratio": 0.31}
        base_value = function(base)
        for _ in range(32):
            # 特征向量本身在旋转下不变：复核候选不偷看坐标、不依赖未声明的输入
            probe = dict(base)
            probe["area_m2"] = float(rng.uniform(1.0, 1e6))
            probe["obstacle_count"] = float(rng.integers(0, 5))
            value = function(probe)
            if abs(float(value) - float(base_value)) > 1e-12:
                return ReviewVerdict(True, (
                    f"无关特征扰动（area_m2/obstacle_count）改变了输出：{value!r} vs {base_value!r}",
                ))
        return ReviewVerdict(False, ("32 组无关特征扰动下输出不变",))


DEFAULT_REVIEWERS: tuple[AdversarialReviewer, ...] = (
    CorrectnessReviewer(),
    DegenerateCaseReviewer(),
    InvarianceReviewer(),
)


def majority_refuted(verdicts: tuple[ReviewVerdict, ...]) -> bool:
    """多数否决即淘汰。平票（偶数复核器）按否决处理——保守侧。"""
    refuted = sum(1 for verdict in verdicts if verdict.refuted)
    return refuted * 2 >= len(verdicts)


def final_refuted(verdicts: tuple[ReviewVerdict, ...]) -> bool:
    """终判：任何 hard 否决直接淘汰（不被多数翻案），其余按多数。"""
    if any(verdict.refuted and verdict.hard for verdict in verdicts):
        return True
    return majority_refuted(verdicts)
