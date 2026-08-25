"""任务 1（M3）真值测试：anytime 性能轨迹记录。

口径：COCO/IOHprofiler 式的「评估次数 → 当前最优」轨迹。
- evaluations_used = 记录 append 时刻全程累计真实 run_pipeline 调用数
  （含轮前基线池 I×P、闸门 1+2+0、候选逐实例评估）。
- cumulative_best_delta = 迄今各轮 hypervolume_delta 非 None 值的 running max，单调不减。

与既有 tests/agent/test_agent.py 的 bitwise 复现测试一起构成完整约束：
后者钉「同 seed 跑两次账本逐位相同」，本文件钉「evaluations_used 真实计数
与 best_delta 单调性」——任何用 round_index×常数 近似计数的实现必败。
"""

from __future__ import annotations

import numpy as np

from agriautolab.agent.evolve import evolve_pool
from agriautolab.agent.ledger import EvolutionRecord, anytime_curve
from agriautolab.agent.proposer import ProposalCandidate

from tests.agent.test_agent import base_pool, make_instance, make_protocol


# 候选 A：恒取主轴方向（与 principal_axis 退化等价，零增量）。
_A_SRC = "def swath_angle_offset_rad(features):\n    return 0.0\n"

# 候选 broken：函数名错（应为 swath_angle_offset_rad），contract 闸必拒。
_BROKEN_SRC = "def wrong_name(features):\n    return 0.0\n"


class _DeterministicProposer:
    """按 context.round_index 返回写死候选的提议者（hermetic、确定性）。"""

    def __init__(self, candidates: tuple[ProposalCandidate, ...]) -> None:
        self._candidates = candidates

    def propose(self, *, stage, context, rng) -> ProposalCandidate:
        return self._candidates[context.round_index]


def test_anytime_evaluations_used_matches_hand_derivation() -> None:
    """a. 核心真值：evaluations_used 逐轮精确对账（真实计数，不是公式近似）。

    手算（I=1、P=2、R=3）：

      基线池一次性消耗 I×P = 1×2 = 2
      → eval 累计 = 2

      第 0 轮：候选 A
        contract 通过 → 1（contract 不调 run_pipeline）
        validation 闸 → +1
        determinism 闸 → +2（两次 run）
        invariance 闸 → 0
        _candidate_points → +1
        小计 +4 → eval 累计 = 6
        delta=0.0（与基线池等效），kept = (0.0 > 0) = False
        best = 0.0

      第 1 轮：候选 broken
        contract 拒 → 0
        小计 +0 → eval 累计 = 6
        delta=None，best 保持 0.0

      第 2 轮：候选 A（同 identity）
        闸门 +3（与第 0 轮同源）
        identity 不在 kept_extra（因为第 0 轮 kept=False）→ _candidate_points +1
        小计 +4 → eval 累计 = 10
        delta=0.0，best 保持 0.0

    杀伤力：用 round_index×常数 近似计数的实现，第 1 轮就会算错（不是 6）。
    """
    instance = make_instance()
    protocol = make_protocol(instance)

    a = ProposalCandidate(algorithm_id="test_zero", source_code=_A_SRC, description="zero")
    broken = ProposalCandidate(algorithm_id="test_broken", source_code=_BROKEN_SRC, description="contract reject")
    candidates = (a, broken, a)

    ledger, kept = evolve_pool(
        base_pool(), (instance,),
        proposer=_DeterministicProposer(candidates),
        protocol=protocol,
        rng=np.random.default_rng(0),
        rounds=3,
    )
    records = ledger.records
    assert len(records) == 3

    # 轮 0
    r0 = records[0]
    assert r0.algorithm_id == "test_zero"
    assert [g.passed for g in r0.gates] == [True, True, True, True]
    assert r0.hypervolume_delta == 0.0
    assert r0.kept is False
    assert r0.evaluations_used == 6
    assert r0.cumulative_best_delta == 0.0

    # 轮 1
    r1 = records[1]
    assert r1.algorithm_id == "test_broken"
    assert r1.gates[0].gate == "contract" and r1.gates[0].passed is False
    assert r1.hypervolume_delta is None
    assert r1.kept is False
    assert r1.evaluations_used == 6
    assert r1.cumulative_best_delta == 0.0  # None 不更新 best

    # 轮 2
    r2 = records[2]
    assert r2.algorithm_id == "test_zero"
    assert [g.passed for g in r2.gates] == [True, True, True, True]
    assert r2.hypervolume_delta == 0.0
    assert r2.kept is False
    assert r2.evaluations_used == 10
    assert r2.cumulative_best_delta == 0.0

    # 候选未被晋升（与基线池等效，HV 不增）
    assert kept == ()


