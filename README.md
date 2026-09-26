# Nathaniel Alexander Sanito — Football Progress & DBU Tracker ⚽

A dedicated, automated football portfolio and progress tracking web app for **Nathaniel Alexander SANITO**, tracking his official match appearances and youth development for **Gentofte-Vangede Idrætsforening (GVI)** within the **Danish Football Association (DBU)**.

---

## 🌟 Profile & Career Overview
- **Player**: Nathaniel Alexander SANITO
- **Club**: Gentofte-Vangede Idrætsforening (GVI)
- **Club ID**: 1556
- **Year of Birth**: 2014
- **Primary Jersey Number**: #8
- **Federation**: Dansk Boldspil-Union (DBU) / DBU Sjælland / DBU København
- **Current Category**: U13 Drenge (Liga Øst 3 & Ungdomspokal)
- **Start Year in GVI**: 2019 (Age 5, U5 Drenge)

---

## 🚀 Key Features

1. **DBU Visual Design Language**:
   - Official DBU Crimson Red (`#C8102E`), Danish crisp white, charcoal/dark slate glassmorphism, and turf emerald accents.
   - Interactive hero profile with jersey #8 badge, club identifiers, and KPI career stat counters.

2. **Official Match History & Team Sheets (`holdkort`)**:
   - **25 Verified Matches** with Nathaniel's name and jersey #8 recorded on official DBU electronic match sheets.
   - Live filters for Season (2026/27 U13 vs 2025/26 U12), Home vs Away, and full-text search across opponents, venues, and scores.
   - One-click links directly to official DBU match protocols (`kampinfo`).

3. **Developmental Journey (2019–2024)**:
   - Chronological milestones tracking Nathaniel's growth from his first 3v3 mini-pitches without goalkeepers (2019), through 5v5 festivals and Futsal medal tournaments (2021–2023), to the big leap to 8:8 on full pitches (2024) and current elite Liga Øst competition.
   - DBU Children's Football (*Børnefodbold*) privacy explanation regarding why official electronic match sheets start at U11/U12.

4. **100% Automated Backend**:
   - Automated with GitHub Actions running twice daily (`06:00` and `18:00` UTC).
   - Scrapes DBU match schedules and team sheets, compiles the data into static JSON, and updates the site without requiring external databases or servers.

---

## 📂 Repository Structure

```
football-progress/
├── .github/
│   └── workflows/
│       └── update-dbu-data.yml    # Twice-daily GitHub Actions cron scraper
├── data/
│   └── nathaniel-data.json        # Compiled static database (matches + milestones)
├── scripts/
│   ├── scraper.py                 # DBU HTML parser and scraper engine
│   ├── build_static_data.py       # Static builder script run by GitHub Actions
│   └── requirements.txt           # Python dependencies (requests, beautifulsoup4)
├── index.html                     # Responsive single-page web app
├── style.css                      # Modern DBU glassmorphism styles
├── app.js                         # Dynamic client application
└── README.md
```

---

## 🌐 Deploying to GitHub Pages

### 1. Initialize Git and Push to GitHub
From the `football-progress` folder in terminal:
```bash
git init
git add .
git commit -m "Initial commit: Nathaniel Sanito Football Progress Web App"
git branch -M main
git remote add origin https://github.com/<YOUR-USERNAME>/football-progress.git
git push -u origin main
```

### 2. Enable GitHub Pages
1. Go to your repository on GitHub: `https://github.com/<YOUR-USERNAME>/football-progress`
2. Click **Settings** ➔ **Pages** (under the "Code and automation" sidebar).
3. Under **Build and deployment**:
   - **Source**: Select `Deploy from a branch`
   - **Branch**: Select `main` / `/ (root)`
4. Click **Save**.
5. Your web app will be live within minutes at:
   `https://<YOUR-USERNAME>.github.io/football-progress/`

### 3. Automated Scraper Workflow
- The workflow in `.github/workflows/update-dbu-data.yml` is already configured.
- Ensure GitHub Actions has write permissions:
  1. Go to **Settings** ➔ **Actions** ➔ **General**.
  2. Under **Workflow permissions**, choose **Read and write permissions**.
  3. Click **Save**.

---

## 💻 Local Development

To run the web app locally:
```bash
# From football-progress directory:
python -m http.server 8080
```
Then visit: `http://localhost:8080` in your web browser.
