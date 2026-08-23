"""公开命令行入口的审计 smoke tests；只验证自检路径能真实启动。"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _run(*args: str) -> str:
    completed = subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + "\n" + completed.stderr
    return completed.stdout


def test_corpus_runner_cli_self_check() -> None:
    assert "self-check: ok" in _run("scripts/run_corpus.py", "--self-check")


def test_fields2benchmark_import_cli_self_check() -> None:
    assert "self-check: ok" in _run("scripts/import_fields2benchmark.py", "--self-check")


def test_recorded_f2c_cli_self_check() -> None:
    assert "self-check: ok" in _run("scripts/validate_f2c_recorded.py", "--self-check")


def test_preregistration_seal_recomputes_cleanly() -> None:
    output = _run("scripts/seal_preregistration.py")
    assert "已封存且一致" in output
