"""Metric specification and metadata declarations."""

from __future__ import annotations

from dataclasses import dataclass, field

from agriautolab.contracts.enums import (
    ComparabilityScope,
    CoverageStage,
    MetricRole,
    OptimizationDirection,
    ProblemKind,
    ScaleBehavior,
)


@dataclass(frozen=True)
class MetricSpec:
    metric_id: str
    unit: str
    optimization_direction: OptimizationDirection
    comparability_scope: ComparabilityScope
    scale_behavior: ScaleBehavior
    rotation_invariant: bool
    role: MetricRole
    applicable_problem_kinds: frozenset[ProblemKind]
    applicable_stage: CoverageStage | None
    protocol_parameters: dict[str, float | int | str] = field(default_factory=dict)
    aggregation_method: str = "arithmetic_mean"
    description: str = ""
    notes: str = ""
    # Canonical name alias; defaults to metric_id if None.
    canonical_name: str | None = None

    @property
    def canonical(self) -> str:
        return self.canonical_name or self.metric_id
