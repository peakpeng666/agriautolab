# AUDIT_NOTE

本文件记录对 Block A 的外部复核结论与后续整改。

## 复核结论（承接自外部独立复核）

核心正确性可信：几何内核、`robust_union`、分段不变性、七条解析真值，以及
`L_area·(1−η_L) = 1 + overlap_ratio` 这个代数恒等式，均由外部断言独立验证通过，
残差量级 1e-12 到 0.00e+00。以下六项不是风格问题，是已用数据证明会出问题的地方。

---

## 2026-08-20 整改：六处问题 + docstring 语言回归

基线：整改前 `pytest -q` 无法收集（包不可 import）。修复任务 1 后基线为 **242 passed / 30 skipped**。
整改后为 **286 passed / 30 skipped**，新增 44 条，原有 242 条断言的数值一条未改。

### 任务 1：字面量 `\n` 与字段改名不一致

**改动位置**

- `src/agriautolab/contracts/problem.py:29` —— 一整行被字面量 `\n` 粘死的注释吞掉了
  `class GridPointToPointProblem`，包无法 import。拆回真实换行，并把注释重写为该类存在的真实理由
  （给 schema 防火墙当反例／对照组），删掉「for compatibility with legacy tests」这个编造的说法。
- `src/agriautolab/contracts/vehicle.py` —— `footprint_width_m` → `body_width_m`，
  与 `geometry/kernel.py`、`metrics/constraints.py`、`validation/validator.py` 以及全部测试对齐。
  同时把无人引用的 `footprint_length_m` 一并改为 `body_length_m`，保持 `body_*` 命名成对。

**验收**：`python -c "import agriautolab"` 通过；`pytest -q` 242 passed，0 failed。

### 任务 2：锁死覆盖率分母（核心）

**改动位置**

- `src/agriautolab/contracts/enums.py` —— 新增 `CoverageTarget`（`ORIGINAL_FIELD` / `MAIN_FIELD`）。
- `src/agriautolab/contracts/protocol.py` —— `BenchmarkProtocol` 增加 `coverage_target: CoverageTarget`，
  **无默认值**；新增 `spec_hash()`，复用 `evidence/hashing.py` 的 `content_hash`。
- `src/agriautolab/metrics/coverage.py` —— 新增 `CoverageTargets` 冻结数据类与
  `resolve_coverage_targets(problem, headland, *, target)`。这是系统里唯一的分母来源：
  `original_field = 地块 − 障碍`，`main_field = 地头阶段主田 ∪ − 障碍`。
  `CoverageTargets.__post_init__` 校验两者面积为正且 `main_field ⊆ original_field`。
- `src/agriautolab/metrics/coverage.py` —— `coverage_stats` 签名由 `coverable: BaseGeometry`
  改为 `targets: CoverageTargets`，并对非 `CoverageTargets` 入参显式抛 `TypeError`。
  `CoverageStats` 同时返回 `coverage_ratio_field` 与 `coverage_ratio_main`，
  外加 `target_kind` 与 `selected_coverage_ratio()`。
- `src/agriautolab/metrics/registry.py` —— 原 `coverage_ratio` 拆成
  `coverage_ratio_field`（`HARD_CONSTRAINT` / `IMPL_INVARIANT`）与
  `coverage_ratio_main`（`DIAGNOSTIC` / `PROTOCOL_BOUND`，`notes` 写明四组实测数值）。
- `src/agriautolab/validation/validator.py` —— 硬门槛改判 `coverage_ratio_field`；
  `validate()` 增加只读关键字参数 `headland: HeadlandArtifact | None = None`，
  分母只能来自地头阶段产物或 `None`（表示没跑地头），仍然无法由调用方自造。
- `tests/conftest.py` —— 新增 `targets_from_geometry` 与 `coverage_targets` 夹具，
  测试侧构造分母同样必须过 `resolve_coverage_targets`。

**新增测试** `tests/stages/test_coverage_denominator.py`

- `test_main_field_ratio_stays_perfect_while_field_ratio_collapses`（参数化 2/6/12/18 米）
  —— 把实测表固化：主田面积 4416/3344/1976/896 m²，对主田覆盖率全为 1.0000，
  对原田分别为 0.8832/0.6688/0.3952/0.1792（rel=1e-3）。
- `test_hard_gate_uses_field_ratio_even_when_protocol_selects_main_field`
  —— 地头 18 米、`tau=0.9`、协议声明 `MAIN_FIELD`，仍必须判 `constraint_violation:coverage_threshold`。
- `test_coverage_stats_rejects_bare_geometry_as_denominator` —— 裸 `BaseGeometry` 抛 `TypeError`。
- `test_coverage_target_changes_protocol_hash` —— `coverage_target` 改变则 `spec_hash()` 改变。
- 另加五条：`test_denominators_do_not_depend_on_declared_target`、
  `test_missing_headland_makes_main_field_equal_original_field`、
  `test_main_field_excludes_obstacles_that_headland_stage_never_saw`、
  `test_hand_built_targets_cannot_place_main_field_outside_original_field`、
  `test_obstacle_outside_field_is_rejected_not_silently_clipped`
  （`resolve_coverage_targets` 同样调用 `validate_obstacles_within_field`：
  越界障碍若被 `difference` 静默裁掉，分母看着正常，少掉的面积再也查不出来自哪里）。

**因签名变更而修改调用方式（断言数值未动）**

- `tests/analytic/test_geometry_truths.py`：三处 `coverable=` → `targets=`，`stats.coverage_ratio` → `stats.coverage_ratio_field`。
- `tests/invariance/test_metric_declarations.py`：`_evaluate` 补上两个新 metric_id 的算法。
- `tests/stages/test_validator.py`：六处 `BenchmarkProtocol(...)` 补 `coverage_target=`。

### 任务 3：`resample_uniform` 的定位

**改动位置**

- `src/agriautolab/metrics/path.py` —— 补 docstring，写明它是低通滤波器而非几何等价变换、
  会切角会缩短长度、`step` 是协议参数（同 step 可比、跨 step 不可比）、主流程不启用及其理由、
  保留它的场景，并记入实测值（150.0 → 134.7 @ step=60）。函数体未改。

**新增测试** `tests/determinism/test_determinism.py`

- `test_resample_uniform_is_a_filter_not_a_geometry_preserving_transform`
  —— 用错开拐点的步长 7.0 / 13.0 / 60.0，断言长度严格小于原长且随步长单调不增。
  刻意不用 50.0：它恰好落在 (100,0) 拐点上，切不到角，测不出滤波行为。
- `test_resample_uniform_step60_cuts_the_documented_15_meters` —— 钉住 134.7 这个实测值。

### 任务 4：删除虚构的兼容层

**改动位置**

- 删除 `src/agriautolab/contracts/robot.py`。「保留 `CoverageRobotSpec` 以免破坏 existing experiments」
  这个理由不成立——这是全新构建，不存在 existing experiments。
- 全仓库 `CoverageRobotSpec` → `VehicleSpec`，共 5 个源码文件、6 个测试文件；
  `src/agriautolab/__init__.py` 的导入与 `__all__` 一并改。

**验收**：无新增测试，原有测试全绿即为验收（该类型在 11 个文件中被构造和使用）。

### 任务 5：PolygonSpec 与 WKT 互转

**改动位置**

- `src/agriautolab/contracts/geometry.py` —— `PolygonSpec` 增加 `from_wkt` 与 `to_wkt`，字段结构不变。
  `from_wkt` 走 `validate_geometry`，不调 `make_valid`；解析失败、非 Polygon、空几何、自交
  一律抛 `GeometryValidationError`。`to_wkt` 经 `shapely.normalize`，并显式传
  `rounding_precision=-1`（shapely 默认 6 位小数会让导出有损，往返哈希对不上）。
  两个方法内用延迟导入，因为 `geometry/validate.py` 依赖本模块，模块级导入会成环。

**新增测试** `tests/contracts/test_wkt_interop.py`

- `test_wkt_roundtrip_preserves_geometry_hash`、`test_wkt_roundtrip_preserves_polygon_with_hole`
- `test_to_wkt_is_lossless_at_float_epsilon`（钉住 0.9999999999999999 不被磨平）
- `test_normalize_makes_ring_start_vertex_irrelevant`
- `test_self_intersecting_wkt_is_rejected_not_repaired`
- `test_non_polygon_and_malformed_wkt_are_rejected`（参数化 5 例）

### 任务 6：`min_turning_radius_m` 允许为 0

**改动位置**

- `src/agriautolab/contracts/vehicle.py` —— `Field(gt=0)` → `Field(ge=0)`，
  新增只读属性 `can_turn_in_place`（阈值 1e-9，因为半径常由传动比反算、会带浮点尾巴）。
- `src/agriautolab/contracts/errors.py` —— 新增 `KinematicModelError`。
- `src/agriautolab/coverage/stages/path.py` —— `DubinsPath.run()` 入口检查 `can_turn_in_place`，
  命中即抛 `KinematicModelError` 并说明原因。Dubins 在 R=0 处 `d = distance/R` 与曲率 `1/R` 同时发散，
  不拦住就会跑出 `ZeroDivisionError` 或满屏 NaN 坐标。
- `src/agriautolab/validation/validator.py` —— 曲率上界改为
  `math.inf if robot.can_turn_in_place else 1.0 / robot.min_turning_radius_m`，否则校验器自身会被 1/0 炸掉。

**新增测试** `tests/stages/test_zero_turning_radius.py`

- `test_can_turn_in_place_threshold`（参数化 0 / 1e-12 / 1e-9 / 1e-6 / 3.0）
- `test_dubins_refuses_zero_radius_with_an_explanatory_message`
- `test_dubins_refusal_precedes_any_nan_or_division_by_zero`
- `test_validator_treats_zero_radius_as_unbounded_curvature`

**修改的既有测试（语义已变，非数值调整）**

- `tests/contracts/test_schema_firewall.py`：`test_ackermann_zero_turn_radius_rejected`
  断言的是「schema 拒绝零半径」，与任务 6 的要求直接冲突，无法只改调用方式保留。
  改为 `test_zero_turn_radius_is_expressible_and_flagged_as_turn_in_place`
  （零半径可构造且 `can_turn_in_place` 为真），并新增
  `test_negative_turn_radius_still_rejected` 保住「负半径仍非法」这条边界。
  原断言的意图（Dubins 类规划器必须拒绝零半径）搬到了
  `tests/stages/test_zero_turning_radius.py`，未丢失。

### 任务 7：docstring 改中文

**改动位置**

- 整改前：docstring 中文 29 / 英文 58。整改后：中文 87 / 英文 0（`src` 与 `tests` 全量）。
- 行内注释同样清零英文：`coverage/stages/route.py` 与 `coverage/stages/swath.py` 两处
  「Compatibility alias」注释改写为真实事实（别名保留是因为 `algorithm_id` 字符串，
  以及 `LongestEdgeSwath` 名不副实——主方向取自最小旋转外接矩形，凹多边形上与「最长边」不一致）。
- 新写的 docstring 只保留三类内容：为什么这样做（含导致该行存在的具体失败）、公式来源、陷阱警告。
  已删掉复述函数名的 Args/Returns 式样板。
- `src/agriautolab/geometry/robust.py` 的 docstring 完整保留了指定事实：
  不要改成 `shapely.unary_union`，500 组随机刚体+相似变换中错 21 次、最大相对误差 40.0%、
  且只在特定旋转角发生。

### 顺带更新

- `README.md`：「本轮已实现」与「工程纪律」两节中因任务 2、5、6 而失准的条目已更正。

## 完成后检查

```
pytest -q                                       -> 286 passed, 30 skipped
grep -rn "unary_union(" src                     -> 无输出
grep -rn "union_all(" src | grep -v grid_size   -> 无输出
grep -rn "NotImplementedError\|TODO\|FIXME" src tests -> 无输出
grep -rn "except.*: *pass" src tests            -> 无输出
缺 quad_segs 的 buffer                           -> 0
```

禁用指标表（`turn_count` / `solution_smoothness` / `mean_clearance` / `normalized_curvature`）未放宽，
`tests/contracts/test_registries.py::test_disabled_metric_registration_fails` 四条参数化全部仍在。
未引入 `shapely`、`pydantic`、`numpy`、`pytest` 以外的依赖。

## 异议

代码已按上述要求实现，以下三点仅作记录。

1. **`CoverageTargets.selected` 的作用范围被我限制了。**
   规格给出的字段列表里有 `selected`，但没说它该驱动哪些量。我只让它决定
   `selected_coverage_ratio()` 返回哪一个比值，没有让它去改 `overlap_ratio`、`missed_ratio`、
   `L_area`、`nonwork_normalized` 的分母——这四项一律用 `original_field` 归一。
   理由：`overlap_ratio` 是 PRIMARY 指标且注册为 `IMPL_INVARIANT`。若它的分母跟着
   `coverage_target` 走，就会复制出任务 2 要消灭的那个缺陷（分母在背后移动），
   并且需要把 `overlap_ratio`、`L_area`、`nonwork_normalized` 一起降级成 `PROTOCOL_BOUND`，
   那是规格没有授权的注册表改动。如果原意是让 `selected` 统管全部面积归一，需要明确指示，
   并接受随之而来的三条指标降级。

2. **`resolve_coverage_targets` 的 `headland=None` 是一个语义分支，不是回退默认值。**
   校验器只拿到 `(problem, robot, path, protocol)`，没有地头产物；不给 `None` 这条路，
   校验器就无法调用唯一的分母解析器。`None` 的含义是「本次运行没有地头阶段，主田即原田」，
   这是事实陈述。但它确实带来一个后果：不传 `headland` 时 `coverage_ratio_main`
   恒等于 `coverage_ratio_field`，作为诊断量没有信息。所以我给 `validate()` 加了
   可选关键字 `headland`，调用方有产物时应当传。

