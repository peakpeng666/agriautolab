#!/usr/bin/env python3
"""导出 Block D 证据链的外部锚定材料（严格只读）。

读取 ``evidence/block_d/ledger.jsonl``，逐条复算哈希链自洽性（复用
``agriautolab.evidence.ledger.verify_artifact_chain`` 的同一规则），向 stdout
打印每条 ``index -> entry_hash`` 对照表、链尾（最后一条）``entry_hash`` 与
记录总数。链在任何一处不一致（缺必需字段、index 断档、previous_hash 断链、
entry_hash 复算不符）都以非零退出码失败（fail-closed），绝不输出半份锚定材料。

本脚本不包含任何写文件调用：``evidence/`` 绝不写回，落盘需求由调用方的
shell 重定向满足，例如::

    python scripts/export_ledger_anchor.py > ledger_anchor.txt

打印的链尾 root hash 用于外部锚定（OpenTimestamps existence proof、Zenodo
版本 DOI 归档），能力边界与操作说明见 ``docs/EVIDENCE_CHAIN.md``。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# 支持不安装包时从仓库根直接 ``python scripts/export_ledger_anchor.py`` 运行；
# 包已 editable 安装时该注入是无害的空操作路径（src 优先级不影响已解析的包）。
REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from agriautolab.contracts.errors import EvidenceChainError  # noqa: E402
from agriautolab.evidence.ledger import verify_artifact_chain  # noqa: E402

DEFAULT_LEDGER = REPO_ROOT / "evidence" / "block_d" / "ledger.jsonl"
REQUIRED_KEYS = ("index", "previous_hash", "payload", "entry_hash")


def load_entries(ledger_path: Path) -> tuple[dict, ...]:
    """只读解析 JSONL；空行忽略，缺必需字段的行就地拒绝，链规则交给 verify 判定。"""
    entries: list[dict] = []
    with ledger_path.open("r", encoding="utf-8") as handle:  # 唯一的文件访问，只读
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"{ledger_path}:{line_number}: 非法 JSON 行：{error}") from error
            if not isinstance(entry, dict):
                raise ValueError(f"{ledger_path}:{line_number}: 条目必须是 JSON 对象")
            missing = [key for key in REQUIRED_KEYS if key not in entry]
            if missing:
                raise ValueError(f"{ledger_path}:{line_number}: 缺少必需字段：{', '.join(missing)}")
            entries.append(entry)
    if not entries:
        raise ValueError(f"{ledger_path}: 空账本，没有可锚定的链尾")
    return tuple(entries)


def export_anchor_report(ledger_path: Path) -> str:
    """复算全链并渲染锚定报告；链不自洽时抛错，不产生任何输出。"""
    entries = load_entries(ledger_path)
    verify_artifact_chain(entries)
    lines = [
        "block-d ledger anchor export (read-only)",
        f"ledger_path: {ledger_path}",
        "index  entry_hash",
    ]
    for entry in entries:
        lines.append(f"{entry['index']:<5}  {entry['entry_hash']}")
    tail = entries[-1]
    lines.append(f"total_entries: {len(entries)}")
    lines.append(f"tail_index: {tail['index']}")
    lines.append(f"tail_entry_hash: {tail['entry_hash']}")
    lines.append("chain_verified: ok")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--ledger",
        type=Path,
        default=DEFAULT_LEDGER,
        help="账本 JSONL 路径（默认：evidence/block_d/ledger.jsonl）",
    )
    args = parser.parse_args()
    try:
        report = export_anchor_report(args.ledger)
    except (OSError, ValueError, EvidenceChainError) as error:
        print(f"export_ledger_anchor: fail-closed，拒绝导出：{error}", file=sys.stderr)
        return 1
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
