"""Fields2Cover 交叉验证适配器：绑定、子进程、离线 CSV 三条路径返回同一结构。"""

from __future__ import annotations

import csv
import importlib.util
import json
import math
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import shapely

from agriautolab.pipeline.hashing import content_hash

from agriautolab.validation import f2c_chain
from agriautolab.validation.f2c_chain import F2C_ROUTE_PLANNERS


class F2CUnavailableError(RuntimeError):
    """请求的 F2C 执行模式在当前环境不可用。"""


class F2CSchemaError(ValueError):
    """离线交换文件不满足锁死的 schema。"""


class RouteAlgorithmMismatchError(ValueError):
    """两侧路线算法不同名，或某一侧没有该名字的实现。

    存在的理由（2026-08-21 实测）：交叉验证规格要求配对同名路线算法，
    地头阶段配了（CW ↔ uniform_headland），路线阶段没配。后果是
    F2C 跑 RP_Snake（访问顺序 [0,2,4,…,20,19,17,…,3,1]，隔行 + 回扫），
    我方跑 boustrophedon_order（相邻），两侧 transit 中位差 −38.11%，
    而这个差被当成了「我方路径更短」。

    陷阱：不许拿名字相近的实现顶替。我方 skip_one_order 的奇数轮是升序
    （0,2,4,…,1,3,5,…），F2C RP_Snake 的奇数轮是降序回扫，两者不是同一条路线。
    没有实现就抛，不要替换。
    """


class CrsMismatchError(ValueError):
    """两侧录制在不同的 working CRS 里，任何残差都无法归因给算法。

    存在的理由（2026-08-21 事故）：F2B wkt.zip 实为 WGS84 经纬度，
    门户声明 EPSG:3301/28992/3346，to_metric_crs 走了「已是米制」快速通道，
    5.0 米地头被当 5.0 度用，地块被内缩吃光。那次响了是因为地块归零，很吵。
    但把 EPSG:28992 误报成 EPSG:3301 是静默的——只让所有长度差几个百分点，
    而那正好是当前 path_length 残差的量级。排除投影差异之前不许归因给算法。
    """


@dataclass(frozen=True)
class F2CRequest:
    request_id: str
    field_wkt: str
    robot_width_m: float
    working_width_m: float
    min_turning_radius_m: float
    headland_width_m: float
    swath_angle_rad: float
    # field_wkt 所在的米制 CRS。故意不给默认值：录制端必须显式声明自己在哪个投影里
    # 干活，否则「忘记声明」和「确实同一投影」在 CSV 里长得一模一样。
    working_crs: str
    # 请求指定的路线算法。交叉验证规格要求配对同名路线算法，
    # 地头阶段早就配了（CW ↔ uniform_headland），路线阶段一直没配——
    # 实测后果：F2C 的 RP_Snake 访问顺序是 [0,2,4,…,20,19,17,…,3,1]（隔行+回扫），
    # 我方 boustrophedon_order 是相邻，两侧 transit 中位差 −38.11%。
    route_algorithm: str


@dataclass(frozen=True)
class F2CResult:
    request_id: str
    path_length: float
    swath_count: float
    swath_length_sum: float
    main_field_area: float
    # 转移五项分解。分量拆解纪律：path_length 是 work + transit 之和，
    # work 已对齐到 +0.169% 而 transit 差 −38.11%，合并报告会把 38% 稀释成 6%（差 6 倍）。
    transit_entry_leg_m: float
    transit_turn_total_m: float
    transit_turn_count: float
    transit_inter_cell_m: float
    transit_exit_leg_m: float
    transit_other_m: float
    # 由执行端回填：它实际在哪个投影里、用哪个路线算法算出了上面这些数。
    # 不是请求的回声——若某一端自己又投影了一次或换了路线，这里就会与另一端分家，然后被比较器拦下。
    working_crs: str
    route_algorithm: str


class F2CAdapter(Protocol):
    def available(self) -> bool: ...
    def run(self, request: F2CRequest) -> F2CResult: ...


_NUMERIC_CSV_COLUMNS = (
    "path_length",
    "swath_count",
    "swath_length_sum",
    "main_field_area",
    "transit_entry_leg_m",
    "transit_turn_total_m",
    "transit_turn_count",
    "transit_inter_cell_m",
    "transit_exit_leg_m",
    "transit_other_m",
)
_TEXT_CSV_COLUMNS = ("working_crs", "route_algorithm")
_CSV_COLUMNS = ("request_id", *_NUMERIC_CSV_COLUMNS, *_TEXT_CSV_COLUMNS)


