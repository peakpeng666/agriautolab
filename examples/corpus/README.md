# 正式语料运行的最小协议样例

三份文件是 v7 终语料实际使用的协议（哈希与 `evidence/v7/manifest.json`
对账一致），可直接作为新实验的起点：

```bash
python scripts/run_corpus.py \
  --corpus ~/agriautolab-data/corpus \
  --configs configs/corpus_13.json \
  --vehicles examples/corpus/vehicles.json \
  --benchmark-protocol examples/corpus/benchmark_protocol.json \
  --corpus-protocol examples/corpus/corpus_protocol.json \
  --output ~/agriautolab-data/runs/experiment_001
```

| 文件 | 内容 | 修改时的身份影响 |
|---|---|---|
| `vehicles.json` | 双机具（R=2.0 只前进 / R=2.5 可倒车） | `vehicles_hash` 变 = `corpus_protocol.json` 必须同步改 |
| `benchmark_protocol.json` | 覆盖门槛、解析超体积参考点模板、倒车代价 | `benchmark_protocol_hash` 变 = 同上 |
| `corpus_protocol.json` | 5 行角 × 2 行距 × CV 折数 + 两协议哈希锚定 | 本身即实验身份的一部分 |

注意：参考点模板不是论文比较尺度——正式比较用逐实例解析参考点
（runner 自动写入 `ref_*` 列）；行向扫描的偏移是实验处理变量
（见预注册修正案 04/05 的 H2 设计）。
