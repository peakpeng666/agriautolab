"""Fields2Benchmark 数据接入：不猜许可证，不在经纬度上做米制几何计算。"""

from __future__ import annotations

import json
import math
import zipfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterable

import shapely
from pyproj import CRS, Transformer
from shapely.geometry.base import BaseGeometry
from shapely.ops import transform

from agriautolab.contracts.errors import GeometryValidationError
from agriautolab.contracts.geometry import GeometryFrame
from agriautolab.pipeline.hashing import content_hash
from agriautolab.pipeline import jsonl_log
from agriautolab.geometry.hashing import geometry_hash
from agriautolab.geometry.validate import validate_geometry


class DatasetLicense(str, Enum):
    """数据记录的实际许可；UNKNOWN 永远不能进入可导出语料。"""

    PUBLIC_DOMAIN = "public-domain"
    CC0_1_0 = "cc0-1.0"
    CC_BY_4_0 = "cc-by-4.0"
    CC_BY_SA_3_0_EE = "cc-by-sa-3.0-ee"
    NON_COMMERCIAL = "non-commercial"
    UNKNOWN = "unknown"


class DatasetLicenseError(ValueError):
    """许可证无法核实或违反导出策略。"""


class CrsDeclarationError(ValueError):
    """声明的 CRS 与坐标量程不自洽。

    存在的理由：F2B wkt.zip 实为 WGS84 经纬度，门户声明
    EPSG:3301/28992/3346，to_metric_crs 走了「已是米制」快速通道、度坐标原样流出，
    5.0 米地头被当 5.0 度用，地块被内缩吃光。当时是靠地块归零才被发现的——
    也就是说，只要错得不够狠，就不会有任何东西响。
    """


@dataclass(frozen=True)
class FieldRecord:
    field_id: str
    geometry: BaseGeometry
    source: str
    license: DatasetLicense
    source_crs: str
    working_crs: str


@dataclass(frozen=True)
class ExportManifest:
    n_input: int
    n_exported: int
    exported_field_ids: tuple[str, ...]
    filtered_non_commercial_ids: tuple[str, ...]
    quarantined_field_ids: tuple[str, ...]
    quarantine_reasons: tuple[str, ...]
    contains_non_commercial: bool
    warning: str | None
    corpus_hash: str
    manifest_hash: str

    def as_dict(self) -> dict[str, object]:
        return {
            "n_input": self.n_input,
            "n_exported": self.n_exported,
            "exported_field_ids": list(self.exported_field_ids),
            "filtered_non_commercial_ids": list(self.filtered_non_commercial_ids),
            "quarantined_field_ids": list(self.quarantined_field_ids),
            "quarantine_reasons": list(self.quarantine_reasons),
            "contains_non_commercial": self.contains_non_commercial,
            "warning": self.warning,
            "corpus_hash": self.corpus_hash,
            "manifest_hash": self.manifest_hash,
        }


# Zenodo 14524735 把荷兰来源列为 PDOK + Nationaal Georegister，但 WKT 文件名只含国家前缀，
# 不能逐地块反推出二者之一；因此 provenance 明确保留组合来源，而不是伪造“全部来自 PDOK”。
# 爱沙尼亚许可链接解析到 CC BY-SA 3.0 EE。未在上游元数据出现的国家必须 UNKNOWN。
_SOURCE_BY_PREFIX = {
    "NL": ("PDOK/Nationaal-Georegister", DatasetLicense.PUBLIC_DOMAIN, "EPSG:28992"),
    "EE": ("INSPIRE-EE", DatasetLicense.CC_BY_SA_3_0_EE, "EPSG:3301"),
    "LT": ("geoportal-lt", DatasetLicense.NON_COMMERCIAL, "EPSG:3346"),
}


def _crs_name(crs: CRS) -> str:
    authority = crs.to_authority()
    return f"{authority[0]}:{authority[1]}" if authority else crs.to_string()


_GEOGRAPHIC_BOUNDS = (180.0, 90.0)
# 投影坐标的量级下界。UTM easting 最小约 1.6e5，northing 在北半球 0 起步，
# 所以只用 |x| 判断；1e4 足够把度（|x|<=180）与米区分开，又不会误伤小 easting。
_PROJECTED_MIN_ABS_X = 1.0e4


