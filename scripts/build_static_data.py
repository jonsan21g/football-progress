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
    {"season": "2025/26", "category": "U12", "label": "GVI U11 Drenge 1 (Guest)", "team_id": 702215, "pool_id": 489509},
    # 2024/25 (U11)
    {"season": "2024/25", "category": "U11", "label": "GVI U11 Drenge 1 Forår", "team_id": 665072, "pool_id": 455967}
]

# Confirmed VinterBold matches where DBU hides holdkort publicly for GDPR/privacy reasons
CONFIRMED_VINTERBOLD_MATCHES = [
    # === U12 VinterBold (2025/26) — 9 matches ===
    {
        "id": "897820",
        "season": "2025/26",
        "category": "U12",
        "team_name": "GVI VinterBold U12 Drenge 2 (14) 8v8",
        "date": "Sun, 16 Nov 2025",
        "raw_date": "søn.16-11 2025",
        "time": "12:00",
        "date_time": "søn.16-11 2025 12:00",
        "home_team": "GVI",
        "away_team": "Skjold",
        "is_home": True,
        "opponent": "Skjold",
        "venue": "GVI. Nymosen",
        "status": "FINISHED",
        "result": "Played",
        "gvi_score": None,
        "opponent_score": None,
        "outcome": "FINISHED",
        "jersey_number": "8",
        "role": "Player / Roster",
        "dbu_url": "https://www.dbu.dk/resultater/kamp/897820_477332/kampinfo"
    },
    {
        "id": "897846",
        "season": "2025/26",
        "category": "U12",
        "team_name": "GVI VinterBold U12 Drenge 2 (14) 8v8",
        "date": "Sat, 29 Nov 2025",
        "raw_date": "lør.29-11 2025",
        "time": "11:10",
        "date_time": "lør.29-11 2025 11:10",
        "home_team": "K.B.",
        "away_team": "GVI",
        "is_home": False,
        "opponent": "K.B.",
        "venue": "Kunst, KB, P. Bangs Vej",
        "status": "FINISHED",
        "result": "Played",
        "gvi_score": None,
        "opponent_score": None,
        "outcome": "FINISHED",
        "jersey_number": "8",
        "role": "Player / Roster",
        "dbu_url": "https://www.dbu.dk/resultater/kamp/897846_477332/kampinfo"
    },
    {
        "id": "897864",
        "season": "2025/26",
        "category": "U12",
        "team_name": "GVI VinterBold U12 Drenge 2 (14) 8v8",
        "date": "Sat, 13 Dec 2025",
        "raw_date": "lør.13-12 2025",
        "time": "12:00",
        "date_time": "lør.13-12 2025 12:00",
        "home_team": "B 1903",
        "away_team": "GVI",
        "is_home": False,
        "opponent": "B 1903",
        "venue": "Gentofte Sportspark Vest",
        "status": "FINISHED",
        "result": "Played",
        "gvi_score": None,
        "opponent_score": None,
        "outcome": "FINISHED",
        "jersey_number": "8",
        "role": "Player / Roster",
        "dbu_url": "https://www.dbu.dk/resultater/kamp/897864_477332/kampinfo"
    },
    {
        "id": "897876",
        "season": "2025/26",
        "category": "U12",
        "team_name": "GVI VinterBold U12 Drenge 2 (14) 8v8",
        "date": "Sun, 11 Jan 2026",
        "raw_date": "søn.11-01 2026",
        "time": "10:00",
        "date_time": "søn.11-01 2026 10:00",
        "home_team": "GVI",
        "away_team": "FB (2)",
        "is_home": True,
        "opponent": "FB (2)",
        "venue": "GVI. Nymosen",
        "status": "FINISHED",
        "result": "Played",
        "gvi_score": None,
        "opponent_score": None,
        "outcome": "FINISHED",
        "jersey_number": "8",
        "role": "Player / Roster",
        "dbu_url": "https://www.dbu.dk/resultater/kamp/897876_477332/kampinfo"
    },
    {
        "id": "897894",
        "season": "2025/26",
        "category": "U12",
        "team_name": "GVI VinterBold U12 Drenge 2 (14) 8v8",
        "date": "Sun, 18 Jan 2026",
        "raw_date": "søn.18-01 2026",
        "time": "13:30",
        "date_time": "søn.18-01 2026 13:30",
        "home_team": "B 1908",
        "away_team": "GVI",
        "is_home": False,
        "opponent": "B 1908",
        "venue": "Sundby Idrætspark",
        "status": "FINISHED",
        "result": "Played",
        "gvi_score": None,
        "opponent_score": None,
        "outcome": "FINISHED",
        "jersey_number": "8",
        "role": "Player / Roster",
        "dbu_url": "https://www.dbu.dk/resultater/kamp/897894_477332/kampinfo"
    },
    {
        "id": "897907",
        "season": "2025/26",
        "category": "U12",
        "team_name": "GVI VinterBold U12 Drenge 2 (14) 8v8",
        "date": "Sat, 24 Jan 2026",
        "raw_date": "lør.24-01 2026",
        "time": "14:00",
        "date_time": "lør.24-01 2026 14:00",
        "home_team": "GVI",
        "away_team": "B.93 (2)",
        "is_home": True,
        "opponent": "B.93 (2)",
        "venue": "GVI. Nymosen",
        "status": "FINISHED",
        "result": "Played",
        "gvi_score": None,
        "opponent_score": None,
        "outcome": "FINISHED",
        "jersey_number": "8",
        "role": "Player / Roster",
        "dbu_url": "https://www.dbu.dk/resultater/kamp/897907_477332/kampinfo"
    },
    {
        "id": "897912",
        "season": "2025/26",
        "category": "U12",
        "team_name": "GVI VinterBold U12 Drenge 2 (14) 8v8",
        "date": "Sat, 28 Feb 2026",
        "raw_date": "lør.28-02 2026",
        "time": "10:00",
        "date_time": "lør.28-02 2026 10:00",
        "home_team": "Tårnby FF",
        "away_team": "GVI",
        "is_home": False,
        "opponent": "Tårnby FF",
        "venue": "Vestamager Idrætsanlæg",
        "status": "FINISHED",
        "result": "Played",
        "gvi_score": None,
        "opponent_score": None,
        "outcome": "FINISHED",
        "jersey_number": "8",
        "role": "Player / Roster",
        "dbu_url": "https://www.dbu.dk/resultater/kamp/897912_477332/kampinfo"
    },
    {
        "id": "897924",
        "season": "2025/26",
        "category": "U12",
        "team_name": "GVI VinterBold U12 Drenge 2 (14) 8v8",
        "date": "Sun, 08 Mar 2026",
        "raw_date": "søn.08-03 2026",
        "time": "10:00",
        "date_time": "søn.08-03 2026 10:00",
        "home_team": "GVI",
        "away_team": "Dragør BK",
        "is_home": True,
        "opponent": "Dragør BK",
        "venue": "GVI. Nymosen",
        "status": "FINISHED",
        "result": "Played",
        "gvi_score": None,
        "opponent_score": None,
        "outcome": "FINISHED",
        "jersey_number": "8",
        "role": "Player / Roster",
        "dbu_url": "https://www.dbu.dk/resultater/kamp/897924_477332/kampinfo"
    },
    {
        "id": "897942",
        "season": "2025/26",
        "category": "U12",
        "team_name": "GVI VinterBold U12 Drenge 2 (14) 8v8",
        "date": "Sat, 21 Mar 2026",
        "raw_date": "lør.21-03 2026",
        "time": "10:00",
        "date_time": "lør.21-03 2026 10:00",
        "home_team": "Nørrebro United (1)",
        "away_team": "GVI",
        "is_home": False,
        "opponent": "Nørrebro United (1)",
        "venue": "Mimersparken",
        "status": "FINISHED",
        "result": "Played",
        "gvi_score": None,
        "opponent_score": None,
        "outcome": "FINISHED",
        "jersey_number": "8",
        "role": "Player / Roster",
        "dbu_url": "https://www.dbu.dk/resultater/kamp/897942_477332/kampinfo"
    },
    # === U11 VinterBold (2024/25) — 10 matches ===
    {
        "id": "416723",
        "season": "2024/25",
        "category": "U11",
        "team_name": "GVI VinterBold U11 Drenge 1 (14) 8v8",
        "date": "Sat, 30 Nov 2024",
        "raw_date": "lør.30-11 2024",
        "time": "10:00",
        "date_time": "lør.30-11 2024 10:00",
        "home_team": "GVI 1",
        "away_team": "B 1903 1",
        "is_home": True,
        "opponent": "B 1903",
        "venue": "GVI. Nymosen",
        "status": "FINISHED",
        "result": "Played",
        "gvi_score": None,
        "opponent_score": None,
        "outcome": "FINISHED",
        "jersey_number": "8",
        "role": "Player / Roster",
        "dbu_url": "https://www.dbu.dk/resultater/kamp/416723_450407/kampinfo"
    },
    {
        "id": "416720",
        "season": "2024/25",
        "category": "U11",
        "team_name": "GVI VinterBold U11 Drenge 1 (14) 8v8",
        "date": "Sun, 08 Dec 2024",
        "raw_date": "søn.08-12 2024",
        "time": "11:00",
        "date_time": "søn.08-12 2024 11:00",
        "home_team": "Hvidovre IF 1",
        "away_team": "GVI 1",
        "is_home": False,
        "opponent": "Hvidovre IF",
        "venue": "Avedøre Stadion Kunstgræs",
        "status": "FINISHED",
        "result": "Played",
        "gvi_score": None,
        "opponent_score": None,
        "outcome": "FINISHED",
        "jersey_number": "8",
        "role": "Player / Roster",
        "dbu_url": "https://www.dbu.dk/resultater/kamp/416720_450407/kampinfo"
    },
    {
        "id": "416763",
        "season": "2024/25",
        "category": "U11",
        "team_name": "GVI VinterBold U11 Drenge 1 (14) 8v8",
        "date": "Sun, 12 Jan 2025",
        "raw_date": "søn.12-01 2025",
        "time": "09:30",
        "date_time": "søn.12-01 2025 09:30",
        "home_team": "Skjold 1",
        "away_team": "GVI 1",
        "is_home": False,
        "opponent": "Skjold",
        "venue": "Ryparken Idrætsanlæg",
        "status": "FINISHED",
        "result": "Played",
        "gvi_score": None,
        "opponent_score": None,
        "outcome": "FINISHED",
        "jersey_number": "8",
        "role": "Player / Roster",
        "dbu_url": "https://www.dbu.dk/resultater/kamp/416763_450407/kampinfo"
    },
    {
        "id": "416774",
        "season": "2024/25",
        "category": "U11",
        "team_name": "GVI VinterBold U11 Drenge 1 (14) 8v8",
        "date": "Sat, 18 Jan 2025",
        "raw_date": "lør.18-01 2025",
        "time": "10:00",
        "date_time": "lør.18-01 2025 10:00",
        "home_team": "GVI 1",
        "away_team": "Skovshoved IF 1",
        "is_home": True,
        "opponent": "Skovshoved IF",
        "venue": "GVI. Nymosen",
        "status": "FINISHED",
        "result": "Played",
        "gvi_score": None,
        "opponent_score": None,
        "outcome": "FINISHED",
        "jersey_number": "8",
        "role": "Player / Roster",
        "dbu_url": "https://www.dbu.dk/resultater/kamp/416774_450407/kampinfo"
    },
    {
        "id": "417233",
        "season": "2024/25",
        "category": "U11",
        "team_name": "GVI VinterBold U11 Drenge 1 (14) 8v8",
        "date": "Sat, 25 Jan 2025",
        "raw_date": "lør.25-01 2025",
        "time": "10:00",
        "date_time": "lør.25-01 2025 10:00",
        "home_team": "GVI 1",
        "away_team": "Hvidovre IF 1",
        "is_home": True,
        "opponent": "Hvidovre IF",
        "venue": "GVI. Nymosen",
        "status": "FINISHED",
        "result": "Played",
        "gvi_score": None,
        "opponent_score": None,
        "outcome": "FINISHED",
        "jersey_number": "8",
        "role": "Player / Roster",
        "dbu_url": "https://www.dbu.dk/resultater/kamp/417233_450407/kampinfo"
    },
    {
        "id": "417257",
        "season": "2024/25",
        "category": "U11",
        "team_name": "GVI VinterBold U11 Drenge 1 (14) 8v8",
        "date": "Sun, 02 Feb 2025",
        "raw_date": "søn.02-02 2025",
        "time": "14:30",
        "date_time": "søn.02-02 2025 14:30",
        "home_team": "B 1903 1",
        "away_team": "GVI 1",
        "is_home": False,
        "opponent": "B 1903",
        "venue": "B1903",
        "status": "FINISHED",
        "result": "Played",
        "gvi_score": None,
        "opponent_score": None,
        "outcome": "FINISHED",
        "jersey_number": "8",
        "role": "Player / Roster",
        "dbu_url": "https://www.dbu.dk/resultater/kamp/417257_450407/kampinfo"
    },
    {
        "id": "416762",
        "season": "2024/25",
        "category": "U11",
        "team_name": "GVI VinterBold U11 Drenge 1 (14) 8v8",
        "date": "Sat, 22 Feb 2025",
        "raw_date": "lør.22-02 2025",
        "time": "11:15",
        "date_time": "lør.22-02 2025 11:15",
        "home_team": "Dragør BK 1",
        "away_team": "GVI 1",
        "is_home": False,
        "opponent": "Dragør BK",
        "venue": "Dragør Bk",
        "status": "FINISHED",
        "result": "Played",
        "gvi_score": None,
        "opponent_score": None,
        "outcome": "FINISHED",
        "jersey_number": "8",
        "role": "Player / Roster",
        "dbu_url": "https://www.dbu.dk/resultater/kamp/416762_450407/kampinfo"
    },
    {
        "id": "417259",
        "season": "2024/25",
        "category": "U11",
        "team_name": "GVI VinterBold U11 Drenge 1 (14) 8v8",
        "date": "Sat, 01 Mar 2025",
        "raw_date": "lør.01-03 2025",
        "time": "10:00",
        "date_time": "lør.01-03 2025 10:00",
        "home_team": "GVI 1",
        "away_team": "Dragør BK 1",
        "is_home": True,
        "opponent": "Dragør BK",
        "venue": "GVI. Nymosen",
        "status": "FINISHED",
        "result": "Played",
        "gvi_score": None,
        "opponent_score": None,
        "outcome": "FINISHED",
        "jersey_number": "8",
        "role": "Player / Roster",
        "dbu_url": "https://www.dbu.dk/resultater/kamp/417259_450407/kampinfo"
    },
    {
        "id": "417262",
        "season": "2024/25",
        "category": "U11",
        "team_name": "GVI VinterBold U11 Drenge 1 (14) 8v8",
        "date": "Sat, 15 Mar 2025",
        "raw_date": "lør.15-03 2025",
        "time": "10:00",
        "date_time": "lør.15-03 2025 10:00",
        "home_team": "GVI 1",
        "away_team": "Skjold 1",
        "is_home": True,
        "opponent": "Skjold",
        "venue": "GVI. Nymosen",
        "status": "FINISHED",
        "result": "Played",
        "gvi_score": None,
        "opponent_score": None,
        "outcome": "FINISHED",
        "jersey_number": "8",
        "role": "Player / Roster",
        "dbu_url": "https://www.dbu.dk/resultater/kamp/417262_450407/kampinfo"
    },
    {
        "id": "417265",
        "season": "2024/25",
        "category": "U11",
        "team_name": "GVI VinterBold U11 Drenge 1 (14) 8v8",
        "date": "Sat, 29 Mar 2025",
        "raw_date": "lør.29-03 2025",
        "time": "12:00",
        "date_time": "lør.29-03 2025 12:00",
        "home_team": "Skovshoved IF 1",
        "away_team": "GVI 1",
        "is_home": False,
        "opponent": "Skovshoved IF",
        "venue": "Skovshoved I P",
        "status": "FINISHED",
        "result": "Played",
        "gvi_score": None,
        "opponent_score": None,
        "outcome": "FINISHED",
        "jersey_number": "8",
        "role": "Player / Roster",
        "dbu_url": "https://www.dbu.dk/resultater/kamp/417265_450407/kampinfo"
    }
]

