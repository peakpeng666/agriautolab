# 更新日志

格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循语义化版本。每轮的完整过程批判见 [AUDIT_NOTE.md](AUDIT_NOTE.md)。

## [未发布]

- **TSPLIB / CVRPLIB 标准实例接入**：新增 `datasets/tsplib.py`——
  `load_tsplib_tsp` / `load_tsplib_cvrp` 把标准实例映射到既有的
  `TSPProblem` / `CVRPProblem` 契约；`TSPLIBInstance` 携带 name / dimension /
  edge_weight_type / 公开最优值 / 声明车辆数 / capacity。

  关键点是**距离语义与文献一致**：TSPLIB 的 `EUC_2D` 是逐边取整
  `nint(sqrt(xd*xd+yd*yd))`，而仓库既有的 `euclidean_node_distance_m` 是精确
  `hypot`——两者不是同一个目标函数，公开最优值全部按前者计算。因此单独提供
  `tsplib_distance` / `tsplib_tour_length` / `tsplib_tour_length_of` /
  `optimality_gap`，与几何距离明确分开，谁也不冒充谁。`nint` 按规范实现为
  `int(x+0.5)`（四舍五入），**不是** Python `round()` 的银行家舍入。

  实测佐证（berlin52 官方最优 tour，公开最优值 7542）：逐边 nint 得 **7542.0**、
  精确欧氏浮点求和得 **7544.3659**、逐边向上取整得 **7570.0**——后两者正是文献中
  常见的两种错法；误用精确欧氏会把 gap 虚报 0.0314%。

  fail-closed 覆盖：仅接受 `EUC_2D` / `CEIL_2D`（GEO / ATT / EXPLICIT 等点名拒绝，
  不按欧氏静默降级）、DIMENSION 与数据不符、重复节点号、缺 section、多仓库、
  仓库 demand 非零、DEMAND 与 COORD 节点集合不一致、显式 `max_vehicles` 与
  COMMENT 声明冲突。车辆数**不从文件名反推**（`A-n32-k5` 的 `k5` 是约定不是声明）。
  真实实例不入仓（不猜第三方数据许可），对应回归测试以
  `AGRIAUTOLAB_TSPLIB_DIR` 环境变量 opt-in，默认跳过。

- **agent 层候选槽位抽象（1→N，行为逐位不变）**：新增 `agent/slots.py`——
  `CandidateSlot` 协议（slot_id / stage / 契约函数名 / 沙箱编译 / 探针值 /
  评估配置构造 / 不变性检查 / 对抗复核器集）与 `SLOTS` 注册表
  （`DEFAULT_SLOT_ID = "swath_angle"`）；`SwathAngleSlot` 的全部语义自
  gates.py 逐字迁移（含 RNG 消耗顺序与错误消息）。四道闸与 `evolve_pool`
  增加 keyword-only `slot` 参数（缺省解析默认槽位，旧调用点零改动），
  `evolve_pool` 另增 `reviewers=None`（缺省用槽位自带复核器集，显式传参
  可覆盖）；`ProposalContext` 与 `EvolutionRecord` 增 `slot_id` 字段（默认
  `swath_angle`；演化账本从未落盘，无迁移）；`PROMPT_TEMPLATES` 按 slot_id
  取模板（`PROMPT_TEMPLATE` 保留为兼容别名），`MockProposer` 按槽位分派
  候选清单。RNG 消耗顺序（master 1 次 integers + 每轮 proposer 1 次
  integers + invariance 8×3 uniform）与黄金 config_id 逐位不变，由
  `tests/agent/test_slots.py` 的真值测试钉住；本次不新增槽位。
