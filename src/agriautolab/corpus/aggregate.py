"""语料级 Pareto 聚合：池身份、有效池与参考点永远随结果一起返回。

两条作用域纪律：

1. 前沿大小不可跨有效池比较：不同实例的 NOT_APPLICABLE 数量不同，
   有效池（产出 ok 行的配置数）随之不同。前沿大小必须与有效池、
   pool_hash 一起记录；有效池 <= 1 的实例不进单点前沿统计（单点前沿
   在那里是"没得选"，不是"无权衡"），有效池 = 0 的实例连前沿都无法
   定义，必须单列计数，不许在 n_instances 里静默消失。
2. 原始超体积不可跨实例聚合：HV 的量纲随地块大小走（参考点固定时
   小地块 HV 反而大），聚合它画出的是地块面积分布。跨实例只聚合
   hv / Π(ref_i)——分母是解析参考点的乘积，纯协议侧、不随池或观测
   变化。归一化分母**不用观测 ideal**：观测 utopia 会随池扩张而移动，
   把 Dolan-Moré 式的池依赖从参考点搬进归一化，等于换了个地方犯同一个错。
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass
from pathlib import Path

from agriautolab.contracts.protocol import HypervolumeReference
from agriautolab.corpus.derived_status import derive_status
from agriautolab.pareto.front import ObjectiveVector, pareto_front, pool_hash
from agriautolab.pareto.hypervolume import hypervolume

_REFERENCE_COLUMNS = ("ref_path_length", "ref_headland_turns", "ref_row_crossings")


@dataclass(frozen=True)
class CorpusParetoSummary:
    """前沿分布与有效池同序返回；reference_scope 说明参考点来自哪里。"""

    n_instances: int                                   # 有效池 >= 1 的实例数（前沿分布的定义域）
    n_instances_in_corpus: int                         # parquet 中出现过的实例总数（任何状态）
    n_instances_with_zero_ok_configs: int              # 有效池 = 0：无前沿可言，单列不许静默消失
    pool_hash: str
    front_size_distribution: tuple[int, ...]
    front_instance_ids: tuple[str, ...]                # 与上行同序（实例名对齐，供 manifest 等消费方映射）
    effective_pool_size_by_instance: tuple[int, ...]   # 与 front_size_distribution 同序
    front_size_ratio_distribution: tuple[float, ...]   # front_size / effective_pool，同序
    front_size_median: float
    n_instances_with_singleton_front: int              # 只统计有效池 >= 2 的实例
    n_singleton_fronts_excluded: int                   # 因有效池 <= 1 被排除出上一行的数量
    n_instances_with_degenerate_pool: int              # 有效池 <= 1（含 0）
    hypervolume_by_instance: tuple[float, ...]         # 原始米制 HV：不可跨实例聚合
    hypervolume_normalized_by_reference: tuple[float, ...]   # hv / Π(ref_i)，无量纲
    reference_by_instance: tuple[HypervolumeReference, ...]
    reference_scope: str                               # "per-instance-analytic" | "global-fallback"


def ecdf(values: tuple[float, ...]) -> tuple[tuple[float, ...], tuple[float, ...]]:
    """COCO/BBOB 风格的经验分布函数；不使用随 solver 集合改变基线的性能剖面。"""
    ordered = tuple(sorted(values))
    if not ordered:
        return (), ()
    n = len(ordered)
    return ordered, tuple((index + 1) / n for index in range(n))


def _reference_of(row: dict, fallback: HypervolumeReference | None, has_ref_columns: bool) -> HypervolumeReference:
    if not has_ref_columns:
        if fallback is None:
            raise ValueError(
                "runs.parquet 没有逐实例参考点列（ref_path_length/...），"
                "且未提供全局参考点；语料运行请用带逐实例参考点列的 runner 重新生成"
            )
        return fallback
    return HypervolumeReference(
        path_length=float(row["ref_path_length"]),
        headland_turns=float(row["ref_headland_turns"]),
        row_crossings=float(row["ref_row_crossings"]),
        basis=str(row.get("ref_basis") or "per-instance"),
    )


def summarize_pareto(runs_parquet: str | Path, *, reference: HypervolumeReference | None = None) -> CorpusParetoSummary:
    """汇总语料前沿。优先读 parquet 自带的逐实例解析参考点；老文件退回全局参考点。

    全局回退只在参考点确实逐实例不可得时使用（reference_scope 会如实标注）——
    固定参考点下的 HV 跨实例聚合测的是地块大小，不是算法质量。
    """
    try:
        import pyarrow.parquet as pq
    except ImportError as error:
        raise RuntimeError("Pareto 语料聚合需要项目声明的 pyarrow>=16") from error
    rows = pq.read_table(runs_parquet).to_pylist()
    config_ids = sorted({str(row["config_id"]) for row in rows})
    has_ref_columns = bool(rows) and all(column in rows[0] for column in _REFERENCE_COLUMNS)

    # 状态一律经 derived_status（validator 事实优先于运行时归并，单一真相源）：
    # 零地头 carve 归并出的 not_applicable 若带 validator_rejected 理由，
    # 在这里按它真实的拒绝类参与统计，不许被读成「没跑过」。
    effective_pool: dict[str, int] = {}
    instances_in_corpus: set[str] = set()
    for row in rows:
        instance_id = str(row["instance_id"])
        instances_in_corpus.add(instance_id)
        if derive_status(str(row["runstatus"]), row.get("failure_reason")) == "ok":
            effective_pool[instance_id] = effective_pool.get(instance_id, 0) + 1

    reference_of_instance: dict[str, HypervolumeReference] = {}
    for row in rows:
        instance_id = str(row["instance_id"])
        if instance_id not in reference_of_instance:
            reference_of_instance[instance_id] = _reference_of(row, reference, has_ref_columns)

    by_instance: dict[str, dict[str, ObjectiveVector]] = {}
    for row in rows:
        if derive_status(str(row["runstatus"]), row.get("failure_reason")) != "ok":
            continue
        values = (row.get("path_length"), row.get("headland_turns"), row.get("row_crossings"))
        if any(value is None for value in values):
            continue
        by_instance.setdefault(str(row["instance_id"]), {})[str(row["config_id"])] = ObjectiveVector(*map(float, values))

    front_sizes: list[int] = []
    effective_sizes: list[int] = []
    ratios: list[float] = []
    hvs: list[float] = []
    hvs_normalized: list[float] = []
    references: list[HypervolumeReference] = []
    singleton = 0
    singleton_excluded = 0
    for instance_id in sorted(by_instance):
        points = by_instance[instance_id]
        effective = effective_pool.get(instance_id, len(points))
        instance_reference = reference_of_instance[instance_id]
        front = pareto_front(points)
        front_points = {config_id: points[config_id] for config_id in front}
        hv = hypervolume(front_points, reference=instance_reference)
        front_sizes.append(len(front))
        effective_sizes.append(effective)
        ratios.append(len(front) / effective if effective > 0 else 0.0)
        hvs.append(hv)
        reference_product = (
            instance_reference.path_length * instance_reference.headland_turns * instance_reference.row_crossings
        )
        hvs_normalized.append(hv / reference_product)
        references.append(instance_reference)
        if effective <= 1:
            singleton_excluded += 1 if len(front) == 1 else 0
        elif len(front) == 1:
            singleton += 1
    degenerate = sum(1 for instance_id in instances_in_corpus if effective_pool.get(instance_id, 0) <= 1)
    zero_ok = sum(1 for instance_id in instances_in_corpus if effective_pool.get(instance_id, 0) == 0)
    return CorpusParetoSummary(
        n_instances=len(by_instance),
        n_instances_in_corpus=len(instances_in_corpus),
        n_instances_with_zero_ok_configs=zero_ok,
        pool_hash=pool_hash(config_ids),
        front_size_distribution=tuple(front_sizes),
        front_instance_ids=tuple(sorted(by_instance)),
        effective_pool_size_by_instance=tuple(effective_sizes),
        front_size_ratio_distribution=tuple(ratios),
        front_size_median=statistics.median(front_sizes) if front_sizes else 0.0,
        n_instances_with_singleton_front=singleton,
        n_singleton_fronts_excluded=singleton_excluded,
        n_instances_with_degenerate_pool=degenerate,
        hypervolume_by_instance=tuple(hvs),
        hypervolume_normalized_by_reference=tuple(hvs_normalized),
        reference_by_instance=tuple(references),
        reference_scope="per-instance-analytic" if has_ref_columns else "global-fallback",
    )
