"""排名偏好独立于 benchmark 定义。混在一起的话，换权重就等于换了一个 benchmark。"""

from pydantic import BaseModel, ConfigDict, Field, model_validator


class MetricPreference(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    metric_id: str = Field(min_length=1)
    weight: float = Field(gt=0.0)


class PreferenceSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    preferences: tuple[MetricPreference, ...]

    @model_validator(mode="after")
    def unique_metrics(self) -> "PreferenceSpec":
        ids = [item.metric_id for item in self.preferences]
        if len(ids) != len(set(ids)):
            raise ValueError("偏好向量中同一指标只能出现一次")
        return self
