"""演化账本：哈希链式相连的演化历史，被淘汰的候选也必须记录。

只记成功候选就是发表偏倚——「演化找到了 3 个好启发式」和
「演化试了 40 个、37 个被闸门否决」是两个完全不同的主张，
后者才是可复现实验该有的记录。
Block A 的 EvidenceLedger 与 EvidenceRecord 强类型绑定（运行证据），
演化记录字段不同，这里按同一哈希链纪律单独建账。
"""

from __future__ import annotations

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
    compiled: bool
    gates: tuple[GateRecord, ...] = ()
    review_refuted: bool | None = None
    review_reasons: tuple[str, ...] = ()
    hypervolume_delta: float | None = None
    kept: bool


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
