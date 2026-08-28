"""G-A.2：转移五项分解的完备性。other_m 是哨兵，不是筐。"""

import math

import pytest

from agriautolab.contracts.artifacts import PathArtifact, PathSegment
from agriautolab.contracts.enums import PathSegmentKind
from agriautolab.contracts.errors import TransitDecompositionError
from agriautolab.contracts.geometry import LineStringSpec, Point
from agriautolab.pipeline.metrics.path import headland_turn_count, transit_breakdown


def segment(sid: str, kind: PathSegmentKind, *points: tuple[float, float]) -> PathSegment:
    return PathSegment(
        segment_id=sid,
        kind=kind,
        line=LineStringSpec(geometry_id=sid, points=tuple(Point(x=x, y=y) for x, y in points)),
    )


def test_five_parts_sum_to_total_transit_and_leave_no_residue() -> None:
    path = PathArtifact(segments=(
        segment("t0", PathSegmentKind.TRANSIT, (0.0, 0.0), (0.0, 10.0)),      # 进场腿 10
        segment("w0", PathSegmentKind.WORK, (0.0, 10.0), (100.0, 10.0)),
        segment("t1", PathSegmentKind.TURN, (100.0, 10.0), (100.0, 13.0)),    # 掉头 3
        segment("w1", PathSegmentKind.WORK, (100.0, 13.0), (0.0, 13.0)),
        segment("t2", PathSegmentKind.TURN, (0.0, 13.0), (0.0, 17.0)),        # 掉头 4
        segment("w2", PathSegmentKind.WORK, (0.0, 17.0), (100.0, 17.0)),
        segment("t3", PathSegmentKind.TRANSIT, (100.0, 17.0), (100.0, 22.0)),  # 出场腿 5
    ))
    breakdown = transit_breakdown(path)
    assert breakdown.entry_leg_m == pytest.approx(10.0)
    assert breakdown.turn_total_m == pytest.approx(7.0)
    assert breakdown.turn_count == 2
    assert breakdown.inter_cell_m == 0.0
    assert breakdown.exit_leg_m == pytest.approx(5.0)
    assert breakdown.other_m == 0.0
    assert breakdown.total_m == pytest.approx(22.0)
    assert breakdown.mean_turn_m == pytest.approx(3.5)


def test_multi_segment_run_between_two_work_segments_counts_as_one_turn() -> None:
    """Dubins 一次掉头被采样成 L/S/L 三段，掉头次数仍然是 1——与 headland_turn_count 同口径。"""
    path = PathArtifact(segments=(
        segment("w0", PathSegmentKind.WORK, (0.0, 0.0), (10.0, 0.0)),
        segment("a", PathSegmentKind.TURN, (10.0, 0.0), (12.0, 1.0)),
        segment("b", PathSegmentKind.TURN, (12.0, 1.0), (12.0, 4.0)),
        segment("c", PathSegmentKind.TURN, (12.0, 4.0), (10.0, 5.0)),
        segment("w1", PathSegmentKind.WORK, (10.0, 5.0), (0.0, 5.0)),
    ))
    breakdown = transit_breakdown(path)
    assert breakdown.turn_count == 1
    assert breakdown.turn_count == headland_turn_count(path)
    assert breakdown.turn_total_m == pytest.approx(
        math.hypot(2.0, 1.0) + 3.0 + math.hypot(2.0, 1.0)
    )


def test_cross_cell_run_leaves_turn_bucket_and_does_not_inflate_turn_count() -> None:
    """跨 cell 转场不是掉头：混进 turn_total_m 会让每次掉头的均值凭空变大。"""
    path = PathArtifact(segments=(
        segment("w0", PathSegmentKind.WORK, (0.0, 0.0), (10.0, 0.0)),
        segment("t0", PathSegmentKind.TURN, (10.0, 0.0), (10.0, 4.0)),
        segment("w1", PathSegmentKind.WORK, (10.0, 4.0), (0.0, 4.0)),
        segment("t1", PathSegmentKind.TRANSIT, (0.0, 4.0), (0.0, 104.0)),
        segment("w2", PathSegmentKind.WORK, (0.0, 104.0), (10.0, 104.0)),
    ))
    breakdown = transit_breakdown(path, cell_of_work_index=(0, 0, 1))
    assert breakdown.turn_count == 1
    assert breakdown.turn_total_m == pytest.approx(4.0)
    assert breakdown.inter_cell_m == pytest.approx(100.0)
    assert breakdown.inter_cell_count == 1
    assert breakdown.other_m == 0.0
    # 唯一能查出「掉头被错记成跨 cell」的等式：other_m 只查长度，查不出归类错误。
    assert headland_turn_count(path) == breakdown.turn_count + breakdown.inter_cell_count


@pytest.mark.parametrize("cells,expect_turns,expect_inter", [
    ((0, 0, 0, 0), 3, 0),
    ((0, 0, 1, 1), 2, 1),
    ((0, 1, 2, 3), 0, 3),
])
def test_turn_plus_inter_cell_count_always_equals_headland_turn_count(cells, expect_turns, expect_inter) -> None:
    """放行条件授权加的字段，用途就是这条恒等式——多 cell 下的分解完备性只能靠它。"""
    segments = []
    for index in range(4):
        y = index * 10.0
        segments.append(segment(f"w{index}", PathSegmentKind.WORK, (0.0, y), (10.0, y)))
        if index < 3:
            segments.append(segment(f"t{index}", PathSegmentKind.TURN, (10.0, y), (0.0, y + 10.0)))
    breakdown = transit_breakdown(PathArtifact(segments=tuple(segments)), cell_of_work_index=cells)
    assert (breakdown.turn_count, breakdown.inter_cell_count) == (expect_turns, expect_inter)
    assert headland_turn_count(PathArtifact(segments=tuple(segments))) == (
        breakdown.turn_count + breakdown.inter_cell_count
    )
    assert breakdown.other_m == 0.0


def test_path_without_any_work_segment_is_rejected() -> None:
    """一条作业段都没有时无法区分首腿尾腿，需抛而不是默默记成进场腿。"""
    path = PathArtifact(segments=(
        segment("t0", PathSegmentKind.TRANSIT, (0.0, 0.0), (0.0, 10.0)),
    ))
    with pytest.raises(TransitDecompositionError):
        transit_breakdown(path)


def test_cell_index_length_must_match_work_segment_count() -> None:
    path = PathArtifact(segments=(
        segment("w0", PathSegmentKind.WORK, (0.0, 0.0), (10.0, 0.0)),
        segment("t0", PathSegmentKind.TURN, (10.0, 0.0), (10.0, 4.0)),
        segment("w1", PathSegmentKind.WORK, (10.0, 4.0), (0.0, 4.0)),
    ))
    with pytest.raises(ValueError):
        transit_breakdown(path, cell_of_work_index=(0, 0, 0))


def test_all_work_path_has_zero_transit() -> None:
    path = PathArtifact(segments=(
        segment("w0", PathSegmentKind.WORK, (0.0, 0.0), (10.0, 0.0)),
    ))
    breakdown = transit_breakdown(path)
    assert breakdown.total_m == 0.0
    assert breakdown.turn_count == 0
    assert breakdown.mean_turn_m == 0.0
