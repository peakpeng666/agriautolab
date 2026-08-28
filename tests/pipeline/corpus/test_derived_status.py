"""derived_status：validator 事实优先于运行时归并（单一真相源，dataset-split 复核确立）。

实测背景：槽 B（no_headland+RS）在可倒车机具上 2 020 行
runstatus=not_applicable 而 failure_reason=validator_rejected:outside_area——
直接 groupby("runstatus") 会把它们读成「没跑过」。
"""

import json
from pathlib import Path

import pytest

from agriautolab.pipeline.corpus.derived_status import (
    DERIVED_STATUS_DEFINITION, derive_status, status_diff_counts,
)

SRC = Path(__file__).resolve().parents[3] / "src" / "agriautolab"


def test_validator_fact_beats_runtime_merge():
    # 零地头 carve 行：运行时归并成 not_applicable，validator 事实是 outside_area
    assert derive_status("not_applicable", "validator_rejected:outside_area") == "outside_area"
    assert derive_status("not_applicable", "validator_rejected:collision") == "collision"


def test_non_validator_statuses_pass_through():
    # ok 行没有 failure_reason；算法-机具配对/塌缩的 failure_reason 是自由文本
    assert derive_status("ok", None) == "ok"
    assert derive_status("ok", "") == "ok"
    assert derive_status("not_applicable", "Reeds-Shepp 需要可倒车机具") == "not_applicable"
    assert derive_status("crash", "SomeError: boom") == "crash"
    # 已具名的行：派生与运行时一致（validator 类即状态名）
    assert derive_status("outside_area", "validator_rejected:outside_area") == "outside_area"


def test_unknown_validator_class_fails_loud():
    with pytest.raises(ValueError, match="未知"):
        derive_status("not_applicable", "validator_rejected:teleported_away")


def test_vocabulary_stays_in_sync_with_runner():
    # 两处声明、一份词典：漂移当场暴露（runner 侧另有对 validator 源码的结构核对）
    from agriautolab.pipeline.corpus.derived_status import _VALIDATOR_REJECTION_CLASSES
    from agriautolab.pipeline.corpus import runner
    assert _VALIDATOR_REJECTION_CLASSES == runner._VALIDATOR_REJECTION_CLASSES


def test_diff_counts_keyed_by_class():
    rows = [
        {"runstatus": "not_applicable", "failure_reason": "validator_rejected:outside_area"},
        {"runstatus": "not_applicable", "failure_reason": "validator_rejected:outside_area"},
        {"runstatus": "ok", "failure_reason": None},
        {"runstatus": "not_applicable", "failure_reason": "Reeds-Shepp 需要可倒车机具"},
    ]
    assert status_diff_counts(rows) == {"not_applicable->outside_area": 2}


def test_aggregation_path_branches_only_through_derived_status():
    # 结构性纪律：aggregate.py 不许拿 runstatus 直接与字面量比较分叉——
    # 状态判断需经过派生层，否则单一真相源在聚合路径上失守。
    source = (SRC / "pipeline" / "corpus" / "aggregate.py").read_text(encoding="utf-8")
    forbidden = ['runstatus") ==', "runstatus\"] ==", "runstatus\") !=", "runstatus\"] !="]
    for pattern in forbidden:
        assert pattern not in source, pattern
    assert source.count("derive_status(") >= 2


def test_manifest_carries_derived_status_contract(tmp_path, c_record, c_vehicle, c_configs, c_benchmark, c_corpus_protocol):
    # 未来运行的 manifest 需自带派生定义与分歧计数（空 dict 也是显式的「无分歧」）
    from agriautolab.pipeline.corpus.runner import CodeVersion, CorpusRunner

    class ConstantClock:
        def __call__(self):
            return 0.0

    root = tmp_path / "runs"
    CorpusRunner(clock=ConstantClock()).run(
        (c_record,), (c_vehicle,), c_configs, c_benchmark, c_corpus_protocol,
        output_dir=root, code_version=CodeVersion("TEST", False, "1" * 64),
    )
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["derived_status_definition"] == DERIVED_STATUS_DEFINITION
    diffs = manifest["runstatus_vs_derived_diff_counts"]
    assert isinstance(diffs, dict)
    assert sum(manifest["derived_status_counts"].values()) == manifest["n_runs"]
    assert sum(diffs.values()) <= manifest["n_runs"]
