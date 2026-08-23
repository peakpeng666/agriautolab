# Block D 分析证据

本目录记录 **AGRIPLAN-PARETO-001 的分析阶段证据链**。它与 `evidence/v7/`
的语料生成证据严格分开：v7 已冻结，不因后续统计/模型开发而回写历史。

## Genesis：D1 field-grouped CV

`ledger.jsonl` 的 index=0 为 `cv_assignment_sealed`，绑定：

- `evidence/v7/cv_assignment.json` 的文件 SHA-256；
- field→fold 明细的 `assignment_hash`；
- D1 完整执行规范的 `spec_hash`；
- v7 manifest 文件 SHA-256 与 `corpus_hash`；
- holdout 文件 SHA-256 与语义 `seal_hash`；
- seed=20260822、10 folds、165 training fields。

折表的完整 field universe 来自 v7 manifest 的逐田 `licenses` 表，而不是
`effective_pool_size_by_instance`。后者是结果派生摘要：D1 首轮干净运行实测发现
12 个 holdout field 不在该映射中；若拿它当全集，会把困难/零有效池田从 CV 身份
中静默删掉。该错误路径已有回归测试禁止复发。

## 复算

```bash
python scripts/prepare_cv_folds.py \
  --manifest evidence/v7/manifest.json \
  --holdout evidence/v7/holdout_seal.json \
  --output /tmp/cv_assignment.json
```

`tests/selection/test_cv.py` 会从冻结 v7 文件重新生成折表并要求与仓库中的
`cv_assignment.json` 完全一致，同时逐条验证本目录的 artifact hash chain。

后续 D2、H1/H2、推荐器 CV 与 H3 的分析产物必须沿本链追加，不得重建 genesis。
