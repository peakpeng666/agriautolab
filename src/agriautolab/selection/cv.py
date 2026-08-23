"""Block D 的 field-grouped CV 身份与冻结折指派。

选择层只消费这里生成的 field -> fold 映射，不在训练时重新随机划分。
折算法用 SHA-256(seed, field_id) 形成稳定伪随机顺序，再 round-robin 分配：
seed 真正参与计算，同时避免 NumPy / sklearn 版本变化改变既定折身份。
"""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from agriautolab.evidence.hashing import content_hash
from agriautolab.evidence.ledger import artifact_chain_entry, verify_artifact_chain

CV_ASSIGNMENT_SCHEMA_VERSION = 1
CV_ASSIGNMENT_ALGORITHM = "sha256-seeded-round-robin-v1"
CV_SEED = 20260822
CV_FOLDS = 10
CV_STUDY_ID = "AGRIPLAN-PARETO-001"
BLOCK_D_LEDGER_GENESIS_EVENT = "cv_assignment_sealed"


class CvFoldRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    field_id: str = Field(min_length=1)
    fold: int = Field(ge=1)


class CvAssignmentEvidence(BaseModel):
    """D1 折表的机器可验身份证据。"""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1]
    study_id: Literal["AGRIPLAN-PARETO-001"]
    algorithm: Literal["sha256-seeded-round-robin-v1"]
    seed: int
    n_folds: int = Field(ge=2)
    manifest_file_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    corpus_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    holdout_file_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    holdout_seal_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    n_all_fields: int = Field(ge=1)
    n_holdout_fields: int = Field(ge=0)
    n_training_fields: int = Field(ge=1)
    fold_sizes: dict[str, int]
    assignments: tuple[CvFoldRecord, ...]
    assignment_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    spec_hash: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def verify_internal_identity(self) -> "CvAssignmentEvidence":
        if self.n_training_fields != len(self.assignments):
            raise ValueError("n_training_fields 与 assignments 数量不一致")
        field_ids = [item.field_id for item in self.assignments]
        if field_ids != sorted(field_ids):
            raise ValueError("assignments 必须按 field_id 排序，保证规范序列化")
        if len(field_ids) != len(set(field_ids)):
            raise ValueError("同一 field_id 只能出现一次")
        if any(item.fold > self.n_folds for item in self.assignments):
            raise ValueError("fold 超出 [1, n_folds]")

        expected_sizes = Counter(item.fold for item in self.assignments)
        normalized_sizes = {str(index): expected_sizes[index] for index in range(1, self.n_folds + 1)}
        if self.fold_sizes != normalized_sizes:
            raise ValueError("fold_sizes 与 assignments 不一致")
        if max(expected_sizes.values()) - min(expected_sizes.values()) > 1:
            raise ValueError("round-robin 折大小不应相差超过 1")

        if self.assignment_hash != assignment_hash(self.assignments):
            raise ValueError("assignment_hash 与 assignments 不一致")
        if self.spec_hash != content_hash(_spec_payload(self)):
            raise ValueError("spec_hash 与 D1 完整规范不一致")
        return self


def _seeded_key(field_id: str, seed: int) -> bytes:
    return hashlib.sha256(f"{seed}\x1f{field_id}".encode("utf-8")).digest()


def assign_grouped_folds(
    field_ids: tuple[str, ...] | list[str],
    *,
    n_folds: int = CV_FOLDS,
    seed: int = CV_SEED,
) -> tuple[CvFoldRecord, ...]:
    """把互异 field_id 确定性分到近乎等大的折中。

    输入顺序不参与结果；同一田的所有派生实例只通过 field_id 查表，因此不可能
    跨折。这里不读取任何目标值、validator 状态或特征，折身份与结果完全独立。
    """
    raw = tuple(str(item) for item in field_ids)
    if not raw:
        raise ValueError("field_ids 不能为空")
    if any(not item for item in raw):
        raise ValueError("field_id 不能为空字符串")
    if len(raw) != len(set(raw)):
        raise ValueError("field_ids 必须互异；重复输入会掩盖分组错误")
    if n_folds < 2:
        raise ValueError("n_folds 必须 >= 2")
    if n_folds > len(raw):
        raise ValueError("n_folds 不能超过训练田数量")

    seeded_order = sorted(raw, key=lambda field_id: (_seeded_key(field_id, seed), field_id))
    fold_of = {field_id: index % n_folds + 1 for index, field_id in enumerate(seeded_order)}
    return tuple(CvFoldRecord(field_id=field_id, fold=fold_of[field_id]) for field_id in sorted(raw))


def assignment_hash(assignments: tuple[CvFoldRecord, ...]) -> str:
    """只绑定 field -> fold 明细；方便下游在不关心文件元数据时对账。"""
    return content_hash([{"field_id": item.field_id, "fold": item.fold} for item in assignments])


