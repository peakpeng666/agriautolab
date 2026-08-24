"""跨契约复用的浮点上界比较。

硬约束不能使用固定绝对容差：`1e-12` 对米级量可能很小，对 `1e-15` 的容量却
等于放宽约束一千倍。这里仅容忍少量 binary64 可表示步长，用于吸收连续减法或
`fsum` 后的舍入尾差；它不是业务容差，也不能把真实超限变成可行。
"""

from __future__ import annotations

import math

_MAX_ROUNDOFF_STEPS = 8


def not_greater_than_with_roundoff(value: float, upper_bound: float) -> bool:
    """判断 `value <= upper_bound`，只容忍有限个相邻 binary64 表示步长。

    两个输入必须是有限非负数。`upper_bound == 0` 时严格比较，避免把最小正浮点数
    当作“零附近容差”免费放行；正上界则最多向 `+inf` 方向移动 8 个 `nextafter`
    步长。这样容差随浮点表示精度缩放，而不会被任意的 `1.0` 下限主导。
    """
    if not math.isfinite(value) or not math.isfinite(upper_bound):
        raise ValueError("浮点上界比较只接受有限数")
    if value < 0.0 or upper_bound < 0.0:
        raise ValueError("浮点上界比较只接受非负数")
    if value <= upper_bound:
        return True
    if upper_bound == 0.0:
        return False

    tolerated_upper_bound = upper_bound
    for _ in range(_MAX_ROUNDOFF_STEPS):
        tolerated_upper_bound = math.nextafter(tolerated_upper_bound, math.inf)
    return value <= tolerated_upper_bound
