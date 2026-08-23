#!/usr/bin/env python3
"""离线 F2C CSV 的自比对账与 schema 冒烟检查。"""

from __future__ import annotations

import argparse
import csv
import tempfile
from pathlib import Path

from agriautolab.cross_validation import F2CRequest, RecordedCsvAdapter, compare_results


def _request(request_id: str) -> F2CRequest:
    return F2CRequest(request_id, "POLYGON EMPTY", 1, 1, 1, 1, 0, "EPSG:0", "boustrophedon")


def _run(path: Path) -> None:
    adapter = RecordedCsvAdapter(path)
    with path.open(newline="", encoding="utf-8") as handle:
        request_ids = [row["request_id"] for row in csv.DictReader(handle)]
    rows = [adapter.run(_request(request_id)) for request_id in request_ids]
    for report in compare_results(rows, rows):
        print(report)


def _self_check() -> None:
    """用冻结适配器的完整 13 列 CSV schema 做最小离线自检。"""
    with tempfile.TemporaryDirectory() as temp:
        path = Path(temp) / "recorded.csv"
        path.write_text(
            "request_id,path_length,swath_count,swath_length_sum,main_field_area,"
            "transit_entry_leg_m,transit_turn_total_m,transit_turn_count,transit_inter_cell_m,"
            "transit_exit_leg_m,transit_other_m,working_crs,route_algorithm\n"
            "demo,10,2,8,50,0,2,1,0,0,0,EPSG:0,boustrophedon\n",
            encoding="utf-8",
        )
        _run(path)
    print("self-check: ok")


def _compare(ours_csv: Path, reference_csv: Path) -> None:
    """我方复算 CSV 与 F2C golden CSV 逐指标对账。"""
    ours = RecordedCsvAdapter(ours_csv)
    reference = RecordedCsvAdapter(reference_csv)
    with ours_csv.open(newline="", encoding="utf-8") as handle:
        ours_rows = [ours.run(_request(row["request_id"])) for row in csv.DictReader(handle)]
    with reference_csv.open(newline="", encoding="utf-8") as handle:
        reference_rows = [reference.run(_request(row["request_id"])) for row in csv.DictReader(handle)]
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