def _parse_result_row(row: dict[str, str]) -> F2CResult:
    try:
        values = tuple(float(row[name]) for name in _NUMERIC_CSV_COLUMNS)
    except ValueError as error:
        raise F2CSchemaError(f"F2C CSV 含非数值指标：{row!r}") from error
    if not all(math.isfinite(value) for value in values):
        raise F2CSchemaError(f"F2C CSV 指标必须为有限数：{row!r}")
    texts = {}
    for name in _TEXT_CSV_COLUMNS:
        value = (row[name] or "").strip()
        if not value:
            raise F2CSchemaError(f"F2C CSV 的 {name} 不能为空：{row!r}")
        texts[name] = value
    return F2CResult(row["request_id"], *values, **texts)


class RecordedCsvAdapter:
    """读取事先由 F2C/F2B 跑出的结果；精确 schema 是离线复核的契约。"""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._rows: dict[str, F2CResult] | None = None

    def available(self) -> bool:
        return self.path.is_file()

    def env_hash(self) -> str:
        """golden 录制环境的内容哈希；env_f2c.json 缺失时抛异常，不静默跳过。

        照 available()=False 抛异常的既有先例：没有环境指纹的 golden 无法对账
        『换 F2C 版本后还是不是同一份 golden』，静默跳过等于把版本漂移埋进证据链。
        """
        env_path = self.path.parent / "env_f2c.json"
        if not env_path.is_file():
            raise F2CUnavailableError(
                f"golden CSV 同目录缺少 env_f2c.json（{env_path}）：录制环境指纹是证据链的一部分"
            )
        return content_hash(json.loads(env_path.read_text(encoding="utf-8")))

    def _load(self) -> dict[str, F2CResult]:
        if not self.available():
            raise F2CUnavailableError(f"Recorded F2C CSV 不存在：{self.path}")
        with self.path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            actual = tuple(reader.fieldnames or ())
            missing = tuple(name for name in _CSV_COLUMNS if name not in actual)
            extra = tuple(name for name in actual if name not in _CSV_COLUMNS)
            if missing or extra or actual != _CSV_COLUMNS:
                raise F2CSchemaError(
                    f"F2C CSV schema 不匹配；缺列={missing}，多余列={extra}，"
                    f"实际顺序={actual}，期望={_CSV_COLUMNS}"
                )
            rows: dict[str, F2CResult] = {}
            for row in reader:
                parsed = _parse_result_row(row)
                if parsed.request_id in rows:
                    raise F2CSchemaError(f"F2C CSV request_id 重复：{parsed.request_id}")
                rows[parsed.request_id] = parsed
        return rows

    def run(self, request: F2CRequest) -> F2CResult:
        if self._rows is None:
            self._rows = self._load()
        if request.request_id not in self._rows:
            raise KeyError(f"Recorded F2C CSV 没有 request_id={request.request_id}")
        return self._rows[request.request_id]


class SubprocessAdapter:
    """调用用户提供的 F2C wrapper 可执行文件，交换 WKT + JSON + 严格 CSV。

    wrapper 接口固定为：`EXE --request request.json --field field.wkt --output result.csv`。
    AgriAutoLab 不重新实现 C++ 算法；wrapper 只负责把本契约翻译到本机 F2C 版本。

    陷阱（实测）：Python 脚本 wrapper 带 shebang 时只能靠 POSIX 直接执行；
    Windows 的 CreateProcess 不认 shebang（WinError 193，"不是有效的 Win32 应用程序"）。
    这里对 python shebang 的脚本显式经 `sys.executable` 调用；
    真正的二进制、批处理或 shell 脚本仍按原样直接执行。
    """

    def __init__(self, executable: str | Path | None = None, *, wsl_command: str | Path | None = None):
        if (executable is None) == (wsl_command is None):
            raise ValueError("executable 与 wsl_command 必须且只能给一个")
        self.executable = str(executable) if executable is not None else None
        # wsl_command 模式：Windows 侧经 wsl.exe 调 WSL 里的 python3 录制壳。
        # 这是 §0 那个两进程形态的正式调用口，不是绕过它。
        self.wsl_command = str(wsl_command) if wsl_command is not None else None

    @staticmethod
    def to_wsl_path(path: str | Path) -> str:
        """D:\\a\\b -> /mnt/d/a/b。已是 POSIX 路径的原样返回。"""
        text = str(path).replace("\\", "/")
        if len(text) >= 2 and text[1] == ":":
            return "/mnt/" + text[0].lower() + text[2:]
        return text

    def available(self) -> bool:
        if self.wsl_command is not None:
            return shutil.which("wsl.exe") is not None
        return Path(self.executable).is_file() or shutil.which(self.executable) is not None

    def _command(self) -> list[str]:
        if self.wsl_command is not None:
            return ["wsl.exe", "-e", "python3", self.to_wsl_path(self.wsl_command)]
        path = Path(self.executable)
        if path.is_file():
            try:
                first_line = path.open("rb").readline().decode("utf-8", errors="replace")
            except OSError:
                first_line = ""
            if first_line.startswith("#!") and "python" in first_line:
                import sys

                return [sys.executable, str(path)]
        return [self.executable]

    def run(self, request: F2CRequest) -> F2CResult:
        if not self.available():
            raise F2CUnavailableError(f"F2C wrapper 不可用：{self.executable or self.wsl_command}")
        with tempfile.TemporaryDirectory(prefix="agriautolab-f2c-") as temp:
            root = Path(temp)
            field_path = root / "field.wkt"
            request_path = root / "request.json"
            output_path = root / "result.csv"
            field_path.write_text(request.field_wkt + "\n", encoding="utf-8")
            request_path.write_text(json.dumps({
                "request_id": request.request_id,
                "robot_width_m": request.robot_width_m,
                "working_width_m": request.working_width_m,
                "min_turning_radius_m": request.min_turning_radius_m,
                "headland_width_m": request.headland_width_m,
                "swath_angle_rad": request.swath_angle_rad,
                "working_crs": request.working_crs,
                "headland_algorithm": "constant_width",
                # 曾经写死 "snake"：那正是两侧跑了不同路线、transit 差 −38.11% 的源头。
                "route_algorithm": request.route_algorithm,
                "path_algorithm": "dubins",
            }, sort_keys=True) + "\n", encoding="utf-8")
            # wsl_command 模式下临时目录是 Windows 路径，必须转成 /mnt/ 才能被 WSL 里的
            # python3 打开——WSL 认不出 C:\Users\...\Temp\...。
            convert = self.to_wsl_path if self.wsl_command is not None else str
            completed = subprocess.run(
                [*self._command(),
                 "--request", convert(request_path),
                 "--field", convert(field_path),
                 "--output", convert(output_path)],
                check=False,
                capture_output=True,
                text=True,
            )
            if completed.returncode != 0:
                raise RuntimeError(
                    f"F2C wrapper 退出码 {completed.returncode}；stderr={completed.stderr.strip()!r}"
                )
            return RecordedCsvAdapter(output_path).run(request)


