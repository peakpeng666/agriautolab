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

SOURCE = "def swath_angle_offset_rad(features):\n    return 0.0\n"


def _result_for(prompt: str, *, response: str = SOURCE) -> CompletionResult:
    return CompletionResult(
        model_id="m1", prompt=prompt, response=response,
        temperature=0.2, top_p=0.95, seed=42,
        prompt_tokens=20, completion_tokens=15,
        cost=0.001, latency_ms=200.0, request_id="req-007",
    )


class _EchoClient:
    """Mock client returning matching prompt provenance."""

    def __init__(self, response: str = SOURCE) -> None:
        self._response = response
        self.calls = 0
        self.last_result: CompletionResult | None = None

    def complete(self, prompt: str) -> CompletionResult:
        self.calls += 1
        self.last_result = _result_for(prompt, response=self._response)
        return self.last_result


class _StalePromptClient:
    """Faulty mock client returning stale prompt provenance."""

    def complete(self, prompt: str) -> CompletionResult:
        return _result_for("stale prompt from another call")


def _context() -> ProposalContext:
    return ProposalContext(
        stage=CoverageStage.SWATH, round_index=0, pool_config_ids=("c1",), slot_id="swath_angle",
    )


def test_propose_records_provenance_and_replay_matches_identity() -> None:
    client = _EchoClient()
    proposer = LLMProposer(client=client)
    online = proposer.propose(
        stage=CoverageStage.SWATH, context=_context(), rng=np.random.default_rng(0),
    )
    result = client.last_result
    assert online.provenance is result
    assert online.source_code == result.response
    # Provenance must match the exact sent prompt
    assert result.prompt == proposer.build_prompt(stage=CoverageStage.SWATH, context=_context())
    # identity（三元组）逐位与 replay 相等——provenance 不进 identity
    replay = replay_candidate(0, result)
    assert candidate_identity(online) == candidate_identity(replay)
    assert candidate_identity(replay) == candidate_identity(replay_candidate(0, result))


def test_propose_rejects_completion_for_a_different_prompt() -> None:
    """Proposer rejects completion when prompt provenance mismatches."""
    proposer = LLMProposer(client=_StalePromptClient())
    with pytest.raises(ValueError, match="does not match"):
        proposer.propose(
            stage=CoverageStage.SWATH, context=_context(), rng=np.random.default_rng(0),
        )


def test_completion_result_is_immutable_after_construction() -> None:
    """provenance 构造后不可改写。

    【证伪力】修复前 CompletionResult 是带 __slots__ 的可写普通类，docstring 却
    声称 frozen。ProposalCandidate 只是浅冻结，而 evolve_pool 在闸门与**注入的
    对抗复核器**跑完之后才序列化 provenance——期间任何持有引用者都能改写字段，
    账本于是为被篡改的元数据背书。
    """
    result = _result_for("p")
    for field, value in (
        ("prompt", "tampered prompt"),
        ("response", "改写的 response"),
        ("cost", 999.0),
        ("model_id", "另一个模型"),
    ):
        with pytest.raises(AttributeError, match="构造后不可变"):
            setattr(result, field, value)
    with pytest.raises(AttributeError, match="构造后不可变"):
        del result.request_id
    # 原值未受影响
    assert result.prompt == "p"
    assert result.model_id == "m1"


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
    ledger.append(_record_with_provenance(0, "x", result))
    ledger.append(_record_with_provenance(1, "y", None))
    ledger.verify()  # 不抛即通过


def test_ledger_provenance_mirrors_completion_validation() -> None:
    """账本里的 ProvenanceRecord 必须与 CompletionResult 同样严格。

    【证伪力】不加约束时，直接构造或从 JSON 还原的记录可以携带 top_p=1.5、
    负 token 数、负成本——`append()` 照样对这些有限值算哈希、`verify()` 照样通过，
    证据链于是为一份违反公开 completion 契约、无法重建成合法 `CompletionResult`
    的 provenance 背书。
    """
    from pydantic import ValidationError

    from agriautolab.agent.ledger import ProvenanceRecord

    base = _result_for("p").to_dict()
    for field, bad in (
        ("top_p", 1.5),
        ("temperature", -0.1),
        ("prompt_tokens", -1),
        ("completion_tokens", -3),
        ("cost", -0.01),
        ("latency_ms", -1.0),
        ("model_id", ""),
        ("request_id", ""),
        ("cost", float("inf")),
    ):
        with pytest.raises(ValidationError):
            ProvenanceRecord(**{**base, field: bad})

    assert ProvenanceRecord(**base).top_p == base["top_p"]


