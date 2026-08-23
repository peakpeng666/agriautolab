from __future__ import annotations

from dataclasses import replace
import importlib.util
import json
from pathlib import Path

import pytest

from agriautolab.confirmatory.h2 import (
    OffsetFrontInstance,
    analyze_h2,
    build_offset_front_instance,
    field_effects,
)
from agriautolab.evidence.ledger import artifact_chain_entry


_SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "analyze_h2.py"
_SCRIPT_SPEC = importlib.util.spec_from_file_location("agriautolab_test_analyze_h2", _SCRIPT_PATH)
assert _SCRIPT_SPEC is not None and _SCRIPT_SPEC.loader is not None
_SCRIPT_MODULE = importlib.util.module_from_spec(_SCRIPT_SPEC)
_SCRIPT_SPEC.loader.exec_module(_SCRIPT_MODULE)
_validate_h1_field_reconciliation = _SCRIPT_MODULE._validate_h1_field_reconciliation
_validate_predecessor = _SCRIPT_MODULE._validate_predecessor


OFFSETS = (0.0, 1.0, 2.0, 3.0, 4.0)
SPACINGS = (0.75, 3.0)
VEHICLES = (0, 1)


def _raw_row(
    field_id: str,
    config_id: str,
    objectives,
    *,
    feature,
    raw: str = "ok",
    reason: str | None = None,
):
    path, turns, crossings = objectives
    return {
        "instance_id": f"{field_id}:principal_axis:0.0:0.75:vehicle:0",
        "field_id": field_id,
        "vehicle_index": 0,
        "config_id": config_id,
        "runstatus": raw,
        "failure_reason": reason,
        "path_length": path,
        "headland_turns": turns,
        "row_crossings": crossings,
        "feature__row_angle_vs_principal": feature,
    }


def _field(field_id: str, bin_values, *, feature_shift: float = 0.0, feature_missing: bool = False):
    result = []
    for offset, values in zip(OFFSETS, bin_values, strict=True):
        assert len(values) == 4
        for (spacing, vehicle), front_size in zip(
            ((spacing, vehicle) for spacing in SPACINGS for vehicle in VEHICLES),
            values,
            strict=True,
        ):
            result.append(OffsetFrontInstance(
                field_id=field_id,
                instance_id=f"{field_id}:principal_axis:{offset}:{spacing}:vehicle:{vehicle}",
                vehicle_index=vehicle,
                offset_rad=offset,
                spacing_m=spacing,
                row_angle_vs_principal=(None if feature_missing else offset + feature_shift),
                front_size=front_size,
            ))
    return tuple(result)


def _estimate(*fields):
    instances = tuple(instance for field in fields for instance in field)
    field_ids = tuple(sorted({instance.field_id for instance in instances}))
    return field_effects(
        instances,
        expected_offsets_rad=OFFSETS,
        expected_spacings_m=SPACINGS,
        expected_vehicle_indices=VEHICLES,
        expected_field_ids=field_ids,
    )


def test_instance_front_allows_null_failure_features_and_uses_recorded_field_id():
    rows = [
        _raw_row("region:a", "a", (1.0, 2.0, 3.0), feature=0.125),
        _raw_row(
            "region:a",
            "b",
            (None, None, None),
            feature=None,
            raw="not_applicable",
            reason="unsupported",
        ),
    ]
    instance = build_offset_front_instance(rows, ("a", "b"))
    assert instance.field_id == "region:a"
    assert instance.offset_rad == 0.0
    assert instance.row_angle_vs_principal == 0.125
    assert instance.front_size == 1

    bad = [dict(row, field_id="different") for row in rows]
    with pytest.raises(ValueError, match="field"):
        build_offset_front_instance(bad, ("a", "b"))


def test_zero_ok_instance_may_have_no_feature_but_defined_front_may_not():
    zero_rows = [
        _raw_row("a", config, (None, None, None), feature=None, raw="not_applicable")
        for config in ("a", "b")
    ]
    zero = build_offset_front_instance(zero_rows, ("a", "b"))
    assert zero.front_size is None
    assert zero.row_angle_vs_principal is None

    defined_rows = [
        _raw_row("a", "a", (1.0, 2.0, 3.0), feature=None),
        _raw_row("a", "b", (2.0, 3.0, 4.0), feature=None),
    ]
    with pytest.raises(ValueError, match="有定义前沿"):
        build_offset_front_instance(defined_rows, ("a", "b"))

    conflict = [
        _raw_row("a", "a", (1.0, 2.0, 3.0), feature=0.1),
        _raw_row("a", "b", (2.0, 3.0, 4.0), feature=0.2),
    ]
    with pytest.raises(ValueError, match="不一致"):
        build_offset_front_instance(conflict, ("a", "b"))


