"""沿最小旋转外接矩形的最长边，按幅宽间距生成 swath 中心线。"""

from __future__ import annotations

import math

from shapely import LineString
from shapely.geometry.base import BaseGeometry

from agriautolab.contracts.artifacts import HeadlandArtifact, Swath, SwathsArtifact
from agriautolab.geometry.validate import line_to_spec, polygon_from_spec


def _line_parts(geometry: BaseGeometry) -> tuple[LineString, ...]:
    if geometry.is_empty:
        return ()
    if geometry.geom_type == "LineString":
        return (geometry,)
    if geometry.geom_type == "MultiLineString":
        return tuple(geometry.geoms)
    if geometry.geom_type == "GeometryCollection":
        return tuple(part for part in geometry.geoms if part.geom_type == "LineString")
    return ()


def _unit_longest_edge(polygon: BaseGeometry) -> tuple[float, float]:
    rectangle = polygon.minimum_rotated_rectangle
    coords = list(rectangle.exterior.coords)[:4]
    edges = []
    for start, end in zip(coords, coords[1:] + coords[:1]):
        dx, dy = end[0] - start[0], end[1] - start[1]
        length = math.hypot(dx, dy)
        edges.append((length, dx / length, dy / length))
    _, ux, uy = max(edges, key=lambda item: (item[0], abs(item[1]), abs(item[2])))
    if ux < 0.0 or (ux == 0.0 and uy < 0.0):
        ux, uy = -ux, -uy
    return ux, uy


class MBRDirectionSwath:
    algorithm_id = "mbr_direction_swath"

    def run(self, headland: HeadlandArtifact, *, working_width_m: float) -> SwathsArtifact:
        if working_width_m <= 0.0:
            raise ValueError("working width must be greater than 0")
        output: list[Swath] = []
        serial = 0
        # 主田可能被障碍夹断成多片：逐片扫掠，每片各自定方向、各自排条数。
        for headland_cell in headland.cells:
          for main_spec in headland_cell.main_field:
            main = polygon_from_spec(main_spec)
            ux, uy = _unit_longest_edge(main)
            nx, ny = -uy, ux
            coords = list(main.exterior.coords)
            u_values = [x * ux + y * uy for x, y in coords]
            n_values = [x * nx + y * ny for x, y in coords]
            u_min, u_max = min(u_values), max(u_values)
            n_min, n_max = min(n_values), max(n_values)
            span = n_max - n_min
            count = max(1, math.ceil(span / working_width_m))
            if count == 1:
                centers = [(n_min + n_max) / 2.0]
            else:
                centers = [n_min + working_width_m / 2.0 + index * working_width_m for index in range(count)]
                centers[-1] = min(centers[-1], n_max - working_width_m / 2.0)
            extension = max(working_width_m, u_max - u_min, 1.0)
            for center in centers:
                start = ((u_min - extension) * ux + center * nx, (u_min - extension) * uy + center * ny)
                end = ((u_max + extension) * ux + center * nx, (u_max + extension) * uy + center * ny)
                intersection = main.intersection(LineString([start, end]))
                parts = sorted(
                    _line_parts(intersection),
                    key=lambda line: (
                        line.centroid.x * nx + line.centroid.y * ny,
                        min(point[0] * ux + point[1] * uy for point in line.coords),
                    ),
                )
                for part in parts:
                    coords_part = list(part.coords)
                    if coords_part[0][0] * ux + coords_part[0][1] * uy > coords_part[-1][0] * ux + coords_part[-1][1] * uy:
                        part = LineString(list(reversed(coords_part)))
                    swath_id = f"swath-{serial:04d}"
                    output.append(
                        Swath(
                            swath_id=swath_id,
                            centerline=line_to_spec(part, swath_id),
                            width_m=working_width_m,
                        )
                    )
                    serial += 1
        return SwathsArtifact(swaths=tuple(output))



# 陷阱：别名叫 LongestEdgeSwath，但主方向取自最小旋转外接矩形，不是直接挑多边形最长的那条边。
# 凸多边形上两者一致，凹多边形上会给出不同方向。保留别名是因为 algorithm_id 用的是 longest_edge_swath。
LongestEdgeSwath = MBRDirectionSwath
