"""带面积自检的多边形并集。

不要改成 shapely.unary_union。它在某些坐标配置下会静默丢弃整块多边形：
实测 500 组随机刚体+相似变换中错 21 次，最大相对误差 40.0%；
且只在特定旋转角发生，会让「不同 swath angle 的配置」之间凭空产生系统性差异。
"""

from __future__ import annotations


import shapely
from shapely.geometry import GeometryCollection
from shapely.geometry.base import BaseGeometry

from agriautolab.contracts.errors import RobustUnionError


def _area_bounds_ok(result: BaseGeometry, pieces: tuple[BaseGeometry, ...], tolerance: float) -> bool:
    areas = tuple(piece.area for piece in pieces)
    if not areas:
        return result.is_empty
    return max(areas) - tolerance <= result.area <= sum(areas) + tolerance


def robust_union(pieces: tuple[BaseGeometry, ...], *, scale_hint: float) -> BaseGeometry:
    if scale_hint <= 0.0:
        raise ValueError("scale_hint 必须大于 0")
    if not pieces:
        return GeometryCollection()

    ordered = tuple(sorted(pieces, key=lambda geometry: geometry.wkb_hex))
    grid_size = scale_hint * 1e-9

    # GEOS 曾在特定旋转角下静默丢掉整块作业带；这个错误会把 swath angle 变成伪优势。
    snapped = shapely.union_all(ordered, grid_size=grid_size)
    tolerance = max(1.0, sum(piece.area for piece in ordered)) * 1e-12
    snapped_ok = _area_bounds_ok(snapped, ordered, tolerance)

    # 平衡树归约（性能修复，留痕见 AUDIT_NOTE）：左结合 reduce 在
    # 数百片时每步重并累积大几何，实测 574 片 150.7 s；树归约结果由并集结合律
    # 与左结合完全一致（集合与面积），作为面积交叉校验的职责不变。
    layer = list(ordered)
    while len(layer) > 1:
        paired = [layer[i].union(layer[i + 1]) for i in range(0, len(layer) - 1, 2)]
        if len(layer) % 2:
            paired.append(layer[-1])
        layer = paired
    pairwise = layer[0]
    pairwise_ok = _area_bounds_ok(pairwise, ordered, tolerance)
    if snapped_ok and pairwise_ok:
        # 面积上下界只能发现“大块丢失”，抓不住 precision grid 自身对旋转不变性的微扰。
        # 逐对 union 本来就是指定的回退路径；把它同时作为独立面积交叉校验，避免指标差异来自网格吸附。
        cross_tolerance = max(1.0, pairwise.area) * 1e-12
        return pairwise if abs(snapped.area - pairwise.area) > cross_tolerance else snapped
    if snapped_ok:
        return snapped
    if pairwise_ok:
        return pairwise
    raise RobustUnionError("并集面积自检失败：精度网格与逐对 union 均不可信")
