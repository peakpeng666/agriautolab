"""排名偏好独立于 benchmark 定义。混在一起的话，换权重就等于换了一个 benchmark。"""

from pydantic import BaseModel, ConfigDict, Field, model_validator


class MetricPreference(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    metric_id: str = Field(min_length=1)
    # 权重允许为 0：偏好单纯形的顶点与棱点需可表达（某一维完全不在乎）。
    weight: float = Field(ge=0.0)


class PreferenceSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    preferences: tuple[MetricPreference, ...]

    @model_validator(mode="after")
    def unique_metrics(self) -> "PreferenceSpec":
        ids = [item.metric_id for item in self.preferences]
        if len(ids) != len(set(ids)):
            raise ValueError("偏好向量中同一指标只能出现一次")
        return self

    @model_validator(mode="after")
    def positive_total_weight(self) -> "PreferenceSpec":
        # 全零权重 = 没有偏好 = 标量化无意义；sum > 0 是最小可用契约。
        if sum(item.weight for item in self.preferences) <= 0.0:
            raise ValueError("preference weights must sum to a positive value (all-zero is meaningless)")
        return self
