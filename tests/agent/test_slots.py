"""候选槽位抽象真值：SLOTS 注册表、默认槽位等价性与黄金 config_id 钉住。

真值标准（docs/OPTIMIZATION_FOUNDATIONS.md §4：断言必须在旧实现下失败）：
旧的硬编码单槽位实现没有 slots 模块、闸门没有 slot 参数、evolve_pool 没有
slot 关键字、账本没有 slot_id 字段——下面的注册表/分派/fail-closed 断言
在那个实现下全部无法通过。

黄金 config_id 取自重构前基线（main=9339d885）实测输出：

    candidate_config(0.5)            -> 438007502ee9011574741cde803be125aabf61f05c24ec7078a6bd952de4003f
    candidate_config(math.pi / 6.0)  -> ee57b34caaafa4498cb89f687d25982955cbe29bb22ef786953f157eda03eba0

gate-reference 田（60x40 矩形）的 PCA 主轴角恰为浮点精确的 0.0，因此固定
偏移 mock 经 SLOTS["swath_angle"].build_config 生成的配置与 candidate_config(offset)
逐位相同——config_id 对浮点 ULP 敏感，这一钉住同时约束了迁移代码的数值路径。
"""

import json
import math

import numpy as np
import pytest

from agriautolab.agent.evolve import KeepRule, evolve_pool
from agriautolab.agent.gates import (
    candidate_config, compile_candidate, contract_gate, determinism_gate, invariance_gate,
    principal_angle_of, validation_gate,
)
from agriautolab.agent.ledger import EvolutionRecord
from agriautolab.agent.proposer import (
    MOCK_CANDIDATES, MOCK_CANDIDATES_BY_SLOT, PROMPT_TEMPLATE, PROMPT_TEMPLATES,
    LLMProposer, MockProposer, ProposalContext,
)
from agriautolab.agent.reviewer import DEFAULT_REVIEWERS
from agriautolab.agent.slots import (
    DEFAULT_SLOT_ID, SLOTS, CandidateSlot, SwathAngleSlot, reference_problem, reference_vehicle,
)
from agriautolab.contracts.enums import CoverageStage

from tests.agent.test_agent import base_pool, make_instance, make_protocol

GOLDEN_CONFIG_ID_OFFSET_HALF = "438007502ee9011574741cde803be125aabf61f05c24ec7078a6bd952de4003f"
GOLDEN_CONFIG_ID_OFFSET_PI_OVER_6 = "ee57b34caaafa4498cb89f687d25982955cbe29bb22ef786953f157eda03eba0"


def test_slots_registry_exposes_swath_angle_as_default() -> None:
    # 旧实现没有注册表：单槽位硬编码在 gates 里，无从谈起 SLOTS/DEFAULT_SLOT_ID。
    assert DEFAULT_SLOT_ID == "swath_angle"
    assert set(SLOTS) == {"swath_angle"}
    slot = SLOTS[DEFAULT_SLOT_ID]
    assert isinstance(slot, SwathAngleSlot)
    assert isinstance(slot, CandidateSlot)  # 协议结构检查（runtime_checkable）
    assert slot.slot_id == "swath_angle"
    assert slot.stage is CoverageStage.SWATH
    assert slot.contract_function == "swath_angle_offset_rad"
    assert slot.reviewers == DEFAULT_REVIEWERS


def test_slot_registries_stay_in_sync() -> None:
    # 三张按槽位分派的表必须同键：SLOTS（闸门/演化语义）、MOCK_CANDIDATES_BY_SLOT
    # 与 PROMPT_TEMPLATES（proposer 分派表）。新增槽位漏登记任何一张时，报错点
    # 前移到这里，而不是等到 evolve_pool 的 ValueError 或 propose/build_prompt 的 KeyError。
    assert set(SLOTS) == set(MOCK_CANDIDATES_BY_SLOT) == set(PROMPT_TEMPLATES)


