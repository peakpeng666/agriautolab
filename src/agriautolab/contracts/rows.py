"""作物行结构：覆盖规划里唯一与长度族正交的目标维度的来源。

通用移动机器人规划把自由空间当各向同性的；农业不是。
果园与温室里沿行走是自由的，横穿行被禁止或有代价。
参数化而不是存折线，是为了让穿行次数与各向异性代价都**可解析计算**——
实测 240 实例 × 12 配置里，crossings 与 length 的秩相关只有 −0.098，
与 turns 是 −0.448：拿掉这个维度，目标空间塌成一根轴。
"""

import math

from pydantic import BaseModel, ConfigDict, Field, model_validator


class RowStructure(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    direction_rad: float
    spacing_m: float = Field(gt=0.0)
    first_offset_m: float = 0.0
    crossable: bool = False
    crossing_penalty: float = Field(default=float("inf"), ge=0.0)
    along_row_cost_factor: float = Field(default=1.0, gt=0.0)

    @model_validator(mode="after")
    def uncrossable_rows_have_infinite_penalty(self) -> "RowStructure":
        # 有限罚金 + 不可横穿是自相矛盾的申报：解析公式会据此给出有限的穿行代价，
        # 与「禁止」语义冲突，必须在构造点拒绝而不是留给下游解释。
        if not self.crossable and math.isfinite(self.crossing_penalty):
            raise ValueError("crossable=False 时 crossing_penalty 必须为 inf：不可横穿就是无穷代价")
        return self

    def crossings_between(self, p: tuple[float, float], q: tuple[float, float]) -> float:
        """线段 p->q 穿越作物行的次数，解析计算，不做离散采样。

        行方向的单位法向 n = (-sin(gamma), cos(gamma))，
        crossings = |(q - p) . n| / spacing。
        只依赖端点投影差，与线段在行方向上走多远无关。
        """
        gamma = self.direction_rad
        nx, ny = -math.sin(gamma), math.cos(gamma)
        projection = (q[0] - p[0]) * nx + (q[1] - p[1]) * ny
        return abs(projection) / self.spacing_m

    def direction_cost_factor(self, heading_rad: float) -> float:
        """沿 heading 行进的各向异性代价系数。

        沿行（|sin(heading-gamma)| -> 0）趋于 along_row_cost_factor；
        垂直行趋于受 crossing_penalty 支配。crossable=False 时 crossing_penalty
        为 inf，任何非零穿行分量返回 inf——不可横穿不是「很贵」，是「不行」。
        公式：factor = along + (perpendicular−along)·|sin(heading−gamma)|，
        其中 perpendicular = crossing_penalty / spacing_m 把每次穿行的罚金
        折算成按距离的系数（穿行密度 = 1/spacing）。
        """
        gamma = self.direction_rad
        cross_component = abs(math.sin(heading_rad - gamma))
        if cross_component == 0.0:
            return self.along_row_cost_factor
        perpendicular = self.crossing_penalty / self.spacing_m
        if not math.isfinite(perpendicular):
            return math.inf
        return self.along_row_cost_factor + (perpendicular - self.along_row_cost_factor) * cross_component


from dataclasses import dataclass
from enum import Enum


class RowDirectionMode(str, Enum):
    PRINCIPAL_AXIS = "principal_axis"
    LONGEST_EDGE = "longest_edge"
    FIXED_OFFSET = "fixed_offset"


@dataclass(frozen=True)
class RowScenario:
    """未观测的作物行方向作为受控实验因子，而不是从边界猜成“真值”。

    PRINCIPAL_AXIS / LONGEST_EDGE 的 offset_rad 是相对相应几何基准方向的偏移；
    FIXED_OFFSET 以全局 x 轴为基准。这里的 PI_DISCRETE 只用于协议扫描网格，
    与 Block B 已冻结的解析 Dubins 圆周率口径分开。
    """

    row_direction_mode: RowDirectionMode
    offset_rad: float
    spacing_m: float
    crossable: bool

    def __post_init__(self) -> None:
        if self.spacing_m <= 0.0:
            raise ValueError("spacing_m 必须为正")

