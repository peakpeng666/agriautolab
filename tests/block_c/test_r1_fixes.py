"""Block C 复核 R1 的整改验收：分组折、有效池、逐实例参考点、冻结池、Windows 修复。"""

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

pyarrow = pytest.importorskip("pyarrow")  # noqa: F841

import pyarrow.parquet as pq

from agriautolab.evidence.hashing import content_hash
from agriautolab.aslib import export_aslib_scenarios
from agriautolab.aslib.exporter import _fold
from agriautolab.contracts.protocol import HypervolumeReference
from agriautolab.corpus.aggregate import summarize_pareto
from agriautolab.corpus.protocol import CorpusProtocol
from agriautolab.corpus.runner import CodeVersion, CorpusRunner
from agriautolab.cross_validation.f2c import SubprocessAdapter
from agriautolab.contracts.rows import RowStructure
from agriautolab.contracts.geometry import Point, PolygonSpec
from agriautolab.contracts.problem import CoverageProblem
from agriautolab.pipeline.config import PipelineConfig
from agriautolab.pipeline.run import run_pipeline


class ConstantClock:
    def __call__(self):
        return 0.0


# ---- C-R1：折按地块分组 ----

def test_all_instances_of_one_field_share_one_fold(tmp_path, c_record, c_vehicle, c_configs, c_benchmark):
    """同地块 2 行向 x 2 行距 = 4 个实例，cv.arff 里必须同折（此前实测散布 8/10 折）。"""
    corpus_protocol = CorpusProtocol(
        protocol_id="grouped-cv-test",
        benchmark_protocol_hash=c_benchmark.spec_hash(),
        row_offsets_rad=(0.0, 0.5),
        row_spacings_m=(0.75, 3.0),
        cv_folds=3,
        vehicles_hash=content_hash(tuple(v.model_dump(mode="json") for v in (c_vehicle,))),
    )
    root = tmp_path / "corpus"
    CorpusRunner(clock=ConstantClock()).run(
        (c_record,), (c_vehicle,), c_configs, c_benchmark, corpus_protocol,
        output_dir=root, code_version=CodeVersion("TEST", False, "5" * 64),
    )
    out = tmp_path / "aslib"
    export_aslib_scenarios(root / "runs.parquet", out, cv_folds=3, row_crossable=True)
    lines = (out / "crossable" / "path_length" / "cv.arff").read_text(encoding="utf-8").splitlines()
    data = [line for line in lines if line and not line.startswith("@") and line != ""]
    folds = {int(line.split(",")[2]) for line in data}
    assert len(data) == 4
    assert len(folds) == 1, f"同一地块的 4 个实例散进了多个折：{sorted(folds)}"
    description = (out / "crossable" / "path_length" / "description.txt").read_text(encoding="utf-8")
    assert "grouped by field_id" in description


def test_fold_hash_spreads_distinct_fields_deterministically() -> None:
    """分组不能退化成全同折：40 块合成地分 10 折应散布 >= 5 个不同折，且两次一致。"""
    fields = [f"F2B_{index:05d}" for index in range(40)]
    first = [_fold(field, 10) for field in fields]
    second = [_fold(field, 10) for field in fields]
    assert first == second
    assert len(set(first)) >= 5


# ---- C-R3：逐实例参考点 ----

def test_runner_writes_per_instance_analytic_reference_columns(tmp_path, c_record, c_vehicle, c_configs, c_benchmark, c_corpus_protocol):
    root = tmp_path / "corpus"
    CorpusRunner(clock=ConstantClock()).run(
        (c_record,), (c_vehicle,), c_configs, c_benchmark, c_corpus_protocol,
        output_dir=root, code_version=CodeVersion("TEST", False, "6" * 64),
    )
    rows = pq.read_table(root / "runs.parquet").to_pylist()
    assert rows
    for row in rows:
        assert row["ref_path_length"] > 0.0
        assert row["ref_headland_turns"] > 0.0
        assert row["ref_row_crossings"] > 0.0
        assert "analytic" in row["ref_basis"]
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["hypervolume_reference_scope"] == "per-instance-analytic"


# ---- C-R2：有效池与退化池 ----

def _write_rows(path, rows):
    import pyarrow as pa

    keys = sorted({key for row in rows for key in row})
    table = pa.Table.from_pylist([{key: row.get(key) for key in keys} for row in rows])
    pq.write_table(table, path)


