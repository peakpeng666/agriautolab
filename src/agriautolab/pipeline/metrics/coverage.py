"""在一对由协议锁定、调用方无法自行替换的分母上计算覆盖率、重叠与非作业行程。"""

from __future__ import annotations

from dataclasses import dataclass, field

from shapely.geometry import GeometryCollection
from shapely.geometry.base import BaseGeometry

from agriautolab.contracts.artifacts import HeadlandArtifact, PathArtifact
from agriautolab.contracts.enums import CoverageTarget, PathSegmentKind
from agriautolab.contracts.errors import CoverageDenominatorError
from agriautolab.contracts.geometry import GeometryFrame
from agriautolab.contracts.problem import CoverageProblem
from agriautolab.geometry.footprint import QUAD_SEGS, sweep_piece
from agriautolab.geometry.hashing import geometry_hash
from agriautolab.geometry.robust import robust_union
from agriautolab.geometry.validate import (
    line_from_spec,
    polygon_from_spec,
    validate_obstacles_within_field,
)

# 只有 resolve_coverage_targets 持有这个令牌。它是模块私有对象，
# 任何绕开解析器直接构造 CoverageTargets 的代码都拿不到它。
_RESOLVED = object()


@dataclass(frozen=True)
class DenominatorProvenance:
    """分母的证据链：记下三个几何的 hash，事后才能对账两条覆盖率是不是同一把尺子量的。

    外部旧基线（gate.jsonl）在序列化时把 path 剥掉了，结果没有任何一个指标能被独立重算。
    分母是同一类东西：如果产物里不记分母，事后没人能判断两条覆盖率是不是同一把尺子量的。
    记了 hash，绕过令牌造出来的分母也会在对账时露出来。

    declared_headland_width_m 是「申报」：调用方给的标量，已在 resolve_coverage_targets
    里被逐 cell 重算对账（可证伪）。headland_ring_hash 是「硬事实」：实际被扣掉的那圈几何
    的哈希，调用方无法申报、无法伪造。两个都留着——一个可证伪，一个不可申报。
    """

    target_kind: CoverageTarget
    declared_headland_width_m: float | None
    original_field_hash: str
    main_field_hash: str
    selected_hash: str
    headland_ring_hash: str | None


@dataclass(frozen=True)
class CoverageTargets:
    """一次性算出的两个覆盖率分母，加上协议声明的那一个。

    存在的理由：分母曾经是 coverage_stats 的自由入参。100x50 田块、幅宽 10，
    只把地头从 2 米开到 18 米，对主田覆盖率四次都是 1.0000，对原田却从 0.8832 掉到 0.1792。
    地头生成本身就是被比较的五个阶段之一，各配置各用各的分母就等于没有比较。

    构造令牌（_token）是本类的第一层守卫，只允许 resolve_coverage_targets 持有。
    这道令牌是纪律，不是安全边界。Python 没有真正的私有，存心绕过永远绕得过去。
    它挡的是「顺手构造一个 CoverageTargets」——那是分母漂移实际发生的方式。
    存心绕过由 G-1.3 的证据链兜底：产物里记了分母的 hash，事后可以复算对账。
    """

    original_field: BaseGeometry
    main_field: BaseGeometry
    selected: BaseGeometry
    target_kind: CoverageTarget
    headland_width_m: float | None
    frame: GeometryFrame
    _token: object = None
    provenance: DenominatorProvenance = field(init=False)

    def __post_init__(self) -> None:
        if self._token is not _RESOLVED:
            raise CoverageDenominatorError(
                "CoverageTargets 只能由 resolve_coverage_targets 构造；"
                "手拼一个分母正是分母漂移实际发生的方式"
            )
        # frame 必须随几何走：hash 把坐标系一并记进去，两条记录只有同尺才能对账。
        original_hash = geometry_hash(self.original_field, self.frame)
        main_hash = geometry_hash(self.main_field, self.frame)
        selected_hash = geometry_hash(self.selected, self.frame)

        if self.original_field.area <= 0.0:
            raise CoverageDenominatorError(f"original_field 面积必须大于 0，实际 {self.original_field.area!r}")
        if self.main_field.area <= 0.0:
            # coverage_ratio_main 的分母就是它；地头或障碍把主田吃光必须当场报，不能留给下游除出 inf。
            raise CoverageDenominatorError(f"main_field 面积必须大于 0，实际 {self.main_field.area!r}")
        spill = self.main_field.difference(self.original_field).area
        tolerance = 1e-12 * max(self.original_field.area, 1.0)
        if spill > tolerance:
            raise CoverageDenominatorError(
                f"main_field 必须含于 original_field：越界面积 {spill!r} 超过相对容差 {tolerance!r}"
                f"（original_field.area={self.original_field.area!r}），否则两个比值不同域、不可并列解读"
            )
        on_main = self.target_kind is CoverageTarget.MAIN_FIELD
        expected_hash = main_hash if on_main else original_hash
        if selected_hash != expected_hash:
            # 用 geometry_hash 比较而不是 is：frozen dataclass 会被复制，is 会假阴性。
            raise CoverageDenominatorError(
                f"selected 与 target_kind={self.target_kind.value} 不符："
                f"selected_hash={selected_hash}，期望 {expected_hash}"
            )
        if self.headland_width_m is None:
            if main_hash != original_hash:
                # 没有地头，主田即原田，两个覆盖率必然相等；不允许「没设地头但主田比原田小」这种状态。
                raise CoverageDenominatorError(
                    "headland_width_m 为 None 时 main_field 必须与 original_field 几何等价，"
                    f"实际 main_hash={main_hash} != original_hash={original_hash}"
                )
            ring_hash = None
        else:
            # 申报了宽度却没扣掉任何环带，等于申报本身是空的，直接拒绝。
            ring = self.original_field.difference(self.main_field)
            if ring.is_empty:
                raise CoverageDenominatorError(
                    f"申报了 headland_width_m={self.headland_width_m!r}，"
                    "original_field 与 main_field 之间却没有被扣掉的环带"
                )
            ring_hash = geometry_hash(ring, self.frame)
        object.__setattr__(
            self,
            "provenance",
            DenominatorProvenance(
                target_kind=self.target_kind,
                declared_headland_width_m=self.headland_width_m,
                original_field_hash=original_hash,
                main_field_hash=main_hash,
                selected_hash=selected_hash,
                headland_ring_hash=ring_hash,
            ),
        )


