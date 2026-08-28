"""语料级协议：把行方向扫描与 CV 折固定进协议哈希。"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator

from agriautolab.contracts.rows import RowDirectionMode
from agriautolab.geometry.discrete import PI_DISCRETE
from agriautolab.pipeline.hashing import content_hash


DEFAULT_ROW_OFFSETS_RAD: tuple[float, ...] = (
    0.0, PI_DISCRETE / 8.0, PI_DISCRETE / 4.0, 3.0 * PI_DISCRETE / 8.0, PI_DISCRETE / 2.0,
)
DEFAULT_ROW_SPACINGS_M: tuple[float, ...] = (0.75, 3.0)


class ReconciliationSamplingSpec(BaseModel):
    """F2C 对账集的分层抽样规则。规则与种子都进协议哈希，换了抽样就换协议。

    存在的理由：按 id 顺序取前 12 块的抽样会偏置样本，
    其中只有 1 块含田内障碍，而全量语料有 33 块含障碍——抽样需分层。
    后果是 main_field_area 那个 0.004% 主要在无障碍情形上取得，
    而 RMA 裁决（F2C 扣障碍 + 扣障碍周围一圈 headland）恰恰是关于障碍的——
    那条裁决当时是「读出来的」，不是「验出来的」。

    约束：不得回退到 id 顺序。按 id 排序取前 N 在这份语料上等价于「全取爱沙尼亚、
    几乎不取带障碍的」，那不是样本，是一个特定子群。
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    seed: int = Field(ge=0)
    total: int = Field(ge=1)
    min_with_obstacles: int = Field(ge=0)
    min_with_multiple_rings: int = Field(ge=0)

    @model_validator(mode="after")
    def strata_fit_in_total(self) -> "ReconciliationSamplingSpec":
        if self.min_with_obstacles > self.total:
            raise ValueError("含障碍的下限不能超过总数")
        if self.min_with_multiple_rings > self.min_with_obstacles:
            raise ValueError("含多内环是含障碍的子集，其下限不能更大")
        return self


DEFAULT_RECONCILIATION_SAMPLING = ReconciliationSamplingSpec(
    # 与 holdout 封存同一个种子日期，便于在证据里对上是哪一轮。
    seed=20260821, total=14, min_with_obstacles=6, min_with_multiple_rings=2,
)


class CorpusProtocol(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    protocol_id: str = Field(min_length=1)
    benchmark_protocol_hash: str = Field(min_length=64, max_length=64)
    reconciliation_sampling: ReconciliationSamplingSpec = DEFAULT_RECONCILIATION_SAMPLING
    row_direction_mode: RowDirectionMode = RowDirectionMode.PRINCIPAL_AXIS
    row_offsets_rad: tuple[float, ...] = DEFAULT_ROW_OFFSETS_RAD
    row_spacings_m: tuple[float, ...] = DEFAULT_ROW_SPACINGS_M
    row_crossable: bool = True
    cv_folds: int = Field(default=10, ge=2)
    # 机具清单的内容哈希（无默认值）：机具清单变了实验身份就变。runner 加载后
    # 与实际 vehicles 逐字节核对——声明可证伪，防「协议里记的是 A 实际跑的是 B」。
    vehicles_hash: str = Field(min_length=64, max_length=64)

    def spec_hash(self) -> str:
        return content_hash(self)
