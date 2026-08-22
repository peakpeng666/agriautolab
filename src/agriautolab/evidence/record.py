"""一次运行的不可变身份、状态，以及独立重算出的指标证据。指标不采信规划器自报值。"""

from pydantic import BaseModel, ConfigDict, Field, model_validator

from agriautolab.contracts.enums import RunStatus
from agriautolab.metrics.coverage import DenominatorProvenance

# 只要指标里出现覆盖率，记录就必须携带分母 provenance，否则两条覆盖率永远无法对账。
_COVERAGE_METRIC_IDS = frozenset({"coverage_ratio_field", "coverage_ratio_main", "overlap_ratio"})


class EvidenceMetric(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    metric_id: str = Field(min_length=1)
    value: float


class EvidenceRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    record_id: str = Field(min_length=1)
    problem_hash: str = Field(min_length=64, max_length=64)
    algorithm_id: str = Field(min_length=1)
    config_hash: str = Field(min_length=64, max_length=64)
    source_hash: str = Field(min_length=64, max_length=64)
    environment_hash: str = Field(min_length=64, max_length=64)
    status: RunStatus
    failure_reason: str | None = None
    metrics: tuple[EvidenceMetric, ...] = ()
    denominator: DenominatorProvenance | None = None
    # F2C 对账记录专用：录制环境（fields2cover 源、SWIG、python 版本）的内容哈希。
    # 换了 F2C 版本，golden 就不是同一份 golden，证据层必须能区分。
    # None 表示该记录与 F2C 无关；对账记录缺失此哈希由比较器侧强制，不在这里猜。
    f2c_env_hash: str | None = Field(default=None, min_length=64, max_length=64)

    @model_validator(mode="after")
    def coverage_metrics_must_carry_denominator(self) -> "EvidenceRecord":
        """上一版基线把 path 剥掉之后没有任何指标能被独立重算；分母不能重蹈覆辙。"""
        if self.denominator is None and any(item.metric_id in _COVERAGE_METRIC_IDS for item in self.metrics):
            raise ValueError(
                "携带覆盖率指标的记录必须同时携带 denominator（分母 provenance）："
                "不记分母，事后没人能判断两条覆盖率是不是同一把尺子量的"
            )
        return self
