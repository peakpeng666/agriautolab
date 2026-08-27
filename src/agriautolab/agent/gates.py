"""Four-gate candidate filter: contract, validation, determinism, invariance."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable, Mapping

from agriautolab.agent.sandbox import SandboxViolation
from agriautolab.contracts.problem import CoverageProblem
from agriautolab.contracts.protocol import BenchmarkProtocol
from agriautolab.contracts.vehicle import VehicleSpec
from agriautolab.pipeline.config import PipelineConfig
from agriautolab.pipeline.run import run_pipeline

if TYPE_CHECKING:
    # Lazy import to avoid circular dependency.
    from agriautolab.agent.slots import CandidateSlot

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


def _default_slot(slot: CandidateSlot | None) -> CandidateSlot:
    """闸门使用的槽位：显式传入优先，否则取注册表默认槽位（swath_angle）。"""
    from agriautolab.agent.slots import DEFAULT_SLOT_ID, SLOTS

    return slot if slot is not None else SLOTS[DEFAULT_SLOT_ID]


def compile_candidate(source_code: str) -> HeuristicFn:
    """沙箱编译并提取契约函数（默认槽位）。任何违规（语法/禁令/缺函数/签名不符）当场抛。"""
    return _default_slot(None).compile(source_code)


def principal_angle_of(problem: CoverageProblem, vehicle: VehicleSpec) -> float:
    """地块自由区域的 PCA 主轴角（swath 槽位语义；实现迁至 slots.py，此处保留兼容入口）。"""
    from agriautolab.agent.slots import principal_angle_of as slot_principal_angle_of

    return slot_principal_angle_of(problem, vehicle)


def candidate_config(angle_rad: float) -> PipelineConfig:
    """候选的评估配置：候选只占用 swath 槽位（fixed_angle + 导出角），其余槽位固定。"""
    from agriautolab.agent.slots import candidate_config as slot_candidate_config

    return slot_candidate_config(angle_rad)


def contract_gate(source_code: str, *, slot: CandidateSlot | None = None) -> tuple[HeuristicFn | None, GateOutcome]:
    """第一道：能过沙箱编译、契约函数存在且签名正确、典型输入下返回有限偏移。"""
    from agriautolab.agent.slots import reference_problem, reference_vehicle

    resolved = _default_slot(slot)
    try:
        function = resolved.compile(source_code)
        resolved.probe_value(function, reference_problem(), reference_vehicle())
    except (SandboxViolation, ValueError, TypeError) as error:
        return None, GateOutcome(GATE_CONTRACT, False, f"{type(error).__name__}: {error}")
    return function, GateOutcome(GATE_CONTRACT, True, "沙箱编译通过，契约签名正确，偏移有限")


def validation_gate(function: HeuristicFn, problem: CoverageProblem, vehicle: VehicleSpec,
                    protocol: BenchmarkProtocol, *, slot: CandidateSlot | None = None,
                    run: Callable = run_pipeline) -> GateOutcome:
    """第二道：产出路径必须过独立 PathValidator。不通过即淘汰，不做就地修补。

    run 是 keyword-only 的运行函数（默认 run_pipeline），用于在评估计数场景下
    注入打点过的执行器；旧调用不传 run 时行为逐位不变。
    """
    try:
        config = _default_slot(slot).build_config(function, problem, vehicle)
        result = run(problem, vehicle, config, protocol)
    except Exception as error:  # noqa: BLE001 -- 闸门把一切失败转为淘汰记录（保留原因），不让循环崩溃
        return GateOutcome(GATE_VALIDATION, False, f"{type(error).__name__}: {error}")
    if result.objectives is None:
        return GateOutcome(GATE_VALIDATION, False, f"校验拒绝：{result.validation.failure_reason}")
    return GateOutcome(GATE_VALIDATION, True, f"校验通过，目标 {result.objectives.as_tuple()}")


def determinism_gate(function: HeuristicFn, problem: CoverageProblem, vehicle: VehicleSpec,
                     protocol: BenchmarkProtocol, *, slot: CandidateSlot | None = None,
                     run: Callable = run_pipeline) -> GateOutcome:
    """第三道：同一输入跑两次，目标向量与路径序列化逐位相同。

    run 是 keyword-only 的运行函数（默认 run_pipeline），用于在评估计数场景下
    注入打点过的执行器；旧调用不传 run 时行为逐位不变。
    """
    try:
        config = _default_slot(slot).build_config(function, problem, vehicle)
        first = run(problem, vehicle, config, protocol)
        second = run(problem, vehicle, config, protocol)
    except Exception as error:  # noqa: BLE001 -- 同上
        return GateOutcome(GATE_DETERMINISM, False, f"{type(error).__name__}: {error}")
    if first.objectives is None or second.objectives is None:
        return GateOutcome(GATE_DETERMINISM, False, "目标向量缺失（校验未通过）")
    if first.objectives != second.objectives or first.path.model_dump_json() != second.path.model_dump_json():
        return GateOutcome(GATE_DETERMINISM, False, "两次运行不一致")
    return GateOutcome(GATE_DETERMINISM, True, "两次运行逐位相同")


def invariance_gate(function: HeuristicFn, problem: CoverageProblem, vehicle: VehicleSpec,
                    protocol: BenchmarkProtocol, rng, *, slot: CandidateSlot | None = None) -> GateOutcome:
    """第四道：随机刚体变换下偏移不变（特征旋转不变，偏移按构造应当继承）。"""
    return _default_slot(slot).invariance_check(function, problem, vehicle, rng)
