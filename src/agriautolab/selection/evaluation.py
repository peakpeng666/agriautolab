"""D3 选择评估：从冻结 v7 运行行构造无 oracle 泄漏的悔值表。"""

from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
from typing import Iterable, Sequence

from agriautolab.contracts.vehicle import VehicleSpec
from agriautolab.corpus.derived_status import derive_status
from agriautolab.pipeline.config import PipelineConfig
from agriautolab.pareto.preference_grid import PREFERENCE_GRID_V1
from agriautolab.selection.pools import static_applicable
from agriautolab.selection.protocol import SELECTION_FEATURE_IDS


@dataclass(frozen=True)
class SelectionInstance:
    """一个场景实例的特征、池身份和 22 偏好悔值。

    `regrets=None` 明确表示 O_x 为空：confirmatory H3 的 oracle 未定义。
    历史 v7 的异常失败行不保存 feature__*；若整个 O_x 为空且没有任何普通
    运行行可恢复特征，`features=None` 也必须保留该实例，而不是把困难样本删掉。
    """

    field_id: str
    instance_id: str
    vehicle_index: int
    features: tuple[float, ...] | None
    nominal: frozenset[str]
    applicable: frozenset[str]
    observed_ok: frozenset[str]
    regrets: tuple[tuple[str, tuple[float, ...]], ...] | None
    random_applicable: tuple[float, ...] | None
    random_nominal: tuple[float, ...] | None

    @property
    def analyzable(self) -> bool:
        return self.regrets is not None

    def regret_vector(self, config_id: str) -> tuple[float, ...]:
        if self.regrets is None:
            raise ValueError(f"{self.instance_id}: O_x 为空，confirmatory regret 未定义")
        for candidate_id, values in self.regrets:
            if candidate_id == config_id:
                return values
        raise KeyError(config_id)


@dataclass(frozen=True)
class FieldLoss:
    field_id: str
    mean_loss: float
    n_analyzable_instances: int
    n_zero_ok_instances: int


def _one_identity(rows: Sequence[dict], key: str):
    values = {row.get(key) for row in rows}
    if len(values) != 1:
        raise ValueError(f"同一 instance 的 {key} 不一致：{sorted(map(str, values))}")
    value = next(iter(values))
    if value is None:
        raise ValueError(f"同一 instance 的 {key} 缺失")
    return value


def _one_float(rows: Sequence[dict], key: str) -> float:
    values = {float(row[key]) for row in rows if row.get(key) is not None}
    if len(values) != 1:
        raise ValueError(f"同一 instance 的 {key} 必须有且只有一个非空值，得到 {len(values)} 个")
    value = next(iter(values))
    if not math.isfinite(value):
        raise ValueError(f"{key} 必须有限")
    return value


def _feature_vector(rows: Sequence[dict], *, required: bool) -> tuple[float, ...] | None:
    values: list[float] = []
    missing: list[str] = []
    for feature_id in SELECTION_FEATURE_IDS:
        key = f"feature__{feature_id}"
        observed = {float(row[key]) for row in rows if row.get(key) is not None}
        if len(observed) > 1:
            raise ValueError(f"同一 instance 的 {key} 出现多个值")
        if not observed:
            missing.append(key)
            continue
        value = next(iter(observed))
        if not math.isfinite(value):
            raise ValueError(f"{key} 必须有限")
        values.append(value)
    if missing:
        if required:
            raise ValueError(f"可分析 instance 缺少 selection 特征：{missing}")
        return None
    return tuple(values)


def _mean_vectors(vectors: Sequence[tuple[float, ...]]) -> tuple[float, ...]:
    if not vectors:
        raise ValueError("不能对空向量集合取均值")
    width = len(vectors[0])
    if any(len(vector) != width for vector in vectors):
        raise ValueError("向量维度不一致")
    return tuple(sum(vector[index] for vector in vectors) / len(vectors) for index in range(width))


