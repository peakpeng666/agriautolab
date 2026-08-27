"""分母守卫的三层：构造令牌、语义不变量、provenance 证据链。

第二层的非凸回归必须用 L 形地块：凸多边形的内偏置角点是尖的，join_style 不起作用，
矩形上 round 与 mitre 给出完全相同的结果（100x50、h=6 时同为 3344.000），
测不出两套实现分家的口子。Fields2Benchmark 的 350 块真实地块没有一块是矩形。
"""

import pytest
from shapely import LineString, box

from agriautolab.contracts.artifacts import HeadlandArtifact, HeadlandCell
from agriautolab.contracts.enums import CoverageTarget
from agriautolab.contracts.errors import CoverageDenominatorError
from agriautolab.contracts.geometry import GeometryFrame, Point, PolygonSpec
from agriautolab.contracts.problem import CoverageProblem
from agriautolab.algorithms.stages.decomposition import NoDecomposition
from agriautolab.algorithms.stages.headland import ConstantWidthHeadland
from agriautolab.algorithms.stages.swath import LongestEdgeSwath
from agriautolab.geometry.footprint import QUAD_SEGS
from agriautolab.geometry.kernel import FieldGeometry
from agriautolab.geometry.validate import (
    line_from_spec,
    polygon_from_spec,
    polygon_parts_to_specs,
)
from agriautolab.pipeline.metrics.coverage import (
    _RESOLVED, CoverageTargets, coverage_stats, resolve_coverage_targets,
)


def l_shape_problem() -> CoverageProblem:
    """100x50 缺右上 40x30 角的 L 形：一个反曲顶点，join_style 在这里开始起作用。"""
    return CoverageProblem(
        problem_id="lshape",
        field=PolygonSpec(
            geometry_id="field",
            exterior=(
                Point(x=0.0, y=0.0), Point(x=100.0, y=0.0), Point(x=100.0, y=20.0),
                Point(x=60.0, y=20.0), Point(x=60.0, y=50.0), Point(x=0.0, y=50.0),
                Point(x=0.0, y=0.0),
            ),
        ),
    )


def task_notch_l_shape_problem() -> CoverageProblem:
    """勘误结案用的形状：任务书实际跑的多边形，缺口 60x30（塔腿 40x30）。

    任务书文字把缺口误写成 40x30；两个 L 各自正确，绝对差一致（7.771064），
    见 AUDIT_NOTE「已封口的分母旁路」一节的结案表。
    """
    return CoverageProblem(
        problem_id="lshape-task",
        field=PolygonSpec(
            geometry_id="field",
            exterior=(
                Point(x=0.0, y=0.0), Point(x=100.0, y=0.0), Point(x=100.0, y=50.0),
                Point(x=60.0, y=50.0), Point(x=60.0, y=20.0), Point(x=0.0, y=20.0),
                Point(x=0.0, y=0.0),
            ),
        ),
    )


def headland_for(problem: CoverageProblem, width_m: float):
    return ConstantWidthHeadland(width_m).run(NoDecomposition().run(problem))


def forced_targets(**overrides) -> CoverageTargets:
    """带着 _RESOLVED 越过第一层令牌，专测第二层语义不变量。

    生产代码永远不该这样构造；这是测试第二层的唯一入口，
    与令牌 docstring 的定位一致（纪律，不是安全边界）。
    """
    original = box(0.0, 0.0, 10.0, 10.0)
    main = box(2.0, 2.0, 8.0, 8.0)
    kwargs = dict(
        original_field=original,
        main_field=main,
        selected=main,
        target_kind=CoverageTarget.MAIN_FIELD,
        headland_width_m=6.0,
        frame=GeometryFrame(),
        _token=_RESOLVED,
    )
    kwargs.update(overrides)
    return CoverageTargets(**kwargs)


def test_direct_construction_without_token_is_rejected() -> None:
    with pytest.raises(CoverageDenominatorError):
        CoverageTargets(
            original_field=box(0.0, 0.0, 10.0, 10.0),
            main_field=box(0.0, 0.0, 10.0, 10.0),
            selected=box(0.0, 0.0, 10.0, 10.0),
            target_kind=CoverageTarget.ORIGINAL_FIELD,
            headland_width_m=None,
            frame=GeometryFrame(),
        )


def test_resolved_targets_feed_coverage_stats(rectangle_problem, robot) -> None:
    headland = headland_for(rectangle_problem, 6.0)
    swaths = LongestEdgeSwath().run(headland, working_width_m=robot.working_width_m)
    lines = tuple(line_from_spec(swath.centerline) for swath in swaths.swaths)
    targets = resolve_coverage_targets(
        rectangle_problem, headland, target=CoverageTarget.MAIN_FIELD, headland_width_m=6.0
    )

    stats = coverage_stats(lines, working_width_m=robot.working_width_m, targets=targets)
    assert 0.0 < stats.coverage_ratio_main <= 1.0 + 1e-12
    assert 0.0 < stats.coverage_ratio_field <= 1.0 + 1e-12
    assert stats.denominator.declared_headland_width_m == 6.0
    for hash_value in (
        stats.denominator.original_field_hash,
        stats.denominator.main_field_hash,
        stats.denominator.selected_hash,
    ):
        assert len(hash_value) == 64


