/**
 * Nathaniel Alexander Sanito - Football Progress Web App
 * Consumes pre-built static dataset from ./data/nathaniel-data.json
 * (Updated automatically by GitHub Actions)
 * 
 * Future-Proof & Dynamic:
 * Automatically scales as Nathaniel advances from U13 to U14, U15, U16 etc.
 */

const state = {
  data: null,
  activeView: 'matches', // 'matches' | 'journey'
  activeFilter: 'ALL', // 'ALL' | <Category> | 'HOME' | 'AWAY'
  searchQuery: ''
};

// DOM Elements
const elements = {
  heroName: document.getElementById('hero-name'),
  heroJersey: document.getElementById('hero-jersey'),
  heroCategoryTag: document.getElementById('hero-category-tag'),
  statsGrid: document.getElementById('hero-stats-grid'),
  tabMatches: document.getElementById('tab-matches'),
  tabJourney: document.getElementById('tab-journey'),
  tabMatchesCount: document.getElementById('tab-matches-count'),
  viewMatches: document.getElementById('view-matches'),
  viewJourney: document.getElementById('view-journey'),
  filteredCount: document.getElementById('filtered-count'),
  seasonPillsContainer: document.getElementById('season-pills'),
  matchSearchInput: document.getElementById('match-search-input'),
  matchesContainer: document.getElementById('matches-container'),
  journeyTimelineContainer: document.getElementById('journey-timeline-container'),
  opponentsCloud: document.getElementById('opponents-cloud'),
  syncBadge: document.getElementById('sync-badge'),
  footerSyncTime: document.getElementById('footer-sync-time')
};

// Initialize App
async function init() {
  setupEventListeners();
  await loadPlayerData();
}

