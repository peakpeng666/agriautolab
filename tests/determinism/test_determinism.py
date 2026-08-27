"""可重复性不得被输入顺序、采样辅助函数或 JSON 键序破坏。"""

import pytest

from agriautolab.contracts.geometry import Point, PolygonSpec
from agriautolab.contracts.problem import CoverageProblem
from agriautolab.contracts.vehicle import VehicleSpec
from agriautolab.pipeline.coverage_config import CoveragePipelineConfig
from agriautolab.pipeline.executor import CoveragePipeline
from agriautolab.pipeline.hashing import content_hash
from agriautolab.geometry.hashing import geometry_hash
from agriautolab.geometry.kernel import FieldGeometry
from agriautolab.pipeline.metrics.path import densify, path_length, resample_uniform


def rect(x0: float, y0: float, x1: float, y1: float, geometry_id: str) -> PolygonSpec:
    return PolygonSpec(geometry_id=geometry_id, exterior=(
        Point(x=x0,y=y0), Point(x=x1,y=y0), Point(x=x1,y=y1), Point(x=x0,y=y1), Point(x=x0,y=y0)
    ))


def test_pipeline_five_runs_identical(rectangle_problem, robot) -> None:
    pipeline = CoveragePipeline(CoveragePipelineConfig(headland_width_m=3.0, dubins_sample_step_m=0.5))
    outputs = [pipeline.run(rectangle_problem, robot).model_dump_json() for _ in range(5)]
    assert len(set(outputs)) == 1


def test_obstacle_order_does_not_change_geometry_hash() -> None:
    field = rect(0, 0, 100, 50, "field")
    a = rect(10, 10, 20, 20, "a")
    b = rect(60, 10, 70, 20, "b")
    robot = VehicleSpec(working_width_m=6, body_width_m=2, min_turning_radius_m=3)
    first = CoverageProblem(problem_id="p1", field=field, obstacles=(a, b))
    second = CoverageProblem(problem_id="p2", field=field, obstacles=(b, a))
    g1 = FieldGeometry.from_problem(first, robot)
    g2 = FieldGeometry.from_problem(second, robot)
    assert geometry_hash(g1.raw_free, first.frame) == geometry_hash(g2.raw_free, second.frame)


def test_densify_preserves_original_vertices_and_length() -> None:
    path = (Point(x=0,y=0), Point(x=10,y=0), Point(x=10,y=10))
    dense = densify(path, 3.0)
    for vertex in path:
        assert vertex in dense
    assert path_length(dense) == pytest.approx(path_length(path), rel=1e-15, abs=1e-15)


def test_resample_uniform_never_lengthens_and_larger_step_cuts_more() -> None:
    path = (Point(x=0,y=0), Point(x=10,y=0), Point(x=10,y=10))
    original = path_length(path)
    fine = path_length(resample_uniform(path, 3.0))
    coarse = path_length(resample_uniform(path, 6.0))
    assert fine <= original + 1e-12
    assert coarse <= fine + 1e-12
    assert coarse < original


@pytest.mark.parametrize("corner,expected_length", [
    ((10.0, 0.0, 10.0, 10.0), 20.0),
    ((100.0, 0.0, 100.0, 50.0), 150.0),
])
def test_resample_uniform_is_a_filter_not_a_geometry_preserving_transform(corner, expected_length: float) -> None:
    """步长必须错开拐点。50.0 这种恰好落在 (100,0) 上的步长切不到角，测不出滤波行为。"""
    x1, y1, x2, y2 = corner
    path = (Point(x=0, y=0), Point(x=x1, y=y1), Point(x=x2, y=y2))
    original = path_length(path)
    assert original == pytest.approx(expected_length, abs=1e-12)

    lengths = [path_length(resample_uniform(path, step)) for step in (7.0, 13.0, 60.0)]
    assert all(length < original for length in lengths)
    for coarser, finer in zip(lengths[1:], lengths):
        assert coarser <= finer + 1e-12


def test_resample_uniform_step60_cuts_the_documented_15_meters() -> None:
    path = (Point(x=0, y=0), Point(x=100, y=0), Point(x=100, y=50))
    assert path_length(resample_uniform(path, 60.0)) == pytest.approx(134.7, abs=0.05)


def test_content_hash_ignores_mapping_key_order() -> None:
    assert content_hash({"a": 1, "b": 2}) == content_hash({"b": 2, "a": 1})