def test_main_field_outside_original_field_is_rejected() -> None:
    with pytest.raises(CoverageDenominatorError) as excinfo:
        forced_targets(
            main_field=box(50.0, 50.0, 60.0, 60.0),
            selected=box(50.0, 50.0, 60.0, 60.0),
        )
    assert "100.0" in str(excinfo.value)


@pytest.mark.parametrize("target,selected_box", [
    (CoverageTarget.MAIN_FIELD, (0.0, 0.0, 10.0, 10.0)),
    (CoverageTarget.ORIGINAL_FIELD, (2.0, 2.0, 8.0, 8.0)),
])
def test_selected_mismatching_target_kind_is_rejected(target: CoverageTarget, selected_box: tuple) -> None:
    with pytest.raises(CoverageDenominatorError) as excinfo:
        forced_targets(target_kind=target, selected=box(*selected_box))
    assert target.value in str(excinfo.value)


def test_none_width_with_shrunk_main_field_is_rejected() -> None:
    """没有地头，主田即原田：main_field 比 original_field 小的状态必须在构造点被拒。"""
    with pytest.raises(CoverageDenominatorError):
        forced_targets(headland_width_m=None)


def test_no_headland_makes_both_ratios_equal_and_provenance_records_none(rectangle_problem) -> None:
    targets = resolve_coverage_targets(rectangle_problem, None, target=CoverageTarget.MAIN_FIELD)
    stats = coverage_stats(
        (LineString([(0.0, 25.0), (100.0, 25.0)]),), working_width_m=10.0, targets=targets
    )
    assert stats.coverage_ratio_field == stats.coverage_ratio_main
    assert stats.denominator.declared_headland_width_m is None
    assert stats.denominator.headland_ring_hash is None
    assert stats.denominator.main_field_hash == stats.denominator.original_field_hash


def test_provenance_is_reproducible_and_isolates_the_headland(rectangle_problem) -> None:
    headland = headland_for(rectangle_problem, 2.0)

    first = resolve_coverage_targets(
        rectangle_problem, headland, target=CoverageTarget.ORIGINAL_FIELD, headland_width_m=2.0
    ).provenance
    second = resolve_coverage_targets(
        rectangle_problem, headland, target=CoverageTarget.ORIGINAL_FIELD, headland_width_m=2.0
    ).provenance
    assert (first.target_kind, first.declared_headland_width_m, first.original_field_hash,
            first.main_field_hash, first.selected_hash, first.headland_ring_hash) == \
           (second.target_kind, second.declared_headland_width_m, second.original_field_hash,
            second.main_field_hash, second.selected_hash, second.headland_ring_hash)

    wider = resolve_coverage_targets(
        rectangle_problem, headland_for(rectangle_problem, 6.0),
        target=CoverageTarget.ORIGINAL_FIELD, headland_width_m=6.0,
    ).provenance
    assert wider.original_field_hash == first.original_field_hash
    assert wider.main_field_hash != first.main_field_hash


def test_field_geometry_no_longer_accepts_headland_width(rectangle_problem, robot) -> None:
    with pytest.raises(TypeError):
        FieldGeometry.from_problem(rectangle_problem, robot, headland_width_m=6.0)
    assert not hasattr(FieldGeometry, "headland")


def test_nonconvex_main_field_area_is_pinned_as_regression_baseline() -> None:
    """非凸回归基线：join=round、quad_segs=QUAD_SEGS 的当前实现值，rel=1e-9 固化。

    矩形测不出这条：凸多边形内偏置角点是尖的，round 与 mitre 同为 3344.000；
    这块 L 形上 mitre 会给 2144.000000，相对差 0.361%。改 QUAD_SEGS 也会漂移
    （8 与 64 之间相对差 8.3e-5），所以基线同时钉住 join 与分辨率两个旋钮。
    """
    problem = l_shape_problem()
    targets = resolve_coverage_targets(
        problem, headland_for(problem, 6.0), target=CoverageTarget.MAIN_FIELD, headland_width_m=6.0
    )
    assert targets.main_field.area == pytest.approx(2151.7710635850867, rel=1e-9)


def test_headland_artifact_without_declared_width_is_rejected(rectangle_problem) -> None:
    with pytest.raises(CoverageDenominatorError):
        resolve_coverage_targets(
            rectangle_problem, headland_for(rectangle_problem, 6.0), target=CoverageTarget.MAIN_FIELD
        )


def test_declared_width_without_headland_artifact_is_rejected(rectangle_problem) -> None:
    with pytest.raises(CoverageDenominatorError):
        resolve_coverage_targets(
            rectangle_problem, None, target=CoverageTarget.MAIN_FIELD, headland_width_m=6.0
        )


def test_nonpositive_declared_width_is_rejected(rectangle_problem) -> None:
    with pytest.raises(CoverageDenominatorError):
        resolve_coverage_targets(
            rectangle_problem, headland_for(rectangle_problem, 6.0),
            target=CoverageTarget.MAIN_FIELD, headland_width_m=0.0,
        )


