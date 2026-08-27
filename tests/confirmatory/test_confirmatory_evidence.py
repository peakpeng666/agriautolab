"""D5/D6 确认性结果 ledger 封存测试。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agriautolab.evaluation.evidence import seal_confirmatory_result
from agriautolab.pipeline import jsonl_log


def _d4_ledger(path: Path) -> None:
    entries = []
    for index, artifact in enumerate(("d1", "pool_census", "selection_protocol_v1", "selection_cv_result")):
        payload = {"artifact": artifact}
        entry = jsonl_log.entry(index, payload)
        entries.append(entry)
    path.write_text("".join(json.dumps(entry, sort_keys=True) + "\n" for entry in entries), encoding="utf-8")


def _result(path: Path, *, code_hash="a" * 64) -> None:
    path.write_text(json.dumps({
        "hypothesis": "H1",
        "identity": {
            "analysis_code_hash": code_hash,
            "protocol_bundle_hash": "b" * 64,
            "runs_parquet_sha256": "c" * 64,
            "pool_hash": "d" * 64,
        },
    }) + "\n", encoding="utf-8")


def test_h1_seal_is_index_four_idempotent_and_conflict_safe(tmp_path: Path):
    ledger = tmp_path / "ledger.jsonl"
    result = tmp_path / "h1.json"
    _d4_ledger(ledger)
    _result(result)
    first = seal_confirmatory_result(
        hypothesis="H1",
        expected_index=4,
        required_previous_artifact="selection_cv_result",
        result_path=result,
        ledger_path=ledger,
    )
    before = ledger.read_bytes()
    second = seal_confirmatory_result(
        hypothesis="H1",
        expected_index=4,
        required_previous_artifact="selection_cv_result",
        result_path=result,
        ledger_path=ledger,
    )
    assert first == second
    assert first["index"] == 4
    assert ledger.read_bytes() == before
    jsonl_log.verify_entries(tuple(json.loads(line) for line in ledger.read_text().splitlines()))

    _result(result, code_hash="e" * 64)
    with pytest.raises(ValueError, match="冲突"):
        seal_confirmatory_result(
            hypothesis="H1",
            expected_index=4,
            required_previous_artifact="selection_cv_result",
            result_path=result,
            ledger_path=ledger,
        )


def test_h1_seal_refuses_wrong_predecessor(tmp_path: Path):
    ledger = tmp_path / "ledger.jsonl"
    result = tmp_path / "h1.json"
    _d4_ledger(ledger)
    entries = [json.loads(line) for line in ledger.read_text().splitlines()]
    entries[-1] = jsonl_log.entry(3, {"artifact": "wrong"})
    ledger.write_text("".join(json.dumps(entry, sort_keys=True) + "\n" for entry in entries))
    _result(result)
    with pytest.raises(ValueError, match="前序"):
        seal_confirmatory_result(
            hypothesis="H1",
            expected_index=4,
            required_previous_artifact="selection_cv_result",
            result_path=result,
            ledger_path=ledger,
        )
