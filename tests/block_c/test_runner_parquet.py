import json

import pytest

pyarrow = pytest.importorskip("pyarrow")

from agriautolab.corpus.runner import CodeVersion, CorpusRunner


class ConstantClock:
    def __call__(self):
        return 0.0


def _run(root, c_record, c_vehicle, c_configs, c_benchmark, c_corpus_protocol, *, stop_after=None):
    return CorpusRunner(clock=ConstantClock()).run(
        (c_record,), (c_vehicle,), c_configs, c_benchmark, c_corpus_protocol,
        output_dir=root,
        code_version=CodeVersion("TEST", False, "1" * 64),
        stop_after=stop_after,
    )


def test_resume_is_byte_identical_to_one_shot(tmp_path, c_record, c_vehicle, c_configs, c_benchmark, c_corpus_protocol):
    full = tmp_path / "full"
    resumed = tmp_path / "resumed"
    _run(full, c_record, c_vehicle, c_configs, c_benchmark, c_corpus_protocol)
    partial = _run(resumed, c_record, c_vehicle, c_configs, c_benchmark, c_corpus_protocol, stop_after=1)
    assert partial == {"interrupted": True, "n_new": 1}
    _run(resumed, c_record, c_vehicle, c_configs, c_benchmark, c_corpus_protocol)
    for name in ("checkpoint.jsonl", "runs.parquet", "manifest.json", "ledger.jsonl"):
        assert (full / name).read_bytes() == (resumed / name).read_bytes(), name


def test_not_applicable_is_retained_and_effective_pool_counted(tmp_path, c_record, c_vehicle, c_configs, c_benchmark, c_corpus_protocol):
    root = tmp_path / "runs"
    manifest = _run(root, c_record, c_vehicle, c_configs, c_benchmark, c_corpus_protocol)
    import pyarrow.parquet as pq
    rows = pq.read_table(root / "runs.parquet").to_pylist()
    statuses = [row["runstatus"] for row in rows]
    assert "not_applicable" in statuses
    assert manifest["nominal_pool_size"] == len(c_configs)
    assert manifest["runstatus_counts"]["not_applicable"] >= 1
    assert all(value <= len(c_configs) for value in manifest["effective_pool_size_by_instance"].values())
    assert any(row.get("path_json") for row in rows if row["runstatus"] == "ok")


def test_dirty_code_version_is_written_to_manifest(tmp_path, c_record, c_vehicle, c_configs, c_benchmark, c_corpus_protocol):
    root = tmp_path / "dirty"
    CorpusRunner(clock=ConstantClock()).run(
        (c_record,), (c_vehicle,), c_configs[:1], c_benchmark, c_corpus_protocol,
        output_dir=root,
        code_version=CodeVersion("WORKTREE", True, "2" * 64),
    )
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["code_version"]["dirty"] is True


def test_headland_collapse_is_not_applicable_not_crash(tmp_path, c_benchmark):
    """真实小地块实测（2026-08-21 探针 30/390）：塌缩是算法不适用于该实例，归 NOT_APPLICABLE。

    崩溃要归零：infeasible / constraint_violation / not_applicable 是数据，crash 不是。
    只认『塌缩』消息标记，其余 ValueError 仍为 CRASH。
    """
    import pyarrow.parquet as pq
    from shapely import Polygon

    from agriautolab.contracts.enums import CoverageTarget
    from agriautolab.contracts.geometry import Point, PolygonSpec  # noqa: F401  (与下方 Polygon 对照)
    from agriautolab.contracts.protocol import HypervolumeReference
    from agriautolab.contracts.vehicle import VehicleSpec
    from agriautolab.corpus.protocol import CorpusProtocol
    from agriautolab.corpus.runner import CodeVersion, CorpusRunner
    from agriautolab.datasets.fields2benchmark import DatasetLicense, FieldRecord
    from agriautolab.pipeline.config import PipelineConfig

    tiny = FieldRecord(
        field_id="ee_tiny",
        geometry=Polygon([(0, 0), (30, 0), (30, 12), (0, 12), (0, 0)]),
        source="self-check", license=DatasetLicense.CC0_1_0,
        source_crs="EPSG:28992", working_crs="EPSG:28992",
    )
    vehicle = VehicleSpec(working_width_m=5.0, body_width_m=2.0, min_turning_radius_m=2.0)
    corpus = CorpusProtocol(
        protocol_id="collapse-corpus", benchmark_protocol_hash=c_benchmark.spec_hash(),
        row_offsets_rad=(0.0,), row_spacings_m=(3.0,), cv_folds=2,
    )
    configs = (
        PipelineConfig("no_decomposition", "uniform_headland", "min_width", "boustrophedon_order",
                       "dubins_transit", {"headland_width_m": 8.0}),   # 12 m 宽地块 + 8 m 地头 -> 塌缩
        PipelineConfig("no_decomposition", "uniform_headland", "min_width", "boustrophedon_order",
                       "dubins_transit", {"headland_width_m": 1.0}),   # 对照：不塌缩
    )
    root = tmp_path / "runs"
    CorpusRunner(clock=ConstantClock()).run(
        (tiny,), (vehicle,), configs, c_benchmark, corpus,
        output_dir=root, code_version=CodeVersion("TEST", False, "9" * 64),
    )
    rows = pq.read_table(root / "runs.parquet").to_pylist()
    assert len(rows) == 2
    statuses = sorted((row["runstatus"], "塌缩" in (row["failure_reason"] or "")) for row in rows)
    assert ("not_applicable", True) in statuses
    assert any(status in {"ok", "other", "constraint_violation"} and not collapsed
               for status, collapsed in statuses)
