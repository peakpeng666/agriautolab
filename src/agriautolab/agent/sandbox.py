"""AST static scanner and restricted execution environment for generated code."""

from __future__ import annotations

import ast
import math
from typing import Any


class SandboxViolation(Exception):
    """Static AST scanner violation in candidate code."""


# Allowed builtins: pure computational primitives only.
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
        raise SandboxViolation(f"Syntax error in candidate code: {error}") from error
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            raise SandboxViolation("Imports forbidden in candidate code; dependencies must be self-contained")
        if isinstance(node, ast.Name) and node.id in _FORBIDDEN_NAMES:
            raise SandboxViolation(f"Forbidden call: {node.id}")
        if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            raise SandboxViolation(f"Dunder attribute access forbidden: {node.attr}")


def run_sandboxed(source: str) -> dict[str, Any]:
    """在受限命名空间里执行候选代码，返回其顶层命名空间。"""
    scan_source(source)
    namespace: dict[str, Any] = {"__builtins__": _ALLOWED_BUILTINS}
    exec(compile(source, "<candidate>", "exec"), namespace)  # noqa: S102 -- 有意为之，见模块 docstring
    return namespace
