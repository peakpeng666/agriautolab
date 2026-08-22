"""按给定方向生成 swath 中心线的公共扫掠逻辑。

五个 swath 算法只在「方向怎么选」上不同，扫掠本身必须同一份实现——
两份扫掠代码会像两份地头代码一样，在某个非凸地块上分家。
中心线取与主田的交线；条数 = ceil(法向跨度 / 幅宽)，首条贴边、末条回收，
这些都是 Block A MBRDirectionSwath 已被 309 条测试约束住的语义。

入口收主田多边形序列（PolygonSpec）而不是 HeadlandArtifact：
no_headland 管线没有地头产物，恒等地头的规范表示就是「主田 = 原 cell」
（见 algorithms/headland/no_headland.py），扫掠不应强迫调用方伪造一个产物。
"""

from __future__ import annotations

import math

from shapely import LineString

from agriautolab.contracts.artifacts import Swath, SwathsArtifact
from agriautolab.contracts.geometry import PolygonSpec
from agriautolab.geometry.validate import line_to_spec, polygon_from_spec


def _line_parts(geometry):
    if geometry.is_empty:
        return ()
    if geometry.geom_type == "LineString":
        return (geometry,)
    if geometry.geom_type == "MultiLineString":
        return tuple(geometry.geoms)
    if geometry.geom_type == "GeometryCollection":
        return tuple(part for part in geometry.geoms if part.geom_type == "LineString")
    return ()


def canonical_direction(ux: float, uy: float) -> tuple[float, float]:
    """方向规范化到右半平面（ux>0，或 ux==0 且 uy>0），消除 180 度歧义。"""
    norm = math.hypot(ux, uy)
    if norm == 0.0:
        raise ValueError("swath 方向不能是零向量")
    ux, uy = ux / norm, uy / norm
    if ux < 0.0 or (ux == 0.0 and uy < 0.0):
        ux, uy = -ux, -uy
    return ux, uy


def swaths_along_direction(mains: tuple[PolygonSpec, ...], ux: float, uy: float, *, working_width_m: float) -> SwathsArtifact:
    if working_width_m <= 0.0:
        raise ValueError("幅宽必须大于 0")
    ux, uy = canonical_direction(ux, uy)
    nx, ny = -uy, ux
    output: list[Swath] = []
    serial = 0
    for main_spec in mains:
        main = polygon_from_spec(main_spec)
        coords = list(main.exterior.coords)
        u_values = [x * ux + y * uy for x, y in coords]
        n_values = [x * nx + y * ny for x, y in coords]
        u_min, u_max = min(u_values), max(u_values)
        n_min, n_max = min(n_values), max(n_values)
        span = n_max - n_min
        count = max(1, math.ceil(span / working_width_m))
        if count == 1:
            centers = [(n_min + n_max) / 2.0]
        else:
            centers = [n_min + working_width_m / 2.0 + index * working_width_m for index in range(count)]
            centers[-1] = min(centers[-1], n_max - working_width_m / 2.0)
        extension = max(working_width_m, u_max - u_min, 1.0)
        for center in centers:
            start = ((u_min - extension) * ux + center * nx, (u_min - extension) * uy + center * ny)
            end = ((u_max + extension) * ux + center * nx, (u_max + extension) * uy + center * ny)
            intersection = main.intersection(LineString([start, end]))
            parts = sorted(
                _line_parts(intersection),
                key=lambda line: (
                    line.centroid.x * nx + line.centroid.y * ny,
                    min(point[0] * ux + point[1] * uy for point in line.coords),
                ),
            )
            for part in parts:
                coords_part = list(part.coords)
                if coords_part[0][0] * ux + coords_part[0][1] * uy > coords_part[-1][0] * ux + coords_part[-1][1] * uy:
                    part = LineString(list(reversed(coords_part)))
                swath_id = f"swath-{serial:04d}"
                output.append(Swath(swath_id=swath_id, centerline=line_to_spec(part, swath_id), width_m=working_width_m))
                serial += 1
    return SwathsArtifact(swaths=tuple(output))
