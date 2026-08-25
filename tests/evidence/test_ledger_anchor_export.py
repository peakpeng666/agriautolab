"""Block D 账本外部锚定导出的只读回归（E：归档与外部锚定）。

真值标准（docs/OPTIMIZATION_FOUNDATIONS.md §4 的精神）：错误实现必须失败——
不复算全链、写回 evidence/、不 fail-closed、链尾对不上，任何一条都会被抓住。
本文件只读 evidence/，绝不写回。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from agriautolab.contracts.errors import EvidenceChainError
from agriautolab.evidence.ledger import artifact_chain_entry, verify_artifact_chain

ROOT = Path(__file__).resolve().parents[2]
LEDGER_PATH = ROOT / "evidence" / "block_d" / "ledger.jsonl"
SCRIPT_PATH = ROOT / "scripts" / "export_ledger_anchor.py"
GENESIS_PREVIOUS_HASH = "0" * 64
TAIL_ENTRY_HASH = "c278bec5af643c81a372ec116deb7cfe2766bcd3fd0793abb74fcddee653c40c"


def _ledger_entries() -> list[dict]:
    return [
        json.loads(line)
        for line in LEDGER_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _run_anchor_script(*args: str) -> subprocess.CompletedProcess[str]:
    # 脚本错误消息含中文：强制子进程 UTF-8 I/O，避免非 UTF-8 locale
    # （如 Windows GBK 裸机）下父进程严格 UTF-8 解码出现假失败。
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        cwd=ROOT,
        check=False,
    )


def test_ledger_has_at_least_eight_contiguous_entries() -> None:
    # 账本追加第 9 条（封存性 corrigendum）是计划内工作流：结构测试只钉住
    # 「index 从 0 连续 + genesis 链接」；条数与链尾时效由 golden tail 哨兵测试
    # （test_anchor_script_reports_eight_entries_and_golden_tail）单独把守。
    entries = _ledger_entries()
    assert len(entries) >= 8
    assert [entry["index"] for entry in entries] == list(range(len(entries)))
    assert entries[0]["previous_hash"] == GENESIS_PREVIOUS_HASH


def test_full_chain_recomputation_is_self_consistent() -> None:
    # 用与 verify_artifact_chain 相同的权威规则逐条对账；
    # 规则本身的回归由 hashing/ledger 的单元测试负责。
    previous = GENESIS_PREVIOUS_HASH
    for index, entry in enumerate(_ledger_entries()):
        expected = artifact_chain_entry(index, previous, entry["payload"])
        assert entry == expected
        previous = entry["entry_hash"]
    verify_artifact_chain(tuple(_ledger_entries()))  # 包内 verify 再跑一遍同一规则，交叉核对


def test_tampered_payload_breaks_chain_recomputation() -> None:
    # 反向真值：篡改一条 payload 后，复算必须发现断链，而不是接受新账本。
    entries = _ledger_entries()
    entries[3]["payload"]["artifact"] = f"tampered:{entries[3]['payload']['artifact']}"
    with pytest.raises(EvidenceChainError):
        verify_artifact_chain(tuple(entries))


def test_anchor_script_is_read_only() -> None:
    # 只读回归：脚本运行前后，evidence/block_d/ledger.jsonl 字节与 mtime 完全不变。
    # 写回 evidence/ 的实现（哪怕写回相同内容）在此必失败。
    before_bytes = LEDGER_PATH.read_bytes()
    before_stamp = LEDGER_PATH.stat().st_mtime_ns
    result = _run_anchor_script()
    assert result.returncode == 0, result.stderr
    assert LEDGER_PATH.read_bytes() == before_bytes
    assert LEDGER_PATH.stat().st_mtime_ns == before_stamp


def test_anchor_script_reports_eight_entries_and_golden_tail() -> None:
    result = _run_anchor_script()
    assert result.returncode == 0, result.stderr
    stdout = result.stdout
    for entry in _ledger_entries():
        assert f"{entry['index']:<5}  {entry['entry_hash']}" in stdout
    assert "total_entries: 8" in stdout
    assert f"tail_entry_hash: {TAIL_ENTRY_HASH}" in stdout
    assert "chain_verified: ok" in stdout


def test_anchor_script_fails_closed_on_broken_chain(tmp_path: Path) -> None:
    # fail-closed：断链账本必须非零退出并报错，绝不打印“已验证”的报告。
    entries = _ledger_entries()
    entries[2]["payload"]["artifact"] = "tampered"
    broken = tmp_path / "ledger.jsonl"
    broken.write_text(
        "".join(json.dumps(entry, sort_keys=True) + "\n" for entry in entries),
        encoding="utf-8",
    )
    result = _run_anchor_script("--ledger", str(broken))
    assert result.returncode != 0
    assert "fail-closed" in result.stderr
    assert "chain_verified" not in result.stdout


def test_anchor_script_fails_closed_on_missing_required_key(tmp_path: Path) -> None:
    # 缺键的合法 JSON 行（无 payload）必须走统一 fail-closed 报告（带行号），
    # 而不是 KeyError 裸栈。
    broken = tmp_path / "missing_key.jsonl"
    broken.write_text(
        '{"index": 0, "previous_hash": "0000", "entry_hash": "aaaa"}\n',
        encoding="utf-8",
    )
    result = _run_anchor_script("--ledger", str(broken))
    assert result.returncode != 0
    assert "fail-closed" in result.stderr
    assert "缺少必需字段" in result.stderr
    assert "payload" in result.stderr
    assert "chain_verified" not in result.stdout