- **组合优化方法学验证层**：将 TSP/CVRP 作为农业 CPP 自动算法设计前的正式
  reference problems 融入主包，而非旁路教程或第二研究主线；新增强类型
  `TSPProblem` / `CVRPProblem`、通用 `ConstructiveProblem` /
  `ConstructiveHeuristic` 协议、TSP 最近邻与 CVRP 最近可行客户人工基线，以及
  独立 evaluator。硬约束由 Problem 掌管，heuristic 只在真实可行动作间决策；
  CVRP 提前回仓从 Problem 内隐策略移回 heuristic，`max_vehicles` 在动作枚举阶段
  即阻止必然开启第 K+1 辆车的伪可行动作。容量语义最终收敛为**严格 binary64
  hard bound**：任何 `demand > capacity` 都不再通过 ULP/固定绝对容差放行；schema
  的车队总运力用 `Fraction.from_float` 精确比较，constructor 将 capacity/demand
  映射为共同二进制整数单位并累计整数负载，evaluator 则以独立 Fraction 路径整路线
  复算。由此同时解决 `1e308` 聚合溢出、`1e-15` 固定容差误放、最小 subnormal
  1 ULP 即 2× 容量以及连续减法漂移；十进制直觉不再覆盖已经进入契约的 binary64
  输入事实。距离派生溢出继续 fail-closed。公共 engine 统一封装 heuristic 执行异常、
  非数值/NaN/Inf 以及任意自定义 `float(score)` 转换异常，并保留异常链。同步校正
  README/ARCHITECTURE/NAMING/包元数据的范围与术语，明确农业 CPP 是主研究对象；
  Study-001 预注册、封存证据与历史 ledger 零改动。
- **D7.1 post-seal integrity corrigendum**：原 H3 结果与 ledger index 0..6
  保持字节/链语义不回写，新增 index=7 修正件；披露 D7 两次“评估完成后、
  写盘前”身份守门中止意味着严格 one-shot 执行主张不成立；补齐所有
  protocol/input/D4 model exact-SHA 前置硬门，已封 H3 后 holdout 重跑
  fail-closed；修复偶数样本 median 实现。H3 冻结主统计量 `mean_D`、p 值、
  失效判据与 Holm 结论不变。
- **release / CI hygiene**：主线版本改为 `0.5.1.dev0`；CI 权限收敛为只读，
  GitHub Actions 固定到完整 SHA，runner 固定 Ubuntu 24.04，测试工具版本固定，
  增加 `pip check` / package metadata / `compileall` 守门；Dependabot 仅维护
  GitHub Actions 供应链；README 撤回旧的严格 one-shot 表述并链接 D7.1。
- **anytime 性能轨迹（M3 任务 1）**：`EvolutionRecord` 加 `evaluations_used`
  与 `cumulative_best_delta` 两字段（带默认值，旧记录零破坏）；
  `gates.validation_gate` / `gates.determinism_gate` 与
  `evolve._pool_points` / `evolve._candidate_points` 加 keyword-only
  `run` 参数（默认 `run_pipeline`，旧调用零改动）；
  `evolve_pool` 构造 `counted_run` 注入**全部**真实评估点
  （轮前基线池 + 三道闸门 + 候选逐实例评估），按全程累计真实调用数记录；
  新增模块级 `agriautolab.agent.ledger.anytime_curve(records) -> tuple[tuple[int, float | None], ...]`
  返回 COCO/IOHprofiler 式"评估次数 → 当前最优 ΔHV"采样点；
  `tests/agent/test_anytime.py` 真值测试覆盖手算对账（I×P+3+候选评估）、
  best 单调不减、ledger.verify 与 anytime_curve 逐点对应；
  既有 bitwise 复现测试零改动通过。
- **route_order 槽位（M3 任务 3 提交一+提交二）**：新增第二候选槽位
  `route_order`（route 阶段条带访问序），与 `swath_angle` 并行登记在
  `SLOTS` / `PROMPT_TEMPLATES` / `MOCK_CANDIDATES_BY_SLOT` 三表。
  提交一将"槽位解析 fail-closed"收紧为硬契约（未知 id / 键与 slot_id
  不一致 / 缺 proposer 表登记 / 协议缺成员四道防线），`DEFAULT_REVIEWERS`
  重命名为 `SWATH_REVIEWERS` 并保留兼容别名，docstring 明言新槽位必须
  自带 reviewer 集。
  提交二新增 `RouteOrderSlot`（八成员协议实现，双参契约
  `next_turn_score(state, candidate)`，invariance 闸断言离散访问序
  逐元素相同）；`agriautolab.algorithms.route.constructive_order.RouteOrderProblem`
  是公共 ConstructiveProblem 的领域 adapter（放农业侧以遵守
  optimization/ 不得 import 农业的依赖纪律）；`RankedSwathOrderPlanner`
  是新 path 阶段 planner id `ranked_swath_order`，按 `params["rank:<swath_id>"]`
  升序访问、swath_id 决胜，缺键即 ValueError fail-closed；
  `evaluate_route_order` 独立复算总转移距离（不构造过程累计值）；
  4 个 mock 候选源码使用旋转不变键 `distance_norm` / `projection_norm`；
  `ROUTE_REVIEWERS` 槽位专属复核集（不设 |v|≤π/2 界）。
  13 个冻结配置不含 `ranked_swath_order` id，其 config_id 逐位不变。
  真值测试：4 条带手算最近邻访问序、NaN 抛 ConstructionError、越界 apply
  抛 ValueError、刚体变换后 stable_id_order rank 序不变、缺 rank 键
  fail-closed、4 mock 候选过完整闸链。
  【结构性发现】route_nearest_neighbor（按 distance_norm 评分）旋转
  后访问序会变——这是正确行为，不是 bug；任务 2 文档 §3.3 已预料。
  任务 2 文档 HEADLAND_TURN_SLOT_DESIGN.md 建议砍出 headland_turn
  槽位被采纳（Study-002 yaml 已据此仅登记 swath_angle + route_order）。
