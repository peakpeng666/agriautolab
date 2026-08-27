"""路径几何的度量定义一律与航点密度无关：共线加密采样不能改善其中任何一项。"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from shapely import LineString, Point as ShapelyPoint
from shapely.geometry.base import BaseGeometry

from agriautolab.contracts.artifacts import PathArtifact
from agriautolab.contracts.enums import PathSegmentKind
from agriautolab.contracts.errors import TransitDecompositionError
from agriautolab.contracts.geometry import Point
from agriautolab.contracts.rows import RowStructure


def _nonzero_vectors(path: tuple[Point, ...]) -> tuple[tuple[float, float], ...]:
    vectors: list[tuple[float, float]] = []
    for left, right in zip(path, path[1:]):
        dx = right.x - left.x
        dy = right.y - left.y
        if dx != 0.0 or dy != 0.0:
            vectors.append((dx, dy))
    return tuple(vectors)


def path_length(path: tuple[Point, ...]) -> float:
    """折线的欧氏弧长，单位米。"""
    return sum(math.dist(path[i].as_tuple(), path[i + 1].as_tuple()) for i in range(len(path) - 1))


def total_heading_change(path: tuple[Point, ...]) -> float:
    vectors = _nonzero_vectors(path)
    headings = tuple(math.atan2(dy, dx) for dx, dy in vectors)
    total = 0.0
    for first, second in zip(headings, headings[1:]):
        delta = (second - first + math.pi) % (2.0 * math.pi) - math.pi
        total += abs(delta)
    return total


def aol(path: tuple[Point, ...]) -> float:
    length = path_length(path)
    if length == 0.0:
        return 0.0
    return total_heading_change(path) / length


def tortuosity(path: tuple[Point, ...]) -> float:
    if len(path) < 2:
        return 1.0
    chord = math.dist(path[0].as_tuple(), path[-1].as_tuple())
    length = path_length(path)
    if chord == 0.0:
        return math.inf if length > 0.0 else 1.0
    return length / chord


def cusp_count(path: tuple[Point, ...], *, angle_tolerance_rad: float = 1e-9) -> int:
    vectors = _nonzero_vectors(path)
    count = 0
    for first, second in zip(vectors, vectors[1:]):
        dot = first[0] * second[0] + first[1] * second[1]
        cross = first[0] * second[1] - first[1] * second[0]
        angle = abs(math.atan2(cross, dot))
        if abs(angle - math.pi) <= angle_tolerance_rad:
            count += 1
    return count


def densify(path: tuple[Point, ...], max_step: float) -> tuple[Point, ...]:
    if max_step <= 0.0:
        raise ValueError("max_step 必须大于 0")
    if len(path) < 2:
        return path
    output: list[Point] = [path[0]]
    for start, end in zip(path, path[1:]):
        distance = math.dist(start.as_tuple(), end.as_tuple())
        quotient = distance / max_step
        nearest = round(quotient)
        divisions = max(1, nearest if math.isclose(quotient, nearest, rel_tol=1e-12, abs_tol=1e-12) else math.ceil(quotient))
        for index in range(1, divisions):
            ratio = index / divisions
            output.append(Point(x=start.x + ratio * (end.x - start.x), y=start.y + ratio * (end.y - start.y)))
        output.append(end)
    return tuple(output)


def resample_uniform(path: tuple[Point, ...], step: float) -> tuple[Point, ...]:
    """低通滤波器，不是几何等价变换。会切角、会缩短长度。

    Example: polyline (0,0)-(100,0)-(100,50) has length 150.0; sampled with step=60 yields 134.7.

    step 是协议参数：同 step 可比，跨 step 不可比。
    当前主流程不启用 —— 角度类指标直接在原始折线上计算即可，
    因为共线插点对航向变化的贡献为 0，纯粹的分段粒度差异本就不影响结果。
    它保留给需要抑制亚尺度锯齿的场景（例如未来接入栅格搜索输出的阶梯状路径）。
    """
    if step <= 0.0:
        raise ValueError("step 必须大于 0")
    if len(path) < 2:
        return path
    line = LineString([point.as_tuple() for point in path])
    if line.length == 0.0:
        return (path[0], path[-1])
    distances = list(np.arange(0.0, line.length, step))
    if not distances or distances[-1] != line.length:
        distances.append(line.length)
    samples = tuple(line.interpolate(distance) for distance in distances)
    return tuple(Point(x=sample.x, y=sample.y) for sample in samples)


def median_clearance(path: tuple[Point, ...], obstacles: BaseGeometry, *, sample_step: float) -> float:
    samples = densify(path, sample_step)
    distances = [obstacles.distance(ShapelyPoint(point.x, point.y)) for point in samples]
    return float(np.median(np.asarray(distances, dtype=float)))


def l0_zero_turn_radius(swath_paths: tuple[tuple[Point, ...], ...]) -> float:
    # Fields2Cover (arXiv:2210.07838) 式 (6)：零转弯半径基线。
    if not swath_paths:
        return 0.0
    total = sum(path_length(path) for path in swath_paths)
    total += sum(
        math.dist(swath_paths[i][-1].as_tuple(), swath_paths[i + 1][0].as_tuple())
        for i in range(len(swath_paths) - 1)
    )
    return total


def min_clearance(path: tuple[Point, ...], obstacles: BaseGeometry) -> float:
    if len(path) < 2:
        return obstacles.distance(ShapelyPoint(path[0].x, path[0].y)) if path else math.inf
    return LineString([point.as_tuple() for point in path]).distance(obstacles)


def transit_length(path: PathArtifact) -> float:
    """TRANSIT 段总长。

    Rank correlation with path_length ≈ 1.0 (transit = length − work);
    而 work ~= 面积/幅宽几乎不随配置变，两者共享同一自由度。注册为 DIAGNOSTIC，
    保留只为诊断「非作业里程里有多少是纯转场」，不进主指标向量。
    """
    return sum(
        math.dist((segment.line.points[0].x, segment.line.points[0].y),
                  (segment.line.points[-1].x, segment.line.points[-1].y))
        for segment in path.segments
        if segment.kind is PathSegmentKind.TRANSIT
    )


def headland_turn_count(path: PathArtifact) -> int:
    """地头掉头次数：相邻作业段之间的转移次数（被作业段夹住的非作业段游程数）。

    与禁用表里的 turn_count 是不同的量：turn_count 数折线顶点，对分段粒度敏感；
    本指标只数「作业段 -> 转移 -> 作业段」的边界，与 Dubins 连接段被采样成
    几条折线无关。放宽禁用表从来不是本指标的目的，两者并存且语义不同。
    """
    turns = 0
    in_transfer = False
    for segment in path.segments:
        if segment.kind is PathSegmentKind.WORK:
            if in_transfer:
                turns += 1
                in_transfer = False
        else:
            in_transfer = True
    return turns


@dataclass(frozen=True)
class TransferBreakdown:
    """转移长度的五项完备分解，专为定位「转移超额到底出在哪一项」而设。

    存在的理由：对账集 12 块地上 swath_length_sum 只差 +0.169%，
    path_length 差 -5.30%，而 transit 差 -38.1% —— 残差全在转移里。
    只有总数查不出 38% 从哪来：得知道它是首尾腿、掉头，还是跨 cell 转场。

    陷阱：other_m 不是「其他」筐，是完备性哨兵。非零即抛，因为分类不完备
    就是分类错误——藏在「其他」里的量永远不会有人去查。

    inter_cell_count 与 turn_count 分开计数，为的是能对上既有指标：
    headland_turn_count 数的是全部「作业->转移->作业」边界，因此恒等于
    turn_count + inter_cell_count。多 cell 语料上这是唯一能交叉校验分解完备性的等式
    （other_m 只查长度，查不出「掉头被错记成跨 cell」这类归类错误）。
    """

    entry_leg_m: float
    turn_total_m: float
    turn_count: int
    inter_cell_m: float
    inter_cell_count: int
    exit_leg_m: float
    other_m: float

    @property
    def total_m(self) -> float:
        return self.entry_leg_m + self.turn_total_m + self.inter_cell_m + self.exit_leg_m + self.other_m

    @property
    def mean_turn_m(self) -> float:
        """每次掉头的平均转移长度；无掉头时为 0.0，不是 NaN（要进 CSV）。"""
        return self.turn_total_m / self.turn_count if self.turn_count else 0.0


def transit_breakdown(
    path: PathArtifact,
    *,
    cell_of_work_index: tuple[int, ...] | None = None,
) -> TransferBreakdown:
    """把全部非作业段按位置归入五项之一，残余必须为 0。

    cell_of_work_index[k] 给出第 k 个作业段所属的 cell 序号；传 None 表示单 cell
    （此时 inter_cell_m 恒为 0）。它不从 Swath 契约里读——Swath 没有 cell_id，
    而 cell 归属可由 cells + 中心线几何唯一确定，不该为此新建第二处住所。

    作用域警告：本分解只在「作业段就是 swath 中心线」的管线上有意义。
    若将来某个 path 阶段改写作业段几何，turn_total_m 与 swath 侧的量就不再同域。
    """
    kinds = [segment.kind for segment in path.segments]
    lengths = [
        path_length(segment.line.points) for segment in path.segments
    ]
    work_positions = [index for index, kind in enumerate(kinds) if kind is PathSegmentKind.WORK]
    total_transit = sum(
        length for length, kind in zip(lengths, kinds) if kind is not PathSegmentKind.WORK
    )
    if not work_positions:
        # 一条作业段都没有：整条路径都是转移，且无法判断首腿还是尾腿。
        # 归入 other_m 并立刻抛出，好过悄悄记成 entry_leg。
        raise TransitDecompositionError(
            f"路径没有任何作业段，{total_transit:.6f} m 转移无法归类"
        )
    if cell_of_work_index is not None and len(cell_of_work_index) != len(work_positions):
        raise ValueError(
            f"cell_of_work_index 长度 {len(cell_of_work_index)} 与作业段数 {len(work_positions)} 不符"
        )

    first_work, last_work = work_positions[0], work_positions[-1]
    entry = sum(lengths[index] for index in range(first_work))
    exit_leg = sum(lengths[index] for index in range(last_work + 1, len(kinds)))

    turn_total = 0.0
    inter_cell = 0.0
    turn_count = 0
    inter_cell_count = 0
    classified = entry + exit_leg
    for order, (left, right) in enumerate(zip(work_positions, work_positions[1:])):
        run = sum(lengths[index] for index in range(left + 1, right))
        classified += run
        same_cell = (
            cell_of_work_index is None
            or cell_of_work_index[order] == cell_of_work_index[order + 1]
        )
        if same_cell:
            turn_total += run
            turn_count += 1
        else:
            inter_cell += run
            inter_cell_count += 1

    other = total_transit - classified
    # 容差按总转移的相对量级给：这里只做浮点求和顺序的兜底，不吸收任何几何差异。
    tolerance = max(1.0, abs(total_transit)) * 1e-12
    if abs(other) > tolerance:
        raise TransitDecompositionError(
            f"转移分解残余 other_m={other:.9f} m（总转移 {total_transit:.6f} m）："
            "有段落既不属于首尾腿也不属于段间转移，分类不完备"
        )
    return TransferBreakdown(
        entry_leg_m=entry,
        turn_total_m=turn_total,
        turn_count=turn_count,
        inter_cell_m=inter_cell,
        inter_cell_count=inter_cell_count,
        exit_leg_m=exit_leg,
        other_m=0.0 if abs(other) <= tolerance else other,
    )


def row_crossings(path: PathArtifact, row_structure: RowStructure | None) -> float:
    """路径对作物行的穿行次数，按段端点解析计算（投影差 / 行距）。

    row_structure 为 None（无行结构地块）时恒为 0。作业段是直线，端点投影即精确值；
    Dubins 转移段是弧，这里按其弦的投影计——弧的真实穿行数只会更多，
    因此该口径是穿行的下界，方向上不会把坏路径看好。此口径已写进注册表 notes。
    """
    if row_structure is None:
        return 0.0
    total = 0.0
    for segment in path.segments:
        points = segment.line.points
        total += row_structure.crossings_between(points[0].as_tuple(), points[-1].as_tuple())
    return total


# legacy 别名：transit 一词与路径阶段语义混叠，规范名 TransferBreakdown。
TransitBreakdown = TransferBreakdown
