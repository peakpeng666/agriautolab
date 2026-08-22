#!/usr/bin/env bash
# 一键安装主入口（WSL2 Ubuntu 22.04）。幂等：连跑两次结果相同。
# 用法：bash scripts/install/setup_wsl.sh
# 四条验收定义（缺一不算一键）：幂等 / 自校验 / 全钉死 / 失败要吵。
set -euo pipefail

cd "$(dirname "$0")/../.."   # 仓库根
REPO_ROOT="$(pwd)"
INSTALL_DIR="$REPO_ROOT/scripts/install"

echo "== AgriAutoLab 一键安装（WSL2 Ubuntu 22.04）=="

# 0) 环境预检（警告但不拦截，除非致命）
if [ -n "${WSL_DISTRO_NAME:-}" ] || grep -qi microsoft /proc/version 2>/dev/null; then
  echo "  运行在 WSL2 内 ✓"
else
  echo "  ⚠️ 未检测到 WSL2。本流程仅在 WSL2 Ubuntu 22.04 验证过。" >&2
fi
UBUNTU_VER="$(lsb_release -rs 2>/dev/null || echo unknown)"
if [ "$UBUNTU_VER" = "22.04" ]; then
  echo "  Ubuntu 22.04 ✓"
else
  echo "  ⚠️ 当前为 Ubuntu ${UBUNTU_VER}，仅在 22.04 验证过（apt 包版本可能不同）。" >&2
fi
case "$REPO_ROOT" in
  /mnt/*) echo "  ⚠️ 仓库在 /mnt/ 下（Windows 盘，9P 协议）：小文件 I/O 慢一到两个数量级，" >&2
          echo "     checkpoint 每行 fsync 的全量运行会被文件系统吃掉。强烈建议迁到原生盘：" >&2
          echo "     git clone <repo> ~/agriautolab && cd ~/agriautolab" >&2 ;;
  *) echo "  原生文件系统 ✓" ;;
esac
export LANG="${LANG:-C.UTF-8}"
if ! locale 2>/dev/null | grep -qi "utf-8"; then
  echo "  ⚠️ locale 非 UTF-8（中文输出可能 UnicodeEncodeError）；已导出 LANG=C.UTF-8" >&2
  export LANG=C.UTF-8
fi

# 1) apt 系统依赖
bash "$INSTALL_DIR/01_apt.sh"

# 2) Fields2Cover 源码构建（固定 commit，幂等）
bash "$INSTALL_DIR/02_fields2cover.sh"

# 3) Python venv + 锁定版本
bash "$INSTALL_DIR/03_python.sh"

# 4) 自校验
bash "$INSTALL_DIR/verify_install.sh"

echo "== 安装完成。激活：source .venv/bin/activate =="
