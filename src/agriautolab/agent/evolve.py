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
from typing import Callable, Mapping, Sequence

import numpy as np

from agriautolab.agent.gates import (
    GateOutcome, contract_gate, determinism_gate, invariance_gate, validation_gate,
)
from agriautolab.agent.ledger import (
    EvolutionLedger, EvolutionRecord, GateRecord, ProvenanceRecord,
)
from agriautolab.agent.proposer import ProposalContext, ProposalCandidate, replay_candidate
from agriautolab.agent.reviewer import AdversarialReviewer, final_refuted
from agriautolab.agent.slots import DEFAULT_SLOT_ID, SLOTS, CandidateSlot
from agriautolab.contracts.problem import CoverageProblem
from agriautolab.contracts.protocol import BenchmarkProtocol
from agriautolab.contracts.vehicle import VehicleSpec
from agriautolab.pipeline.hashing import content_hash
from agriautolab.pipeline.pareto.front import ObjectiveVector
from agriautolab.pipeline.pareto.hypervolume import evaluate_front
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
                 protocol: BenchmarkProtocol, memo: StageMemo,
                 *, run: Callable = run_pipeline) -> list[dict[str, ObjectiveVector]]:
    outputs = []
    for instance in instances:
        points: dict[str, ObjectiveVector] = {}
        for config in pool:
            result = run(instance.problem, instance.vehicle, config, protocol, memo=memo)
            if result.objectives is not None:
                points[result.config_id] = result.objectives
        outputs.append(points)
    return outputs


def _provenance_record(candidate: ProposalCandidate, round_index: int) -> ProvenanceRecord | None:
    """把候选的 provenance 投影成入账模型，并校验**重放身份**确实成立。

    `LLMProposer` 自己会校验后端返回的 prompt，但 `HeuristicProposer` 是公开协议，
    任何注入实现都能构造 `ProposalCandidate`。若不在入账处再校验一次，账本就会
    为「一段重放不出该候选的 provenance」背书，而由那份 provenance 重放出的候选
    与实际被评估的不是同一个——证据链断在最关键的一环。

    校验口径是**完整 identity**，不是只比 `source_code`：`replay_candidate` 会把
    `algorithm_id` 与 `description` 写死成它自己的取值，因此一个源码相同、但
    `algorithm_id` 或 `description` 自定义的候选（公开协议允许）能通过单比源码的
    检查，重放出的 `candidate_identity` 却与记录的 `proposal_hash` 不同。
    直接比 identity 一次覆盖三元组全部字段。
    """
    if candidate.provenance is None:
        return None

    replayed = replay_candidate(round_index, candidate.provenance)
    if candidate_identity(replayed) != candidate_identity(candidate):
        raise ValueError(
            "候选与其 provenance 的重放身份不一致："
            f"request_id={candidate.provenance.request_id!r}，"
            f"algorithm_id={candidate.algorithm_id!r} vs 重放 {replayed.algorithm_id!r}，"
            f"source_code {len(candidate.source_code)} 字符 vs response "
            f"{len(candidate.provenance.response)} 字符；"
            "账本不能为一段重放不出该候选的 provenance 背书"
        )
    return ProvenanceRecord(**candidate.provenance.to_dict())


