"""冻结 D1 field folds 上的 D4 交叉验证；统计单位始终是田。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from agriautolab.selection.evaluation import SelectionInstance, select_sbs
from agriautolab.selection.recommender import PreferenceConditionedRecommender


@dataclass(frozen=True)
class FieldEvaluation:
    field_id: str
    recommender_loss: float | None
    random_applicable_loss: float | None
    random_nominal_loss: float | None
    sbs_loss: float | None
    n_instances: int
    n_analyzable_instances: int
    n_zero_ok_instances: int
    recommendation_count: int
    infeasible_recommendations: int


@dataclass(frozen=True)
class FoldEvaluation:
    fold: int
    n_train_fields: int
    n_test_fields: int
    sbs_config_id: str
    fields: tuple[FieldEvaluation, ...]

    def summary(self) -> dict:
        analyzable = [field for field in self.fields if field.recommender_loss is not None]
        zero_only = [field for field in self.fields if field.n_analyzable_instances == 0]

        def mean(name: str) -> float | None:
            values = [getattr(field, name) for field in analyzable]
            numeric = [float(value) for value in values if value is not None]
            return sum(numeric) / len(numeric) if numeric else None

        recommendation_count = sum(field.recommendation_count for field in self.fields)
        infeasible = sum(field.infeasible_recommendations for field in self.fields)
        return {
            "fold": self.fold,
            "n_train_fields": self.n_train_fields,
            "n_test_fields": self.n_test_fields,
            "n_analyzable_test_fields": len(analyzable),
            "n_zero_ok_test_fields": len(zero_only),
            "sbs_config_id": self.sbs_config_id,
            "field_mean_recommender_loss": mean("recommender_loss"),
            "field_mean_random_applicable_loss": mean("random_applicable_loss"),
            "field_mean_random_nominal_loss": mean("random_nominal_loss"),
            "field_mean_sbs_loss": mean("sbs_loss"),
            "recommendation_count": recommendation_count,
            "infeasible_recommendations": infeasible,
            "infeasible_rate": infeasible / recommendation_count if recommendation_count else None,
        }


def evaluate_fields(
    recommender: PreferenceConditionedRecommender,
    instances: Sequence[SelectionInstance],
    *,
    sbs_config_id: str,
) -> tuple[FieldEvaluation, ...]:
    """对测试实例逐偏好推荐，再按田聚合；zero-OK instance 明确保留计数。"""
    by_field: dict[str, list[SelectionInstance]] = {}
    for instance in instances:
        by_field.setdefault(instance.field_id, []).append(instance)

    results = []
    for field_id in sorted(by_field):
        field_instances = by_field[field_id]
        analyzable = [instance for instance in field_instances if instance.analyzable]
        zero_ok = len(field_instances) - len(analyzable)
        if not analyzable:
            results.append(FieldEvaluation(
                field_id=field_id,
                recommender_loss=None,
                random_applicable_loss=None,
                random_nominal_loss=None,
                sbs_loss=None,
                n_instances=len(field_instances),
                n_analyzable_instances=0,
                n_zero_ok_instances=zero_ok,
                recommendation_count=0,
                infeasible_recommendations=0,
            ))
            continue

        rec_losses: list[float] = []
        applicable_losses: list[float] = []
        nominal_losses: list[float] = []
        sbs_losses: list[float] = []
        infeasible = 0
        recommendation_count = 0
        for instance in analyzable:
            assert instance.random_applicable is not None
            assert instance.random_nominal is not None
            sbs_vector = instance.regret_vector(sbs_config_id)
            for preference_index in range(22):
                recommended = recommender.recommend(instance.features, instance.applicable, preference_index)
                rec_losses.append(instance.regret_vector(recommended)[preference_index])
                applicable_losses.append(instance.random_applicable[preference_index])
                nominal_losses.append(instance.random_nominal[preference_index])
                sbs_losses.append(sbs_vector[preference_index])
                recommendation_count += 1
                if recommended not in instance.observed_ok:
                    infeasible += 1

        results.append(FieldEvaluation(
            field_id=field_id,
            recommender_loss=sum(rec_losses) / len(rec_losses),
            random_applicable_loss=sum(applicable_losses) / len(applicable_losses),
            random_nominal_loss=sum(nominal_losses) / len(nominal_losses),
            sbs_loss=sum(sbs_losses) / len(sbs_losses),
            n_instances=len(field_instances),
            n_analyzable_instances=len(analyzable),
            n_zero_ok_instances=zero_ok,
            recommendation_count=recommendation_count,
            infeasible_recommendations=infeasible,
        ))
    return tuple(results)


def run_frozen_grouped_cv(
    instances: Sequence[SelectionInstance],
    fold_of: Mapping[str, int],
    *,
    cv_spec_hash: str,
    pool_hash: str,
) -> tuple[FoldEvaluation, ...]:
    """严格消费 D1 已落盘的 field→fold；不接受临时重新 split。"""
    if not instances:
        raise ValueError("CV 实例不能为空")
    instance_fields = {instance.field_id for instance in instances}
    if instance_fields != set(fold_of):
        raise ValueError(
            f"CV field universe 与冻结折表不一致：missing={sorted(set(fold_of)-instance_fields)}, "
            f"extra={sorted(instance_fields-set(fold_of))}"
        )
    folds = sorted(set(fold_of.values()))
    if folds != list(range(1, 11)):
        raise ValueError(f"冻结 CV 必须恰好是 1..10 折，得到 {folds}")

    nominal_sets = {instance.nominal for instance in instances}
    if len(nominal_sets) != 1:
        raise ValueError("CV 实例的 nominal pool 不一致")
    nominal = next(iter(nominal_sets))

    results = []
    for fold in folds:
        train = [instance for instance in instances if fold_of[instance.field_id] != fold]
        test = [instance for instance in instances if fold_of[instance.field_id] == fold]
        train_fields = {instance.field_id for instance in train}
        test_fields = {instance.field_id for instance in test}
        if train_fields & test_fields:
            raise AssertionError("field-grouped CV 泄漏：同一田跨 train/test")
        sbs = select_sbs(train, nominal)
        recommender = PreferenceConditionedRecommender(cv_spec_hash=cv_spec_hash, pool_hash=pool_hash).fit(train)
        fields = evaluate_fields(recommender, test, sbs_config_id=sbs)
        results.append(FoldEvaluation(
            fold=fold,
            n_train_fields=len(train_fields),
            n_test_fields=len(test_fields),
            sbs_config_id=sbs,
            fields=fields,
        ))
    return tuple(results)
