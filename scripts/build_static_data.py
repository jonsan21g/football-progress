"""
DBU Static Data Generator (for GitHub Actions & GitHub Pages)
Scrapes DBU for Nathaniel Alexander Sanito's GVI teams and match reports,
outputting static JSON to data/nathaniel-data.json.
Runs on a scheduled cron (e.g. twice daily) in GitHub Actions.
"""

import os
import json
import re
import time
from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup
import scraper

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
PLAYER_NAME_VARIANTS = ["sanito", "nathaniel"]

# Target teams to monitor for Nathaniel:
# Current Season: U13 Drenge (14)
# Historical: U12 (14), U11 (14)
TEAMS_TO_MONITOR = [
    # 2026/27 (U13)
    {"season": "2026/27 (U13)", "category": "U13", "label": "GVI U13 Drenge Liga Øst 3", "team_id": 790700, "pool_id": 507586},
    {"season": "2026/27 (U13)", "category": "U13", "label": "GVI Ungdomspokal U13", "team_id": 798562, "pool_id": 500765},
    {"season": "2026/27 (U13)", "category": "U13", "label": "GVI U13 Drenge 2", "team_id": 798560, "pool_id": 496407},
    # 2025/26 (U12 / U11)
    {"season": "2025/26 (U12)", "category": "U12", "label": "GVI U12 Drenge 1 Efterår", "team_id": 665072, "pool_id": 456042},
    {"season": "2025/26 (U11)", "category": "U11", "label": "GVI U11 Drenge 1 Forår", "team_id": 665072, "pool_id": 455967}
]

