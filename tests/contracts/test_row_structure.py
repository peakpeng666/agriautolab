"""RowStructure 的解析真值与契约校验。"""

import math

import pytest
from pydantic import ValidationError

from agriautolab.contracts.problem import CoverageProblem
from agriautolab.contracts.geometry import Point, PolygonSpec
from agriautolab.contracts.rows import RowStructure


def rows(direction_rad: float = 0.0, spacing_m: float = 2.5) -> RowStructure:
    return RowStructure(direction_rad=direction_rad, spacing_m=spacing_m, crossable=True, crossing_penalty=5.0)


def test_segment_parallel_to_rows_crosses_nothing() -> None:
    structure = rows(direction_rad=0.3)
    # 沿行方向走 100 米：投影到法向为零，穿行数为 0（与走了多远无关）
    ux, uy = math.cos(0.3), math.sin(0.3)
    p = (3.0 * ux, 3.0 * uy)
    q = (103.0 * ux, 103.0 * uy)
    # 真值是精确 0；容差只吃 cos/sin 乘加的浮点残差（实测 1.4e-15），不是放宽
    assert structure.crossings_between(p, q) == pytest.approx(0.0, abs=1e-12)


def test_segment_perpendicular_to_rows_crosses_length_over_spacing() -> None:
    structure = rows(direction_rad=0.0, spacing_m=2.5)
    # 垂直于行、长 L=10：穿行数 = L/s = 4.0（解析真值，非采样）
    assert structure.crossings_between((0.0, 0.0), (0.0, 10.0)) == pytest.approx(4.0, rel=1e-15)
    # 任意角度的行方向下同一定义成立：法向投影 / 行距
    rotated = rows(direction_rad=1.1)
    nx, ny = -math.sin(1.1), math.cos(1.1)
    p = (2.0, -1.0)
    q = (2.0 + 7.0 * nx, -1.0 + 7.0 * ny)
    assert rotated.crossings_between(p, q) == pytest.approx(7.0 / 2.5, rel=1e-15)


def test_uncrossable_rows_must_carry_infinite_penalty() -> None:
    with pytest.raises(ValidationError):
        RowStructure(direction_rad=0.0, spacing_m=2.5, crossable=False, crossing_penalty=5.0)
    # 不可横穿 + inf 罚金是唯一自洽组合
    assert RowStructure(direction_rad=0.0, spacing_m=2.5).crossing_penalty == math.inf


def test_direction_cost_factor_extremes() -> None:
    structure = rows(direction_rad=0.5, spacing_m=2.5)
    assert structure.direction_cost_factor(0.5) == pytest.approx(1.0, rel=1e-15)   # 沿行
    perpendicular = structure.direction_cost_factor(0.5 + math.pi / 2.0)
    assert perpendicular == pytest.approx(5.0 / 2.5, rel=1e-15)                    # 垂直行受罚金支配

    orchard = RowStructure(direction_rad=0.0, spacing_m=2.5)   # 默认不可横穿
    assert orchard.direction_cost_factor(0.0) == 1.0
    assert math.isinf(orchard.direction_cost_factor(0.1))     # 任何非零穿行分量都是 inf


def test_coverage_problem_accepts_optional_row_structure() -> None:
    field = PolygonSpec(
        geometry_id="field",
        exterior=(Point(x=0.0, y=0.0), Point(x=10.0, y=0.0), Point(x=10.0, y=10.0), Point(x=0.0, y=10.0), Point(x=0.0, y=0.0)),
    )
    plain = CoverageProblem(problem_id="p", field=field)
    assert plain.row_structure is None
    with_rows = CoverageProblem(problem_id="p", field=field, row_structure=rows())
    assert with_rows.row_structure is not None and with_rows.row_structure.spacing_m == 2.5
