# O2 证据链：Fields2Cover golden CSV 交叉验证（首批真实对账）

日期：2026-08-21。冻结措辞原样保留：
**「AgriAutoLab 已具备严格对账能力 ≠ 已证明与 Fields2Cover 数值一致」**
本文件记录首次真实对账的全部证据与两个数据集级发现。

## 1. 环境指纹（录制端，WSL Ubuntu-22.04）

| 项 | 值 |
|---|---|
| Fields2Cover | master@`3613525c241538fa9fd9df3e1209ae8184627958`（2025-04-23 后 master 无新提交），2.1.0 |
| Python binding | SWIG 4.0.2 → python 3.10.12（`/usr/lib/python3/dist-packages/fields2cover.py` + `_fields2cover_python.so`） |
| OR-Tools | 9.9.3963（F2C FetchContent 拉取，`/usr/local/lib/cmake/ortools`） |
| GDAL | libgdal.so.30（Ubuntu 22.04 系统包） |
| 录制壳 | `/home/peak/f2c_golden_wrapper.py`，sha256 `26936682194eea3397e01bb1c3968ba0cbc0c4ccd7f8a9d99693a59880a82fcd` |
| 适配器 | **冻结 `cross_validation/f2c.py`（与 r2.zip 逐字节一致，da639e92…），隔离加载绕过包 `__init__`（agriautolab requires-python≥3.11，WSL 系统仅 3.10）** |

冒烟（独立几何手算核对）：100×100 空地 → L=1823.81 / n=18 / sum=1620 / area=8100，
与手算（18 条 90m 航带、主田 90²）一致。

## 2. 语料与请求清单

- 导出：`import_fields2benchmark.py`（ZCode 增 --strict 隔离审计版）
  `--no-allow-non-commercial`：**350 输入 → 235 导出**（EE+NL 自由许可），
  LT 113 块 NON_COMMERCIAL 过滤，2 块几何隔离（nl_field_22/nl_field_32 自交）。
  corpus_hash=`39c587769dce3306e10c32c2aaf37804952c99a5f320b431ed969b35a0fbbbd2`。
- 请求：`build_f2c_requests.py`（ZCode，确定性均匀抽样 12 块、EE/NL 跨国）
  参数写死进 requests.json：robot 2.0 / working 5.0 / radius 2.0 / headland 5.0 / angle π/2。

## 3. 关键发现 1：F2B wkt.zip 的真实 CRS 是 WGS84（元数据漂移）

- 实测三国原始 WKT 均为**经纬度**：EE 26.50°E/58.17°N、NL 5.84°E/53.03°N、
  LT 22.59°E/56.10°N；zip 内无任何元数据文件。
- 冻结 `_SOURCE_BY_PREFIX` 表声明的是各国官方门户投影 CRS（EE:3301、NL:28992、
  LT:3346，均为米制投影）→ 冻结 `to_metric_crs` 判定"已是米制"快速通过 →
  **度坐标原样流出且挂 3301 标签**。
- 后果：以米为单位的参数（headland 5.0）作用于度坐标 → F2C 地头吃光全场
  （`Geometry does not contain point 0`）。Block C 测试全用合成地块故未暴露；
  这是真实语料首次接触才炸出的问题。
- 修复（**未改冻结代码**）：请求构建前用冻结 `to_metric_crs(geometry,
  source_crs="EPSG:4326")` 走其 docstring 早已声明的经纬度路径（按地块质心选局部
  UTM）。UTM 分布：32635×74、32634×23（EE）、32631×78、32632×60（NL）。
  目标 CRS 逐地块进入 working_crs，进 provenance。

## 4. 关键发现 2：RMA 裁决——F2C 扣障碍，且障碍周围同样扣 headland 宽度

100×100 空地含 20×20 孔（40,40)-(60,60)、headland 5.0：
- F2C `headland.area()` = **7200 = 90² − 30²**（不是 8100 不扣、也不是 7700=90²−20²）
- 即：障碍按外边界对待，**障碍 + 双侧 headland 宽度（20+2×5=30）整块扣除**；
  swath 被障碍劈开（18→24 条）。