def build_selection_instance(
    rows: Sequence[dict],
    configs: tuple[PipelineConfig, ...],
    vehicles: tuple[VehicleSpec, ...],
) -> SelectionInstance:
    """由一个完整 instance×nominal-config 矩阵构造冻结悔值表。"""
    if not rows:
        raise ValueError("instance rows 不能为空")
    instance_id = str(_one_identity(rows, "instance_id"))
    field_id = str(_one_identity(rows, "field_id"))
    vehicle_index = int(_one_identity(rows, "vehicle_index"))
    if vehicle_index < 0 or vehicle_index >= len(vehicles):
        raise ValueError(f"{instance_id}: 未知 vehicle_index={vehicle_index}")

    config_id_list = tuple(config.config_id() for config in configs)
    nominal = frozenset(config_id_list)
    if not nominal or len(nominal) != len(config_id_list):
        raise ValueError("nominal 配置池为空或 config_id 重复")
    row_config_ids = [str(row.get("config_id")) for row in rows]
    if len(row_config_ids) != len(set(row_config_ids)):
        raise ValueError(f"{instance_id}: 同一 config_id 出现重复运行行")
    if frozenset(row_config_ids) != nominal:
        raise ValueError(
            f"{instance_id}: nominal 运行矩阵不完整，"
            f"missing={sorted(nominal - set(row_config_ids))}, extra={sorted(set(row_config_ids) - nominal)}"
        )

    config_by_id = {config.config_id(): config for config in configs}
    applicable = frozenset(
        config_id
        for config_id, config in config_by_id.items()
        if static_applicable(config, vehicles[vehicle_index])
    )

    objectives: dict[str, tuple[float, float, float]] = {}
    for row in rows:
        config_id = str(row["config_id"])
        if derive_status(str(row["runstatus"]), row.get("failure_reason")) != "ok":
            continue
        raw = (row.get("path_length"), row.get("headland_turns"), row.get("row_crossings"))
        if any(value is None for value in raw):
            raise ValueError(f"{instance_id}/{config_id}: derived_status=ok 但主目标缺失")
        objective = tuple(float(value) for value in raw)
        if any(not math.isfinite(value) for value in objective):
            raise ValueError(f"{instance_id}/{config_id}: 主目标必须有限")
        objectives[config_id] = objective  # type: ignore[assignment]

    observed_ok = frozenset(objectives)
    if not observed_ok <= applicable:
        raise ValueError(f"{instance_id}: O ⊄ A：{sorted(observed_ok - applicable)}")
    if not applicable <= nominal:
        raise ValueError(f"{instance_id}: A ⊄ N：{sorted(applicable - nominal)}")

    if not observed_ok:
        return SelectionInstance(
            field_id=field_id,
            instance_id=instance_id,
            vehicle_index=vehicle_index,
            features=_feature_vector(rows, required=False),
            nominal=nominal,
            applicable=applicable,
            observed_ok=observed_ok,
            regrets=None,
            random_applicable=None,
            random_nominal=None,
        )

    features = _feature_vector(rows, required=True)
    assert features is not None
    reference = (
        _one_float(rows, "ref_path_length"),
        _one_float(rows, "ref_headland_turns"),
        _one_float(rows, "ref_row_crossings"),
    )
    if any(value <= 0.0 for value in reference):
        raise ValueError(f"{instance_id}: analytic reference 三维必须 >0")

    scalarized: dict[str, tuple[float, ...]] = {}
    for config_id, objective in objectives.items():
        normalized = tuple(value / ref for value, ref in zip(objective, reference))
        scalarized[config_id] = tuple(
            max(weight * value for weight, value in zip(preference, normalized))
            for preference in PREFERENCE_GRID_V1
        )
    oracle = tuple(
        min(values[index] for values in scalarized.values())
        for index in range(len(PREFERENCE_GRID_V1))
    )
    feasible_regrets = {
        config_id: tuple(value - oracle[index] for index, value in enumerate(values))
        for config_id, values in scalarized.items()
    }
    # Amendment 05: rejected/not-applicable config gets R_max(A_x,w)+1.
    # O⊆A，因此已定义的 A 内悔值正是 observed-OK regrets；若某偏好全部并列，max=0。
    penalty = tuple(
        max((values[index] for values in feasible_regrets.values()), default=0.0) + 1.0
        for index in range(len(PREFERENCE_GRID_V1))
    )
    regret_by_config = {config_id: feasible_regrets.get(config_id, penalty) for config_id in nominal}
    random_applicable = _mean_vectors([regret_by_config[config_id] for config_id in sorted(applicable)])
    random_nominal = _mean_vectors([regret_by_config[config_id] for config_id in sorted(nominal)])

    return SelectionInstance(
        field_id=field_id,
        instance_id=instance_id,
        vehicle_index=vehicle_index,
        features=features,
        nominal=nominal,
        applicable=applicable,
        observed_ok=observed_ok,
        regrets=tuple((config_id, regret_by_config[config_id]) for config_id in sorted(nominal)),
        random_applicable=random_applicable,
        random_nominal=random_nominal,
    )


