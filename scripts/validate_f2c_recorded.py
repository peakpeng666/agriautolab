#!/usr/bin/env python3
"""离线 F2C CSV 的自比交叉验证与 schema 冒烟检查。"""

from __future__ import annotations

import argparse
import csv
import tempfile
from pathlib import Path

from agriautolab.cross_validation import F2CRequest, RecordedCsvAdapter, compare_results


def _run(path: Path) -> None:
    adapter = RecordedCsvAdapter(path)
    with path.open(newline="", encoding="utf-8") as handle:
        request_ids = [row["request_id"] for row in csv.DictReader(handle)]
    rows = [adapter.run(F2CRequest(item, "POLYGON EMPTY", 1, 1, 1, 1, 0, "EPSG:0", "boustrophedon")) for item in request_ids]
    reports = compare_results(rows, rows)
    for report in reports:
        print(report)


def _self_check() -> None:
    with tempfile.TemporaryDirectory() as temp:
        path = Path(temp) / "recorded.csv"
        path.write_text(
            "request_id,path_length,swath_count,swath_length_sum,main_field_area\n"
            "demo,10,2,8,50\n",
            encoding="utf-8",
        )
        _run(path)
    print("self-check: ok")


def _compare(ours_csv: Path, reference_csv: Path) -> None:
    """真正的对账模式：我方复算 CSV vs F2C golden CSV，逐指标出报告。"""
    from agriautolab.cross_validation import compare_results
    from agriautolab.cross_validation.f2c import RecordedCsvAdapter

    ours = RecordedCsvAdapter(ours_csv)
    reference = RecordedCsvAdapter(reference_csv)
    with ours_csv.open(newline="", encoding="utf-8") as handle:
        ours_rows = [ours.run(F2CRequest(row["request_id"], "POLYGON EMPTY", 1, 1, 1, 1, 0, "EPSG:0", "boustrophedon"))
                     for row in csv.DictReader(handle)]
    with reference_csv.open(newline="", encoding="utf-8") as handle:
        reference_rows = [reference.run(F2CRequest(row["request_id"], "POLYGON EMPTY", 1, 1, 1, 1, 0, "EPSG:0", "boustrophedon"))
                          for row in csv.DictReader(handle)]
    for report in compare_results(ours_rows, reference_rows):
        print(report)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv", nargs="?", type=Path)
    parser.add_argument("--ours-csv", type=Path, help="对账模式：我方复算 CSV")
    parser.add_argument("--reference-csv", type=Path, help="对账模式：F2C golden CSV")
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    if args.ours_csv is not None and args.reference_csv is not None:
        _compare(args.ours_csv, args.reference_csv)
        return
    if args.self_check:
        _self_check()
        return
    if args.csv is None:
        parser.error("需要 recorded CSV")
    _run(args.csv)


if __name__ == "__main__":
    main()
