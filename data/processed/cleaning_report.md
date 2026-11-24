# Cleaning report

Raw rows: 3327. Removed: 189. Final: 3138 (kept 94.3%).

## Rows removed by rule

| Rule | cen | dap-news | kampucheathmey | Total |
|---|---|---|---|---|
| too short (< 250 chars) | 10 | 44 | 0 | 54 |
| not Khmer (Khmer share < 0.5) | 0 | 51 | 0 | 51 |
| advertorial (phone number + >= 3 promo keywords) | 5 | 40 | 1 | 46 |
| near duplicate (similarity >= 0.8) | 12 | 11 | 1 | 24 |
| exact duplicate (title or text) | 4 | 10 | 0 | 14 |

## Class x source counts: raw -> final

| Class | cen | dap-news | kampucheathmey | Total |
|---|---|---|---|---|
| economy | 250 -> 242 | 360 -> 304 | 0 -> 0 | 610 -> 546 |
| entertainment | 300 -> 296 | 128 -> 123 | 0 -> 0 | 428 -> 419 |
| politics | 250 -> 241 | 400 -> 373 | 0 -> 0 | 650 -> 614 |
| society_health | 300 -> 297 | 174 -> 164 | 0 -> 0 | 474 -> 461 |
| sports | 0 -> 0 | 400 -> 381 | 163 -> 161 | 563 -> 542 |
| technology | 250 -> 243 | 352 -> 313 | 0 -> 0 | 602 -> 556 |

## Final dataset

| Class | Articles | Largest source share | Date range |
|---|---|---|---|
| economy | 546 | 56% (dap-news) | 2020-06-11 .. 2026-11-19 |
| entertainment | 419 | 71% (cen) | 2019-10-30 .. 2026-10-21 |
| politics | 614 | 61% (dap-news) | 2022-10-27 .. 2026-11-20 |
| society_health | 461 | 64% (cen) | 2019-10-11 .. 2025-04-25 |
| sports | 542 | 70% (dap-news) | 2022-07-08 .. 2026-11-24 |
| technology | 556 | 56% (dap-news) | 2019-12-18 .. 2026-11-21 |

Text length (chars): median 1684, min 250, max 21338.
Phone numbers were removed from the text of every kept article. Possible promotional articles kept (>= 4 promo keywords, no phone number; judged on-topic): 50.
Near-duplicate pairs merged: 24. Cross-label conflict pairs dropped: 0.