3. **`FieldGeometry` 里还留着第二套主田计算，任务 2 没有覆盖到它。**
   `geometry/kernel.py` 的 `FieldGeometry.from_problem(..., headland_width_m=...)` 会自己算出
   `main_field` 和 `headland` 两个域，与 `resolve_coverage_targets` 平行。
   目前全仓库没有任何调用方给它传非零的 `headland_width_m`，`FieldGeometry.coverable`
   在任务 2 之后也不再被 `src` 引用（校验器已改用 `targets.original_field`）。
   我没有删它：任务 2 的六条子项没有点名 `FieldGeometry`，删字段属于改公开结构。
   同时也要说清楚，强制点确实已经落到位——`coverage_stats` 只收 `CoverageTargets`，
   所以 `FieldGeometry` 算出来的几何再也喂不进覆盖率分母。
   建议后续单独一轮：删掉 `FieldGeometry` 的 `headland_width_m` 参数、`headland` 与 `coverable`
   两个字段，让「主田」在全仓库只有一处定义。

4. **`LongestEdgeSwath` / `SnakeRoute` 这两个别名与任务 4 删掉的 `CoverageRobotSpec` 同源。**
   它们的原注释同样写着「Compatibility alias」，同样不存在需要兼容的历史调用方。
   区别在于 `CoveragePipelineConfig` 的 `algorithm_id` 字符串确实是 `longest_edge_swath`
   和 `snake_route`，删掉别名要连带改配置默认值与流水线白名单。任务 4 只点名了
   `CoverageRobotSpec`，我没有扩大范围，只把注释改成了真实理由。若要一并清理，
   建议把 `algorithm_id` 一起改成 `mbr_direction_swath` / `boustrophedon_route`，
   并注意这会改变 `CoveragePipelineConfig` 的配置哈希。

---

## 2026-08-20 第二轮：分母旁路封口（任务 G-1/G-2）

上一轮收尾报告写了一句错话：「强制点本身是到位的：`coverage_stats` 只收 `CoverageTargets`，
`FieldGeometry` 算出的几何再也喂不进分母。」类型签名换成 `CoverageTargets` 拦住的是
「传错类型」，不是「自己造分母」——而自己造分母正是任务 2 要根除的那件事。
当时的真实状态是：旁路仍然存在，只是没人走。旁路的完整描述见下面第二节。

本轮改动（基线 **286 passed / 30 skipped**，改后 **303 passed / 30 skipped**，新增 17 条，
原有 286 条断言的数值一条未改）：

- `contracts/errors.py` —— 新增 `CoverageDenominatorError`（继承 `AgriAutoLabError`）。
- `metrics/coverage.py` —— `CoverageTargets` 增加模块私有构造令牌 `_RESOLVED` 与
  `headland_width_m`、`frame` 两个新字段，`__post_init__` 依序执行：令牌检查、两个分母
  面积为正、`main_field ⊆ original_field`（相对容差 1e-12）、`selected` 与 `target_kind`
  用 `geometry_hash` 判几何等价、`headland_width_m is None` 时主田与原田哈希必须相等；
  通过后由 `__post_init__` 填充 `provenance: DenominatorProvenance`（init=False）。
  `resolve_coverage_targets` 新增 `headland_width_m` 关键字参数并做产物/宽度配对检查。
  `CoverageStats` 增加 `denominator: DenominatorProvenance`，`coverage_stats` 原样带入。
- `geometry/kernel.py` —— `FieldGeometry.from_problem` 去掉 `headland_width_m` 参数，
  删除 `main_field` / `headland` / `coverable` 三个字段及其计算。全仓库减地头的地方
  只剩 `resolve_coverage_targets` 一处。
- `validation/validator.py` —— `validate()` 新增 `headland_width_m` 关键字参数，
  与 `headland` 产物一起转发给解析器。
- `evidence/record.py` —— `EvidenceRecord` 新增 `denominator` 字段；只要 `metrics` 里
  出现 `coverage_ratio_field` / `coverage_ratio_main` / `overlap_ratio` 之一而没带
  `denominator`，构造直接失败。覆盖率记录从此不可能不带分母证据进账本。
- `tests/conftest.py` —— `targets_from_geometry` 透传 `headland_width_m`。
- `README.md` —— 「本轮已实现」中分母一行改为三层守卫的表述。

新增测试 `tests/stages/test_denominator_guard.py`（14 个函数、17 条收集项）：
`test_direct_construction_without_token_is_rejected`、
`test_resolved_targets_feed_coverage_stats`、
`test_main_field_outside_original_field_is_rejected`、
`test_selected_mismatching_target_kind_is_rejected`（2 例）、
`test_none_width_with_shrunk_main_field_is_rejected`、
`test_no_headland_makes_both_ratios_equal_and_provenance_records_none`、
`test_provenance_is_reproducible_and_isolates_the_headland`、
`test_field_geometry_no_longer_accepts_headland_width`、
`test_nonconvex_main_field_area_is_pinned_as_regression_baseline`、
`test_headland_artifact_without_declared_width_is_rejected`、
`test_declared_width_without_headland_artifact_is_rejected`、
`test_nonpositive_declared_width_is_rejected`、
`test_evidence_record_requires_denominator_for_coverage_metrics`（3 例）、
`test_evidence_record_carries_denominator_into_the_hash_chain`。

因签名变更而修改调用方式（断言数值未动）：`test_coverage_denominator.py` 四处
`resolve_coverage_targets(...)` 补 `headland_width_m=`，两处 `PathValidator().validate(...)`
补 `headland_width_m=18.0`；`conftest.targets_from_geometry` 补透传参数。

---

## 第一节：被改动的既有断言（规则 3 的例外记录）

全局规则第 3 条是「不许动已通过的断言」。以下两次改动是该规则的例外，各自留痕。
**执行约定：今后若再遇到「必须改既有断言」的情况，先把这一节写完再动手改，
不要改完了回头补记。**

### 记录一（第一轮，任务 6 引发，此处补录为可单独引用的正式记录）

- 测试名与位置：`test_ackermann_zero_turn_radius_rejected`，
  `tests/contracts/test_schema_firewall.py`。
- 原断言断的是什么：schema 层拒绝零转弯半径（`min_turning_radius_m` 为 0 时
  `VehicleSpec` 构造必须失败）。
- 为什么「改调用方式不改数值」救不回来：它断言的就是任务 6 推翻的那条规则本身
  （`gt=0` 改 `ge=0`）。任何保留原断言的写法都与新 schema 直接冲突。
- 新断言：改为 `test_zero_turn_radius_is_expressible_and_flagged_as_turn_in_place`
  （零半径可构造且 `can_turn_in_place` 为真）；新增
  `test_negative_turn_radius_still_rejected` 守住「负半径仍非法」这条边界。
- 原意图搬到了哪里：「Dubins 类规划器必须拒绝零半径」由
  `tests/stages/test_zero_turning_radius.py` 的
  `test_dubins_refuses_zero_radius_with_an_explanatory_message` 与
  `test_dubins_refusal_precedes_any_nan_or_division_by_zero` 接管，未丢失。

### 记录二（本轮，任务 G-1.1/G-1.2 引发）

- 测试名与位置：`test_hand_built_targets_cannot_place_main_field_outside_original_field`，
  `tests/stages/test_coverage_denominator.py`。
- 原断言断的是什么：直接构造 `CoverageTargets` 且 `main_field` 越出 `original_field`
  时抛 `ValueError`（当时它是公开 frozen dataclass，唯一防线是 `__post_init__` 的
  语义校验）。
- 为什么救不回来：G-1.1 给构造加了令牌，直接构造在到达语义校验之前就被
  `CoverageDenominatorError` 拦下；异常类型由 `ValueError` 换成 `CoverageDenominatorError`
  是新错误分类法的必然结果，不是放宽。
- 新断言：同一测试改为携带 `_RESOLVED` 令牌越过第一层、专测第二层语义不变量，
  期望 `CoverageDenominatorError`。测试意图（手造分母必须被拒）保留且被加强——
  现在连「合法几何的手造分母」也进不来了。
- 原意图搬到了哪里：没有外移，原地升级；另在 `test_denominator_guard.py` 的
  `test_main_field_outside_original_field_is_rejected`（断言异常消息携带实测越界面积）
  有一份独立覆盖。

---

## 第二节：已封口的分母旁路

**旁路是什么。** 两部分：`FieldGeometry.from_problem(..., headland_width_m=...)`
里的第二套主田计算（用 `buffer(-w, join_style="round", quad_segs=QUAD_SEGS)` 内偏置，
与 `resolve_coverage_targets` 平行），加上一个公开可构造的 `CoverageTargets`——
两者合起来，任何人都能绕开地头阶段产物自造分母。

**为什么「`coverage_stats` 只收 `CoverageTargets`」不构成强制。** 因为它是公开的
frozen dataclass，下面四行就是当时的完整绕过代码，一行不多：

```python
fg = FieldGeometry.from_problem(problem, robot, headland_width_m=6.0)
targets = CoverageTargets(
    original_field=fg.coverable,
    main_field=fg.field.difference(fg.headland),
    selected=...,
    target_kind=CoverageTarget.MAIN_FIELD,
)
coverage_stats(lines, working_width_m=10.0, targets=targets)
```

类型签名挡的是「传错类型」，不是「自己造分母」。

**数据：两套实现在非凸地块上分家，矩形测不出。** 同一地块、同一地头宽度 h=6：

| 地块 | join=round | join=mitre | 相对差 |
|---|---:|---:|---:|
| 100×50 矩形 | 3344.000 | 3344.000 | 0 |
| L 形（100×50 缺 40×30 角） | 2151.771064 | 2144.000000 | 0.361% |

凸多边形的内偏置角点是尖的，join_style 不起作用；一旦地块非凸（反曲顶点被圆角化），
两套实现就开始分家。同一份代码换 `quad_segs` 8→64 也有 8.3e-5 的漂移。
0.4% 量级的分母漂移落在 τ=0.88 的硬门槛附近，与「不同算法之间的差别」同档。
任务 2 的回归表用的全是矩形，测不出这条；Fields2Benchmark 的 350 块真实地块
没有一块是矩形。非凸回归基线已固化为
`test_nonconvex_main_field_area_is_pinned_as_regression_baseline`（2151.7710635850867，rel=1e-9）。

**勘误（已结案）：** 分歧根因在上一轮任务文本：文字写「缺右上 40×30 角」，实际跑的
多边形是 `Polygon([(0,0),(100,0),(100,50),(60,50),(60,20),(0,20)])`——缺口是
**60×30**（塔腿 40×30，面积 3200），不是文字写的 40×30。按文字建立的是缺口 40×30
（面积 3800）的形状，总面积因此差 600 m²。文字错了，数字没错，两组数字各自正确：

| 形状 | 面积 | round(qs=16) | mitre | 绝对差 | 相对差(对 round) | qs8−qs64 绝对 | 相对 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 缺口 60×30（任务书实跑多边形） | 3200 | 1551.771064 | 1544.000000 | 7.771064 | 0.5008% | 0.178489 | 1.15e-4 |
| 缺口 40×30（按文字建立，本仓库基线） | 3800 | 2151.771064 | 2144.000000 | 7.771064 | 0.3611% | 0.178489 | 8.29e-5 |

两个绝对差完全相同（7.771064 与 0.178489）：两个 L 各有一个反曲顶点、圆角半径
同为 6，误差只发生在那一个角上；相对差不同只是分母不同。上一轮「反曲角几何相同」
的判断成立。回归基线维持缺口 40×30 形状与 2151.7710635850867（rel=1e-9）不变——
固化的本来就是本仓库可复现值；缺口 60×30 形状以 `task_notch_l_shape_problem()`
进入测试，由 mitre 拒绝断言间接钉住。任务表中的 0.5033% 是对 mitre 取的分母
（7.771064/1544.000），本表统一对 round 取分母。

**现在的三层各挡什么。**

1. **构造令牌（纪律层）**：`CoverageTargets` 只能由 `resolve_coverage_targets` 构造，
   直接 `CoverageTargets(...)` 抛 `CoverageDenominatorError`。挡的是「顺手构造」——
   那是分母漂移实际发生的方式。**这一层是纪律，不是安全边界。Python 没有真正的私有，
   存心绕过永远绕得过去**；它由第 3 层兜底。
2. **语义不变量**：即使带着令牌构造，也要逐条过——分母面积为正（异常消息带实测值）、
   `main_field ⊆ original_field`（相对容差 1e-12）、`selected` 与 `target_kind`
   按 `geometry_hash` 几何等价、`headland_width_m is None` 时主田与原田哈希相等
   （没有地头，主田即原田，两个覆盖率必然相等）。
3. **分母 provenance（真正起作用的一层）**：`resolve_coverage_targets` 把三个几何的
   `geometry_hash` 与 `target_kind`、`headland_width_m` 记进 `DenominatorProvenance`，
   `coverage_stats` 带进 `CoverageStats`，`EvidenceRecord` 拒收不带它的覆盖率记录。
   产物里记了分母，事后才能复算对账；绕过令牌造出来的分母也会在对账时露出来。
   理由：上一版基线（gate.jsonl）在序列化时把 path 剥掉了，结果没有任何一个指标
   能被独立重算——分母不能重蹈覆辙。

第 1 层在 `CoverageTargets` docstring 里的原话：「这道令牌是纪律，不是安全边界。
Python 没有真正的私有，存心绕过永远绕得过去。它挡的是『顺手构造一个
CoverageTargets』——那是分母漂移实际发生的方式。存心绕过由 G-1.3 的证据链兜底：
产物里记了分母的 hash，事后可以复算对账。」其中「G-1.3」指本节三层里的第 3 层。

