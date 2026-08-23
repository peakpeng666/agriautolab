# 架构与依赖方向（原 README 的分层说明，长期有效）

AgriAutoLab Block A 是面向农业覆盖路径规划（Coverage Path Planning, CPP）的可复现实验基准内核。
它先把问题契约、几何域、指标、五阶段基线、独立校验与证据链做实，再允许上层做 benchmark、推荐或自动算法设计。
本包只做 Python/Shapely 的二维几何与算法仿真，不模拟动力学或硬件。

## 分层与依赖方向

依赖只能向下：`contracts → geometry → kinematics/algorithms → metrics/coverage/pareto/features/pipeline → validation/evidence/agent`。
`algorithms` 只保存能力卡与 `(stage, ProblemKind)` 分区，不保存“谁应该赢”的知识。
Benchmark 不得 import Terminal；Algorithm 不得知道 selector、LLM、排名或最终推荐结果。

## 本轮已实现（Block A）

- TaskType × ScenarioDynamics × ProblemKind 防火墙与米制 CRS 守卫
- 严格几何校验、规范 WKB 哈希、`robust_union`、统一 `QUAD_SEGS=16`
- flat-cap 机具扫掠；覆盖率分母由 `resolve_coverage_targets` 一处锁定：构造令牌、语义不变量、分母 provenance 三层防自造，地头宽度申报逐 cell 重算可证伪
- `PolygonSpec.from_wkt` / `to_wkt`：对接 Fields2Benchmark 与 Fields2Cover 的 WKT 交换格式
- 路径长度、总航向变化、AOL、tortuosity、cusp、按弧长密化 clearance
- PRIMARY：`overlap_ratio`、`nonwork_normalized`
- HARD_CONSTRAINT：`coverage_ratio_field`、collision、curvature、outside area
- DIAGNOSTIC 且 PROTOCOL_BOUND：`coverage_ratio_main`（分母随 headland 配置变化，禁止用作门槛）
- NoDecomposition → ConstantWidthHeadland → MBRDirectionSwath → BoustrophedonRoute → DubinsPath
- Dubins 六型 LSL/RSR/LSR/RSL/RLR/LRL 的前进最短路
- 独立路径校验器、算法卡注册表、内容/源码/环境哈希与哈希链账本

## Block B 增量（偏好条件下的 Pareto 推荐基建）

- `RowStructure` 契约：穿行数与各向异性代价全部解析可算（`crossings_between` 端点投影 / 行距）
- 五阶段可组合算法池（12 个）：BCD 分解（连通性合并）、恒等/均匀地头、五种 swath
  （fixed_angle/principal_axis/min_width/longest_edge/row_aligned）、三种 route
  （牛耕/隔行/贪心 Rural-Postman——按弧路径而非 TSP 建模）、Dubins 转移
- `kinematics/dubins.py`：六字闭式解 + 5000 组正演闭合（LRL 陷阱按几何推导写并在 docstring 留案）
- `pipeline/`：组合体执行 + 阶段产物按内容哈希记忆化；不可行组合按 RunStatus 记录，不伪造目标向量
- `pareto/`：三维目标向量（path_length/headland_turn_count/row_crossings）、Pareto 前沿
  （pool_hash 必须随前沿量记录）、精确 3D 超体积（参考点由协议必填声明、解析上界导出、
  越界显式标记不静默截断）、加权切比雪夫标量化（可选中非凸前沿点，加权和不能）
- `features/`：10 个农业几何特征 + 逐特征提取耗时 + 不变性契约（200 组随机刚体变换测试）
- `agent/`：沙箱（AST 静态扫描 + 受限 exec，纪律不是安全边界）、四道闸
  （契约/校验/确定性/不变性）、对抗式复核（默认 refuted，多数否决）、
  演化循环（适应度 = 超体积增量，EoH-S CPI 的多目标对应物）、哈希链演化账本（淘汰也记账）
- `prereg/AGRIPLAN-PARETO-001.yaml` + 字节级封存脚本 + `HoldoutVault`（纪律不是安全）
- 指标新增：`transit_length`（与 path_length ρ=1.000，DIAGNOSTIC 不进主向量）、
  `headland_turn_count`（与禁用的 turn_count 语义不同，notes 写明）、`row_crossings`

## 明确未实现

- benchmark runner、selector、agent、LLM/API、MCP、Web 或终端交互层
- Reeds-Shepp、动态重规划、真实车辆动力学、滑移、能耗、电池、质量和摩擦
- Boustrophedon 等分解算法、多个 headland/swath/route/path 候选算法
- Fields2Benchmark/Fields2Cover 外部基线适配器与论文级批量实验
- 非单 Polygon 的 headland 基线输出；复杂拓扑应在后续阶段显式扩展契约

## 安装与测试

```bash
python -m pip install -e ".[dev]"
pytest -q
```

## 工程纪律

1. 指标必须声明可比性；通不过由 `MetricSpec` 驱动的不变性测试，不得进入主排名。
2. 规划器自述一律不采信；可行性和指标由独立校验器从几何重新计算。
3. 失败是数据；失败、超时、拒绝必须保留为 `RunStatus` 与结构化失败原因，不能伪装成零长度。
4. 几何并集必须走 `robust_union`，不得在业务代码绕过自检。
5. 覆盖率分母由 `BenchmarkProtocol.coverage_target` 指定并进入 `spec_hash()`；硬门槛恒用对原田的覆盖率。

## 异议

- `robust_union` 的面积区间自检能抓“整块丢失导致面积越下界”的故障，但对高度重叠几何并非完备证明；后续若把它作为论文核心证据，应增加基于分块覆盖或高精度参考的独立交叉校验。代码仍严格按本轮指定的两层策略实现。
- 规范 WKB 哈希忠实区分浮点 epsilon，但由几何运算新生成的顶点仍可能受 GEOS 版本影响；因此证据链同时记录环境指纹，跨 GEOS 版本不应把结果哈希相同当作默认前提。


## Benchmark design notes

- Vehicle 表示作业车辆约束，不表示动力学机器人。
- Validator 独立重算几何指标，不采信规划器自报结果。
- Artifact 应逐步携带 provenance，用于未来算法库检索和大模型推荐的数据基础。
- 当前 Block A 聚焦二维农业 CPP，不扩展到 ROS、动力学或传感器仿真。
