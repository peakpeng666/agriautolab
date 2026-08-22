"""隔行访问：0,2,4,...,1,3,5,...（真实农机技术）。

R > w/2（转弯半径超过半个幅宽）时，相邻 swath 间的鱼尾掉头需要倒车或大回转；
隔一行访问把掉头换成跨一条 swath 的平移，收获后的地块上这是标准作业法。
"""

from agriautolab.contracts.artifacts import RouteArtifact, SwathsArtifact, SwathTraversal
from agriautolab.contracts.enums import SwathDirection


class SkipOneOrder:
    algorithm_id = "skip_one_order"

    def run(self, artifact: SwathsArtifact) -> RouteArtifact:
        swaths = tuple(sorted(artifact.swaths, key=lambda swath: swath.swath_id))
        even_indices = tuple(index for index in range(len(swaths)) if index % 2 == 0)
        odd_indices = tuple(index for index in range(len(swaths)) if index % 2 == 1)
        traversals = []
        for pass_index, indices in enumerate((even_indices, odd_indices)):
            for position, swath_index in enumerate(indices):
                # 每一轮内部仍交替方向：同轮内相邻访问隔了一条 swath，
                # 方向交替保证转移平移方向一致，不产生额外对折。
                forward = position % 2 == 0
                traversals.append(
                    SwathTraversal(
                        swath_id=swaths[swath_index].swath_id,
                        direction=SwathDirection.FORWARD if forward else SwathDirection.REVERSE,
                    )
                )
        return RouteArtifact(traversals=tuple(traversals), swaths=swaths)
