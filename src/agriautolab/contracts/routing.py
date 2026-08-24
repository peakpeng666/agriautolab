"""标准组合优化路由问题的强类型契约。

TSP/CVRP 在 AgriAutoLab 中不是示例代码，而是自动算法设计方法的参考问题族：
它们提供成熟、可解释的 constructive heuristic 基线，后续与农业规划共享候选生成、
评估和证据纪律。这里仅描述问题数据，不实现求解策略。
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from agriautolab.contracts.enums import ProblemKind, ScenarioDynamics, TaskType
from agriautolab.contracts.geometry import GeometryFrame, Point
from agriautolab.contracts.problem import BaseProblemSpec


class RoutingNode(BaseModel):
    """带稳定身份的二维路由节点。"""

    model_config = ConfigDict(extra="forbid", frozen=True)

    node_id: str = Field(min_length=1)
    position: Point


class TSPProblem(BaseProblemSpec):
    """二维欧氏对称 TSP；固定从 `start_node_id` 出发并回到起点。"""

    task_type: Literal[TaskType.MULTI_POINT_ROUTING] = TaskType.MULTI_POINT_ROUTING
    problem_kind: Literal[ProblemKind.EUCLIDEAN_TSP] = ProblemKind.EUCLIDEAN_TSP
    scenario_dynamics: Literal[ScenarioDynamics.STATIC] = ScenarioDynamics.STATIC
    frame: GeometryFrame = GeometryFrame()
    nodes: tuple[RoutingNode, ...] = Field(min_length=2)
    start_node_id: str

    @model_validator(mode="after")
    def node_identity_must_be_well_formed(self) -> "TSPProblem":
        ids = tuple(node.node_id for node in self.nodes)
        if len(set(ids)) != len(ids):
            raise ValueError("TSP 节点 node_id 必须唯一")
        if self.start_node_id not in set(ids):
            raise ValueError("TSP start_node_id 必须引用已有节点")
        return self


class CVRPCustomer(RoutingNode):
    """CVRP 客户节点；需求必须为严格正数。"""

    demand: float = Field(gt=0.0)


class CVRPProblem(BaseProblemSpec):
    """二维欧氏对称 CVRP，单仓库、同质车辆、每条路线从仓库出发并返回。

    `max_vehicles=None` 表示不额外限制车辆数；若给定，则构造器必须在该上限内完成。
    容量与车辆数都是硬约束，不允许启发式评分函数绕过。
    """

    task_type: Literal[TaskType.MULTI_POINT_ROUTING] = TaskType.MULTI_POINT_ROUTING
    problem_kind: Literal[ProblemKind.EUCLIDEAN_CVRP] = ProblemKind.EUCLIDEAN_CVRP
    scenario_dynamics: Literal[ScenarioDynamics.STATIC] = ScenarioDynamics.STATIC
    frame: GeometryFrame = GeometryFrame()
    depot: RoutingNode
    customers: tuple[CVRPCustomer, ...] = Field(min_length=1)
    vehicle_capacity: float = Field(gt=0.0)
    max_vehicles: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def customer_identity_and_capacity_must_be_well_formed(self) -> "CVRPProblem":
        ids = (self.depot.node_id,) + tuple(customer.node_id for customer in self.customers)
        if len(set(ids)) != len(ids):
            raise ValueError("CVRP 仓库与客户 node_id 必须全局唯一")
        oversized = [
            customer.node_id
            for customer in self.customers
            if customer.demand > self.vehicle_capacity
        ]
        if oversized:
            raise ValueError(f"CVRP 存在单车容量永远无法服务的客户：{oversized}")
        return self
