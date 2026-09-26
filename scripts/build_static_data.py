"""
DBU Static Data Generator (for GitHub Actions & GitHub Pages)
Scrapes DBU for Nathaniel Alexander Sanito's GVI teams and match reports,
outputting static JSON to data/nathaniel-data.json.
Runs on a scheduled cron (e.g. twice daily) in GitHub Actions.

Features Dynamic Team Discovery:
Automatically discovers all active and future GVI youth teams matching
Nathaniel's cohort (14) and age group (U13, U14, U15, etc.) so the scraper
never gets stale as he progresses through age divisions.
"""

import os
import sys
import json
import re
import time
from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup

# Ensure scripts directory is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scraper

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
CLUB_ID = 1556 # Gentofte-Vangede Idrætsforening (GVI)
PLAYER_BIRTH_YEAR = 2014
PLAYER_NAME_VARIANTS = ["sanito", "nathaniel"]

# Archived past seasons with fixed historical pool IDs
HISTORICAL_TEAMS = [
    # 2025/26 (U12)
    {"season": "2025/26", "category": "U12", "label": "GVI U12 Drenge 1 Forår", "team_id": 665072, "pool_id": 489497},
    {"season": "2025/26", "category": "U12", "label": "GVI U12 Drenge 1 Efterår", "team_id": 665072, "pool_id": 456042},
    # 2024/25 (U11)
    {"season": "2024/25", "category": "U11", "label": "GVI U11 Drenge 1 Forår", "team_id": 665072, "pool_id": 455967}
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
        "year": "2024/25",
        "age": "Age 11",
        "category": "U11",
        "format": "8:8 (Official DBU Team Sheets)",
        "format_badge": "U11 8:8",
        "title": "U11 Official Match Sheets & Roster Debut",
        "description": "Nathaniel's first official electronic match sheet appearances in Spring 2025, recording 9 official appearances for GVI U11 Drenge 1.",
        "key_tournaments": [
            "U11 Drenge 1 (14) 8:8 Forår (Blue Pool)"
        ],
        "milestone": "9 official matches on DBU team sheets",
        "icon": "⚽"
    },
    {
        "year": "2025/26",
        "age": "Age 11–12",
        "category": "U12",
        "format": "8:8 (Full Season)",
        "format_badge": "U12 8:8",
        "title": "U12 Campaign & Established Jersey #8",
        "description": "Full 22-match campaign across Autumn 2025 and Spring 2026 as GVI U12 Drenge 1's starting player wearing jersey #8.",
        "key_tournaments": [
            "U12 Drenge 1 (14) 8:8 Efterår (Red Pool)",
            "U12 Drenge 1 (14) 8:8 Forår (Red Pool)"
        ],
        "milestone": "22 verified matches on DBU team sheets",
        "icon": "👕"
    },
    {
        "year": "2026/27",
        "age": "Age 12–13",
        "category": "U13",
        "format": "8:8 / 11:11 (Liga Øst 3 & Cup)",
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

def discover_active_teams(club_id=CLUB_ID, birth_year=PLAYER_BIRTH_YEAR):
    """
    Dynamically discover all active GVI teams for Nathaniel from DBU's live club page.
    Automatically handles U13, U14, U15, U16 etc. as Nathaniel grows up.
    """
    now = datetime.now()
    season_start_year = now.year if now.month >= 7 else now.year - 1
    target_age = season_start_year - birth_year + 1  # 2026: 13 (U13), 2027: 14 (U14), etc.
    season_label = f"{season_start_year}/{str(season_start_year + 1)[-2:]}"
    
    cohort_tag = f"({str(birth_year)[-2:]})" # e.g. '(14)'
    age_tags = [f"u{target_age}", f"u{target_age + 1}"] # e.g. ['u13', 'u14']

    print(f"Dynamically discovering live teams for GVI (Season {season_label}, Age U{target_age}, Cohort {cohort_tag})...")
    
    try:
        all_teams = scraper.get_club_teams(club_id)
    except Exception as e:
        print(f"  Warning: could not fetch live club teams: {e}")
        return []

    discovered = []
    seen = set()

    for t in all_teams:
        cid = t.get("compound_id")
        if not cid or "_" not in str(cid):
            continue
            
        tname = t.get("team_name", "").lower()
        pname = t.get("pool_name", "").lower()

        # Exclude girls/women teams
        if "piger" in tname or "kvinder" in tname or "piger" in pname:
            continue

        is_relevant = False
        if cohort_tag in tname or cohort_tag in pname:
            is_relevant = True
        elif any(tag in tname for tag in age_tags):
            is_relevant = True
        elif "ungdomspokal" in tname or "pokal" in tname:
            if any(tag in tname for tag in age_tags) or cohort_tag in tname:
                is_relevant = True

        if is_relevant and cid not in seen:
            seen.add(cid)
            # Detect age category
            cat = f"U{target_age}"
            cat_match = re.search(r'u(\d{2})', tname)
            if cat_match:
                cat = f"U{cat_match.group(1)}"

            parts = cid.split("_")
            discovered.append({
                "season": season_label,
                "category": cat,
                "label": t["team_name"],
                "team_id": int(parts[0]),
                "pool_id": int(parts[1])
            })

    print(f"  Auto-discovered {len(discovered)} relevant teams for Nathaniel for {season_label}.")
    return discovered

def matches_player(text):
    if not text:
        return False
    t_lower = text.lower()
    return "sanito" in t_lower or "nathaniel" in t_lower

def translate_danish_date(date_str):
    if not date_str:
        return ""
    # "lør.15-08 2026" -> "Sat, 15 Aug 2026"
    s = date_str.strip()
    s = re.sub(r'lør\.?|lor\.?', 'Sat', s, flags=re.I)
    s = re.sub(r'søn\.?|son\.?', 'Sun', s, flags=re.I)
    s = re.sub(r'man\.?', 'Mon', s, flags=re.I)
    s = re.sub(r'tirs?\.?', 'Tue', s, flags=re.I)
    s = re.sub(r'ons\.?', 'Wed', s, flags=re.I)
    s = re.sub(r'tors?\.?', 'Thu', s, flags=re.I)
    s = re.sub(r'fre\.?', 'Fri', s, flags=re.I)

    # Format dd-mm yyyy into "Sat, 15 Aug 2026"
    m = re.match(r'^(Sat|Sun|Mon|Tue|Wed|Thu|Fri)[,\s]*(\d{2})-(\d{2})\s+(\d{4})', s, re.I)
    if m:
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        day_name, day, month_num, year = m.groups()
        month_idx = int(month_num) - 1
        month_name = months[month_idx] if 0 <= month_idx < 12 else month_num
        return f"{day_name}, {day} {month_name} {year}"
    return s

def parse_date(date_str):
    m = re.search(r'(\d{2})-(\d{2})\s+(\d{4})', date_str)
    if m:
        d, mo, y = map(int, m.groups())
        return datetime(y, mo, d)
    
    m_eng = re.search(r'(\d{2})\s+([A-Za-z]{3})\s+(\d{4})', date_str)
    if m_eng:
        d, mo_str, y = m_eng.groups()
        months = {'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6, 'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12}
        mo = months.get(mo_str.lower(), 1)
        return datetime(int(y), mo, int(d))

    return datetime(2020, 1, 1)

def run_build():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    now = datetime.now(timezone.utc)
    print(f"=== Starting Nathaniel Sanito DBU Sync at {now.isoformat()} ===")
    
    # 1. Combine historical teams with dynamically discovered active teams
    seen_compounds = set()
    teams_to_scan = []

    for item in HISTORICAL_TEAMS:
        cid = f"{item['team_id']}_{item['pool_id']}"
        if cid not in seen_compounds:
            seen_compounds.add(cid)
            teams_to_scan.append(item)

    # Dynamic Discovery: fetches current & future seasons automatically (U13, U14, U15...)
    discovered = discover_active_teams(club_id=CLUB_ID, birth_year=PLAYER_BIRTH_YEAR)
    for item in discovered:
        cid = f"{item['team_id']}_{item['pool_id']}"
        if cid not in seen_compounds:
            seen_compounds.add(cid)
            teams_to_scan.append(item)

    print(f"Total teams queued for lineup inspection: {len(teams_to_scan)}")

    all_player_matches = []

    for item in teams_to_scan:
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

                        eng_date = translate_danish_date(m["date"])
                        print(f"  >>> FOUND MATCH #{match_no}: {m['home_team']} vs {m['away_team']} ({eng_date}) -> {m['result']}")
                        all_player_matches.append({
                            "id": match_no,
                            "season": season,
                            "category": category,
                            "team_name": t_label,
                            "date": eng_date,
                            "raw_date": m["date"],
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

                    time.sleep(0.12)
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

    # Calculate category tallies dynamically
    category_counts = {}
    seasons_set = set()
    for m in match_list:
        cat = m.get("category", "Youth")
        category_counts[cat] = category_counts.get(cat, 0) + 1
        seasons_set.add(m.get("season", ""))

    # Active category (e.g. U13 Boys now, U14 Boys next season)
    latest_cat = match_list[0]["category"] if match_list else "U13"
    current_category_label = f"{latest_cat} Boys"

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
            "club_id": CLUB_ID,
            "birth_year": PLAYER_BIRTH_YEAR,
            "current_category": current_category_label,
            "current_team": match_list[0]["team_name"] if match_list else "GVI U13 Drenge Liga Øst 3 (8:8)",
            "primary_jersey": "8",
            "federation": "DBU Sjælland / DBU København / DSU",
            "seasons_active": sorted(list(seasons_set), reverse=True)
        },
        "career_stats": {
            "total_matches_tracked": len(match_list),
            "seasons_tracked": len(seasons_set),
            "categories": category_counts,
            "u13_matches": category_counts.get("U13", 0),
            "u12_matches": category_counts.get("U12", 0),
            "u11_matches": category_counts.get("U11", 0),
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
    print(f"Categories tally: {category_counts}")

if __name__ == "__main__":
    run_build()