- 我方 `UniformHeadland` 同语义（f2b_004 含孔地块对账 0.035% 差），裁决成立。

## 5. 对账结果（12/12 全部跑通，四共有量）

| metric | median rel diff | max rel diff | 结论 |
|---|---|---|---|
| main_field_area | **0.004%** | 0.06% | 语义对齐（含障碍地块 0.035%） |
| swath_length_sum | **0.17%** | 1.85%（f2b_006 离群） | 我方系统性 +0.2~0.4%，边界裁剪口径差异 |
| swath_count | **0（中位）** | 1.0（5 块 ±1） | 边界 epsilon 离散化差，正常 |
| path_length | 6.3% | 13.8%（f2b_004） | **转移段口径系统差**，见下 |

path_length 结构：航带和仅差 0.2-2%，差异主体在 **swath 间转移段**。
10/12 我方偏低（-4.4%~-12.6%），2/12 我方偏高（f2b_004 含孔 +16%、f2b_011 +7.1%）。
候选原因（待 Block D/R4 调查，按先验排序）：
1. 蛇形排序约定不同（F2C `RP_Snake` vs 我方 `BoustrophedonOrder` 的起终点/换向规则）；
2. Dubins 弧长口径（F2C `PP_DubinsCurves` 自身步长 vs 我方 `DubinsTransit(0.25)` 弦密化）；
3. F2C Robot 宽度参与路径几何，我方仅用 min_turning_radius。

## 6. 纪律核查记录

- 12:37 Windows pytest 全绿（`lastfailed={}`，445 冻结测试不受影响）；
- 冻结文件与 r2.zip 逐字节比对：`f2c.py`/`__init__.py`/`report.py`/`corpus_13.json`/
  `AUDIT_NOTE.md` **SAME**；预注册封存 sha256 `8d1326de…` 校验通过；
- 冻结后新增（ZCode，已补 C-R3 记账）：`cross_validation/ours.py`、
  `scripts/build_f2c_requests.py`、`scripts/record_f2c_golden.py`、
  `datasets/fields2benchmark.py` 的 quarantine 函数与 `import_fields2benchmark.py` 的
  --strict 审计模式；
- 本工作区（`o2_workspace/`）在仓库外，不触碰冻结树。

## 7. 产物清单

| 文件 | 说明 |
|---|---|
| `requests_metric.json` | 12 请求，米制 WKT（UTM），参数写死 |
| `golden_f2c.csv` | F2C 2.1.0 录制（12 行，五列 schema） |
| `ours.csv` | 我方冻结 ours.py 复算（12 行，五列 schema） |
| `env_f2c.json` | 录制端环境指纹 |
| `corpus_metric/fields.jsonl` | 235 块米制语料（**O4 前置产物**，含逐块 working_crs） |
| `build_metric_corpus.py` / `record_ours.py` | 驱动脚本（仓库外） |

---

# 第二批：G-A/G-B 诊断闸 + 路线配对证明 + 首轮证据重建（2026-08-21 晚）

## 8. G-A 升级为证明：路线阶段配对后残差塌缩

`RP_Snake` 的实测访问顺序是 `[0,2,4,…,20,19,17,…,3,1]`（偶数升序 + 奇数降序回扫）；
`RP_Boustrophedon` 才是我方 `boustrophedon_order` 的配对方（顺序 `[0,1,2,…]`）。
**配对判据从"推断"升为"证明"的两条证据：**

1. **身份复现**：用 F2C 吐出的访问顺序驱动我方 path 阶段，逐块复现其 transit，
   中位 `rel_diff_vs_golden = −0.1240%`（14 块，下表）。
2. **路线扫描**：同一 swath 输入只换我方路线，`boustrophedon_order` −0.1403%、
   `skip_one_order` +55.7382%——配对方落进零点，非配对方远离，方向性成立。

**配对后残差（14 块分层抽样：含障碍 6 / 多内环 3，`ReconciliationSamplingSpec` 进协议哈希）：**

