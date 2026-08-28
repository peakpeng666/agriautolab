"""把「地头越宽、对主田覆盖率越好看」这张实测表固化成回归断言。

背景：分母曾经是 coverage_stats 的自由入参。100x50 田块、幅宽 10，只改地头宽度，
对主田覆盖率四次都是 1.0000，对原田却是 0.8832 / 0.6688 / 0.3952 / 0.1792。
地头生成是被比较的五个阶段之一，分母跟着它一起变，比较就失去意义。
"""

import pytest
from shapely import box

from conftest import HYPERVOLUME_TEST_REFERENCE, REVERSE_COST_TEST_SPEC
from agriautolab.contracts.enums import CoverageTarget, RunStatus
from agriautolab.contracts.errors import CoverageDenominatorError, GeometryValidationError
from agriautolab.contracts.geometry import GeometryFrame, Point, PolygonSpec
from agriautolab.contracts.problem import CoverageProblem
from agriautolab.contracts.protocol import BenchmarkProtocol
from agriautolab.contracts.vehicle import VehicleSpec
from agriautolab.pipeline.coverage_config import CoveragePipelineConfig
from agriautolab.pipeline.executor import CoveragePipeline
from agriautolab.algorithms.stages.decomposition import NoDecomposition
from agriautolab.algorithms.stages.headland import ConstantWidthHeadland
from agriautolab.algorithms.stages.swath import LongestEdgeSwath
from agriautolab.geometry.validate import line_from_spec, polygon_from_spec
from agriautolab.pipeline.metrics.coverage import (
    _RESOLVED, CoverageTargets, coverage_stats, resolve_coverage_targets,
)


WORKING_WIDTH_M = 10.0

# 地头宽度 -> (主田面积, 对原田覆盖率)。数值来自本仓库实测，不是估算。
HEADLAND_TABLE = (
    (2.0, 4416.0, 0.8832),
    (6.0, 3344.0, 0.6688),
    (12.0, 1976.0, 0.3952),
    (18.0, 896.0, 0.1792),
)


def rectangle_problem() -> CoverageProblem:
    field = PolygonSpec(
        geometry_id="field",
        exterior=(
            Point(x=0.0, y=0.0), Point(x=100.0, y=0.0), Point(x=100.0, y=50.0),
            Point(x=0.0, y=50.0), Point(x=0.0, y=0.0),
        ),
    )
    return CoverageProblem(problem_id="rect", field=field)


def robot() -> VehicleSpec:
    return VehicleSpec(working_width_m=WORKING_WIDTH_M, body_width_m=2.0, min_turning_radius_m=3.0)


def headland_for(problem: CoverageProblem, width_m: float):
    return ConstantWidthHeadland(width_m).run(NoDecomposition().run(problem))


@pytest.mark.parametrize("width_m,main_area_m2,expected_field_ratio", HEADLAND_TABLE)
def test_main_field_ratio_stays_perfect_while_field_ratio_collapses(
    width_m: float, main_area_m2: float, expected_field_ratio: float
) -> None:
    problem = rectangle_problem()
    headland = headland_for(problem, width_m)
    swaths = LongestEdgeSwath().run(headland, working_width_m=WORKING_WIDTH_M)
    lines = tuple(line_from_spec(swath.centerline) for swath in swaths.swaths)
    targets = resolve_coverage_targets(problem, headland, target=CoverageTarget.MAIN_FIELD, headland_width_m=width_m)

    assert targets.main_field.area == pytest.approx(main_area_m2, rel=1e-9)
    stats = coverage_stats(lines, working_width_m=WORKING_WIDTH_M, targets=targets)
    assert stats.coverage_ratio_main == pytest.approx(1.0, rel=1e-3)
    assert stats.coverage_ratio_field == pytest.approx(expected_field_ratio, rel=1e-3)


def test_denominators_do_not_depend_on_declared_target() -> None:
    """target 只决定 selected 指向哪一个；两个比值本身需一模一样。"""
    problem = rectangle_problem()
    headland = headland_for(problem, 12.0)
    swaths = LongestEdgeSwath().run(headland, working_width_m=WORKING_WIDTH_M)
    lines = tuple(line_from_spec(swath.centerline) for swath in swaths.swaths)

    on_field = resolve_coverage_targets(problem, headland, target=CoverageTarget.ORIGINAL_FIELD, headland_width_m=12.0)
    on_main = resolve_coverage_targets(problem, headland, target=CoverageTarget.MAIN_FIELD, headland_width_m=12.0)
    field_stats = coverage_stats(lines, working_width_m=WORKING_WIDTH_M, targets=on_field)
    main_stats = coverage_stats(lines, working_width_m=WORKING_WIDTH_M, targets=on_main)

    assert field_stats.coverage_ratio_field == main_stats.coverage_ratio_field
    assert field_stats.coverage_ratio_main == main_stats.coverage_ratio_main
    assert field_stats.selected_coverage_ratio() == pytest.approx(0.3952, rel=1e-3)
    assert main_stats.selected_coverage_ratio() == pytest.approx(1.0, rel=1e-3)


def test_missing_headland_makes_main_field_equal_original_field() -> None:
    problem = rectangle_problem()
    targets = resolve_coverage_targets(problem, None, target=CoverageTarget.MAIN_FIELD)
    assert targets.main_field.area == pytest.approx(targets.original_field.area, rel=1e-12)


