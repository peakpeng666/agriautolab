"""给几何、阶段契约与 Block C 语料测试提供紧凑、确定的夹具。

纯合成 fixture；不读取真实 350 地块，不要求 F2C。
"""

import pytest
from shapely.geometry import Polygon
from shapely.geometry.base import BaseGeometry

from agriautolab.contracts.artifacts import HeadlandArtifact
from agriautolab.contracts.enums import CoverageTarget
from agriautolab.contracts.geometry import Point, PolygonSpec
from agriautolab.contracts.problem import CoverageProblem
from agriautolab.contracts.protocol import (
    BenchmarkProtocol,
    HypervolumeReference,
    ReverseCostSpec,
)
from agriautolab.contracts.vehicle import VehicleSpec
from agriautolab.evidence.hashing import content_hash
from agriautolab.corpus.protocol import CorpusProtocol
from agriautolab.datasets.fields2benchmark import DatasetLicense, FieldRecord
from agriautolab.geometry.validate import polygon_to_spec
from agriautolab.metrics.coverage import CoverageTargets, resolve_coverage_targets
from agriautolab.pipeline.config import PipelineConfig


# Block B：协议必填的超体积参考点。测试里只满足字段约束，不参与任何数值断言；
# 超体积自身的断言在各测试内用独立声明的参考点。
HYPERVOLUME_TEST_REFERENCE = HypervolumeReference(
    path_length=1.0e7,
    headland_turns=1.0e4,
    row_crossings=1.0e7,
    basis="test-constant",
)

# 任务 7：协议必填的倒车代价。测试里取几何中性值（乘子 1.0、换挡罚 0.0），
# 即「纯几何长度」，因此不改变任何既有断言的数值。
REVERSE_COST_TEST_SPEC = ReverseCostSpec(reverse_length_multiplier=1.0, gear_shift_penalty_m=0.0)


def rectangle_spec(width: float, height: float, geometry_id: str = "field") -> PolygonSpec:
    return PolygonSpec(
        geometry_id=geometry_id,
        exterior=(
            Point(x=0.0, y=0.0),
            Point(x=width, y=0.0),
            Point(x=width, y=height),
            Point(x=0.0, y=height),
            Point(x=0.0, y=0.0),
        ),
    )


def targets_from_geometry(
    geometry: BaseGeometry,
    *,
    target: CoverageTarget = CoverageTarget.ORIGINAL_FIELD,
    headland: HeadlandArtifact | None = None,
    headland_width_m: float | None = None,
    geometry_id: str = "field",
) -> CoverageTargets:
    """测试里构造分母的唯一入口——照样走 resolve_coverage_targets，不允许手拼 CoverageTargets。"""
    problem = CoverageProblem(problem_id=geometry_id, field=polygon_to_spec(geometry, geometry_id))
    return resolve_coverage_targets(problem, headland, target=target, headland_width_m=headland_width_m)


@pytest.fixture
def coverage_targets():
    return targets_from_geometry


@pytest.fixture
def rectangle_problem() -> CoverageProblem:
    return CoverageProblem(problem_id="rect", field=rectangle_spec(100.0, 50.0))


@pytest.fixture
def robot() -> VehicleSpec:
    return VehicleSpec(
        working_width_m=10.0,
        body_width_m=2.0,
        min_turning_radius_m=3.0,
        can_reverse=False,
    )


@pytest.fixture
def c_record():
    return FieldRecord(
        field_id="NL_synthetic",
        # 坐标落在 EPSG:28992 的定义域内（任务 5 的可证伪检查）：
        # RD New 的合法 easting 从 646 起步，原点附近的 (0,0) 是假声明。
        geometry=Polygon([
            (155000, 463000), (155100, 463000), (155100, 463050), (155000, 463050), (155000, 463000),
        ]),
        source="PDOK",
        license=DatasetLicense.CC0_1_0,
        source_crs="EPSG:28992",
        working_crs="EPSG:28992",
    )


@pytest.fixture
def c_vehicle():
    return VehicleSpec(working_width_m=10.0, body_width_m=2.0, min_turning_radius_m=3.0, can_reverse=False)


@pytest.fixture
def c_benchmark():
    return BenchmarkProtocol(
        protocol_id="C-TEST",
        coverage_target="original_field",
        coverage_threshold=0.0,
        hypervolume_reference=HypervolumeReference(
            path_length=1e6, headland_turns=1e4, row_crossings=1e6, basis="test"
        ),
        reverse_cost=REVERSE_COST_TEST_SPEC,
    )


@pytest.fixture
def c_corpus_protocol(c_benchmark, c_vehicle):
    return CorpusProtocol(
        protocol_id="C-CORPUS-TEST",
        benchmark_protocol_hash=c_benchmark.spec_hash(),
        row_offsets_rad=(0.0,),
        row_spacings_m=(3.0,),
        cv_folds=3,
        vehicles_hash=content_hash(tuple(v.model_dump(mode="json") for v in (c_vehicle,))),
    )


@pytest.fixture
def c_configs():
    return (
        PipelineConfig(
            decomposition="no_decomposition",
            headland="uniform_headland",
            swath="fixed_angle",
            route="boustrophedon_order",
            path="dubins_transit",
            params={"headland_width_m": 8.0, "angle_rad": 0.0},
        ),
        PipelineConfig(
            decomposition="no_decomposition",
            headland="no_headland",
            swath="fixed_angle",
            route="boustrophedon_order",
            path="dubins_transit",
            params={"angle_rad": 0.0},
        ),
    )
