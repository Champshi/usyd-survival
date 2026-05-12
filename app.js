/* ===================================================================
   USYD Survival Simulator — JavaScript controller

   Bridges DOM events ↔ PyScript-loaded Python game driver.
   The Python module exposes `window.gameDriver` (a WebGameDriver instance).
   We call:
       gameDriver.render()                  — get current state (Python dict)
       gameDriver.submit(action, payload)   — apply user action, get new state
   Python dicts become PyProxy objects in JS; we use `.toJs(...)` to convert.
   =================================================================== */

const COURSES = ['COMP9120', 'COMP9001', 'COMP9601', 'INFO6007'];
const SKILLS  = ['service', 'teaching', 'coding', 'research'];
const SAVE_KEY = 'usyd_survival_save_v1';

// Helper: convert PyProxy (Python dict / list) to plain JS object
function pyToJs(pyObj) {
  if (pyObj == null) return null;
  if (typeof pyObj.toJs === 'function') {
    return pyObj.toJs({ dict_converter: Object.fromEntries });
  }
  return pyObj;
}

// =====================================================================
// PyScript readiness
// =====================================================================
window.addEventListener('py-ready', () => {
  document.getElementById('boot-screen').classList.add('hidden');
  document.getElementById('app').classList.remove('hidden');
  showTitleScreen();
});

// Fallback: if py-ready never fires (e.g. PyScript error), show error after 30s
setTimeout(() => {
  if (!window.gameDriver) {
    const boot = document.getElementById('boot-screen');
    if (boot && !boot.classList.contains('hidden')) {
      boot.querySelector('.boot-sub').textContent = 'Python failed to load.';
      boot.querySelector('.boot-hint').textContent =
        'Try: serve via "python -m http.server" then open http://localhost:8000';
    }
  }
}, 30000);

// =====================================================================
// Title screen
// =====================================================================
function showTitleScreen() {
  document.getElementById('title-screen').classList.remove('hidden');
  document.getElementById('btn-continue').disabled = !localStorage.getItem(SAVE_KEY);
  document.getElementById('btn-continue').style.opacity =
    localStorage.getItem(SAVE_KEY) ? '1' : '0.4';
}

document.getElementById('btn-new-game').addEventListener('click', () => {
  document.getElementById('title-screen').classList.add('hidden');
  startNewGame();
});

document.getElementById('btn-continue').addEventListener('click', () => {
  if (!localStorage.getItem(SAVE_KEY)) return;
  document.getElementById('title-screen').classList.add('hidden');
  loadGame();
});

document.getElementById('btn-help').addEventListener('click', () => {
  document.getElementById('help-modal').classList.remove('hidden');
});

document.getElementById('btn-help-close').addEventListener('click', () => {
  document.getElementById('help-modal').classList.add('hidden');
});

// =====================================================================
// New game / load game
// =====================================================================
function startNewGame() {
  const name = prompt('What should we call your character?', 'Champ') || 'Champ';
  const state = pyToJs(window.gameDriver.submit('start_new'));
  const state2 = pyToJs(window.gameDriver.submit('set_name', { name }));
  applyState(state2);
}

function loadGame() {
  const saved = JSON.parse(localStorage.getItem(SAVE_KEY));
  const state = pyToJs(window.gameDriver.submit('load_save', { data: saved }));
  applyState(state);
  showToast('Game loaded.');
}

function saveGame(state) {
  if (!state.player) return;
  localStorage.setItem(SAVE_KEY, JSON.stringify(state.player));
}

// =====================================================================
// Master state apply: render dashboard + show appropriate action UI
// =====================================================================
function applyState(state) {
  if (!state) return;
  if (state.player) {
    renderHeader(state.player);
    renderStats(state.player);
    renderCourses(state.player);
    renderSkills(state.player);
    renderEventLog(state.player);
  }
  // Auto-save on each render (cheap with localStorage)
  saveGame(state);

  switch (state.state) {
    case 'morning_plan':   renderMorningPlan(state); break;
    case 'custom_plan':    renderCustomPlan(state); break;
    case 'weekend_pick':   renderWeekendPick(state); break;
    case 'event_choice':   renderEventChoice(state); break;
    case 'day_result':     renderDayResult(state); break;
    case 'exam':           renderExam(state); break;
    case 'ending':         renderEnding(state); break;
    case 'name_input':     /* handled in startNewGame */ break;
    default:               renderActionPanel('<p>...</p>');
  }
}

// =====================================================================
// Dashboard rendering
// =====================================================================
function statClass(v, max=100) {
  const r = v / max;
  if (r >= 0.6) return 'good';
  if (r >= 0.3) return 'warn';
  return 'bad';
}

