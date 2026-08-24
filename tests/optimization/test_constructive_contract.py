"""公共 constructive engine 的运行时契约。"""

import pytest

from agriautolab.optimization import construct_solution
from agriautolab.optimization.constructive import ConstructionError


class _OneStepProblem:
    def initial_state(self):
        return False

    def is_complete(self, state):
        return state is True

    def feasible_actions(self, state):
        return ("finish",)

    def apply_action(self, state, action):
        return True

    def finalize(self, state):
        return "done"


def test_constructive_engine_normalizes_invalid_score_type_to_domain_error() -> None:
    class InvalidScoreHeuristic:
        heuristic_id = "invalid-score"

        def score(self, state, action):
            return "not-a-number"

    with pytest.raises(ConstructionError, match="返回不可用评分"):
        construct_solution(_OneStepProblem(), InvalidScoreHeuristic())


def test_constructive_engine_rejects_score_float_overflow() -> None:
    class OverflowingScore:
        def __float__(self):
            raise OverflowError("cannot represent")

    class OverflowHeuristic:
        heuristic_id = "overflow-score"

        def score(self, state, action):
            return OverflowingScore()

    with pytest.raises(ConstructionError, match="返回不可用评分"):
        construct_solution(_OneStepProblem(), OverflowHeuristic())