def artifact_from_geometry(field, main) -> HeadlandArtifact:
    """手工组装地头产物，专测申报可证伪：产物内容与申报标量刻意不一致。"""
    return HeadlandArtifact(cells=(HeadlandCell(
        cell_id="field",
        main_field=polygon_parts_to_specs(main, "field:main"),
        headland=polygon_parts_to_specs(field.difference(main), "field:headland"),
    ),))


def test_declared_width_mismatching_generated_main_field_is_rejected(rectangle_problem) -> None:
    """用 h=6 生成产物、却申报 12.0：重算对不上，异常消息必须带实测残差。"""
    artifact = headland_for(rectangle_problem, 6.0)
    with pytest.raises(CoverageDenominatorError) as excinfo:
        resolve_coverage_targets(
            rectangle_problem, artifact, target=CoverageTarget.MAIN_FIELD, headland_width_m=12.0
        )
    assert "1368.0" in str(excinfo.value)


def test_mitre_generated_main_field_with_correct_scalar_is_rejected() -> None:
    """生成侧用 mitre 造主田、申报正确的标量 6.0：必须抛。

    这条钉的就是 round/mitre 在非凸地块上 0.4%~0.5% 的分家口子，
    L-shaped polygon with a 60x30 cutout.
    """
    problem = task_notch_l_shape_problem()
    field = polygon_from_spec(problem.field)
    mitre_main = field.buffer(-6.0, cap_style="round", join_style="mitre", quad_segs=QUAD_SEGS)
    artifact = artifact_from_geometry(field, mitre_main)
    with pytest.raises(CoverageDenominatorError) as excinfo:
        resolve_coverage_targets(problem, artifact, target=CoverageTarget.MAIN_FIELD, headland_width_m=6.0)
    assert "7.77" in str(excinfo.value)


def test_variable_width_headland_cannot_be_declared_as_scalar(rectangle_problem) -> None:
    """逐边不同宽度的地头用标量本来就无法描述；申报标量就是申报错了，就该抛。

    这里造一个左边 15 米、其余 6 米的地头（均匀 6 米主田再被抠掉左条带）。
    不加特例分支是刻意的：非均匀地头的正解是产物自带逐边宽度表，不是放宽这条检查。
    """
    field = polygon_from_spec(rectangle_problem.field)
    uniform = field.buffer(-6.0, cap_style="round", join_style="round", quad_segs=QUAD_SEGS)
    variable = uniform.difference(box(0.0, 0.0, 9.0, 50.0))
    artifact = artifact_from_geometry(field, variable)
    with pytest.raises(CoverageDenominatorError):
        resolve_coverage_targets(
            rectangle_problem, artifact, target=CoverageTarget.MAIN_FIELD, headland_width_m=6.0
        )


def test_declared_width_with_ringless_main_field_is_rejected() -> None:
    whole = box(0.0, 0.0, 10.0, 10.0)
    with pytest.raises(CoverageDenominatorError):
        forced_targets(main_field=whole, selected=whole)


def test_headland_ring_hash_tracks_width_not_target_kind(rectangle_problem) -> None:
    headland_2 = headland_for(rectangle_problem, 2.0)
    headland_6 = headland_for(rectangle_problem, 6.0)
    on_main = resolve_coverage_targets(
        rectangle_problem, headland_6, target=CoverageTarget.MAIN_FIELD, headland_width_m=6.0
    ).provenance
    on_field = resolve_coverage_targets(
        rectangle_problem, headland_6, target=CoverageTarget.ORIGINAL_FIELD, headland_width_m=6.0
    ).provenance
    narrow = resolve_coverage_targets(
        rectangle_problem, headland_2, target=CoverageTarget.MAIN_FIELD, headland_width_m=2.0
    ).provenance

    assert on_main.headland_ring_hash == on_field.headland_ring_hash
    assert narrow.headland_ring_hash != on_main.headland_ring_hash
    # 防退化成别名：环带哈希既不等于主田哈希，也不等于原田哈希
    assert on_main.headland_ring_hash not in {on_main.main_field_hash, on_main.original_field_hash}


def test_frame_comes_from_problem_not_the_caller(rectangle_problem) -> None:
    """frame 只能由 problem 推出：resolve 不收 frame 参数，哈希全部挂在 problem 的坐标系上。"""
    first = resolve_coverage_targets(rectangle_problem, None, target=CoverageTarget.MAIN_FIELD)
    second = resolve_coverage_targets(rectangle_problem, None, target=CoverageTarget.MAIN_FIELD)
    assert first.frame == second.frame == rectangle_problem.frame

    projected = rectangle_problem.model_copy(update={"frame": GeometryFrame(crs="EPSG:32650")})
    other = resolve_coverage_targets(projected, None, target=CoverageTarget.MAIN_FIELD)
    # 几何完全相同、只有坐标系不同：三个哈希必须全变，否则 frame 成了自由参数
    assert other.provenance.original_field_hash != first.provenance.original_field_hash
    assert other.provenance.main_field_hash != first.provenance.main_field_hash
    assert other.provenance.selected_hash != first.provenance.selected_hash
