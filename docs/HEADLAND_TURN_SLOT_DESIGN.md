# headland_turn 槽位设计研究（Study-002 scoping）

> 工作流：A3（docs-only）
> 工作树：`~/wt/headland-turn-design`，分支 `docs/headland-turn-slot-design`
> 唯一产出：本文件。**不动任何代码**。
>
> 所有 file:line 引用均用 `grep` 锚点核对过，**不依赖提示词给出的行号**。

## TL;DR

- **现状**：`path` 阶段（`pipeline/run.py:52-57` 的 `_PATHS` 注册表）只暴露两个 wire ID：
  `dubins_transit` / `reeds_shepp_transit`，**均不暴露逐个地头转弯的策略选择点**——
  DubinsPathPlanner（`algorithms/path/dubins_transit.py:13-22`）与
  ReedsSheppPathPlanner（`algorithms/path/reeds_shepp_transit.py:188-…`）
  都把整条路线一次性委托给 `coverage.stages.path.DubinsPath.run(route, robot)`
  或六字闭式解+正演采样，没有 per-turn 决策。
- **结论（诚实）**：建议把 `headland_turn` **砍出** Study-002 候选槽位，列为
  Study-003 候选。研究主张相应收缩为「不主张全阶段自动设计」。
- **判据（按强度排序）**：① path 阶段评估最贵（解析 + 采样两遍以保确定性）；
  ② 解析最短词在多数几何下唯一，启发式自由度天然窄；③ 两槽位
  （`swath_angle` + `route_order`，见 PR #28）已足以支撑"多槽位互补演化"的
  研究主张；④ 与协议级 `ReverseCostSpec` / `allowed_region` 存在耦合，
  而 Study-002 尚未定这些参数。
- **若保留**（审慎的反弹判据）：先实测 PR #28 合并后单次评估成本，预算允许（参考
  Study-001 corpus 的 61,100 次运行级别的开销）再启动 path 阶段槽位设计。

> **本文修订说明（复核后）**：初稿有若干处引用了**不存在的 API** 或**不可能的
> 协议取值**，已逐条据实修正，修正点在正文内就地标注：
> `RouteArtifact.transfer_segments`（不存在，须自派生）、
> `kinematics.dubins.length_optimal`（不存在，且现有 API 跨家族取最短，
> 无法复算被选中的词）、独立 evaluator 缺 `cell_of_work_index`、
> `projection_norm` 未减质心因而不是平移不变量、
> `fixed_angle` 不具旋转等变性（不做 PCA）、
> `reverse_cost=0` 在本仓库构造不出来（`ge=1.0`）。
> 最后一条曾被用作支持"砍掉本槽位"的论据之一，**该论据已减弱**；
> 结论不变，但现在主要依赖判据 ① 与 ②。

---

## 1. path 阶段暴露逐转弯选择点的最小改动方案

### 1.1 现状的结构障碍

`src/agriautolab/pipeline/run.py:52-57`：

```python
_ROUTES = {
    "boustrophedon_order": BoustrophedonRoutePlanner,
    "skip_one_order": SkipOneRoutePlanner,
    "rural_postman_greedy": GreedyRuralPostmanRoutePlanner,
}
_PATHS = {"dubins_transit": DubinsPathPlanner, "reeds_shepp_transit": ReedsSheppPathPlanner}
```

`src/agriautolab/algorithms/path/dubins_transit.py:13-22` 的 `DubinsPathPlanner.run`
接受**整条** `RouteArtifact`，内部 `DubinsPath(self.sample_step_m).run(route, robot)`
一次性走完。没有 per-turn 状态外露给候选。

### 1.2 最小改动路径

新增一个 `path` 阶段的 wire ID —— `selective_turn_transit` —— 并在
`run.py` 的 `_PATHS` 注册到新的 planner 类。

**转移段必须自己派生，`RouteArtifact` 没有现成字段。** 实测其契约只有两个成员：

```python
class RouteArtifact(BaseModel):
    traversals: tuple[SwathTraversal, ...]
    swaths: tuple[Swath, ...]
```

