"""选择层：冻结身份、评估协议与偏好条件推荐器。"""

from agriautolab.selection.cv import (
    CV_ASSIGNMENT_ALGORITHM,
    CV_FOLDS,
    CV_SEED,
    CvAssignmentEvidence,
    CvFoldRecord,
    assign_grouped_folds,
    build_cv_assignment_evidence,
    field_ids_from_manifest,
    register_cv_assignment,
    write_cv_assignment,
)
from agriautolab.selection.evaluation import SelectionInstance, load_selection_instances, select_sbs
from agriautolab.selection.protocol import SELECTION_FEATURE_IDS, selection_protocol_hash, selection_protocol_payload
from agriautolab.selection.recommender import PreferenceConditionedRecommender

__all__ = [
    "CV_ASSIGNMENT_ALGORITHM",
    "CV_FOLDS",
    "CV_SEED",
    "CvAssignmentEvidence",
    "CvFoldRecord",
    "PreferenceConditionedRecommender",
    "SELECTION_FEATURE_IDS",
    "SelectionInstance",
    "assign_grouped_folds",
    "build_cv_assignment_evidence",
    "field_ids_from_manifest",
    "load_selection_instances",
    "register_cv_assignment",
    "select_sbs",
    "selection_protocol_hash",
    "selection_protocol_payload",
    "write_cv_assignment",
]
