"""D3 精确悔值表与训练集读取边界。"""

from pathlib import Path

import pytest

from agriautolab.contracts.vehicle import VehicleSpec
from agriautolab.pipeline.config import PipelineConfig
from agriautolab.selection.evaluation import build_selection_instance, load_selection_instances
from agriautolab.selection.protocol import SELECTION_FEATURE_IDS

VEHICLE = VehicleSpec(working_width_m=5.0, body_width_m=2.0, min_turning_radius_m=2.0, can_reverse=False)
A = PipelineConfig(
    "no_decomposition", "uniform_headland", "min_width", "boustrophedon_order", "dubins_transit",
    {"headland_width_m": 8.0},
)
B = PipelineConfig(
    "no_decomposition", "uniform_headland", "min_width", "boustrophedon_order", "dubins_transit",
    {"headland_width_m": 12.0},
)
CONFIGS = (A, B)


def _row(field: str, instance: str, config: PipelineConfig, objectives, *, ok: bool = True, shift: float = 0.0):
    row = {
        "field_id": field,
        "instance_id": instance,
        "vehicle_index": 0,
        "config_id": config.config_id(),
        "runstatus": "ok" if ok else "outside_area",
        "failure_reason": None if ok else "validator_rejected:outside_area",
        "path_length": objectives[0] if ok else None,
        "headland_turns": objectives[1] if ok else None,
        "row_crossings": objectives[2] if ok else None,
        "ref_path_length": 100.0,
        "ref_headland_turns": 10.0,
        "ref_row_crossings": 10.0,
    }
    for index, feature_id in enumerate(SELECTION_FEATURE_IDS):
        row[f"feature__{feature_id}"] = float(index + 1) + shift
    return row


def test_exact_regret_and_random_applicable_expectation():
    rows = [
        _row("field-a", "instance-a", A, (10.0, 5.0, 2.0)),
        _row("field-a", "instance-a", B, (20.0, 2.0, 1.0)),
    ]
    instance = build_selection_instance(rows, CONFIGS, (VEHICLE,))
    assert instance.analyzable
    a = instance.regret_vector(A.config_id())
    b = instance.regret_vector(B.config_id())
    assert a[0] == pytest.approx(0.0)
    assert b[0] == pytest.approx(0.1)
    assert a[1] == pytest.approx(0.3)
    assert b[1] == pytest.approx(0.0)
    assert a[2] == pytest.approx(0.1)
    assert b[2] == pytest.approx(0.0)
    assert instance.random_applicable is not None
    assert instance.random_applicable[0] == pytest.approx(0.05)
    assert instance.random_applicable[1] == pytest.approx(0.15)
    assert instance.random_applicable[2] == pytest.approx(0.05)


def test_validator_rejection_gets_rmax_plus_one_penalty():
    rows = [
        _row("field-a", "instance-a", A, (10.0, 5.0, 2.0)),
        _row("field-a", "instance-a", B, (20.0, 2.0, 1.0), ok=False),
    ]
    instance = build_selection_instance(rows, CONFIGS, (VEHICLE,))
    assert instance.regret_vector(A.config_id()) == pytest.approx((0.0,) * 22)
    assert instance.regret_vector(B.config_id()) == pytest.approx((1.0,) * 22)
    assert instance.random_applicable == pytest.approx((0.5,) * 22)
    assert instance.random_nominal == pytest.approx((0.5,) * 22)


def test_zero_ok_instance_is_retained_but_regret_is_undefined():
    rows = [
        _row("field-zero", "instance-zero", A, (1.0, 1.0, 1.0), ok=False),
        _row("field-zero", "instance-zero", B, (1.0, 1.0, 1.0), ok=False),
    ]
    instance = build_selection_instance(rows, CONFIGS, (VEHICLE,))
    assert not instance.analyzable
    assert instance.observed_ok == frozenset()
    assert instance.random_applicable is None
    with pytest.raises(ValueError, match="未定义"):
        instance.regret_vector(A.config_id())


def test_zero_ok_historical_failure_rows_may_lack_features_without_disappearing():
    rows = [
        _row("field-zero", "instance-zero", A, (1.0, 1.0, 1.0), ok=False),
        _row("field-zero", "instance-zero", B, (1.0, 1.0, 1.0), ok=False),
    ]
    for row in rows:
        for feature_id in SELECTION_FEATURE_IDS:
            row[f"feature__{feature_id}"] = None
    instance = build_selection_instance(rows, CONFIGS, (VEHICLE,))
    assert not instance.analyzable
    assert instance.features is None
    assert instance.field_id == "field-zero"


def test_loader_scans_only_authorized_training_fields(tmp_path: Path):
    import pyarrow as pa
    import pyarrow.parquet as pq

    rows = [
        _row("train:with:colon", "train-instance", A, (10.0, 5.0, 2.0)),
        _row("train:with:colon", "train-instance", B, (20.0, 2.0, 1.0)),
        _row("holdout-field", "holdout-instance", A, (11.0, 4.0, 2.0), shift=100.0),
        _row("holdout-field", "holdout-instance", B, (21.0, 2.0, 1.0), shift=100.0),
    ]
    path = tmp_path / "runs.parquet"
    pq.write_table(pa.Table.from_pylist(rows), path)
    instances = load_selection_instances(path, ("train:with:colon",), CONFIGS, (VEHICLE,))
    assert len(instances) == 1
    assert instances[0].field_id == "train:with:colon"
    assert instances[0].features is not None
    assert instances[0].features[0] == 1.0


def test_missing_feature_is_loud_failure_for_analyzable_instance():
    rows = [
        _row("field-a", "instance-a", A, (10.0, 5.0, 2.0)),
        _row("field-a", "instance-a", B, (20.0, 2.0, 1.0)),
    ]
    for row in rows:
        row["feature__elongation"] = None
    with pytest.raises(ValueError, match="feature__elongation"):
        build_selection_instance(rows, CONFIGS, (VEHICLE,))
