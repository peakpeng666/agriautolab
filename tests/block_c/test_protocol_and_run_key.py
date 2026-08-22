from agriautolab.corpus.protocol import CorpusProtocol
from agriautolab.corpus.runner import CodeVersion, discover_code_version, run_key


def test_row_grid_is_part_of_protocol_hash(c_benchmark):
    left = CorpusProtocol(
        protocol_id="x", benchmark_protocol_hash=c_benchmark.spec_hash(),
        row_offsets_rad=(0.0, 0.1), row_spacings_m=(0.75, 3.0), cv_folds=3,
        vehicles_hash="0" * 64,
    )
    right = left.model_copy(update={"row_offsets_rad": (0.0, 0.2)})
    assert left.spec_hash() != right.spec_hash()


def test_run_key_is_code_version_sensitive():
    common = dict(problem_hash="a" * 64, vehicle_hash="b" * 64, config_id="cfg", protocol_hash="c" * 64)
    assert run_key(**common, code_version="commit-A") != run_key(**common, code_version="commit-B")


def test_archive_without_git_is_marked_dirty(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "x.py").write_text("x=1\n", encoding="utf-8")
    version = discover_code_version(tmp_path)
    assert version.dirty is True
    assert version.commit == "NO_GIT_METADATA"
