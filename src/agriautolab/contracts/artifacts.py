"""每个阶段产物用各自的类型承载，防止上游把 swath 当 cell 传下去还能跑通。"""

from pydantic import BaseModel, ConfigDict, Field

from agriautolab.contracts.enums import PathSegmentKind, SwathDirection
from agriautolab.contracts.geometry import LineStringSpec, PolygonSpec


class CellsArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    cells: tuple[PolygonSpec, ...]


class HeadlandCell(BaseModel):
    """一个 cell 的地头切分结果。两个域都是**多部件**的。

    为什么是元组而不是单个 PolygonSpec：真实含障碍地块上，
    14 块里 6 块的地头环带是 MultiPolygon（外圈 + 每个障碍周围一圈），
    部分地块主田被障碍夹断成两片。单 Polygon 契约让这些地块直接抛错，
    而关于障碍的 RMA 裁决恰恰只能在这些地块上验。
    """

    model_config = ConfigDict(extra="forbid", frozen=True)
    cell_id: str
    main_field: tuple[PolygonSpec, ...] = Field(min_length=1)
    headland: tuple[PolygonSpec, ...] = Field(min_length=1)


class HeadlandArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    cells: tuple[HeadlandCell, ...]


class Swath(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    swath_id: str
    centerline: LineStringSpec
    width_m: float = Field(gt=0.0)


class SwathsArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    swaths: tuple[Swath, ...]


class SwathTraversal(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    swath_id: str
    direction: SwathDirection


class RouteArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    traversals: tuple[SwathTraversal, ...]
    swaths: tuple[Swath, ...]


class PathSegment(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    segment_id: str
    kind: PathSegmentKind
    line: LineStringSpec
    signed_curvature_m_inv: float = 0.0
    # True = 倒车行驶该段（Reeds-Shepp 带来的自由度）。几何与曲率不受影响；
    # 校验器用它拒绝不可倒车机具的路径。默认 False 保持前向-only 语义不变。
    reversing: bool = False


class PathArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    segments: tuple[PathSegment, ...]