def test_cumulative_best_delta_is_monotone_non_decreasing() -> None:
    """b. cumulative_best_delta 单调不减（比较相邻记录，允许相等）。

    用手动构造的 EvolutionRecord 序列注入一个 -inf 场景，验证 max 行为：
    delta 序列 (0.05, -inf, 0.02) → best 序列 (0.05, 0.05, 0.05)。
    （-inf 参与 max 时不抬高 best，但也不破单调性。）
    不走 EvolutionLedger.append / verify：pydantic 的 model_dump_json 拒 -inf，
    而账本哈希链本就该被 -inf 拒——此测试仅钉 anytime_curve 的单调性。
    """
    deltas = (0.05, float("-inf"), 0.02)
    records = []
    best = None
    for i, d in enumerate(deltas):
        if d is not None:
            best = d if best is None else max(best, d)
        records.append(EvolutionRecord(
            round_index=i,
            algorithm_id=f"r{i}",
            proposal_hash="0" * 64,
            compiled=True,
            gates=(),
            hypervolume_delta=d,
            kept=d > 0.0,
            evaluations_used=10 + i,
            cumulative_best_delta=best,
        ))

    curve = anytime_curve(records)
    assert len(curve) == 3
    # 第二分量单调不减：-inf 与 0.05 取 max = 0.05，0.05 与 0.02 取 max = 0.05
    second = [c[1] for c in curve]
    for prev, curr in zip(second, second[1:]):
        assert prev is not None and curr is not None
        assert curr >= prev
    assert curve[0][1] == 0.05
    assert curve[1][1] == 0.05
    assert curve[2][1] == 0.05


def test_ledger_verify_passes_after_evolution() -> None:
    """c. 全部记录写入后 ledger.verify() 不抛异常。"""
    instance = make_instance()
    protocol = make_protocol(instance)
    a = ProposalCandidate(algorithm_id="test_zero", source_code=_A_SRC, description="zero")
    candidates = (a, a, a, a)
    ledger, _ = evolve_pool(
        base_pool(), (instance,),
        proposer=_DeterministicProposer(candidates),
        protocol=protocol,
        rng=np.random.default_rng(7),
        rounds=4,
    )
    ledger.verify()  # 不抛即通过
    assert all(r.evaluations_used >= 2 for r in ledger.records)  # 至少基线池 2


def test_anytime_curve_matches_records_and_is_monotone() -> None:
    """d. anytime_curve 输出长度 = 轮数，逐点等于记录的两个字段；
    第二分量单调不减。"""
    instance = make_instance()
    protocol = make_protocol(instance)
    a = ProposalCandidate(algorithm_id="test_zero", source_code=_A_SRC, description="zero")
    broken = ProposalCandidate(algorithm_id="test_broken", source_code=_BROKEN_SRC, description="contract reject")
    candidates = (a, broken, a, broken, a)

    ledger, _ = evolve_pool(
        base_pool(), (instance,),
        proposer=_DeterministicProposer(candidates),
        protocol=protocol,
        rng=np.random.default_rng(11),
        rounds=5,
    )
    records = ledger.records
    curve = anytime_curve(records)
    assert len(curve) == len(records)
    for rec, (evals, best) in zip(records, curve):
        assert evals == rec.evaluations_used
        assert best == rec.cumulative_best_delta
    # 第二分量单调不减
    for prev, curr in zip(curve, curve[1:]):
        if prev[1] is not None and curr[1] is not None:
            assert curr[1] >= prev[1]
