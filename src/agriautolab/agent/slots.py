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
from agriautolab.selection.features.extract import extract_instance_features
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

    # 试调用输入的**模板**。每次调用都必须传新副本（见 _probe_inputs）：
    # 沙箱不禁止候选改写入参，`candidate.pop("distance_norm")` 会永久污染类级常量，
    # 之后所有候选都收到被掏空的映射——于是「候选能否通过」取决于它在提议序列里
    # 排第几，而不是它自己写得对不对。
    _PROBE_STATE_TEMPLATE: dict[str, float] = {"visited_count": 1.0, "remaining_count": 3.0}
    _PROBE_CANDIDATE_TEMPLATE: dict[str, float] = {"distance_norm": 1.0, "axis_offset_norm": 0.0}

    @classmethod
    def _probe_inputs(cls) -> tuple[dict[str, float], dict[str, float]]:
        """每次探针调用取一对全新字典，候选改写不了模板。"""
        return dict(cls._PROBE_STATE_TEMPLATE), dict(cls._PROBE_CANDIDATE_TEMPLATE)

    def compile(self, source: str) -> HeuristicFn:
        """沙箱编译并提取契约函数 next_swath_score(state, candidate) -> float。

        试调用：`function(_PROBE_STATE, _PROBE_CANDIDATE)`。

        **任何**异常都转成 SandboxViolation，不只是 TypeError。此前只捕 TypeError，
        于是候选跑出别的异常时会穿透 compile 与 contract_gate，**在写任何账本记录
        之前终止整个 evolve_pool**。最小复现：探针的 `axis_offset_norm` 恰为 0.0，
        候选写 `1.0 / candidate["axis_offset_norm"]` 就抛 ZeroDivisionError。
        候选的运行期失败必须是"这个候选被淘汰"，不能是"实验崩了"。
        """
        namespace = run_sandboxed(source)
        function = namespace.get(self.contract_function)
        if not callable(function):
            raise SandboxViolation(f"候选代码必须定义顶层函数 {self.contract_function}(state, candidate)")
        state, candidate = self._probe_inputs()
        try:
            function(state, candidate)
        except TypeError as error:
            raise SandboxViolation(
                f"契约函数签名不符（应接受两个 dict 形参）：{error}"
            ) from error
        except Exception as error:  # noqa: BLE001 -- 插件边界；原异常经 chaining 保留
            raise SandboxViolation(
                f"候选在契约探针上抛出 {type(error).__name__}：{error}"
            ) from error
        return function

    def probe_value(self, function: HeuristicFn, problem: CoverageProblem,
                    vehicle: VehicleSpec) -> float:
        """在参考输入上取一次分数并收敛为有限 float。

        **求值与 float 转换必须在同一个保护块里。** 此前 `float(value)` 在 try 之外，
        于是候选返回 `10 ** 10000` 时两次函数调用都成功，却在转换处抛 OverflowError；
        而 `contract_gate` 只捕 SandboxViolation / ValueError / TypeError，
        该异常仍会穿透 `evolve_pool` 并在写账本记录之前终止实验。
        """
        state, candidate = self._probe_inputs()
        try:
            value = function(state, candidate)
            coerced = float(value)
        except Exception as error:  # noqa: BLE001 -- 同 compile：候选失败=淘汰，不是崩实验
            raise ValueError(f"候选探针失败：{type(error).__name__}: {error}") from error
        if not math.isfinite(coerced):
            raise ValueError(f"候选返回非有限分数：{value!r}")
        return coerced

    def _geometry_for(self, problem: CoverageProblem, vehicle: VehicleSpec):
        """跑上游三阶段，返回 (swath_id -> 端点, 地块质心, 主轴法向)。

        Do not call run_pipeline here — it would corrupt the anytime evaluation counter.
        """
        from agriautolab.algorithms.headland.uniform_headland import ConstantWidthHeadland
        from agriautolab.algorithms.decomposition.boustrophedon_cells import BoustrophedonDecomposition
        from agriautolab.algorithms.swath.principal_axis import PrincipalAxisSwathGenerator
        from agriautolab.algorithms.route.constructive_order import endpoints_of
        from agriautolab.geometry.validate import polygon_from_spec
        from agriautolab.geometry.robust import robust_union
        from agriautolab.algorithms.swath.principal_axis import principal_axis

        # 上游分解必须与返回的 PipelineConfig 声明的 decomposition 一致。
        # 曾用 BoustrophedonDecomposition 烘焙 rank 却返回 no_decomposition：
        # 有障碍的田上 BCD 会切出不同 cell 布局，重放时条带数量与序号 id 都变，
        # 于是 RankedSwathOrderPlanner 要么报缺 rank 键，要么把 rank 套到
        # 几何上毫不相干的条带上。真值测试 test_baked_ranks_match_replayed_swaths
        # 在有障碍田上钉住这一点。
        cells = BoustrophedonDecomposition().run(problem)
        headland = ConstantWidthHeadland(8.0).run(cells)
        mains = tuple(part for cell in headland.cells for part in cell.main_field)
        swaths = PrincipalAxisSwathGenerator().run(
            mains, working_width_m=vehicle.working_width_m, problem=problem,
        )
        if not swaths.swaths:
            raise ValueError("_geometry_for: 参考田未产生条带，构造空访问序失败")

        # 主轴法向（旋转不变键的来源）
        field = polygon_from_spec(problem.field)
        obstacles = tuple(
            polygon_from_spec(spec) for spec in sorted(problem.obstacles, key=lambda item: item.geometry_id)
        )
        scale_hint = max(field.bounds[2] - field.bounds[0], field.bounds[3] - field.bounds[1], 1.0)
        free = field.difference(robust_union(obstacles, scale_hint=scale_hint)) if obstacles else field
        ux, uy = principal_axis(free if free.geom_type == "Polygon" else free.convex_hull)

        # 质心用真正的多边形质心，与主轴取自同一 free 几何。
        # 曾用外环顶点算术平均：闭合点被重复计数，且插入共线冗余顶点就会改变结果
        # ——60×40 矩形写成 (0,0)…(0,0) 时得 (24,16) 而非 (30,20)。该值同时是
        # distance_norm 的初始出口与 axis_offset_norm 的原点，因此等价的多边形
        # 编码会烘焙出不同的 rank。test_field_centroid_is_encoding_independent 钉住。
        centroid_point = free.centroid
        cx, cy = float(centroid_point.x), float(centroid_point.y)

        # 端点原样返回：进入/离开哪一端由访问序奇偶在 RouteOrderProblem 内部决定
        # （REVERSE 从 points[0] 出，不是 points[-1]）。
        # 返回**主轴**而非法向：法向由主轴派生，而主轴的符号规范化
        # （canonical_direction，principal_axis 内部已做）是 invariance_check
        # 必须复现的语义，把它留在调用方才能忠实模拟真实构建路径。
        endpoints = {s.swath_id: endpoints_of(s) for s in swaths.swaths}
        return endpoints, (cx, cy), (ux, uy)

    @staticmethod
    def _normal_of(axis: tuple[float, float]) -> tuple[float, float]:
        """主轴旋转 90° 得法向。"""
        return (-axis[1], axis[0])

    def _plan(self, function: HeuristicFn, problem: CoverageProblem,
              vehicle: VehicleSpec) -> tuple[str, ...]:
        """上游几何 + 候选决策 → 访问序。"""
        endpoints, centroid, axis = self._geometry_for(problem, vehicle)
        return self._order_for(function, endpoints, vehicle=vehicle,
                               centroid=centroid, normal=self._normal_of(axis))

    @staticmethod
    def _order_for(function: HeuristicFn, endpoints, *, vehicle: VehicleSpec,
                   centroid, normal) -> tuple[str, ...]:
        """给定条带端点几何，直接求候选的访问序（不经过上游生成器）。

        `invariance_check` 用它把候选行为与 swath 生成器的行为**隔离**开，
        理由见该方法的 docstring。
        """
        from agriautolab.algorithms.route.constructive_order import (
            RouteOrderProblem, candidate_features, project_state,
        )
        from agriautolab.optimization.constructive import construct_solution

        problem_obj = RouteOrderProblem(
            endpoints,
            min_turning_radius_m=vehicle.min_turning_radius_m,
            working_width_m=vehicle.working_width_m,
            field_centroid=centroid,
            principal_normal=normal,
        )
        total = len(endpoints)

        class _H:
            heuristic_id: str = "candidate"

            def score(self, state, action) -> float:
                # 动作过 candidate_features 剥掉 swath_id：那是上游按坐标分配的序号，
                # 用它排序等于用坐标 artifact 排序，能绕过全部不变性要求。
                return float(function(
                    project_state(state, total_swath_count=total),
                    candidate_features(action),
                ))

        return construct_solution(problem_obj, _H())

    def build_config(self, function: HeuristicFn, problem: CoverageProblem,
                     vehicle: VehicleSpec) -> PipelineConfig:
        """把候选选出的访问序烘焙进 params["rank:<swath_id>"]。"""
        visit_order = self._plan(function, problem, vehicle)
        rank_params: dict[str, float] = {
            f"rank:{swath_id}": float(index)
            for index, swath_id in enumerate(visit_order)
        }
        params = {"headland_width_m": 8.0, **rank_params}
        return PipelineConfig(
            decomposition="boustrophedon_cells", headland="uniform_headland",
            swath="principal_axis", route="ranked_swath_order", path="dubins_transit",
            params=params,
        )

    # 分数比较容差：绝对项对付接近 0 的分数，相对项对付候选自带的任意量纲。
    # 候选契约**不限定分数量级**，`1e9 * distance_norm` 与 `distance_norm` 是同一个
    # 构造决策（正数缩放不改变 argmin），但纯绝对容差会把前者的 ~1e-5 残差判为漂移。
    _SCORE_ATOL = 1e-9
    _SCORE_RTOL = 1e-9

    def _scores_along(self, function: HeuristicFn, endpoints, order, *, vehicle,
                      centroid, normal) -> list[dict[str, float]]:
        """沿给定访问序逐步取候选对**每个可行动作**的评分。

        返回 [ {swath_id: score} ]，第 k 项对应状态 order[:k]。
        """
        from agriautolab.algorithms.route.constructive_order import (
            RouteOrderProblem, candidate_features, project_state,
        )

        problem_obj = RouteOrderProblem(
            endpoints,
            min_turning_radius_m=vehicle.min_turning_radius_m,
            working_width_m=vehicle.working_width_m,
            field_centroid=centroid,
            principal_normal=normal,
        )
        total = len(endpoints)
        out: list[dict[str, float]] = []
        for k in range(len(order)):
            state = tuple(order[:k])
            # 每个动作都现造一份投影状态，与真实构造路径逐调用重算一致。
            # 复用同一个 dict 会让改写 state 的候选在闸门里与在 build_config 里
            # 表现不同——例如自增 visited_count 的候选在真实路径上产生全并列、
            # 在闸门里却产生递增分数，于是绕过并列拒绝、通过不变性比较，
            # 而实际部署的路线仍完全由 swath_id 决定。
            out.append({
                action["swath_id"]: float(function(
                    project_state(state, total_swath_count=total),
                    candidate_features(action),
                ))
                for action in problem_obj.feasible_actions(state)
            })
        return out

    def invariance_check(self, function: HeuristicFn, problem: CoverageProblem,
                         vehicle: VehicleSpec, rng) -> GateOutcome:
        """8 组随机刚体变换下，候选对每个可行动作的**评分**保持不变。

        与 SwathAngleSlot 的 8×3 uniform 消耗模式一致（theta/tx/ty 顺序）。

        **变换施加在条带几何上，而不是地块上**——这是本方法与初版最关键的差别，
        # Upstream geometric property:

        `PrincipalAxisSwathGenerator` 在**地块**被旋转时并不是刚体等变的。当旋转
        把 PCA 主轴推过 `canonical_direction` 的半平面边界，扫掠方向与法向一起
        翻转，`_sweep.py` 于是从地块的另一侧开始铺条带，**残余余量随之换到另一端**
        # strip positions physically shift (not just re-indexed). Example on a 90×50 field:
        基线条带中心 y = 12.85 / 22.55 / 32.25 / 37.15（间隔 9.7, 9.7, 4.9），
        旋转 1.5857 rad 后逆变换回原坐标是 12.85 / 17.75 / 27.45 / 37.15
        （间隔 4.9, 9.7, 9.7）。两组条带集合根本不是同一批几何对象。

        若照初版那样"旋转地块 → 重跑上游 → 比访问序"，闸门测的就是**生成器的
        等变性**而不是候选的不变性，最近邻这类几何等变的合法候选会被误拒。
        本闸门的职责是拒绝使用非不变特征的候选，不是给 swath 生成器打分。
        因此：上游只跑一次拿到条带集合，随后把**端点、质心、主轴法向一起**做
        刚体变换，再看同一批条带的访问序是否逐元素相同。

        基线取**未变换**的原几何，在循环之前算好。初版把第一次随机变换的结果当
        基线，于是从不与原始坐标下的路线比较——某个只在原始坐标触发分支的候选，
        可以让原始路线与八个扰动路线全都不同却照样过闸。

        生成器本身的非等变性是真实的、已记录的局限，属于上游 swath 层的议题，
        不在本槽位范围内。

        **判定量是评分，不是访问序**——这是第二个关键选择。贪心构造在**评分并列**
        时由稳定枚举序决胜，而刚体变换会引入 ~1e-16 的舍入任意打破并列；一旦某步
        # symmetric reversal causes route divergence. Regular strip spacing is common in CPP (
        90×50 参考田上，第 1 步到两条条带的距离精确同为 9.7 m），因此"比较访问序"
        会让最近邻这类完全合法的候选被随机误拒。

        本闸门要拒的是**使用非不变特征的候选**（例如读原始角度或绝对坐标）。
        那类候选的评分本身就会随变换改变，因此逐动作比较评分既直接命中该性质，
        又对并列免疫。并列翻转不改变任何一个动作的分数，只改变谁被选中。
        """
        from agriautolab.algorithms.swath._sweep import canonical_direction

        try:
            endpoints, centroid, axis = self._geometry_for(problem, vehicle)
            normal = self._normal_of(axis)
            base_order = self._order_for(function, endpoints, vehicle=vehicle,
                                         centroid=centroid, normal=normal)
            base_scores = self._scores_along(function, endpoints, base_order,
                                             vehicle=vehicle, centroid=centroid, normal=normal)
        except Exception as error:  # noqa: BLE001 -- 闸门把一切失败转为淘汰记录
            return GateOutcome(GATE_INVARIANCE, False, f"基线构造失败：{type(error).__name__}: {error}")

        # 退化候选：每一步都把所有可行动作评成同分，等于完全不做决策——访问序
        # 由 feasible_actions 的 swath_id 稳定枚举序决定，而那是上游按坐标分配的
        # 序号。剥掉 swath_id 只堵住了「读」的通道，同分仍能把选择**委托**给它。
        # 更糟的是：条带 id 在扫掠方向翻转时会反转空间对应，于是这种候选可能
        # 表现出纯粹由坐标 artifact 造成的「互补性」，污染 ΔHV 归因。
        for step_index, step in enumerate(base_scores):
            if len(step) < 2:
                continue
            best = min(step.values())
            tied = [swath_id for swath_id, value in step.items() if value == best]
            if len(tied) > 1:
                return GateOutcome(
                    GATE_INVARIANCE, False,
                    f"第 {step_index} 步的最优分并列于 {sorted(tied)!r}：实际选中哪一条"
                    "由 feasible_actions 的 swath_id 枚举序决定，而那是上游按坐标分配的"
                    "序号——候选在这一步没有做出不变量意义上的决策",
                )

        for _ in range(8):
            theta = float(rng.uniform(-math.pi, math.pi))
            tx, ty = float(rng.uniform(-100.0, 100.0)), float(rng.uniform(-100.0, 100.0))
            cos_t, sin_t = math.cos(theta), math.sin(theta)

            def move(point: tuple[float, float]) -> tuple[float, float]:
                return (tx + cos_t * point[0] - sin_t * point[1],
                        ty + sin_t * point[0] + cos_t * point[1])

            moved_endpoints = {
                swath_id: (move(start), move(end)) for swath_id, (start, end) in endpoints.items()
            }
            # 质心随几何平移+旋转；法向只旋转（方向量不平移）。
            #
            # 法向必须再过一次 canonical_direction，复现真实构建路径：
            # _geometry_for 的法向来自 principal_axis，而后者 return 的就是
            # canonical_direction(...)——方向被强制进右半平面（ux>0）。当旋转把主轴
            # 带过该边界，真实构建拿到的是 -R·axis 因而是 -R·normal，而不是 R·normal。
            # 只旋转不规范化的话，闸门永远不会走到符号翻转那一支，于是**有符号的**
            # 有符号投影在闸门里看着不变、在真实构建里却整体反号，
            # 依赖它的候选优先方向被悄悄反转却照样过闸。
            moved_centroid = move(centroid)
            rotated_axis = (cos_t * axis[0] - sin_t * axis[1],
                            sin_t * axis[0] + cos_t * axis[1])
            canonical_ux, canonical_uy = canonical_direction(*rotated_axis)
            moved_normal = (-canonical_uy, canonical_ux)
            try:
                # 沿**同一条基线访问序**取分：比较的是同状态同动作下的评分，
                # 与变换后候选自己会不会选同一条路线无关。
                moved_scores = self._scores_along(
                    function, moved_endpoints, base_order,
                    vehicle=vehicle, centroid=moved_centroid, normal=moved_normal,
                )
            except Exception as error:  # noqa: BLE001 -- 闸门把一切失败转为淘汰记录
                return GateOutcome(GATE_INVARIANCE, False, f"{type(error).__name__}: {error}")

            for step, (base_step, moved_step) in enumerate(zip(base_scores, moved_scores)):
                if set(base_step) != set(moved_step):
                    return GateOutcome(
                        GATE_INVARIANCE, False,
                        f"刚体变换（theta={theta:.4f} rad）后第 {step} 步可行动作集合变化",
                    )
                for swath_id, base_value in base_step.items():
                    moved_value = moved_step[swath_id]
                    drift = abs(moved_value - base_value)
                    allowed = self._SCORE_ATOL + self._SCORE_RTOL * max(
                        abs(base_value), abs(moved_value),
                    )
                    if not math.isfinite(drift) or drift > allowed:
                        return GateOutcome(
                            GATE_INVARIANCE, False,
                            f"刚体变换（theta={theta:.4f} rad）后第 {step} 步对 "
                            f"{swath_id!r} 的评分漂移 {drift:.3e}（容许 {allowed:.3e}）",
                        )
        return GateOutcome(
            GATE_INVARIANCE, True,
            "8 组随机刚体变换下逐状态逐动作评分不变（< 1e-9）",
        )


# 已登记槽位注册表：新增槽位在此登记。本次新增 route_order（任务 3 提交二）。
# 键是槽位 id（wire 身份），进入 ProposalContext.slot_id 与 EvolutionRecord.slot_id。
SLOTS: dict[str, CandidateSlot] = {
    "swath_angle": SwathAngleSlot(),
    "route_order": RouteOrderSlot(),
}

# 默认槽位：闸门与演化循环未显式指定 slot 时解析到这里，单槽位时代行为因此不变。
DEFAULT_SLOT_ID = "swath_angle"
