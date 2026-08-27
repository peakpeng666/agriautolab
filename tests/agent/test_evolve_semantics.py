"""演化循环的语义真值（非仅确定性）：正 ΔHV 候选必须被保留。

历史缺陷：evolve_pool 曾把「已含本候选」的合并池当基线传入
hypervolume_delta，HV(P∪{c}∪{c}) − HV(P∪{c}) 恒为 0，候选永不可能晋升
——而确定性测试照样全绿（永远谁都不保留的算法同样逐位可复现）。
本文件钉住「保留语义」本身。"""

import numpy as np

from agriautolab.agent.evolve import KeepRule, evolve_pool, hypervolume_delta
from agriautolab.agent.proposer import MockProposer
from agriautolab.contracts.protocol import HypervolumeReference
from agriautolab.pipeline.pareto.front import ObjectiveVector

from tests.agent.test_agent import base_pool, make_instance, make_protocol


def test_hypervolume_delta_is_positive_for_dominating_candidate():
    reference = HypervolumeReference(
        path_length=1000.0, headland_turns=1000.0, row_crossings=1000.0, basis="test"
    )

    class _P:
        hypervolume_reference = reference

    pool = [{"base": ObjectiveVector(10.0, 10.0, 10.0)}]
    candidate = ObjectiveVector(9.0, 9.0, 9.0)  # 严格支配基线点
    delta = hypervolume_delta([candidate], pool, _P())
    assert delta > 0.0
    # 基线不得包含候选自身（历史缺陷的精确回归：那时 delta 恒为 0）
    buggy = hypervolume_delta([candidate], [{"base": ObjectiveVector(10.0, 10.0, 10.0),
                                             "c": candidate}], _P())
    assert buggy == 0.0


def test_evolve_keeps_candidate_with_positive_delta_oracle():
    instance = make_instance()
    protocol = make_protocol(instance)
    ledger, kept = evolve_pool(
        base_pool(), (instance,), proposer=MockProposer(), protocol=protocol,
        rng=np.random.default_rng(42), rounds=12, keep_rule=KeepRule.HYPERVOLUME_DELTA,
    )
    deltas = [r.hypervolume_delta for r in ledger.records if r.hypervolume_delta is not None]
    assert deltas, "12 轮内没有任何候选到达 ΔHV 评估（门/复核全灭本身即异常）"
    assert any(d > 0.0 for d in deltas), "无任何正增量——基线混入候选的缺陷复现"
    assert kept, "存在正 ΔHV 候选但未被保留"
    # 账本自洽：HYPERVOLUME_DELTA 规则下 kept ⇔ delta > 0
    for record in ledger.records:
        if record.hypervolume_delta is not None:
            assert record.kept == (record.hypervolume_delta > 0.0)
