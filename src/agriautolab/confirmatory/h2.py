"""D6/H2：冻结二维农业 CPP 协议下的田内偏移处理效应。"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
import statistics
from pathlib import Path
from typing import Iterable, Sequence

from agriautolab.confirmatory.h1 import build_front_instance
from agriautolab.confirmatory.stats import distribution_summary


@dataclass(frozen=True)
class OffsetFrontInstance:
    """One complete nominal-pool instance, annotated with its frozen design cell."""

    field_id: str
    instance_id: str
    vehicle_index: int
    offset_rad: float
    spacing_m: float
    row_angle_vs_principal: float | None
    front_size: int | None


@dataclass(frozen=True)
class OffsetBinEstimate:
    offset_rad: float
    n_instances: int
    n_defined_front_instances: int
    median_front_size: float | None


@dataclass(frozen=True)
class H2FieldEstimate:
    field_id: str
    n_instances: int
    n_defined_front_instances: int
    n_defined_offset_bins: int
    constant_response: bool | None
    spearman_rho: float | None
    median_row_angle_vs_principal: float | None
    median_defined_front_size: float | None
    offset_bins: tuple[OffsetBinEstimate, ...]


def _one_optional_finite_float(rows: Sequence[dict], key: str, instance_id: str) -> float | None:
    # Failure rows in v7 may carry null feature cells.  Consume the unique recorded
    # value instead of requiring all 13 nominal-config rows to repeat it.
    normalized = [float(value) for row in rows if (value := row.get(key)) is not None]
    if not normalized:
        return None
    if not all(math.isfinite(value) for value in normalized):
        raise ValueError(f"{instance_id}: {key} 必须有限")
    if any(value != normalized[0] for value in normalized[1:]):
        raise ValueError(f"{instance_id}: 同一 instance 的 {key} 不一致")
    return normalized[0]


def _parse_design_cell(instance_id: str, field_id: str, vehicle_index: int) -> tuple[float, float]:
    """Parse the runner's frozen ``field:mode:offset:spacing:vehicle:i`` identity."""
    parts = instance_id.rsplit(":", 5)
    if len(parts) != 6:
        raise ValueError(f"instance_id 不符合冻结结构：{instance_id}")
    embedded_field, direction_mode, offset_text, spacing_text, vehicle_label, vehicle_text = parts
    if embedded_field != field_id:
        raise ValueError(f"{instance_id}: instance_id 内 field 与列 field_id 不一致")
    if direction_mode != "principal_axis" or vehicle_label != "vehicle":
        raise ValueError(f"{instance_id}: H2 只接受 principal_axis 冻结场景身份")
    try:
        parsed_vehicle = int(vehicle_text)
        offset = float(offset_text)
        spacing = float(spacing_text)
    except ValueError as error:
        raise ValueError(f"{instance_id}: offset/spacing/vehicle 不可解析") from error
    if parsed_vehicle != vehicle_index:
        raise ValueError(f"{instance_id}: instance_id 内 vehicle 与列 vehicle_index 不一致")
    if not math.isfinite(offset) or not math.isfinite(spacing):
        raise ValueError(f"{instance_id}: offset/spacing 必须有限")
    return offset, spacing


def build_offset_front_instance(
    rows: Sequence[dict],
    nominal_config_ids: Iterable[str],
) -> OffsetFrontInstance:
    """Recompute one Pareto front and bind it to the design offset, never a CV fold."""
    front = build_front_instance(rows, nominal_config_ids)
    offset, spacing = _parse_design_cell(front.instance_id, front.field_id, front.vehicle_index)
    row_angle = _one_optional_finite_float(rows, "feature__row_angle_vs_principal", front.instance_id)
    if front.front_size is not None and row_angle is None:
        raise ValueError(f"{front.instance_id}: 有定义前沿却无 row_angle_vs_principal")
    return OffsetFrontInstance(
        field_id=front.field_id,
        instance_id=front.instance_id,
        vehicle_index=front.vehicle_index,
        offset_rad=offset,
        spacing_m=spacing,
        row_angle_vs_principal=row_angle,
        front_size=front.front_size,
    )


def load_offset_front_instances(
    runs_parquet: str | Path,
    nominal_config_ids: Iterable[str],
) -> tuple[OffsetFrontInstance, ...]:
    """Scan only H2 columns and independently recompute every observed-OK front."""
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
        "feature__row_angle_vs_principal",
    ]
    dataset = ds.dataset(str(runs_parquet), format="parquet")
    missing = sorted(set(columns) - set(dataset.schema.names))
    if missing:
        raise ValueError(f"runs.parquet 缺少 H2 所需列：{missing}")
    grouped: dict[str, list[dict]] = {}
    for batch in dataset.scanner(columns=columns).to_batches():
        for row in batch.to_pylist():
            grouped.setdefault(str(row["instance_id"]), []).append(row)
    if not grouped:
        raise ValueError("runs.parquet 不含运行行")
    nominal = tuple(str(config_id) for config_id in nominal_config_ids)
    return tuple(build_offset_front_instance(grouped[key], nominal) for key in sorted(grouped))


