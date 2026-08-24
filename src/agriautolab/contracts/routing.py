"""标准组合优化路由问题的强类型契约。

TSP/CVRP 在 AgriAutoLab 中不是示例代码，而是自动算法设计方法的参考问题族：
它们提供成熟、可解释的 constructive heuristic 基线，后续与农业规划共享候选生成、
评估和证据纪律。这里仅描述问题数据与静态可行性，不实现任何求解策略。
"""

from __future__ import annotations

import math
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from agriautolab.contracts.enums import ProblemKind, ScenarioDynamics, TaskType
from agriautolab.contracts.geometry import Point
from agriautolab.contracts.numerics import not_greater_than_with_roundoff
from agriautolab.contracts.problem import BaseProblemSpec


class RoutingNode(BaseModel):
    """带稳定身份的二维路由节点；坐标单位继承问题的米制 `GeometryFrame`。"""

    model_config = ConfigDict(extra="forbid", frozen=True)

    node_id: str = Field(min_length=1)
    position: Point


class TSPProblem(BaseProblemSpec):
    """二维欧氏对称 TSP；从固定起点出发并回到同一节点。"""

    task_type: Literal[TaskType.MULTI_POINT_ROUTING] = TaskType.MULTI_POINT_ROUTING
    problem_kind: Literal[ProblemKind.EUCLIDEAN_TSP] = ProblemKind.EUCLIDEAN_TSP
    scenario_dynamics: Literal[ScenarioDynamics.STATIC] = ScenarioDynamics.STATIC
    nodes: tuple[RoutingNode, ...] = Field(min_length=2)
    start_node_id: str = Field(min_length=1)

    @model_validator(mode="after")
    def node_identity_must_be_well_formed(self) -> "TSPProblem":
        node_ids = tuple(node.node_id for node in self.nodes)
        unique_ids = set(node_ids)
        if len(unique_ids) != len(node_ids):
            raise ValueError("TSP 节点 node_id 必须唯一")
        if self.start_node_id not in unique_ids:
            raise ValueError("TSP start_node_id 必须引用已有节点")
        return self


class CVRPCustomer(RoutingNode):
    """CVRP 客户节点；`demand` 为有限严格正数。"""

    demand: float = Field(gt=0.0, allow_inf_nan=False)


class CVRPProblem(BaseProblemSpec):
    """二维欧氏对称 CVRP：单仓库、同质车辆、容量硬约束。

    `max_vehicles=None` 表示不额外限制车辆数；若给定，则它是硬约束。问题契约只做
    无争议的静态不可行性检查（单客户超容量、总需求超总运力）；更强的装箱可行性
    由具体求解过程决定，避免在 schema 层偷偷求一个 NP-hard 子问题。
    """

    task_type: Literal[TaskType.MULTI_POINT_ROUTING] = TaskType.MULTI_POINT_ROUTING
    problem_kind: Literal[ProblemKind.EUCLIDEAN_CVRP] = ProblemKind.EUCLIDEAN_CVRP
    scenario_dynamics: Literal[ScenarioDynamics.STATIC] = ScenarioDynamics.STATIC
    depot: RoutingNode
    customers: tuple[CVRPCustomer, ...] = Field(min_length=1)
    vehicle_capacity: float = Field(gt=0.0, allow_inf_nan=False)
    max_vehicles: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def customer_identity_and_capacity_must_be_well_formed(self) -> "CVRPProblem":
        node_ids = (self.depot.node_id,) + tuple(customer.node_id for customer in self.customers)
        if len(set(node_ids)) != len(node_ids):
            raise ValueError("CVRP 仓库与客户 node_id 必须全局唯一")

        # 单客户静态容量检查与运行时逐项扣减共用同一 binary64 roundoff policy；
        # 不能在 schema 严格比较、运行时却放宽，形成两套“容量可行”的定义。
        oversized = [
            customer.node_id
            for customer in self.customers
            if not not_greater_than_with_roundoff(customer.demand, self.vehicle_capacity)
        ]
        if oversized:
            raise ValueError(f"CVRP 存在单车容量永远无法服务的客户：{oversized}")

        # 每位客户需求都 <= 单车容量；若车辆数不少于客户数，总运力必然足够。
        # 车辆更少时比较 Σ(demand / capacity) 与车辆数，避免有限绝对量求和/乘法
        # 溢出。上界比较与构造器共用同一 roundoff policy，不能各自发明容差。
        if self.max_vehicles is not None and self.max_vehicles < len(self.customers):
            normalized_total_demand = math.fsum(
                customer.demand / self.vehicle_capacity for customer in self.customers
            )
            if not not_greater_than_with_roundoff(
                normalized_total_demand, float(self.max_vehicles)
            ):
                raise ValueError(
                    "CVRP 总需求超过 max_vehicles × vehicle_capacity，问题静态不可行"
                )
        return self
