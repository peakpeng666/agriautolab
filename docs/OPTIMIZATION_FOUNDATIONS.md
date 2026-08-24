# Optimization foundations

TSP/CVRP 是 AgriAutoLab 的**方法学验证问题**，不是新的并列研究主线。它们用定义清楚、
可手算的标准组合优化语义，验证未来自动算法设计所需的公共 problem / heuristic /
evaluator 边界；最终研究对象仍是农业 CPP。

## 1. 统一边界

系统把构造式算法拆成四个角色：

1. **Problem contract**：定义输入、静态不变量与硬约束；
2. **Constructive problem adapter**：维护状态、枚举当前可行动作并执行状态转移；
3. **Heuristic**：只给已经可行的动作评分，分数越小优先；
4. **Evaluator**：构造结束后独立校验解并复算目标。

这条边界保证启发式（包括未来 LLM 生成候选）不能自行放宽容量、访问或农业几何
约束，也不能自报性能。公共 engine 还要求 `feasible_actions` 提供稳定顺序：评分并列
按该顺序决胜，而不是隐式要求任意 Action 类型支持大小比较。heuristic 执行异常、
非法评分类型、float 转换溢出和 NaN/Inf 统一 fail closed 为 `ConstructionError`，
并保留原异常链。

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
提前回仓也是合法 CVRP 决策：Problem adapter 在车队上限允许时把 depot 暴露为 action，
是否采用 fill-until-stuck 由 `CVRPNearestFeasibleCustomerHeuristic` 决定，而不是伪装成
feasibility。

这些标准问题的作用是建立人工 constructive heuristic 的可解释真值，为后续 EoH、
LLM-guided search 与非 LLM 搜索基线提供 reference tasks。它们不是农业算法池中的
coverage component，因此不使用 `CoverageStage` 分类。

## 3. 与农业 CPP 的关系

农业覆盖流水线继续使用强类型五阶段 `PipelineConfig`：

`decomposition -> headland -> swath -> route -> path`

通用 constructive 协议位于方法学验证层。后续若开放农业
`next_swath_score(state, candidate)` 等候选槽位，应通过领域 adapter 接入公共协议，
而不是把 TSP/CVRP 强行塞进 coverage stage，也不是把农业 `PipelineConfig` 泛化成
无类型字典。

## 4. 数值与语义真值

测试必须包含旧缺陷下会失败的真值，而不是只增加覆盖率数字：

- 手算 TSP tour 顺序与闭合长度；
- CVRP 容量触发的回仓与路线闭合；
- Problem 必须暴露仍合法的提前回仓 action，而 nearest-feasible heuristic 才负责
  推迟回仓；
- `0.1 + 0.2 = 0.3` 类二进制尾差不能误杀数学上刚好装满的路线；
- `100 × 0.01 = 1.0` 不能因连续减法累计误差错误拆成第二辆车；constructor 因此
  每个候选都从当前 route 身份重新 `fsum(demand/capacity)`，不保存累计剩余容量；
- `1e-15` 级容量不能因固定 `1e-12` 绝对容差获得“免费容量”；
- 有限 demand 的绝对和可能上溢时仍必须正确拒绝超载；
- evaluator 的容量复算必须与 constructor 的候选负载路径计算独立；回归测试会故意
  破坏 constructor helper，仍要求 evaluator 拒绝 1.2× 超载；
- 有限坐标派生出不可表示的边长/总路程时 evaluator 必须 fail closed；
- 明确可行的 CVRP 实例中，greedy 次序可能因车队上限被 refute；
- 非数值、float 转换溢出、NaN/Inf heuristic score 必须 fail closed；
- 评分完全并列、Action 不可排序时，公共 engine 仍按稳定枚举顺序工作。

容量比较不使用固定 absolute tolerance。`contracts.numerics` 只容忍有限个相邻
binary64 表示步长；上界为零时严格比较。这个 roundoff policy 只处理最终表示误差，
**不用于补偿累计数值算法误差**；若累计误差改变可行域，应修改计算路径而不是扩大
容差。

## 5. 研究纪律

- Study-001 的预注册、封存证据与历史 ledger 不因该扩展而改写；
- 标准问题上的目标由独立 evaluator 复算；
- 新 API 从第一版使用规范名与单位后缀，不制造新的 legacy debt；
- 后续真实 LLM/EoH 实验必须另行记录模型、prompt、采样参数、父代、operator、
  token/cost/latency 与随机种子等 provenance，再进入新的研究协议；
- TSPLIB/CVRPLIB 数据适配、EoH reproduction 与农业迁移是后续增量，代码未落地前
  不写成已实现能力。
