"""把每个 cell 内缩成主田，外圈保留为地头环带。

陷阱：主田面积随地头宽度剧烈变化，绝不能拿它当覆盖率分母。
100x50 田块地头开到 18 米时主田只剩 896 m^2，对主田覆盖率满分而实际只覆盖了原田的 17.9%。
分母一律走 metrics.coverage.resolve_coverage_targets。
"""

from agriautolab.contracts.artifacts import CellsArtifact, HeadlandArtifact, HeadlandCell
from agriautolab.geometry.footprint import QUAD_SEGS
from agriautolab.geometry.validate import polygon_from_spec, polygon_parts_to_specs


class ConstantWidthHeadland:
    algorithm_id = "constant_width_headland"

    def __init__(self, width_m: float) -> None:
        if width_m <= 0.0:
            raise ValueError("地头宽度必须大于 0")
        self.width_m = width_m

    def run(self, cells: CellsArtifact) -> HeadlandArtifact:
        output: list[HeadlandCell] = []
        for cell_spec in cells.cells:
            cell = polygon_from_spec(cell_spec)
            main = cell.buffer(
                -self.width_m,
                cap_style="round",
                join_style="round",
                quad_segs=QUAD_SEGS,
            )
            if main.is_empty:
                raise ValueError(f"{cell_spec.geometry_id}: 地头宽度使 main_field 塌缩")
            headland = cell.difference(main)
            if headland.is_empty:
                raise ValueError(f"{cell_spec.geometry_id}: 内缩没有产生地头环带")
            # 含障碍地块上环带天然是多片（外圈 + 每个障碍周围一圈），
            # 主田也可能被障碍夹断——两者都走多部件转换，不再在这里抛「要求单 Polygon」。
            output.append(
                HeadlandCell(
                    cell_id=cell_spec.geometry_id,
                    main_field=polygon_parts_to_specs(main, f"{cell_spec.geometry_id}:main"),
                    headland=polygon_parts_to_specs(headland, f"{cell_spec.geometry_id}:headland"),
                )
            )
        return HeadlandArtifact(cells=tuple(output))
