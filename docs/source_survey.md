# Source Survey

Checked 2026-11-23. Method: fetched `/robots.txt`, homepage, one paginated section page per site, with a normal browser-style User-Agent. No articles were bulk-downloaded.
Re-check each site's terms of use before scraping; robots.txt is only part of the picture.

## Usable (shortlist)

| Site | robots.txt | Sections found (Khmer) | Pagination / article URLs | Notes |
|---|---|---|---|---|
| **DAP News** `dap-news.com` | Allow all except /wp-admin/ | politic, economic, sport, entertianment (sic), technology, health, national, international, entrepreneur | `/category/<x>/page/N/`; articles `/sport/2026/09/19/632067/` | Best coverage; sections match our classes. Start here. |
| **CEN** `cen.com.kh` | Allow all except /wp-admin/ | national, world, entertainment, science-and-technology, heal-beauty (health) | `/category/<x>/page/N`; articles `/archives/931398.html` | Good for technology, health, entertainment. |
| **Sabay News** `news.sabay.com.kh` | Allow all | entertainment, technology, life (society), sport | `/topics/<x>`; articles `/article/1363101` | Good for entertainment, sport, tech. |
| **BTV** `btv.com.kh` | Disallows /search, /loadmore/, /scroll/, /generate, /viewads/ | development (politics), economic, security (society), tour (culture/tourism) | `/category/<x>`; articles `/article/118936` | Do not use the /loadmore/ endpoint; use normal pages only. Good for politics and economy. |

## Excluded

| Site | Reason |
|---|---|
| Post Khmer, Thmey Thmey | robots.txt: `Content-Signal: ai-train=no` (explicitly forbids training AI models on content). Do not use. |
| Fresh News (`freshnewsasia.com`) | Cloudflare "Just a moment" challenge (HTTP 403); scraping would mean bypassing bot protection. |
| RFA, Koh Santepheap | Did not connect (HTTP 000) from this machine; unreachable, retry later if needed. |
| VOA Khmer (`khmer.voanews.com`) | robots.txt allows, but pages are organised by program, not topic, so there are no clean topic labels. Possible extra source only. |

## Class coverage vs. 4 usable sites

| Class | DAP | CEN | Sabay | BTV |
|---|---|---|---|---|
| Politics | politic | - | - | development |
| Economy/Business | economic | - | - | economic |
| Sports | sport | - | sport | - |
| Entertainment | entertianment | entertainment | entertainment | - |
| Technology | technology | science-and-technology | technology | - |
| Society/Health | health | heal-beauty | life | security |

Every class has at least two sites. Politics and Economy rely on DAP + BTV only, so watch the source balance there.

## Proposed scraping rules
- Delay >= 2 s between requests, single thread, descriptive User-Agent.
- Only normal listing pages and article pages; no search, load-more or ad endpoints.
- Store title, text, label, source, url, date. No author names. Use for coursework only; do not republish article text.
- Cache raw pages locally (`data/raw/`, git-ignored) to avoid re-requesting.

## Open questions for the team
1. Final class list: keep all 6, or drop Society/Health if labels are inconsistent across sites (life vs. security vs. health)?
2. Optionally check `Terms of Use` pages of DAP, CEN, Sabay and BTV manually (in Khmer/English).