因此「逐 transfer 段」要由**相邻有向 traversal 两两配对**派生：第 i 段的起点 =
第 i 个 traversal 按其 `direction` 的出口端点，终点 = 第 i+1 个 traversal 按其
`direction` 的入口端点。n 个 traversal 给出 n−1 个转移段。这与 `route_order`
槽位（PR #28）里 `entry_of`/`exit_of` 按访问序奇偶取端点的做法同源，应当复用
而不是各写一套。**不要**扩展 `RouteArtifact` 契约来塞 `transfer_segments`：
它是刻意精简的产物契约，派生量属于消费方。

planner 对每段枚举离散转弯类型（U-turn / teardrop / curve-only /
hook 等，从现有 Dubins 六字与 Reeds-Shepp 46 字里挑出**正反向约定一致**的子集），
按 `params["turn_type:<segment_index>"]`（如 `"turn_type:3" → "curve_only"`）
烘焙选择。**注意：候选选择是按段枚举+评分的，而不是按段重写解析公式**——解析
最短词仍由 Dubins/Reeds-Shepp 闭式解决定，候选只决定"我接受哪个闭式解家族"。

**因果链（让 13 个冻结 config_id 逐位不变）**：
`src/agriautolab/pipeline/config.py:20-33` 的 `PipelineConfig.config_id` 是
`content_hash({五槽位字符串 + dict(sorted(params.items()))})`，**只哈希自身**，
不引用全局注册表。`configs/corpus_13.json` 的 13 个冻结配置 path 槽位只用
`"dubins_transit"` 与 `"reeds_shepp_transit"`，不引入 `"selective_turn_transit"`；
它们的 `params` 也不含 `"turn_type:<i>"` 键。新增 ID 改的是 `_PATHS` 注册表
**查询路径**，对已有 `config_id` 的输入/输出都是只读。既有 corpus 守卫测试
（钉住"config_id 跨冻结配置逐位相等"）会**自动保护**这一点。

### 1.3 运行时形态与 ConstructiveProblem 化

- **新 planner 接口**：`run(route, robot, *, allowed_region=None) -> PathArtifact`，
  内部按 §1.2 的方式从相邻 traversal 对**派生**转移段（`RouteArtifact` 无
  `transfer_segments` 字段）；
  对每段调用 `_select_turn_type(transfer, params)` 取 `params` 烘焙的离散选择；
  按选择调对应解析闭式解 + 采样；按 `transit` 顺序拼接。
- **ConstructiveProblem 化**（对照 `src/agriautolab/optimization/constructive.py:21-44`）：
  `StateT = tuple[int, ...]`（已选段索引）；`ActionT = Literal["uturn","teardrop","curve_only","hook"]`；
  `feasible_actions(state)` 返回该段在解析可达 + allowed_region 内的**全集**；
  `apply_action` 必须收 `action in feasible_actions(state)`，否则
  `ValueError`（与 CVRP 硬约束纪律一致，见 `cvrp.py:155-156`）；
  `finalize` 返回完整 PathArtifact。**候选只评分，硬约束在 problem 侧**——
  候选返回越界类型被 problem 直接拒，不让闸门吞。
- **agent 侧**：`agent/slots.py` 的 `SLOTS` 新增 `headland_turn` 项；
  `proposer.PROMPT_TEMPLATES["headland_turn"]` 注册契约函数名（如
  `next_turn_score`）；`proposer.MOCK_CANDIDATES_BY_SLOT["headland_turn"]` 提供
  4 个源码级候选（如"恒取 dubins 直行"、"恒取 teardrop"、"按曲率符号选"、
  "按 distance_norm 选"）；`reviewer.py` 加 `headland_turn` 专属复核器集
  （**不**沿用 `DEFAULT_REVIEWERS` 的 |v|≤π/2 假设——离散类型不连续，hard 否决
  只用于"返回非有限 / 抛异常 / 不在枚举内"）。

### 1.4 改动面清单

| 文件 | 变更 |
|---|---|
| `src/agriautolab/pipeline/run.py` | `_PATHS` 注册 `selective_turn_transit` |
| `src/agriautolab/algorithms/path/selective_turn_transit.py`（新） | 段枚举 + 离散选择 + 解析闭式解调度 |
| `src/agriautolab/agent/slots.py` | `HeadlandTurnSlot` 实现八成员协议 |
| `src/agriautolab/agent/proposer.py` | `PROMPT_TEMPLATES` / `MOCK_CANDIDATES_BY_SLOT` 各加一项 |
| `src/agriautolab/agent/reviewer.py` | `HEADLAND_TURN_REVIEWERS`（**不复用** swath 内嵌假设） |
| `tests/agent/test_headland_turn.py`（新） | 真值测试（见 §3 / §4） |