## 本轮备注（含异议）

1. **`CoverageTargets` 比任务给出的字段清单多一个 `frame`。** G-1.2 第 3、4 条要求用
   `geometry_hash` 做几何等价比较，而 `geometry_hash(geometry, frame)` 把坐标系一并
   记进哈希——没有 frame，这两条检查写不出来。frame 从 `problem.frame` 取值。
2. **`resolve_coverage_targets` 新增 `headland_width_m` 关键字参数，传了产物就必须申报宽度。**
   根因是 `HeadlandArtifact` 不携带宽度，provenance 里少这一项就没法按地头配置对账。
   长期正解是把宽度写进产物 schema（阶段自描述），那属于改阶段契约，本轮未做，
   先用「产物与宽度必须成对出现」的检查顶住。
3. **上一轮异议 3（`FieldGeometry` 的第二套主田计算）已在本轮 G-1.4 解决**：
   参数与字段全删，`coverable` 一并清除（它就是 `raw_free` 的别名）。上一轮异议 1、2、4
   维持原状。

---

## 2026-08-20 第三轮：地头宽度申报可证伪（任务 H-1～H-3）

基线 303 passed / 30 skipped，改后 **309 passed / 30 skipped**（新增 6 条，原有断言
数值一条未改）。上一轮悬置的数字分歧已结案，见「已封口的分母旁路」一节改写后的勘误段。

### H-1：申报的地头宽度从「无法核对」变成「可证伪」

- `metrics/coverage.py` —— `resolve_coverage_targets` 拿到地头产物时逐 cell 复原原始
  cell（main ∪ 环带），用申报宽度按地头阶段同一套旋钮（round、QUAD_SEGS）重算主田，
  与产物对账；`symmetric_difference` 超过 1e-9×复原 cell 面积即抛
  `CoverageDenominatorError`，消息带实测残差、两侧面积与申报宽度。
- **与任务书的放置位置有一处刻意偏离**：任务书要求检查放在
  `CoverageTargets.__post_init__`、用 `original_field.buffer(-w)` 重算。该公式在有障碍时
  不成立——original_field 已扣障碍，再内缩会在障碍周围双重收窄，诚实路径实测假阳性
  残差 **472.9 m²**（100×50 田、20×10 内部障碍、h=6），会把上一轮专门钉住的正确分母
  （3344−障碍面积）当错误拒绝。逐 cell 复原对账只用产物自身（障碍不进产物），结构上
  无此假阳性，故检查放在 resolve。令牌仍然只有 resolve 持有，守卫覆盖面等价：任何
  合法构造出来的 CoverageTargets 都已通过对账。
- **实测残差量级**（本轮最有信息量的一组数）：
  - 诚实路径：**0.0**——矩形、两种 L 形、旋转 0.3/0.79/1.9 rad 的矩形全部精确为零。
    容差按任务书初始值 1e-9 相对保留，未放松，余量完整。
  - mitre 生成、申报正确标量 6.0：**7.771**（相对 5e-3 档）→ 抓住。
  - quad_segs=8 生成、申报正确标量：**0.1359**（相对 4e-5 档，缺口 60×30 L 上）→ 抓住。
  - h=6 生成、申报 12.0（矩形）：**1368.0** → 抓住。
  - 逐边变宽（左 15 米、其余 6 米）、申报 6.0：**114.0** → 抓住。
- H-1.2 按要求落实：非均匀地头（Required-Width 公式 `H_i = r_rob·(sin(θ−γ_i)+1)+w_rob/2`
  随 swath angle 逐边变化）用标量本就无法描述，申报标量等于声称均匀，错了就该抛；
  未加任何特例分支，理由与长期正解（HeadlandArtifact 自带生成参数：宽度、是否均匀、
  逐边宽度表）写进了 `resolve_coverage_targets` 的检查处注释。
- `DenominatorProvenance.headland_width_m` 改名 **`declared_headland_width_m`**——名字
  带「申报」，防止下游当成实测值。新增 **`headland_ring_hash`**：
  `geometry_hash(original_field − main_field)`，无地头时为 None。这是实际被扣掉的那圈
  几何，调用方无法申报、无法伪造；标量申报可证伪，环带哈希不可申报，两个都留着。
- `__post_init__` 顺带补一条不变量：申报了宽度、original 与 main 之间却没有环带 → 抛。

### H-2：frame 由 problem 推出——确认属实，未改代码

`resolve_coverage_targets` 上一轮实现就只从 `problem.frame` 取值、不接受 frame 参数
（为写 `geometry_hash` 比较增补的 `frame` 字段没有引入自由参数）。按任务书新增测试
`test_frame_comes_from_problem_not_the_caller`：同一 problem 两次 resolve frame 相同；
几何完全相同、坐标系不同（`EPSG:32650` 对默认）时三个哈希全部变化。

### H-3：git init

目录自此为 git 仓库。`.gitignore`（`__pycache__/`、`*.egg-info/`、`.pytest_cache/`、
`build/`、`dist/`、`.venv/`）先于 `git add` 写入；首次提交收录截至本轮的全部源码、
测试与文档。动机照录任务书：软著申请与可复现基线都要求「某个确切版本」可指认。

### 新增测试（`tests/stages/test_denominator_guard.py`）

- `test_declared_width_mismatching_generated_main_field_is_rejected`（h=6 生成、申报
  12.0；断言消息含实测残差 1368.0）
- `test_mitre_generated_main_field_with_correct_scalar_is_rejected`（缺口 60×30 L 形，
  手工 mitre 产物 + 正确标量；断言消息含 7.77——钉住 0.4%~0.5% 口子）
- `test_variable_width_headland_cannot_be_declared_as_scalar`（H-1.2 的行为测试）
- `test_declared_width_with_ringless_main_field_is_rejected`
- `test_headland_ring_hash_tracks_width_not_target_kind`（改 h 变、改 target_kind 不变；
  环带哈希不等于主田/原田哈希，防退化成别名）
- `test_frame_comes_from_problem_not_the_caller`（H-2）

验收第 2 条（申报正确 → 通过且 provenance 记录该值）由上一轮的
`test_resolved_targets_feed_coverage_stats` 覆盖（字段改名后断言
`declared_headland_width_m == 6.0`）。字段改名涉及的四处既有测试更新均为调用方式，
断言数值未动。

### 本轮异议

无。唯一偏离（检查放在 resolve 而非 `__post_init__`）的理由与实测依据见 H-1；
任务书的容差条款（实测过不去再记录再定）在本轮以更强的形式满足——诚实路径残差
为 0，容差余量分毫未动。


---

# Block B（2026-08-21）：偏好条件下的 Pareto 推荐基建

基线：Block A 冻结于 309 passed / 30 skipped（提交 5e1c513）。
Block B 增量后：**399 passed / 30 skipped**。Block A 的 309 条断言数值一条未改；
因 `BenchmarkProtocol` 新增必填字段 `hypervolume_reference`（任务书 §4.3 要求无默认值），
11 处 Block A 测试构造点补了该字段（调用方式，断言数值未动），测试参考点常量放在
`tests/conftest.py:HYPERVOLUME_TEST_REFERENCE`。

## 模块清单与新增测试

| 模块 | 位置 | 新增测试 |
|---|---|---|
| RowStructure | `contracts/rows.py`（`CoverageProblem.row_structure` 可选字段） | `tests/contracts/test_row_structure.py`（5 函数） |
| 离散 π 常量 | `geometry/discrete.py` | `tests/analytic/test_pi_discrete.py`（3 函数） |
| Dubins 六字 | `kinematics/dubins.py` | `tests/analytic/test_dubins_truths.py`（6 函数） |
| BCD 分解 | `algorithms/decomposition/boustrophedon_cells.py` | `tests/stages/test_boustrophedon_cells.py`（4 函数） |
| 地头 ×2 | `algorithms/headland/{no_headland,uniform_headland}.py` | 管线测试覆盖 |
| swath ×5 | `algorithms/swath/{_sweep,fixed_angle,principal_axis,min_width,longest_edge,row_aligned}.py` | `tests/pipeline/test_pipeline.py` 内覆盖 |
| route ×3 | `algorithms/route/{boustrophedon_order,skip_one_order,rural_postman_greedy}.py` | 同上 |
| path ×1 | `algorithms/path/dubins_transit.py`（委托 Block A DubinsPath） | 同上 |
| 算法目录 | `algorithms/catalog.py`（12 卡片） | — |
| 组合管线 | `pipeline/{config,run}.py`（StageMemo 记忆化） | `tests/pipeline/test_pipeline.py`（7 函数） |
| Pareto 前沿 | `pareto/front.py` | `tests/pareto/test_pareto_core.py`（9 函数） |
| 超体积 | `pareto/hypervolume.py`（协议参考点 + 解析上界） | 同上 |
| 标量化 | `pareto/scalarize.py`（加权切比雪夫） | 同上 |
| 特征 | `features/{extract,invariance}.py` | `tests/features/test_features.py`（8 函数） |
| 沙箱 | `agent/sandbox.py` | `tests/agent/test_agent.py`（16 函数） |
| 提议者 | `agent/proposer.py`（LLM 接口 + Mock） | 同上 |
| 四道闸 | `agent/gates.py` | 同上 |
| 对抗复核 | `agent/reviewer.py`（3 维度 + 多数否决） | 同上 |
| 演化账本 | `agent/ledger.py`（哈希链） | 同上 |
| 演化循环 | `agent/evolve.py`（超体积增量适应度） | 同上 |
| 留出集 | `evidence/holdout.py` | `tests/determinism/test_holdout_vault.py`（3 函数） |
| 预注册 | `prereg/AGRIPLAN-PARETO-001.yaml` + `scripts/seal_preregistration.py` | 封存哈希 8d1326de651ed91cce66ed01fc24a7a527064fe9ec7c1cedd83793e7c23f6a80 |
| 指标 ×3 | `metrics/path.py` + 注册表（transit_length/headland_turn_count/row_crossings） | 不变性测试由注册表生成（`_evaluate` 补三支） |

## §9 十六条解析真值的实测值

| # | 断言 | 实测值 |
|---|---|---|
| 1 | Dubins 六字 5000 组随机位姿正演闭合 | 最大误差 **4.944e-13**（< 1e-12；22461 个有效字全命中，六字各至少出现一次） |
| 2 | 反平行 d=4, R=1 | **5.141592653589793** = π+2 精确（对 5.141593 差 < 5e-7） |
| 3 | 同点掉头 d=0, R=1, 航向差 π | **7.330382858376183** = 7π/3；LRL/RLR 并列最优，三段 (π/3, 5π/3, π/3) |
| 4 | 正前方 d=10 | **10.0**（LSL 退化为纯直线） |
| 5 | R=0 交给 Dubins | `KinematicModelError`（长度与字枚举两个入口都拦） |
| 6 | BCD 矩形+单障碍 | **4 个 cell**（异议一：规格写 3，经典 BCD 无非任意规则可给出 3）；面积和 4800.0 精确；菱形障碍 4 cell（朴素切分 6），L 形无障碍 1 cell |
| 7 | 平行于行的线段穿行数 | **0**（实测浮点残差 1.42e-15，真值精确 0） |
| 8 | 垂直于行 L=10, s=2.5 | **4.0** 精确（任意行方向下法向投影/行距同样精确） |
| 9 | 单点前沿超体积 | (A−a)(B−b)(C−c) 精确；实测 (7)(6)(4)=**168.0**（rel 1e-15） |
| 10 | 加被支配点 | 超体积**不变**（逐位相等） |
| 11 | 加非支配点 | **严格增大**（断言 > 基线 + 1e-9） |
| 12 | 非凸前沿 | 等权切比雪夫选中中间点（0.4667 < 0.6667）；**1001×1001 权重网格上加权和从未选中它**（解析上需 w1<0.6w2 且 w2<0.6w1 同时成立，矛盾） |
| 13 | min_width 条数 | L 形幅宽 10：min_width **5** ≤ principal 6 = longest_edge 5 = 角 0° 5 < 角 90° 10 < 斜向 0.7rad 11 |
| 14 | 特征旋转不变性 200 组 | 最大相对误差 **3.226e-13**（< 1e-9） |
| 15 | 沙箱静态扫描 | import/from/open/eval/exec/__import__/双下划线属性 6 类构造**全部拒绝**；白名单外内建（pow）运行时 NameError |
| 16 | MockProposer 演化跑两次 | 账本 JSON **逐位相同**（保留候选身份元组相同） |

交叉验证补充：精确 3D 超体积（x 扫掠 + 2D 压缩）对 200 万点体素蒙特卡洛
46613.9375 vs 46616.4000（相对差 1.0e-4，在 MC 噪声内）。
PI_DISCRETE = 3.1365484905469396（n=64），两条归档事故由它解析复现：
反曲角 round−mitre = w²(1−π_d/4) = 7.771064、障碍环带 = 周长·w + π_d·w² = 472.9157。

目标空间的活体证据（100×50 矩形、行方向 90°、幅宽 10、地头 8）：
min_width：L=379.29 / turns=3 / crossings=140.53；
row_aligned：L=416.40 / turns=8 / crossings=30.40——**crossings 压掉 78%，代价是长度 +10%、掉头 +5 次**，
turns 与 crossings 的冲突（实测秩相关 −0.448）在自家管线上直接可见。

## 异议（代码仍按规格实现，此处留痕）

1. **BCD 的「恰好 3 个 cell」（§3.2/§9-6）无法由经典规则给出，按实测 4 固化。**
   矩形+内部障碍的截面分析：[左, 1 区间] / [障碍带, 2 区间] / [右, 1 区间]，任意两个
   相邻截面连通性都不同，IN=OUT 合并规则下无可合并，4 是正确输出。要得到 3 必须引入
   非对称的任意规则（把某一个通道并入邻 cell，另一侧会围出环形），那不是 BCD。
   防护意图（不合并会暴涨）已用更强形式钉住：菱形障碍下朴素切分 6 → 合并 4，
   面积守恒精确。若下游复核认定 3 另有所指（例如障碍贴边的退化情形），需要规格澄清。
