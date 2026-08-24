"""硬约束浮点上界比较的解析边界。"""

import math

from agriautolab.contracts.numerics import not_greater_than_with_roundoff


def _next_float(value: float, steps: int) -> float:
    for _ in range(steps):
        value = math.nextafter(value, math.inf)
    return value


def test_zero_upper_bound_has_no_positive_roundoff_slack() -> None:
    assert not not_greater_than_with_roundoff(math.nextafter(0.0, math.inf), 0.0)
    assert not not_greater_than_with_roundoff(1e-15, 0.0)


def test_positive_upper_bound_accepts_only_bounded_float_steps() -> None:
    assert not_greater_than_with_roundoff(_next_float(1.0, 8), 1.0)
    assert not not_greater_than_with_roundoff(_next_float(1.0, 9), 1.0)


def test_roundoff_policy_scales_without_fixed_absolute_floor() -> None:
    upper_bound = 1e-15
    nearby = math.nextafter(upper_bound, math.inf)
    material_overflow = 2e-15

    assert not_greater_than_with_roundoff(nearby, upper_bound)
    assert not not_greater_than_with_roundoff(material_overflow, upper_bound)
