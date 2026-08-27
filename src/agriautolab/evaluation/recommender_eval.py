"""Recommender evaluation: one-shot field-level preference-conditioned Tchebycheff regret on holdout.

Estimand: per-field D_f = L_f^rec - 0.5 * L_f^rand_applicable (exact random-applicable
expectation); sign-flip permutation with 10^4 resamples, seed 20260822, one-sided
(smaller D_f is the alternative); both tracks reported (70 fields / 68 fields after
excluding the 2 debug-probe fields); zero-ok instances stay counted but enter no loss.
"""

from __future__ import annotations

from statistics import median
from typing import Sequence

PERMUTATION_N = 10_000
PERMUTATION_SEED = 20260822
PROBE_FIELDS = frozenset({"ee_field_37", "ee_field_117"})


def permutation_sign_flip_test(
    d_values: Sequence[float],
    *,
    n_permutations: int = PERMUTATION_N,
    seed: int = PERMUTATION_SEED,
) -> dict:
    """单侧（更小）符号翻转置换检验；加一法保证 p > 0。"""
    import numpy as np

    values = np.asarray([float(value) for value in d_values], dtype=float)
    observed = float(values.mean())
    rng = np.random.Generator(np.random.PCG64(seed))
    count = 0
    for _ in range(n_permutations):
        signs = rng.choice(np.asarray([-1.0, 1.0]), size=values.size)
        if float((values * signs).mean()) <= observed:
            count += 1
    return {
        "method": "sign-flip permutation, one-sided (smaller), add-one",
        "statistic": "mean_D",
        "observed_mean": observed,
        "n": int(values.size),
        "n_permutations": n_permutations,
        "seed": seed,
        "n_as_or_more_extreme": count,
        "pvalue": (count + 1) / (n_permutations + 1),
    }


def _track(fields, field_d: dict) -> dict:
    d_values = [field_d[field.field_id] for field in fields]
    test = permutation_sign_flip_test(d_values)
    rec = [field.recommender_loss for field in fields]
    ra = [field.random_applicable_loss for field in fields]
    return {
        "n_fields": len(fields),
        "mean_recommender_loss": sum(rec) / len(rec),
        "mean_random_applicable_loss": sum(ra) / len(ra),
        "mean_D": sum(d_values) / len(d_values),
        "median_D": median(d_values),
        "negative_D_share": sum(1 for value in d_values if value < 0) / len(d_values),
        "permutation": test,
    }


def evaluate_recommender(recommender, training_instances, holdout_instances) -> dict:
    """Run the one-shot holdout recommender evaluation; SBS learns only from training fields."""
    from agriautolab.selection.evaluation import select_sbs
    from agriautolab.selection.experiment import evaluate_fields

    all_config_ids = set()
    for instance in training_instances:
        all_config_ids |= instance.nominal
    sbs_config_id = select_sbs(training_instances, sorted(all_config_ids))

    fields = evaluate_fields(recommender, holdout_instances, sbs_config_id=sbs_config_id)
    analyzable = [field for field in fields if field.recommender_loss is not None]
    field_d = {
        field.field_id: field.recommender_loss - 0.5 * field.random_applicable_loss
        for field in analyzable
    }
    track_70 = _track(analyzable, field_d)
    track_68 = _track(
        [field for field in analyzable if field.field_id not in PROBE_FIELDS],
        field_d,
    )

    # 随机可适用基线的不可行率：uniform over A_x 抽到非 OK 配置的概率
    instance_share = []
    for instance in holdout_instances:
        if instance.analyzable:
            missing = len(instance.applicable - instance.observed_ok)
            instance_share.append(missing / len(instance.applicable))
    random_infeasible_rate = (
        sum(instance_share) / len(instance_share)
        if instance_share
        else 0.0
    )
    recommendation_count = sum(field.recommendation_count for field in fields)
    infeasible = sum(field.infeasible_recommendations for field in fields)
    recommender_infeasible_rate = (
        infeasible / recommendation_count
        if recommendation_count
        else 0.0
    )

    failure = {
        "criterion_1_mean_regret_not_below_half_random": track_70["mean_D"] >= 0.0,
        "criterion_2_infeasible_rate_above_random_applicable": (
            recommender_infeasible_rate > random_infeasible_rate
        ),
        "any_triggered": False,
    }
    failure["any_triggered"] = (
        failure["criterion_1_mean_regret_not_below_half_random"]
        or failure["criterion_2_infeasible_rate_above_random_applicable"]
    )

    return {
        "estimand": (
            "field-level preference-conditioned weighted Tchebycheff regret on holdout; "
            "D_f = L_f^rec - 0.5 * L_f^rand_applicable; one-shot holdout consumption"
        ),
        "sbs_config_id": sbs_config_id,
        "n_holdout_fields_total": len(fields),
        "n_analyzable_fields": len(analyzable),
        "n_zero_ok_only_fields": len(fields) - len(analyzable),
        "recommendation_count": recommendation_count,
        "infeasible_recommendations": infeasible,
        "recommender_infeasible_rate": recommender_infeasible_rate,
        "random_applicable_infeasible_rate": random_infeasible_rate,
        "track_70": track_70,
        "track_68_excluding_probe_fields": track_68,
        "failure_thresholds": failure,
        "scope_validity": (
            "Preference-conditional selection under the frozen 2-D agricultural CPP "
            "simulation protocol; holdout consumed once at the recommender evaluation stage."
        ),
    }


# Legacy aliases
analyze_h3 = evaluate_recommender
