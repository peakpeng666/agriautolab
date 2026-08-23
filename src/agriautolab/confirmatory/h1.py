"""D5/H1：田级 Pareto 前沿中位数的冻结确认性分析。"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from pathlib import Path
import statistics
from typing import Iterable, Sequence

from agriautolab.confirmatory.stats import distribution_summary, wilcoxon_greater
from agriautolab.corpus.derived_status import derive_status
from agriautolab.pareto.front import ObjectiveVector, pareto_front


@dataclass(frozen=True)
class FrontInstance:
    field_id: str
    instance_id: str
    vehicle_index: int
    front_size: int | None


@dataclass(frozen=True)
class H1FieldEstimate:
    field_id: str
    n_instances: int
    n_defined_front_instances: int
    n_zero_ok_instances: int
    median_defined_front_size: float | None
    median_zero_as_zero_front_size: float


def _one(rows: Sequence[dict], key: str):
    values = {row.get(key) for row in rows}
    if len(values) != 1:
        raise ValueError(f"同一 instance 的 {key} 不一致：{sorted(map(str, values))}")
    value = next(iter(values))
    if value is None:
        raise ValueError(f"同一 instance 的 {key} 缺失")
    return value


def build_front_instance(rows: Sequence[dict], nominal_config_ids: Iterable[str]) -> FrontInstance:
    """从完整 instance×nominal-config 矩阵重算 observed-OK Pareto 前沿。"""
    if not rows:
        raise ValueError("instance rows 不能为空")
    expected = frozenset(str(config_id) for config_id in nominal_config_ids)
    if not expected:
        raise ValueError("nominal 配置池不能为空")
    seen = [str(row.get("config_id")) for row in rows]
    if len(seen) != len(set(seen)):
        raise ValueError("同一 instance/config 出现重复运行行")
    if frozenset(seen) != expected:
        raise ValueError(
            "instance 运行矩阵不完整："
            f"missing={sorted(expected - set(seen))}, extra={sorted(set(seen) - expected)}"
        )

    instance_id = str(_one(rows, "instance_id"))
    field_id = str(_one(rows, "field_id"))
    vehicle_index = int(_one(rows, "vehicle_index"))
    points: dict[str, ObjectiveVector] = {}
    for row in rows:
        if derive_status(str(row["runstatus"]), row.get("failure_reason")) != "ok":
            continue
        config_id = str(row["config_id"])
        raw = (row.get("path_length"), row.get("headland_turns"), row.get("row_crossings"))
        if any(value is None for value in raw):
            raise ValueError(f"{instance_id}/{config_id}: derived_status=ok 但主目标缺失")
        values = tuple(float(value) for value in raw)
        if any(not math.isfinite(value) for value in values):
            raise ValueError(f"{instance_id}/{config_id}: 主目标必须有限")
        points[config_id] = ObjectiveVector(*values)

    front_size = len(pareto_front(points)) if points else None
    return FrontInstance(field_id, instance_id, vehicle_index, front_size)


def load_front_instances(
    runs_parquet: str | Path,
    nominal_config_ids: Iterable[str],
) -> tuple[FrontInstance, ...]:
    """只扫描 H1/H2 所需列；状态一律由 ``derive_status`` 决定。"""
    import pyarrow.dataset as ds

    columns = [
        "instance_id",
        "field_id",
        "vehicle_index",
        "config_id",
        "runstatus",
        "failure_reason",
        "path_length",
        "headland_turns",
        "row_crossings",
    ]
    dataset = ds.dataset(str(runs_parquet), format="parquet")
    missing = sorted(set(columns) - set(dataset.schema.names))
    if missing:
        raise ValueError(f"runs.parquet 缺少 H1/H2 所需列：{missing}")
    grouped: dict[str, list[dict]] = {}
    for batch in dataset.scanner(columns=columns).to_batches():
        for row in batch.to_pylist():
            grouped.setdefault(str(row["instance_id"]), []).append(row)
    if not grouped:
        raise ValueError("runs.parquet 不含运行行")
    nominal = tuple(str(config_id) for config_id in nominal_config_ids)
    return tuple(build_front_instance(grouped[key], nominal) for key in sorted(grouped))


def field_estimates(
    instances: Sequence[FrontInstance],
    *,
    expected_field_ids: Iterable[str] | None = None,
) -> tuple[H1FieldEstimate, ...]:
    """形成修正案 03 的主口径与零记 0 敏感性口径。"""
    by_field: dict[str, list[FrontInstance]] = {}
    seen_instances: set[str] = set()
    for instance in instances:
        if instance.instance_id in seen_instances:
            raise ValueError(f"重复 instance_id：{instance.instance_id}")
        seen_instances.add(instance.instance_id)
        by_field.setdefault(instance.field_id, []).append(instance)

    if expected_field_ids is not None:
        expected = frozenset(str(field_id) for field_id in expected_field_ids)
        actual = frozenset(by_field)
        if actual != expected:
            raise ValueError(f"field universe 不一致：missing={sorted(expected-actual)}, extra={sorted(actual-expected)}")

    result = []
    for field_id in sorted(by_field):
        rows = by_field[field_id]
        defined = [int(row.front_size) for row in rows if row.front_size is not None]
        zero_as_zero = [0 if row.front_size is None else int(row.front_size) for row in rows]
        result.append(H1FieldEstimate(
            field_id=field_id,
            n_instances=len(rows),
            n_defined_front_instances=len(defined),
            n_zero_ok_instances=len(rows) - len(defined),
            median_defined_front_size=None if not defined else float(statistics.median(defined)),
            median_zero_as_zero_front_size=float(statistics.median(zero_as_zero)),
        ))
    return tuple(result)


def analyze_h1(
    estimates: Sequence[H1FieldEstimate],
    *,
    alpha_family: float = 0.01,
    family_size: int = 3,
) -> dict:
    """执行 H1 主检验；Holm 精确调整明确等待 H2/H3 全部 p 值。"""
    if not estimates:
        raise ValueError("H1 至少需要一块田")
    if family_size < 1 or not (0.0 < alpha_family < 1.0):
        raise ValueError("Holm family 参数非法")
    main_values = [item.median_defined_front_size for item in estimates if item.median_defined_front_size is not None]
    sensitivity_values = [item.median_zero_as_zero_front_size for item in estimates]
    if not main_values:
        raise ValueError("H1 没有任何可分析田")
    main = [float(value) for value in main_values]
    zero_fields = sum(item.median_defined_front_size is None for item in estimates)
    test = wilcoxon_greater(main, null_value=1.0)
    raw_p = float(test["pvalue"])
    conservative_adjusted_upper = min(1.0, family_size * raw_p)
    holm_guaranteed = conservative_adjusted_upper <= alpha_family
    main_distribution = distribution_summary(main)
    single_front_share = sum(value == 1.0 for value in main) / len(main)
    zero_field_share = zero_fields / len(estimates)
    return {
        "estimand": (
            "per-field median Pareto-front size over instances with at least one derived-status OK config; "
            "fields with no defined front excluded from the primary test"
        ),
        "n_all_fields": len(estimates),
        "n_analyzable_fields": len(main),
        "n_zero_ok_fields": zero_fields,
        "zero_ok_field_share": zero_field_share,
        "primary_distribution": main_distribution,
        "sensitivity_zero_instance_as_front_zero_distribution": distribution_summary(sensitivity_values),
        "single_front_field_share_primary": single_front_share,
        "wilcoxon": test,
        "multiplicity": {
            "family": ["H1", "H2", "H3"],
            "family_size": family_size,
            "familywise_alpha": alpha_family,
            "exact_holm_adjusted_p": None,
            "exact_holm_status": "pending_H2_H3_pvalues_for_final_ordering",
            "bonferroni_upper_bound_on_adjusted_p": conservative_adjusted_upper,
            "holm_rejection_guaranteed_regardless_pending_pvalues": holm_guaranteed,
        },
        "preregistered_failure_checks": {
            "primary_field_median_equals_1": main_distribution["median"] == 1.0,
            "more_than_90pct_primary_fields_equal_1": single_front_share > 0.90,
            "zero_ok_field_share_above_30pct_interpretation_limit": zero_field_share > 0.30,
        },
        "fields": [asdict(item) for item in estimates],
    }

