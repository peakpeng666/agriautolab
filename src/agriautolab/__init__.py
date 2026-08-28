"""顶层只暴露问题与车辆契约。其余类型需从子包显式导入，免得一次 import 就把几何内核全拖进来。"""

from agriautolab.contracts.problem import CoverageProblem, GridPointToPointProblem
from agriautolab.contracts.vehicle import VehicleSpec

__all__ = ["CoverageProblem", "GridPointToPointProblem", "VehicleSpec"]
