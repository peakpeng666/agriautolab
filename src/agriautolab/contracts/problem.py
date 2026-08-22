"""在 schema 边界上让不兼容的规划问题无法混淆：覆盖问题塞 goal、点到点问题塞 field，都必须当场失败。"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from agriautolab.contracts.enums import ProblemKind, ScenarioDynamics, TaskType
from agriautolab.contracts.geometry import GeometryFrame, Point, PolygonSpec
from agriautolab.contracts.rows import RowStructure


class BaseProblemSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    problem_id: str = Field(min_length=1)
    task_type: TaskType
    scenario_dynamics: ScenarioDynamics = ScenarioDynamics.STATIC
    problem_kind: ProblemKind
    frame: GeometryFrame = GeometryFrame()


class CoverageProblem(BaseProblemSpec):
    task_type: Literal[TaskType.COVERAGE] = TaskType.COVERAGE
    problem_kind: Literal[ProblemKind.POLYGON_COVERAGE_2D] = ProblemKind.POLYGON_COVERAGE_2D
    field: PolygonSpec
    obstacles: tuple[PolygonSpec, ...] = ()
    forbidden_crossing_zones: tuple[PolygonSpec, ...] = ()
    # None 表示地块没有行结构（大田轮廓作业）；有行结构时 row_aligned swath 与
    # row_crossings 指标才可用——它们拒绝静默退化，见各算法入口检查。
    row_structure: RowStructure | None = None


# 保留点到点问题是为了给 schema 防火墙提供反例：只有存在第二种 ProblemKind，
# "覆盖问题塞入 goal 字段会被拒绝" 这条断言才有对照组。它不参与覆盖规划流程。
class GridPointToPointProblem(BaseProblemSpec):
    task_type: Literal[TaskType.POINT_TO_POINT] = TaskType.POINT_TO_POINT
    problem_kind: Literal[ProblemKind.GRID_P2P_2D] = ProblemKind.GRID_P2P_2D
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    start: Point
    goal: Point
    blocked: tuple[Point, ...] = ()