## 2. 候选函数签名应该是什么？能看到哪些特征？

### 2.1 签名建议

```python
def next_turn_score(state: Mapping[str, float], candidate: Mapping[str, float]) -> float
```

与 `docs/OPTIMIZATION_FOUNDATIONS.md:50` 的 `next_swath_score(state, candidate)`
形态严格对齐——这保证**领域 adapter** 接入公共 constructive 协议时不需要扭曲签名。

### 2.2 可用键清单（**必须旋转不变**）

- `state["visited_transfer_count"]`：已选段数（无量纲）
- `state["remaining_transfer_count"]`：未选段数（无量纲）
- `state["curvature_sign_balance"]`：已选段曲率符号 ±1 的累计（无量纲；旋转不变）
- `state["distance_remaining_norm"]`：剩余转移总长 / `min_turning_radius`（无量纲）

- `candidate["distance_norm"]`：本段欧氏起讫距离 / `min_turning_radius`
- `candidate["projection_norm"]`：**（段中点 − 地块质心）** 在已选主轴法向上的
  投影 / `working_width`

  > **必须先减质心，否则这个键在平移下不是不变量。** 设中点 `p`、法向 `n`、
  > 平移 `t`，未减质心时投影从 `p·n` 变为 `p·n + t·n`——整体加同一常数。
  > 纯按该键排序看不出（同序），但只要候选把它与 `distance_norm` 混合加权
  > （例如 `0.6*d + 0.4*proj`），次序就会随 `tx`/`ty` 改变，候选于是**因为
  > 平移而非自身缺陷**被 invariance 闸拒。减去随刚体变换协变的原点
  > （地块质心或转移段集合质心）之后，`(p−c)·n` 才真正平移不变。
  >
  > 这不是假设性风险：PR #28 的 `route_order` 槽位实现里出现过同一缺陷，
  > 已由 `test_projection_is_translation_invariant` 钉住并修复。新槽位应
  > 直接复用 `algorithms/route/constructive_order.py::project_candidate` 的
  > 减质心写法。
- `candidate["curvature_sign"]`：本段解析解的曲率符号 ∈ {-1.0, 0.0, +1.0}（无量纲）
- `candidate["turn_type_onehot"]`：四选一 one-hot（无量纲，4 维）

**为什么这些键必须旋转不变**：`src/agriautolab/features/invariance.py:13-34` 的
`FEATURE_INVARIANCE` 表里所有可计算特征默认 `rotation_invariant=True`；演化闸门
的 invariance 闸（`SwathAngleSlot.invariance_check`，`slots.py:147-182`）是
8 组随机刚体变换后要求偏移不变——headland_turn 槽位的 invariance 闸需沿用同一
8×3 uniform 消耗模式（见 §3）。如果键含 `direction_deg` 这种 raw 角度，invariance
闸当场把它打死。

**禁止**：
- raw 角度（`direction_deg`、`angle_rad`）—— 旋转变换下会跳变
- raw 坐标（`x_m`、`y_m`）—— 平移变换下会跳变
- 任何 `area_m2` / `perimeter_area_ratio` 这类**地块级**特征——单段决策看不到地块
- `runtime_ms` 类的实现性指标——既看不到，也不该被候选利用

## 3. 不变性闸对"离散转弯类型选择"怎么定义？

### 3.1 定义

```
对 8 组独立随机刚体变换（每组 3 次 uniform，顺序 theta/tx/ty，范围
(-pi,pi) 与 (-100,100)×2；与 SwathAngleSlot.invariance_check 完全相同的
消耗模式，slots.py:155-157）：

  设 base_sequence = 候选在参考田上烘焙的逐段 turn_type 序列
  设 rotated_sequence_i = 旋转变换 i 后重新烘焙的逐段 turn_type 序列

  闸门通过 iff 对所有 i：rotated_sequence_i 元素逐位 == base_sequence
```

### 3.2 与 swath_angle 的语义区别

| | swath_angle 槽位 | headland_turn 槽位 |
|---|---|---|
| 决策量 | 标量 `angle_rad`（连续） | 离散序列 `tuple[turn_type, ...]` |
| 不变语义 | "旋转后偏移漂移 < 1e-9" | "旋转后序列逐元素相同" |
| 闸门实现 | `abs(rotated - base) < 1e-9` | `tuple(rotated) == tuple(base)` |
| 浮点容差 | 必要（ULP 噪声） | 不必要（离散相等） |
| 漂移诊断 | 报"漂移 X.3e" | 报"在 index K 处由 X 变 Y" |

