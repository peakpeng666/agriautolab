import json

import pytest
from shapely.geometry import Polygon

from agriautolab.contracts.problem import CoverageProblem
from agriautolab.datasets.fields2benchmark import (
    DatasetLicense,
    DatasetLicenseError,
    FieldRecord,
    export_corpus,
    to_metric_crs,
)


def _record(field_id, license_value):
    return FieldRecord(
        field_id=field_id,
        geometry=Polygon([(0, 0), (10, 0), (10, 5), (0, 5), (0, 0)]),
        source="test",
        license=license_value,
        source_crs="EPSG:28992",
        working_crs="EPSG:28992",
    )


def test_license_filter_and_manifest_chain(tmp_path):
    manifest = export_corpus(
        (_record("free", DatasetLicense.CC0_1_0), _record("nc", DatasetLicense.NON_COMMERCIAL)),
        path=tmp_path,
        # 旧的 allow_non_commercial=False 等价于「既要用也要发」：
        # 两项用途都声明时，仅许非商业使用的记录被排除。断言数值不变。
        allow_analysis=True, allow_redistribution=True,
    )
    assert manifest.exported_field_ids == ("free",)
    assert manifest.filtered_non_commercial_ids == ("nc",)
    ledger = json.loads((tmp_path / "ledger.jsonl").read_text(encoding="utf-8"))
    assert ledger["payload"]["manifest_hash"] == manifest.manifest_hash


def test_unknown_license_is_rejected(tmp_path):
    with pytest.raises(DatasetLicenseError, match="mystery"):
        export_corpus((_record("mystery", DatasetLicense.UNKNOWN),), path=tmp_path,
                      allow_analysis=True, allow_redistribution=True)


def test_analysis_only_export_of_non_commercial_carries_an_explicit_warning(tmp_path):
    """仅供分析（不再分发）时，仅许非商业使用的记录可以进语料，但需带警告。"""
    manifest = export_corpus((_record("nc", DatasetLicense.NON_COMMERCIAL),), path=tmp_path,
                             allow_analysis=True, allow_redistribution=False)
    assert manifest.warning is not None and "不得公开再分发" in manifest.warning
    assert manifest.contains_non_commercial is True
    assert manifest.exported_field_ids == ("nc",)


def test_redistribution_excludes_non_commercial_records(tmp_path):
    """声明要再分发时，LT 那类记录需被排除——上游只给了「使用」，没给「分发」。"""
    manifest = export_corpus(
        (_record("free", DatasetLicense.CC0_1_0), _record("nc", DatasetLicense.NON_COMMERCIAL)),
        path=tmp_path, allow_analysis=True, allow_redistribution=True,
    )
    assert manifest.exported_field_ids == ("free",)
    assert manifest.filtered_non_commercial_ids == ("nc",)
    assert manifest.warning is None


def test_declaring_no_purpose_at_all_is_rejected(tmp_path):
    """两项都不声明不是「最保守」，是没说要干什么——导出本身失去意义。"""
    with pytest.raises(DatasetLicenseError, match="至少要声明一项用途"):
        export_corpus((_record("free", DatasetLicense.CC0_1_0),), path=tmp_path,
                      allow_analysis=False, allow_redistribution=False)


def test_metric_projection_identity_for_known_metric_rectangle():
    # 坐标需落在 EPSG:28992 的定义域内：RD New 的合法 easting 从 646 起步，
    # 原点附近的 (0,0) 是假声明，会被 _verify_declared_crs 拒。
    ox, oy = 155000.0, 463000.0
    geometry = Polygon([(ox, oy), (ox + 100, oy), (ox + 100, oy + 50), (ox, oy + 50), (ox, oy)])
    projected, crs = to_metric_crs(geometry, source_crs="EPSG:28992")
    assert crs == "EPSG:28992"
    assert abs(projected.area - 5000.0) / 5000.0 < 1e-6


