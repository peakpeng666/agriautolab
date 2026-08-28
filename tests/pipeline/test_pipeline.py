"""run_pipeline 的确定性、记忆化与 min_width 条数真值（解析真值清单 13）。"""

import math

import pytest

from conftest import REVERSE_COST_TEST_SPEC

from agriautolab.contracts.enums import CoverageTarget
from agriautolab.contracts.protocol import BenchmarkProtocol
from agriautolab.contracts.rows import RowStructure
from agriautolab.algorithms.swath.min_width import swath_count_at_direction
from agriautolab.algorithms.swath.principal_axis import principal_axis
from agriautolab.algorithms.swath.longest_edge import longest_edge_direction
from agriautolab.contracts.geometry import Point, PolygonSpec
from agriautolab.contracts.problem import CoverageProblem
from agriautolab.contracts.vehicle import VehicleSpec
from agriautolab.pipeline.pareto.hypervolume import analytic_reference
from agriautolab.pipeline.config import PipelineConfig
from agriautolab.pipeline.run import StageMemo, run_pipeline
from agriautolab.geometry.validate import polygon_from_spec


def rect_field() -> PolygonSpec:
    return PolygonSpec(geometry_id="field", exterior=(
        Point(x=0.0, y=0.0), Point(x=100.0, y=0.0), Point(x=100.0, y=50.0),
        Point(x=0.0, y=50.0), Point(x=0.0, y=0.0)))


def l_field() -> PolygonSpec:
    return PolygonSpec(geometry_id="field", exterior=(
        Point(x=0.0, y=0.0), Point(x=100.0, y=0.0), Point(x=100.0, y=20.0),
        Point(x=60.0, y=20.0), Point(x=60.0, y=50.0), Point(x=0.0, y=50.0),
        Point(x=0.0, y=0.0)))


def make_protocol(problem, vehicle) -> BenchmarkProtocol:
    return BenchmarkProtocol(
        protocol_id="test", coverage_target=CoverageTarget.ORIGINAL_FIELD,
        coverage_threshold=0.0, hypervolume_reference=analytic_reference(problem, vehicle),
        reverse_cost=REVERSE_COST_TEST_SPEC,
    )


def feasible_config(**overrides) -> PipelineConfig:
    # 地头 8 米：前进 Dubins 掉头向 swath 端点外鼓出约 2R（R=3），地头 6 米在
    # L 形的窄段零余量、数值上必越界——掉头空间需大于鼓包量，这是物理不是容差问题。
    values = dict(
        decomposition="no_decomposition", headland="uniform_headland", swath="min_width",
        route="boustrophedon_order", path="dubins_transit", params={"headland_width_m": 8.0},
    )
    values.update(overrides)
    return PipelineConfig(**values)


def test_min_width_direction_minimizes_swath_count() -> None:
    """真值 13：min_width 角下的作业段条数 <= 任何其他角（含其余四种 swath 算法的方向）。"""
    from agriautolab.algorithms.swath.min_width import min_width_direction

    polygon = polygon_from_spec(l_field())
    working_width = 10.0
    min_count = swath_count_at_direction(polygon, *min_width_direction(polygon), working_width)
    others = {
        "principal_axis": principal_axis(polygon),
        "longest_edge": longest_edge_direction(polygon),
        "fixed_0": (1.0, 0.0),
        "fixed_90": (0.0, 1.0),
        "diagonal": (math.cos(0.7), math.sin(0.7)),
    }
    for name, (ux, uy) in others.items():
        assert min_count <= swath_count_at_direction(polygon, ux, uy, working_width), name


def test_pipeline_is_deterministic_and_objectives_reproducible() -> None:
    problem = CoverageProblem(problem_id="p", field=l_field())
    vehicle = VehicleSpec(working_width_m=10.0, body_width_m=2.0, min_turning_radius_m=3.0)
    protocol = make_protocol(problem, vehicle)
    config = feasible_config()
    first = run_pipeline(problem, vehicle, config, protocol)
    second = run_pipeline(problem, vehicle, config, protocol)
    assert first.validation.status.value == "ok"
    assert first.objectives == second.objectives
    assert first.path.model_dump_json() == second.path.model_dump_json()
    assert first.config_id == config.config_id()