def test_ledger_provenance_cannot_be_mutated_through_records() -> None:
    """账本里的 provenance 深度不可变——嵌套赋值不能悄悄破坏 entry hash。

    【证伪力】修复前 provenance 是普通 dict，而 pydantic 的 frozen=True 只禁止
    属性赋值、不阻止嵌套容器被改。调用方拿到 ledger.records 后写
    record.provenance["prompt"] = ... 就能改掉已经参与 entry hash 计算的内容，
    于是账本在寻常嵌套赋值之后**自发 verify() 失败**——与同一条记录里
    tuple / 冻结模型字段的行为不一致。
    """
    ledger = EvolutionLedger()
    result = _result_for("p")
    ledger.append(_record_with_provenance(0, "x", result))
    ledger.verify()

    record = ledger.records[0]
    with pytest.raises((TypeError, ValueError, AttributeError)):
        record.provenance.prompt = "tampered prompt"
    with pytest.raises(TypeError):
        record.provenance["prompt"] = "tampered prompt"   # 不再是 dict

    assert record.provenance.prompt == "p"
    ledger.verify()   # 仍然自洽


def test_provenance_must_match_the_candidate_source() -> None:
    """入账前必须校验 provenance.response 与候选源码一致。

    【证伪力】`HeuristicProposer` 是公开协议，任何注入实现都能构造
    `ProposalCandidate`。此前 `evolve.py` 直接把 provenance 投影入账、不校验关系，
    于是账本会为「一段没有产生该候选的模型响应」背书，而 `replay_candidate`
    由那份 response 重建出的 proposal hash 与实际被评估的候选不一致。
    """
    from agriautolab.agent.evolve import _provenance_record
    from agriautolab.agent.proposer import ProposalCandidate

    from agriautolab.agent.proposer import replay_candidate

    # 与 replay_candidate 逐字一致的候选：通过
    good = replay_candidate(0, _result_for("p", response=SOURCE))
    assert _provenance_record(good, 0) is not None

    # 源码不符：拒
    mismatched = ProposalCandidate(
        algorithm_id=good.algorithm_id, source_code=SOURCE, description=good.description,
        provenance=_result_for("p", response="def swath_angle_offset_rad(f):\n    return 1.0\n"),
    )
    with pytest.raises(ValueError, match="重放身份不一致"):
        _provenance_record(mismatched, 0)

    # 源码相符、但 algorithm_id 自定义：仍须拒。
    # 【证伪力】只比 source_code 的版本会放行它，而 replay_candidate 把
    # algorithm_id / description 写死成自己的取值，重放出的 candidate_identity
    # 与记录的 proposal_hash 不同——账本与重放对不上。
    custom_id = ProposalCandidate(
        algorithm_id="my_custom_id", source_code=SOURCE, description=good.description,
        provenance=_result_for("p", response=SOURCE),
    )
    with pytest.raises(ValueError, match="重放身份不一致"):
        _provenance_record(custom_id, 0)

    # description 自定义同理
    custom_desc = ProposalCandidate(
        algorithm_id=good.algorithm_id, source_code=SOURCE, description="自定义描述",
        provenance=_result_for("p", response=SOURCE),
    )
    with pytest.raises(ValueError, match="重放身份不一致"):
        _provenance_record(custom_desc, 0)

    # MockProposer 路径：无 provenance 不受影响
    assert _provenance_record(
        ProposalCandidate(algorithm_id="a", source_code=SOURCE, description="d"), 0,
    ) is None


def _record_with_provenance(round_index, algorithm_id, result):
    from agriautolab.agent.ledger import EvolutionRecord, ProvenanceRecord

    provenance = ProvenanceRecord(**result.to_dict()) if result is not None else None
    return EvolutionRecord(
        round_index=round_index,
        algorithm_id=algorithm_id,
        proposal_hash="0" * 64,
        compiled=True,
        gates=(),
        kept=False,
        provenance=provenance,
    )