- **LLM provenance 入账与重放校验（M3 任务 4）**：`proposer.CompletionResult`
  加十一必填字段（model_id / prompt / response / temperature / top_p / seed /
  prompt_tokens / completion_tokens / cost / latency_ms / request_id），
  构造期 fail-closed 校验（非空 / [0,1] / 有限 / 非负 int / 有限非负 float），
  并以 `__setattr__` / `__delattr__` 守卫做到**构造后深度不可变**；
  `ModelClient` 协议改 `complete(prompt) -> CompletionResult`；
  `ProposalCandidate` 加 `provenance: CompletionResult | None = None`（旧构造
  零破坏；MockProposer 不设置 → 恒为 None）；`LLMProposer.propose` 重构为
  委托 `_candidate_from_completion(round_index, result)`，在线构造与
  `replay_candidate` 共享同一函数 → identity 逐位一致有结构性保证；
  `EvolutionRecord` 加 `provenance: dict | None = None`，evolve.append 写入
  `candidate.provenance.to_dict()`；**identity 三元组（algorithm_id/
  source_code/description）冻结不动**，provenance 不进 `candidate_identity` 哈希。
  `tests/agent/test_provenance.py` 真值测试 6 个：CompletionResult fail-closed
  三类（空 model_id / 负 cost / 超界 top_p）、LLMProposer 注入后 provenance
  齐全 + source_code == response + replay identity 逐位相等、MockProposer 跑
  evolve_pool 时 record.provenance 全 None、带 provenance 记录 ledger.verify
  不抛。前置 cherry-pick：任务 1 commit acffd9c（anytime 性能轨迹）。

## [0.5.0] — 2026-08-24

- **D7/H3 原始封存（Study-001 结案）**：H3 未获支持
  （mean_D=+0.0587，p=0.821，失效判据 1 触发；判据 2 通过；双轨一致）；
  Holm 终表 H1 支持 / H2 支持 / H3 不支持；封存前两次身份守门中止事故
  contemporaneous 留痕。D7.1 后续对其执行纪律与次要 median 实现做只追加修正。
- D2 三层池普查：selection/pools.py（N/A/O 契约 + 逐实例包含校验）、
  scripts/pool_census.py、evidence/block_d/pool_census.json（4,700 实例，
  A 层 v0=11/v1=13）+ Block D ledger index=1；5 条测试
- 第三次转折发起（docs/TURNING_POINT.md）：生成式研究线章程 + 两份外部
  AI 输入的批判性核验（H2 退化实证、空白前提联网抽查成立）
- 修正案 04：H2 田内重复测量设计、H3 偏好条件 Tchebycheff 悔值首要端点
- 文档小债清偿：12 特征（3 处）、安装预期 530→546（INSTALL_TRANSCRIPT
  为历史证据不改）
- D0.4 执行规范封口（修正案 05，最终修正案）：零权重契约、
  PREFERENCE_GRID_V1 坐标冻结（22 点+哈希）、H3 非 oracle 精确期望基线
  与田级聚合、不可行罚则、H2 常数响应记 0；examples/corpus/ 补齐
- D1 field-grouped CV 身份冻结：235-field universe − 70-field holdout = 165
  training fields，seed 20260822、10 折（17×5 + 16×5）；完整折表、assignment/spec
  hash 与 Block D 分析链 genesis 落盘。首轮干净 runner 暴露
  `effective_pool_size_by_instance` 不能代表全集（12 个 holdout field 缺席），
  已改用结果无关的 manifest `licenses` 表并加重放回归测试
