#!/usr/bin/env python3
"""从冻结 dataset-split manifest + holdout partition 生成 field-grouped CV 折表。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from agriautolab.selection.cv import (
    CV_FOLDS,
    CV_SEED,
    build_cv_assignment_evidence,
    register_cv_assignment,
    write_cv_assignment,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--holdout", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, help="可选：把折表封为基准结果账本 genesis")
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
    if args.ledger is not None and args.output.exists():
        # 已封存重跑：先在临时位置渲染，与封存哈希不一致时覆盖前拒绝
        from agriautolab.pipeline import jsonl_log

        if jsonl_log.read_sealed_sha256(args.ledger, "cv_assignment", "cv_assignment_file_sha256") is not None:
            tmp = args.output.with_name(args.output.name + ".tmp")
            write_cv_assignment(evidence, tmp)
            jsonl_log.replace_unless_sealed(tmp, args.output, args.ledger, "cv_assignment", "cv_assignment_file_sha256")
        else:
            write_cv_assignment(evidence, args.output)
    else:
        write_cv_assignment(evidence, args.output)
    ledger_entry = None
    if args.ledger is not None:
        ledger_entry = register_cv_assignment(evidence, args.output, args.ledger)
    print(
        "cv assignment: "
        f"all={evidence.n_all_fields}, holdout={evidence.n_holdout_fields}, "
        f"train={evidence.n_training_fields}, folds={evidence.fold_sizes}, "
        f"assignment_hash={evidence.assignment_hash}, spec_hash={evidence.spec_hash}"
    )
    if ledger_entry is not None:
        print(f"block-d ledger genesis={ledger_entry['entry_hash']}")
    if args.print_json:
        print("---BEGIN-CV-ASSIGNMENT-JSON---")
        print(json.dumps(evidence.model_dump(mode="json"), ensure_ascii=False, indent=2, sort_keys=True))
        print("---END-CV-ASSIGNMENT-JSON---")


if __name__ == "__main__":
    main()