**关键差异**：swath_angle 闸门**容许 ULP 级偏差**（容差 1e-9，见
`slots.py:177-181`），因为连续标量在浮点路径上不可避免。headland_turn 闸门
是**严格相等**——离散枚举没有 ULP 噪声，序列错位即为违反。如果某个版本引入了
"按曲率符号 + 1e-6 阈值选类型"这种伪连续判断，invariance 闸门会立刻把它打死
（旋转后曲率符号可能恰好跨 0，类型就跳了），这种"接近但不同"是研究对象该有的
失败模式，不是 bug。

### 3.3 结构性风险与处理

**风险**：`headland_turn` 槽位的 invariance 闸**强于** swath_angle；某些
swath 生成器在 id 分配上不具旋转等变性（`min_width` 生成器在旋转后主轴方向
解算可能因数值抖动产生**相邻枚举**互换），这会让"同候选的同源码在旋转后
给出不同 turn_type 序列"成为候选源码的问题还是生成器的问题。**处理决策**：

1. 闸门**不**豁免——豁免 invariance 等于把这条轴线砍掉，研究主张就空了。
2. 候选源码**必须**用旋转不变键（见 §2.2）做评分；任何包含 raw 角度的候选
   在 invariance 闸必拒。
3. 若实测发现 swath 生成器 id 分配漂移（`min_width` 是高风险项，因它解
   `min_width_direction` 闭式解），§4 真值测试必须用 **`principal_axis`** 作为
   参考生成器：它按 PCA 主轴取方向，主轴随地块一同旋转，因此是旋转等变的。

   > **不要用 `fixed_angle`。** 实测其实现是
   > `swaths_along_direction(mains, cos(self.angle_rad), sin(self.angle_rad), ...)`
   > ——方向直接来自协议参数，**完全不做 PCA**。只旋转地块而不同时旋转
   > `params["angle_rad"]` 时，条带方向不变而地块变了，条带数量与邻接关系
   > 都会变，严格序列闸会把一个本来不变的转弯启发式判为失败——**失败原因
   > 在上游生成器，不在候选**。若确需用 `fixed_angle` 做对照，必须把刚体
   > 旋转量显式加进 `angle_rad`（`angle_rad + theta`），与
   > `SwathAngleSlot.invariance_check` 对 `row_structure.direction_rad`
   > 的协变处理同源。

## 4. 独立 evaluator 如何在不复用候选逻辑的前提下复算转弯代价？

### 4.1 纪律来源

`src/agriautolab/optimization/cvrp.py:159-167` 的 `_exact_route_demand` 是
本仓库"独立复算"纪律的标本：

```python
def _exact_route_demand(customer_ids, customers_by_id) -> Fraction:
    """独立于 constructor 整数单位状态，精确复算 binary64 路线总需求。"""
    return sum(
        (Fraction.from_float(customers_by_id[customer_id].demand) for customer_id in customer_ids),
        Fraction(0),
    )
```

要点：**不复用 constructor 任何累计值**，独立从原始输入（`customers_by_id`
dict）按**新路径**（Fraction.from_float）复算，注释明言"独立"。

### 4.2 headland_turn 独立 evaluator

```python
def evaluate_headland_turn_path(
    path_artifact: PathArtifact,
    route: RouteArtifact,
    robot: VehicleSpec,
    *,
    turn_type_sequence: tuple[str, ...],
    cell_of_work_index: tuple[int, ...],   # 必需，见下
) -> TransferBreakdown:
    """对 path_artifact 逐 transfer 段用 kinematics 独立复算长度与可行性。

    不调用 selective_turn_transit planner 的任何内部状态：按 turn_type_sequence
    对每段**在候选家族内**独立复算（见下），与 planner 自报值对照，
    差异 > 1e-6 抛 ValueError。
    """
```

**为什么必须逐段独立**：planner 在 `selective_turn_transit` 内部有累计状态
（`curvature_sign_balance` 等被未来候选可能利用的中间量）。如果 evaluator
接受 planner 自报的中间结果，就是允许候选把"对自己有利的统计偏差"洗进评估
——**违反独立性原则**。

