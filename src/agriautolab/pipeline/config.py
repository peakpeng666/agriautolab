"""五阶段组合体的配置身份：稳定 config_id 进协议哈希与证据链。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from agriautolab.pipeline.hashing import content_hash


@dataclass(frozen=True)
class PipelineConfig:
    decomposition: str
    headland: str
    swath: str
    route: str
    path: str
    params: Mapping[str, float] = field(default_factory=dict)

    def config_id(self) -> str:
        """稳定 id：五个阶段槽位 + 排序后的参数表的内容哈希。

        用内容哈希而不是拼字符串：参数键序不同、嵌套结构不同都会改变拼接结果，
        而内容哈希只看内容（sort_keys），同一配置永远同一 id。
        """
        return content_hash({
            "decomposition": self.decomposition,
            "headland": self.headland,
            "swath": self.swath,
            "route": self.route,
            "path": self.path,
            "params": dict(sorted(self.params.items())),
        })

    def stage_slots(self) -> tuple[tuple[str, str], ...]:
        return (
            ("decomposition", self.decomposition),
            ("headland", self.headland),
            ("swath", self.swath),
            ("route", self.route),
            ("path", self.path),
        )
