"""Reeds-Shepp 转移 path 阶段：允许倒车的连接段，零地头组合的解锁件。

Dubins 前向-only 掉头必须向 swath 端点外鼓出约 2R——零地头下永远越界（实测
constraint_violation:outside_area）。倒车把掉头换成「进-退-进」的三点转向，
鼓包收进作业走廊内，零地头才成为可行配置。词选与长度来自
kinematics.reeds_shepp（认证等级见其 docstring：可行且不劣于 Dubins，不保证全局最优）。
"""

from __future__ import annotations

import math

from agriautolab.contracts.artifacts import PathArtifact, PathSegment, RouteArtifact
from agriautolab.contracts.enums import PathSegmentKind, SwathDirection
from agriautolab.contracts.errors import KinematicModelError
from agriautolab.contracts.geometry import LineStringSpec, Point, Pose2D
from agriautolab.contracts.vehicle import VehicleSpec
from agriautolab.kinematics.reeds_shepp import ReverseCostModel, reeds_shepp_word, reeds_shepp_words


def _sample_arc(pose: Pose2D, angle: float, *, left: bool, radius: float, step: float):
    """弧段采样：角度带符号（负 = 倒车行驶），几何与曲率不受行进方向影响。"""
    arc_length = abs(angle) * radius
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
            # 右转分支与左转镜像对称（Block A DubinsPath 原式）：此处曾把 y 的差分方向
            # 抄反，采样弧翻到对称象限，row_aligned 对角场景 y 掉到 -1.9、outside_area 13.2 m²。
            y = pose.y + radius * (math.cos(yaw) - math.cos(pose.yaw_rad))
        points.append(Point(x=x, y=y))
    end_yaw = pose.yaw_rad + (angle if left else -angle)
    return tuple(points), Pose2D(x=points[-1].x, y=points[-1].y, yaw_rad=end_yaw)


def _sample_straight(pose: Pose2D, length: float, step: float):
    """直线采样：负长度 = 倒车（沿航向反方向）。"""
    end = Pose2D(
        x=pose.x + length * math.cos(pose.yaw_rad),
        y=pose.y + length * math.sin(pose.yaw_rad),
        yaw_rad=pose.yaw_rad,
    )
    divisions = max(1, math.ceil(abs(length) / step))
    points = []
    for index in range(divisions + 1):
        fraction = index / divisions
        points.append(Point(
            x=pose.x + length * fraction * math.cos(pose.yaw_rad),
            y=pose.y + length * fraction * math.sin(pose.yaw_rad),
        ))
    return tuple(points), end


def _sample_word_polyline(start: Pose2D, word, radius: float, per_segment: int = 48):
    """稠密采样词折线（包含性筛查用；最终判定仍由校验器的精确扫掠做）。"""
    points: list[tuple[float, float]] = [(start.x, start.y)]
    x, y, yaw = start.x, start.y, start.yaw_rad
    for letter, normalized in zip(word.letters, word.params):
        if letter == "S":
            for index in range(1, per_segment + 1):
                length = normalized * radius * index / per_segment
                points.append((x + length * math.cos(yaw), y + length * math.sin(yaw)))
            length = normalized * radius
            x += length * math.cos(yaw)
            y += length * math.sin(yaw)
        else:
            sign = 1.0 if letter == "L" else -1.0
            center_x = x - sign * radius * math.sin(yaw)
            center_y = y + sign * radius * math.cos(yaw)
            for index in range(1, per_segment + 1):
                yaw_partial = yaw + sign * normalized * index / per_segment
                points.append((
                    center_x + sign * radius * math.sin(yaw_partial),
                    center_y - sign * radius * math.cos(yaw_partial),
                ))
            yaw = yaw + sign * normalized
            x = center_x + sign * radius * math.sin(yaw)
            y = center_y - sign * radius * math.cos(yaw)
    return points


def _contained_word(start: Pose2D, goal: Pose2D, radius: float, body_width_m: float, allowed_region):
    """按代价升序取第一个车体扫掠不越出允许域的词。

    最短词常有等长孪生：先前进的版本向端点外鼓包（约 2R），先倒车的时间反演
    孪生把掉头收进作业走廊——长度完全相同（时间反演对称的直接推论）。
    没有任何词包含在域内时返回 None，调用方退回最短词、交给校验器裁决。
    """
    from shapely import LineString
    from shapely.geometry.base import BaseGeometry as _BaseGeometry  # noqa: F401
    from agriautolab.geometry.footprint import QUAD_SEGS

    words = sorted(
        reeds_shepp_words(start, goal, radius),
        key=lambda word: (word.geometric_length(radius), word.name),
    )
    for word in words:
        polyline = LineString(_sample_word_polyline(start, word, radius))
        sweep = polyline.buffer(body_width_m / 2.0, cap_style="round", join_style="round", quad_segs=QUAD_SEGS)
        if sweep.difference(allowed_region).area <= 1e-9:
            return word
    return None


