"""算法兼容性与指标可比性规则必须在注册那一刻就能强制执行。"""

import pytest

from agriautolab.algorithms.card import AlgorithmCard
from agriautolab.algorithms.registry import AlgorithmRegistry
from agriautolab.contracts.enums import (
    AlgorithmMaturity, AlgorithmSourceType, ComparabilityScope, CoverageStage, MetricRole,
    OptimizationDirection, ProblemKind, ScaleBehavior,
)
from agriautolab.contracts.errors import MetricRegistrationError
from agriautolab.pipeline.metrics.registry import register_metric
from agriautolab.pipeline.metrics.spec import MetricSpec


def test_algorithm_registry_partitions_by_problem_kind() -> None:
    registry = AlgorithmRegistry()
    card = AlgorithmCard(
        algorithm_id="swath-a", name="Swath A", stage=CoverageStage.SWATH,
        supported_problem_kinds=frozenset({ProblemKind.POLYGON_COVERAGE_2D}),
        maturity=AlgorithmMaturity.BASELINE, source_type=AlgorithmSourceType.INTERNAL,
    )
    registry.register(card)
    assert registry.compatible(CoverageStage.SWATH, ProblemKind.POLYGON_COVERAGE_2D) == (card,)
    assert registry.compatible(CoverageStage.SWATH, ProblemKind.GRID_P2P_2D) == ()


@pytest.mark.parametrize("metric_id", ["turn_count", "solution_smoothness", "mean_clearance", "normalized_curvature"])
def test_disabled_metric_registration_fails(metric_id: str) -> None:
    spec = MetricSpec(
        metric_id=metric_id, unit="1", optimization_direction=OptimizationDirection.MINIMIZE,
        comparability_scope=ComparabilityScope.IMPL_INVARIANT, scale_behavior=ScaleBehavior.INVARIANT,
        rotation_invariant=True, role=MetricRole.DIAGNOSTIC,
        applicable_problem_kinds=frozenset({ProblemKind.POLYGON_COVERAGE_2D}), applicable_stage=CoverageStage.PATH,
    )
    with pytest.raises(MetricRegistrationError):
        register_metric(spec)


def test_non_invariant_scope_requires_notes() -> None:
    spec = MetricSpec(
        metric_id="temporary_protocol_metric", unit="1", optimization_direction=OptimizationDirection.MINIMIZE,
        comparability_scope=ComparabilityScope.PROTOCOL_BOUND, scale_behavior=ScaleBehavior.INVARIANT,
        rotation_invariant=True, role=MetricRole.DIAGNOSTIC,
        applicable_problem_kinds=frozenset({ProblemKind.POLYGON_COVERAGE_2D}), applicable_stage=CoverageStage.PATH,
    )
    with pytest.raises(MetricRegistrationError):
        register_metric(spec)


def test_primary_metric_set_is_exactly_two() -> None:
    from agriautolab.contracts.enums import MetricRole
    from agriautolab.pipeline.metrics.registry import METRIC_REGISTRY
    primary = {metric_id for metric_id, spec in METRIC_REGISTRY.items() if spec.role is MetricRole.PRIMARY}
    assert primary == {"overlap_ratio", "nonwork_normalized"}