- 工程成熟化：GitHub Actions CI（ruff + 双 Python 矩阵 pytest）、ruff 接入
  （冻结件排除）、README 重写（项目级 + 目录树 + 徽章）、CONTRIBUTING、
  PR/Issue 模板、CHANGELOG、版本 0.4.0
- ruff 首扫清零：修掉 1 处 F821 潜在未定义名（`PolygonSpec` 注解）与
  26 处未用导入、4 处未用变量
- 命名/注释对齐第二批：39 处「Block A/B/C」轮次标签从生产源码改写为
  语义描述（历史归 AUDIT_NOTE/CHANGELOG）；README 目录树补齐
  agent/datasets/validation 三包；模块 docstring 覆盖率核验 100%
- 迭代痕迹清零：src/tests/scripts 全量扫描轮次标签、run 版本号、复核编号
  （C-R1 等）、任务号、裸章节号、日期——全部语义化或移出；测试目录
  `tests/block_c/`→`tests/corpus/`、`test_r1_fixes.py`→`test_corpus_guards.py`；
  `evidence/README.md` 证据集索引（历史唯一住所 = AUDIT_NOTE）

## [0.4.0] — 2026-08-23

### canonical 命名层（PR #1）

- `docs/NAMING.md`：总纲——证据身份（wire ID）永不改，规范名只在 API 层
- 两处语义修正：`row_crossing_equivalent`（实现为连续等价量）、
  `runtime_s`（原 ID 单位在撒谎）
- `MetricSpec.canonical_name` + 注册表反查；`ObjectiveVector` 规范字段 +
  legacy 兼容；`features/schema.py`；12 个算法类 canonical + 别名
  （修复一处委托同名遮蔽递归）；`reconciliation/`、`benchmark/` 规范包
- 注释清扫第一批：日期/田 ID/轮次标签移出生产源码
- 验收：pool_hash/协议哈希/冻结件字节/parquet 契约对 v7 全量重放一致

## [0.3.0] — 2026-08-23

### v7 终语料与复核落地

- v7 终跑（干净提交 ed1bccb）：61,100 行四桶封闭，**other=0、crash=0**；
  66 崩溃行去向逐一对账（ULP 闭合容差修复 = 交裁决而非放行）
- `derived_status` 单一真相入口（validator 事实优先于运行时归并）+ 7 测试
- 零地头定理（最短路径形式下越界深度恒 ≥ R）与「RS 可零地头」主张收回
- `status_crosstab`：config×机具×状态交叉表、有效池完整分布（双口径中位）
- `evidence/v7/` 溯源件：ledger 哈希链 61,101 条逐条复算验证全过
- 修正案 03：统计单位钉地块层（防伪重复虚增 √20 倍）、留出集探针披露
  与 H3 双轨、已见统计量披露

## [0.2.0] — 2026-08-22

### WSL 迁移、一键安装与双机具

- 一键安装五件套（apt/F2C 编译/Python/校验/锁文件）+ 净室 agri-clean
  实测 EXIT 0、九项自校验全过（docs/INSTALL_TRANSCRIPT.md）
- Python 下限 3.11→3.10（WSL 迁移轮，冻结改动留痕）；跨平台字节冻结
  （.gitattributes LF + corpus_13 哈希重钉）
- §4.1 other 归零：具名状态映射（封闭词典 + 未知原因响亮失败）
- §4.3 manifest 取聚合器（450 个零 ok 实例不再静默消失）
- §4.4 双机具 + `vehicles_hash` 协议强制核对（RS 槽位真跑解锁）
- §4.6 checkpoint 跑完 gzip（mtime=0 字节确定）
- 真实数据连环缺陷修复：RS 零长直线守卫、Minkowski 对偶包含加速、
  robust_union 平衡树归约（150.7 s→秒级，结果数学同一）

## [0.1.0] — 2026-08-21

### Blocks A/B/C 基线（523 passed）

- L1 契约/几何内核/指标注册表/证据链；L2 五阶段算法池 + Dubins/RS +
  Pareto 三件套 + 10 特征 + 预注册封存；L3 数据接入（Fields2Benchmark
  350→235 许可过滤）、F2C 对账（金标 + 环境指纹）、语料运行器、ASlib 导出
- 覆盖率分母三层守卫；235 全量四轮 crash 轨迹 1,852→1,002→10→0
