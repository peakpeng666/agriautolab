"""pareto 核心的解析真值（§9 真值 9–12）与超体积精确性。"""

import pytest

from conftest import REVERSE_COST_TEST_SPEC

from agriautolab.contracts.enums import CoverageTarget
from agriautolab.contracts.preference import MetricPreference, PreferenceSpec


def _ref(path_length: float = 10.0, headland_turns: float = 10.0, row_crossings: float = 10.0):
    from agriautolab.contracts.protocol import HypervolumeReference

    return HypervolumeReference(
        path_length=path_length, headland_turns=headland_turns, row_crossings=row_crossings,
        basis="test",
    )


def _vec(a: float, b: float, c: float):
    from agriautolab.pareto.front import ObjectiveVector

    return ObjectiveVector(path_length=a, headland_turns=b, row_crossings=c)


def test_single_point_hypervolume_is_box_volume() -> None:
    """真值 9：单点前沿 {(a,b,c)}，参考 (A,B,C) -> 超体积 = (A-a)(B-b)(C-c)。"""
    from agriautolab.pareto.hypervolume import hypervolume

    reference = _ref(path_length=10.0, headland_turns=8.0, row_crossings=5.0)
    value = hypervolume({"cfg": _vec(3.0, 2.0, 1.0)}, reference=reference)
    assert value == pytest.approx(7.0 * 6.0 * 4.0, rel=1e-15)


def test_degenerate_dimension_gives_2d_area_times_thickness() -> None:
    """真值 9b（规格第 2 条验收）：第三维全相等 -> 二维超体积 x 常数厚度。"""
    from agriautolab.pareto.hypervolume import hypervolume

    reference = _ref(path_length=10.0, headland_turns=10.0, row_crossings=2.0)
    points = {"a": _vec(2.0, 6.0, 1.0), "b": _vec(6.0, 2.0, 1.0)}
    # 二维角箱：a 箱 8x4=32，b 箱 4x8=32，重叠 [6,10]x[6,10]=16 -> 并集 48；厚度 = 2-1 = 1
    value = hypervolume(points, reference=reference)
    assert value == pytest.approx(48.0 * 1.0, rel=1e-12)


def test_two_overlapping_boxes_exact_union() -> None:
    """精确并集（非蒙特卡洛的证明）：交叉双箱的超体积可手算。"""
    from agriautolab.pareto.hypervolume import hypervolume

    reference = _ref(10.0, 10.0, 10.0)
    # a=(0,0,0) 与 b=(5,5,5)：箱 [0,10]^3 与 [5,15]^3 越界截掉 -> [5,10]^3
    value = hypervolume({"a": _vec(0.0, 0.0, 0.0), "b": _vec(5.0, 5.0, 5.0)}, reference=reference)
    assert value == pytest.approx(1000.0 + 125.0 - 125.0, rel=1e-12)  # 大箱包含小箱


def test_dominated_point_does_not_change_hypervolume() -> None:
    """真值 10：加入被支配点，超体积不变。"""
    from agriautolab.pareto.hypervolume import hypervolume
    from agriautolab.pareto.front import pareto_front

    reference = _ref(10.0, 10.0, 10.0)
    base = {"a": _vec(2.0, 6.0, 4.0), "b": _vec(6.0, 2.0, 4.0)}
    extended = dict(base)
    extended["dominated"] = _vec(7.0, 7.0, 7.0)   # 被 a 与 b 同时支配
    assert hypervolume(base, reference=reference) == pytest.approx(
        hypervolume(extended, reference=reference), rel=1e-15
    )
    assert pareto_front(extended) == {"a", "b"}


def test_nondominated_point_strictly_increases_hypervolume() -> None:
    """真值 11：加入非支配点，超体积严格增大。"""
    from agriautolab.pareto.hypervolume import hypervolume

    reference = _ref(10.0, 10.0, 10.0)
    base = {"a": _vec(2.0, 6.0, 4.0), "b": _vec(6.0, 2.0, 4.0)}
    extended = dict(base)
    extended["c"] = _vec(4.0, 4.0, 4.5)   # 非支配
    assert hypervolume(extended, reference=reference) > hypervolume(base, reference=reference) + 1e-9


