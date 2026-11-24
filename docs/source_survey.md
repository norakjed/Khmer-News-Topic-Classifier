# Source Survey

Checked 2026-11-23 to 2026-11-24. Method: fetched `/robots.txt`, homepage, one paginated section page per site, with a normal browser-style User-Agent. No articles were bulk-downloaded during the survey.
Re-check each site's terms of use before scraping; robots.txt is only part of the picture.

## Usable (shortlist)

| Site | robots.txt | Sections found (Khmer) | Pagination / article URLs | Notes |
|---|---|---|---|---|
| **DAP News** `dap-news.com` | Allow all except /wp-admin/ | politic, economic, sport, entertianment (sic), technology, health, national, international, entrepreneur | `/category/<x>/page/N/`; articles `/sport/2026/09/19/632067/` | Best coverage; sections match our classes. Main source. |
| **CEN** `cen.com.kh` | Allow all except /wp-admin/ | national (sub: politics, business-2, social), world, entertainment, science-and-technology, heal-beauty (health) | `/category/<x>/page/N`; articles `/archives/931398.html` | Large archive. Second source for politics, economy, entertainment, technology, health. |
| **Kampuchea Thmey** `kampucheathmey.com` | `Crawl-delay: 10` | sports (other categories exist) | `/category/sports/page/N`; articles `/sports/1210813` | Second source for sports only. 10 s delay is applied automatically. Inserts invisible zero-width spaces between words: must be stripped. |
| **BTV** `btv.com.kh` | Disallows /search, /loadmore/, /scroll/, /generate, /viewads/ | development (politics), economic, security (society), tour (culture/tourism) | `/category/<x>`; articles `/article/118936` | Not scraped yet. Do not use the /loadmore/ endpoint; use normal pages only. |

## Excluded

| Site | Reason |
|---|---|
| Post Khmer, Thmey Thmey | robots.txt: `Content-Signal: ai-train=no` (explicitly forbids training AI models on content). Do not use. |
| Fresh News (`freshnewsasia.com`) | Cloudflare "Just a moment" challenge (HTTP 403); scraping would mean bypassing bot protection. |
| RFA | Did not connect (HTTP 000) from this machine. |
| VOA Khmer (`khmer.voanews.com`) | robots.txt allows, but pages are organised by program, not topic, so there are no clean topic labels. |
| Cambodianess | English, and robots.txt carries `ai-train=no`. |
| AKP | robots.txt disallows all crawling. |
| Koh Santepheap Daily (`kohsantepheapdaily.com.kh`) | Khmer with a sports category, but pagination does not work (only the latest ~22 articles are reachable). |

## Class coverage

| Class | DAP | CEN | Kampuchea Thmey | BTV |
|---|---|---|---|---|
| Politics | politic | national/politics | - | development |
| Economy/Business | economic | national/business-2 | - | economic |
| Sports | sport | - | sports | - |
| Entertainment | entertianment | entertainment | - | - |
| Technology | technology | science-and-technology | - | - |
| Society/Health | health | heal-beauty | - | security |

Every class has at least two sources (DAP + one other).

## Proposed scraping rules
- Delay >= 2 s between requests (or the site's own Crawl-delay if longer), single thread, descriptive User-Agent.
- Only normal listing pages and article pages; no search, load-more or ad endpoints.
- Store title, text, label, source, url, date. No author names. Use for coursework only; do not republish article text.
- Cache raw pages locally (`data/raw/`, git-ignored) to avoid re-requesting.

## Open questions for the team
1. Final class list: keep all 6, or drop Society/Health if labels are inconsistent across sites (life vs. security vs. health)?
2. Optionally check `Terms of Use` pages of DAP, CEN, Kampuchea Thmey and BTV manually (in Khmer/English).