def _projected_extent(source: CRS) -> tuple[float, float, float, float] | None:
    """把声明 CRS 的 area_of_use（经纬度框）投到它自己坐标系里，得到有效数值范围。

    这是「用 pyproj 查 CRS 属性交叉判定」的落点：光看量程分不清
    「10 米见方的合法小 easting」与「经纬度」，但 area_of_use 分得清——
    RD New (EPSG:28992) 的合法 easting 从 646 起步，(0,0) 根本不在它的定义域里。

    边界留 1% 余量：area_of_use 是官方给的粗框，地块贴边时不该被误杀。
    """
    area = source.area_of_use
    if area is None:
        return None
    projector = Transformer.from_crs(CRS.from_epsg(4326), source, always_xy=True)
    xs: list[float] = []
    ys: list[float] = []
    for lon in (area.west, area.east):
        for lat in (area.south, area.north):
            x, y = projector.transform(lon, lat)
            if math.isfinite(x) and math.isfinite(y):
                xs.append(float(x))
                ys.append(float(y))
    if not xs or not ys:
        return None
    margin_x = (max(xs) - min(xs)) * 0.01
    margin_y = (max(ys) - min(ys)) * 0.01
    return (min(xs) - margin_x, min(ys) - margin_y, max(xs) + margin_x, max(ys) + margin_y)


def _verify_declared_crs(geometry: BaseGeometry, declared_crs: str) -> None:
    """声明的 CRS 必须与坐标量程自洽，否则抛 CrsDeclarationError。

    实测事故：F2B wkt.zip 实为 WGS84 经纬度，门户声明
    EPSG:3301/28992/3346；快速通道把 5.0 米地头当 5.0 度用，地块被内缩吃光。
    那次响了是因为地块归零；把 28992 误报成 3301 则是静默的，
    只让所有长度差几个百分点——正好是当时 path_length 残差的量级。

    判据：坐标落在 |x|<=180 且 |y|<=90 而声明投影坐标系 -> 抛；
    |x| > 1e4 而声明地理坐标系 -> 抛。

    陷阱：小范围投影坐标可能恰好落在 ±180 内（局部工程坐标系、或截断过的 easting），
    所以量程不是唯一判据——先用 pyproj 的 is_geographic 定性，再用量程验证，
    两者不一致才抛。只靠量程会把合法的小 easting 投影坐标误杀。

    作用域：本函数只能证伪「坐标不可能属于所声明的那个 CRS」这一档。
    把 EPSG:28992 误报成 EPSG:3301 时，如果坐标恰好同时落在两者的有效范围内，
    它抓不出来——那需要与权威边界或已知控制点对账。
    **这是纪律不是保证**，写在这里以免被当成后者。
    """
    source = CRS.from_user_input(declared_crs)
    min_x, min_y, max_x, max_y = geometry.bounds
    extreme_x = max(abs(min_x), abs(max_x))
    extreme_y = max(abs(min_y), abs(max_y))
    looks_geographic = extreme_x <= _GEOGRAPHIC_BOUNDS[0] and extreme_y <= _GEOGRAPHIC_BOUNDS[1]

    if source.is_geographic:
        if extreme_x > _PROJECTED_MIN_ABS_X:
            raise CrsDeclarationError(
                f"声明 {declared_crs}（地理坐标系，单位度）但坐标量程 |x|max={extreme_x!r} "
                f"远超 {_PROJECTED_MIN_ABS_X!r}：这批坐标是米制投影，声明错了"
            )
        return

    extent = _projected_extent(source)
    if extent is not None:
        west, south, east, north = extent
        inside = west <= min_x and max_x <= east and south <= min_y and max_y <= north
        if not inside:
            hint = "：这批坐标看着像经纬度" if looks_geographic else ""
            raise CrsDeclarationError(
                f"声明 {declared_crs} 但坐标落在它的有效范围之外{hint}"
                f"（实测 x∈[{min_x!r},{max_x!r}]，y∈[{min_y!r},{max_y!r}]；"
                f"该 CRS 有效范围 x∈[{west!r},{east!r}]，y∈[{south!r},{north!r}]）。"
                "F2B wkt.zip 就是这样：门户声明 EPSG:3301/28992/3346，实际是 WGS84 度，"
                "5.0 米地头被当 5.0 度用，地块被内缩吃光"
            )
        return

    # 没有 area_of_use 的投影 CRS（局部工程坐标系等）：退回纯量程判据。
    # 这条兜底比上面弱得多，但总比什么都不查强。
    if looks_geographic:
        raise CrsDeclarationError(
            f"声明 {declared_crs}（投影坐标系，单位米，且无 area_of_use 可交叉判定）"
            f"但坐标落在 |x|<=180、|y|<=90 内"
            f"（实测 x∈[{min_x!r},{max_x!r}]，y∈[{min_y!r},{max_y!r}]）：这批坐标像经纬度"
        )


