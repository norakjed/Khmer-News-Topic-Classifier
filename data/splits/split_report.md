# Split report

Seed 42; 3,138 articles; train/val/test = 70%/15%/15%; 5 cross-validation folds inside train. Stratified by class x source.

## Split sizes

| split | articles | share |
|---|---|---|
| train | 2196 | 70.0% |
| val | 471 | 15.0% |
| test | 471 | 15.0% |

## Articles per class

| label | train | val | test | total |
|---|---|---|---|---|
| economy | 382 | 82 | 82 | 546 |
| entertainment | 294 | 63 | 62 | 419 |
| politics | 430 | 92 | 92 | 614 |
| society_health | 321 | 70 | 70 | 461 |
| sports | 380 | 81 | 81 | 542 |
| technology | 389 | 83 | 84 | 556 |

## Articles per source

| source | train | val | test | total |
|---|---|---|---|---|
| cen | 924 | 197 | 198 | 1319 |
| dap-news | 1159 | 250 | 249 | 1658 |
| kampucheathmey | 113 | 24 | 24 | 161 |

## Class x source

| class | source | train | val | test |
|---|---|---|---|---|
| economy | cen | 170 | 36 | 36 |
| economy | dap-news | 212 | 46 | 46 |
| entertainment | cen | 208 | 44 | 44 |
| entertainment | dap-news | 86 | 19 | 18 |
| politics | cen | 169 | 36 | 36 |
| politics | dap-news | 261 | 56 | 56 |
| society_health | cen | 207 | 45 | 45 |
| society_health | dap-news | 114 | 25 | 25 |
| sports | dap-news | 267 | 57 | 57 |
| sports | kampucheathmey | 113 | 24 | 24 |
| technology | cen | 170 | 36 | 37 |
| technology | dap-news | 219 | 47 | 47 |

## Cross-validation folds (train only): articles per class

| class | fold 0 | fold 1 | fold 2 | fold 3 | fold 4 |
|---|---|---|---|---|---|
| economy | 76 | 77 | 77 | 76 | 76 |
| entertainment | 59 | 58 | 59 | 59 | 59 |
| politics | 87 | 86 | 85 | 86 | 86 |
| society_health | 65 | 64 | 64 | 64 | 64 |
| sports | 76 | 76 | 76 | 76 | 76 |
| technology | 77 | 78 | 78 | 78 | 78 |