def _reeds_shepp_segments(start: Pose2D, goal: Pose2D, radius: float, step: float,
                          serial_start: int, cost_model: ReverseCostModel, allowed_region=None,
                          body_width_m: float = 0.0):
    if allowed_region is not None:
        word = _contained_word(start, goal, radius, body_width_m, allowed_region)
        if word is None:
            word = reeds_shepp_word(start, goal, radius, cost_model=cost_model)
    else:
        word = reeds_shepp_word(start, goal, radius, cost_model=cost_model)
    pose = start
    output: list[PathSegment] = []
    serial = serial_start
    for letter, normalized in zip(word.letters, word.params):
        length = normalized * radius
        if abs(length) <= 1e-12:
            continue
        if letter == "S":
            points, pose = _sample_straight(pose, length, step)
            curvature = 0.0
        else:
            points, pose = _sample_arc(pose, normalized, left=(letter == "L"), radius=radius, step=step)
            curvature = (1.0 if letter == "L" else -1.0) / radius
        segment_id = f"path-{serial:05d}"
        output.append(PathSegment(
            segment_id=segment_id,
            kind=PathSegmentKind.TURN,
            line=LineStringSpec(geometry_id=segment_id, points=points),
            signed_curvature_m_inv=curvature,
            reversing=length < 0.0,
        ))
        serial += 1
    if output:
        # 与 DubinsPath 同款收尾：把最后一个采样点对齐到精确终点，采样截断误差不过夜。
        last = output[-1]
        patched = last.line.points[:-1] + (goal.point(),)
        output[-1] = last.model_copy(update={"line": last.line.model_copy(update={"points": patched})})
    return tuple(output), serial


class ReedsSheppTransit:
    algorithm_id = "reeds_shepp_transit"

    def __init__(self, sample_step_m: float = 0.25, *, cost_model: ReverseCostModel) -> None:
        """cost_model 无默认值：倒车代价是协议参数（BenchmarkProtocol.reverse_cost），
        由调用方从协议里取出后显式传入。给默认值等于让阶段自己决定目标函数。"""
        if sample_step_m <= 0.0:
            raise ValueError("采样步长必须大于 0")
        self.sample_step_m = sample_step_m
        self.cost_model = cost_model

    def run(self, route: RouteArtifact, robot: VehicleSpec, *, allowed_region=None) -> PathArtifact:
        # Reeds-Shepp 的全部意义在倒车；不可倒车的机具应走 Dubins 阶段，
        # 在这里静默跑前向词等于伪装成"用了 RS"。
        if not robot.can_reverse:
            raise KinematicModelError(
                "reeds_shepp_transit 需要可倒车机具（can_reverse=True）；"
                "纯前向车辆请使用 dubins_transit"
            )
        swath_by_id = {swath.swath_id: swath for swath in route.swaths}
        segments: list[PathSegment] = []
        serial = 0
        previous_end: Pose2D | None = None
        for traversal in route.traversals:
            swath = swath_by_id[traversal.swath_id]
            points = swath.centerline.points if traversal.direction is SwathDirection.FORWARD else tuple(reversed(swath.centerline.points))
            heading = math.atan2(points[-1].y - points[0].y, points[-1].x - points[0].x)
            start_pose = Pose2D(x=points[0].x, y=points[0].y, yaw_rad=heading)
            end_pose = Pose2D(x=points[-1].x, y=points[-1].y, yaw_rad=heading)
            if previous_end is not None:
                connector, serial = _reeds_shepp_segments(
                    previous_end, start_pose, robot.min_turning_radius_m,
                    self.sample_step_m, serial, self.cost_model,
                    allowed_region=allowed_region, body_width_m=robot.body_width_m,
                )
                segments.extend(connector)
            segment_id = f"path-{serial:05d}"
            segments.append(PathSegment(
                segment_id=segment_id,
                kind=PathSegmentKind.WORK,
                line=LineStringSpec(geometry_id=segment_id, points=points),
                signed_curvature_m_inv=0.0,
            ))
            serial += 1
            previous_end = end_pose
        return PathArtifact(segments=tuple(segments))
