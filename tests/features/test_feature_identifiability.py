"""常设检查：进入实例定义、且影响目标或可行性的场景参数，必须至少被一个特征看见。

由「行距缺口」确立的缺陷类——**映射欠定**：两个实例特征向量完全相同
而最优配置不同，推荐器在数学上不可辨识。这与前五轮的「同一事实两处住」「跨作用域
使用」不同族，是第三类。任何新增场景参数都必须在本表登记并接受检查；
`crossable` 例外地走分层（协议级变量）而非特征，理由见表内注释与 AUDIT_NOTE。
"""

import math

import pytest

from agriautolab.contracts.geometry import Point, PolygonSpec
from agriautolab.contracts.problem import CoverageProblem
from agriautolab.contracts.rows import RowStructure
from agriautolab.contracts.vehicle import VehicleSpec
from agriautolab.corpus.protocol import CorpusProtocol
from agriautolab.features.extract import extract_instance_features


def _problem(direction_rad: float, spacing_m: float, crossable: bool = True) -> CoverageProblem:
    field = PolygonSpec(geometry_id="field", exterior=(
        Point(x=0.0, y=0.0), Point(x=80.0, y=0.0), Point(x=80.0, y=40.0),
        Point(x=0.0, y=40.0), Point(x=0.0, y=0.0),
    ))
    rows = RowStructure(
        direction_rad=direction_rad, spacing_m=spacing_m, crossable=crossable,
        crossing_penalty=10.0 if crossable else math.inf,
    )
    return CoverageProblem(problem_id="identifiability", field=field, row_structure=rows)


def _vehicle(working_width: float = 9.7, radius: float = 3.0) -> VehicleSpec:
    return VehicleSpec(working_width_m=working_width, body_width_m=2.0, min_turning_radius_m=radius)


def _features(**overrides) -> dict[str, float]:
    defaults = dict(direction_rad=0.4, spacing_m=2.5, crossable=True, working_width=9.7, radius=3.0)
    defaults.update(overrides)
    problem = _problem(defaults["direction_rad"], defaults["spacing_m"], defaults["crossable"])
    vehicle = _vehicle(defaults["working_width"], defaults["radius"])
    return extract_instance_features(problem, vehicle).values


@pytest.mark.parametrize("dof,base,variant,witness", [
    ("row offset/direction", {}, {"direction_rad": 1.1}, "row_angle_vs_principal"),
    ("row spacing", {}, {"spacing_m": 5.0}, "crossing_density"),
    ("working width", {}, {"working_width": 4.0}, "turning_ratio"),
    ("min turning radius", {}, {"radius": 1.0}, "turning_ratio"),
])
def test_every_objective_relevant_scenario_dof_is_visible_in_features(dof, base, variant, witness):
    """仅在该自由度上不同的两个实例，特征向量必须不同，且见证特征必须就是不同的那个。"""
    left = _features(**base)
    right = _features(**variant)
    assert left != right, f"{dof}：特征向量完全相同——映射欠定"
    assert left[witness] != right[witness], f"{dof}：{witness} 未能见证该自由度"


def test_spacing_variants_differ_in_both_new_features():
    """行距双特征都必须对 spacing 敏感（一个标定穿行量纲，一个标定幅宽-行距比）。"""
    base = _features(spacing_m=2.5)
    wider = _features(spacing_m=5.0)
    assert wider["crossing_density"] == pytest.approx(0.5 * base["crossing_density"], rel=1e-12)
    assert wider["spacing_to_width_ratio"] == pytest.approx(2.0 * base["spacing_to_width_ratio"], rel=1e-12)


def test_crossable_is_handled_by_stratification_not_features():
    """crossable 无特征可见——按裁定走分层：它是 CorpusProtocol 的字段并进入协议哈希。

    可穿越与不可穿越是两个问题族（crossing_penalty 有限 vs inf），混在一个推荐器里
    训练是错的；协议哈希携带它意味着一次语料运行就是一个层，跨层合并必然改变
    协议身份并留下证据。若未来某块把 crossable 接进可行性门槛，本条分层语义不变。
    """
    left = _features(crossable=True)
    right = _features(crossable=False)
    assert left == right   # 特征确实看不见它——这正是必须分层的原因

    protocol_kwargs = dict(
        protocol_id="stratification-check",
        benchmark_protocol_hash="0" * 64,
        row_offsets_rad=(0.0,),
        row_spacings_m=(2.5,),
        vehicles_hash="0" * 64,
    )
    crossable_run = CorpusProtocol(row_crossable=True, **protocol_kwargs)
    uncrossable_run = CorpusProtocol(row_crossable=False, **protocol_kwargs)
    assert crossable_run.spec_hash() != uncrossable_run.spec_hash(), (
        "crossable 必须进入协议哈希：这是分层的载体，翻层而哈希不变等于跨层混训不留痕"
    )


def test_feature_set_has_no_other_blind_scenario_dofs():
    """场景参数白名单之外不得有影响目标却无特征可见的自由度（登记制）。

    当前进入实例定义的全部参数：direction_rad/spacing/crossable（行结构）与
    working_width/min_turning_radius/body_width（机具）。逐个断言可见性：
    body_width 通过 swath_count_at_minwidth 间接可见吗——不：swath_count 只吃
    working_width。但 body_width 不影响三维目标（只影响车体扫掠硬约束的裕量），
    按「影响目标或可行性」的登记标准，它属于裕量参数而非场景自由度；
    若未来把它接进场景扫描，必须回来给它登记特征。
    """
    base = _features()
    thinner_body = extract_instance_features(
        _problem(0.4, 2.5), _vehicle(9.7, 3.0).model_copy(update={"body_width_m": 1.0})
    ).values
    assert base == thinner_body   # 如实记录：body_width 当前不可见（见 docstring 的登记裁定）
