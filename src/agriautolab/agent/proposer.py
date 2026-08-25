"""启发式提议者：LLM 后端可注入，测试只用确定性 mock。

候选代码的契约槽位（这是 Agent 层唯一开放的算法自由度）：

    def swath_angle_offset_rad(features: Mapping[str, float]) -> float

返回相对地块 PCA 主轴的扫掠角偏移。特征是旋转不变的（features/invariance.py），
偏移量因此按构造旋转不变——这不变性由第四道闸（invariance gate）强制兑现，
不靠候选代码自觉。

槽位分三处登记：agent/slots.py 的 SLOTS（闸门与演化循环语义）、本模块的
PROMPT_TEMPLATES（LLM 提示词）与 MOCK_CANDIDATES_BY_SLOT（确定性 mock 候选
清单）。本模块按 ProposalContext.slot_id 分派；漏登记 SLOTS 会在 evolve_pool
处 ValueError，漏登记本模块两表会在 propose/build_prompt 时 KeyError——
都 fail-closed，三表键一致性由 tests/agent/test_slots.py 钉住。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

import numpy as np

from agriautolab.contracts.enums import CoverageStage


@dataclass(frozen=True)
class ProposalContext:
    stage: CoverageStage
    round_index: int
    pool_config_ids: tuple[str, ...]
    # DEFAULT_SLOT_ID 的字面量镜像：本模块有意不依赖 slots.py（proposer 可独立于
    # 槽位注册表被 import），与注册表键的一致性由 tests/agent/test_slots.py 钉住。
    slot_id: str = "swath_angle"


@dataclass(frozen=True)
class ProposalCandidate:
    algorithm_id: str
    source_code: str
    description: str
    # LLM 调用 provenance（任务 4）：MockProposer 不设置，恒为 None。
    # identity 三元组（algorithm_id/source_code/description）不含 provenance，
    # 因此 provenance 不进 candidate_identity 哈希。
    provenance: CompletionResult | None = None


class HeuristicProposer(Protocol):
    def propose(self, *, stage: CoverageStage, context: ProposalContext, rng: np.random.Generator) -> ProposalCandidate:
        ...


# 写死的候选清单：每个都是完整、可编译、契约合规的启发式。
# 注意源码里没有 import：沙箱把 math 放进受限内建，import 是静态扫描的禁令。
# Mock 从中按 rng 取——完全 hermetic：无网络、无时钟、无全局随机。
MOCK_CANDIDATES: tuple[ProposalCandidate, ...] = (
    ProposalCandidate(
        algorithm_id="evolved_offset_zero",
        source_code=(
            "def swath_angle_offset_rad(features):\n"
            "    return 0.0\n"
        ),
        description="恒取主轴方向（对照组：与 principal_axis 等价的退化候选）",
    ),
    ProposalCandidate(
        algorithm_id="evolved_offset_diagonal",
        source_code=(
            "def swath_angle_offset_rad(features):\n"
            "    return math.pi / 6.0\n"
        ),
        description="固定偏移 pi/6：往斜向偏一点的常数策略",
    ),
    ProposalCandidate(
        algorithm_id="evolved_offset_elongation_driven",
        source_code=(
            "def swath_angle_offset_rad(features):\n"
            "    elongation = features.get('elongation', 1.0)\n"
            "    return min(0.3 * (elongation - 1.0), math.pi / 4.0)\n"
        ),
        description="越不细长越敢斜：偏移随 elongation 线性增长，上限 pi/4",
    ),
    ProposalCandidate(
        algorithm_id="evolved_offset_row_conflict_driven",
        source_code=(
            "def swath_angle_offset_rad(features):\n"
            "    conflict = features.get('row_angle_vs_principal', 0.0)\n"
            "    return 0.5 * conflict\n"
        ),
        description="顺行-顺形状冲突越大，越往行方向让一半",
    ),
)

# 每个槽位一份确定性候选清单：MockProposer 按 ProposalContext.slot_id 分派。
# 未知 slot_id 直接 KeyError（fail-closed），不静默回退。
MOCK_CANDIDATES_BY_SLOT: dict[str, tuple[ProposalCandidate, ...]] = {
    "swath_angle": MOCK_CANDIDATES,
}


class MockProposer:
    """确定性 mock：从写死清单里按注入的 rng 取，序列可复现。"""

    def propose(self, *, stage: CoverageStage, context: ProposalContext, rng: np.random.Generator) -> ProposalCandidate:
        candidates = MOCK_CANDIDATES_BY_SLOT[context.slot_id]
        index = int(rng.integers(0, len(candidates)))
        return candidates[index]


class CompletionResult:
    """模型后端单次调用的完整结果（含 provenance 十一字段）。

    字段全部必填；__post_init__ 做 fail-closed 校验（model_id/request_id 非空、
    temperature/top_p 有限且在 [0,1]、tokens 为 int >= 0、cost/latency_ms 有限
    且 >= 0）。这是 evidence 链的入口——任何字段缺失都视同未做 provenance。

    to_dict 返回 JSON 可序列化 dict；replay_candidate 用其离线重建 ProposalCandidate。
    """

    __slots__ = (
        "model_id", "prompt", "response", "temperature", "top_p", "seed",
        "prompt_tokens", "completion_tokens", "cost", "latency_ms", "request_id",
    )

    def __init__(
        self,
        *,
        model_id: str,
        prompt: str,
        response: str,
        temperature: float,
        top_p: float,
        seed: int,
        prompt_tokens: int,
        completion_tokens: int,
        cost: float,
        latency_ms: float,
        request_id: str,
    ) -> None:
        if not model_id:
            raise ValueError("CompletionResult.model_id 不能为空")
        if not request_id:
            raise ValueError("CompletionResult.request_id 不能为空")
        for name, value in (("temperature", temperature), ("top_p", top_p)):
            try:
                f = float(value)
            except (TypeError, ValueError) as error:
                raise ValueError(f"CompletionResult.{name} 必须是有限浮点：{value!r}") from error
            if not (0.0 <= f <= 1.0) or not _isfinite(f):
                raise ValueError(f"CompletionResult.{name} 必须在 [0,1] 且有限：{f!r}")
        for name, value in (("prompt_tokens", prompt_tokens), ("completion_tokens", completion_tokens)):
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ValueError(f"CompletionResult.{name} 必须为 int >= 0：{value!r}")
        for name, value in (("cost", cost), ("latency_ms", latency_ms)):
            try:
                f = float(value)
            except (TypeError, ValueError) as error:
                raise ValueError(f"CompletionResult.{name} 必须是有限浮点：{value!r}") from error
            if not _isfinite(f) or f < 0.0:
                raise ValueError(f"CompletionResult.{name} 必须 >= 0 且有限：{f!r}")
        if not isinstance(seed, int) or isinstance(seed, bool):
            raise ValueError(f"CompletionResult.seed 必须为 int：{seed!r}")
        self.model_id = str(model_id)
        self.prompt = str(prompt)
        self.response = str(response)
        self.temperature = float(temperature)
        self.top_p = float(top_p)
        self.seed = int(seed)
        self.prompt_tokens = int(prompt_tokens)
        self.completion_tokens = int(completion_tokens)
        self.cost = float(cost)
        self.latency_ms = float(latency_ms)
        self.request_id = str(request_id)

    def to_dict(self) -> dict[str, Any]:
        """JSON 可序列化 dict；入账 / replay 唯一入口。"""
        return {
            "model_id": self.model_id,
            "prompt": self.prompt,
            "response": self.response,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "seed": self.seed,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "cost": self.cost,
            "latency_ms": self.latency_ms,
            "request_id": self.request_id,
        }


def _isfinite(value: float) -> bool:
    import math
    return math.isfinite(value)


class ModelClient(Protocol):
    def complete(self, prompt: str) -> CompletionResult:
        ...


PROMPT_TEMPLATES: dict[str, str] = {
    "swath_angle": """你在一个农业覆盖路径规划的算法演化循环里担任启发式提议者。

