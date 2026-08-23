"""录制壳的静态守卫：它必须能在 WSL / python3.10 上跑，而这里是 Windows / 3.12。

跨版本兼容性没法在本进程里真跑出来，所以这组测试守的是**能静态守住的那部分**：
不 import agriautolab、只用 3.10 兼容语法、与适配器共用同一份链路实现。
真跑的证据在 AUDIT_NOTE 里（WSL 上的实际录制输出）。
"""

import ast
import pathlib

import pytest

from agriautolab.cross_validation import f2c_chain
from agriautolab.cross_validation.f2c import PythonBindingAdapter, SubprocessAdapter


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
CHAIN = REPO_ROOT / "src" / "agriautolab" / "cross_validation" / "f2c_chain.py"
RECORDER_DIR = REPO_ROOT / "scripts" / "f2c_recorder"
PY310_SENSITIVE = (CHAIN, RECORDER_DIR / "record_golden.py", RECORDER_DIR / "env_probe.py")


def imported_module_names(path: pathlib.Path) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


@pytest.mark.parametrize("path", PY310_SENSITIVE, ids=lambda p: p.name)
def test_recorder_side_never_imports_agriautolab(path: pathlib.Path) -> None:
    """import 了 agriautolab 就会在 WSL py3.10 上撞 typing.Self —— 实测复现过。"""
    offenders = {name for name in imported_module_names(path) if name.split(".")[0] == "agriautolab"}
    assert not offenders, f"{path.name} 不能 import agriautolab：{sorted(offenders)}"


@pytest.mark.parametrize("path", PY310_SENSITIVE, ids=lambda p: p.name)
def test_recorder_side_declares_future_annotations(path: pathlib.Path) -> None:
    """没有它，X | Y 注解在 3.10 上会在 import 期求值报错。"""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    assert any(
        isinstance(node, ast.ImportFrom) and node.module == "__future__"
        and any(alias.name == "annotations" for alias in node.names)
        for node in tree.body
    ), f"{path.name} 缺 from __future__ import annotations"


@pytest.mark.parametrize("path", PY310_SENSITIVE, ids=lambda p: p.name)
def test_recorder_side_avoids_311_only_typing_names(path: pathlib.Path) -> None:
    """typing.Self / assert_never / LiteralString 都是 3.11 才有的。"""
    forbidden = {"Self", "assert_never", "LiteralString", "TypeVarTuple", "Unpack"}
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    used = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module in {"typing", "typing_extensions"}:
            used.update(alias.name for alias in node.names)
    assert not (used & forbidden), f"{path.name} 用了 3.11+ typing 名：{sorted(used & forbidden)}"
    # except* 是 3.11 语法；ast 在 3.12 上能解析，所以只能按源码文本查。
    assert "except*" not in source


def test_recorder_and_adapter_share_one_chain_implementation() -> None:
    """等价性由「只有一份实现」保证，不靠事后比对两份输出。

    录制期有两个一次性壳（/home/peak/f2c_golden_wrapper.py 与
    o2_workspace/record_golden_standalone.py），它们随时可能各自漂移。
    """
    adapter_source = (REPO_ROOT / "src" / "agriautolab" / "cross_validation" / "f2c.py").read_text(
        encoding="utf-8"
    )
    assert "f2c_chain.run_chain" in adapter_source
    recorder_source = (RECORDER_DIR / "record_golden.py").read_text(encoding="utf-8")
    assert "chain.run_chain" in recorder_source
    assert "f2c_chain.py" in recorder_source
    # 两侧都不得自己再拼一条链路。
    for source in (adapter_source, recorder_source):
        assert "SG_BruteForce" not in source
        assert "PP_DubinsCurves" not in source


def test_recorder_csv_columns_match_the_locked_schema() -> None:
    """录制壳写的列必须与 RecordedCsvAdapter 认的列逐位一致，否则录完才发现读不了。"""
    from agriautolab.cross_validation.f2c import _CSV_COLUMNS

    namespace: dict = {}
    for node in ast.parse((RECORDER_DIR / "record_golden.py").read_text(encoding="utf-8")).body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "CSV_COLUMNS":
            namespace["CSV_COLUMNS"] = ast.literal_eval(node.value)
    assert namespace["CSV_COLUMNS"] == _CSV_COLUMNS


def test_route_planner_map_is_shared_and_excludes_lookalikes() -> None:
    """只映射语义相同的。我方 skip_one_order 与 RP_Snake 回扫方向不同，不许硬配。"""
    from agriautolab.cross_validation.f2c import F2C_ROUTE_PLANNERS
    from agriautolab.cross_validation.ours import OURS_ROUTE_ALGORITHMS

    assert F2C_ROUTE_PLANNERS is f2c_chain.F2C_ROUTE_PLANNERS
    assert F2C_ROUTE_PLANNERS["boustrophedon"] == "RP_Boustrophedon"
    assert set(OURS_ROUTE_ALGORITHMS) == {"boustrophedon"}
    assert "snake" not in OURS_ROUTE_ALGORITHMS


def test_wsl_command_mode_builds_a_wsl_invocation() -> None:
    adapter = SubprocessAdapter(wsl_command=r"D:\repo\scripts\f2c_recorder\record_golden.py")
    assert adapter._command() == [
        "wsl.exe", "-e", "python3", "/mnt/d/repo/scripts/f2c_recorder/record_golden.py",
    ]
    assert SubprocessAdapter.to_wsl_path("/already/posix") == "/already/posix"


def test_subprocess_adapter_requires_exactly_one_mode() -> None:
    with pytest.raises(ValueError):
        SubprocessAdapter()
    with pytest.raises(ValueError):
        SubprocessAdapter("exe", wsl_command="script.py")


def test_transit_breakdown_from_states_rejects_a_pathless_of_swaths() -> None:
    class _State:
        def __init__(self, length, kind):
            self.len = length
            self.type = kind

    class _Path:
        def __init__(self, states):
            self._states = states

        def size(self):
            return len(self._states)

        def getState(self, index):
            return self._states[index]

    with pytest.raises(f2c_chain.F2CChainError, match="SWATH"):
        f2c_chain.transit_breakdown_from_states(_Path([_State(1.0, 2), _State(2.0, 2)]))

    breakdown = f2c_chain.transit_breakdown_from_states(
        _Path([_State(3.0, 2), _State(10.0, 1), _State(4.0, 2), _State(10.0, 1), _State(5.0, 2)])
    )
    assert breakdown["transit_entry_leg_m"] == pytest.approx(3.0)
    assert breakdown["transit_turn_total_m"] == pytest.approx(4.0)
    assert breakdown["transit_turn_count"] == 1.0
    assert breakdown["transit_exit_leg_m"] == pytest.approx(5.0)
    assert breakdown["transit_other_m"] == 0.0


def test_unknown_route_algorithm_is_refused_by_the_chain() -> None:
    with pytest.raises(f2c_chain.F2CChainError, match="route_algorithm"):
        f2c_chain.route_planner(object(), "no_such_route")


def test_python_binding_adapter_delegates_instead_of_reimplementing() -> None:
    assert hasattr(PythonBindingAdapter, "route_identity")
    assert hasattr(PythonBindingAdapter, "_run_chain")
