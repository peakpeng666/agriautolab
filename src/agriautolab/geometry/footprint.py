"""机具扫掠按矩形带计算，不是端部带圆帽的胶囊。"""

from __future__ import annotations

from shapely.geometry.base import BaseGeometry

from agriautolab.geometry.robust import robust_union

QUAD_SEGS = 16


def sweep_piece(line: BaseGeometry, width_m: float) -> BaseGeometry:
    if width_m <= 0.0:
        raise ValueError("working width must be greater than 0")
    # 端部需 flat cap：机具沿作业线扫掠的是矩形，round cap 会按分段数虚增面积。
    return line.buffer(
        width_m / 2.0,
        cap_style="flat",
        join_style="round",
        quad_segs=QUAD_SEGS,
    )


def sweep_union(lines: tuple[BaseGeometry, ...], width_m: float, *, scale_hint: float) -> BaseGeometry:
    pieces = tuple(sweep_piece(line, width_m) for line in lines)
    return robust_union(pieces, scale_hint=scale_hint)
