"""把 RowScenario 解析成 Block B 唯一的 RowStructure 契约。"""

from __future__ import annotations

import math

from shapely.geometry.base import BaseGeometry

from agriautolab.algorithms.swath.longest_edge import longest_edge_direction
from agriautolab.algorithms.swath.principal_axis import principal_axis
from agriautolab.contracts.rows import RowDirectionMode, RowScenario, RowStructure


def resolve_row_structure(geometry: BaseGeometry, scenario: RowScenario) -> RowStructure:
    """实验因子只决定方向；真正被规划器/指标消费的事实仍只有 RowStructure 一处住所。"""
    if scenario.row_direction_mode is RowDirectionMode.PRINCIPAL_AXIS:
        ux, uy = principal_axis(geometry)
        base = math.atan2(uy, ux)
    elif scenario.row_direction_mode is RowDirectionMode.LONGEST_EDGE:
        ux, uy = longest_edge_direction(geometry)
        base = math.atan2(uy, ux)
    else:
        base = 0.0
    direction = base + scenario.offset_rad
    return RowStructure(
        direction_rad=direction,
        spacing_m=scenario.spacing_m,
        crossable=scenario.crossable,
        crossing_penalty=scenario.spacing_m if scenario.crossable else float("inf"),
    )
