"""经典 Boustrophedon 分解：反曲临界线切分 + 连通性相同的相邻条带合并。

Choset & Pignon (1998) 的覆盖分解：沿扫掠方向取事件 x（边界顶点），事件之间
自由空间的截面区间集恒定；相邻截面区间数一致且逐段衔接时合并为同一 cell。

陷阱（旧基线的实测 bug）：在每个障碍顶点的 x 处都切一刀、不做连通性合并，
作业段数暴涨 6-8 倍，转弯项虚高——比较就在目标空间里失真。
本实现只在与区间集真正发生变化的事件处切开。
"""

from __future__ import annotations

import math

import shapely
from shapely import LineString
from shapely.affinity import rotate as shp_rotate
from shapely.geometry import box as shp_box

from agriautolab.contracts.artifacts import CellsArtifact
from agriautolab.contracts.problem import CoverageProblem
from agriautolab.contracts.errors import GeometryValidationError
from agriautolab.geometry.footprint import QUAD_SEGS
from agriautolab.geometry.robust import robust_union
from shapely.geometry import GeometryCollection
from agriautolab.geometry.validate import polygon_from_spec, polygon_to_spec, validate_obstacles_within_field


def _unit_longest_edge(polygon) -> tuple[float, float]:
    rectangle = polygon.minimum_rotated_rectangle
    coords = list(rectangle.exterior.coords)[:4]
    edges = []
    for start, end in zip(coords, coords[1:] + coords[:1]):
        dx, dy = end[0] - start[0], end[1] - start[1]
        length = math.hypot(dx, dy)
        edges.append((length, dx / length, dy / length))
    _, ux, uy = max(edges, key=lambda item: (item[0], abs(item[1]), abs(item[2])))
    if ux < 0.0 or (ux == 0.0 and uy < 0.0):
        ux, uy = -ux, -uy
    return ux, uy


def _cross_section(free, x: float) -> tuple[tuple[float, float], ...]:
    """竖直扫掠线与自由空间的截面区间，按 y 升序。"""
    line = LineString([(x, free.bounds[1] - 1.0), (x, free.bounds[3] + 1.0)])
    intersection = free.intersection(line)
    if intersection.is_empty:
        return ()
    parts = []
    if intersection.geom_type == "LineString":
        parts = (intersection,)
    elif intersection.geom_type in ("MultiLineString", "GeometryCollection"):
        parts = tuple(part for part in intersection.geoms if part.geom_type == "LineString")
    intervals = []
    for part in parts:
        ys = [coord[1] for coord in part.coords]
        intervals.append((min(ys), max(ys)))
    return tuple(sorted(intervals))


def _connectivity_continues(current: tuple[tuple[float, float], ...], following: tuple[tuple[float, float], ...]) -> bool:
    """相邻截面同连通性：区间数相同，且按序逐段衔接（重叠即衔接）。"""
    if len(current) != len(following):
        return False
    return all(
        max(a[0], b[0]) < min(a[1], b[1])
        for a, b in zip(current, following)
    )


