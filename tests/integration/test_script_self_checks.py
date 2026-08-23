"""公开脚本的最小自检必须能在已安装开发环境中直接运行。"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _run_script(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def test_corpus_runner_self_check() -> None:
    result = _run_script("scripts/run_corpus.py", "--self-check")
    assert result.returncode == 0, result.stderr
    assert "self-check: ok" in result.stdout


def test_recorded_f2c_self_check() -> None:
    result = _run_script("scripts/validate_f2c_recorded.py", "--self-check")
    assert result.returncode == 0, result.stderr
    assert "self-check: ok" in result.stdout
