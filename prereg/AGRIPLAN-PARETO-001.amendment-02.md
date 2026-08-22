# AGRIPLAN-PARETO-001 预注册修正案 02：统计单位与许可可用样本量

日期：2026-08-21。承接修正案 01（AUDIT_NOTE R1-1 段，统计单位 3500 实例 → 350 地块）。

## 1. 被封存文件与不可回改性

原封存文件 `prereg/AGRIPLAN-PARETO-001.yaml`
（sha256 `8d1326de651ed91cce66ed01fc24a7a527064fe9ec7c1cedd83793e7c23f6a80`）
**不回改、不重封**。预注册的价值在改动留痕；本文件是第二份正式修正案。

## 2. 统计单位再修正

实测语料经几何隔离与许可过滤后，自由许可（CC0 / CC BY-SA 3.0 EE）地块为 **235 块**：

- 350 输入 − 2 块几何隔离（nl_field_22 / nl_field_32，EuroCrops 数字化自交伪影，
  剔除未修复、manifest 留痕）− 113 块立陶宛 NON_COMMERCIAL 过滤 = **235**。
- H1 / H2 / H3 的一切显著性检验，独立单位按 **n = 235（地块）** 计，
  自由度、功效分析、置信区间同步以 235 为基数。

## 3. 许可解读对样本量的影响（待人裁定，本修正案不预设结论）

`docs/refs/licenses/fields2benchmark.md` 复核发现：Zenodo 记录的 `LICENSE` 文件
为 CC BY-SA 4.0 全文（无 NonCommercial 条款），而元数据字段写 CC-BY-4.0（两者不一致）；
立陶宛上游原文限制的是**使用**（"Tik nekomerciniam naudojimui / Non-commercial use only" +
"Autoriaus teisės / Copyright"），再分发**没有任何授权**。

两种读法的后果：

| 读法 | 分析可用 n | 公开再分发 n |
|---|---:|---:|
| 保守（现行默认）：LT 仅限非商业使用且不授再分发 | **235** | **235** |
| 若裁定 Zenodo 的 CC BY-SA 4.0 LICENSE 文件覆盖全数据集 | 348（350−2 隔离） | 仍 235（LT 再分发无授权） |

**本修正案不预设结论**：待人裁定。裁定采纳第二种读法前，一切分析按 n = 235 执行；
若裁定采纳，n = 348 的分析构成新的预处理决定，须在结果章节先于任何检验声明。

## 4. 折与留出集的对应

留出集已按 field 级 30%（seed 20260821）于全量运行前封存
（`run235/out/holdout_seal.json`，seal_hash 见文件；70/235 = 29.79%）。
折分组（C-R1）与留出分组同键（field_id），二者不得一个按实例一个按地块。
