"""语料级顺序运行器：checkpoint 可续跑，Parquet 保留路径几何，失败也占一行。"""

from __future__ import annotations

import json
import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Sequence

import shapely
from shapely.geometry import Polygon

from agriautolab.contracts.enums import RunStatus
from agriautolab.contracts.errors import KinematicModelError
from agriautolab.contracts.geometry import GeometryFrame
from agriautolab.contracts.problem import CoverageProblem
from agriautolab.contracts.rows import RowScenario
from agriautolab.contracts.vehicle import VehicleSpec
from agriautolab.corpus.protocol import CorpusProtocol
from agriautolab.datasets.fields2benchmark import (
    DatasetLicense,
    DatasetLicenseError,
    FieldRecord,
    field_record_hash,
)
from agriautolab.datasets.rows import resolve_row_structure
from agriautolab.evidence.hashing import content_hash, source_hash
from agriautolab.evidence.ledger import artifact_chain_entry
from agriautolab.features.extract import extract_instance_features
from agriautolab.geometry.validate import polygon_to_spec
from agriautolab.pipeline.config import PipelineConfig
from agriautolab.pipeline.run import run_pipeline
from agriautolab.pareto.front import pool_hash
from agriautolab.pareto.hypervolume import analytic_reference


@dataclass(frozen=True)
class CodeVersion:
    commit: str
    dirty: bool
    source_tree_hash: str

    def identity(self) -> str:
        return content_hash({"commit": self.commit, "dirty": self.dirty, "source_tree_hash": self.source_tree_hash})


def discover_code_version(root: str | Path) -> CodeVersion:
    """优先记录 git commit + dirty；发布 ZIP 无 .git 时退回源码树哈希并强制 dirty=True。

    ZIP 天生不携带 git 对象库。把“无 git”伪装成 clean 会错误承诺可复现性，所以退化时
    仍给源码树一个稳定身份，但明确 dirty=True；下游正式实验应在 git checkout 中运行。
    """
    root = Path(root)
    tree_hash = source_hash(root / "src")
    try:
        commit = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"], check=True, capture_output=True, text=True
        ).stdout.strip()
        dirty = bool(subprocess.run(
            ["git", "-C", str(root), "status", "--porcelain"], check=True, capture_output=True, text=True
        ).stdout.strip())
        return CodeVersion(commit=commit, dirty=dirty, source_tree_hash=tree_hash)
    except (OSError, subprocess.CalledProcessError):
        return CodeVersion(commit="NO_GIT_METADATA", dirty=True, source_tree_hash=tree_hash)


def run_key(*, problem_hash: str, vehicle_hash: str, config_id: str, protocol_hash: str, code_version: str) -> str:
    """唯一运行键；算法代码变了就必须变键，不能复用旧结果。"""
    return content_hash({
        "problem_hash": problem_hash,
        "vehicle_hash": vehicle_hash,
        "config_id": config_id,
        "protocol_hash": protocol_hash,
        "code_version": code_version,
    })


def field_record_to_problem(record: FieldRecord, row_scenario: RowScenario) -> CoverageProblem:
    """把 WKT 内环显式提升为 obstacles，避免障碍只藏在 Polygon holes 里导致特征计数为 0。"""
    geometry = record.geometry
    if geometry.geom_type != "Polygon":
        raise ValueError(f"{record.field_id}: 当前语料契约要求单 Polygon，得到 {geometry.geom_type}")
    exterior = Polygon(geometry.exterior)
    obstacles = tuple(Polygon(ring) for ring in geometry.interiors)
    rows = resolve_row_structure(exterior, row_scenario)
    return CoverageProblem(
        problem_id=f"{record.field_id}:{row_scenario.row_direction_mode.value}:{row_scenario.offset_rad!r}:{row_scenario.spacing_m!r}",
        field=polygon_to_spec(exterior, f"{record.field_id}:field"),
        obstacles=tuple(polygon_to_spec(item, f"{record.field_id}:obstacle:{index}") for index, item in enumerate(obstacles)),
        row_structure=rows,
        frame=GeometryFrame(crs=record.working_crs),
    )


# validator 拒绝原因的封闭词典（与 validation/validator.py 的 failure_reason 一一对应）。
# 分类完备性常设规则：任何 "other/misc" 兜底桶都是分类错误。v4 全量实测 9 314 行
# other 里其实只有两类（outside_area 6 054 / collision 3 260），每行都带具名原因——
# 兜底桶藏住的是映射的懒惰，不是数据的无类可归。
_VALIDATOR_REJECTION_CLASSES = frozenset({
    "empty_path", "discontinuous_endpoints", "collision", "curvature_limit",
    "reverse_without_gear", "outside_area", "forbidden_crossing",
    "coverage_threshold", "nonfinite_metric",
})


