#!/usr/bin/env bash
# 系统依赖（apt）。幂等：已装的跳过。
# 需要 sudo；无密码 sudo 缺失时给出可操作错误而不是半成功。
set -euo pipefail

if ! command -v sudo >/dev/null 2>&1; then
  echo "❌ 缺 sudo。以 root 运行本脚本，或先：apt-get install -y sudo 并把用户加入 sudo 组" >&2
  exit 1
fi
if ! sudo -n true 2>/dev/null && ! sudo -S true </dev/null 2>/dev/null; then
  :   # 交互式 sudo 可用，正常
fi

PACKAGES=(
  build-essential ca-certificates cmake doxygen g++ git
  libeigen3-dev libgdal-dev libpython3-dev python3 python3-pip python3-venv
  python3-matplotlib python3-tk lcov libgtest-dev libtbb-dev swig
  libgeos-dev gnuplot libtinyxml2-dev nlohmann-json3-dev
)
# 逐包检查，输出哪些缺失；全在则直接通过（幂等的关键）
MISSING=()
for p in "${PACKAGES[@]}"; do
  dpkg -s "$p" >/dev/null 2>&1 || MISSING+=("$p")
done
if [ "${#MISSING[@]}" -eq 0 ]; then
  echo "  [01_apt] 全部系统依赖已在（跳过 apt）✓"
else
  echo "  [01_apt] 缺 ${#MISSING[@]} 个包：${MISSING[*]}"
  sudo apt-get update
  sudo apt-get install -y --no-install-recommends "${MISSING[@]}"
fi

# 坑：系统 python3-pytest-cov 的 .pth 会在解释器启动时注入旧钩子，
# 与 venv 里的新 pytest 冲突（实测 6.2.5 的钩子签名炸 9.x）。
# 封闭 venv 方案（03_python.sh）天然免疫；此处检测并提示，不静默。
if [ -f /usr/lib/python3/dist-packages/pytest-cov.pth ]; then
  echo "  [01_apt] 注意：系统存在 pytest-cov.pth（对封闭 venv 无害，已免疫）"
fi
