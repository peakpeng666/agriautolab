"""推荐器与冻结 field-CV 的回归测试。"""

import pytest

from agriautolab.selection.evaluation import SelectionInstance
from agriautolab.selection.experiment import run_frozen_grouped_cv
from agriautolab.selection.protocol import SELECTION_FEATURE_IDS
from agriautolab.selection.recommender import PreferenceConditionedRecommender

A = "config-a"
B = "config-b"


def _instance(field: str, index: int) -> SelectionInstance:
    features = tuple(float(index + offset) for offset in range(len(SELECTION_FEATURE_IDS)))
    a = tuple(0.05 + 0.001 * index + 0.0001 * preference for preference in range(22))
    b = tuple(0.15 - 0.001 * index + 0.0001 * (21 - preference) for preference in range(22))
    random = tuple((left + right) / 2.0 for left, right in zip(a, b))
    return SelectionInstance(
        field_id=field,
        instance_id=f"{field}:instance",
        vehicle_index=0,
        features=features,
        nominal=frozenset({A, B}),
        applicable=frozenset({A, B}),
        observed_ok=frozenset({A, B}),
        regrets=((A, a), (B, b)),
        random_applicable=random,
        random_nominal=random,
    )


def test_recommender_never_bypasses_static_applicable_gate():
    instances = tuple(_instance(f"field-{index}", index) for index in range(6))
    model = PreferenceConditionedRecommender(cv_spec_hash="a" * 64, pool_hash="b" * 64).fit(instances)
    assert model.recommend(instances[0].features, (A,), 0) == A
    assert model.recommend(instances[0].features, (B,), 21) == B
    with pytest.raises(ValueError, match="A_x 为空"):
        model.recommend(instances[0].features, (), 0)
    with pytest.raises(ValueError, match="未拟合"):
        model.recommend(instances[0].features, ("ghost",), 0)
    with pytest.raises(ValueError, match=r"\[0, 21\]"):
        model.recommend(instances[0].features, (A, B), 22)


def test_model_metadata_binds_protocol_and_library_version():
    instances = tuple(_instance(f"field-{index}", index) for index in range(4))
    model = PreferenceConditionedRecommender(cv_spec_hash="c" * 64, pool_hash="d" * 64).fit(instances)
    metadata = model.metadata()
    assert metadata["cv_spec_hash"] == "c" * 64
    assert metadata["pool_hash"] == "d" * 64
    assert len(metadata["feature_ids"]) == 12
    assert metadata["fitted_config_ids"] == [A, B]
    assert metadata["sklearn_version"]
    assert metadata["params"]["random_state"] == 20260822
    assert metadata["params"]["n_jobs"] == 1


def test_grouped_cv_consumes_exact_frozen_field_map():
    instances = tuple(_instance(f"field-{index}", index) for index in range(10))
    fold_of = {f"field-{index}": index + 1 for index in range(10)}
    results = run_frozen_grouped_cv(
        instances,
        fold_of,
        cv_spec_hash="e" * 64,
        pool_hash="f" * 64,
    )
    assert len(results) == 10
    for result in results:
        assert result.n_train_fields == 9
        assert result.n_test_fields == 1
        assert len(result.fields) == 1
        assert result.fields[0].n_analyzable_instances == 1

    bad_map = dict(fold_of)
    bad_map.pop("field-9")
    with pytest.raises(ValueError, match="universe"):
        run_frozen_grouped_cv(instances, bad_map, cv_spec_hash="e" * 64, pool_hash="f" * 64)
