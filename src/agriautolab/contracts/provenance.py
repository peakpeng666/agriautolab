"""可复现产物所需的最小溯源字段。"""

from pydantic import BaseModel, ConfigDict, Field


class Provenance(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    generated_by: str = Field(min_length=1)
    algorithm_id: str = Field(min_length=1)
    input_hash: str = Field(min_length=1)
    config_hash: str = Field(min_length=1)
