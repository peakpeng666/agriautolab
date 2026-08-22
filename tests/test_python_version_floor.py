"""Python 版本下限契约。

为什么是 3.10 而不是 3.11：Ubuntu 22.04 LTS 的系统 Python 是 3.10.12，
Fields2Cover 的 SWIG binding 绑在系统解释器上。为了让 F2C 与本项目在
同一解释器下可用，下限锁 3.10；升到 3.11+ 会导致 binding 不可见——
这不是"顺手升级"能改的。>=3.10 是下限不是钉死，3.11/3.12 照常可跑。
"""

import sys


def test_python_version_floor_is_3_10() -> None:
    assert sys.version_info >= (3, 10)