def _row(instance, config, status, objectives, field, ref=(100.0, 10.0, 10.0)):
    base = {
        "run_key": f"{instance}:{config}",
        "field_id": field,
        "instance_id": instance,
        "config_id": config,
        "runstatus": status,
        "ref_path_length": ref[0], "ref_headland_turns": ref[1], "ref_row_crossings": ref[2],
        "ref_basis": "analytic: test",
    }
    if objectives is None:
        base.update({"path_length": None, "headland_turns": None, "row_crossings": None})
    else:
        base.update({
            "path_length": objectives[0], "headland_turns": objectives[1], "row_crossings": objectives[2],
        })
    return base


def test_aggregate_reports_effective_pool_degenerate_and_normalized_hv(tmp_path):
    parquet = tmp_path / "runs.parquet"
    _write_rows(parquet, [
        # A：两个 ok 配置，一个支配另一个 -> 有效池 2，前沿 1（计入 singleton）
        _row("A", "c1", "ok", (10.0, 2.0, 3.0), "F1"),
        _row("A", "c2", "ok", (12.0, 2.0, 3.0), "F1"),
        # B：只有一个 ok 配置 -> 有效池 1，前沿单点是「没得选」，排除出 singleton 统计
        _row("B", "c1", "ok", (12.0, 2.0, 3.0), "F2"),
        # C：全部不可行 -> 有效池 0，必须单列，不许在 n_instances 里静默消失
        _row("C", "c1", "not_applicable", None, "F3"),
        _row("C", "c2", "not_applicable", None, "F3"),
    ])
    summary = summarize_pareto(parquet)
    assert summary.n_instances == 2                       # A、B
    assert summary.n_instances_in_corpus == 3             # A、B、C
    assert summary.n_instances_with_zero_ok_configs == 1  # C
    assert summary.n_instances_with_degenerate_pool == 2  # B(1) + C(0)
    assert summary.n_instances_with_singleton_front == 1  # 仅 A
    assert summary.n_singleton_fronts_excluded == 1       # B 的单点前沿被排除并计数
    assert summary.effective_pool_size_by_instance == (2, 1)
    assert summary.front_size_ratio_distribution == (0.5, 1.0)
    assert summary.reference_scope == "per-instance-analytic"
    # A 的前沿点 (10,2,3)，参考 (100,10,10)：HV = 90*8*7 = 5040；归一化 = 5040/10000
    assert summary.hypervolume_by_instance[0] == pytest.approx(5040.0, rel=1e-12)
    assert summary.hypervolume_normalized_by_reference[0] == pytest.approx(0.504, rel=1e-12)


def test_aggregate_global_fallback_and_missing_reference(tmp_path):
    rows = [_row("A", "c1", "ok", (10.0, 2.0, 3.0), "F1")]
    for row in rows:
        for key in ("ref_path_length", "ref_headland_turns", "ref_row_crossings", "ref_basis"):
            row.pop(key)
    parquet = tmp_path / "runs.parquet"
    _write_rows(parquet, rows)
    fallback = HypervolumeReference(path_length=100.0, headland_turns=10.0, row_crossings=10.0, basis="fallback")
    assert summarize_pareto(parquet, reference=fallback).reference_scope == "global-fallback"
    with pytest.raises(ValueError, match="逐实例参考点"):
        summarize_pareto(parquet)


# ---- C-R4：冻结的 13 配置池 ----

# 冻结哈希基线随修正案更新（2026-08-21 O1 落地：RS 两槽位替换原零地头 Dubins 对照）。
# 每次变更必须在 AUDIT_NOTE 留修正案记录——这个常量存在的意义就是让"顺手改一下"过不了测试。
# 2026-08-22 重钉：.gitattributes 强制 LF 后按 LF 字节重算（内容零变化，跨平台一致性）。
# Windows 文本模式曾把文件写成 CRLF，冻结哈希钉了 CRLF 字节 → Linux 检出必炸。
CORPUS_13_SHA256 = "502b1e9053b598d62daafa0b3a819f3cebc8385cb356aa908433582b93083a57"