function moneyClass(m) {
  if (m >= 500) return 'good';
  if (m >= 0) return 'warn';
  return 'bad';
}

function pixelBar(value, max, width=14, color='good') {
  const ratio = Math.max(0, Math.min(1, value / max));
  const filled = Math.round(ratio * width);
  const bar = '█'.repeat(filled) + '░'.repeat(width - filled);
  return `<span class="stat-bar ${color}">${bar}</span>`;
}

function renderHeader(p) {
  document.getElementById('hdr-week').textContent = `Week ${p.week}`;
  document.getElementById('hdr-day').textContent = p.day_name;
  const phase = document.getElementById('hdr-phase');
  if (p.exam_phase) {
    phase.textContent = 'EXAM WEEK';
    phase.classList.add('exam');
  } else {
    phase.textContent = 'Study Week';
    phase.classList.remove('exam');
  }
  document.getElementById('hdr-counter').textContent = `Day ${p.total_day} / 105`;
  document.getElementById('hdr-progress').style.width = `${(p.total_day / 105) * 100}%`;
}

function renderStats(p) {
  const eCls = statClass(p.energy);
  const hCls = statClass(p.health);
  const mCls = moneyClass(p.money);
  const stats = document.getElementById('stats-panel');

  stats.querySelector('[data-stat="energy"]').outerHTML = pixelBar(p.energy, 100, 14, eCls).replace('class="stat-bar', 'data-stat="energy" class="stat-bar');
  stats.querySelector('[data-stat="health"]').outerHTML = pixelBar(p.health, 100, 14, hCls).replace('class="stat-bar', 'data-stat="health" class="stat-bar');
  stats.querySelector('[data-stat="money"]').outerHTML  = pixelBar(Math.max(0, p.money), 5000, 14, mCls).replace('class="stat-bar', 'data-stat="money" class="stat-bar');

  setStatValue('energy', `${Math.round(p.energy)}/100`, eCls);
  setStatValue('health', `${Math.round(p.health)}/100`, hCls);
  setStatValue('money',  `$${Math.round(p.money)}`, mCls);
}

function setStatValue(stat, txt, cls) {
  const el = document.querySelector(`[data-stat-value="${stat}"]`);
  el.textContent = txt;
  el.className = `stat-value ${cls}`;
}

function renderCourses(p) {
  const container = document.getElementById('courses-list');
  container.innerHTML = COURSES.map(code => {
    const v = p.courses[code];
    const cls = v >= 50 ? 'good' : v >= 30 ? 'warn' : 'bad';
    return `
      <div class="stat-row">
        <span class="stat-label">${code}</span>
        ${pixelBar(v, 100, 14, cls)}
        <span class="stat-value ${cls}">${v.toFixed(1)}%</span>
      </div>`;
  }).join('');
}

function renderSkills(p) {
  const container = document.getElementById('skills-list');
  container.innerHTML = SKILLS.map(s => {
    const v = p.skills[s];
    return `
      <div class="stat-row">
        <span class="stat-label">${s.charAt(0).toUpperCase()+s.slice(1)}</span>
        ${pixelBar(v, 100, 14, 'good').replace('class="stat-bar good"','class="stat-bar" style="color:var(--magenta)"')}
        <span class="stat-value" style="color:var(--magenta)">${v.toFixed(1)}</span>
      </div>`;
  }).join('');

  const flagsRow = document.getElementById('flags-row');
  const pills = [];
  if (p.addiction_uses > 0) {
    const cls = p.addiction_uses >= 10 ? 'bad' : 'warn';
    pills.push(`<span class="flag-pill ${cls}">Addiction: ${p.addiction_uses}</span>`);
  }
  if (p.ra_days > 0)    pills.push(`<span class="flag-pill good">RA days: ${p.ra_days}</span>`);
  if (p.prof_favor > 0) pills.push(`<span class="flag-pill good">Prof favour: ${p.prof_favor}</span>`);
  if (p.won_lottery)    pills.push(`<span class="flag-pill warn">LOTTERY WINNER</span>`);
  flagsRow.innerHTML = pills.length ? pills.join('') : '<span style="color:var(--text-muted)">(no flags yet)</span>';
}

function renderEventLog(p) {
  const log = document.getElementById('event-log');
  const lines = (p.event_log || []).slice(-12);
  log.innerHTML = lines.map(line => {
    let cls = 'action';
    if (line.includes('[+]')) cls = 'good';
    else if (line.includes('[-]') || line.includes('[!]')) cls = 'bad';
    else if (line.startsWith('Day') || line.startsWith('Welcome') || line.includes('Auto-saved')) cls = 'system';
    return `<p class="${cls}">${escapeHtml(line)}</p>`;
  }).join('');
  log.scrollTop = log.scrollHeight;
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, m => (
    { '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[m]
  ));
}

