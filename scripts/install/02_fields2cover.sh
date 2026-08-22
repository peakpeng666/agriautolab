#!/usr/bin/env bash
# Fields2Cover 源码构建（固定 commit 3613525c）。幂等：产物存在且 commit 匹配则跳过。
# OR-Tools 9.9.3963 由 F2C 的 FetchContent 按 SHA256 拉取（cmake/F2CUtils.cmake），
# 不走 apt。构建含 OR-Tools 编译，首次约 20-40 分钟——没卡死，只是慢。
set -euo pipefail

F2C_COMMIT="3613525c241538fa9fd9df3e1209ae8184627958"
F2C_DIR="$HOME/Fields2Cover"
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
ENV_JSON="$REPO_ROOT/evidence/env_f2c.json"

# 幂等判据：git 工作树存在 + HEAD 匹配 + binding 可 import
if [ -d "$F2C_DIR/.git" ]; then
  CURRENT="$(git -C "$F2C_DIR" rev-parse HEAD)"
  if [ "$CURRENT" = "$F2C_COMMIT" ] && python3 -c "import fields2cover" >/dev/null 2>&1; then
    echo "  [02_f2c] Fields2Cover@$CURRENT 已构建且 binding 可用（跳过）✓"
  else
    echo "  [02_f2c] commit 或 binding 不匹配（HEAD=$CURRENT），重 checkout 构建"
    git -C "$F2C_DIR" fetch --depth 1 origin "$F2C_COMMIT" || true
    git -C "$F2C_DIR" checkout "$F2C_COMMIT"
    _build=1
  fi
else
  git clone --depth 1 https://github.com/Fields2Cover/Fields2Cover "$F2C_DIR"
  git -C "$F2C_DIR" fetch --depth 1 origin "$F2C_COMMIT"
  git -C "$F2C_DIR" checkout "$F2C_COMMIT"
  _build=1
fi

if [ -n "${_build:-}" ] || [ ! -f "$F2C_DIR/build/install_manifest.txt" ]; then
  echo "  [02_f2c] 构建（Release + BUILD_PYTHON）。OR-Tools 首次要编译，预计 20-40 分钟。"
  cmake -S "$F2C_DIR" -B "$F2C_DIR/build" -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF
  cmake --build "$F2C_DIR/build" -j"$(nproc)"
  sudo cmake --install "$F2C_DIR/build"
  sudo ldconfig
fi

python3 -c "import fields2cover" || {
  echo "❌ F2C 构建完成但 binding 不可 import。检查 /usr/lib/python3/dist-packages/fields2cover.py 是否生成" >&2
  exit 1
}

# 环境指纹：commit / SWIG / python / OR-Tools 实际版本 → evidence/env_f2c.json
ORTOOLS="unavailable"
for f in /usr/local/lib/cmake/ortools/OrToolsConfigVersion.cmake /usr/local/lib/cmake/ortools/ortools-config-version.cmake; do
  [ -f "$f" ] && ORTOOLS="$(grep -o 'PACKAGE_VERSION "[^"]*"' "$f" | head -1 | cut -d'"' -f2)" && break
done
mkdir -p "$(dirname "$ENV_JSON")"
cat > "$ENV_JSON" <<JSON
{
  "fields2cover_source": "HEAD@${F2C_COMMIT} (2025-04-23)",
  "swig": "$(swig -version | head -3 | tr '\n' ' ' | sed 's/  */ /g')",
  "python": "$(python3 -V 2>&1 | cut -d' ' -f2)",
  "ortools": "${ORTOOLS}",
  "platform": "$(uname -a)",
  "fields2cover_binding": "$(python3 -c 'import fields2cover, inspect; print(inspect.getfile(fields2cover))')"
}
JSON
echo "  [02_f2c] 环境指纹 -> $ENV_JSON（其内容哈希已在证据链：RecordedCsvAdapter.env_hash）"