2. **「uniform_headland 必须走 resolve_coverage_targets」按字面不可实现，按意图实现。**
   resolve_coverage_targets 是分母解析器（吃地头产物，不产产物）；算法层的均匀内缩
   委托 Block A 的 ConstantWidthHeadland（全仓库唯一减地头实现，G-1.4 的教训），
   分母一律走 resolve_coverage_targets。两条各就各位。
3. **no_headland 的规范表示是 None，且扫掠域用车体中心可行域（body/2 内缩）。**
   空环带在 PolygonSpec 里不可表示；硬把恒等地头塞进 HeadlandArtifact 会造出
   「申报宽度却没有环带」的自相矛盾产物（上一轮 H-1 的检查会正确拒绝它）。
   中心可行域内缩是运动学包含（车体不出界），不是地头（分母仍是原田）——
   即便如此，无地头 + 前进-only Dubins 的掉头鼓包（约 2R）仍会被 outside_area 拒绝，
   这是物理：掉头空间正是地头存在的理由。此类组合按「失败是数据」记录
   （status=constraint_violation，objectives=None），不伪造数字。
4. **kinematics/dubins.py 与 coverage/stages/path.py 存在约 60 行公式重复。**
   Block A 冻结不允许重构其采样器；新模块按规格成为长度/代价的解析正典
   （带 5000 组闭合测试，含 LRL 陷阱说明）。两份实现各有测试把守。
5. **规格声称「Block A 实现了 preregister() 与 HoldoutVault」——不属实。**
   Block A（309 测试、提交 5e1c513）里两者都不存在（grep 可证）。Block B 补了
   `evidence/holdout.py`（含指定的「这是纪律不是安全」原话）与封存脚本，
   预注册文件本体在 `prereg/`。此差异如实记录，避免下游误以为 Block A 已有该设施。
6. **scipy 与 scikit-learn 白名单但零使用。** ConvexHull 用 shapely 的
   `convex_hull`（已在白名单），Spearman 只出现在预注册文本里（假设检验是
   Block C 的实验，不是本包代码），推荐器本体不在 §8 交付清单中（H3 注明属 Block C）。
   少两个依赖不损任何规格功能。
7. **headland_turn_count / row_crossings 注册为 DIAGNOSTIC 而非 PRIMARY。**
   Block A 有一条测试钉死 PRIMARY 恰为 {overlap_ratio, nonwork_normalized}；
   主向量成员资格由 `pareto.ObjectiveVector` 声明，无需占用注册表 PRIMARY 语义
   （notes 里写明了这层关系）。这是为不动 Block A 断言做的最小选择。
8. **π_discrete 条款与 Dubins 表内数字存在规格内部张力，按表数值实现。**
   「π 相关真值一律用 π_discrete」的适用域是 buffer 圆弧几何（其自带例子全是 buffer）；
   Dubins 弧长是解析量（angle·R），表内 5.141593/7.330383 本身就是 math.pi 值。
   实现按表数值（math.pi），π_discrete 用于 buffer 断言并有测试钉死两种口径的差
   （7.771064 vs 7.725666）。

## 未实现 / 不完整

- **LLMProposer 不发起网络请求（按规格 §6.2）**：接口 + 提示词模板完整，
  模型客户端为注入式 Protocol，未注入时调用报错。真实调用是 Block C。
- **推荐器本体（H3 的被试）不在 Block B 交付清单**：特征、精确前沿、偏好标量化、
  留出集封存都就位，推荐器本身留给 Block C（预注册已注明）。
- 除此之外无未完成项；无桩（自检 grep 0 命中）。

---

# Block C（2026-08-21）：真实数据接入、F2C 对账仪器与语料级产物

定位：Block C 不再把 AgriAutoLab 包装成另一个 Fields2Benchmark；本块只补齐
“真实地块进入契约 → 与 Fields2Cover/F2B 的共有量对账 → 可恢复地跑满语料 →
输出可独立重算的 Parquet/ASlib/SVG 产物”这条证据链。实例空间投影、ISA 与推荐器
没有进入本块。

当前沙箱实测：**414 passed / 32 skipped**。其中 Block B 冻结基线仍为
**399 passed / 30 skipped**；Block C 新增且在本机实际执行的测试为 15 条。
另有 2 个 Block C 测试模块因当前环境没有 `pyarrow` 被 pytest 在收集阶段跳过，
其中包含 5 个需要真实 Parquet 的验收测试。三条脚本自检均实际运行通过：
`import_fields2benchmark.py --self-check`、`validate_f2c_recorded.py --self-check`、
`run_corpus.py --self-check`。

## 模块清单与新增测试

| 模块 | 实现位置 | 主要新增测试 |
|---|---|---|
| 许可证/CRS/WKT 数据接入 | `datasets/fields2benchmark.py` | `tests/block_c/test_data_ingest.py` |
| 行方向实验因子解析 | `contracts/rows.py`、`datasets/rows.py` | `test_protocol_and_run_key.py` + 数据/管线既有测试 |
| 行扫描协议与协议哈希 | `corpus/protocol.py` | `test_row_grid_is_part_of_protocol_hash` |
| F2C 三适配器 | `cross_validation/f2c.py` | `tests/block_c/test_cross_validation.py` |
| 共有指标交叉验证报告 | `cross_validation/report.py` | `test_recorded_csv_self_comparison_has_zero_residual` |
| 代码版本/run key | `corpus/runner.py` | `test_run_key_is_code_version_sensitive`、`test_archive_without_git_is_marked_dirty` |
| checkpoint + Parquet 运行器 | `corpus/runner.py` | `tests/block_c/test_runner_parquet.py`（本机因缺 pyarrow 未执行） |
| 产物哈希链 | `evidence/ledger.py` | `test_license_filter_and_manifest_chain` + runner 测试 |
| ASlib 三目标拆分导出 | `aslib/exporter.py` | `test_aslib_three_scenarios_and_fixed_cv`（本机未执行） |
| 语料 Pareto 聚合/ECDF | `corpus/aggregate.py` | 由 Parquet 产物链消费；本机未做 pyarrow 端到端实跑 |
| Figure 1 手写 SVG | `scripts/make_figure_front.py` | `test_svg_is_xml_and_circle_count_equals_csv_rows`（本机未执行） |
| 真实数据脚本层 | `scripts/import_fields2benchmark.py`、`run_corpus.py`、`validate_f2c_recorded.py` | 三个 `--self-check` 实跑 |

## §7.2 十四条验收的实测值

这里严格区分“代码/测试已实现”与“当前机器实际执行”。缺 `pyarrow` 的项不写成通过。

| # | 断言 | 本机实测 |
|---|---|---|
| 1 | 混合许可 + `allow_non_commercial=False` | 输入 **2**，导出 **1**；`exported_field_ids=('free',)`，`filtered_non_commercial_ids=('nc',)`；manifest 哈希进入 ledger payload |
| 2 | `UNKNOWN` 许可 | 抛 **DatasetLicenseError**，消息含 `mystery` |
| 3 | 100 m × 50 m 已知米制矩形 | 投影保持 `EPSG:28992`；面积 **5000.0 m²**，相对误差 **0.0**（阈值 1e-6） |
| 4 | EPSG:4326 直接进入 `FieldScenario/CoverageProblem` | 抛 **ValueError**，消息命中“单位是度”守卫 |
| 5 | `run_key` 对 code_version 敏感 | commit-A=`033ff456504c5db13973326777c9f8438192b0b5937bc26b6589b3531035a05b`；commit-B=`d1db83676996f87f9135ea8bb06de8b7af7d79b6e2e9d997f2ff4d3952fae3f0`，两者不同 |
| 6 | 脏工作区 | 无 `.git` 的发布树解析为 `commit='NO_GIT_METADATA'`、`dirty=True`；**manifest 写入 dirty=True 的 Parquet 端到端测试已写但本机未执行** |
| 7 | 中断续跑与一次跑完逐位相同 | 测试已实现：比较 `checkpoint.jsonl/runs.parquet/manifest.json/ledger.jsonl` 四文件逐字节相同；**本机未执行（缺 pyarrow）** |
| 8 | `NOT_APPLICABLE` 保留、有效池正确 | 测试已实现，且 `instance_id` 已纳入 vehicle，防止多机具时有效池 > 名义池；**本机未执行（缺 pyarrow）** |
| 9 | ASlib 三 scenario | 导出器实现 `path_length/headland_turns/row_crossings` 三目录及扩展声明；**本机未执行（缺 pyarrow）** |
| 10 | `cv.arff` 折固定 | 折由 instance_id 的 SHA-256 确定；两次逐字节比较测试已写；**本机未执行（缺 pyarrow）** |
| 11 | Recorded CSV 缺列 | 抛 **F2CSchemaError**；实测消息明确 `缺列=('swath_length_sum',)`，同时列出实际/期望顺序 |
| 12 | 人工 Recorded CSV 自比 | `path_length/swath_count/swath_length_sum/main_field_area` 四报告的 `max_abs_diff=max_rel_diff=median_rel_diff=0.0` |
| 13 | 行方向扫描网格进入协议哈希 | offsets=(0,0.1) 时 `4f0e43bef7ffb6fb5252ecffdb8f4b7725f8bb51326b6db61fb514767d62de3f`；改为 (0,0.2) 后 `ab5a60651373e7fd79dce192257e2b0de63ca6cd6604d56f3579534dd41dd3a5`；默认 5 偏移为 `(0, 0.3920685613182424, 0.7841371226364848, 1.1762056839547272, 1.5682742452729697)`（来自 `PI_DISCRETE`） |
| 14 | SVG 可 XML 解析且点数=CSV 行数 | 手写 SVG 与 XML/circle-count 测试已实现；**本机未执行（缺 pyarrow）** |

额外钉住两条没有列进 14 项但直接关系证据可信度的事实：

- 同一 `field_id` 只要几何改变，`field_record_hash` 必变；语料哈希不再只哈 field_id，
  而是哈 `source/license/source_crs/working_crs/geometry_hash` 的记录集合。
- 合成 `wkt.zip` 实测元数据映射：NL → `PDOK/Nationaal-Georegister` + `public-domain`；
  EE → `INSPIRE-EE` + `cc-by-sa-3.0-ee`；LT → `geoportal-lt` + `non-commercial`。

## §3.5 地头定义对账结论

Fields2Benchmark 的 Required Width (RW) 逐边公式为：

`H_i = r_rob * (sin(theta - gamma_i) + 1) + w_rob / 2`。

因此当题目问“自动保证任意最坏方向所需的宽度是多少”时，`sin(.)` 的上界为 1，
参考答案是 **`2*r_rob + w_rob/2`**；不是单独的 `R`。而 Constant Width (CW)
是另一种算法，只有 **CW ↔ 本仓库 `uniform_headland`** 才是共有语义，不能拿 RW
面积与定宽实现硬比。

同时必须说明一个规格与仓库事实不一致之处：当前 Block A/B/C **不存在一个名为
`headland_turn_clearance` 的单一函数**可直接逐行与 F2B RW 参考实现对账。因此本轮完成的
是“论文公式/算法语义级对账 + CW 适配器约束”，不是不存在函数的伪函数级验证。
若后续确实要引入 RW，应新增成明确的新 headland strategy，并独立测试，而不是把
`uniform_headland` 偷偷改成 RW。

## 批判性异议与已知不足

1. **许可证任务书的三值枚举不足以忠实描述真实 Zenodo 元数据。**
   Zenodo 14524735 对荷兰列出 PDOK 与 Nationaal Georegister，并把相关许可写为
   CC0/Public Domain；爱沙尼亚许可链接实际解析为 **CC BY-SA 3.0 EE**；立陶宛明确
   “Non-commercial use only”。因此代码扩展了 `PUBLIC_DOMAIN`、`CC_BY_SA_3_0_EE`
   等值，而没有把 NL/EE 错标成 CC-BY-4.0。`UNKNOWN` 仍保持硬拒绝。

2. **荷兰单个 WKT 的精确来源不可从 F2B 文件名恢复。**
   文件名只有 `nl_` 国家前缀，Zenodo 却列了两个荷兰来源。把每块都写成 `PDOK`
   会制造虚假的 provenance，所以本块记录 `PDOK/Nationaal-Georegister`。若以后能获得
   F2B 作者的逐地块映射表，应替换成真正的记录级来源。

3. **任务书说“名义 13 个配置”，Block B 的实测叙事却是 240×12 配置，且仓库没有
   一份冻结的 13-config protocol 清单。** `algorithms/catalog.py` 登记的是阶段算法卡，
   不是 13 个完整 `PipelineConfig`。Block C 正式脚本因此要求调用方显式提供**恰好 13**
   个配置 JSON 并把 pool hash 入产物，但没有擅自发明“第 13 配置”。后续必须冻结这份
   13-config 文件，否则“名义 13”仍只是文字约束。

4. **验收 #7 与真实 wall-clock timing 存在逻辑张力。**
   若 `planning_s/postprocessing_s/validation_s/feature_costs` 记录真实 `perf_counter`，
   两次独立执行不可能逐位相同。测试使用注入的确定时钟，只验证“恢复机制、排序、缓存键、
   指标、路径与序列化”没有因中断改变；生产默认仍记录真实 wall-clock。不能为了字节相同
   把真实耗时删掉或伪造为常量。

