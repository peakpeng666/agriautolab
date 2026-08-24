# Block D 分析证据

本目录记录 **AGRIPLAN-PARETO-001 的分析阶段证据链**。它与 `evidence/v7/`
的语料生成证据严格分开：v7 已冻结，不因后续统计/模型开发而回写历史。

## 链上身份

`ledger.jsonl` 当前八条依次为：

1. **index=0 / D1 `cv_assignment_sealed`**：绑定 field→fold 明细、D1 spec、
   v7 corpus/manifest、holdout seal、seed=20260822、10 folds、165 training fields；
2. **index=1 / D2 `pool_census`**：绑定 4,700 实例三层池普查，N=13、
   A(v0)=11、A(v1)=13；
3. **index=2 / D3 `selection_protocol_v1`**：在任何模型 CV 结果之前冻结
   12 个 wire-feature 的顺序、22 点偏好网格、三层基线、zero-OK 处理边界、
   ExtraTrees 固定参数和 D1 CV identity；
4. **index=3 / D4 `selection_cv_result`**：绑定训练侧 CV 报告、模型二进制、
   模型元数据与 D3 协议四项哈希；
5. **index=4 / D5 `h1_confirmatory_result`**：绑定 `h1_result.json`、分析代码
   bundle、预注册/修正案 bundle、v7 runs 与冻结池身份；
6. **index=5 / D6 `h2_confirmatory_result`**：绑定 H2 结果与代码/协议/数据身份，
   并以前序 H1 结果逐田对账后追加；
7. **index=6 / D7 `h3_confirmatory_result`**：原始 H3 封存。主结论为 H3 未获支持：
   `mean_D=0.058717510697747215`，单侧符号翻转置换
   `p=0.8208179182081792`，预注册失效判据 1 触发；
8. **index=7 / D7.1 `h3_postseal_corrigendum`**：对 D7 合并后发现的执行纪律/
   实现问题做**只追加修正**。原 `h3_result.json` 与 ledger index 0..6 不回写。

D1 的完整 field universe 来自 v7 manifest 的逐田 `licenses` 表，而不是
`effective_pool_size_by_instance`。后者是结果派生摘要：首轮干净运行发现
12 个 holdout field 不在该映射中；若拿它当全集，会把困难/零有效池田从 CV
身份中静默删掉。该错误路径已有回归测试禁止复发。

D2 的普查入口强制每个 instance 的 nominal 配置矩阵完整且唯一；
截断/重复运行行、从 `instance_id` 猜 `field_id`、重复追加 ledger 都会响亮失败。

## D3 协议封存

`selection_protocol_v1.json` 是**结果前协议**，不是结果报告。当前身份：

- preference grid: `PREFERENCE_GRID_V1`, 22 points；
- protocol hash: `be5d2e6106529fc751fecfe047b6da079c5534073d99249366f36a657e838e8c`；
- model: one multi-output `ExtraTreesRegressor` per config，seed 20260822，
  `n_jobs=1`，无超参数搜索；
- training scope: 只消费 D1 的 165 training fields。

O_x 为空时，Amendment 05 没有给出可唯一执行的 confirmatory regret oracle。
因此协议把这类实例标为 `regret_undefined` 并保留计数；H3 最终 70 块留出田中
58 块可分析、12 块 zero-OK 单列。

## D5–D7 正式结果

- **H1**：235 田中 193 田可分析，42 田全零 ok（17.872%）；主口径田级前沿
  中位 3.0（IQR 2.0–3.0）；Wilcoxon `greater`
  原始 p=`2.3921204051674115e-30`，Holm 调整
  `7.176361215502235e-30`，支持 H1。
- **H2**：190 田有至少 3 个定义偏移档，`n3/n4/n5=1/0/189`；田内 Spearman
  rho 中位 `0.35355339059327373`；Pratt 零处理的 Wilcoxon `greater`
  原始 p=`1.2024559145397036e-12`，Holm 调整
  `2.4049118290794072e-12`，支持 H2。
