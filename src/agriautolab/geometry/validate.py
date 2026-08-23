"""非法几何在计算前直接拒绝，不做静默拓扑修复。

陷阱：这里绝不能出现 make_valid。被偷偷修好的地块会让后续所有面积指标
建立在一块没人见过的多边形上，而且从结果里看不出来。
"""

from __future__ import annotations

import math

from shapely import LineString, Polygon
from shapely.geometry.base import BaseGeometry

from agriautolab.contracts.errors import GeometryValidationError
from agriautolab.contracts.geometry import LineStringSpec, Point, PolygonSpec


def polygon_from_spec(spec: PolygonSpec) -> Polygon:
    polygon = Polygon(
        [point.as_tuple() for point in spec.exterior],
        [[point.as_tuple() for point in ring] for ring in spec.holes],
    )
    validate_geometry(polygon, geometry_id=spec.geometry_id)
    return polygon


def line_from_spec(spec: LineStringSpec) -> LineString:
    line = LineString([point.as_tuple() for point in spec.points])
    validate_geometry(line, geometry_id=spec.geometry_id)
    if line.length == 0.0:
        raise GeometryValidationError(f"{spec.geometry_id}: 线长度必须大于 0")
    return line


def point_tuple(point: Point) -> tuple[float, float]:
    return point.as_tuple()


def validate_geometry(geometry: BaseGeometry, *, geometry_id: str = "geometry") -> None:
    if geometry.is_empty:
        raise GeometryValidationError(f"{geometry_id}: 几何不能为空")
    bounds = geometry.bounds
    if not all(math.isfinite(value) for value in bounds):
        raise GeometryValidationError(f"{geometry_id}: 几何包含 NaN 或无穷坐标")
    if not geometry.is_valid:
        raise GeometryValidationError(f"{geometry_id}: 几何非法或自交")


def validate_obstacles_within_field(field: Polygon, obstacles: tuple[tuple[str, Polygon], ...]) -> None:
    for obstacle_id, obstacle in obstacles:
        if not field.covers(obstacle):
            raise GeometryValidationError(f"{obstacle_id}: 障碍物越出 field 边界")


def polygon_to_spec(geometry: BaseGeometry, geometry_id: str) -> PolygonSpec:
    if geometry.geom_type != "Polygon":
        raise GeometryValidationError(f"{geometry_id}: 当前基线要求单 Polygon，得到 {geometry.geom_type}")
    polygon = geometry
    exterior = tuple(Point(x=float(x), y=float(y)) for x, y in polygon.exterior.coords)
    holes = tuple(
        tuple(Point(x=float(x), y=float(y)) for x, y in ring.coords)
        for ring in polygon.interiors
    )
    return PolygonSpec(geometry_id=geometry_id, exterior=exterior, holes=holes)


def polygon_parts_to_specs(geometry: BaseGeometry, geometry_id: str) -> tuple[PolygonSpec, ...]:
    """把 Polygon 或 MultiPolygon 拆成有序的 PolygonSpec 元组。

    存在的理由：含障碍地块的地头环带常是 MultiPolygon（外圈 + 每个障碍周围一圈），
    主田也可能被障碍夹断成多片（真实对账集 14 块中前者 6 块、后者 1 块）。
    此前 polygon_to_spec 直接抛「当前基线要求单 Polygon」，于是含障碍地块根本跑不完 ——
    而 RMA 那条关于障碍的裁决恰恰需要这些地块才能验。

    排序按 (面积降序, WKB 十六进制) —— 面积给人看，WKB 破平保证确定性：
    GEOS 的 MultiPolygon 成员顺序不在契约里，直接用它会让同一块地两次跑出不同 spec 顺序。
    """
    if geometry.is_empty:
        raise GeometryValidationError(f"{geometry_id}: 几何不能为空")
    if geometry.geom_type == "Polygon":
        parts = (geometry,)
    elif geometry.geom_type == "MultiPolygon":
        parts = tuple(sorted(geometry.geoms, key=lambda part: (-part.area, part.wkb_hex)))
    else:
        raise GeometryValidationError(
            f"{geometry_id}: 需要 Polygon 或 MultiPolygon，得到 {geometry.geom_type}"
        )
    return tuple(
        polygon_to_spec(part, f"{geometry_id}#{index}" if len(parts) > 1 else geometry_id)
        for index, part in enumerate(parts)
    )


def line_to_spec(geometry: BaseGeometry, geometry_id: str) -> LineStringSpec:
    if geometry.geom_type != "LineString":
        raise GeometryValidationError(f"{geometry_id}: 当前基线要求 LineString，得到 {geometry.geom_type}")
    return LineStringSpec(
        geometry_id=geometry_id,
        points=tuple(Point(x=float(x), y=float(y)) for x, y in geometry.coords),
    )
