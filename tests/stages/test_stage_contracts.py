"""逐个阶段单独对照其几何输入输出契约。"""

import math

import pytest
from shapely import Polygon

from agriautolab.contracts.artifacts import HeadlandArtifact, HeadlandCell, Swath, SwathsArtifact
from agriautolab.contracts.enums import PathSegmentKind, SwathDirection
from agriautolab.contracts.geometry import LineStringSpec, Point
from agriautolab.coverage.stages.decomposition import NoDecomposition
from agriautolab.coverage.stages.headland import ConstantWidthHeadland
from agriautolab.coverage.stages.path import DubinsPath
from agriautolab.coverage.stages.route import SnakeRoute
from agriautolab.coverage.stages.swath import LongestEdgeSwath
from agriautolab.geometry.robust import robust_union
from agriautolab.geometry.validate import line_from_spec, polygon_from_spec


def test_decomposition_preserves_field_area(rectangle_problem) -> None:
    cells = NoDecomposition().run(rectangle_problem)
    geometries = tuple(polygon_from_spec(cell) for cell in cells.cells)
    union = robust_union(geometries, scale_hint=100.0)
    field = polygon_from_spec(rectangle_problem.field)
    assert union.area == pytest.approx(field.area, rel=1e-12)
    assert all(field.covers(cell) for cell in geometries)


def test_decomposition_has_no_cell_overlap(rectangle_problem) -> None:
    cells = NoDecomposition().run(rectangle_problem)
    geometries = tuple(polygon_from_spec(cell) for cell in cells.cells)
    overlap = sum(a.intersection(b).area for i, a in enumerate(geometries) for b in geometries[i+1:])
    assert overlap == 0.0


def test_headland_partitions_cell(rectangle_problem) -> None:
    cells = NoDecomposition().run(rectangle_problem)
    result = ConstantWidthHeadland(5.0).run(cells)
    original = polygon_from_spec(cells.cells[0])
    main = polygon_from_spec(result.cells[0].main_field[0])
    headland = polygon_from_spec(result.cells[0].headland[0])
    assert original.covers(main)
    assert original.covers(headland)
    assert main.intersection(headland).area == pytest.approx(0.0, abs=1e-12)
    assert main.union(headland).area == pytest.approx(original.area, rel=1e-12)


def _manual_headland() -> HeadlandArtifact:
    main = Polygon([(0,0), (100,0), (100,50), (0,50), (0,0)])
    head = Polygon([(110,0), (111,0), (111,1), (110,1), (110,0)])
    from agriautolab.geometry.validate import polygon_to_spec
    return HeadlandArtifact(cells=(HeadlandCell(
        cell_id="c", main_field=(polygon_to_spec(main, "main"),), headland=(polygon_to_spec(head, "head"),)
    ),))


@pytest.mark.parametrize("width,expected", [(10.0, 5), (12.0, 5), (25.0, 2), (60.0, 1)])
def test_swath_count_matches_ceiling_on_rectangle(width: float, expected: int) -> None:
    swaths = LongestEdgeSwath().run(_manual_headland(), working_width_m=width)
    assert len(swaths.swaths) == expected


def test_swath_centerlines_stay_in_main_field() -> None:
    artifact = _manual_headland()
    main = polygon_from_spec(artifact.cells[0].main_field[0])
    swaths = LongestEdgeSwath().run(artifact, working_width_m=12.0)
    assert all(main.covers(line_from_spec(swath.centerline)) for swath in swaths.swaths)


def _three_swaths() -> SwathsArtifact:
    swaths = []
    for index, y in enumerate((5.0, 15.0, 25.0)):
        line = LineStringSpec(
            geometry_id=f"s{index}",
            points=(Point(x=0,y=y), Point(x=100,y=y)),
        )
        swaths.append(Swath(swath_id=f"s{index}", centerline=line, width_m=10.0))
    return SwathsArtifact(swaths=tuple(swaths))


def test_route_visits_each_swath_once_and_alternates() -> None:
    route = SnakeRoute().run(_three_swaths())
    assert {item.swath_id for item in route.traversals} == {"s0", "s1", "s2"}
    assert len(route.traversals) == 3
    assert tuple(item.direction for item in route.traversals) == (
        SwathDirection.FORWARD, SwathDirection.REVERSE, SwathDirection.FORWARD
    )


def test_path_is_continuous_and_curvature_bounded(robot) -> None:
    route = SnakeRoute().run(_three_swaths())
    path = DubinsPath(sample_step_m=0.5).run(route, robot)
    assert path.segments
    assert any(segment.kind is PathSegmentKind.TURN for segment in path.segments)
    assert sum(segment.kind is PathSegmentKind.WORK for segment in path.segments) == 3
    for left, right in zip(path.segments, path.segments[1:]):
        assert left.line.points[-1] == right.line.points[0]
    limit = 1.0 / robot.min_turning_radius_m
    assert all(math.isfinite(point.x) and math.isfinite(point.y) for segment in path.segments for point in segment.line.points)
    assert max(abs(segment.signed_curvature_m_inv) for segment in path.segments) <= limit + 1e-12


@pytest.mark.parametrize("radius", [1.0, 3.0, 8.0])
def test_dubins_curvature_tracks_robot_radius(radius: float) -> None:
    from agriautolab.contracts.vehicle import VehicleSpec
    robot = VehicleSpec(working_width_m=10, body_width_m=2, min_turning_radius_m=radius)
    path = DubinsPath(sample_step_m=0.2).run(SnakeRoute().run(_three_swaths()), robot)
    assert max(abs(segment.signed_curvature_m_inv) for segment in path.segments) <= 1.0 / radius + 1e-12
