# evidence/：证据与实验记录索引

历史与过程批判的唯一住所是仓库根的 [AUDIT_NOTE.md](../AUDIT_NOTE.md)
（只追加，不回改）；里程碑叙事在 [CHANGELOG.md](../CHANGELOG.md)。
本目录只放**可复算的证据件**，按证据集组织：

| 证据集 | 内容 | 入口 |
|---|---|---|
| `env_geometry.json` | 几何引擎契约：已验证的 GEOS/shapely 组合（换引擎=换真值） | `tests/test_geometry_engine.py` 消费 |
| `o2/` | 与 Fields2Cover 的数值对账：金标 CSV、请求清单、环境指纹、对账脚本 | `../docs` 与 AUDIT_NOTE O2 段 |
| `v7/` | 终语料溯源件：manifest 副本、留出集封存、D1 CV 折表、状态交叉表、大件 sha256、ledger 链复算记录 | `evidence/v7/README.md` |
| `block_d/` | 选择/统计分析证据链；genesis 为 D1 field-grouped CV 折身份，后续分析只追加不重建 | `evidence/block_d/README.md` |

大件（runs.parquet / checkpoint.jsonl.gz / ledger.jsonl，GB 级）**不进仓库**，
留在数据目录，凭 `v7/provenance.json` 的 sha256 随时对账——复核者需要的
是小件，不是字节搬运。

新增证据的规则：先问「它能不能被复算」——不能的是叙事，归 AUDIT_NOTE；
能的才进本目录，并在这里登记一行。
