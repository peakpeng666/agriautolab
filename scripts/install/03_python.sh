#!/usr/bin/env bash
# 封闭 venv + 锁定版本 + F2C binding 拷入。
# 为什么封闭（--system-site-packages 的反例，实测踩坑记录）：
#   系统 dist-packages 的 pytest-cov.pth 在解释器启动时注入旧钩子（6.2.5 签名），
#   与 venv 的 pytest 9 冲突且 -p no: 屏蔽不住。封闭 venv 对一切系统 .pth 地雷免疫。
#   F2C binding 以拷贝方式进 venv（fields2cover.py + _fields2cover_python.so），
#   其依赖的 libFields2Cover.so 在 /usr/local/lib，由 ldconfig 解析。
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

python3 -m venv .venv
.venv/bin/pip install --quiet --timeout 120 --retries 5 -r scripts/install/requirements.lock
.venv/bin/pip install --quiet -e .

# F2C binding 拷入（幂等）
SITE="$(.venv/bin/python -c 'import site; print(site.getsitepackages()[0])')"
for f in fields2cover.py _fields2cover_python.so; do
  SRC="/usr/lib/python3/dist-packages/$f"
  if [ -f "$SRC" ]; then
    cmp -s "$SRC" "$SITE/$f" || cp "$SRC" "$SITE/$f"
  else
    echo "❌ 缺 $SRC：先跑 02_fields2cover.sh" >&2
    exit 1
  fi
done
echo "  [03_python] venv 就绪（封闭 + F2C binding 已拷入）✓"
