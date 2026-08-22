"""证据哈希链式相连，删除、重排、篡改都会在 verify 时暴露。"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from agriautolab.contracts.errors import EvidenceChainError
from agriautolab.evidence.hashing import content_hash
from agriautolab.evidence.record import EvidenceRecord


class LedgerEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    index: int = Field(ge=0)
    previous_hash: str
    record: EvidenceRecord
    entry_hash: str


class EvidenceLedger:
    def __init__(self) -> None:
        self._entries: list[LedgerEntry] = []

    @property
    def entries(self) -> tuple[LedgerEntry, ...]:
        return tuple(self._entries)

    def append(self, record: EvidenceRecord) -> LedgerEntry:
        previous_hash = self._entries[-1].entry_hash if self._entries else "0" * 64
        index = len(self._entries)
        entry_hash = content_hash({
            "index": index,
            "previous_hash": previous_hash,
            "record": record.model_dump(mode="json"),
        })
        entry = LedgerEntry(index=index, previous_hash=previous_hash, record=record, entry_hash=entry_hash)
        self._entries.append(entry)
        return entry

    def verify(self) -> None:
        previous_hash = "0" * 64
        for index, entry in enumerate(self._entries):
            expected = content_hash({
                "index": index,
                "previous_hash": previous_hash,
                "record": entry.record.model_dump(mode="json"),
            })
            if entry.index != index or entry.previous_hash != previous_hash or entry.entry_hash != expected:
                raise EvidenceChainError(f"账本在 index={index} 处断链")
            previous_hash = entry.entry_hash


def artifact_chain_entry(index: int, previous_hash: str, payload: dict) -> dict:
    """非 EvidenceRecord 产物复用同一证据模块的哈希链规则。

    manifest/cross-validation 不是一次规划运行，强塞进 EvidenceRecord 会伪造算法字段；
    因此只抽象“前哈希 + payload”的链条，而不是复制一套 ledger 模块。
    """
    entry_hash = content_hash({"index": index, "previous_hash": previous_hash, "payload": payload})
    return {"index": index, "previous_hash": previous_hash, "payload": payload, "entry_hash": entry_hash}


def verify_artifact_chain(entries: tuple[dict, ...]) -> None:
    previous_hash = "0" * 64
    for index, entry in enumerate(entries):
        expected = artifact_chain_entry(index, previous_hash, entry["payload"])
        if entry != expected:
            raise EvidenceChainError(f"产物账本在 index={index} 处断链")
        previous_hash = entry["entry_hash"]
