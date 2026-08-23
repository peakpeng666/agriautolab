"""原子封存守卫与评审硬门语义的回归（D7 前置缺陷批次 2）。"""

from pathlib import Path

import pytest

from agriautolab.agent.reviewer import ReviewVerdict, final_refuted, majority_refuted
from agriautolab.evidence.atomic import atomic_write, commit_guarded, sealed_sha_for, sha256_bytes


def _ledger_with_sha(tmp_path: Path, artifact: str, key: str, sha: str) -> Path:
    ledger = tmp_path / "ledger.jsonl"
    ledger.write_text(
        '{"index": 0, "payload": {"artifact": "%s", "%s": "%s"}}\n' % (artifact, key, sha),
        encoding="utf-8",
    )
    return ledger


def test_guarded_commit_refuses_mismatch_before_touching_final(tmp_path):
    final = tmp_path / "sealed.json"
    final.write_bytes(b"original")
    ledger = _ledger_with_sha(tmp_path, "pool_census", "file_sha256", sha256_bytes(b"original"))
    tmp = tmp_path / "sealed.json.tmp"
    tmp.write_bytes(b"drifted")
    with pytest.raises(ValueError, match="拒绝覆盖"):
        commit_guarded(tmp, final, ledger, "pool_census", "file_sha256")
    assert final.read_bytes() == b"original"  # 旧件未被破坏


def test_guarded_commit_idempotent_replace_on_identical(tmp_path):
    final = tmp_path / "sealed.json"
    final.write_bytes(b"same")
    ledger = _ledger_with_sha(tmp_path, "pool_census", "file_sha256", sha256_bytes(b"same"))
    tmp = tmp_path / "sealed.json.tmp"
    tmp.write_bytes(b"same")
    commit_guarded(tmp, final, ledger, "pool_census", "file_sha256")
    assert final.read_bytes() == b"same"


def test_guarded_commit_allows_unsealed_and_atomic_write(tmp_path):
    ledger = tmp_path / "empty-ledger.jsonl"
    ledger.write_text("", encoding="utf-8")
    final = tmp_path / "new.json"
    tmp = tmp_path / "new.json.tmp"
    tmp.write_bytes(b"fresh")
    commit_guarded(tmp, final, ledger, "pool_census", "file_sha256")
    assert final.read_bytes() == b"fresh"
    assert not tmp.exists()  # 原子替换不留残骸
    atomic_write(final, b"v2")
    assert final.read_bytes() == b"v2"
    assert sealed_sha_for(ledger, "pool_census", "file_sha256") is None


def test_hard_verdict_cannot_be_outvoted():
    verdicts = (
        ReviewVerdict(True, ("正确性探针炸了",), hard=True),
        ReviewVerdict(False, ()),
        ReviewVerdict(False, ()),
    )
    assert majority_refuted(verdicts) is False  # 旧语义：1/3 被翻案
    assert final_refuted(verdicts) is True  # 新语义：硬否决不可翻案


def test_advisory_majority_still_works_and_tie_refutes():
    advisory = (ReviewVerdict(False, ()), ReviewVerdict(False, ()), ReviewVerdict(False, ()))
    assert final_refuted(advisory) is False
    two_refuted = (ReviewVerdict(True, ()), ReviewVerdict(True, ()), ReviewVerdict(False, ()))
    assert final_refuted(two_refuted) is True
    tie = (ReviewVerdict(True, ()), ReviewVerdict(False, ()))
    assert final_refuted(tie) is True  # 平票按否决（保守）
