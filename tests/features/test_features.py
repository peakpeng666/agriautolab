"""特征旋转不变性（解析真值清单 14）：200 组随机刚体变换，相对误差 < 1e-9。

不是手挑几个例子——实测经验：随机变换测试抓出过 unary_union
静默丢多边形（500 组错 21 次，最大 40.0%）。
"""

import math

import numpy as np
import pytest
from shapely import Polygon
from shapely.affinity import rotate as shp_rotate
from shapely.affinity import scale as shp_scale
from shapely.affinity import translate as shp_translate

from agriautolab.contracts.problem import CoverageProblem
from agriautolab.contracts.rows import RowStructure
from agriautolab.contracts.vehicle import VehicleSpec
from agriautolab.selection.features.extract import extract_instance_features, reflex_vertex_count
from agriautolab.selection.features.invariance import FEATURE_INVARIANCE
from agriautolab.geometry.validate import polygon_to_spec


BASE_FIELD = Polygon([(0.0, 0.0), (100.0, 0.0), (100.0, 20.0), (60.0, 20.0), (60.0, 50.0), (0.0, 50.0)])
BASE_OBSTACLE = Polygon([(20.0, 5.0), (35.0, 5.0), (35.0, 14.0), (20.0, 14.0)])


def build_problem(theta: float = 0.0, scale: float = 1.0, tx: float = 0.0, ty: float = 0.0,
                  row_direction: float = 0.4) -> CoverageProblem:
    def transform(geometry):
        moved = shp_scale(geometry, xfact=scale, yfact=scale, origin=(0.0, 0.0))
        moved = shp_rotate(moved, theta, origin=(0.0, 0.0), use_radians=True)
        return shp_translate(moved, xoff=tx, yoff=ty)

    field = polygon_to_spec(transform(BASE_FIELD), "field")
    obstacle = polygon_to_spec(transform(BASE_OBSTACLE), "obs")
    rows = RowStructure(
        direction_rad=row_direction + theta, spacing_m=2.5 * scale,
        crossable=True, crossing_penalty=10.0 * scale,
    )
    return CoverageProblem(problem_id="p", field=field, obstacles=(obstacle,), row_structure=rows)


def vehicle(scale: float = 1.0) -> VehicleSpec:
    # 幅宽取 9.7： swath_count = ceil(span/width) 在整比处不连续，测试几何必须避开边界
    return VehicleSpec(working_width_m=9.7 * scale, body_width_m=2.0 * scale, min_turning_radius_m=3.0 * scale)


def test_feature_rotation_invariance_under_200_random_rigid_transforms() -> None:
    """真值 14：随机刚体（旋转+平移）变换下，声明旋转不变的特征相对误差 < 1e-9。"""
    rng = np.random.default_rng(20260821)
    baseline = extract_instance_features(build_problem(), vehicle()).values
    worst = {name: 0.0 for name in baseline}
    for _ in range(200):
        theta = float(rng.uniform(-math.pi, math.pi))
        tx, ty = float(rng.uniform(-500.0, 500.0)), float(rng.uniform(-500.0, 500.0))
        transformed = extract_instance_features(build_problem(theta=theta, tx=tx, ty=ty), vehicle()).values
        for name, contract in FEATURE_INVARIANCE.items():
            if not contract.rotation_invariant:
                continue
            base, moved = baseline[name], transformed[name]
            tolerance = 1e-9 * max(abs(base), abs(moved), 1.0)
            worst[name] = max(worst[name], abs(moved - base) / max(abs(base), 1.0) if base != moved else 0.0)
            assert abs(moved - base) <= tolerance, (
                f"{name}: {moved!r} vs {base!r} (rel {abs(moved - base) / max(abs(base), 1.0):.3e}, theta={theta:.4f})"
            )
    assert all(value < 1e-9 for value in worst.values())


@pytest.mark.parametrize("scale", [0.5, 2.0, 3.7])
def test_declared_scale_invariance_holds_under_similarity(scale: float) -> None:
    """缩放不变契约：几何与机具同倍缩放，声明不变的特征不变；area_m2 按平方缩放。"""
    baseline = extract_instance_features(build_problem(), vehicle()).values
    scaled = extract_instance_features(build_problem(scale=scale), vehicle(scale)).values
    for name, contract in FEATURE_INVARIANCE.items():
        if not contract.scale_invariant:
            continue
        assert scaled[name] == pytest.approx(baseline[name], rel=1e-9, abs=1e-12), name
    assert scaled["area_m2"] == pytest.approx(baseline["area_m2"] * scale * scale, rel=1e-9)


def test_row_angle_feature_omitted_without_row_structure() -> None:
    problem = build_problem()
    plain = problem.model_copy(update={"row_structure": None})
    values = extract_instance_features(plain, vehicle()).values
    assert "row_angle_vs_principal" not in values
    assert "row_angle_vs_principal" in extract_instance_features(problem, vehicle()).values


def test_reflex_vertex_count_known_truths() -> None:
    assert reflex_vertex_count(Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])) == 0
    l_shape = Polygon([(0, 0), (100, 0), (100, 20), (60, 20), (60, 50), (0, 50)])
    assert reflex_vertex_count(l_shape) == 1
    with_hole = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)],
                        [[(4, 4), (6, 4), (6, 6), (4, 6)]])
    # 矩形障碍的 4 个凸角在自由空间里都是 270 度反曲角
    assert reflex_vertex_count(with_hole) == 4


def test_feature_extraction_records_elapsed_seconds() -> None:
    features = extract_instance_features(build_problem(), vehicle())
    assert set(features.elapsed_s) == set(features.values)
    assert all(seconds >= 0.0 for seconds in features.elapsed_s.values())


def test_base_instance_feature_values_are_finite_and_sane() -> None:
    values = extract_instance_features(build_problem(), vehicle()).values
    expected_keys = {
        "area_m2", "perimeter_area_ratio", "convexity_deficiency", "elongation",
        "reflex_vertex_count", "obstacle_count", "obstacle_area_ratio",
        "row_angle_vs_principal", "crossing_density", "spacing_to_width_ratio",
        "turning_ratio", "swath_count_at_minwidth",
    }
    assert set(values) == expected_keys
    # 行距可见性（O3 整改）：sqrt(3665)/2.5 与 2.5/9.7 的解析值
    assert values["crossing_density"] == pytest.approx(math.sqrt(3800.0 - 135.0) / 2.5, rel=1e-12)
    assert values["spacing_to_width_ratio"] == pytest.approx(2.5 / 9.7, rel=1e-15)
    assert values["reflex_vertex_count"] == 5.0   # L 形 1 个 + 矩形障碍 4 个
    assert values["obstacle_count"] == 1.0
    assert 0.0 <= values["row_angle_vs_principal"] <= math.pi / 2.0 + 1e-12
    assert values["turning_ratio"] == pytest.approx(3.0 / 9.7)
    assert values["area_m2"] == pytest.approx(3800.0 - 135.0, rel=1e-9)