class BoustrophedonCells:
    algorithm_id = "boustrophedon_cells"

    def run(self, problem: CoverageProblem) -> CellsArtifact:
        field = polygon_from_spec(problem.field)
        obstacle_items = tuple(
            (spec.geometry_id, polygon_from_spec(spec))
            for spec in sorted(problem.obstacles, key=lambda item: item.geometry_id)
        )
        validate_obstacles_within_field(field, obstacle_items)
        scale_hint = max(field.bounds[2] - field.bounds[0], field.bounds[3] - field.bounds[1], 1.0)
        obstacle_union = robust_union(tuple(item[1] for item in obstacle_items), scale_hint=scale_hint)
        free = field.difference(obstacle_union)
        if free.is_empty:
            raise ValueError("自由空间为空：障碍覆盖了整个地块")

        ux, uy = _unit_longest_edge(free)
        angle_rad = math.atan2(uy, ux)
        # 绕自由空间质心旋转而不是坐标原点：UTM 坐标 ~5e6，绕原点转再转回的浮点舍入
        # 足以让边缘近乎共线的真实地块自交（ee_field_77 实测）；绕质心坐标量级 ~1e2。
        pivot = (free.centroid.x, free.centroid.y)
        swept = shp_rotate(free, -math.degrees(angle_rad), origin=pivot) if angle_rad != 0.0 else free

        components = (swept,) if swept.geom_type == "Polygon" else tuple(swept.geoms)
        cells = []
        for component in components:
            events = sorted({coord[0] for coord in component.exterior.coords} |
                            {coord[0] for ring in component.interiors for coord in ring.coords})
            if len(events) < 2:
                cells.append(component)
                continue
            epsilon = 1e-7 * scale_hint
            # 逐截面中点取区间集；相邻截面同连通性则并入同一组。
            # 235 全量实测暴露两个真实缺陷（ee_field_6 面积只剩 2.6%、143 块交出
            # GeometryCollection）：两端点建箱只适用于通道 y 界在组内单调的地块，
            # 透镜形（两端薄中间厚）会把箱切小、通道被夹断时端点通道数不匹配。
            # 正确构造是沿组内**全部截面**采样通道的上下包络，围成包络多边形再交自由空间。
            sections: list[tuple[tuple[float, float], ...]] = []
            groups: list[tuple[int, int, tuple[tuple[float, float], ...]]] = []
            for index in range(len(events) - 1):
                mid = (events[index] + events[index + 1]) / 2.0
                intervals = _cross_section(component, mid)
                sections.append(intervals)
                if not intervals:
                    continue
                if groups and _connectivity_continues(groups[-1][2], intervals):
                    start, _, _ = groups[-1]
                    groups[-1] = (start, index + 1, intervals)
                else:
                    groups.append((index, index + 1, intervals))
            # 单元构造（235 全量实测教训，三种真实缺陷都出在这里）：
            # a) 组端点建箱在透镜形地块上只覆盖两端薄区（ee_field_6 面积剩 2.6%）；
            # b) 组级包络多边形在重复采样列/夹断列上非法（ee_field_77 零 cell）；
            # c) 通道在组端点夹断时端点通道数不匹配（143 块 IndexError）。
            # 正解：**逐段**建箱——段内(两事件之间)边界是线性函数，段两端点截面的
            # min/max 恰好精确覆盖该段；通道集合以段中点截面为准（缺失即夹断，跳过该列）。
            # 段箱并集再交自由空间，跨通道不会渗透：段内通道区间两两不交。
            for start_section, end_section, anchor in groups:
                channel_count = len(anchor)
                for channel in range(channel_count):
                    pieces = []
                    for i in range(start_section, end_section):
                        mid_iv = sections[i]
                        if channel >= len(mid_iv):
                            continue
                        y_low, y_high = mid_iv[channel]
                        for x_probe in (events[i] + epsilon, events[i + 1] - epsilon):
                            column = _cross_section(component, x_probe)
                            # 端点列的通道配置必须与中点一致才能用来细化边界：
                            # nl_field_191476 实测——洞尖藏在段内时端点只见 1 个通道，
                            # 把整带 y 界灌进通道 0 会与通道 1 重叠 1357 m^2（cells 并集
                            # 正确而两两重叠）。配置不一致就跳过该列：宁欠勿重，
                            # 欠覆盖的尖角由相邻组（配置已变）的箱接住。
                            if len(column) == len(mid_iv) and channel < len(column):
                                y_low = min(y_low, column[channel][0])
                                y_high = max(y_high, column[channel][1])
                        pieces.append(shp_box(events[i], y_low, events[i + 1], y_high))
                    if not pieces:
                        continue
                    cells.append(robust_union(tuple(pieces), scale_hint=scale_hint))
        # 真实地块实测（235 全量）在回转阶段暴露三类数值伪影，处置原则：归一化只作用于
        # **我们自己的箱并集**（无洞、面积良定义），绝不作用于带洞自由空间的交——
        # nl_field_191476 实测：对含洞 cell 做 buffer(0) 会把洞并进外环，面积虚增 1357 m^2
        # 恰等于洞面积。因此顺序是：箱并集转回原 frame -> （必要时）归一化并面积对账
        # -> 与原始 free 求交，洞由求交天然保留。
        specs: list[PolygonSpec] = []
        assigned_parts: list = []
        for merged in cells:
            restored = shp_rotate(merged, math.degrees(angle_rad), origin=pivot) if angle_rad != 0.0 else merged
            if not restored.is_valid:
                cleaned = restored.buffer(0, join_style="round", quad_segs=QUAD_SEGS)
                if cleaned.is_empty or not cleaned.is_valid:
                    raise GeometryValidationError("段箱并集转回原坐标后非法且 buffer(0) 无法归一化")
                if abs(cleaned.area - restored.area) > max(restored.area, 1.0) * 1e-9:
                    raise GeometryValidationError(
                        f"段箱并集归一化前后面积不一致：{restored.area!r} -> {cleaned.area!r}，"
                        "这是真自交不是数值伪影，拒绝静默修复"
                    )
                restored = cleaned
            cell = free.intersection(restored)
            parts = cell.geoms if hasattr(cell, "geoms") else (cell,)
            for part in parts:
                if part.geom_type == "Polygon" and not part.is_empty and part.area > 0.0:
                    # BCD cell 的定义是自由空间的一个**划分**。真实地块上通道数在组边界
                    # 抖动（2<->3）时，后组的箱会覆盖前组已占的区域（nl_field_191476 实测
                    # 两两重叠 1357 m^2 恰为洞面积）。按序做差集互斥化：cell 减去此前
                    # 所有 cell 的并——精确集合运算，不是几何修复；划分语义由此构造保证。
                    # 逐个对已分配 cell 做差集（不用增量 robust_union：235 实测三块地在
                    # 几十次累积后触发网格面积自检；差集是精确运算且无需并集）。
                    assigned = part
                    for previous in assigned_parts:
                        assigned = assigned.difference(previous)
                        if assigned.is_empty:
                            break
                    if assigned.is_empty or assigned.area <= 0.0:
                        continue
                    for piece in (assigned.geoms if hasattr(assigned, "geoms") else (assigned,)):
                        if piece.geom_type == "Polygon" and piece.area > 0.0:
                            specs.append(polygon_to_spec(piece, f"cell-{len(specs):04d}"))
                    assigned_parts.append(part)
        return CellsArtifact(cells=tuple(specs))