def _corpus_run_status(
    status: RunStatus, failure_reason: str | None, *, config: PipelineConfig, vehicle: VehicleSpec
) -> str:
    """语料级具名状态：没有 other 桶，未知的拒绝原因当场抛错（响亮失败）。

    ok/timeout/memout/crash/not_applicable 保持 ASlib 六值语义；
    约束违反与数值错误升格为具名值（validator 拒绝原因原样成为状态名），
    ASlib 导出层再做六值聚合（那层的 other 是格式词表的约束，不是我们的分类）。
    """
    if status in {RunStatus.OK, RunStatus.TIMEOUT, RunStatus.MEMOUT, RunStatus.CRASH,
                  RunStatus.INVALID_INPUT}:
        return status.value
    if status in {RunStatus.UNSUPPORTED, RunStatus.INFEASIBLE, RunStatus.INFEASIBLE_KINEMATICS,
                  RunStatus.NOT_APPLICABLE}:
        return RunStatus.NOT_APPLICABLE.value
    if status is RunStatus.COLLISION:
        return "collision"
    if status is RunStatus.NUMERICAL_ERROR:
        return "numerical_error"
    if status is RunStatus.CONSTRAINT_VIOLATION:
        # 前进-only Dubins 在零地头上的掉头鼓包是算法-机具 pairing 的必然，
        # 不是实例不可行：归 not_applicable（既定语义，保留）。
        if config.headland == "no_headland" and vehicle.min_turning_radius_m > 0.0:
            return RunStatus.NOT_APPLICABLE.value
        reason = failure_reason or ""
        if reason.startswith("validator_rejected:"):
            klass = reason.split(":", 1)[1]
            if klass in _VALIDATOR_REJECTION_CLASSES:
                return klass
            raise ValueError(
                f"未知的 validator 拒绝原因 {klass!r}：请先把它加进 _VALIDATOR_REJECTION_CLASSES，"
                "不许落进任何兜底桶（分类完备性规则）"
            )
        raise ValueError(
            f"CONSTRAINT_VIOLATION 缺少可分类的 failure_reason（得到 {failure_reason!r}）"
        )
    raise ValueError(f"无法分类的 RunStatus: {status!r}——加具名映射，不许兜底")


def _append_checkpoint(path: Path, row: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def _load_checkpoint(path: Path) -> dict[str, dict[str, object]]:
    if not path.exists():
        return {}
    rows: dict[str, dict[str, object]] = {}
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        row = json.loads(line)
        key = str(row["run_key"])
        if key in rows:
            raise ValueError(f"checkpoint 第 {line_number} 行 run_key 重复：{key}")
        rows[key] = row
    return rows


def _write_parquet(rows: Sequence[dict[str, object]], path: Path) -> None:
    """一行一次运行；路径 JSON 永远保留，稀疏诊断列按全体键并集补 null。

    旧基线曾在序列化时剥掉路径，导致任何指标都无法独立重算；这里宁可文件大一点，
    也不以“节省空间”为理由删除原始路径几何。
    """
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError as error:
        raise RuntimeError("写 runs.parquet 需要项目声明的 pyarrow>=16") from error
    keys = sorted({key for row in rows for key in row})
    normalized = [{key: row.get(key) for key in keys} for row in rows]
    table = pa.Table.from_pylist(normalized)
    pq.write_table(table, path, compression="zstd")


def _write_artifact_ledger(path: Path, manifest_hash: str, run_rows: Sequence[dict[str, object]]) -> None:
    entries = []
    previous = "0" * 64
    payloads = [{"artifact": "manifest", "hash": manifest_hash}] + [
        {"artifact": "run", "run_key": row["run_key"], "row_hash": content_hash(row)} for row in run_rows
    ]
    for index, payload in enumerate(payloads):
        entry = artifact_chain_entry(index, previous, payload)
        entries.append(entry)
        previous = entry["entry_hash"]
    path.write_text("".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in entries), encoding="utf-8")


