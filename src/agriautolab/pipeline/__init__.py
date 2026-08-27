"""pipeline/ 层的包出口。

注意：本包 __init__ 刻意保持轻量——不在此再导出 run/executor 的重类型。
pipeline.hashing 会被 contracts 层反向引用，任何在这里触发的重导入都会
把 contracts.protocol 的加载拉进循环导入。
"""

from agriautolab.pipeline.config import PipelineConfig

__all__ = ["PipelineConfig"]
