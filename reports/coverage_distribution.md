# Coverage distribution report

Source: `runs.parquet` (SHA-256 `a143d7cd912c06a38ffa4596f990a6c4b3745a729350ee50e327e015779cccdd`)
Total rows: 61100

## Runstatus row counts

| status | rows |
|---|---:|
| ok | 31,168 |
| outside_area | 12,718 |
| not_applicable | 10,040 |
| collision | 7,174 |

## coverage\_ratio\_field distribution (OK rows only)

| stat | value |
|---|---:|
| n | 31168 |
| min | 0.143417 |
| p5 | 0.560861 |
| p25 | 0.686937 |
| p50 | 0.759031 |
| p75 | 0.811895 |
| p95 | 0.885590 |
| max | 0.923548 |

## OK rows below thresholds

- OK rows total: 31,168
- below_0.99: 31,168 (100.00%)
- below_0.95: 31,168 (100.00%)
- below_0.90: 30,682 (98.44%)

## coverage\_ratio\_field by headland stage (OK rows)

| headland | n | min | p50 | max |
|---|---:|---:|---:|---:|
| uniform_headland | 31,168 | 0.1434 | 0.7590 | 0.9235 |

## coverage\_ratio\_field by config\_id (OK rows)

| config\_id | headland | swath | n | min | p50 | max | <0.99 |
|---|---|---|---:|---:|---:|---:|---:|
| `0f0087b4bce0…` | uniform_headland | fixed_angle | 2,830 | 0.5136 | 0.7625 | 0.9127 | 2,830 |
| `1e07c37de63c…` | uniform_headland | longest_edge | 3,160 | 0.4066 | 0.7610 | 0.9171 | 3,160 |
| `28e61f999761…` | uniform_headland | row_aligned | 2,948 | 0.4232 | 0.7629 | 0.9235 | 2,948 |
| `3fade1fcd68b…` | uniform_headland | min_width | 2,650 | 0.4497 | 0.7700 | 0.9182 | 2,650 |
| `4574095631bc…` | uniform_headland | principal_axis | 2,590 | 0.4148 | 0.7638 | 0.9126 | 2,590 |
| `485fccc852cf…` | uniform_headland | min_width | 3,230 | 0.4248 | 0.7637 | 0.9235 | 3,230 |
| `4e24c2b38e3c…` | uniform_headland | row_aligned | 1,508 | 0.4232 | 0.7626 | 0.9235 | 1,508 |
| `6bdde7389b87…` | uniform_headland | min_width | 1,120 | 0.5322 | 0.7610 | 0.9011 | 1,120 |
| `7965a962930e…` | uniform_headland | row_aligned | 2,682 | 0.4541 | 0.7637 | 0.9235 | 2,682 |
| `8ce138a275e9…` | uniform_headland | min_width | 3,010 | 0.1434 | 0.6584 | 0.8863 | 3,010 |
| `a331cae1f1b3…` | uniform_headland | min_width | 2,470 | 0.4497 | 0.7626 | 0.9182 | 2,470 |
| `adf5ed70e0f4…` | uniform_headland | fixed_angle | 2,970 | 0.4243 | 0.7629 | 0.9234 | 2,970 |

### Configurations in the frozen pool with zero OK rows

| config\_id | headland | swath | route | path | rows |
|---|---|---|---|---|---:|
| `c942f952646d…` | no_headland | min_width | boustrophedon_order | reeds_shepp_transit | 4,700 |

## coverage\_ratio\_field vs coverage\_ratio\_main (OK rows)

coverage\_ratio\_main: n=31168, min=0.767995, p50=0.989782, max=0.999997

main − field: min=0.072232, p50=0.231107, max=0.686804
All differences positive (main > field in every row): True
main ≥ 0.99: 15,190 rows; main ≥ 0.95: 30,854 rows

## Exclusion flow

- Input fields: 235
- Fields with ≥ 1 OK instance: 193
- Fields with zero OK instances: 42

### Row accounting

```
61,100 planner runs
├─ 31,168  ok
├─ 19,012  not ok, in a field that succeeded elsewhere
└─ 10,920  every run of a field with zero ok
```

Sums to the parquet row count: True

### Zero-OK field failure categories (row counts)

| category | rows |
|---|---:|
| collision | 6,820 |
| outside_area | 2,420 |
| headland_collapse | 840 |
| kinematics_mismatch | 840 |

### not\_applicable rows by failure category

| category | rows |
|---|---:|
| kinematics_mismatch | 4,700 |
| headland_collapse | 3,320 |
| outside_area | 2,020 |

