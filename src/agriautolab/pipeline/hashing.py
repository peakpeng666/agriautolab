"""为证据记录生成确定的内容、源码树与环境指纹。

陷阱：content_hash 需 sort_keys 且 allow_nan=False。
键序不同要得到同一哈希；而 NaN 一旦被序列化进 JSON，两条实际不同的记录会撞成同一个哈希。
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import platform
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TypeAlias

from pydantic import BaseModel

JsonScalar: TypeAlias = str | int | float | bool | None
JsonValue: TypeAlias = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]


def _json_value(value: JsonValue | BaseModel) -> JsonValue:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_json_value(item) for item in value]
    return value


def content_hash(value: JsonValue | BaseModel) -> str:
    payload = json.dumps(_json_value(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def source_hash(path: str | Path) -> str:
    root = Path(path)
    if root.is_file():
        return hashlib.sha256(root.read_bytes()).hexdigest()
    files = tuple(sorted(file for file in root.rglob("*") if file.is_file() and "__pycache__" not in file.parts))
    digest = hashlib.sha256()
    for file in files:
        digest.update(file.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(file.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def environment_fingerprint() -> str:
    payload: dict[str, JsonValue] = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "packages": {
            name: importlib.metadata.version(name)
            for name in ("numpy", "pydantic", "shapely")
        },
    }
    return content_hash(payload)