def resolve_coverage_targets(
    problem: CoverageProblem,
    headland: HeadlandArtifact | None,
    *,
    target: CoverageTarget,
    headland_width_m: float | None = None,
) -> CoverageTargets:
    """由 problem 与 headland 阶段产物导出两个分母，这是系统里唯一的分母来源。

    headland 传 None 表示本次运行没跑地头阶段，此时主田就是原田——
    这是事实陈述，不是回退默认值：没有地头就没有被扣掉的环带。
    传了 headland 产物就必须同时申报 headland_width_m：产物本身不带宽度，
    而 provenance 里少记这一项，两条记录就没法按地头配置对账。
    申报不是自由填写：它会被逐 cell 重算对账（见下方循环注释），对不上就抛。

    陷阱：地头阶段的 cell 来自未扣障碍的原始地块，所以主田必须再减一次障碍，
    否则障碍面积会同时算进分子域和分母。
    """
    if headland is None and headland_width_m is not None:
        raise CoverageDenominatorError(
            f"没有地头产物却申报了 headland_width_m={headland_width_m!r}：宽度只能来自实际跑过的地头阶段"
        )
    if headland is not None and headland_width_m is None:
        raise CoverageDenominatorError("有地头产物却没申报 headland_width_m：provenance 会变成无法对账的记录")
    if headland_width_m is not None and headland_width_m <= 0.0:
        raise CoverageDenominatorError(f"headland_width_m 必须大于 0，实际 {headland_width_m!r}")

    field = polygon_from_spec(problem.field)
    scale_hint = max(field.bounds[2] - field.bounds[0], field.bounds[3] - field.bounds[1], 1.0)
    obstacle_items = tuple(
        (spec.geometry_id, polygon_from_spec(spec))
        for spec in sorted(problem.obstacles, key=lambda item: item.geometry_id)
    )
    # 越界障碍必须报错而不是被 difference 静默裁掉：裁掉之后分母看着正常，
    # 少掉的那块面积再也查不出来自哪里。
    validate_obstacles_within_field(field, obstacle_items)
    obstacles = tuple(item[1] for item in obstacle_items)
    obstacle_union = robust_union(obstacles, scale_hint=scale_hint) if obstacles else GeometryCollection()
    original_field = field.difference(obstacle_union)
    if headland is None:
        main_field = original_field
    else:
        # 申报的地头宽度必须可证伪。口径：**不绕损耗环**。
        # 备选口径 buffer(main∪ring, -W) 与 main 对账，在 UTM 大坐标真实地块上的
        # buffer->difference->union->buffer 弦弧往返损耗实测达 rel 4.5e-04（真实地块、
        # w=12、残差 4.9 m²），与 mitre 信号（rel ~3e-03）只差一个量级，噪声地板太高。
        # 新口径是两条**无往返**的断言，诚实路径残差为精确 0 或网格噪声：
        # (a) main == cell.buffer(-W)——与生成侧同一调用直接对账：错宽度（~10-50%）、
        #     mitre（w²(1-π_d/4)·面积比）、quad_segs（弦弧差）全部被干净抓住；
        # (b) main ∪ ring == cell——环带恰好补满、无重叠无遗漏（划分语义）。
        # 不放在 CoverageTargets.__post_init__ 里做：那里只有 original_field（已扣障碍），
        # 用它重算会在障碍周围双重内缩，诚实路径实测假阳性残差 472.9 m²
        # （100x50 田、20x10 内部障碍、h=6），会把正确的分母当错误拒绝。
        #
        # 非均匀地头（逐边不同宽度，Required-Width 公式 H_i = r_rob*(sin(theta-gamma_i)+1) + w_rob/2
        # 随 swath angle 变化）用一个标量本来就无法描述：申报一个标量宽度本身就等于
        # 声称「这个地头是均匀的」，不均匀却申报了标量，就是申报错了，就该抛。
        # 不为它加特例分支。长期正解：HeadlandArtifact 应当携带自己的生成参数
        # （宽度、是否均匀、逐边宽度表），届时这条检查改为与产物自带参数对账。
        mains = []
        for cell in headland.cells:
            # 含障碍地块上主田与环带都可能是多片，先各自并起来再对账。
            main = robust_union(
                tuple(polygon_from_spec(part) for part in cell.main_field), scale_hint=scale_hint
            )
            ring = robust_union(
                tuple(polygon_from_spec(part) for part in cell.headland), scale_hint=scale_hint
            )
            cells_union = robust_union((main, ring), scale_hint=scale_hint)
            # (b) 划分语义：主田与环带互斥（无重叠）。复原完整性由 (a) 间接保证：
            # main=cell.buffer(-W) 且 ring 与 main 互斥，则 ring 必然来自 cell−main。
            partition_residual = main.intersection(ring).area
            # (a) 直接证伪：同一旋钮重算主田
            reconstructed = cells_union.buffer(
                -headland_width_m,
                cap_style="round",
                join_style="round",
                quad_segs=QUAD_SEGS,
            )
            width_residual = main.symmetric_difference(reconstructed).area
            # 实测噪声地板：UTM 坐标网格往返 rel ~5e-04；错宽度/mitre 在 rel 1e-2 以上。
            # 容差取 2e-03：距两侧各留 4 倍以上间隔。合成坐标（小数值）下往返为精确 0。
            tolerance = 2e-3 * max(cells_union.area, 1.0)
            if width_residual > tolerance or partition_residual > tolerance:
                raise CoverageDenominatorError(
                    f"{cell.cell_id}: 申报的地头宽度 {headland_width_m!r} 与产物不符："
                    f"重算主田与产物主田的 symmetric_difference 面积 {width_residual!r}，"
                    f"划分残差 {partition_residual!r}（容差 {tolerance!r}；"
                    f"产物主田 {main.area!r} m²，重算 {reconstructed.area!r} m²）"
                )
            mains.append(main)
        main_field = robust_union(tuple(mains), scale_hint=scale_hint).difference(obstacle_union)
    selected = main_field if target is CoverageTarget.MAIN_FIELD else original_field
    return CoverageTargets(
        original_field=original_field,
        main_field=main_field,
        selected=selected,
        target_kind=target,
        headland_width_m=headland_width_m,
        frame=problem.frame,
        _token=_RESOLVED,
    )


