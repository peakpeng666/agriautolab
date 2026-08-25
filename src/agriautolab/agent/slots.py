"""候选槽位抽象：把 agent 层开放的算法自由度从硬编码单槽位改为可登记多槽位。

一个 CandidateSlot 完整描述某个 pipeline 阶段上开放的启发式槽位：槽位 id、
所属阶段、契约函数名、沙箱编译、探针值检查、评估配置构造、不变性检查与
对抗复核器集。四道闸（gates.py）与演化循环（evolve.py）通过槽位对象引用
这些语义。新增槽位要登记三处：本模块的 SLOTS 字典（漏登记 -> evolve_pool
对未知 slot id 抛 ValueError）、proposer.py 的 PROMPT_TEMPLATES 与
MOCK_CANDIDATES_BY_SLOT（漏登记 -> propose/build_prompt 时 KeyError）；
三表键一致性由 tests/agent/test_slots.py 钉住。

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
from agriautolab.agent.reviewer import ROUTE_REVIEWERS, SWATH_REVIEWERS, AdversarialReviewer
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


def reference_problem() -> CoverageProblem:
    """契约闸的参考田（60x40 矩形，无障碍）：主轴角浮点精确为 0.0。"""
    from agriautolab.contracts.geometry import Point, PolygonSpec

    return CoverageProblem(
        problem_id="gate-reference",
        field=PolygonSpec(geometry_id="field", exterior=(
            Point(x=0.0, y=0.0), Point(x=60.0, y=0.0), Point(x=60.0, y=40.0),
            Point(x=0.0, y=40.0), Point(x=0.0, y=0.0),
        )),
    )


def reference_vehicle() -> VehicleSpec:
    """契约闸的参考机具。"""
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
    reviewers: tuple[AdversarialReviewer, ...] = SWATH_REVIEWERS

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


class RouteOrderSlot:
    """route 阶段的条带访问序槽位：契约函数 next_swath_score(state, candidate) -> float。

    与 SwathAngleSlot 的语义区别：
    - 契约函数是**双参** (state, candidate)，不是单参 (features)；
    - probe_value / invariance_check 的形态必须适配"双参 + 离散序贯"——不设 |v|≤π/2 界；
    - build_config **不**调用 run_pipeline（会污染任务 1 的评估计数），
      直接调上游阶段类拿 swaths，用 construct_solution 求访问序，把
      排名烘焙进 params 即可；
    - reviewers 用 ROUTE_REVIEWERS（不复用 SWATH_REVIEWERS 的 swath 值域假设）。
    """

    slot_id: str = "route_order"
    stage: CoverageStage = CoverageStage.ROUTE
    contract_function: str = "next_swath_score"
    reviewers: tuple[AdversarialReviewer, ...] = ROUTE_REVIEWERS

    # 试调用输入：作为槽位私有常量，compile 后立即用这对输入验签名
    _PROBE_STATE: dict[str, float] = {"visited_count": 1.0, "remaining_count": 3.0}
    _PROBE_CANDIDATE: dict[str, float] = {"distance_norm": 1.0, "projection_norm": 0.0}

    def compile(self, source: str) -> HeuristicFn:
        """沙箱编译并提取契约函数 next_swath_score(state, candidate) -> float。

        试调用：function(_PROBE_STATE, _PROBE_CANDIDATE) 捕 TypeError 报签名不符。
        """
        namespace = run_sandboxed(source)
        function = namespace.get(self.contract_function)
        if not callable(function):
            raise SandboxViolation(f"候选代码必须定义顶层函数 {self.contract_function}(state, candidate)")
        try:
            function(self._PROBE_STATE, self._PROBE_CANDIDATE)
        except TypeError as error:
            raise SandboxViolation(
                f"契约函数签名不符（应接受两个 dict 形参）：{error}"
            ) from error
        return function

    def probe_value(self, function: HeuristicFn, problem: CoverageProblem,
                    vehicle: VehicleSpec) -> float:
        """route 槽位不暴露单一标量探针；返回 0.0（无 π/2 界，参考田上跑一次）。"""
        try:
            value = function(self._PROBE_STATE, self._PROBE_CANDIDATE)
        except (TypeError, ValueError) as error:
            raise ValueError(f"候选探针失败：{type(error).__name__}: {error}") from error
        if not math.isfinite(float(value)):
            raise ValueError(f"候选返回非有限分数：{value!r}")
        return float(value)

    def build_config(self, function: HeuristicFn, problem: CoverageProblem,
                     vehicle: VehicleSpec) -> PipelineConfig:
        """直接调上游阶段类拿 swaths，用 construct_solution 求访问序。

        关键纪律：禁止调用 run_pipeline——会污染任务 1 的评估计数。
        候选选择通过 params["rank:<swath_id>"] 烘焙；rank = 访问序号。
        """
        from agriautolab.algorithms.headland.uniform_headland import ConstantWidthHeadland
        from agriautolab.coverage.stages.decomposition import NoDecomposition
        from agriautolab.algorithms.swath.principal_axis import PrincipalAxisSwathGenerator
        from agriautolab.algorithms.route.constructive_order import (
            RouteOrderProblem, endpoints_of, project_state,
        )
        from agriautolab.geometry.validate import polygon_from_spec
        from agriautolab.geometry.robust import robust_union
        from agriautolab.algorithms.swath.principal_axis import principal_axis
        from agriautolab.optimization.constructive import (
            construct_solution,
        )

        # 上游分解必须与返回的 PipelineConfig 声明的 decomposition 一致。
        # 曾用 BoustrophedonDecomposition 烘焙 rank 却返回 no_decomposition：
        # 有障碍的田上 BCD 会切出不同 cell 布局，重放时条带数量与序号 id 都变，
        # 于是 RankedSwathOrderPlanner 要么报缺 rank 键，要么把 rank 套到
        # 几何上毫不相干的条带上。真值测试 test_baked_ranks_match_replayed_swaths
        # 在有障碍田上钉住这一点。
        cells = NoDecomposition().run(problem)
        headland = ConstantWidthHeadland(8.0).run(cells)
        mains = tuple(part for cell in headland.cells for part in cell.main_field)
        swaths = PrincipalAxisSwathGenerator().run(
            mains, working_width_m=vehicle.working_width_m, problem=problem,
        )
        if not swaths.swaths:
            raise ValueError("build_config: 参考田未产生条带，构造空访问序失败")

        # 主轴法向（旋转不变键的来源）
        field = polygon_from_spec(problem.field)
        obstacles = tuple(
            polygon_from_spec(spec) for spec in sorted(problem.obstacles, key=lambda item: item.geometry_id)
        )
        scale_hint = max(field.bounds[2] - field.bounds[0], field.bounds[3] - field.bounds[1], 1.0)
        free = field.difference(robust_union(obstacles, scale_hint=scale_hint)) if obstacles else field
        ux, uy = principal_axis(free if free.geom_type == "Polygon" else free.convex_hull)
        # 地块质心 = 简单算术（不调 shapely）
        ext = problem.field.exterior
        cx = sum(p.x for p in ext) / len(ext)
        cy = sum(p.y for p in ext) / len(ext)

        # 几何由构造函数必填注入：端点原样进去，进入/离开哪一端由访问序奇偶在
        # RouteOrderProblem 内部决定（REVERSE 从 points[0] 出，不是 points[-1]）。
        problem_obj = RouteOrderProblem(
            {s.swath_id: endpoints_of(s) for s in swaths.swaths},
            min_turning_radius_m=vehicle.min_turning_radius_m,
            working_width_m=vehicle.working_width_m,
            field_centroid=(cx, cy),
            principal_normal=(-uy, ux),  # 旋转 90° 得法向
        )
        total_swath_count = len(swaths.swaths)

        # 构造沙箱评分函数：state, candidate -> float，调用槽位的实际候选
        candidate_fn = function

        class _SandboxHeuristic:
            heuristic_id: str = "candidate"

            def score(self, state, action) -> float:
                # state 必须先投影成 Mapping 再交给候选：construct_solution 传进来的是
                # 原始 tuple[str, ...]，而契约与 prompt 模板向候选承诺的是
                # {"visited_count", "remaining_count"}。不投影则任何用 state.get(...)
                # 的候选都会在此抛异常 → ConstructionError → 被 validation 闸淘汰，
                # 槽位静默退化成 action-only 启发式。
                return float(candidate_fn(
                    project_state(state, total_swath_count=total_swath_count), action,
                ))

        visit_order = construct_solution(problem_obj, _SandboxHeuristic())
        # 烘焙 rank：访问序号 = rank（rank 升序访问；并列按 swath_id 决胜）
        rank_params: dict[str, float] = {
            f"rank:{swath_id}": float(index)
            for index, swath_id in enumerate(visit_order)
        }
        params = {"headland_width_m": 8.0, **rank_params}
        return PipelineConfig(
            decomposition="no_decomposition", headland="uniform_headland",
            swath="principal_axis", route="ranked_swath_order", path="dubins_transit",
            params=params,
        )

    def invariance_check(self, function: HeuristicFn, problem: CoverageProblem,
                         vehicle: VehicleSpec, rng) -> GateOutcome:
        """8 组随机刚体变换下，build_config 烘焙的访问序逐元素相同（离散序不变）。

        与 SwathAngleSlot 的 8×3 uniform 消耗模式完全一致（theta/tx/ty 顺序），
        但判定标准从「标量差 < 1e-9」改为「tuple 相等」——离散枚举无 ULP 噪声。
        """
        from shapely.affinity import rotate as shp_rotate, translate as shp_translate

        from agriautolab.geometry.validate import polygon_from_spec, polygon_to_spec

        base_order: tuple[str, ...] | None = None
        for _ in range(8):
            theta = float(rng.uniform(-math.pi, math.pi))
            tx, ty = float(rng.uniform(-100.0, 100.0)), float(rng.uniform(-100.0, 100.0))

            def move(geometry):
                return shp_translate(shp_rotate(geometry, theta, origin=(0.0, 0.0), use_radians=True), tx, ty)

            rotated = problem.model_copy(update={
                "field": polygon_to_spec(move(polygon_from_spec(problem.field)), problem.field.geometry_id),
                "obstacles": tuple(
                    polygon_to_spec(move(polygon_from_spec(spec)), spec.geometry_id) for spec in problem.obstacles
                ),
            })
            try:
                config = self.build_config(function, rotated, vehicle)
            except Exception as error:  # noqa: BLE001 -- 闸门把一切失败转为淘汰记录
                return GateOutcome(GATE_INVARIANCE, False, f"{type(error).__name__}: {error}")
            order = tuple(
                key.removeprefix("rank:") for key, _ in sorted(
                    ((k, v) for k, v in config.params.items() if k.startswith("rank:")),
                    key=lambda kv: (kv[1], kv[0]),
                )
            )
            if base_order is None:
                base_order = order
            elif order != base_order:
                # 找出第一个差异位置以便诊断
                for index, (a, b) in enumerate(zip(order, base_order)):
                    if a != b:
                        return GateOutcome(
                            GATE_INVARIANCE, False,
                            f"旋转 {theta:.4f} rad 后访问序在 index {index} 由 {a!r} 变 {b!r}",
                        )
                return GateOutcome(
                    GATE_INVARIANCE, False,
                    f"旋转 {theta:.4f} rad 后访问序长度变化 {len(order)} vs {len(base_order)}",
                )
        return GateOutcome(GATE_INVARIANCE, True, "8 组随机刚体变换下访问序逐元素相同")


# 已登记槽位注册表：新增槽位在此登记。本次新增 route_order（任务 3 提交二）。
# 键是槽位 id（wire 身份），进入 ProposalContext.slot_id 与 EvolutionRecord.slot_id。
SLOTS: dict[str, CandidateSlot] = {
    "swath_angle": SwathAngleSlot(),
    "route_order": RouteOrderSlot(),
}

# 默认槽位：闸门与演化循环未显式指定 slot 时解析到这里，单槽位时代行为因此不变。
DEFAULT_SLOT_ID = "swath_angle"
