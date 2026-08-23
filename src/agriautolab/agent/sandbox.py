"""生成代码的执行沙箱：AST 静态扫描 + 受限 exec。

受限 exec 不构成安全边界，无法阻止刻意绕过。
它挡的是「模型顺手写了个 open('/etc/passwd')」。真正的隔离是进程/容器级，本项目不做。
（沿用任务书原话；不得将其表述为安全保证。）
"""

from __future__ import annotations

import ast
import math
from typing import Any


class SandboxViolation(Exception):
    """候选代码命中静态扫描禁令。"""


# __builtins__ 白名单：只有纯计算原语；名字不在表里的内建一律不可见。
_ALLOWED_BUILTINS = {
    "math": math,
    "len": len,
    "range": range,
    "min": min,
    "max": max,
    "abs": abs,
    "sum": sum,
    "enumerate": enumerate,
    "sorted": sorted,
    "tuple": tuple,
    "list": list,
    "float": float,
    "int": int,
}

_FORBIDDEN_NAMES = {"open", "eval", "exec", "compile", "__import__", "input", "globals", "locals", "vars", "getattr"}


def scan_source(source: str) -> None:
    """静态扫描（先于任何执行）：import、open/eval/exec 族、双下划线属性访问一律拒绝。

    只靠运行时白名单不够： AttributeError 类的绕过、装饰器里的花样，
    都会在静态树上现形。扫描不过，代码根本不进 exec。
    """
    try:
        tree = ast.parse(source)
    except SyntaxError as error:
        raise SandboxViolation(f"候选代码语法错误：{error}") from error
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            raise SandboxViolation("候选代码禁止 import：依赖必须在白名单内自足")
        if isinstance(node, ast.Name) and node.id in _FORBIDDEN_NAMES:
            raise SandboxViolation(f"候选代码禁止使用 {node.id}")
        if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            raise SandboxViolation(f"候选代码禁止访问双下划线属性：{node.attr}")


def run_sandboxed(source: str) -> dict[str, Any]:
    """在受限命名空间里执行候选代码，返回其顶层命名空间。"""
    scan_source(source)
    namespace: dict[str, Any] = {"__builtins__": _ALLOWED_BUILTINS}
    exec(compile(source, "<candidate>", "exec"), namespace)  # noqa: S102 -- 有意为之，见模块 docstring
    return namespace