def _spec_payload(evidence: CvAssignmentEvidence | dict) -> dict:
    if isinstance(evidence, CvAssignmentEvidence):
        payload = evidence.model_dump(mode="json")
    else:
        payload = dict(evidence)
    payload.pop("spec_hash", None)
    return payload


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def field_ids_from_manifest(manifest: dict) -> tuple[str, ...]:
    """从 v7 manifest 的许可证表恢复完整 field universe。

    不能从 effective_pool_size_by_instance 反推全集：该映射是结果摘要，零有效池
    或前处理阶段无有效实例的困难田可能不出现。`licenses` 则由导出语料逐田写入，
    与结果无关，正好是 D1 需要的全语料身份源。
    """
    licenses = manifest.get("licenses")
    if not isinstance(licenses, dict) or not licenses:
        raise ValueError("manifest 缺少逐田 licenses，无法建立结果无关的 field universe")
    fields = tuple(sorted(str(field_id) for field_id in licenses))
    if any(not field_id for field_id in fields):
        raise ValueError("manifest licenses 含空 field_id")

    effective = manifest.get("effective_pool_size_by_instance")
    if isinstance(effective, dict):
        observed_fields: set[str] = set()
        for instance_id in effective:
            field_id, separator, _ = str(instance_id).partition(":")
            if not separator or not field_id:
                raise ValueError(f"无法从 instance_id 恢复 field_id：{instance_id!r}")
            observed_fields.add(field_id)
        unknown = sorted(observed_fields - set(fields))
        if unknown:
            raise ValueError(f"effective-pool 摘要引用了 licenses 不存在的田：{unknown}")
    return fields


def build_cv_assignment_evidence(
    manifest_path: str | Path,
    holdout_path: str | Path,
    *,
    n_folds: int = CV_FOLDS,
    seed: int = CV_SEED,
) -> CvAssignmentEvidence:
    """由冻结 v7 manifest + holdout seal 构造唯一 D1 折表。"""
    manifest_file = Path(manifest_path)
    holdout_file = Path(holdout_path)
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    holdout = json.loads(holdout_file.read_text(encoding="utf-8"))

    all_fields = field_ids_from_manifest(manifest)
    holdout_fields = tuple(str(item) for item in holdout.get("field_ids", ()))
    if len(holdout_fields) != len(set(holdout_fields)):
        raise ValueError("holdout seal 含重复 field_id")
    unknown_holdout = sorted(set(holdout_fields) - set(all_fields))
    if unknown_holdout:
        raise ValueError(f"holdout 含 manifest 不存在的田：{unknown_holdout}")
    training_fields = tuple(sorted(set(all_fields) - set(holdout_fields)))
    assignments = assign_grouped_folds(training_fields, n_folds=n_folds, seed=seed)
    counts = Counter(item.fold for item in assignments)

    base = {
        "schema_version": CV_ASSIGNMENT_SCHEMA_VERSION,
        "study_id": CV_STUDY_ID,
        "algorithm": CV_ASSIGNMENT_ALGORITHM,
        "seed": seed,
        "n_folds": n_folds,
        "manifest_file_sha256": _sha256_file(manifest_file),
        "corpus_hash": str(manifest["corpus_hash"]),
        "holdout_file_sha256": _sha256_file(holdout_file),
        "holdout_seal_hash": str(holdout["seal_hash"]),
        "n_all_fields": len(all_fields),
        "n_holdout_fields": len(holdout_fields),
        "n_training_fields": len(training_fields),
        "fold_sizes": {str(index): counts[index] for index in range(1, n_folds + 1)},
        "assignments": [item.model_dump(mode="json") for item in assignments],
        "assignment_hash": assignment_hash(assignments),
    }
    base["spec_hash"] = content_hash(base)
    return CvAssignmentEvidence.model_validate(base)


def write_cv_assignment(evidence: CvAssignmentEvidence, path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(evidence.model_dump(mode="json"), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def cv_assignment_ledger_payload(evidence: CvAssignmentEvidence, assignment_path: str | Path) -> dict:
    """把 D1 折表绑定到 Block D 分析链；不修改冻结 v7 语料账本。"""
    path = Path(assignment_path)
    return {
        "event": BLOCK_D_LEDGER_GENESIS_EVENT,
        "study_id": evidence.study_id,
        "cv_assignment_file_sha256": _sha256_file(path),
        "assignment_hash": evidence.assignment_hash,
        "spec_hash": evidence.spec_hash,
        "manifest_file_sha256": evidence.manifest_file_sha256,
        "corpus_hash": evidence.corpus_hash,
        "holdout_file_sha256": evidence.holdout_file_sha256,
        "holdout_seal_hash": evidence.holdout_seal_hash,
        "seed": evidence.seed,
        "n_folds": evidence.n_folds,
        "n_training_fields": evidence.n_training_fields,
    }


def seal_cv_assignment_in_block_d_ledger(
    evidence: CvAssignmentEvidence,
    assignment_path: str | Path,
    ledger_path: str | Path,
) -> dict:
    """把 CV 折表封为 Block D 分析账本的 genesis；重复执行只允许精确重放。

    后续 D2/D3 可在同一 JSONL 链上追加。若链已存在且第一条与当前折表不一致，
    直接失败，禁止用“重新生成”覆盖既有分析历史。
    """
    ledger_file = Path(ledger_path)
    payload = cv_assignment_ledger_payload(evidence, assignment_path)
    expected = artifact_chain_entry(0, "0" * 64, payload)

    if ledger_file.exists():
        entries = tuple(
            json.loads(line)
            for line in ledger_file.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
        verify_artifact_chain(entries)
        if not entries:
            raise ValueError("Block D ledger 文件存在但为空；拒绝静默覆盖")
        if entries[0] != expected:
            raise ValueError("Block D ledger genesis 与当前 D1 折表不一致；拒绝改写分析历史")
        return entries[0]

    ledger_file.parent.mkdir(parents=True, exist_ok=True)
    ledger_file.write_text(json.dumps(expected, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    verify_artifact_chain((expected,))
    return expected