5. **当前交付尚未完成真实 F2B/F2C 数值交叉验证。**
   三适配器都不是桩：RecordedCsv 严格 schema 可运行，Subprocess 真调用可执行文件，
   Python binding 按官方 CW→swath→Snake→Dubins 链路实现。但当前环境没有
   `fields2cover` binding/二进制，用户也没有提供一份真正由 F2B 跑出的 recorded CSV。
   因而“零残差”只发生在人工 CSV 自比，**不能宣称 AgriAutoLab 已与 F2B 在真实地块上
   数值一致**。这是 Block C 交付后优先级最高的实证任务。

6. **当前沙箱没有 `pyarrow`，5 个关键 Parquet 端到端验收未实跑。**
   项目依赖已声明 `pyarrow>=16`，代码没有 CSV 假冒 Parquet 的退路；缺依赖时明确报错。
   本次仍交 ZIP，但 `runs.parquet`、ASlib 与 SVG 的最终链路必须在下游安装 pyarrow 后
   第一时间复核。这里宁可留红，不做伪绿。

7. **真实 350 地块没有在 pytest 中跑，也没有在本沙箱下载。**
   这是规格要求的 hermetic 测试纪律，不是遗漏；真实路径只放 `scripts/`。
   但也意味着当前交付没有给出“350×13×5×2×N”的实际完成时间、失败比例和产物尺寸。
   这些只能在拿到官方 `wkt.zip` 后实测。

8. **CRS 映射依赖任务书/来源知识，不是 WKT 自描述事实。**
   纯 WKT 本身不携带 CRS。当前 NL/EE/LT 分别按 EPSG:28992/3301/3346 接入；若官方
   `wkt.zip` 实际已经重投影或版本发生变化，仅凭文件内容无法检测。正式导入前应对至少
   每国若干地块做坐标量级/已知面积 sanity check，并把版本与数据文件哈希一起归档。

9. **`to_metric_crs` 的经纬度兜底使用局部 UTM，而不是严格“局部等面积/等距”投影。**
   对本项目三国输入，这条兜底正常不会触发，因为它们按协议本身就是米制投影；对未来
   WGS84 数据，UTM 是局部米制、保角投影，不应在论文里误称为严格等面积。若面积误差成为
   研究对象，应换成明确的等面积 CRS/自定义投影契约，而不是扩大当前函数的学术承诺。

10. **PythonBindingAdapter 未在真实 Fields2Cover 安装上做版本级运行验证。**
    代码按当前官方 Python 教程 API 编写，但 F2C Python binding 通常需要本地编译，且
    版本间可能有 API 变化。`available=False` 时 run 会明确抛错，不会返回假结果；下游应
    用目标 F2C commit 做一次 smoke + recorded golden CSV 固化。

11. **Figure 1 默认画“一个实例”的三目标前沿，而不是把 350 个地块原始米制目标混成
    一个伪前沿。** 不同地块的 path_length/turns/crossings 尺度不同，直接混画在数学上
    没有共同 dominance 语义。脚本因此确定性选择一个实例（可显式指定），图上仍标总
    `n_instances/pool_hash/reference/protocol_hash`。若论文要做“语料级 Figure 1”，应先定义
    合法的归一化/ECDF 聚合，而不是偷偷把不同实例原始目标混在一起。

12. **手写 SVG 的 Pareto “连线”只是视觉导引，不是 3D Pareto 曲面的拓扑边。**
    三目标有限点集没有天然的一维前沿排序；当前 polyline 按投影顺序连接，只服务可读性。
    论文图注必须避免把这条线解释为连续 Pareto surface。

13. **ASlib 导出是“ASlib 风格三场景拆分”，尚未用官方/第三方 ASlib parser 做兼容验证。**
    它生成题目要求的五类文件，并在 description 中明确三目标拆分和禁止偷加权；但在本机
    缺 pyarrow 的前提下尚未完成外部 parser round-trip。下游复核应把这当格式验收，而非
    已有的事实。

14. **ZIP 发布树没有 `.git`，所以 code_version 无法凭空给出真实 commit。**
    这种情况下本块用 `source_tree_hash + commit='NO_GIT_METADATA' + dirty=True`，宁可标脏
    也不伪装 clean。正式论文实验应从 git checkout 运行，让 run key 真正携带 commit。

## 本块没有做的事（按范围刻意不做）

- 没有 ISA、实例空间投影、推荐器或 LLM 算法推荐；它们属于 Block D。
- 没有新增覆盖规划算法，也没有重实现 Fields2Cover 算法。
- 没有并行/数据库/Web/仪表盘。
- 没有把 row direction 从几何“猜成观测真值”；它只作为受控实验因子进入协议哈希。

## 静态纪律

交付前再次执行任务书六类扫描：禁止桩/吞异常、直接 `unary_union`、缺 `grid_size` 的
`union_all`、全局 `np.random`、scipy/sklearn import 均为 **0 命中**；所有 `.buffer()`
调用均显式带 `quad_segs`，缺失数 **0**；`compileall src tests scripts` 退出码 **0**。

---

# Block C-R1 整改（2026-08-21，第一轮复核回复）

复核对象：本目录交付（zip SHA-256 `f0b0946d…`）。整改前本机 **418 passed / 1 failed /
30 skipped**（失败为 Windows 子进程兼容，见 R1-5）；整改后 **427 passed / 30 skipped**
（新增 8 条整改验收）。复核侧 419 passed 的全部条目维持通过。

## R1-1 🔴 CV 折按 field_id 分组（复核 C-R1，照单全收）

- `aslib/exporter.py:_fold` 的分组键从 `instance_id` 改为 `field_id`；`cv.arff` 逐实例
  查其 field_id（runs.parquet 自带该列）。`description.txt` 增加声明：
  「folds are grouped by field_id, an extension of the fixed ASlib cv assumption」。
- 实测对账：整改前同一地块的 10 个场景实例散布进 10 折中的 **8 个**；整改后
  同地块 2×2 网格的 4 个实例**全部同折**（`test_all_instances_of_one_field_share_one_fold`）。
  40 块合成地分 10 折仍散布 ≥5 折（分组不退化、无随机盐）。
- **统计单位修正案（不改已封存文件）**：预注册 `AGRIPLAN-PARETO-001.yaml` 已于
  Block B 封存（sha256 `8d1326de…`，本轮验证完好），H2/H3 的独立单位按 **n=350（地块）**
  而非 3500（实例）修正。按预注册纪律，封存文件不回改；本段即为修正案（amendment），
  效力等同于假设检验计划的事先更正，留痕供下游裁决是否重新封存。

## R1-2 🟠 有效池与退化池（复核 C-R2，照单全收并加一档）

`CorpusParetoSummary` 新增：`effective_pool_size_by_instance`（与前沿分布同序）、
`front_size_ratio_distribution`、`n_instances_with_degenerate_pool`、
`n_singleton_fronts_excluded`。singleton 统计只数有效池 ≥ 2 的实例。
**比复核多堵的一档**：有效池 = 0 的实例此前在 `n_instances` 里静默消失，
现在 `n_instances_with_zero_ok_configs` 单列（`test_aggregate_reports_effective_pool_degenerate_and_normalized_hv`
用 A/B/C 三实例逐字段断言）。有效池从 parquet 独立重算，不采信 manifest 单侧声明。

## R1-3 🟠 超体积参考点逐实例化（复核 C-R3，方向照单、方案有替换）

- runner 逐实例调用 Block B 已有的 `pareto.hypervolume.analytic_reference(problem, vehicle)`，
  参考点随行落盘（`ref_path_length/ref_headland_turns/ref_row_crossings/ref_basis`），
  manifest 记录 `hypervolume_reference_scope: "per-instance-analytic"`。
  复核说「逐实例那层没人实现」不确——该函数 2026-08-21 随 Block B 交付
  （pareto/hypervolume.py:133），Block C 的语料链路此前零调用，本轮接上。
  `run_corpus.py` 的 `basis="self-check"` 写死常量已改为显式标注的占位模板，
  不参与任何前沿计算。
- **归一化方案与复核不同**：`hv_normalized = HV / Π(ref_i)`，分母是解析参考点乘积
  （纯协议侧、池稳定）。复核建议的 `HV / Π(ref_i − ideal_i)` 若 ideal 取**观测最优**，
  会随池扩张移动，把 Dolan-Moré 式池依赖从参考点搬进归一化——同一错误的换个住处。
  若坚持 ideal 口径，ideal 必须来自解析下界（如 面积/幅宽 的作业里程下界），不得观测。
  原始米制 HV 保留但 docstring 与本节均标注**不可跨实例聚合**。

## R1-4 🟡 冻结 configs/corpus_13.json（复核 C-R4，照单实施、两处偏离声明）

- 13 个配置逐条带 `reason` 与配置同文件同审计；文件 sha256
  `f451aec287cb17f8d4700d19e314b9faed9d7891c77cfe41f7a843d4bb50f06a` 被
  `test_corpus_13_is_frozen_with_reasons` 钉为回归基线；`run_corpus --configs`
  默认指向该文件，装载器强制「恰好 13 且每个有理由」，manifest 记录 `pool_file_sha256`。
- 组成覆盖五条轴：方向族（min_width/principal/longest_edge/fixed 0/fixed π/2）、
  路线（牛耕/隔行/RPP）、分解（BCD/不分解）、地头强度（8/12 米）、行冲突
  （row_aligned × 三种路线）+ 零地头对照。
- **偏离一（与复核建议相左）**：`no_headland + reeds_shepp` 未纳入——仓库不存在
  Reeds-Shepp 实现（路径阶段只有 dubins_transit），复核 §五刚裁定「不发明第 13 个
  配置」，§六又要求包含一个不存在的算法，二者矛盾。本轮放入的是
  `no_headland + dubins` 对照（预期全 NOT_APPLICABLE，其不可行率本身是被报告的量），
  并把「实现 Reeds-Shepp 后替换该对照」列为开放项。
- **偏离二**：`pool_hash` 保持配置内容哈希（`config_id` 排序后的 content hash），
  另加 `pool_file_sha256` 记录文件字节哈希。复核说「文件内容哈希即 pool_hash」——
  字节哈希对 JSON 键序/空白敏感，语义未变而哈希变更是错误失效；内容哈希才是
  「同一池同一身份」。两个哈希并存，各司其职。
- 可行性实测：13 配置在标准实例上除零地头对照（constraint_violation，符合预期）
  全部 ok（`test_corpus_13_feasibility_smoke`）。

## R1-5 🟢 Windows 子进程修复（替换复核已过时的 C-R6）

- 复核的 C-R6（pyarrow 提为硬依赖）**在交付里已是既成事实**（pyproject 声明
  `pyarrow>=16`、`pyproj>=3.6`；本机 `pip install -e .` 即装上），该项作废。
- 替换为复核漏检的环境缺陷：`SubprocessAdapter` 直接 exec 带 shebang 的脚本，
  Windows CreateProcess 报 WinError 193（复核环境是 POSIX 故未见）。
  现对 python shebang 脚本显式经 `sys.executable` 调用，真二进制不受影响
  （`test_subprocess_adapter_routes_python_shebang_through_interpreter` +
  原 `test_subprocess_and_recorded_return_same_result_type` 在 Windows 转绿）。
  复核报告的「419 passed」应加环境注记：POSIX 全绿、Windows 此前 1 失败。

## R1-6 特征账目勘误与新增盲区（复核 §2.2 的修正，非任务项）

- 复核称「8 个特征只依赖地块多边形，只有 row_angle 与 turning_ratio 随场景变」，
  两个方向都不准，实测（features.extract）：
  同地块换行向/行距，只有 `row_angle_vs_principal` 变（**单机具语料下 9/10 恒定，
  泄漏比复核所述更重**）；换机具幅宽时 `swath_count_at_minwidth` 也变
  （它依赖 working_width，复核把它列入地块恒定集是错的——多机具语料是 7/10 恒定）。
  结论不变：按地块分组是必要条件，账目以本节为准。
- **复核未见的盲区**：10 个特征没有任何一个看得见行距 spacing，而
  row_crossings 与 1/spacing 成比例、最优配置随行距移动——仅差行距的两个实例
  特征完全相同、标签可能不同。这是推荐器的可辨识性缺口（不是泄漏），
  与 C-R1 同批进入异议清单；候选解是给特征集加行距相关量（如
  crossing_density = 主轴跨度/spacing），属 Block D 推荐器前置工作。

## 常设规则（承接复核建议，自本轮起生效）

> 新增任何聚合/统计量之前先问：**这个量在什么作用域内有效？我正在跨越那个
> 作用域吗？** 已记录的同类缺陷：分母（Block A）、前沿大小/超体积参考点（Block B/C
> 规格）、CV 折（Block C）、有效池=0 的实例消失（本轮 R1-2 新增一例）。
> 注意其中两次的根因在规格侧而非实现侧，规则对两侧同等适用。

---

# Block C 冻结后整改（2026-08-21，冻结报告回复：O1/O3）

冻结报告留四个开放项：O1（Reeds-Shepp 断线）、O2（golden CSV）、O3（特征可辨识性）、
O4（350 地块全量）。本轮解决 O1 与 O3（本环境可解的全部）；O2 需外部 F2C 环境、
O4 需真实数据集，维持开放。基线 427 passed / 30 skipped → 整改后 **445 passed / 30 skipped**。

## O3 特征可辨识性（Block D 阻塞项，全量修复）

- 新增两个无量纲特征（`features/extract.py`）：`crossing_density = sqrt(可作业面积)/spacing_m`
  与 `spacing_to_width_ratio = spacing_m/working_width_m`，不变性契约（平移/旋转/缩放不变）
  随 `FEATURE_INVARIANCE` 自动进入 200 组随机变换测试。
