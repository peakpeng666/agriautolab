"""benchmark：语料基准运行时的规范入口（corpus 的规范名）。

物理实现留在 agriautolab.corpus（runner / protocol / aggregate /
derived_status），本包只做规范名转发，单一真相源不变。

新代码：

    from agriautolab.benchmark import CorpusRunner, summarize_pareto, derive_status
"""

from agriautolab.corpus.aggregate import CorpusParetoSummary, ecdf, summarize_pareto
from agriautolab.corpus.derived_status import (
    DERIVED_STATUS_DEFINITION,
    derive_status,
    status_diff_counts,
)
from agriautolab.corpus.protocol import CorpusProtocol
from agriautolab.corpus.runner import CodeVersion, CorpusRunner, discover_code_version

__all__ = [
    "CorpusParetoSummary",
    "ecdf",
    "summarize_pareto",
    "DERIVED_STATUS_DEFINITION",
    "derive_status",
    "status_diff_counts",
    "CorpusProtocol",
    "CodeVersion",
    "CorpusRunner",
    "discover_code_version",
]
