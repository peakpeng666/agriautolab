# Optimization foundations

AgriAutoLab 的标准组合优化问题不是旁路教程，而是农业自动算法设计的方法学基准。

## 1. 统一边界

系统把构造式算法拆成四个角色：

1. **Problem contract**：定义状态与硬约束；
2. **Constructive problem adapter**：枚举当前可行动作并执行状态转移；
3. **Heuristic**：只给已经可行的动作评分，分数越小优先；
4. **Evaluator**：在构造结束后独立校验解并复算目标。

这条边界保证启发式（包括未来 LLM 生成的候选）不能自行放宽容量、覆盖或访问约束，也不能自报性能。

## 2. 当前标准问题

- `EUCLIDEAN_TSP`：二维欧氏对称 TSP，闭合 Hamiltonian cycle；
- `EUCLIDEAN_CVRP`：二维欧氏对称 CVRP，单仓库、同质车辆、容量硬约束，可选车辆数上限。

首批人工基线：

- TSP nearest neighbor；
- CVRP nearest feasible customer。

它们的作用是建立手工 constructive heuristic 的可解释真值，为后续 EoH/LLM4AD 类方法提供 reference tasks。它们不是农业算法池中的 coverage component，因此不使用 `CoverageStage` 分类。

## 3. 与农业 CPP 的关系

农业覆盖流水线继续使用强类型的五阶段 `PipelineConfig`：

`decomposition -> headland -> swath -> route -> path`

通用 constructive 协议位于它的上游方法学层。后续若开放农业 `next_swath_score(state, candidate)` 等候选槽位，应通过领域 adapter 接入公共协议，而不是把 TSP/CVRP 强行塞进 coverage stage。

## 4. 研究纪律

- Study-001 的预注册、封存证据与历史 ledger 不因该扩展而改写；
- 标准问题上的目标由独立 evaluator 复算；
- 语义测试优先固定“手算可知”的小实例，而不只断言程序可运行或结果可重复；
- 后续真实 LLM/EoH 实验必须另行记录模型、prompt、采样参数、父代与 operator 等 provenance，再进入新的研究协议。
