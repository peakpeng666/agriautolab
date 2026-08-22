"""覆盖路径规划用的车辆规格。

只建模几何与运动约束，刻意不建模动力学、传感器与硬件：
那些量一旦进来，Block A 的指标就不再能由最终路径几何独立重算。
"""

from pydantic import BaseModel, ConfigDict, Field


class VehicleSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    working_width_m: float = Field(gt=0.0)
    # 车体宽度与机具幅宽必须分开：碰撞和越界判定用车体，覆盖率分子用机具，
    # 二者混用会让宽机具窄车体的配置凭空少算碰撞面积。
    body_width_m: float = Field(gt=0.0)
    body_length_m: float = Field(gt=0.0, default=1.0)
    # 允许为 0：差速车与履带车可以原地转向，gt=0 会让这两类车根本无法表达。
    # 代价是零半径下曲率无界，必须由路径阶段自己拒绝——见 DubinsPath.run。
    min_turning_radius_m: float = Field(ge=0.0)
    can_reverse: bool = False

    @property
    def can_turn_in_place(self) -> bool:
        # 用 1e-9 而不是 == 0.0：半径常由传动比反算，会带浮点尾巴。
        return self.min_turning_radius_m <= 1e-9
