"""Synthetic data tests for recommender evaluation (no real holdout data accessed)."""

import math

from agriautolab.evaluation.recommender_eval import (
    PROBE_FIELDS,
    analyze_h3,
    permutation_sign_flip_test,
)
from agriautolab.selection.evaluation import SelectionInstance


def _instance(
    field: str,
    iid: str,
    *,
    regrets_a,
    regrets_b,
    ra,
    rn,
    ok_b=True,
    features=(1.0, 2.0),
):
    nominal = frozenset({"a", "b"})
    regrets = (
        ("a", tuple(regrets_a)),
        ("b", tuple(regrets_b)),
    )
    return SelectionInstance(
        field_id=field,
        instance_id=iid,
        vehicle_index=1,
        features=features,
        nominal=nominal,
        applicable=nominal,
        observed_ok=frozenset({"a", "b"} if ok_b else {"a"}),
        regrets=regrets,
        random_applicable=tuple(ra),
        random_nominal=tuple(rn),
    )


def _zeros_22(value):
    return [value] * 22


class _OracleRecommender:
    """总选该偏好下最优配置的作弊推荐器（用于检验聚合数学）。"""

    def recommend(self, features, applicable, preference_index):
        return "a"


class _BadRecommender:
    def recommend(self, features, applicable, preference_index):
        return "b"


def _make(field_prefix, n_fields):
    out = []
    for f in range(n_fields):
        field = f"{field_prefix}_{f}"
        for k in range(2):
            out.append(
                _instance(
                    field,
                    f"{field}:i{k}",
                    regrets_a=_zeros_22(0.0),
                    regrets_b=_zeros_22(1.0),
                    ra=_zeros_22(0.4),
                    rn=_zeros_22(0.6),
                )
            )
    return out


def test_permutation_deterministic_and_add_one():
    values = [0.1, -0.2, 0.05, -0.3, -0.15]
    first = permutation_sign_flip_test(values, n_permutations=500, seed=20260822)
    second = permutation_sign_flip_test(values, n_permutations=500, seed=20260822)
    assert first == second  # 种子钉死，逐位复现
    assert first["pvalue"] == (first["n_as_or_more_extreme"] + 1) / 501
    assert 0.0 < first["pvalue"] <= 1.0


def test_analyze_h3_dual_track_and_math():
    holdout = _make("h", 6) + [
        _instance(
            "ee_field_37",
            "ee_field_37:i0",
            regrets_a=_zeros_22(0.0),
            regrets_b=_zeros_22(1.0),
            ra=_zeros_22(0.4),
            rn=_zeros_22(0.6),
        ),
    ]
    training = _make("t", 4)
    result = analyze_h3(_OracleRecommender(), training, holdout)
    assert result["track_70"]["n_fields"] == 7
    assert result["track_68_excluding_probe_fields"]["n_fields"] == 6
    assert "ee_field_37" in PROBE_FIELDS
    # 推荐器恒选 a（悔值 0），D = 0 - 0.5*0.4 = -0.2
    assert math.isclose(result["track_70"]["mean_D"], -0.2, abs_tol=1e-12)
    assert result["track_70"]["negative_D_share"] == 1.0
    assert result["failure_thresholds"]["any_triggered"] is False


def test_even_field_median_uses_conventional_definition():
    training = _make("t", 3)
    holdout = []
    for index, random_loss in enumerate((0.2, 0.4, 0.6, 0.8)):
        field = f"h_{index}"
        holdout.append(
            _instance(
                field,
                f"{field}:i0",
                regrets_a=_zeros_22(0.0),
                regrets_b=_zeros_22(1.0),
                ra=_zeros_22(random_loss),
                rn=_zeros_22(0.6),
            )
        )

    result = analyze_h3(_OracleRecommender(), training, holdout)
    # D = (-0.1, -0.2, -0.3, -0.4)，偶数样本中位数应取中间两项均值。
    assert math.isclose(result["track_70"]["median_D"], -0.25, abs_tol=1e-12)


def test_failure_criterion_triggers_when_recommender_bad():
    holdout = _make("h", 5)
    training = _make("t", 3)
    result = analyze_h3(_BadRecommender(), training, holdout)
    # 恒选 b（悔值 1）> 0.5*0.4=0.2 → D=+0.8 → 失效判据 1 触发
    assert result["failure_thresholds"][
        "criterion_1_mean_regret_not_below_half_random"
    ]
    assert result["failure_thresholds"]["any_triggered"] is True


def test_zero_ok_instances_counted_not_consumed():
    zero = SelectionInstance(
        field_id="z",
        instance_id="z:i0",
        vehicle_index=1,
        features=None,
        nominal=frozenset({"a", "b"}),
        applicable=frozenset({"a", "b"}),
        observed_ok=frozenset(),
        regrets=None,
        random_applicable=None,
        random_nominal=None,
    )
    result = analyze_h3(
        _OracleRecommender(),
        _make("t", 3),
        _make("h", 4) + [zero],
    )
    assert result["n_holdout_fields_total"] == 5
    assert result["n_analyzable_fields"] == 4
    assert result["n_zero_ok_only_fields"] == 1
    assert result["track_70"]["n_fields"] == 4


def test_random_infeasible_rate_reflects_applicable_gap():
    gap = _instance(
        "g",
        "g:i0",
        regrets_a=_zeros_22(0.0),
        regrets_b=_zeros_22(1.0),
        ra=_zeros_22(0.4),
        rn=_zeros_22(0.6),
        ok_b=False,
    )
    result = analyze_h3(_OracleRecommender(), _make("t", 3), [gap])
    assert math.isclose(result["random_applicable_infeasible_rate"], 0.5)  # 1/2 of A_x
