# 一键安装（WSL2 Ubuntu 22.04）

## 完整流程（逐字可粘贴）

```bash
# 前置：Windows 上装好 WSL2 的 Ubuntu 22.04（wsl --install -d Ubuntu-22.04）
wsl -d Ubuntu-22.04
git clone https://github.com/peakpeng666/agriautolab.git ~/agriautolab
cd ~/agriautolab
bash scripts/install/setup_wsl.sh        # 一条命令；含 F2C 源码构建，首次 20-40 分钟
source .venv/bin/activate
python -m pytest -q                       # 预期 546 passed / 30 skipped
```

`setup_wsl.sh` 幂等：连跑两次，第二次全部跳过不重装。逐项自校验用
`bash scripts/install/verify_install.sh`（任何 ❌ 退出码非 0 并给修复命令）。

## 四条验收定义

1. **幂等**：apt 逐包 dpkg -s 检查；F2C 按 commit + import 双判据跳过；venv/binding 按内容跳过
2. **自校验**：`verify_install.sh` 逐项 ✅/❌（Ubuntu/Python/locale/原生盘/GEOS/lock/F2C/CRLF/全量测试）
3. **全钉死**：apt 包清单固定；F2C commit `3613525c` 固定；OR-Tools 9.9.3963 由 F2C FetchContent
   按 SHA256 拉取；Python 3.10.12（系统）；pip 版本见 `requirements.lock`；
   **GEOS 3.13.1** 见 `evidence/env_geometry.json`（换 GEOS = 换引擎，解析真值须重验）
4. **失败要吵**：每一步失败都打印缺什么、用什么命令装；半成功比失败更坏

## 关键设计决定（为什么这样装）

| 决定 | 理由 |
|---|---|
| 仓库与数据放 WSL 原生盘（~/） | /mnt/（Windows 盘）走 9P，小文件 I/O 慢一到两个数量级；checkpoint 每行 fsync 的全量运行尤其受害。代码 `~/agriautolab`，数据产物 `~/agriautolab-data/`，跨盘只在交付时 cp 一次 |
| **封闭 venv**（非 --system-site-packages） | 实测踩坑：系统 `pytest-cov.pth` 在解释器启动时注入旧钩子（6.2.5 签名）炸掉 venv 的 pytest 9，`-p no:` 屏蔽不住。F2C binding 用拷贝方式进 venv（fields2cover.py + _fields2cover_python.so），其 libFields2Cover.so 由 ldconfig 解析 |
| Python 3.10（系统自带） | F2C 的 SWIG binding 绑系统解释器；下限锁 3.10 让两者同解释器可用。>=3.10 是下限不是钉死 |
| numpy 3.10 上锁 2.2.6 | numpy 2.4.4 无 cp310 wheel；numpy 版本不影响几何结果（GEOS 才影响，两侧同为 3.13.1） |

## 产物位置

- F2C 源码：`~/Fields2Cover`（commit 3613525c）
- F2C 库：`/usr/local/lib/libFields2Cover.so`；binding：venv `site-packages/`（拷贝自系统 dist-packages）
- OR-Tools 9.9.3963：`/usr/local/`（F2C FetchContent 拉，版本记入 `evidence/env_f2c.json`）
- 环境指纹：`evidence/env_f2c.json`（F2C/SWIG/python/OR-Tools，内容哈希进证据链）+
  `evidence/env_geometry.json`（shapely/GEOS，解析真值的引擎契约）
