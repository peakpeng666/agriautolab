"""统一目标函数符号，优化器就不必为每个阶段写 maximize/minimize 分支。"""

from __future__ import annotations

from abc import ABC, abstractmethod

from agriautolab.contracts.artifacts import (
    CellsArtifact,
    HeadlandArtifact,
    PathArtifact,
    RouteArtifact,
    SwathsArtifact,
)
from agriautolab.contracts.enums import CoverageStage, ObjectiveRole

Artifact = CellsArtifact | HeadlandArtifact | SwathsArtifact | RouteArtifact | PathArtifact


class Objective(ABC):
    objective_id: str
    stage: CoverageStage
    role: ObjectiveRole

    @abstractmethod
    def raw_cost(self, artifact: Artifact) -> float:
        """按目标本身的数学方向返回；符号翻转交给 cost。"""

    def is_minimizing(self) -> bool:
        return True

    def cost(self, artifact: Artifact) -> float:
        # Fields2Cover 的 minimizing-sign 约定让优化器只处理最小化；方向差异留在 objective 内部。
        return (1.0 if self.is_minimizing() else -1.0) * self.raw_cost(artifact)
