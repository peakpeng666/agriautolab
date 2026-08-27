"""真实数据接入：许可证、CRS、Fields2Benchmark WKT 与 TSPLIB/CVRPLIB 标准实例。

TSPLIB 入口**刻意不在这里 re-export**：`fields2benchmark` 模块级依赖 pyproj/shapely，
而 TSPLIB 解析只依赖 `contracts`。保持
`from agriautolab.datasets.tsplib import load_tsplib_tsp` 零重依赖，
标准实例接入才能在没有地理栈的环境里单独使用。
"""

from .fields2benchmark import (
    DatasetLicense,
    DatasetLicenseError,
    ExportManifest,
    FieldRecord,
    export_corpus,
    QuarantinedField,
    load_fields2benchmark_wkt_zip,
    load_fields2benchmark_wkt_zip_with_quarantine,
    load_exported_corpus,
    to_metric_crs,
)

__all__ = [
    "DatasetLicense",
    "DatasetLicenseError",
    "ExportManifest",
    "FieldRecord",
    "export_corpus",
    "QuarantinedField",
    "load_fields2benchmark_wkt_zip",
    "load_fields2benchmark_wkt_zip_with_quarantine",
    "load_exported_corpus",
    "to_metric_crs",
]