# Verified Developmental Journey (2019–2024 Grassroots & Børnefodbold)
DEVELOPMENTAL_JOURNEY = [
    {
        "year": "2019",
        "age": "Age 5",
        "category": "U5 & U6",
        "format": "3v3 (Small pitch without goalkeepers)",
        "format_badge": "3v3",
        "title": "First Steps at GVI",
        "description": "Nathaniel began his football journey at Gentofte-Vangede IF at age 5. Play took place on small 3v3 pitches focused on maximum ball touches, joy of movement, and early dribbling.",
        "key_tournaments": [
            "U5 Drenge (14) 3v3 Forår (Pulje 1)",
            "U6 Drenge (14) 3v3 Efterår (Pulje 1 & 2)"
        ],
        "milestone": "First registered DBU cohort teams in GVI (Born 2014)",
        "icon": "🌱"
    },
    {
        "year": "2020",
        "age": "Age 6",
        "category": "U7",
        "format": "3v3 (Fast rotations & small goals)",
        "format_badge": "3v3",
        "title": "DBU Weekend Festivals & Ball Mastery",
        "description": "Participated in 5 rounds of DBU Copenhagen/Zealand weekend festivals. Fast-paced play, continuous finishing on small goals, and 1v1 duels against neighboring clubs.",
        "key_tournaments": [
            "U7 Drenge (14) 3v3 Efterår (Rounds 1–5)",
            "Festival matches vs HIK, Skovshoved, etc."
        ],
        "milestone": "5 completed DBU festival rounds in the autumn",
        "icon": "⚡"
    },
    {
        "year": "2021",
        "age": "Age 7",
        "category": "U7 & U8",
        "format": "3v3 Spring ➔ 5v5 Autumn + Futsal",
        "format_badge": "3v3 ➔ 5v5",
        "title": "Transition to 5v5 & Futsal Medal Tournaments",
        "description": "A major developmental milestone: stepping up from 3v3 to 5v5 on grass with dedicated goalkeepers, throw-ins, and debut in DBU Futsal indoor medal tournaments.",
        "key_tournaments": [
            "U8 Drenge (14) 5v5 Efterår",
            "DBU Futsal Medaljestævner (A+B tiers)",
            "DBU VinterBold U8 Drenge"
        ],
        "milestone": "First 5v5 matches with goalkeepers and DBU Futsal",
        "icon": "🧤"
    },
    {
        "year": "2022",
        "age": "Age 8",
        "category": "U8 & U9",
        "format": "5v5 (Full Season)",
        "format_badge": "5v5",
        "title": "Positional Play, Vision & Passing",
        "description": "Full competitive season in 5v5 focusing on build-up play from the goalkeeper, combination passing, and developing positional awareness in attack and defense.",
        "key_tournaments": [
            "U8 Drenge (14) 5v5 Forår",
            "U9 Drenge (14) 5v5 Efterår",
            "VinterBOLD U9 (Weeks 45, 47, 49)"
        ],
        "milestone": "21 GVI (14) tournament pools across DBU divisions",
        "icon": "🎯"
    },
    {
        "year": "2023",
        "age": "Age 9",
        "category": "U9 & U10",
        "format": "5:5 (High tempo & technical depth)",
        "format_badge": "5:5",
        "title": "High Press, Transitions & Tactical Skill",
        "description": "Consolidation on the 5:5 pitch with sharper tactical comprehension, immediate counter-pressing, and quick passing combinations in GVI's top grassroots groups.",
        "key_tournaments": [
            "U10 Drenge 1 (14) 5:5 Efterår (White Pool)",
            "U9 Drenge (14) 5:5 Forår",
            "VinterBOLD U10 Drenge"
        ],
        "milestone": "24 GVI (14) tournament pools registered in DBU",
        "icon": "🔥"
    },
    {
        "year": "2024",
        "age": "Age 10",
        "category": "U10 & U11",
        "format": "5:5 Spring ➔ 8:8 Full Pitch Autumn",
        "format_badge": "5:5 ➔ 8:8",
        "title": "The Big Leap: 8:8 Format & Tactical Maturity",
        "description": "The crucial transition to 8:8 football on large pitches in Autumn 2024. Introduction of the offside rule, structured tactical lines (defense, midfield, attack), and preparation for official electronic team sheets.",
        "key_tournaments": [
            "U11 Drenge 1 (14) 8:8 Efterår (Black Pool)",
            "U10 Drenge 1 (14) 5:5 Forår (Blue Pool)",
            "Fixtures vs B.93, Vanløse IF, Dragør BK, Skovshoved"
        ],
        "milestone": "Debut in 8:8 format on large pitch with offside rule",
        "icon": "🚀"
    },
    {
        "year": "2025",
        "age": "Age 11",
        "category": "U11 & U12",
        "format": "8:8 (Official DBU Team Sheets)",
        "format_badge": "8:8 Lineups",
        "title": "Official Match Sheets & Jersey #8",
        "description": "First season with publicly published electronic match rosters and official match scores. Nathaniel establishes his role wearing jersey #8 for GVI.",
        "key_tournaments": [
            "U12 Drenge 1 (14) 8:8 Efterår",
            "U11 Drenge 1 (14) 8:8 Forår"
        ],
        "milestone": "19 officially verified matches on DBU team sheets",
        "icon": "👕"
    },
    {
        "year": "2026/27",
        "age": "Age 12–13",
        "category": "U13",
        "format": "8:8 / 11:11 (Liga Øst 3 & Pokal)",
        "format_badge": "Liga Øst",
        "title": "Elite Youth: Liga Øst 3 & Youth Cup",
        "description": "Current active season. Highest competitive regional tier across Zealand and Copenhagen against K.B., Frem, Skjold, Frederikssund, Himmelev-Veddelev, Taastrup FC, and more.",
        "key_tournaments": [
            "U13 Drenge Liga Øst 3 (8:8)",
            "Ungdomspokalen U13 Drenge"
        ],
        "milestone": "Permanent jersey #8 in Liga Øst 3 & Ungdomspokal",
        "icon": "🏆"
    }
]

def matches_player(text):
    if not text:
        return False
    t_lower = text.lower()
    return "sanito" in t_lower or "nathaniel" in t_lower

def parse_date(date_str):
    m = re.search(r'(\d{2})-(\d{2})\s+(\d{4})', date_str)
    if m:
        d, mo, y = map(int, m.groups())
        return datetime(y, mo, d)
    return datetime(2020, 1, 1)