def test_stage_memo_hits_on_shared_prefix() -> None:
    """记忆化可观测：共享 headland 前缀的两个配置，第二次只算新增阶段。"""
    problem = CoverageProblem(problem_id="p", field=rect_field())
    vehicle = VehicleSpec(working_width_m=10.0, body_width_m=2.0, min_turning_radius_m=3.0)
    protocol = make_protocol(problem, vehicle)
    base = feasible_config(swath="min_width")
    variant = feasible_config(swath="principal_axis")
    memo = StageMemo()
    run_pipeline(problem, vehicle, base, protocol, memo=memo)
    run_pipeline(problem, vehicle, variant, protocol, memo=memo)
    assert memo.hits >= 3   # decomposition + headland + path(+route 视排序) 复用
    assert memo.misses >= 5


def test_no_headland_combination_is_recorded_as_infeasible_not_raised() -> None:
    """失败是数据：无地头 + 前进 Dubins 掉头出界 -> 结构化状态，目标向量为 None。"""
    problem = CoverageProblem(problem_id="p", field=rect_field())
    vehicle = VehicleSpec(working_width_m=10.0, body_width_m=2.0, min_turning_radius_m=3.0)
    protocol = make_protocol(problem, vehicle)
    config = PipelineConfig(
        "no_decomposition", "no_headland", "min_width", "boustrophedon_order", "dubins_transit", {}
    )
    result = run_pipeline(problem, vehicle, config, protocol)
    assert result.validation.failure_reason == "validator_rejected:outside_area"
    assert result.objectives is None


def test_row_aligned_objective_tradeoff_is_visible() -> None:
    """目标冲突在管线上可见：顺行把 crossings 压低、长度升高（turns 与 crossings 冲突）。"""
    rows = RowStructure(direction_rad=math.pi / 2.0, spacing_m=2.5, crossable=True, crossing_penalty=10.0)
    problem = CoverageProblem(problem_id="p", field=rect_field(), row_structure=rows)
    vehicle = VehicleSpec(working_width_m=10.0, body_width_m=2.0, min_turning_radius_m=3.0)
    protocol = make_protocol(problem, vehicle)
    shape_aligned = run_pipeline(problem, vehicle, feasible_config(), protocol).objectives
    row_aligned = run_pipeline(
        problem, vehicle, feasible_config(swath="row_aligned"), protocol
    ).objectives
    assert row_aligned.row_crossings < shape_aligned.row_crossings
    assert row_aligned.path_length > shape_aligned.path_length


def test_row_aligned_without_row_structure_is_rejected() -> None:
    from agriautolab.algorithms.swath.row_aligned import RowAlignedSwath
    from agriautolab.algorithms.stages.decomposition import NoDecomposition

    problem = CoverageProblem(problem_id="p", field=rect_field())
    cells = NoDecomposition().run(problem)
    with pytest.raises(ValueError):
        RowAlignedSwath().run(cells.cells, working_width_m=10.0, problem=problem)


def test_missing_required_param_is_rejected() -> None:
    problem = CoverageProblem(problem_id="p", field=rect_field())
    vehicle = VehicleSpec(working_width_m=10.0, body_width_m=2.0, min_turning_radius_m=3.0)
    protocol = make_protocol(problem, vehicle)
    config = PipelineConfig(
        "no_decomposition", "uniform_headland", "fixed_angle", "boustrophedon_order",
        "dubins_transit", {"headland_width_m": 6.0},   # 缺 angle_rad
    )
    with pytest.raises(ValueError, match="angle_rad"):
        run_pipeline(problem, vehicle, config, protocol)