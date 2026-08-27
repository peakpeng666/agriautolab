from __future__ import annotations

import math

import pytest

from agriautolab.evaluation.pareto_optimality import FrontInstance, analyze_h1, build_front_instance, field_estimates
from agriautolab.evaluation.stats import wilcoxon_greater


def _row(config_id: str, objectives, *, raw="ok", reason=None):
    path, turns, crossings = objectives
    return {
        "instance_id": "field-a:principal_axis:0.0:0.75:vehicle:0",
        "field_id": "field-a",
        "vehicle_index": 0,
        "config_id": config_id,
        "runstatus": raw,
        "failure_reason": reason,
        "path_length": path,
        "headland_turns": turns,
        "row_crossings": crossings,
    }


def test_front_recomputation_uses_derived_status_and_three_objectives():
    rows = [
        _row("a", (1.0, 3.0, 3.0)),
        _row("b", (3.0, 1.0, 3.0)),
        # raw=ok 也不能盖过 validator 的具名拒绝事实；否则它会虚假支配 a/b。
        _row("c", (0.0, 0.0, 0.0), raw="ok", reason="validator_rejected:outside_area"),
    ]
    instance = build_front_instance(rows, ("a", "b", "c"))
    assert instance.front_size == 2


def test_front_recomputation_rejects_incomplete_duplicate_or_invalid_ok_rows():
    with pytest.raises(ValueError, match="不完整"):
        build_front_instance([_row("a", (1, 2, 3))], ("a", "b"))
    with pytest.raises(ValueError, match="重复"):
        build_front_instance([_row("a", (1, 2, 3)), _row("a", (2, 3, 4))], ("a",))
    with pytest.raises(ValueError, match="主目标缺失"):
        build_front_instance([_row("a", (None, 2, 3))], ("a",))
    with pytest.raises(ValueError, match="有限"):
        build_front_instance([_row("a", (math.inf, 2, 3))], ("a",))


def test_field_estimands_keep_main_and_zero_as_zero_sensitivity_separate():
    instances = (
        FrontInstance("a", "a-1", 0, 1),
        FrontInstance("a", "a-2", 0, 3),
        FrontInstance("a", "a-3", 0, None),
        FrontInstance("b", "b-1", 0, None),
        FrontInstance("b", "b-2", 0, None),
    )
    estimates = field_estimates(instances, expected_field_ids=("a", "b"))
    assert estimates[0].median_defined_front_size == 2.0
    assert estimates[0].median_zero_as_zero_front_size == 1.0
    assert estimates[1].median_defined_front_size is None
    assert estimates[1].median_zero_as_zero_front_size == 0.0

    result = analyze_h1(estimates)
    assert result["n_analyzable_fields"] == 1
    assert result["n_zero_ok_fields"] == 1
    assert result["primary_distribution"]["median"] == 2.0
    assert result["sensitivity_zero_instance_as_front_zero_distribution"]["median"] == 0.5


def test_wilcoxon_all_null_values_reports_no_positive_evidence():
    result = wilcoxon_greater([1.0, 1.0, 1.0], null_value=1.0)
    assert result["pvalue"] == 1.0
    assert result["n_nonzero_differences"] == 0