def test_field_effects_enforce_design_and_report_3_4_5_bins_constant_zero_and_sensitivity():
    increasing = _field("a", tuple(([value] * 3 + [None]) for value in (1, 2, 3, 4, 5)), feature_shift=0.01)
    constant = _field("b", tuple(([2] * 4) for _ in OFFSETS), feature_shift=0.02)
    three_decreasing = _field(
        "c",
        ((3, 3, None, None), (2, 2, None, None), (1, 1, None, None), (None,) * 4, (None,) * 4),
        feature_shift=0.03,
    )
    four_increasing = _field(
        "d",
        ((1,) * 4, (2,) * 4, (3,) * 4, (4,) * 4, (None,) * 4),
        feature_shift=0.04,
    )
    only_two = _field(
        "e",
        ((1,) * 4, (2,) * 4, (None,) * 4, (None,) * 4, (None,) * 4),
        feature_shift=0.05,
    )
    zero = _field("z", ((None,) * 4,) * 5, feature_missing=True)
    estimates = _estimate(increasing, constant, three_decreasing, four_increasing, only_two, zero)
    by_field = {item.field_id: item for item in estimates}

    assert by_field["a"].offset_bins[0].n_defined_front_instances == 3
    assert by_field["a"].offset_bins[0].median_front_size == 1.0
    assert by_field["a"].spearman_rho == pytest.approx(1.0)
    assert by_field["b"].constant_response is True
    assert by_field["b"].spearman_rho == 0.0
    assert by_field["c"].n_defined_offset_bins == 3
    assert by_field["c"].spearman_rho == pytest.approx(-1.0)
    assert by_field["e"].spearman_rho is None
    assert by_field["z"].median_row_angle_vs_principal is None

    result = analyze_h2(estimates)
    assert result["n_analyzable_fields"] == 4
    assert result["n_fewer_than_3_defined_offset_bins"] == 2
    assert (result["n_3_bins"], result["n_4_bins"], result["n_5_bins"]) == (1, 1, 2)
    assert result["n_constant_response_fields"] == 1
    assert result["n_zero_ok_fields"] == 1
    assert result["wilcoxon"]["zero_method"] == "pratt"
    assert result["wilcoxon"]["n"] == 4
    assert result["wilcoxon"]["n_zero_differences"] == 1
    assert result["full_5_bin_sensitivity"]["n_fields"] == 2
    assert result["full_5_bin_sensitivity"]["status"] == "secondary_sensitivity__not_in_holm_family"
    assert result["deprecated_cross_field_descriptive"]["status"] == "descriptive_only__not_a_confirmatory_test"
    assert "no cross-field explanatory interpretation" in result["deprecated_cross_field_descriptive"]["interpretation"]
    assert result["multiplicity"]["exact_holm_adjusted_p"] is None
    assert result["multiplicity"]["exact_holm_status"] == "pending_H3_pvalue_for_final_ordering"


def test_field_effects_reject_missing_or_duplicate_frozen_design_cells():
    complete = _field("a", tuple(([1] * 4) for _ in OFFSETS))
    with pytest.raises(ValueError, match="设计矩阵不完整"):
        _estimate(complete[:-1])
    with pytest.raises(ValueError, match="重复设计单元"):
        _estimate(complete + (replace(complete[0], instance_id="different-instance"),))
    with pytest.raises(ValueError, match="5 个"):
        field_effects(
            complete,
            expected_offsets_rad=OFFSETS[:-1],
            expected_spacings_m=SPACINGS,
        )


def test_all_constant_responses_are_included_as_zero_not_dropped():
    estimates = _estimate(_field("a", tuple(([2] * 4) for _ in OFFSETS)))
    result = analyze_h2(estimates)
    assert result["n_analyzable_fields"] == 1
    assert result["n_constant_response_fields"] == 1
    assert result["primary_rho_distribution"]["median"] == 0.0
    assert result["wilcoxon"]["pvalue"] == 1.0
    assert result["wilcoxon"]["zero_method"] == "pratt"
    assert result["wilcoxon"]["n"] == 1
    assert result["wilcoxon"]["n_nonzero_differences"] == 0


def _h1_document(estimates):
    return {
        "hypothesis": "H1",
        "analysis": {
            "fields": [
                {
                    "field_id": item.field_id,
                    "n_instances": item.n_instances,
                    "n_defined_front_instances": item.n_defined_front_instances,
                    "median_defined_front_size": item.median_defined_front_size,
                }
                for item in estimates
            ]
        },
    }


def test_h1_field_reconciliation_detects_front_drift():
    estimates = _estimate(_field("a", tuple(([2] * 4) for _ in OFFSETS)))
    document = _h1_document(estimates)
    _validate_h1_field_reconciliation(document, estimates)
    document["analysis"]["fields"][0]["median_defined_front_size"] = 99.0
    with pytest.raises(ValueError, match="前沿.*漂移"):
        _validate_h1_field_reconciliation(document, estimates)


def test_h1_predecessor_sha_tamper_is_rejected(tmp_path: Path):
    h1_result = tmp_path / "h1_result.json"
    h1_result.write_text(json.dumps({"hypothesis": "H1"}) + "\n", encoding="utf-8")
    import hashlib

    entries = []
    previous = "0" * 64
    for index, artifact in enumerate(("d1", "pool_census", "selection_protocol_v1", "selection_cv_result")):
        entry = artifact_chain_entry(index, previous, {"artifact": artifact})
        entries.append(entry)
        previous = entry["entry_hash"]
    payload = {
        "artifact": "h1_confirmatory_result",
        "result_file_sha256": hashlib.sha256(h1_result.read_bytes()).hexdigest(),
    }
    entries.append(artifact_chain_entry(4, previous, payload))
    assert _validate_predecessor(tuple(entries), h1_result)["hypothesis"] == "H1"

    h1_result.write_text(json.dumps({"hypothesis": "H1", "tampered": True}) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="index=4"):
        _validate_predecessor(tuple(entries), h1_result)
