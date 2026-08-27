from __future__ import annotations

import json
from pathlib import Path

import pytest

from agriautolab.evaluation.evidence import seal_confirmatory_result
from agriautolab.pipeline import jsonl_log


def _h1_ledger(path: Path) -> None:
    entries = []
    for index, artifact in enumerate((
        "d1",
        "pool_census",
        "selection_protocol_v1",
        "selection_cv_result",
        "h1_confirmatory_result",
    )):
        entry = jsonl_log.entry(index, {"artifact": artifact})
        entries.append(entry)
    path.write_text(
        "".join(json.dumps(entry, sort_keys=True) + "\n" for entry in entries),
        encoding="utf-8",
    )


def _h2_result(path: Path, *, code_hash: str = "a" * 64) -> None:
    path.write_text(json.dumps({
        "hypothesis": "H2",
        "identity": {
            "analysis_code_hash": code_hash,
            "protocol_bundle_hash": "b" * 64,
            "runs_parquet_sha256": "c" * 64,
            "pool_hash": "d" * 64,
            # D6 additionally binds these inputs; the generic sealer preserves the
            # complete result file through result_file_sha256.
            "pool_census_sha256": "e" * 64,
            "selection_protocol_sha256": "f" * 64,
            "h1_result_sha256": "1" * 64,
        },
    }) + "\n", encoding="utf-8")


def test_h2_seal_is_index_five_idempotent_and_conflict_safe(tmp_path: Path):
    ledger = tmp_path / "ledger.jsonl"
    result = tmp_path / "h2.json"
    _h1_ledger(ledger)
    _h2_result(result)
    first = seal_confirmatory_result(
        hypothesis="H2",
        expected_index=5,
        required_previous_artifact="h1_confirmatory_result",
        result_path=result,
        ledger_path=ledger,
    )
    before = ledger.read_bytes()
    second = seal_confirmatory_result(
        hypothesis="H2",
        expected_index=5,
        required_previous_artifact="h1_confirmatory_result",
        result_path=result,
        ledger_path=ledger,
    )
    assert first == second
    assert first["index"] == 5
    assert first["payload"]["artifact"] == "h2_confirmatory_result"
    assert ledger.read_bytes() == before
    jsonl_log.verify_entries(tuple(json.loads(line) for line in ledger.read_text().splitlines()))

    _h2_result(result, code_hash="9" * 64)
    with pytest.raises(ValueError, match="冲突"):
        seal_confirmatory_result(
            hypothesis="H2",
            expected_index=5,
            required_previous_artifact="h1_confirmatory_result",
            result_path=result,
            ledger_path=ledger,
        )


def test_h2_seal_refuses_wrong_index_four_predecessor(tmp_path: Path):
    ledger = tmp_path / "ledger.jsonl"
    result = tmp_path / "h2.json"
    _h1_ledger(ledger)
    entries = [json.loads(line) for line in ledger.read_text().splitlines()]
    entries[-1] = jsonl_log.entry(4, {"artifact": "wrong"})
    ledger.write_text("".join(json.dumps(entry, sort_keys=True) + "\n" for entry in entries))
    _h2_result(result)
    with pytest.raises(ValueError, match="前序"):
        seal_confirmatory_result(
            hypothesis="H2",
            expected_index=5,
            required_previous_artifact="h1_confirmatory_result",
            result_path=result,
            ledger_path=ledger,
        )

