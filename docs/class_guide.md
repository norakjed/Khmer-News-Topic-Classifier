# Class Guide (draft, based on docs/source_survey.md)

Labels come from each news site's section. Section URLs below are relative to each site.

| Final class | DAP News | CEN | Kampuchea Thmey | BTV |
|---|---|---|---|---|
| Politics | /category/politic/ | /category/national/politics | - | /category/development |
| Economy/Business | /category/economic/ | /category/national/business-2 | - | /category/economic |
| Sports | /category/sport/ | - | /category/sports | - |
| Entertainment | /category/entertianment/ | /category/entertainment | - | - |
| Technology | /category/technology/ | /category/science-and-technology | - | - |
| Society/Health | /category/health/ | /category/heal-beauty | - | /category/security |

Sections deliberately NOT used: national/international (mixed topics), advertising/promote content, flood, covid19, specialedition, scholar, weird, hong-suy (fortune telling), CEN national/social (shares the society_health label with heal-beauty).

Rules:
- Drop a class if it has fewer than ~300 articles; each class from at least 2 sites.
- Society/Health merges different site sections; spot-check about 100 articles and split or drop it if inconsistent.
- Dedupe by URL and by normalised title (sites may repost the same story).
