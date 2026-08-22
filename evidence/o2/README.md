# O2 对账证据（小体积子集入仓）

本目录是 `o2_workspace/`（仓库外工作区）的**小体积证据快照**，随代码一起版本化，
让仓库自含「与 Fields2Cover 数值一致性」的全部对账依据。大体积产物
（235 全量 `runs.parquet` 2.2 GB、探针输出、米制语料）不入 git，留在本地工作区，
复现路径见 `scripts/` 与 `AUDIT_NOTE.md`。

| 文件 | 内容 |
|---|---|
| `O2_EVIDENCE.md` | 对账证据主文档（环境指纹、G-A/G-B 诊断闸、路线配对证明、首轮证据重建、判据三件套） |
| `requests_metric.json` / `requests_snake12.json` / `requests.json` | 请求清单：14 块配对版 / 首轮 12 块重建版 / 首轮度坐标事故版（仅存档） |
| `golden_f2c.csv` / `golden_f2c_snake12.csv` | F2C 录制的 golden（配对版 / 首轮 snake 重建版），13 列锁定 schema |
| `ours.csv` / `ours_snake12.csv` | 我方复算（同 schema） |
| `golden_route.json` / `golden_route_snake12.json` | F2C 吐出的 swath 访问顺序（路线身份证明） |
| `route_scan.json` | 路线扫描留痕（boustrophedon −0.14% / skip_one +55.7%） |
| `env_f2c.json` | 录制端环境指纹（F2C commit 3613525c / SWIG 4.0.2 / py3.10.12），其内容哈希进证据链 |
| `reconcile.py` | 对账报告脚本（配对残差、含障碍子集、身份复现、路线扫描），可复跑 |

复跑对账：golden 侧需在装有 F2C binding 的环境（`scripts/f2c_recorder/`）；
我方侧 `python reconcile.py`（Windows 或 WSL 均可，import agriautolab）。

冻结措辞原样保留：**「AgriAutoLab 已具备严格对账能力 ≠ 已证明与 Fields2Cover 数值一致」**
——数值一致的正式表述以 `O2_EVIDENCE.md` §8 的配对残差表为准。