async function loadPlayerData() {
  elements.matchesContainer.innerHTML = '<p class="text-muted" style="text-align: center; padding: 2rem;">Loading Nathaniel\'s match history...</p>';

  try {
    const res = await fetch('./data/nathaniel-data.json', { cache: 'no-cache' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    state.data = data;

    renderHeroProfile(data.player, data.career_stats, data.matches);
    renderFilterPills(data.matches);
    renderOpponents(data.matches);
    renderMatches();
    renderDevelopmentalJourney(data.developmental_journey || []);

    const total = data.matches.length;
    if (elements.syncBadge) {
      elements.syncBadge.textContent = `${total} Lineups Tracked`;
    }
    if (elements.tabMatchesCount) {
      elements.tabMatchesCount.textContent = total;
    }
    if (elements.footerSyncTime && data.metadata && data.metadata.last_updated_human) {
      elements.footerSyncTime.textContent = `Last synchronized with DBU: ${data.metadata.last_updated_human}`;
    }
  } catch (err) {
    elements.matchesContainer.innerHTML = `
      <div style="background: rgba(200, 16, 46, 0.08); border: 1px solid #fecaca; border-radius: 12px; padding: 1.5rem; text-align: center; color: #b91c1c;">
        <h3>Could not load data</h3>
        <p style="margin-top: 0.5rem; font-size: 0.9rem;">Please verify that <code>./data/nathaniel-data.json</code> exists.</p>
      </div>
    `;
  }
}

function renderHeroProfile(player, stats, matches) {
  if (elements.heroName) elements.heroName.textContent = player.full_name;
  if (elements.heroJersey) {
    const jersey = player.primary_jersey || "8";
    elements.heroJersey.textContent = jersey.startsWith("#") ? jersey : `#${jersey}`;
  }
  
  if (elements.heroCategoryTag) {
    elements.heroCategoryTag.textContent = `${player.current_category || 'U13 Boys'} (Liga Øst)`;
  }

  // Dynamic KPI Stats Grid
  if (elements.statsGrid) {
    const categoriesTally = stats.categories || {};
    
    // Sort categories descending: U15, U14, U13, U12, U11...
    const sortedCats = Object.keys(categoriesTally).sort((a, b) => {
      const numA = parseInt(a.replace(/\D/g, ''), 10) || 0;
      const numB = parseInt(b.replace(/\D/g, ''), 10) || 0;
      return numB - numA;
    });

    let html = `
      <div class="stat-card">
        <span class="stat-value">${stats.total_matches_tracked || matches.length}</span>
        <span class="stat-label">Official Lineups</span>
      </div>
    `;

    for (const cat of sortedCats) {
      const count = categoriesTally[cat];
      const sampleMatch = matches.find(m => m.category === cat);
      const seasonShort = sampleMatch && sampleMatch.season ? ` (${sampleMatch.season})` : '';
      html += `
        <div class="stat-card">
          <span class="stat-value">${count}</span>
          <span class="stat-label">${cat} Matches${seasonShort}</span>
        </div>
      `;
    }

    html += `
      <div class="stat-card stat-highlight">
        <span class="stat-value">2019</span>
        <span class="stat-label">Started at GVI (U5)</span>
      </div>
    `;

    elements.statsGrid.innerHTML = html;
  }
}

/**
 * Dynamically generate Category filter pills from the data
 * Automatically creates pills for U13, U14, U15 etc. as new matches arrive
 */
function renderFilterPills(matches) {
  if (!elements.seasonPillsContainer) return;

  const categoryCounts = {};
  for (const m of matches) {
    const cat = m.category || 'Youth';
    categoryCounts[cat] = (categoryCounts[cat] || 0) + 1;
  }

  // Sort categories descending
  const sortedCategories = Object.keys(categoryCounts).sort((a, b) => {
    const numA = parseInt(a.replace(/\D/g, ''), 10) || 0;
    const numB = parseInt(b.replace(/\D/g, ''), 10) || 0;
    return numB - numA;
  });

  let html = `
    <button class="filter-pill ${state.activeFilter === 'ALL' ? 'active' : ''}" data-filter="ALL">
      All Matches (${matches.length})
    </button>
  `;

  for (const cat of sortedCategories) {
    const count = categoryCounts[cat];
    const sampleMatch = matches.find(m => m.category === cat);
    const seasonText = sampleMatch && sampleMatch.season ? ` — ${sampleMatch.season}` : '';
    html += `
      <button class="filter-pill ${state.activeFilter === cat ? 'active' : ''}" data-filter="${cat}">
        ${cat}${seasonText} (${count})
      </button>
    `;
  }

  html += `
    <button class="filter-pill ${state.activeFilter === 'HOME' ? 'active' : ''}" data-filter="HOME">Home</button>
    <button class="filter-pill ${state.activeFilter === 'AWAY' ? 'active' : ''}" data-filter="AWAY">Away</button>
  `;

  elements.seasonPillsContainer.innerHTML = html;

  elements.seasonPillsContainer.querySelectorAll('.filter-pill').forEach(pill => {
    pill.addEventListener('click', () => {
      elements.seasonPillsContainer.querySelectorAll('.filter-pill').forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      state.activeFilter = pill.dataset.filter;
      renderMatches();
    });
  });
}

function renderOpponents(matches) {
  if (!elements.opponentsCloud) return;
  const opponents = [...new Set(matches.map(m => m.opponent))].sort();
  elements.opponentsCloud.innerHTML = opponents.map(opp => `
    <button class="opponent-chip" data-opponent="${escapeHtml(opp)}">
      ${escapeHtml(opp)}
    </button>
  `).join('');

  elements.opponentsCloud.querySelectorAll('.opponent-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      const opp = chip.dataset.opponent;
      elements.matchSearchInput.value = opp;
      state.searchQuery = opp.toLowerCase();
      switchView('matches');
      renderMatches();
      elements.matchesContainer.scrollIntoView({ behavior: 'smooth' });
    });
  });
}

/**
 * Format date string and translate Danish day abbreviation into English
 * e.g., "lør.15-08 2026" or "Sat, 15 Aug 2026"
 */
