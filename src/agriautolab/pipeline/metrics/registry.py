"""不可比或对采样密度敏感的指标在注册时就被拒，进不了实验。"""

from __future__ import annotations

from agriautolab.contracts.enums import (
    ComparabilityScope,
    CoverageStage,
    CoverageTarget,
    MetricRole,
    OptimizationDirection,
    ProblemKind,
    ScaleBehavior,
)
from agriautolab.contracts.errors import MetricRegistrationError
from agriautolab.pipeline.metrics.spec import MetricSpec


DISABLED_METRICS: dict[str, str] = {
    "turn_count": "折线顶点计数随分段粒度变化，不代表物理转弯次数；改用 total_heading_change",
    "solution_smoothness": "OMPL 形式对航点密度高度敏感，不具实现不变性",
    "mean_clearance": "航点算术平均会给密集采样区额外权重；改用按弧长采样的 median_clearance",
    "normalized_curvature": "已知实现含固定 0.3 单位最小间距，缩放后不可比",
}

METRIC_REGISTRY: dict[str, MetricSpec] = {}


def register_metric(spec: MetricSpec) -> MetricSpec:
    if spec.metric_id in DISABLED_METRICS:
        raise MetricRegistrationError(f"{spec.metric_id} 已禁用：{DISABLED_METRICS[spec.metric_id]}")
    if spec.metric_id in METRIC_REGISTRY:
        raise MetricRegistrationError(f"重复指标：{spec.metric_id}")
    if spec.comparability_scope is not ComparabilityScope.IMPL_INVARIANT and not spec.notes.strip():
        raise MetricRegistrationError("非 IMPL_INVARIANT 指标必须说明可比性边界")
    if spec.aggregation_method not in {"arithmetic_mean", "geometric_mean", "median"}:
        raise MetricRegistrationError(f"不支持的聚合方法：{spec.aggregation_method}")
    METRIC_REGISTRY[spec.metric_id] = spec
    return spec