# Confirmed Autumn 2024 U11 matches from official Mit DBU protocol records
CONFIRMED_AUTUMN_U11_MATCHES = [
    {
        "id": "439319",
        "season": "2024/25",
        "category": "U11",
        "team_name": "GVI U11 Drenge 1 (14) 8v8 Efterår",
        "date": "Sat, 31 Aug 2024",
        "raw_date": "lør.31-08 2024",
        "time": "12:00",
        "date_time": "lør.31-08 2024 12:00",
        "home_team": "GVI 1",
        "away_team": "B.93 2",
        "is_home": True,
        "opponent": "B.93",
        "venue": "GVI. Nymosen",
        "status": "FINISHED",
        "result": "Played",
        "gvi_score": None,
        "opponent_score": None,
        "outcome": "FINISHED",
        "jersey_number": "8",
        "role": "Player / Roster",
        "dbu_url": "https://www.dbu.dk/resultater/kamp/439319_418098/kampinfo"
    },
    {
        "id": "439322",
        "season": "2024/25",
        "category": "U11",
        "team_name": "GVI U11 Drenge 1 (14) 8v8 Efterår",
        "date": "Sat, 07 Sep 2024",
        "raw_date": "lør.07-09 2024",
        "time": "11:00",
        "date_time": "lør.07-09 2024 11:00",
        "home_team": "Vanløse 1",
        "away_team": "GVI 1",
        "is_home": False,
        "opponent": "Vanløse",
        "venue": "Vanløse Idrætspark",
        "status": "FINISHED",
        "result": "Played",
        "gvi_score": None,
        "opponent_score": None,
        "outcome": "FINISHED",
        "jersey_number": "8",
        "role": "Player / Roster",
        "dbu_url": "https://www.dbu.dk/resultater/kamp/439322_418098/kampinfo"
    },
    {
        "id": "437935",
        "season": "2024/25",
        "category": "U11",
        "team_name": "GVI U11 Drenge 1 (14) 8v8 Efterår",
        "date": "Sun, 08 Sep 2024",
        "raw_date": "søn.08-09 2024",
        "time": "13:00",
        "date_time": "søn.08-09 2024 13:00",
        "home_team": "Skovshoved IF 1",
        "away_team": "GVI 1",
        "is_home": False,
        "opponent": "Skovshoved IF",
        "venue": "Skovshoved I P",
        "status": "FINISHED",
        "result": "4 - 4",
        "gvi_score": 4,
        "opponent_score": 4,
        "outcome": "DRAW",
        "jersey_number": "8",
        "role": "Player / Roster",
        "dbu_url": "https://www.dbu.dk/resultater/kamp/437935_418098/kampinfo"
    },
    {
        "id": "439335",
        "season": "2024/25",
        "category": "U11",
        "team_name": "GVI U11 Drenge 1 (14) 8v8 Efterår",
        "date": "Sat, 21 Sep 2024",
        "raw_date": "lør.21-09 2024",
        "time": "10:00",
        "date_time": "lør.21-09 2024 10:00",
        "home_team": "Dragør BK 1",
        "away_team": "GVI 1",
        "is_home": False,
        "opponent": "Dragør BK",
        "venue": "Dragør Bk",
        "status": "FINISHED",
        "result": "Played",
        "gvi_score": None,
        "opponent_score": None,
        "outcome": "FINISHED",
        "jersey_number": "8",
        "role": "Player / Roster",
        "dbu_url": "https://www.dbu.dk/resultater/kamp/439335_418098/kampinfo"
    },
    {
        "id": "439341",
        "season": "2024/25",
        "category": "U11",
        "team_name": "GVI U11 Drenge 1 (14) 8v8 Efterår",
        "date": "Sat, 28 Sep 2024",
        "raw_date": "lør.28-09 2024",
        "time": "12:00",
        "date_time": "lør.28-09 2024 12:00",
        "home_team": "GVI 1",
        "away_team": "B 1903 1",
        "is_home": True,
        "opponent": "B 1903",
        "venue": "GVI. Nymosen",
        "status": "FINISHED",
        "result": "3 - 6",
        "gvi_score": 3,
        "opponent_score": 6,
        "outcome": "LOSS",
        "jersey_number": "8",
        "role": "Player / Roster",
        "dbu_url": "https://www.dbu.dk/resultater/kamp/439341_418098/kampinfo"
    },
    {
        "id": "439425",
        "season": "2024/25",
        "category": "U11",
        "team_name": "GVI U11 Drenge 1 (14) 8v8 Efterår",
        "date": "Fri, 04 Oct 2024",
        "raw_date": "fre.04-10 2024",
        "time": "17:00",
        "date_time": "fre.04-10 2024 17:00",
        "home_team": "GVI 1",
        "away_team": "Skjold 1",
        "is_home": True,
        "opponent": "Skjold",
        "venue": "GVI. Nymosen",
        "status": "FINISHED",
        "result": "Played",
        "gvi_score": None,
        "opponent_score": None,
        "outcome": "FINISHED",
        "jersey_number": "8",
        "role": "Player / Roster",
        "dbu_url": "https://www.dbu.dk/resultater/kamp/439425_418098/kampinfo"
    },
    {
        "id": "439417",
        "season": "2024/25",
        "category": "U11",
        "team_name": "GVI U11 Drenge 1 (14) 8v8 Efterår",
        "date": "Sat, 05 Oct 2024",
        "raw_date": "lør.05-10 2024",
        "time": "14:00",
        "date_time": "lør.05-10 2024 14:00",
        "home_team": "K.B. 4",
        "away_team": "GVI 1",
        "is_home": False,
        "opponent": "K.B.",
        "venue": "Kunst, KB, P. Bangs Vej",
        "status": "FINISHED",
        "result": "Played",
        "gvi_score": None,
        "opponent_score": None,
        "outcome": "FINISHED",
        "jersey_number": "8",
        "role": "Player / Roster",
        "dbu_url": "https://www.dbu.dk/resultater/kamp/439417_418098/kampinfo"
    },
    {
        "id": "491053",
        "season": "2024/25",
        "category": "U11",
        "team_name": "GVI U11 Drenge 2 (14) 8v8 Efterår",
        "date": "Sun, 06 Oct 2024",
        "raw_date": "søn.06-10 2024",
        "time": "10:00",
        "date_time": "søn.06-10 2024 10:00",
        "home_team": "GVI 2",
        "away_team": "K.B. 5",
        "is_home": True,
        "opponent": "K.B.",
        "venue": "GVI. Nymosen",
        "status": "FINISHED",
        "result": "Played",
        "gvi_score": None,
        "opponent_score": None,
        "outcome": "FINISHED",
        "jersey_number": "8",
        "role": "Player / Roster",
        "dbu_url": "https://www.dbu.dk/resultater/kamp/491053_418100/kampinfo"
    },
    {
        "id": "439430",
        "season": "2024/25",
        "category": "U11",
        "team_name": "GVI U11 Drenge 1 (14) 8v8 Efterår",
        "date": "Sat, 26 Oct 2024",
        "raw_date": "lør.26-10 2024",
        "time": "12:30",
        "date_time": "lør.26-10 2024 12:30",
        "home_team": "Vestia 1",
        "away_team": "GVI 1",
        "is_home": False,
        "opponent": "Vestia",
        "venue": "Bavnehøj Idrætsanlæg",
        "status": "FINISHED",
        "result": "Played",
        "gvi_score": None,
        "opponent_score": None,
        "outcome": "FINISHED",
        "jersey_number": "8",
        "role": "Player / Roster",
        "dbu_url": "https://www.dbu.dk/resultater/kamp/439430_418098/kampinfo"
    }
]

