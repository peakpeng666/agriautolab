# 更新日志

格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循语义化版本。每轮的完整过程批判见 [AUDIT_NOTE.md](AUDIT_NOTE.md)。

## [未发布]

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