def _install_defaults() -> None:
    common = frozenset({ProblemKind.GRID_P2P_2D, ProblemKind.POLYGON_COVERAGE_2D})
    coverage = frozenset({ProblemKind.POLYGON_COVERAGE_2D})
    specs = (
        MetricSpec("path_length", "m", OptimizationDirection.MINIMIZE, ComparabilityScope.IMPL_INVARIANT,
                   ScaleBehavior.LINEAR, True, MetricRole.DIAGNOSTIC, common, CoverageStage.PATH,
                   description="欧氏折线弧长"),
        MetricSpec("total_heading_change", "1", OptimizationDirection.MINIMIZE, ComparabilityScope.IMPL_INVARIANT,
                   ScaleBehavior.INVARIANT, True, MetricRole.DIAGNOSTIC, common, CoverageStage.PATH,
                   description="相邻非零路径段之间的绝对航向变化总和"),
        MetricSpec("aol", "1", OptimizationDirection.MINIMIZE, ComparabilityScope.IMPL_INVARIANT,
                   ScaleBehavior.INVERSE_LINEAR, True, MetricRole.DIAGNOSTIC, common, CoverageStage.PATH,
                   description="总航向变化除以路径长度",
                   canonical_name="heading_change_per_meter"),
        MetricSpec("tortuosity", "1", OptimizationDirection.MINIMIZE, ComparabilityScope.IMPL_INVARIANT,
                   ScaleBehavior.INVARIANT, True, MetricRole.DIAGNOSTIC, common, CoverageStage.PATH,
                   description="路径长度与端点欧氏距离之比"),
        MetricSpec("cusp_count", "count", OptimizationDirection.MINIMIZE, ComparabilityScope.IMPL_INVARIANT,
                   ScaleBehavior.INVARIANT, True, MetricRole.DIAGNOSTIC, common, CoverageStage.PATH,
                   description="方向发生约 pi 翻转的尖点数量",
                   notes="与被禁用的 turn_count 形似而不同族：turn_count 数折线顶点，加密采样就会变；"
                         "尖点是运动学奇点（行进方向反号的那一点），把一段弧采成 3 段还是 30 段，"
                         "尖点位置和个数都不变，因此对分段粒度不敏感。"
                         "Reeds-Shepp 引入倒车后它才有非零取值，用于诊断「省下的长度是拿几次换挡换的」；"
                         "注册为 DIAGNOSTIC，不进主指标向量"),
        MetricSpec("coverage_ratio_field", "1", OptimizationDirection.MAXIMIZE, ComparabilityScope.IMPL_INVARIANT,
                   ScaleBehavior.INVARIANT, True, MetricRole.HARD_CONSTRAINT, coverage, CoverageStage.PATH,
                   description="扫掠并集在原始可作业区（地块扣除障碍）内的面积比例；硬门槛只认这一条"),
        MetricSpec("coverage_ratio_main", "1", OptimizationDirection.MAXIMIZE, ComparabilityScope.PROTOCOL_BOUND,
                   ScaleBehavior.INVARIANT, True, MetricRole.DIAGNOSTIC, coverage, CoverageStage.PATH,
                   protocol_parameters={"coverage_target": CoverageTarget.MAIN_FIELD.value},
                   description="扫掠并集在主田（扣除地头后）内的面积比例",
                   notes="分母随 headland 配置变化：100x50 田块幅宽 10，地头 2/6/12/18 米对应主田 "
                         "4416/3344/1976/896 m^2，四种配置该比值全是 1.0000，而对原田分别只有 "
                         "0.8832/0.6688/0.3952/0.1792。只能在 headland 配置完全相同的运行之间比较，"
                         "禁止用作硬门槛，禁止进入跨协议排名"),
        MetricSpec("overlap_ratio", "1", OptimizationDirection.MINIMIZE, ComparabilityScope.IMPL_INVARIANT,
                   ScaleBehavior.INVARIANT, True, MetricRole.PRIMARY, coverage, CoverageStage.PATH,
                   description="裁剪后各作业带面积和减并集面积，再除以作业域面积"),
        MetricSpec("nonwork_normalized", "1", OptimizationDirection.MINIMIZE, ComparabilityScope.IMPL_INVARIANT,
                   ScaleBehavior.INVARIANT, True, MetricRole.PRIMARY, coverage, CoverageStage.PATH,
                   description="非作业路径长度乘幅宽后除以作业域面积"),
        MetricSpec("outside_area", "m^2", OptimizationDirection.MINIMIZE, ComparabilityScope.IMPL_INVARIANT,
                   ScaleBehavior.QUADRATIC, True, MetricRole.HARD_CONSTRAINT, coverage, CoverageStage.PATH,
                   description="车体扫掠落在允许域之外的面积"),
        MetricSpec("collision_area", "m^2", OptimizationDirection.MINIMIZE, ComparabilityScope.IMPL_INVARIANT,
                   ScaleBehavior.QUADRATIC, True, MetricRole.HARD_CONSTRAINT, coverage, CoverageStage.PATH,
                   description="车体扫掠与障碍物交叠面积"),
        MetricSpec("L_R", "m", OptimizationDirection.MINIMIZE, ComparabilityScope.IMPL_INVARIANT,
                   ScaleBehavior.LINEAR, True, MetricRole.DIAGNOSTIC, coverage, CoverageStage.PATH,
                   description="覆盖路径总弧长"),
        MetricSpec("L_area", "1", OptimizationDirection.MINIMIZE, ComparabilityScope.IMPL_INVARIANT,
                   ScaleBehavior.INVARIANT, True, MetricRole.DIAGNOSTIC, coverage, CoverageStage.PATH,
                   description="L_R 乘工作幅宽后除以作业域面积",
                   canonical_name="normalized_path_length"),
        MetricSpec("eta_L", "1", OptimizationDirection.MINIMIZE, ComparabilityScope.IMPL_INVARIANT,
                   ScaleBehavior.INVARIANT, True, MetricRole.DIAGNOSTIC, coverage, CoverageStage.PATH,
                   description="非作业路径长度占总路径长度的比例",
                   canonical_name="nonwork_length_ratio"),
        MetricSpec("turning_overhead_ratio", "1", OptimizationDirection.MINIMIZE, ComparabilityScope.IMPL_INVARIANT,
                   ScaleBehavior.INVARIANT, True, MetricRole.DIAGNOSTIC, coverage, CoverageStage.PATH,
                   description="TURN 段长度占总路径长度的比例"),
        MetricSpec("transit_length", "m", OptimizationDirection.MINIMIZE, ComparabilityScope.IMPL_INVARIANT,
                   ScaleBehavior.LINEAR, True, MetricRole.DIAGNOSTIC, common, CoverageStage.PATH,
                   description="TRANSIT 段总长",
                   notes="Rank correlation with path_length ≈ 1.0 (transit=length−work); treated as diagnostic."
                         "而 work 约等于面积/幅宽、几乎不随配置变，两者共享同一自由度。"
                         "保留仅为诊断，不进主指标向量"),
        MetricSpec("headland_turn_count", "count", OptimizationDirection.MINIMIZE, ComparabilityScope.IMPL_INVARIANT,
                   ScaleBehavior.INVARIANT, True, MetricRole.DIAGNOSTIC, coverage, CoverageStage.PATH,
                   description="地头掉头次数：相邻作业段之间的转移次数",
                   notes="与禁用表里的 turn_count 是不同的量：turn_count 数折线顶点、对分段粒度敏感；"
                         "本指标只数被作业段夹住的非作业游程，与转移段被采样成几条折线无关。"
                         "禁用表未因此放宽，两者语义并存。"
                         "它是主目标向量的第二维，但角色保持 DIAGNOSTIC——"
                         "主向量的成员资格由 pareto.ObjectiveVector 声明，不占用注册表 PRIMARY 语义"),
        MetricSpec("row_crossings", "count", OptimizationDirection.MINIMIZE, ComparabilityScope.IMPL_INVARIANT,
                   ScaleBehavior.INVARIANT, True, MetricRole.DIAGNOSTIC, coverage, CoverageStage.PATH,
                   description="路径对作物行的穿行次数，按段端点解析计算",
                   canonical_name="row_crossing_equivalent",
                   notes="无行结构（row_structure=None）时恒为 0；作业段按直线端点计为精确值，"
                         "弧形转移段按弦投影计，是该口径的下界。行结构是目标空间里唯一与长度族"
                         "Orthogonal to path_length dimension (rank correlation ≈ −0.10)."
                         "它是主目标向量的第三维，角色同 headland_turn_count 保持 DIAGNOSTIC"),
        MetricSpec("swath_count", "count", OptimizationDirection.MINIMIZE, ComparabilityScope.IMPL_INVARIANT,
                   ScaleBehavior.INVARIANT, True, MetricRole.DIAGNOSTIC, coverage, CoverageStage.SWATH,
                   description="输出中作业 swath 的数量"),
        MetricSpec("headland_area_ratio", "1", OptimizationDirection.MINIMIZE, ComparabilityScope.IMPL_INVARIANT,
                   ScaleBehavior.INVARIANT, True, MetricRole.DIAGNOSTIC, coverage, CoverageStage.HEADLAND,
                   description="headland 面积占 cell 面积的比例"),
        MetricSpec("min_clearance", "m", OptimizationDirection.MAXIMIZE, ComparabilityScope.IMPL_INVARIANT,
                   ScaleBehavior.LINEAR, True, MetricRole.DIAGNOSTIC, common, CoverageStage.PATH,
                   description="连续路径几何到障碍物的最小欧氏距离"),
        MetricSpec("median_clearance", "m", OptimizationDirection.MAXIMIZE, ComparabilityScope.PROTOCOL_BOUND,
                   ScaleBehavior.LINEAR, True, MetricRole.DIAGNOSTIC, common, CoverageStage.PATH,
                   protocol_parameters={"clearance_sample_step_m": 0.25},
                   description="沿弧长密化采样点到障碍物的中位距离",
                   notes="采样步长属于 BenchmarkProtocol；缩放不变性测试必须同步缩放该步长"),
        MetricSpec("collision_checks", "count", OptimizationDirection.MINIMIZE, ComparabilityScope.IMPL_BOUND,
                   ScaleBehavior.UNDEFINED, False, MetricRole.DIAGNOSTIC, common, CoverageStage.PATH,
                   description="实现执行的碰撞检测次数",
                   notes="由未来 benchmark harness 计数；契约层禁止 benchmark runner，因此这里只声明契约"),
        MetricSpec("objective_evaluations", "count", OptimizationDirection.MINIMIZE, ComparabilityScope.IMPL_BOUND,
                   ScaleBehavior.UNDEFINED, False, MetricRole.DIAGNOSTIC, common, None,
                   description="搜索过程中目标函数求值次数",
                   notes="属于算法实现过程计数，不能由最终路径几何重建"),
        MetricSpec("runtime_ms", "s", OptimizationDirection.MINIMIZE, ComparabilityScope.PROTOCOL_BOUND,
                   ScaleBehavior.UNDEFINED, False, MetricRole.DIAGNOSTIC, common, None,
                   protocol_parameters={"clock": "monotonic"},
                   description="运行时长；ID 保留 runtime_ms，但规范值在证据层换算为 SI 秒",
                   notes="依赖硬件、系统负载和计时协议，禁止进入跨协议主排名",
                   canonical_name="runtime_s"),
    )
    for spec in specs:
        register_metric(spec)


def metric_by_canonical(canonical: str) -> MetricSpec:
    """按规范名反查（API/论文层入口）；证据层永远按 metric_id。"""
    for spec in METRIC_REGISTRY.values():
        if spec.canonical == canonical:
            return spec
    raise KeyError(f"未知规范名 {canonical!r}：规范名见 docs/NAMING.md 对照表")


def _check_canonical_uniqueness() -> None:
    seen: set[str] = set()
    for spec in METRIC_REGISTRY.values():
        if spec.canonical in seen:
            raise MetricRegistrationError(f"规范名重复：{spec.canonical}")
        seen.add(spec.canonical)


_install_defaults()


# 默认指标装完再查重（顺序反了就是对空表空跑）
_check_canonical_uniqueness()