def _strict_finite_grid(values: Iterable[float], *, name: str, size: int) -> tuple[float, ...]:
    grid = tuple(float(value) for value in values)
    if len(grid) != size or len(set(grid)) != size:
        raise ValueError(f"{name} 必须是 {size} 个不重复档位")
    if not all(math.isfinite(value) for value in grid):
        raise ValueError(f"{name} 必须全部有限")
    if grid != tuple(sorted(grid)):
        raise ValueError(f"{name} 必须按冻结的升序给出")
    return grid


def _spearman_nonconstant(x: Sequence[float], y: Sequence[float]) -> float:
    from scipy.stats import spearmanr

    result = spearmanr(x, y)
    rho = float(result.statistic)
    if not math.isfinite(rho):
        raise ValueError("Spearman rho 非有限；常数响应必须由 Amendment 05 分支处理")
    if rho < -1.0 - 1e-12 or rho > 1.0 + 1e-12:
        raise ValueError(f"Spearman rho 越界：{rho}")
    return min(1.0, max(-1.0, rho))


def wilcoxon_greater_pratt(values: Iterable[float], *, null_value: float) -> dict:
    """One-sided Wilcoxon with Pratt ranking so Amendment-05 zero rhos remain in n.

    H1's already-sealed analysis deliberately remains on ``zero_method='wilcox'``.
    H2 needs a distinct rule: constant within-field responses are defined as rho=0
    and must enter the signed-rank sample.  Pratt ranks zeros with the full sample,
    while their own ranks make no positive or negative contribution.
    """
    import numpy as np
    from scipy import __version__ as scipy_version
    from scipy.stats import wilcoxon

    array = np.asarray(tuple(float(value) for value in values), dtype=float)
    if array.size == 0:
        raise ValueError("Wilcoxon 不能消费空样本")
    if not np.isfinite(array).all() or not math.isfinite(null_value):
        raise ValueError("Wilcoxon 只接受有限值")
    differences = array - float(null_value)
    n_zero = int(np.count_nonzero(differences == 0.0))
    common = {
        "alternative": "greater",
        "null_value": float(null_value),
        "zero_method": "pratt",
        "zero_rule": "Amendment_05_constant_response_rho_zero_retained_in_ranked_sample",
        "correction": False,
        "method": "approx",
        "scipy_version": scipy_version,
        "n": int(array.size),
        "n_zero_differences": n_zero,
        "n_nonzero_differences": int(array.size - n_zero),
    }
    if n_zero == array.size:
        return {
            **common,
            "statistic": 0.0,
            "pvalue": 1.0,
            "zstatistic": None,
            "all_differences_zero": True,
        }
    result = wilcoxon(
        differences,
        zero_method="pratt",
        correction=False,
        alternative="greater",
        method="approx",
    )
    zstatistic = getattr(result, "zstatistic", None)
    return {
        **common,
        "statistic": float(result.statistic),
        "pvalue": float(result.pvalue),
        "zstatistic": None if zstatistic is None else float(zstatistic),
        "all_differences_zero": False,
    }


