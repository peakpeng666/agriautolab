"""Buffer 圆弧的离散 π 常量。

QUAD_SEGS 近似下的圆弧是内接正多边形，不是连续弧；凡断言落在被 buffer 圆角化过的
几何上的解析真值，必须用 π_discrete，用 math.pi 必然对不上。

公式：内接正 n 边形面积 = 0.5·n·sin(2π/n)，n = 4·QUAD_SEGS（一个整圆由四个象限、
每象限 QUAD_SEGS 段组成）。Block A 两次实测踩坑：
反曲顶点 round−mitre 面积差 = w²·(1 − π_d/4) = 7.771064（连续值 7.725666 对不上）；
障碍环带假阳性 = 周长·w + π_d·w² = 472.9157。

注意：Dubins 曲线的弧长是解析量（angle·R），与 buffer 无关——那些断言仍用 math.pi。
"""

import math

from agriautolab.geometry.footprint import QUAD_SEGS

PI_DISCRETE = 0.5 * (4 * QUAD_SEGS) * math.sin(2.0 * math.pi / (4 * QUAD_SEGS))
