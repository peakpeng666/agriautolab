# AgriAutoLab 架构与依赖方向

AgriAutoLab 的**主研究对象始终是二维农业覆盖路径规划（CPP）**。TSP/CVRP 不是第二条
并列项目主线，而是自动算法设计前的方法学验证层：它们提供定义清楚、可手算、可对照
标准 benchmark 的 reference problems，用来验证 constructive heuristic、独立 evaluator
与后续 search/design 方法的公共边界。系统只做算法与二维几何仿真，不模拟真实车辆
动力学或硬件。

架构目标不是把所有问题塞进一个“万能 planner”，而是共享真正共性的协议，同时保留
农业 CPP、TSP、CVRP 各自的强类型问题语义。

## 1. 主研究线与方法学验证层

### 1.1 农业 CPP 主研究线

```text
contracts
   ↓
geometry → kinematics
   ↓
algorithms/{decomposition,headland,swath,route,path}
   ↓
pipeline
   ↓
validation + metrics
   ↓
corpus / pareto / selection / confirmatory / evidence
```

农业流水线使用固定五阶段：

`decomposition → headland → swath → route → path`

`CoverageStage` 是农业领域枚举，不承担通用组合优化分类职责。TSP/CVRP 不应为了
复用注册表而假装成某个 coverage stage。

### 1.2 组合优化方法学验证层

```text
contracts/routing + contracts/numerics
      ↓
optimization/constructive
      ↓
optimization/{tsp,cvrp,routing}
      ↓
algorithms/constructive
      ↓
future search/design methods
```

公共 constructive 协议只规定：

1. problem adapter 枚举当前可行动作；
2. heuristic 给**已可行**动作评分；
3. engine 按稳定枚举顺序选择最低分动作；
4. 独立 evaluator 在完成后重新校验解并复算目标。

因此硬约束属于 Problem，而不是 heuristic。未来 LLM 生成候选也只能进入受限评分槽位，
不能自行声明容量、访问或农业几何约束已经满足。

当前这一层只包含人工 TSP/CVRP constructive baselines 与语义真值，不包含
TSPLIB/CVRPLIB corpus、EoH reproduction、真实 LLM provenance 或农业迁移实验。

## 2. 依赖纪律

- `contracts/` 是跨模块数据边界，不依赖求解器、推荐器或 LLM；
- `contracts/numerics.py` 只保存低层 binary64 上界比较策略，不包含领域求解逻辑；
- `optimization/` 可以依赖 contracts，但不能 import 农业 `pipeline/`、selector 或 LLM；
- `algorithms/constructive/` 依赖标准问题 adapter 与公共 constructive protocol；
- 农业 `algorithms/` 不知道 selector、LLM、最终排名或论文结论；
- evaluator/validator 不采信算法自报性能；
- `evidence/` 记录可复核身份与产物，`confirmatory/` 不回写历史封存结果。

任何跨层便利 import 如果造成“算法知道自己应该赢”“候选能绕过硬约束”或循环依赖，
都视为架构错误而不是工程捷径。

## 3. 农业 CPP 已实现能力

- TaskType × ScenarioDynamics × ProblemKind schema 防火墙与米制 CRS 守卫；
- 严格几何校验、规范 WKB 哈希、`robust_union`、统一离散化纪律；
- 覆盖率分母由统一入口解析，并携带可复核 provenance；
- Boustrophedon decomposition、headland、五类 swath、三类 route、Dubins 与
  Reeds-Shepp 路径连接等 **14 个算法组件**；
- `configs/corpus_13.json` 固定 **13 个 pipeline configurations**，这与算法组件数
  不是同一概念；
- `RowStructure`、独立 PathValidator、指标注册表与农业三目标
  `path_length / headland_turn_count / row_crossing_equivalent`；
- Pareto front、精确 3D hypervolume、偏好标量化；
- Fields2Benchmark 数据接入、Fields2Cover 数值对账、断点续跑语料运行器；
- selection / confirmatory / append-only evidence discipline。

Study-001 的预注册、H1/H2/H3 结果、corrigendum 与历史 ledger 均属于冻结研究事实；
后续方法学扩展不得通过重写它们来获得“更漂亮”的叙事。

## 4. 标准组合优化验证能力

当前正式支持：