| metric | 中位 rel | max\|rel\| |
|---|---:|---:|
| `transit_turn_total_m` | **−0.1403%** | 25.1845% |
| `path_length` | **+0.1182%** | 11.4779% |
| `swath_length_sum` | +0.1505% | 3.1064% |
| `main_field_area` | +0.0081% | 0.4485% |
| `transit_entry_leg_m` / `exit_leg_m` / `inter_cell_m` | **0.0000%（两侧恒为 0）** | 0 |

含障碍子集单列（RMA 裁决的可验形式）：main_field_area +0.0766%（含障碍 6 块）
vs +0.0061%（无障碍 8 块）——障碍语义在含孔地块上被数据复验，不是被口头采纳。

复跑：`cd o2_workspace && python reconcile.py`；留痕 `route_scan.json`、`golden_route.json`。

## 9. G-B：两侧 working_crs 逐请求一致，投影差异已排除

14 块逐请求核对 `working_crs`：per-field 4 CRS（UTM 32631/32632/32634/32635）两侧一致；
不一致即 `CrsMismatchError` 拒绝比较（`_verify_declared_crs` + pyproj `area_of_use` 交叉判定，
`tests/block_c/test_crs_declaration.py`）。

## 10. 首轮证据重建（golden 灭失 → 重录 → 四数逐一复现）

首轮 12 块（RP_Snake 未配对）的 `golden_f2c.csv` 在配对版覆盖时未留档——证据保全缺口，
本轮补救：按 AUDIT_NOTE G-A.2 表的 field_id + 首轮参数重建请求清单
（`requests_snake12.json`），WSL 重录 golden（`golden_f2c_snake12.csv`，
同 F2C commit `3613525c`），我方按当时实际的 boustrophedon 复算（`ours_snake12.csv`）。
**账本更正的四个数字逐一复现**：

| 量 | 交接所称 | 本轮重算 |
|---|---:|---:|
| \|Δ\|/max 中位（旧判据的"6.3%"） | 6.3451% | **+6.3451%** ✓ |
| Δ/max 中位（有符号） | −5.2953% | **−5.2953%** ✓ |
| \|Δ\|/max max（旧报） | 13.7783% | **+13.7783%** ✓ |
| \|Δ\|/golden max | 15.9801% | **+15.9801%** ✓ |

结论：6.3% → −5.2953% 的变化 **100% 来自符号约定**（绝对值中位 vs 有符号中位），
分母没变过；`|Δ|/max` 与 `|Δ|/golden` 在中位上恒等（中位落在 golden>ours 的 10/12 块里），
只在 ours>golden 的 2 块分家，后果落在 max（13.7783% vs 15.9801%）。
`compare_results` 字段已更名 `max_abs_rel_diff_vs_golden` / `median_rel_diff_vs_golden` /
`Disagreement.rel_diff_vs_golden`，分母恒取 golden。

## 11. 闸门判据（放行条件 3 的替换文本，旧判据作废）

**作废**：「`mean_turn` 应接近 7.283」。7.283 = π·R + d − 2R 只在矩形、端点对齐、
相邻牛耕下成立；387 次掉头实测 **0 次端点对齐**（纵向偏移中位 2.71 m），
该判据在真实地块上永远红，红得毫无信息量。

**替换为三件套**：
1. **掉头对自身最优**：实测掉头 / 该姿态 Dubins 最优 ≈ 1.0（实测中位 0.999655；
   弦差 θ²/24 已由步长收敛测试钉死）；
2. **路线阶段两侧配对同名**：`route_algorithm` 显式进请求清单，
   `RouteAlgorithmMismatchError` 拒绝不同名比较；
3. **`other_m == 0`**：转移五项分解分类完备，没有第二个筐（恒等式
   `headland_turn_count == turn_count + inter_cell_count` 有测试）。

## 12. 环境指纹入证据链（本轮 §3.1）

