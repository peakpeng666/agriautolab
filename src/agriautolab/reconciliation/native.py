"""native：我方（native pipeline）侧的对账求值，规范 API。

实现零复制：直接转发 cross_validation.ours（legacy 模块继续可用，
证据与测试引用它的地方不受影响）。
"""

from __future__ import annotations

from agriautolab.cross_validation.ours import compute_ours, compute_ours_detail

__all__ = ["evaluate_native_pipeline", "evaluate_native_pipeline_detail", "compute_ours", "compute_ours_detail"]

# 规范名 = 动词开头表达动作（docs/NAMING.md）；legacy 名保留转发。
evaluate_native_pipeline = compute_ours
evaluate_native_pipeline_detail = compute_ours_detail