@dataclass(frozen=True)
class CoverageStats:
    coverage_ratio_field: float
    coverage_ratio_main: float
    overlap_ratio: float
    missed_ratio: float
    covered_area_m2: float
    overlap_area_m2: float
    target_kind: CoverageTarget
    denominator: DenominatorProvenance

    def selected_coverage_ratio(self) -> float:
        """协议声明作为头条数字的那个比值；硬门槛不走这里，硬门槛只认 coverage_ratio_field。"""
        if self.target_kind is CoverageTarget.MAIN_FIELD:
            return self.coverage_ratio_main
        return self.coverage_ratio_field


def coverage_stats(
    lines: tuple[BaseGeometry, ...],
    *,
    working_width_m: float,
    targets: CoverageTargets,
) -> CoverageStats:
    """同时给出对原田和对主田的覆盖率；重叠与遗漏一律用原田归一，不随地头配置漂移。

    返回值携带 targets 的分母 provenance：这是覆盖率记录事后可对账的唯一凭据，
    不允许在传播链上被剥掉。
    """
    if not isinstance(targets, CoverageTargets):
        raise TypeError(
            "coverage_stats 只接受 resolve_coverage_targets 产出的 CoverageTargets；"
            "裸几何会让调用方自选分母，那正是本函数要堵死的口子"
        )
    original = targets.original_field
    scale_hint = max(original.bounds[2] - original.bounds[0], original.bounds[3] - original.bounds[1], 1.0)
    clipped = tuple(sweep_piece(line, working_width_m).intersection(original) for line in lines)
    clipped_nonempty = tuple(piece for piece in clipped if not piece.is_empty)
    union = robust_union(clipped_nonempty, scale_hint=scale_hint)
    # 分子和分母必须同域；这里即使上游 footprint 越界，分子也只认对应分母域内的面积。
    covered_field = union.intersection(original).area
    covered_main = union.intersection(targets.main_field).area
    overlap = max(0.0, sum(piece.area for piece in clipped_nonempty) - covered_field)
    return CoverageStats(
        coverage_ratio_field=covered_field / original.area,
        coverage_ratio_main=covered_main / targets.main_field.area,
        overlap_ratio=overlap / original.area,
        missed_ratio=(original.area - covered_field) / original.area,
        covered_area_m2=covered_field,
        overlap_area_m2=overlap,
        target_kind=targets.target_kind,
        denominator=targets.provenance,
    )


