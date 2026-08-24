# 发布纪律

本项目的 release 不只是代码快照；它还可能锚定预注册、语料、模型和分析证据。
因此发布过程采用“版本可更新，历史不可改写”的原则。

## 发布前硬门

1. `main` 上 `lint`、`tests (3.10)`、`tests (3.12)` 全绿；
2. `python -m pip check`、源码 `compileall` 与包元数据检查通过；
3. `pyproject.toml` 版本与拟发布 tag 一致，`CHANGELOG.md` 有对应版本节；
4. `prereg/` 的冻结原件、已封存 result、ledger 历史 entry 禁止为“整理”而回写；
5. 若发现封存后缺陷，只能追加 corrigendum 与后继 ledger entry；
6. release tag 必须指向经过 PR+CI 的明确 commit，禁止 force-move 已公开 tag；
7. 发布说明必须披露会影响复现解释的 corrigendum / protocol deviation。

## main 分支版本

未正式打 tag 的主线使用 PEP 440 开发版本，例如 `0.5.1.dev0`。真正发布
`v0.5.1` 时，先通过独立 PR 把版本改为 `0.5.1`、关闭 changelog 的未发布节，
等 CI 全绿后再从该 merge commit 创建不可移动 tag/release。

## 已知历史例外

`v0.5.0` 是 Study-001 的原始科学结案 release，但其 tag 内的
`pyproject.toml` 仍为 `0.4.0`。该历史不通过移动 tag 或改写旧 commit 修补；
从 `0.5.1.dev0` 起恢复“源码版本—changelog—tag”一致性约束。
