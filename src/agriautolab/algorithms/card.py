"""算法卡片只描述能解什么，不编码任何「该赢」的主张。"""

from pydantic import BaseModel, ConfigDict, Field

from agriautolab.contracts.enums import (
    AlgorithmMaturity,
    AlgorithmSourceType,
    CoverageStage,
    ProblemKind,
)


class AlgorithmCard(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    algorithm_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    stage: CoverageStage
    supported_problem_kinds: frozenset[ProblemKind]
    maturity: AlgorithmMaturity
    source_type: AlgorithmSourceType
    source_reference: str = ""
    deterministic: bool = True

    def supports(self, problem_kind: ProblemKind) -> bool:
        # 兼容性只由 ProblemKind 决定；TaskType 只是任务语义，不能作为算法选择捷径。
        return problem_kind in self.supported_problem_kinds