def run_build():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    now = datetime.now(timezone.utc)
    print(f"=== Starting Nathaniel Sanito DBU Sync at {now.isoformat()} ===")
    
    all_player_matches = []

    for item in TEAMS_TO_MONITOR:
        t_label = item["label"]
        team_id = item["team_id"]
        pool_id = item["pool_id"]
        season = item["season"]
        category = item["category"]

        print(f"\nChecking: {t_label} ({team_id}_{pool_id})...")
        try:
            data = scraper.get_team_matches(team_id, pool_id)
            matches = data.get("matches", [])
            print(f"  Schedule matches: {len(matches)}")

            for m in matches:
                match_no = m["match_number"]
                url = f"https://www.dbu.dk/resultater/kamp/{match_no}_{pool_id}/kampinfo"
                
                try:
                    resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=8)
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    tables = soup.find_all('table')

                    found = False
                    jersey = "8"

                    for t in tables:
                        for tr in t.find_all('tr'):
                            cells = [td.get_text(strip=True) for td in tr.find_all(['td', 'th'])]
                            for c in cells:
                                if matches_player(c):
                                    found = True
                                    for num in cells:
                                        if num.isdigit():
                                            jersey = num
                                            break
                                    break
                            if found:
                                break
                        if found:
                            break

                    if found:
                        is_home = "gvi" in m["home_team"].lower()
                        result = m.get("result")
                        outcome = "FINISHED"
                        gvi_score = None
                        opp_score = None

                        if result and "-" in result:
                            parts = result.split("-")
                            try:
                                h_score = int(parts[0].strip())
                                a_score = int(parts[1].strip())
                                gvi_score = h_score if is_home else a_score
                                opp_score = a_score if is_home else h_score
                                if gvi_score > opp_score:
                                    outcome = "WIN"
                                elif gvi_score == opp_score:
                                    outcome = "DRAW"
                                else:
                                    outcome = "LOSS"
                            except ValueError:
                                pass

                        print(f"  >>> FOUND MATCH #{match_no}: {m['home_team']} vs {m['away_team']} ({m['date']}) -> {m['result']}")
                        all_player_matches.append({
                            "id": match_no,
                            "season": season,
                            "category": category,
                            "team_name": t_label,
                            "date": m["date"],
                            "time": m["time"],
                            "date_time": m.get("date_time", ""),
                            "home_team": m["home_team"],
                            "away_team": m["away_team"],
                            "is_home": is_home,
                            "opponent": m["away_team"] if is_home else m["home_team"],
                            "venue": m["venue"],
                            "status": m["status"],
                            "result": result or "Played",
                            "gvi_score": gvi_score,
                            "opponent_score": opp_score,
                            "outcome": outcome,
                            "jersey_number": jersey,
                            "role": "Player / Roster",
                            "dbu_url": url
                        })

                    time.sleep(0.15)
                except Exception as match_err:
                    print(f"    Failed match {match_no}: {match_err}")

        except Exception as e:
            print(f"  Error checking {t_label}: {e}")

    # Remove duplicates if any
    unique_matches = {}
    for m in all_player_matches:
        unique_matches[m["id"]] = m
    match_list = list(unique_matches.values())

    # Sort latest first
    match_list.sort(key=lambda m: parse_date(m["date"]), reverse=True)

    profile_dataset = {
        "metadata": {
            "last_updated_utc": now.isoformat(),
            "last_updated_human": now.strftime("%d-%m-%Y %H:%M UTC")
        },
        "player": {
            "full_name": "Nathaniel Alexander Sanito",
            "short_name": "Nathaniel Sanito",
            "club": "Gentofte-Vangede Idrætsforening (GVI)",
            "club_short": "GVI",
            "club_id": 1556,
            "birth_year": 2014,
            "current_category": "U13 Boys",
            "current_team": "GVI U13 Drenge Liga Øst 3 (8:8)",
            "primary_jersey": "8",
            "federation": "DBU Sjælland / DBU København / DSU",
            "seasons_active": ["2026/27 (U13)", "2025/26 (U12)", "2024/25 (U11)"]
        },
        "career_stats": {
            "total_matches_tracked": len(match_list),
            "seasons_tracked": 2,
            "current_season_matches": len([m for m in match_list if "2026/27" in m["season"]]),
            "historical_matches": len([m for m in match_list if "2025/26" in m["season"]]),
            "last_match_date": match_list[0]["date"] if match_list else "",
            "opponents_faced_count": len(set(m["opponent"] for m in match_list))
        },
        "developmental_journey": DEVELOPMENTAL_JOURNEY,
        "matches": match_list
    }

    out_file = os.path.join(OUTPUT_DIR, "nathaniel-data.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(profile_dataset, f, indent=2, ensure_ascii=False)

    print(f"\n=== Build Complete! Saved {len(match_list)} matches to {out_file} ===")

if __name__ == "__main__":
    run_build()
