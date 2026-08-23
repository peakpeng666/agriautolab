"""恒等地头：主田 = 原田，不发生任何内缩。"""

from agriautolab.contracts.problem import CoverageProblem


class NoHeadland:
    algorithm_id = "no_headland"

    def run(self, problem: CoverageProblem):
        """返回 None 是语义，不是缺省值。

        契约层的 resolve_coverage_targets 把 headland=None 定义为「本次运行
        没跑地头，主田即原田」；而空环带在 PolygonSpec 里不可表示
        （validate_geometry 拒绝空几何），所以「恒等地头」的唯一规范表示就是 None。
        申报宽度与恒等产物也不可能在逐 cell 重算对账下同时成立——
        声明了宽度却没有环带会被 CoverageTargets 直接拒绝。
        """
        return None
