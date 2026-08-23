from __future__ import annotations

import json
from pathlib import Path

import pytest

from agriautolab.selection.cv import (
    CV_ASSIGNMENT_ALGORITHM,
    CV_FOLDS,
    CV_SEED,
    CvAssignmentEvidence,
    assign_grouped_folds,
    build_cv_assignment_evidence,
)


def test_grouped_folds_are_deterministic_balanced_and_order_independent() -> None:
    fields = [f"field_{index:03d}" for index in range(165)]
    first = assign_grouped_folds(fields, n_folds=10, seed=20260822)
    second = assign_grouped_folds(list(reversed(fields)), n_folds=10, seed=20260822)

    assert first == second
    sizes = {fold: sum(item.fold == fold for item in first) for fold in range(1, 11)}
    assert sorted(sizes.values()) == [16, 16, 16, 16, 16, 17, 17, 17, 17, 17]


def test_seed_changes_assignment() -> None:
    fields = [f"field_{index:03d}" for index in range(40)]
    one = assign_grouped_folds(fields, n_folds=5, seed=1)
    two = assign_grouped_folds(fields, n_folds=5, seed=2)
    assert [(x.field_id, x.fold) for x in one] != [(x.field_id, x.fold) for x in two]


def test_invalid_group_inputs_fail_loudly() -> None:
    with pytest.raises(ValueError, match="互异"):
        assign_grouped_folds(["a", "a"], n_folds=2)
    with pytest.raises(ValueError, match="超过"):
        assign_grouped_folds(["a", "b"], n_folds=3)


def test_build_evidence_excludes_holdout_and_binds_source_files(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    holdout_path = tmp_path / "holdout.json"
    manifest_path.write_text(json.dumps({
        "corpus_hash": "a" * 64,
        "effective_pool_size_by_instance": {
            "field_a:principal_axis:0:0.75:vehicle:0": 1,
            "field_b:principal_axis:0:0.75:vehicle:0": 0,
            "field_c:principal_axis:0:0.75:vehicle:0": 2,
            "field_d:principal_axis:0:0.75:vehicle:0": 3,
        },
    }), encoding="utf-8")
    holdout_path.write_text(json.dumps({
        "field_ids": ["field_b"],
        "seal_hash": "b" * 64,
    }), encoding="utf-8")

    evidence = build_cv_assignment_evidence(manifest_path, holdout_path, n_folds=3, seed=7)
    assert evidence.n_all_fields == 4
    assert evidence.n_holdout_fields == 1
    assert evidence.n_training_fields == 3
    assert {item.field_id for item in evidence.assignments} == {"field_a", "field_c", "field_d"}
    assert "field_b" not in {item.field_id for item in evidence.assignments}
    assert evidence.fold_sizes == {"1": 1, "2": 1, "3": 1}

    roundtrip = CvAssignmentEvidence.model_validate_json(evidence.model_dump_json())
    assert roundtrip == evidence


def test_d1_frozen_constants_match_preregistration() -> None:
    assert CV_SEED == 20260822
    assert CV_FOLDS == 10
    assert CV_ASSIGNMENT_ALGORITHM == "sha256-seeded-round-robin-v1"