def test_golden_config_ids_pinned_through_slot_build_config() -> None:
    # gate-reference 田主轴角恰为 0.0（浮点精确），固定偏移 mock 的 build_config
    # 与 candidate_config(offset) 逐位同构；黄金值来自重构前基线实测。
    assert principal_angle_of(reference_problem(), reference_vehicle()) == 0.0
    slot = SLOTS["swath_angle"]
    half = slot.build_config(lambda features: 0.5, reference_problem(), reference_vehicle())
    sixth = slot.build_config(lambda features: math.pi / 6.0, reference_problem(), reference_vehicle())
    assert half.config_id() == GOLDEN_CONFIG_ID_OFFSET_HALF
    assert sixth.config_id() == GOLDEN_CONFIG_ID_OFFSET_PI_OVER_6
    # gates 的兼容入口与槽位实现同源：同输入必须同 config_id
    assert candidate_config(0.5).config_id() == GOLDEN_CONFIG_ID_OFFSET_HALF
    assert candidate_config(math.pi / 6.0).config_id() == GOLDEN_CONFIG_ID_OFFSET_PI_OVER_6


def test_gates_default_slot_equals_explicit_swath_slot() -> None:
    # 不传 slot（旧调用点形态）与显式传 SLOTS["swath_angle"] 必须逐位等价。
    instance = make_instance()
    protocol = make_protocol(instance)
    slot = SLOTS["swath_angle"]
    source = MOCK_CANDIDATES[2].source_code

    default_fn, default_outcome = contract_gate(source)
    explicit_fn, explicit_outcome = contract_gate(source, slot=slot)
    assert default_outcome == explicit_outcome
    assert default_fn is not None and explicit_fn is not None
    assert default_fn({"elongation": 2.0}) == explicit_fn({"elongation": 2.0})
    assert compile_candidate(source)({"elongation": 2.0}) == default_fn({"elongation": 2.0})

    assert validation_gate(default_fn, instance.problem, instance.vehicle, protocol) == \
        validation_gate(default_fn, instance.problem, instance.vehicle, protocol, slot=slot)
    assert determinism_gate(default_fn, instance.problem, instance.vehicle, protocol) == \
        determinism_gate(default_fn, instance.problem, instance.vehicle, protocol, slot=slot)
    assert invariance_gate(default_fn, instance.problem, instance.vehicle, protocol,
                           np.random.default_rng(7)) == \
        invariance_gate(default_fn, instance.problem, instance.vehicle, protocol,
                        np.random.default_rng(7), slot=slot)


def test_evolve_pool_default_equals_explicit_slot() -> None:
    instance = make_instance()
    protocol = make_protocol(instance)

    def run(**slot_kwargs) -> tuple[str, tuple[str, ...]]:
        ledger, kept = evolve_pool(
            base_pool(), (instance,), proposer=MockProposer(), protocol=protocol,
            rng=np.random.default_rng(42), rounds=4, keep_rule=KeepRule.HYPERVOLUME_DELTA,
            **slot_kwargs,
        )
        return "|".join(record.model_dump_json() for record in ledger.records), tuple(k.identity for k in kept)

    default_ledger, default_kept = run()
    explicit_ledger, explicit_kept = run(slot="swath_angle")
    assert default_ledger == explicit_ledger
    assert default_kept == explicit_kept
    # 账本逐条携带槽位身份（旧 EvolutionRecord 无此字段）
    for chunk in explicit_ledger.split("|"):
        assert json.loads(chunk)["slot_id"] == "swath_angle"


def test_evolve_pool_rejects_unknown_slot_id() -> None:
    # fail-closed：未登记的槽位 id 当场 ValueError，不静默回退默认槽位。
    instance = make_instance()
    protocol = make_protocol(instance)
    with pytest.raises(ValueError, match="route_angle"):
        evolve_pool(
            base_pool(), (instance,), proposer=MockProposer(), protocol=protocol,
            rng=np.random.default_rng(0), rounds=1, slot="route_angle",
        )