def _candidate_points(function, instances: Sequence[Instance],
                      protocol: BenchmarkProtocol, slot: CandidateSlot,
                      *, run: Callable = run_pipeline) -> list[ObjectiveVector | None]:
    """逐实例评估候选；**任一实例失败记 None，不抛出**。

    四道闸只在单个探针实例上跑（按 problem_id 稳定选取），因此候选完全可能在探针
    上成功、在后面某个实例上抛异常——例如某个与距离相关的分母恰好为 0，或该实例
    的几何让 build_config 走进 ConstructionError。此前这里是无保护的列表推导，
    异常会穿过 evolve_pool 并**在写账本记录之前终止整个实验**。

    记 None 即可：hypervolume_delta 对任一 None 返回 -inf，候选因此不晋升，
    而账本仍如实记下这一轮——「被淘汰」是结果，不是崩溃。
    """
    points: list[ObjectiveVector | None] = []
    for instance in instances:
        try:
            config = slot.build_config(function, instance.problem, instance.vehicle)
            points.append(run(instance.problem, instance.vehicle, config, protocol).objectives)
        except Exception:  # noqa: BLE001 -- 插件边界：候选在某实例上的失败=该实例无目标
            points.append(None)
    return points


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
    slot: str = DEFAULT_SLOT_ID,
    reviewers: tuple[AdversarialReviewer, ...] | None = None,
) -> tuple[EvolutionLedger, tuple[KeptCandidate, ...]]:
    """演化循环主体。返回（账本, 保留候选）。失败候选照记账——只记成功就是发表偏倚。

    slot 是槽位 id（SLOTS 注册表的键）：闸门语义、复核器集与提示词模板都按它
    分派；未登记的 id 当场 ValueError（fail-closed），不静默回退默认槽位。
    reviewers 缺省用槽位自带的复核器集，显式传参可覆盖。
    """
    if rounds <= 0:
        raise ValueError("rounds must be positive")
    if not instances:
        raise ValueError("instances 不能为空")
    if slot not in SLOTS:
        raise ValueError(f"未知候选槽位 id：{slot!r}（已登记：{tuple(sorted(SLOTS))}）")
    candidate_slot = SLOTS[slot]
    if candidate_slot.slot_id != slot:
        raise ValueError(
            f"槽位注册键 {slot!r} 与 slot_id {candidate_slot.slot_id!r} 不一致："
            "注册键即 wire ID，两者需相同，否则实验归因错位"
        )
    # 三表齐全性：proposer 的 PROMPT_TEMPLATES 与 MOCK_CANDIDATES_BY_SLOT 也需
    # 登记该 slot，否则 LLM/Mock 提议者会在轮循环内 KeyError 静默炸（不在
    # 闸门 try/except 范围内）。在进入轮循环之前 fail-closed 是为让错误立即
    # 可见，不污染账本。
    from agriautolab.agent.proposer import MOCK_CANDIDATES_BY_SLOT, PROMPT_TEMPLATES

    if slot not in PROMPT_TEMPLATES:
        raise ValueError(
            f"槽位 {slot!r} 缺 PROMPT_TEMPLATES 登记：LLM 提议将 KeyError。"
            f"已登记键：{tuple(sorted(PROMPT_TEMPLATES))}"
        )
    if slot not in MOCK_CANDIDATES_BY_SLOT:
        raise ValueError(
            f"槽位 {slot!r} 缺 MOCK_CANDIDATES_BY_SLOT 登记：Mock 提议将 KeyError。"
            f"已登记键：{tuple(sorted(MOCK_CANDIDATES_BY_SLOT))}"
        )
    # 协议完整性：八成员都存在。前四个是数据（slot_id/stage/contract_function/
    # reviewers），后四个是方法（compile/probe_value/build_config/invariance_check）。
    # 缺 build_config / invariance_check 等会被闸门 try/except 静默吞——
    # 这是 fail-closed 需前置的原因。
    _data_members = ("slot_id", "stage", "contract_function", "reviewers")
    _method_members = ("compile", "probe_value", "build_config", "invariance_check")
    missing: list[str] = []
    for name in _data_members:
        if not hasattr(candidate_slot, name):
            missing.append(name)
    for name in _method_members:
        attr = getattr(candidate_slot, name, None)
        if attr is None or not callable(attr):
            missing.append(name)
    if missing:
        raise ValueError(
            f"槽位 {slot!r} 协议缺成员：{missing}。"
            "缺 build_config / invariance_check 等会被闸门 try/except 静默吞，"
            "需在 evolve_pool 进入轮循环前 fail-closed。"
        )
    active_reviewers = candidate_slot.reviewers if reviewers is None else reviewers
    ledger = EvolutionLedger()
    memo = StageMemo()
    # 评估计数器：所有 run_pipeline 调用经 counted_run 转发，含基线池一次性消耗、
    # 三道闸门（contract 闸不计入）与候选逐实例评估。计数器是「真实评估次数」的唯一
    # 来源，不得用 round_index 或任何公式近似。
    counter = {"n": 0}

    def counted_run(*args, **kwargs):
        counter["n"] += 1
        return run_pipeline(*args, **kwargs)

    pool_points = _pool_points(instances, base_pool, protocol, memo, run=counted_run)
    # RNG 流按（主种子, 轮, 组件）派生：修改验证/复核的随机消耗不再移动提议流，
    # 否则只是加强检查就会改变整条搜索轨迹。
    master_seed = int(rng.integers(0, 2**63))
    # 已保留候选的逐实例目标向量并入池（后续候选的增量相对「基础池 + 已保留」计算）
    kept_extra: dict[str, list[ObjectiveVector | None]] = {}
    kept: list[KeptCandidate] = []
    # running best：迄今各轮 hypervolume_delta 非 None 值的 max，单调不减；
    # 唯一值是 -inf 时保持 -inf，单调性仍成立。
    best_delta: float | None = None

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
            gates.append(validation_gate(function, probe.problem, probe.vehicle, protocol, slot=candidate_slot, run=counted_run))
            gates.append(determinism_gate(function, probe.problem, probe.vehicle, protocol, slot=candidate_slot, run=counted_run))
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
                objectives = _candidate_points(function, instances, protocol, candidate_slot, run=counted_run)
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

        if delta is not None:
            best_delta = delta if best_delta is None else max(best_delta, delta)

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
            evaluations_used=counter["n"],
            cumulative_best_delta=best_delta,
            provenance=_provenance_record(candidate, round_index),
        ))
    ledger.verify()
    return ledger, tuple(kept)
