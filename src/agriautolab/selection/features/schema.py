"""实例特征的规范名词汇表（docs/NAMING.md 的特征部分）。

wire ID（特征键、parquet 的 feature__* 列名、预注册 H2 引用的
row_angle_vs_principal）是证据身份，永不改；规范名只用于 API 与
论文叙事。L4（选择层）一律通过本表取规范名。
"""

from __future__ import annotations

# wire ID -> 规范名；未列出的特征两者同名。
FEATURE_CANONICAL_NAMES: dict[str, str] = {
    "perimeter_area_ratio": "perimeter_sqrt_area_ratio",
    "crossing_density": "field_scale_to_row_spacing_ratio",
    "spacing_to_width_ratio": "row_spacing_to_working_width_ratio",
    "turning_ratio": "turning_radius_to_working_width_ratio",
    "row_angle_vs_principal": "crop_row_angle_to_principal_axis_rad",
}


def canonical_feature_name(wire_id: str) -> str:
    return FEATURE_CANONICAL_NAMES.get(wire_id, wire_id)
