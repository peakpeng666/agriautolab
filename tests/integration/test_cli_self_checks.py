"""公开命令行入口与安装面的审计 smoke tests。"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


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


def test_source_and_scripts_compile() -> None:
    _run("-m", "compileall", "-q", "src", "scripts")


def test_installed_dependencies_are_consistent() -> None:
    _run("-m", "pip", "check")


@pytest.mark.parametrize("script", [
    "scripts/build_f2c_requests.py",
    "scripts/import_fields2benchmark.py",
    "scripts/make_figure_front.py",
    "scripts/record_f2c_golden.py",
    "scripts/run_corpus.py",
    "scripts/status_crosstab.py",
    "scripts/validate_f2c_recorded.py",
    "scripts/f2c_recorder/env_probe.py",
    "scripts/f2c_recorder/record_golden.py",
])
def test_public_cli_help_starts(script: str) -> None:
    _run(script, "--help")


def test_corpus_runner_cli_self_check() -> None:
    assert "self-check: ok" in _run("scripts/run_corpus.py", "--self-check")


def test_fields2benchmark_import_cli_self_check() -> None:
    assert "self-check: ok" in _run("scripts/import_fields2benchmark.py", "--self-check")


def test_recorded_f2c_cli_self_check() -> None:
    assert "self-check: ok" in _run("scripts/validate_f2c_recorded.py", "--self-check")


def test_preregistration_seal_recomputes_cleanly() -> None:
    output = _run("scripts/seal_preregistration.py")
    assert "已封存且一致" in output
