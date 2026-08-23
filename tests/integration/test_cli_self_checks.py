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
ZENODO_WKT_URL = "https://zenodo.org/api/records/14524735/files/wkt.zip/content"
ZENODO_WKT_MD5 = "dc054560af2a388996de201e3fe193dd"
V7_CORPUS_HASH = "996f7960d51d5c9bbcff02d76acebbdf55ca6a736bf65bfa9fbf03d180fdd3eb"


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


def _official_wkt_payload() -> bytes:
    with urllib.request.urlopen(ZENODO_WKT_URL, timeout=60) as response:
        payload = response.read()
    assert hashlib.md5(payload).hexdigest() == ZENODO_WKT_MD5
    return payload


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

    payload = _official_wkt_payload()
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


def test_wgs84_archive_interpretation_reproduces_v7_corpus_hash(tmp_path: Path) -> None:
    """把 archive 编码 CRS 正确设为 EPSG:4326 后，应精确重建 v7 的 235 田身份。"""
    from agriautolab.contracts.errors import GeometryValidationError
    from agriautolab.datasets.fields2benchmark import (
        DatasetLicense,
        FieldRecord,
        QuarantinedField,
        export_corpus,
        to_metric_crs,
    )
    from agriautolab.geometry.validate import validate_geometry

    source_meta = {
        "NL": ("PDOK/Nationaal-Georegister", DatasetLicense.PUBLIC_DOMAIN),
        "EE": ("INSPIRE-EE", DatasetLicense.CC_BY_SA_3_0_EE),
        "LT": ("geoportal-lt", DatasetLicense.NON_COMMERCIAL),
    }
    records: list[FieldRecord] = []
    quarantined: list[QuarantinedField] = []
    with zipfile.ZipFile(io.BytesIO(_official_wkt_payload())) as archive:
        for name in sorted(item for item in archive.namelist() if item.lower().endswith(".wkt")):
            field_id = Path(name).stem
            source, license_value = source_meta[field_id[:2].upper()]
            geometry = shapely.from_wkt(archive.read(name).decode("utf-8").strip())
            try:
                validate_geometry(geometry, geometry_id=field_id)
            except GeometryValidationError:
                quarantined.append(QuarantinedField(field_id, str(shapely.is_valid_reason(geometry))))
                continue
            metric, working_crs = to_metric_crs(geometry, source_crs="EPSG:4326")
            records.append(FieldRecord(
                field_id=field_id,
                geometry=metric,
                source=source,
                license=license_value,
                source_crs="EPSG:4326",
                working_crs=working_crs,
            ))

    manifest = export_corpus(
        records,
        path=tmp_path / "corpus",
        allow_analysis=True,
        allow_redistribution=True,
        quarantined=tuple(quarantined),
    )
    assert manifest.n_input == 350
    assert len(quarantined) == 2
    assert manifest.n_exported == 235
    assert manifest.corpus_hash == V7_CORPUS_HASH, (
        "正确解释 WGS84 后仍未重现 v7 corpus_hash："
        f"actual={manifest.corpus_hash}, expected={V7_CORPUS_HASH}"
    )