def path_work_lines(path: PathArtifact) -> tuple[BaseGeometry, ...]:
    return tuple(line_from_spec(segment.line) for segment in path.segments if segment.kind is PathSegmentKind.WORK)


def nonwork_normalized(path: PathArtifact, *, working_width_m: float, work_area_m2: float) -> float:
    if work_area_m2 <= 0.0:
        raise ValueError("work_area_m2 必须大于 0")
    nonwork_length = sum(
        line_from_spec(segment.line).length
        for segment in path.segments
        if segment.kind is not PathSegmentKind.WORK
    )
    return nonwork_length * working_width_m / work_area_m2


@dataclass(frozen=True)
class PathLengthBreakdown:
    total_m: float
    work_m: float
    nonwork_m: float
    turn_m: float
    transit_m: float


def path_length_breakdown(path: PathArtifact) -> PathLengthBreakdown:
    work = turn = transit = 0.0
    for segment in path.segments:
        length = line_from_spec(segment.line).length
        if segment.kind is PathSegmentKind.WORK:
            work += length
        elif segment.kind is PathSegmentKind.TURN:
            turn += length
        else:
            transit += length
    total = work + turn + transit
    return PathLengthBreakdown(total_m=total, work_m=work, nonwork_m=turn + transit, turn_m=turn, transit_m=transit)


def l_area(path: PathArtifact, *, working_width_m: float, work_area_m2: float) -> float:
    if work_area_m2 <= 0.0:
        raise ValueError("work_area_m2 必须大于 0")
    return path_length_breakdown(path).total_m * working_width_m / work_area_m2


def eta_l(path: PathArtifact) -> float:
    lengths = path_length_breakdown(path)
    return lengths.nonwork_m / lengths.total_m if lengths.total_m > 0.0 else 0.0


def turning_overhead_ratio(path: PathArtifact) -> float:
    lengths = path_length_breakdown(path)
    return lengths.turn_m / lengths.total_m if lengths.total_m > 0.0 else 0.0


def swath_count(path: PathArtifact) -> int:
    return sum(segment.kind is PathSegmentKind.WORK for segment in path.segments)


def headland_area_ratio(main_field: BaseGeometry, headland: BaseGeometry) -> float:
    total = main_field.area + headland.area
    if total <= 0.0:
        raise ValueError("main_field + headland 面积必须大于 0")
    return headland.area / total