def test_proposer_dispatches_prompt_and_mocks_by_slot_id() -> None:
    # 提示词模板按槽位登记：单槽位时代的公开名 PROMPT_TEMPLATE 是其中一个值。
    assert set(PROMPT_TEMPLATES) == {"swath_angle"}
    assert PROMPT_TEMPLATE == PROMPT_TEMPLATES["swath_angle"]

    context = ProposalContext(stage=CoverageStage.SWATH, round_index=0, pool_config_ids=(),
                              slot_id="swath_angle")
    default_context = ProposalContext(stage=CoverageStage.SWATH, round_index=0, pool_config_ids=())
    assert default_context.slot_id == "swath_angle"  # 旧构造零改动，缺省即 swath
    prompt = LLMProposer().build_prompt(stage=CoverageStage.SWATH, context=context)
    assert "swath_angle_offset_rad" in prompt
    assert prompt == LLMProposer().build_prompt(stage=CoverageStage.SWATH, context=default_context)

    # MockProposer 按 slot_id 分派到候选清单，且恰好消耗 1 次 rng.integers
    candidate = MockProposer().propose(stage=CoverageStage.SWATH, context=default_context,
                                       rng=np.random.default_rng(3))
    reference_rng = np.random.default_rng(3)
    expected = MOCK_CANDIDATES[int(reference_rng.integers(0, len(MOCK_CANDIDATES)))]
    assert candidate is expected

    # 未知 slot_id：mock 与提示词都 fail-closed（KeyError），不静默回退
    unknown = ProposalContext(stage=CoverageStage.SWATH, round_index=0, pool_config_ids=(),
                              slot_id="route_angle")
    with pytest.raises(KeyError):
        MockProposer().propose(stage=CoverageStage.SWATH, context=unknown, rng=np.random.default_rng(0))
    with pytest.raises(KeyError):
        LLMProposer().build_prompt(stage=CoverageStage.SWATH, context=unknown)


class _RecordingRng:
    """记录型 rng 包装：把 uniform(low, high) 的调用参数与返回值按序记下。

    只代理 uniform——被测路径若改经其他 rng 方法消耗随机数，这里直接
    AttributeError，本身即「只能经 uniform 消耗」的一条约束。
    """

    def __init__(self, rng):
        self._rng = rng
        self.calls: list[tuple[float, float, float]] = []   # (low, high, value)

    def uniform(self, low, high):
        value = self._rng.uniform(low, high)
        self.calls.append((low, high, value))
        return value


def test_invariance_consumes_exactly_three_uniforms_per_group() -> None:
    # 不变性检查的 RNG 消耗是行为契约：8 组 × 每组恰 3 次 uniform，顺序
    # theta/tx/ty、范围 (-pi, pi) 与 (-100, 100)x2。记录型包装与同 seed 参考
    # 序列逐项比对——调用次数、每次 (low, high)（顺序+范围）与返回值同时钉住：
    # 交换 theta/tx、篡改范围或增删一次调用都会让元组序列先失配。
    slot = SLOTS["swath_angle"]
    problem, vehicle = reference_problem(), reference_vehicle()
    function = slot.compile(MOCK_CANDIDATES[0].source_code)

    recorded = _RecordingRng(np.random.default_rng(11))
    outcome = slot.invariance_check(function, problem, vehicle, recorded)
    assert outcome.passed

    reference = np.random.default_rng(11)
    expected_calls = [
        (low, high, reference.uniform(low, high))
        for _ in range(8)
        for low, high in ((-math.pi, math.pi), (-100.0, 100.0), (-100.0, 100.0))
    ]
    assert recorded.calls == expected_calls


def test_ledger_records_slot_id() -> None:
    record = EvolutionRecord(round_index=0, algorithm_id="x", proposal_hash="0" * 64,
                             compiled=True, kept=False)
    assert record.slot_id == "swath_angle"  # 默认槽位身份（旧记录无此字段）
    assert record.model_dump()["slot_id"] == "swath_angle"
