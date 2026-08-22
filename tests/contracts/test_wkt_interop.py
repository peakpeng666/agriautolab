"""钉住 WKT 互转，这是接 Fields2Benchmark 350 块真实地块的唯一入口。

数据来源：Zenodo 记录 14524735 的 wkt.zip（211 KB）；Fields2Cover 同样以 WKT 交换。
"""

import pytest

from agriautolab.contracts.errors import GeometryValidationError
from agriautolab.contracts.geometry import GeometryFrame, Point, PolygonSpec
from agriautolab.geometry.hashing import geometry_hash
from agriautolab.geometry.validate import polygon_from_spec


FRAME = GeometryFrame()


def hash_of(spec: PolygonSpec) -> str:
    return geometry_hash(polygon_from_spec(spec), FRAME)


def rectangle(geometry_id: str = "a") -> PolygonSpec:
    return PolygonSpec(
        geometry_id=geometry_id,
        exterior=(
            Point(x=0.0, y=0.0), Point(x=10.0, y=0.0), Point(x=10.0, y=5.0),
            Point(x=0.0, y=5.0), Point(x=0.0, y=0.0),
        ),
    )


def test_wkt_roundtrip_preserves_geometry_hash() -> None:
    original = rectangle()
    assert hash_of(PolygonSpec.from_wkt(original.to_wkt(), geometry_id="a")) == hash_of(original)


def test_wkt_roundtrip_preserves_polygon_with_hole() -> None:
    original = PolygonSpec(
        geometry_id="h",
        exterior=(
            Point(x=0.0, y=0.0), Point(x=10.0, y=0.0), Point(x=10.0, y=10.0),
            Point(x=0.0, y=10.0), Point(x=0.0, y=0.0),
        ),
        holes=((
            Point(x=2.0, y=2.0), Point(x=4.0, y=2.0), Point(x=4.0, y=4.0),
            Point(x=2.0, y=4.0), Point(x=2.0, y=2.0),
        ),),
    )
    assert hash_of(PolygonSpec.from_wkt(original.to_wkt(), geometry_id="h")) == hash_of(original)


def test_to_wkt_is_lossless_at_float_epsilon() -> None:
    """默认 rounding_precision=6 会把这条边磨平，往返哈希就对不上了。"""
    original = PolygonSpec(
        geometry_id="c",
        exterior=(
            Point(x=0.0, y=0.0), Point(x=0.9999999999999999, y=0.0), Point(x=1.0, y=1.0),
            Point(x=0.0, y=1.0), Point(x=0.0, y=0.0),
        ),
    )
    assert "0.9999999999999999" in original.to_wkt()
    assert hash_of(PolygonSpec.from_wkt(original.to_wkt(), geometry_id="c")) == hash_of(original)


def test_normalize_makes_ring_start_vertex_irrelevant() -> None:
    shifted = PolygonSpec(
        geometry_id="b",
        exterior=(
            Point(x=10.0, y=0.0), Point(x=10.0, y=5.0), Point(x=0.0, y=5.0),
            Point(x=0.0, y=0.0), Point(x=10.0, y=0.0),
        ),
    )
    assert shifted.to_wkt() == rectangle().to_wkt()


def test_self_intersecting_wkt_is_rejected_not_repaired() -> None:
    """禁止 make_valid：自交地块必须退回数据准备环节，不能被偷偷改成另一块地。"""
    with pytest.raises(GeometryValidationError):
        PolygonSpec.from_wkt("POLYGON ((0 0, 10 10, 10 0, 0 10, 0 0))", geometry_id="bowtie")


@pytest.mark.parametrize("wkt", [
    "LINESTRING (0 0, 1 1)",
    "POINT (0 0)",
    "POLYGON EMPTY",
    "NOT WKT AT ALL",
    "",
])
def test_non_polygon_and_malformed_wkt_are_rejected(wkt: str) -> None:
    with pytest.raises(GeometryValidationError):
        PolygonSpec.from_wkt(wkt, geometry_id="x")
