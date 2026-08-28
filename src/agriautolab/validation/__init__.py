"""可行性的唯一裁定者是独立校验，不是规划器自报。

包出口同时承载 F2C/F2B 交叉验证入口（原 cross_validation 包并入本包）。
"""

from agriautolab.validation.validator import PathValidator
from agriautolab.validation.f2c import (
    F2CRequest,
    F2CResult,
    PythonBindingAdapter,
    RecordedCsvAdapter,
    SubprocessAdapter,
)
from agriautolab.validation.report import CrossValidationReport, compare_results

__all__ = [
    "PathValidator",
    "F2CRequest",
    "F2CResult",
    "PythonBindingAdapter",
    "RecordedCsvAdapter",
    "SubprocessAdapter",
    "CrossValidationReport",
    "compare_results",
]
