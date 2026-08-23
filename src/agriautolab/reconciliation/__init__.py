"""reconciliation：与 Fields2Cover 的数值对账（cross_validation 的规范名）。

改名动机：cross_validation/ 里做的是外部库数值对账，不是机器学习交叉
验证；选择层（推荐器训练）将需要真正的分组 CV，名字必须让位。物理实现留在
cross_validation/（其中 f2c.py 为字节冻结适配器，原路径原字节永不动），
本包只提供规范 API 面：

    from agriautolab.reconciliation import native
    native.evaluate_native_pipeline(request)      # 规范名
    # 等价于 cross_validation.ours.compute_ours   # legacy 名
"""

from agriautolab.reconciliation import native

__all__ = ["native"]
