## 动机

为什么改这一条（一句话；对应哪条规则/哪轮复核/哪个 issue）。

## 改动

- 

## 验收门

- [ ] `pytest -q` 全绿（数量不降）
- [ ] `ruff check .` 通过
- [ ] 未触碰冻结件（`cross_validation/f2c.py` / `configs/corpus_13.json` / `prereg/*.yaml`）
- [ ] 语料类改动附重放对账（pool_hash / 协议哈希 / 冻结件 sha256）
- [ ] wire ID 未改；新增规范名已进 `docs/NAMING.md` 对照表
- [ ] CHANGELOG 已更新（用户可见变化）

## 异议 / 取舍

有没有按规格实现但声明异议的地方；没有写「无」。
