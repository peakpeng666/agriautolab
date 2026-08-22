"""顺序访问：按 swath 序号 0,1,2,... 交替方向，即经典牛耕式。"""

import math

from agriautolab.contracts.artifacts import RouteArtifact, SwathsArtifact, SwathTraversal
from agriautolab.contracts.enums import SwathDirection


def _normal_axis(swaths) -> tuple[float, float]:
    first = swaths[0].centerline.points
    dx = first[-1].x - first[0].x
    dy = first[-1].y - first[0].y
    norm = math.hypot(dx, dy)
    return -dy / norm, dx / norm


class BoustrophedonOrder:
    algorithm_id = "boustrophedon_order"

    def run(self, artifact: SwathsArtifact) -> RouteArtifact:
        if not artifact.swaths:
            return RouteArtifact(traversals=(), swaths=())
        nx, ny = _normal_axis(artifact.swaths)

        def order_key(swath):
            midpoint = swath.centerline.points[0], swath.centerline.points[-1]
            value = ((midpoint[0].x + midpoint[1].x) / 2.0) * nx + ((midpoint[0].y + midpoint[1].y) / 2.0) * ny
            return (value, swath.swath_id)

        swaths = tuple(sorted(artifact.swaths, key=order_key))
        traversals = tuple(
            SwathTraversal(
                swath_id=swath.swath_id,
                direction=SwathDirection.FORWARD if index % 2 == 0 else SwathDirection.REVERSE,
            )
            for index, swath in enumerate(swaths)
        )
        return RouteArtifact(traversals=traversals, swaths=swaths)
