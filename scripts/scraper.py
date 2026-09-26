"""
DBU Scraper Core
Extracts club search, team rosters, standings, and match schedules from dbu.dk.
"""

import re
import urllib.parse
from typing import Dict, List, Optional, Any
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.dbu.dk"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "da-DK,da;q=0.9,en-US;q=0.8,en;q=0.7"
}

def search_clubs(query: str) -> List[Dict[str, Any]]:
    """Search for clubs by name or partial name."""
    url = f"{BASE_URL}/resultater/klubsoeg/?q={urllib.parse.quote(query)}"
    resp = requests.get(url, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    
    soup = BeautifulSoup(resp.text, "html.parser")
    clubs = []
    
    # Matching club links: /resultater/Klub/{club_id}
    for a in soup.find_all("a"):
        href = a.get("href", "")
        match = re.search(r"/resultater/Klub/(\d+)", href, re.IGNORECASE)
        if match:
            clubs.append({
                "id": int(match.group(1)),
                "name": a.get_text(strip=True),
                "url": f"{BASE_URL}{href}"
            })
    return clubs

def get_club_info(club_id: int) -> Dict[str, Any]:
    """Extract club name, venues, and contact info from /klub/{club_id}/klubinfo."""
    url = f"{BASE_URL}/resultater/klub/{club_id}/klubinfo"
    resp = requests.get(url, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    
    soup = BeautifulSoup(resp.text, "html.parser")
    header = soup.find("h2")
    club_name = header.get_text(strip=True) if header else f"Club {club_id}"
    
    venues = []
    for tr in soup.find_all("tr"):
        tds = tr.find_all("td")
        if tds:
            venues.append(tds[0].get_text(separator=" ", strip=True))
            
    return {
        "id": club_id,
        "name": club_name,
        "venues": venues
    }

def get_club_teams(club_id: int) -> List[Dict[str, Any]]:
    """Extract all teams and pools from /klub/{club_id}/holdoversigt."""
    url = f"{BASE_URL}/resultater/klub/{club_id}/holdoversigt"
    resp = requests.get(url, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    
    soup = BeautifulSoup(resp.text, "html.parser")
    teams = []
    current_category = "General"
    
    table = soup.find("table", class_=lambda c: c and ("dbu-data-table" in c or "table" in c))
    if not table:
        return []
        
    for tr in table.find_all("tr"):
        # Check for category header (Senior, Ungdom, etc.)
        th = tr.find("th")
        if th and th.get("colspan"):
            current_category = th.get_text(strip=True)
            continue
            
        tds = tr.find_all("td")
        if len(tds) >= 2:
            team_link = tds[0].find("a")
            pool_link = tds[1].find("a")
            
            team_name = tds[0].get_text(strip=True)
            pool_name = tds[1].get_text(strip=True)
            
            href = team_link.get("href", "") if team_link else ""
            match = re.search(r"/resultater/hold/(\d+)_(\d+)", href, re.IGNORECASE)
            
            team_id = int(match.group(1)) if match else None
            pool_id = int(match.group(2)) if match else None
            
            teams.append({
                "category": current_category,
                "team_name": team_name,
                "pool_name": pool_name,
                "team_id": team_id,
                "pool_id": pool_id,
                "compound_id": f"{team_id}_{pool_id}" if team_id and pool_id else None,
                "url": f"{BASE_URL}{href}" if href else None
            })
    return teams

def get_team_standings(team_id: int, pool_id: int) -> Dict[str, Any]:
    """Extract league standings table from /resultater/hold/{team_id}_{pool_id}/stilling."""
    url = f"{BASE_URL}/resultater/hold/{team_id}_{pool_id}/stilling"
    resp = requests.get(url, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    
    soup = BeautifulSoup(resp.text, "html.parser")
    
    # Pool / Team header
    header = soup.find("div", class_="sr--header")
    pool_title = header.get_text(separator=" - ", strip=True) if header else ""
    
    # Table has class 'sr--pool-position--table' or 'dbu-data-table'
    table = soup.find("table", class_=lambda c: c and ("pool-position" in c or "dbu-data-table" in c))
    if not table:
        return {"pool_title": pool_title, "standings": []}
        
    standings = []
    rows = table.find_all("tr")
    
    for tr in rows:
        tds = tr.find_all("td")
        if len(tds) >= 7:
            # Columns: Pos, TeamName, K (matches), V (won), U (draw), T (lost), Score (goals), P (points)
            pos_text = tds[0].get_text(strip=True)
            if not pos_text.isdigit():
                continue
                
            team_name = tds[1].get_text(strip=True)
            # Remove trailing info icon text like ' i' or ' !'
            team_name = re.sub(r'\s+[i!]$', '', team_name)
            
            played = tds[2].get_text(strip=True)
            won = tds[3].get_text(strip=True)
            draw = tds[4].get_text(strip=True)
            lost = tds[5].get_text(strip=True)
            score = tds[6].get_text(strip=True)
            points = tds[7].get_text(strip=True) if len(tds) > 7 else "0"
            
            standings.append({
                "position": int(pos_text),
                "team": team_name,
                "played": int(played) if played.isdigit() else 0,
                "won": int(won) if won.isdigit() else 0,
                "draw": int(draw) if draw.isdigit() else 0,
                "lost": int(lost) if lost.isdigit() else 0,
                "goals": score,
                "points": int(points) if points.isdigit() else 0
            })
            
    return {
        "pool_id": pool_id,
        "team_id": team_id,
        "pool_title": pool_title,
        "standings": standings
    }

def get_team_matches(team_id: int, pool_id: int) -> Dict[str, Any]:
    """Extract match schedule from /resultater/hold/{team_id}_{pool_id}/kampprogram."""
    url = f"{BASE_URL}/resultater/hold/{team_id}_{pool_id}/kampprogram"
    resp = requests.get(url, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    
    soup = BeautifulSoup(resp.text, "html.parser")
    table = soup.find("table", class_=lambda c: c and "dbu-data-table" in c)
    if not table:
        return {"matches": []}
        
    matches = []
    for tr in table.find_all("tr"):
        cells = [td.get_text(strip=True) for td in tr.find_all("td")]
        # Columns: [0]=empty, [1]=Kampnr, [2]=Dato, [3]=Tid, [4]=Hjemme, [5]=Ude, [6]=Spillested, [7]=Resultat
        if len(cells) >= 7:
            match_no = cells[1]
            date = cells[2]
            time = cells[3]
            home = cells[4]
            away = cells[5]
            stadium = cells[6] if len(cells) > 6 else ""
            result = cells[7] if len(cells) > 7 else ""
            
            # Clean up result (e.g. '3 - 0' or empty if not yet played)
            if not result or result == "-":
                status = "UPCOMING"
                score = None
            else:
                status = "FINISHED"
                score = result
                
            matches.append({
                "match_number": match_no,
                "date": date,
                "time": time,
                "date_time": f"{date} {time}".strip(),
                "home_team": home,
                "away_team": away,
                "venue": stadium,
                "status": status,
                "result": score
            })
            
    return {
        "pool_id": pool_id,
        "team_id": team_id,
        "matches": matches
    }
