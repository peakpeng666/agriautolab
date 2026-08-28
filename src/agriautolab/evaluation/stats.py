"""确认性检验共用的、显式参数化的统计小工具。"""

from __future__ import annotations

import math
from typing import Iterable

import numpy as np


def distribution_summary(values: Iterable[float]) -> dict:
    """返回线性分位数口径的有限值分布摘要。"""
    array = np.asarray(tuple(float(value) for value in values), dtype=float)
    if array.size == 0:
        raise ValueError("分布摘要不能消费空样本")
    if not np.isfinite(array).all():
        raise ValueError("分布摘要只接受有限值")
    q1, median, q3 = np.quantile(array, (0.25, 0.5, 0.75), method="linear")
    return {
        "n": int(array.size),
        "min": float(np.min(array)),
        "q1": float(q1),
        "median": float(median),
        "q3": float(q3),
        "max": float(np.max(array)),
        "mean": float(np.mean(array)),
        "iqr": float(q3 - q1),
        "quantile_method": "numpy.quantile(method=linear)",
    }


def wilcoxon_greater(values: Iterable[float], *, null_value: float) -> dict:
    """One-sided univariate Wilcoxon: location parameter greater than ``null_value``.

    样本含大量 ties/zeros，故明确用渐近法而不让 SciPy 的 ``auto`` 随版本
    选择算法。零差按 Wilcox 规则从秩和中移除；全零样本单独定义为 p=1，
    表示对正向备择没有证据。
    """
    from scipy import __version__ as scipy_version
    from scipy.stats import wilcoxon

    array = np.asarray(tuple(float(value) for value in values), dtype=float)
    if array.size == 0:
        raise ValueError("Wilcoxon 不能消费空样本")
    if not np.isfinite(array).all() or not math.isfinite(null_value):
        raise ValueError("Wilcoxon 只接受有限值")
    differences = array - float(null_value)
    zero_mask = differences == 0.0
    n_zero = int(np.count_nonzero(zero_mask))
    common = {
        "alternative": "greater",
        "null_value": float(null_value),
        "zero_method": "wilcox",
        "correction": False,
        "method": "approx",
        "scipy_version": scipy_version,
        "n": int(array.size),
        "n_zero_differences": n_zero,
        "n_nonzero_differences": int(array.size - n_zero),
    }
    if n_zero == array.size:
        return {**common, "statistic": 0.0, "pvalue": 1.0, "zstatistic": None, "all_differences_zero": True}

    result = wilcoxon(
        differences,
        zero_method="wilcox",
        correction=False,
        alternative="greater",
        method="approx",
    )
    zstatistic = getattr(result, "zstatistic", None)
    return {
        **common,
        "statistic": float(result.statistic),
        "pvalue": float(result.pvalue),
        "zstatistic": None if zstatistic is None else float(zstatistic),
        "all_differences_zero": False,
    }

