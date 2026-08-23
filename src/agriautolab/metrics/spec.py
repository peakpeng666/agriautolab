"""先声明一个指标能怎么比，它的数值才允许进入排名。"""

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
    # 规范名（API/论文层）；None 时规范名即 metric_id。证据身份永远是 metric_id。
    canonical_name: str | None = None

    @property
    def canonical(self) -> str:
        return self.canonical_name or self.metric_id
