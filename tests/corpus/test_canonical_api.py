"""canonical API 层测试：规范名可解析、与 legacy 身份恒等、wire ID 不变。"""

from pathlib import Path

import pytest



def test_metric_canonical_names_resolve_to_same_specs():
    from agriautolab.pipeline.metrics.registry import METRIC_REGISTRY, metric_by_canonical

    pairs = {
        "row_crossing_equivalent": "row_crossings",
        "runtime_s": "runtime_ms",
        "heading_change_per_meter": "aol",
        "nonwork_length_ratio": "eta_L",
        "normalized_path_length": "L_area",
    }
    for canonical, wire in pairs.items():
        spec = metric_by_canonical(canonical)
        assert spec is METRIC_REGISTRY[wire]
    # 未改名的指标 canonical 即 metric_id
    assert metric_by_canonical("path_length") is METRIC_REGISTRY["path_length"]
    with pytest.raises(KeyError):
        metric_by_canonical("row_crossings_v2")


def test_wire_ids_unchanged_for_evidence_identity():
    from agriautolab.pipeline.metrics.registry import METRIC_REGISTRY

    for wire in ("row_crossings", "runtime_ms", "aol", "eta_L", "L_area", "path_length",
                 "headland_turn_count"):
        assert wire in METRIC_REGISTRY


def test_objective_vector_accepts_legacy_kwargs_and_properties():
    from agriautolab.pipeline.pareto.front import ObjectiveVector

    legacy = ObjectiveVector(path_length=1.0, headland_turns=2.0, row_crossings=3.0)
    canonical = ObjectiveVector(path_length=1.0, headland_turn_count=2.0, row_crossing_equivalent=3.0)
    positional = ObjectiveVector(1.0, 2.0, 3.0)
    assert legacy == canonical == positional
    assert legacy.headland_turns == 2.0 and legacy.row_crossings == 3.0
    assert legacy.headland_turn_count == 2.0 and legacy.row_crossing_equivalent == 3.0
    with pytest.raises(TypeError, match="缺少目标维"):
        ObjectiveVector(path_length=1.0)


def test_feature_canonical_mapping_keeps_wire_ids():
    from agriautolab.selection.features.schema import canonical_feature_name

    assert canonical_feature_name("row_angle_vs_principal") == "crop_row_angle_to_principal_axis_rad"
    assert canonical_feature_name("elongation") == "elongation"  # 未改名者恒等


def test_algorithm_classes_canonical_with_legacy_aliases():
    from agriautolab.algorithms.decomposition.boustrophedon_cells import (
        BoustrophedonCells, BoustrophedonDecomposition,
    )
    from agriautolab.algorithms.headland.uniform_headland import (
        ConstantWidthHeadland, UniformHeadland,
    )
    from agriautolab.algorithms.path.dubins_transit import DubinsPathPlanner, DubinsTransit
    from agriautolab.algorithms.swath.min_width import MinWidthSwath, MinimumWidthSwathGenerator

    assert BoustrophedonCells is BoustrophedonDecomposition
    assert UniformHeadland is ConstantWidthHeadland
    assert DubinsTransit is DubinsPathPlanner
    assert MinWidthSwath is MinimumWidthSwathGenerator
    # wire ID（进 config_id/pool_hash 的字符串）不受类名影响
    assert ConstantWidthHeadland.algorithm_id == "uniform_headland"





def test_frozen_files_untouched():
    """字节冻结件的哈希门：f2c.py 适配器与语料池文件不允许被任何重构改动。

    注意：f2c.py 随 cross_validation→validation 搬迁时仅改写了 3 行导入路径
    （evidence.hashing→pipeline.hashing、cross_validation→validation），
    适配逻辑字节未动；哈希门钉住搬迁后的新字节（旧字节哈希见 study-001-frozen tag）。
    """
    root = Path(__file__).resolve().parents[2]
    import hashlib

    def sha256(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    assert sha256(root / "src/agriautolab/validation/f2c.py") == (
        "40e5d910ff623943ae07ada4f4183eee1e652fea38007dcdfaf8f061ddc5e3b5"
    )
    assert sha256(root / "configs/corpus_13.json") == (
        "502b1e9053b598d62daafa0b3a819f3cebc8385cb356aa908433582b93083a57"
    )
