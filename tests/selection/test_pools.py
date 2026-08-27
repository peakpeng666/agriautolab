"""三层池契约测试：静态规则、包含不变量、语料完整性与证据封存。"""

import json
from pathlib import Path

import pytest

from agriautolab.contracts.vehicle import VehicleSpec
from agriautolab.pipeline import jsonl_log
from agriautolab.pipeline.config import PipelineConfig
from agriautolab.selection.pools import InstancePools, seal_pool_census_ledger, static_applicable

FORWARD_ONLY = VehicleSpec(working_width_m=5.0, body_width_m=2.0, min_turning_radius_m=2.0, can_reverse=False)
REVERSING = VehicleSpec(working_width_m=5.0, body_width_m=2.0, min_turning_radius_m=2.5, can_reverse=True)

DUBINS = PipelineConfig(
    "no_decomposition",
    "uniform_headland",
    "min_width",
    "boustrophedon_order",
    "dubins_transit",
    {"headland_width_m": 8.0},
)
DUBINS_12M = PipelineConfig(
    "no_decomposition",
    "uniform_headland",
    "min_width",
    "boustrophedon_order",
    "dubins_transit",
    {"headland_width_m": 12.0},
)
RS = PipelineConfig(
    "no_decomposition",
    "uniform_headland",
    "row_aligned",
    "boustrophedon_order",
    "reeds_shepp_transit",
    {"headland_width_m": 8.0},
)


def _write_runs(tmp_path: Path, rows: list[dict]) -> Path:
    import pyarrow as pa
    import pyarrow.parquet as pq

    table = pa.Table.from_pylist(rows)
    path = tmp_path / "runs.parquet"
    pq.write_table(table, path)
    return path


def _run_row(instance_id: str, field_id: str, config: PipelineConfig, *, status: str = "ok") -> dict:
    return {
        "instance_id": instance_id,
        "field_id": field_id,
        "config_id": config.config_id(),
        "vehicle_index": 0,
        "runstatus": status,
        "failure_reason": None if status == "ok" else "validator_rejected:outside_area",
    }


def test_static_applicability_pairs_rs_with_reverse_capability():
    assert static_applicable(RS, REVERSING)
    assert not static_applicable(RS, FORWARD_ONLY)
    assert static_applicable(DUBINS, REVERSING)
    assert static_applicable(DUBINS, FORWARD_ONLY)


def test_unknown_stage_slot_is_not_applicable():
    typo = PipelineConfig(
        "no_decomposition",
        "uniform_headland",
        "min_width",
        "boustrophedon_order",
        "dubins_transit_typo",
        {},
    )
    assert not static_applicable(typo, REVERSING)


def test_containment_invariants_fail_loud():
    base = dict(
        instance_id="f:a:0:0.75:vehicle:0",
        field_id="f",
        vehicle_index=0,
        nominal=frozenset({"dubins", "rs"}),
    )
    InstancePools(applicable=frozenset({"dubins"}), observed_ok=frozenset(), **base).verify_containment()
    with pytest.raises(ValueError, match="O ⊄ A"):
        InstancePools(
            applicable=frozenset({"dubins"}), observed_ok=frozenset({"rs"}), **base
        ).verify_containment()
    with pytest.raises(ValueError, match="A ⊄ N"):
        InstancePools(
            applicable=frozenset({"dubins", "ghost"}), observed_ok=frozenset(), **base
        ).verify_containment()


def test_census_enforces_invariants_and_preserves_recorded_field_id(tmp_path):
    from agriautolab.selection.pools import census_from_runs

    field_id = "farm:west:parcel-7"
    iid = "opaque-instance-id-that-must-not-be-parsed"
    parquet = _write_runs(
        tmp_path,
        [
            _run_row(iid, field_id, DUBINS),
            _run_row(iid, field_id, DUBINS_12M, status="not_applicable"),
        ],
    )
    census = census_from_runs(parquet, (DUBINS, DUBINS_12M), (FORWARD_ONLY,))
    assert census["n_instances"] == 1
    assert census["nominal_size"] == 2
    assert census["applicable_by_vehicle"] == {"0": 2}
    pools = census["instances"][0]
    assert pools.field_id == field_id
    assert pools.observed_ok == {DUBINS.config_id()}


def test_census_rejects_truncated_or_duplicate_instance_matrix(tmp_path):
    from agriautolab.selection.pools import census_from_runs

    iid = "field-a:scenario"
    truncated = _write_runs(tmp_path, [_run_row(iid, "field-a", DUBINS)])
    with pytest.raises(ValueError, match="运行矩阵不完整"):
        census_from_runs(truncated, (DUBINS, DUBINS_12M), (FORWARD_ONLY,))

    duplicate = _write_runs(
        tmp_path,
        [
            _run_row(iid, "field-a", DUBINS),
            _run_row(iid, "field-a", DUBINS),
            _run_row(iid, "field-a", DUBINS_12M),
        ],
    )
    with pytest.raises(ValueError, match="重复运行行"):
        census_from_runs(duplicate, (DUBINS, DUBINS_12M), (FORWARD_ONLY,))


def test_pool_census_ledger_sealing_is_idempotent_and_conflict_safe(tmp_path):
    ledger = tmp_path / "ledger.jsonl"
    genesis = jsonl_log.entry(0, {"event": "cv_assignment_sealed", "study_id": "study"})
    ledger.write_text(json.dumps(genesis, sort_keys=True) + "\n", encoding="utf-8")
    payload = {
        "artifact": "pool_census",
        "file_sha256": "a" * 64,
        "nominal_size": 13,
        "applicable_by_vehicle": {"0": 11, "1": 13},
        "n_instances": 4700,
        "cv_spec_hash": "b" * 64,
    }

    first = seal_pool_census_ledger(payload, ledger)
    bytes_after_first = ledger.read_bytes()
    second = seal_pool_census_ledger(payload, ledger)
    assert second == first
    assert ledger.read_bytes() == bytes_after_first
    assert len(ledger.read_text(encoding="utf-8").splitlines()) == 2

    conflicting = dict(payload, file_sha256="c" * 64)
    with pytest.raises(ValueError, match="冲突"):
        seal_pool_census_ledger(conflicting, ledger)


