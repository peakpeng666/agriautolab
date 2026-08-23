"""Agent 层：沙箱静态扫描（真值 15）、演化循环确定性（真值 16）与四道闸。"""

import numpy as np
import pytest

from conftest import REVERSE_COST_TEST_SPEC

from agriautolab.agent.evolve import Instance, KeepRule, evolve_pool
from agriautolab.agent.gates import (
    contract_gate, determinism_gate, invariance_gate, validation_gate,
)
from agriautolab.agent.ledger import EvolutionLedger, EvolutionRecord
from agriautolab.agent.proposer import MOCK_CANDIDATES, LLMProposer, MockProposer, ProposalContext
from agriautolab.agent.reviewer import (
    DEFAULT_REVIEWERS, majority_refuted,
)
from agriautolab.agent.sandbox import SandboxViolation, run_sandboxed, scan_source
from agriautolab.contracts.enums import CoverageStage, CoverageTarget
from agriautolab.contracts.geometry import Point, PolygonSpec
from agriautolab.contracts.problem import CoverageProblem
from agriautolab.contracts.protocol import BenchmarkProtocol
from agriautolab.contracts.rows import RowStructure
from agriautolab.contracts.vehicle import VehicleSpec
from agriautolab.pareto.hypervolume import analytic_reference
from agriautolab.pipeline.config import PipelineConfig


def make_instance(row_direction: float | None = 0.9) -> Instance:
    field = PolygonSpec(geometry_id="field", exterior=(
        Point(x=0.0, y=0.0), Point(x=80.0, y=0.0), Point(x=80.0, y=40.0),
        Point(x=0.0, y=40.0), Point(x=0.0, y=0.0),
    ))
    rows = None
    if row_direction is not None:
        rows = RowStructure(direction_rad=row_direction, spacing_m=2.5, crossable=True, crossing_penalty=10.0)
    problem = CoverageProblem(problem_id="agent", field=field, row_structure=rows)
    vehicle = VehicleSpec(working_width_m=9.7, body_width_m=2.0, min_turning_radius_m=3.0)
    return Instance(problem=problem, vehicle=vehicle)


def make_protocol(instance: Instance) -> BenchmarkProtocol:
    return BenchmarkProtocol(
        protocol_id="agent", coverage_target=CoverageTarget.ORIGINAL_FIELD,
        coverage_threshold=0.0, hypervolume_reference=analytic_reference(instance.problem, instance.vehicle),
        reverse_cost=REVERSE_COST_TEST_SPEC,
    )


def base_pool() -> list[PipelineConfig]:
    return [
        PipelineConfig("no_decomposition", "uniform_headland", "min_width", "boustrophedon_order",
                       "dubins_transit", {"headland_width_m": 8.0}),
        PipelineConfig("no_decomposition", "uniform_headland", "principal_axis", "skip_one_order",
                       "dubins_transit", {"headland_width_m": 8.0}),
    ]


# ---- 真值 15：沙箱静态扫描 ----

@pytest.mark.parametrize("source", [
    "import math\ndef f(x):\n    return 0.0\n",
    "def swath_angle_offset_rad(features):\n    return open('/etc/passwd') and 0.0\n",
    "def swath_angle_offset_rad(features):\n    return eval('0.0')\n",
    "def swath_angle_offset_rad(features):\n    return __import__('math').pi\n",
    "def swath_angle_offset_rad(features):\n    return (1).__class__.__name__ == 'int' and 0.0\n",
    "from math import pi\ndef swath_angle_offset_rad(features):\n    return 0.0\n",
])
def test_sandbox_rejects_forbidden_constructs(source: str) -> None:
    with pytest.raises(SandboxViolation):
        scan_source(source)


def test_sandbox_runs_whitelisted_code() -> None:
    namespace = run_sandboxed(
        "def swath_angle_offset_rad(features):\n"
        "    return max(0.0, min(math.pi / 4.0, 0.1 * features.get('elongation', 1.0)))\n"
    )
    assert namespace["swath_angle_offset_rad"]({"elongation": 3.0}) > 0.0


def test_sandbox_hides_non_whitelisted_builtins() -> None:
    # pow 不在静态禁令表里（静态层不拦），但不在白名单里——运行时必须 NameError。
    # 这证明白名单是真实的执行约束，不只是扫描器的说辞。
    namespace = run_sandboxed("def probe():\n    return pow(2, 3)\n")
    with pytest.raises(NameError):
        namespace["probe"]()


# ---- 四道闸 ----

