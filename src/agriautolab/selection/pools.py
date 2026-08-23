"""三层配置池契约：nominal / static-applicable / observed-OK（D2 普查的内核）。

三层集合必须彻底分开，任何结果派生集合都不得反过来定义样本全集：

- N（nominal）：协议声明的全部配置，与实例无关；
- A（static-applicable）：规划前可知的适用性——问题类型 × 机具能力，
  **不看 validator 结果**。H3 的 random_applicable 基线从这一层取期望；
- O（observed-OK）：实际跑完并通过 validator 的配置（结果派生）。

恒有 O ⊆ A ⊆ N。**O ⊄ A 不是数据现象，是 applicability 契约有 bug**，
本模块的选择是当场抛错而不是记录继续。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from agriautolab.contracts.enums import ProblemKind
from agriautolab.contracts.vehicle import VehicleSpec
from agriautolab.pipeline.config import PipelineConfig

# 机具能力 × 路径阶段的静态配对表：唯一的车辆相关静态规则。
# 声明在这里而不是散在算法里——「谁需要倒车」是契约不是实现细节。
_REVERSING_PATH_STAGES = frozenset({"reeds_shepp_transit"})


def static_applicable(config: PipelineConfig, vehicle: VehicleSpec, *,
                      problem_kind: ProblemKind = ProblemKind.POLYGON_COVERAGE_2D) -> bool:
    """规划前可知的适用性判定（不触碰几何、不触碰 validator 结果）。"""
    if config.path in _REVERSING_PATH_STAGES and not vehicle.can_reverse:
        return False
    # 五阶段槽位必须落在目录为该问题类型声明的兼容集合内（拼写错误在此暴露）
    from agriautolab.contracts.enums import CoverageStage
    from agriautolab.algorithms.catalog import build_catalog
    registry = build_catalog()
    for stage, algorithm_id in (
        (CoverageStage.DECOMPOSITION, config.decomposition),
        (CoverageStage.HEADLAND, config.headland),
        (CoverageStage.SWATH, config.swath),
        (CoverageStage.ROUTE, config.route),
        (CoverageStage.PATH, config.path),
    ):
        if algorithm_id not in {card.algorithm_id for card in registry.compatible(stage, problem_kind)}:
            return False
    return True


@dataclass(frozen=True)
class InstancePools:
    """单个实例的三层集合成员（config_id 级）。"""

    instance_id: str
    field_id: str
    vehicle_index: int
    nominal: frozenset[str]
    applicable: frozenset[str]
    observed_ok: frozenset[str]

    def verify_containment(self) -> None:
        if not self.observed_ok <= self.applicable:
            raise ValueError(
                f"O ⊄ A（applicability 契约 bug）@ {self.instance_id}: "
                f"{sorted(self.observed_ok - self.applicable)}"
            )
        if not self.applicable <= self.nominal:
            raise ValueError(
                f"A ⊄ N（池身份 bug）@ {self.instance_id}: "
                f"{sorted(self.applicable - self.nominal)}"
            )


def census_from_runs(runs_parquet: str | Path, configs: tuple[PipelineConfig, ...],
                     vehicles: tuple[VehicleSpec, ...]) -> dict:
    """从语料 parquet 计算三层普查（状态一律 derived_status）。

    holdout 田的 O 层聚合仅作描述统计——任何建模消费在 H3 开留出集之前禁止。
    """
    from agriautolab.corpus.derived_status import derive_status

    config_ids = {config.config_id() for config in configs}
    per_vehicle_applicable = {
        index: frozenset(
            config.config_id() for config in configs if static_applicable(config, vehicle)
        )
        for index, vehicle in enumerate(vehicles)
    }

    import pyarrow.parquet as pq

    rows: dict[str, dict] = {}
    for batch in pq.ParquetFile(runs_parquet).iter_batches(
        batch_size=16384,
        columns=["instance_id", "config_id", "vehicle_index", "runstatus", "failure_reason"],
    ):
        for iid, cid, vid, raw, reason in zip(
            batch.column(0).to_pylist(), batch.column(1).to_pylist(), batch.column(2).to_pylist(),
            batch.column(3).to_pylist(), batch.column(4).to_pylist(),
        ):
            slot = rows.setdefault(iid, {"field": iid.split(":")[0], "vehicle": vid, "ok": set()})
            if derive_status(str(raw), reason) == "ok":
                slot["ok"].add(cid)

    instances = []
    for iid in sorted(rows):
        slot = rows[iid]
        pools = InstancePools(
            instance_id=iid, field_id=slot["field"], vehicle_index=slot["vehicle"],
            nominal=frozenset(config_ids),
            applicable=per_vehicle_applicable[slot["vehicle"]],
            observed_ok=frozenset(slot["ok"]),
        )
        pools.verify_containment()
        instances.append(pools)
    return {
        "n_instances": len(instances),
        "nominal_size": len(config_ids),
        "applicable_by_vehicle": {str(v): len(s) for v, s in sorted(per_vehicle_applicable.items())},
        "instances": instances,
    }
