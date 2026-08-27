"""Dubins 最短路的六字闭式解与正演闭合。

分类依据 Shkel & Lumelsky (2001), "Classification of the Dubins set",
Practical Planning of the Shortest Paths for Car-Like Robots: Anisotropic
Cost Factors 的六字枚举（LSL/RSR/LSR/RSL/RLR/LRL）；LaValle, Planning
Algorithms (2006) 式 (15.44) 保证最短前进路径必在这六个 word 里。

# Common implementation error: LRL word q computed as mod2pi(mod2pi(b) - a + mod2pi(2p)),
该式只在 t = -p 时成立，一般情况下三段转角不闭合（t - p + q != b - a）。
抄来的版本在 5000 组随机位姿的正演闭合测试里终点误差到过 3.1e+01，
六个字里只有 LRL 错，而五个手工样例一个都没命中它——正演闭合必须随机、必须大量。
本模块的 LRL 按几何推导：
    tmp = (6 - d^2 + 2cos(a-b) + 2d(sin b - sin a)) / 8
    p   = mod2pi(2pi - acos(tmp))
    psi = atan2(cos b - cos a, d + sin a - sin b)
    t   = mod2pi(psi + p/2 - a)
    q   = mod2pi(b - a - t + p)          # 三段转角代数和闭合：t - p + q = b - a
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from agriautolab.contracts.errors import KinematicModelError
from agriautolab.contracts.geometry import Pose2D

TWO_PI = 2.0 * math.pi


def _m2p(angle: float) -> float:
    return angle % TWO_PI


@dataclass(frozen=True)
class DubinsWord:
    name: str
    params: tuple[float, float, float]   # 归一化三段长度（弧度为单位的转角 / 直线长除以 R）

    def length(self, radius: float) -> float:
        return sum(self.params) * radius


def _lsl(a: float, b: float, d: float) -> tuple[float, float, float] | None:
    sa, sb, ca, cb = math.sin(a), math.sin(b), math.cos(a), math.cos(b)
    cab = math.cos(a - b)
    tmp0 = d + sa - sb
    p2 = 2.0 + d * d - 2.0 * cab + 2.0 * d * (sa - sb)
    if p2 < 0.0:
        return None
    tmp1 = math.atan2(cb - ca, tmp0)
    return (_m2p(tmp1 - a), math.sqrt(p2), _m2p(b - tmp1))


def _rsr(a: float, b: float, d: float) -> tuple[float, float, float] | None:
    sa, sb, ca, cb = math.sin(a), math.sin(b), math.cos(a), math.cos(b)
    cab = math.cos(a - b)
    tmp0 = d - sa + sb
    p2 = 2.0 + d * d - 2.0 * cab + 2.0 * d * (sb - sa)
    if p2 < 0.0:
        return None
    tmp1 = math.atan2(ca - cb, tmp0)
    return (_m2p(a - tmp1), math.sqrt(p2), _m2p(tmp1 - b))


def _lsr(a: float, b: float, d: float) -> tuple[float, float, float] | None:
    sa, sb, ca, cb = math.sin(a), math.sin(b), math.cos(a), math.cos(b)
    cab = math.cos(a - b)
    p2 = -2.0 + d * d + 2.0 * cab + 2.0 * d * (sa + sb)
    if p2 < 0.0:
        return None
    p = math.sqrt(p2)
    tmp0 = math.atan2(-ca - cb, d + sa + sb) - math.atan2(-2.0, p)
    return (_m2p(tmp0 - a), p, _m2p(tmp0 - b))


def _rsl(a: float, b: float, d: float) -> tuple[float, float, float] | None:
    sa, sb, ca, cb = math.sin(a), math.sin(b), math.cos(a), math.cos(b)
    cab = math.cos(a - b)
    p2 = -2.0 + d * d + 2.0 * cab - 2.0 * d * (sa + sb)
    if p2 < 0.0:
        return None
    p = math.sqrt(p2)
    tmp0 = math.atan2(ca + cb, d - sa - sb) - math.atan2(2.0, p)
    return (_m2p(a - tmp0), p, _m2p(b - tmp0))


def _rlr(a: float, b: float, d: float) -> tuple[float, float, float] | None:
    sa, sb, ca, cb = math.sin(a), math.sin(b), math.cos(a), math.cos(b)
    cab = math.cos(a - b)
    tmp0 = (6.0 - d * d + 2.0 * cab + 2.0 * d * (sa - sb)) / 8.0
    if abs(tmp0) > 1.0:
        return None
    p = _m2p(TWO_PI - math.acos(tmp0))
    t = _m2p(a - math.atan2(ca - cb, d - sa + sb) + p / 2.0)
    q = _m2p(a - b - t + p)
    return (t, p, q)


def _lrl(a: float, b: float, d: float) -> tuple[float, float, float] | None:
    tmp = (6.0 - d * d + 2.0 * math.cos(a - b) + 2.0 * d * (math.sin(b) - math.sin(a))) / 8.0
    if abs(tmp) > 1.0:
        return None
    p = _m2p(TWO_PI - math.acos(tmp))
    psi = math.atan2(math.cos(b) - math.cos(a), d + math.sin(a) - math.sin(b))
    t = _m2p(psi + p / 2.0 - a)
    q = _m2p(b - a - t + p)          # 三段转角代数和闭合：t - p + q = b - a
    return t, p, q


_WORDS = (
    ("LSL", _lsl),
    ("RSR", _rsr),
    ("LSR", _lsr),
    ("RSL", _rsl),
    ("RLR", _rlr),
    ("LRL", _lrl),
)


def dubins_words(start: Pose2D, goal: Pose2D, radius: float) -> tuple[DubinsWord, ...]:
    """返回六个 word 中数值有效的全部解（含三段参数），供正演闭合测试逐一验证。"""
    if radius <= 0.0:
        raise KinematicModelError(f"Dubins 半径必须大于 0，实际 {radius!r}")
    dx, dy = goal.x - start.x, goal.y - start.y
    distance = math.hypot(dx, dy)
    theta = math.atan2(dy, dx) if distance > 0.0 else 0.0
    alpha = _m2p(start.yaw_rad - theta)
    beta = _m2p(goal.yaw_rad - theta)
    d = distance / radius
    output = []
    for name, solver in _WORDS:
        params = solver(alpha, beta, d)
        if params is not None:
            output.append(DubinsWord(name=name, params=params))
    if not output:
        raise ValueError("两位姿之间不存在数值有效的 Dubins 解")
    return tuple(output)


def dubins_word(start: Pose2D, goal: Pose2D, radius: float) -> DubinsWord:
    """最短 word；总长并列时按名字字典序破平，保证确定性。"""
    words = dubins_words(start, goal, radius)
    return min(words, key=lambda word: (word.length(radius), word.name))


def dubins_length(p0: tuple[float, float, float], p1: tuple[float, float, float], radius: float) -> float:
    """(x,y,theta) -> (x,y,theta) 的最短 Dubins 路长。radius 必须 > 0。

    R=0（可原地转向）在此抛 KinematicModelError，与 DubinsPath 契约对 R=0
    入口的裁决一致：d = distance/R 与曲率 1/R 在零半径处同时发散。
    """
    if radius <= 0.0:
        raise KinematicModelError(f"min_turning_radius_m={radius!r}：Dubins 曲线在零半径下无定义")
    start = Pose2D(x=p0[0], y=p0[1], yaw_rad=p0[2])
    goal = Pose2D(x=p1[0], y=p1[1], yaw_rad=p1[2])
    return dubins_word(start, goal, radius).length(radius)


def dubins_endpoint(start: Pose2D, word: DubinsWord, radius: float) -> Pose2D:
    """按 word 正演到终点，用于闭合校验（与长度公式互为独立复核）。"""
    x, y, yaw = start.x, start.y, start.yaw_rad
    for primitive, normalized in zip(word.name, word.params):
        if primitive == "S":
            x += normalized * radius * math.cos(yaw)
            y += normalized * radius * math.sin(yaw)
        else:
            sign = 1.0 if primitive == "L" else -1.0
            center_x = x - sign * radius * math.sin(yaw)
            center_y = y + sign * radius * math.cos(yaw)
            yaw = yaw + sign * normalized
            x = center_x + sign * radius * math.sin(yaw)
            y = center_y - sign * radius * math.cos(yaw)
    return Pose2D(x=x, y=y, yaw_rad=yaw)
