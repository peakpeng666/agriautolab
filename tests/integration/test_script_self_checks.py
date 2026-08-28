"""Public scripts must at least import and pass their code-identity self-check in the dev environment."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

EVALUATION_SCRIPTS = (
    "scripts/evaluate_pareto_optimality.py",
    "scripts/evaluate_feature_effects.py",
    "scripts/evaluate_recommender.py",
)


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


def test_evaluation_scripts_import_and_report_code_identity() -> None:
    """The three evaluation scripts must import and run _code_identity() without error.

    This guards against half-renamed imports (e.g. an old codename symbol that no
    longer exists) and against ANALYSIS_CODE_FILES referencing a missing file.
    """
    for relative in EVALUATION_SCRIPTS:
        spec = importlib.util.spec_from_file_location("m", ROOT / relative)
        assert spec is not None and spec.loader is not None, relative
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        files, analysis_code_hash = module._code_identity()
        assert len(files) >= 1
        assert len(analysis_code_hash) == 64
