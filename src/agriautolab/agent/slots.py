"""候选槽位抽象：把 agent 层开放的算法自由度从硬编码单槽位改为可登记多槽位。

一个 CandidateSlot 完整描述某个 pipeline 阶段上开放的启发式槽位：槽位 id、
所属阶段、契约函数名、沙箱编译、探针值检查、评估配置构造、不变性检查与
对抗复核器集。四道闸（gates.py）与演化循环（evolve.py）通过槽位对象引用
这些语义；新增槽位只需实现协议并登记进 SLOTS 字典。

当前唯一登记的槽位是 swath_angle（swath 阶段的扫掠角偏移启发式）。其全部
语义自 gates.py 逐字迁移——包括 RNG 消耗顺序（8 组 × 每组 3 次 uniform，
theta/tx/ty）与错误消息文本——因此单槽位时代的行为逐位不变。

import 方向（无环）：slots -> gates（闸门结果类型）+ slots -> reviewer；
gates 对 slots 只做函数内延迟导入（默认槽位解析），不形成模块级环。
"""

from __future__ import annotations

import math
from typing import Protocol, runtime_checkable

from agriautolab.agent.gates import GATE_INVARIANCE, GateOutcome, HeuristicFn
from agriautolab.agent.reviewer import AdversarialReviewer, DEFAULT_REVIEWERS
from agriautolab.agent.sandbox import SandboxViolation, run_sandboxed
from agriautolab.contracts.enums import CoverageStage
from agriautolab.contracts.problem import CoverageProblem
from agriautolab.contracts.vehicle import VehicleSpec
from agriautolab.features.extract import extract_instance_features
from agriautolab.pipeline.config import PipelineConfig


@runtime_checkable
class CandidateSlot(Protocol):
    """一个开放的候选槽位：演化循环在某个 pipeline 阶段让生成式启发式占据的自由度。

    probe_value 在候选违规（偏移越界/非有限/类型错误）时抛 ValueError/TypeError，
    闸门负责把异常转为淘汰记录——槽位只承载语义，不承载流程。
    """

    slot_id: str
    stage: CoverageStage
    contract_function: str
    reviewers: tuple[AdversarialReviewer, ...]

    def compile(self, source: str) -> HeuristicFn: ...

    def probe_value(self, function: HeuristicFn, problem: CoverageProblem,
                    vehicle: VehicleSpec) -> float: ...

    def build_config(self, function: HeuristicFn, problem: CoverageProblem,
                     vehicle: VehicleSpec) -> PipelineConfig: ...

    def invariance_check(self, function: HeuristicFn, problem: CoverageProblem,
                         vehicle: VehicleSpec, rng) -> GateOutcome: ...


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


class SwathAngleSlot:
    """swath 阶段的扫掠角偏移槽位：契约函数 swath_angle_offset_rad(features) -> float。

    语义与 gates.py 单槽位时代一一对应：compile = 原 compile_candidate、
    probe_value = 原 _offset_only、build_config = 原
    candidate_config(_candidate_angle(...))、invariance_check = 原
    invariance_gate 循环体（RNG 消耗顺序逐字保留）。
    """

    slot_id: str = "swath_angle"
    stage: CoverageStage = CoverageStage.SWATH
    contract_function: str = "swath_angle_offset_rad"
    reviewers: tuple[AdversarialReviewer, ...] = DEFAULT_REVIEWERS

    def compile(self, source: str) -> HeuristicFn:
        """沙箱编译并提取契约函数。任何违规（语法/禁令/缺函数/签名不符）当场抛。"""
        namespace = run_sandboxed(source)
        function = namespace.get(self.contract_function)
        if not callable(function):
            raise SandboxViolation(f"候选代码必须定义顶层函数 {self.contract_function}(features)")
        try:
            function({"elongation": 1.0})
        except TypeError as error:
            raise SandboxViolation(f"契约函数签名不符（应接受一个 features 映射）：{error}") from error
        return function

    def probe_value(self, function: HeuristicFn, problem: CoverageProblem,
                    vehicle: VehicleSpec) -> float:
        return _offset_only(function, problem, vehicle)

    def build_config(self, function: HeuristicFn, problem: CoverageProblem,
                     vehicle: VehicleSpec) -> PipelineConfig:
        return candidate_config(_candidate_angle(function, problem, vehicle))

    def invariance_check(self, function: HeuristicFn, problem: CoverageProblem,
                         vehicle: VehicleSpec, rng) -> GateOutcome:
        """随机刚体变换下偏移不变（特征旋转不变，偏移按构造应当继承）。"""
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
                    base_offset = self.probe_value(function, problem, vehicle)
                rotated_offset = self.probe_value(function, rotated, vehicle)
            except Exception as error:  # noqa: BLE001 -- 闸门把一切失败转为淘汰记录（保留原因），不让循环崩溃
                return GateOutcome(GATE_INVARIANCE, False, f"{type(error).__name__}: {error}")
            if abs(rotated_offset - base_offset) > 1e-9:
                return GateOutcome(
                    GATE_INVARIANCE, False,
                    f"旋转 {theta:.4f} rad 后偏移漂移 {abs(rotated_offset - base_offset):.3e}",
                )
        return GateOutcome(GATE_INVARIANCE, True, "8 组随机刚体变换下偏移不变（< 1e-9）")


# 已登记槽位注册表：新增槽位在此登记（本次重构不新增）。键是槽位 id（wire 身份），
# 进入 ProposalContext.slot_id 与 EvolutionRecord.slot_id。
SLOTS: dict[str, CandidateSlot] = {"swath_angle": SwathAngleSlot()}

# 默认槽位：闸门与演化循环未显式指定 slot 时解析到这里，单槽位时代行为因此不变。
DEFAULT_SLOT_ID = "swath_angle"
