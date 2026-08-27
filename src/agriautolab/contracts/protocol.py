"""把评测协议参数与问题定义、用户偏好彻底分开。"""

from pydantic import BaseModel, ConfigDict, Field

from agriautolab.contracts.enums import CoverageTarget
from agriautolab.pipeline.hashing import content_hash


class HypervolumeReference(BaseModel):
    """超体积参考点：三维目标各自的解析上界，由协议声明并进入协议哈希。

    浮动的参考点 = 浮动的分母：若参考点取自观测到的最差值，换一个算法池，
    同一前沿的超体积就变了，跨池不可比——这正是 Dolan-Moré 性能剖面在
    solver 集合变化下不稳定的同一个病。参考点必须由协议声明的解析上界导出，
    basis 字段记录用的是哪组公式。
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    path_length: float = Field(gt=0.0)
    headland_turns: float = Field(gt=0.0)
    row_crossings: float = Field(gt=0.0)
    basis: str = Field(min_length=1)


class ReverseCostSpec(BaseModel):
    """倒车代价的两个协议参数。无默认值，且进入协议哈希。

    换了倒车偏好就是换了目标函数：同一条 Reeds-Shepp 路径在
    multiplier=1.0 与 multiplier=8.0 下的排序可以完全不同。
    给默认值等于允许「忘记声明」与「确实选了 1.0」在证据里长得一样。

    两个参数不冗余：长度乘子表达「倒车更慢」，换挡罚表达「宁可多走一点
    也别多换一次挡」——后者是固定成本，乘子怎么调都表达不出来。
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    reverse_length_multiplier: float = Field(ge=1.0)
    gear_shift_penalty_m: float = Field(ge=0.0)


class BenchmarkProtocol(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    protocol_id: str = Field(min_length=1)
    # 故意不给默认值：分母是协议的一部分，必须每次显式声明。
    # 一旦给了默认值，"忘记指定" 和 "选择原田" 在证据里长得一模一样。
    coverage_target: CoverageTarget
    coverage_threshold: float = Field(default=0.99, ge=0.0, le=1.0)
    area_epsilon_m2: float = Field(default=1e-9, ge=0.0)
    resample_step_m: float = Field(default=0.25, gt=0.0)
    clearance_sample_step_m: float = Field(default=0.25, gt=0.0)
    # 同样故意不给默认值：超体积的尺子（参考点）换了，两次运行在前沿层面
    # must be distinguishable at the evidence layer for fair comparison.
    hypervolume_reference: HypervolumeReference
    # Reverse cost configuration affects the objective function.
    reverse_cost: ReverseCostSpec

    def spec_hash(self) -> str:
        """协议内容哈希。coverage_target、hypervolume_reference、reverse_cost 都必须进入哈希。"""
        return content_hash(self)
