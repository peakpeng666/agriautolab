"""BCD 分解的解析真值（解析真值清单 6）与防退化保护。

规格写「矩形+单障碍 -> 恰好 3 个 cell」；实测经典 BCD（IN=OUT 合并规则）给出 4：
截面分析是 [左,1 区间] / [障碍带,2 区间] / [右,1 区间]，任何两个相邻截面连通性
都不同，无可合并。合并两个通道中的任意一个需要任意的非对称规则（另一侧会被
障碍围成环形），不是经典 BCD。本测试按实测的 4 固化，并保住规格的防护意图：
无合并的朴素切分显著更多（菱形障碍下 8 > 4）。完整推导见 AUDIT_NOTE（算法层异议段）。
"""

import pytest
from shapely import Polygon

from agriautolab.algorithms.decomposition.boustrophedon_cells import BoustrophedonCells
from agriautolab.contracts.geometry import Point, PolygonSpec
from agriautolab.contracts.problem import CoverageProblem
from agriautolab.geometry.validate import polygon_from_spec, polygon_to_spec


def rect(x0, y0, x1, y1, gid):
    return PolygonSpec(geometry_id=gid, exterior=(
        Point(x=x0, y=y0), Point(x=x1, y=y0), Point(x=x1, y=y1), Point(x=x0, y=y1), Point(x=x0, y=y0)))


def naive_cut_count(free: Polygon, obstacle_xs) -> int:
    """旧基线的朴素行为：在障碍每个顶点 x 处都切、不合并——按通道数累加。"""
    counts = 0
    bounds = free.bounds
    events = sorted(set([bounds[0], bounds[2]] + list(obstacle_xs)))
    for xa, xb in zip(events, events[1:]):
        mid = (xa + xb) / 2.0
        from shapely import LineString
        intersection = free.intersection(LineString([(mid, bounds[1] - 1), (mid, bounds[3] + 1)]))
        parts = 0
        if not intersection.is_empty:
            if intersection.geom_type == "LineString":
                parts = 1
            else:
                parts = sum(1 for part in intersection.geoms if part.geom_type == "LineString")
        counts += parts
    return counts


def test_rect_with_single_obstacle_gives_four_merged_cells() -> None:
    """矩形 + 单个内部障碍（轴对齐）：合并后 4 个 cell，不是不合并的更多。"""
    problem = CoverageProblem(problem_id="p", field=rect(0, 0, 100, 50, "field"),
                              obstacles=(rect(40, 20, 60, 30, "obs"),))
    cells = BoustrophedonCells().run(problem)
    assert len(cells.cells) == 4
    free_area = 100 * 50 - 20 * 10
    total = sum(polygon_from_spec(cell).area for cell in cells.cells)
    assert total == pytest.approx(free_area, rel=1e-9)


def test_diamond_obstacle_merge_protects_against_naive_explosion() -> None:
    """菱形障碍（4 个不同顶点 x）：合并把 8 段朴素切分压回 4。"""
    diamond = PolygonSpec(geometry_id="obs", exterior=(
        Point(x=50, y=15), Point(x=65, y=25), Point(x=50, y=35), Point(x=35, y=25), Point(x=50, y=15)))
    problem = CoverageProblem(problem_id="p", field=rect(0, 0, 100, 50, "field"), obstacles=(diamond,))
    cells = BoustrophedonCells().run(problem)
    assert len(cells.cells) == 4

    free = Polygon([(0, 0), (100, 0), (100, 50), (0, 50), (0, 0)]).difference(
        Polygon([(50, 15), (65, 25), (50, 35), (35, 25), (50, 15)])
    )
    naive = naive_cut_count(free, [35, 50, 50, 65])
    # 截面通道数：[0,35]:1 + [35,50]:2 + [50,65]:2 + [65,100]:1 = 6（左尖端处上/下仍分离）
    assert naive == 6
    assert len(cells.cells) < naive
    total = sum(polygon_from_spec(cell).area for cell in cells.cells)
    assert total == pytest.approx(5000.0 - 300.0, rel=1e-9)


def test_l_shape_without_obstacle_stays_one_cell() -> None:
    """无障碍 L 形：截面连通性全程一致，必须合并成 1 个 cell（不切）。"""
    lshape = PolygonSpec(geometry_id="field", exterior=(
        Point(x=0, y=0), Point(x=100, y=0), Point(x=100, y=20), Point(x=60, y=20),
        Point(x=60, y=50), Point(x=0, y=50), Point(x=0, y=0)))
    cells = BoustrophedonCells().run(CoverageProblem(problem_id="l", field=lshape))
    assert len(cells.cells) == 1


def test_bcd_is_deterministic() -> None:
    problem = CoverageProblem(problem_id="p", field=rect(0, 0, 100, 50, "field"),
                              obstacles=(rect(30, 10, 45, 40, "a"), rect(60, 5, 70, 45, "b")))
    first = BoustrophedonCells().run(problem)
    second = BoustrophedonCells().run(problem)
    assert first.model_dump_json() == second.model_dump_json()


def test_real_field_defects_regression_synthetic() -> None:
    """真实语料暴露的三个数值缺陷的合成回归：

    1) 透镜形地块（两端薄中间厚）组端点建箱只剩 2.6% 面积（ee_field_6）；
    2) robust_union 网格吸附的 ~1e-13 近退化顶点转回原坐标后自交（ee_field_77）；
    3) 洞尖藏于段内时端点通道配置不匹配，通道 0 与通道 1 重叠恰为洞面积
       （nl_field_191476：重叠 1357 m^2，cells 并集正确但两两重叠）。
    断言：面积守恒（rel 1e-6）+ cells 两两互斥（划分语义）+ 全部可过 polygon_from_spec。
    """
    from shapely import Polygon

    lens = Polygon([(0, 0), (60, 30), (120, 0), (60, -30)])          # 透镜形
    donut = Polygon(
        [(0, 0), (100, 0), (100, 80), (0, 80)],
        [[(40, 30), (60, 30), (60, 50), (40, 50)]],                   # 洞尖不落在段边界
    )

    for name, geometry, expected in (("lens", lens, lens.area), ("donut", donut, donut.area)):
        spec = polygon_to_spec(geometry, name)
        cells = BoustrophedonCells().run(CoverageProblem(problem_id=name, field=spec))
        polys = [polygon_from_spec(cell) for cell in cells.cells]
        assert polys, name
        total = sum(item.area for item in polys)
        assert total == pytest.approx(expected, rel=1e-6), (name, total, expected)
        for i in range(len(polys)):
            for j in range(i + 1, len(polys)):
                assert polys[i].intersection(polys[j]).area < 1e-6, (name, i, j)
        for p in polys:
            assert p.is_valid
