# 证据链的能力边界与外部锚定

本页说明 `evidence/block_d/ledger.jsonl` 哈希链**能**与**不能**提供什么保证，
以及如何用外部锚定补上缺口。

措辞纪律：本项目的账本是 **hash chain（哈希链），不是 blockchain（区块链）**。
它没有区块、没有分布式共识、没有矿工或 token。在任何对外材料中把它说成
“区块链”都是错误表述。

## 提供什么

- **链内一致性**：每条 `entry_hash` 由
  `content_hash({index, previous_hash, payload})` 派生（SHA-256，键排序、
  紧凑分隔符，见 `src/agriautolab/evidence/hashing.py`）。任何一条记录的
  身份都绑定前一条的哈希；genesis 的 `previous_hash` 为 64 个 `0`。
- **篡改可检测**：改动任何一条历史记录的内容，该条的 `entry_hash` 随之改变，
  使其后**全部**条目的 `previous_hash` 链接断裂。`verify_artifact_chain`
  重放全链时会在第一个断点响亮失败，而不是静默通过。
- **追加式内容寻址**：条目只追加、不回写；多数 payload 还绑定相关文件的
  SHA-256，使“账本条目 ↔ 落盘文件”也形成字节级身份。

## 不提供什么

- **外部时间证明**：账本内的时间戳来自本地机器时钟，可伪造、可回拨。链本身
  不能证明“某内容在某个时刻已经存在”。
- **非否认性（non-repudiation）**：没有数字签名，无法把某条记录绑定到某个
  不可抵赖的身份。
- **共识机制**：这是单机账本，没有多方验证者。攻击者可以把整条链连同 genesis
  一起重新生成出一条自洽的新链，复算本身无法发现这种整体替换。

一句话：哈希链证明的是**链内部**的自洽与相对既有条目的不可静默篡改；它不证明
链**外部**的时间、身份或多方共识。

## 如何补上：外部锚定

`scripts/export_ledger_anchor.py`（严格只读）复算全链并把锚定材料打印到
stdout，落盘由 shell 重定向完成：

```bash
python scripts/export_ledger_anchor.py > ledger_anchor.txt
```

把报告中的**链尾 root hash**（`tail_entry_hash`，即最后一条的 `entry_hash`）
提交给外部锚定服务，使“该 root hash 在某时刻已存在”获得独立于本仓库的证明：

- **OpenTimestamps**：把 root hash 挂锚到 Bitcoin 公链时间证明
  （注意：锚定动作借用外部公链，这不改变本仓库账本是哈希链的定性），
  事后可独立验证 existence proof；
- **Zenodo 版本 DOI 归档**：发布带版本 DOI 的软件版本记录（仓库根的
  `CITATION.cff` 与 `.zenodo.json` 提供归档元数据），归档记录自带时间戳
  与内容指纹。

## 与 force-push 防护的关系

Git 历史（包括 tag）可以被 force-push 重写；本仓库的冻结纪律是**流程纪律**，
不是密码学防护。外部锚定补的正是这一层：某个 root hash 一旦被外部服务记录，
“该 hash 在某时刻已存在”就不再依赖本仓库的任何字节。事后即使整条 Git 历史
被重写、账本被整体重造，外部锚点也无法被追溯性伪造——任何人都能用锚定材料
证明“现在仓库里的链不是当时被锚定的那条链”。锚定应随每次封存性追加
（新的 ledger 条目）重新执行，root hash 因此总是对应当前链尾。
