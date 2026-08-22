"""把预注册文件的内容哈希写进证据链。

对 yaml 做字节级 SHA-256，写入 prereg/AGRIPLAN-PARETO-001.seal.json；
再次运行时对账而不是重封（重封等于改主张）。无时钟、无随机：
封存记录只由文件字节决定，任何环境重算都得到同一结果。

用法：python scripts/seal_preregistration.py
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PREREG_FILE = REPO_ROOT / "prereg" / "AGRIPLAN-PARETO-001.yaml"
SEAL_FILE = REPO_ROOT / "prereg" / "AGRIPLAN-PARETO-001.seal.json"


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    if not PREREG_FILE.is_file():
        print(f"找不到预注册文件：{PREREG_FILE}", file=sys.stderr)
        return 1
    digest = file_digest(PREREG_FILE)
    if SEAL_FILE.is_file():
        sealed = json.loads(SEAL_FILE.read_text(encoding="utf-8"))
        if sealed["file_sha256"] == digest:
            print(f"已封存且一致：{SEAL_FILE}")
            print(f"  sha256 = {digest}")
            return 0
        print("封存对不上：预注册文件在封存后被修改过。", file=sys.stderr)
        print(f"  封存时 {sealed['file_sha256']}", file=sys.stderr)
        print(f"  当前   {digest}", file=sys.stderr)
        return 2
    SEAL_FILE.write_text(
        json.dumps(
            {
                "study_id": "AGRIPLAN-PARETO-001",
                "file": PREREG_FILE.name,
                "file_sha256": digest,
                "bytes": PREREG_FILE.stat().st_size,
                "seal_rule": "字节级 SHA-256；重算即对账，不重封",
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"已封存：{SEAL_FILE}")
    print(f"  sha256 = {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