# Verified Developmental Journey (2021–2027 Grassroots & Youth Football)
# Standardized Pitch Dimensions: 3v3 mini-pitches, 5v5 small pitches, 8v8 half-pitches, 11v11 full pitches
DEVELOPMENTAL_JOURNEY = [
    {
        "year": "2021",
        "age": "Age 6",
        "category": "U7",
        "format": "3v3 (Mini-pitches without goalkeepers)",
        "format_badge": "3v3",
        "title": "Official DBU Debut & Weekend Festivals at GVI",
        "description": "Nathaniel was officially registered in GVI and made his official DBU debut on 2 May 2021 in U7 Drenge 3v3. Participated in 4 festival rounds (8 matches) against BK Skjold, JIF Hakoah, KB, and Jægersborg BK on small 3v3 mini-pitches focused on agility, dribbling, and ball touches.",
        "key_tournaments": [
            "U7 Drenge (14) 3v3 uøvet Forår (Debut: 02-05-2021)",
            "3v3 Festivals vs BK Skjold, JIF Hakoah, KB, Jægersborg BK"
        ],
        "milestone": "Official DBU debut on 2 May 2021 (8 festival matches in 3v3)",
        "icon": "🌱"
    },
    {
        "year": "2021/22",
        "age": "Age 7",
        "category": "U8",
        "format": "5v5 (Small pitches with goalkeepers) + Futsal",
        "format_badge": "3v3 ➔ 5v5",
        "title": "Transition to 5v5 & Competitive Festival Circuits",
        "description": "Stepped up from 3v3 to 5v5 with dedicated goalkeepers, throw-ins, and larger pitch dimensions. Played 21 festival matches for GVI 2 across Autumn 2021 (9 matches in 5v5) and Spring 2022 (12 matches in 5v5).",
        "key_tournaments": [
            "U8 Drenge (14) 5v5 Efterår (9 matches vs FB, Brønshøj, Skjold, KB, Hellas, FA 2000, B 1903, Fix, Sundby)",
            "U8 Drenge (14) 5v5 Forår (12 matches vs Hellas, Vanløse, Frem, FA 2000, KB, AB Tårnby, Sundby, B 1903)",
            "DBU Futsal & Winter Indoor Circuits (5v5)"
        ],
        "milestone": "21 matches across Autumn & Spring in 5v5 festival rounds",
        "icon": "🧤"
    },
    {
        "year": "2022/23",
        "age": "Age 8",
        "category": "U9",
        "format": "5v5 (Full Season)",
        "format_badge": "5v5",
        "title": "Positional Awareness, Vision & Passing",
        "description": "Continued development in 5v5 with GVI 3, focusing on build-up play from the back, combination passing, and spatial orientation in attack and defense. Recorded 8 festival matches in 5v5 across Copenhagen.",
        "key_tournaments": [
            "U9 Drenge (14) 5v5 Efterår (8 matches vs KB, Husum, Fremad Valby, Hellas, B.93, Brønshøj, Nørrebro United, FB)",
            "DBU VinterBOLD U9 Series (5v5)"
        ],
        "milestone": "8 matches in Autumn 5v5 festival circuits",
        "icon": "🎯"
    },
    {
        "year": "2023/24",
        "age": "Age 9",
        "category": "U10",
        "format": "5v5 (High Tempo & Counter-Pressing)",
        "format_badge": "5v5",
        "title": "High Tempo, Transitions & Tactical Skill",
        "description": "Sharp acceleration in tactical game comprehension, aggressive counter-pressing, and rapid transitions in 5v5 across GVI 3 and GVI 1. Recorded 9 festival matches across Autumn 2023 and Spring 2024.",
        "key_tournaments": [
            "U10 Drenge 2 (14) 5v5 Efterår (6 matches vs BK Hekla, KB, Fremad Valby, Nørrebro United, FA 2000)",
            "U10 Drenge 1 (14) 5v5 Forår (3 matches vs B.93, FA 2000, B 1903)",
            "DBU VinterBOLD U10 Series (5v5)"
        ],
        "milestone": "9 matches across Autumn and Spring in 5v5 circuits",
        "icon": "🔥"
    },
    {
        "year": "2024/25",
        "age": "Age 10–11",
        "category": "U11",
        "format": "8v8 (Half-Pitches & Official Match Sheets)",
        "format_badge": "U11 8v8",
        "title": "The Big Leap: 8v8 on Half-Pitches & 28 Campaign Matches",
        "description": "The decisive leap to 8v8 football on half-pitches with the offside rule and structured tactical lines. Complete 28-match year-round campaign (9 in Autumn 2024 + 10 in VinterBold 2024/25 + 9 in Spring 2025) as a core starter for GVI 1.",
        "key_tournaments": [
            "U11 Drenge 1 (14) 8v8 Efterår — Sort Pulje (9 matches vs B.93, Vanløse, Skovshoved, Dragør, B 1903, Skjold, KB, Vestia)",
            "VinterBold U11 Drenge 1 (14) 8v8 — Pulje 1 (10 matches vs B 1903, Hvidovre, Skjold, Skovshoved, Dragør)",
            "U11 Drenge 1 (14) 8v8 Forår — Blå Pulje (9 matches vs Dragør, Skovshoved, Brønshøj, B.93, Fremad Valby, KB, Vanløse, Vestia)"
        ],
        "milestone": "28 verified 8v8 matches on half-pitches across Autumn, Winter & Spring",
        "icon": "🚀"
    },
    {
        "year": "2025/26",
        "age": "Age 11–12",
        "category": "U12",
        "format": "8v8 (Half-Pitches — Full 32-Match Campaign)",
        "format_badge": "U12 8v8",
        "title": "U12 Campaign on Half-Pitches & Established Jersey #8",
        "description": "Full 32-match campaign on half-pitches across Autumn 2025 (10 matches), VinterBold 2025/26 (9 matches), Spring 2026 (12 matches), and 1 guest appearance wearing jersey #8 as GVI U12 Drenge's core starter.",
        "key_tournaments": [
            "U12 Drenge 1 (14) 8v8 Efterår — Rød Pulje (10 matches)",
            "VinterBold U12 Drenge 2 (14) 8v8 — Pulje 1 (9 matches)",
            "U12 Drenge 1 (14) 8v8 Forår — Rød Pulje (12 matches)",
            "Guest appearance for U11 Drenge 1 (15) on 02-05-2026 (#14)"
        ],
        "milestone": "32 verified 8v8 matches on half-pitches across autumn, winter, and spring",
        "icon": "👕"
    },
    {
        "year": "2026/27",
        "age": "Age 12–13",
        "category": "U13",
        "format": "8v8 Half-Pitches ➔ 11v11 Full Pitches (Liga Øst 3 & Cup)",
        "format_badge": "Liga Øst 8v8 / 11v11",
        "title": "Elite Regional Youth: Liga Øst 3 & Transition to Full Pitches",
        "description": "Current active season in the top regional competitive tier across Zealand and Copenhagen against elite clubs including K.B., Frem, Skjold, Frederikssund, Himmelev-Veddelev, and Taastrup FC, preparing for full-pitch 11v11 football.",
        "key_tournaments": [
            "U13 Drenge Liga Øst 3 8v8 efterår (14) 2026",
            "Ungdomspokalen U13 Drenge 8v8 (14) 26/27"
        ],
        "milestone": "Permanent jersey #8 in Liga Øst 3 & Ungdomspokal",
        "icon": "🏆"
    }
]

