# NAMING.md：命名与注释规则（canonical + legacy 双层词汇表）

本仓库存在两套词汇：**规范名（canonical）**面向新代码与论文叙事，
**证据名（wire/legacy ID）**是已落盘证据的身份。规则只有一条总纲：

> **证据身份永不改；规范名只存在于 API 层。**

改一个已进 parquet / manifest / 预注册 / pool_hash 的字符串，等于把
历史实验的身份换掉——v7 的 61 100 行会立刻变成「另一个实验」。
因此：wire ID（`row_crossings`、`dubins_transit`、`runtime_ms`、
`row_angle_vs_principal`…）永久保留；规范名以别名/属性/canonical_name
的形式并存，新代码用规范名。

## 1. 词汇规则

- **领域名表达事物**：`working_width_m`（工作幅宽，不是笼统的 width）。
- **类名表达角色**：`TSPNearestNeighborHeuristic`、`CVRPConstructiveProblem`；
  不用 `Helper`、`Manager`、`Thing` 这类无法说明职责的名字。
- **函数名表达动作**：`extract_instance_features`、`evaluate_tsp_tour`、
  `construct_solution`。
- **字段名表达数学意义与单位**：已知物理量用 SI 后缀（`_m`、`_rad`、`_s`）；
  TSP/CVRP 的 `tour_length_m`、`total_distance_m` 同样遵守。CVRP 的
  `demand` / `vehicle_capacity` 是 benchmark 自身的同量纲容量单位，不擅自冒充 kg/L。
- **五阶段槽位字符串是 wire ID**：`dubins_transit` / `reeds_shepp_transit` /
  `min_width` / `no_headland`… 进 config_id 与 pool_hash，永不改。
- **问题族与领域阶段分开命名**：`ProblemKind.EUCLIDEAN_TSP/CVRP` 描述问题族；
  `CoverageStage` 只描述农业覆盖的 decomposition/headland/swath/route/path，
  不拿 `CoverageStage.ROUTE` 给 TSP/CVRP 强行分类。
- **研究主线与验证层分开命名**：农业 CPP 是主研究对象；TSP/CVRP 是
  methodology/reference problems。除非后续研究协议真的改变，不把验证层称为
  “第二主线”或用包结构反向扩大课题边界。

## 2. 语义修正（canonical 与 wire identity）

两处不是「难看」而是**语义错误**，规范名纠正之、wire ID 保留之：

| wire ID（证据身份，保留） | 规范名（API 层） | 原因 |
|---|---|---|
| `row_crossings` | `row_crossing_equivalent` | 实现是横向位移/行距的连续量，不是整数「穿行次数」 |
| `runtime_ms` | `runtime_s` | 注册单位本来就是秒，ID 在撒谎 |

其余规范名对照（显示与 API 层使用，证据层不动）：

| wire ID | 规范名 |
|---|---|
| `aol` | `heading_change_per_meter` |
| `eta_L` | `nonwork_length_ratio` |
| `L_area` | `normalized_path_length` |
| `perimeter_area_ratio` | `perimeter_sqrt_area_ratio` |
| `crossing_density` | `field_scale_to_row_spacing_ratio` |
| `spacing_to_width_ratio` | `row_spacing_to_working_width_ratio` |
| `turning_ratio` | `turning_radius_to_working_width_ratio` |
| `row_angle_vs_principal` | `crop_row_angle_to_principal_axis_rad` |

指标规范名经 `MetricSpec.canonical_name` 声明（`registry.metric_by_canonical`
可反查）；特征规范名集中在 `features/schema.py`；`ObjectiveVector` 字段用
规范名（`headland_turn_count` / `row_crossing_equivalent`），同时永久接受
legacy 关键字与属性。参数键 `path_sample_step_m` 优先，`dubins_sample_step_m`
作为 legacy 键继续被接受。

## 3. 类名与算法身份

农业五阶段的历史算法 ID 已进入 config hash / pool hash，因此只能保留 wire identity。
类名可以在不改变证据身份的前提下收敛，但不为“整齐”制造无消费者的双名层。

标准组合优化验证层从第一版起直接使用角色明确的规范名：

