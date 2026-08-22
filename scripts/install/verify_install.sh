#!/usr/bin/env bash
# 安装自校验：逐项 ✅/❌，任何一项失败退出码非 0 并给修复命令。
set -uo pipefail   # 不用 -e：逐项检查要自己控退出码

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"
FAIL=0
ok()   { echo "  ✅ $1"; }
bad()  { echo "  ❌ $1"; echo "     修复：$2" >&2; FAIL=1; }

# 1 Ubuntu 版本
V="$(lsb_release -rs 2>/dev/null || echo unknown)"
[ "$V" = "22.04" ] && ok "Ubuntu 22.04" || ok "Ubuntu $V（⚠️ 仅 22.04 验证过，继续）"

# 2 Python
PY="$( .venv/bin/python -c 'import sys; print("%d.%d.%d" % sys.version_info[:3])' 2>/dev/null || echo missing)"
[ "$PY" = "3.10.12" ] && ok "Python 3.10.12" \
  || { [ "$PY" = "missing" ] && bad "venv 缺失（$PY）" "bash scripts/install/03_python.sh" \
       || ok "Python $PY（非 3.10.12，仅参考）"; }

# 3 locale
locale 2>/dev/null | grep -qi "utf-8" && ok "LANG 含 UTF-8（当前 ${LANG:-unset}）" \
  || bad "locale 无 UTF-8" "export LANG=C.UTF-8 并重试；或 sudo locale-gen C.UTF-8"

# 4 不在 /mnt/ 下
case "$PWD" in /mnt/*) bad "仓库在 /mnt/（9P 慢盘）" "git clone <repo> ~/agriautolab && cd ~/agriautolab" ;;
                   *) ok "原生文件系统" ;; esac

# 5 shapely/GEOS 与 env_geometry.json 一致
GEOSCHECK="$(.venv/bin/python - <<'PY' 2>&1
import json, pathlib, shapely
payload = json.loads(pathlib.Path("evidence/env_geometry.json").read_text(encoding="utf-8"))
verified = {i["geos_version_string"] for i in payload["verified"]}
print("MATCH" if shapely.geos_version_string in verified else "MISMATCH:" + shapely.geos_version_string + " not in " + ",".join(sorted(verified)))
PY
)"
case "$GEOSCHECK" in
  MATCH) ok "shapely $(.venv/bin/python -c 'import shapely;print(shapely.__version__)') / GEOS $(.venv/bin/python -c 'import shapely;print(shapely.geos_version_string)')（与 env_geometry.json 一致）" ;;
  *) bad "GEOS 不在已验证集合：$GEOSCHECK" "解析真值须在本引擎重跑验证（tests/test_geometry_engine.py 会警告）" ;;
esac

# 6 依赖版本与 lock 一致
LOCKBAD="$(.venv/bin/pip freeze 2>/dev/null | sort > /tmp/_fz.txt; grep -oE '^[a-zA-Z0-9_-]+==[^ ]+' scripts/install/requirements.lock | sort | while read -r line; do
  grep -qi "^${line%%==*}==" /tmp/_fz.txt || echo "$line 缺失"; grep -qi "^${line%%==*}==" /tmp/_fz.txt && ! grep -qi "^$line\$" /tmp/_fz.txt && echo "$line 版本不符"; done)"
[ -z "$LOCKBAD" ] && ok "pip 依赖与 requirements.lock 一致" || bad "依赖偏离 lock：$LOCKBAD" "bash scripts/install/03_python.sh"

# 7 fields2cover 可 import 且 commit 匹配
if .venv/bin/python -c "import fields2cover" 2>/dev/null; then
  HEAD="$(git -C "$HOME/Fields2Cover" rev-parse HEAD 2>/dev/null || echo none)"
  [ "$HEAD" = "3613525c241538fa9fd9df3e1209ae8184627958" ] \
    && ok "import fields2cover 成功，commit=3613525c…" \
    || bad "F2C commit=$HEAD（应为 3613525c…）" "bash scripts/install/02_fields2cover.sh"
else
  bad "import fields2cover 失败" "bash scripts/install/02_fields2cover.sh"
fi

# 8 无 CRLF 文件
CRLF_FILES="$(grep -rlIU $'\r' --include='*.sh' --include='*.py' --include='*.json' src scripts tests configs prereg 2>/dev/null | head -3)"
[ -z "$CRLF_FILES" ] && ok "无 CRLF 文件（.gitattributes eol=lf）" \
  || bad "CRLF 文件：$CRLF_FILES" "git add --renormalize . && git checkout -- ."

# 9 全量测试（解析真值随之复验）
if .venv/bin/python -m pytest -q >/tmp/_pytest.log 2>&1; then
  ok "pytest -q → $(tail -1 /tmp/_pytest.log)"
else
  bad "pytest 失败：$(tail -5 /tmp/_pytest.log)" "查看 /tmp/_pytest.log；先修测试再谈复现"
fi

echo "——"
[ "$FAIL" -eq 0 ] && echo "全部通过 ✅" || { echo "存在 ❌，见上（退出码 1）"; exit 1; }
