"""F2C 公共链路的唯一一份实现：CW -> fixed-angle -> <协议路线> -> Dubins。

**本模块刻意不 import 任何 agriautolab 内容，且只用 python3.10 兼容语法。**

理由（实测，2026-08-21）：F2C binding 绑在 WSL 的 python3.10，agriautolab 要求 3.11+
（contracts/geometry.py 用了 typing.Self）。两进程是既定架构，不是障碍。
于是链路必须能被两边同时使用：

- Windows / py3.11+：`PythonBindingAdapter` 直接 import 本模块；
- WSL / py3.10：`scripts/f2c_recorder/record_golden.py` 用 importlib
  按文件路径加载本模块，绕开包 `__init__` 的 3.11 语法。

由此「正式壳与适配器等价」不是靠事后比对两份输出，而是**只有一份实现**。
上一轮有两个一次性壳（/home/peak/f2c_golden_wrapper.py 与 record_golden_standalone.py），
它们随时可能各自漂移——这就是收敛掉它们的原因。

陷阱：本模块里任何 3.11+ 语法（typing.Self、X | Y 的运行期求值、除
`from __future__ import annotations` 之外的新式注解）都会让 WSL 侧录制直接 ImportError，
而且只在录 golden 时才炸。tests/block_c/test_f2c_recorder.py 静态守住这条。
"""

from __future__ import annotations

# 协议声明的路线算法名 -> F2C route planner 类名。
# 只映射语义确实相同的；名字相近但访问顺序不同的绝不入表。
F2C_ROUTE_PLANNERS = {
    "boustrophedon": "RP_Boustrophedon",
    "snake": "RP_Snake",
    "spiral": "RP_Spiral",
}

# F2C PathState.type 的取值：1 = SWATH（作业），2 = TURN（转移）。
# 实测 sum(state.len) 与 OBJ_PathLength().computeCost(path) 逐位相等
# （f2b_000_ee_field_10 上同为 1329.3096533749797），所以分解与总长同域。
_SWATH_STATE_TYPE = 1


class F2CChainError(RuntimeError):
    """链路本身的失败：缺 planner、路径不含作业段、分解有残余。"""


def build_cells(f2c, shapely_polygon):
    cell = f2c.Cell()
    cell.addRing(_ring(f2c, shapely_polygon.exterior.coords))
    for interior in shapely_polygon.interiors:
        cell.addRing(_ring(f2c, interior.coords))
    cells = f2c.Cells()
    cells.addGeometry(cell)
    return cells


def _ring(f2c, coordinates):
    ring = f2c.LinearRing()
    for x, y in coordinates:
        ring.addGeometry(f2c.Point(float(x), float(y)))
    return ring


def route_planner(f2c, route_algorithm):
    name = F2C_ROUTE_PLANNERS.get(route_algorithm)
    if name is None:
        raise F2CChainError(
            "F2C 侧没有 route_algorithm=%r 的对应实现；可用：%s"
            % (route_algorithm, sorted(F2C_ROUTE_PLANNERS))
        )
    planner = getattr(f2c, name, None)
    if planner is None:
        raise F2CChainError("本机 F2C 没有 %s（版本差异）" % name)
    return planner()


def transit_breakdown_from_states(path):
    """从 PathState 序列切出与我方 metrics.path.transit_breakdown 同口径的分解。

    陷阱：F2C 单 cell 链路没有跨 cell 概念，inter_cell 恒为 0。
    这个 0 是「本链路不产生跨 cell 转场」，不是「已验证无跨 cell 转场」。
    """
    lengths = []
    is_work = []
    for index in range(path.size()):
        state = path.getState(index)
        lengths.append(float(state.len))
        is_work.append(int(state.type) == _SWATH_STATE_TYPE)
    total = sum(lengths)
    work_positions = [index for index in range(len(is_work)) if is_work[index]]
    if not work_positions:
        raise F2CChainError("F2C 路径不含任何 SWATH 段，转移无法归类")
    first = work_positions[0]
    last = work_positions[-1]
    entry = sum(lengths[index] for index in range(first))
    exit_leg = sum(lengths[index] for index in range(last + 1, len(is_work)))
    turn_total = 0.0
    turn_count = 0
    for position in range(len(work_positions) - 1):
        left = work_positions[position]
        right = work_positions[position + 1]
        turn_total += sum(lengths[index] for index in range(left + 1, right))
        turn_count += 1
    work_total = sum(lengths[index] for index in work_positions)
    other = total - work_total - entry - turn_total - exit_leg
    if abs(other) > max(1.0, total) * 1e-12:
        raise F2CChainError("F2C 转移分解残余 %.9f m，分类不完备" % other)
    return {
        "transit_entry_leg_m": entry,
        "transit_turn_total_m": turn_total,
        "transit_turn_count": float(turn_count),
        "transit_inter_cell_m": 0.0,
        "transit_exit_leg_m": exit_leg,
        "transit_other_m": 0.0,
    }


def run_chain(f2c, shapely_polygon, params):
    """跑一次完整链路，返回标量结果 + swath 访问顺序 + 转移分解。

    params 需要的键：robot_width_m / working_width_m / min_turning_radius_m /
    headland_width_m / swath_angle_rad / route_algorithm。
    """
    cells = build_cells(f2c, shapely_polygon)
    robot = f2c.Robot(params["robot_width_m"], params["working_width_m"])
    if hasattr(robot, "setMinTurningRadius"):
        robot.setMinTurningRadius(params["min_turning_radius_m"])
    else:
        robot.setMinRadius(params["min_turning_radius_m"])
    headland = f2c.HG_Const_gen().generateHeadlands(cells, params["headland_width_m"])
    raw = f2c.SG_BruteForce().generateSwaths(
        params["swath_angle_rad"], params["working_width_m"], headland.getGeometry(0)
    )
    sorted_swaths = route_planner(f2c, params["route_algorithm"]).genSortedSwaths(raw)
    path = f2c.PP_PathPlanning().planPath(robot, sorted_swaths, f2c.PP_DubinsCurves())

    visits = []
    for index in range(sorted_swaths.size()):
        swath = sorted_swaths.at(index)
        visits.append({
            "swath_id": int(swath.getId()),
            "start": [float(swath.startPoint().getX()), float(swath.startPoint().getY())],
            "end": [float(swath.endPoint().getX()), float(swath.endPoint().getY())],
            "length_m": float(swath.length()),
        })

    scalars = {
        "path_length": float(f2c.OBJ_PathLength().computeCost(path)),
        "swath_count": float(sorted_swaths.size()),
        "swath_length_sum": float(
            f2c.OBJ_SwathLength().computeCost(headland.getGeometry(0), sorted_swaths)
        ),
        "main_field_area": float(headland.area()),
    }
    scalars.update(transit_breakdown_from_states(path))
    return {
        "scalars": scalars,
        "route_identity": {
            "route_algorithm": params["route_algorithm"],
            "generated_swath_count": int(raw.size()),
            "visit_order": [item["swath_id"] for item in visits],
            "visits": visits,
        },
    }
