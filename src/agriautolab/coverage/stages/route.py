"""按法向坐标排序逐条访问 swath，方向交替。"""

from __future__ import annotations

import math

from agriautolab.contracts.artifacts import RouteArtifact, Swath, SwathsArtifact, SwathTraversal
from agriautolab.contracts.enums import SwathDirection


def _midpoint(swath: Swath) -> tuple[float, float]:
    first = swath.centerline.points[0]
    last = swath.centerline.points[-1]
    return ((first.x + last.x) / 2.0, (first.y + last.y) / 2.0)


class BoustrophedonRoute:
    algorithm_id = "boustrophedon_route"

    def run(self, artifact: SwathsArtifact) -> RouteArtifact:
        if not artifact.swaths:
            return RouteArtifact(traversals=(), swaths=())
        first_line = artifact.swaths[0].centerline.points
        dx = first_line[-1].x - first_line[0].x
        dy = first_line[-1].y - first_line[0].y
        norm = math.hypot(dx, dy)
        nx, ny = -dy / norm, dx / norm
        swaths = tuple(sorted(artifact.swaths, key=lambda swath: (_midpoint(swath)[0] * nx + _midpoint(swath)[1] * ny, swath.swath_id)))
        traversals = tuple(
            SwathTraversal(
                swath_id=swath.swath_id,
                direction=SwathDirection.FORWARD if index % 2 == 0 else SwathDirection.REVERSE,
            )
            for index, swath in enumerate(swaths)
        )
        return RouteArtifact(traversals=traversals, swaths=swaths)



# 类名按农业 CPP 文献的术语取作 Boustrophedon；SnakeRoute 是同一个类的别名，
# 保留它是因为流水线配置里的 algorithm_id 用的就是 snake_route 这个字符串。
SnakeRoute = BoustrophedonRoute
