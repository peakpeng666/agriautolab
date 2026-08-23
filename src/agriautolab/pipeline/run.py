"""run_pipeline：逐阶段执行组合体，中间产物按内容哈希记忆化。

组合体数量是乘性的（12 算法的笛卡尔积），同一 (阶段, 输入哈希, 算法, 参数)
只算一次——不记忆化跑不动。记忆化只作用于阶段产物（artifact），
校验与目标向量每次照算（它们便宜，且要吃到最新的协议参数）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
import time
from typing import Any, Callable, Mapping

from agriautolab.algorithms.decomposition.boustrophedon_cells import BoustrophedonDecomposition
from agriautolab.algorithms.headland.no_headland import NoHeadland
from agriautolab.algorithms.headland.uniform_headland import ConstantWidthHeadland
from agriautolab.algorithms.path.dubins_transit import DubinsPathPlanner
from agriautolab.algorithms.path.reeds_shepp_transit import ReedsSheppPathPlanner
from agriautolab.algorithms.route.boustrophedon_order import BoustrophedonRoutePlanner
from agriautolab.algorithms.route.rural_postman_greedy import GreedyRuralPostmanRoutePlanner
from agriautolab.algorithms.route.skip_one_order import SkipOneRoutePlanner
from agriautolab.algorithms.swath.fixed_angle import FixedAngleSwathGenerator
from agriautolab.algorithms.swath.longest_edge import LongestEdgeSwathGenerator
from agriautolab.algorithms.swath.min_width import MinimumWidthSwathGenerator
from agriautolab.algorithms.swath.principal_axis import PrincipalAxisSwathGenerator
from agriautolab.algorithms.swath.row_aligned import RowAlignedSwathGenerator
from agriautolab.contracts.enums import RunStatus
from agriautolab.contracts.artifacts import (
    CellsArtifact, HeadlandArtifact, PathArtifact, RouteArtifact, SwathsArtifact,
)
from agriautolab.contracts.problem import CoverageProblem
from agriautolab.contracts.protocol import BenchmarkProtocol
from agriautolab.contracts.vehicle import VehicleSpec
from agriautolab.coverage.stages.decomposition import NoDecomposition
from agriautolab.evidence.hashing import content_hash
from agriautolab.metrics.path import TransferBreakdown, transit_breakdown
from agriautolab.metrics.path import headland_turn_count as headland_turn_count_metric
from agriautolab.metrics.path import row_crossings as row_crossings_metric
from agriautolab.pareto.front import ObjectiveVector
from agriautolab.pipeline.config import PipelineConfig
from agriautolab.validation.validator import PathValidator, ValidationResult

_DECOMPOSITIONS = {"no_decomposition": NoDecomposition, "boustrophedon_cells": BoustrophedonDecomposition}
_HEADLANDS = {"no_headland": NoHeadland, "uniform_headland": ConstantWidthHeadland}
_SWATHS = {
    "fixed_angle": FixedAngleSwathGenerator,
    "principal_axis": PrincipalAxisSwathGenerator,
    "min_width": MinimumWidthSwathGenerator,
    "longest_edge": LongestEdgeSwathGenerator,
    "row_aligned": RowAlignedSwathGenerator,
}
_ROUTES = {
    "boustrophedon_order": BoustrophedonRoutePlanner,
    "skip_one_order": SkipOneRoutePlanner,
    "rural_postman_greedy": GreedyRuralPostmanRoutePlanner,
}
_PATHS = {"dubins_transit": DubinsPathPlanner, "reeds_shepp_transit": ReedsSheppPathPlanner}


@dataclass
class StageMemo:
    """中间产物记忆化：key = (阶段, 输入哈希, 算法, 参数) 的内容哈希。

    命中计数是审计证据的一部分（「组合体乘性」不是修辞，是可以被看到的数字）。
    """

    store: dict[str, Any] = field(default_factory=dict)
    hits: int = 0
    misses: int = 0

    def key(self, stage: str, algorithm_id: str, params: Mapping[str, float], input_artifact: Any) -> str:
        return content_hash({
            "stage": stage,
            "algorithm": algorithm_id,
            "params": dict(sorted(params.items())),
            "input": content_hash(input_artifact.model_dump(mode="json")),
        })

    def get_or_compute(self, key: str, compute):
        if key in self.store:
            self.hits += 1
            return self.store[key]
        self.misses += 1
        value = compute()
        self.store[key] = value
        return value


@dataclass(frozen=True)
class PipelineTiming:
    planning_s: float
    postprocessing_s: float
    validation_s: float


@dataclass(frozen=True)
class PipelineResult:
    config: PipelineConfig
    config_id: str
    path: PathArtifact
    validation: ValidationResult
    objectives: ObjectiveVector | None
    headland_width_m: float | None
    # 转移五项分解。总数查不出超额出在哪一项——这是 G-A 诊断闸要的强制分类。
    transit: TransferBreakdown
    timing: PipelineTiming = PipelineTiming(0.0, 0.0, 0.0)


def _objectives_or_none(problem, path, validation) -> ObjectiveVector | None:
    """不可行组合没有目标向量：失败是数据（RunStatus + 结构化原因），不是异常。

    无地头 + 前进-only Dubins 就是典型：掉头向界外鼓出最多 2R，outside_area
    必然拒绝——掉头空间正是地头存在的理由，这里不伪造数字、不放宽门槛。
    """
    if validation.status is not RunStatus.OK:
        return None
    return ObjectiveVector(
        path_length=validation.metric("path_length"),
        headland_turns=float(headland_turn_count_metric(path)),
        row_crossings=row_crossings_metric(path, problem.row_structure),
    )


def _cell_of_work_index(cells: CellsArtifact, route: RouteArtifact) -> tuple[int, ...] | None:
    """按路线顺序给出每个作业段所属的 cell 序号；单 cell 时返回 None。

    cell 归属不存进 Swath 契约：它由 cells 与中心线几何唯一确定，
    新建第二处住所只会多一个可能与几何分家的地方。中点判定即可——
    swath 中心线是主田与扫掠线的交线，整条都在同一个 cell 内。
    """
    if len(cells.cells) <= 1:
        return None
    from agriautolab.geometry.validate import line_from_spec, polygon_from_spec

    polygons = tuple(polygon_from_spec(cell) for cell in cells.cells)
    swath_by_id = {swath.swath_id: swath for swath in route.swaths}
    order: list[int] = []
    for traversal in route.traversals:
        centerline = line_from_spec(swath_by_id[traversal.swath_id].centerline)
        midpoint = centerline.interpolate(0.5, normalized=True)
        distances = [polygon.distance(midpoint) for polygon in polygons]
        order.append(min(range(len(polygons)), key=lambda index: distances[index]))
    return tuple(order)


def _require_param(config: PipelineConfig, name: str, stage: str) -> float:
    if name not in config.params:
        raise ValueError(f"阶段 {stage} 需要 params[{name!r}]，PipelineConfig 里没有")
    return float(config.params[name])


def _center_free_polygons(cell: Any, body_width_m: float) -> tuple:
    """cell 内缩 body/2 的车体中心可行域（PolygonSpec 元组），语义同 Block A FieldGeometry.center_free。

    真实地块实测：内缩可把颈缩地块劈成 MultiPolygon——
    两个部件都是合法扫掠域，按片返回而不是拒绝；语义同 BCD 的多部件 cell 处理。
    """
    from agriautolab.geometry.footprint import QUAD_SEGS
    from agriautolab.geometry.validate import polygon_from_spec, polygon_to_spec

    polygon = polygon_from_spec(cell)
    eroded = polygon.buffer(
        -body_width_m / 2.0, cap_style="round", join_style="round", quad_segs=QUAD_SEGS,
    )
    if eroded.is_empty:
        raise ValueError(
            f"{getattr(cell, 'geometry_id', 'cell')}: cell 太窄，内缩半个车宽后没有可行中心域"
        )
    parts = eroded.geoms if hasattr(eroded, "geoms") else (eroded,)
    return tuple(
        polygon_to_spec(part, f"{cell.geometry_id}:center-free:{index}")
        for index, part in enumerate(parts)
    )


def run_pipeline(
    problem: CoverageProblem,
    vehicle: VehicleSpec,
    config: PipelineConfig,
    protocol: BenchmarkProtocol,
    *,
    memo: StageMemo | None = None,
    clock: Callable[[], float] = time.perf_counter,
) -> PipelineResult:
    """执行一个五阶段组合体并独立校验，返回路径、校验结果与三维目标向量。"""
    if config.decomposition not in _DECOMPOSITIONS:
        raise ValueError(f"未知 decomposition：{config.decomposition}")
    if config.headland not in _HEADLANDS:
        raise ValueError(f"未知 headland：{config.headland}")
    if config.swath not in _SWATHS:
        raise ValueError(f"未知 swath：{config.swath}")
    if config.route not in _ROUTES:
        raise ValueError(f"未知 route：{config.route}")
    if config.path not in _PATHS:
        raise ValueError(f"未知 path：{config.path}")
    memo = memo if memo is not None else StageMemo()
    planning_started = clock()

    cells: CellsArtifact = memo.get_or_compute(
        memo.key("decomposition", config.decomposition, {}, problem),
        lambda: _DECOMPOSITIONS[config.decomposition]().run(problem),
    )

    if config.headland == "no_headland":
        headland_artifact: HeadlandArtifact | None = None
        headland_width_m: float | None = None
        # 扫掠域取车体中心可行域（cell 内缩 body/2），不是地头：分母仍是原田
        # （resolve(problem, None) 的既定语义），这里只是让中心线不把车体带出边界——
        # 否则 no_headland 组合被 outside_area 全部拒绝，运动学内缩与地头是两回事。
        # 颈缩地块内缩成多片：逐片展开成独立扫掠域（实测颈缩地块两片）。
        mains = tuple(
            part
            for cell in cells.cells
            for part in _center_free_polygons(cell, vehicle.body_width_m)
        )
    else:
        width = _require_param(config, "headland_width_m", "headland")
        headland_artifact = memo.get_or_compute(
            memo.key("headland", config.headland, {"headland_width_m": width}, cells),
            lambda: _HEADLANDS[config.headland](width).run(cells),
        )
        headland_width_m = width
        mains = tuple(part for cell in headland_artifact.cells for part in cell.main_field)

    swath_params = {"angle_rad": _require_param(config, "angle_rad", "swath")} if config.swath == "fixed_angle" else {}
    swaths: SwathsArtifact = memo.get_or_compute(
        memo.key("swath", config.swath, swath_params, headland_artifact if headland_artifact is not None else cells),
        lambda: _SWATHS[config.swath](**({"angle_rad": swath_params["angle_rad"]} if swath_params else {})).run(
            mains, working_width_m=vehicle.working_width_m, problem=problem
        ),
    )

    if config.route == "rural_postman_greedy":
        route: RouteArtifact = memo.get_or_compute(
            memo.key("route", config.route, {"radius": vehicle.min_turning_radius_m}, swaths),
            lambda: _ROUTES[config.route]().run(swaths, min_turning_radius_m=vehicle.min_turning_radius_m),
        )
    else:
        route = memo.get_or_compute(
            memo.key("route", config.route, {}, swaths),
            lambda: _ROUTES[config.route]().run(swaths),
        )

    # 规范参数键 path_sample_step_m；dubins_sample_step_m 为 legacy 键，两者等价。
    sample_step = float(config.params.get("path_sample_step_m", config.params.get("dubins_sample_step_m", 0.25)))
    if config.path == "reeds_shepp_transit":
        # 允许域 = 可作业区：等长孪生词里优先选把掉头收进场内的那个（见该阶段 docstring）。
        from agriautolab.geometry.kernel import FieldGeometry
        from agriautolab.kinematics.reeds_shepp import ReverseCostModel

        allowed_region = FieldGeometry.from_problem(problem, vehicle).raw_free
        # 倒车代价来自协议，不由阶段自选：换了倒车偏好就是换了目标函数。
        # 它同时进记忆化 key——否则两种偏好会共用同一条缓存路径。
        cost_model = ReverseCostModel(
            reverse_length_multiplier=protocol.reverse_cost.reverse_length_multiplier,
            gear_shift_penalty_m=protocol.reverse_cost.gear_shift_penalty_m,
        )
        path: PathArtifact = memo.get_or_compute(
            memo.key("path", config.path, {
                "dubins_sample_step_m": sample_step,
                "reverse_length_multiplier": cost_model.reverse_length_multiplier,
                "gear_shift_penalty_m": cost_model.gear_shift_penalty_m,
            }, route),
            lambda: _PATHS[config.path](sample_step, cost_model=cost_model).run(
                route, vehicle, allowed_region=allowed_region
            ),
        )
    else:
        path = memo.get_or_compute(
            memo.key("path", config.path, {"dubins_sample_step_m": sample_step}, route),
            lambda: _PATHS[config.path](sample_step).run(route, vehicle),
        )

    planning_finished = clock()
    validation_started = clock()
    validation = PathValidator().validate(
        problem, vehicle, path, protocol,
        headland=headland_artifact, headland_width_m=headland_width_m,
    )
    validation_finished = clock()
    post_started = clock()
    objectives = _objectives_or_none(problem, path, validation)
    transit = transit_breakdown(path, cell_of_work_index=_cell_of_work_index(cells, route))
    post_finished = clock()
    return PipelineResult(
        config=config,
        config_id=config.config_id(),
        path=path,
        validation=validation,
        objectives=objectives,
        headland_width_m=headland_width_m,
        transit=transit,
        timing=PipelineTiming(
            planning_s=planning_finished - planning_started,
            postprocessing_s=post_finished - post_started,
            validation_s=validation_finished - validation_started,
        ),
    )
