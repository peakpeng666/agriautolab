# AgriAutoLab

[![CI](https://github.com/peakpeng666/agriautolab/actions/workflows/ci.yml/badge.svg)](https://github.com/peakpeng666/agriautolab/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](pyproject.toml)
[![tests](https://github.com/peakpeng666/agriautolab/actions/workflows/ci.yml/badge.svg)](https://github.com/peakpeng666/agriautolab/actions/workflows/ci.yml)

农业覆盖路径规划（Coverage Path Planning）的**研究级基准与分析层**：
把 13 个可组合规划配置在 235 块真实农田上全部跑通（61,100 次运行、
零崩溃、零未分类失败），量化「路程 / 地头掉头 / 作物行横穿等价量」
三目标之间的权衡，并在冻结证据纪律下研究偏好条件算法选择。

分层与依赖方向见 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)。
选择层的阶段性进度以 [evidence/block_d/](evidence/block_d/) 的分析账本为准
（每一步的封存条目即事实，不在 README 复述过程状态）。
三目标第三维历史 wire ID 为 `row_crossings`，规范语义名为
`row_crossing_equivalent`；它表达连续跨行等价量，不冒充实际逐行整数计数。

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

净室安装记录与九项自校验见 [docs/INSTALL_TRANSCRIPT.md](docs/INSTALL_TRANSCRIPT.md)。

## 文件目录结构说明

```text
└── agriautolab
    ├── src/agriautolab            // 主包
    │   ├── contracts/             // 契约层：问题、几何、机具、协议（依赖最底层）
    │   ├── geometry/              // 几何内核：robust_union、校验、离散化
    │   ├── kinematics/            // Dubins / Reeds-Shepp 运动学
    │   ├── agent/                 // LLM 演化循环（提案-闸门-账本，mock 后端）
    │   ├── algorithms/            // 五阶段算法实现（canonical 类名 + legacy 别名）
    │   ├── coverage/              // 冻结的阶段基线（兼容层）
    │   ├── datasets/              // Fields2Benchmark 接入：许可过滤、CRS 守卫、隔离
    │   ├── pipeline/              // 五阶段组合与执行入口
    │   ├── validation/            // 独立路径校验器（几何/运动学/行穿越）
    │   ├── metrics/               // 指标注册表：不可比指标进门即拒
    │   ├── features/              // 12 个实例特征 + 规范名词汇表
    │   ├── pareto/                // 前沿、超体积、偏好标量化与冻结偏好网格
    │   ├── corpus/                // 语料运行器（断点续跑、清单、账本）
    │   ├── benchmark/             // corpus 的规范入口（薄转发）
    │   ├── selection/             // Block D：冻结 CV 身份，后续承载推荐器
    │   ├── confirmatory/          // D5/D6：田级 H1/H2 统计量与显式零值规则
    │   ├── cross_validation/      // F2C 数值对账（f2c.py 字节冻结）
    │   ├── reconciliation/        // cross_validation 的规范名
    │   ├── aslib/                 // ASlib 格式导出（每目标一个 scenario）
    │   └── evidence/              // 内容哈希、哈希链账本、留出集封存
    ├── configs/corpus_13.json     // 13 配置池（哈希钉死 502b1e90…）
    ├── prereg/                    // 原预注册永不回改 + 修正案 01–05（05 为最终封口）
    ├── evidence/                  // v7 溯源、F2C 对账、Block D 分析链
    ├── docs/                      // 架构、命名、转折章程、安装记录
    ├── scripts/                   // 安装、语料运行、对账、D1 折表重放
    ├── tests/                     // 解析真值、不变量、确定性、证据重放、回归
    └── AUDIT_NOTE.md              // 全部迭代与整改的完整留痕（导师可查）
```

## 核心数字（v7 终语料，提交 ed1bccb）

| 量 | 值 |
|---|---|
| 真实地块 | 235（EE+NL 自由许可；350 输入过滤而来） |
| 运行 | 61,100 = 235 田 × 5 行角 × 2 行距 × 2 机具 × 13 配置 |
| ok / 不适用 / 出界 / 碰撞 | 31,168 / 10,040 / 12,718 / 7,174 |
| 兜底桶 other / 崩溃 crash | **0 / 0**（分类完备性验收） |
| 有效池 | ≥1 OK 实例口径中位 10/13；全实例另含 924 个零 OK 实例 |
| Pareto 前沿 / H1 | 193 可分析田主口径中位 3.0；42/235 零-ok 田；单侧 p=2.3921e-30 |
| Block D D1 | 165 training fields / 10 grouped folds；seed 20260822；17×5 + 16×5 |
| Block D D4 | 训练侧 3,300 实例 / 165 田；10 折 CV + final fit；模型 308 MB 留数据目录 |
| Block D D6 / H2 | 190 可分析田；n3/n4/n5=1/0/189；田内 rho 中位 0.3536；Pratt 单侧 p=1.2025e-12 |

v7 溯源件在 [evidence/v7/](evidence/v7/)，Block D 分析哈希链从
[evidence/block_d/](evidence/block_d/) 的 D1 genesis 开始。

## 研究纪律

原预注册不回改；修正案 01–05 只追加，其中 05 已声明为最终 confirmatory
执行规范封口。独立统计单位为 field；H1/H2 按修正案使用冻结全语料作田级
前沿/受控处理检验，不消费模型或留出划分成员关系。留出集 70/235 地块在
分析前密封，H3 只在最终模型评估阶段一次性打开并按 70/68 双轨报告。D1 训练折在任何推荐器训练
之前落盘并进入独立 Block D 哈希链，后续训练不得重新 split。全部过程批判与
整改见 [AUDIT_NOTE.md](AUDIT_NOTE.md)，命名与注释规则见
[docs/NAMING.md](docs/NAMING.md)，转折与执行顺序见
[docs/TURNING_POINT.md](docs/TURNING_POINT.md)。

## 许可

代码与派生数据的许可声明待数据集上游（Zenodo 记录内 LICENSE 文件与
元数据不一致）裁定后挂牌，裁定前按更严一方（CC BY-SA）行事：
[docs/refs/licenses/fields2benchmark.md](docs/refs/licenses/fields2benchmark.md)。
