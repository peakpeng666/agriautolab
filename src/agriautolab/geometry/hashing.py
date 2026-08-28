"""对已校验几何按规范坐标序做哈希，不降精度。

陷阱：写 WKB 前需 normalize，否则同一块地换个起始顶点就是另一个哈希；
但不能顺手做精度削减，那会让 1.0 与 0.9999999999999999 撞成同一块地。
"""

from __future__ import annotations

import hashlib

import shapely
from shapely.geometry.base import BaseGeometry

from agriautolab.contracts.geometry import GeometryFrame
from agriautolab.geometry.validate import validate_geometry


def geometry_hash(geometry: BaseGeometry, frame: GeometryFrame) -> str:
    validate_geometry(geometry)
    normalized = shapely.normalize(geometry)
    wkb = shapely.to_wkb(normalized, output_dimension=2, byte_order=1)
    frame_bytes = (
        f"crs={frame.crs!r};x={frame.x_axis};y={frame.y_axis};unit={frame.unit};".encode("utf-8")
    )
    return hashlib.sha256(frame_bytes + wkb).hexdigest()