def test_hard_gate_uses_field_ratio_even_when_protocol_selects_main_field() -> None:
    """地头 18 米、tau=0.9：协议即使声明按主田报数，门槛也需按原田判不可行。"""
    problem = rectangle_problem()
    vehicle = robot()
    path = CoveragePipeline(CoveragePipelineConfig(headland_width_m=18.0, dubins_sample_step_m=0.5)).run(problem, vehicle)
    headland = headland_for(problem, 18.0)

    from agriautolab.validation.validator import PathValidator

    rejected = PathValidator().validate(
        problem, vehicle, path,
        BenchmarkProtocol(hypervolume_reference=HYPERVOLUME_TEST_REFERENCE, reverse_cost=REVERSE_COST_TEST_SPEC, protocol_id="p", coverage_target=CoverageTarget.MAIN_FIELD, coverage_threshold=0.9),
        headland=headland,
        headland_width_m=18.0,
    )
    assert rejected.status is RunStatus.CONSTRAINT_VIOLATION
    assert rejected.failure_reason == "validator_rejected:coverage_threshold"

    reported = PathValidator().validate(
        problem, vehicle, path,
        BenchmarkProtocol(hypervolume_reference=HYPERVOLUME_TEST_REFERENCE, reverse_cost=REVERSE_COST_TEST_SPEC, protocol_id="p", coverage_target=CoverageTarget.MAIN_FIELD, coverage_threshold=0.0),
        headland=headland,
        headland_width_m=18.0,
    )
    assert reported.status is RunStatus.OK
    assert reported.metric("coverage_ratio_main") == pytest.approx(1.0, rel=1e-3)
    assert reported.metric("coverage_ratio_field") == pytest.approx(0.1792, rel=1e-3)


def test_coverage_stats_rejects_bare_geometry_as_denominator() -> None:
    lines = ()
    with pytest.raises(TypeError):
        coverage_stats(lines, working_width_m=WORKING_WIDTH_M, field=box(0.0, 0.0, 100.0, 50.0))
    with pytest.raises(TypeError):
        coverage_stats(lines, working_width_m=WORKING_WIDTH_M, targets=box(0.0, 0.0, 100.0, 50.0))


def test_hand_built_targets_cannot_place_main_field_outside_original_field() -> None:
    """构造令牌挡的是「顺手构造」；这里带着令牌越过第一层，验证第二层语义不变量仍在岗。

    期望的异常类型随 G-1 轮从 ValueError 改为 CoverageDenominatorError，
    历史留痕见 study-001-frozen tag。
    """
    with pytest.raises(CoverageDenominatorError):
        CoverageTargets(
            original_field=box(0.0, 0.0, 10.0, 10.0),
            main_field=box(50.0, 50.0, 60.0, 60.0),
            selected=box(50.0, 50.0, 60.0, 60.0),
            target_kind=CoverageTarget.MAIN_FIELD,
            headland_width_m=6.0,
            frame=GeometryFrame(),
            _token=_RESOLVED,
        )


def test_main_field_excludes_obstacles_that_headland_stage_never_saw() -> None:
    """陷阱回归：地头阶段的 cell 没扣障碍，主田分母需自己再扣一次。"""
    problem = rectangle_problem()
    obstacle = PolygonSpec(
        geometry_id="obs",
        exterior=(
            Point(x=40.0, y=20.0), Point(x=60.0, y=20.0), Point(x=60.0, y=30.0),
            Point(x=40.0, y=30.0), Point(x=40.0, y=20.0),
        ),
    )
    with_obstacle = problem.model_copy(update={"obstacles": (obstacle,)})
    headland = headland_for(problem, 6.0)
    targets = resolve_coverage_targets(with_obstacle, headland, target=CoverageTarget.MAIN_FIELD, headland_width_m=6.0)

    obstacle_area = polygon_from_spec(obstacle).area
    assert targets.original_field.area == pytest.approx(5000.0 - obstacle_area, rel=1e-12)
    assert targets.main_field.area == pytest.approx(3344.0 - obstacle_area, rel=1e-12)


def test_obstacle_outside_field_is_rejected_not_silently_clipped() -> None:
    """越界障碍被 difference 裁掉的话，分母看着正常，少掉的面积再也查不出来自哪里。"""
    problem = rectangle_problem()
    outside = PolygonSpec(
        geometry_id="outside",
        exterior=(
            Point(x=90.0, y=20.0), Point(x=120.0, y=20.0), Point(x=120.0, y=30.0),
            Point(x=90.0, y=30.0), Point(x=90.0, y=20.0),
        ),
    )
    with pytest.raises(GeometryValidationError):
        resolve_coverage_targets(
            problem.model_copy(update={"obstacles": (outside,)}),
            None,
            target=CoverageTarget.ORIGINAL_FIELD,
        )


def test_coverage_target_changes_protocol_hash() -> None:
    on_field = BenchmarkProtocol(hypervolume_reference=HYPERVOLUME_TEST_REFERENCE, reverse_cost=REVERSE_COST_TEST_SPEC, protocol_id="p", coverage_target=CoverageTarget.ORIGINAL_FIELD)
    on_main = BenchmarkProtocol(hypervolume_reference=HYPERVOLUME_TEST_REFERENCE, reverse_cost=REVERSE_COST_TEST_SPEC, protocol_id="p", coverage_target=CoverageTarget.MAIN_FIELD)
    assert on_field.spec_hash() != on_main.spec_hash()
    assert on_field.spec_hash() == BenchmarkProtocol(hypervolume_reference=HYPERVOLUME_TEST_REFERENCE, reverse_cost=REVERSE_COST_TEST_SPEC, 
        protocol_id="p", coverage_target=CoverageTarget.ORIGINAL_FIELD
    ).spec_hash()