def load_selection_instances(
    runs_parquet: str | Path,
    field_ids: Iterable[str],
    configs: tuple[PipelineConfig, ...],
    vehicles: tuple[VehicleSpec, ...],
) -> tuple[SelectionInstance, ...]:
    """只扫描明确给定的 field 集；D4 训练入口不得读取 holdout 行。

    使用 Arrow dataset predicate，而不是先把 61,100 行 materialize 后在 Python
    丢掉 holdout。返回值仍逐 instance 强制完整 nominal 矩阵。
    """
    import pyarrow.dataset as ds

    allowed_fields = frozenset(str(field_id) for field_id in field_ids)
    if not allowed_fields:
        raise ValueError("field_ids 不能为空")
    feature_columns = [f"feature__{feature_id}" for feature_id in SELECTION_FEATURE_IDS]
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
        "ref_path_length",
        "ref_headland_turns",
        "ref_row_crossings",
        *feature_columns,
    ]
    dataset = ds.dataset(str(runs_parquet), format="parquet")
    missing_columns = sorted(set(columns) - set(dataset.schema.names))
    if missing_columns:
        raise ValueError(f"runs.parquet 缺少 selection 所需列：{missing_columns}")
    scanner = dataset.scanner(columns=columns, filter=ds.field("field_id").isin(sorted(allowed_fields)))

    grouped: dict[str, list[dict]] = {}
    for batch in scanner.to_batches():
        for row in batch.to_pylist():
            field_id = str(row["field_id"])
            if field_id not in allowed_fields:
                raise AssertionError("Arrow field predicate 泄漏了未授权 field")
            grouped.setdefault(str(row["instance_id"]), []).append(row)
    if not grouped:
        raise ValueError("筛选后的训练集没有任何运行行")

    instances = tuple(
        build_selection_instance(grouped[instance_id], configs, vehicles)
        for instance_id in sorted(grouped)
    )
    seen_fields = {instance.field_id for instance in instances}
    missing_fields = sorted(allowed_fields - seen_fields)
    if missing_fields:
        raise ValueError(f"请求的训练 field 在 runs.parquet 中缺失：{missing_fields}")
    return instances


def field_mean_loss(instances: Sequence[SelectionInstance], config_id: str) -> tuple[FieldLoss, ...]:
    """按田聚合配置损失；zero-OK instance 只计数，不伪造 regret。"""
    by_field: dict[str, list[SelectionInstance]] = {}
    for instance in instances:
        by_field.setdefault(instance.field_id, []).append(instance)
    result = []
    for field_id in sorted(by_field):
        field_instances = by_field[field_id]
        analyzable = [instance for instance in field_instances if instance.analyzable]
        zero_ok = len(field_instances) - len(analyzable)
        if not analyzable:
            continue
        vectors = [instance.regret_vector(config_id) for instance in analyzable]
        mean_loss = sum(sum(vector) / len(vector) for vector in vectors) / len(vectors)
        result.append(FieldLoss(field_id, mean_loss, len(analyzable), zero_ok))
    return tuple(result)


def select_sbs(instances: Sequence[SelectionInstance], config_ids: Iterable[str]) -> str:
    """训练侧 field-level loss 最小的单一配置；并列按 config_id 稳定决胜。"""
    candidates = sorted(set(config_ids))
    if not candidates:
        raise ValueError("SBS 候选不能为空")
    scored: list[tuple[float, str]] = []
    for config_id in candidates:
        field_losses = field_mean_loss(instances, config_id)
        if not field_losses:
            continue
        scored.append((sum(item.mean_loss for item in field_losses) / len(field_losses), config_id))
    if not scored:
        raise ValueError("没有可定义 SBS 的可分析训练田")
    return min(scored)[1]
