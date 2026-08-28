"""用最短的、只前进的 Dubins 原语在有界曲率下连接有序 swath。"""

from __future__ import annotations

import math
from dataclasses import dataclass

from agriautolab.contracts.artifacts import PathArtifact, PathSegment, RouteArtifact
from agriautolab.contracts.enums import PathSegmentKind, SwathDirection
from agriautolab.contracts.errors import KinematicModelError
from agriautolab.contracts.geometry import LineStringSpec, Point, Pose2D
from agriautolab.contracts.vehicle import VehicleSpec


@dataclass(frozen=True)
class _DubinsWord:
    name: str
    params: tuple[float, float, float]


def _mod2pi(angle: float) -> float:
    return angle % (2.0 * math.pi)


def _lsl(alpha: float, beta: float, d: float) -> tuple[float, float, float] | None:
    sa, sb, ca, cb = math.sin(alpha), math.sin(beta), math.cos(alpha), math.cos(beta)
    cab = math.cos(alpha - beta)
    tmp0 = d + sa - sb
    p2 = 2.0 + d * d - 2.0 * cab + 2.0 * d * (sa - sb)
    if p2 < 0.0:
        return None
    tmp1 = math.atan2(cb - ca, tmp0)
    return (_mod2pi(tmp1 - alpha), math.sqrt(p2), _mod2pi(beta - tmp1))


def _rsr(alpha: float, beta: float, d: float) -> tuple[float, float, float] | None:
    sa, sb, ca, cb = math.sin(alpha), math.sin(beta), math.cos(alpha), math.cos(beta)
    cab = math.cos(alpha - beta)
    tmp0 = d - sa + sb
    p2 = 2.0 + d * d - 2.0 * cab + 2.0 * d * (sb - sa)
    if p2 < 0.0:
        return None
    tmp1 = math.atan2(ca - cb, tmp0)
    return (_mod2pi(alpha - tmp1), math.sqrt(p2), _mod2pi(tmp1 - beta))


def _lsr(alpha: float, beta: float, d: float) -> tuple[float, float, float] | None:
    sa, sb, ca, cb = math.sin(alpha), math.sin(beta), math.cos(alpha), math.cos(beta)
    cab = math.cos(alpha - beta)
    p2 = -2.0 + d * d + 2.0 * cab + 2.0 * d * (sa + sb)
    if p2 < 0.0:
        return None
    p = math.sqrt(p2)
    tmp0 = math.atan2(-ca - cb, d + sa + sb) - math.atan2(-2.0, p)
    return (_mod2pi(tmp0 - alpha), p, _mod2pi(tmp0 - beta))


def _rsl(alpha: float, beta: float, d: float) -> tuple[float, float, float] | None:
    sa, sb, ca, cb = math.sin(alpha), math.sin(beta), math.cos(alpha), math.cos(beta)
    cab = math.cos(alpha - beta)
    p2 = -2.0 + d * d + 2.0 * cab - 2.0 * d * (sa + sb)
    if p2 < 0.0:
        return None
    p = math.sqrt(p2)
    tmp0 = math.atan2(ca + cb, d - sa - sb) - math.atan2(2.0, p)
    return (_mod2pi(alpha - tmp0), p, _mod2pi(beta - tmp0))


def _rlr(alpha: float, beta: float, d: float) -> tuple[float, float, float] | None:
    sa, sb, ca, cb = math.sin(alpha), math.sin(beta), math.cos(alpha), math.cos(beta)
    cab = math.cos(alpha - beta)
    tmp0 = (6.0 - d * d + 2.0 * cab + 2.0 * d * (sa - sb)) / 8.0
    if abs(tmp0) > 1.0:
        return None
    p = _mod2pi(2.0 * math.pi - math.acos(tmp0))
    t = _mod2pi(alpha - math.atan2(ca - cb, d - sa + sb) + p / 2.0)
    q = _mod2pi(alpha - beta - t + p)
    return (t, p, q)


