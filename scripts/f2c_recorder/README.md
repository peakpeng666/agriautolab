# F2C 录制壳

在 **WSL / python3.10** 上录制 golden；agriautolab 本体在 **Windows / python3.11+** 上被测。

## 为什么是两个进程

F2C 的 Python binding 由 SWIG 绑在 WSL 的 `python3.10`；agriautolab 要求 3.11+
（`src/agriautolab/contracts/geometry.py` 用了 `typing.Self`）。

**不要为此重建 binding，也不要给仓库降级。** 两进程是既定架构，
Block C 的三适配器设计（binding / subprocess / recorded CSV）就是为它准备的：

```
WSL / py3.10                          Windows / py3.11+
────────────────                      ─────────────────
scripts/f2c_recorder  ──emit──>  golden_f2c.csv  ──read──>  RecordedCsvAdapter
（不 import agriautolab）        golden_route.json          （仓库内，被测）
```

本目录下的脚本**只依赖 python3.10 + fields2cover + shapely**，
不 import 任何 agriautolab 内容。链路实现按文件路径加载
`src/agriautolab/cross_validation/f2c_chain.py` —— 那个模块同样不 import agriautolab、
只用 3.10 兼容语法，因此录制壳与 `PythonBindingAdapter` **共用同一份链路实现**，
等价性由构造保证，不靠事后比对两份输出。

已知会踩的坑：直接跑 `scripts/record_f2c_golden.py`（旧脚本）在 py3.10 上会
`ImportError: cannot import name 'Self' from 'typing'` —— 那条路径 import 了 agriautolab 包。
用本目录的 `record_golden.py`。

## 复现命令（WSL 内，逐字可粘贴）

仓库经 `/mnt/d` 挂载。以下把 `REPO` 与 `WORK` 设成你自己的路径。

```bash
export REPO=/mnt/d/Peak/Desktop/URP/agriautolab-blockC/agriautolab-blockC
export WORK=/mnt/d/Peak/Desktop/URP/o2_workspace
```

### 1. 环境指纹（先录，它要进证据链）

```bash
python3 "$REPO/scripts/f2c_recorder/env_probe.py" --output "$WORK/env_f2c.json" --f2c-source "$HOME/Fields2Cover"
```

`--f2c-source` 指向 F2C 的 git 工作树；没有工作树时该字段记为 `unavailable: ...`，
**不会伪造一个 commit**。

### 2. 录 golden

```bash
python3 "$REPO/scripts/f2c_recorder/record_golden.py" --requests "$WORK/requests_metric.json" --output "$WORK/golden_f2c.csv" --route-output "$WORK/golden_route.json"
```

请求清单里每条必须带 `working_crs` 与 `route_algorithm`；缺一个就中止，不填默认值。
清单由 Windows 侧的 `scripts/build_f2c_requests.py` 生成。

### 3. 从 Windows 侧一键调用（可选）

```bash
python -c "from agriautolab.cross_validation.f2c import SubprocessAdapter; print(SubprocessAdapter.wsl_command('/mnt/d/.../record_golden.py'))"
```

`SubprocessAdapter(wsl_command=...)` 会用 `wsl.exe -e python3 ...` 跨过去调用，
Windows 路径自动转 `/mnt/`。

## 输出

| 文件 | 内容 |
|---|---|
| `golden_f2c.csv` | 13 列，schema 与 `RecordedCsvAdapter` 锁死 |
| `golden_route.json` | 每条请求的 swath 访问顺序与端点几何 |
| `env_f2c.json` | F2C commit / SWIG / python / OR-Tools 指纹 |

`golden_route.json` 的用途是**身份证明**：上一轮只有 bracket（我方相邻 −38.11% /
隔行 +31.04%），那只说明 F2C 落在两者之间，不构成身份。实测 `RP_Snake` 的访问顺序是
`[0,2,4,…,20,19,17,…,3,1]`（偶数升序 + 奇数降序回扫），`RP_Boustrophedon` 才是
我方 `boustrophedon_order` 的配对方。
