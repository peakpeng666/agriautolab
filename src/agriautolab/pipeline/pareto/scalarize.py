"""加权切比雪夫标量化：能覆盖整个（含非凸部分的）Pareto 前沿的偏好算子。"""

from __future__ import annotations

from agriautolab.contracts.preference import PreferenceSpec
from agriautolab.contracts.protocol import HypervolumeReference
from agriautolab.pipeline.pareto.front import ObjectiveVector

_DIMENSION_METRIC_IDS = ("path_length", "headland_turn_count", "row_crossings")


def preference_weights(preference: PreferenceSpec) -> tuple[float, float, float]:
    """把偏好向量映射到三维目标权重；未列出的维度取 1.0（均权缺省）。

    声明了不属于主向量的 metric_id 直接拒绝——静默忽略一个权重比报错更糟。
    """
    weights = [1.0, 1.0, 1.0]
    for item in preference.preferences:
        try:
            index = _DIMENSION_METRIC_IDS.index(item.metric_id)
        except ValueError:
            raise ValueError(
                f"{item.metric_id!r} 不是主目标向量的维度（可选：{', '.join(_DIMENSION_METRIC_IDS)}）"
            ) from None
        weights[index] = item.weight
    return (weights[0], weights[1], weights[2])


def scalarize(vector: ObjectiveVector, *, preference: PreferenceSpec, reference: HypervolumeReference) -> float:
    """加权切比雪夫标量化（最小化），归一化用协议参考点。

    用切比雪夫而不是加权和的理由：加权和只能找到 Pareto 前沿**凸包**上的点，
    非凸区域的解永远选不出来；切比雪夫能覆盖整个前沿。
    见 Miettinen, Nonlinear Multiobjective Optimization (1999), Thm 3.4.5。
    归一化必须用协议参考点，不用观测极值——理由同 hypervolume：浮动的尺子
    量不出可比较的偏好次序。
    """
    weights = preference_weights(preference)
    normalized = (
        vector.path_length / reference.path_length,
        vector.headland_turns / reference.headland_turns,
        vector.row_crossings / reference.row_crossings,
    )
    return max(weight * value for weight, value in zip(weights, normalized))
