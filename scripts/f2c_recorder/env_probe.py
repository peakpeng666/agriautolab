#!/usr/bin/env python3
"""录制环境指纹：F2C commit、SWIG 版本、python 版本、OR-Tools 版本。

**只依赖 python3.10 标准库，不 import agriautolab。**

存在的理由：换了 F2C 版本，golden 就不是同一份 golden。
env_f2c.json 必须进证据链哈希（见 evidence/record.py 的 f2c_env_hash），
否则「同一份 golden」这句话在证据层无法证伪。
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import platform
import subprocess


def run(command, cwd=None):
    try:
        completed = subprocess.run(
            command, cwd=cwd, capture_output=True, text=True, timeout=60,
        )
    except (OSError, subprocess.SubprocessError) as error:
        return "unavailable: %s" % error
    if completed.returncode != 0:
        return "unavailable: exit %d %s" % (completed.returncode, completed.stderr.strip()[:120])
    return completed.stdout.strip()


def fields2cover_source(source_dir):
    if not source_dir or not os.path.isdir(os.path.join(source_dir, ".git")):
        return "unavailable: 未提供 --f2c-source 或不是 git 工作树"
    commit = run(["git", "rev-parse", "HEAD"], cwd=source_dir)
    date = run(["git", "show", "-s", "--format=%cs", "HEAD"], cwd=source_dir)
    branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=source_dir)
    return "%s@%s (%s)" % (branch, commit, date)


def binding_location():
    spec = importlib.util.find_spec("fields2cover")
    if spec is None:
        return "unavailable: fields2cover 未安装"
    return spec.origin or "unavailable: 无 origin"


def ortools_version():
    spec = importlib.util.find_spec("ortools")
    if spec is None:
        return "unavailable: ortools 未安装（F2C 可能静态链接了 OR-Tools）"
    try:
        import ortools  # noqa: PLC0415  运行期探测，不能在顶层 import

        return getattr(ortools, "__version__", "installed, 无 __version__")
    except ImportError as error:
        return "unavailable: %s" % error


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--f2c-source", default=os.environ.get("F2C_SOURCE_DIR", ""))
    args = parser.parse_args()
    payload = {
        "fields2cover_source": fields2cover_source(args.f2c_source),
        "fields2cover_binding": binding_location(),
        "swig": run(["swig", "-version"]).replace("\n", " ").strip(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "ortools": ortools_version(),
    }
    with open(args.output, "w", encoding="utf-8") as handle:
        # sort_keys：这份 JSON 要进内容哈希，键序不能影响哈希。
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
    for key in sorted(payload):
        print("%-24s %s" % (key, payload[key]))
    print("env fingerprint -> %s" % args.output)


if __name__ == "__main__":
    main()
