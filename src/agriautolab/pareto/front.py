"""Pareto 前沿与目标向量：主指标向量是三维，全部最小化。

path_length / headland_turns / row_crossings。transit_length 因与 path_length
秩相关 rho=1.000（240 实例实测）降为 DIAGNOSTIC，不进向量（见注册表 notes）。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from agriautolab.evidence.hashing import content_hash

ConfigId = str


@dataclass(frozen=True, init=False)
class ObjectiveVector:
    """三维主目标向量，全部最小化。字段用规范名（docs/NAMING.md）。

    证据层（parquet 列名、wire ID）仍是 headland_turns / row_crossings；
    这里永久接受 legacy 关键字并提供 legacy 属性，旧构造点零改动。
    位置顺序三时代一致：path_length, 转弯维, 穿行维。
    """

    path_length: float              # m，越小越好
    headland_turn_count: float      # count，越小越好
    row_crossing_equivalent: float  # 1（横向位移/行距），越小越好

    def __init__(self, path_length=None, headland_turn_count=None, row_crossing_equivalent=None, *,
                 headland_turns=None, row_crossings=None):
        if headland_turns is not None:
            headland_turn_count = headland_turns
        if row_crossings is not None:
            row_crossing_equivalent = row_crossings
        missing = [name for name, value in (
            ("path_length", path_length),
            ("headland_turn_count", headland_turn_count),
            ("row_crossing_equivalent", row_crossing_equivalent),
        ) if value is None]
        if missing:
            raise TypeError(f"ObjectiveVector 缺少目标维: {missing}（canonical 或 legacy 关键字至少给一个）")
        object.__setattr__(self, "path_length", float(path_length))
        object.__setattr__(self, "headland_turn_count", float(headland_turn_count))
        object.__setattr__(self, "row_crossing_equivalent", float(row_crossing_equivalent))

    @property
    def headland_turns(self) -> float:
        return self.headland_turn_count

    @property
    def row_crossings(self) -> float:
        return self.row_crossing_equivalent

    def as_tuple(self) -> tuple[float, float, float]:
        return (self.path_length, self.headland_turn_count, self.row_crossing_equivalent)


def dominates(left: ObjectiveVector, right: ObjectiveVector, *, rtol: float = 1e-12) -> bool:
    """left 是否支配 right（最小化）。严格不等式 + 相对容差，不用绝对 eps。

    容差取 rtol * max(|a_i|, |b_i|)：两位有效数字相当的值视为并列，
    避免浮点尾差制造假支配；并列时 any(...) 的严格劣必须有超出容差的维度。
    """
    better_somewhere = False
    for a, b in zip(left.as_tuple(), right.as_tuple()):
        tolerance = rtol * max(abs(a), abs(b), 1e-300)
        if a > b + tolerance:
            return False
        if a < b - tolerance:
            better_somewhere = True
    return better_somewhere


def pareto_front(points: Mapping[ConfigId, ObjectiveVector], *, rtol: float = 1e-12) -> frozenset[ConfigId]:
    """返回非支配集合。

    **前沿大小不可跨算法池比较。** 往池子里加配置只会让前沿单调变大或不变。
    报告"前沿有 6 个配置"而不说池子是哪 12 个，等于没说。
    任何前沿相关的量都必须与产生它的 `pool_hash` 一起记录。
    """
    return frozenset(
        config_id
        for config_id, vector in points.items()
        if not any(dominates(other, vector, rtol=rtol) for other_id, other in points.items() if other_id != config_id)
    )


def pool_hash(config_ids: Iterable[ConfigId]) -> str:
    """池身份：池中全部 config_id 排序后的内容哈希。前沿量必须与它一起记录。"""
    return content_hash({"config_ids": sorted(config_ids)})
