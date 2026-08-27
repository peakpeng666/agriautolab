"""演化账本：哈希链式相连的演化历史，被淘汰的候选也必须记录。

只记成功候选就是发表偏倚——「演化找到了 3 个好启发式」和
「演化试了 40 个、37 个被闸门否决」是两个完全不同的主张，
后者才是可复现实验该有的记录。
evidence 层的 EvidenceLedger 与 EvidenceRecord 强类型绑定（运行证据），
Separate ledger maintained per benchmark run using the same hash-chain structure.
"""

from __future__ import annotations

from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict, Field

from agriautolab.contracts.errors import EvidenceChainError
from agriautolab.pipeline.hashing import content_hash


class GateRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    gate: str
    passed: bool
    detail: str


class ProvenanceRecord(BaseModel):
    """LLM 单次调用的 provenance，作为**深度不可变**的强类型模型入账。

    此前这里存的是普通 `dict`。pydantic 的 `frozen=True` 只禁止属性赋值，
    不阻止嵌套容器被改：拿到 `ledger.records` 的调用方写
    `record.provenance["prompt"] = ...` 就能改掉已经参与 entry hash 计算的内容，
    于是一个公开暴露的账本会在寻常的嵌套赋值之后**自发 verify() 失败**——
    与同一条记录里 tuple / 冻结模型字段的行为不一致。

    改成全标量字段的 frozen 模型后没有可变嵌套状态，哈希稳定。
    字段与 `proposer.CompletionResult` 一一对应（同 GateRecord 的镜像做法：
    账本模型不 import agent 内其他模块，保持可独立 import）。
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    # 约束与 proposer.CompletionResult 的构造期校验逐条对应。缺了它们，
    # 直接构造或从 JSON 还原的记录可以携带 top_p=1.5、负 token 数、负成本——
    # append() 照样对这些有限值算哈希、verify() 照样通过，证据链于是为一份
    # **违反公开 completion 契约、无法重建成合法 CompletionResult** 的 provenance
    # 背书。校验必须在两处都成立，不能只靠上游。
    model_id: str = Field(min_length=1)
    prompt: str
    response: str
    temperature: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    top_p: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    seed: int
    prompt_tokens: int = Field(ge=0)
    completion_tokens: int = Field(ge=0)
    cost: float = Field(ge=0.0, allow_inf_nan=False)
    latency_ms: float = Field(ge=0.0, allow_inf_nan=False)
    request_id: str = Field(min_length=1)


class EvolutionRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    round_index: int = Field(ge=0)
    algorithm_id: str = Field(min_length=1)
    proposal_hash: str = Field(min_length=64, max_length=64)
    # 候选槽位 id（agent/slots.py 的 SLOTS 注册表键；字面量是 DEFAULT_SLOT_ID 的
    # 镜像——本模块有意不依赖 agent 内其他模块，保持账本模型可独立 import）。
    # 演化账本从未落盘，无历史迁移问题；一旦开始落盘，slot_id 即成为
    # 证据身份（wire ID）永不改。
    slot_id: str = "swath_angle"
    compiled: bool
    gates: tuple[GateRecord, ...] = ()
    review_refuted: bool | None = None
    review_reasons: tuple[str, ...] = ()
    hypervolume_delta: float | None = None
    kept: bool
    # 记录 append 时刻的全程累计真实 run_pipeline 调用数（含轮前基线池 I×P、
    # gate counts (1 contract, 2 validation, 0 skipped) per candidate evaluation.
    evaluations_used: int = 0
    # 迄今各轮 hypervolume_delta 非 None 值的 running max，单调不减；
    # 任何 delta 仍为 None 时也保持上轮值。口径是 COCO/IOHprofiler 式的
    # "评估次数 → 当前最优"轨迹。
    cumulative_best_delta: float | None = None
    # LLM 调用的 provenance（任务 4）。MockProposer 不设置 → 恒为 None。
    # provenance 不进 candidate_identity：identity 仍由三元组
    # （algorithm_id/source_code/description）决定，provenance 仅作 evidence 链
    # 附加字段，replay 重建后逐位相同。用 ProvenanceRecord 而非 dict 是为了
    # 深度不可变——理由见该类 docstring。
    provenance: ProvenanceRecord | None = None


class EvolutionLedger:
    """链式账本：append 时用前一条哈希作盐，verify 复算全链。"""

    def __init__(self) -> None:
        self._records: list[tuple[str, EvolutionRecord]] = []   # (entry_hash, record)

    @property
    def records(self) -> tuple[EvolutionRecord, ...]:
        return tuple(record for _, record in self._records)

    def _entry_hash(self, previous_hash: str, record: EvolutionRecord) -> str:
        return content_hash({
            "previous_hash": previous_hash,
            "record": record.model_dump(mode="json"),
        })

    def append(self, record: EvolutionRecord) -> str:
        previous_hash = self._records[-1][0] if self._records else "0" * 64
        entry_hash = self._entry_hash(previous_hash, record)
        self._records.append((entry_hash, record))
        return entry_hash

    def verify(self) -> None:
        previous_hash = "0" * 64
        for entry_hash, record in self._records:
            expected = self._entry_hash(previous_hash, record)
            if entry_hash != expected:
                raise EvidenceChainError(f"演化账本在 {record.algorithm_id}（round {record.round_index}）处断链")
            previous_hash = entry_hash


def anytime_curve(records: Sequence[EvolutionRecord]) -> tuple[tuple[int, float | None], ...]:
    """COCO/IOHprofiler 式 anytime 轨迹：逐轮返回 (evaluations_used, cumulative_best_delta)。

    口径与 EvolutionRecord 的两个新字段严格一致——评估次数（含基线池与闸门）作为
    横轴，当前最优 ΔHV（running max，单调不减）作为纵轴。O(n)。
    """
    return tuple((record.evaluations_used, record.cumulative_best_delta) for record in records)
