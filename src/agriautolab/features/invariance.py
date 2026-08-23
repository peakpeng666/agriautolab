"""特征的不变性契约：每个特征声明在什么变换下必须不变，由测试用随机变换兑现。

与 MetricSpec 驱动的不变性测试同一纪律：契约是数据，
测试由契约生成，新增特征忘了声明会直接失败。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FeatureInvariance:
    translation_invariant: bool = True
    rotation_invariant: bool = True
    scale_invariant: bool = False


# area_m2 / 计数类不是缩放不变（面积随 lambda^2、计数不随几何缩放的机具联动）；
# row_angle_vs_principal 按定义旋转不变（行方向与主轴一起转）。
FEATURE_INVARIANCE: dict[str, FeatureInvariance] = {
    "area_m2": FeatureInvariance(scale_invariant=False),
    "perimeter_area_ratio": FeatureInvariance(scale_invariant=True),
    "convexity_deficiency": FeatureInvariance(scale_invariant=True),
    "elongation": FeatureInvariance(scale_invariant=True),
    "reflex_vertex_count": FeatureInvariance(scale_invariant=True),
    "obstacle_count": FeatureInvariance(scale_invariant=True),
    "obstacle_area_ratio": FeatureInvariance(scale_invariant=True),
    "row_angle_vs_principal": FeatureInvariance(scale_invariant=True),
    "crossing_density": FeatureInvariance(scale_invariant=True),
    "spacing_to_width_ratio": FeatureInvariance(scale_invariant=True),
    "turning_ratio": FeatureInvariance(scale_invariant=True),
    "swath_count_at_minwidth": FeatureInvariance(scale_invariant=True),
}
