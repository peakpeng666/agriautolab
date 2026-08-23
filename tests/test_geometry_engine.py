"""几何引擎版本契约：GEOS 换版 = 产物换版。

已验证集合在 evidence/env_geometry.json。当前运行时不在集合内时**警告并要求
重跑解析真值**，不直接 fail——换 GEOS 是合法的，但必须重新验证，
不能默认沿用旧结论（与 env_f2c.json 同一条纪律）。
"""

import json
import pathlib
import warnings

import shapely


def _verified_geos() -> set[str]:
    payload = json.loads((pathlib.Path(__file__).resolve().parents[1] / "evidence" / "env_geometry.json").read_text(encoding="utf-8"))
    return {item["geos_version_string"] for item in payload["verified"]}


def test_geos_version_is_in_verified_set() -> None:
    current = shapely.geos_version_string
    verified = _verified_geos()
    if current not in verified:
        warnings.warn(
            f"GEOS {current} 不在已验证集合 {sorted(verified)}：union_all 网格行为与 buffer "
            "离散化可能已变，PI_DISCRETE / 反曲角 / 障碍假阳性等解析真值必须在本引擎上"
            "重跑验证后才能沿用（把结果补进 evidence/env_geometry.json）",
            stacklevel=2,
        )


def test_shapely_is_pinned() -> None:
    assert shapely.__version__ == "2.1.2", (
        f"shapely {shapely.__version__} 偏离锁文件（scripts/install/requirements.lock）；"
        "shapely 大版本绑定 GEOS 行为，升级=换引擎"
    )
