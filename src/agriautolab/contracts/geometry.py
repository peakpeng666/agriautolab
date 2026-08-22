"""几何以不可变契约类型跨模块传递。Shapely 对象可变，泄漏出去就没法保证同一份输入两次算出同一结果。"""

from __future__ import annotations

import math
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator


_GEOGRAPHIC_CRS = {
    "EPSG:4326",
    "EPSG:4269",
    "EPSG:4258",
    "EPSG:4490",
    "WGS84",
    "CRS84",
}


class Point(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    x: float
    y: float

    @field_validator("x", "y")
    @classmethod
    def finite_coordinate(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("坐标必须是有限数")
        return value

    def as_tuple(self) -> tuple[float, float]:
        return (self.x, self.y)


class Pose2D(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    x: float
    y: float
    yaw_rad: float

    @field_validator("x", "y", "yaw_rad")
    @classmethod
    def finite_value(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("位姿必须由有限数构成")
        return value

    def point(self) -> Point:
        return Point(x=self.x, y=self.y)


class PolygonSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    geometry_id: str = Field(min_length=1)
    exterior: tuple[Point, ...]
    holes: tuple[tuple[Point, ...], ...] = ()

    @field_validator("exterior")
    @classmethod
    def enough_exterior_vertices(cls, ring: tuple[Point, ...]) -> tuple[Point, ...]:
        if len(ring) < 4:
            raise ValueError("多边形外环至少需要 4 个点（含闭合点）")
        return ring

    @classmethod
    def from_wkt(cls, wkt: str, *, geometry_id: str) -> "PolygonSpec":
        """从 WKT 构造。先经 validate_geometry 校验，不做任何自动修复。

        存在的理由：Fields2Benchmark 的 350 块真实地块（Zenodo 14524735，wkt.zip 211 KB）
        和 Fields2Cover 都以 WKT 交换，而本仓库的 PolygonSpec 用点列。

        陷阱：这里绝不能调 make_valid。自交地块必须报错退回给数据准备环节，
        偷偷修好的拓扑会让后续所有面积指标建立在一块没人见过的多边形上。
        """
        import shapely
        from shapely.errors import ShapelyError

        # 延迟导入：geometry.validate 依赖本模块，模块级导入会成环。
        from agriautolab.contracts.errors import GeometryValidationError
        from agriautolab.geometry.validate import polygon_to_spec, validate_geometry

        try:
            geometry = shapely.from_wkt(wkt)
        except (ShapelyError, TypeError) as error:
            raise GeometryValidationError(f"{geometry_id}: WKT 无法解析") from error
        if geometry is None:
            raise GeometryValidationError(f"{geometry_id}: WKT 解析结果为空")
        validate_geometry(geometry, geometry_id=geometry_id)
        return polygon_to_spec(geometry, geometry_id)

    def to_wkt(self) -> str:
        """导出 WKT。经 shapely.normalize 规范化，保证同一几何得到同一字符串。

        陷阱：必须显式传 rounding_precision=-1。shapely 默认按 6 位小数四舍五入，
        那会让 to_wkt 变成有损操作，往返后 geometry_hash 对不上。
        """
        import shapely

        from agriautolab.geometry.validate import polygon_from_spec

        normalized = shapely.normalize(polygon_from_spec(self))
        return shapely.to_wkt(normalized, rounding_precision=-1, trim=True, output_dimension=2)


class LineStringSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    geometry_id: str = Field(min_length=1)
    points: tuple[Point, ...]

    @field_validator("points")
    @classmethod
    def enough_points(cls, points: tuple[Point, ...]) -> tuple[Point, ...]:
        if len(points) < 2:
            raise ValueError("线至少需要两个点")
        return points

    def reversed(self) -> Self:
        return self.model_copy(update={"points": tuple(reversed(self.points))})


class GeometryFrame(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    crs: str | None = None
    x_axis: str = "east"
    y_axis: str = "north"
    unit: str = "m"

    @field_validator("crs")
    @classmethod
    def reject_geographic_crs(cls, crs: str | None) -> str | None:
        if crs is not None and crs.upper() in _GEOGRAPHIC_CRS:
            raise ValueError("该 CRS 的单位是度，长度和面积会随纬度产生不同误差；请先投影到米制坐标系")
        return crs

    @field_validator("unit")
    @classmethod
    def require_meters(cls, unit: str) -> str:
        if unit != "m":
            raise ValueError("Block A 只接受米制局部或投影坐标")
        return unit
