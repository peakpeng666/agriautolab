"""内容寻址的证据必须稳定，链上篡改必须可检出。"""

import pytest

from agriautolab.contracts.enums import RunStatus
from agriautolab.contracts.errors import EvidenceChainError
from agriautolab.evidence.ledger import EvidenceLedger, LedgerEntry
from agriautolab.evidence.record import EvidenceRecord


def record(record_id: str) -> EvidenceRecord:
    h = "a" * 64
    return EvidenceRecord(
        record_id=record_id, problem_hash=h, algorithm_id="alg", config_hash=h,
        source_hash=h, environment_hash=h, status=RunStatus.OK,
    )


def test_ledger_verifies_after_two_appends() -> None:
    ledger = EvidenceLedger()
    ledger.append(record("r1"))
    ledger.append(record("r2"))
    ledger.verify()
    assert ledger.entries[1].previous_hash == ledger.entries[0].entry_hash


def test_ledger_detects_tampered_hash() -> None:
    ledger = EvidenceLedger()
    ledger.append(record("r1"))
    entry = ledger._entries[0]
    ledger._entries[0] = LedgerEntry(index=entry.index, previous_hash=entry.previous_hash, record=entry.record, entry_hash="0" * 64)
    with pytest.raises(EvidenceChainError):
        ledger.verify()
