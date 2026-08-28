"""canonical_name 查重需在非空注册表上执行（顺序回归）。"""

from agriautolab.pipeline.metrics.registry import METRIC_REGISTRY, _check_canonical_uniqueness, register_metric
from agriautolab.pipeline.metrics.spec import MetricSpec
from agriautolab.contracts.enums import ComparabilityScope, OptimizationDirection, ScaleBehavior, MetricRole, ProblemKind
from agriautolab.contracts.enums import CoverageStage


def test_uniqueness_check_runs_on_populated_registry():
    assert len(METRIC_REGISTRY) > 0  # 默认指标已装
    _check_canonical_uniqueness()  # 不抛


def test_duplicate_canonical_name_is_rejected():
    spec = MetricSpec("dup_canon_test", "1", OptimizationDirection.MINIMIZE,
                      ComparabilityScope.IMPL_INVARIANT, ScaleBehavior.INVARIANT, True,
                      MetricRole.DIAGNOSTIC, frozenset({ProblemKind.POLYGON_COVERAGE_2D}),
                      CoverageStage.PATH, canonical_name="path_length")
    register_metric(spec)  # metric_id 唯一，注册本身通过
    try:
        import pytest
        with pytest.raises(Exception):
            _check_canonical_uniqueness()
    finally:
        del METRIC_REGISTRY["dup_canon_test"]