- `TSPProblem` / `CVRPProblem`：输入问题契约；
- `TSPConstructiveProblem` / `CVRPConstructiveProblem`：把领域状态适配到公共
  constructive protocol；
- `TSPNearestNeighborHeuristic` / `CVRPNearestFeasibleCustomerHeuristic`：
  人工评分规则；
- `TSPEvaluation` / `CVRPEvaluation`：独立 evaluator 的输出，不由 heuristic 生成。

`14 algorithm components`、`13 frozen pipeline configurations`、`N generated
heuristic candidates` 是三种不同计数，文档与论文中不得简写成“13 个算法”。

agent 层候选槽位抽象使用角色明确的规范名：`CandidateSlot`（协议）、
`SwathAngleSlot`（swath 槽位实现）、`SLOTS`（注册表字典）与
`DEFAULT_SLOT_ID`。槽位 id（当前仅 `swath_angle`）进入
`ProposalContext.slot_id` 与 `EvolutionRecord.slot_id`，按总纲属于将来的
证据身份：演化账本一旦开始落盘，已用的 slot id 即为 wire ID 永不改。

演化账本加 anytime 性能轨迹字段（`EvolutionRecord.evaluations_used`、
`EvolutionRecord.cumulative_best_delta`）与模块级函数
`agriautolab.agent.ledger.anytime_curve(records) -> tuple[tuple[int, float | None], ...]`。
字段为「真实 run_pipeline 调用累计数」与「迄今各轮 hypervolume_delta 非 None
值的 running max」；`anytime_curve` 按这两个字段返回 COCO/IOHprofiler 式的
"评估次数 → 当前最优"采样点，O(n)。口径与 `evaluations_used` 字段 docstring
一致，是 Study-002 预算公式的唯一来源。

LLM provenance（任务 4）：`agriautolab.agent.proposer.CompletionResult`
（frozen dataclass，十一必填字段 + `to_dict()` JSON 序列化入口）、
`agriautolab.agent.proposer.replay_candidate(round_index, result)`
（离线重放入口，无网络、确定性，构造共享 `_candidate_from_completion`）。
`ProposalCandidate.provenance: CompletionResult | None`（MockProposer 恒为 None）；
`EvolutionRecord.provenance: dict | None` 由 `evolve.append` 写入
`candidate.provenance.to_dict()`。**provenance 不进 `candidate_identity` 哈希**——
identity 仍由三元组（algorithm_id/source_code/description）决定，provenance 仅
作 evidence 链附加字段。`ModelClient` 协议改 `complete(prompt) -> CompletionResult`，
本模块仍然零网络（注入由调用方接入）。

## 4. 包结构命名

当前真实包名就是文档事实，不再维护“计划中的 canonical 幽灵目录”：

- `contracts/`：跨模块强类型数据契约；`routing.py` 放 TSP/CVRP 输入契约；
- `optimization/`：constructive problem / heuristic / evaluator 方法学验证层；
- `algorithms/constructive/`：标准问题的人工 constructive baselines；
- `pipeline/`：农业 CPP 五阶段组合与执行；
- `corpus/`：真实语料批量运行与产物；
- `cross_validation/`：历史名称虽不完美，但含字节冻结 F2C 适配器，原路径保留；
- `selection/`、`confirmatory/`、`evidence/`：分别承担推荐、确证统计和证据纪律。

若未来确需改包名，必须以兼容入口 + 明确迁移期完成，不允许只改 README 先制造
第二套“逻辑目录”。

## 5. 注释规则

**英文标识符 + 简洁中文注释。** 生产源码注释只承担四件事：

1. 坐标系与参考系（UTM、顺时针为负…）；
2. 单位与量纲（若名字装不下）；
3. 状态与不变量的含义；
4. 非显然决策的原因（为什么不用显然的做法）。

**不进生产源码**：日期、迭代轮次（Block A/B/C）、field ID、历史实测
数字（「0/4000」「150.7 s」）、修复过程叙事。这些住在 AUDIT_NOTE.md、
evidence/、tests/、docs/ 里——它们是历史，历史有专门的住所。

constructive / LLM 候选代码再加一条：**注释不能替代契约**。例如“容量不会超”
必须由 `feasible_actions` / evaluator 证明，不能靠 heuristic docstring 声明。
