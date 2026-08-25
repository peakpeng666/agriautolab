"""ranked_swath_order：按 params["rank:<swath_id>"] 浮点值排序的条带访问序。

设计依据（任务 3 A2 提交二）：候选选择【烘焙进 params】，不通过函数注入
run_pipeline——理由是"同 id 假身份"纪律（evolve.py 模块 docstring 明言
同 id 候选不许伪装成不同候选；注入会让不同候选产生相同 config_id）。
烘焙与 SwathAngleSlot.build_config 把 angle_rad 烘焙进 params 的先例一致。

排序规则：按 rank 升序；rank 相同按 swath_id 字典序决胜（稳定）。
方向：第 i 个访问（0 基）偶数 FORWARD、奇数 REVERSE——与 BoustrophedonRoutePlanner
同源（boustrophedon_order.py:32）。
任一条带缺 rank 键 → ValueError（fail-closed，消息列出缺失 id）。
13 个冻结配置不含该 id，其 config_id 逐位不变。
"""

from __future__ import annotations

from agriautolab.contracts.artifacts import RouteArtifact, SwathsArtifact, SwathTraversal
from agriautolab.contracts.enums import SwathDirection


class RankedSwathOrderPlanner:
    algorithm_id = "ranked_swath_order"

    def run(self, artifact: SwathsArtifact, *, ranks: dict[str, float]) -> RouteArtifact:
        """按 ranks[swath_id] 升序访问；rank 相同按 swath_id 字典序；缺键即 ValueError。"""
        if not artifact.swaths:
            return RouteArtifact(traversals=(), swaths=())
        all_ids = tuple(swath.swath_id for swath in artifact.swaths)
        missing = tuple(sorted(swath_id for swath_id in all_ids if swath_id not in ranks))
        if missing:
            raise ValueError(
                f"ranked_swath_order 缺 rank 键：{missing}。"
                f"已登记 rank 键：{tuple(sorted(ranks))}；条带 id：{all_ids}"
            )
        # 稳定排序：先按 rank 升序，再按 swath_id 字典序
        ordered = tuple(sorted(artifact.swaths, key=lambda s: (ranks[s.swath_id], s.swath_id)))
        traversals = tuple(
            SwathTraversal(
                swath_id=swath.swath_id,
                direction=SwathDirection.FORWARD if index % 2 == 0 else SwathDirection.REVERSE,
            )
            for index, swath in enumerate(ordered)
        )
        return RouteArtifact(traversals=traversals, swaths=ordered)


# legacy 别名：canonical 类名见 docs/NAMING.md。
RankedSwathOrder = RankedSwathOrderPlanner
