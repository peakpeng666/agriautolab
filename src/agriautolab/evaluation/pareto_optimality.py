"""Per-field Pareto front median confirmatory analysis (primary evaluation track)."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from pathlib import Path
import statistics
from typing import Iterable, Sequence

from agriautolab.evaluation.stats import distribution_summary, wilcoxon_greater
from agriautolab.pipeline.corpus.derived_status import derive_status
from agriautolab.pipeline.pareto.front import ObjectiveVector, pareto_front


@dataclass(frozen=True)
class FrontInstance:
    field_id: str
    instance_id: str
    vehicle_index: int
    front_size: int | None


@dataclass(frozen=True)
class ParetoFrontEstimate:
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
    """Scan only the columns the analysis needs; status always comes from ``derive_status``."""
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
        raise ValueError(f"Missing required evaluation columns in runs dataset: {missing}")
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
) -> tuple[ParetoFrontEstimate, ...]:
    """Build the primary and zero-as-zero sensitivity estimates per field."""
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
        result.append(ParetoFrontEstimate(
            field_id=field_id,
            n_instances=len(rows),
            n_defined_front_instances=len(defined),
            n_zero_ok_instances=len(rows) - len(defined),
            median_defined_front_size=None if not defined else float(statistics.median(defined)),
            median_zero_as_zero_front_size=float(statistics.median(zero_as_zero)),
        ))
    return tuple(result)


def evaluate_pareto_optimality(
    estimates: Sequence[ParetoFrontEstimate],
    *,
    alpha_family: float = 0.01,
    family_size: int = 3,
) -> dict:
    """Run the primary Pareto front-size test; exact Holm adjustment waits for the other family p-values."""
    if not estimates:
        raise ValueError("At least one field is required for Pareto front evaluation.")
    if family_size < 1 or not (0.0 < alpha_family < 1.0):
        raise ValueError("Invalid Holm family parameters")
    main_values = [item.median_defined_front_size for item in estimates if item.median_defined_front_size is not None]
    sensitivity_values = [item.median_zero_as_zero_front_size for item in estimates]
    if not main_values:
        raise ValueError("No analyzable fields remain for Pareto front evaluation.")
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
            "family": ["pareto_optimality", "feature_effects", "recommender_eval"],
            "family_size": family_size,
            "familywise_alpha": alpha_family,
            "exact_holm_adjusted_p": None,
            "holm_adjusted_p_status": "awaiting_downstream_p_values",
            "bonferroni_upper_bound_on_adjusted_p": conservative_adjusted_upper,
            "holm_guaranteed_rejection": holm_guaranteed,
        },
        "failure_thresholds": {
            "primary_field_median_equals_1": main_distribution["median"] == 1.0,
            "more_than_90pct_primary_fields_equal_1": single_front_share > 0.90,
            "zero_ok_field_share_above_30pct_interpretation_limit": zero_field_share > 0.30,
        },
        "fields": [asdict(item) for item in estimates],
    }



# Legacy alias
analyze_h1 = evaluate_pareto_optimality