def _load_run_corpus():
    module_path = Path(__file__).resolve().parents[2] / "scripts" / "run_corpus.py"
    spec = importlib.util.spec_from_file_location("run_corpus_r1", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_corpus_13_is_frozen_with_reasons() -> None:
    """文件哈希是回归基线：改一个字节都必须显式改这里的常量。"""
    path = Path(__file__).resolve().parents[2] / "configs" / "corpus_13.json"
    assert hashlib.sha256(path.read_bytes()).hexdigest() == CORPUS_13_SHA256
    items = json.loads(path.read_text(encoding="utf-8"))
    assert len(items) == 13
    assert all(str(item.get("reason", "")).strip() for item in items)
    configs = _load_run_corpus()._load_configs(path)
    assert len({config.config_id() for config in configs}) == 13   # 无重复配置


def test_corpus_13_feasibility_smoke(c_benchmark, robot) -> None:
    """全部 13 配置在标准实例上必须产出 ok：零地头槽位换 RS 后（O1 落地）已无结构性不可行组合。

    RS 配置用可倒车机具验证（can_reverse=True）；Dubins 配置用默认前向机具。
    """
    module = _load_run_corpus()
    path = Path(__file__).resolve().parents[2] / "configs" / "corpus_13.json"
    configs = module._load_configs(path)
    field = PolygonSpec(geometry_id="field", exterior=(
        Point(x=0.0, y=0.0), Point(x=100.0, y=0.0), Point(x=100.0, y=50.0),
        Point(x=0.0, y=50.0), Point(x=0.0, y=0.0),
    ))
    problem = CoverageProblem(
        problem_id="smoke", field=field,
        row_structure=RowStructure(direction_rad=0.6, spacing_m=2.5, crossable=True, crossing_penalty=10.0),
    )
    reverse_vehicle = robot.model_copy(update={"can_reverse": True})
    infeasible = {}
    for config in configs:
        vehicle = reverse_vehicle if config.path == "reeds_shepp_transit" else robot
        result = run_pipeline(problem, vehicle, config, c_benchmark)
        if result.validation.status.value != "ok":
            infeasible[f"{config.headland}/{config.swath}/{config.path}"] = result.validation.status.value
    assert infeasible == {}, infeasible


def test_zero_headland_reeds_shepp_is_feasible_and_dubins_is_not(c_benchmark, robot) -> None:
    """O1 的核心物理断言：零地头下 Dubins 必越界（前向掉头鼓包 2R），RS 等长孪生词收进场内。"""
    problem = CoverageProblem(
        problem_id="zh",
        field=PolygonSpec(geometry_id="field", exterior=(
            Point(x=0.0, y=0.0), Point(x=100.0, y=0.0), Point(x=100.0, y=50.0),
            Point(x=0.0, y=50.0), Point(x=0.0, y=0.0),
        )),
    )
    reverse_vehicle = robot.model_copy(update={"can_reverse": True})
    dubins_result = run_pipeline(
        problem, robot,
        PipelineConfig("no_decomposition", "no_headland", "min_width", "boustrophedon_order", "dubins_transit", {}),
        c_benchmark,
    )
    rs_result = run_pipeline(
        problem, reverse_vehicle,
        PipelineConfig("no_decomposition", "no_headland", "min_width", "boustrophedon_order", "reeds_shepp_transit", {}),
        c_benchmark,
    )
    assert dubins_result.validation.failure_reason == "validator_rejected:outside_area"
    assert rs_result.validation.status.value == "ok"
    assert rs_result.objectives is not None


def test_reverse_segments_rejected_without_reverse_gear(c_benchmark, robot) -> None:
    """校验器倒车闸：含 reversing 段的路径在不可倒车机具上必须 INFEASIBLE_KINEMATICS。"""
    from agriautolab.contracts.artifacts import PathArtifact, PathSegment
    from agriautolab.contracts.enums import PathSegmentKind, RunStatus
    from agriautolab.contracts.geometry import LineStringSpec
    from agriautolab.validation.validator import PathValidator

    problem = CoverageProblem(
        problem_id="gear",
        field=PolygonSpec(geometry_id="field", exterior=(
            Point(x=0.0, y=0.0), Point(x=100.0, y=0.0), Point(x=100.0, y=50.0),
            Point(x=0.0, y=50.0), Point(x=0.0, y=0.0),
        )),
    )
    path = PathArtifact(segments=(PathSegment(
        segment_id="w", kind=PathSegmentKind.WORK,
        line=LineStringSpec(geometry_id="w", points=(Point(x=5.0, y=25.0), Point(x=95.0, y=25.0))),
        signed_curvature_m_inv=0.0, reversing=True,
    ),))
    rejected = PathValidator().validate(problem, robot, path, c_benchmark)
    assert rejected.status is RunStatus.INFEASIBLE_KINEMATICS
    assert rejected.failure_reason == "validator_rejected:reverse_without_gear"


# ---- Windows 修复 ----

def test_subprocess_adapter_routes_python_shebang_through_interpreter(tmp_path) -> None:
    script = tmp_path / "fake_f2c"
    script.write_text("#!/usr/bin/env python3\nprint('x')\n", encoding="utf-8")
    command = SubprocessAdapter(script)._command()
    assert command[0] == sys.executable
    assert command[1] == str(script)
    # 非脚本可执行文件不受影响
    binary = tmp_path / "real_wrapper.exe"
    binary.write_bytes(b"")
    assert SubprocessAdapter(binary)._command() == [str(binary)]
