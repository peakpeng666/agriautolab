"""留出集封存：HoldoutVault。

封存不提供防篡改保证（拿到仓库的人可改任何文件），它提供的是
是「实验开始后留出集没有被动过」这条可审计的主张。封存记录只含
problem_id 列表、种子与内容哈希，不含时钟（确定性纪律），重算即可对账。
"""

from __future__ import annotations

from typing import Iterable

from pydantic import BaseModel, ConfigDict, Field

from agriautolab.evidence.hashing import content_hash


class HoldoutSeal(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    problem_ids: tuple[str, ...] = Field(min_length=1)
    seed: int
    seal_hash: str = Field(min_length=64, max_length=64)


class HoldoutVault:
    """封存一次，之后只能对账。重复封存直接拒绝——「重新封存」就是换留出集。"""

    def __init__(self) -> None:
        self._seal: HoldoutSeal | None = None

    @property
    def seal(self) -> HoldoutSeal | None:
        return self._seal

    def _hash(self, problem_ids: tuple[str, ...], seed: int) -> str:
        return content_hash({"problem_ids": sorted(problem_ids), "seed": seed})

    def seal_holdout(self, problem_ids: tuple[str, ...], *, seed: int) -> HoldoutSeal:
        if self._seal is not None:
            raise RuntimeError("留出集已封存：重新封存等于换留出集，拒绝")
        if not problem_ids:
            raise ValueError("留出集不能为空")
        self._seal = HoldoutSeal(
            problem_ids=tuple(sorted(problem_ids)), seed=seed,
            seal_hash=self._hash(tuple(problem_ids), seed),
        )
        return self._seal

    def verify(self, problem_ids: tuple[str, ...], *, seed: int) -> None:
        """对账失败抛 ValueError：留出集与封存记录不一致，实验不得引用它。"""
        if self._seal is None:
            raise ValueError("留出集尚未封存")
        if tuple(sorted(problem_ids)) != self._seal.problem_ids or seed != self._seal.seed:
            raise ValueError(
                "留出集与封存记录不一致：实验中途换留出集是预注册要防的那件事"
            )
        if self._hash(tuple(problem_ids), seed) != self._seal.seal_hash:
            raise ValueError("封存哈希对不上")


def field_level_holdout(
    field_ids: Iterable[str], *, fraction: float, seed: int
) -> tuple[str, ...]:
    """按 field_id 分组抽留出集，返回排序后的留出 field_id 元组。

    **必须按地块分组，不能按实例分组**（与 CV 折分组同一条纪律）：
    一块地会派生出 10N 个实例（行偏移 x 行距 x 机具），它们的特征绝大部分由地块决定。
    按实例封存 = 同一块地同时进训练与留出 = 泄漏，而这正是按实例分组泄漏的另一个出口。

    随机走注入的 numpy.random.Generator（种子显式），不用全局随机。
    返回值排序，使封存哈希与抽取顺序无关。
    """
    import numpy as np

    if not 0.0 < fraction < 1.0:
        raise ValueError(f"留出比例必须在 (0,1) 内，实际 {fraction!r}")
    unique = sorted(set(field_ids))
    if not unique:
        raise ValueError("没有可供封存的地块")
    count = max(1, round(len(unique) * fraction))
    if count >= len(unique):
        raise ValueError(
            f"留出比例 {fraction!r} 会吃掉全部 {len(unique)} 块地，训练集为空"
        )
    generator = np.random.default_rng(seed)
    picked = generator.choice(np.asarray(unique, dtype=object), size=count, replace=False)
    return tuple(sorted(str(item) for item in picked))


def instance_in_holdout(field_id: str, holdout_field_ids: Iterable[str]) -> bool:
    """实例是否属于留出集——只看它所属地块，不看实例自身。

    这是「同一 field_id 的全部实例 in_holdout 必须相同」这条不变量的唯一实现点：
    只要所有调用方都走这里，就不可能出现同地块跨集的情形。
    """
    return field_id in set(holdout_field_ids)
