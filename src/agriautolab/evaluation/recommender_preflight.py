"""H3 确证执行前硬门。

所有冻结身份检查必须先于 joblib 反序列化和 holdout runs 读取。
这个模块只做字节身份与链式前置条件验证，不执行任何统计分析。
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from agriautolab.evaluation.records import sha256_file
from agriautolab.pipeline import jsonl_log


@dataclass(frozen=True)
class H3Preflight:
    entries: tuple[dict, ...]
    cv: dict
    holdout: dict
    metadata: dict
    pool_hash: str
    selection_protocol_hash: str


def _load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"预期 JSON object：{path}")
    return value


def _read_verified_ledger(path: Path) -> tuple[dict, ...]:
    entries = jsonl_log.read_entries(path)
    jsonl_log.verify_entries(entries)
    return entries


def _require_artifact(entries: tuple[dict, ...], index: int, artifact: str) -> dict:
    if len(entries) <= index:
        raise ValueError(f"Block D ledger 缺少 index={index}")
    entry = entries[index]
    if entry.get("index") != index or entry.get("payload", {}).get("artifact") != artifact:
        raise ValueError(f"Block D index={index} 必须是 {artifact}")
    return entry


def _require_genesis(entries: tuple[dict, ...]) -> dict:
    if not entries:
        raise ValueError("Block D ledger 为空")
    entry = entries[0]
    if entry.get("index") != 0 or entry.get("payload", {}).get("event") != "cv_assignment_sealed":
        raise ValueError("Block D index=0 必须是 cv_assignment_sealed")
    return entry


def _require_d1_d6_prefix(entries: tuple[dict, ...]) -> tuple[dict, dict, dict, dict, dict]:
    d1 = _require_genesis(entries)
    d2 = _require_artifact(entries, 1, "pool_census")
    d3 = _require_artifact(entries, 2, "selection_protocol_v1")
    d4 = _require_artifact(entries, 3, "selection_cv_result")
    _require_artifact(entries, 4, "h1_confirmatory_result")
    d6 = _require_artifact(entries, 5, "h2_confirmatory_result")
    return d1, d2, d3, d4, d6


def _reject_existing_h3(entries: tuple[dict, ...]) -> None:
    if any(
        entry.get("payload", {}).get("artifact") == "h3_confirmatory_result"
        for entry in entries
    ):
        raise ValueError("H3 已封存；禁止再次执行 holdout。仅允许离线验证既有证据。")


def ensure_h3_holdout_unsealed(ledger_path: Path) -> None:
    """仅读 ledger 的最前置闸门；已封 H3 时不得触碰其他 H3 输入。"""
    entries = _read_verified_ledger(ledger_path)
    _require_d1_d6_prefix(entries)
    _reject_existing_h3(entries)


def verify_h3_preflight(
    *,
    ledger_path: Path,
    runs_path: Path,
    configs_path: Path,
    vehicles_path: Path,
    cv_path: Path,
    holdout_path: Path,
    pool_census_path: Path,
    selection_protocol_path: Path,
    h2_result_path: Path,
    model_path: Path,
    metadata_path: Path,
    protocol_bundle_hash: str,
    reject_if_h3_sealed: bool,
) -> H3Preflight:
    """验证 H3 所有冻结输入；返回解析后的安全元数据。

    `reject_if_h3_sealed=True` 时，只要 ledger 已含 H3，就在读取其他输入前拒绝。
    CLI 的 holdout 模式还会先调用 `ensure_h3_holdout_unsealed`，确保连协议文件
    哈希都不会在已封存状态下被重新消费。
    """
    entries = _read_verified_ledger(ledger_path)
    d1, d2, d3, d4, d6 = _require_d1_d6_prefix(entries)
    if reject_if_h3_sealed:
        _reject_existing_h3(entries)

    if sha256_file(pool_census_path) != d2["payload"].get("file_sha256"):
        raise ValueError("D2 pool census 文件与 ledger index=1 绑定字节不一致")
    if sha256_file(selection_protocol_path) != d3["payload"].get("file_sha256"):
        raise ValueError("D3 selection protocol 文件与 ledger index=2 绑定字节不一致")
    if sha256_file(h2_result_path) != d6["payload"].get("result_file_sha256"):
        raise ValueError("H2 结果文件与 ledger index=5 绑定字节不一致")
    if protocol_bundle_hash != d6["payload"].get("protocol_bundle_hash"):
        raise ValueError("H3 预注册协议 bundle 与已封 H2 协议身份不一致")

    census = _load_json(pool_census_path)
    selection_protocol = _load_json(selection_protocol_path)
    h2_result = _load_json(h2_result_path)

    sources = census.get("sources", {})
    expected_inputs = {
        "runs.parquet": (sha256_file(runs_path), sources.get("runs_parquet_sha256")),
        "corpus_13.json": (sha256_file(configs_path), sources.get("configs_sha256")),
        "vehicles.json": (sha256_file(vehicles_path), sources.get("vehicles_sha256")),
        "cv_assignment.json": (sha256_file(cv_path), d1["payload"].get("cv_assignment_file_sha256")),
        "holdout_seal.json": (sha256_file(holdout_path), d1["payload"].get("holdout_file_sha256")),
    }
    mismatched = {
        name: {"actual": actual, "expected": expected}
        for name, (actual, expected) in expected_inputs.items()
        if actual != expected
    }
    if mismatched:
        raise ValueError(f"H3 冻结输入字节漂移：{mismatched}")

    # D4 模型二进制和 metadata 必须在 joblib.load 之前逐字节绑定。
    model_sha256 = sha256_file(model_path)
    metadata_sha256 = sha256_file(metadata_path)
    if model_sha256 != d4["payload"].get("model_file_sha256"):
        raise ValueError("H3 模型字节与 D4 ledger index=3 绑定模型不一致")
    if metadata_sha256 != d4["payload"].get("metadata_file_sha256"):
        raise ValueError("H3 模型 metadata 与 D4 ledger index=3 绑定字节不一致")

    cv = _load_json(cv_path)
    holdout = _load_json(holdout_path)
    metadata = _load_json(metadata_path)

    if cv.get("spec_hash") != d1["payload"].get("spec_hash"):
        raise ValueError("CV spec_hash 与 D1 genesis 不一致")
    if holdout.get("seal_hash") != d1["payload"].get("holdout_seal_hash"):
        raise ValueError("holdout seal_hash 与 D1 genesis 不一致")

    if selection_protocol.get("cv_spec_hash") != cv.get("spec_hash"):
        raise ValueError("D3 selection protocol 的 CV identity 与 D1 不一致")
    if selection_protocol.get("spec_hash") != d4["payload"].get("protocol_hash"):
        raise ValueError("D4 模型协议与 D3 selection protocol 不一致")
    if selection_protocol.get("pool_hash") != d3["payload"].get("pool_hash"):
        raise ValueError("D3 selection protocol 的 pool_hash 与 ledger 不一致")

    expected_metadata = {
        "protocol_hash": selection_protocol.get("spec_hash"),
        "cv_spec_hash": cv.get("spec_hash"),
        "pool_hash": selection_protocol.get("pool_hash"),
    }
    metadata_mismatch = {
        key: {"actual": metadata.get(key), "expected": expected}
        for key, expected in expected_metadata.items()
        if metadata.get(key) != expected
    }
    if metadata_mismatch:
        raise ValueError(f"D4 recommender metadata 身份不一致：{metadata_mismatch}")

    h2_identity = h2_result.get("identity", {})
    predecessor_expected = {
        "runs_parquet_sha256": expected_inputs["runs.parquet"][0],
        "configs_sha256": expected_inputs["corpus_13.json"][0],
        "vehicles_sha256": expected_inputs["vehicles.json"][0],
        "pool_hash": selection_protocol.get("pool_hash"),
        "protocol_bundle_hash": protocol_bundle_hash,
    }
    predecessor_mismatch = {
        key: {"actual": h2_identity.get(key), "expected": expected}
        for key, expected in predecessor_expected.items()
        if h2_identity.get(key) != expected
    }
    if predecessor_mismatch:
        raise ValueError(f"H2 前序与 H3 数据/协议身份不一致：{predecessor_mismatch}")

    holdout_fields = tuple(sorted(str(field_id) for field_id in holdout.get("field_ids", ())))
    training_fields = tuple(sorted(str(item["field_id"]) for item in cv.get("assignments", ())))
    if len(holdout_fields) != 70 or len(training_fields) != 165:
        raise ValueError("H3 冻结划分必须是 70 holdout / 165 training fields")
    if set(holdout_fields) & set(training_fields):
        raise ValueError("留出集与训练折重叠：封存身份已坏")

    return H3Preflight(
        entries=entries,
        cv=cv,
        holdout=holdout,
        metadata=metadata,
        pool_hash=str(selection_protocol["pool_hash"]),
        selection_protocol_hash=str(selection_protocol["spec_hash"]),
    )
