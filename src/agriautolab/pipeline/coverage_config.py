"""把阶段身份与几何协议旋钮冻结成可复现的流水线配置：配置哈希变了，结果才允许变。"""

from pydantic import BaseModel, ConfigDict, Field, model_validator

from agriautolab.contracts.enums import CoverageStage


class StageConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    stage: CoverageStage
    algorithm_id: str = Field(min_length=1)


class CoveragePipelineConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    decomposition: StageConfig = StageConfig(stage=CoverageStage.DECOMPOSITION, algorithm_id="no_decomposition")
    headland: StageConfig = StageConfig(stage=CoverageStage.HEADLAND, algorithm_id="constant_width_headland")
    swath: StageConfig = StageConfig(stage=CoverageStage.SWATH, algorithm_id="longest_edge_swath")
    route: StageConfig = StageConfig(stage=CoverageStage.ROUTE, algorithm_id="snake_route")
    path: StageConfig = StageConfig(stage=CoverageStage.PATH, algorithm_id="dubins_path")
    headland_width_m: float = Field(default=3.0, gt=0.0)
    dubins_sample_step_m: float = Field(default=0.25, gt=0.0)

    @model_validator(mode="after")
    def stage_slots_match(self) -> "CoveragePipelineConfig":
        expected = (
            (self.decomposition, CoverageStage.DECOMPOSITION),
            (self.headland, CoverageStage.HEADLAND),
            (self.swath, CoverageStage.SWATH),
            (self.route, CoverageStage.ROUTE),
            (self.path, CoverageStage.PATH),
        )
        for config, stage in expected:
            if config.stage is not stage:
                raise ValueError(f"{stage.value} 槽位不能装入 {config.stage.value} 配置")
        return self
