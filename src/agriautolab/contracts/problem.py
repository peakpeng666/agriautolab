"""规划问题的公共 schema 边界。

不兼容字段必须在构造时失败：覆盖问题不能混入 point-to-point 字段，标准路由问题也
不应借用农业 field/vehicle 语义。TSP/CVRP 的专有契约放在 `contracts.routing`。
"""

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


# 轻量 point-to-point 契约仍用于 schema 防火墙测试，但不参与农业覆盖流水线。
# 标准多点路由问题单独放在 contracts.routing，避免把 depot/demand 等字段塞进这里。
class GridPointToPointProblem(BaseProblemSpec):
    task_type: Literal[TaskType.POINT_TO_POINT] = TaskType.POINT_TO_POINT
    problem_kind: Literal[ProblemKind.GRID_P2P_2D] = ProblemKind.GRID_P2P_2D
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    start: Point
    goal: Point
    blocked: tuple[Point, ...] = ()
