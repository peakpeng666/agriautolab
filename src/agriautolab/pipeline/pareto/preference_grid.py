"""PREFERENCE_GRID_V1：偏好条件评估的冻结偏好网格（修正案 05 封口件）。

口头描述（"均匀撒 N 个点"）不可复现——网格的全部坐标逐项列在这里并
写入 evidence/preference_grid_v1.json，哈希进分析协议。构造规则：

- 3 个顶点：单维权重 1，其余 0（极端偏好）；
- 9 个棱点：每条棱取 t ∈ {1/4, 1/2, 3/4}；
- 10 个内部点：严格内部整数格点 {(i, j, k)/6 : i,j,k ≥ 1, i+j+k = 6}。

共 22 个，顺序即下述枚举顺序（顶点 → 棱按维对序 → 内部按字典序）。
任何改动 = 换网格 = 换协议，必须升版本号 V2 并重新封存。
"""

from __future__ import annotations

import hashlib
import json

from agriautolab.contracts.preference import MetricPreference, PreferenceSpec

_DIMENSION_METRIC_IDS = ("path_length", "headland_turn_count", "row_crossings")

_VERTICES: tuple[tuple[float, float, float], ...] = (
    (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0),
)
_EDGES: tuple[tuple[float, float, float], ...] = tuple(
    point
    for i, j in ((0, 1), (0, 2), (1, 2))
    for t in (0.25, 0.5, 0.75)
    for point in [tuple(
        t if axis == i else (1.0 - t if axis == j else 0.0) for axis in range(3)
    )]
)
_INTERIOR: tuple[tuple[float, float, float], ...] = tuple(
    (i / 6.0, j / 6.0, k / 6.0)
    for i in range(1, 6) for j in range(1, 6) for k in range(1, 6)
    if i + j + k == 6
)

PREFERENCE_GRID_V1: tuple[tuple[float, float, float], ...] = (
    _VERTICES + _EDGES + _INTERIOR
)
assert len(PREFERENCE_GRID_V1) == 22


def preference_grid_hash(grid: tuple[tuple[float, float, float], ...] = PREFERENCE_GRID_V1) -> str:
    """规范序坐标数组的 sha256；evidence JSON 以同一字节重算对账。"""
    payload = json.dumps([list(map(float, w)) for w in grid], separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def grid_to_preference_spec(w: tuple[float, float, float]) -> PreferenceSpec:
    """网格点 → PreferenceSpec：三维全部显式声明（零权重必须显式，不靠缺省）。"""
    return PreferenceSpec(preferences=tuple(
        MetricPreference(metric_id=metric_id, weight=weight)
        for metric_id, weight in zip(_DIMENSION_METRIC_IDS, w)
    ))
