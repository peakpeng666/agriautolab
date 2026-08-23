#!/usr/bin/env python3
"""从冻结 v7 manifest + holdout seal 生成 Block D 的 field-grouped CV 折表。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from agriautolab.selection.cv import CV_FOLDS, CV_SEED, build_cv_assignment_evidence, write_cv_assignment


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--holdout", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--folds", type=int, default=CV_FOLDS)
    parser.add_argument("--seed", type=int, default=CV_SEED)
    parser.add_argument("--print-json", action="store_true", help="审计/CI 用：把完整规范 JSON 打到 stdout")
    args = parser.parse_args()

    evidence = build_cv_assignment_evidence(
        args.manifest,
        args.holdout,
        n_folds=args.folds,
        seed=args.seed,
    )
    write_cv_assignment(evidence, args.output)
    print(
        "cv assignment: "
        f"all={evidence.n_all_fields}, holdout={evidence.n_holdout_fields}, "
        f"train={evidence.n_training_fields}, folds={evidence.fold_sizes}, "
        f"assignment_hash={evidence.assignment_hash}, spec_hash={evidence.spec_hash}"
    )
    if args.print_json:
        print("---BEGIN-CV-ASSIGNMENT-JSON---")
        print(json.dumps(evidence.model_dump(mode="json"), ensure_ascii=False, indent=2, sort_keys=True))
        print("---END-CV-ASSIGNMENT-JSON---")


if __name__ == "__main__":
    main()
