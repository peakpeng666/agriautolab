# AgriAutoLab

[![CI](https://github.com/peakpeng666/agriautolab/actions/workflows/ci.yml/badge.svg)](https://github.com/peakpeng666/agriautolab/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](pyproject.toml)
[![tests](https://img.shields.io/badge/tests-544%20passed-brightgreen)](tests/)

农业覆盖路径规划（Coverage Path Planning）的**研究级基准与分析层**：
把 13 个可组合规划配置在 235 块真实农田上全部跑通（61,100 次运行、
零崩溃、零未分类失败），量化「路程 / 掉头 / 横穿作物行」三目标之间的
真实权衡，并训练看一眼田块形状就能推荐配置的选择器。

三层冻结（L1 域核心 / L2 算法层 / L3 基准层）已交付，分层与依赖方向见
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)；L4 选择层（Block D）待开工。
三目标向量的第三维 `row_crossings`（横穿作物行）是本项目首倡的农业专属
目标——拿掉它，目标空间会塌成一根轴。

## 快速开始

一键环境（WSL2 Ubuntu 22.04，含 Fields2Cover 编译，幂等可重跑）：

```bash
git clone https://github.com/peakpeng666/agriautolab.git
bash agriautolab/scripts/install/setup_wsl.sh
```

只跑测试（任意 Linux/Windows，Python ≥3.10，无需 F2C）：

```bash
pip install -e .[dev] "shapely==2.1.2"
pytest -q          # 544 passed / 30 skipped
```

净室安装记录与九项自校验见 [docs/INSTALL_TRANSCRIPT.md](docs/INSTALL_TRANSCRIPT.md)。

## 文件目录结构说明

```
└── agriautolab
    ├── src/agriautolab            // 主包
    │   ├── contracts/             // 契约层：问题、几何、机具、协议（依赖最底层）
    │   ├── geometry/              // 几何内核：robust_union、校验、离散化
    │   ├── kinematics/            // Dubins / Reeds-Shepp 48 词运动学
    │   ├── agent/                 // LLM 演化循环（提案-闸门-账本，mock 后端）
    │   ├── algorithms/            // 五阶段算法实现（canonical 类名 + legacy 别名）
    │   ├── coverage/              // 冻结的阶段基线（兼容层，实现唯一来源）
    │   ├── datasets/              // Fields2Benchmark 接入：许可过滤、CRS 守卫、隔离
    │   ├── pipeline/              // 五阶段组合与执行入口
    │   ├── validation/            // 独立路径校验器（几何/运动学/行穿越）
    │   ├── metrics/               // 指标注册表：不可比指标进门即拒
    │   ├── features/              // 10 个实例特征 + 规范名词汇表
    │   ├── pareto/                // 前沿、超体积、偏好标量化
    │   ├── corpus/                // 语料运行器（断点续跑、清单、账本）
    │   ├── benchmark/             // corpus 的规范入口（薄转发）
    │   ├── cross_validation/      // F2C 数值对账（f2c.py 字节冻结）
    │   ├── reconciliation/        // cross_validation 的规范名
    │   ├── aslib/                 // ASlib 格式导出（每目标一个 scenario）
    │   └── evidence/              // 内容哈希、哈希链账本、留出集封存
    ├── configs/corpus_13.json     // 13 配置池（哈希钉死 502b1e90…）
    ├── prereg/                    // 预注册（sha256 8d1326de… 永不回改）+ 修正案 01–03
    ├── evidence/                  // 对账金标、环境指纹、v7 溯源件（manifest/账本校验）
    ├── docs/                      // 设计文档、NAMING.md、迭代报告、安装记录
    ├── scripts/                   // 一键安装五件套、语料运行、交叉表分析
    ├── tests/                     // 544 项：解析真值、不变量、确定性、回归
    └── AUDIT_NOTE.md              // 全部迭代与整改的完整留痕（导师可查）
```

## 核心数字（v7 终语料，提交 ed1bccb）

| 量 | 值 |
|---|---|
| 真实地块 | 235（EE+NL 自由许可；350 输入过滤而来） |
| 运行 | 61,100 = 235 田 × 5 行角 × 2 行距 × 2 机具 × 13 配置 |
| ok / 不适用 / 出界 / 碰撞 | 31,168 / 10,040 / 12,718 / 7,174 |
| 兜底桶 other / 崩溃 crash | **0 / 0**（分类完备性验收） |
| 有效池 | 中位 10/13，最大 12（双机具解锁 RS） |
| Pareto 前沿 | 中位 3.0（典型田上有三种合理答案） |

溯源件（含 ledger 哈希链 61,101 条逐条复算验证）在 [evidence/v7/](evidence/v7/)。

## 研究纪律

预注册先封存后看数（H1 权衡存在 / H2 权衡由田形决定 / H3 推荐器胜随机
一倍），改动只追加修正案；留出集 70/235 地块跑前密封、看过结果后禁止
重封；每个数字可经哈希链追回出处。全部过程批判与整改见
[AUDIT_NOTE.md](AUDIT_NOTE.md)，命名与注释规则见 [docs/NAMING.md](docs/NAMING.md)，
贡献流程见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 许可

代码与派生数据的许可声明待数据集上游（Zenodo 记录内 LICENSE 文件与
元数据不一致）裁定后挂牌，裁定前按更严一方（CC BY-SA）行事：
[docs/refs/licenses/fields2benchmark.md](docs/refs/licenses/fields2benchmark.md)。