class PythonBindingAdapter:
    """按 Fields2Cover 2.x 官方教程的 CW→fixed-angle→<协议指定路线>→Dubins 公共链路运行。

    只实现可直接同义对账的一条链，故意不把 Required Width 或其他优化器塞进来；
    交叉验证的价值来自“语义相同”，不是尽量多调用 API。

    路线算法由 request.route_algorithm 指定，不再写死 RP_Snake——
    写死那次的代价是两侧跑了不同的路线，transit 差 −38.11% 被读成了算法优势。
    """

    def available(self) -> bool:
        return importlib.util.find_spec("fields2cover") is not None

    @staticmethod
    def _params(request: F2CRequest) -> dict:
        return {
            "robot_width_m": request.robot_width_m,
            "working_width_m": request.working_width_m,
            "min_turning_radius_m": request.min_turning_radius_m,
            "headland_width_m": request.headland_width_m,
            "swath_angle_rad": request.swath_angle_rad,
            "route_algorithm": request.route_algorithm,
        }

    def _run_chain(self, request: F2CRequest) -> dict:
        if not self.available():
            raise F2CUnavailableError("fields2cover Python binding 未安装")
        import fields2cover as f2c

        polygon = shapely.from_wkt(request.field_wkt)
        if polygon.geom_type != "Polygon":
            raise ValueError("PythonBindingAdapter 当前只接受单 Polygon WKT；多 cell 请在上层逐 cell 对账")
        try:
            return f2c_chain.run_chain(f2c, polygon, self._params(request))
        except f2c_chain.F2CChainError as error:
            # 链路模块不认识仓库的异常类型（它刻意不 import agriautolab），在这里翻译。
            message = str(error)
            if "route_algorithm" in message:
                raise RouteAlgorithmMismatchError(message) from error
            raise F2CSchemaError(message) from error

    def run(self, request: F2CRequest) -> F2CResult:
        scalars = self._run_chain(request)["scalars"]
        return F2CResult(
            request_id=request.request_id,
            **scalars,
            # F2C 直接吃传入坐标、不做投影，所以它干活的投影就是请求声明的那个。
            # 这里是执行端的如实回报，不是把请求抄一遍——换个会自投影的适配器就该写别的值。
            working_crs=request.working_crs,
            route_algorithm=request.route_algorithm,
        )

    def route_identity(self, request: F2CRequest) -> dict:
        """吐出 F2C 实际的 swath 访问顺序与几何，供任务 3 的验收复现用。

        存在的理由：上一轮只有 bracket（相邻 −38.11% / 隔行 +31.04%），
        那只证明 F2C 落在两者之间，不构成身份证明——同样兼容
        「RP_Snake 带 skip 参数」「Robot 宽度参与转移几何」「路径含进出腿」等解释。
        身份只能由 F2C 自己吐出的顺序 + 几何来定。
        """
        identity = self._run_chain(request)["route_identity"]
        return {"request_id": request.request_id, **identity}