- 常设检查 `tests/features/test_feature_identifiability.py`：对场景参数空间的每个自由度
  （行向/行距/幅宽/转弯半径）构造仅在该自由度上不同的实例对，断言特征向量必变且见证特征正确；
  `crossable` 按裁定走**分层**——断言它是 CorpusProtocol 字段并进入协议哈希（翻层必留痕）；
  `body_width` 如实登记为"当前不可见且不影响三维目标"（裕量参数，非场景自由度；
  未来若进入场景扫描必须回来登记）。
- 勘误采纳：单机具语料恒定特征实为 **9/10**（复核原判 8/10 偏轻）；多机具变幅宽时 7/10。
- 新缺陷类入常设清单：**映射欠定**（两个实例特征相同而最优配置不同）——与前五轮的
  "同一事实两处住""跨作用域使用"不同族，登记制检查是它的常设哨兵。

## O1 Reeds-Shepp（按可认证范围实施）

- `kinematics/reeds_shepp.py`：CSC 四族 + CCC 两族的**符号长度**闭式解（与 Dubins 同源公式
  但不做 mod2pi，负长度即倒车段）x {原始, mod2pi, mod2pi-2pi} 三种弧段口径 x
  {恒等, 镜像, 反向, 镜像x反向} 四个目标对称变体。**认证等级如实声明**：可行且
  **不劣于 Dubins**，不保证全局最优（CCCC/CCSC/CCSCC 三族未实现，待与既定规格 §七
  对齐后补——该规格文本本轮仍未获得，此为实现范围的现实边界，不是含糊）。
- 验证电池（tests/analytic/test_reeds_shepp.py，实测数字）：
  - 正演闭合：600 位姿全部候选词，最大误差 **1.63e-13**（全量电池 15 万词同级）；
  - Dubins 支配：800/800 位姿 RS ≤ Dubins（前向-only 是 RS 子集，结构性保证）；
  - 时间反演对称：500/500 位姿 start→goal 与 goal→start 最短值相同（rel 1e-12）；
  - 解析真值：直线 d=10 → **10.0**；同点换向 pi → **pi*R 精确**（前进弧+倒退弧各 pi/2
    的尖点旋转，优于 Dubins 的 7pi/3≈7.330）；反平行 d=4 → 与 Dubins 持平 pi+2=5.1416
    （RS 无增益，如出现更短值反而可疑）；近反平行走廊增益实测 max **5.77 m**。
  - 开发期实测踩坑两处，均已修复并被电池覆盖：(1) mod2pi 误施于直线段（米制长度
    折 2pi 造出不存在的路径，闭合必败，曾静默丢词 884/3000）；(2) 反向变体的映射
    应为"顺序倒转+逐段取负"，只取负不倒序导致方向不对称 4947/5000。
- `ReverseCostModel(reverse_cost_factor>=1)`：cost = 前进长 + factor x 倒车长；
  factor=1 为纯几何长度。供 Block D 注入倒车偏好做敏感性分析。
- 契约与闸门：`PathSegment.reversing: bool = False`（additive）；校验器新增倒车闸——
  含 reversing 段的路径配不可倒车机具 → INFEASIBLE_KINEMATICS
  (`validator_rejected:reverse_without_gear`)；runner 把 KinematicModelError 归为
  NOT_APPLICABLE 而非 CRASH（算法-机具不匹配是"不适用"，不是崩溃）。
- `algorithms/path/reeds_shepp_transit.py` + 管线接线 + 目录卡（maturity=RESEARCH，
  source_reference 注明认证等级）。
- **本轮最有信息量的发现：等长孪生词。** 最短词常有时间反演孪生：先前进的版本向
  swath 端点外鼓包约 2R，先倒车的孪生把掉头收进作业走廊——**两者长度完全相同**
  （时间反演对称的直接推论）。默认字典序 tie-break 恰好选中出界版。转移阶段因此接受
  允许域（pipeline 传入 field-障碍），按代价升序取第一个车体扫掠不越域的词。
  实测：100x50、R=3、body=2、地头 8、行向 0.6 rad——零地头+RS 从
  constraint_violation:outside_area 转 **ok**（L=565.2/turns=4），同几何零地头+Dubins
  仍被正确拒绝；13 配置冒烟全绿。
  开发期采样器事故（已修）：右转弧 y 差分方向抄反，采样弧翻到对称象限
  （row_aligned 对角场景 y 掉至 -1.9、outside_area 13.2 m²）——正是等长孪生词的
  包含性筛查把不一致暴露出来的。
- **corpus_13 修正案**（冻结哈希基线随修正案更新，这正是哈希钉死的意义）：
  新 sha256 `9e898a3468b6a2f9afacbd7f11f2df2646c549ac6edaf3afd25078972803d2a4`。
  变更：槽位 12 换 `row_aligned + reeds_shepp`（复核 §六 原始组成建议的
  "row_aligned 两个路径变体"），槽位 13 换 `no_headland + reeds_shepp`
  （复核断言的"唯一让零地头可行的组合"，本轮实测成立）。被替换的两个槽位
  （row_aligned+RPP、no_headland+Dubins 对照）的理由链保留在本文件历史与
  R1-4 节；RPP 轴仍有槽位 7 覆盖。**RS 配置要求 can_reverse 机具**，
  车辆清单不匹配时运行器记 NOT_APPLICABLE。

## 维持开放（本轮不可解）

- **O2**：golden CSV 需目标 F2C 环境编译与录制；措辞原样保留——
  「AgriAutoLab 已具备严格对账能力 ≠ 已证明与 Fields2Cover 数值一致」。
  重点核对项不变：F2B 的 RMA 是否扣障碍。
- **O4**：350 地块全量未跑；跑前注意 RS 配置的机具清单约束（can_reverse）。

## 复核 §1.1 的可选项按建议记档

紧解析下界（path >= 面积/幅宽、turns >= 1、crossings >= 沿行解析穿行数）可让
归一化超体积铺满 [0,1]、分辨率更高——记为 **Block D 备选**，实施时必须全部解析、
一个观测值不许进。当前 Π(ref_i) 口径（ideal=0）保持不变。

## C-R3：O2 首批真实对账 + 外部工具链记账（2026-08-21）

触发：O2 环境由外部工具（ZCode）在 WSL Ubuntu-22.04 内就绪，本条目补记其冻结后
改动并记录首次真实 golden CSV 对账结果。完整证据链见 `o2_workspace/O2_EVIDENCE.md`
（仓库外工作区，冻结树未动）。

### 冻结后改动补记（此前未记账，行为兼容：12:37 Windows pytest 全绿）

- `src/agriautolab/cross_validation/ours.py`（新增）：我方对账复算，语义假设显式
  声明、三口径（main/field/ring 面积）待裁决不预猜。
- `src/agriautolab/datasets/fields2benchmark.py`：新增 quarantine 机制
  （`load_fields2benchmark_wkt_zip_with_quarantine`，几何不合法地块隔离入 manifest）。
- `scripts/import_fields2benchmark.py`：新增 `--strict` 审计模式（17 行增量）。
- `scripts/build_f2c_requests.py` / `scripts/record_f2c_golden.py`（新增）：O2 请求
  清单构建与录制端。注意：前者直读 jsonl 原始 wkt，**未做米制化**（见下 CRS 勘误），
  录制前必须换用米制语料；后者按 docstring 需 python≥3.11 环境跑 agriautolab 包，
  而 WSL 系统仅 3.10（typing.Self 实测 ImportError）——本轮回放改用仓库外录制壳
  隔离加载冻结 f2c.py，逻辑即冻结 PythonBindingAdapter 本体。

### 环境指纹（录制端）

F2C master@`3613525c`（2025-04-23 后无新提交）× SWIG 4.0.2 × python 3.10.12 ×
OR-Tools 9.9.3963（FetchContent）× GDAL 3.4（系统包）。code_version 一律写
`2.1.0-master@3613525c`。

### 数据集级发现 1：F2B wkt.zip 真实 CRS = WGS84，冻结表元数据漂移

三国原始 WKT 实测均为经纬度（EE 26.5/58.2、NL 5.8/53.0、LT 22.6/56.1），而
`_SOURCE_BY_PREFIX` 声明各国官方门户投影（3301/28992/3346，米制）→ `to_metric_crs`
快速通道原样放行度坐标。合成地块测试不暴露，真实语料首触即炸（F2C 地头吃光全场）。
**勘误修正案（Block D/R4 落地）**：`_SOURCE_BY_PREFIX` 的 source_crs 应改
EPSG:4326（或按国家核实），O4 全量必须用米制语料；本轮未改冻结代码，仅以
`to_metric_crs(source_crs="EPSG:4326")`（其 docstring 声明的经纬度路径）生成
`o2_workspace/corpus_metric/fields.jsonl`（235 块，逐块 UTM working_crs）。

### 数据集级发现 2：RMA 裁决——扣障碍，且障碍周围同样扣 headland 宽度

实测 100×100 含 20×20 孔：F2C `headland.area()`=7200=90²−30²（障碍+双侧 headland
整块扣除），swath 被劈开。我方 UniformHeadland 同语义（含孔地块对账 0.035% 差）。

### 首批真实对账（12/12，四共有量，参数 2/5/2/5/π2）

| metric | median rel | max rel | 判定 |
|---|---|---|---|
| main_field_area | 0.004% | 0.06% | 语义对齐 |
| swath_length_sum | 0.17% | 1.85% | 边界裁剪口径差 |
| swath_count | 0（7/12 精确） | 1.0（±1） | epsilon 离散化差 |
| path_length | 6.3% | 13.8% | **转移段口径系统差，待查** |

path_length 差异主体不在航带（仅 0.2-2%）而在 swath 间转移段：10/12 我方偏低
4.4-12.6%，含孔地块（f2b_004）与 f2b_011 我方偏高 16%/7.1%。候选：蛇形排序约定、
Dubins 弧长密化口径（我方 0.25）、F2C Robot 宽度参与路径几何。**冻结措辞维持成立**
（机制已验证 ≠ 数值一致已证明）；O2 从"不可解"转为"机制跑通 + 首批可解释残差"，
转移口径收敛调查列 Block D/R4。

### O4 前置就绪

米制语料已备（235 块）；跑前仍需：holdout 封存（field 级 30%、seed 20260821）、
RS 配置机具清单约束（can_reverse）。


---

## Block D 前置 · 两道诊断闸（2026-08-21）

基线：任务书写的是 427 passed / 30 skipped，实测仓库已到 **446 passed / 30 skipped**。
按实测的 446 作基线。本轮结束为 **470 passed / 30 skipped**，新增 24 条，
446 条既有断言的数值一条未改。

**本轮只做 G-A 与 G-B，任务 2–10 未开工**（闸门要求报完数字等裁定）。

### G-A：转移段解析真值 —— 结论是**口径差，不是实现 bug**

#### G-A.1 / G-A.2 明细已迁出

解析真值表（14 条）、转移五项分解逐块表与第三组实测（0 次端点对齐等）按 §3.5 去重规则
迁至 `o2_workspace/O2_EVIDENCE.md` §13；本文件只保留判定与结论。
#### G-A.2 转移五项分解（`src/agriautolab/metrics/path.py::transit_breakdown`）

12 块地、387 次掉头，逐块实测：

（逐块表已迁 `O2_EVIDENCE.md` §13。）

- `entry_leg_m` / `exit_leg_m` / `inter_cell_m`：**全 12 块恒为 0.00**，占 transit 的 0.0000%。
  我方路径从第一条作业段起、到最后一条作业段止，不含进出田块的腿。
- `other_m`：全 12 块恒为 0；`turn_total_m` 与 `path_length − swath_length_sum` 的最大偏差 5.116e-13 m。
  分类完备，没有第二个筐。
- 我方 `mean_turn` 中位 **11.1907 m**，是理想 Π-turn 7.2832 的 **1.5365 倍**。

按闸门给的判据（首尾腿为 0 且掉头本身 > 7.283），这一步读作「实现 bug」。
**但判据的前提不成立，所以不能这么读**——补测的第三组数字给出了实际原因：

| 量 | 实测 |
|---|---:|
| 实测掉头长度 / 该姿态对自身的 Dubins 最优 | 中位 **0.999655**（min 0.999560, max 0.999875） |
| 逐姿态 Dubins 最优 中位 | **9.3689 m**（理想 Π-turn 为 7.2832 m） |
| 相邻两段端点的纵向偏移 abs(Δu) 中位 | **2.7122 m**（最大 152.02 m） |
| 相邻两段横向间距 abs(Δn) 中位 | 5.0000 m（= 幅宽 d，94.8% 的掉头精确等于 d） |
| **端点严格对齐（abs(Δu)<1e-6）且间距恰为 d 的掉头** | **387 次里 0 次** |

三条结论：

1. **掉头生成器是最优的**：实测掉头 = 该姿态对自身的 Dubins 最短，比值 0.9997。
   差的那 0.03% 是弧被采成折线的弦差（θ²/24，θ = step/R，step=0.25），
   已由 `test_sampled_turn_converges_to_analytic_as_step_shrinks` 钉住（步长减半、亏损降到四分之一）。
   **没有实现 bug。**
2. **7.283 这个基准在这批地上不适用**：387 次掉头里 0 次满足「端点对齐」这个前提。
   F2B 是真实不规则地块，相邻航带被裁到锯齿边界上，纵向偏移中位 2.71 m。
   在真实姿态对上，可达的最优中位是 9.37 m，不是 7.28 m。
   「比自己模式的最优高 50%」是在跟一个没有任何一次掉头满足的理想值比。
