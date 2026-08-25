"""演化账本：哈希链式相连的演化历史，被淘汰的候选也必须记录。

只记成功候选就是发表偏倚——「演化找到了 3 个好启发式」和
「演化试了 40 个、37 个被闸门否决」是两个完全不同的主张，
后者才是可复现实验该有的记录。
evidence 层的 EvidenceLedger 与 EvidenceRecord 强类型绑定（运行证据），
演化记录字段不同，这里按同一哈希链纪律单独建账。
"""

from __future__ import annotations

from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict, Field

from agriautolab.contracts.errors import EvidenceChainError
from agriautolab.evidence.hashing import content_hash


class GateRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    gate: str
    passed: bool
    detail: str


class EvolutionRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    round_index: int = Field(ge=0)
    algorithm_id: str = Field(min_length=1)
    proposal_hash: str = Field(min_length=64, max_length=64)
    # 候选槽位 id（agent/slots.py 的 SLOTS 注册表键；字面量是 DEFAULT_SLOT_ID 的
    # 镜像——本模块有意不依赖 agent 内其他模块，保持账本模型可独立 import）。
    # 演化账本从未落盘，无历史迁移问题；一旦开始落盘，slot_id 即成为
    # 证据身份（wire ID）永不改。
    slot_id: str = "swath_angle"
    compiled: bool
    gates: tuple[GateRecord, ...] = ()
    review_refuted: bool | None = None
    review_reasons: tuple[str, ...] = ()
    hypervolume_delta: float | None = None
    kept: bool
    # 记录 append 时刻的全程累计真实 run_pipeline 调用数（含轮前基线池 I×P、
    # 闸门 1+2+0、候选逐实例评估）。这是 Study-002 预算口径的唯一来源。
    evaluations_used: int = 0
    # 迄今各轮 hypervolume_delta 非 None 值的 running max，单调不减；
    # 任何 delta 仍为 None 时也保持上轮值。口径是 COCO/IOHprofiler 式的
    # "评估次数 → 当前最优"轨迹。
    cumulative_best_delta: float | None = None


class EvolutionLedger:
    """链式账本：append 时用前一条哈希作盐，verify 复算全链。"""

    def __init__(self) -> None:
        self._records: list[tuple[str, EvolutionRecord]] = []   # (entry_hash, record)

    @property
    def records(self) -> tuple[EvolutionRecord, ...]:
        return tuple(record for _, record in self._records)

    def _entry_hash(self, previous_hash: str, record: EvolutionRecord) -> str:
        return content_hash({
            "previous_hash": previous_hash,
            "record": record.model_dump(mode="json"),
        })

    def append(self, record: EvolutionRecord) -> str:
        previous_hash = self._records[-1][0] if self._records else "0" * 64
        entry_hash = self._entry_hash(previous_hash, record)
        self._records.append((entry_hash, record))
        return entry_hash

    def verify(self) -> None:
        previous_hash = "0" * 64
        for entry_hash, record in self._records:
            expected = self._entry_hash(previous_hash, record)
            if entry_hash != expected:
                raise EvidenceChainError(f"演化账本在 {record.algorithm_id}（round {record.round_index}）处断链")
            previous_hash = entry_hash


def anytime_curve(records: Sequence[EvolutionRecord]) -> tuple[tuple[int, float | None], ...]:
    """COCO/IOHprofiler 式 anytime 轨迹：逐轮返回 (evaluations_used, cumulative_best_delta)。

    口径与 EvolutionRecord 的两个新字段严格一致——评估次数（含基线池与闸门）作为
    横轴，当前最优 ΔHV（running max，单调不减）作为纵轴。O(n)。
    """
    return tuple((record.evaluations_used, record.cumulative_best_delta) for record in records)