- **H3**：70 块留出田中 58 块可分析、12 块 zero-OK；推荐器平均悔值
  `0.3436621245152262`，random_applicable 精确期望
  `0.569889227634958`，`mean_D=0.058717510697747215`；
  10,000 次单侧 sign-flip permutation `p=0.8208179182081792`。
  失效判据 1 触发，H3 **不支持**。两块 probe field 均属于 zero-OK，
  70/68 双轨的 58 块可分析集合与主统计量相同。

Study-001 的 Holm 家族终表因此为 **H1 支持 / H2 支持 / H3 不支持**。

## D7.1 post-seal corrigendum

D7 合并后代码复核发现三项问题，机器可读原件见
[`h3_corrigendum.json`](h3_corrigendum.json)：

1. **P1 / protocol deviation**：D7 当时的协议身份校验位于 `analyze_h3` 之后。
    contemporaneous audit 已记录两次执行在“评估完成后、写盘前”被身份守门
   中止，因此“严格一次性执行”这一说法不成立。没有证据表明两次中止产生的
   H3 结果被输出、写盘、写入 ledger 或用于调整统计口径。
2. **P1 / model identity gap**：旧实现未在 `joblib.load` 前把模型与 metadata
   的 SHA-256 硬绑定到 D4 index=3。封存的 H3 结果所记录的两项 SHA 与 D4
   实际完全一致，所以这是守门缺陷，不是已发现的错模型消费。
3. **P2 / descriptive median**：旧 `_track()` 在偶数 n=58 时取 upper median，
   不符合常规定义。该字段只属描述统计；H3 的冻结主统计量是 `mean_D`，
   因此主检验、p 值、失效判据与 Holm 结论均不变。因为原封存没有保存逐田
   D 值，本项目**不重新消费 holdout**只为补算这个次要描述量；原
   `median_D=-0.10510520090865455` 明确标记为无效历史值。

修复后的 H3 执行路径采用 fail-closed 顺序：

```text
ledger 连续性/既有 H3 检查
→ 预注册与修正案字节身份
→ D1 CV/holdout 文件字节
→ D2 runs/configs/vehicles 字节
→ D3 selection protocol 字节
→ D6 前序数据/协议身份
→ D4 model + metadata exact SHA
→ 解析 metadata 并核协议/cv/pool
→ joblib.load
→ 模型对象身份自检
→ 才允许读取 runs 中的 target fields
```

一旦 ledger 已含 `h3_confirmatory_result`，`--fields holdout` 会在读取其他
H3 输入前立即拒绝；后续只能验证既有证据，不能把已知结果重新包装成新的
confirmatory run。

## 复算与验证入口

D1：

```bash
python scripts/prepare_cv_folds.py \
  --manifest evidence/v7/manifest.json \
  --holdout evidence/v7/holdout_seal.json \
  --output /tmp/cv_assignment.json
```

D3-D4 真实训练侧 CV（需要数据机上的 v7 `runs.parquet`）：

```bash
python scripts/train_selection.py \
  --runs ~/agriautolab-data/out_v7/runs.parquet \
  --configs configs/corpus_13.json \
  --vehicles examples/corpus/vehicles.json \
  --cv evidence/v7/cv_assignment.json \
  --protocol evidence/block_d/selection_protocol_v1.json \
  --output-dir ~/agriautolab-data/d4 \
  --ledger evidence/block_d/ledger.jsonl
```

D5/D6 的历史复算入口保持不变：

```bash
python scripts/analyze_h1.py --runs ~/agriautolab-data/out_v7/runs.parquet
python scripts/analyze_h2.py --runs ~/agriautolab-data/out_v7/runs.parquet
```

**D7 不再提供重跑式复算。** `tests/confirmatory/` 现在验证原 H3 字节、ledger
index=6、D7.1 corrigendum index=7、preflight fail-closed 顺序与统计实现，
从而把“历史不可改”和“以后不能再犯”同时写进 CI。