def _lrl(alpha: float, beta: float, d: float) -> tuple[float, float, float] | None:
    sa, sb, ca, cb = math.sin(alpha), math.sin(beta), math.cos(alpha), math.cos(beta)
    cab = math.cos(alpha - beta)
    tmp0 = (6.0 - d * d + 2.0 * cab + 2.0 * d * (-sa + sb)) / 8.0
    if abs(tmp0) > 1.0:
        return None
    p = _mod2pi(2.0 * math.pi - math.acos(tmp0))
    t = _mod2pi(-alpha - math.atan2(ca - cb, d + sa - sb) + p / 2.0)
    q = _mod2pi(beta - alpha - t + p)
    return (t, p, q)


# LaValle, Planning Algorithms (2006) 式 (15.44)：最短前进 Dubins 路径只需检查六个 word。
# 下列归一化闭式解沿用 Walker Dubins-Curves 对 Shkel & Lumelsky (2001) 分类公式的实现约定。
_WORDS = (
    ("LSL", _lsl),
    ("RSR", _rsr),
    ("LSR", _lsr),
    ("RSL", _rsl),
    ("RLR", _rlr),
    ("LRL", _lrl),
)


def _shortest_word(start: Pose2D, goal: Pose2D, radius: float) -> _DubinsWord:
    dx, dy = goal.x - start.x, goal.y - start.y
    distance = math.hypot(dx, dy)
    theta = math.atan2(dy, dx) if distance > 0.0 else 0.0
    alpha = _mod2pi(start.yaw_rad - theta)
    beta = _mod2pi(goal.yaw_rad - theta)
    d = distance / radius
    candidates: list[_DubinsWord] = []
    for name, solver in _WORDS:
        params = solver(alpha, beta, d)
        if params is not None:
            candidates.append(_DubinsWord(name=name, params=params))
    if not candidates:
        raise ValueError("两位姿之间不存在数值有效的 Dubins 解")
    return min(candidates, key=lambda word: (sum(word.params), word.name))


def _sample_arc(pose: Pose2D, angle: float, *, left: bool, radius: float, step: float) -> tuple[tuple[Point, ...], Pose2D]:
    arc_length = angle * radius
    divisions = max(1, math.ceil(arc_length / step))
    points = [pose.point()]
    for index in range(1, divisions + 1):
        partial = angle * index / divisions
        if left:
            yaw = pose.yaw_rad + partial
            x = pose.x + radius * (math.sin(yaw) - math.sin(pose.yaw_rad))
            y = pose.y - radius * (math.cos(yaw) - math.cos(pose.yaw_rad))
        else:
            yaw = pose.yaw_rad - partial
            x = pose.x + radius * (math.sin(pose.yaw_rad) - math.sin(yaw))
            y = pose.y + radius * (math.cos(yaw) - math.cos(pose.yaw_rad))
        points.append(Point(x=x, y=y))
    end = Pose2D(x=points[-1].x, y=points[-1].y, yaw_rad=yaw)
    return tuple(points), end


def _sample_straight(pose: Pose2D, length: float) -> tuple[tuple[Point, ...], Pose2D]:
    # UTM 坐标 ~5e6 下双精度步长 ~1e-9 m：绝对长度低于它的直线段起终点舍入为同一点，
    # 2 点重合的 LineString 被 validate_geometry 判「点数不足」（235 全量实测 610/30550，
    # 全部在 rural_postman_greedy 排序的连接段上）。坐标尺度阈值内原地保持位姿。
    coordinate_epsilon = 1e-9 * max(abs(pose.x), abs(pose.y), 1.0)
    if abs(length) <= coordinate_epsilon:
        return (pose.point(), pose.point()), pose
    end = Pose2D(
        x=pose.x + length * math.cos(pose.yaw_rad),
        y=pose.y + length * math.sin(pose.yaw_rad),
        yaw_rad=pose.yaw_rad,
    )
    return (pose.point(), end.point()), end