// =====================================================================
// Action panel renderers — one per game state
// =====================================================================
function renderActionPanel(html) {
  document.getElementById('action-content').innerHTML = html;
}

function renderMorningPlan(state) {
  const presets = state.options.presets || [];
  const cards = presets.map(p => `
    <div class="preset-card" data-preset="${p.key}">
      <div class="label">${p.name}</div>
      <div class="desc">${p.description}</div>
    </div>`).join('');

  renderActionPanel(`
    <h2>:: Morning planning — Week ${state.player.week}, ${state.player.day_name} ::</h2>
    <p>You have <b>8h</b> of active time today. Pick a preset, or go custom:</p>
    <div class="preset-grid">${cards}</div>
    <div class="action-row">
      <button class="btn" id="btn-custom">Custom plan</button>
      <button class="btn" id="btn-back-to-title">Back to Title</button>
    </div>
  `);

  document.querySelectorAll('.preset-card').forEach(card => {
    card.addEventListener('click', () => {
      applyState(pyToJs(window.gameDriver.submit('pick_preset', { preset: card.dataset.preset })));
    });
  });
  document.getElementById('btn-custom').addEventListener('click', () => {
    applyState(pyToJs(window.gameDriver.submit('tweak_preset')));
  });
  document.getElementById('btn-back-to-title').addEventListener('click', () => {
    applyState(pyToJs(window.gameDriver.submit('restart')));
    showTitleScreen();
  });
}

function renderCustomPlan(state) {
  const opts = state.options;
  const courseRows = (opts.courses || []).map(c => `
    <div class="plan-row">
      <label>Study ${c}</label>
      <input type="number" min="0" max="8" value="0" data-plan="study" data-key="${c}">
    </div>`).join('');
  const jobRows = (opts.jobs || []).map(j => `
    <div class="plan-row">
      <label>${j.name} ($${j.pay.toFixed(0)}/h)</label>
      <input type="number" min="0" max="8" value="0" data-plan="work" data-key="${j.key}">
    </div>`).join('');

  renderActionPanel(`
    <h2>:: Custom plan ::</h2>
    <div class="custom-plan-form">
      ${courseRows}
      ${jobRows}
      <div class="plan-row">
        <label>Rest hours</label>
        <input type="number" min="0" max="8" value="0" data-plan="rest">
      </div>
      <div class="plan-row">
        <label>Meal quality</label>
        <select data-plan="meal_quality">
          <option value="0">Skip meal</option>
          <option value="1">Noodles ($5)</option>
          <option value="2" selected>Wentworth ($15)</option>
          <option value="3">Newtown dinner ($30)</option>
        </select>
      </div>
      <div class="plan-row">
        <label>Use stimulants?</label>
        <select data-plan="use_stimulants">
          <option value="false" selected>No</option>
          <option value="true">Yes (+35 energy, -8 health, +1 addiction)</option>
        </select>
      </div>
    </div>
    <div class="plan-summary" id="plan-summary">Total: 0h / 8h</div>
    <div class="action-row">
      <button class="btn btn-primary" id="btn-submit-plan">Execute Plan</button>
      <button class="btn" id="btn-back-presets">Back to Presets</button>
    </div>
  `);

  const inputs = document.querySelectorAll('[data-plan]');
  function updateSum() {
    let total = 0;
    inputs.forEach(inp => {
      if (inp.dataset.plan === 'study' || inp.dataset.plan === 'work' || inp.dataset.plan === 'rest') {
        total += parseInt(inp.value) || 0;
      }
    });
    const sumEl = document.getElementById('plan-summary');
    sumEl.textContent = `Total: ${total}h / 8h`;
    sumEl.classList.toggle('over', total > 8);
  }
  inputs.forEach(inp => inp.addEventListener('input', updateSum));

  document.getElementById('btn-submit-plan').addEventListener('click', () => {
    const plan = { study: {}, work: {}, rest: 0, meal_quality: 2, use_stimulants: false };
    inputs.forEach(inp => {
      const t = inp.dataset.plan;
      const k = inp.dataset.key;
      if (t === 'study') plan.study[k] = parseInt(inp.value) || 0;
      else if (t === 'work') plan.work[k] = parseInt(inp.value) || 0;
      else if (t === 'rest') plan.rest = parseInt(inp.value) || 0;
      else if (t === 'meal_quality') plan.meal_quality = parseInt(inp.value);
      else if (t === 'use_stimulants') plan.use_stimulants = inp.value === 'true';
    });
    applyState(pyToJs(window.gameDriver.submit('submit_custom', { plan })));
  });
  document.getElementById('btn-back-presets').addEventListener('click', () => {
    applyState({ ...state, state: 'morning_plan' });
  });
}

