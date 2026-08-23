"""封存产物的原子提交：先校验后落盘，杜绝「先覆盖再被 sealer 拒绝」。

规则：若账本里该 artifact 已有封存哈希，且新产物字节与之不同——
在写盘之前拒绝（旧件原样保留）；相同则幂等跳过或原子替换。
未封存过的 artifact 走普通原子写（临时文件 + os.replace）。
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_write(path: Path, data: bytes) -> None:
    """临时文件 + os.replace：读者要么看到旧件要么看到完整新件。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(data)
    os.replace(tmp, path)


def sealed_sha_for(ledger_path: str | Path, artifact: str, key: str) -> str | None:
    """账本中该 artifact 封存时记录的文件哈希（key 为 payload 内哈希字段名）。"""
    path = Path(ledger_path)
    if not path.exists():
        return None
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line).get("payload", {})
        if payload.get("artifact") == artifact and key in payload:
            return str(payload[key])
    return None


def commit_guarded(tmp: Path, final: Path, ledger_path: str | Path, artifact: str, key: str) -> None:
    """把 tmp 提交为 final，先过封存守卫。

    已封存且字节不同 → 拒绝（final 保持原样，tmp 由调用方清理）；
    已封存且相同 → 幂等替换；未封存 → 原子替换。
    """
    sealed = sealed_sha_for(ledger_path, artifact, key)
    if sealed is not None and sha256_file(tmp) != sealed:
        raise ValueError(
            f"新产物与已封存的 {artifact}（{key}={sealed[:16]}…）字节不一致："
            "拒绝覆盖。封存后的重算必须逐字节复现，否则是身份漂移，不是重跑。"
        )
    final.parent.mkdir(parents=True, exist_ok=True)
    os.replace(tmp, final)