def _dubins_segments(start: Pose2D, goal: Pose2D, radius: float, step: float, serial_start: int) -> tuple[tuple[PathSegment, ...], int]:
    word = _shortest_word(start, goal, radius)
    pose = start
    output: list[PathSegment] = []
    serial = serial_start
    for primitive, normalized_length in zip(word.name, word.params):
        if normalized_length <= 1e-14:
            continue
        if primitive == "S":
            points, pose = _sample_straight(pose, normalized_length * radius)
            curvature = 0.0
        else:
            left = primitive == "L"
            points, pose = _sample_arc(pose, normalized_length, left=left, radius=radius, step=step)
            curvature = (1.0 if left else -1.0) / radius
        segment_id = f"path-{serial:05d}"
        output.append(
            PathSegment(
                segment_id=segment_id,
                kind=PathSegmentKind.TURN,
                line=LineStringSpec(geometry_id=segment_id, points=points),
                signed_curvature_m_inv=curvature,
            )
        )
        serial += 1
    if output:
        last = output[-1]
        patched_points = last.line.points[:-1] + (goal.point(),)
        output[-1] = last.model_copy(update={"line": last.line.model_copy(update={"points": patched_points})})
    # 坐标尺度下的零长直线段被折叠成 2 个重合点：不携带几何，留在产物里只会让
    # 校验器在 line_from_spec 判「点数不足」（235 全量实测）。尾段被 patch 过的除外——
    # patch 保证首尾点合法；真正的零长尾段同样按重合过滤。
    output = [
        segment for segment in output
        if len(segment.line.points) != 2 or segment.line.points[0] != segment.line.points[1]
    ]
    return tuple(output), serial


def _heading(points: tuple[Point, ...]) -> float:
    return math.atan2(points[-1].y - points[0].y, points[-1].x - points[0].x)


class DubinsPath:
    algorithm_id = "dubins_path"

    def __init__(self, sample_step_m: float = 0.25) -> None:
        if sample_step_m <= 0.0:
            raise ValueError("Dubins sample step must be greater than 0")
        self.sample_step_m = sample_step_m

    def run(self, route: RouteArtifact, robot: VehicleSpec) -> PathArtifact:
        # Dubins 曲线在 R=0 处无定义：归一化距离 d = distance / R 与曲率 1/R 同时发散。
        # 不在入口拦住的话，可原地转向的车会一路跑出 ZeroDivisionError 或满屏 NaN 坐标。
        if robot.can_turn_in_place:
            raise KinematicModelError(
                f"min_turning_radius_m={robot.min_turning_radius_m} 表示可原地转向，"
                "Dubins 曲线在零半径下无定义；这类车需要换用支持原地转向的路径阶段"
            )
        swath_by_id = {swath.swath_id: swath for swath in route.swaths}
        segments: list[PathSegment] = []
        serial = 0
        previous_end: Pose2D | None = None
        for traversal in route.traversals:
            swath = swath_by_id[traversal.swath_id]
            points = swath.centerline.points if traversal.direction is SwathDirection.FORWARD else tuple(reversed(swath.centerline.points))
            heading = _heading(points)
            start_pose = Pose2D(x=points[0].x, y=points[0].y, yaw_rad=heading)
            end_pose = Pose2D(x=points[-1].x, y=points[-1].y, yaw_rad=heading)
            if previous_end is not None:
                connector, serial = _dubins_segments(
                    previous_end,
                    start_pose,
                    robot.min_turning_radius_m,
                    self.sample_step_m,
                    serial,
                )
                segments.extend(connector)
            segment_id = f"path-{serial:05d}"
            segments.append(
                PathSegment(
                    segment_id=segment_id,
                    kind=PathSegmentKind.WORK,
                    line=LineStringSpec(geometry_id=segment_id, points=points),
                    signed_curvature_m_inv=0.0,
                )
            )
            serial += 1
            previous_end = end_pose
        return PathArtifact(segments=tuple(segments))
