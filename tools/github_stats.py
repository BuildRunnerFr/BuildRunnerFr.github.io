#!/usr/bin/env python3
"""Relève les chiffres GitHub d'Ethan et les range dans content/github.json.

Usage :  python3 tools/github_stats.py      (demande l'outil « gh », connecté au compte)
Le site est statique : ces chiffres sont un relevé daté, à refaire de temps en temps.
"""
import json
import subprocess
from collections import defaultdict
from datetime import date
from pathlib import Path

QUERY = """query { viewer { login createdAt
  repositories(first: 100, ownerAffiliations: OWNER) { totalCount nodes { isPrivate isFork
    languages(first: 12, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name } } } } }
  contributionsCollection { contributionCalendar { totalContributions weeks { contributionDays { date contributionCount } } } } } }"""

raw = subprocess.run(["gh", "api", "graphql", "-f", "query=" + QUERY], capture_output=True, text=True, check=True).stdout
v = json.loads(raw)["data"]["viewer"]
repos = [r for r in v["repositories"]["nodes"] if not r["isFork"]]

# langages : chaque dépôt pèse autant, pour qu'un gros dépôt n'écrase pas les autres
share = defaultdict(float)
counted = 0
for r in repos:
    edges = r["languages"]["edges"]
    total = sum(e["size"] for e in edges)
    if not total:
        continue
    counted += 1
    for e in edges:
        share[e["node"]["name"]] += e["size"] / total
langs = sorted(((n, s / counted) for n, s in share.items()), key=lambda x: -x[1])
top = [[n, round(s * 100, 1)] for n, s in langs[:5]]
rest = round(100 - sum(p for _, p in top), 1)
if rest > 0:
    top.append(["other", rest])

days = [d for w in v["contributionsCollection"]["contributionCalendar"]["weeks"] for d in w["contributionDays"]]
opened = v["createdAt"][:10]
days = [d for d in days if d["date"] >= opened[:8] + "01"]
best = max(days, key=lambda d: d["contributionCount"])
out = {
    "login": v["login"],
    "synced": date.today().isoformat(),
    "account_opened": opened,
    "repos": len(repos),
    "public_repos": sum(not r["isPrivate"] for r in repos),
    "contributions": v["contributionsCollection"]["contributionCalendar"]["totalContributions"],
    "active_days": sum(1 for d in days if d["contributionCount"]),
    "best_day": {"date": best["date"], "count": best["contributionCount"]},
    "languages_count": len(share),
    "languages": top,
    "days": [[d["date"], d["contributionCount"]] for d in days],
}
path = Path(__file__).resolve().parent.parent / "content" / "github.json"
path.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print("écrit", path.name, {k: out[k] for k in ("repos", "public_repos", "contributions", "active_days", "best_day", "languages_count", "languages")})
