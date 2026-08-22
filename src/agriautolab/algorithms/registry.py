"""按覆盖阶段与具体 ProblemKind 分区存放算法卡片。"""

from __future__ import annotations

from agriautolab.algorithms.card import AlgorithmCard
from agriautolab.contracts.enums import CoverageStage, ProblemKind
from agriautolab.contracts.errors import AlgorithmRegistrationError


class AlgorithmRegistry:
    def __init__(self) -> None:
        self._cards: dict[str, AlgorithmCard] = {}
        self._partitions: dict[tuple[CoverageStage, ProblemKind], list[str]] = {}

    def register(self, card: AlgorithmCard) -> None:
        if card.algorithm_id in self._cards:
            raise AlgorithmRegistrationError(f"重复算法：{card.algorithm_id}")
        self._cards[card.algorithm_id] = card
        for problem_kind in sorted(card.supported_problem_kinds, key=lambda item: item.value):
            key = (card.stage, problem_kind)
            self._partitions.setdefault(key, []).append(card.algorithm_id)
            self._partitions[key].sort()

    def get(self, algorithm_id: str) -> AlgorithmCard:
        try:
            return self._cards[algorithm_id]
        except KeyError as error:
            raise KeyError(f"未知算法：{algorithm_id}") from error

    def compatible(self, stage: CoverageStage, problem_kind: ProblemKind) -> tuple[AlgorithmCard, ...]:
        ids = self._partitions.get((stage, problem_kind), [])
        return tuple(self._cards[algorithm_id] for algorithm_id in ids)
