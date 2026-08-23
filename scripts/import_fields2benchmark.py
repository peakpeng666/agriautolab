#!/usr/bin/env python3
"""把 Fields2Benchmark wkt.zip 导入许可感知的 AgriAutoLab 语料。"""

from __future__ import annotations

import argparse
import tempfile
import zipfile
from pathlib import Path

from shapely.geometry import Polygon

from agriautolab.datasets.fields2benchmark import (
    export_corpus, load_fields2benchmark_wkt_zip, load_fields2benchmark_wkt_zip_with_quarantine,
)


def _self_check() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        archive = root / "wkt.zip"
        with zipfile.ZipFile(archive, "w") as handle:
            for name in ("NL_demo", "EE_demo", "LT_demo"):
                handle.writestr(f"{name}.wkt", Polygon([(0, 0), (10, 0), (10, 5), (0, 5), (0, 0)]).wkt)
        records = load_fields2benchmark_wkt_zip(archive)
        manifest = export_corpus(records, path=root / "out",
                                 allow_analysis=True, allow_redistribution=True)
        assert manifest.n_input == 3 and manifest.n_exported == 2
        assert manifest.filtered_non_commercial_ids == ("LT_demo",)
    print("self-check: ok")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wkt-zip", type=Path)
    parser.add_argument("--output", type=Path)
    # 「用」与「发」拆成两个开关，都无默认值。
    # 许可 -> 用途的映射是待人裁定的法律解读，见 docs/refs/licenses/fields2benchmark.md。
    parser.add_argument("--allow-analysis", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--allow-redistribution", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--strict", action="store_true",
                        help="任何地块被隔离（几何不合法）都视为错误退出；审计模式")
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    if args.self_check:
        _self_check()
        return
    if (args.wkt_zip is None or args.output is None
            or args.allow_analysis is None or args.allow_redistribution is None):
        parser.error("正式导入必须显式给 --wkt-zip、--output、"
                     "--allow-analysis/--no-allow-analysis 与 "
                     "--allow-redistribution/--no-allow-redistribution")
    records, quarantined = load_fields2benchmark_wkt_zip_with_quarantine(args.wkt_zip)
    if args.strict and quarantined:
        raise SystemExit("strict 模式：以下地块因几何不合法被隔离："
                         + ", ".join(item.field_id for item in quarantined))
    manifest = export_corpus(
        records, path=args.output,
        allow_analysis=args.allow_analysis, allow_redistribution=args.allow_redistribution,
        quarantined=quarantined,
    )
    if quarantined:
        print(f"已隔离 {len(quarantined)} 个几何不合法地块（剔除未修复，已入 manifest）：")
        for item in quarantined:
            print(f"  {item.field_id}: {item.reason}")
    print(manifest)


if __name__ == "__main__":
    main()