function renderWeekendPick(state) {
  const cards = (state.options.activities || []).map(a => `
    <div class="weekend-card" data-key="${a.key}">
      <div class="label">${a.label}</div>
      <div class="desc">${a.description}</div>
    </div>`).join('');

  renderActionPanel(`
    <h2>:: Weekend — pick one activity ::</h2>
    <div class="weekend-grid">${cards}</div>
  `);

  document.querySelectorAll('.weekend-card').forEach(card => {
    card.addEventListener('click', () => {
      applyState(pyToJs(window.gameDriver.submit('pick_weekend', { key: card.dataset.key })));
    });
  });
}

function renderEventChoice(state) {
  const e = state.pending_event;
  if (!e) return;
  const modal = document.getElementById('event-modal');
  document.getElementById('event-icon').textContent = e.icon;
  document.getElementById('event-name').textContent = e.name;
  document.getElementById('event-description').textContent = e.description;

  const choicesDiv = document.getElementById('event-choices');
  choicesDiv.innerHTML = '';
  e.choices.forEach((c, i) => {
    const btn = document.createElement('button');
    btn.className = 'btn btn-primary';
    btn.textContent = c.label;
    btn.addEventListener('click', () => {
      modal.classList.add('hidden');
      applyState(pyToJs(window.gameDriver.submit('pick_event_choice', { index: i })));
    });
    choicesDiv.appendChild(btn);
  });
  modal.classList.remove('hidden');
  // Render dashboard panel content shown below the modal
  renderActionPanel(`<p>… resolving today's events …</p>`);
}

function renderDayResult(state) {
  const messages = (state.messages || []).map(m => `<p>${escapeHtml(m)}</p>`).join('');
  renderActionPanel(`
    <h2>:: End of day — Week ${state.player.week}, ${state.player.day_name} ::</h2>
    ${messages || '<p>(no events today)</p>'}
    <div class="action-row">
      <button class="btn btn-primary" id="btn-next-day">Next Day →</button>
    </div>
  `);
  document.getElementById('btn-next-day').addEventListener('click', () => {
    applyState(pyToJs(window.gameDriver.submit('next_day')));
  });
}

function renderExam(state) {
  renderActionPanel(`
    <h2 style="color:var(--red)">:: EXAM WEEK ::</h2>
    <p>The semester is over. Time to find out how you did. Good luck.</p>
    <div class="action-row">
      <button class="btn btn-primary" id="btn-run-exams">Sit the Exams</button>
    </div>
  `);
  document.getElementById('btn-run-exams').addEventListener('click', () => {
    applyState(pyToJs(window.gameDriver.submit('run_exams')));
  });
}

function renderEnding(state) {
  const e = state.ending;
  if (!e) return;
  document.getElementById('ending-title').textContent = e.title;
  document.getElementById('ending-text').textContent = e.text;

  const p = state.player;
  const examAvg = p.exam_scores
    ? (Object.values(p.exam_scores).reduce((a,b)=>a+b,0) / 4).toFixed(1)
    : '—';
  document.getElementById('ending-stats').innerHTML = `
    <div>Money: $${Math.round(p.money)}</div>
    <div>Health: ${Math.round(p.health)}/100</div>
    <div>Energy: ${Math.round(p.energy)}/100</div>
    <div>Average exam: ${examAvg}</div>
    <div>Best skill: ${getBestSkill(p)}</div>
  `;
  document.getElementById('ending-modal').classList.remove('hidden');

  // Clear save on ending
  localStorage.removeItem(SAVE_KEY);
}

function getBestSkill(p) {
  let best = 'service'; let bestVal = -1;
  for (const k of SKILLS) if (p.skills[k] > bestVal) { best = k; bestVal = p.skills[k]; }
  return `${best} (${bestVal.toFixed(0)})`;
}

document.getElementById('btn-restart').addEventListener('click', () => {
  document.getElementById('ending-modal').classList.add('hidden');
  applyState(pyToJs(window.gameDriver.submit('restart')));
  showTitleScreen();
});

// =====================================================================
// Toast helper
// =====================================================================
let toastTimeout;
function showToast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.remove('hidden');
  clearTimeout(toastTimeout);
  toastTimeout = setTimeout(() => t.classList.add('hidden'), 2400);
}
