"""校验器的拒绝需是结构化数据，不能被伪装成一次零代价的成功运行。"""

from conftest import HYPERVOLUME_TEST_REFERENCE, REVERSE_COST_TEST_SPEC
from agriautolab.contracts.artifacts import PathArtifact, PathSegment
from agriautolab.contracts.enums import CoverageTarget, PathSegmentKind, RunStatus
from agriautolab.contracts.geometry import LineStringSpec, Point, PolygonSpec
from agriautolab.contracts.problem import CoverageProblem
from agriautolab.contracts.protocol import BenchmarkProtocol
from agriautolab.contracts.vehicle import VehicleSpec
from agriautolab.validation.validator import PathValidator


def rect(x0: float, y0: float, x1: float, y1: float, geometry_id: str) -> PolygonSpec:
    return PolygonSpec(geometry_id=geometry_id, exterior=(
        Point(x=x0,y=y0), Point(x=x1,y=y0), Point(x=x1,y=y1), Point(x=x0,y=y1), Point(x=x0,y=y0)
    ))


def segment(points, kind=PathSegmentKind.WORK, curvature=0.0, sid="p") -> PathSegment:
    return PathSegment(
        segment_id=sid, kind=kind,
        line=LineStringSpec(geometry_id=sid, points=tuple(Point(x=x,y=y) for x,y in points)),
        signed_curvature_m_inv=curvature,
    )


def base_robot() -> VehicleSpec:
    return VehicleSpec(working_width_m=4, body_width_m=1, min_turning_radius_m=2)


def test_validator_accepts_feasible_path_with_zero_coverage_threshold() -> None:
    problem = CoverageProblem(problem_id="p", field=rect(0,0,100,50,"field"))
    path = PathArtifact(segments=(segment(((1,25),(99,25))),))
    result = PathValidator().validate(problem, base_robot(), path, BenchmarkProtocol(hypervolume_reference=HYPERVOLUME_TEST_REFERENCE, reverse_cost=REVERSE_COST_TEST_SPEC, protocol_id="p", coverage_target=CoverageTarget.ORIGINAL_FIELD, coverage_threshold=0.0))
    assert result.status is RunStatus.OK
    assert result.metric("path_length") == 98.0


def test_validator_rejects_discontinuous_endpoints_without_raising() -> None:
    problem = CoverageProblem(problem_id="p", field=rect(0,0,100,50,"field"))
    path = PathArtifact(segments=(segment(((1,10),(20,10)), sid="a"), segment(((21,10),(30,10)), sid="b")))
    result = PathValidator().validate(problem, base_robot(), path, BenchmarkProtocol(hypervolume_reference=HYPERVOLUME_TEST_REFERENCE, reverse_cost=REVERSE_COST_TEST_SPEC, protocol_id="p", coverage_target=CoverageTarget.ORIGINAL_FIELD, coverage_threshold=0.0))
    assert result.status is RunStatus.CONSTRAINT_VIOLATION
    assert result.failure_reason == "validator_rejected:discontinuous_endpoints"


def test_validator_rejects_collision() -> None:
    obstacle = rect(40,20,60,30,"obs")
    problem = CoverageProblem(problem_id="p", field=rect(0,0,100,50,"field"), obstacles=(obstacle,))
    path = PathArtifact(segments=(segment(((1,25),(99,25))),))
    result = PathValidator().validate(problem, base_robot(), path, BenchmarkProtocol(hypervolume_reference=HYPERVOLUME_TEST_REFERENCE, reverse_cost=REVERSE_COST_TEST_SPEC, protocol_id="p", coverage_target=CoverageTarget.ORIGINAL_FIELD, coverage_threshold=0.0))
    assert result.status is RunStatus.COLLISION
    assert result.failure_reason == "validator_rejected:collision"


def test_validator_rejects_curvature_limit() -> None:
    problem = CoverageProblem(problem_id="p", field=rect(0,0,100,50,"field"))
    path = PathArtifact(segments=(segment(((1,25),(99,25)), curvature=1.0),))
    result = PathValidator().validate(problem, base_robot(), path, BenchmarkProtocol(hypervolume_reference=HYPERVOLUME_TEST_REFERENCE, reverse_cost=REVERSE_COST_TEST_SPEC, protocol_id="p", coverage_target=CoverageTarget.ORIGINAL_FIELD, coverage_threshold=0.0))
    assert result.status is RunStatus.INFEASIBLE_KINEMATICS


def test_validator_rejects_coverage_threshold() -> None:
    problem = CoverageProblem(problem_id="p", field=rect(0,0,100,50,"field"))
    path = PathArtifact(segments=(segment(((1,25),(99,25))),))
    result = PathValidator().validate(problem, base_robot(), path, BenchmarkProtocol(hypervolume_reference=HYPERVOLUME_TEST_REFERENCE, reverse_cost=REVERSE_COST_TEST_SPEC, protocol_id="p", coverage_target=CoverageTarget.ORIGINAL_FIELD, coverage_threshold=0.9))
    assert result.status is RunStatus.CONSTRAINT_VIOLATION
    assert result.failure_reason == "validator_rejected:coverage_threshold"
