import csv
import importlib.util
import xml.etree.ElementTree as ET

import pytest

pytest.importorskip("pyarrow")

from agriautolab.aslib import export_aslib_scenarios
from agriautolab.corpus.runner import CodeVersion, CorpusRunner


class ConstantClock:
    def __call__(self):
        return 0.0


def _corpus(tmp_path, c_record, c_vehicle, c_configs, c_benchmark, c_corpus_protocol):
    root = tmp_path / "corpus"
    CorpusRunner(clock=ConstantClock()).run(
        (c_record,), (c_vehicle,), c_configs, c_benchmark, c_corpus_protocol,
        output_dir=root,
        code_version=CodeVersion("TEST", False, "3" * 64),
    )
    return root


def test_aslib_three_scenarios_and_fixed_cv(tmp_path, c_record, c_vehicle, c_configs, c_benchmark, c_corpus_protocol):
    corpus = _corpus(tmp_path, c_record, c_vehicle, c_configs, c_benchmark, c_corpus_protocol)
    out_a = tmp_path / "aslib-a"
    out_b = tmp_path / "aslib-b"
    scenarios_a = export_aslib_scenarios(corpus / "runs.parquet", out_a, cv_folds=3, row_crossable=True)
    scenarios_b = export_aslib_scenarios(corpus / "runs.parquet", out_b, cv_folds=3, row_crossable=True)
    assert {path.name for path in scenarios_a} == {"path_length", "headland_turns", "row_crossings"}
    for name in ("path_length", "headland_turns", "row_crossings"):
        description = (out_a / "crossable" / name / "description.txt").read_text(encoding="utf-8")
        assert "ASlib assumes a single objective" in description
        assert (out_a / "crossable" / name / "cv.arff").read_bytes() == (
            out_b / "crossable" / name / "cv.arff"
        ).read_bytes()


def test_crossable_strata_export_to_separate_trees(tmp_path, c_record, c_vehicle, c_configs, c_benchmark, c_corpus_protocol):
    """任务 6：crossable 做分层不做特征——两层的 scenario 目录与 id 必须能分辨。"""
    corpus = _corpus(tmp_path, c_record, c_vehicle, c_configs, c_benchmark, c_corpus_protocol)
    out = tmp_path / "aslib-strata"
    crossable = export_aslib_scenarios(corpus / "runs.parquet", out, cv_folds=3, row_crossable=True)
    uncrossable = export_aslib_scenarios(corpus / "runs.parquet", out, cv_folds=3, row_crossable=False)
    assert {path.parent.name for path in crossable} == {"crossable"}
    assert {path.parent.name for path in uncrossable} == {"uncrossable"}
    assert set(crossable).isdisjoint(uncrossable)
    text = (out / "uncrossable" / "path_length" / "description.txt").read_text(encoding="utf-8")
    assert "scenario_id: agriautolab-path_length-uncrossable" in text
    assert "row_crossable: false" in text
    assert "two problem families" in text


def test_svg_is_xml_and_circle_count_equals_csv_rows(tmp_path, c_record, c_vehicle, c_configs, c_benchmark, c_corpus_protocol):
    corpus = _corpus(tmp_path, c_record, c_vehicle, c_configs, c_benchmark, c_corpus_protocol)
    module_path = __import__("pathlib").Path(__file__).resolve().parents[2] / "scripts" / "make_figure_front.py"
    spec = importlib.util.spec_from_file_location("make_figure_front", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    svg = tmp_path / "front.svg"
    data = tmp_path / "front.csv"
    module.generate(corpus / "runs.parquet", corpus / "manifest.json", svg, data, None)
    tree = ET.parse(svg)
    circles = tree.findall("{http://www.w3.org/2000/svg}circle")
    with data.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(circles) == len(rows)
    assert len(rows) > 0