3. **残差的真实来源是路线算法不配对**。同一批地、同一 swath 输入，只换路线算法：

   | 我方路线算法 | transit 中位 `rel_diff_vs_golden` |
   |---|---:|
   | `boustrophedon_order`（相邻） | **−38.11 %** |
   | `skip_one_order`（隔一行） | **+31.04 %** |

   F2C 的 `RP_Snake` 落在两者之间——**F2C 的 `RP_Snake` 非相邻牛耕**。此后实测其访问顺序为
   `[0,2,4,…,20,19,17,…,3,1]`（偶数升序 + 奇数降序回扫，`golden_route.json` 留痕），
   而 `RP_Boustrophedon` 才是 `boustrophedon_order` 的配对方（顺序 `[0,1,2,…]`）。
   本段早先写的「F2C 跑跳行/隔行」按裁定降级为「非相邻牛耕」：bracket 不构成身份证明，
   实测顺序才是。配对后 transit 残差从 −38.11% 塌到 **−0.1403%**，
   全部数字与复跑命令见 `o2_workspace/O2_EVIDENCE.md` §8。

**G-A 判定：口径差（路线阶段），不是实现 bug。修法是任务 3，不是去查 Dubins 代码。**

未闭合的一点，明说：F2C 侧我只有 `path_length` 与 `swath_length_sum` 两个数，
**无法对 F2C 的 transit 做同样的五项分解**。因此「F2C 那边首尾腿是不是 0」目前是未知的，
不能排除 F2C 的 transit 里含有我方没有的进出场腿。要闭合它，录制壳必须同时吐出 F2C 侧的分解
（`OBJ_PathLength` 之外还要拿到分段结构）——这归任务 2。

### G-B：两侧 working CRS —— **一致，投影差异已排除**

实现位置：

- `F2CRequest.working_crs` / `F2CResult.working_crs`（`src/agriautolab/cross_validation/f2c.py`），
  **均无默认值**：忘记声明和确实同投影不能在 CSV 里长得一样。
- `_CSV_COLUMNS` 增列 `working_crs`（第 6 列）；空字符串按 schema 错误拒绝。
- `report.py::_require_same_working_crs`：任一请求两侧不一致 → 抛 `CrsMismatchError`，
  照 `available()=False` 的先例，不返回空报告、不静默比较。
- `CrossValidationReport.working_crs` 记录两侧共同的投影。

实跑（golden 在 WSL/py3.10 重录，ours 在 Windows/py3.12 重录，两份 CSV 独立产生）：

| request_id | ours | golden |
|---|:--|:--|
| f2b_000_ee_field_10 … f2b_004_ee_field_64（5 块） | EPSG:32635 | EPSG:32635 |
| f2b_005_nl_field_1, 006, 008, 009, 010, 011（6 块） | EPSG:32631 | EPSG:32631 |
| f2b_007_nl_field_166 | EPSG:32632 | EPSG:32632 |

**12/12 一致**，比较器未拒绝，`report.working_crs = 'per-field(3 CRS)'`。
逐地块局部 UTM 是既定形态，全语料本就不是同一个投影（235 块分布：
32631×78 / 32635×74 / 32632×60 / 32634×23），因此比较器只要求**同一请求两侧一致**，
不要求全语料同一 CRS。

坐标量程与声明自洽（x≈4.2–6.7e5、y≈5.7–6.5e6 米，UTM 量级，不是度）：

```
f2b_000_ee_field_10    x in [470526.2,470640.5]  y in [6447507.1,6447676.8]   声明 EPSG:32635
f2b_011_nl_field_77    x in [669277.1,669405.4]  y in [5728711.1,5728900.6]   声明 EPSG:32631
```

重录后的残差与重录前**逐位一致**（golden 数值未变，只多了一列）：

| metric | n | median `rel_diff_vs_golden` | max |
|---|---:|---:|---:|
| path_length | 12 | **−5.2953 %** | 13.7783 % |
| swath_length_sum | 12 | +0.1685 % | 1.8495 % |
| swath_count | 12 | 0.0000 % | 4.0000 % |
| main_field_area | 12 | +0.0040 % | 0.0628 % |

**G-B 判定：投影已排除，无需重录 golden 重算残差。G-A 的结论在当前残差上成立。**

注：`path_length` 上一轮记的是 6.3%，本轮记 −5.2953%。差别是分母口径——
上一轮用 `max(abs(a),abs(b))` 做分母且取绝对值，本轮按任务 9 的纪律统一为
`(ours − golden) / golden` 并把方向留在符号里。同一批数据，未重跑。

### 本轮改动位置与新增测试

| 位置 | 改动 |
|---|---|
| `src/agriautolab/contracts/errors.py` | 新增 `TransitDecompositionError` |
| `src/agriautolab/metrics/path.py` | 新增 `TransitBreakdown` + `transit_breakdown()`，`other_m` 非零即抛 |
| `src/agriautolab/pipeline/run.py` | `PipelineResult.transit`；`_cell_of_work_index()` 由 cells+中心线几何定 cell 归属，不进 Swath 契约 |
| `src/agriautolab/cross_validation/f2c.py` | `working_crs` 进 Request/Result/CSV；新增 `CrsMismatchError` |
| `src/agriautolab/cross_validation/report.py` | `_require_same_working_crs()`；`CrossValidationReport.working_crs` |
| `src/agriautolab/cross_validation/ours.py` | `compute_ours_detail` 增 7 个转移分解字段 |
| `scripts/build_f2c_requests.py` | 请求清单带出 `working_crs` |
| `scripts/record_f2c_golden.py`、`scripts/validate_f2c_recorded.py` | 跟随签名变更 |

新增测试（24 条）：

- `tests/analytic/test_transit_analytic_truth.py`（14）：
  `test_pi_turn_closed_form_matches_dubins_solver`（4 参数化）、
  `test_boustrophedon_turn_on_rectangle_hits_the_analytic_minimum`（4 参数化）、
  `test_sampled_turn_converges_to_analytic_as_step_shrinks`、
  `test_bulge_region_lengths_are_pinned`（3 参数化）、
  `test_bulge_and_pi_turn_agree_at_the_d_equals_2r_boundary`、
  `test_pi_turn_formula_refuses_the_bulge_region`
- `tests/analytic/test_transit_breakdown.py`（6）：
  `test_five_parts_sum_to_total_transit_and_leave_no_residue`、
  `test_multi_segment_run_between_two_work_segments_counts_as_one_turn`、
  `test_cross_cell_run_leaves_turn_bucket_and_does_not_inflate_turn_count`、
  `test_path_without_any_work_segment_is_rejected`、
  `test_cell_index_length_must_match_work_segment_count`、
  `test_all_work_path_has_zero_transit`
- `tests/block_c/test_cross_validation.py`（4 新增）：
  `test_comparator_refuses_when_the_two_sides_used_different_working_crs`、
  `test_comparator_records_the_shared_working_crs_on_every_report`、
  `test_per_field_utm_is_allowed_as_long_as_the_two_sides_agree`、
  `test_empty_working_crs_column_is_rejected_by_schema`

### 异议（代码仍按规格实现）

1. **规格给的 `R=3.0/d=8.0 → 9.42477796076938` 与规格自己的式子矛盾。**
   `π·R + d − 2R` 在 R=3/d=8 上是 11.42477796076938，解算器也给这个数；
   9.42477796076938 恰好等于 `π·3`，即漏掉了 `+d−2R` 那一项（d=2R=6 时才成立）。
   我按式子钉 11.4248，并**另加一行 R=3.0/d=6.0**——规格那个数在它成立的参数上照样被钉住。
2. **`rel = 1e-9` 在采样路径上做不到。** 路径阶段把弧采成折线，弦差是 θ²/24（θ=step/R），
   step=0.25 时整体约 5e-4。解析层（`dubins_length`）按 1e-9 钉，管线层按 2e-3 钉，
   另加一条收敛测试证明这个差纯粹是离散化。把 1e-9 硬套在采样路径上只会得到一条必然红的测试。
3. **d/R=1.0 的参考值 6.032484 与实测 6.032529644843455 差 7.6e-6。**
   规格原话是「实测钉住即可」，故按实测钉。
4. **d/R=2.0 的「最优字 = LSL」是并列，不是唯一。** 该处 LSL（π/2+0+π/2）与 LRL 同为 π·R，
   现有实现按 `(长度, 字名)` 字典序破平得到 LRL。真值钉长度，字只断言落在并列集合里。
5. **`TransitBreakdown` 没有 `inter_cell_count` 字段，所以多 cell 情形下无法用
   `headland_turn_count == turn_count + inter_cell_count` 做交叉校验。**
   我按规格给的六字段实现，未加第七个。完备性改由 `other_m == 0` 保证（规格选定的机制），
   单 cell 情形下的一致性有测试覆盖。若要多 cell 的交叉校验，需要授权加这个字段。

### 没做 / 没闭合的（明说）

- **任务 2–10 全部未开工**，按闸门要求停在这里等裁定。
- **F2C 侧的转移五项分解拿不到**（只有两个标量），因此「F2C 的 transit 里有没有进出场腿」未知。
  归任务 2：录制壳需要同时吐出 F2C 侧的分段结构。
- **`scripts/record_f2c_golden.py` 在 WSL py3.10 上仍然跑不了**（`typing.Self`，实测复现）。
  本轮为出 G-B 的数，在仓库外写了一次性录制壳
  `D:\Peak\Desktop\URP\o2_workspace\record_golden_standalone.py`（不 import agriautolab、
  只依赖 fields2cover + shapely，链路与 `PythonBindingAdapter.run` 逐行同义）。
  **它现在是仓库外的一次性脚本，不可复现形态**——正式化归任务 2。
- **`_verify_declared_crs` 未实现**（任务 5）。G-B 只做到「两侧声明一致」，
  没做到「声明与坐标量程自洽」。本轮的量程核对是手工一次性的，不是常设检查。

---

## 留痕：任务 5 使三条既有测试的 fixture 失效（改坐标，不改断言）

规则 3 要求「若出现无法救回的，先把留痕写进 AUDIT_NOTE.md 再动手改」。这里先记。

任务 5 的 `_verify_declared_crs` 用 pyproj 的 `area_of_use` 交叉判定「坐标是否可能属于
所声明的 CRS」。三条既有测试用的是原点附近的合成多边形，却声明了国家投影 CRS：

| 测试 | fixture | 声明 CRS | 该 CRS 的合法范围 |
|---|---|---|---|
| `test_metric_projection_identity_for_known_metric_rectangle` | `(0,0)-(100,50)` | EPSG:28992 | x∈[-2191, 287184]，y∈[305001, 640399] |
| `test_fields2benchmark_country_metadata_is_explicit` | `(0,0)-(10,5)` | 28992 / 3301 / 3346 | 同上三国各自范围 |
| `test_self_intersecting_fields_are_quarantined_not_repaired` | `(0,0)-(10,10)` | EPSG:28992 | 同上 |

**这三个 fixture 本身就是假声明**：RD New 的合法 easting 从 646 起步，(0,0) 不在它的定义域里。
换句话说，新检查不是把对的测试判错了，是把一直存在的假声明暴露了——这正是任务 5 想要的效果。

处理：**只平移 fixture 坐标到各自声明 CRS 的合法范围内，断言一条不动**
（面积仍为 5000.0、license 枚举仍是那三个、自交仍被隔离且 reason 含 Self-intersection）。
- EPSG:28992 -> 原点取 (155000, 463000)
- EPSG:3301  -> 原点取 (600000, 6500000)
- EPSG:3346  -> 原点取 (500000, 6100000)

## 留痕：任务 7 使两条既有 RS 断言失效（改口径，不改事实）

1. `test_all_candidate_words_close_on_random_poses` 断言 `checked > 15000`。
   这个数是**旧实现过量生成候选**的产物：旧版对每族枚举 {raw, mod2pi, mod2pi-2pi}
   三种弧段口径 x 4 变体，靠闭合过滤兜底，600 组位姿产出 >15000 个候选词。
   补齐 CCCC/CCSC/CCSCC 之后，生成的是去重后的 Reeds-Shepp 48 字全集，
   同样 600 组位姿只产出 3841 个候选——**变少是对的**，说明不再重复生成同一条路径。
   处理：把断言从「候选个数 > 15000」改为「命中的不同带符号字形 == 48」——
   钉住的是可数事实而不是实现产物。闭合误差断言（< 1e-9）原样保留。

2. `ReverseCostModel(reverse_cost_factor=2.0)` 单参数改为两参数
   （`reverse_length_multiplier` + `gear_shift_penalty_m`，规格要求）。
   处理：改调用方式；`cost = 前进 + mult x 倒车` 这条算术断言原样保留，
   另加换挡罚项的断言。

---

# Block C 收尾轮（2026-08-21 晚，交接任务 §3.1–§3.6）

基线 **520 passed / 30 skipped**（与交接预告一致，实测为准）；本轮止于
**522 passed / 30 skipped**（新增：塌缩映射 1、环境指纹 1；235 全量另计）。
证据细节一律在 `o2_workspace/O2_EVIDENCE.md`（§8–§13），本节只留判定与指针。

## 探针 30/390 crash 的诊断与归零（交接 §3.4 前置）

交接猜「可能与 HeadlandCell 多部件或 no_headland 组合有关」——**两者都不是**。
实测 `probe_out/runs.parquet`：30 个 crash 全部是同一配置
（`boustrophedon_cells + uniform_headland(8) + min_width`）在 3 块小 EE 地上的
`ValueError: 地头宽度使 main_field 塌缩`。这是「算法给不出该实例的解」，
按 `KinematicModelError → NOT_APPLICABLE` 的既定先例归 `NOT_APPLICABLE`
（`runner.py::_failure_row` 统一失败行构造；只认「塌缩」消息标记，其余 ValueError 仍 CRASH）。
修复后 3 块探针复跑：**crash 0/390**（ok 254 / not_applicable 90 / other 46），
回归测试 `test_headland_collapse_is_not_applicable_not_crash`。
其余 46 个 `other` 是 `validator_rejected:outside_area`（真实几何不可行，是数据）；
60 个 `not_applicable` 是 RS 两槽位配不可倒车机具（见异议 1）。

## 各项落点

