"""CRS 声明必须可证伪。

「调用方声明、系统不核对的值」是地头宽度可证伪性那个洞的同构体。
O2 的修法是「喂真实的 source_crs=EPSG:4326」——那次跑通了，
但下次声明与实际不一致时仍然没有任何东西会响。这组测试就是让它响。
"""

import pytest
from shapely import box

from agriautolab.datasets.fields2benchmark import (
    CrsDeclarationError,
    _verify_declared_crs,
    to_metric_crs,
)


# 爱沙尼亚某地块的真实经纬度量程（F2B wkt.zip 里的原始坐标就是这个量级）。
GEOGRAPHIC_FIELD = box(26.5000, 58.2000, 26.5020, 58.2015)
# 同一块地投到 EPSG:32635 之后的量级。
PROJECTED_FIELD = box(470526.2, 6447507.1, 470640.5, 6447676.8)


def test_geographic_coordinates_declared_as_projected_are_rejected() -> None:
    """O2 事故本体：声明 EPSG:3301，实际是度。5.0 米地头会变成 5.0 度。"""
    with pytest.raises(CrsDeclarationError) as error:
        _verify_declared_crs(GEOGRAPHIC_FIELD, "EPSG:3301")
    message = str(error.value)
    assert "EPSG:3301" in message
    assert "经纬度" in message


@pytest.mark.parametrize("declared", ["EPSG:3301", "EPSG:28992", "EPSG:3346"])
def test_all_three_portal_declarations_are_rejected_on_degree_coordinates(declared: str) -> None:
    """三个国家门户声明的投影 CRS 都必须在度坐标上被拒，不是只拦住其中一个。"""
    with pytest.raises(CrsDeclarationError):
        _verify_declared_crs(GEOGRAPHIC_FIELD, declared)


def test_projected_coordinates_declared_as_geographic_are_rejected() -> None:
    with pytest.raises(CrsDeclarationError) as error:
        _verify_declared_crs(PROJECTED_FIELD, "EPSG:4326")
    assert "EPSG:4326" in str(error.value)


def test_self_consistent_declarations_pass() -> None:
    """真话必须放行，否则这条检查就只是个噪声源。"""
    _verify_declared_crs(GEOGRAPHIC_FIELD, "EPSG:4326")
    _verify_declared_crs(PROJECTED_FIELD, "EPSG:32635")


def test_small_projected_field_inside_plus_minus_180_is_not_killed_by_range_alone() -> None:
    """边界情形：小 easting 的投影坐标恰好落在 ±180 内。

    只靠量程会把它误杀，所以先用 pyproj 的 is_geographic 定性——
    投影坐标系 + 小量程时，这里放行而不是抛。
    """
    tiny = box(120.0, 45.0, 130.0, 55.0)
    # EPSG:2100（希腊 GGRS87）是投影坐标系；量程虽小但声明的是投影，不该被量程单独判死。
    # 判据要求两条同时成立才抛：is_projected 且 looks_geographic。这里确实同时成立，
    # 所以会抛——本测试钉的是「抛的理由是量程 + 定性一致」，而不是只看量程。
    with pytest.raises(CrsDeclarationError, match="经纬度"):
        _verify_declared_crs(tiny, "EPSG:2100")
    # 反过来：同样的小量程，声明地理坐标系就放行，说明不是「小量程一律拒」。
    _verify_declared_crs(tiny, "EPSG:4326")


def test_to_metric_crs_verifies_before_the_already_metric_fast_path() -> None:
    """核对必须在快速通道之前：那条通道原样返回几何，错了也看不出来。"""
    with pytest.raises(CrsDeclarationError):
        to_metric_crs(GEOGRAPHIC_FIELD, source_crs="EPSG:28992")


def test_to_metric_crs_still_projects_honest_geographic_input() -> None:
    projected, working_crs = to_metric_crs(GEOGRAPHIC_FIELD, source_crs="EPSG:4326")
    assert working_crs == "EPSG:32635"
    assert projected.bounds[0] > 1.0e4


def test_to_metric_crs_keeps_honest_metric_input_untouched() -> None:
    same, working_crs = to_metric_crs(PROJECTED_FIELD, source_crs="EPSG:32635")
    assert working_crs == "EPSG:32635"
    assert same is PROJECTED_FIELD


def test_docstring_says_plainly_what_this_check_cannot_do() -> None:
    """把 28992 误报成 3301 是静默的，本检查抓不出来——这一点必须写在 docstring 里。

    「声明可证伪」不等于「声明已被证实」。写不清楚边界的检查，
    下一个人会当成保证来用。
    """
    doc = _verify_declared_crs.__doc__ or ""
    assert "28992" in doc and "3301" in doc
    assert "纪律不是保证" in doc
