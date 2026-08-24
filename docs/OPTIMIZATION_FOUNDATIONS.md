# Optimization foundations

AgriAutoLab 的标准组合优化问题不是旁路教程，而是农业自动算法设计的方法学基准。

## 1. 统一边界

系统把构造式算法拆成四个角色：

1. **Problem contract**：定义输入、静态不变量与硬约束；
2. **Constructive problem adapter**：维护状态、枚举当前可行动作并执行状态转移；
3. **Heuristic**：只给已经可行的动作评分，分数越小优先；
4. **Evaluator**：构造结束后独立校验解并复算目标。

这条边界保证启发式（包括未来 LLM 生成候选）不能自行放宽容量、访问或农业几何
约束，也不能自报性能。公共 engine 还要求 `feasible_actions` 提供稳定顺序：评分并列
按该顺序决胜，而不是隐式要求任意 Action 类型支持大小比较。

## 2. 当前标准问题与 API

- `ProblemKind.EUCLIDEAN_TSP` / `TSPProblem`：二维欧氏对称 TSP，闭合
  Hamiltonian cycle；
- `ProblemKind.EUCLIDEAN_CVRP` / `CVRPProblem`：二维欧氏对称 CVRP，单仓库、
  同质车辆、容量硬约束，可选 `max_vehicles`；
- `TSPConstructiveProblem` / `CVRPConstructiveProblem`：领域状态机 adapter；
- `TSPNearestNeighborHeuristic`：TSP 最近邻人工基线；
- `CVRPNearestFeasibleCustomerHeuristic`：CVRP 最近可行客户人工基线；
- `TSPEvaluation.tour_length_m` / `CVRPEvaluation.total_distance_m`：独立复算指标。

CVRP schema 只提前拒绝无争议的静态不可行情况，例如单客户需求超过单车容量、
总需求超过给定车队总容量；它不在数据契约里偷偷解决更强的装箱可行性问题。

这些标准问题的作用是建立手工 constructive heuristic 的可解释真值，为后续
EoH/LLM4AD 类方法提供 reference tasks。它们不是农业算法池中的 coverage component，
因此不使用 `CoverageStage` 分类。

## 3. 与农业 CPP 的关系

农业覆盖流水线继续使用强类型五阶段 `PipelineConfig`：

`decomposition -> headland -> swath -> route -> path`

通用 constructive 协议位于其上游方法学层。后续若开放农业
`next_swath_score(state, candidate)` 等候选槽位，应通过领域 adapter 接入公共协议，
而不是把 TSP/CVRP 强行塞进 coverage stage，也不是把农业 `PipelineConfig` 泛化成
无类型字典。

## 4. 语义测试原则

P1 的测试必须包含旧缺陷下会失败的真值，而不是只增加覆盖率数字：

- 手算 TSP tour 顺序与闭合长度；
- CVRP 容量触发的强制回仓与路线闭合；
- 明确可行的 CVRP 实例中，greedy 次序可能因车队上限被 refute；
- 非有限 heuristic score 必须 fail closed；
- 评分完全并列、Action 不可排序时，公共 engine 仍按稳定枚举顺序工作。

## 5. 研究纪律

- Study-001 的预注册、封存证据与历史 ledger 不因该扩展而改写；
- 标准问题上的目标由独立 evaluator 复算；
- 新 API 从第一版使用规范名与单位后缀，不制造新的 legacy debt；
- 后续真实 LLM/EoH 实验必须另行记录模型、prompt、采样参数、父代、operator、
  token/cost/latency 与随机种子等 provenance，再进入新的研究协议；
- TSPLIB/CVRPLIB 数据适配、EoH reproduction 与农业迁移是后续增量，代码未落地前
  不写成已实现能力。