| 项 | 落点 | 测试 |
|---|---|---|
| §3.1 环境指纹入证据链 | `RecordedCsvAdapter.env_hash()`（缺失抛异常）+ `EvidenceRecord.f2c_env_hash` | `test_env_f2c_hash_is_required_and_sensitive` |
| §3.2 判据三件套 | `O2_EVIDENCE.md` §11（旧 7.283 判据作废：387 次掉头 0 次端点对齐） | 既有收敛测试维持 |
| §3.2 措辞降级 | 本文件 G-A 段「跑跳行/隔行」→「`RP_Snake` 非相邻牛耕」+ 实测顺序 | — |
| §3.3 账本更正 | `O2_EVIDENCE.md` §10：四数（6.3451/−5.2953/13.7783/15.9801）**由重建的首轮证据逐一复现** | 字段更名已在冻结代码 |
| §3.3 修正案 02 | `prereg/AGRIPLAN-PARETO-001.amendment-02.md`（sha256 f0416911…；封存 yaml 8d1326de… 验证完好未动） | — |
| §3.5 去重 | G-A.1 真值表与逐块明细迁 `O2_EVIDENCE.md` §13，此处留指针 | — |
| 首轮证据重建 | `requests_snake12.json` / `golden_f2c_snake12.csv` / `ours_snake12.csv` / `golden_route_snake12.json` | 可复跑（WSL 重录 + 冻结 ours.py） |

## 任务 7 数字（独立复核）

- **48 个不同带符号字形在随机位姿中全部命中**（本轮 5000 位姿独立复数：字形恰 48）；
- 交接称命中 51/64 个构造，本轮按 name 去重数出 **64/64**——计数口径差异
  （交接的 51 用的构造名未含组合索引），不影响任何结论；要害是 48 字全集命中；
- RS ≤ Dubins **5000/5000**（既有测试钉住）；
- `_selection_candidates` 并入 Dubins 六字（倒车罚 1e9 时纯前进字必须有落点）已在冻结代码。

## 任务 8 许可证（指针）

原文摘录与两处不一致（Zenodo LICENSE=CC BY-SA 4.0 vs 元数据 CC-BY-4.0；
LT 上游限使用、再分发无授权）见 `docs/refs/licenses/fields2benchmark.md`。
解读：分析 n 可达 348、再分发 235——**待人裁定，本轮一切分析按 n=235 执行**
（amendment-02 §3 不预设结论）。

## 235 全量（交接 §3.4）

输入：`run235/corpus`（corpus_hash 996f7960…，235 块米制）、13 配置（corpus_13.json
哈希 9e898a34…）、1 台不可倒车机具。**跑前自动封存**：field 级 30%、seed 20260821，
`holdout_seal.json`（70/235 = 29.79%，seal_hash be973254…）。
探针 390 次/26 s 实测外推全程约 34 分钟起（真实地块方差更大，实际更长）。

## 异议（代码/运行按规格执行，此处留痕）

1. **RS 两槽位在全量实验里零贡献**：`vehicles.json` 是 1 台**不可倒车**机具，
   corpus_13 的 12/13 号配置（reeds_shepp_transit）在全部 235 块上恒为
   NOT_APPLICABLE（探针 60/390 实证），有效池 13 → 11。这不是 bug（NOT_APPLICABLE
   是数据），但 O1 的全部意义（非嵌套算法轴、零地头解锁）在本实验设计下不会被测到。
   改机具清单 = 改协议身份 = 实验设计变更，需授权；本轮按现行清单跑，论文须声明有效池 11。
2. **首轮 golden 灭失是流程缺陷**：配对版覆盖 `golden_f2c.csv` 时未按 route_algorithm
   分名存档，导致账本更正的四个数一度只存在于转述里。本轮重建补档（O2_EVIDENCE §10），
   并立规矩：**golden 文件名必须带 route_algorithm 后缀**（本轮已按此命名 snake12 文件）。
3. **交接对 crash 的预判（多部件/no_headland）方向错了**，实测是大地头塌缩——
   记录在此不是为了指责，是因为「先查 parquet 再猜原因」这个顺序值得固化。
4. **`other`（outside_area）在探针占 11.8%**：真实几何不可行是数据，但论文报
   有效池分布时必须把它与 NOT_APPLICABLE 分开列，否则「有效池 11」会被读成「13 里挂了 2 个」。

## 未完成 / 不完整（明说）

- **235 全量在跑**（后台），跑完后本节补 manifest 验证、runstatus 分布与三目标前沿图；
  数字未出之前，本节不写任何结论性表述。
- **F2C 侧转移五项分解仍未闭合**（golden 只有标量，拿不到 F2C 的分段结构）——任务 2 遗留，
  需要录制壳吐出分段。
- **amendment-02 的 n=348 分支待人裁定**，裁定前一切分析 n=235。

## 首轮 235 全量暴露的 BCD 三个真实缺陷与修复（2026-08-21 深夜）

首轮全量（run235/out）30 550 行里 crash 1 852（6.1%），全部集中在
`boustrophedon_cells`，逐层解剖出**三个**真实缺陷——探针 3 块地一个都没炸出来，
合成测试也没盖住，只有真实语料全量才暴露。这是「真实数据首触即炸」的第三次实证
（前两次：度坐标 CRS、许可证枚举）。

| # | 缺陷 | 实测表现 | 根因 | 修复 |
|---|---|---|---|---|
| 1 | 组端点建箱在透镜形地块上失效 | ee_field_6 面积剩 2.6%（16 457→432）| 组两端点 y 界外推整组，两端薄中间厚的通道被切小 | 逐段建箱：段内边界线性，段两端点截面即精确界 |
| 2 | 网格吸附伪影转回原坐标后自交 | ee_field_77 cell 非法 | robust_union 吸附留 ~1e-13 近退化顶点，旋转放大成尖刺 | 归一化只作用于**无洞的箱并集**并强制面积对账（rel 1e-9 超差即抛）；在原 frame 与 free 求交，洞天然保留 |
| 3 | 洞尖藏于段内时通道重叠 | nl_field_191476 两两重叠 1 357 m² 恰为洞面积 | 端点列通道配置与中点不一致时整带 y 灌进通道 0 | 配置不一致的列跳过；BCD 划分语义由逐 cell 差集互斥化兜底 |

另：绕原点旋转改绕质心（UTM ~5e6 坐标下绕原点的舍入本身就够制造自交）。

**修复后全语料实测**（235/235，`test_real_field_defects_regression_synthetic` 钉住）：
fail=0；面积守恒中位 9.5e-11、最差 2.99e-08；cells 两两重叠全语料合计 1.6e-06 m²。
既有 BCD 测试 4 条全绿（矩形 4 cell / 菱形 4 / L 形 1 / 确定性），523 passed。

首轮 run235/out 的 1 852 个 crash 行随修复作废（checkpoint 的 run_key 含源码哈希，
代码一变全部失效），已用修复后代码重启全量（run235/out_v2，跑前 holdout 对账通过）。

## 第二轮 v2 暴露的三个新缺陷与修复（2026-08-22 凌晨）

v2（BCD 修复后）30 550 行 crash 降至 1 002，解剖出三个新缺陷，全部真实数据首触型：

| # | 缺陷 | 实测 | 根因 | 修复 |
|---|---|---|---|---|
| 4 | 地头申报对账的旧口径噪声地板太高 | nl_field_15/w=12 残差 4.9 m²（rel 4.5e-04），382 行被误杀 | buffer→difference→union→buffer 弦弧往返在 UTM 大坐标的量化损耗，与 mitre 信号（rel ~3e-03）只差一个量级 | **口径重设计（不是放宽容差）**：去掉往返环，改两条无损耗断言——(a) `main == cell.buffer(-W)`（与生成侧同一调用，错宽度/mitre/qs8 全被干净抓住）；(b) `main ∩ ring ≈ 0`（划分互斥）。容差 2e-03 相对，距噪声地板（5e-04）与最小语义信号（mitre ~3e-03）各留 4 倍以上间隔 |
| 5 | Dubins 直线段在 UTM 坐标尺度下零长化 | 610/30550，全部在 RPP 排序的连接段，`path-XXXXX: 点数不足` | 坐标 ~5e6 处双精度步长 ~1e-9 m，低于它的绝对长度起终点舍入为同一点；Block A 的 1e-14 归一化阈值量的是弧度不是米 | `_sample_straight` 坐标尺度阈值内原地保持位姿；产物里 2 点重合段直接过滤（不携带几何） |
| 6 | BCD 细窄 cell 的塌缩是合法不适用 | ee_field_107 等 | 分解后的 cell 宽度 < 2×地头宽 | 无需修：runner 已按塌缩→NOT_APPLICABLE 映射（失败是数据，类别要对） |

修复后 523 passed / 30 skipped；三个原 crash 场地直跑验证：nl_field_15→ok、
ee_field_114(RPP)→constraint_violation（数据）、ee_field_10(BCD)→ok。
已启动第三次全量（run235/out_v3）。

**过程异议（留痕）**：缺陷 4 的第一反应是放宽容差（实测残差写进文档再定），
但实测噪声 4.5e-04 与 mitre 信号 3e-03 间隔不足一个量级，放宽容差会把要抓的东西放跑。
重设计口径消掉往返损耗后，容差才有干净的两侧间隔——「先量噪声地板再定容差」
这条纪律救了一次错误的放宽。

## v3 结果与第三个缺陷轮（2026-08-22 早）

v3（对账口径重设计 + 零长段守卫后）30 550 行：**crash 降至 10/30550（0.03%）**，
ok 14 876 / not_applicable 6 350 / other 9 314。剩余 10 个 crash 全部同一根因：

| # | 缺陷 | 实测 | 根因 | 修复 |
|---|---|---|---|---|
| 7 | 颈缩地块的中心可行域内缩成 MultiPolygon | nl_field_7（no_headland 配置）| 主体内缩 body/2 后地块被颈缩劈成两片，`polygon_to_spec` 拒绝非单 Polygon | `_center_free_polygons` 按片返回（语义同 BCD 多部件 cell：每片都是合法扫掠域），修复后直跑验证 nl_field_7 → constraint_violation（合法数据：该地块零地头 Dubins 确实出界） |

有效池中位 10（名义 13）：RS 两槽位恒 NOT_APPLICABLE（不可倒车机具）+ 大地头配置
在细窄地块上塌缩/出界。已启动 v4 终跑（run_key 含源码哈希，代码一变全量重算）。

**三轮全量的 crash 轨迹**：1 852 → 1 002 → 10 → （v4 目标 0）。每一轮都是上一轮
修复暴露下一层缺陷——真实数据的首触效应在 235 块上比 3 块探针强两个数量级。

## v4 终跑结果（2026-08-22）

**crash 0/30550。** 30 550 行：ok 14 876（48.7%）/ not_applicable 6 360 / other 9 314。
有效池中位 10（名义 13）、min 1、max 11，有 ok 的实例 1 900/2 350（450 个实例有效池 0：
全部配置在该行场景下不可行——40 块地在所有行方向上均无法产出合法路径，是数据不是缺陷）。

**两配置 ok 率恒 0**（异议 1 的实测坐实）：corpus_13 的两个 RS 槽位
（`row_aligned+reeds_shepp` 与 `no_headland+min_width+reeds_shepp`）配不可倒车机具，
30 550 行全部 NOT_APPLICABLE。有效池实际由 11 个配置贡献。

四轮 crash 轨迹：**1 852 → 1 002 → 10 → 0**。产物：runs.parquet / manifest.json /
ledger.jsonl / holdout_seal.json / figure_front.svg+csv（前沿图实例
ee_field_103:principal_axis:0.0:0.75，10 点 3 在前沿）。全部产物在 `o2_workspace/run235/out_v4/`。

H1 前置观察（不作检验结论，检验按预注册在 Block D 出）：前沿中位大小等数字
待分析阶段从 runs.parquet 正式聚合，此处只交付跑完的语料与前沿图。

## 留痕：Python 下限 3.11→3.10 的两处冻结代码改动（WSL 迁移轮，改动前记录）

**动机**：Ubuntu 22.04 LTS 系统 Python 为 3.10.12，Fields2Cover 的 SWIG binding
绑在系统解释器上；下限降到 3.10 让 F2C 与本项目同解释器可用（升 3.11+ 则
binding 不可见，这不是"顺手升级"能改的）。>=3.10 是下限不是钉死——3.11/3.12
照跑，Windows 侧不受影响。

| 文件 | 改动 | 性质 |
|---|---|---|
| `src/agriautolab/contracts/geometry.py` | `from typing import Self` → `from typing_extensions import Self` | 注解来源替换，零行为变化；typing_extensions 是 pydantic 硬依赖，任何可安装环境必然在场（全局规则第 4 条本轮已将其列入白名单） |
| `pyproject.toml` | `requires-python = ">=3.11"` → `">=3.10"` | 放宽下限，不改任何已过断言 |

按 §2.1 纪律：不靠 grep 找 3.11 语法，改完后在 Ubuntu 3.10 上**跑全套测试**，
跑不过的才是要改的。

## 留痕：corpus_13 冻结哈希重钉（换行规范化，内容零变化）

**命中规则：分类完备性/单一真相源的前置——字节级冻结必须平台无关。**
Windows 文本模式曾把 corpus_13.json 写成 CRLF，冻结哈希 `9e898a34…` 钉的是
CRLF 字节；git blob 实为 LF，Linux 检出后哈希必不匹配（WSL 3.10 首跑实测复现，
523 passed + 1 failed 即此）。修复：`.gitattributes` 强制 LF + 文件重写为 LF +
哈希重钉 `502b1e90…`。JSON 内容逐字节（除换行）零变化。**今后所有字节级
冻结一律以 LF 为准**，CRLF 检查进安装自校验。
