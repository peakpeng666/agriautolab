"""任务 4（M3 C）真值测试：LLM provenance 入账与重放校验。

覆盖：CompletionResult fail-closed 校验、LLMProposer.propose 注入 client 后的
provenance 字段、replay_candidate 与在线候选 identity 逐位相等、MockProposer
与 evolve_pool 组合时 record.provenance 为 None、ledger.verify 不抛。
"""

from __future__ import annotations

import numpy as np
import pytest

from agriautolab.agent.evolve import candidate_identity, evolve_pool
from agriautolab.agent.ledger import EvolutionLedger
from agriautolab.agent.proposer import (
    CompletionResult, LLMProposer, MockProposer, ProposalContext,
    replay_candidate,
)
from agriautolab.contracts.enums import CoverageStage

from tests.agent.test_agent import base_pool, make_instance, make_protocol


# ---- a. CompletionResult fail-closed ----

def test_completion_result_rejects_empty_model_id() -> None:
    with pytest.raises(ValueError, match="model_id"):
        CompletionResult(
            model_id="", prompt="p", response="r",
            temperature=0.2, top_p=0.95, seed=0,
            prompt_tokens=1, completion_tokens=1,
            cost=0.0, latency_ms=10.0, request_id="req-1",
        )


def test_completion_result_rejects_negative_cost() -> None:
    with pytest.raises(ValueError, match="cost"):
        CompletionResult(
            model_id="m", prompt="p", response="r",
            temperature=0.2, top_p=0.95, seed=0,
            prompt_tokens=1, completion_tokens=1,
            cost=-0.01, latency_ms=10.0, request_id="req-1",
        )


def test_completion_result_rejects_out_of_range_top_p() -> None:
    with pytest.raises(ValueError, match="top_p"):
        CompletionResult(
            model_id="m", prompt="p", response="r",
            temperature=0.2, top_p=1.5, seed=0,
            prompt_tokens=1, completion_tokens=1,
            cost=0.0, latency_ms=10.0, request_id="req-1",
        )


# ---- b. propose + replay identity 一致 ----

class _FakeClient:
    """假模型后端：每次 complete 返回固定 CompletionResult。"""

    def __init__(self, result: CompletionResult) -> None:
        self._result = result
        self.calls = 0

    def complete(self, prompt: str) -> CompletionResult:
        self.calls += 1
        return self._result


def test_propose_records_provenance_and_replay_matches_identity() -> None:
    result = CompletionResult(
        model_id="m1", prompt="PROMPT", response=(
            "def swath_angle_offset_rad(features):\n    return 0.0\n"
        ),
        temperature=0.2, top_p=0.95, seed=42,
        prompt_tokens=20, completion_tokens=15,
        cost=0.001, latency_ms=200.0, request_id="req-007",
    )
    proposer = LLMProposer(client=_FakeClient(result))
    context = ProposalContext(
        stage=CoverageStage.SWATH, round_index=0, pool_config_ids=("c1",), slot_id="swath_angle",
    )
    rng = np.random.default_rng(0)

    online = proposer.propose(stage=CoverageStage.SWATH, context=context, rng=rng)
    assert online.provenance is result
    assert online.source_code == result.response  # 源码来自 response
    # identity（三元组）逐位与 replay 相等——provenance 不进 identity
    replay = replay_candidate(0, result)
    assert candidate_identity(online) == candidate_identity(replay)
    # 重放确定性：两次 replay 同一 result identity 逐位相同
    assert candidate_identity(replay) == candidate_identity(replay_candidate(0, result))


# ---- c. MockProposer + evolve_pool → record.provenance 全 None ----

def test_evolve_pool_with_mock_proposer_records_no_provenance() -> None:
    instance = make_instance()
    protocol = make_protocol(instance)
    ledger, _ = evolve_pool(
        base_pool(), (instance,),
        proposer=MockProposer(),
        protocol=protocol,
        rng=np.random.default_rng(0),
        rounds=3,
    )
    assert len(ledger.records) == 3
    for record in ledger.records:
        assert record.provenance is None


# ---- d. 带 provenance 的记录 ledger.verify 不抛 ----

def test_ledger_verify_passes_with_provenance_records() -> None:
    ledger = EvolutionLedger()
    result = CompletionResult(
        model_id="m1", prompt="p", response="r",
        temperature=0.2, top_p=0.95, seed=0,
        prompt_tokens=1, completion_tokens=1,
        cost=0.0, latency_ms=0.0, request_id="req-1",
    )
    ledger.append(_record_with_provenance(0, "x", result.to_dict()))
    ledger.append(_record_with_provenance(1, "y", None))
    ledger.verify()  # 不抛即通过


def _record_with_provenance(round_index, algorithm_id, provenance):
    from agriautolab.agent.ledger import EvolutionRecord
    return EvolutionRecord(
        round_index=round_index,
        algorithm_id=algorithm_id,
        proposal_hash="0" * 64,
        compiled=True,
        gates=(),
        kept=False,
        provenance=provenance,
    )