def field_effects(
    instances: Sequence[OffsetFrontInstance],
    *,
    expected_offsets_rad: Iterable[float],
    expected_spacings_m: Iterable[float],
    expected_vehicle_indices: Iterable[int] = (0, 1),
    expected_field_ids: Iterable[str] | None = None,
) -> tuple[H2FieldEstimate, ...]:
    """Build Amendment 04/05 field effects after enforcing the full 5×2×2 design."""
    offsets = _strict_finite_grid(expected_offsets_rad, name="offset grid", size=5)
    spacings = _strict_finite_grid(expected_spacings_m, name="spacing grid", size=2)
    vehicles = tuple(int(value) for value in expected_vehicle_indices)
    if len(vehicles) != 2 or len(set(vehicles)) != 2:
        raise ValueError("vehicle grid 必须是 2 个不重复索引")

    by_field: dict[str, list[OffsetFrontInstance]] = {}
    seen_instances: set[str] = set()
    for instance in instances:
        if instance.instance_id in seen_instances:
            raise ValueError(f"重复 instance_id：{instance.instance_id}")
        seen_instances.add(instance.instance_id)
        by_field.setdefault(instance.field_id, []).append(instance)

    if expected_field_ids is not None:
        expected_fields = frozenset(str(field_id) for field_id in expected_field_ids)
        actual_fields = frozenset(by_field)
        if actual_fields != expected_fields:
            raise ValueError(
                f"field universe 不一致：missing={sorted(expected_fields-actual_fields)}, "
                f"extra={sorted(actual_fields-expected_fields)}"
            )
    if not by_field:
        raise ValueError("H2 至少需要一块田")

    expected_cells = frozenset(
        (offset, spacing, vehicle)
        for offset in offsets
        for spacing in spacings
        for vehicle in vehicles
    )
    estimates: list[H2FieldEstimate] = []
    for field_id in sorted(by_field):
        rows = by_field[field_id]
        actual_cells: dict[tuple[float, float, int], OffsetFrontInstance] = {}
        for row in rows:
            if row.front_size is not None and row.row_angle_vs_principal is None:
                raise ValueError(f"{row.instance_id}: 有定义前沿却无 row_angle_vs_principal")
            cell = (float(row.offset_rad), float(row.spacing_m), int(row.vehicle_index))
            if cell in actual_cells:
                raise ValueError(f"{field_id}: 重复设计单元 {cell}")
            actual_cells[cell] = row
        actual_cell_set = frozenset(actual_cells)
        if actual_cell_set != expected_cells:
            raise ValueError(
                f"{field_id}: 5×2×2 设计矩阵不完整："
                f"missing={sorted(expected_cells-actual_cell_set)}, extra={sorted(actual_cell_set-expected_cells)}"
            )

        bins: list[OffsetBinEstimate] = []
        for offset in offsets:
            bin_rows = [row for row in rows if row.offset_rad == offset]
            defined = [int(row.front_size) for row in bin_rows if row.front_size is not None]
            bins.append(OffsetBinEstimate(
                offset_rad=offset,
                n_instances=len(bin_rows),
                n_defined_front_instances=len(defined),
                median_front_size=None if not defined else float(statistics.median(defined)),
            ))

        analyzable_bins = [item for item in bins if item.median_front_size is not None]
        if len(analyzable_bins) >= 3:
            responses = [float(item.median_front_size) for item in analyzable_bins]
            constant_response = len(set(responses)) == 1
            # Amendment 05: a constant response is a genuine zero effect, never a missing rho.
            rho = 0.0 if constant_response else _spearman_nonconstant(
                [item.offset_rad for item in analyzable_bins], responses
            )
        else:
            constant_response = None
            rho = None

        defined_fronts = [int(row.front_size) for row in rows if row.front_size is not None]
        row_angles = [
            float(row.row_angle_vs_principal)
            for row in rows
            if row.row_angle_vs_principal is not None
        ]
        if not all(math.isfinite(value) for value in row_angles):
            raise ValueError(f"{field_id}: row_angle_vs_principal 必须有限")
        estimates.append(H2FieldEstimate(
            field_id=field_id,
            n_instances=len(rows),
            n_defined_front_instances=len(defined_fronts),
            n_defined_offset_bins=len(analyzable_bins),
            constant_response=constant_response,
            spearman_rho=rho,
            median_row_angle_vs_principal=(
                None if not row_angles else float(statistics.median(row_angles))
            ),
            median_defined_front_size=(
                None if not defined_fronts else float(statistics.median(defined_fronts))
            ),
            offset_bins=tuple(bins),
        ))
    return tuple(estimates)


def _deprecated_cross_field_descriptive(estimates: Sequence[H2FieldEstimate]) -> dict:
    paired = [
        item
        for item in estimates
        if item.median_defined_front_size is not None
        and item.median_row_angle_vs_principal is not None
    ]
    x = [float(item.median_row_angle_vs_principal) for item in paired]
    y = [float(item.median_defined_front_size) for item in paired]
    rho: float | None
    reason: str | None
    if len(paired) < 2:
        rho, reason = None, "fewer_than_2_defined_field_pairs"
    elif len(set(x)) == 1:
        rho, reason = None, "constant_field_level_feature"
    elif len(set(y)) == 1:
        rho, reason = None, "constant_field_level_response"
    else:
        rho, reason = _spearman_nonconstant(x, y), None
    return {
        "status": "descriptive_only__not_a_confirmatory_test",
        "n_field_pairs": len(paired),
        "n_fields_missing_defined_front_response": sum(
            item.median_defined_front_size is None for item in estimates
        ),
        "n_fields_missing_feature_median": sum(
            item.median_row_angle_vs_principal is None for item in estimates
        ),
        "feature_distribution": None if not x else distribution_summary(x),
        "response_distribution": None if not y else distribution_summary(y),
        "spearman_rho": rho,
        "undefined_reason": reason,
        "interpretation": (
            "Amendment 03 cross-field estimand is downgraded: field-level X is a design constant plus "
            "principal-axis estimation noise and has no cross-field explanatory interpretation."
        ),
    }


