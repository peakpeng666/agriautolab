"""Block D 选择层：从冻结实验身份开始，而不是从模型实现开始。"""

from agriautolab.selection.cv import (
    CV_ASSIGNMENT_ALGORITHM,
    CV_FOLDS,
    CV_SEED,
    CvAssignmentEvidence,
    CvFoldRecord,
    assign_grouped_folds,
    build_cv_assignment_evidence,
    field_ids_from_manifest,
    seal_cv_assignment_in_block_d_ledger,
    write_cv_assignment,
)

__all__ = [
    "CV_ASSIGNMENT_ALGORITHM",
    "CV_FOLDS",
    "CV_SEED",
    "CvAssignmentEvidence",
    "CvFoldRecord",
    "assign_grouped_folds",
    "build_cv_assignment_evidence",
    "field_ids_from_manifest",
    "seal_cv_assignment_in_block_d_ledger",
    "write_cv_assignment",
]
