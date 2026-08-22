"""Fields2Cover/F2B 交叉验证入口。"""

from .f2c import F2CRequest, F2CResult, PythonBindingAdapter, RecordedCsvAdapter, SubprocessAdapter
from .report import CrossValidationReport, compare_results

__all__ = [
    "F2CRequest", "F2CResult", "PythonBindingAdapter", "RecordedCsvAdapter", "SubprocessAdapter",
    "CrossValidationReport", "compare_results",
]