def test_geographic_crs_guard_still_rejects_degrees():
    with pytest.raises(ValueError, match="单位是度"):
        CoverageProblem.model_validate({
            "problem_id": "bad",
            "field": {
                "geometry_id": "field",
                "exterior": [
                    {"x": 0, "y": 0}, {"x": 1, "y": 0}, {"x": 1, "y": 1}, {"x": 0, "y": 0}
                ],
            },
            "frame": {"crs": "EPSG:4326"},
        })


def test_fields2benchmark_country_metadata_is_explicit(tmp_path):
    import zipfile
    import shapely
    from agriautolab.datasets.fields2benchmark import load_fields2benchmark_wkt_zip

    archive_path = tmp_path / "wkt.zip"
    # 每国的 fixture 需落在该国声明 CRS 的定义域内（可证伪检查）。
    origins = {"nl": (155000.0, 463000.0), "ee": (600000.0, 6500000.0), "lt": (500000.0, 6100000.0)}

    def rect(origin):
        ox, oy = origin
        return shapely.to_wkt(
            Polygon([(ox, oy), (ox + 10, oy), (ox + 10, oy + 5), (ox, oy + 5), (ox, oy)])
        )

    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("wkt/nl_field_1.wkt", rect(origins["nl"]))
        archive.writestr("wkt/ee_field_1.wkt", rect(origins["ee"]))
        archive.writestr("wkt/lt_field_1.wkt", rect(origins["lt"]))
    records = {record.field_id: record for record in load_fields2benchmark_wkt_zip(archive_path)}
    assert records["nl_field_1"].source == "PDOK/Nationaal-Georegister"
    assert records["nl_field_1"].license is DatasetLicense.PUBLIC_DOMAIN
    assert records["ee_field_1"].license is DatasetLicense.CC_BY_SA_3_0_EE
    assert records["lt_field_1"].license is DatasetLicense.NON_COMMERCIAL


def test_corpus_record_hash_changes_when_geometry_changes():
    from agriautolab.datasets.fields2benchmark import field_record_hash

    left = _record("same-id", DatasetLicense.CC0_1_0)
    right = FieldRecord(
        field_id=left.field_id,
        geometry=Polygon([(0, 0), (11, 0), (11, 5), (0, 5), (0, 0)]),
        source=left.source,
        license=left.license,
        source_crs=left.source_crs,
        working_crs=left.working_crs,
    )
    assert field_record_hash(left) != field_record_hash(right)


def test_self_intersecting_fields_are_quarantined_not_repaired(tmp_path):
    """真实数据策略（实测 350 块中 2 块自交）：剔除并记录，不 make_valid。"""
    import zipfile as zf

    from agriautolab.datasets.fields2benchmark import (
        export_corpus, load_fields2benchmark_wkt_zip_with_quarantine,
    )

    # nl_* 声明 EPSG:28992，坐标要落在 RD New 定义域内。
    bowtie = "POLYGON ((155000 463000, 155010 463010, 155010 463000, 155000 463010, 155000 463000))"
    square = "POLYGON ((155000 463000, 155010 463000, 155010 463010, 155000 463010, 155000 463000))"
    archive_path = tmp_path / "mixed.zip"
    with zf.ZipFile(archive_path, "w") as archive:
        archive.writestr("wkt/nl_good.wkt", square)
        archive.writestr("wkt/nl_bad.wkt", bowtie)

    records, quarantined = load_fields2benchmark_wkt_zip_with_quarantine(archive_path)
    assert [record.field_id for record in records] == ["nl_good"]
    assert [item.field_id for item in quarantined] == ["nl_bad"]
    assert "Self-intersection" in quarantined[0].reason

    manifest = export_corpus(records, path=tmp_path / "out",
                             allow_analysis=True, allow_redistribution=True,
                             quarantined=quarantined)
    payload = manifest.as_dict()
    assert payload["quarantined_field_ids"] == ["nl_bad"]
    assert payload["quarantine_reasons"] == [quarantined[0].reason]
    assert payload["n_input"] == 2 and payload["n_exported"] == 1
