#!/usr/bin/env python3
"""正式 F2C 录制壳。**只依赖 python3.10 + fields2cover + shapely，不 import agriautolab。**

链路实现不在本文件里：它按文件路径加载
`src/agriautolab/validation/f2c_chain.py`（该模块刻意不 import 任何 agriautolab
内容、且只用 3.10 兼容语法），从而绕开包 `__init__` 的 3.11 语法。
于是「录制壳与 PythonBindingAdapter 等价」是**只有一份实现**，不是事后比对两份输出。

为什么不重建 binding、也不给仓库降级：F2C binding 绑在 WSL 的 python3.10，
两进程是既定架构（三适配器设计就是为它准备的），
不是需要消除的障碍。

输出两份：
  --output       golden CSV，schema 与 RecordedCsvAdapter 锁死的 13 列一致
  --route-output swath 访问顺序与几何（JSON），路线配对的身份证明用

任何请求失败立即中止——缺行的 golden 文件比没有 golden 更坏。
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import os
import sys

CSV_COLUMNS = (
    "request_id",
    "path_length",
    "swath_count",
    "swath_length_sum",
    "main_field_area",
    "transit_entry_leg_m",
    "transit_turn_total_m",
    "transit_turn_count",
    "transit_inter_cell_m",
    "transit_exit_leg_m",
    "transit_other_m",
    "working_crs",
    "route_algorithm",
)

_REQUIRED_REQUEST_KEYS = (
    "request_id", "field_wkt", "robot_width_m", "working_width_m",
    "min_turning_radius_m", "headland_width_m", "swath_angle_rad",
    "working_crs", "route_algorithm",
)


def load_chain(repo_root):
    """按文件路径加载 f2c_chain，绕开 agriautolab 包 __init__ 的 3.11 语法。"""
    path = os.path.join(repo_root, "src", "agriautolab", "validation", "f2c_chain.py")
    if not os.path.isfile(path):
        raise SystemExit("找不到链路模块：%s（--repo-root 指对了吗）" % path)
    spec = importlib.util.spec_from_file_location("f2c_chain", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["f2c_chain"] = module
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--requests", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--route-output", required=True)
    parser.add_argument(
        "--repo-root",
        default=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        help="仓库根目录；默认按本脚本位置推断",
    )
    args = parser.parse_args()

    try:
        import fields2cover as f2c
    except ImportError as error:
        raise SystemExit("fields2cover 不可用：本脚本必须在装有 F2C binding 的环境运行（%s）" % error)
    import shapely

    chain = load_chain(args.repo_root)
    with open(args.requests, encoding="utf-8") as handle:
        payload = json.load(handle)

    rows = []
    identities = []
    for item in payload["requests"]:
        missing = [key for key in _REQUIRED_REQUEST_KEYS if key not in item]
        if missing:
            raise SystemExit("请求 %s 缺字段：%s" % (item.get("request_id", "?"), missing))
        polygon = shapely.from_wkt(item["field_wkt"])
        if polygon.geom_type != "Polygon":
            raise SystemExit("录制壳只接受单 Polygon WKT：%s" % item["request_id"])
        params = {key: item[key] for key in (
            "robot_width_m", "working_width_m", "min_turning_radius_m",
            "headland_width_m", "swath_angle_rad", "route_algorithm",
        )}
        result = chain.run_chain(f2c, polygon, params)
        row = {"request_id": item["request_id"]}
        row.update(result["scalars"])
        row["working_crs"] = item["working_crs"]
        row["route_algorithm"] = item["route_algorithm"]
        rows.append(row)
        identity = {"request_id": item["request_id"]}
        identity.update(result["route_identity"])
        identities.append(identity)
        print(
            "%s: L=%.4f n=%.0f sum=%.4f area=%.4f turn_total=%.4f n_turn=%.0f "
            "entry=%.4f exit=%.4f crs=%s route=%s" % (
                row["request_id"], row["path_length"], row["swath_count"],
                row["swath_length_sum"], row["main_field_area"],
                row["transit_turn_total_m"], row["transit_turn_count"],
                row["transit_entry_leg_m"], row["transit_exit_leg_m"],
                row["working_crs"], row["route_algorithm"],
            )
        )

    with open(args.output, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    with open(args.route_output, "w", encoding="utf-8") as handle:
        json.dump({"identities": identities}, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print("golden CSV: %d 行 -> %s" % (len(rows), args.output))
    print("route identity: %d 条 -> %s" % (len(identities), args.route_output))


if __name__ == "__main__":
    main()
