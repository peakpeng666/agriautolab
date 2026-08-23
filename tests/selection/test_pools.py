"""三层池契约测试：静态规则、包含不变量、普查结构（D2）。"""

import json
from pathlib import Path

import pytest

from agriautolab.contracts.vehicle import VehicleSpec
from agriautolab.pipeline.config import PipelineConfig
from agriautolab.selection.pools import InstancePools, static_applicable

FORWARD_ONLY = VehicleSpec(working_width_m=5.0, body_width_m=2.0, min_turning_radius_m=2.0, can_reverse=False)
REVERSING = VehicleSpec(working_width_m=5.0, body_width_m=2.0, min_turning_radius_m=2.5, can_reverse=True)

DUBINS = PipelineConfig("no_decomposition", "uniform_headland", "min_width",
                        "boustrophedon_order", "dubins_transit", {"headland_width_m": 8.0})
DUBINS_12M = PipelineConfig("no_decomposition", "uniform_headland", "min_width",
                            "boustrophedon_order", "dubins_transit", {"headland_width_m": 12.0})
RS = PipelineConfig("no_decomposition", "uniform_headland", "row_aligned",
                    "boustrophedon_order", "reeds_shepp_transit", {"headland_width_m": 8.0})


def test_static_applicability_pairs_rs_with_reverse_capability():
    assert static_applicable(RS, REVERSING)
    assert not static_applicable(RS, FORWARD_ONLY)
    assert static_applicable(DUBINS, REVERSING)
    assert static_applicable(DUBINS, FORWARD_ONLY)


def test_unknown_stage_slot_is_not_applicable():
    typo = PipelineConfig("no_decomposition", "uniform_headland", "min_width",
                          "boustrophedon_order", "dubins_transit_typo", {})
    assert not static_applicable(typo, REVERSING)


def test_containment_invariants_fail_loud():
    base = dict(instance_id="f:a:0:0.75:vehicle:0", field_id="f", vehicle_index=0,
                nominal=frozenset({"dubins", "rs"}))
    InstancePools(applicable=frozenset({"dubins"}), observed_ok=frozenset(), **base).verify_containment()
    with pytest.raises(ValueError, match="O ⊄ A"):
        InstancePools(applicable=frozenset({"dubins"}), observed_ok=frozenset({"rs"}), **base).verify_containment()
    with pytest.raises(ValueError, match="A ⊄ N"):
        InstancePools(applicable=frozenset({"dubins", "ghost"}), observed_ok=frozenset(), **base).verify_containment()


def test_census_enforces_invariants_per_instance(tmp_path):
    import pyarrow as pa
    import pyarrow.parquet as pq
    from agriautolab.selection.pools import census_from_runs

    iid = "f:principal_axis:0.0:0.75:vehicle:0"
    table = pa.table({
        "instance_id": pa.array([iid, iid], pa.string()),
        "config_id": pa.array([DUBINS.config_id(), DUBINS_12M.config_id()], pa.string()),
        "vehicle_index": pa.array([0, 0], pa.int64()),
        "runstatus": pa.array(["ok", "not_applicable"], pa.string()),
        "failure_reason": pa.array([None, "validator_rejected:outside_area"], pa.string()),
    })
    parquet = tmp_path / "runs.parquet"
    pq.write_table(table, parquet)
    census = census_from_runs(parquet, (DUBINS, DUBINS_12M), (FORWARD_ONLY,))
    assert census["n_instances"] == 1
    assert census["nominal_size"] == 2
    assert census["applicable_by_vehicle"] == {"0": 2}
    pools = census["instances"][0]
    # derived_status 口径：carve 行（not_applicable + validator 理由）不算 ok
    assert pools.observed_ok == {DUBINS.config_id()}


def test_committed_census_artifact_structure():
    """CI 上钉住普查产物的结构契约（文件随 D2 提交）。"""
    path = Path(__file__).resolve().parents[2] / "evidence" / "block_d" / "pool_census.json"
    if not path.exists():
        pytest.skip("普查产物在数据机上生成后提交")
    doc = json.loads(path.read_text(encoding="utf-8"))
    assert doc["stage"] == "D2-pool-census"
    assert doc["nominal_size"] == 13
    assert doc["invariants"]["o_subset_a"] and doc["invariants"]["a_subset_n"]
    assert doc["summary"]["train_fields"] == 165
    assert doc["summary"]["holdout_fields"] == 70
    assert len(doc["fields"]) == 235
    for field in doc["fields"]:
        assert field["split"] in {"train", "holdout"}
        assert (field["fold"] is None) == (field["split"] == "holdout")
