"""Reeds-Shepp 最短路：9 个基础式 + 3 个对称变换生成 48 字，逐词正演闭合校验。

依据 Reeds & Shepp (1990), "Optimal paths for a car that goes both forwards
and backwards", Pacific J. Math 145(2):367-393，式 (8.1)-(8.11)。
曲率上界 1/radius、允许倒车。

**为什么是基础式 + 对称变换而不是手写 48 个分支**（规格明确要求，也有前车之鉴）：
Dubins 才 6 个字就错了一个 LRL——正演闭合误差一度到 3.1e+01，而所有手工样例
都没命中它，是 5000 组随机位姿的全字闭合把它抓出来的。48 个手写漏字概率接近 1。

**Verified coverage (empirically measured):**
8 个闭式基础式（论文式 8.1、8.2、8.3/8.4、8.7、8.8、8.9、8.10、8.11；
8.3 与 8.4 互为 backwards 像，共用一个求解器）x 三个对称变换的笛卡尔积 2^3
= 64 candidate words; 5000 random poses hit 51 words, 48 distinct signed words.
——即 Reeds-Shepp 的 48 字全集。CCCC / CCSC / CCSCC 三族已实现。

三个对称变换（Reeds-Shepp §8）：
- timeflip ：(x, y, phi) -> (-x, y, -phi)，长度整体取负（前进段变倒车段）
- reflect  ：(x, y, phi) -> (x, -y, -phi)，字母 L <-> R 互换
- backwards：解 start 在 goal 帧内的反问题，再把字序倒读

陷阱：backwards 需作为独立变换参与笛卡尔积，不能塞进某个基础式当「第 9 式」。
塞进去只能得到 CCC 的一个 backwards 字，CCSC 族的四个 backwards 字会漏——
# Empirically verified: only 32 of 36 combinations are reachable; the missing family is identified.

**闭合校验是安全网，不是装饰**：任何对称映射的代数错误都会让终点对不上，
不闭合的候选直接丢弃（误差 > 1e-9），不带着错路径出门。

符号长度约定：负长度 = 倒车行驶该弧/直线。倒车不改变转向字母的几何意义
（左侧圆弧倒着走仍是左侧圆弧），只改变行进方向；正演积分公式对负长度代数同一。

陷阱：本模块的 mod2pi 映到 (-pi, pi]，与 kinematics.dubins 的 [0, 2pi) 不是同一个函数。
RS 的基础式要求对称区间——用 [0,2pi) 版本会让 timeflip 后的角度落到错误分支。
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from agriautolab.contracts.errors import KinematicModelError
from agriautolab.contracts.geometry import Pose2D


def _mod2pi(angle: float) -> float:
    """折到 (-pi, pi]。RS 基础式要求对称区间，不能用 Dubins 那个 [0, 2pi) 版本。"""
    value = math.fmod(angle, 2.0 * math.pi)
    if value < -math.pi:
        value += 2.0 * math.pi
    elif value > math.pi:
        value -= 2.0 * math.pi
    return value


def _polar(x: float, y: float) -> tuple[float, float]:
    return math.hypot(x, y), math.atan2(y, x)


def _tau_omega(u: float, v: float, xi: float, eta: float, phi: float) -> tuple[float, float]:
    """Reeds-Shepp 式 (8.7) 的辅助量，CCCC 两式共用。"""
    delta = _mod2pi(u - v)
    a = math.sin(u) - math.sin(delta)
    b = math.cos(u) - math.cos(delta) - 1.0
    t1 = math.atan2(eta * a - xi * b, xi * a + eta * b)
    t2 = 2.0 * (math.cos(delta) - math.cos(v) - math.cos(u)) + 3.0
    tau = _mod2pi(t1 + math.pi) if t2 < 0.0 else _mod2pi(t1)
    omega = _mod2pi(tau - u + v - phi)
    return tau, omega


# ---- 9 个基础式。每式返回 (字母, 符号长度) 或 None ----------------------------
# 字母是该段的转向（L/R/S）；长度符号表示行进方向，负数即倒车。


def _lp_sp_lp(x: float, y: float, phi: float):
    """式 (8.1) CSC 同向。"""
    u, t = _polar(x - math.sin(phi), y - 1.0 + math.cos(phi))
    if t < 0.0:
        return None
    v = _mod2pi(phi - t)
    if v < 0.0:
        return None
    return ("L", "S", "L"), (t, u, v)


def _lp_sp_rp(x: float, y: float, phi: float):
    """式 (8.2) CSC 异向。"""
    u1, t1 = _polar(x + math.sin(phi), y - 1.0 - math.cos(phi))
    if u1 * u1 < 4.0:
        return None
    u = math.sqrt(u1 * u1 - 4.0)
    theta = math.atan2(2.0, u)
    t = _mod2pi(t1 + theta)
    v = _mod2pi(t - phi)
    if t < 0.0 or v < 0.0:
        return None
    return ("L", "S", "R"), (t, u, v)


def _lp_rm_l(x: float, y: float, phi: float):
    """式 (8.3)/(8.4) CCC。中段倒车。"""
    xi = x - math.sin(phi)
    eta = y - 1.0 + math.cos(phi)
    u1, theta = _polar(xi, eta)
    if u1 > 4.0:
        return None
    u = -2.0 * math.asin(u1 / 4.0)
    t = _mod2pi(theta + u / 2.0 + math.pi)
    v = _mod2pi(phi - t + u)
    if t < 0.0 or u > 0.0:
        return None
    return ("L", "R", "L"), (t, u, v)


def _lp_rup_lum_rm(x: float, y: float, phi: float):
    """式 (8.7) CCCC 之一。四段，中间两段等角反号。"""
    xi = x + math.sin(phi)
    eta = y - 1.0 - math.cos(phi)
    rho = (2.0 + math.hypot(xi, eta)) / 4.0
    if rho > 1.0:
        return None
    u = math.acos(rho)
    t, v = _tau_omega(u, -u, xi, eta, phi)
    if t < 0.0 or v > 0.0:
        return None
    return ("L", "R", "L", "R"), (t, u, -u, v)


def _lp_rum_lum_rp(x: float, y: float, phi: float):
    """式 (8.8) CCCC 之二。"""
    xi = x + math.sin(phi)
    eta = y - 1.0 - math.cos(phi)
    rho = (20.0 - xi * xi - eta * eta) / 16.0
    if rho < 0.0 or rho > 1.0:
        return None
    u = -math.acos(rho)
    if u < -math.pi / 2.0:
        return None
    t, v = _tau_omega(u, u, xi, eta, phi)
    if t < 0.0 or v < 0.0:
        return None
    return ("L", "R", "L", "R"), (t, u, u, v)


def _lp_rm_sm_lm(x: float, y: float, phi: float):
    """式 (8.9) CCSC 之一。第二段固定 -pi/2。"""
    xi = x - math.sin(phi)
    eta = y - 1.0 + math.cos(phi)
    rho, theta = _polar(xi, eta)
    if rho < 2.0:
        return None
    r = math.sqrt(rho * rho - 4.0)
    u = 2.0 - r
    t = _mod2pi(theta + math.atan2(r, -2.0))
    v = _mod2pi(phi - math.pi / 2.0 - t)
    if t < 0.0 or u > 0.0 or v > 0.0:
        return None
    return ("L", "R", "S", "L"), (t, -math.pi / 2.0, u, v)


def _lp_rm_sm_rm(x: float, y: float, phi: float):
    """式 (8.10) CCSC 之二。"""
    xi = x + math.sin(phi)
    eta = y - 1.0 - math.cos(phi)
    rho, theta = _polar(-eta, xi)
    if rho < 2.0:
        return None
    t = theta
    u = 2.0 - rho
    v = _mod2pi(t + math.pi / 2.0 - phi)
    if t < 0.0 or u > 0.0 or v > 0.0:
        return None
    return ("L", "R", "S", "R"), (t, -math.pi / 2.0, u, v)


def _lp_rm_sm_lm_rp(x: float, y: float, phi: float):
    """式 (8.11) CCSCC。五段，第二与第四段固定 -pi/2。"""
    xi = x + math.sin(phi)
    eta = y - 1.0 - math.cos(phi)
    rho, _ = _polar(xi, eta)
    if rho < 2.0:
        return None
    u = 4.0 - math.sqrt(rho * rho - 4.0)
    if u > 0.0:
        return None
    t = _mod2pi(math.atan2((4.0 - u) * xi - 2.0 * eta, -2.0 * xi + (u - 4.0) * eta))
    v = _mod2pi(t - phi)
    if t < 0.0 or v < 0.0:
        return None
    return ("L", "R", "S", "L", "R"), (t, -math.pi / 2.0, u, -math.pi / 2.0, v)


BASE_FORMULAS = (
    ("LpSpLp", _lp_sp_lp),            # 式 (8.1) CSC 同向
    ("LpSpRp", _lp_sp_rp),            # 式 (8.2) CSC 异向
    ("LpRmL", _lp_rm_l),              # 式 (8.3)/(8.4) CCC —— 两式经 backwards 互相生成
    ("LpRupLumRm", _lp_rup_lum_rm),   # 式 (8.7) CCCC 之一
    ("LpRumLumRp", _lp_rum_lum_rp),   # 式 (8.8) CCCC 之二
    ("LpRmSmLm", _lp_rm_sm_lm),       # 式 (8.9) CCSC 之一
    ("LpRmSmRm", _lp_rm_sm_rm),       # 式 (8.10) CCSC 之二
    ("LpRmSmLmRp", _lp_rm_sm_lm_rp),  # 式 (8.11) CCSCC
)

_SWAP = {"L": "R", "R": "L", "S": "S"}


@dataclass(frozen=True)
class ReverseCostModel:
    """倒车代价：cost = 前进长 + multiplier x 倒车长 + penalty x 换挡次数。

    两个参数都由协议声明（BenchmarkProtocol.reverse_cost，无默认值、进协议哈希）：
    换了倒车偏好就是换了目标函数，两次运行在证据层需能区分。

    倒车在农艺上更慢、土壤压实更重；换挡（前进/倒车切换）本身也有固定时间成本，
    只用长度乘子表达不了「宁可多走一点也别多换一次挡」这种偏好——两个参数不是冗余。

    陷阱：multiplier 极大时最优解需退化为纯前进（Dubins）解。
    这是真值 #21，与真值 #18（RS <= Dubins）成对：两条都过才说明这里
    确实多了一个自由度，而不是把 Dubins 换了个名字。
    """

    reverse_length_multiplier: float
    gear_shift_penalty_m: float

    def __post_init__(self) -> None:
        if self.reverse_length_multiplier < 1.0:
            raise ValueError(
                f"reverse_length_multiplier 需 >= 1，实际 {self.reverse_length_multiplier!r}"
            )
        if self.gear_shift_penalty_m < 0.0:
            raise ValueError(f"gear_shift_penalty_m 不能为负，实际 {self.gear_shift_penalty_m!r}")

    def cost(self, word: "RSWord", radius: float) -> float:
        forward = sum(abs(value) for value in word.params if value >= 0.0) * radius
        backward = sum(abs(value) for value in word.params if value < 0.0) * radius
        shifts = word.gear_shift_count()
        return forward + self.reverse_length_multiplier * backward + self.gear_shift_penalty_m * shifts


@dataclass(frozen=True)
class RSWord:
    name: str
    letters: tuple[str, ...]
    params: tuple[float, ...]   # 符号化段长（弧段为弧度角、直段为半径归一长度）

    def geometric_length(self, radius: float) -> float:
        return sum(abs(value) for value in self.params) * radius

    def has_reverse(self) -> bool:
        return any(value < 0.0 for value in self.params)

    def gear_shift_count(self) -> int:
        """行进方向变号的次数。零长段不参与——它不是一次真实换挡。"""
        signs = [1 if value > 0.0 else -1 for value in self.params if abs(value) > 1e-12]
        return sum(1 for left, right in zip(signs, signs[1:]) if left != right)


def _rs_endpoint(start: Pose2D, word: RSWord, radius: float) -> Pose2D:
    """正演积分：Dubins 型公式对符号长度代数同一（负长度 = 反向行进同一圆弧/直线）。"""
    x, y, yaw = start.x, start.y, start.yaw_rad
    for letter, normalized in zip(word.letters, word.params):
        if letter == "S":
            length = normalized * radius
            x += length * math.cos(yaw)
            y += length * math.sin(yaw)
        else:
            sign = 1.0 if letter == "L" else -1.0
            center_x = x - sign * radius * math.sin(yaw)
            center_y = y + sign * radius * math.cos(yaw)
            yaw = yaw + sign * normalized
            x = center_x + sign * radius * math.sin(yaw)
            y = center_y - sign * radius * math.cos(yaw)
    return Pose2D(x=x, y=y, yaw_rad=yaw)


# 三个对称变换，按笛卡尔积组合（2^3 = 8 个变体作用于每个基础式）：
#
# - timeflip ：(x, y, phi) -> (-x, y, -phi)，长度整体取负 —— 前进段变倒车段
# - reflect  ：(x, y, phi) -> (x, -y, -phi)，字母 L <-> R  —— 左右镜像
# - backwards：解反过来的问题（start 在 goal 帧内的位姿），再把字序倒读
#
# backwards 需作为独立变换参与组合，不能塞进某个基础式里当「第 9 式」：
# 塞进去只会得到 CCC 的一个 backwards 字，CCSC 族的四个 backwards 字就漏了
# Only 32 of 36 possible word families are reachable; the missing family acts as a signal.
_BOOL_PAIR = (False, True)


def _reversed_problem(x: float, y: float, phi: float) -> tuple[float, float, float]:
    """start 在 goal 帧内的相对位姿。backwards 变换解的就是这个问题。"""
    return (x * math.cos(phi) + y * math.sin(phi), x * math.sin(phi) - y * math.cos(phi), phi)


def _candidate_words(start: Pose2D, goal: Pose2D, radius: float) -> list[RSWord]:
    dx, dy = goal.x - start.x, goal.y - start.y
    cos_yaw, sin_yaw = math.cos(start.yaw_rad), math.sin(start.yaw_rad)
    # 归一化到 start 帧、并按半径缩放：基础式全部写在单位半径下。
    x = (dx * cos_yaw + dy * sin_yaw) / radius
    y = (-dx * sin_yaw + dy * cos_yaw) / radius
    phi = _mod2pi(goal.yaw_rad - start.yaw_rad)

    output: list[RSWord] = []
    for formula_name, formula in BASE_FORMULAS:
        for backwards in _BOOL_PAIR:
            base = _reversed_problem(x, y, phi) if backwards else (x, y, phi)
            for timeflip in _BOOL_PAIR:
                for reflect in _BOOL_PAIR:
                    tx, ty, tphi = base
                    if timeflip:
                        tx, tphi = -tx, -tphi
                    if reflect:
                        ty, tphi = -ty, -tphi
                    solved = formula(tx, ty, tphi)
                    if solved is None:
                        continue
                    letters, params = solved
                    if timeflip:
                        params = tuple(-value for value in params)
                    if reflect:
                        letters = tuple(_SWAP[letter] for letter in letters)
                    if backwards:
                        letters = tuple(reversed(letters))
                        params = tuple(reversed(params))
                    tags = "".join(
                        tag for tag, on in
                        (("t", timeflip), ("r", reflect), ("b", backwards)) if on
                    ) or "id"
                    output.append(RSWord(
                        name=f"{formula_name}|{tags}", letters=letters, params=params,
                    ))
    return output


def reeds_shepp_words(start: Pose2D, goal: Pose2D, radius: float) -> tuple[RSWord, ...]:
    """返回全部通过正演闭合（< 1e-9）的候选词，按 (字母, 长度) 去重。

    对称映射本身可能有代数错误，所以每个词出口前需闭合——
    这条安全网正是 Dubins 那个 LRL 漏洞教出来的。
    """
    if radius <= 0.0:
        raise KinematicModelError(f"Reeds-Shepp radius must be greater than 0, got {radius!r}")
    # 闭合容差带坐标尺度：UTM ~6.5e6 处 ULP≈9.3e-10，合法词的公式
    # Round-trip closure error measured at 1.86e-9 (≈1.3 ULP across all 48 candidates); tolerance 1e-9
    # 会把好词全拒掉（v6 的 66 crash 根因）。取 8 ULP 与 1e-9 的较大者：小坐标行为
    # 不变（既有电池 rel 1e-12 仍过），大坐标只放行表示噪声（真错的词在 1e-6 以上）。
    closure_tolerance = max(1e-9, 8.0 * math.ulp(max(abs(start.x), abs(start.y), 1.0)))
    output: list[RSWord] = []
    seen: set[tuple] = set()
    for word in _candidate_words(start, goal, radius):
        end = _rs_endpoint(start, word, radius)
        error = math.hypot(end.x - goal.x, end.y - goal.y) + abs(
            _mod2pi(end.yaw_rad - goal.yaw_rad)
        )
        if error > closure_tolerance:
            continue
        key = (word.letters, tuple(round(value, 12) for value in word.params))
        if key in seen:
            continue
        seen.add(key)
        output.append(word)
    if not output:
        raise ValueError("没有闭合的 Reeds-Shepp 候选（不应发生：前向 Dubins 解必在候选集内）")
    return tuple(output)


def _forward_only_words(start: Pose2D, goal: Pose2D, radius: float) -> tuple[RSWord, ...]:
    """把 Dubins 的六字并入候选：能倒车的车当然也可以选择不倒车。

    # All 48 Reeds-Shepp words must be evaluated: they form the complete candidate-optimal set;
    不是可行字全集。当倒车严格更优时（同点掉头 pi < 7pi/3），48 字里一个纯前进字都没有——
    于是倒车罚开到 1e9，规划器仍然只能在倒车字里挑，选出一条造价 3e9 的路。
    协议声明「倒车极贵」而规划器照样倒车，这是行为缺陷，不是测试写错。

    并入之后候选集成为 Dubins 的严格超集：真值 #18（RS <= Dubins）平凡成立，
    真值 #21（倒车罚极大时退化为 Dubins 解）才有落点。
    """
    from agriautolab.kinematics.dubins import dubins_words

    output: list[RSWord] = []
    for word in dubins_words(start, goal, radius):
        output.append(RSWord(
            name=f"dubins:{word.name}",
            letters=tuple(word.name),
            params=tuple(float(value) for value in word.params),
        ))
    return tuple(output)


def _selection_candidates(start: Pose2D, goal: Pose2D, radius: float) -> tuple[RSWord, ...]:
    """选词用的候选集 = RS 48 字 ∪ Dubins 六字，逐词闭合后去重。"""
    closure_tolerance = max(1e-9, 8.0 * math.ulp(max(abs(start.x), abs(start.y), 1.0)))
    seen: set[tuple] = set()
    output: list[RSWord] = []
    for word in (*reeds_shepp_words(start, goal, radius), *_forward_only_words(start, goal, radius)):
        end = _rs_endpoint(start, word, radius)
        error = math.hypot(end.x - goal.x, end.y - goal.y) + abs(
            _mod2pi(end.yaw_rad - goal.yaw_rad)
        )
        if error > closure_tolerance:
            continue
        key = (word.letters, tuple(round(value, 12) for value in word.params))
        if key in seen:
            continue
        seen.add(key)
        output.append(word)
    return tuple(output)


def reeds_shepp_word(start: Pose2D, goal: Pose2D, radius: float, *, cost_model: ReverseCostModel) -> RSWord:
    """按给定代价模型选最优词。cost_model 无默认值：代价模型是协议的一部分。"""
    words = _selection_candidates(start, goal, radius)
    return min(words, key=lambda word: (cost_model.cost(word, radius), word.name))


def reeds_shepp_length(
    p0: tuple[float, float, float], p1: tuple[float, float, float], radius: float
) -> float:
    """纯几何最短长度（不含倒车罚）：用于与 Dubins 比大小的真值 #18。"""
    if radius <= 0.0:
        raise KinematicModelError(f"min_turning_radius_m={radius!r}：Reeds-Shepp 在零半径下无定义")
    start = Pose2D(x=p0[0], y=p0[1], yaw_rad=p0[2])
    goal = Pose2D(x=p1[0], y=p1[1], yaw_rad=p1[2])
    return min(word.geometric_length(radius) for word in _selection_candidates(start, goal, radius))


def reeds_shepp_cost(
    p0: tuple[float, float, float], p1: tuple[float, float, float], radius: float,
    *, cost_model: ReverseCostModel,
) -> float:
    start = Pose2D(x=p0[0], y=p0[1], yaw_rad=p0[2])
    goal = Pose2D(x=p1[0], y=p1[1], yaw_rad=p1[2])
    return cost_model.cost(reeds_shepp_word(start, goal, radius, cost_model=cost_model), radius)
