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
    "route_order": (
        ProposalCandidate(
            algorithm_id="route_nearest_neighbor",
            source_code=(
                "def next_swath_score(state, candidate):\n"
                "    return candidate.get('distance_norm', 0.0)\n"
            ),
            description="贪心最近邻：每次选出口到条带入口距离归一化最小的未访问条带",
        ),
        ProposalCandidate(
            algorithm_id="route_outward_axis_order",
            source_code=(
                "def next_swath_score(state, candidate):\n"
                "    return -candidate.get('axis_offset_norm', 0.0)\n"
            ),
            description="由外向内：先访问离主轴最远的条带（axis_offset_norm 的反序）",
        ),
        ProposalCandidate(
            algorithm_id="route_axis_offset_order",
            source_code=(
                "def next_swath_score(state, candidate):\n"
                "    return candidate.get('axis_offset_norm', 0.0)\n"
            ),
            description="由内向外：先访问离主轴最近的条带（axis_offset_norm 升序）",
        ),
        ProposalCandidate(
            algorithm_id="route_mixed",
            source_code=(
                "def next_swath_score(state, candidate):\n"
                "    return 0.6 * candidate.get('distance_norm', 0.0) + 0.4 * candidate.get('axis_offset_norm', 0.0)\n"
            ),
            description="距离与投影加权混合；权重 0.6/0.4 写死于源码（不来自 features）",
        ),
    ),
}


class MockProposer:
    """确定性 mock：从写死清单里按注入的 rng 取，序列可复现。"""

    def propose(self, *, stage: CoverageStage, context: ProposalContext, rng: np.random.Generator) -> ProposalCandidate:
        candidates = MOCK_CANDIDATES_BY_SLOT[context.slot_id]
        index = int(rng.integers(0, len(candidates)))
        return candidates[index]


class CompletionResult:
    """模型后端单次调用的完整结果（含 provenance 十一字段）。

    字段全部必填；构造期做 fail-closed 校验（model_id/request_id 非空、
    temperature/top_p 有限且在 [0,1]、tokens 为 int >= 0、cost/latency_ms 有限
    且 >= 0）。这是 evidence 链的入口——任何字段缺失都视同未做 provenance。

    **不可变性是契约的一部分**：`__setattr__` / `__delattr__` 一律拒绝。
    `ProposalCandidate` 只是浅冻结，而 `evolve_pool` 在四道闸与**注入的对抗复核器**
    跑完之后才把 provenance 序列化入账；若字段可写，任何持有引用者都能在
    「实际调用」与「写入账本」之间改写元数据，账本于是为被篡改的数据背书。

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
        # 经 object.__setattr__ 落字段：本类的 __setattr__ 一律拒绝，
        # 构造之后 provenance 不可变（见类 docstring 的不可变性契约）。
        for name, coerced in (
            ("model_id", str(model_id)),
            ("prompt", str(prompt)),
            ("response", str(response)),
            ("temperature", float(temperature)),
            ("top_p", float(top_p)),
            ("seed", int(seed)),
            ("prompt_tokens", int(prompt_tokens)),
            ("completion_tokens", int(completion_tokens)),
            ("cost", float(cost)),
            ("latency_ms", float(latency_ms)),
            ("request_id", str(request_id)),
        ):
            object.__setattr__(self, name, coerced)

    def __setattr__(self, name: str, value: object) -> None:
        raise AttributeError(
            f"CompletionResult 构造后不可变，拒绝改写 {name!r}：provenance 是证据链的"
            "入账内容；若能在闸门与对抗复核之后被改写，账本证明的就不是真实发生的那次调用"
        )

    def __delattr__(self, name: str) -> None:
        raise AttributeError(f"CompletionResult 构造后不可变，拒绝删除 {name!r}")

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
Imports, eval/exec, and dunder attributes are forbidden. Code executes in a sandbox.
目标：让 Pareto 前沿的超体积增大（造互补性，不是造单项冠军）。
""",
    "route_order": """你在一个农业覆盖路径规划的算法演化循环里担任启发式提议者。

阶段：{stage}
当前池子的配置：{pool}
轮次：{round_index}

请只输出一个 Python 函数定义，不要任何解释：

    def next_swath_score(state, candidate):
        ...

输入 state 与 candidate 都是 dict[str, float]；可用键（全部旋转不变、无量纲）：
  state: visited_count, remaining_count
  candidate: distance_norm（出口到条带入口欧氏距离 / min_turning_radius）、
             axis_offset_norm（条带中心在主轴法向的投影 / working_width）

返回值：浮点分数，越小优先级越高；必须有限。
可用内建：math, len, range, min, max, abs, sum, enumerate, sorted, tuple, list, float, int。
Imports, eval/exec, and dunder attributes are forbidden. Code executes in a sandbox.
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
        if result.prompt != prompt:
            # fail closed：后端返回的 provenance 必须对应本次实际发出的请求。
            # Ensure provenance prompt matches the prompt sent to the model.
            # 「哪个请求产生了这个响应」这一主张就无法成立。
            raise ValueError(
                "CompletionResult.prompt does not match sent prompt: "
                f"request_id={result.request_id!r}，"
                f"Sent {len(prompt)} chars, received {len(result.prompt)} chars"
            )
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

    Deterministic replay requirement: prompt and response must match byte-for-byte.
    在线产生的 ProposalCandidate 在 identity（三元组 algorithm_id/source_code/
    description）上逐位相等。
    """
    return _candidate_from_completion(round_index, result)
