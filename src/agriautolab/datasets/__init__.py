"""真实数据接入：许可证、CRS 与 Fields2Benchmark WKT 入口。"""

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
