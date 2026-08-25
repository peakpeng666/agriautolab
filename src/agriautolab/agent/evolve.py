"""演化循环：提议 -> 编译 -> 四道闸 -> 评估 -> 超体积增量 -> 保留/淘汰 -> 记账。

适应度 = 新算法把 Pareto 前沿撑大了多少（HV(pool ∪ {c}) − HV(pool)，按实例取均值），
不是平均代价。这是 EoH-S（arXiv 2508.03082）的 Complementary Performance Index
在多目标下的对应物。用平均代价做适应度会选出「整体最好」的算法，而整体最好的
算法恰恰不增加互补性——240 实例实测的嵌套支配现象（VBS−SBS gap 0.0299）就是这么来的。

保留的候选以 ProposalCandidate 本身留在结果里，而不是伪装成静态 PipelineConfig：
候选的角度是逐实例由特征导出的，静态配置表达不了这一点，
把哈希塞进参数表只会制造同 id 的假身份。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Sequence

import numpy as np

from agriautolab.agent.gates import (
    GateOutcome, contract_gate, determinism_gate, invariance_gate, validation_gate,
)
from agriautolab.agent.ledger import EvolutionLedger, EvolutionRecord, GateRecord
from agriautolab.agent.proposer import ProposalContext, ProposalCandidate
from agriautolab.agent.reviewer import AdversarialReviewer, final_refuted
from agriautolab.agent.slots import SLOTS, CandidateSlot
from agriautolab.contracts.problem import CoverageProblem
from agriautolab.contracts.protocol import BenchmarkProtocol
from agriautolab.contracts.vehicle import VehicleSpec
from agriautolab.evidence.hashing import content_hash
from agriautolab.pareto.front import ObjectiveVector
from agriautolab.pareto.hypervolume import evaluate_front
from agriautolab.pipeline.config import PipelineConfig
from agriautolab.pipeline.run import StageMemo, run_pipeline


class KeepRule(Enum):
    """保留规则只有一个：超体积增量为正。平均代价规则已被实测否证（见模块 docstring）。"""

    HYPERVOLUME_DELTA = "hypervolume_delta"


@dataclass(frozen=True)
class Instance:
    problem: CoverageProblem
    vehicle: VehicleSpec


@dataclass(frozen=True)
class KeptCandidate:
    """通过全部闸门且增量为正的候选：源码 + 身份哈希 + 逐实例目标向量。"""

    candidate: ProposalCandidate
    identity: str
    objectives: tuple[ObjectiveVector | None, ...]


def candidate_identity(candidate: ProposalCandidate) -> str:
    return content_hash({
        "algorithm_id": candidate.algorithm_id,
        "source_code": candidate.source_code,
        "description": candidate.description,
    })


def _pool_points(instances: Sequence[Instance], pool: Sequence[PipelineConfig],
                 protocol: BenchmarkProtocol, memo: StageMemo) -> list[dict[str, ObjectiveVector]]:
    outputs = []
    for instance in instances:
        points: dict[str, ObjectiveVector] = {}
        for config in pool:
            result = run_pipeline(instance.problem, instance.vehicle, config, protocol, memo=memo)
            if result.objectives is not None:
                points[result.config_id] = result.objectives
        outputs.append(points)
    return outputs


def _candidate_points(function, instances: Sequence[Instance],
                      protocol: BenchmarkProtocol, slot: CandidateSlot) -> list[ObjectiveVector | None]:
    return [
        run_pipeline(instance.problem, instance.vehicle,
                     slot.build_config(function, instance.problem, instance.vehicle),
                     protocol).objectives
        for instance in instances
    ]


def hypervolume_delta(objectives_per_instance: Sequence[ObjectiveVector | None],
                      pool_points: Sequence[Mapping[str, ObjectiveVector]],
                      protocol: BenchmarkProtocol) -> float:
    """HV(pool ∪ {candidate}) − HV(pool)，按实例取均值。任一实例不可行 -> -inf。"""
    reference = protocol.hypervolume_reference
    deltas = []
    for objectives, points in zip(objectives_per_instance, pool_points):
        if objectives is None:
            return float("-inf")
        extended = dict(points)
        extended["candidate"] = objectives
        deltas.append(
            evaluate_front(extended, reference=reference).hypervolume
            - evaluate_front(points, reference=reference).hypervolume
        )
    return float(np.mean(deltas))


def evolve_pool(
    base_pool: Sequence[PipelineConfig],
    instances: Sequence[Instance],
    *,
    proposer,
    protocol: BenchmarkProtocol,
    rng: np.random.Generator,
    rounds: int,
    keep_rule: KeepRule = KeepRule.HYPERVOLUME_DELTA,
    slot: str = "swath_angle",
    reviewers: tuple[AdversarialReviewer, ...] | None = None,
) -> tuple[EvolutionLedger, tuple[KeptCandidate, ...]]:
    """演化循环主体。返回（账本, 保留候选）。失败候选照记账——只记成功就是发表偏倚。

    slot 是槽位 id（SLOTS 注册表的键）：闸门语义、复核器集与提示词模板都按它
    分派；未登记的 id 当场 ValueError（fail-closed），不静默回退默认槽位。
    reviewers 缺省用槽位自带的复核器集，显式传参可覆盖。
    """
    if rounds <= 0:
        raise ValueError("rounds 必须为正")
    if not instances:
        raise ValueError("instances 不能为空")
    if slot not in SLOTS:
        raise ValueError(f"未知候选槽位 id：{slot!r}（已登记：{tuple(sorted(SLOTS))}）")
    candidate_slot = SLOTS[slot]
    active_reviewers = candidate_slot.reviewers if reviewers is None else reviewers
    ledger = EvolutionLedger()
    memo = StageMemo()
    pool_points = _pool_points(instances, base_pool, protocol, memo)
    # RNG 流按（主种子, 轮, 组件）派生：修改验证/复核的随机消耗不再移动提议流，
    # 否则只是加强检查就会改变整条搜索轨迹。
    master_seed = int(rng.integers(0, 2**63))
    # 已保留候选的逐实例目标向量并入池（后续候选的增量相对「基础池 + 已保留」计算）
    kept_extra: dict[str, list[ObjectiveVector | None]] = {}
    kept: list[KeptCandidate] = []

    for round_index in range(rounds):
        context = ProposalContext(
            stage=candidate_slot.stage,
            round_index=round_index,
            pool_config_ids=tuple(sorted(
                [config.config_id() for config in base_pool] + list(kept_extra.keys())
            )),
            slot_id=slot,
        )
        proposer_rng = np.random.default_rng([master_seed, round_index, 0])
        gate_rng = np.random.default_rng([master_seed, round_index, 1])
        candidate: ProposalCandidate = proposer.propose(stage=candidate_slot.stage, context=context, rng=proposer_rng)
        identity = candidate_identity(candidate)

        function, contract_outcome = contract_gate(candidate.source_code, slot=candidate_slot)
        gates: list[GateOutcome] = [contract_outcome]
        if function is not None:
            # 探针按 problem_id 稳定选取：候选晋升不得依赖实例的输入顺序
            probe = min(instances, key=lambda item: item.problem.problem_id)
            gates.append(validation_gate(function, probe.problem, probe.vehicle, protocol, slot=candidate_slot))
            gates.append(determinism_gate(function, probe.problem, probe.vehicle, protocol, slot=candidate_slot))
            gates.append(invariance_gate(function, probe.problem, probe.vehicle, protocol, gate_rng, slot=candidate_slot))
        all_passed = all(outcome.passed for outcome in gates)

        review_refuted: bool | None = None
        review_reasons: tuple[str, ...] = ()
        delta: float | None = None
        was_kept = False
        if all_passed and function is not None:
            verdicts = tuple(reviewer.review(candidate, function) for reviewer in active_reviewers)
            review_refuted = final_refuted(verdicts)
            review_reasons = tuple(reason for verdict in verdicts for reason in verdict.reasons)
            if not review_refuted and identity not in kept_extra:
                objectives = _candidate_points(function, instances, protocol, candidate_slot)
                # 基线 = 基础池 + 已保留候选（不含本候选）：ΔHV 度量「加入本候选」
                # 的真实增量。曾把已含本候选的合并池当基线传入，导致恒为 0、
                # 候选永不可能晋升——真值测试已钉住。
                baseline = [
                    dict(points, **{key: values[index] for key, values in kept_extra.items()})
                    for index, points in enumerate(pool_points)
                ]
                delta = hypervolume_delta(objectives, baseline, protocol)
                was_kept = delta > 0.0 if keep_rule is KeepRule.HYPERVOLUME_DELTA else False
                if was_kept:
                    kept_extra[identity] = list(objectives)
                    kept.append(KeptCandidate(candidate=candidate, identity=identity,
                                              objectives=tuple(objectives)))

        ledger.append(EvolutionRecord(
            round_index=round_index,
            algorithm_id=candidate.algorithm_id,
            proposal_hash=identity,
            slot_id=slot,
            compiled=function is not None,
            gates=tuple(GateRecord(gate=o.gate, passed=o.passed, detail=o.detail) for o in gates),
            review_refuted=review_refuted,
            review_reasons=review_reasons,
            hypervolume_delta=delta,
            kept=was_kept,
        ))
    ledger.verify()
    return ledger, tuple(kept)