def test_reference_change_changes_hypervolume_and_protocol_hash() -> None:
    """真值 12（规格第 5 条验收）：参考点变化 -> 超体积变化，且协议哈希变化。"""
    from agriautolab.contracts.protocol import BenchmarkProtocol
    from agriautolab.pareto.hypervolume import hypervolume

    points = {"a": _vec(2.0, 6.0, 4.0)}
    first = _ref(10.0, 10.0, 10.0)
    second = _ref(12.0, 10.0, 10.0)
    assert hypervolume(points, reference=first) < hypervolume(points, reference=second)

    protocol_first = BenchmarkProtocol(
        protocol_id="p", coverage_target=CoverageTarget.ORIGINAL_FIELD,
        coverage_threshold=0.0, hypervolume_reference=first, reverse_cost=REVERSE_COST_TEST_SPEC,
    )
    protocol_second = BenchmarkProtocol(
        protocol_id="p", coverage_target=CoverageTarget.ORIGINAL_FIELD,
        coverage_threshold=0.0, hypervolume_reference=second, reverse_cost=REVERSE_COST_TEST_SPEC,
    )
    assert protocol_first.spec_hash() != protocol_second.spec_hash()
    assert protocol_first.spec_hash() == BenchmarkProtocol(
        protocol_id="p", coverage_target=CoverageTarget.ORIGINAL_FIELD,
        coverage_threshold=0.0, hypervolume_reference=first, reverse_cost=REVERSE_COST_TEST_SPEC,
    ).spec_hash()


def test_beyond_reference_is_flagged_not_silently_clipped() -> None:
    from agriautolab.pareto.hypervolume import beyond_reference, evaluate_front

    reference = _ref(10.0, 10.0, 10.0)
    points = {"ok": _vec(2.0, 2.0, 2.0), "beyond": _vec(11.0, 1.0, 1.0)}
    assert beyond_reference(points, reference=reference) == {"beyond"}
    evaluation = evaluate_front(points, reference=reference)
    assert evaluation.beyond_reference == {"beyond"}
    assert evaluation.front == {"ok"}
    assert evaluation.hypervolume == pytest.approx(8.0 * 8.0 * 8.0, rel=1e-12)
    assert len(evaluation.pool_hash) == 64


def test_chebyshev_selects_concave_point_no_weighted_sum_can() -> None:
    """真值 12b（规格 §4.4 验收）：非凸前沿，切比雪夫可选中间点，任何加权和都选不中。"""
    from agriautolab.pareto.scalarize import scalarize

    reference = _ref(1.5, 1.5, 1.5)
    left = _vec(0.2, 1.0, 0.4)
    middle = _vec(0.7, 0.7, 0.4)   # 在两端连线的外侧（远离原点），非凸
    right = _vec(1.0, 0.2, 0.4)

    equal = PreferenceSpec(preferences=(
        MetricPreference(metric_id="path_length", weight=1.0),
        MetricPreference(metric_id="headland_turn_count", weight=1.0),
    ))
    scores = {name: scalarize(v, preference=equal, reference=reference) for name, v in
              (("left", left), ("middle", middle), ("right", right))}
    assert min(scores, key=scores.get) == "middle"

    # 加权和：任何权重都选不中 middle（解析证明：需要 w1<0.6w2 且 w2<0.6w1 同时成立）
    best_seen = set()
    steps = 1001
    for i in range(steps):
        w1 = i / (steps - 1)
        for j in range(steps):
            w2 = j / (steps - 1)
            if w1 == 0.0 and w2 == 0.0:
                continue
            values = {
                "left": w1 * left.path_length + w2 * left.headland_turns,
                "middle": w1 * middle.path_length + w2 * middle.headland_turns,
                "right": w1 * right.path_length + w2 * right.headland_turns,
            }
            best_seen.add(min(values, key=values.get))
    assert best_seen <= {"left", "right"}
    assert "middle" not in best_seen