`env_f2c.json` 的内容哈希进入 `RecordedCsvAdapter.env_hash()`（缺失抛异常不静默），
`EvidenceRecord.f2c_env_hash` 字段可携带；改动任一字段哈希必变
（`tests/block_c/test_cross_validation.py::test_env_f2c_hash_is_required_and_sensitive`）。
当前环境：F2C `HEAD@3613525c`（2025-04-23）、SWIG 4.0.2、python 3.10.12、
OR-Tools 9.9.3963（F2C FetchContent）。


## 13. 首批 G-A 明细（自 AUDIT_NOTE 迁入，§3.5 去重）

#### G-A.1 解析真值（`tests/analytic/test_transit_analytic_truth.py`，14 条）

相邻牛耕、d ≥ 2R 的最短前进掉头 = `π·R + d − 2R`（LSL 退化的 Π 形：
两个 π/2 弧各横移 R，中间直行 d−2R）。解算器逐位对上：

| R | d | 解析式 | dubins_length | 最优字 |
|---:|---:|---:|---:|:--|
| 2.0 | 5.0 | 7.283185307179586 | 7.283185307179587 | LSL |
| 3.0 | 8.0 | **11.42477796076938** | 11.42477796076938 | LSL |
| 1.5 | 4.0 | 5.712388980384690 | 5.71238898038469 | LSL |
| 3.0 | 6.0 | 9.42477796076938 | 9.42477796076938 | LRL（与 LSL 并列） |

d < 2R 鼓包区（length/R，R=1）：

| d/R | 实测最优字 | length/R |
|---:|:--|---:|
| 0.0 | LRL（与 RLR 并列） | 7.330382858376183 |
| 1.0 | RLR | **6.032529644843455** |
| 2.0 | LRL（与 LSL 并列） | 3.141592653589793 |

π 取用：Dubins 弧长是解析量（angle·R），与 buffer 圆角化无关，
按 `geometry/discrete.py` 第 11 行已写明的既定约定用 `math.pi`，不用 `PI_DISCRETE`。

| request_id | n_swath | entry | turn_total | n_turn | inter_cell | exit | other | mean_turn | /7.283 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| f2b_000_ee_field_10 | 21 | 0.00 | 274.86 | 20 | 0.00 | 0.00 | 0.00 | 13.743 | 1.887 |
| f2b_001_ee_field_146 | 27 | 0.00 | 317.00 | 26 | 0.00 | 0.00 | 0.00 | 12.192 | 1.674 |
| f2b_002_ee_field_183 | 32 | 0.00 | 274.46 | 31 | 0.00 | 0.00 | 0.00 | 8.854 | 1.216 |
| f2b_003_ee_field_24 | 27 | 0.00 | 284.77 | 26 | 0.00 | 0.00 | 0.00 | 10.953 | 1.504 |
| f2b_004_ee_field_64 | 26 | 0.00 | 815.78 | 25 | 0.00 | 0.00 | 0.00 | 32.631 | 4.480 |
| f2b_005_nl_field_1 | 64 | 0.00 | 686.42 | 63 | 0.00 | 0.00 | 0.00 | 10.896 | 1.496 |
| f2b_006_nl_field_13 | 24 | 0.00 | 252.23 | 23 | 0.00 | 0.00 | 0.00 | 10.966 | 1.506 |
| f2b_007_nl_field_166 | 45 | 0.00 | 496.12 | 44 | 0.00 | 0.00 | 0.00 | 11.275 | 1.548 |
| f2b_008_nl_field_25 | 44 | 0.00 | 374.81 | 43 | 0.00 | 0.00 | 0.00 | 8.716 | 1.197 |
| f2b_009_nl_field_44 | 37 | 0.00 | 399.82 | 36 | 0.00 | 0.00 | 0.00 | 11.106 | 1.525 |
| f2b_010_nl_field_59131 | 25 | 0.00 | 576.18 | 24 | 0.00 | 0.00 | 0.00 | 24.007 | 3.296 |
| f2b_011_nl_field_77 | 27 | 0.00 | 826.17 | 26 | 0.00 | 0.00 | 0.00 | 31.776 | 4.363 |

