"""公开命令行入口、安装面与官方数据入口的审计 smoke tests。"""

from __future__ import annotations

import hashlib
import io
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

import pytest
import shapely


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


def test_official_fields2benchmark_archive_exposes_current_crs_regression(tmp_path: Path) -> None:
    """官方 raw WKT 是经纬度；当前按国家投影 CRS 解释会被守卫拒绝。"""
    from agriautolab.datasets.fields2benchmark import (
        CrsDeclarationError,
        load_fields2benchmark_wkt_zip_with_quarantine,
    )

    url = "https://zenodo.org/api/records/14524735/files/wkt.zip/content"
    with urllib.request.urlopen(url, timeout=60) as response:
        payload = response.read()
    assert hashlib.md5(payload).hexdigest() == "dc054560af2a388996de201e3fe193dd"

    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        names = sorted(name for name in archive.namelist() if name.lower().endswith(".wkt"))
        assert len(names) == 350
        sample = shapely.from_wkt(archive.read(names[0]).decode("utf-8").strip())
        min_x, min_y, max_x, max_y = sample.bounds
        assert max(abs(min_x), abs(max_x)) <= 180.0
        assert max(abs(min_y), abs(max_y)) <= 90.0

    archive_path = tmp_path / "wkt.zip"
    archive_path.write_bytes(payload)
    with pytest.raises(CrsDeclarationError):
        load_fields2benchmark_wkt_zip_with_quarantine(archive_path)
