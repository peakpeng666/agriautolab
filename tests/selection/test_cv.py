from __future__ import annotations

import json
from pathlib import Path

import pytest

from agriautolab.evidence.ledger import verify_artifact_chain
from agriautolab.selection.cv import (
    CV_ASSIGNMENT_ALGORITHM,
    CV_FOLDS,
    CV_SEED,
    CvAssignmentEvidence,
    assign_grouped_folds,
    build_cv_assignment_evidence,
    field_ids_from_manifest,
    seal_cv_assignment_in_block_d_ledger,
    write_cv_assignment,
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


def test_field_universe_comes_from_result_independent_manifest_licenses() -> None:
    manifest = {
        "licenses": {"field_a": "cc0", "field_b": "cc0"},
        # field_b 模拟零有效池/无摘要田：它不在 result-derived 映射里也不能被 D1 丢掉。
        "effective_pool_size_by_instance": {
            "field_a:principal_axis:0:0.75:vehicle:0": 1,
        },
    }
    assert field_ids_from_manifest(manifest) == ("field_a", "field_b")


def _fixture_sources(tmp_path: Path) -> tuple[Path, Path]:
    manifest_path = tmp_path / "manifest.json"
    holdout_path = tmp_path / "holdout.json"
    manifest_path.write_text(json.dumps({
        "corpus_hash": "a" * 64,
        "licenses": {
            "field_a": "cc0", "field_b": "cc0", "field_c": "cc0", "field_d": "cc0",
        },
        "effective_pool_size_by_instance": {
            "field_a:principal_axis:0:0.75:vehicle:0": 1,
            # field_b 故意不出现：holdout 身份不能依赖有效池摘要。
            "field_c:principal_axis:0:0.75:vehicle:0": 2,
            "field_d:principal_axis:0:0.75:vehicle:0": 3,
        },
    }), encoding="utf-8")
    holdout_path.write_text(json.dumps({
        "field_ids": ["field_b"],
        "seal_hash": "b" * 64,
    }), encoding="utf-8")
    return manifest_path, holdout_path


def test_build_evidence_excludes_holdout_and_binds_source_files(tmp_path: Path) -> None:
    manifest_path, holdout_path = _fixture_sources(tmp_path)
    evidence = build_cv_assignment_evidence(manifest_path, holdout_path, n_folds=3, seed=7)
    assert evidence.n_all_fields == 4
    assert evidence.n_holdout_fields == 1
    assert evidence.n_training_fields == 3
    assert {item.field_id for item in evidence.assignments} == {"field_a", "field_c", "field_d"}
    assert "field_b" not in {item.field_id for item in evidence.assignments}
    assert evidence.fold_sizes == {"1": 1, "2": 1, "3": 1}

    roundtrip = CvAssignmentEvidence.model_validate_json(evidence.model_dump_json())
    assert roundtrip == evidence


def test_cv_assignment_can_be_sealed_as_idempotent_block_d_genesis(tmp_path: Path) -> None:
    manifest_path, holdout_path = _fixture_sources(tmp_path)
    evidence = build_cv_assignment_evidence(manifest_path, holdout_path, n_folds=3, seed=7)
    assignment_path = tmp_path / "cv_assignment.json"
    ledger_path = tmp_path / "block_d_ledger.jsonl"
    write_cv_assignment(evidence, assignment_path)

    first = seal_cv_assignment_in_block_d_ledger(evidence, assignment_path, ledger_path)
    replay = seal_cv_assignment_in_block_d_ledger(evidence, assignment_path, ledger_path)
    assert replay == first
    entries = tuple(json.loads(line) for line in ledger_path.read_text(encoding="utf-8").splitlines())
    assert len(entries) == 1
    assert entries[0]["payload"]["assignment_hash"] == evidence.assignment_hash
    verify_artifact_chain(entries)

    assignment_path.write_text(assignment_path.read_text(encoding="utf-8") + " ", encoding="utf-8")
    with pytest.raises(ValueError, match="genesis"):
        seal_cv_assignment_in_block_d_ledger(evidence, assignment_path, ledger_path)


def test_committed_v7_cv_assignment_exactly_regenerates() -> None:
    root = Path(__file__).resolve().parents[2]
    expected_path = root / "evidence" / "v7" / "cv_assignment.json"
    expected = CvAssignmentEvidence.model_validate_json(expected_path.read_text(encoding="utf-8"))
    regenerated = build_cv_assignment_evidence(
        root / "evidence" / "v7" / "manifest.json",
        root / "evidence" / "v7" / "holdout_seal.json",
    )
    assert regenerated == expected


def test_d1_frozen_constants_match_preregistration() -> None:
    assert CV_SEED == 20260822
    assert CV_FOLDS == 10
    assert CV_ASSIGNMENT_ALGORITHM == "sha256-seeded-round-robin-v1"