function formatDisplayDate(dateStr) {
  if (!dateStr) return '';
  let str = dateStr.trim();

  // If already in "Sat, 15 Aug 2026" format, return as-is
  if (/^(Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s+\d{2}\s+[A-Za-z]{3}\s+\d{4}$/.test(str)) {
    return str;
  }

  // Replace Danish day abbreviations with English
  str = str.replace(/lør\.?|lor\.?/gi, 'Sat')
           .replace(/søn\.?|son\.?/gi, 'Sun')
           .replace(/man\.?/gi, 'Mon')
           .replace(/tirs?\.?/gi, 'Tue')
           .replace(/ons\.?/gi, 'Wed')
           .replace(/tors?\.?/gi, 'Thu')
           .replace(/fre\.?/gi, 'Fri');

  // Format "Sat 15-08 2026" -> "Sat, 15 Aug 2026"
  const m = str.match(/^(Sat|Sun|Mon|Tue|Wed|Thu|Fri)[,\s]*(\d{2})-(\d{2})\s+(\d{4})/i);
  if (m) {
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const dayName = m[1];
    const day = m[2];
    const monthIdx = parseInt(m[3], 10) - 1;
    const year = m[4];
    const monthName = months[monthIdx] || m[3];
    return `${dayName}, ${day} ${monthName} ${year}`;
  }

  return str;
}

function renderMatches() {
  if (!state.data || !state.data.matches || !elements.matchesContainer) return;

  const matches = state.data.matches;
  const filtered = matches.filter(m => {
    // 1. Dynamic Age Category / Venue Filter (works for U13, U14, U15 etc.)
    let passFilter = true;
    if (state.activeFilter === 'HOME') passFilter = m.is_home;
    else if (state.activeFilter === 'AWAY') passFilter = !m.is_home;
    else if (state.activeFilter === 'U13') passFilter = m.category === 'U13';
    else if (state.activeFilter === 'U12') passFilter = m.category === 'U12';
    else if (state.activeFilter === 'U11') passFilter = m.category === 'U11';
    else if (state.activeFilter !== 'ALL') passFilter = m.category === state.activeFilter;

    // 2. Search Query Filter
    let passSearch = true;
    if (state.searchQuery) {
      const q = state.searchQuery;
      passSearch = m.opponent.toLowerCase().includes(q) ||
                   m.home_team.toLowerCase().includes(q) ||
                   m.away_team.toLowerCase().includes(q) ||
                   (m.venue && m.venue.toLowerCase().includes(q)) ||
                   m.team_name.toLowerCase().includes(q) ||
                   (m.date && m.date.toLowerCase().includes(q));
    }

    return passFilter && passSearch;
  });

  if (elements.filteredCount) {
    elements.filteredCount.textContent = `${filtered.length} matches`;
  }

  if (filtered.length === 0) {
    elements.matchesContainer.innerHTML = '<p class="text-muted" style="text-align: center; padding: 2rem;">No matches match the selected criteria.</p>';
    return;
  }

  elements.matchesContainer.innerHTML = filtered.map((m, idx) => {
    let outcomeClass = 'outcome-played';
    let outcomeText = m.result || 'Played';
    let outcomeLabel = 'Lineup Verified';

    if (m.outcome === 'WIN') {
      outcomeClass = 'outcome-win';
      outcomeLabel = 'GVI Win';
    } else if (m.outcome === 'LOSS') {
      outcomeClass = 'outcome-loss';
      outcomeLabel = 'Defeat';
    } else if (m.outcome === 'DRAW') {
      outcomeClass = 'outcome-draw';
      outcomeLabel = 'Draw';
    }

    let catClass = 'category-u13';
    if (m.category === 'U12') catClass = 'category-u12';
    else if (m.category === 'U11') catClass = 'category-u11';
    else if (m.category === 'U14') catClass = 'category-u14';
    else if (m.category === 'U15') catClass = 'category-u15';

    const isLatest = idx === 0 && state.activeFilter === 'ALL' && !state.searchQuery;
    const formattedDate = formatDisplayDate(m.date);

    return `
      <div class="match-item-card ${isLatest ? 'latest-match' : ''}">
        <!-- Col 1: Date & Metadata -->
        <div class="col-meta">
          <span class="match-date-badge">${escapeHtml(formattedDate)}</span>
          <span class="match-season-badge">${escapeHtml(m.season)} (${escapeHtml(m.category)}) ${isLatest ? '• 🌟 Latest' : ''}</span>
        </div>

        <!-- Col 2: Fixture Details -->
        <div class="col-fixture">
          <div class="fixture-header">
            <span class="category-tag ${catClass}">${escapeHtml(m.team_name)}</span>
            <span class="ha-tag ${m.is_home ? 'ha-home' : 'ha-away'}">${m.is_home ? 'Home' : 'Away'}</span>
          </div>
          <div class="fixture-teams">
            <span>${escapeHtml(m.home_team)}</span>
            <span class="vs-sep">vs</span>
            <span>${escapeHtml(m.away_team)}</span>
          </div>
          ${m.venue ? `<div class="venue-info">📍 ${escapeHtml(m.venue)}</div>` : ''}
        </div>

        <!-- Col 3: Score & Result -->
        <div class="col-result">
          <div class="outcome-pill ${outcomeClass}">
            <span>${escapeHtml(outcomeText)}</span>
            <span class="outcome-label">${outcomeLabel}</span>
          </div>
        </div>

        <!-- Col 4: DBU Protocol Link -->
        <div class="col-action">
          <a href="${escapeHtml(m.dbu_url)}" target="_blank" rel="noopener noreferrer" class="btn-dbu-protocol">
            DBU Match Sheet ↗
          </a>
        </div>
      </div>
    `;
  }).join('');
}

function renderDevelopmentalJourney(journeyList) {
  if (!elements.journeyTimelineContainer) return;

  if (!journeyList || journeyList.length === 0) {
    elements.journeyTimelineContainer.innerHTML = '<p class="text-muted">No developmental milestones recorded.</p>';
    return;
  }

  elements.journeyTimelineContainer.innerHTML = journeyList.map((item, idx) => {
    const isRecent = idx >= journeyList.length - 2;
    const tournamentsHtml = (item.key_tournaments || []).map(t => `<li>${escapeHtml(t)}</li>`).join('');

    return `
      <div class="timeline-milestone-card ${isRecent ? 'milestone-recent' : ''}">
        <div class="timeline-node">${escapeHtml(item.icon || '⚽')}</div>
        
        <div class="milestone-top">
          <div class="milestone-badges">
            <span class="badge badge-year">${escapeHtml(item.year)}</span>
            <span class="badge badge-age">${escapeHtml(item.age)}</span>
            <span class="badge badge-category">${escapeHtml(item.category)}</span>
            <span class="badge badge-format">${escapeHtml(item.format_badge || item.format)}</span>
          </div>
        </div>

        <h3 class="milestone-title">
          <span>${escapeHtml(item.title)}</span>
        </h3>

        <p class="milestone-desc">${escapeHtml(item.description)}</p>

        ${tournamentsHtml ? `
          <div class="milestone-tournaments">
            <span class="tournaments-label">Registered DBU Tournaments & Festivals:</span>
            <ul class="tournaments-list">
              ${tournamentsHtml}
            </ul>
          </div>
        ` : ''}

        <div class="milestone-callout">
          <span>🎯</span>
          <span><strong>Milestone:</strong> ${escapeHtml(item.milestone)}</span>
        </div>
      </div>
    `;
  }).join('');
}

function switchView(viewName) {
  state.activeView = viewName;

  if (viewName === 'matches') {
    elements.tabMatches.classList.add('active');
    elements.tabJourney.classList.remove('active');
    elements.viewMatches.style.display = 'block';
    elements.viewJourney.style.display = 'none';
  } else {
    elements.tabJourney.classList.add('active');
    elements.tabMatches.classList.remove('active');
    elements.viewMatches.style.display = 'none';
    elements.viewJourney.style.display = 'block';
  }
}

function setupEventListeners() {
  // View Switcher Tabs
  if (elements.tabMatches) {
    elements.tabMatches.addEventListener('click', () => switchView('matches'));
  }
  if (elements.tabJourney) {
    elements.tabJourney.addEventListener('click', () => switchView('journey'));
  }

  // Search Input
  if (elements.matchSearchInput) {
    elements.matchSearchInput.addEventListener('input', (e) => {
      state.searchQuery = e.target.value.toLowerCase().trim();
      renderMatches();
    });
  }
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

window.addEventListener('DOMContentLoaded', init);
