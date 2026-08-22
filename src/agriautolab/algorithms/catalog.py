"""Block B 算法目录：五阶段 × 每阶段少量正交候选，全部登记进 AlgorithmRegistry。

池子的成员是 12 个（§3.2 下界，不超额）：多塞算法不增加互补性——
240 实例 × 12 配置实测单目标 VBS−SBS gap 只有 0.0299，覆盖规划策略嵌套支配，
往池子里加算法长不出 SAT 那种范式互补。把前沿撑开的机制交给 Agent 层（agent/）。
"""

from __future__ import annotations

from agriautolab.algorithms.card import AlgorithmCard
from agriautolab.algorithms.registry import AlgorithmRegistry
from agriautolab.contracts.enums import AlgorithmMaturity, AlgorithmSourceType, CoverageStage, ProblemKind

_COVERAGE = frozenset({ProblemKind.POLYGON_COVERAGE_2D})


def build_catalog() -> AlgorithmRegistry:
    """构建一个新的算法目录。每次调用返回独立实例，避免可变全局状态。"""
    registry = AlgorithmRegistry()
    cards = (
        # ---- decomposition ----
        AlgorithmCard(
            algorithm_id="no_decomposition", name="No decomposition", stage=CoverageStage.DECOMPOSITION,
            supported_problem_kinds=_COVERAGE, maturity=AlgorithmMaturity.BASELINE,
            source_type=AlgorithmSourceType.INTERNAL,
        ),
        AlgorithmCard(
            algorithm_id="boustrophedon_cells", name="Boustrophedon cell decomposition",
            stage=CoverageStage.DECOMPOSITION, supported_problem_kinds=_COVERAGE,
            maturity=AlgorithmMaturity.BASELINE, source_type=AlgorithmSourceType.PAPER_REPRODUCTION,
            source_reference="Choset & Pignon, Coverage Path Planning: The Boustrophedon Decomposition (1998)",
        ),
        # ---- headland ----
        AlgorithmCard(
            algorithm_id="no_headland", name="Identity headland", stage=CoverageStage.HEADLAND,
            supported_problem_kinds=_COVERAGE, maturity=AlgorithmMaturity.BASELINE,
            source_type=AlgorithmSourceType.INTERNAL,
        ),
        AlgorithmCard(
            algorithm_id="uniform_headland", name="Uniform constant-width headland",
            stage=CoverageStage.HEADLAND, supported_problem_kinds=_COVERAGE,
            maturity=AlgorithmMaturity.BASELINE, source_type=AlgorithmSourceType.INTERNAL,
        ),
        # ---- swath ----
        AlgorithmCard(
            algorithm_id="fixed_angle", name="Fixed sweep angle", stage=CoverageStage.SWATH,
            supported_problem_kinds=_COVERAGE, maturity=AlgorithmMaturity.BASELINE,
            source_type=AlgorithmSourceType.INTERNAL,
        ),
        AlgorithmCard(
            algorithm_id="principal_axis", name="Boundary PCA principal axis", stage=CoverageStage.SWATH,
            supported_problem_kinds=_COVERAGE, maturity=AlgorithmMaturity.BASELINE,
            source_type=AlgorithmSourceType.INTERNAL,
        ),
        AlgorithmCard(
            algorithm_id="min_width", name="Minimum-width sweep direction", stage=CoverageStage.SWATH,
            supported_problem_kinds=_COVERAGE, maturity=AlgorithmMaturity.BASELINE,
            source_type=AlgorithmSourceType.INTERNAL,
        ),
        AlgorithmCard(
            algorithm_id="longest_edge", name="Longest polygon edge direction", stage=CoverageStage.SWATH,
            supported_problem_kinds=_COVERAGE, maturity=AlgorithmMaturity.BASELINE,
            source_type=AlgorithmSourceType.INTERNAL,
        ),
        AlgorithmCard(
            algorithm_id="row_aligned", name="Row-aligned sweep", stage=CoverageStage.SWATH,
            supported_problem_kinds=_COVERAGE, maturity=AlgorithmMaturity.BASELINE,
            source_type=AlgorithmSourceType.INTERNAL,
        ),
        # ---- route ----
        AlgorithmCard(
            algorithm_id="boustrophedon_order", name="Sequential boustrophedon order",
            stage=CoverageStage.ROUTE, supported_problem_kinds=_COVERAGE,
            maturity=AlgorithmMaturity.BASELINE, source_type=AlgorithmSourceType.INTERNAL,
        ),
        AlgorithmCard(
            algorithm_id="skip_one_order", name="Skip-one order", stage=CoverageStage.ROUTE,
            supported_problem_kinds=_COVERAGE, maturity=AlgorithmMaturity.BASELINE,
            source_type=AlgorithmSourceType.INTERNAL,
        ),
        AlgorithmCard(
            algorithm_id="rural_postman_greedy", name="Greedy Rural Postman order",
            stage=CoverageStage.ROUTE, supported_problem_kinds=_COVERAGE,
            maturity=AlgorithmMaturity.BASELINE, source_type=AlgorithmSourceType.PAPER_REPRODUCTION,
            source_reference="管梅谷 (1962) 中国邮递员问题；RPP 弧路径建模（非 TSP）",
        ),
        # ---- path ----
        AlgorithmCard(
            algorithm_id="dubins_transit", name="Dubins transit connectors", stage=CoverageStage.PATH,
            supported_problem_kinds=_COVERAGE, maturity=AlgorithmMaturity.BASELINE,
            source_type=AlgorithmSourceType.PAPER_REPRODUCTION,
            source_reference="Dubins (1957); Shkel & Lumelsky (2001) 六字分类",
        ),
        AlgorithmCard(
            algorithm_id="reeds_shepp_transit", name="Reeds-Shepp transit connectors (allows reverse)",
            stage=CoverageStage.PATH, supported_problem_kinds=_COVERAGE,
            maturity=AlgorithmMaturity.RESEARCH,
            source_type=AlgorithmSourceType.PAPER_REPRODUCTION,
            source_reference="Reeds & Shepp (1990)。已实现 CSC/CCC 六族的符号长度字 + 48 候选；"
                             "CCCC/CCSC/CCSCC 未实现：可行且不劣于 Dubins，不保证全局最优",
        ),
    )
    for card in cards:
        registry.register(card)
    return registry
