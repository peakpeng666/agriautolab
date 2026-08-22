"""候选算法的四道闸：契约、校验、确定性、不变性。不过闸即淘汰，不修一下再用。"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Mapping

from agriautolab.agent.sandbox import SandboxViolation, run_sandboxed
from agriautolab.contracts.problem import CoverageProblem
from agriautolab.contracts.protocol import BenchmarkProtocol
from agriautolab.contracts.vehicle import VehicleSpec
from agriautolab.features.extract import extract_instance_features
from agriautolab.pipeline.config import PipelineConfig
from agriautolab.pipeline.run import run_pipeline

HeuristicFn = Callable[[Mapping[str, float]], float]

GATE_CONTRACT = "contract"
GATE_VALIDATION = "validation"
GATE_DETERMINISM = "determinism"
GATE_INVARIANCE = "invariance"


@dataclass(frozen=True)
class GateOutcome:
    gate: str
    passed: bool
    detail: str


def compile_candidate(source_code: str) -> HeuristicFn:
    """沙箱编译并提取契约函数。任何违规（语法/禁令/缺函数/签名不符）当场抛。"""
    namespace = run_sandboxed(source_code)
    function = namespace.get("swath_angle_offset_rad")
    if not callable(function):
        raise SandboxViolation("候选代码必须定义顶层函数 swath_angle_offset_rad(features)")
    try:
        function({"elongation": 1.0})
    except TypeError as error:
        raise SandboxViolation(f"契约函数签名不符（应接受一个 features 映射）：{error}") from error
    return function


def principal_angle_of(problem: CoverageProblem, vehicle: VehicleSpec) -> float:
    from agriautolab.algorithms.swath.principal_axis import principal_axis
    from agriautolab.geometry.robust import robust_union
    from agriautolab.geometry.validate import polygon_from_spec

    field = polygon_from_spec(problem.field)
    obstacles = tuple(
        polygon_from_spec(spec) for spec in sorted(problem.obstacles, key=lambda item: item.geometry_id)
    )
    scale_hint = max(field.bounds[2] - field.bounds[0], field.bounds[3] - field.bounds[1], 1.0)
    free = field.difference(robust_union(obstacles, scale_hint=scale_hint)) if obstacles else field
    ux, uy = principal_axis(free if free.geom_type == "Polygon" else free.convex_hull)
    return math.atan2(uy, ux)


def candidate_config(angle_rad: float) -> PipelineConfig:
    """候选的评估配置：候选只占用 swath 槽位（fixed_angle + 导出角），其余槽位固定。"""
    return PipelineConfig(
        decomposition="no_decomposition", headland="uniform_headland", swath="fixed_angle",
        route="boustrophedon_order", path="dubins_transit",
        params={"headland_width_m": 8.0, "angle_rad": angle_rad},
    )


def _offset_only(function: HeuristicFn, problem: CoverageProblem, vehicle: VehicleSpec) -> float:
    features = extract_instance_features(problem, vehicle).values
    offset = function(features)
    if not math.isfinite(offset) or abs(offset) > math.pi / 2.0 + 1e-12:
        raise ValueError(f"候选返回的偏移越界或非有限：{offset!r}")
    return offset


def _candidate_angle(function: HeuristicFn, problem: CoverageProblem, vehicle: VehicleSpec) -> float:
    return principal_angle_of(problem, vehicle) + _offset_only(function, problem, vehicle)


def contract_gate(source_code: str) -> tuple[HeuristicFn | None, GateOutcome]:
    """第一道：能过沙箱编译、契约函数存在且签名正确、典型输入下返回有限偏移。"""
    try:
        function = compile_candidate(source_code)
        _offset_only(function, _reference_problem(), _reference_vehicle())
    except (SandboxViolation, ValueError, TypeError) as error:
        return None, GateOutcome(GATE_CONTRACT, False, f"{type(error).__name__}: {error}")
    return function, GateOutcome(GATE_CONTRACT, True, "沙箱编译通过，契约签名正确，偏移有限")


def _reference_problem() -> CoverageProblem:
    from agriautolab.contracts.geometry import Point, PolygonSpec

    return CoverageProblem(
        problem_id="gate-reference",
        field=PolygonSpec(geometry_id="field", exterior=(
            Point(x=0.0, y=0.0), Point(x=60.0, y=0.0), Point(x=60.0, y=40.0),
            Point(x=0.0, y=40.0), Point(x=0.0, y=0.0),
        )),
    )


def _reference_vehicle() -> VehicleSpec:
    return VehicleSpec(working_width_m=9.7, body_width_m=2.0, min_turning_radius_m=3.0)


def validation_gate(function: HeuristicFn, problem: CoverageProblem, vehicle: VehicleSpec,
                     protocol: BenchmarkProtocol) -> GateOutcome:
    """第二道：产出路径必须过 Block A 的 PathValidator。不通过直接淘汰，不许修一下再用。"""
    try:
        result = run_pipeline(problem, vehicle, candidate_config(_candidate_angle(function, problem, vehicle)), protocol)
    except Exception as error:  # noqa: BLE001 -- 闸门把一切失败转为淘汰记录（保留原因），不让循环崩溃
        return GateOutcome(GATE_VALIDATION, False, f"{type(error).__name__}: {error}")
    if result.objectives is None:
        return GateOutcome(GATE_VALIDATION, False, f"校验拒绝：{result.validation.failure_reason}")
    return GateOutcome(GATE_VALIDATION, True, f"校验通过，目标 {result.objectives.as_tuple()}")


def determinism_gate(function: HeuristicFn, problem: CoverageProblem, vehicle: VehicleSpec,
                     protocol: BenchmarkProtocol) -> GateOutcome:
    """第三道：同一输入跑两次，目标向量与路径序列化逐位相同。"""
    try:
        angle = _candidate_angle(function, problem, vehicle)
        first = run_pipeline(problem, vehicle, candidate_config(angle), protocol)
        second = run_pipeline(problem, vehicle, candidate_config(angle), protocol)
    except Exception as error:  # noqa: BLE001 -- 同上
        return GateOutcome(GATE_DETERMINISM, False, f"{type(error).__name__}: {error}")
    if first.objectives is None or second.objectives is None:
        return GateOutcome(GATE_DETERMINISM, False, "目标向量缺失（校验未通过）")
    if first.objectives != second.objectives or first.path.model_dump_json() != second.path.model_dump_json():
        return GateOutcome(GATE_DETERMINISM, False, "两次运行不一致")
    return GateOutcome(GATE_DETERMINISM, True, "两次运行逐位相同")


def invariance_gate(function: HeuristicFn, problem: CoverageProblem, vehicle: VehicleSpec,
                     protocol: BenchmarkProtocol, rng) -> GateOutcome:
    """第四道：随机刚体变换下偏移不变（特征旋转不变，偏移按构造应当继承）。"""
    from shapely.affinity import rotate as shp_rotate, translate as shp_translate

    from agriautolab.geometry.validate import polygon_from_spec, polygon_to_spec

    base_offset = None
    for _ in range(8):
        theta = float(rng.uniform(-math.pi, math.pi))
        tx, ty = float(rng.uniform(-100.0, 100.0)), float(rng.uniform(-100.0, 100.0))

        def move(geometry):
            return shp_translate(shp_rotate(geometry, theta, origin=(0.0, 0.0), use_radians=True), tx, ty)

        field = move(polygon_from_spec(problem.field))
        rows = problem.row_structure
        rotated = problem.model_copy(update={
            "field": polygon_to_spec(field, problem.field.geometry_id),
            "obstacles": tuple(
                polygon_to_spec(move(polygon_from_spec(spec)), spec.geometry_id) for spec in problem.obstacles
            ),
            "row_structure": rows.model_copy(update={"direction_rad": rows.direction_rad + theta}) if rows else None,
        })
        try:
            if base_offset is None:
                base_offset = _offset_only(function, problem, vehicle)
            rotated_offset = _offset_only(function, rotated, vehicle)
        except Exception as error:  # noqa: BLE001 -- 同上
            return GateOutcome(GATE_INVARIANCE, False, f"{type(error).__name__}: {error}")
        if abs(rotated_offset - base_offset) > 1e-9:
            return GateOutcome(
                GATE_INVARIANCE, False,
                f"旋转 {theta:.4f} rad 后偏移漂移 {abs(rotated_offset - base_offset):.3e}",
            )
    return GateOutcome(GATE_INVARIANCE, True, "8 组随机刚体变换下偏移不变（< 1e-9）")
