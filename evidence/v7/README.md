# v7 终跑溯源件（Block D 前最终语料）

大件（GB 级）留在数据目录 `~/agriautolab-data/out_v7/`，凭 sha256 对账
（见 provenance.json）；本目录只进复核者与审稿人需要的小件。

| 文件 | 内容 |
|---|---|
| `manifest.json` | 运行清单原样副本：code_version `ed1bccb`（clean）、四桶计数（other=0/crash=0）、有效池逐实例、前沿中位 3.0、协议哈希 |
| `holdout_seal.json` | 留出集封存（field 级 30%，seed 20260821，跑前密封） |
| `status_crosstab.json` / `.md` | config × 机具 × derived_status 交叉表 + 有效池完整分布（scripts/status_crosstab.py 生成） |
| `provenance.json` | 大件 sha256（runs.parquet / checkpoint.jsonl.gz / ledger.jsonl）+ ledger 哈希链逐条复算验证（61 101 条全过） |

已知口径提示：manifest 的 `effective_pool_size_by_instance` 只含 ≥1 ok 的
3 776 实例；全实例口径（含 924 个零 ok）的分布与双口径中位见 status_crosstab。
状态语义：`derived_status`（validator 事实优先）与 `runstatus`（运行时归并）
的分歧 = 2 020 行 not_applicable→outside_area，定义见
src/agriautolab/corpus/derived_status.py 与 AUDIT_NOTE。
