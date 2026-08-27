"""零转弯半径必须能表达，而且必须在 Dubins 阶段入口被挡住。

Dubins 曲线在 R=0 处无定义：归一化距离 d = distance / R 与曲率 1/R 同时发散。
以前靠 schema 的 gt=0 顺手挡住，代价是差速车和履带车根本进不了系统。
"""

import math

import pytest

from conftest import HYPERVOLUME_TEST_REFERENCE, REVERSE_COST_TEST_SPEC
from agriautolab.contracts.artifacts import PathArtifact, PathSegment, Swath, SwathsArtifact
from agriautolab.contracts.enums import CoverageTarget, PathSegmentKind, RunStatus
from agriautolab.contracts.errors import KinematicModelError
from agriautolab.contracts.geometry import LineStringSpec, Point, PolygonSpec
from agriautolab.contracts.problem import CoverageProblem
from agriautolab.contracts.protocol import BenchmarkProtocol
from agriautolab.contracts.vehicle import VehicleSpec
from agriautolab.algorithms.stages.path import DubinsPath
from agriautolab.algorithms.stages.route import SnakeRoute
from agriautolab.validation.validator import PathValidator


def tracked_vehicle() -> VehicleSpec:
    return VehicleSpec(working_width_m=10.0, body_width_m=2.0, min_turning_radius_m=0.0)


def two_swaths() -> SwathsArtifact:
    swaths = tuple(
        Swath(
            swath_id=f"s{index}",
            centerline=LineStringSpec(
                geometry_id=f"s{index}",
                points=(Point(x=0.0, y=y), Point(x=100.0, y=y)),
            ),
            width_m=10.0,
        )
        for index, y in enumerate((5.0, 15.0))
    )
    return SwathsArtifact(swaths=swaths)


@pytest.mark.parametrize("radius,expected", [(0.0, True), (1e-12, True), (1e-9, True), (1e-6, False), (3.0, False)])
def test_can_turn_in_place_threshold(radius: float, expected: bool) -> None:
    assert VehicleSpec(working_width_m=10.0, body_width_m=2.0, min_turning_radius_m=radius).can_turn_in_place is expected


def test_dubins_refuses_zero_radius_with_an_explanatory_message() -> None:
    route = SnakeRoute().run(two_swaths())
    with pytest.raises(KinematicModelError) as error:
        DubinsPath(sample_step_m=0.5).run(route, tracked_vehicle())
    message = str(error.value)
    assert "原地转向" in message
    assert "Dubins" in message


def test_dubins_refusal_precedes_any_nan_or_division_by_zero() -> None:
    """回归点：错误必须在入口抛出，而不是让 d = distance / 0 先产生 inf/NaN 坐标。"""
    route = SnakeRoute().run(two_swaths())
    with pytest.raises(KinematicModelError):
        DubinsPath(sample_step_m=0.5).run(route, VehicleSpec(
            working_width_m=10.0, body_width_m=2.0, min_turning_radius_m=0.0,
        ))


def test_validator_treats_zero_radius_as_unbounded_curvature() -> None:
    """校验器不能被 1/0 炸掉：可原地转向的车没有曲率上界。"""
    field = PolygonSpec(
        geometry_id="field",
        exterior=(
            Point(x=0.0, y=0.0), Point(x=100.0, y=0.0), Point(x=100.0, y=50.0),
            Point(x=0.0, y=50.0), Point(x=0.0, y=0.0),
        ),
    )
    problem = CoverageProblem(problem_id="p", field=field)
    path = PathArtifact(segments=(PathSegment(
        segment_id="w0",
        kind=PathSegmentKind.WORK,
        line=LineStringSpec(geometry_id="w0", points=(Point(x=1.0, y=25.0), Point(x=99.0, y=25.0))),
        signed_curvature_m_inv=1000.0,
    ),))
    result = PathValidator().validate(
        problem, tracked_vehicle(), path,
        BenchmarkProtocol(hypervolume_reference=HYPERVOLUME_TEST_REFERENCE, reverse_cost=REVERSE_COST_TEST_SPEC, protocol_id="p", coverage_target=CoverageTarget.ORIGINAL_FIELD, coverage_threshold=0.0),
    )
    assert result.status is RunStatus.OK
    assert math.isfinite(result.metric("path_length"))
