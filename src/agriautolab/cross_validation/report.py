"""只对共有语义的量出交叉验证报告。"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass
from typing import Iterable

from agriautolab.cross_validation.f2c import (
    CrsMismatchError,
    F2CResult,
    RouteAlgorithmMismatchError,
)


@dataclass(frozen=True)
class Disagreement:
    request_id: str
    ours: float
    reference: float
    abs_diff: float
    # 有符号，分母恒为 reference（golden）。名字里带 vs_golden 是纪律不是修辞：
    # 本项目已三次因百分比分母产生歧义（round−mitre 的 0.5033/0.5008、超体积归一化、
    # 以及 6.3451%/−5.2953% 这一次）。口头约定留不住，只能写进列名。
    rel_diff_vs_golden: float


@dataclass(frozen=True)
class CrossValidationReport:
    metric_id: str
    n_compared: int
    max_abs_diff: float
    # 取绝对值后的最大，与有符号的中位分开命名：一个量既叫 max 又带符号会读错方向。
    max_abs_rel_diff_vs_golden: float
    median_rel_diff_vs_golden: float
    disagreements: tuple[Disagreement, ...]
    # 两侧共同的 working CRS 与路线算法。比较能进行下去就说明两侧一致，所以各只存一个值。
    working_crs: str
    route_algorithm: str


def _require_same_working_crs(left: dict[str, F2CResult], right: dict[str, F2CResult]) -> str:
    """两侧必须在同一 working CRS 里录制，否则拒绝比较。

    照 available()=False 时抛异常的先例：不返回空报告、不静默比较。
    投影差异会以百分之几的形式渗进所有长度，与算法差异同量级且不可分辨——
    先排除它，才谈得上把残差归因给算法。
    """
    mismatched = tuple(
        (request_id, left[request_id].working_crs, right[request_id].working_crs)
        for request_id in sorted(left)
        if left[request_id].working_crs != right[request_id].working_crs
    )
    if mismatched:
        head = "; ".join(f"{rid}: ours={a} reference={b}" for rid, a, b in mismatched[:5])
        raise CrsMismatchError(
            f"{len(mismatched)}/{len(left)} 个请求两侧 working CRS 不一致，拒绝比较：{head}"
            + ("…" if len(mismatched) > 5 else "")
        )
    distinct = {row.working_crs for row in left.values()}
    # 逐地块局部 UTM 是既定形态：同一请求两侧一致即可，不要求全语料同一个 CRS。
    return sorted(distinct)[0] if len(distinct) == 1 else f"per-field({len(distinct)} CRS)"


def _require_same_route_algorithm(left: dict[str, F2CResult], right: dict[str, F2CResult]) -> str:
    """两侧必须跑同名路线算法，否则拒绝比较（Block C 规格 §3.5）。

    地头阶段早就配对了（CW ↔ uniform_headland），路线阶段一直没配。
    实测代价：F2C RP_Snake 访问顺序 [0,2,4,…,20,19,17,…,3,1]（隔行+回扫）
    对我方 boustrophedon_order（相邻），transit 中位差 −38.11%，
    而这个差曾被读成「我方路径更短」。
    """
    mismatched = tuple(
        (request_id, left[request_id].route_algorithm, right[request_id].route_algorithm)
        for request_id in sorted(left)
        if left[request_id].route_algorithm != right[request_id].route_algorithm
    )
    if mismatched:
        head = "; ".join(f"{rid}: ours={a} reference={b}" for rid, a, b in mismatched[:5])
        raise RouteAlgorithmMismatchError(
            f"{len(mismatched)}/{len(left)} 个请求两侧路线算法不同名，拒绝比较：{head}"
            + ("…" if len(mismatched) > 5 else "")
        )
    distinct = {row.route_algorithm for row in left.values()}
    if len(distinct) != 1:
        raise RouteAlgorithmMismatchError(
            f"同一批对账里混了多个路线算法：{sorted(distinct)}；一次只比一种"
        )
    return distinct.pop()


def compare_results(
    ours: Iterable[F2CResult],
    reference: Iterable[F2CResult],
    *,
    relative_tolerance: float = 1e-6,
) -> tuple[CrossValidationReport, ...]:
    """request_id 对齐后逐指标比较；初始相对容差固定 1e-6，不在函数内自适应放宽。"""
    left = {row.request_id: row for row in ours}
    right = {row.request_id: row for row in reference}
    if left.keys() != right.keys():
        raise ValueError(f"交叉验证 request_id 集合不同：ours-only={sorted(left.keys()-right.keys())}, ref-only={sorted(right.keys()-left.keys())}")
    working_crs = _require_same_working_crs(left, right)
    route_algorithm = _require_same_route_algorithm(left, right)
    reports = []
    # 分量拆解纪律：path_length = work + transit，work 已对齐而 transit 没有时，
    # 只报 path_length 会把 −38% 稀释成 −6%（差 6 倍）。转移分量必须单列。
    for metric in (
        "path_length", "swath_count", "swath_length_sum", "main_field_area",
        "transit_entry_leg_m", "transit_turn_total_m", "transit_turn_count",
        "transit_inter_cell_m", "transit_exit_leg_m",
    ):
        abs_diffs: list[float] = []
        rel_diffs: list[float] = []
        disagreements: list[Disagreement] = []
        for request_id in sorted(left):
            a = float(getattr(left[request_id], metric))
            b = float(getattr(right[request_id], metric))
            absolute = abs(a - b)
            # 分母恒为 reference。旧实现用 max(|a|,|b|)：在 ours > golden 的样本上
            # 它给出偏小的相对差（实测 f2b_004 13.7783% vs 15.9801%），
            # 而且随两侧谁大谁小切换分母，跨样本不是同一个量。
            relative = (a - b) / b if b != 0.0 else math.inf if a != b else 0.0
            abs_diffs.append(absolute)
            rel_diffs.append(relative)
            if abs(relative) > relative_tolerance:
                disagreements.append(Disagreement(request_id, a, b, absolute, relative))
        reports.append(CrossValidationReport(
            metric_id=metric,
            n_compared=len(left),
            max_abs_diff=max(abs_diffs, default=0.0),
            max_abs_rel_diff_vs_golden=max((abs(value) for value in rel_diffs), default=0.0),
            median_rel_diff_vs_golden=statistics.median(rel_diffs) if rel_diffs else 0.0,
            disagreements=tuple(disagreements),
            working_crs=working_crs,
            route_algorithm=route_algorithm,
        ))
    return tuple(reports)
