## 动机

为什么改这一条（一句话；对应哪条规则/哪轮复核/哪个 issue）。

## 改动

- 

## 验收门

- [ ] `pytest -q` 全绿（数量不降）
- [ ] `ruff check .` 通过
- [ ] `python -m pip check` 与 `compileall` 通过
- [ ] 未回写已封存的 prereg / result / ledger 历史 entry；若属 post-seal 修正，已追加 corrigendum
- [ ] 未触碰字节冻结件（`cross_validation/f2c.py` / `configs/corpus_13.json` / 原预注册 YAML）
- [ ] 语料类改动附重放对账（pool_hash / 协议哈希 / 冻结件 sha256）
- [ ] wire ID 未改；新增规范名已进 `docs/NAMING.md` 对照表
- [ ] CHANGELOG 已更新（用户可见变化）
- [ ] 若涉及 release：版本、changelog、目标 tag commit 一致，且不移动既有公开 tag

## 异议 / 取舍

有没有按规格实现但声明异议的地方；没有写「无」。
