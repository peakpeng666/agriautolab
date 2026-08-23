"""交叉验证的三条适配器路径、锁死 schema，以及两道拒绝比较的闸（CRS / 路线算法）。"""

import pytest

from agriautolab.cross_validation.f2c import (
    CrsMismatchError,
    F2CRequest,
    F2CResult,
    F2CSchemaError,
    F2CUnavailableError,
    PythonBindingAdapter,
    RecordedCsvAdapter,
    RouteAlgorithmMismatchError,
    SubprocessAdapter,
)
from agriautolab.cross_validation.report import compare_results


COLUMNS = (
    "request_id,path_length,swath_count,swath_length_sum,main_field_area,"
    "transit_entry_leg_m,transit_turn_total_m,transit_turn_count,"
    "transit_inter_cell_m,transit_exit_leg_m,transit_other_m,working_crs,route_algorithm\n"
)
CRS = "EPSG:32635"
ROUTE = "boustrophedon"
# path,swath_count,swath_sum,area,entry,turn_total,turn_count,inter_cell,exit,other
NUMBERS = "12.5,2,10,40,0,2.5,1,0,0,0"
ROW = f"r1,{NUMBERS},{CRS},{ROUTE}\n"
REQ = F2CRequest("r1", "POLYGON((0 0,10 0,10 5,0 5,0 0))", 2, 5, 3, 6, 0, CRS, ROUTE)


def result(request_id: str = "r1", path_length: float = 12.5, *,
           crs: str = CRS, route: str = ROUTE) -> F2CResult:
    """构造一条结果行。转移分量给成自洽的小数字，本组测试只关心 schema 与两道闸。"""
    return F2CResult(
        request_id=request_id, path_length=path_length, swath_count=2.0,
        swath_length_sum=10.0, main_field_area=40.0,
        transit_entry_leg_m=0.0, transit_turn_total_m=2.5, transit_turn_count=1.0,
        transit_inter_cell_m=0.0, transit_exit_leg_m=0.0, transit_other_m=0.0,
        working_crs=crs, route_algorithm=route,
    )


def test_recorded_csv_self_comparison_has_zero_residual(tmp_path):
    path = tmp_path / "f2c.csv"
    path.write_text(COLUMNS + ROW, encoding="utf-8")
    row = RecordedCsvAdapter(path).run(REQ)
    reports = compare_results((row,), (row,))
    assert all(
        report.max_abs_diff == 0.0 and report.max_abs_rel_diff_vs_golden == 0.0
        for report in reports
    )


