"""D4 偏好条件推荐器：每个配置一个固定规格的多输出 ExtraTrees。"""

from __future__ import annotations

import importlib.metadata
import json
from pathlib import Path
from typing import Iterable, Sequence

from agriautolab.selection.evaluation import SelectionInstance
from agriautolab.selection.protocol import (
    RECOMMENDER_PARAMS,
    RECOMMENDER_SKLEARN_VERSION,
    SELECTION_FEATURE_IDS,
    selection_protocol_hash,
)


class PreferenceConditionedRecommender:
    """预测每个配置在 22 个冻结偏好上的悔值，再在 A_x 内选最小者。"""

    def __init__(self, *, cv_spec_hash: str, pool_hash: str):
        self.cv_spec_hash = cv_spec_hash
        self.pool_hash = pool_hash
        self.protocol_hash = selection_protocol_hash(cv_spec_hash=cv_spec_hash, pool_hash=pool_hash)
        self._models: dict[str, object] = {}
        self._training_fields: tuple[str, ...] = ()

    @property
    def fitted_config_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._models))

    @property
    def training_fields(self) -> tuple[str, ...]:
        return self._training_fields

    def fit(self, instances: Sequence[SelectionInstance]) -> "PreferenceConditionedRecommender":
        """按配置拟合 22 维 regret；只用该配置静态适用且 oracle 可定义的实例。"""
        if not instances:
            raise ValueError("训练实例不能为空")
        actual_sklearn = importlib.metadata.version("scikit-learn")
        if actual_sklearn != RECOMMENDER_SKLEARN_VERSION:
            raise RuntimeError(
                f"selection protocol 要求 scikit-learn=={RECOMMENDER_SKLEARN_VERSION}，"
                f"当前为 {actual_sklearn}"
            )
        from sklearn.ensemble import ExtraTreesRegressor

        nominal_sets = {instance.nominal for instance in instances}
        if len(nominal_sets) != 1:
            raise ValueError("训练实例的 nominal pool 必须一致")
        nominal = next(iter(nominal_sets))
        models: dict[str, object] = {}
        for config_id in sorted(nominal):
            eligible = [
                instance
                for instance in instances
                if instance.analyzable and config_id in instance.applicable
            ]
            if len(eligible) < 2:
                raise ValueError(f"{config_id}: 可用于拟合的静态适用实例不足 2 个")
            if any(instance.features is None for instance in eligible):
                raise ValueError(f"{config_id}: 可分析训练实例缺少特征，证据 schema 自相矛盾")
            x = [instance.features for instance in eligible]
            y = [instance.regret_vector(config_id) for instance in eligible]
            model = ExtraTreesRegressor(**RECOMMENDER_PARAMS)
            model.fit(x, y)
            models[config_id] = model

        self._models = models
        self._training_fields = tuple(sorted({instance.field_id for instance in instances}))
        return self

    def predict_regrets(
        self,
        features: Sequence[float],
        applicable_config_ids: Iterable[str],
    ) -> dict[str, tuple[float, ...]]:
        if not self._models:
            raise ValueError("推荐器尚未 fit")
        feature_vector = tuple(float(value) for value in features)
        if len(feature_vector) != len(SELECTION_FEATURE_IDS):
            raise ValueError(f"特征维数必须为 {len(SELECTION_FEATURE_IDS)}")
        candidates = sorted(set(applicable_config_ids))
        if not candidates:
            raise ValueError("A_x 为空，无法推荐")
        missing = [config_id for config_id in candidates if config_id not in self._models]
        if missing:
            raise ValueError(f"A_x 含未拟合配置：{missing}")
        predictions = {}
        for config_id in candidates:
            raw = self._models[config_id].predict([feature_vector])[0]
            values = tuple(max(0.0, float(value)) for value in raw)
            if len(values) != 22:
                raise ValueError(f"{config_id}: 模型输出不是 22 维")
            predictions[config_id] = values
        return predictions

    def recommend(self, features: Sequence[float], applicable_config_ids: Iterable[str], preference_index: int) -> str:
        if preference_index < 0 or preference_index >= 22:
            raise ValueError("preference_index 必须在 [0, 21]")
        predictions = self.predict_regrets(features, applicable_config_ids)
        return min((values[preference_index], config_id) for config_id, values in predictions.items())[1]

    def metadata(self) -> dict:
        if not self._models:
            raise ValueError("推荐器尚未 fit")
        return {
            "class": type(self).__name__,
            "protocol_hash": self.protocol_hash,
            "cv_spec_hash": self.cv_spec_hash,
            "pool_hash": self.pool_hash,
            "feature_ids": list(SELECTION_FEATURE_IDS),
            "fitted_config_ids": list(self.fitted_config_ids),
            "training_fields": list(self.training_fields),
            "sklearn_version": importlib.metadata.version("scikit-learn"),
            "params": dict(RECOMMENDER_PARAMS),
        }

    def save(self, model_path: str | Path, metadata_path: str | Path) -> None:
        """模型二进制与可审计 metadata 分开落盘；metadata 绑定协议和 sklearn 版本。"""
        if not self._models:
            raise ValueError("推荐器尚未 fit")
        import joblib

        model_file = Path(model_path)
        metadata_file = Path(metadata_path)
        model_file.parent.mkdir(parents=True, exist_ok=True)
        metadata_file.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, model_file, compress=3)
        metadata_file.write_text(
            json.dumps(self.metadata(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