- `ProblemKind.EUCLIDEAN_TSP`：二维欧氏对称 TSP；
- `ProblemKind.EUCLIDEAN_CVRP`：单仓库、同质车辆、容量硬约束的二维欧氏 CVRP；
- 通用 `ConstructiveProblem` / `ConstructiveHeuristic` 协议；
- TSP nearest-neighbor 人工基线；
- CVRP nearest-feasible-customer 人工基线；
- TSP/CVRP 独立 evaluator 与手算语义真值测试；
- 派生距离与容量比较的 fail-closed 浮点边界：有限输入不能静默产生 `inf`，硬容量
  只容忍有限个 binary64 roundoff steps，不使用固定绝对容差。

标准问题的目的不是把项目改造成通用运筹库，而是给“基本算法复现 → 自动算法设计
方法验证 → 农业迁移”提供已知语义和可复核 reference tasks。

TSPLIB/CVRPLIB 数据适配、EoH reproduction、真实模型 provenance 与自动算法设计
实验属于后续增量；在代码和证据真正存在前不得写成“已实现”。

## 5. Agent 层的准确能力边界

当前 `agent/` 是**农业 swath 方向启发式演化骨架**，不是完整 EoH reproduction：

- 候选槽位为受限的 swath-angle heuristic；
- 有 AST 扫描、验证/确定性/几何不变性闸门、对抗探针和演化账本；
- LLM backend 通过接口注入，默认测试使用 hermetic mock；
- 候选适应度基于农业三目标 hypervolume contribution。

因此文档应写“LLM/heuristic evolution skeleton”或具体槽位能力，不把它泛称为已经完成的
通用 automatic algorithm design framework。后续 search/design 层应复用
`optimization/` 的问题—候选—评价边界，再逐步迁移农业 slot。

## 6. 数值与硬约束纪律

几何、距离与容量都属于科学计算边界，不能把“输入是 finite”误当作“派生量必然 finite”。
当前标准问题遵循：

1. 欧氏边长若因有限坐标差值溢出，evaluator 明确失败；
2. 多段距离用 `math.fsum`，总量无法有限表示时明确失败；
3. CVRP 不累加可能溢出的绝对 route demand，而逐客户验证剩余容量；
4. fleet preflight 比较无量纲 `Σ(demand / capacity)` 与车辆数；
5. 容量 roundoff 只允许少量相邻 binary64 表示步长；`upper_bound == 0` 时严格比较，
   禁止固定 `1e-12` 一类绝对容差给小尺度容量“白送空间”。

这里的 roundoff policy 是数值表示纪律，不是业务可行性放宽。

## 7. 范围边界

以下能力明确不在当前范围：动态重规划、真实车辆动力学、滑移、能耗、电池、质量与
摩擦、硬件在环、ROS/Gazebo/Isaac 级机器人仿真。

标准 TSP/CVRP 也不意味着无限扩张成所有 OR 问题；新增问题族必须满足至少一个条件：

1. 是老师任务与项目方法链的直接组成；
2. 能作为农业规划算法设计的明确方法学对照；
3. 有标准 benchmark，可形成可复核实验而非展示性 demo。

## 8. 工程纪律

1. **强类型优先**：不要用 `dict[str, Any]` 抹平 TSP/CVRP/CPP 的真实差异。
2. **硬约束属于问题**：heuristic 只排序可行动作，不能自行放宽约束。
3. **独立复算**：规划器/heuristic 自报指标一律不采信。
4. **语义真值优先于测试计数**：必须有旧缺陷下会红的解析或手算断言。
5. **稳定顺序显式化**：tie-break 不依赖 set/dict 偶然遍历，也不要求任意 Action
   类型实现比较运算。
6. **失败是数据**：失败、超时、拒绝必须保留结构化原因，不能伪装成零代价。
7. **证据身份永不改**：进入 parquet/manifest/prereg/pool hash 的 wire ID 不因命名
   审美重写；新 API 从第一天使用规范名和单位后缀。
8. **几何纪律不旁路**：农业几何并集、分母、CRS 与离散化继续走既有守卫。
9. **浮点容差必须有量纲依据**：硬约束禁止固定绝对 floor；允许的 roundoff 必须与
   binary64 表示精度绑定并由语义测试钉死。

## 9. 安装与测试

```bash
python -m pip install -e ".[dev]"
pytest -q
```

Ubuntu 22.04 是项目主要研究环境；CI 兼容矩阵与安装入口的环境语义应在后续运维批次
继续收敛，但不与算法正确性或研究证据修改混成同一提交。