def discover_active_teams(club_id=CLUB_ID, birth_year=PLAYER_BIRTH_YEAR):
    now = datetime.now()
    season_start_year = now.year if now.month >= 7 else now.year - 1
    target_age = season_start_year - birth_year + 1
    season_label = f"{season_start_year}/{str(season_start_year + 1)[-2:]}"
    
    cohort_tag = f"({str(birth_year)[-2:]})"
    age_tags = [f"u{target_age}", f"u{target_age + 1}"]

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

        if "piger" in tname or "kvinder" in tname or "piger" in pname:
            continue

        is_relevant = False
        if cohort_tag in tname or cohort_tag in pname:
            is_relevant = True
        elif any(tag in tname or tag in pname for tag in age_tags):
            is_relevant = True
        elif any(kw in tname or kw in pname for kw in ["ungdomspokal", "pokal", "vinterbold", "futsal", "forår"]):
            if any(tag in tname or tag in pname for tag in age_tags) or cohort_tag in tname or cohort_tag in pname:
                is_relevant = True

        if is_relevant and cid not in seen:
            seen.add(cid)
            cat = f"U{target_age}"
            cat_match = re.search(r'u(\d{2})', tname + " " + pname)
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
    s = date_str.strip()
    s = re.sub(r'lør\.?|lor\.?', 'Sat', s, flags=re.I)
    s = re.sub(r'søn\.?|son\.?', 'Sun', s, flags=re.I)
    s = re.sub(r'man\.?', 'Mon', s, flags=re.I)
    s = re.sub(r'tirs?\.?', 'Tue', s, flags=re.I)
    s = re.sub(r'ons\.?', 'Wed', s, flags=re.I)
    s = re.sub(r'tors?\.?', 'Thu', s, flags=re.I)
    s = re.sub(r'fre\.?', 'Fri', s, flags=re.I)

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
    
    out_file = os.path.join(OUTPUT_DIR, "nathaniel-data.json")
    existing_matches = {}
    if os.path.exists(out_file):
        try:
            with open(out_file, "r", encoding="utf-8") as f:
                cached_data = json.load(f)
                for m in cached_data.get("matches", []):
                    existing_matches[m["id"]] = m
            print(f"Preloaded {len(existing_matches)} verified matches from database.")
        except Exception as e:
            print(f"Note: Could not preload existing matches: {e}")
    
    seen_compounds = set()
    teams_to_scan = []

    for item in HISTORICAL_TEAMS:
        cid = f"{item['team_id']}_{item['pool_id']}"
        if cid not in seen_compounds:
            seen_compounds.add(cid)
            teams_to_scan.append(item)

    discovered = discover_active_teams(club_id=CLUB_ID, birth_year=PLAYER_BIRTH_YEAR)
    for item in discovered:
        cid = f"{item['team_id']}_{item['pool_id']}"
        if cid not in seen_compounds:
            seen_compounds.add(cid)
            teams_to_scan.append(item)

    print(f"Total teams queued for lineup inspection: {len(teams_to_scan)}")

    all_player_matches = []
    # Seed with confirmed VinterBold and U11 Autumn matches (where DBU hides holdkort publicly for GDPR/privacy reasons)
    for vm in CONFIRMED_VINTERBOLD_MATCHES:
        all_player_matches.append(vm)
    for am in CONFIRMED_AUTUMN_U11_MATCHES:
        all_player_matches.append(am)

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

    unique_matches = dict(existing_matches)
    for m in all_player_matches:
        unique_matches[m["id"]] = m
    match_list = list(unique_matches.values())

    match_list.sort(key=lambda m: parse_date(m["date"]), reverse=True)

    category_counts = {}
    seasons_set = set()
    for m in match_list:
        cat = m.get("category", "Youth")
        category_counts[cat] = category_counts.get(cat, 0) + 1
        seasons_set.add(m.get("season", ""))

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
            "first_registered_year": 2021,
            "first_registered_date": "02-05-2021",
            "current_category": current_category_label,
            "current_team": match_list[0]["team_name"] if match_list else "GVI U13 Drenge Liga Øst 3 8v8",
            "primary_jersey": "8",
            "federation": "DBU Sjælland / DBU København",
            "seasons_active": sorted(list(seasons_set), reverse=True)
        },
        "career_stats": {
            "total_matches_tracked": len(match_list),
            "seasons_tracked": len(seasons_set),
            "categories": category_counts,
            "u13_matches": category_counts.get("U13", 0),
            "u12_matches": category_counts.get("U12", 0),
            "u11_matches": category_counts.get("U11", 0),
            "first_registered_year": 2021,
            "grassroots_festival_matches": 46,
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