**但复算必须复算"被选中的那个词"，不是全局最短词。** 这是本节最容易写错的地方：

实测 `src/agriautolab/kinematics/dubins.py` 的公开 API 只有

```
dubins_words(start, goal, radius) -> tuple[DubinsWord, ...]   # 全部可行家族
dubins_word(start, goal, radius)  -> DubinsWord               # 跨家族取最短
dubins_length(p0, p1, radius)     -> float                    # 跨家族取最短长度
dubins_endpoint(start, word, radius) -> Pose2D
```

**没有 `length_optimal`**。而 `dubins_word` / `dubins_length` 都是**跨家族求最小**，
完全忽略 `turn_type_sequence`。若拿它们做复算，会出现两种错误：候选**故意**选了
非最短家族时，evaluator 拿最短词去比对 → 差异超阈值 → 合法候选被误拒；或者
反过来报出一个与实际所选转弯无关的代价。

正确做法：调 `dubins_words(...)`（Reeds-Shepp 侧同理用 `reeds_shepp_words`）拿到
**全部家族**，按 `turn_type_sequence[i]` 从中**挑出被选中的那一个**，再对它
`dubins_endpoint` 正演闭合校验并取长度。这样复算路径与 planner 同源但独立，
差异只在浮点 ULP，且能真正验证"候选选的那个词"。

**`cell_of_work_index` 为什么必需**：`TransferBreakdown` 的
`turn_total_m` 与 `inter_cell_m` 是两个不同类别，而实测
`metrics/path.py` 的 `transit_breakdown(path, *, cell_of_work_index)` 正是靠这个
映射把二者分开。`RouteArtifact` **刻意不携带 cell 归属**，所以只给
`path_artifact + route` 的签名在多 cell 路线上无法产出承诺的分解——实现只能把
所有作业段间连接一律当成转弯，两个类别同时失真。因此 evaluator 必须显式接收
`cell_of_work_index`（或能派生它的 `CellsArtifact`）。

### 4.3 TransferBreakdown 守门

`metrics/path.py:174-…` 的 `TransferBreakdown` 五项分解（`entry_leg_m` /
`turn_total_m` / `inter_cell_m` / `exit_leg_m` / `other_m`）是「完备性哨兵」：
`other_m ≠ 0` 当场抛（注释明言"非零即抛，因为分类不完备就是分类错误"）。
headland_turn 槽位的独立 evaluator 必须用同一个 `TransferBreakdown` 类型
返回，不另造一个新分解类——避免**新指标悄悄绕开完备性守门**。

## 5. 这个槽位是否值得进 Study-002？双向论证

### 5.1 支持进 Study-002 的证据

- **几何空间真实存在**：Dubins 六字 + Reeds-Shepp 46 字确实提供了多个解析解家族；
  在某些地块（带障碍、allowed_region 收窄）下不同家族的可达性不同，**选哪个家族**
  是真实决策点，不只是参数微调。
- **互补性可能**：swath_angle 选扫掠方向、route_order 选访问序——这两者选完后，
  headland_turn 决定"端到端如何过渡"。三槽位覆盖了"长程几何 + 离散序贯 + 短程
  过渡"的完整决策谱，**研究主张更饱满**。
- **可证伪**：invariance 闸的离散相等是强约束（不像 swath_angle 有 1e-9 容差），
  阴性结果（"演化在 headland_turn 上无法超越解析最短词"）本身就是有信息量的结论。

### 5.2 反对进 Study-002 的证据

- **评估成本**：path 阶段是五阶段里评估最贵的（Dubins 解析 + 采样两遍以保
  确定性；transfer 段数随 swaths 线性增长）。粗估每候选每实例 path 阶段耗时
  ≥10× 于 route_order 槽位（实测需要任务 3 合并后跑任务 1 的 `anytime_curve`
  才能给硬数字）。Study-001 corpus 是 61 100 次运行级别；若 Study-002 四臂
  × 165 训练田 × 13 池 × R 轮的评估数已逼近 corpus 量级，再加 path 阶段多
  消耗 10×，**预算爆炸**。
- **解析最短词主导**：Dubins/Reeds-Shepp 闭式解在多数几何下给出**唯一最短词**，
  候选"选择不同家族"只在边界几何上（非对称、allowed_region 紧、reverse_cost
  极化）有自由度。**启发式自由度天然窄**——这是任务 2 spec 描述里直接说出的
  事实。
