"""HoldoutVault：封存一次、对账拒绝不一致。"""

import pytest

from agriautolab.evidence.holdout import HoldoutVault


def test_seal_once_then_verify_accepts_identical_holdout() -> None:
    vault = HoldoutVault()
    seal = vault.seal_holdout(("p3", "p1", "p2"), seed=20260821)
    assert seal.problem_ids == ("p1", "p2", "p3")   # 排序封存，顺序不是身份的一部分
    vault.verify(("p2", "p1", "p3"), seed=20260821)


def test_double_sealing_is_rejected() -> None:
    vault = HoldoutVault()
    vault.seal_holdout(("a",), seed=1)
    with pytest.raises(RuntimeError, match="重新封存"):
        vault.seal_holdout(("b",), seed=2)


def test_verify_rejects_changed_holdout_and_unsealed_vault() -> None:
    with pytest.raises(ValueError, match="尚未封存"):
        HoldoutVault().verify(("a",), seed=1)
    vault = HoldoutVault()
    vault.seal_holdout(("a", "b"), seed=1)
    with pytest.raises(ValueError, match="不一致"):
        vault.verify(("a", "c"), seed=1)
    with pytest.raises(ValueError, match="不一致"):
        vault.verify(("a", "b"), seed=2)


# ---- 封存必须按 field_id 分组 ----------------------------------------

def test_all_instances_of_one_field_share_the_same_in_holdout_flag() -> None:
    """同一 field_id 的全部实例，in_holdout 必须相同。

    按实例封存 = 同一块地同时进训练与留出 = 泄漏，
    正是折分组泄漏的另一个出口。
    """
    from agriautolab.evidence.holdout import field_level_holdout, instance_in_holdout

    fields = tuple(f"F2B_{index:05d}" for index in range(235))
    holdout = field_level_holdout(fields, fraction=0.3, seed=20260821)
    # 每块地派生 10 个实例（行偏移 x 行距 x 机具），标记只看地块。
    for field_id in fields:
        flags = {
            instance_in_holdout(field_id, holdout)
            for _ in range(10)
        }
        assert len(flags) == 1, f"{field_id} 的实例散进了训练与留出两侧"
    assert all(instance_in_holdout(field_id, holdout) for field_id in holdout)
    assert not any(
        instance_in_holdout(field_id, holdout) for field_id in fields if field_id not in holdout
    )


def test_field_level_holdout_hits_the_declared_fraction_and_is_deterministic() -> None:
    """预注册参数：field 级 30%、seed 20260821。235 块 -> 70 块（29.79%）。"""
    from agriautolab.evidence.holdout import field_level_holdout

    fields = tuple(f"F2B_{index:05d}" for index in range(235))
    first = field_level_holdout(fields, fraction=0.3, seed=20260821)
    assert len(first) == 70
    assert first == field_level_holdout(fields, fraction=0.3, seed=20260821)
    assert first != field_level_holdout(fields, fraction=0.3, seed=1)
    assert first == tuple(sorted(first))   # 排序：封存哈希与抽取顺序无关


def test_field_level_holdout_refuses_degenerate_fractions() -> None:
    from agriautolab.evidence.holdout import field_level_holdout

    fields = ("a", "b", "c")
    for bad in (0.0, 1.0, -0.1, 1.5):
        with pytest.raises(ValueError):
            field_level_holdout(fields, fraction=bad, seed=1)
    with pytest.raises(ValueError, match="训练集为空"):
        field_level_holdout(("only",), fraction=0.9, seed=1)


def test_sealing_field_level_holdout_round_trips_through_the_vault() -> None:
    """封存的是 field_id，不是实例 id——对账也必须在同一粒度上。"""
    from agriautolab.evidence.holdout import HoldoutVault, field_level_holdout

    fields = tuple(f"F2B_{index:05d}" for index in range(50))
    holdout = field_level_holdout(fields, fraction=0.3, seed=20260821)
    vault = HoldoutVault()
    seal = vault.seal_holdout(holdout, seed=20260821)
    assert seal.problem_ids == holdout
    vault.verify(field_level_holdout(fields, fraction=0.3, seed=20260821), seed=20260821)
    with pytest.raises(ValueError):
        vault.verify(holdout[:-1], seed=20260821)
