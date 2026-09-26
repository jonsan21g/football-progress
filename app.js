/**
 * Nathaniel Alexander Sanito - Football Progress Web App
 * Consumes pre-built static dataset from ./data/nathaniel-data.json
 * (Updated automatically by GitHub Actions)
 */

const state = {
  data: null,
  activeView: 'matches', // 'matches' | 'journey'
  activeFilter: 'ALL', // 'ALL' | 'U13' | 'U12' | 'U11' | 'HOME' | 'AWAY'
  searchQuery: ''
};

// DOM Elements
const elements = {
  heroName: document.getElementById('hero-name'),
  heroJersey: document.getElementById('hero-jersey'),
  statTotalMatches: document.getElementById('stat-total-matches'),
  statU13Matches: document.getElementById('stat-u13-matches'),
  statU12Matches: document.getElementById('stat-u12-matches'),
  statU11Matches: document.getElementById('stat-u11-matches'),
  statStartYear: document.getElementById('stat-start-year'),
  tabMatches: document.getElementById('tab-matches'),
  tabJourney: document.getElementById('tab-journey'),
  tabMatchesCount: document.getElementById('tab-matches-count'),
  viewMatches: document.getElementById('view-matches'),
  viewJourney: document.getElementById('view-journey'),
  filteredCount: document.getElementById('filtered-count'),
  filterPills: document.querySelectorAll('.filter-pill'),
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

    renderHeroProfile(data.player, data.career_stats);
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

function renderHeroProfile(player, stats) {
  if (elements.heroName) elements.heroName.textContent = player.full_name;
  if (elements.heroJersey) elements.heroJersey.textContent = player.primary_jersey || "8";
  
  if (elements.statTotalMatches) elements.statTotalMatches.textContent = stats.total_matches_tracked;
  if (elements.statU13Matches) elements.statU13Matches.textContent = stats.u13_matches;
  if (elements.statU12Matches) elements.statU12Matches.textContent = stats.u12_matches;
  if (elements.statU11Matches) elements.statU11Matches.textContent = stats.u11_matches;
  if (elements.statStartYear) elements.statStartYear.textContent = "2019";
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
    // 1. Age Category / Venue Filter
    let passFilter = true;
    if (state.activeFilter === 'U13') passFilter = m.category === 'U13';
    else if (state.activeFilter === 'U12') passFilter = m.category === 'U12';
    else if (state.activeFilter === 'U11') passFilter = m.category === 'U11';
    else if (state.activeFilter === 'HOME') passFilter = m.is_home;
    else if (state.activeFilter === 'AWAY') passFilter = !m.is_home;

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

    const catClass = m.category === 'U13' ? 'category-u13' : (m.category === 'U12' ? 'category-u12' : 'category-u11');
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

  // Filter Pills (U13, U12, U11, HOME, AWAY)
  elements.filterPills.forEach(pill => {
    pill.addEventListener('click', () => {
      elements.filterPills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      state.activeFilter = pill.dataset.filter;
      renderMatches();
    });
  });

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

