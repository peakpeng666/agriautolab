#!/usr/bin/env python3
"""用 Fields2Cover Python binding 录制 golden CSV（在装有 F2C 的 Linux/WSL 上运行）。

用法（WSL 内，仓库经 /mnt/d 挂载）：
  PYTHONPATH=/mnt/d/Peak/Desktop/URP/agriautolab-blockC/agriautolab-blockC/src \
  python3 scripts/record_f2c_golden.py --requests requests.json --output golden_f2c.csv

CSV schema 与 RecordedCsvAdapter 锁死的五列一致。逐请求打印结果行，
任何请求失败立即中止——缺行的 golden 文件比没有 golden 更坏。
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from agriautolab.validation import PythonBindingAdapter
from agriautolab.validation.f2c import F2CRequest

CSV_COLUMNS = ("request_id", "path_length", "swath_count", "swath_length_sum", "main_field_area", "working_crs")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--requests", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    adapter = PythonBindingAdapter()
    if not adapter.available():
        raise SystemExit("fields2cover 不可用：本脚本必须在装有 F2C Python binding 的环境运行")

    payload = json.loads(args.requests.read_text(encoding="utf-8"))
    rows = []
    for item in payload["requests"]:
        request = F2CRequest(
            request_id=item["request_id"],
            field_wkt=item["field_wkt"],
            robot_width_m=item["robot_width_m"],
            working_width_m=item["working_width_m"],
            min_turning_radius_m=item["min_turning_radius_m"],
            headland_width_m=item["headland_width_m"],
            swath_angle_rad=item["swath_angle_rad"],
            working_crs=item["working_crs"],
        )
        result = adapter.run(request)
        rows.append({
            "request_id": result.request_id,
            "path_length": result.path_length,
            "swath_count": result.swath_count,
            "swath_length_sum": result.swath_length_sum,
            "main_field_area": result.main_field_area,
            "working_crs": result.working_crs,
        })
        print(f"{result.request_id}: L={result.path_length:.3f} n={result.swath_count:.0f} "
              f"sum={result.swath_length_sum:.3f} area={result.main_field_area:.3f}")

    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"golden CSV: {len(rows)} 行 -> {args.output}")


if __name__ == "__main__":
    main()
