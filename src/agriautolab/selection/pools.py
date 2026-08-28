"""三层配置池契约：nominal / static-applicable / observed-OK。

三层集合需彻底分开，任何结果派生集合都不得反过来定义样本全集：

- N（nominal）：协议声明的全部配置，与实例无关；
- A（static-applicable）：规划前可知的适用性——问题类型 × 机具能力，
  **不看 validator 结果**。recommender 评估的 random_applicable 基线从这一层取期望；
- O（observed-OK）：实际跑完并通过 validator 的配置（结果派生）。

恒有 O ⊆ A ⊆ N。O ⊄ A 不是数据现象，而是 applicability 契约有 bug。
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from agriautolab.contracts.enums import ProblemKind
from agriautolab.contracts.vehicle import VehicleSpec
from agriautolab.pipeline import jsonl_log
from agriautolab.pipeline.config import PipelineConfig

# 机具能力 × 路径阶段的静态配对表：谁需要倒车是契约，不是运行结果。
_REVERSING_PATH_STAGES = frozenset({"reeds_shepp_transit"})
_POOL_CENSUS_ARTIFACT = "pool_census"
_BLOCK_D_GENESIS_EVENT = "cv_assignment_sealed"


def static_applicable(
    config: PipelineConfig,
    vehicle: VehicleSpec,
    *,
    problem_kind: ProblemKind = ProblemKind.POLYGON_COVERAGE_2D,
) -> bool:
    """规划前可知的适用性判定（不触碰几何、不触碰 validator 结果）。"""
    if config.path in _REVERSING_PATH_STAGES and not vehicle.can_reverse:
        return False

    from agriautolab.algorithms.catalog import build_catalog
    from agriautolab.contracts.enums import CoverageStage

    registry = build_catalog()
    for stage, algorithm_id in (
        (CoverageStage.DECOMPOSITION, config.decomposition),
        (CoverageStage.HEADLAND, config.headland),
        (CoverageStage.SWATH, config.swath),
        (CoverageStage.ROUTE, config.route),
        (CoverageStage.PATH, config.path),
    ):
        compatible = {card.algorithm_id for card in registry.compatible(stage, problem_kind)}
        if algorithm_id not in compatible:
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


def census_from_runs(
    runs_parquet: str | Path,
    configs: tuple[PipelineConfig, ...],
    vehicles: tuple[VehicleSpec, ...],
) -> dict:
    """从语料 parquet 计算三层普查（状态一律 derived_status）。

    每个 instance 需恰好含 nominal 配置各一行。缺行、重复行、未知配置，
    或同一 instance 内 field/vehicle 身份不一致，都说明输入语料不完整或损坏，
    需在形成普查统计和证据之前失败。
    """
    from agriautolab.pipeline.corpus.derived_status import derive_status

    config_id_list = tuple(config.config_id() for config in configs)
    config_ids = frozenset(config_id_list)
    if not config_ids:
        raise ValueError("nominal 配置池不能为空")
    if len(config_ids) != len(config_id_list):
        raise ValueError("nominal 配置池含重复 config_id")
    if not vehicles:
        raise ValueError("vehicles 不能为空")

    per_vehicle_applicable = {
        index: frozenset(config.config_id() for config in configs if static_applicable(config, vehicle))
        for index, vehicle in enumerate(vehicles)
    }

    import pyarrow.parquet as pq

    rows: dict[str, dict] = {}
    for batch in pq.ParquetFile(runs_parquet).iter_batches(
        batch_size=16384,
        columns=["instance_id", "field_id", "config_id", "vehicle_index", "runstatus", "failure_reason"],
    ):
        columns = [batch.column(index).to_pylist() for index in range(6)]
        for iid, field_id, cid, vid, raw, reason in zip(*columns):
            iid = str(iid)
            field_id = str(field_id)
            cid = str(cid)
            vid = int(vid)
            if cid not in config_ids:
                raise ValueError(f"语料含 nominal 池之外的 config_id @ {iid}: {cid}")
            if vid not in per_vehicle_applicable:
                raise ValueError(f"语料引用未知 vehicle_index @ {iid}: {vid}")

            slot = rows.setdefault(iid, {"field": field_id, "vehicle": vid, "seen": set(), "ok": set()})
            if slot["field"] != field_id:
                raise ValueError(f"同一 instance_id 对应多个 field_id @ {iid}")
            if slot["vehicle"] != vid:
                raise ValueError(f"同一 instance_id 对应多个 vehicle_index @ {iid}")
            if cid in slot["seen"]:
                raise ValueError(f"同一 instance/config 出现重复运行行 @ {iid}: {cid}")
            slot["seen"].add(cid)
            if derive_status(str(raw), reason) == "ok":
                slot["ok"].add(cid)

    instances = []
    for iid in sorted(rows):
        slot = rows[iid]
        missing = config_ids - slot["seen"]
        extra = slot["seen"] - config_ids
        if missing or extra:
            raise ValueError(
                f"instance 运行矩阵不完整 @ {iid}: missing={sorted(missing)}, extra={sorted(extra)}"
            )
        pools = InstancePools(
            instance_id=iid,
            field_id=slot["field"],
            vehicle_index=slot["vehicle"],
            nominal=config_ids,
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


def seal_pool_census_ledger(payload: dict, ledger_path: str | Path) -> dict:
    """把 pool census 封为基准结果账本 index=1；重复重放需幂等。

    已有完全相同的 index=1 时直接返回；已有冲突 pool census 记录、日志结构异常，
    或 genesis 之外出现了别的历史时拒绝改写。
    """
    ledger_file = Path(ledger_path)
    if not ledger_file.exists():
        raise ValueError("基准结果账本不存在；pool census 不能绕过 genesis")
    entries = jsonl_log.read_entries(ledger_file)
    jsonl_log.verify_entries(entries)
    if not entries or entries[0]["index"] != 0 or entries[0]["payload"].get("event") != _BLOCK_D_GENESIS_EVENT:
        raise ValueError("基准结果账本缺少合法 genesis")

    census_entries = [entry for entry in entries if entry["payload"].get("artifact") == _POOL_CENSUS_ARTIFACT]
    if census_entries:
        if len(census_entries) != 1 or census_entries[0]["index"] != 1:
            raise ValueError("基准结果账本中 pool_census 位置/数量异常")
        if census_entries[0]["payload"] != payload:
            raise ValueError("已封存的 pool census 与当前重放 payload 冲突")
        return census_entries[0]

    if len(entries) != 1:
        raise ValueError("pool census 尚未封存，但账本已含 genesis 之后的其他事件；拒绝重排历史")
    entry = jsonl_log.entry(1, payload)
    with ledger_file.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
    jsonl_log.verify_entries(entries + (entry,))
    return entry