def to_metric_crs(geometry: BaseGeometry, *, source_crs: str) -> tuple[BaseGeometry, str]:
    """把几何变换到米制 CRS，并返回目标 CRS 名称。

    先核对 source_crs 的声明与坐标量程自洽（_verify_declared_crs）：
    声明不核对就等于没有声明——这是地头宽度可证伪性那个洞的同构体。

    米制投影原样保留，避免不必要的重投影误差；经纬度按地块质心选局部 UTM。
    目标 CRS 必须进入 provenance，因为换一个投影，长度、面积与路径最优性都会一起改变。
    """
    validate_geometry(geometry)
    _verify_declared_crs(geometry, source_crs)
    source = CRS.from_user_input(source_crs)
    axis_units = {axis.unit_name.lower() for axis in source.axis_info if axis.unit_name}
    if source.is_projected and axis_units and all("metre" in unit or "meter" in unit for unit in axis_units):
        return geometry, _crs_name(source)

    to_wgs84 = Transformer.from_crs(source, CRS.from_epsg(4326), always_xy=True)
    centroid_wgs84 = transform(to_wgs84.transform, geometry.centroid)
    lon, lat = float(centroid_wgs84.x), float(centroid_wgs84.y)
    zone = int((lon + 180.0) // 6.0) + 1
    zone = min(max(zone, 1), 60)
    epsg = (32600 if lat >= 0.0 else 32700) + zone
    target = CRS.from_epsg(epsg)
    projector = Transformer.from_crs(source, target, always_xy=True)
    projected = transform(projector.transform, geometry)
    validate_geometry(projected)
    return projected, f"EPSG:{epsg}"


def field_record_hash(record: FieldRecord) -> str:
    return content_hash({
        "field_id": record.field_id,
        "source": record.source,
        "license": record.license.value,
        "source_crs": record.source_crs,
        "working_crs": record.working_crs,
        "geometry_hash": geometry_hash(record.geometry, GeometryFrame(crs=record.working_crs)),
    })


def _manifest_payload(records: tuple[FieldRecord, ...], filtered: tuple[str, ...],
                      warning: str | None, quarantined: tuple[QuarantinedField, ...]) -> dict[str, object]:
    hashes = tuple(field_record_hash(record) for record in records)
    return {
        "n_input": len(records) + len(filtered) + len(quarantined),
        "n_exported": len(records),
        "exported_field_ids": [record.field_id for record in records],
        "filtered_non_commercial_ids": list(filtered),
        "quarantined_field_ids": [item.field_id for item in quarantined],
        "quarantine_reasons": [item.reason for item in quarantined],
        "contains_non_commercial": any(record.license is DatasetLicense.NON_COMMERCIAL for record in records),
        "warning": warning,
        "corpus_hash": content_hash({"record_hashes": sorted(hashes)}),
    }


# 许可证 -> 允许的用途。**这是法律解读，待人裁定，不是已确认的结论。**
#
# 原文摘录见 docs/refs/licenses/fields2benchmark.md。判断依据（逐条）：
# - LT（113 块）上游元数据原文：
#     Naudojimo ribotumas (Use Limitation): Tik nekomerciniam naudojimui (Non-commercial use only)
#     Prieigos apribojimai (Access Constraints): Autoriaus teisės (Copyright)
#     Naudojimo apribojimai (Use Constraints): Autoriaus teisės (Copyright)
#   「Use Limitation = 非商业使用」限制的是**使用**；学术研究属于非商业使用，
#   因此 ANALYSIS 记为允许。而 Access/Use Constraints 只写「Copyright」——
#   没有任何再分发授权，默认版权即禁止再分发，因此 REDISTRIBUTION 记为不允许。
# - NL：CC0 1.0 + Public Domain Mark 1.0，两项用途都允许。
# - EE：CC BY-SA 3.0 EE，两项都允许（附署名与相同方式共享义务，由下游承担）。
#
# 陷阱：Zenodo 记录自身的 LICENSE 文件是 CC BY-SA 4.0（全文无 NonCommercial 条款），
# 而记录元数据字段写的是 CC-BY-4.0 —— 两者不一致。且无论哪个，F2B 都不可能
# 就 LT 部分授出它自己没有的再分发权。上游约束优先，不因打包而消失。
LICENSE_PERMITS_ANALYSIS = frozenset({
    DatasetLicense.PUBLIC_DOMAIN, DatasetLicense.CC0_1_0,
    DatasetLicense.CC_BY_SA_3_0_EE, DatasetLicense.NON_COMMERCIAL,
})
LICENSE_PERMITS_REDISTRIBUTION = frozenset({
    DatasetLicense.PUBLIC_DOMAIN, DatasetLicense.CC0_1_0, DatasetLicense.CC_BY_SA_3_0_EE,
})


def export_corpus(
    records: Iterable[FieldRecord], *, path: str | Path,
    allow_analysis: bool, allow_redistribution: bool,
    quarantined: tuple[QuarantinedField, ...] = (),
) -> ExportManifest:
    """导出可审计的 WKT JSONL 语料；用途必须由调用方逐项显式声明。

    为什么是两个开关而不是一个 allow_non_commercial：
    「用」与「发」是两件事。LT 的 113 块（占 350 的 32%）上游写的是
    「Non-commercial use only」+「Copyright」——非商业**使用**有明文许可，
    **再分发**没有任何授权。一刀切成一个布尔量，等于把「不能发」误读成「不能用」，
    白白丢掉 32% 的样本（235 -> 348，样本量 +48%）。

    UNKNOWN 先于用途策略检查：未知许可绝不能因为「恰好不是 NON_COMMERCIAL」而漏过。
    manifest_hash 自包含于 ledger 的首条 payload_hash，确保许可声明也进入证据链。

    **本函数不设默认值，且许可 -> 用途的映射是待裁定的法律解读**
    （见 LICENSE_PERMITS_* 上方的原文摘录）。调用方必须自己声明用途，
    代码不替任何人做法律判断。
    """
    incoming = tuple(records)
    unknown = tuple(record.field_id for record in incoming if record.license is DatasetLicense.UNKNOWN)
    if unknown:
        raise DatasetLicenseError("许可证 UNKNOWN 的记录禁止导出：" + ", ".join(unknown))
    if not allow_analysis and not allow_redistribution:
        raise DatasetLicenseError("至少要声明一项用途：allow_analysis 与 allow_redistribution 不能都为 False")

    required = set()
    if allow_analysis:
        required.add(LICENSE_PERMITS_ANALYSIS)
    if allow_redistribution:
        required.add(LICENSE_PERMITS_REDISTRIBUTION)

    def permitted(record: FieldRecord) -> bool:
        return all(record.license in allowed for allowed in required)

    filtered = tuple(record.field_id for record in incoming if not permitted(record))
    exported = tuple(record for record in incoming if permitted(record))
    warning = (
        "本导出包含仅限非商业使用的数据；已按 allow_redistribution=False 导出，不得公开再分发"
        if any(record.license is DatasetLicense.NON_COMMERCIAL for record in exported)
        else None
    )
    payload = _manifest_payload(exported, filtered, warning, quarantined)
    payload["n_input"] = len(incoming) + len(quarantined)
    manifest_hash = content_hash(payload)
    manifest = ExportManifest(
        n_input=len(incoming) + len(quarantined),
        n_exported=len(exported),
        exported_field_ids=tuple(record.field_id for record in exported),
        filtered_non_commercial_ids=filtered,
        quarantined_field_ids=tuple(item.field_id for item in quarantined),
        quarantine_reasons=tuple(item.reason for item in quarantined),
        contains_non_commercial=bool(payload["contains_non_commercial"]),
        warning=warning,
        corpus_hash=str(payload["corpus_hash"]),
        manifest_hash=manifest_hash,
    )

    root = Path(path)
    root.mkdir(parents=True, exist_ok=True)
    rows = []
    for record in exported:
        rows.append(json.dumps({
            "field_id": record.field_id,
            "source": record.source,
            "license": record.license.value,
            "source_crs": record.source_crs,
            "working_crs": record.working_crs,
            "wkt": shapely.to_wkt(shapely.normalize(record.geometry), rounding_precision=-1, trim=True),
        }, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    (root / "fields.jsonl").write_text("\n".join(rows) + ("\n" if rows else ""), encoding="utf-8")
    (root / "manifest.json").write_text(
        json.dumps(manifest.as_dict(), ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    ledger_payload = {"artifact": "export_manifest", "manifest_hash": manifest_hash}
    ledger_entry = jsonl_log.entry(0, ledger_payload)
    (root / "ledger.jsonl").write_text(
        json.dumps(ledger_entry, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


@dataclass(frozen=True)
class QuarantinedField:
    """被隔离的地块：几何不合法（如自交），剔除而非修复。

    真实 EuroCrops 数据实测 350 块中 2 块自交（具体 id 与隔离记录见 AUDIT_NOTE，
    实测如此）。本仓库禁止 make_valid：隐式修复的拓扑会使后续
    所有面积指标建立在一块没人见过的多边形上；正确的处置是显式剔除并记录，
    剔除本身进入 manifest 与证据链。
    """

    field_id: str
    reason: str


def load_fields2benchmark_wkt_zip_with_quarantine(
    path: str | Path,
) -> tuple[tuple[FieldRecord, ...], tuple[QuarantinedField, ...]]:
    """读取地块并隔离不合法几何；文件名前缀决定来源、许可与原始 CRS。

    返回 (合法记录, 隔离清单)。隔离不是修复：被剔除的地块连同 shapely 的
    is_valid_reason 一起进清单，导出端把它写进 manifest。
    未知国家前缀仍标记 UNKNOWN 交由导出闸门拒绝——新版本数据集扩国家时
    会立即抛错，不会静默继承错误许可。
    """
    records: list[FieldRecord] = []
    quarantined: list[QuarantinedField] = []
    with zipfile.ZipFile(path) as archive:
        for name in sorted(item for item in archive.namelist() if item.lower().endswith(".wkt")):
            field_id = Path(name).stem
            prefix = field_id[:2].upper()
            source, license_value, source_crs = _SOURCE_BY_PREFIX.get(
                prefix, ("unknown", DatasetLicense.UNKNOWN, "EPSG:4326")
            )
            text = archive.read(name).decode("utf-8").strip()
            geometry = shapely.from_wkt(text)
            try:
                validate_geometry(geometry, geometry_id=field_id)
            except GeometryValidationError:
                quarantined.append(QuarantinedField(
                    field_id=field_id, reason=str(shapely.is_valid_reason(geometry)),
                ))
                continue
            metric, working_crs = to_metric_crs(geometry, source_crs=source_crs)
            records.append(FieldRecord(
                field_id=field_id,
                geometry=metric,
                source=source,
                license=license_value,
                source_crs=source_crs,
                working_crs=working_crs,
            ))
    return tuple(records), tuple(quarantined)


def load_fields2benchmark_wkt_zip(path: str | Path) -> tuple[FieldRecord, ...]:
    """兼容入口：只返回合法记录。需要隔离清单的调用方请用 *_with_quarantine。"""
    return load_fields2benchmark_wkt_zip_with_quarantine(path)[0]


def load_exported_corpus(path: str | Path) -> tuple[FieldRecord, ...]:
    """读取 export_corpus 产生的 fields.jsonl；不从 manifest 反推或补猜许可证。"""
    root = Path(path)
    rows = []
    for line_number, line in enumerate((root / "fields.jsonl").read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        item = json.loads(line)
        try:
            license_value = DatasetLicense(item["license"])
        except ValueError as error:
            raise DatasetLicenseError(f"fields.jsonl 第 {line_number} 行许可证不在枚举中：{item.get('license')!r}") from error
        geometry = shapely.from_wkt(item["wkt"])
        validate_geometry(geometry, geometry_id=str(item["field_id"]))
        rows.append(FieldRecord(
            field_id=str(item["field_id"]),
            geometry=geometry,
            source=str(item["source"]),
            license=license_value,
            source_crs=str(item["source_crs"]),
            working_crs=str(item["working_crs"]),
        ))
    return tuple(rows)