- **协议纠缠**：headland_turn 的合理选择与协议级 `ReverseCostSpec` 和
  `allowed_region` 强耦合，Study-002 的协议细节尚未确定（见任务 5），
  把它一起绑进来等于多绑一个未定参数。

  > **勘误（本轮复核修正）**：本节初稿写的是「`reverse_cost=0` 时所有解析解
  > 代价相等、`reverse_cost` 极大时只能选直行」。这两个论据都不成立，因为
  > 实测 `contracts/protocol.py` 的约束是
  > `reverse_length_multiplier: float = Field(ge=1.0)`——**取 0 在本仓库
  > 根本构造不出来**，倒车永远不比前进便宜；换挡罚则是独立的非负项。
  > 即便取几何退化设置 `(multiplier=1, penalty=0)`，不同家族的几何长度本来
  > 就不同，代价并不相等；换挡罚则极大时解趋近**纯前向 Dubins 词**，也不是
  > 「只能选直行」。
  >
  > 用有效取值重述后，本条论据**减弱但未推翻**：真实存在的耦合是
  > `multiplier` 与 `gear_shift_penalty` 共同决定含倒车家族（Reeds-Shepp）
  > 相对纯前向家族的相对代价，从而改变候选的可选面。这仍然是一个未定协议
  > 参数与研究结论的纠缠，只是不再有「代价全等」「退化为单点」这样的极端形态。
  > 结论所依赖的主要论据仍是**评估成本**与**解析最短词主导**两条。
- **与两槽位重叠**：swath_angle（选长程方向）已经决定了"主轴大致怎么走"，
  route_order（选访问序）决定了"哪些段相邻"。**headland_turn 的很多选择
  被前两槽位隐式决定**——三槽位的"互补"是表面的，实际自由度被前两槽位锁
  了大半。

### 5.3 结论

**建议砍出 Study-002，列为 Study-003 候选。** 研究主张相应收缩：

| 现状假设 | 砍出 headland_turn 后 |
|---|---|
| "演化能在三槽位上同时发现互补启发式" | "演化能在双槽位上发现互补启发式" |
| "path 阶段是评估预算的主要压力点" | "swath + route 是预算主要压力点" |
| "全阶段自动设计是可行研究路线" | "自动设计有阶段边界：path 阶段当前不适合" |

**诚实动机**：Study-001 的 H3 是预注册阴性结果（"H3 未获支持"——见
`CHANGELOG.md:48-83` 的 D7/H3 段），这是项目的优点。Study-002 不必为了"三个
槽位"凑齐而硬做 headland_turn——阴性结论（"headland_turn 不适合自动设计"）
同样是**有信息量的预注册结果**，且更符合 H3 既往发现所暗示的"自动设计有阶段
边界"的研究方向。

### 5.4 若保留的判据（审慎的反弹条件）

仅当以下**全部**成立时，headland_turn 才进 Study-002：

1. 任务 3（route_order）合并后，跑任务 1 的 `anytime_curve` 实测**单次评估
   成本中位数 ≤ 0.5× 当前 corpus 单次运行中位数**（即 route_order 没有把
   评估代价推高到不可接受）；
2. Study-002 协议细节（`reverse_cost`、`allowed_region`）已在任务 5 预注册
   中固定，不留 headland_turn 与协议纠缠的余地；
3. Study-002 预算公式（任务 5 的 I×P + Σ_round(3 + [I if evaluated])）的
   总评估数 ≤ 5× Study-001 corpus（305 500 次）——留出 path 阶段 10× 系数
   后的上限。

否则**维持砍出决策**。

---

## 对 Study-002 的建议与影响

- **本文件交付**：研究主张（结论 §5.3）建议"砍出 headland_turn"；
- **任务 3（route_order）继续推进**——双槽位足以支撑"多槽位互补演化"主张；
- **任务 4（LLM provenance）继续推进**——与槽位数无关；
- **任务 5（Study-002 预注册）写 `non_goals` 时**：把 headland_turn 列为
  显式非目标，并引用本文件 §5.3 作为研究主张收缩的判据来源；
- **后续**（非 M3 范围）：Study-003 启动时如要重启 headland_turn 评估，需
  先有 path 阶段成本实测与协议细节固定两项前置（§5.4 三条件）。
