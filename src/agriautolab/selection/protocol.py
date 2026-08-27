"""选择层的冻结执行协议：先定义评估与模型，再允许看 CV 结果。"""

from __future__ import annotations

from agriautolab.pipeline.hashing import content_hash
from agriautolab.pipeline.pareto.preference_grid import preference_grid_hash

SELECTION_PROTOCOL_VERSION = 1
SELECTION_STUDY_ID = "AGRIPLAN-PARETO-001"
SELECTION_SEED = 20260822

# wire feature ID 是 v7 parquet 的证据身份；顺序进入模型协议哈希。
SELECTION_FEATURE_IDS: tuple[str, ...] = (
    "area_m2",
    "perimeter_area_ratio",
    "convexity_deficiency",
    "elongation",
    "reflex_vertex_count",
    "obstacle_count",
    "obstacle_area_ratio",
    "row_angle_vs_principal",
    "crossing_density",
    "spacing_to_width_ratio",
    "turning_ratio",
    "swath_count_at_minwidth",
)

RECOMMENDER_CLASS = "sklearn.ensemble.ExtraTreesRegressor"
RECOMMENDER_SKLEARN_VERSION = "1.7.2"
RECOMMENDER_PARAMS = {
    "n_estimators": 192,
    "max_features": 1.0,
    "min_samples_leaf": 2,
    "bootstrap": False,
    "random_state": SELECTION_SEED,
    "n_jobs": 1,
}

ZERO_OK_POLICY = "regret_undefined__retain_and_block_confirmatory_h3"


def selection_protocol_payload(*, cv_spec_hash: str, pool_hash: str) -> dict:
    """D3-D4 的唯一机器可验协议；不包含任何 CV 结果。"""
    return {
        "schema_version": SELECTION_PROTOCOL_VERSION,
        "study_id": SELECTION_STUDY_ID,
        "seed": SELECTION_SEED,
        "cv_spec_hash": cv_spec_hash,
        "pool_hash": pool_hash,
        "feature_ids": list(SELECTION_FEATURE_IDS),
        "preference_grid": {
            "id": "PREFERENCE_GRID_V1",
            "n_points": 22,
            "hash": preference_grid_hash(),
        },
        "loss": {
            "name": "preference_conditioned_tchebycheff_regret",
            "normalization": "per-instance analytic reference columns",
            "oracle": "minimum over observed-OK pool O_x",
            "rejected_or_not_applicable_penalty": "max observed regret among A_x + 1",
            "zero_ok_policy": ZERO_OK_POLICY,
        },
        "baselines": {
            "primary": "random_applicable_exact_mean_over_A_x",
            "secondary": [
                "random_nominal_exact_mean_over_N_x",
                "SBS_training_field_level_loss",
            ],
            "oracle_sampling": False,
        },
        "cv": {
            "unit": "field_id",
            "fold_source": "evidence/v7/cv_assignment.json",
            "resplitting_forbidden": True,
            "holdout_consumption": "forbidden_before_D7_H3",
        },
        "recommender": {
            "class": RECOMMENDER_CLASS,
            "scikit_learn_version": RECOMMENDER_SKLEARN_VERSION,
            "params": dict(RECOMMENDER_PARAMS),
            "fit": "one multi-output model per config; rows restricted to instances where config in A_x",
            "sample_weight": "equal_per_analyzable_instance",
            "target": "22-vector of deterministic regrets",
            "inference": "filter candidates by A_x then choose minimum predicted regret at preference index",
            "hyperparameter_search": False,
        },
    }


def selection_protocol_hash(*, cv_spec_hash: str, pool_hash: str) -> str:
    return content_hash(selection_protocol_payload(cv_spec_hash=cv_spec_hash, pool_hash=pool_hash))
