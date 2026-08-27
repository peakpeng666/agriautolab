"""评审硬门语义回归（原 tests/evidence/test_atomic_and_review_semantics.py 的 review 部分）。"""

from agriautolab.agent.reviewer import ReviewVerdict, final_refuted, majority_refuted


def test_hard_verdict_cannot_be_outvoted():
    verdicts = (
        ReviewVerdict(True, ("正确性探针炸了",), hard=True),
        ReviewVerdict(False, ()),
        ReviewVerdict(False, ()),
    )
    assert majority_refuted(verdicts) is False  # 旧语义：1/3 被翻案
    assert final_refuted(verdicts) is True  # 新语义：硬否决不可翻案


def test_advisory_majority_still_works_and_tie_refutes():
    advisory = (ReviewVerdict(False, ()), ReviewVerdict(False, ()), ReviewVerdict(False, ()))
    assert final_refuted(advisory) is False
    two_refuted = (ReviewVerdict(True, ()), ReviewVerdict(True, ()), ReviewVerdict(False, ()))
    assert final_refuted(two_refuted) is True
    tie = (ReviewVerdict(True, ()), ReviewVerdict(False, ()))
    assert final_refuted(tie) is True  # 平票按否决（保守）
