# AgriAutoLab

[![CI](https://github.com/peakpeng666/agriautolab/actions/workflows/ci.yml/badge.svg)](https://github.com/peakpeng666/agriautolab/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](pyproject.toml)
<!-- DOI badge placeholder: replace after Zenodo archival release -->
[![DOI](https://img.shields.io/badge/DOI-10.5281%2Fzenodo.XXXXXXX-lightgrey)](https://doi.org/10.5281/zenodo.XXXXXXX)

面向农业覆盖路径规划（Coverage Path Planning, CPP）的研究级基准、分析与算法设计实验框架。
农业主线以 13 个冻结 pipeline configuration 在 235 块真实农田上完成 61,100 次全量运行
（零崩溃、零未分类失败），量化「路程 / 地头掉头 / 作物行横穿等价量」三目标权衡，并在
冻结证据纪律下研究偏好条件算法选择。

TSP/CVRP 作为方法学验证层进入正式主包：用强类型问题契约、constructive heuristic 协议、
独立 evaluator 与 TSPLIB/CVRPLIB 标准格式加载器验证后续算法设计方法的公共边界。
人工基线、解析真值与 TSPLIB 格式支持已实现；EoH/LLM reproduction 与农业迁移仍是后续工作，
不写成已完成能力。标准问题服务于农业 CPP 主研究对象，不与其并列改写项目定位。

分层与依赖方向见 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)，组合优化公共边界见
[docs/OPTIMIZATION_FOUNDATIONS.md](docs/OPTIMIZATION_FOUNDATIONS.md)。基准结果账本
（`benchmarks/results/benchmark_ledger.jsonl`）的每一步封存条目即事实，README 不复述过程状态。

## 快速开始

一键环境（WSL2 Ubuntu 22.04，含 Fields2Cover 编译，幂等可重跑）：

```bash
git clone https://github.com/peakpeng666/agriautolab.git
bash agriautolab/scripts/install/setup_wsl.sh
```

只跑测试（任意 Linux/Windows，Python ≥3.10，无需 F2C）：

```bash
pip install -e .[dev] "shapely==2.1.2"
pytest -q          # 以 CI 徽章为准（计数随提交演进，不在文档硬编码）
```

净室安装记录与自校验已随冻结研究归档：见
[study-001-frozen tag 的 docs/INSTALL_TRANSCRIPT.md](https://github.com/peakpeng666/agriautolab/blob/study-001-frozen/docs/INSTALL_TRANSCRIPT.md)
（主干不再携带该文档，复现方式见下节）。

## 包结构

```text
src/agriautolab/
├── contracts/       // 强类型问题/几何/机具/协议契约；含 TSP/CVRP 路由契约
├── geometry/        // 几何内核：robust_union、校验、离散化
├── kinematics/      // Dubins / Reeds-Shepp 运动学
├── algorithms/      // 五阶段算法 + 标准问题人工 constructive baselines
├── optimization/    // constructive problem/heuristic/evaluator 方法学验证层
├── pipeline/        // 五阶段串联执行、指标、Pareto、内容哈希、JSONL 实验日志
├── selection/       // 特征提取、冻结 CV、偏好条件推荐器与评估
├── evaluation/      // 确证统计：Pareto 前沿、行角效应、推荐器评估与前检
├── datasets/        // Fields2Benchmark 接入：许可过滤、CRS 守卫、隔离；TSPLIB/CVRPLIB
├── agent/           // 农业 swath 启发式演化循环（LLM 后端注入，默认 mock）
└── validation/      // 独立路径校验器 + F2C/F2B 交叉验证对账
```

配套数据与脚本：

```text
├── configs/standard_configs.json   // 13 个冻结 pipeline configuration
├── dataset_splits/                 // 语料划分产物（manifest、CV 折表、holdout partition）
├── benchmarks/results/             // 基准结果账本与封存产物
├── docs/                           // 架构、命名、优化方法学边界、安装/发布记录
├── scripts/                        // 安装、语料运行、对账、评估入口
└── tests/                          // 解析真值、不变量、确定性、证据重放、回归
```

## 核心数字

| 量 | 值 |
|---|---|
| 真实地块 | 235（EE+NL 自由许可；350 输入过滤而来） |
| 运行 | 61,100 = 235 田 × 5 行角 × 2 行距 × 2 机具 × 13 配置 |
| ok / 不适用 / 出界 / 碰撞 | 31,168 / 10,040 / 12,718 / 7,174 |
| 兜底桶 other / 崩溃 crash | **0 / 0**（分类完备性验收） |
| 有效池 | ≥1 OK 实例口径中位 10/13；全实例另含 924 个零 OK 实例 |

冻结研究的完整结果（三条确证检验的统计量、p 值、失效判据与 Holm 结论）以封存形式保存在
`study-001-frozen` tag，见下节。

## 历史研究复现（study-001-frozen tag）

本项目的第一轮完整研究（预注册、修正案、235 田全量运行、三条确证检验与封存结果）已整体
冻结在 **`study-001-frozen`** tag（对应 commit `566748a`）：

```bash
git fetch origin study-001-frozen
git checkout study-001-frozen     # 证据链在该 tag 上自洽可验
```

- tag 对象 SHA：`fcdd8e7faf4a1f1464636dabf9c3254fbe81e956`
- 目标 commit SHA：`566748a7290e2a4d53f44288937a442351b5d797`
- 该 tag 包含：预注册与修正案 01–05、`evidence/` 目录中的溯源与 F2C 对账、
  分析账本（含全部封存结果与追加记录）、`prereg/` 与 `AUDIT_NOTE.md` 的完整历史。

主干仓库不再携带这些冻结产物：分析与统计代码已按新命名体系迁移（见
[docs/NAMING.md](docs/NAMING.md)），复现请始终从上述 tag 出发，而不是主干上的仓库内路径。

## 研究纪律

预注册不回改；修正案只追加。独立统计单位为 field；Pareto 前沿与行角效应检验使用冻结
全语料，推荐器评估使用预先密封的 70/235 地块 holdout。当前实现一旦发现推荐器结果已封存，
会在读取其他输入前 fail-closed 拒绝 holdout 重跑。全部迭代与整改的完整留痕见
`AUDIT_NOTE.md`（历史版本位于 `study-001-frozen` tag；主干不再维护该文件）。
命名与注释规则见 [docs/NAMING.md](docs/NAMING.md)，发布纪律见
[docs/RELEASE.md](docs/RELEASE.md)。

## 许可

本仓库代码以 Apache License 2.0 发布：[LICENSE](LICENSE)；引用与归档元数据见
[CITATION.cff](CITATION.cff) 与 [.zenodo.json](.zenodo.json)。

上游数据集（Fields2Benchmark）的许可状态仍待裁定（Zenodo 记录内 LICENSE 文件与元数据
不一致）：数据集派生物在裁定前继续按更严一方（CC BY-SA）行事，裁定依据与原文摘录见
[docs/refs/licenses/fields2benchmark.md](docs/refs/licenses/fields2benchmark.md)。
