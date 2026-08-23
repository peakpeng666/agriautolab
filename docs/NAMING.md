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
- **类名表达角色**：`DubinsPathPlanner`（planner 是角色），
  `MinimumWidthSwathGenerator`（generator 是角色）。
- **函数名表达动作**：`extract_instance_features`、`summarize_pareto`。
- **字段名表达数学意义与单位**：SI 单位后缀（`_m`、`_rad`、`_s`），
  量纲进名字不进注释（`turning_radius_to_working_width_ratio`）。
- **五阶段槽位字符串是 wire ID**：`dubins_transit` / `reeds_shepp_transit` /
  `min_width` / `no_headland`… 进 config_id 与 pool_hash，永不改。

## 2. 语义修正（本轮改动的动机）

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

## 3. 类名对照（canonical 类 + legacy 别名）

`DubinsPathPlanner`/`DubinsTransit`、`ReedsSheppPathPlanner`/`ReedsSheppTransit`、
`BoustrophedonDecomposition`/`BoustrophedonCells`、`ConstantWidthHeadland`/
`UniformHeadland`、`MinimumWidthSwathGenerator`/`MinWidthSwath`、
`FixedAngleSwathGenerator`/`FixedAngleSwath`、`PrincipalAxisSwathGenerator`/
`PrincipalAxisSwath`、`LongestEdgeSwathGenerator`/`LongestEdgeSwathDirection`、
`RowAlignedSwathGenerator`/`RowAlignedSwath`、`BoustrophedonRoutePlanner`/
`BoustrophedonOrder`、`SkipOneRoutePlanner`/`SkipOneOrder`、
`GreedyRuralPostmanRoutePlanner`/`RuralPostmanGreedy`、
`TransferBreakdown`/`TransitBreakdown`。旧名一律保留为模块级别名。

## 4. 包结构

- `reconciliation/` 是 `cross_validation/` 的规范名（那里做的是 F2C 数值
  对账，不是机器学习交叉验证；Block D 将需要真正的 CV，名字必须让位）。
  `cross_validation/f2c.py` 为字节冻结的适配器，原路径原字节永不动。
- `benchmark/` 是 `corpus/` 的规范入口（语料=基准的运行时载体）。
- `domain/`、`planning/`、`selection/` 在 Block D 开工时按本规则创建，
  不预建空壳。

## 5. 注释规则

**英文标识符 + 简洁中文注释。** 生产源码注释只承担四件事：

1. 坐标系与参考系（UTM、顺时针为负…）；
2. 单位与量纲（若名字装不下）；
3. 状态与不变量的含义；
4. 非显然决策的原因（为什么不用显然的做法）。

**不进生产源码**：日期、迭代轮次（Block A/B/C）、field ID、历史实测
数字（「0/4000」「150.7 s」）、修复过程叙事。这些住在 AUDIT_NOTE.md、
evidence/、tests/、docs/ 里——它们是历史，历史有专门的住所。
