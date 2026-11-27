#!/usr/bin/env python3
"""Relève sur GitHub ce que le site affiche, et le range dans content/.

- content/github.json : chiffres du compte, calendrier d'activité, et pour chaque dépôt ses dates et ses langages
- content/readmes/<dépôt>.md : le README des dépôts publics, affiché sur la page de chaque projet

Usage :  python3 tools/github_stats.py      (demande l'outil « gh », connecté au compte)
Le site est statique : c'est un relevé daté, à refaire de temps en temps, puis `python3 build.py`.
"""
import json
import subprocess
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUERY = """query { viewer { login createdAt
  repositories(first: 100, ownerAffiliations: OWNER) { nodes { name isPrivate isFork createdAt pushedAt
    defaultBranchRef { name }
    languages(first: 12, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name } } } } }
  contributionsCollection { contributionCalendar { totalContributions weeks { contributionDays { date contributionCount } } } } } }"""


def gh(*args):
    return subprocess.run(["gh", *args], capture_output=True, text=True, check=True).stdout


def shares(edges):
    total = sum(e["size"] for e in edges)
    return [(e["node"]["name"], e["size"] / total) for e in edges] if total else []


v = json.loads(gh("api", "graphql", "-f", "query=" + QUERY))["data"]["viewer"]
repos = [r for r in v["repositories"]["nodes"] if not r["isFork"]]

# langages du compte : chaque dépôt pèse autant, pour qu'un gros dépôt n'écrase pas les autres
share = defaultdict(float)
counted = 0
for r in repos:
    parts = shares(r["languages"]["edges"])
    if parts:
        counted += 1
        for name, part in parts:
            share[name] += part
langs = sorted(((n, s / counted) for n, s in share.items()), key=lambda x: -x[1])
top = [[n, round(s * 100, 1)] for n, s in langs[:5]]
rest = round(100 - sum(p for _, p in top), 1)
if rest > 0:
    top.append(["other", rest])


def one_repo(r):
    parts = [[n, round(p * 100, 1)] for n, p in shares(r["languages"]["edges"]) if p >= 0.005]
    return {"created": r["createdAt"][:10], "pushed": r["pushedAt"][:10], "languages": parts, "branch": (r["defaultBranchRef"] or {}).get("name", "main")}


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
    "language_repos": {name: sum(1 for r in repos if any(e["node"]["name"] == name for e in r["languages"]["edges"])) for name in share},
    "public": {r["name"]: one_repo(r) for r in repos if not r["isPrivate"]},
    # dépôts privés : seulement leurs dates, sans leur nom
    "private": sorted(([r["createdAt"][:10], r["pushedAt"][:10]] for r in repos if r["isPrivate"])),
    "days": [[d["date"], d["contributionCount"]] for d in days],
}
(ROOT / "content" / "github.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

readmes = ROOT / "content" / "readmes"
readmes.mkdir(exist_ok=True)
saved = []
for name in out["public"]:
    if name == v["login"] or name.endswith(".github.io"):
        continue
    try:
        text = gh("api", f"repos/{v['login']}/{name}/readme", "-H", "Accept: application/vnd.github.raw")
    except subprocess.CalledProcessError:
        continue
    (readmes / f"{name}.md").write_text(text, encoding="utf-8")
    saved.append(name)
print("écrit github.json :", {k: out[k] for k in ("repos", "public_repos", "contributions", "active_days", "languages_count")})
print("README relevés :", ", ".join(saved))
