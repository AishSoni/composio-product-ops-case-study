// Case study renderer - injects data into template
(function() {
  'use strict';

  const data = window.CASE_STUDY_DATA;
  if (!data) {
    console.warn('No case study data found');
    return;
  }

  // Render patterns
  const patternGrid = document.getElementById('pattern-grid');
  if (patternGrid && data.patterns) {
    patternGrid.innerHTML = data.patterns.map(p => `
      <div class="pattern-card">
        <h4>${p.title}</h4>
        <p>${p.desc}</p>
      </div>
    `).join('');
  }

  // Render easy wins
  const easyWins = document.getElementById('easy-wins');
  if (easyWins && data.easyWins) {
    easyWins.innerHTML = data.easyWins.map(r => `
      <li><strong>${r.name}</strong> (${r.category}) - ${r.access}, ${r.verdict}, ${r.mcp} MCP</li>
    `).join('');
  }

  // Render outreach
  const outreach = document.getElementById('outreach');
  if (outreach && data.outreach) {
    outreach.innerHTML = data.outreach.map(r => `
      <li><strong>${r.name}</strong> (${r.category}) - Blocker: ${r.blocker}</li>
    `).join('');
  }

  // Render table rows
  const tableBody = document.getElementById('table-body');
  if (tableBody && data.tableRows) {
    tableBody.innerHTML = data.tableRows.join('');
  }

  // Render verification stats
  const verificationStats = document.getElementById('verification-stats');
  if (verificationStats && data.verification) {
    const v = data.verification;
    verificationStats.innerHTML = `
      <div class="stat"><strong>${v.checked}</strong> URLs checked</div>
      <div class="stat"><strong>${v.live}</strong> live (${Math.round(v.live/v.checked*100)}%)</div>
      <div class="stat warning"><strong>${v.dead}</strong> dead (${Math.round(v.dead/v.checked*100)}%)</div>
      <div class="stat"><strong>24/25</strong> rows verified (96%)</div>
      <div class="stat"><strong>199/200</strong> fields verified (99.5%)</div>
      <div class="stat note">1 row corrected (LinkedIn Ads MCP: community -> none_found)</div>
    `;
  }

  // Render misses
  const misses = document.getElementById('misses');
  if (misses && data.misses) {
    misses.innerHTML = data.misses.map(m => `
      <li><strong>${m.name}</strong> - ${m.field}: ${m.url} (${m.status})</li>
    `).join('');
  }

  // Populate category filter
  const categoryFilter = document.getElementById('filter-category');
  if (categoryFilter && data.tableRows) {
    const rows = data.tableRows;
    const parser = new DOMParser();
    const categories = new Set();
    rows.forEach(rowHtml => {
      const doc = parser.parseFromString('<table><tbody>' + rowHtml + '</tbody></table>', 'text/html');
      const cat = doc.querySelector('tr').dataset.category;
      if (cat) categories.add(cat);
    });
    [...categories].sort().forEach(c => {
      const opt = document.createElement('option');
      opt.value = c; opt.textContent = c;
      categoryFilter.appendChild(opt);
    });
  }

  // Table filtering logic
  const table = document.getElementById('research-table');
  const rows = Array.from(table?.tBodies?.[0]?.rows || []);
  const filters = {
    category: document.getElementById('filter-category'),
    verdict: document.getElementById('filter-verdict'),
    access: document.getElementById('filter-access'),
    mcp: document.getElementById('filter-mcp'),
  };

  function applyFilters() {
    const cat = filters.category.value;
    const ver = filters.verdict.value;
    const acc = filters.access.value;
    const mcp = filters.mcp.value;

    rows.forEach(row => {
      const show = (!cat || row.dataset.category === cat) &&
                   (!ver || row.dataset.verdict === ver) &&
                   (!acc || row.dataset.access === acc) &&
                   (!mcp || row.dataset.mcp === mcp);
      row.style.display = show ? '' : 'none';
    });
  }

  Object.values(filters).forEach(sel => sel?.addEventListener('change', applyFilters));

  document.addEventListener('keydown', (e) => {
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT' || e.target.tagName === 'TEXTAREA') return;
    if (e.key === '1') filters.category?.focus();
    if (e.key === '2') filters.verdict?.focus();
    if (e.key === '3') filters.access?.focus();
    if (e.key === '4') filters.mcp?.focus();
    if (e.key === 'Escape') {
      Object.values(filters).forEach(s => s && (s.value = ''));
      applyFilters();
    }
  });
})();