def test_contract_gate_accepts_mock_candidates_and_rejects_bad_ones() -> None:
    for candidate in MOCK_CANDIDATES:
        function, outcome = contract_gate(candidate.source_code)
        assert outcome.passed, outcome.detail
        assert function is not None
    broken, outcome = contract_gate("def other_name(features):\n    return 0.0\n")
    assert broken is None and not outcome.passed


def test_validation_determinism_invariance_gates_pass_for_sound_candidate() -> None:
    instance = make_instance()
    protocol = make_protocol(instance)
    function, outcome = contract_gate(MOCK_CANDIDATES[2].source_code)
    assert outcome.passed
    rng = np.random.default_rng(7)
    assert validation_gate(function, instance.problem, instance.vehicle, protocol).passed
    assert determinism_gate(function, instance.problem, instance.vehicle, protocol).passed
    assert invariance_gate(function, instance.problem, instance.vehicle, protocol, rng).passed


# ---- 复核器 ----

def test_reviewers_default_to_refuted_only_with_concrete_probes() -> None:
    function, outcome = contract_gate(MOCK_CANDIDATES[1].source_code)
    assert outcome.passed
    for reviewer in DEFAULT_REVIEWERS:
        verdict = reviewer.review(MOCK_CANDIDATES[1], function)
        assert not verdict.refuted
        assert verdict.reasons          # refuted=False 必须附带具体探针结果
    assert not majority_refuted(tuple(
        reviewer.review(MOCK_CANDIDATES[1], function) for reviewer in DEFAULT_REVIEWERS
    ))


def test_majority_refuted_is_conservative_on_ties() -> None:
    from agriautolab.agent.reviewer import ReviewVerdict

    assert majority_refuted((ReviewVerdict(True, ("a",)), ReviewVerdict(False, ("b",))))
    assert not majority_refuted((ReviewVerdict(False, ("a",)), ReviewVerdict(False, ("b",))))


# ---- 真值 16：演化循环确定性 ----

def test_evolution_with_mock_proposer_is_bitwise_reproducible() -> None:
    instance = make_instance()
    protocol = make_protocol(instance)
    pool = base_pool()

    def run_once() -> str:
        ledger, kept = evolve_pool(
            pool, (instance,), proposer=MockProposer(), protocol=protocol,
            rng=np.random.default_rng(42), rounds=4, keep_rule=KeepRule.HYPERVOLUME_DELTA,
        )
        return "|".join(record.model_dump_json() for record in ledger.records), tuple(k.identity for k in kept)

    first_ledger, first_kept = run_once()
    second_ledger, second_kept = run_once()
    assert first_ledger == second_ledger
    assert first_kept == second_kept


def test_evolution_ledger_records_eliminated_candidates_too() -> None:
    """被淘汰的候选也要记——只记成功就是发表偏倚。"""

    class BrokenProposer:
        def propose(self, *, stage, context, rng):
            from agriautolab.agent.proposer import ProposalCandidate

            return ProposalCandidate(
                algorithm_id="always_broken",
                source_code="def swath_angle_offset_rad(features):\n    return open('x') and 0.0\n",
                description="静态扫描必拒",
            )

    instance = make_instance()
    protocol = make_protocol(instance)
    ledger, kept = evolve_pool(
        base_pool(), (instance,), proposer=BrokenProposer(), protocol=protocol,
        rng=np.random.default_rng(1), rounds=3,
    )
    assert kept == ()
    assert len(ledger.records) == 3
    assert all(record.gates[0].gate == "contract" and not record.gates[0].passed for record in ledger.records)
    ledger.verify()


def test_ledger_chain_breaks_on_tamper() -> None:
    ledger = EvolutionLedger()
    record = EvolutionRecord(round_index=0, algorithm_id="x", proposal_hash="0" * 64,
                             compiled=True, kept=False)
    ledger.append(record)
    ledger.verify()
    ledger._records[0] = (ledger._records[0][0], record.model_copy(update={"kept": True}))
    with pytest.raises(Exception):
        ledger.verify()


def test_llm_proposer_refuses_without_injected_client() -> None:
    proposer = LLMProposer()
    context = ProposalContext(stage=CoverageStage.SWATH, round_index=0, pool_config_ids=())
    with pytest.raises(RuntimeError, match="MockProposer"):
        proposer.propose(stage=CoverageStage.SWATH, context=context, rng=np.random.default_rng(0))
    # 提示词模板本身是可构建的（注入真模型的入口）
    assert "swath_angle_offset_rad" in proposer.build_prompt(stage=CoverageStage.SWATH, context=context)