def test_recorded_csv_missing_column_names_it(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text("request_id,path_length,swath_count,main_field_area\nr1,1,2,3\n", encoding="utf-8")
    with pytest.raises(F2CSchemaError, match="swath_length_sum"):
        RecordedCsvAdapter(path).run(REQ)


def test_recorded_csv_extra_column_is_rejected(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text(COLUMNS.rstrip("\n") + ",surprise\n" + ROW.rstrip("\n") + ",5\n", encoding="utf-8")
    with pytest.raises(F2CSchemaError, match="surprise"):
        RecordedCsvAdapter(path).run(REQ)


def test_unavailable_adapters_fail_loudly(tmp_path):
    with pytest.raises(F2CUnavailableError):
        RecordedCsvAdapter(tmp_path / "missing.csv").run(REQ)
    with pytest.raises(F2CUnavailableError):
        SubprocessAdapter(tmp_path / "missing-exe").run(REQ)
    if not PythonBindingAdapter().available():
        with pytest.raises(F2CUnavailableError):
            PythonBindingAdapter().run(REQ)


def test_subprocess_and_recorded_return_same_result_type(tmp_path):
    recorded = tmp_path / "recorded.csv"
    recorded.write_text(COLUMNS + ROW, encoding="utf-8")
    script = tmp_path / "fake_f2c"
    script.write_text(
        "#!/usr/bin/env python3\n"
        "import argparse, pathlib\n"
        "p=argparse.ArgumentParser(); p.add_argument('--request'); p.add_argument('--field');"
        " p.add_argument('--output'); a=p.parse_args()\n"
        f"pathlib.Path(a.output).write_text({(COLUMNS + ROW)!r})\n",
        encoding="utf-8",
    )
    script.chmod(0o755)
    a = RecordedCsvAdapter(recorded).run(REQ)
    b = SubprocessAdapter(script).run(REQ)
    assert type(a) is type(b) is F2CResult
    assert a == b


def test_relative_difference_denominator_is_always_golden_and_keeps_its_sign() -> None:
    """分母纪律：分母恒为 reference，符号留在数里，不随谁大谁小切换。

    实测样本（f2b_004_ee_field_64）：ours=1872.3412 golden=1614.3647。
    旧的 max(|a|,|b|) 分母给 13.7783%，按 golden 分母是 15.9801% —— 相差 2.2 个百分点。
    """
    ours = result(path_length=1872.3412123402554)
    golden = result(path_length=1614.3646580038485)
    report = compare_results((ours,), (golden,))[0]
    assert report.metric_id == "path_length"
    assert report.median_rel_diff_vs_golden == pytest.approx(0.159801, rel=1e-4)
    assert report.max_abs_rel_diff_vs_golden == pytest.approx(0.159801, rel=1e-4)
    assert report.disagreements[0].rel_diff_vs_golden > 0.0

    flipped = compare_results((golden,), (ours,))[0]
    assert flipped.median_rel_diff_vs_golden < 0.0
    assert flipped.max_abs_rel_diff_vs_golden == pytest.approx(0.137783, rel=1e-4)


def test_transit_components_are_reported_separately_from_path_length() -> None:
    """分量拆解纪律：work 已对齐而 transit 没有时，只报 path_length 会把差异稀释 6 倍。"""
    metrics = {report.metric_id for report in compare_results((result(),), (result(),))}
    assert {"transit_turn_total_m", "transit_turn_count", "transit_entry_leg_m",
            "transit_exit_leg_m", "transit_inter_cell_m"} <= metrics


def test_comparator_refuses_when_the_two_sides_used_different_working_crs() -> None:
    """G-B：投影不一致时残差不可归因给算法，必须抛，不返回空报告、不静默比较。"""
    with pytest.raises(CrsMismatchError) as error:
        compare_results((result(crs="EPSG:32635"),), (result(crs="EPSG:3301"),))
    message = str(error.value)
    assert "EPSG:32635" in message and "EPSG:3301" in message and "r1" in message


def test_comparator_refuses_when_the_two_sides_used_different_route_algorithms() -> None:
    """路线阶段必须配对。这正是 −38.11% 的由来。"""
    with pytest.raises(RouteAlgorithmMismatchError) as error:
        compare_results((result(route="boustrophedon"),), (result(route="snake"),))
    message = str(error.value)
    assert "boustrophedon" in message and "snake" in message and "r1" in message


def test_comparator_refuses_a_batch_that_mixes_route_algorithms() -> None:
    """一次只比一种路线：混批的中位数不属于任何一个算法。"""
    rows = (result("r1", route="boustrophedon"), result("r2", route="snake"))
    with pytest.raises(RouteAlgorithmMismatchError, match="混了多个"):
        compare_results(rows, rows)


def test_comparator_records_shared_crs_and_route_on_every_report() -> None:
    row = result()
    reports = compare_results((row,), (row,))
    assert all(report.working_crs == CRS and report.route_algorithm == ROUTE for report in reports)


def test_per_field_utm_is_allowed_as_long_as_the_two_sides_agree() -> None:
    """逐地块局部 UTM 是既定形态：不要求全语料同一投影，只要求同一请求两侧一致。"""
    ours = (result("r1", crs="EPSG:32635"), result("r2", crs="EPSG:32631"))
    reports = compare_results(ours, ours)
    assert all(report.working_crs == "per-field(2 CRS)" for report in reports)


@pytest.mark.parametrize("column,blank_row", [
    ("working_crs", f"r1,{NUMBERS},,{ROUTE}\n"),
    ("route_algorithm", f"r1,{NUMBERS},{CRS},\n"),
])
def test_blank_declaration_columns_are_rejected_by_schema(tmp_path, column, blank_row) -> None:
    """空字符串不算声明：忘记填和确实一致不能在 CSV 里长得一样。"""
    path = tmp_path / "blank.csv"
    path.write_text(COLUMNS + blank_row, encoding="utf-8")
    with pytest.raises(F2CSchemaError, match=column):
        RecordedCsvAdapter(path).run(REQ)


def test_ours_side_refuses_a_route_algorithm_it_does_not_implement() -> None:
    """不许拿名字相近的实现顶替：skip_one_order 的回扫方向与 F2C RP_Snake 不同。"""
    from agriautolab.cross_validation.ours import compute_ours

    request = F2CRequest(
        "r1", "POLYGON((0 0,100 0,100 50,0 50,0 0))", 2, 5, 3, 6, 0, CRS, "snake",
    )
    with pytest.raises(RouteAlgorithmMismatchError, match="snake"):
        compute_ours(request)


def test_env_f2c_hash_is_required_and_sensitive(tmp_path):
    """§3.1：golden 的录制环境指纹必须进哈希；缺失抛异常，改动任一字段哈希必变。"""
    import json

    from agriautolab.cross_validation.f2c import RecordedCsvAdapter

    env = {
        "fields2cover_source": "HEAD@3613525c241538fa9fd9df3e1209ae8184627958 (2025-04-23)",
        "swig": "SWIG Version 4.0.2",
        "python": "3.10.12",
    }
    golden = tmp_path / "golden_f2c.csv"
    golden.write_text("request_id,path_length,swath_count,swath_length_sum,main_field_area\nr1,10,2,8,50\n", encoding="utf-8")
    adapter = RecordedCsvAdapter(golden)

    # 缺失 env_f2c.json：抛异常，不静默
    with pytest.raises(Exception, match="env_f2c.json"):
        adapter.env_hash()

    (tmp_path / "env_f2c.json").write_text(json.dumps(env, sort_keys=True), encoding="utf-8")
    first = adapter.env_hash()
    assert len(first) == 64

    # 任一字段改动 -> 哈希变
    env["swig"] = "SWIG Version 4.1.0"
    (tmp_path / "env_f2c.json").write_text(json.dumps(env, sort_keys=True), encoding="utf-8")
    second = adapter.env_hash()
    assert second != first

    # EvidenceRecord 携带该哈希的通道畅通
    from agriautolab.contracts.enums import RunStatus
    from agriautolab.evidence.record import EvidenceRecord
    record = EvidenceRecord(
        record_id="f2c-seal", problem_hash="0" * 64, algorithm_id="golden",
        config_hash="0" * 64, source_hash="0" * 64, environment_hash=first,
        status=RunStatus.OK, f2c_env_hash=second,
    )
    assert record.f2c_env_hash == second
