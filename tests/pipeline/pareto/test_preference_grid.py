"""PREFERENCE_GRID_V1 契约：坐标冻结、哈希对账、零权重可表达（修正案 05 封口）。"""

import json
import math
from pathlib import Path

import pytest

from agriautolab.contracts.preference import MetricPreference, PreferenceSpec
from agriautolab.pipeline.pareto.preference_grid import (
    PREFERENCE_GRID_V1, grid_to_preference_spec, preference_grid_hash,
)
from agriautolab.pipeline.pareto.scalarize import preference_weights

EVIDENCE = Path(__file__).resolve().parents[3] / "evidence" / "preference_grid_v1.json"


def test_grid_is_on_simplex_and_unique():
    assert len(PREFERENCE_GRID_V1) == 22
    for w in PREFERENCE_GRID_V1:
        assert all(x >= 0.0 for x in w)
        assert math.isclose(sum(w), 1.0, abs_tol=1e-12)
    assert len(set(PREFERENCE_GRID_V1)) == 22
    # 三个顶点与三棱中点需在场（偏好条件评估的极端与对称探针）
    for vertex in ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)):
        assert vertex in PREFERENCE_GRID_V1
    for midpoint in ((0.5, 0.5, 0.0), (0.5, 0.0, 0.5), (0.0, 0.5, 0.5)):
        assert midpoint in PREFERENCE_GRID_V1


def test_grid_hash_matches_evidence_file():
    doc = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    assert doc["n"] == len(PREFERENCE_GRID_V1)
    assert [tuple(w) for w in doc["coordinates"]] == list(PREFERENCE_GRID_V1)
    assert doc["sha256"] == preference_grid_hash()


def test_zero_weight_vertices_are_expressible():
    # 修正案 04 的单纯形顶点在旧契约（weight > 0）下不可表达——本测试钉住修复
    for vertex in ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)):
        spec = grid_to_preference_spec(vertex)
        assert preference_weights(spec) == vertex


def test_all_grid_points_roundtrip_through_contract():
    for w in PREFERENCE_GRID_V1:
        assert preference_weights(grid_to_preference_spec(w)) == w


def test_all_zero_weights_rejected_but_zero_mixture_accepted():
    with pytest.raises(ValueError, match="positive"):
        PreferenceSpec(preferences=(
            MetricPreference(metric_id="path_length", weight=0.0),
            MetricPreference(metric_id="headland_turn_count", weight=0.0),
            MetricPreference(metric_id="row_crossings", weight=0.0),
        ))
    # 负权重仍然非法
    with pytest.raises(ValueError):
        MetricPreference(metric_id="path_length", weight=-0.1)
    # 边界：恰好全零之外的最小合法混合
    PreferenceSpec(preferences=(
        MetricPreference(metric_id="path_length", weight=0.0),
        MetricPreference(metric_id="headland_turn_count", weight=1e-12),
        MetricPreference(metric_id="row_crossings", weight=0.0),
    ))
