# 贡献指南

## 开工前四问（每个实质缺陷都归四类之一）

| 规则 | 问自己 |
|---|---|
| 单一真相源 | 这个事实仓库里已有住所吗？有就改接口，别建第二处 |
| 作用域有效性 | 这个量在什么作用域内有效？我在跨越它吗？ |
| 声明可证伪 | 调用方申报的值，系统能核对吗？能就必须核对 |
| 分类完备性 | 有没有 other/misc 兜底桶？有就是分类错误，收尾必须为 0 |

（第五类已出现过一次：映射欠定——特征看不见的量若改变最优解，
特征层必须显式声明其不可见性。）

## 硬约束（改了即作废全部历史实验身份）

- **wire ID 永不改**：`row_crossings`、`dubins_transit`、`uniform_headland`
  等已进 parquet/manifest/预注册/pool_hash 的字符串。规范名走
  `docs/NAMING.md` 的 canonical 层（别名/属性/`canonical_name`）。
- **冻结证据只追加、不修漂亮**：预注册原件、已封存 result 与 ledger 历史
  entry 一旦进入公开证据链，就不能为了修 bug 或整理文字而回写。封存后发现
  缺陷必须新增 corrigendum + 后继 ledger entry，并明确主推断是否改变。
- **字节冻结件零接触**：`src/agriautolab/cross_validation/f2c.py`、
  `configs/corpus_13.json`、`prereg/AGRIPLAN-PARETO-001.yaml`
  （哈希门测试钉住；预注册只允许按既有协议追加允许的历史修正文件）。
- **shapely 钉 2.1.2**：shapely 大版本绑定 GEOS 行为，升级 = 换几何引擎，
  必须先重跑解析真值并把 GEOS 版本补进 `evidence/env_geometry.json`。
- **已公开 tag 不移动**：release 历史有缺陷也走新版本或 corrigendum；禁止
  force-move tag 去制造“从未出错”的历史。完整规则见 `docs/RELEASE.md`。

## 流程

1. 分支开发 → 本地至少跑 `ruff check .` 与 `pytest -q`；PR 上以 CI 为准
2. CI 必须通过 lint、Python 3.10/3.12 pytest、`pip check`、package metadata、
   `compileall`
3. PR 模板逐项过一遍（动机/验收门/冻结证据/异议）
4. 语料类改动须附对账：pool_hash、协议哈希、冻结件 sha256 重放一致
5. 涉及 confirmatory evidence 时，必须说明是**新分析、复算还是 post-seal
   corrigendum**；三者不能混写
6. 历史叙事（日期、田 ID、迭代轮次、修复过程）进 `AUDIT_NOTE.md`，
   不进生产源码——生产注释只讲坐标系、单位、状态含义、非显然原因

## 注释与命名

英文标识符 + 简洁中文注释；详见 [docs/NAMING.md](docs/NAMING.md)。
