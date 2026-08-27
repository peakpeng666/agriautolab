"""derived_status：分析层的唯一状态真相，由 failure_reason 派生（v7 复核确立）。

runstatus 是**运行时**的分类决策，含规则性归并（如零地头 carve：
no_headland 下 CONSTRAINT_VIOLATION 归 not_applicable——那是「算法族-地形
配对必然」的裁决，不是「没跑过」）。failure_reason 是**验证器/算法的原始
拒绝事实**。两者冲突时以更细的 failure_reason 为准：同一事实只能有一个
真相入口，聚合器与推荐器一律消费 derived_status，不许直读 runstatus 分叉。

已知分歧（v7 实测）：2 020 行 runstatus=not_applicable 而
failure_reason=validator_rejected:outside_area——零地头+RS 槽 B。
差异逐类计数随 manifest 落盘（runstatus_vs_derived_diff_counts）。
"""

from __future__ import annotations

# 与 runner._VALIDATOR_REJECTION_CLASSES 同一词表、两处声明：
# 测试钉住二者相等（词表漂移当场暴露），runner 侧另有对 validator 源码的
# 结构性核对，这里复用同一份封闭词典保证派生不会发明不存在的类。
_VALIDATOR_REJECTION_CLASSES = frozenset({
    "empty_path", "discontinuous_endpoints", "collision", "curvature_limit",
    "reverse_without_gear", "outside_area", "forbidden_crossing",
    "coverage_threshold", "nonfinite_metric",
})

DERIVED_STATUS_DEFINITION = (
    "validator 拒绝事实优先于运行时归并：failure_reason 以 "
    "validator_rejected:<class> 开头时，derived_status=<class>（未知类当场抛错）；"
    "否则 derived_status=runstatus（ok/crash/timeout/memout/invalid_input 与 "
    "算法-机具配对、塌缩等 not_applicable 的 failure_reason 是自由文本，无更细真相）。"
    "聚合器与推荐器一律消费本列；runstatus 仅作运行溯源。"
)


def derive_status(runstatus: str, failure_reason: str | None) -> str:
    """validator 事实 > 运行时状态；未知拒绝类响亮失败，不落任何兜底。"""
    reason = failure_reason or ""
    if reason.startswith("validator_rejected:"):
        klass = reason.split(":", 1)[1]
        if klass not in _VALIDATOR_REJECTION_CLASSES:
            raise ValueError(
                f"未知的 validator 拒绝原因 {klass!r}：请先把它加进 "
                "_VALIDATOR_REJECTION_CLASSES（与 runner 侧同步），不许落进任何兜底桶"
            )
        return klass
    return runstatus


def status_diff_counts(rows) -> dict[str, int]:
    """逐类计数 runstatus 与 derived_status 的分歧（空 dict = 无分歧）。

    键形如 "not_applicable->outside_area"：跑了、被验证器拒了，
    但被运行时规则归并成了 not_applicable 的行——读语料的人必须能看见。
    """
    diffs: dict[str, int] = {}
    for row in rows:
        raw = str(row["runstatus"])
        derived = derive_status(raw, row.get("failure_reason"))
        if derived != raw:
            key = f"{raw}->{derived}"
            diffs[key] = diffs.get(key, 0) + 1
    return diffs
