# Block D 分析证据

本目录记录 **AGRIPLAN-PARETO-001 的分析阶段证据链**。它与 `evidence/v7/`
的语料生成证据严格分开：v7 已冻结，不因后续统计/模型开发而回写历史。

## 链上身份

`ledger.jsonl` 当前六条依次为：

1. **index=0 / D1 `cv_assignment_sealed`**：绑定 field→fold 明细、D1 spec、
   v7 corpus/manifest、holdout seal、seed=20260822、10 folds、165 training fields；
2. **index=1 / D2 `pool_census`**：绑定 4,700 实例三层池普查，N=13、
   A(v0)=11、A(v1)=13；
3. **index=2 / D3 `selection_protocol_v1`**：在任何模型 CV 结果之前冻结
   12 个 wire-feature 的顺序、22 点偏好网格、三层基线、zero-OK 处理边界、
   ExtraTrees 固定参数和 D1 CV identity；
4. **index=3 / D4 `selection_cv_result`**：绑定训练侧 CV 报告、308 MB 模型、
   模型元数据与 D3 协议四项哈希；
5. **index=4 / D5 `h1_confirmatory_result`**：绑定 `h1_result.json`、分析代码
   bundle、预注册/修正案 bundle、v7 runs 与冻结池身份；
6. **index=5 / D6 `h2_confirmatory_result`**：同样绑定 H2 结果与代码/协议/
   数据身份，并以前序 H1 结果逐田对账后追加。

D1 的完整 field universe 来自 v7 manifest 的逐田 `licenses` 表，而不是
`effective_pool_size_by_instance`。后者是结果派生摘要：首轮干净运行发现
12 个 holdout field 不在该映射中；若拿它当全集，会把困难/零有效池田从 CV
身份中静默删掉。该错误路径已有回归测试禁止复发。

D2 的普查入口现在还强制每个 instance 的 nominal 配置矩阵完整且唯一；
截断/重复运行行、从 `instance_id` 猜 `field_id`、重复追加 ledger 都会响亮失败。

## D3 协议封存

`selection_protocol_v1.json` 是**结果前协议**，不是结果报告。当前身份：

- preference grid: `PREFERENCE_GRID_V1`, 22 points；
- protocol hash: `be5d2e6106529fc751fecfe047b6da079c5534073d99249366f36a657e838e8c`；
- model: one multi-output `ExtraTreesRegressor` per config，seed 20260822，
  `n_jobs=1`，无超参数搜索；
- training scope: 只消费 D1 的 165 training fields；holdout 在 D7/H3 前禁止读取。

O_x 为空时，Amendment 05 没有给出可唯一执行的 confirmatory regret oracle。
因此协议明确把这类实例标为 `regret_undefined` 并保留计数；D3/D4 不以静默
剔除或临时罚值替代预注册。该边界在 D7 前必须被审计解决。

## 复算入口

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

## D5/D6 正式结果

- **H1**：235 田中 193 田可分析，42 田全零 ok（17.872%）；主口径田级前沿
  中位 3.0（IQR 2.0–3.0），零实例记前沿 0 的敏感性中位仍为 3.0；
  Wilcoxon `greater` 原始 p=`2.3921204051674115e-30`。
- **H2**：190 田有至少 3 个定义偏移档，`n3/n4/n5=1/0/189`；田内 Spearman
  rho 中位 `0.35355339059327373`，常数响应田明确记 rho=0；Pratt 零处理的
  Wilcoxon `greater` 原始 p=`1.2024559145397036e-12`。全 5 档敏感性
  n=189、中位相同、p=`1.968291923037038e-12`。

两项的 Holm 精确调整仍等待 H3 p 值排序；当前只报告保守的 `3p` 上界，
两项均已小于族 alpha=0.01。H1/H2 都是冻结全语料上的田级前沿/处理检验，
没有装载推荐器、CV 折表或 holdout 成员清单；**D7/H3 仍未执行**。

```bash
python scripts/analyze_h1.py --runs ~/agriautolab-data/out_v7/runs.parquet
python scripts/analyze_h2.py --runs ~/agriautolab-data/out_v7/runs.parquet
```

训练脚本只允许沿 index=2 后追加 `selection_cv_result`（index=3），D5/D6
也分别只允许占用 index=4/5，且全部重放幂等。`tests/selection/` 与
`tests/confirmatory/` 会重算结构、输入身份与哈希链，禁止修改既有证据历史。