阶段：{stage}
当前池子的配置：{pool}
轮次：{round_index}

请只输出一个 Python 函数定义，不要任何解释：

    def swath_angle_offset_rad(features):
        ...

输入 features 是 dict[str, float]，可用键（全部无量纲或显式带单位）：
area_m2, perimeter_area_ratio, convexity_deficiency, elongation,
reflex_vertex_count, obstacle_count, obstacle_area_ratio,
row_angle_vs_principal, turning_ratio, swath_count_at_minwidth。

返回值：相对地块 PCA 主轴的扫掠角偏移（弧度），必须在 [-pi/2, pi/2] 内且有限。
可用内建：math, len, range, min, max, abs, sum, enumerate, sorted, tuple, list, float, int。
禁止 import、open、eval、exec、双下划线属性。代码会在受限沙箱里执行并过四道闸。
目标：让 Pareto 前沿的超体积增大（造互补性，不是造单项冠军）。
""",
}

# 单槽位时代的公开名：swath 槽位提示词模板的兼容别名（PROMPT_TEMPLATES 的值本体）。
PROMPT_TEMPLATE = PROMPT_TEMPLATES["swath_angle"]


class LLMProposer:
    """真实模型后端。本模块不发起任何网络请求，只定义接口与提示词模板。

    模型客户端由构造注入（真模型由调用方接入）；不注入就调用是配置错误，
    当场报错而不是降级到 mock——静默降级会让「测试后端」混进真实证据链。
    """

    def __init__(self, client: ModelClient | None = None) -> None:
        self._client = client

    def build_prompt(self, *, stage: CoverageStage, context: ProposalContext) -> str:
        return PROMPT_TEMPLATES[context.slot_id].format(
            stage=stage.value,
            pool=", ".join(context.pool_config_ids),
            round_index=context.round_index,
        )

    def propose(self, *, stage: CoverageStage, context: ProposalContext, rng: np.random.Generator) -> ProposalCandidate:
        if self._client is None:
            raise RuntimeError(
                "LLMProposer 没有注入模型客户端：本模块不携带网络后端；"
                "测试请用 MockProposer"
            )
        prompt = self.build_prompt(stage=stage, context=context)
        result = self._client.complete(prompt)
        return _candidate_from_completion(context.round_index, result)


def _candidate_from_completion(round_index: int, result: CompletionResult) -> ProposalCandidate:
    """从 CompletionResult 构造 ProposalCandidate，provenance 字段携带原 result。

    在线构造与 replay_candidate 共享此函数 → identity 逐位一致有结构性保证。
    """
    return ProposalCandidate(
        algorithm_id=f"evolved_llm_{round_index:03d}",
        source_code=result.response,
        description="LLM 提议（注入真实后端后产生）",
        provenance=result,
    )


def replay_candidate(round_index: int, result: CompletionResult) -> ProposalCandidate:
    """离线重放：直接委托 _candidate_from_completion，docstring 明言无网络、确定性。

    重放时 result.response 与 result.prompt 必须与在线调用逐位相同；replay 与
    在线产生的 ProposalCandidate 在 identity（三元组 algorithm_id/source_code/
    description）上逐位相等。
    """
    return _candidate_from_completion(round_index, result)
