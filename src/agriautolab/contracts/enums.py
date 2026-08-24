"""集中存放构成兼容性与证据边界的封闭词表。散落的字符串常量会让这些边界在 review 时不可见。"""

from enum import Enum


class TaskType(str, Enum):
    POINT_TO_POINT = "point_to_point"
    COVERAGE = "coverage"
    MULTI_POINT_ROUTING = "multi_point_routing"


class ScenarioDynamics(str, Enum):
    STATIC = "static"
    ONE_SHOT_CHANGE = "one_shot_change"
    EVENT_REPLAN = "event_replan"


class ProblemKind(str, Enum):
    """决定算法兼容性的具体问题族，而不是宽泛任务标签。"""

    GRID_P2P_2D = "grid_p2p_2d"
    POLYGON_COVERAGE_2D = "polygon_coverage_2d"
    EUCLIDEAN_TSP = "euclidean_tsp"
    EUCLIDEAN_CVRP = "euclidean_cvrp"


class RunStatus(str, Enum):
    OK = "ok"
    INVALID_INPUT = "invalid_input"
    UNSUPPORTED = "unsupported"
    INFEASIBLE = "infeasible"
    CONSTRAINT_VIOLATION = "constraint_violation"
    TIMEOUT = "timeout"
    MEMOUT = "memout"
    NOT_APPLICABLE = "not_applicable"
    CRASH = "crash"
    OTHER = "other"
    NUMERICAL_ERROR = "numerical_error"
    COLLISION = "collision"
    INFEASIBLE_KINEMATICS = "infeasible_kinematics"


class PathSegmentKind(str, Enum):
    WORK = "work"
    TURN = "turn"
    TRANSIT = "transit"


class CoverageStage(str, Enum):
    """农业覆盖流水线的领域阶段；不得拿来给 TSP/CVRP 等通用算法强行分类。"""

    DECOMPOSITION = "decomposition"
    HEADLAND = "headland"
    SWATH = "swath"
    ROUTE = "route"
    PATH = "path"


class SwathDirection(str, Enum):
    FORWARD = "forward"
    REVERSE = "reverse"


class CoverageTarget(str, Enum):
    """覆盖率的分母定义。必须由协议指定，不能由调用方临时决定。

    陷阱：地头宽度是被比较的对象之一。若各配置各用各的主田做分母，
    100x50 田块地头开到 18 米时对主田覆盖率仍是 1.0，而实际只覆盖了原田的 17.9%。
    """

    ORIGINAL_FIELD = "original_field"   # 原始地块扣除障碍
    MAIN_FIELD = "main_field"           # 扣除地头后的主田


class OptimizationDirection(str, Enum):
    MINIMIZE = "minimize"
    MAXIMIZE = "maximize"


class ComparabilityScope(str, Enum):
    IMPL_INVARIANT = "impl_invariant"
    IMPL_BOUND = "impl_bound"
    PROTOCOL_BOUND = "protocol_bound"


class ScaleBehavior(str, Enum):
    INVARIANT = "invariant"
    LINEAR = "linear"
    QUADRATIC = "quadratic"
    INVERSE_LINEAR = "inverse_linear"
    UNDEFINED = "undefined"


class MetricRole(str, Enum):
    PRIMARY = "primary"
    DIAGNOSTIC = "diagnostic"
    HARD_CONSTRAINT = "hard_constraint"


class ObjectiveRole(str, Enum):
    SEARCH_OBJECTIVE = "search_objective"
    EVAL_METRIC = "eval_metric"
    BOTH = "both"


class AlgorithmMaturity(str, Enum):
    BASELINE = "baseline"
    RESEARCH = "research"
    VERIFIED = "verified"


class AlgorithmSourceType(str, Enum):
    INTERNAL = "internal"
    PAPER_REPRODUCTION = "paper_reproduction"
    EXTERNAL_LIBRARY = "external_library"