def _failure_row(
    key: str,
    record,
    run_instance_id: str,
    vehicle_index: int,
    config: PipelineConfig,
    status: RunStatus,
    error: Exception,
    reference_columns: dict[str, object],
    features,
) -> dict[str, object]:
    """失败行统一构造：失败是数据，类别必须分对，且行 schema 与成功行完全一致。"""
    return {
        "run_key": key,
        "field_id": record.field_id,
        "instance_id": run_instance_id,
        "vehicle_index": vehicle_index,
        "config_id": config.config_id(),
        "runstatus": status.value,
        "failure_reason": f"{type(error).__name__}: {error}",
        "path_length": None,
        "headland_turns": None,
        "row_crossings": None,
        "planning_s": None,
        "postprocessing_s": None,
        "validation_s": None,
        "feature_cost_total_s": sum(features.elapsed_s.values()),
        "path_json": None,
        **reference_columns,
    }


class CorpusRunner:
    """单机顺序运行全网格；checkpoint 每行 fsync，崩溃后按 run_key 精确续跑。

    规模基线是 350×配置池×5 行偏移×2 行距×机具规格。Block B 的单配置毫秒级，
    本块不引入并行/数据库；真正需要防的是中途失败后从头重跑，以及代码变化后误命中旧缓存。
    """

    def __init__(self, *, clock: Callable[[], float] = time.perf_counter):
        self.clock = clock

    def run(
        self,
        records: Iterable[FieldRecord],
        vehicles: Sequence[VehicleSpec],
        configs: Sequence[PipelineConfig],
        benchmark_protocol,
        corpus_protocol: CorpusProtocol,
        *,
        output_dir: str | Path,
        code_version: CodeVersion,
        stop_after: int | None = None,
        pool_file_sha256: str | None = None,
    ) -> dict[str, object]:
        records = tuple(records)
        unknown = [record.field_id for record in records if record.license is DatasetLicense.UNKNOWN]
        if unknown:
            raise DatasetLicenseError("运行器拒绝 UNKNOWN 许可证记录：" + ", ".join(unknown))
        if corpus_protocol.benchmark_protocol_hash != benchmark_protocol.spec_hash():
            raise ValueError("CorpusProtocol 内的 benchmark_protocol_hash 与实际 BenchmarkProtocol 不一致")
        root = Path(output_dir)
        root.mkdir(parents=True, exist_ok=True)
        checkpoint = root / "checkpoint.jsonl"
        prior = _load_checkpoint(checkpoint)
        protocol_hash = corpus_protocol.spec_hash()
        current_keys: list[str] = []
        produced = 0

        for record in sorted(records, key=lambda item: item.field_id):
            for offset in corpus_protocol.row_offsets_rad:
                for spacing in corpus_protocol.row_spacings_m:
                    row_scenario = RowScenario(
                        row_direction_mode=corpus_protocol.row_direction_mode,
                        offset_rad=offset,
                        spacing_m=spacing,
                        crossable=corpus_protocol.row_crossable,
                    )
                    for vehicle_index, vehicle in enumerate(vehicles):
                        problem = field_record_to_problem(record, row_scenario)
                        problem_hash = content_hash(problem)
                        vehicle_hash = content_hash(vehicle)
                        features = extract_instance_features(problem, vehicle, clock=self.clock)
                        run_instance_id = f"{problem.problem_id}:vehicle:{vehicle_index}"
                        # 逐实例解析参考点（Block B pareto.hypervolume.analytic_reference）：
                        # 固定全局参考点下的超体积跨实例测的是地块大小，不是算法质量。
                        # 参考点随行落盘，聚合端独立重算，不采信任何单侧声明。
                        instance_reference = analytic_reference(problem, vehicle)
                        reference_columns = {
                            "ref_path_length": instance_reference.path_length,
                            "ref_headland_turns": instance_reference.headland_turns,
                            "ref_row_crossings": instance_reference.row_crossings,
                            "ref_basis": instance_reference.basis,
                        }
                        for config in configs:
                            key = run_key(
                                problem_hash=problem_hash,
                                vehicle_hash=vehicle_hash,
                                config_id=config.config_id(),
                                protocol_hash=protocol_hash,
                                code_version=code_version.identity(),
                            )
                            current_keys.append(key)
                            if key in prior:
                                continue
                            try:
                                result = run_pipeline(problem, vehicle, config, benchmark_protocol, clock=self.clock)
                                status = _corpus_run_status(
                                    result.validation.status, result.validation.failure_reason,
                                    config=config, vehicle=vehicle,
                                )
                                row: dict[str, object] = {
                                    "run_key": key,
                                    "field_id": record.field_id,
                                    "instance_id": run_instance_id,
                                    "vehicle_index": vehicle_index,
                                    "config_id": config.config_id(),
                                    "runstatus": status,
                                    "failure_reason": result.validation.failure_reason,
                                    "path_length": result.objectives.path_length if result.objectives else None,
                                    "headland_turns": result.objectives.headland_turns if result.objectives else None,
                                    "row_crossings": result.objectives.row_crossings if result.objectives else None,
                                    "planning_s": result.timing.planning_s,
                                    "postprocessing_s": result.timing.postprocessing_s,
                                    "validation_s": result.timing.validation_s,
                                    "feature_cost_total_s": sum(features.elapsed_s.values()),
                                    "path_json": result.path.model_dump_json(),
                                    **reference_columns,
                                }
                                for name, value in sorted(features.values.items()):
                                    row[f"feature__{name}"] = value
                                for name, value in sorted(features.elapsed_s.items()):
                                    row[f"feature_cost__{name}"] = value
                                for metric in result.validation.metrics:
                                    row[f"metric__{metric.metric_id}"] = metric.value
                            except KinematicModelError as error:
                                # 算法与机具不匹配（如 RS 之于不可倒车车辆）是 NOT_APPLICABLE
                                # 不是崩溃：失败是数据，但失败类别必须分对。
                                row = _failure_row(
                                    key, record, run_instance_id, vehicle_index, config,
                                    RunStatus.NOT_APPLICABLE, error, reference_columns, features,
                                )
                            except ValueError as error:
                                # 真实地块实测（2026-08-21 探针）：3 块小 EE 地在 8/12 米地头下
                                # main_field 塌缩（coverage/stages/headland.py 的固定消息），
                                # 30/390 全 crash。算法在该实例上给不出解，与机具不匹配
                                # 同属 NOT_APPLICABLE——crash 要归零，不是可接受状态。
                                # 只认这一个消息标记：其余 ValueError 仍走 CRASH，不许扩大豁免面。
                                status = RunStatus.NOT_APPLICABLE if "塌缩" in str(error) else RunStatus.CRASH
                                row = _failure_row(
                                    key, record, run_instance_id, vehicle_index, config,
                                    status, error, reference_columns, features,
                                )
                            except Exception as error:
                                row = _failure_row(
                                    key, record, run_instance_id, vehicle_index, config,
                                    RunStatus.CRASH, error, reference_columns, features,
                                )
                            _append_checkpoint(checkpoint, row)
                            prior[key] = row
                            produced += 1
                            if stop_after is not None and produced >= stop_after:
                                return {"interrupted": True, "n_new": produced}

        selected = tuple(prior[key] for key in current_keys)
        _write_parquet(selected, root / "runs.parquet")
        counts: dict[str, int] = {}
        for row in selected:
            status = str(row["runstatus"])
            counts[status] = counts.get(status, 0) + 1
        nominal_pool = len(configs)
        effective_by_instance: dict[str, int] = {}
        for row in selected:
            if row["runstatus"] == RunStatus.OK.value:
                instance_id = str(row["instance_id"])
                effective_by_instance[instance_id] = effective_by_instance.get(instance_id, 0) + 1
        manifest_base = {
            "corpus_hash": content_hash({
                "record_hashes": sorted(field_record_hash(record) for record in records)
            }),
            "protocol_hash": protocol_hash,
            "benchmark_protocol_hash": benchmark_protocol.spec_hash(),
            "code_version": {"commit": code_version.commit, "dirty": code_version.dirty, "source_tree_hash": code_version.source_tree_hash},
            "licenses": {record.field_id: record.license.value for record in records},
            "contains_non_commercial": any(
                record.license is DatasetLicense.NON_COMMERCIAL for record in records
            ),
            "license_warning": (
                "本语料包含仅限非商业使用的数据"
                if any(record.license is DatasetLicense.NON_COMMERCIAL for record in records)
                else None
            ),
            "n_runs": len(selected),
            "runstatus_counts": counts,
            "nominal_pool_size": nominal_pool,
            "pool_hash": pool_hash(config.config_id() for config in configs),
            "pool_file_sha256": pool_file_sha256,
            "hypervolume_reference": benchmark_protocol.hypervolume_reference.model_dump(mode="json"),
            "hypervolume_reference_scope": "per-instance-analytic",
            "effective_pool_size_by_instance": effective_by_instance,
            "row_offsets_rad": list(corpus_protocol.row_offsets_rad),
            "row_spacings_m": list(corpus_protocol.row_spacings_m),
            "cv_folds": corpus_protocol.cv_folds,
        }
        manifest_hash = content_hash(manifest_base)
        manifest = {**manifest_base, "manifest_hash": manifest_hash}
        (root / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        _write_artifact_ledger(root / "ledger.jsonl", manifest_hash, selected)
        return manifest
