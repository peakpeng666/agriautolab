"""几何、注册、证据三类失败各有独立异常类型，调用方才能分别处置，而不是统一 except Exception。"""


class AgriAutoLabError(Exception):
    """需让调用方看见的失败的基类。"""


class GeometryValidationError(AgriAutoLabError):
    """输入几何违反了已声明的几何前置条件。"""


class MetricRegistrationError(AgriAutoLabError):
    """指标声明自相矛盾，或者命中了禁用表。"""


class AlgorithmRegistrationError(AgriAutoLabError):
    """算法卡片与注册表中已有条目冲突。"""


class KinematicModelError(AgriAutoLabError):
    """车辆运动学与所选路径原语不相容，例如把可原地转向的车交给 Dubins 曲线。"""


class RobustUnionError(AgriAutoLabError):
    """精度网格与逐对 union 两条路径都没通过面积自检。"""


class EvidenceChainError(AgriAutoLabError):
    """账本记录与前一条哈希对不上。"""


class CoverageDenominatorError(AgriAutoLabError):
    """覆盖率分母绕开了 resolve_coverage_targets 这条唯一构造路径，或语义不变量不成立。"""


class TransitDecompositionError(AgriAutoLabError):
    """转移长度存在没被归类的残余。

    分类不完备就是分类错误：留一个「其他」筐，50% 的超额就能永远藏在里面不被发现。
    """


class TSPLIBFormatError(AgriAutoLabError):
    """TSPLIB / CVRPLIB 实例不满足本契约的接入前提。

    两类：文件本身不合规（缺 section、声明与数据不一致、多仓库、仓库 demand 非零），
    以及**语义无法无损映射**（GEO / ATT / EXPLICIT 等边权类型）。后者拒绝而不是
    按欧氏静默降级——那会产出看着合理、实则与公开最优值不可比的数。
    """