def _sensitivity(values: Sequence[float], *, n_constant: int) -> dict:
    if not values:
        return {
            "status": "secondary_sensitivity__not_in_holm_family",
            "available": False,
            "n_fields": 0,
            "n_constant_response_fields": 0,
            "rho_distribution": None,
            "wilcoxon": None,
            "reason": "no_fields_with_all_5_defined_offset_bins",
        }
    return {
        "status": "secondary_sensitivity__not_in_holm_family",
        "available": True,
        "n_fields": len(values),
        "n_constant_response_fields": n_constant,
        "rho_distribution": distribution_summary(values),
        "wilcoxon": wilcoxon_greater_pratt(values, null_value=0.0),
        "reason": None,
    }


def analyze_h2(
    estimates: Sequence[H2FieldEstimate],
    *,
    alpha_family: float = 0.01,
    family_size: int = 3,
) -> dict:
    """Run H2; exact Holm adjustment remains pending until H3 supplies its p-value."""
    if not estimates:
        raise ValueError("H2 至少需要一块田")
    if family_size < 1 or not (0.0 < alpha_family < 1.0):
        raise ValueError("Holm family 参数非法")
    field_ids = [item.field_id for item in estimates]
    if len(field_ids) != len(set(field_ids)):
        raise ValueError("H2 field estimates 含重复 field_id")

    analyzable = [item for item in estimates if item.spearman_rho is not None]
    if not analyzable:
        raise ValueError("H2 没有 >=3 个定义偏移档的可分析田")
    if any(item.n_defined_offset_bins not in (3, 4, 5) for item in analyzable):
        raise ValueError("可分析田的定义偏移档数必须为 3/4/5")
    if any(item.constant_response is None for item in analyzable):
        raise ValueError("可分析田必须明确 constant_response")

    rhos = [float(item.spearman_rho) for item in analyzable]
    test = wilcoxon_greater_pratt(rhos, null_value=0.0)
    raw_p = float(test["pvalue"])
    conservative_adjusted_upper = min(1.0, family_size * raw_p)
    counts = {
        bins: sum(item.n_defined_offset_bins == bins for item in analyzable)
        for bins in (3, 4, 5)
    }
    full_five = [item for item in analyzable if item.n_defined_offset_bins == 5]
    full_five_rhos = [float(item.spearman_rho) for item in full_five]
    zero_ok_fields = sum(item.n_defined_front_instances == 0 for item in estimates)
    primary_distribution = distribution_summary(rhos)
    return {
        "estimand": (
            "within each field, median Pareto-front size in each defined design-offset bin "
            "(2 spacings x 2 vehicles), followed by within-field Spearman rho; constant responses equal rho=0"
        ),
        "scope_validity": (
            "Controlled within-field treatment effect under the frozen 2-D agricultural CPP simulation protocol; "
            "row direction is a scanned scenario factor, not an observed production-field crop direction."
        ),
        "n_all_fields": len(estimates),
        "n_analyzable_fields": len(analyzable),
        "n_fewer_than_3_defined_offset_bins": len(estimates) - len(analyzable),
        "n_zero_ok_fields": zero_ok_fields,
        "zero_ok_field_share": zero_ok_fields / len(estimates),
        "n_3_bins": counts[3],
        "n_4_bins": counts[4],
        "n_5_bins": counts[5],
        "n_constant_response_fields": sum(bool(item.constant_response) for item in analyzable),
        "primary_rho_distribution": primary_distribution,
        "wilcoxon": test,
        "full_5_bin_sensitivity": _sensitivity(
            full_five_rhos,
            n_constant=sum(bool(item.constant_response) for item in full_five),
        ),
        "deprecated_cross_field_descriptive": _deprecated_cross_field_descriptive(estimates),
        "multiplicity": {
            "family": ["H1", "H2", "H3"],
            "family_size": family_size,
            "familywise_alpha": alpha_family,
            "exact_holm_adjusted_p": None,
            "exact_holm_status": "pending_H3_pvalue_for_final_ordering",
            "bonferroni_upper_bound_on_adjusted_p": conservative_adjusted_upper,
            "holm_rejection_guaranteed_regardless_pending_pvalue": (
                conservative_adjusted_upper <= alpha_family
            ),
        },
        "preregistered_failure_checks": {
            "median_within_field_rho_le_zero": primary_distribution["median"] <= 0.0,
            "n_analyzable_fields_below_150": len(analyzable) < 150,
        },
        "fields": [asdict(item) for item in estimates],
    }
