"""问题 schema 需在构造时拒绝跨任务字段和不安全的坐标系。"""

import pytest
from pydantic import ValidationError

from agriautolab.contracts.geometry import GeometryFrame, Point, PolygonSpec
from agriautolab.contracts.problem import CoverageProblem, GridPointToPointProblem
from agriautolab.contracts.vehicle import VehicleSpec
from agriautolab.geometry.hashing import geometry_hash
from agriautolab.geometry.validate import polygon_from_spec


def rectangle(start_x: float = 0.0) -> PolygonSpec:
    return PolygonSpec(
        geometry_id="field",
        exterior=(
            Point(x=start_x, y=0.0), Point(x=10.0, y=0.0), Point(x=10.0, y=5.0),
            Point(x=start_x, y=5.0), Point(x=start_x, y=0.0),
        ),
    )


def test_coverage_problem_rejects_goal() -> None:
    with pytest.raises(ValidationError):
        CoverageProblem(problem_id="c", field=rectangle(), goal=Point(x=1, y=1))


def test_grid_problem_rejects_field() -> None:
    with pytest.raises(ValidationError):
        GridPointToPointProblem(
            problem_id="g", width=10, height=10, start=Point(x=0, y=0), goal=Point(x=9, y=9), field=rectangle()
        )


@pytest.mark.parametrize("crs", ["EPSG:4326", "EPSG:4269", "EPSG:4258", "EPSG:4490", "WGS84", "CRS84"])
def test_geographic_crs_rejected_with_actionable_message(crs: str) -> None:
    with pytest.raises(ValidationError) as error:
        GeometryFrame(crs=crs)
    message = str(error.value)
    assert "度" in message
    assert "投影" in message


def test_zero_turn_radius_is_expressible_and_flagged_as_turn_in_place() -> None:
    """零半径不再由 schema 拒绝：差速车和履带车本来就能原地转向。

    拒绝的位置搬到了 DubinsPath.run —— 无定义的是 Dubins 曲线，不是这类车。
    见 tests/stages/test_zero_turning_radius.py。
    """
    vehicle = VehicleSpec(working_width_m=6.0, body_width_m=1.2, min_turning_radius_m=0.0, can_reverse=False)
    assert vehicle.can_turn_in_place
    assert not VehicleSpec(
        working_width_m=6.0, body_width_m=1.2, min_turning_radius_m=3.0, can_reverse=False
    ).can_turn_in_place


def test_negative_turn_radius_still_rejected() -> None:
    with pytest.raises(ValidationError):
        VehicleSpec(working_width_m=6.0, body_width_m=1.2, min_turning_radius_m=-0.1, can_reverse=False)


def test_json_roundtrip_is_exact() -> None:
    problem = CoverageProblem(problem_id="c", field=rectangle(), frame=GeometryFrame(crs=None))
    restored = CoverageProblem.model_validate_json(problem.model_dump_json())
    assert restored == problem


def test_canonical_hash_ignores_ring_start_vertex() -> None:
    first = PolygonSpec(
        geometry_id="a",
        exterior=(Point(x=0,y=0), Point(x=10,y=0), Point(x=10,y=5), Point(x=0,y=5), Point(x=0,y=0)),
    )
    second = PolygonSpec(
        geometry_id="b",
        exterior=(Point(x=10,y=0), Point(x=10,y=5), Point(x=0,y=5), Point(x=0,y=0), Point(x=10,y=0)),
    )
    frame = GeometryFrame()
    assert geometry_hash(polygon_from_spec(first), frame) == geometry_hash(polygon_from_spec(second), frame)


def test_canonical_hash_preserves_float_epsilon() -> None:
    first = PolygonSpec(
        geometry_id="a",
        exterior=(Point(x=0,y=0), Point(x=1.0,y=0), Point(x=1,y=1), Point(x=0,y=1), Point(x=0,y=0)),
    )
    second = PolygonSpec(
        geometry_id="b",
        exterior=(Point(x=0,y=0), Point(x=0.9999999999999999,y=0), Point(x=1,y=1), Point(x=0,y=1), Point(x=0,y=0)),
    )
    frame = GeometryFrame()
    assert geometry_hash(polygon_from_spec(first), frame) != geometry_hash(polygon_from_spec(second), frame)
