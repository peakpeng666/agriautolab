"""启发式提议者：LLM 后端可注入，测试只用确定性 mock。

候选代码的契约槽位（这是 Agent 层唯一开放的算法自由度）：

    def swath_angle_offset_rad(features: Mapping[str, float]) -> float

返回相对地块 PCA 主轴的扫掠角偏移。特征是旋转不变的（features/invariance.py），
偏移量因此按构造旋转不变——这不变性由第四道闸（invariance gate）强制兑现，
不靠候选代码自觉。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np

from agriautolab.contracts.enums import CoverageStage


@dataclass(frozen=True)
class ProposalContext:
    stage: CoverageStage
    round_index: int
    pool_config_ids: tuple[str, ...]


@dataclass(frozen=True)
class ProposalCandidate:
    algorithm_id: str
    source_code: str
    description: str


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


class MockProposer:
    """确定性 mock：从写死清单里按注入的 rng 取，序列可复现。"""

    def propose(self, *, stage: CoverageStage, context: ProposalContext, rng: np.random.Generator) -> ProposalCandidate:
        index = int(rng.integers(0, len(MOCK_CANDIDATES)))
        return MOCK_CANDIDATES[index]


class ModelClient(Protocol):
    def complete(self, prompt: str) -> str:
        ...


PROMPT_TEMPLATE = """你在一个农业覆盖路径规划的算法演化循环里担任启发式提议者。

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
"""


class LLMProposer:
    """真实模型后端。Block B 不发起任何网络请求，只定义接口与提示词模板。

    模型客户端由构造注入（Block C 接真模型）；不注入就调用是配置错误，
    当场报错而不是降级到 mock——静默降级会让「测试后端」混进真实证据链。
    """

    def __init__(self, client: ModelClient | None = None) -> None:
        self._client = client

    def build_prompt(self, *, stage: CoverageStage, context: ProposalContext) -> str:
        return PROMPT_TEMPLATE.format(
            stage=stage.value,
            pool=", ".join(context.pool_config_ids),
            round_index=context.round_index,
        )

    def propose(self, *, stage: CoverageStage, context: ProposalContext, rng: np.random.Generator) -> ProposalCandidate:
        if self._client is None:
            raise RuntimeError(
                "LLMProposer 没有注入模型客户端：Block B 不携带网络后端，"
                "实际调用属于 Block C；测试请用 MockProposer"
            )
        source = self._client.complete(self.build_prompt(stage=stage, context=context))
        return ProposalCandidate(
            algorithm_id=f"evolved_llm_{context.round_index:03d}",
            source_code=source,
            description="LLM 提议（Block C 注入真实后端后产生）",
        )
