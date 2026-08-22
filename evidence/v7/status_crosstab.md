# config × 机具 × derived_status 交叉表（H1 前置）

行数 61100；derived_status 分歧：{'not_applicable->outside_area': 2020}

| 配置 | 机具 | 行数 | ok | ok% | 具名拒绝% | NA | 事实上出池(≥80%拒) |
|---|---:|---:|---:|---:|---:|---:|:--:|
| no_decomposition+uniform_headland+fixed_angle+boustrophedon_order+dubins_transit@8.0m/a=0.0000 | v0 | 2350 | 1420 | 60.4% | 39.6% | 0 |  |
| no_decomposition+uniform_headland+longest_edge+boustrophedon_order+dubins_transit@8.0m | v0 | 2350 | 1580 | 67.2% | 32.8% | 0 |  |
| no_decomposition+uniform_headland+row_aligned+boustrophedon_order+dubins_transit@8.0m | v0 | 2350 | 1478 | 62.9% | 37.1% | 0 |  |
| no_decomposition+uniform_headland+min_width+boustrophedon_order+dubins_transit@8.0m | v0 | 2350 | 1330 | 56.6% | 43.4% | 0 |  |
| no_decomposition+uniform_headland+principal_axis+boustrophedon_order+dubins_transit@8.0m | v0 | 2350 | 1300 | 55.3% | 44.7% | 0 |  |
| no_decomposition+uniform_headland+min_width+rural_postman_greedy+dubins_transit@8.0m | v0 | 2350 | 1610 | 68.5% | 31.5% | 0 |  |
| no_decomposition+uniform_headland+row_aligned+boustrophedon_order+reeds_shepp_transit@8.0m | v0 | 2350 | 0 | 0.0% | 0.0% | 2350 |  |
| boustrophedon_cells+uniform_headland+min_width+boustrophedon_order+dubins_transit@8.0m | v0 | 2350 | 560 | 23.8% | 5.5% | 1660 |  |
| no_decomposition+uniform_headland+row_aligned+skip_one_order+dubins_transit@8.0m | v0 | 2350 | 1342 | 57.1% | 42.9% | 0 |  |
| no_decomposition+uniform_headland+min_width+boustrophedon_order+dubins_transit@12.0m | v0 | 2350 | 1510 | 64.3% | 35.7% | 0 |  |
| no_decomposition+uniform_headland+min_width+skip_one_order+dubins_transit@8.0m | v0 | 2350 | 1240 | 52.8% | 47.2% | 0 |  |
| no_decomposition+uniform_headland+fixed_angle+boustrophedon_order+dubins_transit@8.0m/a=1.5708 | v0 | 2350 | 1490 | 63.4% | 36.6% | 0 |  |
| no_decomposition+no_headland+min_width+boustrophedon_order+reeds_shepp_transit | v0 | 2350 | 0 | 0.0% | 0.0% | 2350 |  |
| no_decomposition+uniform_headland+fixed_angle+boustrophedon_order+dubins_transit@8.0m/a=0.0000 | v1 | 2350 | 1410 | 60.0% | 40.0% | 0 |  |
| no_decomposition+uniform_headland+longest_edge+boustrophedon_order+dubins_transit@8.0m | v1 | 2350 | 1580 | 67.2% | 32.8% | 0 |  |
| no_decomposition+uniform_headland+row_aligned+boustrophedon_order+dubins_transit@8.0m | v1 | 2350 | 1470 | 62.5% | 37.5% | 0 |  |
| no_decomposition+uniform_headland+min_width+boustrophedon_order+dubins_transit@8.0m | v1 | 2350 | 1320 | 56.2% | 43.8% | 0 |  |
| no_decomposition+uniform_headland+principal_axis+boustrophedon_order+dubins_transit@8.0m | v1 | 2350 | 1290 | 54.9% | 45.1% | 0 |  |
| no_decomposition+uniform_headland+min_width+rural_postman_greedy+dubins_transit@8.0m | v1 | 2350 | 1620 | 68.9% | 31.1% | 0 |  |
| no_decomposition+uniform_headland+row_aligned+boustrophedon_order+reeds_shepp_transit@8.0m | v1 | 2350 | 1508 | 64.2% | 35.8% | 0 |  |
| boustrophedon_cells+uniform_headland+min_width+boustrophedon_order+dubins_transit@8.0m | v1 | 2350 | 560 | 23.8% | 5.5% | 1660 |  |
| no_decomposition+uniform_headland+row_aligned+skip_one_order+dubins_transit@8.0m | v1 | 2350 | 1340 | 57.0% | 43.0% | 0 |  |
| no_decomposition+uniform_headland+min_width+boustrophedon_order+dubins_transit@12.0m | v1 | 2350 | 1500 | 63.8% | 36.2% | 0 |  |
| no_decomposition+uniform_headland+min_width+skip_one_order+dubins_transit@8.0m | v1 | 2350 | 1230 | 52.3% | 47.7% | 0 |  |
| no_decomposition+uniform_headland+fixed_angle+boustrophedon_order+dubins_transit@8.0m/a=1.5708 | v1 | 2350 | 1480 | 63.0% | 37.0% | 0 |  |
| no_decomposition+no_headland+min_width+boustrophedon_order+reeds_shepp_transit | v1 | 2350 | 0 | 0.0% | 100.0% | 0 | **是** |

## 有效池分布（实例数 = 4700）

零 ok 924；≤1 1192；min 0 / Q1 1 / 中位(全实例) 8.0 / 中位(仅≥1ok，manifest 口径) 10.0 / Q3 11 / max 12；**均值 6.6315**
直方图（池大小:实例数）：0:924, 1:268, 2:150, 3:144, 4:198, 5:220, 6:162, 7:192, 8:156, 9:138, 10:640, 11:1026, 12:482
