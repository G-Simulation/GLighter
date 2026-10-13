/* Lärmprotokoll / Noise Log – Oberfläche */
(function () {
'use strict';

/* ================= Grundlagen ================= */
const $ = id => document.getElementById(id);
const DPR = () => window.devicePixelRatio || 1;
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const pad = n => String(n).padStart(2, '0');
const hms = ms => { const d = new Date(ms); return pad(d.getHours()) + ':' + pad(d.getMinutes()) + ':' + pad(d.getSeconds()); };
const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const numTxt = x => { x = String(x).replace('-', '−'); return typeof lang !== 'undefined' && lang === 'en' ? x : x.replace('.', ','); };   // deutsche Schreibweise „−70,7“
const f1 = v => v == null || v === '' || !isFinite(+v) ? '–' : numTxt((+v).toFixed(1));
const f2 = v => v == null || v === '' || !isFinite(+v) ? '–' : numTxt((+v).toFixed(2));
const fdb = v => v == null || v === '' || !isFinite(+v) ? (v || '–') : numTxt(String(v));   // Werte aus der Liste (Text) wie gespeichert, nur anders geschrieben
const fmtDur = v => { const x = parseFloat(v); return isNaN(x) ? '–' : numTxt(x < 10 ? x.toFixed(2) : x.toFixed(1)) + ' s'; };

let lang = 'de';
function pickLang(s) { lang = (s && s !== 'auto') ? s : ((navigator.language || 'de').toLowerCase().startsWith('de') ? 'de' : 'en'); }
function t(k, v) {
  let s = (I18N[lang] || I18N.de)[k];
  if (s === undefined) s = I18N.de[k];
  if (s === undefined) return k;
  if (v) for (const x in v) s = s.split('{' + x + '}').join(v[x]);
  return s;
}
function tr() {
  document.documentElement.lang = lang;
  document.title = t('title');
  document.querySelectorAll('[data-i]').forEach(e => { e.textContent = t(e.dataset.i); });
  document.querySelectorAll('[data-ia]').forEach(e => { e.title = t(e.dataset.ia); e.setAttribute('aria-label', t(e.dataset.ia)); });
  document.querySelectorAll('[data-iph]').forEach(e => { e.placeholder = t(e.dataset.iph); });
  if (matchMedia('(pointer: coarse)').matches && $('livenote')) $('livenote').textContent = t('livenote_touch');   // Handy: passende Bedienhinweise
  if (matchMedia('(pointer: coarse)').matches && $('dthint')) $('dthint').textContent = t('dt_hint_touch');
  let seen = true; try { seen = !!localStorage.getItem('laerm_help'); localStorage.setItem('laerm_help', '1'); } catch (e) { }
  if (!seen) document.querySelectorAll('details.hlp').forEach(x => { x.open = true; });     // beim ersten Besuch offen, danach zugeklappt
}

/* Hinweis "sehr leise" wegklickbar (gilt fuer diese Sitzung im Browser) */
const BOFF = new Set((() => { try { return JSON.parse(sessionStorage.getItem('laerm_boff') || '[]'); } catch (e) { return []; } })());
const BX = () => `<button class="bclose" type="button" aria-label="${esc(t('a_close'))}" title="${esc(t('a_close'))}">✕</button>`;
document.addEventListener('click', e => { const b = e.target.closest('.banner .bclose'); if (!b) return; const id = b.closest('.banner').id; BOFF.add(id); try { sessionStorage.setItem('laerm_boff', JSON.stringify([...BOFF])); } catch (x) { } $(id).style.display = 'none'; });
/* Kopfzeile auf dem Handy: Stoppen und Design wandern ins Menue "⋯" */
const MOBILE = matchMedia('(max-width: 600px)');
function placeHeader() {
  const m = $('hmenu'), hd = document.querySelector('header'), into = MOBILE.matches;
  for (const id of ['recbtn', 'themebtn', 'hbbtn']) { const b = $(id); if (into && b.parentNode !== m) m.appendChild(b); if (!into && b.parentNode === m) hd.insertBefore(b, $('sbtn')); }
  if (!into) m.hidden = true;
}
/* Handbuch (eigene Seite, Wiki) – an einer bestimmten Stelle öffnen */
function hbOpen(at) { const th = document.documentElement.getAttribute('data-theme') || ''; const w = window.open('handbuch.html?lang=' + lang + (th ? '&theme=' + th : '') + '#' + (at || ''), 'gaslighter_hb'); if (w) w.focus(); }
document.addEventListener('click', e => { const a = e.target.closest && e.target.closest('[data-hb]'); if (!a) return; e.preventDefault(); e.stopPropagation(); hbOpen(a.dataset.hb); });
const HB_SEC = { s_pro: 'pro', s_thr: 'einstellungen/s_thr', s_time: 'einstellungen/s_time', s_ha: 'home-assistant/regeln', habox: 'home-assistant/regeln', s_sched: 'einstellungen/s_sched', schedbox: 'einstellungen/s_sched',
  s_notes: 'einstellungen/s_notes', s_rec: 'einstellungen/s_rec', s_wav: 'einstellungen/s_wav', s_video: 'einstellungen/s_video', s_misc: 'einstellungen/s_misc', s_audio: 'einstellungen/s_audio',
  srcbox: 'geraete', srcbox1: 'geraete/karte', calbox: 'geraete/einpegeln', s_cal: 'geraete/einpegeln', pfbox: 'ki/tonprofile', s_prof: 'ki/tonprofile', bkbox: 'sicherung', s_backup: 'sicherung',
  rsbox: 'sicherung/zuruecksetzen', s_reset: 'sicherung/zuruecksetzen', diagset: 'fehlerbehebung', s_diag: 'fehlerbehebung' };
function toggleHMenu(e) {
  e.stopPropagation(); const m = $('hmenu'); m.hidden = !m.hidden;
  if (!m.hidden) { const r = $('hmore').getBoundingClientRect(); m.style.top = (r.bottom + 6) + 'px'; m.style.right = Math.max(8, innerWidth - r.right) + 'px'; }
}
document.addEventListener('click', e => { const m = $('hmenu'); if (m && !m.hidden && !e.target.closest('#hmenu,#hmore')) m.hidden = true; });
/* Datum/Uhrzeit lesbar: "So 04.10. 12:25:20" */
function fmtDay(ds) {
  const d = new Date(ds + 'T12:00:00'); if (isNaN(d)) return ds;
  return d.toLocaleDateString(lang === 'en' ? 'en-GB' : 'de-DE', { weekday: 'short', day: '2-digit', month: '2-digit', year: 'numeric' }).replace(',', '');
}
/* Nachweis: Abstand der Spitze zum lautesten Pegel der Zeit davor (ohne Störungen), z. B. laufender Fernseher */
function preInfo(g, pk) {
  if (!g || g.pre_max == null || !g.pre_s || isNaN(pk)) return [];
  const s = g.pre_s, w = s >= 60 ? Math.round(s / 60) + ' min' : s + ' s', d = pk - g.pre_max;
  return [[t(d > 0 ? 'pre_col' : 'pre_col_lt'), (d > 0 ? '+' + numTxt(d.toFixed(1)) : numTxt((-d).toFixed(1))) + ' dB · ' + w, t(d > 0 ? 'pre_tip' : 'pre_tip_no', { w, m: g.pre_max.toFixed(1), d: d.toFixed(1) })]];
}
function fmtWhen(iso) {
  const d = new Date(iso); if (isNaN(d)) return String(iso || '').replace('T', ' ');
  const L = lang === 'en' ? 'en-GB' : 'de-DE';
  return d.toLocaleDateString(L, { weekday: 'short', day: '2-digit', month: '2-digit' }).replace(',', '') + ' ' + d.toLocaleTimeString(L, { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}
/* Design: Auto (folgt Home Assistant, sonst dem Browser), Hell, Dunkel */
let THEME = 'auto'; try { THEME = localStorage.getItem('laerm_theme') || 'auto'; } catch (e) { }
function haDark() {          // Ingress laeuft im selben Ursprung wie Home Assistant: dessen Design laesst sich auslesen
  try {
    const p = window.parent; if (!p || p === window) return null;
    const ha = p.document.querySelector('home-assistant'), d = ha && ha.hass && ha.hass.themes && ha.hass.themes.darkMode;
    return typeof d === 'boolean' ? d : null;
  } catch (e) { return null; }
}
function applyTheme() {
  let res = THEME === 'light' || THEME === 'dark' ? THEME : null;
  if (!res) { const h = haDark(); if (h !== null) res = h ? 'dark' : 'light'; }
  const r = document.documentElement, was = r.getAttribute('data-theme');
  if (res) r.setAttribute('data-theme', res); else r.removeAttribute('data-theme');
  const b = $('themebtn');
  if (b) { b.textContent = (THEME === 'auto' ? '🌓 ' : THEME === 'dark' ? '🌙 ' : '☀ ') + t('th_' + THEME); b.title = t('th_tip'); }
  if (was !== res) { readColors(); if (typeof NV !== 'undefined' && NV.open) drawNight(); }
}
let C = {};
function readColors() {
  try { readNC(); } catch (e) { }
  const cs = getComputedStyle(document.documentElement), g = n => cs.getPropertyValue(n).trim();
  C = { tx: g('--tx'), mut: g('--mut'), bd: g('--bd'), grid: g('--grid'), acc: g('--acc'), thr: g('--thr'), bgl: g('--bgl'), red: g('--red'), pv: g('--pv'), card: g('--card') };
}
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', readColors);

function fit(c) {
  const r = DPR(), w = Math.round(c.clientWidth * r), h = Math.round(c.clientHeight * r);
  if (c.width !== w) c.width = w;
  if (c.height !== h) c.height = h;
}

/* ================= Daten ================= */
const MAXR = 6000, RING = 6000, NB = 32, DELAY = 350;
let recs = [];            // {s, ts, l, b, t, a, w:Int16Array(20), sp:Uint8Array(32)}
let lastSeq = -1, firstAvail = 0, boot = null, st = null, off = 0, offInit = false, CUR = null, bands = [];
let lastCount = -1, lastOk = 0;
let selSrc = 'main', SOURCES = [], PHONE = { port: null, ip: null, tls: false, tls_error: '', ffmpeg: true };

function decode(r) {
  const wb = atob(r[6]), sb = atob(r[7]);
  const nw = Math.min(30, wb.length >> 1), w = new Int16Array(30);   // 20 Min/Max + 10 Effektivwerte (ab 1.7.1)
  for (let i = 0; i < nw; i++) { let v = wb.charCodeAt(2 * i) | (wb.charCodeAt(2 * i + 1) << 8); if (v > 32767) v -= 65536; w[i] = v; }
  const sp = new Uint8Array(NB);
  for (let i = 0; i < NB && i < sb.length; i++) sp[i] = sb.charCodeAt(i);
  return { s: r[0], ts: r[1], l: r[2], b: r[3], t: r[4], a: r[5], w, sp };
}
function lowerBound(ts) { let lo = 0, hi = recs.length; while (lo < hi) { const m = (lo + hi) >> 1; if (recs[m].ts < ts) lo = m + 1; else hi = m; } return lo; }

function resetData() { recs = []; lastSeq = -1; firstAvail = 0; clearRing(); }

async function poll() {
  let again = false;
  try {
    const want = selSrc;
    const res = await fetch((lastSeq < 0 ? 'data?limit=1200' : 'data?since=' + lastSeq) + '&src=' + encodeURIComponent(want), { cache: 'no-store' });
    const j = await res.json();
    if (want !== selSrc || j.src !== selSrc) throw new Error('source switched');   // Antwort einer alten Quelle verwerfen
    if (boot !== null && j.boot !== boot) resetData();          // Add-on wurde neu gestartet
    boot = j.boot;
    const o = j.now - Date.now();
    off = offInit ? off + clamp((o - off) * 0.05, -5, 5) : o; offInit = true;   // Uhrabgleich ganz sanft (Netz-Schwankungen ließen die Anzeige ruckeln)
    firstAvail = j.first; st = j.st; lastOk = Date.now();
    if (st.bands && st.bands.length) bands = st.bands;
    if (j.r.length) {
      const nr = j.r.map(decode);
      if (recs.length && nr[0].s <= recs[recs.length - 1].s) {          // Ueberlappung entfernen
        const ls = recs[recs.length - 1].s; while (nr.length && nr[0].s <= ls) nr.shift();
      }
      for (const r of nr) { recs.push(r); specWrite(r); }
      if (recs.length > MAXR) recs.splice(0, recs.length - MAXR);
      if (nr.length) lastSeq = nr[nr.length - 1].s;
      again = j.r.length >= 1200 && j.last > lastSeq;
    } else if (lastSeq < 0 && j.last > 0) {
      lastSeq = j.last;
    }
    updateStatus();
  } catch (e) { /* naechster Versuch */ }
  setTimeout(poll, again ? 0 : (document.hidden || NV.open || PV.open ? 1000 : 250));
}

/* Wächter: kommen länger keine Daten (z. B. über Nacht die Anmeldung bei Home Assistant abgelaufen oder der Rechner schlief),
   wird geprüft, ob der Server antwortet. Antwortet er nicht mit Daten, sondern mit Anmeldeseite/Fehler, lädt die Seite neu. */
setInterval(async () => {
  if (document.hidden || !lastOk || Date.now() - lastOk < 30000) return;
  let bad = false;
  try {
    const r = await fetch('data?limit=1&src=' + encodeURIComponent(selSrc), { cache: 'no-store' });
    if (r.status === 401 || r.status === 403 || !(r.headers.get('content-type') || '').includes('json')) bad = true;
    else { resetData(); lastOk = Date.now(); }            // Server da: Live-Daten frisch holen
  } catch (e) { return; }                                // Server (noch) nicht erreichbar: weiter warten
  if (bad) {
    let last = 0; try { last = +sessionStorage.getItem('laerm_reload') || 0; } catch (e) { }
    if (Date.now() - last > 120000) { try { sessionStorage.setItem('laerm_reload', String(Date.now())); } catch (e) { } try { (window.top || window).location.reload(); } catch (e) { location.reload(); } }
  }
}, 10000);
document.addEventListener('visibilitychange', () => {    // Rechner/Tab wieder wach: sofort frische Daten
  if (!document.hidden && lastOk && Date.now() - lastOk > 30000) { resetData(); }
});
let loadingOld = false, lastOld = 0;
async function loadOlder() {
  if (loadingOld || !recs.length || recs[0].s <= firstAvail || recs.length >= MAXR || Date.now() - lastOld < 300) return;
  lastOld = Date.now();
  loadingOld = true;
  try {
    const want = selSrc;
    const j = await (await fetch('data?before=' + recs[0].s + '&limit=1200&src=' + encodeURIComponent(want), { cache: 'no-store' })).json();
    if (want !== selSrc || j.src !== selSrc) { loadingOld = false; return; }
    const nr = j.r.map(decode).filter(r => !recs.length || r.s < recs[0].s);
    if (nr.length) { recs = nr.concat(recs); nr.forEach(specWrite); if (recs.length > MAXR) recs.splice(0, recs.length - MAXR); }
  } catch (e) { }
  loadingOld = false;
}

/* ================= Ansicht ================= */
const SPANS = [10, 30, 60, 120, 300, 600];
const view = { live: true, end: 0, span: 60, mode: 'level' };
const yv = { auto: true, lo: -100, hi: -30 };
const wg = { auto: true, g: 50 };
let hoverX = null;

function nowServer() { return Date.now() + off; }
/* Live: Wiedergabe mit kleiner, sich anpassender Verzögerung. Die Messwerte kommen in Paketen; läuft die Anzeige schneller als
   die Daten, endet die Kurve vor dem rechten Rand und springt beim nächsten Paket nach (sieht aus, als ändere sie die Länge).
   Deshalb wird die Verzögerung so geführt, dass immer schon Daten bis zum Rand da sind – sanft, ohne Sprünge. */
const PLAY = { delay: DELAY, minLead: 1e9, t: 0 };
function playAdapt(dt) {
  if (!recs.length || !view.live) return;
  const lead = recs[recs.length - 1].ts - (nowServer() - PLAY.delay);       // so viel liegt schon bereit
  if (lead < 60) PLAY.delay = Math.min(4000, PLAY.delay + Math.min(dt * 0.25, 60 - lead));   // knapp: Anzeige etwas langsamer
  PLAY.minLead = Math.min(PLAY.minLead, lead);
  if (performance.now() - PLAY.t > 3000) {        // 3 s lang immer reichlich da: Verzögerung langsam verkleinern
    if (PLAY.minLead > 250) PLAY.delay = Math.max(DELAY, PLAY.delay - Math.min(100, (PLAY.minLead - 250) / 3));
    PLAY.minLead = 1e9; PLAY.t = performance.now();
  }
}
function viewRange() {
  if (view.live) view.end = nowServer() - PLAY.delay;
  return [view.end - view.span * 1000, view.end];
}
function setLive(on) {
  view.live = on;
  const b = $('livebtn'); b.classList.toggle('paused', !on);
  b.querySelector('b').textContent = t(on ? 'live' : 'paused');
  const g = $('cvbtns'); if (g) g.hidden = on;           // "Zurueck zu Live" / "Bereich pruefen" nur nach dem Zurueckblaettern
}
/* Aufzeichnung starten/stoppen */
let REC_PAUSED = null;
function syncRec(s) {
  const pz = !!(s && s.paused); REC_PAUSED = pz;
  const b = $('recbtn'); b.classList.toggle('off', pz);
  b.querySelector('span').textContent = t(pz ? 'rec_start' : 'rec_stop');
  b.title = t(pz ? 'rec_start_tip' : 'rec_stop_tip');
  const since = s && s.paused_since ? new Date(s.paused_since) : null;
  const until = s && s.paused_until ? new Date(s.paused_until) : null, L = lang === 'en' ? 'en-GB' : 'de-DE';
  const html = !pz ? '' : until && !isNaN(until)
    ? t('rec_banner_until', { u: until.toLocaleTimeString(L, { hour: '2-digit', minute: '2-digit' }), r: s.paused_reason ? ' (' + esc(s.paused_reason) + ')' : '' })
    : t('rec_banner', { t: since && !isNaN(since) ? since.toLocaleString(L, { weekday: 'short', hour: '2-digit', minute: '2-digit' }) : '–' });
  const e = $('b_rec');
  e.style.display = pz ? 'block' : 'none'; if (e.innerHTML !== html) e.innerHTML = html;
}
/* Stoppen: fuer 15 min / 1 h / bis man wieder startet */
function recMenu() {
  let m = $('recmenu');
  if (!m) { m = el('div', { id: 'recmenu', className: 'hmenu recmenu' }); document.body.appendChild(m); document.addEventListener('click', e => { if (!m.hidden && !e.target.closest('#recmenu,#recbtn')) m.hidden = true; }); }
  let last = 30; try { last = +localStorage.getItem('laerm_pausemin') || 30; } catch (e) { }
  m.innerHTML = `<small>${esc(t('rec_menu_t'))}</small>` + [[15, t('rec_15')], [60, t('rec_60')], [180, t('rec_180')]].map(([n, l]) => `<button type="button" class="chip" data-m="${n}">${esc(l)}</button>`).join('') +
    `<div class="recrow"><span class="recin"><input type="number" id="recmin" min="1" max="1440" step="1" value="${last}" inputmode="numeric" aria-label="${esc(t('rec_min'))}"><span>${esc(t('rec_min'))}</span></span><button type="button" class="chip pri" id="recminok">OK</button></div>` +
    `<div class="recrow"><span class="recin"><span>${esc(t('rec_until'))}</span><input type="time" id="recuntil" aria-label="${esc(t('rec_until'))}"></span><button type="button" class="chip pri" id="recuntilok">OK</button></div>` +
    `<input type="text" id="recwhy" maxlength="80" placeholder="${esc(t('rec_reason'))}">` +
    `<button type="button" class="chip" data-m="0">${esc(t('rec_stop_open'))}</button>`;
  const go = async n => {
    m.hidden = true;
    try { const r = await (await fetch('pause', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ minutes: n, reason: $('recwhy').value }) })).json(); if (st) Object.assign(st, { paused: r.paused, paused_since: r.since, paused_until: r.until, paused_reason: r.reason }); syncRec(st || {}); updateStatus(); } catch (e) { alert(t('saveerr')); }
  };
  m.querySelectorAll('button[data-m]').forEach(b => b.onclick = () => { const n = +b.dataset.m; if (n > 0) go(n); else { m.hidden = true; toggleRec(true); } });
  $('recminok').onclick = () => { const n = Math.round(+$('recmin').value); if (!(n >= 1)) return; try { localStorage.setItem('laerm_pausemin', Math.min(1440, n)); } catch (e) { } go(Math.min(1440, n)); };
  $('recmin').onkeydown = e => { if (e.key === 'Enter') $('recminok').click(); };
  $('recuntilok').onclick = () => {                      // bis Uhrzeit (heute, sonst morgen)
    const v = $('recuntil').value; if (!/^\d\d:\d\d$/.test(v)) return;
    const now = new Date(), u = new Date(now); u.setHours(+v.slice(0, 2), +v.slice(3), 0, 0); if (u <= now) u.setDate(u.getDate() + 1);
    go(Math.max(1, Math.ceil((u - now) / 60000)));
  };
  m.hidden = false;
  const r = $('recbtn').getBoundingClientRect(); m.style.top = (r.bottom + 6) + 'px'; m.style.left = Math.max(8, Math.min(innerWidth - m.offsetWidth - 8, r.left)) + 'px'; m.style.right = 'auto';
}
async function toggleRec(sure) {
  const on = REC_PAUSED === true;                     // gestoppt -> starten
  if (!on && sure !== true) { recMenu(); return; }
  if (!on && !confirm(t('rec_confirm'))) return;
  const b = $('recbtn'); b.disabled = true;
  try {
    const r = await (await fetch('recording', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ on }) })).json();
    if (!r.ok) throw new Error(r.error || 'error');
    if (st) { st.paused = r.paused; st.paused_since = r.since; st.paused_until = null; }
    syncRec({ paused: r.paused, paused_since: r.since }); updateStatus();
  } catch (e) { alert(t('saveerr') + ' ' + e.message); }
  b.disabled = false;
}
/* Eigene Referenzlinien des gewaehlten Geraets */
const REF_COLORS = ['#7048e8', '#2b8a3e', '#e8590c', '#1c7ed6', '#c2255c', '#868e96'];
function curRefs(id) { const s = srcById(id || selSrc); return (s && s.refs) || []; }
// Linienbeschriftung mit halbdurchsichtigem Hintergrund (wie bei den Referenzlinien), damit sie ueber der Kurve lesbar bleibt
/* Schwelle außerhalb der Skala: gestrichelt am oberen bzw. unteren Rand (nur die Abschnitte außerhalb), Beschriftung mit Pfeil.
   pts: [[x, Wert], ...] in Zeitfolge. Liefert true, wenn etwas am Rand gezeichnet wurde. */
function thrEdge(c, pts, lo, hi, L, T, pw, ph, d, col, w) {
  let any = false;
  for (const [edge, test] of [[T + 1 * d, v => v > hi], [T + ph - 1 * d, v => v < lo]]) {
    c.beginPath(); let on = false;
    for (const [x, v] of pts) { if (v != null && test(v)) { if (!on) { c.moveTo(Math.max(L, x), edge); on = true; } else c.lineTo(Math.min(L + pw, x), edge); any = true; } else on = false; }
    c.setLineDash([7 * d, 4 * d]); c.strokeStyle = col; c.lineWidth = (w || 2) * d; c.stroke(); c.setLineDash([]);
  }
  return any;
}
const thrTxt = (v, lo, hi) => t('threshold') + ' ' + v.toFixed(1) + ' dB' + (v > hi ? ' ↑' : v < lo ? ' ↓' : '');
function lblBox(c, txt, x, y, col, d) {
  const tw = c.measureText(txt).width, al = c.textAlign, x0 = al === 'right' ? x - tw : al === 'center' ? x - tw / 2 : x;
  c.save(); c.fillStyle = C.card; c.globalAlpha = .85; c.fillRect(x0 - 4 * d, y - 11 * d, tw + 8 * d, 15 * d); c.restore();
  c.fillStyle = col; c.fillText(txt, x, y);
}
// yOf(v) -> Liste von y-Positionen (Balken: oben und gespiegelt unten); lo/hi = sichtbarer Bereich
function drawRefs(c, refs, yOf, lo, hi, L, pw, T, ph, d) {
  if (!refs.length) return;
  c.save(); c.font = '600 ' + (11 * d) + 'px system-ui'; c.textAlign = 'left';
  for (const r of refs) {
    const lab = (r.label ? r.label + ' ' : '') + r.db.toFixed(1) + ' dB';
    if (r.db < lo || r.db > hi) {                        // ausserhalb: kleiner Hinweis am Rand
      const up = r.db > hi, y = up ? T + 12 * d : T + ph - 4 * d;
      c.fillStyle = r.color; c.globalAlpha = .9; c.fillText((up ? '▲ ' : '▼ ') + lab, L + 6 * d, y); c.globalAlpha = 1;
      continue;
    }
    c.strokeStyle = r.color; c.lineWidth = 1.5 * d; c.setLineDash([2 * d, 3 * d]);
    for (const y of yOf(r.db)) { c.beginPath(); c.moveTo(L, y); c.lineTo(L + pw, y); c.stroke(); }
    c.setLineDash([]);
    const y = yOf(r.db)[0], tw = c.measureText(lab).width;
    c.fillStyle = C.card; c.globalAlpha = .85; c.fillRect(L + 4 * d, y - 13 * d, tw + 8 * d, 15 * d); c.globalAlpha = 1;
    c.fillStyle = r.color; c.fillText(lab, L + 8 * d, y - 2 * d);
  }
  c.restore();
}
function goLive() { histExit(); setLive(true); yv.auto = true; if (typeof wg !== 'undefined') wg.auto = true; syncAutoBtn(); markDirty(); }
function spanLabel(s) {
  s = Math.round(s); if (s < 60) return s + ' s';
  if (s < 3600) return (s % 60 ? Math.floor(s / 60) + ':' + pad(s % 60) : s / 60) + ' min';
  const m = Math.round(s / 60); return (m % 60 ? Math.floor(m / 60) + ':' + pad(m % 60) : m / 60) + ' h';
}
function spanSel(s) {                                // Auswahl „Zeitfenster“: feste Stufe oder der gezoomte Wert
  const sel = $('span'); if (!sel) return; let c = sel.querySelector('option[data-cus]');
  const o = [...sel.options].find(x => !x.dataset.cus && +x.value === s);
  if (o) { if (c) c.remove(); sel.value = o.value; return; }
  if (!c) { c = document.createElement('option'); c.dataset.cus = '1'; }
  c.value = String(s); c.textContent = spanLabel(s);
  const nx = [...sel.options].find(x => !x.dataset.cus && +x.value > s); sel.insertBefore(c, nx || null); sel.value = c.value;
}
function setSpan(s) { const was = histOn(); view.span = s; spanSel(s); if (LDT.hist && LDT.zoom) { const e = LDT.to; LDT.from = e - s * 1000; } else if (LONG_SPAN(s)) LDT.zoom = false; if (was || histOn()) syncLongSpan(); }
function setMode(m) {
  view.mode = m;
  $('m_level').classList.toggle('on', m === 'level'); $('m_wave').classList.toggle('on', m === 'wave'); if ($('laybtn')) $('laybtn').hidden = m === 'wave';
  syncAutoBtn();
}
function syncAutoBtn() { if (yv.auto) yv.tlo = yv.thi = null; syncAutoBtn2(); }
function syncAutoBtn2() { $('zauto').classList.toggle('on', yv.auto); $('main').classList.toggle('yfree', !yv.auto); }

/* Auto-Zoom: Bereich eng um die sichtbaren Werte (Pegel, Hintergrund, Schwelle), mind. minSpan dB.
   Mit Hysterese: das Ziel aendert sich nur, wenn Werte herausragen oder der Bereich deutlich zu gross ist. */
function autoY(mn, mx, minSpan, padF) {
  const sp = Math.max(mx - mn, 0.5), pad = Math.max(0.4, sp * padF);
  let lo = mn - pad, hi = mx + pad;
  if (hi - lo < minSpan) { const m = (hi + lo) / 2; lo = m - minSpan / 2; hi = m + minSpan / 2; }
  if (yv.tlo == null || lo < yv.tlo || hi > yv.thi || (yv.thi - yv.tlo) > 1.5 * (hi - lo) + 1) {
    const q = (hi - lo) < 12 ? 0.5 : 1;                   // auf 0,5 bzw. 1 dB runden
    yv.tlo = Math.floor(lo / q) * q; yv.thi = Math.ceil(hi / q) * q;
  }
  const k = smoothK(250);
  yv.lo += (yv.tlo - yv.lo) * k; yv.hi += (yv.thi - yv.hi) * k;
  if (Math.abs(yv.tlo - yv.lo) > 0.05 || Math.abs(yv.thi - yv.hi) > 0.05) animating = true;
}
function timeTicks(t0, t1, maxTicks, minor) {
  const span = (t1 - t0) / 1000;
  const steps = [1, 2, 5, 10, 15, 30, 60, 120, 300, 600];
  const sub = { 1: 0.2, 2: 0.5, 5: 1, 10: 2, 15: 5, 30: 5, 60: 10, 120: 30, 300: 60, 600: 120 };
  let step = steps[steps.length - 1];
  for (const s of steps) if (span / s <= maxTicks) { step = s; break; }
  const out = [], ms = Math.round((minor ? sub[step] : step) * 1000);
  for (let x = Math.ceil(t0 / ms) * ms; x <= t1; x += ms) out.push(x);
  return out;
}
/* dB-Skala: Hauptschritt so fein wie moeglich (Beschriftungen mind. minPx auseinander), dazu Zwischenstriche.
   px = Hoehe (bzw. Breite) in Geraetepixeln fuer den Bereich lo..hi. Liefert [{v, major}] und das Format. */
function dbTicks(lo, hi, px, minPx) {
  const per = px / Math.max(1e-6, hi - lo), d = DPR();
  const steps = [0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50];
  let major = 50; for (const st of steps) if (st * per >= minPx * d) { major = st; break; }
  let minor = major / ((major === 2 || major === 20 || major === 0.2) ? 4 : 5);
  if (minor * per < 5 * d) minor = major / 2;
  if (minor * per < 5 * d) minor = major;
  const out = [], k0 = Math.ceil(lo / minor - 1e-9), k1 = Math.floor(hi / minor + 1e-9);
  for (let k = k0; k <= k1 && out.length < 2000; k++) {
    const v = Math.round(k * minor * 100) / 100, q = v / major;
    out.push({ v, major: Math.abs(q - Math.round(q)) < 1e-6 });
  }
  return { ticks: out, fmt: v => major < 1 ? v.toFixed(1) : String(v) };
}
/* Zeitraster: Hauptlinien und zarte Zwischenlinien */
function timeGrid(c, X, t0, t1, T, ph, col) {
  c.lineWidth = 1; c.strokeStyle = col;
  c.globalAlpha = .4;
  for (const tk of timeTicks(t0, t1, 8, true)) { const x = Math.round(X(tk)) + .5; c.beginPath(); c.moveTo(x, T); c.lineTo(x, T + ph); c.stroke(); }
  c.globalAlpha = 1;
  for (const tk of timeTicks(t0, t1, 8)) { const x = Math.round(X(tk)) + .5; c.beginPath(); c.moveTo(x, T); c.lineTo(x, T + ph); c.stroke(); }
}
/* Raster zeichnen: Hauptlinien kraeftiger mit Beschriftung, Zwischenlinien zart, kurze Striche an der Achse */
function drawDbGrid(c, ys, L, pw, d, label, gridCol, labCol) {
  for (const { y, major, text } of ys) {
    const yy = Math.round(y) + .5;
    c.strokeStyle = gridCol; c.lineWidth = 1; c.globalAlpha = major ? 1 : .45;
    c.beginPath(); c.moveTo(L, yy); c.lineTo(L + pw, yy); c.stroke();
    c.globalAlpha = 1; c.strokeStyle = labCol;
    c.beginPath(); c.moveTo(L - (major ? 5 : 3) * d, yy); c.lineTo(L, yy); c.stroke();
    if (major && label && text != null) { c.fillStyle = labCol; c.fillText(text, L - 7 * d, yy + 4 * d); }
  }
}
const gapBefore = i => i > 0 && recs[i].s !== recs[i - 1].s + 1;
function eventSpans(i0, i1, cb, core) {          // core: nur der Teil ueber der Schwelle (a=2), sonst mit Nachlauf
  let s = -1;
  for (let i = i0; i <= i1 + 1; i++) {
    const on = i <= i1 && recs[i] && (core ? recs[i].a === 2 : recs[i].a);
    if (s >= 0 && (!on || gapBefore(i))) { cb(recs[s].ts - 100, recs[i - 1].ts); s = -1; }
    if (on && s < 0) s = i;
  }
}

/* Vorlauf: Zeit vor dem Ausloesen, die zum Ereignis gehoert (KI-Auswertung, ggf. Ton). Beim Ausloesen rueckwirkend
   markieren - so lang wie fuer das Geraet eingestellt, aber nie in ein vorheriges Ereignis oder ueber eine Datenluecke hinweg. */
function preRollSpans(i0, i1, cb) {
  const c = effCfg(selSrc), pre = (c && c.pre_roll_s != null ? +c.pre_roll_s : 5) * 1000;
  if (!c || !c.save_audio) return groupSpans(i0, i1, cb);   // ohne echten Ton gibt es keinen Vorlauf: Störungen kurz hintereinander zusammenfassen
  if (!(pre > 0)) return;
  for (let i = Math.max(i0, 1); i <= i1; i++) {
    if (!recs[i] || recs[i].a !== 2 || (recs[i - 1].a && !gapBefore(i))) continue;   // nur echter Beginn einer Stoerung
    const end = recs[i].ts - 100; let j = i - 1;
    while (j >= 0 && !recs[j].a && !gapBefore(j + 1) && recs[j].ts - 100 >= end - pre) j--;
    const start = Math.max(end - pre, recs[j + 1] ? recs[j + 1].ts - 100 : end);
    if (end > start) cb(start, end);
  }
}

/* Ohne echten Ton: Störungen, die höchstens „Gruppe: höchste Pause“ auseinander liegen, hell verbunden (wie die Gruppen in der Liste) */
function groupSpans(i0, i1, cb) {
  const gap = ((CUR && CUR.group_pause_s) || 120) * 1000, sp = [];
  eventSpans(i0, i1, (a, b) => sp.push([a, b]), true);
  let cur = null, n = 0;
  for (const [a, b] of sp) {
    if (cur && a - cur[1] <= gap) { cur[1] = b; n++; continue; }
    if (cur && n > 1) cb(cur[0], cur[1]);
    cur = [a, b]; n = 1;
  }
  if (cur && n > 1) cb(cur[0], cur[1]);
}
/* ---------- Pegelspur ---------- */
/* ================= Ebenen (Layer): zusaetzliche Kurven nach Lautstaerke und Frequenz ================= */
const LAY = { lvl: true, bg: true, thr: true, lo: false, mid: false, hi: false, dom: false, cen: false };
try { Object.assign(LAY, JSON.parse(localStorage.getItem('laerm_layers') || '{}')); } catch (e) { }
const LCOL = { lo: '#e8590c', mid: '#2b8a3e', hi: '#7048e8', dom: '#d6336c', cen: '#f59f00' };
const layersOn = () => LAY.lo || LAY.mid || LAY.hi || LAY.dom || LAY.cen;
function deriv(r, centers) {          // aus den 32 Frequenzbaendern: Pegel tief/mittel/hoch, dominante Frequenz, Klangschwerpunkt
  if (r.dv !== undefined) return r.dv;
  if (!centers || centers.length !== NB || !r.sp) return (r.dv = null);
  let pl = 0, pm = 0, ph = 0, mx = -1, mi = 0, sp = 0, sl = 0;
  for (let k = 0; k < NB; k++) {
    const p = Math.pow(10, (r.sp[k] / 2 - 130) / 10), f = centers[k];
    if (f < 250) pl += p; else if (f < 2000) pm += p; else ph += p;
    if (r.sp[k] > mx) { mx = r.sp[k]; mi = k; }
    sp += p; sl += p * Math.log(f);
  }
  const dB = p => p > 0 ? 10 * Math.log10(p) : null;
  return (r.dv = { lo: dB(pl), mid: dB(pm), hi: dB(ph), dom: centers[mi], cen: sp > 0 ? Math.exp(sl / sp) : null });
}
const isSound = r => r.l != null && (r.a || (r.b != null && r.l >= r.b + 6));
function accLayers(acc, r, centers) {
  if (!layersOn()) return;
  const dv = deriv(r, centers); if (!dv) return;
  if (LAY.lo) acc(dv.lo); if (LAY.mid) acc(dv.mid); if (LAY.hi) acc(dv.hi);
}
/* pts: [{x, r, brk}] sichtbare Datensaetze mit Pixel-x. Y = dB-Achse, Frequenz-Ebenen laufen logarithmisch von 50 Hz bis 8 kHz ueber die Hoehe. */
function drawLayers(c, pts, Y, centers, d, L, pw, T, ph) {
  if (!layersOn() || !pts.length) return;
  const F0 = Math.log(50), F1 = Math.log(8000), Yf = f => T + ph * (1 - (Math.log(f) - F0) / (F1 - F0));
  const lines = [['lo', v => v.lo], ['mid', v => v.mid], ['hi', v => v.hi]];
  for (const [id, g] of lines) if (LAY[id]) {
    c.beginPath(); let on = false;
    for (const p of pts) { const dv = deriv(p.r, centers), v = dv ? g(dv) : null; if (v == null || p.brk) on = false; if (v == null) continue; const y = Y(v); if (!on) { c.moveTo(p.x, y); on = true; } else c.lineTo(p.x, y); }
    c.strokeStyle = LCOL[id]; c.lineWidth = 1.5 * d; c.lineJoin = 'round'; c.globalAlpha = .95; c.stroke(); c.globalAlpha = 1;
  }
  if (LAY.cen) {
    c.beginPath(); let on = false;
    for (const p of pts) { const dv = deriv(p.r, centers); if (!dv || !isSound(p.r) || p.brk) on = false; if (!dv || !isSound(p.r)) continue; const y = Yf(dv.cen); if (!on) { c.moveTo(p.x, y); on = true; } else c.lineTo(p.x, y); }
    c.strokeStyle = LCOL.cen; c.lineWidth = 1.6 * d; c.lineJoin = 'round'; c.stroke();
  }
  if (LAY.dom) {
    c.fillStyle = LCOL.dom; c.globalAlpha = .75;
    for (const p of pts) { const dv = deriv(p.r, centers); if (!dv || !isSound(p.r)) continue; c.beginPath(); c.arc(p.x, Yf(dv.dom), 1.8 * d, 0, 7); c.fill(); }
    c.globalAlpha = 1;
  }
  // rechte Frequenzachse (nur wenn eine Frequenz-Ebene an ist) und Legende
  c.font = '600 ' + (10 * d) + 'px system-ui'; c.textAlign = 'right';
  if (LAY.dom || LAY.cen) {
    c.fillStyle = LAY.dom ? LCOL.dom : LCOL.cen; c.globalAlpha = .85;
    for (const f of [100, 200, 500, 1000, 2000, 5000]) { const y = Yf(f); c.fillText((f >= 1000 ? f / 1000 + ' kHz' : f + ' Hz'), L + pw - 4 * d, y - 2 * d); c.fillRect(L + pw - 3 * d, y, 3 * d, 1 * d); }
    c.globalAlpha = 1;
  }
  let lx = L + 8 * d; c.textAlign = 'left';
  for (const id of ['lo', 'mid', 'hi', 'dom', 'cen']) if (LAY[id]) { c.fillStyle = LCOL[id]; const s = '■ ' + t('lay_s_' + id); c.fillText(s, lx, T + 14 * d); lx += c.measureText(s).width + 12 * d; }
}
function buildLayerPop(anchor) {
  let pop = $('laypop');
  if (!pop) { pop = el('div', { id: 'laypop', className: 'laypop' }); document.body.appendChild(pop); document.addEventListener('pointerdown', e => { if (!pop.hidden && !pop.contains(e.target) && !e.target.closest('.laybtn')) pop.hidden = true; }); }
  const rows = [['lvl', ''], ['bg', ''], ['thr', ''], ['lo', LCOL.lo], ['mid', LCOL.mid], ['hi', LCOL.hi], ['dom', LCOL.dom], ['cen', LCOL.cen]];
  pop.innerHTML = `<b>${esc(t('lay_title'))}</b>` + rows.map(([id, col], i) => `${i === 3 ? `<hr><small>${esc(t('lay_freq_grp'))}</small>` : ''}<label><input type="checkbox" data-l="${id}"${LAY[id] ? ' checked' : ''}><i style="background:${col || (id === 'lvl' ? C.acc : id === 'bg' ? C.bgl : C.thr)}"></i>${esc(t('lay_' + id))}</label>`).join('') + `<small class="lh">${esc(t('lay_hint'))}</small>`;
  pop.querySelectorAll('input').forEach(i => i.onchange = () => {
    LAY[i.dataset.l] = i.checked; try { localStorage.setItem('laerm_layers', JSON.stringify(LAY)); } catch (e) { }
    markDirty(); if ($('evdlg').open) evDraw(); if (histOn()) dtDraw(LDT);
  });
  const host = $('evdlg').open ? $('evdlg') : document.body;
  if (pop.parentNode !== host) host.appendChild(pop);
  pop.hidden = false;
  const r = anchor.getBoundingClientRect();
  pop.style.top = Math.min(innerHeight - pop.offsetHeight - 8, r.bottom + 6) + 'px';
  pop.style.left = Math.max(8, Math.min(innerWidth - pop.offsetWidth - 8, r.right - pop.offsetWidth)) + 'px';
}

/* ================= Kurven mit uPlot (MIT, github.com/leeoniya/uPlot) =================
   uPlot zeichnet Raster, Achsen und die Pegel-Kurven bzw. Lautstärke-Balken. Unsere Leinwand liegt genau darüber
   (durchsichtig): Bedienung, Störungen, Notizen, Beschriftungen, Tooltips. Spektrogramm und Druck bleiben eigene Bilder. */
const UPS = new WeakMap();
function dayTicks(a, b, maxT) {                      // Zeitmarken für lange Zeiträume, auf volle Ortszeit
  const steps = [1e3, 2e3, 5e3, 10e3, 30e3, 60e3, 120e3, 300e3, 600e3, 900e3, 1800e3, 3600e3, 7200e3, 10800e3, 21600e3, 43200e3, 864e5, 1728e5, 6048e5];
  const st = steps.find(s2 => (b - a) / s2 <= maxT) || 6048e5, tz = new Date(a).getTimezoneOffset() * 60000, out = [];
  for (let x = Math.ceil((a - tz) / st) * st + tz; x <= b && out.length < 200; x += st) out.push(x);
  return { ticks: out, step: st };
}
function upLabel(ms, step) { const d = new Date(ms); return step < 60e3 ? hms(ms) : step < 864e5 ? pad(d.getHours()) + ':' + pad(d.getMinutes()) : pad(d.getDate()) + '.' + pad(d.getMonth() + 1) + '.'; }
function upHide(cv) { const e = UPS.get(cv); if (e) e.host.style.display = 'none'; }
/* cfg: { kind: 'lvl' | 'wave', L, R, T, B (CSS-Pixel wie unsere Zeichnung), pal(): Farben, day: lange Zeitachse, act: Störung rot auf der Kurve } */
const AXL = () => innerWidth < 600 ? 40 : 52;     // Live-Bild: Breite der dB-Beschriftung (Handy schmaler, ohne „dB“ je Zahl)
function upGet(cv, cfg) {
  const key = [cfg.kind, cfg.L, cfg.R, cfg.T, cfg.B, !!cfg.day, !!cfg.act, !!cfg.rel].join('|');
  let e = UPS.get(cv);
  if (e && e.key !== key) { e.u.destroy(); e.host.remove(); e = null; }
  if (!e) {
    let wrap = cv.parentNode;
    if (!wrap.classList.contains('upw')) {
      if (wrap.classList.contains('ndcvw')) wrap.classList.add('upw');
      else { wrap = document.createElement('div'); wrap.className = 'upw'; cv.parentNode.insertBefore(wrap, cv); wrap.appendChild(cv); }
    }
    const host = document.createElement('div'); host.className = 'uphost'; wrap.insertBefore(host, cv);
    const P = cfg.pal, font = '11px system-ui', axisCol = () => P().mut, gridCol = () => P().grid;
    const xAxis = { scale: 'x', size: cfg.B, stroke: axisCol, font, gap: 4, grid: { stroke: gridCol, width: 1 }, ticks: { stroke: gridCol, width: 1, size: 4 },
      splits: (u, ai, a, b) => {
        if (cfg.rel) { const st = ([0.5, 1, 2, 5, 10, 15, 30, 60].find(q => (b - a) / 1000 / q <= 10) || 60) * 1000, out = []; for (let x = Math.ceil(a / st) * st; x <= b; x += st) out.push(x); return out; }
        return cfg.day ? dayTicks(a, b, Math.max(3, Math.min(12, Math.floor(u.bbox.width / DPR() / 72)))).ticks : timeTicks(a, b, Math.max(3, Math.min(8, Math.floor(u.bbox.width / DPR() / 80))));   // schmal (Handy): weniger Uhrzeiten
      },
      values: (u, sp) => { const st = sp.length > 1 ? sp[1] - sp[0] : 60e3; return sp.map(v => cfg.rel ? (Math.round(v / 100) / 10) + ' s' : cfg.day ? upLabel(v, st) : hms(v)); } };
    let yAxis;
    if (cfg.kind === 'wave') {                        // Balken gespiegelt um die Mitte: Beschriftung oben in dB
      yAxis = { scale: 'y', size: cfg.L, stroke: axisCol, font, gap: 4, grid: { stroke: gridCol, width: 1 }, ticks: { show: false },
        splits: u => { const m = u._wv; if (!m) return [0]; const out = [0]; for (const k of m.ticks) { const f = m.F(k.v); if (f > 0.04) out.push(f, -f); } return out; },
        values: (u, sp) => sp.map(v => { const m = u._wv; if (!m || v <= 0) return ''; const k = m.ticks.find(q => Math.abs(m.F(q.v) - v) < 1e-9); return k ? m.fmt(k.v) + (cfg.day || cfg.L < 52 ? '' : ' dB') : ''; }) };
    } else {
      yAxis = { scale: 'y', size: cfg.L, stroke: axisCol, font, gap: 4, grid: { stroke: gridCol, width: 1 }, ticks: { stroke: gridCol, width: 1, size: 3 },
        splits: (u, ai, a, b) => dbTicks(a, b, u.bbox.height, cfg.day ? 18 : 24).ticks.filter(k => k.major).map(k => k.v),
        values: (u, sp) => { const f = dbTicks(u.scales.y.min, u.scales.y.max, u.bbox.height, cfg.day ? 18 : 24).fmt; return sp.map(v => f(v) + (cfg.day || cfg.L < 52 ? '' : ' dB')); } };
    }
    let series;
    if (cfg.kind === 'wave') {
      const bars = uPlot.paths.bars({ size: [0.82, Infinity, 1], align: 1 });
      const mk = (col, a) => ({ scale: 'y', paths: bars, fill: () => ca(P()[col], a), stroke: () => 'transparent', width: 0, fillTo: () => 0, points: { show: false } });
      series = [{}, mk('acc', 0.75), mk('warn', 1), mk('red', 1), mk('acc', 0.75), mk('warn', 1), mk('red', 1)];
    } else {
      series = [{}, { scale: 'y', stroke: () => P().acc, width: cfg.day ? 1.2 : 1.6, fill: () => ca(P().acc, cfg.day ? 0.22 : 0.15), fillTo: u => u.scales.y.min, points: { show: false } },   // Fläche nach unten (sonst bis 0 dB nach oben)
        { scale: 'y', stroke: () => P().bgl, width: 1.5, points: { show: false } },
        { scale: 'y', stroke: () => P().thr, width: cfg.day ? 1.5 : 2, dash: cfg.day ? [4, 3] : [7, 4], paths: uPlot.paths.stepped({ align: 1 }), points: { show: false } }];
      if (cfg.act) series.push({ scale: 'y', stroke: () => P().red, width: 1.6, points: { show: false } });
    }
    const opts = { width: Math.max(50, cv.clientWidth), height: Math.max(40, cv.clientHeight), pxAlign: 1, legend: { show: false }, select: { show: false },
      cursor: { show: false, drag: { x: false, y: false }, points: { show: false } },
      padding: [cfg.T, cfg.R, 0, 0], scales: { x: { time: false, auto: false }, y: { auto: false, range: (u, a, b) => [a, b] } },
      axes: [xAxis, yAxis], series };
    const u = new uPlot(opts, series.map(() => []), host);
    e = { u, host, key, dk: null }; UPS.set(cv, e);
  }
  e.host.style.display = '';
  const w = Math.max(50, cv.clientWidth), h = Math.max(40, cv.clientHeight);
  if (e.u.width !== w || e.u.height !== h) e.u.setSize({ width: w, height: h });
  return e;
}
const dayPal = () => ({ acc: NC.acc, bgl: NC.mut, thr: NC.warn, red: NC.red, warn: NC.warn, grid: NC.grid, mut: NC.mut });
let UPID = 0;
function dayData(r, wave, F) {                       // Verlauf: Abschnitte (Mitte), Lücken unterbrechen die Linie
  const step = r.step || (r.to - r.from) / 1200, half = step / 2, gapMs = Math.max(400, 3 * step);
  if (wave) {
    const X = [], S = [[], [], [], [], [], []];
    for (const p of r.pts) { if (p[1] == null) continue; const v = Math.max(0.012, F(p[1])), tv = p[4], k = tv == null ? 0 : p[1] >= tv ? 2 : p[1] >= tv - 3 ? 1 : 0;
      X.push(p[0]); for (let j = 0; j < 6; j++) S[j].push(j === k ? v : j === k + 3 ? -v : null); }
    return [X, ...S];
  }
  const X = [], P = [], Bg = [], Th = [], Ac = []; let prev = null;
  for (const p of r.pts) {
    if (prev != null && p[0] - prev > gapMs) { X.push(prev + half + 1); P.push(null); Bg.push(null); Th.push(null); Ac.push(null); }
    X.push(p[0] + half); P.push(p[1]); Bg.push(p[3]); Th.push(p[4]); Ac.push(p[5] && p[1] != null ? p[1] : null); prev = p[0];
  }
  return [X, P, Bg, Th, Ac];
}
const livePal = () => ({ acc: C.acc, bgl: C.bgl, thr: C.thr, red: C.red, warn: C.thr, grid: C.grid, mut: C.mut });
function liveLvlData() {                             // Live-Pegelspur: Zeit, Pegel, Hintergrund, Schwelle (Lücken unterbrechen die Linie)
  const n = recs.length, X = [], P = [], Bg = [], Th = [];
  for (let i = 0; i < n; i++) {
    const r = recs[i];
    if (i && gapBefore(i)) { X.push(r.ts - 51); P.push(null); Bg.push(null); Th.push(null); }
    X.push(r.ts - 50); P.push(r.l != null && r.l > -125 ? r.l : null); Bg.push(r.b != null ? r.b : null); Th.push(r.t != null ? r.t : null);
  }
  return [X, P, Bg, Th];
}
function waveData(group, F) {                       // Lautstärke-Balken: je Gruppe der lauteste Block, Farbe nach Abstand zur Schwelle
  const X = [], S = [[], [], [], [], [], []]; let cur = null;
  const push = () => { if (!cur) return; const v = Math.max(0.012, F(cur.l)), k = cur.t == null ? 0 : cur.l >= cur.t ? 2 : cur.l >= cur.t - 3 ? 1 : 0;
    X.push(cur.ts0); for (let j = 0; j < 6; j++) S[j].push(j === k ? v : j === k + 3 ? -v : null); };
  for (let i = 0; i < recs.length; i++) {
    const r = recs[i], gid = Math.floor(r.s / group);
    if (!cur || cur.gid !== gid || gapBefore(i)) { push(); cur = { gid, ts0: r.ts - 100, l: r.l, t: r.t }; }
    else { if (r.l > cur.l) cur.l = r.l; if (r.t != null) cur.t = r.t; }
  }
  push();
  return [X, ...S];
}
/* Daten und Ausschnitt setzen; dk: Kennung der Daten (nur bei Änderung neu übergeben) */
function upDraw(e, dk, mkData, x0, x1, y0, y1) {
  const u = e.u;
  u.batch(() => {
    if (e.dk !== dk) { e.dk = dk; u.setData(mkData(), false); }
    u.setScale('x', { min: x0, max: x1 });
    u.setScale('y', { min: y0, max: y1 });
  });
}
function drawLevel(cv, t0, t1) {
  fit(cv);
  const d = DPR(), c = cv.getContext('2d'), w = cv.width, h = cv.height;
  const L = AXL() * d, R = 14 * d, T = 10 * d, B = 22 * d, pw = w - L - R, ph = h - T - B;   // unten Platz für die Zeitachse
  const X = ts => L + pw * (ts - t0) / (t1 - t0);
  const i0 = Math.max(0, lowerBound(t0 - 200)), i1 = Math.min(recs.length - 1, lowerBound(t1 + 200));
  // Auto-Zoom
  if (i1 >= i0) {
    let mn = 1e9, mx = -1e9;
    const acc = v => { if (v != null && v > -125) { if (v < mn) mn = v; if (v > mx) mx = v; } };
    for (let i = i0; i <= i1; i++) { const r = recs[i]; if (LAY.lvl) acc(r.l); if (LAY.bg) acc(r.b); accLayers(acc, r, bands); }   // Schwelle zählt nicht (steht sonst am Rand)
    if (mn <= mx) {
      yv.dmn = mn; yv.dmx = mx; yv.dmed = recs[Math.min(i1, (i0 + i1) >> 1)].l;
      if (yv.auto) autoY(mn, mx, 3, 0.08);
      else if (yv.anchor) {                              // hineingezoomt: unten bündig am tiefsten Wert, nur die Höhe ist gezoomt
        const sp = yv.span || (yv.hi - yv.lo), lo = Math.floor((mn - Math.max(0.3, sp * 0.03)) * 10) / 10, k = smoothK(250);
        yv.lo += (lo - yv.lo) * k; yv.hi += (lo + sp - yv.hi) * k;
        if (Math.abs(lo - yv.lo) > 0.05 || Math.abs(lo + sp - yv.hi) > 0.05) animating = true;
      }
    }
  }
  const Y = v => T + ph * (1 - clamp((v - yv.lo) / (yv.hi - yv.lo), 0, 1));
  c.clearRect(0, 0, w, h);
  // Raster, Achsen, Pegel, Hintergrund, Schwelle: uPlot
  const up = upGet(cv, { kind: 'lvl', L: AXL(), R: 14, T: 10, B: 22, pal: livePal });
  up.u.setSeries(1, { show: !!LAY.lvl }); up.u.setSeries(2, { show: !!LAY.bg }); up.u.setSeries(3, { show: !!LAY.thr });
  upDraw(up, recs.length + ':' + (recs.length ? recs[0].s + ':' + recs[recs.length - 1].s : ''), liveLvlData, t0, t1, yv.lo, yv.hi);
  if (i1 < i0) return;
  c.save(); c.beginPath(); c.rect(L, T, pw, ph); c.clip();
  // Ereignisse
  { const light = (a, b) => { c.fillStyle = C.red + '06'; c.fillRect(X(a), T, X(b) - X(a), ph); c.fillStyle = C.red + '55'; c.fillRect(X(a), T, X(b) - X(a), 2 * d); };
    eventSpans(i0, i1, light); preRollSpans(i0, i1, light); }               // Nachlauf und Vorlauf hellrot
  eventSpans(i0, i1, (a, b) => { c.fillStyle = C.red + '0e'; c.fillRect(X(a), T, X(b) - X(a), ph); c.fillStyle = C.red; c.fillRect(X(a), T, X(b) - X(a), 3 * d); }, true);
  if (layersOn()) {
    const step = Math.max(1, Math.floor((i1 - i0) / (pw / d * 2))), pts = [];
    for (let i = i0; i <= i1; i += step) pts.push({ x: X(recs[i].ts - 50), r: recs[i], brk: gapBefore(i) });
    drawLayers(c, pts, Y, bands, d, L, pw, T, ph);
  }
  drawRefs(c, curRefs(), v => [Y(v)], yv.lo, yv.hi, L, pw, T, ph, d);
  if (LAY.thr) { const tp = []; for (let i = i0; i <= i1; i++) { if (gapBefore(i)) tp.push([X(recs[i].ts - 51), null]); tp.push([X(recs[i].ts - 50), recs[i].t]); } thrEdge(c, tp, yv.lo, yv.hi, L, T, pw, ph, d, C.thr, 2); }   // Schwelle außerhalb: am Rand
  // Live-Punkt
  const lr = recs[i1];
  if (view.live && lr) {
    const x = X(lr.ts - 50), y = Y(lr.l), p = (Date.now() % 1200) / 1200;
    c.fillStyle = C.acc; c.beginPath(); c.arc(x, y, 3.5 * d, 0, 7); c.fill();
    c.strokeStyle = C.acc; c.globalAlpha = 1 - p; c.lineWidth = 1.5 * d; c.beginPath(); c.arc(x, y, (4 + 9 * p) * d, 0, 7); c.stroke(); c.globalAlpha = 1;
  }
  c.restore();
  // Beschriftung rechts
  if (lr) {
    c.font = '600 ' + (11 * d) + 'px system-ui'; c.textAlign = 'right';
    if (lr.t != null && LAY.thr) {
      const out = lr.t > yv.hi || lr.t < yv.lo;
      lblBox(c, out ? thrTxt(lr.t, yv.lo, yv.hi) : t('threshold') + ' ' + lr.t.toFixed(1), L + pw - 4 * d, lr.t > yv.hi ? T + 16 * d : lr.t < yv.lo ? T + ph - 6 * d : Y(lr.t) - 5 * d, C.thr, d);
    }
    if (lr.b != null && LAY.bg) {                     // außerhalb: unter bzw. über der Schwellen-Beschriftung, mit Pfeil
      const up = lr.b > yv.hi, dn = lr.b < yv.lo;
      lblBox(c, t('background') + ' ' + lr.b.toFixed(1) + (up ? ' ↑' : dn ? ' ↓' : ''), L + pw - 4 * d, up ? T + 34 * d : dn ? T + ph - 24 * d : Y(lr.b) + 14 * d, C.bgl, d);
    }
  }
  drawHover(c, X, Y, L, T, pw, ph, d, t0, t1, false);
}
/* Zeitachse unter der Pegelspur bzw. den Lautstärke-Balken (wie unter dem Spektrogramm) */
function drawTimeAxis(c, X, L, T, pw, ph, h, d, t0, t1) {
  c.save(); c.font = (11 * d) + 'px system-ui'; c.textAlign = 'center'; c.fillStyle = C.mut;
  for (const tk of timeTicks(t0, t1, 8, true)) { const x = X(tk); if (x >= L && x <= L + pw) c.fillRect(x - .5, T + ph, 1, 2 * d); }
  for (const tk of timeTicks(t0, t1, 8)) { const x = X(tk); if (x < L || x > L + pw) continue; c.fillRect(x - .5, T + ph, 1, 5 * d); const s2 = hms(tk), hw = c.measureText(s2).width / 2; if (x - hw < L || x + hw > L + pw) continue; c.fillText(s2, x, h - 5 * d); }
  c.restore();
}

/* ---------- Wellenform ---------- */
function drawWave(cv, t0, t1) {
  /* Lautstaerke-Balken (Sprachmemo-Stil): Balkenhoehe = Pegel in dB, Farbe = unter / nahe / ueber der Schwelle */
  fit(cv);
  const d = DPR(), c = cv.getContext('2d'), w = cv.width, h = cv.height;
  const L = AXL() * d, R = 14 * d, T = 10 * d, B = 22 * d, pw = w - L - R, ph = h - T - B, mid = T + ph / 2;   // unten Platz für die Zeitachse
  const X = ts => L + pw * (ts - t0) / (t1 - t0);
  const i0 = Math.max(0, lowerBound(t0 - 200)), i1 = Math.min(recs.length - 1, lowerBound(t1 + 200));
  if (i1 >= i0) {                                   // gleiche Auto-Skala wie die Pegelspur, unten etwas Luft
    let mn = 1e9, mx = -1e9;
    const acc = v => { if (v != null && v > -125) { if (v < mn) mn = v; if (v > mx) mx = v; } };
    for (let i = i0; i <= i1; i++) { const r = recs[i]; acc(r.l); acc(r.b); }
    if (mn <= mx) { yv.dmn = mn; yv.dmx = mx; yv.dmed = recs[Math.min(i1, (i0 + i1) >> 1)].l; if (yv.auto) autoY(mn - 2, mx, 5, 0.08); }   // leise Balken bleiben sichtbar
  }
  const F = v => clamp((v - yv.lo) / (yv.hi - yv.lo), 0, 1);      // 0 = unten (leise), 1 = oben (laut)
  const Hh = v => Math.max(1.5 * d, F(v) * ph / 2);
  c.clearRect(0, 0, w, h);
  // Raster, Achsen und Balken: uPlot (gespiegelt um die Mitte; mehrere 100-ms-Blöcke je Balken, feste Gruppen, lautester zählt)
  const pxPer = pw / ((t1 - t0) / 100), group = Math.max(1, Math.ceil((3 * d) / pxPer));
  const up = upGet(cv, { kind: 'wave', L: AXL(), R: 14, T: 10, B: 22, pal: livePal });
  up.u._wv = { ticks: dbTicks(yv.lo, yv.hi, ph / 2, 22).ticks.filter(k => k.major), F, fmt: dbTicks(yv.lo, yv.hi, ph / 2, 22).fmt };
  const ylo = Math.round(yv.lo * 20) / 20, yhi = Math.round(yv.hi * 20) / 20;
  upDraw(up, [recs.length, recs.length ? recs[0].s + ':' + recs[recs.length - 1].s : '', group, ylo, yhi].join('|'), () => waveData(group, F), t0, t1, -1, 1);
  if (i1 < i0) return;
  c.save(); c.beginPath(); c.rect(L, T, pw, ph); c.clip();
  { const light = (a, b) => { c.fillStyle = C.red + '0a'; c.fillRect(X(a), T, X(b) - X(a), ph); }; eventSpans(i0, i1, light); preRollSpans(i0, i1, light); }
  eventSpans(i0, i1, (a, b) => { c.fillStyle = C.red + '14'; c.fillRect(X(a), T, X(b) - X(a), ph); }, true);
  drawRefs(c, curRefs(), v => [mid - F(v) * ph / 2, mid + F(v) * ph / 2], yv.lo, yv.hi, L, pw, T, ph, d);
  // Schwelle und Hintergrund als Linien
  const lr = recs[i1];
  for (const [key, col, lab, dash] of [['b', C.bgl, t('background'), [3, 4]], ['t', C.thr, t('threshold'), [8, 4]]]) {
    // Verlauf ueber die Zeit (wandert mit dem Hintergrund), oben und gespiegelt unten
    c.setLineDash(dash.map(q => q * d)); c.strokeStyle = col; c.lineWidth = 2 * d;
    for (const sg of [1, -1]) {
      c.beginPath(); let on = false, py = 0;
      for (let i = i0; i <= i1; i++) {
        const v = recs[i][key]; if (v == null || gapBefore(i)) { on = false; if (v == null) continue; }
        const x = X(recs[i].ts - 50), y = mid - sg * F(v) * ph / 2;
        if (!on) { c.moveTo(x, y); on = true; } else { c.lineTo(x, py); c.lineTo(x, y); }
        py = y;
      }
      c.stroke();
    }
    c.setLineDash([]);
    const v = lr[key];
    if (v == null || ((v < yv.lo || v > yv.hi) && key !== 't')) continue;
    const off = F(v) * ph / 2; c.textAlign = 'right'; c.font = '600 ' + (11 * d) + 'px system-ui';
    const txt = key === 't' ? thrTxt(v, yv.lo, yv.hi) : lab + ' ' + v.toFixed(1) + ' dB', ty = lab === t('background') ? mid - off + 15 * d : mid - off - 5 * d, tw = c.measureText(txt).width;
    c.fillStyle = C.card; c.globalAlpha = .85; c.fillRect(L + pw - 8 * d - tw, ty - 11 * d, tw + 8 * d, 15 * d); c.globalAlpha = 1;   // lesbar ueber den Balken
    c.fillStyle = col; c.fillText(txt, L + pw - 4 * d, ty);
  }
  c.restore();
  drawHover(c, X, null, L, T, pw, ph, d, t0, t1, true);
}

/* Bereich markieren (Live-Bild und Verlauf in Protokolle): Knopf „🏷 Bereich markieren“, dann Bereich waagerecht aufziehen und
   benennen. Eine vorhandene Art (Tonprofil oder benannter Bereich) kann gewählt werden – gleicher Name = gleiche Art, die KI lernt daraus. */
const MK = { on: false, sel: null, names: null, pop: null };
function toast(msg, ms) {
  let el_ = $('toast'); if (!el_) { el_ = el('div', { id: 'toast', className: 'toast' }); el_.setAttribute('role', 'status'); document.body.appendChild(el_); }
  el_.textContent = msg; el_.classList.add('on'); clearTimeout(el_._t); el_._t = setTimeout(() => el_.classList.remove('on'), ms || 4000);
}
document.addEventListener('click', e => { if (e.target.closest && e.target.closest('.mkend')) mkSet(false); });
function mkSet(on) {
  MK.on = !!on; if (MK.on && typeof DR !== 'undefined' && DR.on) drSet(false); document.body.classList.toggle('marking', MK.on);
  document.querySelectorAll('.mkbtn').forEach(b => { b.classList.toggle('on', MK.on); b.setAttribute('aria-pressed', String(MK.on)); });
  if (MK.on) mkNames(); else mkClose();                 // Hinweis steht direkt über dem Graphen (.mkhint)
}
/* 🗑 Bereich löschen (Verlauf in Protokolle): Zeitraum aufziehen, alle Störungen darin löschen – Tagesaufzeichnung und
   Prüfsummen-Kette bleiben unverändert, an der Stelle entsteht eine Notiz als Hinweis */
const DR = { on: false };
function drSet(on) {
  DR.on = !!on; if (DR.on && MK.on) mkSet(false); document.body.classList.toggle('marking', DR.on || MK.on);
  document.querySelectorAll('.drbtn').forEach(b => { b.classList.toggle('on', DR.on); b.setAttribute('aria-pressed', String(DR.on)); });
  if (DR.on) toast(t('dr_on'), 6000);
}
async function drOpen(src, a, b) {
  drSet(false);
  let d = $('drdlg');
  if (!d) { d = el('dialog', { id: 'drdlg', className: 'evdlg drdlg' }); document.body.appendChild(d); }
  const L = locale(), fd = x => new Date(x).toLocaleString(L, { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit' });
  d.innerHTML = `<h3>🗑 ${esc(t('dr_title'))}</h3><p><b>${esc(fd(a))} – ${esc(fd(b))}</b></p>
    <label class="drl">${esc(t('a_device'))} <select id="drsrc"></select></label>
    <p id="drcnt" class="drcnt">…</p>
    <label class="drl">${esc(t('dr_note'))}<input type="text" id="drnote" maxlength="300" placeholder="${esc(t('dr_note_ph'))}"></label>
    <p class="mut">${esc(t('dr_hint'))}</p>
    <div class="ntedbtns"><button type="button" class="drx">${esc(t('cancel'))}</button><button type="button" class="danger drgo" disabled>🗑 ${esc(t('dr_go'))}</button></div>`;
  const sel = d.querySelector('#drsrc'); option(sel, 'all', t('all_sources')); viewSources().forEach(x => option(sel, x.id, viewName(x.id))); sel.value = [...sel.options].some(o => o.value === src) ? src : 'all';
  const go = d.querySelector('.drgo'), cnt = d.querySelector('#drcnt');
  const count = async () => {
    cnt.textContent = '…'; go.disabled = true;
    try { const j = await (await fetch('delete_range', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ a, b, src: sel.value, preview: 1 }) })).json(); cnt.textContent = t('dr_count', { n: j.n || 0 }); go.disabled = !j.n; } catch (e) { cnt.textContent = t('saveerr'); }
  };
  sel.onchange = count; count();
  d.querySelector('.drx').onclick = () => d.close();
  go.onclick = async () => {
    go.disabled = true;
    try {
      const j = await (await fetch('delete_range', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ a, b, src: sel.value, note: d.querySelector('#drnote').value }) })).json();
      if (!j.ok) throw new Error(j.error || 'error');
      d.close(); toast(t('dr_done', { n: j.deleted || 0 }));
      lastCount = -1; EVSIG = ''; await loadEvents(); syncDelBar(); loadSources(); if (NV.open) loadNight(); fnRefresh();
    } catch (e) { alert(t('saveerr') + ' ' + e.message); go.disabled = false; }
  };
  d.showModal();
}
async function mkNames() {
  try { const j = await (await fetch('label_names', { cache: 'no-store' })).json(); MK.names = j.names || []; } catch (e) { MK.names = MK.names || []; }
  return MK.names;
}
function mkClose() { if (MK.pop) MK.pop.hidden = true; const s0 = MK.sel; MK.sel = null; if (s0 && s0.redraw) s0.redraw(); }
function mkFmt(ms) { const d = new Date(ms); return hms(ms) + (lang === 'en' ? '.' : ',') + Math.floor(d.getMilliseconds() / 100); }
async function mkOpen(src, a, b, cx, cy, redraw, ext) {
  if (b - a < 150) { toast(t('mk_short')); redraw && redraw(); return; }
  if (b - a > 120000) { toast(t('mk_long')); redraw && redraw(); return; }
  MK.sel = Object.assign({ src, a, b, redraw }, ext || {}); tipHide();
  let p = MK.pop;
  if (!p) {
    p = MK.pop = el('div', { id: 'mkpop', className: 'lbpop mkpop' }); p.setAttribute('role', 'dialog'); p.hidden = true;
    p.innerHTML = `<b id="mktitle"></b><div id="mksub" class="mksub"></div><input id="mkname" type="text" maxlength="60" list="mkdl" autocomplete="off"><datalist id="mkdl"></datalist>
      <div id="mkquick" class="lbquick"></div><small class="mkhint"></small><div class="ntedbtns"><button type="button" id="mkcancel"></button><button type="button" id="mksave" class="pri"></button></div>`;
    document.body.appendChild(p);
    $('mkcancel').onclick = mkClose; $('mksave').onclick = mkSave;
    $('mkname').addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); mkSave(); } else if (e.key === 'Escape') mkClose(); });
    document.addEventListener('pointerdown', e => { if (!p.hidden && !p.contains(e.target) && !e.target.closest('canvas')) mkClose(); }, true);
  }
  const nm = (SOURCES.find(x => x.id === src) || {}).name || src, dur = (b - a) / 1000;
  $('mktitle').textContent = '🏷 ' + t('mk_title'); $('mksub').textContent = nm + ' · ' + mkFmt(a) + ' – ' + mkFmt(b) + ' (' + (lang === 'de' ? dur.toFixed(1).replace('.', ',') : dur.toFixed(1)) + ' s)';
  $('mkname').placeholder = t('lb_ph'); $('mkcancel').textContent = t('cancel'); $('mksave').textContent = t('lb_save'); p.querySelector('.mkhint').textContent = t('mk_hint');
  $('mkname').value = '';
  const fill = L => {
    $('mkdl').innerHTML = L.map(n => `<option value="${esc(n.name)}">`).join('');
    $('mkquick').innerHTML = L.length ? `<small class="lbqh">${esc(t('mk_have'))}</small>` + L.slice(0, 16).map(n => `<button type="button" class="chip ntchip" data-n="${esc(n.name)}">${n.pf ? '🧩 ' : '🏷 '}${esc(n.name)}</button>`).join('') : '';
    $('mkquick').querySelectorAll('button').forEach(x => x.onclick = () => { $('mkname').value = x.dataset.n; $('mkquick').querySelectorAll('button').forEach(y => y.classList.toggle('on', y === x)); $('mkname').focus(); });
  };
  fill(MK.names || []);
  p.hidden = false;
  const w = p.offsetWidth, h = p.offsetHeight, vw = document.documentElement.clientWidth, vh = window.innerHeight;
  p.style.position = 'fixed'; p.style.left = clamp(cx - w / 2, 8, Math.max(8, vw - w - 8)) + 'px'; p.style.top = (cy + 14 + h > vh - 8 ? Math.max(8, cy - 14 - h) : cy + 14) + 'px';
  if (matchMedia('(pointer:fine)').matches) $('mkname').focus();
  mkNames().then(L => { if (!p.hidden) fill(L); });
}
async function mkSave() {
  const sel = MK.sel, name = $('mkname').value.trim(); if (!sel) return;
  if (!name) { $('mkname').focus(); return; }
  $('mksave').disabled = true;
  try {
    const j = await (await fetch('mark', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ src: sel.src, a: Math.round(sel.a), b: Math.round(sel.b), name }) })).json();
    if (!j.ok) throw new Error(t({ length: 'mk_long', 'no data': 'mk_nodata', 'bad label': 'lb_empty', limit: 'mk_limit' }[j.error] || 'saveerr'));
    if (j.names) MK.names = j.names;
    toast(j.how === 'event' ? t('mk_ok_ev', { n: name }) : t('mk_ok_pf', { n: name }) + (j.emb ? '' : ' ' + t('mk_noemb')), 6000);
    mkClose(); EVSIG = ''; if (NV.open) { loadEvents(); dtLoad(DT, true); } else levLoad(true);
  } catch (e) { toast(e.message || t('saveerr')); }
  finally { $('mksave').disabled = false; }
}
function drawMk(c, X, T, ph, d, live) {               // markierter Bereich (beim Aufziehen und solange das Benennen offen ist)
  const m = MK.sel; if (!m || !!m.live !== !!live) return;
  const x0 = X(Math.min(m.a, m.b)), x1 = X(Math.max(m.a, m.b));
  c.fillStyle = ca(C.acc, 0.22); c.fillRect(x0, T, Math.max(1, x1 - x0), ph);
  c.strokeStyle = C.acc; c.lineWidth = 1.5 * d; c.beginPath(); c.moveTo(x0, T); c.lineTo(x0, T + ph); c.moveTo(x1, T); c.lineTo(x1, T + ph); c.stroke();
}
/* Tooltip zu einer Störung (Live-Bild und Verlauf): Einzelheiten beim Darüberfahren mit der Maus bzw. beim Antippen */
const ETIP = { el: null, html: "", own: "" };
function tipHide(own) { if (!ETIP.el || ETIP.el.hidden || (own && ETIP.own !== own)) return; ETIP.el.hidden = true; ETIP.html = ''; ETIP.own = ''; }
function tipShow(own, html, cx, cy, left) {          // cx/cy: Stelle am Bildschirm (neben dem Strich), left: lieber links davon
  if (!ETIP.el) {
    ETIP.el = el('div', { id: 'evtip', className: 'evtip' }); ETIP.el.hidden = true; ETIP.el.setAttribute('role', 'tooltip'); document.body.appendChild(ETIP.el);
    window.addEventListener('scroll', () => tipHide(), { passive: true, capture: true });
    document.addEventListener('pointerdown', e => { if (e.target.tagName !== 'CANVAS') tipHide(); }, true);   // Touch: Tippen daneben schließt
  }
  if (html !== ETIP.html) { ETIP.el.innerHTML = html; ETIP.html = html; }
  ETIP.own = own; ETIP.el.hidden = false;
  const w = ETIP.el.offsetWidth, h = ETIP.el.offsetHeight, vw = document.documentElement.clientWidth, vh = window.innerHeight;
  let x = left ? cx - 14 - w : cx + 14; if (x + w > vw - 8) x = cx - 14 - w; if (x < 8) x = Math.min(cx + 14, vw - 8 - w); x = Math.max(8, x);
  const y = clamp(cy, 8, Math.max(8, vh - 8 - h));
  ETIP.el.style.transform = `translate(${Math.round(x)}px,${Math.round(y)}px)`;
}
function tipHtml(o) {
  const nm = id => viewName(id) || '';
  const dur = Math.max(0, (o.to - o.from) / 1000), ds = dur < 10 ? dur.toFixed(1) : String(Math.round(dur));
  const rows = [], kv = (k, v) => rows.push(`<dt>${esc(k)}</dt><dd>${v}</dd>`);
  if (o.pk != null) kv(t('peak'), `${esc(f1(o.pk))} dBFS`);
  if (o.th != null) kv(t('threshold'), `${esc(f1(o.th))} dBFS${o.pk != null && o.pk > o.th ? ` <small>+${esc(f1(o.pk - o.th))} dB</small>` : ''}`);
  if (o.bg != null) kv(t('background'), `${esc(f1(o.bg))} dBFS`);
  if (o.art && (!CUR || CUR.classify !== false)) kv(t('tip_art'), artChip(o.art, o.ac, o.am));
  if (o.prof) kv(t('tip_prof'), `<span class="art prof${o.pbg ? ' bgp' : ''}">🧩 ${esc(o.prof)}${o.pc != null ? ` <small>${esc(o.pc)} %</small>` : ''}</span>`);
  if (o.grp > 1) kv(t('tip_grp'), esc(t('tip_grp_n', { n: o.grp })));
  const also = [...new Set((o.also || []).filter(x => x && x !== o.src))];
  if (also.length) kv(t('tip_also'), esc(also.map(nm).join(', ')));
  if (o.nt) kv(t('tip_notes'), String(o.nt));
  return `<div class="evtiph"><i class="evtipd${o.other ? ' oth' : ''}"></i><b>${esc(t(o.other ? 'tip_other' : 'tip_ev'))}</b>${o.run ? `<em>${esc(t('tip_run'))}</em>` : ''}</div>`
    + `<div class="evtips">${esc(nm(o.src))}</div>`
    + `<div class="evtipt">${hms(o.from)} – ${o.run ? '…' : hms(o.to)}<span>${esc(lang === 'de' ? ds.replace('.', ',') : ds)} s</span></div>`
    + (rows.length ? `<dl>${rows.join('')}</dl>` : '');
}
/* Live-Bild: Störung an der Stelle (aus den Messwerten), Einzelheiten aus der Liste „Ereignisse heute“, sobald sie dort steht */
function liveTipAt(i) {
  let a = i, b = i; while (a > 0 && recs[a - 1].a && !gapBefore(a)) a--; while (b < recs.length - 1 && recs[b + 1].a && !gapBefore(b + 1)) b++;
  let pk = -1e9; for (let k = a; k <= b; k++) if (recs[k].l != null && recs[k].l > pk) pk = recs[k].l;
  const from = recs[a].ts - 100, to = recs[b].ts, run = b === recs.length - 1 && nowServer() - DELAY - recs[b].ts < 1500;
  const o = { src: selSrc, from, to, run, pk: pk > -1e9 ? pk : null, th: recs[a].t, bg: recs[a].b };
  const row = ((LEV.data && LEV.data.events) || []).find(r => (r.quelle_id || 'main') === selSrc && (() => { const s0 = new Date(r.start).getTime(), s1 = s0 + (r.dauer_s || 0) * 1000; return s0 <= to + 1500 && s1 >= from - 1500; })());
  if (row) {
    const nm_ = v => v == null || v === '' || !isFinite(+v) ? null : +v;   // Werte aus der Liste kommen als Text
    Object.assign(o, { th: nm_(row.schwelle_dbfs) != null ? nm_(row.schwelle_dbfs) : o.th, bg: nm_(row.hintergrund_dbfs) != null ? nm_(row.hintergrund_dbfs) : o.bg, art: row.art, ac: row.art_c, am: row.art_man,
      prof: row.prof, pc: row.prof_ok ? null : row.prof_c, pbg: row.bg, nt: row.notes, also: (row.devs || []).map(x => x[0]) });
    const g = row.grp != null && LEV.data.grps ? LEV.data.grps[String(row.grp)] : null; if (g) o.grp = g.n;
    if (nm_(row.spitze_dbfs) != null && !run) o.pk = Math.max(o.pk == null ? -1e9 : o.pk, nm_(row.spitze_dbfs));
  }
  return o;
}
function drawHover(c, X, Y, L, T, pw, ph, d, t0, t1) {
  drawMk(c, X, T, ph, d, true); drawZs(c, X, T, ph, d);
  if (hoverX == null || drag) { tipHide('live'); return; }
  const x = hoverX * d; if (x < L || x > L + pw) { tipHide('live'); return; }
  const ts = t0 + (x - L) / pw * (t1 - t0), i = lowerBound(ts); const r = recs[i];
  if (!r || r.ts - 100 > ts + 50) { tipHide('live'); return; }
  c.strokeStyle = C.tx; c.globalAlpha = .4; c.lineWidth = d; c.beginPath(); c.moveTo(x, T); c.lineTo(x, T + ph); c.stroke(); c.globalAlpha = 1;
  if (Y) { c.fillStyle = C.acc; c.beginPath(); c.arc(x, Y(r.l), 3.5 * d, 0, 7); c.fill(); }
  const ms = new Date(ts).getMilliseconds();
  const lines = [hms(ts) + '.' + Math.floor(ms / 100), t('level') + ': ' + f1(r.l) + ' dBFS', t('background') + ': ' + f1(r.b), t('threshold') + ': ' + f1(r.t)];
  c.font = (12 * d) + 'px system-ui';
  const bw = Math.max(...lines.map(s => c.measureText(s).width)) + 16 * d, bh = lines.length * 17 * d + 10 * d;
  let bx = x + 10 * d; if (bx + bw > L + pw) bx = x - 10 * d - bw;
  const by = T + 6 * d;
  c.fillStyle = C.card; c.strokeStyle = C.bd; c.lineWidth = d; c.beginPath(); c.rect(bx, by, bw, bh); c.fill(); c.stroke();
  c.textAlign = 'left';
  lines.forEach((s, k) => { c.fillStyle = k === 0 ? C.tx : (k === 3 ? C.thr : k === 2 ? C.bgl : C.acc); c.fillText(s, bx + 8 * d, by + 20 * d + k * 17 * d); });
  if (r.a && c.canvas.id !== 'spec' && !MK.sel) {               // auf einer Störung: Einzelheiten darunter
    const rc = c.canvas.getBoundingClientRect(), k = rc.width ? c.canvas.width / rc.width : d;
    try { tipShow('live', tipHtml(liveTipAt(i)), rc.left + x / k, rc.top + (by + bh) / k + 6, bx < x); } catch (e) { tipHide('live'); }
  } else tipHide('live');
}

/* ---------- Spektrogramm ---------- */
const ring = document.createElement('canvas'); ring.width = RING; ring.height = NB;
const rctx = ring.getContext('2d');
const col1 = rctx.createImageData(1, NB);
const LUT = new Uint8ClampedArray(256 * 3);
let sLo = 40, sHi = 150, lastRange = 0;
const STOPS = [[0, 0, 4], [31, 12, 72], [85, 15, 109], [136, 34, 106], [186, 54, 85], [227, 89, 51], [249, 140, 10], [249, 201, 50], [252, 255, 164]];
function cmap(x) {
  const p = clamp(x, 0, 1) * (STOPS.length - 1), i = Math.floor(p), f = p - i, a = STOPS[i], b = STOPS[Math.min(i + 1, STOPS.length - 1)];
  return [a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, a[2] + (b[2] - a[2]) * f];
}
function buildLUT() { for (let v = 0; v < 256; v++) { const c = cmap((v - sLo) / (sHi - sLo)); LUT[3 * v] = c[0]; LUT[3 * v + 1] = c[1]; LUT[3 * v + 2] = c[2]; } }
function clearRing() { rctx.clearRect(0, 0, RING, NB); }
function specWrite(r) {
  const px = col1.data;
  for (let i = 0; i < NB; i++) { const o = 4 * (NB - 1 - i), v = r.sp[i]; px[o] = LUT[3 * v]; px[o + 1] = LUT[3 * v + 1]; px[o + 2] = LUT[3 * v + 2]; px[o + 3] = 255; }
  rctx.putImageData(col1, r.s % RING, 0);
}
function recolorAll() {
  const img = rctx.createImageData(RING, NB), px = img.data;
  for (const r of recs) {
    const x = r.s % RING;
    for (let i = 0; i < NB; i++) { const o = 4 * ((NB - 1 - i) * RING + x), v = r.sp[i]; px[o] = LUT[3 * v]; px[o + 1] = LUT[3 * v + 1]; px[o + 2] = LUT[3 * v + 2]; px[o + 3] = 255; }
  }
  rctx.putImageData(img, 0, 0);
}
function autoRange(i0, i1) {
  if (Date.now() - lastRange < 1000 || i1 < i0) return;
  lastRange = Date.now();
  const hist = new Uint32Array(256); let n = 0;
  const stepI = Math.max(1, Math.floor((i1 - i0) / 1500));
  for (let i = i0; i <= i1; i += stepI) { const sp = recs[i].sp; for (let k = 0; k < NB; k++) { hist[sp[k]]++; n++; } }
  if (n < 32) return;
  const pct = q => { let acc = 0; const lim = q * n; for (let v = 0; v < 256; v++) { acc += hist[v]; if (acc >= lim) return v; } return 255; };
  const lo = pct(0.05), hi = Math.max(pct(0.997), lo + 40);
  if (Math.abs(lo - sLo) > 4 || Math.abs(hi - sHi) > 4) { sLo = lo; sHi = hi; buildLUT(); recolorAll(); }
}
function drawSpec(cv, t0, t1) {
  fit(cv);
  const d = DPR(), c = cv.getContext('2d'), w = cv.width, h = cv.height;
  const L = AXL() * d, R = 14 * d, T = 2 * d, B = 22 * d, pw = w - L - R, ph = h - T - B;
  const X = ts => L + pw * (ts - t0) / (t1 - t0);
  const i0 = Math.max(0, lowerBound(t0 - 200)), i1 = Math.min(recs.length - 1, lowerBound(t1 + 200));
  autoRange(Math.max(0, lowerBound(t0)), Math.min(recs.length - 1, lowerBound(t1)));
  c.clearRect(0, 0, w, h);
  c.fillStyle = '#000004'; c.fillRect(L, T, pw, ph);
  c.save(); c.beginPath(); c.rect(L, T, pw, ph); c.clip();
  c.imageSmoothingEnabled = true;
  let a = i0;
  while (a <= i1) {
    let b = a; while (b < i1 && recs[b + 1].s === recs[b].s + 1) b++;
    const n = b - a + 1, sx = recs[a].s % RING, x0 = X(recs[a].ts - 100), x1 = X(recs[b].ts);
    if (sx + n <= RING) c.drawImage(ring, sx, 0, n, NB, x0, T, x1 - x0, ph);
    else { const n1 = RING - sx, xm = x0 + (x1 - x0) * n1 / n; c.drawImage(ring, sx, 0, n1, NB, x0, T, xm - x0, ph); c.drawImage(ring, 0, 0, n - n1, NB, xm, T, x1 - xm, ph); }
    a = b + 1;
  }
  if (i1 >= i0) { const light = (ea, eb) => { c.fillStyle = C.red + '55'; c.fillRect(X(ea), T, X(eb) - X(ea), 2 * d); }; eventSpans(i0, i1, light); preRollSpans(i0, i1, light); eventSpans(i0, i1, (ea, eb) => { c.fillStyle = C.red; c.fillRect(X(ea), T, X(eb) - X(ea), 3 * d); }, true); }
  drawMk(c, X, T, ph, d, true); drawZs(c, X, T, ph, d);
  if (hoverX != null && !drag) { const x = hoverX * d; if (x >= L && x <= L + pw) { c.strokeStyle = '#fff'; c.globalAlpha = .5; c.lineWidth = d; c.beginPath(); c.moveTo(x, T); c.lineTo(x, T + ph); c.stroke(); c.globalAlpha = 1; } }
  c.restore();
  // Frequenzachse
  c.font = (11 * d) + 'px system-ui'; c.textAlign = 'right'; c.fillStyle = C.mut;
  if (bands.length === NB) {
    const l0 = Math.log(bands[0]), l1 = Math.log(bands[NB - 1]);
    const fy = f => T + ph * (1 - ((Math.log(f) - l0) / (l1 - l0) * (NB - 1) + 0.5) / NB);
    const labs = ph / d > 110 ? [50, 100, 200, 500, 1000, 2000, 5000] : [100, 500, 2000];
    c.strokeStyle = C.mut; c.lineWidth = 1;
    for (const dec of [10, 100, 1000]) for (let m = 1; m <= 9; m++) {         // Zwischenstriche 20, 30 ... 9000 Hz
      const f = dec * m; if (f < bands[0] || f > bands[NB - 1]) continue;
      const y = Math.round(fy(f)) + .5, big = labs.includes(f);
      c.beginPath(); c.moveTo(L - (big ? 5 : 2.5) * d, y); c.lineTo(L, y); c.stroke();
      if (big) c.fillText(f >= 1000 ? (f / 1000) + 'k' : f, L - 7 * d, y + 4 * d);
    }
    c.save(); c.translate(11 * d, T + ph / 2); c.rotate(-Math.PI / 2); c.textAlign = 'center'; c.fillText(t('hz'), 0, 0); c.restore();
  }
  // Zeitachse
  c.textAlign = 'center'; c.fillStyle = C.mut;
  for (const tk of timeTicks(t0, t1, 8, true)) { const x = X(tk); if (x >= L && x <= L + pw) c.fillRect(x - .5, T + ph, 1, 2 * d); }
  // Platz fuer "● LIVE" rechts freihalten, damit keine Uhrzeit darunter liegt
  const tf = c.font, liveTxt = '● ' + t('live'); c.font = '700 ' + (11 * d) + 'px system-ui'; const liveW = view.live ? c.measureText(liveTxt).width + 8 * d : 0; c.font = tf;
  for (const tk of timeTicks(t0, t1, Math.max(3, Math.min(8, Math.floor(pw / d / 80))))) { const x = X(tk); if (x < L || x > L + pw) continue; c.fillRect(x - .5, T + ph, 1, 5 * d); const s = hms(tk), hw = c.measureText(s).width / 2; if (x - hw < L || x + hw > L + pw - liveW) continue; c.fillText(s, x, h - 6 * d); }
  if (view.live) { c.textAlign = 'right'; c.fillStyle = C.red; c.font = '700 ' + (11 * d) + 'px system-ui'; c.fillText(liveTxt, L + pw, h - 6 * d); }
}

/* ---------- Interaktion ---------- */
let drag = null;
function bindCanvas(cv, isSpec) {
  const tAt = e => { const [a0, b0] = viewRange(), r = cv.getBoundingClientRect(); return a0 + clamp((e.clientX - r.left - AXL()) / Math.max(20, r.width - AXL() - 14), 0, 1) * (b0 - a0); };
  let mk = null, zs = null;
  cv.addEventListener('pointerdown', e => {
    if (MK.on && (!e.button)) {                      // Bereich markieren: Bild anhalten, Bereich aufziehen
      const [, end] = viewRange(); if (view.live) { view.live = false; view.end = end; setLive(false); }
      mkClose(); mk = { id: e.pointerId, a: tAt(e), x: e.clientX }; MK.sel = { live: true, a: mk.a, b: mk.a, redraw: markDirty }; cv.setPointerCapture(e.pointerId); markDirty(); return;
    }
    if (e.shiftKey && !e.button) {                    // Umschalt + Ziehen: Bereich aufziehen, darauf zoomen
      const [, end] = viewRange(); if (view.live) { view.live = false; view.end = end; setLive(false); }
      zs = { id: e.pointerId, x: e.clientX }; ZS.sel = { a: tAt(e), b: tAt(e) }; cv.setPointerCapture(e.pointerId); markDirty(); return;
    }
    const [, end] = viewRange(), r = cv.getBoundingClientRect();
    drag = { x: e.clientX, y: e.clientY, end, w: r.width - AXL() - 14, h: r.height - (isSpec ? 18 : 32), lo: yv.lo, hi: yv.hi, moved: false, axis: null };
    if (e.pointerType !== 'mouse') hoverX = e.clientX - r.left;   // Finger/Stift: Tippen zeigt die Werte (und Einzelheiten einer Störung)
    cv.setPointerCapture(e.pointerId);
  });
  cv.addEventListener('pointermove', e => {
    const r = cv.getBoundingClientRect(); hoverX = e.clientX - r.left;
    if (mk && e.pointerId === mk.id && MK.sel) { MK.sel.b = tAt(e); markDirty(); return; }
    if (zs && e.pointerId === zs.id && ZS.sel) { ZS.sel.b = tAt(e); markDirty(); return; }
    if (!drag) return;
    const dx = e.clientX - drag.x, dy = e.clientY - drag.y;
    if (!drag.moved && Math.abs(dx) < 4 && Math.abs(dy) < 4) return;
    if (!drag.axis) {
      // senkrecht ziehen verschiebt die Skala (nur mit Auto aus, nicht im Spektrogramm), waagerecht blaettert in der Zeit
      drag.axis = (!isSpec && !yv.auto && Math.abs(dy) > Math.abs(dx)) ? 'y' : 'x';
      drag.moved = true; cv.classList.add(drag.axis === 'y' ? 'dragy' : 'drag');
      if (drag.axis === 'x' && view.live) setLive(false);
    }
    if (drag.axis === 'y') {
      yv.anchor = false;
      // Balken: die halbe Hoehe entspricht dem ganzen dB-Bereich, Pegelspur: die ganze Hoehe
      const span = drag.hi - drag.lo, ph = Math.max(40, view.mode === 'wave' ? drag.h / 2 : drag.h);
      const dv = dy / ph * span * (view.mode === 'wave' ? -1 : 1);
      let lo = drag.lo + dv, hi = drag.hi + dv;
      if (lo < -160) { hi += -160 - lo; lo = -160; } if (hi > 10) { lo -= hi - 10; hi = 10; }
      yv.lo = lo; yv.hi = hi; markDirty();
      return;
    }
    const end = drag.end - dx / Math.max(50, drag.w) * view.span * 1000, now = nowServer() - DELAY;
    if (end >= now) { setLive(true); } else { view.live = false; view.end = end; setLive(false); }
    if (!view.live && recs.length && recs[0].s <= firstAvail && end - view.span * 1000 < recs[0].ts - 1000) { drag = null; histEnter(end - view.span * 1000, end); return; }   // weiter zurück als der Arbeitsspeicher: Tagesverlauf
  });
  const up = e => {
    if (zs) {
      const m = zs, z = ZS.sel; zs = null; ZS.sel = null;
      if (z && e.type === 'pointerup' && Math.abs(e.clientX - m.x) >= 4) { const a = Math.min(z.a, z.b), b = Math.max(z.a, z.b); zoomLiveX(Math.max(5, (b - a) / 1000) / view.span, 1, b); }
      markDirty(); return;
    }
    if (mk) { const m = mk; mk = null; if (MK.sel && e.type === 'pointerup') { const a = Math.min(MK.sel.a, MK.sel.b), b = Math.max(MK.sel.a, MK.sel.b); MK.sel = null; if (Math.abs(e.clientX - m.x) < 4) { markDirty(); return; } mkOpen(selSrc, a, b, e.clientX, e.clientY, markDirty, { live: true }); } else mkClose(); markDirty(); return; }
    if (drag && drag.moved) { cv.classList.remove('drag', 'dragy'); if (e.pointerType !== 'mouse') hoverX = null; } drag = null;
  };
  cv.addEventListener('pointerup', up); cv.addEventListener('pointercancel', up);
  cv.addEventListener('pointerleave', e => { if (e.pointerType === 'mouse') hoverX = null; });
  document.addEventListener('pointerdown', e => { if (e.pointerType !== 'mouse' && e.target !== cv && hoverX != null && !e.target.closest('canvas')) hoverX = null; });
  cv.addEventListener('dblclick', () => { histExit(); setLive(true); yv.auto = true; yv.anchor = false; wg.auto = true; syncAutoBtn(); setSpan(view.preset || 60); });
  bindPinch(cv, () => viewRange(), x => clamp((x - AXL()) / Math.max(20, cv.getBoundingClientRect().width - AXL() - 14), 0, 1), (f, t2) => {   // zwei Finger: Zeit
    const ns = clamp((t2 - f) / 1000, 5, 86400), now = nowServer() - DELAY;
    if (view.live || t2 >= now) { if (!view.live) setLive(true); setSpan(Math.round(ns * 10) / 10); }
    else { view.end = t2; setSpan(Math.round(ns * 10) / 10); }
    markDirty();
  }, () => { drag = null; }, () => { });
  cv.addEventListener('wheel', e => {
    e.preventDefault();
    const u = wheelPx(e), r0 = cv.getBoundingClientRect(), xIn = e.clientX - r0.left;
    const side = Math.abs(e.deltaX) > Math.abs(e.deltaY), dy = u * (side ? e.deltaX : e.deltaY); if (!dy) return;
    const yZoom = !isSpec && (e.shiftKey || xIn < AXL()) && !side;     // Umschalt + Mausrad oder über der dB-Beschriftung: Höhe
    if (!yZoom) {
      if (side && !e.shiftKey && !e.ctrlKey) {         // seitlich wischen: in der Zeit verschieben
        const [a, b] = viewRange(), sh = dy / Math.max(50, r0.width - AXL() - 14) * (b - a), now = nowServer() - DELAY;
        const end = (view.live ? now : view.end) + sh; if (end >= now) setLive(true); else { view.live = false; view.end = end; setLive(false); } markDirty(); return;
      }
      zoomLiveX(wheelK(dy, e.ctrlKey), (xIn - AXL()) / Math.max(20, r0.width - AXL() - 14)); return;   // Mausrad / Touchpad-Spreizen: Zeit
    } else {
      const f = Math.exp(clamp(dy, -300, 300) * (e.ctrlKey ? 0.008 : 0.0014));   // Mausrad-Raster ≈ 15 %, Touchpad fein
      if (view.mode === 'level') {
        const r = cv.getBoundingClientRect(), ph = r.height - 32, fy = clamp((e.clientY - r.top - 10) / ph, 0, 1);
        zoomY(f, yv.hi - fy * (yv.hi - yv.lo));
      } else zoomY(f);
    }
  }, { passive: false });
}
/* Live-Bild: Zeit zoomen (stufenlos). Live: rechter Rand bleibt „jetzt“; angehalten: die Stelle unter der Maus bleibt stehen.
   Weiter als der Arbeitsspeicher (10 min) geht es nahtlos in den Tagesverlauf. */
function zoomLiveX(k, fx, end0) {
  const ns = clamp(Math.round(view.span * k * 10) / 10, 5, 86400); if (ns === view.span) return;
  if (view.live) { setSpan(ns); markDirty(); return; }
  const [a, b] = viewRange(), c = a + clamp(fx, 0, 1) * (b - a), now = nowServer() - DELAY;
  let end = end0 != null ? end0 : c + (1 - clamp(fx, 0, 1)) * ns * 1000;
  if (end >= now) { setSpan(ns); setLive(true); markDirty(); return; }
  const start = end - ns * 1000;
  if (ns > 600 || (recs.length && recs[0].s <= firstAvail && start < recs[0].ts - 1000)) { view.span = ns; spanSel(ns); histEnter(start, end); return; }
  view.end = end; setSpan(ns); markDirty();
}
const ZS = { sel: null };                             // Umschalt + Ziehen: aufgezogener Bereich (Live-Bild)
function drawZs(c, X, T, ph, d) {
  const m = ZS.sel; if (!m) return; const x0 = X(Math.min(m.a, m.b)), x1 = X(Math.max(m.a, m.b));
  c.fillStyle = ca(C.acc, 0.18); c.fillRect(x0, T, Math.max(1, x1 - x0), ph); c.strokeStyle = C.acc; c.lineWidth = d; c.strokeRect(x0, T, Math.max(1, x1 - x0), ph);
}
function zoomY(f, center) {
  if (view.mode === 'level' && yv.dmn != null) {      // Pegelspur: unten bündig am tiefsten sichtbaren Wert, die Schwelle spielt keine Rolle
    const sp = clamp((yv.hi - yv.lo) * f, 1, 160), lo = Math.floor((yv.dmn - Math.max(0.3, sp * 0.03)) * 10) / 10;
    yv.lo = Math.max(-160, lo); yv.hi = Math.min(10, yv.lo + sp); yv.span = yv.hi - yv.lo; yv.anchor = true; yv.auto = false; syncAutoBtn(); markDirty(); return;
  }
  let c = center;
  if (c == null) {            // Tasten +/-: um die Mitte der sichtbaren Werte zoomen, damit die Kurve im Bild bleibt
    c = (yv.lo + yv.hi) / 2;
    if (yv.dmn != null && yv.dmx - yv.dmn < (yv.hi - yv.lo) * f) c = (yv.dmn + yv.dmx) / 2;
    else if (f < 1) {                                       // hineinzoomen: dorthin, wo die Kurve meistens liegt
      const i0 = lowerBound(viewRange()[0]), i1 = recs.length - 1, v = [];
      for (let i = Math.max(0, i0); i <= i1 && v.length < 4000; i++) if (recs[i].l > -125) v.push(recs[i].l);
      if (v.length) { v.sort((a, b) => a - b); c = v[v.length >> 1]; }
    }
  }
  let lo = c - (c - yv.lo) * f, hi = c + (yv.hi - c) * f;
  if (center == null) { const sp = (yv.hi - yv.lo) * f; lo = c - sp / 2; hi = c + sp / 2; }   // Tasten: Kurve in die Mitte holen
  if (hi - lo < 1) { lo = c - 0.5; hi = c + 0.5; }          // feinster Zoom: 1 dB ueber die ganze Hoehe
  if (hi - lo > 160) return;
  yv.lo = Math.max(-160, lo); yv.hi = Math.min(10, hi); yv.auto = false; syncAutoBtn();
}

/* ================= Status, Kennzahlen ================= */
function winText(s) { return s.bg_window + ' ' + (s.bg_unit === 'min' ? 'min' : 's'); }
function updateStatus() {
  if (!st) return;
  const p = $('pill'); p.className = 'pill'; let txt = t('quiet');
  if (st.enabled === false) { txt = t('src_off'); p.classList.add('w'); }
  else if (st.type === 'phone' && (st.age > 3 || !st.phone_online)) { txt = t('phone_wait'); p.classList.add('w'); }
  else if (st.age > 3) { txt = t('nodata'); p.classList.add('w'); }
  else if (st.silent) { txt = t('silent'); p.classList.add('w'); }
  else if (st.learning) { txt = t('learning', { p: st.learn_pct || 0 }); p.classList.add('w'); }
  else if (st.active) { txt = t('event'); p.classList.add('a'); }
  else if (st.paused) { txt = t('stopped'); p.classList.add('w'); }
  else if (st.ha_hold) { txt = t('ha_pill', { l: st.ha_hold.label }); p.classList.add('w'); }
  else if (st.forced) { txt = t('outside_forced'); p.classList.add('man'); }
  else if (!st.listening) { txt = t('outside'); p.classList.add('w'); }
  const clk = !!st.forced || (!st.listening && !st.paused && txt === t('outside'));
  p.classList.toggle('clk', clk); p.tabIndex = clk ? 0 : -1; p.title = clk ? t(st.forced ? 'outside_off_tip' : 'outside_on_tip') : '';
  p.tabIndex = clk ? 0 : -1;
  if (clk && (txt === t('outside') || txt === t('outside_forced'))) txt += st.forced ? ' · ⏹' : ' · ▶ ' + t('outside_go');   // Zusatz nur beim passenden Zustand
  p.onclick = clk ? async () => {
    try { await fetch('force', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ on: !st.forced, src: selSrc }) }); } catch (e) { }
    if (typeof poll === 'function') poll();
  } : null;
  p.textContent = txt;
  const E = liveCfg(selSrc), mode = CUR ? E.thr_mode : 'bounded';
  // Im Rundlauf: geraetebezogene Hinweise kompakt in der Leiste (sonst springt die Seite bei jedem Wechsel)
  const compact = TILE.on && liveDevs().length > 1, warns = [];
  const DEVB = { b_sil: 'w_sil', b_flo: 'w_flo', b_low: 'w_low', b_ha: '' };
  const ban = (id, show, html) => {
    const e = $(id), inBar = compact && id in DEVB;
    if (inBar && show) warns.push({ id, html, short: id === 'b_ha' ? '⏸ ' + t('ha_pill', { l: st.ha_hold ? st.ha_hold.label : '' }) : '⚠ ' + t(DEVB[id]) });
    e.style.display = show && !inBar ? 'block' : 'none'; if (show && e.innerHTML !== html) e.innerHTML = html;
  };
  ban('b_err', !!st.error, t('errmsg', { e: esc(st.error) }));
  { const h = st.ha_hold; ban('b_ha', !!h && !st.paused, h ? (h.until ? t('ha_banner_after', { l: esc(h.label), u: new Date(h.until).toLocaleTimeString(lang === 'en' ? 'en-GB' : 'de-DE', { hour: '2-digit', minute: '2-digit' }) }) : t('ha_banner', { l: esc(h.label), s: esc(h.state || '') })) : ''); }
  syncRec(st);
  ban('b_sil', !st.error && st.silent, t('silentmsg'));
  ban('b_flo', !st.silent && (st.floor || st.ceil) && !BOFF.has('b_flo'), (st.floor ? t('floormsg', { v: f1(st.thr) }) : t('ceilmsg', { v: f1(st.thr) })) + BX());
  ban('b_low', !st.silent && !st.floor && st.base != null && st.base < -85 && !BOFF.has('b_low'), t('lowmsg', { v: f1(st.base) }) + BX());
  { const tw = $('tilewarn'), key = JSON.stringify(warns.map(w => w.short));
    if (tw.dataset.k !== key) { tw.dataset.k = key; tw.innerHTML = warns.map(w => `<span class="twarn${w.id === 'b_ha' ? ' ha' : ''}" title="${esc(w.html.replace(/<[^>]+>/g, '').replace('✕', '').trim())}">${esc(w.short)}</span>`).join(''); } }
  renderTiles(st, selSrc);
  if (st.all_total !== lastCount) { lastCount = st.all_total; evRefreshSoon(); }
}

/* Neue Störungen: Listen höchstens alle 5 s neu laden und nicht mitten in einer Störung (sonst ruckelt das Live-Bild) */
const EVR = { t: 0, timer: 0 };
function evRefreshSoon() {
  clearTimeout(EVR.timer);
  const wait = Math.max(0, 5000 - (Date.now() - EVR.t)) + (st && st.active && Date.now() - EVR.t < 20000 ? 2000 : 0);
  EVR.timer = setTimeout(() => { if (st && st.active && Date.now() - EVR.t < 20000) return evRefreshSoon(); EVR.t = Date.now(); loadEvents(); levLoad(); }, wait);
}
/* Kacheln (Pegel, Hintergrund, Schwelle, Geraeusch, Ereignisse) fuer ein Geraet */
function renderTiles(S, sid) {
  if (!S) return;
  const E = liveCfg(sid), mode = CUR ? E.thr_mode : 'bounded';
  { const la = S.live_art, on = !!la && S.enabled !== false && !S.silent, box = $('livart');
    box.style.display = on ? '' : 'none';
    if (on) {
      const q = la.g === 'quiet', g = la.g;
      $('vart').textContent = q ? t('live_quiet') : (ART_ICON[g] || '❓') + ' ' + artName(g);
      $('vart').style.color = q ? 'var(--mut)' : (ART_COL[g] || 'inherit');
      $('vartm').textContent = q ? '' : (g !== 'other' ? la.c + ' %' : '') + (la.top ? (g !== 'other' ? ' · ' : '') + la.top : '');
    } }
  $('vl').textContent = S.silent ? '–' : f1(S.level);
  $('vb').textContent = mode === 'fixed' ? '–' : f1(S.base);
  $('vt').textContent = f1(S.thr);
  if (CUR) {
    $('vbm').textContent = mode === 'fixed' ? t('bg_fixed') : t({ median: 'bg_median', max: 'bg_max', min: 'bg_min', mean: 'bg_mean' }[E.bg_stat] || 'bg_quiet', { w: winText(E) });
    let m = mode === 'fixed' ? t('m_fixed') : mode === 'dynamic' ? t('m_dynamic', { o: numTxt(E.offset_db) }) : t('m_bounded', { o: numTxt(E.offset_db), lo: numTxt(E.min_db), hi: numTxt(E.thr_max_db) });
    if (srcById(sid) && srcById(sid).own) m += ' · ' + t('own_tag');
    if (S.slot) m += ' · ' + t('slot_tag', { s: S.slot });
    if (S.floor) m += ' · ' + t('at_floor'); if (S.ceil) m += ' · ' + t('at_ceil');
    $('vtm').textContent = m;
  }
  $('vc').textContent = S.count_today;
  $('vct').textContent = t('today_total', { n: S.count_total }) + (SOURCES.length > 1 ? ' · ' + t('all_src', { n: S.all_today }) : '');
}
/* Rundlauf: wechselt automatisch durch alle Geraete, die live sind (Kacheln, Grafik und Live-Bild), mit Animation.
   Haelt an, solange man etwas tut: in der Zeit zurueckblaettern, anhoeren, Dialoge, Nachtbericht, kurz nach manueller Auswahl. */
const lsNum = (k, d, lo, hi) => { try { const v = +localStorage.getItem(k); return v >= lo && v <= hi ? v : d; } catch (e) { return d; } };
const TILE = { on: (() => { try { return localStorage.getItem('laerm_tileshow') !== '0'; } catch (e) { return true; } })(), at: Date.now(), manual: false, busy: false, key: '',
  ms: lsNum('laerm_tile_s', 8, 3, 120) * 1000, anim: lsNum('laerm_tile_anim', 600, 150, 3000) };
const rotActive = () => TILE.on && !TILE.manual && liveDevs().length > 1;    // Rundlauf laeuft (nicht von Hand angehalten)
function liveDevs() { return SOURCES.filter(x => x.enabled !== false && x.online); }
function tileHeld() {
  return !view.live || document.hidden || NV.open || PV.open || !!document.querySelector('dialog[open]') || !!drag;
}
function tileBar() {
  const devs = liveDevs(), bar = $('tilebar'), show = devs.length > 1;
  bar.hidden = !show; if (!show) return;
  const run = rotActive(), held = run && tileHeld(), s = srcById(selSrc);
  const key = JSON.stringify([devs.map(d => d.id), selSrc, run, held, TILE.at, TILE.ms, lang]);
  if (key === TILE.key) return; TILE.key = key;
  $('tilename').textContent = (SRC_ICON[s && s.type] || '') + ' ' + (s ? s.name : '');
  const left = Math.max(0, TILE.ms - (Date.now() - TILE.at));
  $('tiledots').innerHTML = devs.map(d => `<button type="button" class="tdot${d.id === selSrc ? ' cur' : ''}${run && !held && d.id === selSrc ? ' run' : ''}" data-id="${esc(d.id)}" title="${esc(d.name)}" aria-label="${esc(d.name)}" style="--dur:${left}ms;--from:${(1 - left / TILE.ms).toFixed(3)}"></button>`).join('');
  $('tiledots').querySelectorAll('.tdot').forEach(b => b.onclick = () => { TILE.manual = true; TILE.key = ''; if (b.dataset.id !== selSrc) tileGo(b.dataset.id, true); else { tileBar(); evFollow(); } });
  const pb = $('tileplay'); pb.textContent = run ? '⏸' : '▶'; pb.title = t(run ? 'tile_pause' : 'tile_play'); pb.setAttribute('aria-label', pb.title);
  bar.classList.toggle('held', held); bar.classList.toggle('stopped', !run);
}

/* Slider: der aktuelle Inhalt schiebt sich komplett nach links hinaus, das naechste Geraet gleichzeitig von rechts herein.
   Beide bleiben voll deckend. Technik: Kopie des alten Inhalts (Grafiken pixelgenau) liegt im Rahmen, darunter wird
   sofort auf das neue Geraet umgestellt; dann gleiten beide um die volle Breite. */
function slideCopy(vp) {
  const inner = vp.querySelector(':scope > .slideinner'); if (!inner) return null;
  const cl = inner.cloneNode(true); cl.classList.add('slidecopy'); cl.removeAttribute('id');
  cl.querySelectorAll('[id]').forEach(e => e.removeAttribute('id'));
  const fi = inner.querySelectorAll('select,input'), fc = cl.querySelectorAll('select,input');   // aktuelle Werte der Auswahlfelder mitnehmen
  fi.forEach((f, k) => { const g = fc[k]; if (!g) return; if (f.type === 'checkbox' || f.type === 'radio') g.checked = f.checked; else g.value = f.value; });
  const src = inner.querySelectorAll('canvas'), dst = cl.querySelectorAll('canvas');
  src.forEach((c, k) => { const d = dst[k]; if (!d) return; d.width = c.width; d.height = c.height; try { d.getContext('2d').drawImage(c, 0, 0); } catch (e) { } });
  cl.querySelectorAll('.cvbtns').forEach(e => e.remove());
  vp.style.height = vp.offsetHeight + 'px';                // Hoehe waehrend der Bewegung festhalten
  vp.appendChild(cl);
  return { vp, inner, cl };
}
async function tileGo(id, now) {
  if (TILE.busy || id === selSrc) return;
  TILE.busy = true;
  const c = DCACHE[id], from = selSrc;
  if (!c || Date.now() - c.t > 4000) { try { await prefetchDev(id); } catch (e) { } }
  if (selSrc !== from || (!now && !rotActive())) { TILE.busy = false; return; }      // inzwischen von Hand gewaehlt
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const parts = reduce ? [] : [$('vp1')].filter(v => v && v.offsetParent).map(slideCopy).filter(Boolean);
  parts.forEach(p => { p.inner.style.transition = 'none'; p.inner.style.transform = 'translateX(100%)'; });
  selectSource(id, true);
  markDirty(); updateStatus();
  await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));       // neues Geraet ist gezeichnet (noch rechts ausserhalb)
  const d = TILE.anim, ease = 'cubic-bezier(.65,0,.35,1)';
  parts.forEach(p => {
    p.vp.style.height = Math.max(p.vp.offsetHeight, p.inner.offsetHeight) + 'px';
    p.cl.style.transition = p.inner.style.transition = `transform ${d}ms ${ease}`;
    p.cl.style.transform = 'translateX(-100%)'; p.inner.style.transform = 'translateX(0)';
  });
  if (parts.length) await new Promise(r => setTimeout(r, d + 30));
  parts.forEach(p => { p.cl.remove(); p.inner.style.transition = p.inner.style.transform = ''; p.vp.style.height = ''; });
  TILE.at = Date.now(); TILE.busy = false; TILE.pf = null; tileBar();
}
/* Einstellungen des Rundlaufs (pro Browser): Anzeigedauer je Geraet und Geschwindigkeit des Schiebens */
function tileSetPop() {
  let m = $('tilepop');
  if (!m) { m = el('div', { id: 'tilepop', className: 'hmenu tilepop' }); document.body.appendChild(m); document.addEventListener('click', e => { if (!m.hidden && !e.target.closest('#tilepop,#tileset')) m.hidden = true; }); }
  m.innerHTML = `<b>${esc(t('tile_set'))}</b>
    <label>${esc(t('tile_show'))} <span><input type="range" id="tsms" min="3" max="60" step="1" value="${TILE.ms / 1000}"> <output id="tsmsv">${TILE.ms / 1000} s</output></span></label>
    <label>${esc(t('tile_speed'))} <span><input type="range" id="tsan" min="150" max="2000" step="50" value="${TILE.anim}"> <output id="tsanv">${(TILE.anim / 1000).toFixed(2)} s</output></span></label>
    <small>${esc(t('tile_set_hint'))}</small>`;
  $('tsms').oninput = e => { TILE.ms = +e.target.value * 1000; $('tsmsv').textContent = e.target.value + ' s'; try { localStorage.setItem('laerm_tile_s', e.target.value); } catch (x) { } TILE.key = ''; tileBar(); };
  $('tsan').oninput = e => { TILE.anim = +e.target.value; $('tsanv').textContent = (TILE.anim / 1000).toFixed(2) + ' s'; try { localStorage.setItem('laerm_tile_anim', e.target.value); } catch (x) { } };
  m.hidden = false;
  const r = $('tileset').getBoundingClientRect(); m.style.top = (r.bottom + 6) + 'px'; m.style.right = Math.max(8, innerWidth - r.right) + 'px'; m.style.left = 'auto';
}
function tileTick() {
  const devs = liveDevs();
  if (rotActive() && !TILE.busy) {
    if (tileHeld()) TILE.at = Date.now();             // waehrend man etwas tut: Zeit laeuft nicht
    else {
      const i = devs.findIndex(d => d.id === selSrc), nx = devs[(i + 1) % devs.length].id;
      if (Date.now() - TILE.at >= TILE.ms - 2500 && TILE.pf !== nx) { TILE.pf = nx; prefetchDev(nx).catch(() => { }); }   // naechstes Geraet vorab laden
      if (Date.now() - TILE.at >= TILE.ms || i < 0) tileGo(nx);
    }
  }
  tileBar();
}
/* ================= Geraeuschart (lokale KI) ================= */
const ART_ORDER = ['knock', 'door', 'steps', 'voice', 'tv', 'scrape', 'signal', 'animal', 'noise', 'other'];
const ART_ICON = { knock: '🔨', door: '🚪', steps: '👣', voice: '🗣', tv: '📺', scrape: '🔩', signal: '🔔', animal: '🐾', noise: '〰', other: '❓' };
const ART_COL = { knock: '#e0314b', door: '#e8590c', steps: '#f0a500', voice: '#7048e8', tv: '#1c7ed6', scrape: '#c2255c', signal: '#2b8a3e', animal: '#66a80f', noise: '#868e96', other: '#adb5bd' };
const artName = g => t('art_' + (ART_ORDER.includes(g) ? g : 'other'));
function artChip(g, c, man) {
  if (!g) return '';
  return `<span class="art a-${g}${man ? ' man' : ''}" title="${esc(t(man ? 'art_man_tip' : 'art_ai_tip'))}">${ART_ICON[g] || '❓'} ${esc(artName(g))}${c != null && !man && g !== 'other' ? ` <small>${c} %</small>` : ''}</span>`;
}
function artResultHTML(res) {
  const bars = Object.entries(res.groups || {}).filter(([, v]) => v > 0).slice(0, 5).map(([g, v]) =>
    `<div class="gbar"><span>${ART_ICON[g] || ''} ${esc(artName(g))}</span><div><i style="width:${Math.max(2, v)}%;background:${ART_COL[g] || '#888'}"></i></div><span>${v} %</span></div>`).join('');
  const tl = (res.timeline || []).map(p => `<i style="background:${ART_COL[p.g] || '#888'}" title="${esc(p.t.toFixed(1) + ' s · ' + artName(p.g) + ' ' + p.pct + ' % · ' + p.db + ' dB')}"></i>`).join('');
  const used = [...new Set((res.timeline || []).map(p => p.g))];
  const leg = used.map(g => `<span><b style="color:${ART_COL[g]}">■</b> ${esc(artName(g))}</span>`).join('');
  const top = (res.top || []).slice(0, 5).map(x => `<span>${esc(x.name)} ${x.pct} %</span>`).join('');
  return `<div class="big">${ART_ICON[res.art] || '❓'} ${esc(artName(res.art))} <small>${res.art === 'other' ? esc(t('art_unclear')) : res.conf + ' % ' + esc(t('art_sure'))}</small></div>
    <div class="gbars">${bars}</div>
    ${tl ? `<div><small>${esc(t('art_timeline', { s: res.seconds }))}${res.cut ? ' · ' + esc(t('art_cut')) : ''}</small><div class="tline">${tl}</div><div class="tlleg">${leg}</div></div>` : ''}
    ${top ? `<div><small>${esc(t('art_top'))}</small><div class="topc">${top}</div></div>` : ''}`;
}
/* Einstellungen: läuft der KI-Fingerabdruck? (heute gespeichert je Gerät, übersprungen, Rechenzeit) */
async function fpStat() {
  let s = null; try { s = (await (await fetch('art_status', { cache: 'no-store' })).json()).fp; } catch (e) { }
  const b = $('fpstat'); if (!b || !s) return;
  const dv = (s.devs || []).filter(d => !DEV || d.id === DEV);
  b.textContent = !s.ki ? '⚠ ' + t(s.why === 'model' ? 'pt_kimodel' : 'fp_st_noki') : !s.on ? '⚠ ' + t('fp_st_off')
    : '✔ ' + t('fp_st_on', { d: dv.map(d => (SOURCES.length > 1 ? d.name + ': ' : '') + (d.on ? d.today : t('fp_off'))).join(' · '), s: s.skip, ms: Math.round(s.ms) });
  b.classList.toggle('warn', !s.ki || !s.on);
}
async function loadArtStatus() {
  try {
    const s = await (await fetch('art_status', { cache: 'no-store' })).json(), el = $('artstat');
    if (!s.available || !s.enabled) { el.textContent = ''; return; }
    el.textContent = s.pending > 0 ? '🔎 ' + t('art_running', { n: s.pending }) : (s.error ? '⚠ ' + s.error : '');
  } catch (e) { }
}
/* Ereignisse nachtraeglich mit der KI pruefen (auch bereits eingeordnete neu) */
let ART_WAIT = 0;
async function recheckEvents(files, after) {
  files = files.filter(Boolean); if (!files.length) return;
  try {
    const r = await (await fetch('classify_events', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ files }) })).json();
    if (!r.ok) { alert(t(r.error === 'off' ? 'art_off_msg' : 'art_err') + (r.error && r.error !== 'off' ? ' (' + r.error + ')' : '')); return; }
    if (!r.queued) { alert(t('art_noemb')); return; }
    $('artstat').textContent = '⏳ ' + t('art_recheck_run', { n: r.queued });
  } catch (e) { alert(t('saveerr') + ' ' + e.message); return; }
  clearTimeout(ART_WAIT);
  const t0 = Date.now();
  const wait = async () => {
    let s = null; try { s = await (await fetch('art_status', { cache: 'no-store' })).json(); } catch (e) { }
    if (s && s.pending > 0 && Date.now() - t0 < 600000) { $('artstat').textContent = '⏳ ' + t('art_recheck_run', { n: s.pending }); ART_WAIT = setTimeout(wait, 1500); return; }
    await loadEvents(); if (after) after();
    $('artstat').textContent = '✔ ' + t('art_recheck_done'); setTimeout(loadArtStatus, 6000);
  };
  ART_WAIT = setTimeout(wait, 1200);
}
async function classifyRange() {
  const [t0, t1] = viewRange(), box = $('classres'), b = $('classrange');
  b.disabled = true; box.hidden = false; box.textContent = '⏳ ' + t('art_analysing');
  try {
    const r = await fetch(`classify_range?src=${encodeURIComponent(selSrc)}&from=${Math.floor(t0)}&to=${Math.ceil(Math.min(t1, t0 + 60000))}`, { cache: 'no-store' });
    const j = await r.json();
    if (!j.ok) throw new Error(j.error || 'error');
    box.innerHTML = `<div class="row"><b>${esc(t('art_range_res', { s: j.seconds }))}</b><button class="chip" id="classx" type="button">✕</button></div>` + artResultHTML(j);
    $('classx').onclick = () => { box.hidden = true; };
  } catch (e) { box.textContent = '⚠ ' + t('art_err') + ' ' + e.message; }
  b.disabled = false;
}
async function checkFile(f) {
  const box = $('chkres'), au = $('chkaudio');
  if (!f) return;
  $('chkname').textContent = f.name + ' (' + (f.size / 1048576).toFixed(1) + ' MB)';
  if (au.dataset.u) URL.revokeObjectURL(au.dataset.u);
  au.dataset.u = URL.createObjectURL(f); au.src = au.dataset.u; au.hidden = false;
  box.hidden = false; box.textContent = '⏳ ' + t('art_analysing');
  try {
    const j = await (await fetch('classify', { method: 'POST', headers: { 'Content-Type': 'application/octet-stream' }, body: f })).json();
    if (!j.ok) throw new Error(j.error || 'error');
    box.innerHTML = artResultHTML(j);
  } catch (e) { box.textContent = '⚠ ' + t('art_err') + ' ' + e.message; }
}
async function setArt(k, group) {
  try {
    const r = await (await fetch('art_set', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ k, group }) })).json();
    if (!r.ok) throw new Error(r.error || 'error');
    loadEvents(); return r;
  } catch (e) { alert(t('saveerr') + ' ' + e.message); }
}
function renderEvProf(j) {                          // gelerntes Profil der Störung: anzeigen, bestätigen, ändern, lösen
  const box = $('evprof'), p = j.prof || {}, names = j.pnames || [];
  if (!names.length && !p.prof) { box.hidden = true; return; }
  box.hidden = false;
  box.innerHTML = `<span class="art prof${p.bg ? ' bgp' : ''}">🧩 ${p.prof ? esc(p.prof) + (p.prof_ok ? ' ✓' : p.prof_c != null ? ' <small>' + p.prof_c + ' %</small>' : '') : esc(t('pf_none_ev'))}${p.bg ? ' · ' + esc(t('pf_bg_short')) : ''}</span>
    ${p.prof && !p.prof_ok ? `<button type="button" class="chip" id="evpfok">✓ ${esc(t('pf_confirm'))}</button>` : ''}
    <label><small>${esc(t('pf_change'))}</small> <select id="evpfsel"><option value="">${esc(t('pf_none_opt'))}</option>${names.map(n => `<option${n === p.prof ? ' selected' : ''}>${esc(n)}</option>`).join('')}</select></label>`;
  const set = async name => {
    try { await fetch('profile', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ action: 'confirm', datei: EVV.row.datei, name }) }); } catch (e) { }
    const j2 = await (await fetch('event?k=' + encodeURIComponent(EVV.k), { cache: 'no-store' })).json(); if (j2.ok) renderEvProf(j2); EVSIG = ''; if (NV.open) loadEvents();
  };
  const ok = $('evpfok'); if (ok) ok.onclick = () => set(p.prof);
  $('evpfsel').onchange = e => set(e.target.value);
}
function renderEvArt(j) {
  const box = $('evart'), a = j.art, r = j.row;
  if (!r.datei) { box.innerHTML = ''; return; }
  // Neu bewerten geht nur ohne Ton: aus gespeicherten KI-Fingerabdruecken (Einstellung "KI-Fingerabdruck speichern")
  const canRe = !!(j.ki && j.ki.emb) && !(CUR && CUR.classify === false);
  const reBtn = canRe ? ` <button type="button" class="chip" id="evrecheck" title="${esc(t('art_recheck_tip'))}">🔎 ${esc(t('art_recheck'))}</button>` : '';
  const bindRe = () => { const b = $('evrecheck'); if (b) b.onclick = () => { b.disabled = true; b.textContent = '⏳ ' + t('art_analysing'); recheckEvents([r.datei], async () => { const j2 = await (await fetch('event?k=' + encodeURIComponent(EVV.k), { cache: 'no-store' })).json(); if (j2.ok && $('evdlg').open) { renderEvArt(j2); EVV.marks = (j2.ki && j2.ki.marks) || []; evDraw(); } }); }; };
  if (!a) {
    box.innerHTML = `<span class="art a-other">❓ ${esc(t(CUR && CUR.classify === false ? 'art_off_short' : j.legacy ? 'art_none' : 'art_pending'))}</span>` + reBtn;
    bindRe(); return;
  }
  const fm = {}; for (const m of (j.ki && j.ki.marks) || []) fm[m[2]] = Math.max(fm[m[2]] || 0, m[3]);
  const g = a.man || a.g, fk = Object.keys(fm).sort((u, v) => fm[v] - fm[u]).slice(0, 3);
  const top = fk.length ? fk.map(k => `${esc(((j.fine || {})[k] || {}).name || k)} ${fm[k]} %`).join(' · ') : (a.top || []).slice(0, 3).map(x => `${esc(x[0])} ${x[1]} %`).join(' · ');
  const kd = kindsHTML(j.ki && j.ki.kinds, j.fine);                 // Liste, was alles vorkam (mit Anzahl bzw. Dauer)
  box.innerHTML = `${artChip(g, a.c, !!a.man)}${kd ? `<span class="evkinds" title="${esc(t('kinds_col'))}">${kd}</span>` : `<span title="${esc(t('art_top'))}"><small>${top}</small></span>`}${reBtn}
    <label><small>${esc(t('art_correct'))}</small> <select id="evartsel"><option value="">${esc(t('art_auto'))}</option>${ART_ORDER.map(x => `<option value="${x}"${a.man === x ? ' selected' : ''}>${ART_ICON[x]} ${esc(artName(x))}</option>`).join('')}</select></label>`;
  bindRe();
  $('evartsel').onchange = async e => {
    const r2 = await setArt(EVV.k, e.target.value);
    if (r2) { const j2 = await (await fetch('event?k=' + encodeURIComponent(EVV.k), { cache: 'no-store' })).json(); if (j2.ok) renderEvArt(j2); }
  };
}

/* ================= Ereignisse ================= */
let EV = null;
let EVN = (() => { try { const v = localStorage.getItem('laerm_evn'); return v == null ? 200 : +v; } catch (e) { return 200; } })();   // Anzahl Zeilen (0 = alle)
async function loadEvents() {
  if (!NV.open) return;                             // Ereignisliste gibt es nur im Reiter Protokolle
  const q = perQuery(); if (q == null) return;
  const want = q + '&n=' + EVN;
  try { const j = await (await fetch('events?' + want, { cache: 'no-store' })).json(); if (want !== perQuery() + '&n=' + EVN) return; EV = j; renderEvents(); loadArtStatus(); } catch (e) { }
}
function renderEvents() {
  if (!EV) return;
  const mxh = Math.max(1, ...EV.hours);
  $('hours').innerHTML = EV.hours.map((c, h) => `<div class="hb" title="${h}:00 – ${c}"><em>${c || ''}</em><i style="height:${Math.round(100 * c / mxh)}%"></i><span>${h}</span></div>`).join('');
  const mxd = Math.max(1, ...EV.days.map(x => x[1]));
  $('days').innerHTML = `<tr><th>${t('date')}</th><th></th><th>${t('count')}</th></tr>` + (EV.days.length ? EV.days.map(([d, c]) =>
    `<tr><td>${esc(fmtDay(d))}</td><td class="bw"><div class="dbar" style="width:${Math.max(3, Math.round(100 * c / mxd))}%"></div></td><td>${c}</td></tr>`).join('') : `<tr><td colspan="3" class="empty">${t('none')}</td></tr>`);
  const useArt = !CUR || CUR.classify !== false;
  syncLabelFilter(); sfltBuild();
  $('artflt').querySelectorAll('option').forEach(o => { if (o.value && o.value !== '_notes' && !o.value.startsWith('lb:')) o.hidden = !useArt; }); artMsBuild();
  const one = (r, flt) => flt === '_notes' ? r.notes > 0 : flt.startsWith('lb:') ? (r.labels || []).includes(flt.slice(3)) : !useArt ? true : flt === '_none' ? !r.art : r.art === flt;
  const evs = SHIDE.has('_ev') ? [] : EV.events.filter(r => !ARTSEL.size || [...ARTSEL].some(f => one(r, f)));   // Art: Mehrfachauswahl, eine passende genügt
  // Nur neu aufbauen, wenn sich etwas geaendert hat. Der Player ist von der Tabelle getrennt: Wiedergabe laeuft weiter.
  const grpMode = EVVIEW === 'grp';
  const sv = sensVis();
  const sig = JSON.stringify([useArt, lang, grpMode, evs.map(r => [r.k, r.ha_on, r.start, r.art, r.art_c, r.art_man, r.video, r.audio, r.datei, r.notes, r.labels, r.kinds, r.prof, r.prof_c, r.prof_ok, r.inc, r.grp, r.lead, r.devs, r.bg]), SOURCES.map(x => [x.id, x.name]), sv, [...SHIDE]]);
  if (sig === EVSIG) return;
  EVSIG = sig;
  evGrid(evs, sv, useArt, grpMode);
}
/* ================= Ereignistabelle mit Tabulator (MIT, tabulator.info) =================
   Eine Zeile je Störung bzw. Sensor-Ereignis; Gruppen als aufklappbare Zeilen (dataTree).
   Sortieren per Klick auf die Spaltenüberschrift, Filter mit Mehrfachauswahl unter Quelle und Art. */
let TBL = null, TBL_KEY = '', EVDATA = [];
const SEL = new Set();                               // ausgewählte Störungen (Schlüssel k) – überlebt Neuzeichnen, Sortieren, Filtern
const ek = r => r.k || `${r.start}|${r.quelle_id || 'main'}|${r.datei || ''}|0`;
function evSrcName(r) { const s = SOURCES.find(x => x.id === (r.quelle_id || 'main')); return r.quelle || (s && s.name) || r.quelle_id || ''; }
function evTags(r) { const a = []; if (r.prof) a.push('🧩 ' + r.prof); for (const n of r.labels || []) a.push('🏷 ' + n); if (r.art) a.push((ART_ICON[r.art] || '') + ' ' + artName(r.art)); return a; }
function evRows(evs, sv, grpMode) {
  const G = EV.grps || {}, out = [], seen = new Map();
  const one = r => ({ _t: 'ev', id: ek(r), r, start: new Date(r.start).getTime(), src: evSrcName(r), tags: evTags(r), dur: +r.dauer_s || 0, pk: r.spitze_dbfs, thr: r.schwelle_dbfs, bg: r.hintergrund_dbfs });
  for (const r of evs) {
    if (grpMode && r.inc != null && !r.lead) continue;      // gleiche Störung an mehreren Geräten: eine Zeile (lautestes Gerät), Spalte „Geräte“ zeigt die anderen
    const g = grpMode && r.grp != null ? G[r.grp] : null;
    if (g && g.n > 1) {
      let p = seen.get(r.grp);
      if (!p) { p = { _t: 'grp', id: 'g' + r.grp, gid: String(r.grp), g, start: new Date(g.a).getTime(), src: '', tags: [], dur: +g.dur || 0, pk: null, _children: [] }; seen.set(r.grp, p); out.push(p); }
      const c = one(r); p._children.push(c); for (const x of c.tags) if (!p.tags.includes(x)) p.tags.push(x); if (!p.src) p.src = c.src; else if (p.src !== c.src && !p.srcs) p.srcs = true;
      if (c.pk != null && (p.pk == null || c.pk > p.pk)) p.pk = c.pk;
    } else out.push(one(r));
  }
  for (const x of sv) out.push({ _t: 'sens', id: 's:' + x.key, x, start: x.a, src: x.kind === 'ha' ? 'Home Assistant' : x.name || '', tags: [sensIcon(x.kind) + ' ' + sensLabel(x)], dur: Math.max(0, (x.b - x.a) / 1000), pk: x.peak != null ? x.peak : null });
  out.sort((a, b) => b.start - a.start);
  return out;
}
function evAllEv() { const out = []; if (!TBL) return out; const walk = rows => { for (const d of rows) { if (d._t === 'ev') out.push(d); if (d._children) walk(d._children); } }; walk(TBL.getData('active')); return out; }
function evSelToggle(keys, on) {                     // eine Störung = alle Geräte: Auswahl gilt für alle Zeilen derselben Störung
  for (const k of keys) { const r = EV.events.find(y => ek(y) === k); const sib = r && r.inc != null ? EV.events.filter(y => y.inc === r.inc).map(ek) : [k]; for (const x of sib) on ? SEL.add(x) : SEL.delete(x); }
  if (TBL) TBL.getRows('active').forEach(function re(row) { row.reformat(); (row.getTreeChildren ? row.getTreeChildren() : []).forEach(re); });
  syncDelBar();
}
function evGrid(evs, sv, useArt, grpMode) {
  const box = $('events'); if (!box || typeof Tabulator === 'undefined') return;
  const data = EVDATA = evRows(evs, sv, grpMode), hasDev = evs.some(r => (r.devs || []).length > 1), hasPlay = evs.some(r => r.play);
  const valid = new Set(EV.events.map(ek)); for (const k of [...SEL]) if (!valid.has(k)) SEL.delete(k);
  const nar = matchMedia('(max-width:600px)').matches, key = JSON.stringify([lang, useArt, nar]);
  const fmtCell = fn => cell => fn(cell.getRow().getData(), cell);
  const chk = d => d._t === 'ev' ? `<input type="checkbox" class="ckc"${SEL.has(d.id) ? ' checked' : ''} aria-label="${esc(t('ev_sel'))}">`
    : d._t === 'grp' ? `<input type="checkbox" class="ckg"${d._children.every(c => SEL.has(c.id)) ? ' checked' : ''} aria-label="${esc(t('sel_all'))}">` : '';
  const profChip = r => r.prof ? `<span class="art prof${r.bg ? ' bgp' : ''}" title="${esc(t(r.prof_ok ? 'pf_ok_tip' : 'pf_auto_tip'))}">🧩 ${esc(r.prof)}${r.prof_ok ? ' ✓' : r.prof_c != null ? ` <small>${r.prof_c} %</small>` : ''}${r.bg ? ' · ' + esc(t('pf_bg_short')) : ''}</span>` : '';
  const srcHTML = r => srcCell(r).replace(/^<td[^>]*>/, '').replace(/<\/td>$/, '');
  const cols = [
    { formatter: 'responsiveCollapse', width: 30, minWidth: 30, hozAlign: 'center', headerSort: false, responsive: 0, cssClass: 'rcol' },
    { field: 'sel', title: '', headerSort: false, width: nar ? 32 : 40, minWidth: 32, hozAlign: 'center', responsive: 0, cssClass: 'ck',
      titleFormatter: () => { const c = document.createElement('input'); c.type = 'checkbox'; c.id = 'ckall'; c.title = t('sel_all'); c.onclick = e => e.stopPropagation(); c.onchange = () => { evSelToggle(evAllEv().map(d => d.id), c.checked); }; return c; },
      formatter: fmtCell(chk),
      cellClick: (e, cell) => { const d = cell.getRow().getData(); if (d._t === 'ev') evSelToggle([d.id], !SEL.has(d.id)); else if (d._t === 'grp') { const all = d._children.every(c => SEL.has(c.id)); evSelToggle(d._children.map(c => c.id), !all); } } },
    { field: 'play', title: '', headerSort: false, width: 48, minWidth: 48, visible: hasPlay, responsive: 0, cssClass: 'pl',
      formatter: fmtCell(d => d._t === 'ev' && d.r.play ? `<button class="pbtn" type="button" aria-label="${esc(t('ev_play_snd'))}" title="${esc(t('ev_play_snd'))}">▶</button>` : ''),
      cellClick: (e, cell) => { const d = cell.getRow().getData(); if (d._t === 'ev' && e.target.closest('.pbtn')) { e.stopPropagation(); openEvent(d.id, null, true); } } },
    { field: 'start', title: t('start'), sorter: 'number', minWidth: nar ? 120 : 230, widthGrow: 2, responsive: 0, cssClass: 'tm',
      formatter: fmtCell(d => d._t === 'grp' ? `<b>${esc(clockOf(d.g.a).slice(0, nar ? 5 : 8))}–${esc(clockOf(d.g.b).slice(0, nar ? 5 : 8))}</b> <span class="mut">· ${nar ? '×' + d.g.n : esc(t('grp_n', { n: d.g.n }))}</span>`
        : d._t === 'sens' ? `${esc(fmtWhen(new Date(d.x.a).toISOString()))}${d.x.note ? `<span class="ntc" title="${esc(d.x.note)}">📝</span>` : ''}`
        : `${esc(nar ? fmtWhen(d.r.start).replace(/^\S+\s/, '') : fmtWhen(d.r.start))}${d.r.notes ? `<span class="ntc" title="${esc(t('nt_title', { n: d.r.notes }))}">📝 ${d.r.notes}</span>` : ''}`) },
    { field: 'src', title: t('src_col'), minWidth: 160, widthGrow: 2, responsive: 2, cssClass: 'srcc',
      headerFilter: msFilter(() => [...new Set(EVDATA.flatMap(function f(d) { return [d.src].concat((d._children || []).flatMap(f)); }).filter(Boolean))].sort((a, b) => a.localeCompare(b))),
      headerFilterFunc: (hv, rv, rd) => !hv || !hv.length || hv.includes(rv) || (rd._children || []).some(c => hv.includes(c.src)), headerFilterLiveFilter: false,
      formatter: fmtCell(d => d._t === 'ev' ? srcHTML(d.r) : d._t === 'sens' ? `<span class="si">${d.x.kind === 'ha' ? '🏠' : '📱'}</span><span class="sn"><b>${esc(d.src)}</b></span>` : d.srcs ? '<span class="mut">…</span>' : `<span class="sn"><b>${esc(d.src)}</b></span>`) },
    { field: 'tags', title: t('art_col'), minWidth: nar ? 110 : 210, widthGrow: 2, visible: useArt, responsive: 1, cssClass: 'artc', headerSort: false,
      headerFilter: msFilter(() => [...new Set(EVDATA.flatMap(function f(d) { return d.tags.concat((d._children || []).flatMap(f)); }).concat(((EV && EV.ha_names) || []).filter(x => x[1] === 'event').map(x => sensIcon('ha') + ' ' + x[0])))].sort((a, b) => a.localeCompare(b))), headerFilterLiveFilter: false, headerFilterFunc: (hv, rv) => !hv || !hv.length || (rv || []).some(x => hv.includes(x)),
      formatter: fmtCell(d => {
        if (d._t === 'sens') return `<span class="art sensc">${sensIcon(d.x.kind)} ${esc(sensLabel(d.x))}</span>${d.x.note ? `<div class="hant">📝 ${esc(d.x.note)}</div>` : ''}`;
        if (d._t === 'grp') return d.g.prof ? `<span class="art prof">🧩 ${esc(d.g.kind)}</span>` : d.g.kind && d.g.kind !== '?' ? artChip(d.g.kind, null, false) : esc(t('art_pending'));
        const r = d.r; return `${(r.ha_on || []).filter(n => !SHIDE.has('ha:' + n)).map(n => `<span class="art haon" title="${esc(t('ha_on_tip'))}">📡 ${esc(n)} ${esc(t('ha_on'))}</span>`).join('')}${profChip(r)}${(r.labels || []).map(n => `<span class="art lbl" title="${esc(t('lb_own'))}">🏷 ${esc(n)}</span>`).join('')}${r.art ? artChip(r.art, r.art_c, r.art_man) : (r.datei && !(r.labels || []).length && !r.prof ? '<span class="noclip" title="' + esc(t('art_pending')) + '">…</span>' : (r.labels || []).length || r.prof ? '' : '<span class="noclip">–</span>')}`; }) },
    { field: 'kinds', title: t('kinds_col'), minWidth: 150, widthGrow: 2, visible: useArt, responsive: 4, headerSort: false, cssClass: 'kinds', formatter: fmtCell(d => d._t === 'ev' ? kindsHTML(d.r.kinds, EV.fine) : '') },
    { field: 'devs', title: t('devs_col'), minWidth: 130, visible: hasDev, responsive: 5, headerSort: false, cssClass: 'devc',
      formatter: fmtCell(d => { if (d._t !== 'ev') return ''; const x = d.r.devs || []; if (x.length < 2) return '<span class="noclip">–</span>';
        return x.map((v, i) => `<span class="dvp${i === 0 ? ' top' : ''}${v[3] === d.r.k ? ' own' : ''}" title="${esc(v[1])}">${esc(shortName(v[1]))} ${v[2] != null ? v[2].toFixed(0) : '–'}</span>`).join(''); }) },
    { field: 'dur', title: t('dur'), sorter: 'number', minWidth: 90, responsive: 2, cssClass: 'dur', formatter: fmtCell(d => esc(fmtDur(d.dur)) + (d._t === 'sens' && d.x.open ? ' · ' + esc(t('mot_open')) : '')) },
    { field: 'pk', title: t('peak'), sorter: 'number', minWidth: 105, responsive: 3, cssClass: 'pk',
      formatter: fmtCell(d => d.pk == null ? '' : d._t === 'sens' ? esc(f2(d.pk)) + ' <small>' + esc(d.x.unit || '') + '</small>' : esc(fdb(d.pk)) + ' <small>dBFS</small>') },
    { field: 'thr', title: t('thr_col'), sorter: 'number', minWidth: 120, responsive: 6, formatter: fmtCell(d => d._t === 'ev' ? esc(fdb(d.thr)) : '') },
    { field: 'bg', title: t('bg_col'), sorter: 'number', minWidth: 140, responsive: 6, formatter: fmtCell(d => d._t === 'ev' ? esc(fdb(d.bg)) : '') },
    { field: 'clip', title: t('spur_col'), headerSort: false, minWidth: 70, responsive: 5, cssClass: 'clipc',
      formatter: fmtCell(d => { if (d._t !== 'ev') return ''; const r = d.r; return `${r.audio ? `<span class="sndmk" title="${esc(t('snd_mark'))}">🔊</span>` : ''}${r.video ? `<button class="vbtn" title="${esc(t('vid_open'))}" aria-label="${esc(t('vid_open'))}">🎥</button>` : ''}<span class="cs">${r.clip_s && !(r.datei || '').endsWith('.ltv') ? esc(r.clip_s) + ' s' : ''}</span>`; }),
      cellClick: (e, cell) => { const d = cell.getRow().getData(); if (d._t === 'ev' && e.target.closest('.vbtn')) { e.stopPropagation(); openEvent(d.id); } } },
    { field: 'act', title: '', headerSort: false, width: 50, minWidth: 50, hozAlign: 'right', responsive: 0, cssClass: 'act',
      formatter: fmtCell(d => d._t === 'ev' ? `<button class="more" title="${esc(t('actions'))}" aria-label="${esc(t('actions'))}">⋮</button>` : d._t === 'sens' ? `<button class="sned" type="button" title="${esc(t('ha_note'))}" aria-label="${esc(t('ha_note'))}">✎</button>` : ''),
      cellClick: (e, cell) => { const row = cell.getRow(), d = row.getData(); e.stopPropagation();
        if (d._t === 'ev') { const b = cell.getElement().getBoundingClientRect(); openRowMenu(row.getElement(), b.right - 190, b.bottom + 4); }
        else if (d._t === 'sens') haPop({ a: d.x.a, b: d.x.b, name: sensLabel(d.x), note: d.x.note || '', key: d.x.key }); } },
  ];
  if (!TBL || TBL_KEY !== key) {
    if (TBL) { try { TBL.destroy(); } catch (e) { } TBL = null; }
    TBL_KEY = key; box.innerHTML = '';
    TBL = new Tabulator(box, {
      data, columns: cols, index: 'id', layout: 'fitColumns', responsiveLayout: 'collapse', responsiveLayoutCollapseStartOpen: false,
      dataTree: true, dataTreeElementColumn: 'start', dataTreeStartExpanded: row => EVOPEN.has(row.getData().gid || ''), dataTreeChildIndent: 14, dataTreeBranchElement: false,
      dataTreeCollapseElement: '<span class="gtog">▾</span>', dataTreeExpandElement: '<span class="gtog">▸</span>',
      renderVertical: data.length > 400 ? 'virtual' : 'basic', height: data.length > 400 ? '75vh' : false, maxHeight: '75vh',
      placeholder: t('none'), headerSortElement: '<span class="srt"></span>', initialSort: [{ column: 'start', dir: 'desc' }],
      persistence: { sort: true, columns: ['width'] }, persistenceID: 'gl_evtbl',
      rowFormatter: row => { const d = row.getData(), el = row.getElement();
        el.dataset.k = d._t === 'ev' ? d.id : ''; el.dataset.f = d._t === 'ev' ? d.r.datei || '' : ''; el.dataset.inc = d._t === 'ev' && d.r.inc != null ? d.r.inc : '';
        el.classList.toggle('grph', d._t === 'grp'); el.classList.toggle('sensr', d._t === 'sens'); el.classList.toggle('sel', d._t === 'ev' && SEL.has(d.id));
        el.classList.toggle('bgrow', !!(d._t === 'ev' ? d.r.bg || d.r.inc_bg : d._t === 'grp' && d.g.bg)); el.classList.toggle('gm', row.getTreeParent && !!row.getTreeParent()); },
    });
    TBL.on('rowClick', (e, row) => { if (e.target.closest('input,button,a,.ck,.gtog')) return; const d = row.getData();
      if (d._t === 'ev') dtJump(d.id, row.getElement());
      else if (d._t === 'grp') row.treeToggle();
      else if (d._t === 'sens') { const x = d.x; DT.mark = [x.a, Math.max(x.b, x.a + 1000)]; DT.from = x.a - 120000; DT.to = Math.max(x.b, x.a + 1000) + 120000; dtLoad(DT, true); $('ndaybox').scrollIntoView({ behavior: 'smooth', block: 'start' }); } });
    TBL.on('rowDblClick', (e, row) => { const d = row.getData(); if (d._t === 'ev' && !e.target.closest('input,button,a')) openEvent(d.id); });
    TBL.on('rowContext', (e, row) => { const d = row.getData(); if (d._t !== 'ev') return; e.preventDefault(); openRowMenu(row.getElement(), e.clientX, e.clientY); });
    TBL.on('dataTreeRowExpanded', row => { EVOPEN.add(row.getData().gid); });
    TBL.on('dataTreeRowCollapsed', row => { EVOPEN.delete(row.getData().gid); });
    TBL.on('dataFiltered', (f, rows) => { evCount(rows.map(r => r.getData())); });
    TBL.on('tableBuilt', () => { TBL._built = true; evCount(data); syncDelBar(); });
  } else if (TBL._built) {
    TBL.replaceData(data);
    for (const [f, v] of [['play', hasPlay], ['devs', hasDev]]) { try { v ? TBL.showColumn(f) : TBL.hideColumn(f); } catch (e) { } }
    evCount(TBL.getData('active')); syncDelBar();
  } else setTimeout(() => { EVSIG = ''; renderEvents(); }, 200);
}
matchMedia('(max-width:600px)').addEventListener('change', () => { EVSIG = ''; renderEvents(); });
/* Filter unter der Spaltenüberschrift: Liste mit Häkchen (Mehrfachauswahl), Knopf zeigt „alle“ bzw. die Auswahl */
function msFilter(valuesFn) {
  return (cell, onRendered, success) => {
    const b = el('button', { type: 'button', className: 'msf' }); let cur = [];
    const label = () => { b.textContent = (!cur.length ? t('sf_any') : cur.length === 1 ? cur[0] : t('ms_n', { n: cur.length })) + ' ▾'; b.classList.toggle('on', cur.length > 0); };
    const v0 = cell.getValue(); if (Array.isArray(v0)) cur = v0.slice(); label();
    b.onclick = e => {
      e.stopPropagation(); document.querySelectorAll('.msfpop').forEach(x => x.remove());
      const vals = (typeof valuesFn === 'function' ? valuesFn() : []).concat(cur.filter(x => !(typeof valuesFn === 'function' ? valuesFn() : []).includes(x)));
      const pop = el('div', { className: 'msfpop sfltl' }), r = b.getBoundingClientRect();
      pop.style.position = 'fixed'; pop.style.left = Math.max(8, Math.min(r.left, innerWidth - 280)) + 'px'; pop.style.top = (r.bottom + 4) + 'px';
      pop.innerHTML = `<div class="sfltb"><button type="button" class="chip" data-a="all">${esc(t('sf_all'))}</button><button type="button" class="chip" data-a="none">${esc(t('ms_clear'))}</button></div>` +
        (vals.length ? vals.map((v, i) => `<label><input type="checkbox" data-i="${i}"${cur.includes(v) ? ' checked' : ''}> ${esc(v)}</label>`).join('') : `<small class="mut">${esc(t('none'))}</small>`);
      const apply = () => { label(); success(cur.length ? cur.slice() : ''); };
      pop.querySelectorAll('input[data-i]').forEach(c => c.onchange = () => { const v = vals[+c.dataset.i]; cur = c.checked ? [...new Set(cur.concat([v]))] : cur.filter(x => x !== v); apply(); });
      pop.querySelector('[data-a=all]').onclick = () => { cur = vals.slice(); pop.querySelectorAll('input[data-i]').forEach(c => c.checked = true); apply(); };
      pop.querySelector('[data-a=none]').onclick = () => { cur = []; pop.querySelectorAll('input[data-i]').forEach(c => c.checked = false); apply(); };
      pop.onclick = ev => ev.stopPropagation();
      document.body.appendChild(pop);
      const close = ev => { if (!pop.contains(ev.target) && ev.target !== b) { pop.remove(); document.removeEventListener('click', close, true); } };
      setTimeout(() => document.addEventListener('click', close, true), 0);
      const onScroll = ev => { if (pop.contains(ev.target)) return; pop.remove(); removeEventListener('scroll', onScroll, true); }; addEventListener('scroll', onScroll, true);   // beim Scrollen schließen (sonst steht die Liste neben der Spalte)
    };
    return b;
  };
}
function evCount(rows) {                             // Zählung über der Tabelle: Störungen und Sensor-Ereignisse getrennt
  let e = 0, s = 0; const walk = l => { for (const d of l) { if (d._t === 'ev') e++; else if (d._t === 'sens') s++; if (d._children) walk(d._children); } }; walk(rows || []);
  const el = $('evcnt'); if (el) el.textContent = t('ev_cnt', { e, s });
}
const EVOPEN = new Set();
/* Sensor-Filter (Mehrfachauswahl): ausgeblendete Sensoren als 'ha:<Name>', 'vib', 'cam', '_ev' (Störungen) */
let SHIDE = (() => { try { return new Set(JSON.parse(localStorage.getItem('gl_shide') || '[]')); } catch (e) { return new Set(); } })();
/* Filter „Art“ oben als Mehrfachauswahl (z. B. Stimme + Musik): die versteckte Auswahl #artflt liefert die Einträge */
const ARTSEL = new Set();
function artApply() { NV.art = !ARTSEL.size ? '' : ARTSEL.size === 1 ? [...ARTSEL][0] : JSON.stringify([...ARTSEL]); EVSIG = ''; loadNight(); if (EV) renderEvents(); artMsBuild(); }
function artMsBuild() {
  const sel = $('artflt'); if (!sel) return; let box = $('artms');
  if (!box) { box = el('span', { id: 'artms', className: 'sflt artms' }); sel.after(box); }
  const items = [...sel.options].filter(o => o.value && !o.hidden).map(o => [o.value, o.textContent]);
  for (const k of [...ARTSEL]) if (!items.some(i => i[0] === k)) ARTSEL.delete(k);
  const sig = JSON.stringify([items, [...ARTSEL]]); if (box.dataset.sig === sig) return; box.dataset.sig = sig;
  const wasOpen = box.querySelector('details') && box.querySelector('details').open;
  const lbl = !ARTSEL.size ? t('art_all') : ARTSEL.size === 1 ? (items.find(i => ARTSEL.has(i[0])) || ['', ''])[1] : t('art_n', { n: ARTSEL.size });
  box.innerHTML = `<details class="sfltd"${wasOpen ? ' open' : ''}><summary class="chip${ARTSEL.size ? ' pri' : ''}">${esc(lbl)} ▾</summary><div class="sfltl">
    <div class="sfltb"><button type="button" class="chip" data-a="none">${esc(t('art_all'))}</button></div>
    ${items.map(([k, l]) => `<label><input type="checkbox" data-k="${esc(k)}"${ARTSEL.has(k) ? ' checked' : ''}> ${esc(l)}</label>`).join('')}</div></details>`;
  box.querySelectorAll('input[data-k]').forEach(c => c.onchange = () => { c.checked ? ARTSEL.add(c.dataset.k) : ARTSEL.delete(c.dataset.k); artApply(); });
  box.querySelector('button[data-a=none]').onclick = () => { ARTSEL.clear(); artApply(); };
}
document.addEventListener('click', e => { for (const id of ['artms', 'sflt']) { const b = $(id), d = b && b.querySelector('details[open]'); if (d && !b.contains(e.target)) d.open = false; } });
function shideSave() { try { localStorage.setItem('gl_shide', JSON.stringify([...SHIDE])); } catch (e) { } }
const sensKey = x => x.kind === 'ha' ? 'ha:' + x.name : x.kind;
const sensIcon = k => k === 'vib' ? '🫨' : k === 'cam' ? '🏃' : '📡';
const sensLabel = x => x.kind === 'ha' ? x.name : t(x.kind === 'vib' ? 'sens_vib' : 'sens_cam');
function sensVis() { return ((EV && EV.sens) || []).filter(x => !SHIDE.has(sensKey(x))); }
/* Auswahlliste „Sensoren“ (Mehrfachauswahl): Störungen, jede HA-Regel, Handy-Erschütterung, Handy-Bewegung */
function sfltBuild() {
  const box = $('sflt'); if (!box) return;
  const ha = new Set(); for (const x of (EV && EV.sens) || []) if (x.kind === 'ha') ha.add(x.name); for (const a of (NV.data && NV.data.ha) || []) ha.add(a[2]);
  for (const r of (HAR && HAR.rules) || []) if (r.enabled !== false && r.mode !== 'pause') ha.add(r.label || r.name || r.entity);
  for (const x of (EV && EV.ha_names) || []) ha.add(x[0]);   // alle angelegten Regeln, auch ohne Meldung im Zeitraum
  const items = [['_ev', '🔴 ' + t('sf_ev')], ...[...ha].filter(Boolean).sort((a, b) => a.localeCompare(b)).map(n => ['ha:' + n, '📡 ' + n]), ['vib', '🫨 ' + t('sens_vib')], ['cam', '🏃 ' + t('sens_cam')]];
  const sig = JSON.stringify([items, [...SHIDE], lang]); if (box.dataset.sig === sig) return; box.dataset.sig = sig;
  const on = items.filter(i => !SHIDE.has(i[0])).length, wasOpen = box.querySelector('details') && box.querySelector('details').open;
  box.innerHTML = `<details class="sfltd"${wasOpen ? ' open' : ''}><summary class="chip">📡 ${esc(t('sf_btn'))} <small>${on}/${items.length}</small></summary><div class="sfltl">
    <div class="sfltb"><button type="button" class="chip" data-a="all">${esc(t('sf_all'))}</button><button type="button" class="chip" data-a="none">${esc(t('sf_none'))}</button></div>
    ${items.map(([k, l]) => `<label><input type="checkbox" data-k="${esc(k)}"${SHIDE.has(k) ? '' : ' checked'}> ${esc(l)}</label>`).join('')}</div></details>`;
  const apply = () => { shideSave(); EVSIG = ''; renderEvents(); if (NV.open && typeof renderNight === 'function' && NV.data) renderNight(); dtLoad(DT, true); sfltBuild(); };
  box.querySelectorAll('input[data-k]').forEach(c => c.onchange = () => { c.checked ? SHIDE.delete(c.dataset.k) : SHIDE.add(c.dataset.k); apply(); });
  box.querySelectorAll('button[data-a]').forEach(b => b.onclick = () => { for (const [k] of items) b.dataset.a === 'all' ? SHIDE.delete(k) : SHIDE.add(k); apply(); });
}
/* ================= Dashboard: Bereiche als Panels (GridStack, MIT) =================
   Jeder Bereich hat oben eine Leiste: ⠿ verschieben (nur im Modus „Layout anpassen“), Titel, ▾ einklappen, ✕ ausblenden.
   Breite ändern an der Seite; die Höhe folgt dem Inhalt. Am Handy stehen alle untereinander. Gespeichert je Browser. */
const DASH = { grids: {}, def: {}, st: {}, edit: false, ro: null };
function dashDefs() {
  const lv = $('liveview'), nv = $('nightview'), pg = nv.querySelector('.pgrid');
  let ha = $('nhalist'); if (!ha) { ha = el('div', { id: 'nhalist', className: 'nnotes nhalist' }); $('nnotes').after(ha); }
  return {
    live: [
      { id: 'fn', t: 'pn_fn', nodes: [$('fnpanel')], w: 12 },
      { id: 'live', t: 'livetitle', nodes: [$('srcbar') && $('srcbar').parentElement, $('tilebar'), $('vp1')], w: 12 },
      { id: 'ldev', t: 'lev_title', nodes: [$('ldevcard')], w: 12 }],
    prot: [
      { id: 'sum', t: 'pn_sum', nodes: [$('nweek'), nv.querySelector('.nsum')], w: 12 },
      { id: 'run', t: 'pn_run', nodes: [$('nrun')], w: 12, auto: true },
      { id: 'day', t: 'dt_title', nodes: [$('ndaybox')], w: 12 },
      { id: 'hours', t: 'hours', nodes: [pg && pg.children[0]], w: 6 },
      { id: 'days', t: 'days', nodes: [pg && pg.children[1]], w: 6 },
      { id: 'ev', t: 'list', nodes: [nv.querySelector('.pevcard')], w: 12, vis: true },
      { id: 'notes', t: 'pn_notes', nodes: [$('nnotes')], w: 12, auto: true },
      { id: 'ha', t: 'pn_ha', nodes: [ha], w: 12, off: true, vis: true, auto: true }],
  };
}
function dashLoadSt(v) { try { return JSON.parse(localStorage.getItem('gl_dash_' + v) || 'null') || {}; } catch (e) { return {}; } }
function dashSave(v) {
  const g = DASH.grids[v], st = DASH.st[v]; if (!g) return;
  st.lay = g.save(false).map(x => ({ id: x.id, x: x.x, y: x.y, w: x.w }));
  try { localStorage.setItem('gl_dash_' + v, JSON.stringify(st)); } catch (e) { }
}
function dashInit() {
  if (typeof GridStack === 'undefined' || DASH.inited) return; DASH.inited = true;
  const defs = dashDefs();
  DASH.ro = new ResizeObserver(ents => { for (const e of ents) { const it = e.target.closest('.grid-stack-item'), g = it && it.gridstackNode && it.gridstackNode.grid; if (g) g.resizeToContent(it); } });
  for (const [v, list] of Object.entries(defs)) {
    const host = v === 'live' ? $('liveview') : $('nightview'), first = list.map(p => p.nodes[0]).find(Boolean); if (!first) continue;
    const st = DASH.st[v] = dashLoadSt(v); st.col = st.col || {}; st.off = st.off || list.filter(p => p.off).map(p => p.id); st.vis = st.vis || {};
    const bar = el('div', { className: 'dashbar' }), gEl = el('div', { className: 'grid-stack dashgrid' }); gEl.dataset.view = v;
    first.before(bar); bar.after(gEl);
    const lay = {}; for (const x of st.lay || []) lay[x.id] = x;
    const items = [];
    for (const p of list) {
      const ns = p.nodes.filter(Boolean); if (!ns.length) continue;
      const it = el('div', { className: 'grid-stack-item' }), ct = el('div', { className: 'grid-stack-item-content' }), pn = el('div', { className: 'pnl' }); pn.dataset.p = p.id;
      const hd = el('div', { className: 'pnlhd' });
      hd.innerHTML = `<span class="pdrag" title="${esc(t('dash_drag'))}">⠿</span><b data-i="${p.t}">${esc(t(p.t))}</b><span class="pnlx"></span>` +
        (p.vis ? `<button type="button" class="pvis" title="${esc(t('dash_vis_tip'))}">⌖ ${esc(t('dash_vis'))}</button>` : '') +
        `<button type="button" class="pcol" aria-label="${esc(t('dash_col'))}" title="${esc(t('dash_col'))}">▾</button><button type="button" class="phide" aria-label="${esc(t('dash_hide'))}" title="${esc(t('dash_hide'))}">✕</button>`;
      const bd = el('div', { className: 'pnlbd' }); ns.forEach(n => bd.appendChild(n));
      pn.append(hd, bd); ct.appendChild(pn); it.appendChild(ct);
      const L = lay[p.id]; it.setAttribute('gs-id', p.id); it.setAttribute('gs-w', String(L ? L.w : p.w)); if (L) { it.setAttribute('gs-x', L.x); it.setAttribute('gs-y', L.y); }
      gEl.appendChild(it); items.push([p, it, pn]);
      hd.querySelector('.pcol').onclick = () => { st.col[p.id] = !st.col[p.id]; dashApply(v); dashSave(v); };
      hd.querySelector('.phide').onclick = () => { if (!st.off.includes(p.id)) st.off.push(p.id); dashApply(v); dashSave(v); dashBar(v); };
      hd.ondblclick = e => { if (!e.target.closest('button')) hd.querySelector('.pcol').click(); };
      if (p.vis) hd.querySelector('.pvis').onclick = () => { st.vis[p.id] = !st.vis[p.id]; dashApply(v); dashSave(v); visChanged(); };
      if (p.auto) { const n0 = ns[0]; const sync = () => pn.classList.toggle('pempty', !!n0.hidden || !n0.childElementCount); new MutationObserver(sync).observe(n0, { attributes: true, attributeFilter: ['hidden'], childList: true }); sync(); }
    }
    pg_cleanup(host);
    const g = DASH.grids[v] = GridStack.init({ column: 12, cellHeight: 8, margin: 6, float: false, staticGrid: true, sizeToContent: true, handle: '.pdrag', animate: true,
      resizable: { handles: 'e,w' }, columnOpts: { breakpoints: [{ w: 760, c: 1 }], layout: 'list' } }, gEl);
    g.on('change', () => { if (DASH.edit) dashSave(v); });     // auch Höhenänderungen durch den Inhalt: nur im Bearbeiten speichern
    g.on('resizestop dragstop', () => { dashSave(v); dashResized(); });
    items.forEach(([p, it, pn]) => DASH.ro.observe(pn));
    DASH.def[v] = list;
    dashApply(v); dashBar(v);
  }
}
function pg_cleanup(host) { const pg = host.querySelector('.pgrid'); if (pg && !pg.children.length) pg.remove(); }
function dashApply(v) {
  const g = DASH.grids[v], st = DASH.st[v]; if (!g) return;
  g.el.querySelectorAll(':scope > .grid-stack-item').forEach(it => { const id = it.getAttribute('gs-id'), pn = it.querySelector('.pnl');
    pn.classList.toggle('pcolx', !!st.col[id]); pn.querySelector('.pcol').textContent = st.col[id] ? '▸' : '▾';
    const vb = pn.querySelector('.pvis'); if (vb) vb.classList.toggle('on', !!st.vis[id]);
    const off = st.off.includes(id);
    if (off && it.gridstackNode) { g.removeWidget(it, false, false); it.style.display = 'none'; }
    else if (!off && !it.gridstackNode) { it.style.display = ''; it.setAttribute('gs-y', '9999'); it.removeAttribute('gs-x'); g.makeWidget(it); }   // wieder eingeblendet: unten anfügen
    if (!off) g.resizeToContent(it); });
}
function dashResized() { clearTimeout(DASH.rt); DASH.rt = setTimeout(() => { window.dispatchEvent(new Event('resize')); if (TBL) try { TBL.redraw(); } catch (e) { } }, 120); }
function dashRefresh() { for (const v of Object.keys(DASH.grids)) { const g = DASH.grids[v]; g.onResize(); g.getGridItems().forEach(it => g.resizeToContent(it)); } }
function dashBar(v) {
  const g = DASH.grids[v], st = DASH.st[v], bar = g && g.el.previousElementSibling; if (!bar) return;
  const defs = DASH.def[v] || [];
  bar.innerHTML = `<button type="button" class="chip dedit${DASH.edit ? ' pri' : ''}">▦ ${esc(t(DASH.edit ? 'dash_done' : 'dash_edit'))}</button>` +
    (DASH.edit ? `<span class="dashoff">${defs.map(p => `<label><input type="checkbox" data-p="${p.id}"${st.off.includes(p.id) ? '' : ' checked'}> ${esc(t(p.t))}</label>`).join('')}</span><button type="button" class="chip dreset">↺ ${esc(t('dash_reset'))}</button>` :
      st.off.length ? `<small class="mut">${esc(t('dash_hidden', { n: st.off.length }))}</small>` : '');
  bar.querySelector('.dedit').onclick = () => { DASH.edit = !DASH.edit; for (const k of Object.keys(DASH.grids)) { DASH.grids[k].setStatic(!DASH.edit); DASH.grids[k].el.classList.toggle('dashedit', DASH.edit); dashBar(k); } };
  bar.querySelectorAll('.dashoff input').forEach(c => c.onchange = () => { const id = c.dataset.p; st.off = st.off.filter(x => x !== id); if (!c.checked) st.off.push(id); dashApply(v); dashSave(v); });
  const rs = bar.querySelector('.dreset'); if (rs) rs.onclick = () => { if (!confirm(t('dash_reset_q'))) return; try { localStorage.removeItem('gl_dash_' + v); } catch (e) { } location.reload(); };
}
/* „nur sichtbarer Bereich“: Tabelle bzw. Sensor-Liste folgen dem Zoom im Verlauf */
function dashVis(id) { const st = DASH.st.prot; return !!(st && st.vis && st.vis[id]) && DT.from != null && DT.to != null; }
function visChanged() { clearTimeout(DASH.vt); DASH.vt = setTimeout(() => { if (TBL && TBL._built) { if (dashVis('ev')) TBL.setFilter(d => d.start + (d.dur || 0) * 1000 >= DT.from && d.start <= DT.to); else TBL.clearFilter(); } haListRender(); }, 250); }

/* Anklickbare Stelle im Verlauf: bei Überlappung (z. B. Fernseher und Türsensor gleichzeitig) gewinnt die engste Fläche */
function hitAt(S, x, y) {
  let best = null, bs = Infinity;
  for (const q of S.downHit || []) { if (x < q[0] || x > q[1] || (q[4] != null && y > q[4]) || (q[5] != null && y < q[5])) continue;
    const sp = (q[4] != null ? q[4] : 1e4) - (q[5] != null ? q[5] : -1e4) + (q[1] - q[0]) * 1e-3; if (sp < bs) { bs = sp; best = q; } }
  return best;
}
/* Farbe je Sensor (Regel „als Ereignis“): selbst gewählt, sonst fest aus dem Namen – gleich in allen Zeilen und Ansichten */
const SENS_PAL = ['#e8590c', '#d6336c', '#7048e8', '#0ca678', '#f59f00', '#1098ad', '#ae3ec9', '#74b816'];
function sensCol(a) { if (a && a[6]) return a[6]; const n = String((a && a[2]) || ''); let h = 0; for (let i = 0; i < n.length; i++) h = (h * 31 + n.charCodeAt(i)) >>> 0; return SENS_PAL[h % SENS_PAL.length]; }
function haLanes(list) { const m = new Map(); for (const n of [...new Set(list.map(a => a[2]))].sort((a, b) => a.localeCompare(b))) m.set(n, m.size); return m; }   // feste Reihenfolge der Spuren (nach Name), gleich in allen Zeilen                            // aufgeklappte Gruppen
let EVVIEW = (() => { try { return localStorage.getItem('laerm_evview') || 'grp'; } catch (e) { return 'grp'; } })();
const clockOf = iso => { const d = new Date(iso); return isNaN(d) ? '' : pad(d.getHours()) + ':' + pad(d.getMinutes()) + ':' + pad(d.getSeconds()); };
const shortName = n => { n = String(n || ''); return n.length > 12 ? n.slice(0, 11) + '…' : n; };
let EVSIG = '';
/* Filter "Art": eigene Namen der benannten Bereiche zusaetzlich zu den Geraeuscharten */
function syncLabelFilter() {
  const sel = $('artflt'), want = [...new Set(EV.events.flatMap(r => r.labels || []))].sort((a, b) => a.localeCompare(b));
  const have = [...sel.options].filter(o => o.value.startsWith('lb:')).map(o => o.value.slice(3));
  if (JSON.stringify(want) === JSON.stringify(have)) return;
  const cur = sel.value;
  [...sel.options].filter(o => o.value.startsWith('lb:')).forEach(o => o.remove());
  const none = [...sel.options].find(o => o.value === '_none');
  for (const n of want) { const o = document.createElement('option'); o.value = 'lb:' + n; o.textContent = '🏷 ' + n; sel.insertBefore(o, none || null); }
  sel.value = [...sel.options].some(o => o.value === cur) ? cur : '';
}
const SRC_ICON = { local: '🎙', phone: '📱', url: '📡' };
function srcCell(r) {
  const s = SOURCES.find(x => x.id === (r.quelle_id || 'main'));
  const type = s ? s.type : (r.quelle_id === 'main' || !r.quelle_id ? 'local' : '');
  const name = r.quelle || (s && s.name) || r.quelle_id || '';
  const dev = s ? (s.device_info || (type === 'local' ? t('input_dev', { d: (CUR && CUR.device) || 'default' }) : t('type_' + type))) : t('src_gone');
  return `<td class="srcc"><span class="si" title="${esc(type ? t('type_' + type) : t('src_gone'))}">${SRC_ICON[type] || '❓'}</span><span class="sn"><b>${esc(name)}</b><small>${esc(dev)}</small></span></td>`;
}
function selectedKeys() { return [...SEL]; }
function syncDelBar() {
  const n = selectedKeys().length, bar = $('delbar');
  bar.style.display = n ? 'flex' : 'none'; $('artsel').hidden = !!(CUR && CUR.classify === false); $('events').classList.toggle('selmode', n > 0);
  $('delcount').textContent = t('sel_count', { n });
  const all = $('ckall'), tot = evAllEv().length;
  if (all) { all.checked = n > 0 && n >= tot; all.indeterminate = n > 0 && n < tot; }
}
async function deleteEvents(keys) {
  if (!keys.length) return;
  if (!confirm(keys.length === 1 ? t('confirm_del_ev') : t('confirm_del_evs', { n: keys.length }))) return;
  try {
    const r = await (await fetch('delete_events', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ keys }) })).json();
    if (!r.ok) throw new Error(r.error || 'error');
    if (r.deleted < keys.length) alert(t('del_partial', { n: r.deleted, m: keys.length }));
    lastCount = -1; await loadEvents(); syncDelBar(); loadSources(); if (NV.open) loadNight();   // Kopfzahlen und Verlauf auch neu
  } catch (e) { alert(t('saveerr') + ' ' + e.message); }
}
/* Kontextmenue je Zeile (Knopf ⋮ oder Rechtsklick) */
function openRowMenu(tr, x, y) {
  const m = $('rowmenu'), f = tr.dataset.f;
  const dl = m.querySelector('a.dl');
  if (f && !/\.wav$/i.test(f)) { dl.href = 'clips/' + encodeURIComponent(f); dl.setAttribute('download', f); dl.classList.remove('dis'); }
  else { dl.removeAttribute('href'); dl.classList.add('dis'); }
  m.querySelector('.del1').onclick = () => { closeRowMenu(); deleteEvents([tr.dataset.k]); };
  m.querySelector('.view1').onclick = () => { closeRowMenu(); openEvent(tr.dataset.k); };
  const a1 = m.querySelector('.art1'); a1.hidden = !f || /\.wav$/i.test(f) || (CUR && CUR.classify === false);
  a1.onclick = () => { closeRowMenu(); recheckEvents([f]); };
  m.querySelector('.sel1').onclick = () => { closeRowMenu(); evSelToggle([tr.dataset.k], !SEL.has(tr.dataset.k)); };
  { const on = SEL.has(tr.dataset.k), s1 = m.querySelector('.sel1'); s1.querySelector('.mi').textContent = on ? '☑' : '☐'; s1.querySelector('span').textContent = t(on ? 'm_unselect' : 'm_select'); }
  m.style.display = 'block';
  const w = m.offsetWidth, h = m.offsetHeight;
  m.style.left = Math.max(8, Math.min(x, innerWidth - w - 8)) + 'px';
  m.style.top = Math.max(8, Math.min(y, innerHeight - h - 8)) + 'px';
  document.querySelectorAll('#events .menu').forEach(r => r.classList.remove('menu')); tr.classList.add('menu');
  const first = m.querySelector('a.dl:not(.dis)') || m.querySelector('.sel1'); MENU_AT = Date.now(); if (first) first.focus({ preventScroll: true });
}
/* ---------- Ereignis ansehen: gespeicherte Laermspur, "Ablauf zeigen", Marker und benannte Bereiche ---------- */
/* Ablauf ohne Ton: eine Uhr mit derselben Schnittstelle wie ein Mediaplayer (currentTime, play, pause ...),
   damit Abspiel-Linie, Sprung zu Notizen und das stumme Video unveraendert funktionieren. */
class VClock {
  constructor(dur) { this.duration = dur; this.t = 0; this.paused = true; this.ended = false; this.raf = 0; this.readyState = 4; this.onplay = this.onpause = this.onended = this.ontimeupdate = null; }
  get currentTime() { if (!this.paused) this.t = Math.min(this.duration, this.t0 + (performance.now() - this.p0) / 1000); return this.t; }
  set currentTime(v) { this.t = clamp(v || 0, 0, this.duration); this.t0 = this.t; this.p0 = performance.now(); this.ended = false; if (this.ontimeupdate) this.ontimeupdate(); }
  play() {
    if (!this.paused) return Promise.resolve();
    if (this.t >= this.duration - 0.01) this.t = 0;
    this.paused = false; this.ended = false; this.t0 = this.t; this.p0 = performance.now();
    const tick = () => {
      if (this.paused) return;
      const ct = this.currentTime; if (this.ontimeupdate) this.ontimeupdate();
      if (ct >= this.duration) { this.paused = true; this.ended = true; if (this.onended) this.onended(); return; }
      this.raf = requestAnimationFrame(tick);
    };
    this.raf = requestAnimationFrame(tick); if (this.onplay) this.onplay();
    return Promise.resolve();
  }
  pause() { if (this.paused) return; this.t = this.currentTime; this.paused = true; cancelAnimationFrame(this.raf); if (this.onpause) this.onpause(); }
  addEventListener(_e, f) { f(); }
}
const EVV = { g: null, row: null, a: null, k: null, raf: 0, lut: null, labels: { l: [], rej: [] }, sugg: [], marks: [], fine: {}, names: [], hit: [] };
function evDecode(g) {
  const nb = (g.bands || []).length || NB;
  const R = g.recs.map(r => { const sb = atob(r[5] || ''), sp = new Uint8Array(nb); for (let i = 0; i < nb && i < sb.length; i++) sp[i] = sb.charCodeAt(i); return { o: r[0], l: r[1], b: r[2], t: r[3], a: r[4], sp }; });
  R.nb = nb; R.step = g.step || 100;
  return R;
}
const ART_HEX = { knock: '#e0314b', door: '#e8590c', steps: '#f0a500', voice: '#7048e8', tv: '#1c7ed6', scrape: '#c2255c', signal: '#2b8a3e', animal: '#66a80f', noise: '#868e96', other: '#868e96' };
const darkUI = () => { const r = document.documentElement.getAttribute('data-theme'); return r ? r === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches; };
const lbCol = name => { let h = 0; for (const ch of String(name)) h = (h * 31 + ch.charCodeAt(0)) >>> 0; return `hsl(${h % 360} 70% ${darkUI() ? 64 : 45}%)`; };   // dunkel: heller, sonst kaum lesbar
async function openEvent(k, seekOff, autoPlay) {
  const d = $('evdlg'); EVV.k = k; EVV.notes = []; EVV.sel = null; ntEditorClose(); lbPopClose(); renderNotes();
  $('evinfo').textContent = t('listen_load'); $('evnone').textContent = ''; if (!d.open) d.showModal();
  let j;
  try { j = await (await fetch('event?k=' + encodeURIComponent(k), { cache: 'no-store' })).json(); } catch (e) { j = { ok: false }; }
  if (!j.ok) { $('evinfo').textContent = t('ev_gone'); return; }
  const r = j.row; EVV.row = r; EVV.g = j.graph; EVV.spc = null;
  EVV.d = j.graph ? evDecode(j.graph) : [];
  EVV.marks = (j.ki && j.ki.marks) || []; EVV.fine = j.fine || {}; EVV.labels = j.labels || { l: [], rej: [] }; EVV.sugg = j.sugg || []; EVV.names = j.names || [];
  EVV.vOff = j.graph && j.graph.core ? j.graph.core[0] / 1000 : 0;          // Video beginnt mit dem Ereignis, die Spur mit dem Umfeld davor
  $('evtitle').textContent = '📈 ' + fmtWhen(r.start) + ' · ' + (r.quelle || r.quelle_id || '');
  $('evinfo').innerHTML = [[t('dur'), fmtDur(r.dauer_s)], [t('peak'), fdb(r.spitze_dbfs) + ' dBFS'], [t('thr_col'), fdb(r.schwelle_dbfs) + ' dBFS'],
    [t('bg_col'), fdb(r.hintergrund_dbfs) + ' dBFS'], [t('spur_len'), r.clip_s ? r.clip_s + ' s' : '–']].concat(preInfo(j.graph, parseFloat(r.spitze_dbfs))).concat(haInfo(j.graph)).map(([a, b, tip]) => `<span${tip ? ` title="${esc(tip)}"` : ''}><small>${esc(a)}</small><b>${esc(String(b))}</b></span>`).join('');
  renderEvArt(j); renderEvProf(j);
  EVV.notes = j.notes || []; if (j.note_tags) NOTE_TAGS = j.note_tags; renderNotes(); renderLabels(); EVV.snote = j.snote || {}; renderSubs(j); enoteShow(j.enote || ''); renderEvLists(j.plists); renderCmp(j); renderEvFn(j.fnotes);
  $('evnone').textContent = !j.graph ? t('ev_nograph') : j.graph.final === false ? t('ev_partial') : '';
  document.querySelector('.evcvs').style.display = j.graph ? '' : 'none';
  if (EVV.a) { EVV.a.pause(); EVV.a = null; }
  const pb = $('evplay'), dl = $('evdl'), vdl = $('evvdl');
  const vbox = $('evvidbox'), vv = $('evvid'); vbox.hidden = !r.video; vv.pause(); vv.removeAttribute('src'); vv.load(); vv.muted = true;
  const au = $('evaudio'); au.pause(); au.removeAttribute('src'); au.load();
  const snd = EVV.snd = !!j.wav;                          // echter Ton nur, wenn fuer das Geraet eingeschaltet
  if (snd) au.src = 'clips/' + encodeURIComponent(j.wav);
  EVV.aOff = j.graph && j.graph.core && /\.lsp$/i.test(r.datei || '') ? j.graph.core[0] / 1000 : 0;   // Ton beginnt mit dem Vorlauf
  const stem = r.datei ? r.datei.replace(/\.(wav|lsp)$/i, '') : '';
  if (j.graph) {
    const total = Math.max(0.5, parseFloat(j.graph.clip_s) || (EVV.d.length ? EVV.d[EVV.d.length - 1].o / 1000 : 0));
    const a = EVV.a = new VClock(total);
    if (r.video) vv.src = 'clips/' + encodeURIComponent(stem + '.mp4');
    const lbl = snd ? 'ev_play_snd' : 'ev_show';
    a.onended = a.onpause = () => { pb.textContent = '▶ ' + t(lbl); if (!vv.paused) vv.pause(); if (!au.paused) au.pause(); evDraw(); };
    a.onplay = () => { pb.textContent = '⏸ ' + t('ev_show_stop'); evLoop(); };
    a.ontimeupdate = () => {
      $('evtime').textContent = a.currentTime.toFixed(1) + ' / ' + total.toFixed(1) + ' s';
      if (snd && au.readyState >= 1) {                     // Ton (falls gespeichert) an der richtigen Stelle mitlaufen lassen
        const at = a.currentTime - EVV.aOff;
        if (at < 0 || at > (au.duration || 0)) { if (!au.paused) au.pause(); }
        else { if (Math.abs(au.currentTime - at) > 0.25) au.currentTime = at; if (!a.paused && au.paused) au.play().catch(() => { }); if (a.paused && !au.paused) au.pause(); }
      }
      if (r.video && vv.readyState >= 1) {                 // stummes Video mitlaufen lassen
        const vt = a.currentTime - EVV.vOff;
        if (vt < 0 || vt > (vv.duration || 0)) { if (!vv.paused) vv.pause(); vv.currentTime = clamp(vt, 0, vv.duration || 0); }
        else { if (Math.abs(vv.currentTime - vt) > 0.35) vv.currentTime = vt; if (!a.paused && vv.paused) vv.play().catch(() => { }); if (a.paused && !vv.paused) vv.pause(); }
      }
    };
    pb.disabled = false; pb.textContent = '▶ ' + t(lbl); $('evtime').textContent = '0.0 / ' + total.toFixed(1) + ' s';
  } else { pb.disabled = true; pb.textContent = '▶ ' + t('ev_show'); $('evtime').textContent = ''; }
  pb.hidden = !snd; $('evtime').hidden = !snd;          // Abspielen nur mit gespeichertem echtem Ton (sonst ausgeblendet)
  const lsp = /\.lsp$/i.test(r.datei || '');
  dl.style.display = lsp ? '' : 'none'; if (lsp) { dl.href = 'clips/' + encodeURIComponent(r.datei); dl.setAttribute('download', r.datei); }
  vdl.style.display = r.video ? '' : 'none'; if (r.video) { vdl.href = 'clips/' + encodeURIComponent(stem + '.mp4'); vdl.setAttribute('download', stem + '.mp4'); }
  $('evlegacy').hidden = !j.legacy || snd;
  const wn = $('evwavnote'); wn.hidden = !j.wav_skip && !(j.has_wav && !snd && !j.legacy);
  wn.textContent = j.wav_skip === 'voice' ? t('snd_skip_voice') : j.wav_skip === 'error' ? t('snd_skip_err') : t('snd_off_hint');
  requestAnimationFrame(evDraw);
  if (seekOff != null) ntSeek(seekOff); else if (autoPlay && EVV.a && snd) EVV.a.play();
}
function evLoop() { cancelAnimationFrame(EVV.raf); const f = () => { evDraw(); if (EVV.a && !EVV.a.paused) EVV.raf = requestAnimationFrame(f); }; EVV.raf = requestAnimationFrame(f); }
/* ================= Protokolllisten ================= */
const PV = { open: false, lists: [], cur: '', ev: null, form: '' };
try { PV.cur = localStorage.getItem('laerm_plist') || ''; } catch (e) { }
async function plFetch() { try { PV.lists = (await (await fetch('plists', { cache: 'no-store' })).json()).lists || []; } catch (e) { } plFillMove(); return PV.lists; }
async function plPost(name, body) {
  const r = await (await fetch(name, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })).json();
  if (!r.ok) throw new Error(r.error || 'error'); if (r.lists) { PV.lists = r.lists; plFillMove(); } return r;
}
function plName(id) { const x = PV.lists.find(l => l.id === id); return x ? x.name : id; }
function plFillMove() {                                     // Auswahlleiste der Gesamtliste: "In Liste uebernehmen"
  const sel = $('plmove'); if (!sel) return;
  sel.innerHTML = `<option value="">📋 ${esc(t('pl_move'))}</option>` + PV.lists.map(l => `<option value="${esc(l.id)}">${esc(l.name)}</option>`).join('');
  sel.hidden = !PV.lists.length; sel.setAttribute('aria-label', t('pl_move'));
}
function plRefresh() {                               // Filter „Liste“ im Reiter Protokolle, dazu Werkzeuge und Notiz der gewählten Liste
  if (PV.cur && !PV.lists.some(l => l.id === PV.cur)) PV.cur = '';
  const sel = $('nplist'); sel.innerHTML = `<option value="">${esc(t('pl_all'))}</option>` + PV.lists.map(l => `<option value="${esc(l.id)}">📋 ${esc(l.name)} (${l.n})</option>`).join(''); sel.value = PV.cur;
  const has = !!PV.cur; $('plbody').hidden = !has; $('plren').hidden = $('pldel').hidden = !has; $('plrmsel').hidden = !has;
  $('pladd').title = t('pl_new'); $('plren').title = t('pl_rename'); $('pldel').title = t('pl_delete');
  if (!has) return;
  const L = PV.lists.find(l => l.id === PV.cur);
  const ta = $('plnote'); if (document.activeElement !== ta) { ta.value = L.note || ''; ta.dataset.old = L.note || ''; }
  const rules = SOURCES.flatMap(s => (s.plists || []).filter(r => r.id === PV.cur).map(r => s.name + (r.from || r.to ? ` ${r.from || '00:00'}–${r.to || '24:00'}` : ` (${t('pl_always')})`)));
  $('plinfo').textContent = rules.length ? t('pl_auto', { r: rules.join(' · ') }) : t('pl_auto_none');
}
function plFormOpen(kind) {
  PV.form = kind; $('plform').hidden = false; const i = $('plname');
  i.value = kind === 'ren' ? plName(PV.cur) : ''; i.focus(); i.select();
}
async function plFormOk() {
  const v = $('plname').value.trim(); if (!v) return;
  try {
    if (PV.form === 'add') { const r = await plPost('plist_add', { name: v }); PV.cur = r.id; try { localStorage.setItem('laerm_plist', PV.cur); } catch (e) { } }
    else await plPost('plist_edit', { id: PV.cur, name: v });
    $('plform').hidden = true; plRefresh(); loadNight();
  } catch (e) { alert(t('saveerr')); }
}
async function plNoteSave() {
  const ta = $('plnote'); if (!PV.cur || ta.value.trim() === (ta.dataset.old || '').trim()) return;
  $('plstat').textContent = t('en_saving');
  try { await plPost('plist_edit', { id: PV.cur, note: ta.value }); ta.dataset.old = ta.value; $('plstat').textContent = t('en_saved'); } catch (e) { $('plstat').textContent = t('saveerr'); }
}
/* Ereignisfenster: in welchen Listen steht das Ereignis, von Hand hinzufuegen */
function renderEvLists(ids) {
  const box = $('evlists'); EVV.plists = ids || [];
  if (!PV.lists.length) { box.innerHTML = ''; return; }
  const rest = PV.lists.filter(l => !EVV.plists.includes(l.id));
  box.innerHTML = `<small>${esc(t('pl_in'))}</small>` + EVV.plists.map(id => `<span class="art lbl plchip">📋 ${esc(plName(id))}<button type="button" class="plx" data-id="${esc(id)}" title="${esc(t('pl_remove'))}" aria-label="${esc(t('pl_remove'))}">✕</button></span>`).join('') +
    (rest.length ? `<select class="pladd" aria-label="${esc(t('pl_move'))}"><option value="">＋ ${esc(t('pl_move'))}</option>${rest.map(l => `<option value="${esc(l.id)}">${esc(l.name)}</option>`).join('')}</select>` : '');
  box.querySelectorAll('.plx').forEach(b => b.onclick = async () => { try { await plPost('plist_mem', { id: b.dataset.id, keys: [EVV.k], add: false }); renderEvLists(EVV.plists.filter(x => x !== b.dataset.id)); } catch (e) { alert(t('saveerr')); } });
  const sel = box.querySelector('.pladd'); if (sel) sel.onchange = async () => { const id = sel.value; if (!id) return; try { await plPost('plist_mem', { id, keys: [EVV.k], add: true }); renderEvLists(EVV.plists.concat(id)); } catch (e) { alert(t('saveerr')); } };
}

/* Was kam in einer Stoerung vor: "✊ Klopfen ×10 · 🍽 Geschirr ×3 · 🎵 Musik 12 s" */
function kindsHTML(list, fine) {
  if (!list || !list.length) return '';
  const dur = s => s >= 60 ? Math.floor(s / 60) + ':' + String(Math.round(s % 60)).padStart(2, '0') + ' min' : (s < 10 ? s.toFixed(1) : Math.round(s)) + ' s';
  return list.map(([k, n, d]) => { const f = (fine || {})[k] || {}; return `<span class="kd" title="${esc((f.name || k) + (n != null ? ' · ' + dur(d) : ''))}">${f.icon || '•'} ${esc(f.name || k)} <b>${n != null ? '×' + n : dur(d)}</b></span>`; }).join('');
}
function fineName(k) { const f = EVV.fine[k]; return f ? f.name : k; }
function fineIcon(k) { const f = EVV.fine[k]; return f ? f.icon : '•'; }
// Text in einer Pille; liefert die Breite
function pill(c, txt, x, y, bg, fg, d, dashed) {
  c.font = '600 ' + (10.5 * d) + 'px system-ui'; const w = c.measureText(txt).width + 10 * d, h = 15 * d;
  c.fillStyle = bg; c.beginPath(); c.roundRect ? c.roundRect(x, y, w, h, 7 * d) : c.rect(x, y, w, h); c.fill();
  if (dashed) { c.setLineDash([3 * d, 2 * d]); c.strokeStyle = fg; c.lineWidth = 1 * d; c.stroke(); c.setLineDash([]); }
  c.fillStyle = fg; c.textAlign = 'left'; c.fillText(txt, x + 5 * d, y + 11 * d);
  return w;
}
function evDraw() {
  const g = EVV.g, R = EVV.d; if (!g || !R || !R.length || !$('evdlg').open) return;
  const NBe = R.nb || NB, stp = R.step || 100;
  const total = Math.max(500, (g.clip_s || 0) * 1000, R[R.length - 1].o);
  // Pegel
  const cv = $('evcv'); fit(cv);
  const d = DPR(), c = cv.getContext('2d'), w = cv.width, h = cv.height, L = 52 * d, Rr = 14 * d, T = 10 * d, B = 22 * d, pw = w - L - Rr, ph = h - T - B;
  const X = o => L + pw * o / total;
  let mn = 1e9, mx = -1e9; for (const r of R) { for (const v of [LAY.lvl ? r.l : null, LAY.bg ? r.b : null, LAY.thr ? r.t : null]) if (v != null && v > -125) { mn = Math.min(mn, v); mx = Math.max(mx, v); } accLayers(v => { if (v != null && v > -125) { mn = Math.min(mn, v); mx = Math.max(mx, v); } }, r, g.bands); }
  if (mn > mx) { mn = -90; mx = -30; }
  const pad = Math.max(1, (mx - mn) * 0.08); let lo = mn - pad, hi = mx + pad; if (hi - lo < 6) { const m = (hi + lo) / 2; lo = m - 3; hi = m + 3; }
  const Y = v => T + ph * (1 - clamp((v - lo) / (hi - lo), 0, 1));
  c.clearRect(0, 0, w, h); c.font = (11 * d) + 'px system-ui'; c.textAlign = 'right'; c.lineWidth = 1;
  // Raster, dB-Achse, Zeitachse (Sekunden ab Beginn der Spur), Pegel, Hintergrund, Schwelle: uPlot
  const up = upGet(cv, { kind: 'lvl', L: 52, R: 14, T: 10, B: 22, pal: livePal, rel: true });
  up.u.setSeries(1, { show: !!LAY.lvl }); up.u.setSeries(2, { show: !!LAY.bg }); up.u.setSeries(3, { show: !!LAY.thr });
  upDraw(up, (R._uid || (R._uid = ++UPID)) + '', () => { const Xs = [], P = [], Bg = [], Th = []; for (const r of R) { Xs.push(r.o - stp / 2); P.push(r.l != null && r.l > -125 ? r.l : null); Bg.push(r.b != null ? r.b : null); Th.push(r.t != null ? r.t : null); } return [Xs, P, Bg, Th]; }, 0, total, lo, hi);
  c.save(); c.beginPath(); c.rect(L, T, pw, ph); c.clip();
  // Ereignis (rot) und Nachlauf; a=2 ueber der Schwelle, a=1 Nachlauf (heller); aeltere Ereignisse kennen nur a=1
  const hasCore = R.some(r => r.a === 2);
  const spans = (test, fill, bar, bh) => { let s0 = -1; for (let i = 0; i <= R.length; i++) { const on = i < R.length && test(R[i].a); if (on && s0 < 0) s0 = i; if (!on && s0 >= 0) { const a0 = X(R[s0].o - stp), a1 = X(R[i - 1].o); c.fillStyle = fill; c.fillRect(a0, T, a1 - a0, ph); c.fillStyle = bar; c.fillRect(a0, T, a1 - a0, bh * d); s0 = -1; } } };
  if (hasCore) spans(a => a === 1, C.red + '0c', C.red + '55', 2);
  if (hasCore) {                                      // Vorlauf hellrot wie der Nachlauf
    const c0 = g.core && g.core[0] != null ? g.core[0] : (R[0].o - stp), first = R.find(r => r.a === 2);
    if (first && first.o - stp > c0) { const a0 = X(c0), a1 = X(first.o - stp); c.fillStyle = C.red + '0c'; c.fillRect(a0, T, a1 - a0, ph); c.fillStyle = C.red + '55'; c.fillRect(a0, T, a1 - a0, 2 * d); }
  }
  spans(a => hasCore ? a === 2 : !!a, C.red + '26', C.red, 3);
  // Benannte Bereiche (von Hand) und Vorschlaege
  for (const x of EVV.labels.l || []) { const col = lbCol(x.name), a0 = X(x.a), a1 = X(x.b); c.fillStyle = col.replace(')', ' / .16)'); c.fillRect(a0, T, a1 - a0, ph); c.fillStyle = col; c.fillRect(a0, T + ph - 3 * d, a1 - a0, 3 * d); }
  const core = g.core && g.core.length > 1 && g.core[0] != null ? g.core : null, outside = x => core && (x[1] < core[0] || x[0] > core[1]);   // Vorschläge außerhalb der Störung zurücknehmen
  for (const x of EVV.sugg || []) { const col = lbCol(x[2]), a0 = X(x[0]), a1 = X(x[1]); c.globalAlpha = outside(x) ? 0.3 : 1; c.strokeStyle = col; c.lineWidth = 1.5 * d; c.setLineDash([5 * d, 4 * d]); c.strokeRect(a0, T + 1 * d, a1 - a0, ph - 2 * d); c.setLineDash([]); }
  c.globalAlpha = 1;
  if (core) { c.strokeStyle = C.red; c.lineWidth = 1.5 * d; c.beginPath(); for (const o of [core[0], core[1]]) { const x = X(o); c.moveTo(x, T); c.lineTo(x, T + ph); } c.stroke(); }   // Beginn und Ende der Störung
  if (EVV.sel) { const a0 = X(Math.min(EVV.sel.a, EVV.sel.b)), a1 = X(Math.max(EVV.sel.a, EVV.sel.b)); c.fillStyle = C.acc + '33'; c.fillRect(a0, T, a1 - a0, ph); c.strokeStyle = C.acc; c.lineWidth = 1.5 * d; c.strokeRect(a0, T, a1 - a0, ph); }
  const line = (key, col, wd, dash) => { c.beginPath(); let on = false; for (const r of R) { const v = r[key]; if (v == null) { on = false; continue; } const x = X(r.o - stp / 2), y = Y(v); if (!on) { c.moveTo(x, y); on = true; } else c.lineTo(x, y); } c.setLineDash(dash.map(q => q * d)); c.strokeStyle = col; c.lineWidth = wd * d; c.stroke(); c.setLineDash([]); };
  // Pegel, Hintergrund und Schwelle zeichnet uPlot
  drawLayers(c, R.map(r => ({ x: X(r.o - stp / 2), r, brk: false })), Y, g.bands, d, L, pw, T, ph);
  drawRefs(c, g.refs || [], v => [Y(v)], lo, hi, L, pw, T, ph, d);
  // KI-Marker: Leiste unten in der Grafik (Symbol und Name, wenn Platz ist)
  EVV.hit = [];
  for (const m of EVV.marks) {                        // Farbe wie die Geraeuschart-Gruppe, Text nur wenn er hineinpasst
    const a0 = X(m[0]), a1 = Math.max(X(m[1]), X(m[0]) + 3 * d), y = T + ph - 19 * d, txt = fineIcon(m[2]) + ' ' + fineName(m[2]) + ' ' + m[3] + ' %';
    const col = ART_HEX[(EVV.fine[m[2]] || {}).group] || ART_HEX.other;
    c.save(); c.globalAlpha = .22; c.fillStyle = col; c.fillRect(a0, y, a1 - a0, 16 * d); c.globalAlpha = 1; c.fillStyle = col; c.fillRect(a0, y + 14 * d, a1 - a0, 2 * d); c.restore();
    c.font = '600 ' + (10 * d) + 'px system-ui'; c.textAlign = 'left';
    const short = fineIcon(m[2]), lab = c.measureText(txt).width + 6 * d <= a1 - a0 ? txt : c.measureText(short).width + 4 * d <= a1 - a0 ? short : '';
    if (lab) { c.fillStyle = C.tx; c.fillText(lab, a0 + 3 * d, y + 11.5 * d); }
    EVV.hit.push({ x0: a0 / d, x1: a1 / d, y0: y / d, y1: (y + 16 * d) / d, tip: fineName(m[2]) + ' ' + m[3] + ' %' });
  }
  // Notizen: Linie + Faehnchen mit Nummer
  (EVV.notes || []).forEach((n, i) => {
    const x = X(n.off * 1000), col = noteCol(n), hl = EVV.ntHi === n.id;
    c.strokeStyle = col; c.lineWidth = (hl ? 2.5 : 1.5) * d; c.setLineDash([4 * d, 3 * d]); c.beginPath(); c.moveTo(x, T + 16 * d); c.lineTo(x, T + ph); c.stroke(); c.setLineDash([]);
    c.fillStyle = col; c.beginPath(); c.arc(x, T + 9 * d, 8 * d, 0, 2 * Math.PI); c.fill();
    c.fillStyle = '#fff'; c.font = '700 ' + (10 * d) + 'px system-ui'; c.textAlign = 'center'; c.fillText(String(i + 1), x, T + 12.5 * d);
  });
  // Beschriftung der Bereiche (oben, unter den Notiz-Faehnchen); ueberlappende Beschriftungen weichen in die naechste Zeile aus
  const lanes = [], lane = (x0, wdt) => { let i = 0; while (lanes[i] != null && lanes[i] > x0 - 4 * d) i++; lanes[i] = x0 + wdt; return T + 20 * d + i * 18 * d; };
  c.font = '600 ' + (10.5 * d) + 'px system-ui';
  for (const x of (EVV.labels.l || []).slice().sort((u, v) => u.a - v.a)) { const txt = '🏷 ' + x.name, x0 = X(x.a) + 2 * d; pill(c, txt, x0, lane(x0, c.measureText(txt).width + 10 * d), lbCol(x.name), '#fff', d); }
  for (const x of (EVV.sugg || []).slice().sort((u, v) => u[0] - v[0])) {
    const txt = x[2] + '? ' + x[3] + ' %', x0 = X(x[0]) + 2 * d; c.font = '600 ' + (10.5 * d) + 'px system-ui';
    c.globalAlpha = outside(x) ? 0.35 : 1;
    const y0 = lane(x0, c.measureText(txt).width + 10 * d), wdt = pill(c, txt, x0, y0, C.card, lbCol(x[2]), d, true); c.globalAlpha = 1;
    EVV.hit.push({ x0: x0 / d, x1: (x0 + wdt) / d, y0: y0 / d, y1: (y0 + 15 * d) / d, sugg: x });
  }
  if (NTE && !NTE.id) { const x = X((EVV.ntPrev != null ? EVV.ntPrev : NTE.off) * 1000); c.strokeStyle = C.acc; c.lineWidth = 2 * d; c.setLineDash([2 * d, 3 * d]); c.beginPath(); c.moveTo(x, T); c.lineTo(x, T + ph); c.stroke(); c.setLineDash([]); }
  // Ablauf-Linie
  if (EVV.a && (EVV.a.currentTime > 0 || !EVV.a.paused)) { const x = X(EVV.a.currentTime * 1000); c.strokeStyle = '#2b8a3e'; c.lineWidth = 2.5 * d; c.beginPath(); c.moveTo(x, T); c.lineTo(x, T + ph); c.stroke(); }
  c.restore();
  c.textAlign = 'right'; c.font = '600 ' + (11 * d) + 'px system-ui';
  if (g.thr != null && LAY.thr) {
    const out = g.thr > hi || g.thr < lo;
    if (out) thrEdge(c, R.map(r => [X(r.o - stp / 2), r.t != null ? r.t : g.thr]), lo, hi, L, T, pw, ph, d, C.thr, 2);
    lblBox(c, out ? thrTxt(g.thr, lo, hi) : t('threshold') + ' ' + g.thr.toFixed(1), L + pw - 4 * d, g.thr > hi ? T + 16 * d : g.thr < lo ? T + ph - 6 * d : Y(g.thr) - 5 * d, C.thr, d);
  }
  // Spektrum
  const sv = $('evsp'); fit(sv);
  const s = sv.getContext('2d'), sw = sv.width, sh = sv.height, sT = 2 * d, sB = 4 * d, sph = sh - sT - sB;
  s.clearRect(0, 0, sw, sh); s.fillStyle = C.grid; s.fillRect(L, sT, pw, sph);   // Bereich ohne Daten neutral (wie die leere Pegelgrafik), nicht schwarz
  if (!EVV.spc || EVV.spc.R !== R) {                  // Spektrogramm-Bild nur einmal pro Ereignis berechnen
    const hist = new Uint32Array(256); let n = 0; for (const r of R) for (let k = 0; k < NBe; k++) { hist[r.sp[k]]++; n++; }
    const pct = q => { let acc = 0; for (let v = 0; v < 256; v++) { acc += hist[v]; if (acc >= q * n) return v; } return 255; };
    const lo2 = pct(0.05), hi2 = Math.max(pct(0.997), lo2 + 40);
    const tc = document.createElement('canvas'); tc.width = R.length; tc.height = NBe;
    const img = tc.getContext('2d').createImageData(R.length, NBe), px = img.data;
    R.forEach((r, x) => { for (let k = 0; k < NBe; k++) { const cc = cmap((r.sp[k] - lo2) / (hi2 - lo2)), o = 4 * ((NBe - 1 - k) * R.length + x); px[o] = cc[0]; px[o + 1] = cc[1]; px[o + 2] = cc[2]; px[o + 3] = 255; } });
    tc.getContext('2d').putImageData(img, 0, 0); EVV.spc = { R, tc };
  }
  const tmp = EVV.spc.tc;
  s.imageSmoothingEnabled = true; s.drawImage(tmp, X(R[0].o - stp), sT, X(R[R.length - 1].o) - X(R[0].o - stp), sph);
  for (const x of EVV.labels.l || []) { const col = lbCol(x.name); s.strokeStyle = col; s.lineWidth = 2 * d; s.strokeRect(X(x.a), sT + 1 * d, X(x.b) - X(x.a), sph - 2 * d); }
  if (EVV.sel) { const a0 = X(Math.min(EVV.sel.a, EVV.sel.b)), a1 = X(Math.max(EVV.sel.a, EVV.sel.b)); s.fillStyle = '#ffffff33'; s.fillRect(a0, sT, a1 - a0, sph); s.strokeStyle = C.acc; s.lineWidth = 1.5 * d; s.strokeRect(a0, sT, a1 - a0, sph); }
  (EVV.notes || []).forEach(n => { const x = X(n.off * 1000); s.strokeStyle = noteCol(n); s.lineWidth = 1.5 * d; s.beginPath(); s.moveTo(x, sT); s.lineTo(x, sT + sph); s.stroke(); });
  if (EVV.a && (EVV.a.currentTime > 0 || !EVV.a.paused)) { const x = X(EVV.a.currentTime * 1000); s.strokeStyle = '#fff'; s.lineWidth = 2 * d; s.beginPath(); s.moveTo(x, sT); s.lineTo(x, sT + sph); s.stroke(); }
  EVV.geo = { L: L / d, pw: pw / d, total };
  drawCmp();
}
function evAt(e) { const r = e.currentTarget.getBoundingClientRect(), gg = EVV.geo; return gg ? clamp((e.clientX - r.left - gg.L) / gg.pw, 0, 1) * gg.total : 0; }
function evSeek(e) {
  if (EVV.lpDone) { EVV.lpDone = false; return; }      // langes Druecken hat eine Notiz angelegt
  if (EVV.dragDone) { EVV.dragDone = false; return; }  // Bereich wurde aufgezogen
  if (!EVV.a || !EVV.geo) return;
  if (e.currentTarget.id === 'evcv') {                 // Klick auf einen Vorschlag: bestaetigen oder ablehnen
    const r = e.currentTarget.getBoundingClientRect(), x = e.clientX - r.left, y = e.clientY - r.top;
    const h = EVV.hit.find(q => q.sugg && x >= q.x0 && x <= q.x1 && y >= q.y0 && y <= q.y1);
    if (h) { suggPop(h.sugg, e.clientX, e.clientY); return; }
  }
  EVV.a.currentTime = evAt(e) / 1000; if (EVV.a.paused) EVV.a.play(); evDraw();
}
/* Bereich aufziehen (Maus oder Finger waagerecht ziehen) und benennen */
function lbBind() {
  for (const id of ['evcv', 'evsp']) {
    const cv = $(id); let st = null;
    cv.addEventListener('pointerdown', e => { if (e.button && e.button !== 0) return; st = { x: e.clientX, y: e.clientY, a: evAt(e), id: e.pointerId, on: false }; });
    cv.addEventListener('pointermove', e => {
      if (!st || e.pointerId !== st.id) return;
      if (!st.on && Math.abs(e.clientX - st.x) > 8 && Math.abs(e.clientX - st.x) > Math.abs(e.clientY - st.y)) { st.on = true; try { cv.setPointerCapture(e.pointerId); } catch (x) { } lbPopClose(); if (EVV.a && !EVV.a.paused) EVV.a.pause(); }
      if (st.on) { EVV.sel = { a: st.a, b: evAt(e) }; evDraw(); }
      const r = cv.getBoundingClientRect(), x = e.clientX - r.left, y = e.clientY - r.top;     // Hinweis beim Zeigen auf einen KI-Marker
      const h = !st.on && EVV.hit.find(q => q.tip && x >= q.x0 && x <= q.x1 && y >= q.y0 && y <= q.y1); cv.title = h ? h.tip : '';
    });
    const end = e => {
      if (!st) return;
      if (st.on) { EVV.dragDone = true; const a = Math.min(EVV.sel.a, EVV.sel.b), b = Math.max(EVV.sel.a, EVV.sel.b); if (b - a >= 150) lbPopOpen({ a, b }, e.clientX, e.clientY); else { EVV.sel = null; evDraw(); } }
      st = null;
    };
    cv.addEventListener('pointerup', end); cv.addEventListener('pointercancel', () => { st = null; EVV.sel = null; evDraw(); });
  }
  $('evlbl').onclick = () => { EVV.lbHint = !EVV.lbHint; $('evlbhint').hidden = !EVV.lbHint; };
}
const fmtRange = (a, b) => fmtOff(Math.round(a / 100) / 10) + '–' + fmtOff(Math.round(b / 100) / 10);
function lbPopClose() { const p = $('lbpop'); if (p) p.hidden = true; }
function popPlace(p, x, y) { const dr = $('evdlg').getBoundingClientRect(); p.hidden = false; const w = p.offsetWidth, h = p.offsetHeight; p.style.left = clamp(x - dr.left - w / 2, 8, dr.width - w - 8) + 'px'; p.style.top = clamp(y - dr.top + 12, 8, dr.height - h - 8) + 'px'; }
function lbPopOpen(sel, x, y, edit) {
  const p = $('lbpop'); EVV.sel = sel; EVV.lbEdit = edit || null;
  // Vorschlaege fuer den Namen: KI-Marker in diesem Bereich, dann eigene Namen, dann alle Arten
  const inR = EVV.marks.filter(m => Math.min(m[1], sel.b) - Math.max(m[0], sel.a) > 0).sort((u, v) => v[3] - u[3]).map(m => fineName(m[2]));
  const own = EVV.names.map(n => n.name), kiN = [...new Set(inR)].filter(n => !own.includes(n)).slice(0, 6);
  $('lbtitle').textContent = t(edit ? 'lb_edit_t' : 'lb_title', { r: fmtRange(sel.a, sel.b) });
  $('lbname').value = edit ? edit.name : '';
  $('lbquick').innerHTML = (own.length ? `<small class="lbqh">${esc(t('mk_have'))}</small>` + EVV.names.slice(0, 16).map(n => `<button type="button" class="chip ntchip" data-n="${esc(n.name)}">${n.pf ? '🧩 ' : '🏷 '}${esc(n.name)}</button>`).join('') : '')
    + (kiN.length ? `<small class="lbqh">${esc(t('mk_ki'))}</small>` + kiN.map(n => `<button type="button" class="chip ntchip" data-n="${esc(n)}">${esc(n)}</button>`).join('') : '');
  $('lbquick').querySelectorAll('button').forEach(b => b.onclick = () => { $('lbname').value = b.dataset.n; $('lbname').focus(); });
  $('lbdl').innerHTML = [...new Set([...EVV.names.map(n => n.name), ...Object.values(EVV.fine).map(f => f.name)])].map(n => `<option value="${esc(n)}">`).join('');
  popPlace(p, x, y); $('lbname').focus(); evDraw();
}
async function lbPost(action, data) {
  const r = await (await fetch('label_' + action, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(Object.assign({ k: EVV.k }, data)) })).json();
  if (!r.ok) throw new Error(r.error === 'bad label' ? t('lb_empty') : (r.error || 'error'));
  EVV.labels = r.labels; EVV.sugg = r.sugg || []; EVV.names = r.names || EVV.names; renderLabels(); evDraw(); EVSIG = ''; loadEvents();
  return r;
}
async function lbSave() {
  const name = $('lbname').value.trim(), sel = EVV.sel; if (!sel) return;
  if (!name) { $('lbname').focus(); return; }
  try { await lbPost(EVV.lbEdit ? 'edit' : 'add', { id: EVV.lbEdit && EVV.lbEdit.id, a: Math.round(sel.a), b: Math.round(sel.b), name }); EVV.sel = null; lbPopClose(); evDraw(); }
  catch (e) { alert(t('saveerr') + ' ' + e.message); }
}
function suggPop(x, cx, cy) {
  const p = $('sgpop');
  $('sgtitle').textContent = t('lb_sugg_q', { n: x[2], p: x[3], r: fmtRange(x[0], x[1]) });
  $('sgyes').onclick = async () => { p.hidden = true; try { await lbPost('add', { a: x[0], b: x[1], name: x[2] }); } catch (e) { alert(e.message); } };
  $('sgno').onclick = async () => { p.hidden = true; try { await lbPost('reject', { a: x[0], b: x[1], name: x[2] }); } catch (e) { alert(e.message); } };
  $('sgshow').onclick = () => { p.hidden = true; EVV.a.currentTime = Math.max(0, x[0] / 1000 - 1); EVV.a.play(); };
  popPlace(p, cx, cy);
}
/* Einzelereignisse innerhalb der Stoerung: jede Spitze bzw. jedes Geraeusch mit Uhrzeit, Art, Sicherheit, Spitze und Dauer */
function renderSubs(j) {
  const box = $('subbox'), L = (j.ki && j.ki.subs) || [];
  box.hidden = !j.ki;
  if (!j.ki) return;
  const t0 = j.graph && j.graph.t0, fine = j.fine || {};
  const clk = ms => { if (!t0) return fmtOffS(ms); const d = new Date(t0 + ms); return d.toLocaleTimeString(lang === 'en' ? 'en-GB' : 'de-DE', { hour: '2-digit', minute: '2-digit', second: '2-digit' }) + (lang === 'en' ? '.' : ',') + Math.floor(d.getMilliseconds() / 100); };
  $('subhead').textContent = t('sub_head', { n: L.length });
  $('sublist').innerHTML = L.length ? L.map(([ms, k, pct, pk, dur], i) => { const f = fine[k] || {};
    const sn = (EVV.snote || {})[String(ms)] || '';
    return `<div class="ntrow subrow" data-ms="${ms}" tabindex="0"><span class="ntnum subic">${f.icon || '•'}</span><span class="ntoff">${esc(clk(ms))}</span><span class="nttx"><b>${esc(f.name || k)}</b>${pct ? ` <small>${pct} %</small>` : ''}${sn ? `<span class="subnote">📝 ${esc(sn)}</span>` : ''}</span><span class="subpk">${pk != null ? esc(pk.toFixed(1)) + ' <small>dBFS</small>' : ''}</span><span class="subdur">${dur ? esc((dur / 1000).toFixed(1)) + ' s' : ''}</span><span class="ntact"><button type="button" class="subed" title="${esc(t(sn ? 'sn_edit' : 'sn_add'))}" aria-label="${esc(t(sn ? 'sn_edit' : 'sn_add'))}">✎</button></span></div>`; }).join('')
    : `<div class="ntnone">${esc(t('sub_none'))}</div>`;
  $('sublist').querySelectorAll('.subrow').forEach(r => {
    r.onclick = e => { if (e.target.closest('.subed,.subin')) return; if (!EVV.a) return; EVV.a.currentTime = Math.max(0, +r.dataset.ms / 1000 - 1); EVV.a.play(); };
    r.onkeydown = e => { if (e.key === 'Enter' && e.target === r) r.click(); };
    r.querySelector('.subed').onclick = () => subNoteEdit(r, j);
  });
}
/* Notiz zu einem Einzelereignis: direkt in der Zeile bearbeiten (Enter = speichern, Esc = abbrechen, leer = loeschen) */
function subNoteEdit(r, j) {
  if (r.querySelector('.subin')) return;
  const ms = r.dataset.ms, old = (EVV.snote || {})[ms] || '';
  const inp = el('input', { type: 'text', className: 'subin', maxLength: 500, value: old, placeholder: t('sn_ph') });
  r.querySelector('.nttx').appendChild(inp); inp.focus();
  const done = async save => {
    if (!inp.isConnected) return;
    if (save && inp.value.trim() !== old) {
      try { const x = await (await fetch('snote', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ k: EVV.k, ms: +ms, text: inp.value }) })).json(); if (!x.ok) throw new Error(x.error); EVV.snote = x.snote; EVSIG = ''; loadEvents(); } catch (e) { alert(t('saveerr')); }
    }
    renderSubs(j);
  };
  inp.onkeydown = e => { if (e.key === 'Enter') { e.preventDefault(); done(true); } else if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); done(false); } };
  inp.onblur = () => done(true);
}
/* Notiz zum Gesamtereignis: wird beim Verlassen des Feldes gespeichert */
function enoteShow(text) {
  const ta = $('enote'); ta.value = text; ta.dataset.old = text; $('enstat').textContent = '';
}
async function enoteSave() {
  const ta = $('enote'); if (ta.value.trim() === (ta.dataset.old || '').trim()) return;
  $('enstat').textContent = t('en_saving');
  try {
    const x = await (await fetch('enote', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ k: EVV.k, text: ta.value }) })).json();
    if (!x.ok) throw new Error(x.error);
    ta.dataset.old = x.enote; $('enstat').textContent = t('en_saved'); EVSIG = ''; loadEvents();
  } catch (e) { $('enstat').textContent = t('saveerr'); }
}
function fmtOffS(ms) { const s = ms / 1000; return Math.floor(s / 60) + ':' + (s % 60).toFixed(1).padStart(4, '0'); }
function renderLabels() {
  const box = $('lblist'); if (!box) return;
  const L = (EVV.labels.l || []).slice().sort((a, b) => a.a - b.a), S = EVV.sugg || [];
  $('lbhead').textContent = t('lb_list', { n: L.length });
  box.innerHTML = (L.length || S.length ? '' : `<div class="ntnone">${esc(t('lb_none'))}</div>`) +
    L.map(x => `<div class="ntrow lbrow" data-id="${esc(x.id)}" tabindex="0"><span class="ntnum" style="background:${lbCol(x.name)}">🏷</span><span class="ntoff">${esc(fmtRange(x.a, x.b))}</span><span class="nttx"><b>${esc(x.name)}</b></span>
      <span class="ntact"><button type="button" class="lbsim" title="${esc(t('lb_similar'))}" aria-label="${esc(t('lb_similar'))}">🔎</button><button type="button" class="lbed" title="${esc(t('nt_edit'))}" aria-label="${esc(t('nt_edit'))}">✎</button><button type="button" class="lbdel" title="${esc(t('nt_del'))}" aria-label="${esc(t('nt_del'))}">🗑</button></span></div>`).join('') +
    S.map((x, i) => `<div class="ntrow lbrow sg" data-s="${i}" tabindex="0"><span class="ntnum sgn" style="border-color:${lbCol(x[2])};color:${lbCol(x[2])}">?</span><span class="ntoff">${esc(fmtRange(x[0], x[1]))}</span><span class="nttx">${esc(t('lb_sugg'))}: <b>${esc(x[2])}</b> <small>${x[3]} %</small></span>
      <span class="ntact"><button type="button" class="sgy" title="${esc(t('lb_yes'))}">✓</button><button type="button" class="sgn2" title="${esc(t('lb_no'))}">✕</button></span></div>`).join('');
  box.querySelectorAll('.lbrow:not(.sg)').forEach(row => {
    const x = L.find(q => q.id === row.dataset.id);
    row.onclick = e => { if (e.target.closest('button')) return; EVV.a && (EVV.a.currentTime = Math.max(0, x.a / 1000 - 1), EVV.a.play()); };
    row.querySelector('.lbed').onclick = e => { const b = e.currentTarget.getBoundingClientRect(); lbPopOpen({ a: x.a, b: x.b }, b.left, b.bottom, x); };
    row.querySelector('.lbdel').onclick = async () => { if (!confirm(t('lb_del_q', { n: x.name }))) return; try { await lbPost('del', { id: x.id }); } catch (e) { alert(e.message); } };
    row.querySelector('.lbsim').onclick = () => openSimilar(x.name);
  });
  box.querySelectorAll('.lbrow.sg').forEach(row => {
    const x = S[+row.dataset.s];
    row.onclick = e => { if (e.target.closest('button')) return; EVV.a && (EVV.a.currentTime = Math.max(0, x[0] / 1000 - 1), EVV.a.play()); };
    row.querySelector('.sgy').onclick = async () => { try { await lbPost('add', { a: x[0], b: x[1], name: x[2] }); } catch (e) { alert(e.message); } };
    row.querySelector('.sgn2').onclick = async () => { try { await lbPost('reject', { a: x[0], b: x[1], name: x[2] }); } catch (e) { alert(e.message); } };
  });
}
/* Aehnliche finden: alle Ereignisse nach einem gelernten Namen durchsuchen */
async function openSimilar(name) {
  const dl = $('simdlg'); $('simtitle').textContent = '🔎 ' + t('lb_sim_title', { n: name }); $('simlist').innerHTML = `<div class="ntnone">⏳ ${esc(t('lb_sim_run'))}</div>`; $('siminfo').textContent = '';
  if (!dl.open) dl.showModal();
  let j; try { j = await (await fetch('similar?name=' + encodeURIComponent(name), { cache: 'no-store' })).json(); } catch (e) { j = { ok: false, error: e.message }; }
  if (!j.ok) { $('simlist').innerHTML = `<div class="ntnone">${esc(j.error === 'no examples' ? t('lb_sim_noex') : t('art_err'))}</div>`; return; }
  $('siminfo').textContent = t('lb_sim_count', { n: j.n, m: j.searched }) + (j.cut ? ' · ' + t('lb_sim_cut') : '');
  $('simlist').innerHTML = j.hits.length ? j.hits.map((x, i) => `<div class="ntrow simrow" data-i="${i}" tabindex="0"><span class="ntnum" style="background:${lbCol(name)}">${x.own ? '🏷' : '▶'}</span><span class="ntoff" data-clk=" · ${esc(x.quelle)}">${esc(fmtWhen(x.start))}</span><span class="ntclk">${esc(x.quelle)}</span><span class="nttx">${esc(fmtRange(x.a, x.b))} · ${x.own ? esc(t('lb_own')) : x.pct + ' %'}</span><span></span></div>`).join('')
    : `<div class="ntnone">${esc(t('lb_sim_none'))}</div>`;
  $('simlist').querySelectorAll('.simrow').forEach(r => { const x = j.hits[+r.dataset.i]; r.onclick = () => { dl.close(); openEvent(x.k, Math.max(0, x.a / 1000)); }; r.onkeydown = e => { if (e.key === 'Enter') r.click(); }; });
}
/* ================= Alle Notizen (Uebersicht, CSV, Protokoll) ================= */
const NTA = { tags: new Set(), list: [] };
function ntaParams(extra) {
  const p = new URLSearchParams();
  if ($('ntafrom').value) p.set('from', $('ntafrom').value); if ($('ntato').value) p.set('to', $('ntato').value);
  if ($('ntasrc').value !== 'all') p.set('src', $('ntasrc').value);
  if (NTA.tags.size) p.set('tags', [...NTA.tags].join(',')); if ($('ntaq').value.trim()) p.set('q', $('ntaq').value.trim());
  for (const k in (extra || {})) if (extra[k]) p.set(k, extra[k]);
  return p.toString();
}
async function ntaLoad() {
  try { NTA.list = (await (await fetch('notes?' + ntaParams(), { cache: 'no-store' })).json()).notes || []; } catch (e) { NTA.list = []; }
  const L = NTA.list.slice().reverse();
  $('ntacount').textContent = t('nt_title', { n: L.length });
  $('ntalist').innerHTML = L.length ? L.map((n, i) => `<div class="ntrow nta" data-i="${i}" tabindex="0"><span class="ntnum" style="background:${noteCol(n)}">▶</span>
      <span class="ntoff" data-clk=" · ${esc(n.clock)}${n.rz ? ' 🌙' : ''}">${esc(fmtDay(n.date || n.start.slice(0, 10)))}</span><span class="ntclk">${esc(n.clock)}${n.rz ? ' 🌙' : ''}</span>
      <span class="nttx">${(n.tags || []).map(ntTag).join('')}${n.text ? `<span class="ntt">${esc(n.text)}</span>` : ''}${n.witness ? `<span class="ntw">👤 ${esc(n.witness)}</span>` : ''}<span class="ntw">${esc(n.quelle)}</span></span><span></span></div>`).join('')
    : `<div class="ntnone">${esc(t('nt_none_all'))}</div>`;
  $('ntalist').querySelectorAll('.ntrow').forEach(r => { const n = L[+r.dataset.i]; r.onclick = () => { $('ntadlg').close(); if (n.free) fnOpen(n); else openEvent(n.k, n.off); }; r.onkeydown = e => { if (e.key === 'Enter') r.click(); }; });
  ntaLinks();
}
function ntaLinks() {
  const pr = { name: $('ntaname').value.trim(), addr: $('ntaaddr').value.trim(), flat: $('ntaflat').value.trim(), all: $('ntaall').checked ? '1' : '' };
  try { localStorage.setItem('laerm_proto', JSON.stringify(pr)); } catch (e) { }
  $('ntacsv').href = 'notes.csv?' + ntaParams(); $('ntaproto').href = 'protokoll.html?' + ntaParams(pr);
}
function openAllNotes() {
  const sel = $('ntasrc'), opts = [['all', t('all_sources')]].concat(SOURCES.map(x => [x.id, x.name]));
  sel.innerHTML = opts.map(([v, l]) => `<option value="${esc(v)}">${esc(l)}</option>`).join('');
  $('ntatags').innerHTML = Object.keys(NOTE_TAGS).map(g => NOTE_TAGS[g].map(tg => `<button type="button" class="chip ntchip g-${g}${NTA.tags.has(tg) ? ' on' : ''}" data-t="${tg}">${esc(t('nt_' + tg))}</button>`).join('')).join('');
  $('ntatags').querySelectorAll('.ntchip').forEach(b => b.onclick = () => { const tg = b.dataset.t; NTA.tags.has(tg) ? NTA.tags.delete(tg) : NTA.tags.add(tg); b.classList.toggle('on'); ntaLoad(); });
  try { const pr = JSON.parse(localStorage.getItem('laerm_proto') || '{}'); $('ntaname').value = pr.name || ''; $('ntaaddr').value = pr.addr || ''; $('ntaflat').value = pr.flat || ''; $('ntaall').checked = pr.all === '1'; } catch (e) { }
  $('ntadlg').showModal(); ntaLoad();
}
function ntaBind() {
  for (const id of ['ntafrom', 'ntato', 'ntasrc']) $(id).onchange = ntaLoad;
  let tq = 0; $('ntaq').oninput = () => { clearTimeout(tq); tq = setTimeout(ntaLoad, 300); };
  for (const id of ['ntaname', 'ntaaddr', 'ntaflat', 'ntaall']) $(id).addEventListener('input', ntaLinks), $(id).addEventListener('change', ntaLinks);
  $('ntax').onclick = () => $('ntadlg').close();
}
/* ================= Notizen zu Zeitpunkten im Clip ================= */
let NOTE_TAGS = { src: ['oben', 'unten', 'nebenan', 'treppenhaus', 'draussen', 'unklar'], kind: ['klopfen', 'schritte', 'musik', 'stimmen', 'tuer', 'moebel', 'bohren', 'hund'],
  lvl: ['leicht', 'deutlich', 'stark'], eff: ['aufgewacht', 'kind_geweckt', 'kein_schlaf', 'gestoert'], act: ['geklingelt', 'angesprochen', 'verwaltung', 'polizei'], misc: ['zeuge', 'serie'] };
const NT_GCOL = { src: '#0ca678', kind: '#e0314b', lvl: '#f08c00', eff: '#7048e8', act: '#1c7ed6', misc: '#868e96' };
function ntGroup(tag) { for (const g in NOTE_TAGS) if (NOTE_TAGS[g].includes(tag)) return g; return 'misc'; }
function noteCol(n) {                                  // Farbe nach wichtigstem Tag: Auswirkung > Art > Massnahme > Rest
  const tg = n.tags || []; for (const g of ['eff', 'kind', 'act', 'lvl', 'src', 'misc']) if (tg.some(x => ntGroup(x) === g)) return NT_GCOL[g];
  return C.acc;
}
const ntTag = tg => `<span class="ntag g-${ntGroup(tg)}">${esc(t('nt_' + tg))}</span>`;
const fmtOff = o => { const m = Math.floor(o / 60), s2 = o - m * 60; return m + ':' + (s2 < 10 ? '0' : '') + s2.toFixed(1); };
function ntNow() {                                     // Position fuer eine neue Notiz: Ablauf-Linie, sonst Spitze
  if (EVV.a && EVV.a.currentTime > 0) return Math.round(EVV.a.currentTime * 10) / 10;
  const R = EVV.d || [], st2 = (R.step || 100) / 2; let best = null; for (const r of R) if (r.l != null && (!best || r.l > best.l)) best = r;
  return best ? Math.max(0, Math.round((best.o - st2) / 100) / 10) : 0;
}
function ntSyncBtn() { const b = $('evnote'); if (b) b.innerHTML = '📝 ' + esc(t('nt_add_at', { t: fmtOff(ntNow()) })); }
let NTE = null;                                        // offene Eingabe: { id|null, off, tags:Set }
function ntEditorOpen(off, note) {
  if (EVV.a && !EVV.a.paused) EVV.a.pause();
  NTE = { id: note ? note.id : null, off: note ? note.off : off, tags: new Set(note ? note.tags || [] : []) }; EVV.ntPrev = NTE.off;
  const box = $('nted'); box.hidden = false;
  $('ntoff').value = NTE.off.toFixed(1); $('nttext').value = note ? note.text || '' : ''; $('ntwit').value = note ? note.witness || '' : '';
  $('ntsave').textContent = t(note ? 'nt_update' : 'nt_save'); $('ntedtitle').textContent = t(note ? 'nt_edit_t' : 'nt_new');
  $('nttags').innerHTML = Object.keys(NOTE_TAGS).map(g => `<div class="ntgrp g-${g}"><div class="ntgl">${esc(t('ntg_' + g))}</div><div class="ntgc">${NOTE_TAGS[g].map(tg => `<button type="button" class="ntchip g-${g}${NTE.tags.has(tg) ? ' on' : ''}" data-t="${tg}" aria-pressed="${NTE.tags.has(tg)}">${esc(t('nt_' + tg))}</button>`).join('')}</div></div>`).join('');
  ntClock();
  $('nttags').querySelectorAll('.ntchip').forEach(b => b.onclick = () => { const tg = b.dataset.t; NTE.tags.has(tg) ? NTE.tags.delete(tg) : NTE.tags.add(tg); b.classList.toggle('on'); b.setAttribute('aria-pressed', NTE.tags.has(tg)); ntWit(); });
  ntWit(); EVV.ntHi = NTE.id; evDraw();
  box.scrollIntoView({ block: 'nearest' }); setTimeout(() => $('nttext').focus({ preventScroll: true }), 30);
}
function ntClock() {                                  // echte Uhrzeit zur eingestellten Stelle
  const g = EVV.g, off = parseFloat($('ntoff').value) || 0, el2 = $('ntclock');
  if (!g || !g.t0) { el2.textContent = ''; return; }
  const d = new Date(g.t0 + off * 1000);
  el2.textContent = '🕒 ' + d.toLocaleTimeString(lang === 'en' ? 'en-GB' : 'de-DE', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}
function ntWit() { $('ntwitl').hidden = !NTE || !NTE.tags.has('zeuge'); }
function ntEditorClose() { NTE = null; EVV.ntPrev = null; const b = $('nted'); if (b) b.hidden = true; EVV.ntHi = null; }
async function ntPost(action, body) {
  const r = await (await fetch('note_' + action, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(Object.assign({ k: EVV.k }, body)) })).json();
  if (!r.ok) throw new Error(r.error === 'empty' ? t('nt_empty') : r.error === 'limit' ? t('nt_limit') : (r.error || 'error'));
  EVV.notes = r.notes; renderNotes(); evDraw(); EVSIG = ''; loadEvents();
  return r;
}
async function ntSave() {
  if (!NTE) return;
  const off = clamp(parseFloat($('ntoff').value) || 0, 0, 3600);
  const body = { off, text: $('nttext').value, tags: [...NTE.tags], witness: $('ntwit').value };
  try { await ntPost(NTE.id ? 'edit' : 'add', NTE.id ? Object.assign(body, { id: NTE.id }) : body); ntEditorClose(); evDraw(); }
  catch (e) { alert(e.message); }
}
let NT_UNDO = null;
async function ntDelete(n) {
  try { await ntPost('del', { id: n.id }); } catch (e) { alert(e.message); return; }
  clearTimeout(NT_UNDO && NT_UNDO.timer);
  NT_UNDO = { n, timer: setTimeout(() => { NT_UNDO = null; renderNotes(); }, 5000) }; renderNotes();
}
async function ntUndo() {
  if (!NT_UNDO) return; const n = NT_UNDO.n; clearTimeout(NT_UNDO.timer); NT_UNDO = null;
  try { await ntPost('add', { off: n.off, text: n.text, tags: n.tags, witness: n.witness }); } catch (e) { alert(e.message); }
}
function ntSeek(off) {                                 // Ablauf 1 s vor der Notiz beginnen (Zusammenhang sehen)
  if (!EVV.a) return;
  EVV.a.currentTime = Math.max(0, off - 1); EVV.a.play(); evDraw();
}
function renderNotes() {
  const box = $('ntlist'); if (!box) return;
  const ns = EVV.notes || [];
  $('nthead').textContent = t('nt_title', { n: ns.length });
  box.innerHTML = (ns.length ? ns.map((n, i) => `<div class="ntrow${EVV.ntHi === n.id ? ' hi' : ''}" data-id="${esc(n.id)}" tabindex="0">
      <span class="ntnum" style="background:${noteCol(n)}">${i + 1}</span>
      <span class="ntoff" data-clk="${n.clock ? ' · ' + esc(n.clock) + (n.approx ? '*' : '') + (n.rz ? ' 🌙' : '') : ''}">${fmtOff(n.off)}</span><span class="ntclk">${esc(n.clock || '')}${n.approx ? '*' : ''}${n.rz ? ' <span class="ntrz" title="' + esc(t('nt_rz_tip')) + '">🌙</span>' : ''}</span>
      <span class="nttx">${(n.tags || []).map(ntTag).join('')}${n.text ? `<span class="ntt">${esc(n.text)}</span>` : ''}${n.witness ? `<span class="ntw">👤 ${esc(n.witness)}</span>` : ''}</span>
      <span class="ntact"><button type="button" class="nted1" title="${esc(t('nt_edit'))}" aria-label="${esc(t('nt_edit'))}">✎</button><button type="button" class="ntdel1" title="${esc(t('nt_del'))}" aria-label="${esc(t('nt_del'))}">🗑</button></span></div>`).join('')
    : `<div class="ntnone">${esc(t('nt_none'))}</div>`) +
    (NT_UNDO ? `<div class="ntundo">${esc(t('nt_deleted'))} <button type="button" id="ntundo" class="chip">${esc(t('nt_undo'))}</button></div>` : '');
  box.querySelectorAll('.ntrow').forEach(row => {
    const n = ns.find(x => x.id === row.dataset.id);
    row.onclick = e => { if (e.target.closest('button')) return; ntSeek(n.off); };
    row.onkeydown = e => { if (e.key === 'Enter') ntSeek(n.off); };
    row.querySelector('.nted1').onclick = () => ntEditorOpen(n.off, n);
    row.querySelector('.ntdel1').onclick = () => ntDelete(n);
  });
  const u = $('ntundo'); if (u) u.onclick = ntUndo;
  ntSyncBtn();
}
function ntBind() {
  $('evnote').onclick = () => ntEditorOpen(ntNow());
  $('ntsave').onclick = ntSave; $('ntcancel').onclick = () => { ntEditorClose(); evDraw(); };
  const nudge = dv => { const v = Math.max(0, (parseFloat($('ntoff').value) || 0) + dv); $('ntoff').value = v.toFixed(1); if (NTE) { NTE.off = v; EVV.ntPrev = v; } ntClock(); evDraw(); };
  $('ntminus').onclick = () => nudge(-0.1); $('ntplus').onclick = () => nudge(0.1);
  $('ntoff').oninput = () => { if (NTE) EVV.ntPrev = parseFloat($('ntoff').value) || 0; ntClock(); evDraw(); };
  $('nttext').onkeydown = e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); ntSave(); } if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); ntEditorClose(); evDraw(); } };
  $('evdlg').addEventListener('keydown', e => {          // Taste N: Notiz an der Abspiel-Linie
    if ((e.key === 'n' || e.key === 'N') && !e.ctrlKey && !e.metaKey && !e.altKey && !e.target.closest('input,textarea,select')) { e.preventDefault(); ntEditorOpen(ntNow()); }
  });
  // langes Druecken (Handy) bzw. Rechtsklick auf die Grafik: Notiz an dieser Stelle
  for (const id of ['evcv', 'evsp']) {
    const cv = $(id); let lp = null;
    const offAt = x => { const gg = EVV.geo; return gg ? Math.round(clamp((x - gg.L) / gg.pw, 0, 1) * gg.total / 100) / 10 : 0; };
    cv.addEventListener('pointerdown', e => {
      const r = cv.getBoundingClientRect(), x = e.clientX - r.left, y0 = e.clientY;
      clearTimeout(lp && lp.t); lp = { x: e.clientX, y: y0, t: setTimeout(() => { EVV.lpDone = true; if (navigator.vibrate) navigator.vibrate(20); ntEditorOpen(offAt(x)); }, 550) };
    });
    cv.addEventListener('pointermove', e => { if (lp && (Math.abs(e.clientX - lp.x) > 8 || Math.abs(e.clientY - lp.y) > 8)) { clearTimeout(lp.t); lp = null; } });
    for (const ev of ['pointerup', 'pointercancel', 'pointerleave']) cv.addEventListener(ev, () => { if (lp) { clearTimeout(lp.t); lp = null; } });
    cv.addEventListener('contextmenu', e => { e.preventDefault(); if (lp) { clearTimeout(lp.t); lp = null; } const r = cv.getBoundingClientRect(); ntEditorOpen(offAt(e.clientX - r.left)); });
  }
  setInterval(() => { if ($('evdlg').open && !NTE) ntSyncBtn(); }, 250);
}
function closeRowMenu() { $('rowmenu').style.display = 'none'; document.querySelectorAll('#events .menu').forEach(r => r.classList.remove('menu')); }
document.addEventListener('click', e => { if (!e.target.closest('#rowmenu')) closeRowMenu(); });
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeRowMenu(); });
document.addEventListener('focusin', e => { if ($('rowmenu').style.display === 'block' && !e.target.closest('#rowmenu')) closeRowMenu(); });
let MENU_AT = 0;
window.addEventListener('scroll', () => { if (Date.now() - MENU_AT > 400) closeRowMenu(); }, true);   // nicht direkt nach dem Oeffnen (Fokus kann kurz scrollen)
/* ================= Quellen (Server-Mikrofon, Handys, Streams) ================= */
function srcState(s) {
  if (!s.enabled) return ['off', t('src_off')];
  if (s.pro_lock) return ['off', '🔒 ' + t('pro_src_lock')];
  if (s.error && !s.online) return ['err', s.error];
  if (!s.online) return ['wait', s.type === 'phone' ? t('phone_wait') : t('src_wait')];
  if (s.silent) return ['wait', t('src_silent')];
  if (s.active) return ['ev', t('event')];
  return ['ok', t('src_ok')];
}
/* Live-Bild: nur wenn das gewaehlte Geraet Video sendet und das Live-Bild eingeschaltet ist */
const VID_SIZES = [240, 420, 680];
let VID = { src: null, timer: 0, rot: 0, size: (() => { try { return Math.min(2, +localStorage.getItem('laerm_vidsize') || 1); } catch (e) { return 1; } })() };
function vidLayout() {
  const img = $('vidimg'), fr = $('vidframe'), box = $('vidlive');
  const nw = img.naturalWidth, nh = img.naturalHeight; if (!nw || !nh) return;
  const side = VID.rot % 180 !== 0, ar = side ? nh / nw : nw / nh;      // Seitenverhaeltnis nach dem Drehen
  const full = !!document.fullscreenElement;
  const maxW = full ? innerWidth : box.clientWidth, maxH = full ? innerHeight : VID_SIZES[VID.size];
  let dw = Math.min(maxW, maxH * ar), dh = dw / ar;
  fr.style.width = dw + 'px'; fr.style.height = dh + 'px';
  img.style.width = (side ? dh : dw) + 'px'; img.style.height = (side ? dw : dh) + 'px';
  img.style.transform = `translate(-50%,-50%) rotate(${VID.rot}deg)`;
  $('vidsz').textContent = ['S', 'M', 'L'][VID.size];
}
function vidSize() { VID.size = (VID.size + 1) % 3; try { localStorage.setItem('laerm_vidsize', VID.size); } catch (e) { } vidLayout(); }
async function vidRotate() {
  const s = srcById(selSrc); if (!s) return;
  const rot = ((s.video_rot || 0) + 90) % 360; s.video_rot = rot; VID.rot = rot; vidLayout();
  try { await srcPost({ action: 'update', id: s.id, video_rot: rot }); } catch (e) { alert(t('saveerr') + ' ' + e.message); }
}
function vidFull() { const f = $('vidframe'); if (document.fullscreenElement) document.exitFullscreen(); else if (f.requestFullscreen) f.requestFullscreen().catch(() => { }); }
function syncVideo() {
  const s = srcById(selSrc), box = $('vidlive'), on = !!(s && s.video_show);
  box.hidden = !on;
  if (on) {
    $('vidcap').textContent = '🎥 ' + s.name + ' · ' + t('vid_live') + (s.video_fps ? ' · ' + s.video_fps + ' ' + t('vid_fps') : '') + ' · ' + (s.video_rec ? '⏺ ' + t('vid_rec_on') : t('vid_rec_off'));
    if (VID.rot !== (s.video_rot || 0)) { VID.rot = s.video_rot || 0; vidLayout(); }
  }
  if (on && !VID.timer) {
    const img = $('vidimg');
    const next = () => { VID.timer = 0; const cur = srcById(selSrc); if (!cur || !cur.video_show || document.hidden) { if (cur && cur.video_show) VID.timer = setTimeout(next, 1000); return; } img.src = 'video_live?src=' + encodeURIComponent(selSrc) + '&t=' + Date.now(); };
    img.onload = () => { vidLayout(); VID.timer = setTimeout(next, VID_SIZES[VID.size] > 300 ? 250 : 500); };
    img.onerror = () => { VID.timer = setTimeout(next, 2000); };
    VID.timer = -1; next();
  }
  if (!on && VID.timer) { clearTimeout(VID.timer); VID.timer = 0; $('vidimg').removeAttribute('src'); }
}
async function loadSources() {
  try {
    const j = await (await fetch('sources', { cache: 'no-store' })).json();
    SOURCES = j.sources || []; FORMER = (j.former || []).map(x => ({ id: x.id, name: x.name, former: true }));
    PHONE = { port: j.phone_port, ip: j.lan_ip, tls: j.tls, tls_error: j.tls_error, ffmpeg: j.ffmpeg };
    if (!SOURCES.some(s => s.id === selSrc)) selectSource('main');
    renderSrcBar(); evFollow(); syncVideo(); if ($('fnpsrc')) fnpSrc();
    if ($('dlg').open) refreshSourceRows();
  } catch (e) { }
}
function renderSrcBar() {
  const bar = $('srcbar');
  const html = SOURCES.map(s => {
    const [cls, tip] = srcState(s);
    const M = s.motion || {}, mo = (M.vib && M.vib.active ? '<b class="motact" title="' + esc(t('mot_vib')) + '">🫨</b>' : '') + (M.cam && M.cam.active ? '<b class="motact" title="' + esc(t('mot_cam')) + '">🏃</b>' : '');
    return `<button class="chip${s.id === selSrc ? ' sel' : ''}" data-id="${esc(s.id)}" title="${esc(tip)}"><i class="dot ${cls}"></i><span class="cn">${esc(s.name)}</span>${mo}<em>${s.count_today || 0}</em></button>`;
  }).join('');
  if (bar.dataset.h !== html) {
    bar.dataset.h = html; bar.innerHTML = html;
    bar.querySelectorAll('.chip').forEach(b => b.onclick = () => {      // von Hand gewaehlt: Rundlauf steht, Wechsel gleitet wie im Rundlauf
      TILE.manual = true; TILE.key = '';
      if (b.dataset.id === selSrc) { tileBar(); evFollow(); return; }
      if (liveDevs().length > 1) tileGo(b.dataset.id, true); else selectSource(b.dataset.id);
    });
  }
}
/* Zwischenspeicher je Geraet: beim Wechsel sofort die letzten Daten zeigen (kein leeres Bild), danach nur Neues nachladen */
const DCACHE = {};
const DC_MAX_AGE = 100000;
function cacheCur() { if (recs.length && lastSeq >= 0) DCACHE[selSrc] = { recs, lastSeq, firstAvail, st, bands, boot, t: Date.now() }; }
async function prefetchDev(id) {
  const c = DCACHE[id], fresh = c && Date.now() - c.t < DC_MAX_AGE && c.boot === boot;
  const r = await fetch((fresh ? 'data?since=' + c.lastSeq : 'data?limit=1200') + '&src=' + encodeURIComponent(id), { cache: 'no-store' });
  const j = await r.json(); if (j.src !== id || id === selSrc) return;
  let R = fresh ? c.recs.slice() : [], ls = fresh ? c.lastSeq : -1;
  for (const x of j.r.map(decode)) if (x.s > ls) { R.push(x); ls = x.s; }
  if (R.length > MAXR) R.splice(0, R.length - MAXR);
  DCACHE[id] = { recs: R, lastSeq: R.length ? ls : (j.last || -1), firstAvail: j.first, st: j.st, bands: (j.st && j.st.bands && j.st.bands.length) ? j.st.bands : bands, boot: j.boot, t: Date.now() };
}
function selectSource(id, auto) {
  if (id === selSrc) return;
  if (!auto) { TILE.manual = true; TILE.at = Date.now(); }   // von Hand gewaehlt: Rundlauf steht, bis neu geladen oder ▶ gedrueckt wird
  cacheCur();
  const c = DCACHE[id];
  selSrc = id;
  if (c && Date.now() - c.t < DC_MAX_AGE && c.boot === boot && c.recs.length) {
    recs = c.recs; lastSeq = c.lastSeq; firstAvail = c.firstAvail; st = c.st; if (c.bands && c.bands.length) bands = c.bands; recolorAll();
  } else { resetData(); st = null; }
  lastCount = -1; yv.auto = true; wg.auto = true; syncAutoBtn(); setLive(true); if (st) updateStatus();
  if (histOn()) dtLoad(LDT, true);                 // zurückgespult: Tagesverlauf des neuen Geräts
  renderSrcBar(); markDirty(); evFollow();
}
/* Ereignisliste und Statistik: folgen standardmaessig dem Geraet der Live-Ansicht (auch im Rundlauf) */
let EVSRC = (() => { try { return localStorage.getItem('laerm_evsrc') || 'live'; } catch (e) { return 'live'; } })();
function evSrc() { return NV.src || 'all'; }        // Ereignisliste: Gerät aus dem Filter des Reiters Protokolle
let EVLAST = null;
function evFollow() {                                  // nur neu laden, wenn sich die Auswahl der Liste wirklich aendert
  syncEvFilter();
  const want = evSrc(); if (want === EVLAST) return;
  EVLAST = want; EVSIG = ''; loadEvents();
}
function syncEvFilter() {
  const sel = $('evsrc'), cur = EVSRC; if (!sel) return;   // Gerät wählt jetzt der Filter im Reiter Protokolle
  const ls = srcById(selSrc);
  const opts = [['live', rotActive() ? t('ev_auto_all') : t('ev_follow', { n: ls ? ls.name : '' })], ['all', t('all_sources')]].concat(SOURCES.map(s => [s.id, s.name]));
  const key = JSON.stringify(opts);
  if (sel.dataset.k === key) return;
  sel.dataset.k = key; sel.innerHTML = opts.map(([v, l]) => `<option value="${esc(v)}">${esc(l)}</option>`).join('');
  sel.value = opts.some(o => o[0] === cur) ? cur : 'live'; EVSRC = sel.value;
  sel.parentElement.style.display = SOURCES.length > 1 ? '' : 'none';
}
async function srcPost(body) {
  const r = await (await fetch('sources', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })).json();
  if (!r.ok) throw new Error(r.error || 'error');
  SOURCES = r.sources; renderSrcBar(); syncEvFilter();
  return r;
}
/* ================= Pause durch Home Assistant (Regeln) ================= */
const HAR = { rules: [], info: {}, ents: null, timer: 0 };
function haDefaults(ent) {
  const dom = (ent || '').split('.')[0];
  if (dom === 'media_player') return { states: 'on, playing', after_min: 1, max_h: 8 };
  if (dom === 'sensor') return { states: '>1', after_min: 30, max_h: 2 };
  return { states: 'on', after_min: 1, max_h: 8 };
}
function haBox() {
  const fs = el('fieldset', { id: 'habox', className: 'ff' }); fs.dataset.sec = 's_ha';
  const lg = el('legend', { textContent: t('s_ha') }); const ti = tipIcon('t_ha'); if (ti) lg.appendChild(ti); fs.appendChild(lg);
  fs.appendChild(el('small', { className: 'schedhelp', textContent: t('h_ha') }));
  fs.appendChild(el('div', { id: 'hastat', className: 'hastat' }));
  fs.appendChild(el('div', { id: 'halist', className: 'halist' }));
  const add = el('button', { type: 'button', textContent: '+ ' + t('ha_add') });
  add.onclick = () => { HAR.rules.push(Object.assign({ id: '', entity: '', src: 'all', enabled: true, label: '' }, haDefaults(''))); haRender(true); };
  fs.appendChild(add);
  fs.appendChild(el('datalist', { id: 'haents' }));
  haLoad(); haLoadEnts();
  clearInterval(HAR.timer); HAR.timer = setInterval(() => { if (!$('dlg').open || !$('habox')) { clearInterval(HAR.timer); return; } haLoad(true); }, 5000);
  return fs;
}
async function haLoad(onlyState) {
  try { const r = await (await fetch('ha_rules', { cache: 'no-store' })).json(); HAR.info = r; if (!onlyState || !document.activeElement || !document.activeElement.closest('#halist')) { HAR.rules = r.rules; haRender(); } else haStates(r.rules); } catch (e) { }
}
async function haLoadEnts() {
  try { const r = await (await fetch('ha_entities', { cache: 'no-store' })).json(); HAR.ents = r.entities || []; const dl = $('haents'); if (dl) dl.innerHTML = HAR.ents.map(e => `<option value="${esc(e.id)}">${esc(e.name)} (${esc(e.state)})</option>`).join(''); } catch (e) { }
}
function haStateTxt(r) {
  if (!r.entity) return '';
  if (r.err) return '⚠ ' + r.err;
  if (r.now_state == null) return t('ha_wait');
  if (r.mode === 'note') return (r.label ? r.label + ' · ' : r.name && r.name !== r.entity ? r.name + ' · ' : '') + t('ha_now', { s: r.now_state }) + ' · 📝 ' + t(r.active ? 'ha_noting' : 'ha_noting_off');
  return (r.label ? r.label + ' · ' : r.name && r.name !== r.entity ? r.name + ' · ' : '') + t('ha_now', { s: r.now_state }) + ' · ' + (r.hold ? (r.active ? '⏸ ' + t('ha_holding') : '⏸ ' + t('ha_after', { u: r.until ? new Date(r.until).toLocaleTimeString(lang === 'en' ? 'en-GB' : 'de-DE', { hour: '2-digit', minute: '2-digit' }) : '' })) : (r.capped ? '⚠ ' + t('ha_capped') : '▶ ' + t('ha_rec')));
}
function haStates(rows) { rows.forEach(r => { const e = document.querySelector(`#halist .harow[data-id="${r.id}"] .hanow`); if (e) { e.textContent = haStateTxt(r); e.classList.toggle('hold', !!r.hold); } }); }
function haRender(focusLast) {
  const box = $('halist'), st = $('hastat'); if (!box) return;
  const i = HAR.info || {};
  st.textContent = i.available === false ? '⚠ ' + t('ha_noapi') : i.ok === false && i.error ? '⚠ ' + t('ha_err', { e: i.error }) : '';
  box.innerHTML = '';
  if (!HAR.rules.length) box.appendChild(el('div', { className: 'ntnone', textContent: t('ha_none') }));
  HAR.rules.forEach((r, idx) => {
    const row = el('div', { className: 'harow' }); row.dataset.id = r.id || '';
    const on = el('input', { type: 'checkbox', checked: r.enabled !== false, title: t('ha_enabled') });
    const ent = el('input', { type: 'text', value: r.entity || '', placeholder: 'media_player.fernseher', className: 'haent' }); ent.setAttribute('list', 'haents');
    const src = el('select', { className: 'hasrc', title: t('ha_src') });
    option(src, 'all', t('all_sources')); SOURCES.forEach(x => option(src, x.id, x.name)); src.value = r.src || 'all';
    const sts = el('input', { type: 'text', value: r.states || '', placeholder: 'on, playing  ·  !off  ·  >1', className: 'hasts', title: t('ha_states_tip') });
    const aft = el('input', { type: 'number', min: 0, max: 240, step: 1, value: r.after_min ?? 1, className: 'n', title: t('ha_after_tip') });
    const mx = el('input', { type: 'number', min: 0, max: 48, step: 1, value: r.max_h ?? 8, className: 'n', title: t('ha_max_tip') });
    const del = el('button', { type: 'button', className: 'hadel', textContent: '✕', title: t('nt_del') });
    const now = el('small', { className: 'hanow' + (r.hold ? ' hold' : ''), textContent: haStateTxt(r) });
    const nmi = el('input', { type: 'text', value: r.label || '', maxLength: 60, placeholder: r.name && r.name !== r.entity ? r.name : t('ha_name_ph'), className: 'haname', title: t('ha_name_tip') });   // Name, unter dem die Regel festgehalten wird
    const md = el('select', { className: 'hamode', title: t('ha_model') });   // pausieren oder nur festhalten (z. B. Fernseher an/aus)
    option(md, 'pause', t('ha_mode_pause')); option(md, 'note', t('ha_mode_note')); option(md, 'event', t('ha_mode_event')); md.value = ['pause', 'event'].includes(r.mode) ? r.mode : 'note';          // neue Regeln: nur vermerken (Standard)
    const l1 = el('div', { className: 'harow1' }); l1.append(on, ent, src, del);
    const l2 = el('div', { className: 'harow2' });
    const lab = (txt, inp, unit) => { const L = el('label'); L.append(document.createTextNode(txt + ' '), inp); if (unit) L.append(' ' + unit); return L; };
    const note = md.value !== 'pause';
    const la = lab(t('ha_afterl'), aft, 'min'), lm = lab(t('ha_maxl'), mx, 'h'); la.hidden = lm.hidden = note;
    const nmNow = r.label || r.name || r.entity || '';
    const colI = el('input', { type: 'color', className: 'hacol', value: r.color || sensCol([0, 0, nmNow]), title: t('ha_col_tip') });
    const colR = el('button', { type: 'button', className: 'chip hacolr', textContent: '↺', title: t('ha_col_auto'), hidden: !r.color });
    const lc = lab(t('ha_col'), colI); lc.appendChild(colR); lc.hidden = md.value !== 'event';   // Farbe des Fähnchens im Verlauf (nur „als Ereignis“)
    colI.addEventListener('change', () => { HAR.rules[idx].color = colI.value; colR.hidden = false; haSave(); });
    colR.onclick = () => { HAR.rules[idx].color = ''; colI.value = sensCol([0, 0, nmNow]); colR.hidden = true; haSave(); };
    l2.append(lab(t('ha_name'), nmi), lab(t('ha_model'), md), lab(t(note ? 'ha_whenn' : 'ha_when'), sts), la, lm, lc);
    row.append(l1, l2, now); box.appendChild(row);
    const upd = () => { Object.assign(HAR.rules[idx], { enabled: on.checked, entity: ent.value.trim(), label: nmi.value.trim(), src: src.value, states: sts.value, after_min: +aft.value, max_h: +mx.value, mode: md.value }); haSave(); };
    md.addEventListener('change', () => { upd(); haRender(); });
    ent.addEventListener('change', () => { const d = haDefaults(ent.value.trim()); if (!sts.value || sts.value === haDefaults('').states) { sts.value = d.states; aft.value = d.after_min; mx.value = d.max_h; } upd(); });
    for (const x of [on, src, sts, aft, mx, nmi]) x.addEventListener('change', upd);
    del.onclick = () => { HAR.rules.splice(idx, 1); haSave(); haRender(); };
    if (focusLast && idx === HAR.rules.length - 1) setTimeout(() => ent.focus(), 30);
  });
}
async function haSave() {
  try {
    const r = await (await fetch('ha_rules', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ rules: HAR.rules.filter(x => x.entity) }) })).json();
    if (r.ok) { const keep = HAR.rules.filter(x => !x.entity); HAR.info = r; HAR.rules = r.rules.concat(keep); haStates(r.rules); document.querySelectorAll('#halist .harow').forEach((row, i) => { if (HAR.rules[i]) row.dataset.id = HAR.rules[i].id || ''; }); flash($('habox')); }
  } catch (e) { alert(t('saveerr') + ' ' + e.message); }
}
/* Einstellungs-Bereiche einklappbar; Zustand pro Browser gemerkt */
const SEC_OPEN_DEFAULT = { s_pro: true, s_prof: true, srcbox1: true, srcbox: true, s_time: true, s_thr: true, s_ha: true, s_backup: true, s_diag: true };
function secState() { try { return JSON.parse(localStorage.getItem('laerm_secs') || '{}'); } catch (e) { return {}; } }
function makeCollapsible() {
  const st = secState();
  $('sbody').querySelectorAll(':scope > fieldset').forEach(fs => {
    const key = fs.dataset.sec || fs.id; if (!key || key === 'devbox' || fs.dataset.coll) return;
    const lg = fs.querySelector(':scope > legend'); if (!lg) return;
    fs.dataset.coll = '1'; fs.classList.add('coll');
    const open = key in st ? st[key] : !!SEC_OPEN_DEFAULT[key];
    fs.classList.toggle('shut', !open);
    lg.tabIndex = 0; lg.setAttribute('role', 'button'); lg.setAttribute('aria-expanded', String(open));
    const flip = () => { const o = fs.classList.toggle('shut') === false; lg.setAttribute('aria-expanded', String(o)); const s2 = secState(); s2[key] = o; try { localStorage.setItem('laerm_secs', JSON.stringify(s2)); } catch (e) { } };
    lg.onclick = e => { if (e.target.closest('.tip,.tipi,button,input')) return; flip(); };
    lg.onkeydown = e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); flip(); } };
    const hbk = HB_SEC[key]; if (hbk && !lg.querySelector('.hbleg')) { const a = el('a', { href: '#', className: 'hbleg', textContent: '📖', title: t('hb_more') }); a.dataset.hb = hbk; lg.appendChild(a); }   // Kapitel im Handbuch
  });
}
function openSec(key) { if (SEC_TAB[key]) setSTab(SEC_TAB[key]); const fs = $('sbody').querySelector(`fieldset[data-sec="${key}"], fieldset#${key}`); if (fs && fs.classList.contains('shut')) fs.querySelector(':scope > legend').click(); return fs; }
/* Einstellungen in Reitern; Inhalte der Bereiche bleiben unveraendert. Bereiche ohne Reiter (Auswahl des Geraets) stehen in jedem Reiter. */
const STABS = [['dev', 'st_dev'], ['det', 'st_det'], ['time', 'st_time'], ['save', 'st_save'], ['gen', 'st_gen']];
const SEC_TAB = { s_pro: 'gen', s_wav: 'save', s_reset: 'gen', rsbox: 'gen', s_prof: 'det', pfbox: 'det', srcbox1: 'dev', diagset: 'gen', s_diag: 'gen', srcbox: 'dev', calbox: 'dev', s_cal: 'dev', s_audio: 'dev', s_thr: 'det', s_time: 'time', s_sched: 'time', schedbox: 'time', s_ha: 'time', habox: 'time', s_notes: 'time', s_rec: 'save', s_video: 'save', s_misc: 'gen', s_backup: 'gen', bkbox: 'gen' };
let STAB = 'dev'; try { STAB = localStorage.getItem('laerm_stab') || 'dev'; } catch (e) { }
if (!STABS.some(x => x[0] === STAB)) STAB = 'dev';
function applySTab() {
  $('sbody').querySelectorAll(':scope > fieldset').forEach(fs => { const k = SEC_TAB[fs.dataset.sec] || SEC_TAB[fs.id]; fs.classList.toggle('tabhide', !!k && k !== STAB); });
}
function setSTab(k, keep) {
  STAB = k;
  $('stabs').querySelectorAll('.stab').forEach(x => { const on = x.dataset.tab === k; x.classList.toggle('cur', on); x.setAttribute('aria-selected', String(on)); if (on) { const b = $('stabs'); if (x.offsetLeft < b.scrollLeft || x.offsetLeft + x.offsetWidth > b.scrollLeft + b.clientWidth) b.scrollLeft = x.offsetLeft - 8; } });
  applySTab(); if (!keep) $('sbody').scrollTop = 0; hideTip();
  try { localStorage.setItem('laerm_stab', k); } catch (e) { }
}
function initSTabs() {
  const b = $('stabs'); b.innerHTML = '';
  for (const [k, l] of STABS) { const x = el('button', { type: 'button', className: 'stab', textContent: t(l) }); x.dataset.tab = k; x.setAttribute('role', 'tab'); x.onclick = () => setSTab(k); b.appendChild(x); }
  setSTab(STAB, true); syncSTabs();
  if (!initSTabs.obs) { initSTabs.obs = new MutationObserver(applySTab); initSTabs.obs.observe($('sbody'), { childList: true }); }
}
/* Diagnosemodus: blendet unten die Diagnose (Mikrofon, Soundkarte) ein; gilt pro Browser */
function diagOn() { try { return localStorage.getItem('laerm_diag') === '1'; } catch (e) { return false; } }
function diagApply() { const on = diagOn(); $('diagbox').hidden = !on; if (on) { $('diagbox').open = true; diagT = 0; loadDiag(); } }
function diagBox() {
  const fs = el('fieldset', { id: 'diagset' }); fs.dataset.sec = 's_diag';
  const lg = el('legend', { textContent: t('s_diag') }); const ti = tipIcon('t_diagmode'); if (ti) lg.appendChild(ti); fs.appendChild(lg);
  const l = el('label', { className: 'bkchk' }); const cb = el('input', { type: 'checkbox', id: 'diagmode', checked: diagOn() });
  l.append(cb, el('span', { textContent: t('diag_mode') })); fs.appendChild(l);
  fs.appendChild(el('small', { className: 'bkhelp', textContent: t('h_diagmode') }));
  cb.onchange = () => { try { localStorage.setItem('laerm_diag', cb.checked ? '1' : '0'); } catch (e) { } diagApply(); };
  return fs;
}
/* Komplette Sicherung: herunterladen und einspielen (zusammenfuehren) */
/* Zurücksetzen: gewählte Teile löschen; vorher Sicherung anbieten, ohne Sicherung doppelte Abfrage */
function rsBox() {
  const fs = el('fieldset', { id: 'rsbox' }); fs.dataset.sec = 's_reset';
  fs.appendChild(el('legend', { textContent: t('s_reset') }));
  fs.appendChild(el('small', { className: 'bkhelp', textContent: t('h_reset') }));
  const box = el('div', { className: 'rsparts' });
  for (const k of ['data', 'notes', 'profiles', 'settings']) { const l = el('label', { className: 'chip' }), c = el('input', { type: 'checkbox', checked: true }); c.dataset.p = k; l.append(c, document.createTextNode(' ' + t('rs_' + k))); box.appendChild(l); }
  fs.appendChild(box);
  const r = el('div', { className: 'bkrow' }), go = el('button', { type: 'button', className: 'danger', textContent: t('rs_go') });
  const step = el('div', { className: 'rsstep', hidden: true }), msg = el('div', { className: 'calst' });
  r.appendChild(go); fs.append(r, step, msg);
  const parts = () => [...box.querySelectorAll('input:checked')].map(c => c.dataset.p);
  const names = () => parts().map(p => t('rs_' + p)).join(', ');
  const run = async () => {
    msg.textContent = t('rs_running');
    try { const j = await (await fetch('reset', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ parts: parts(), confirm: 'RESET' }) })).json();
      if (!j.ok) throw new Error(j.error); formDirty = false; msg.textContent = '✓ ' + t('rs_done'); setTimeout(() => location.reload(), 1500);
    } catch (e) { msg.textContent = t('saveerr') + ' ' + e.message; }
  };
  go.onclick = () => {
    if (!parts().length) { msg.textContent = t('rs_none'); return; }
    step.hidden = false; msg.textContent = '';
    step.innerHTML = `<b>${esc(t('rs_backup_q'))}</b><div class="bkrow"><a class="chip pri" id="rsdl" href="backup.zip" download>⬇ ${esc(t('bk_down'))}</a><button type="button" class="chip" id="rsnodl">${esc(t('rs_nobackup'))}</button><button type="button" class="chip" id="rsx">${esc(t('cancel'))}</button></div><div id="rsok" class="bkrow" hidden><button type="button" class="danger" id="rsnow">${esc(t('rs_now'))}</button></div>`;
    $('rsx').onclick = () => { step.hidden = true; };
    $('rsdl').onclick = () => { $('rsok').hidden = false; msg.textContent = t('rs_after_dl'); };
    $('rsnow').onclick = () => { if (confirm(t('rs_q1', { p: names() }))) run(); };
    $('rsnodl').onclick = () => { if (confirm(t('rs_q2', { p: names() }))) run(); };   // ohne Sicherung: eine deutliche Abfrage
  };
  return fs;
}
function bkBox() {
  const fs = el('fieldset', { id: 'bkbox' }); fs.dataset.sec = 's_backup';
  const lg = el('legend', { textContent: t('s_backup') }); const ti = tipIcon('t_backup'); if (ti) lg.appendChild(ti); fs.appendChild(lg);
  fs.appendChild(el('small', { className: 'bkhelp', textContent: t('h_backup') }));
  const r1 = el('div', { className: 'bkrow' });
  const dl = el('a', { className: 'chip', href: 'backup.zip', textContent: '⬇ ' + t('bk_down') }); dl.setAttribute('download', '');
  r1.appendChild(dl); fs.appendChild(r1);
  const r2 = el('div', { className: 'bkrow' });
  const pick = el('label', { className: 'chip pickbtn' }); const fi = el('input', { type: 'file', id: 'bkfile', accept: '.zip,application/zip', hidden: true });
  pick.append('📂 ' + t('bk_pick'), fi);
  const fname = el('span', { className: 'chkname', id: 'bkname' });
  r2.append(pick, fname); fs.appendChild(r2);
  const r3 = el('label', { className: 'bkchk' }); const cb = el('input', { type: 'checkbox', id: 'bkset', checked: true });
  r3.append(cb, el('span', { textContent: t('bk_settings') })); fs.appendChild(r3);
  const r4 = el('div', { className: 'bkrow' });
  const go = el('button', { type: 'button', className: 'pri', id: 'bkgo', textContent: t('bk_restore'), disabled: true });
  const msg = el('span', { id: 'bkmsg', className: 'bkmsg' }); msg.setAttribute('aria-live', 'polite');
  r4.append(go, msg); fs.appendChild(r4);
  fi.onchange = () => { const f = fi.files[0]; fname.textContent = f ? f.name + ' · ' + (f.size / 1048576).toFixed(1) + ' MB' : ''; go.disabled = !f; msg.textContent = ''; };
  const pv = el('div', { id: 'bkpv', className: 'bkpv' }); pv.hidden = true; fs.appendChild(pv);
  const reset = () => { go.disabled = !fi.files[0]; pick.classList.remove('off'); };
  go.onclick = () => {                               // 1. hochladen und ansehen, 2. Geräte wählen, 3. einspielen
    const f = fi.files[0]; if (!f) return;
    go.disabled = true; pick.classList.add('off'); pv.hidden = true;
    // in Teilen zu 8 MB hochladen: Home Assistant lässt über die Seitenleiste nur ~16 MB je Anfrage durch
    const fail = e => { msg.textContent = t('bk_err', { e }); reset(); };
    const id = [...crypto.getRandomValues(new Uint8Array(8))].map(b => b.toString(16).padStart(2, '0')).join(''), CH = 8 * 1048576;
    (async () => {
      let off = 0, r = {};
      while (off < f.size) {
        const part = f.slice(off, Math.min(f.size, off + CH));
        let ok = false;
        for (let tr = 0; tr < 3 && !ok; tr++) {
          try {
            const res = await fetch(`restore_part?id=${id}&off=${off}&total=${f.size}`, { method: 'POST', body: part, headers: { 'Content-Type': 'application/octet-stream' } });
            r = {}; try { r = await res.json(); } catch (e) { r = { ok: false, error: res.status }; }
            if (r.ok || (r.error !== 'incomplete' && r.error !== 'order' && res.status < 500)) ok = true;
            else if (r.error === 'order' && r.have != null) { off = r.have; ok = true; r = { ok: true, retry: true }; }
          } catch (e) { r = { ok: false, error: 'network' }; await new Promise(z => setTimeout(z, 1500)); }
        }
        if (!r.ok) return fail(r.error === 'space' ? t('bk_space', { n: r.need_mb, f: r.free_mb }) : r.error === 'busy' ? t('bk_busy') : (r.error || 'network'));
        if (r.retry) continue;
        off += part.size;
        msg.textContent = t('bk_up', { p: Math.floor(off / f.size * 100) });
      }
      msg.textContent = ''; bkPreview(pv, r, cb, msg, reset);
    })();
  };
  {                                                  // Suchverzeichnis (SQLite): nur abgeleitete Daten, Originale bleiben unberührt
    const r9 = el('div', { className: 'bkrow sidxrow' }), info = el('small', { className: 'mut' }), clr = el('button', { type: 'button', className: 'chip', textContent: '↻ ' + t('sx_clear') });
    const load = async () => { try { const j = await (await fetch('sidx', { cache: 'no-store' })).json();
      info.textContent = j.ok === false && j.err ? t('sx_off') : t('sx_info', { d: j.chain || 0, a: j.agg || 0, s: ((j.size || 0) / 1048576).toFixed(1) }); } catch (e) { } };
    clr.onclick = async () => { if (!confirm(t('sx_clear_q'))) return; try { await fetch('sidx_clear', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' }); } catch (e) { } load(); };
    r9.append(el('span', { textContent: '🗂 ' + t('sx_title') + ' ' }), info, clr); fs.appendChild(r9);
    fs.appendChild(el('small', { className: 'bkhelp', textContent: t('sx_help') })); load();
  }
  return fs;
}
/* Vorschau der Sicherung: welche Geräte, wie es hier aussieht; Auswahl, dann einspielen */
function bkPreview(pv, r, cb, msg, reset) {
  const L = locale(), when = r.created ? new Date(r.created).toLocaleString(L) : '';
  const st = d => d.status === 'unreachable' ? '⚠ ' + t('bk_d_unreach') : d.status === 'phone' ? '📱 ' + t('bk_d_phone') : '✔ ' + t('bk_d_ok');
  const rows = r.devices.map(d => `<label class="bkdev"><input type="checkbox" data-id="${esc(d.id)}" data-off="${d.status === 'unreachable' ? 1 : 0}" checked>
      <b>${esc(d.name)}</b><small>${esc(t(d.exists ? 'bk_d_exists' : 'bk_d_new'))} · ${esc(st(d))}</small></label>`).join('');
  pv.innerHTML = `<div class="bkpvh">${esc(t('bk_pv_head', { v: r.app || '?', d: when, n: r.files || 0 }))}</div>
    <div class="bkpvdev"${cb.checked ? '' : ' hidden'}><small>${esc(t('bk_pv_devs'))}</small>${rows || `<small>–</small>`}
      ${r.keep && r.keep.length ? `<small class="bkkeep">${esc(t('bk_pv_keep', { l: r.keep.map(k => k.name).join(', ') }))}</small>` : ''}
      ${r.mic && !r.mic.found ? `<small class="bkwarn">⚠ ${esc(t('bk_pv_mic', { d: r.mic.device }))}</small>` : ''}</div>
    <div class="bkpvdev"${cb.checked ? ' hidden' : ''}><small>${esc(t('bk_pv_noset'))}</small></div>
    <div class="ntedbtns"><button type="button" class="bkcancel">${esc(t('cancel'))}</button><button type="button" class="pri bkrun">${esc(t('bk_restore_go'))}</button></div>`;
  if (r.pro_needed) {                               // ohne Pro (kostenloser Import schon genutzt): nur ansehen
    const run = pv.querySelector('.bkrun'); const g = el('button', { type: 'button', className: 'pri', textContent: '🔒 ' + t('bk_restore_go') });
    g.onclick = () => proGate('imp'); run.replaceWith(g);
    pv.querySelector('.ntedbtns').before(el('small', { className: 'bkwarn', textContent: '🔒 ' + t('pro_imp_need') }));
  } else if (r.free_import) pv.querySelector('.ntedbtns').before(el('small', { className: 'bkkeep', textContent: 'ℹ ' + t('pro_imp_free') }));
  pv.hidden = false;
  cb.onchange = () => { const b = pv.querySelectorAll('.bkpvdev'); if (b.length) { b[0].hidden = !cb.checked; b[1].hidden = cb.checked; } };
  pv.querySelector('.bkcancel').onclick = async () => { try { await fetch('restore_go', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{"cancel":true}' }); } catch (e) { } pv.hidden = true; reset(); };
  pv.querySelector('.bkrun').onclick = async () => {
    const sel = [...pv.querySelectorAll('.bkdev input')], pick = sel.filter(x => x.checked).map(x => x.dataset.id), off = sel.filter(x => x.checked && x.dataset.off === '1').map(x => x.dataset.id);
    if (!confirm(t('bk_confirm', { n: '' }).replace(/„\s*“\s*/, '') + (cb.checked ? '\n\n' + t('bk_confirm_set') : ''))) return;
    let j = {}; try { j = await (await fetch('restore_go', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ settings: cb.checked, pick, off }) })).json(); } catch (e) { }
    if (j.error === 'pro') { proGate('imp'); return; }
    if (!j.ok) { msg.textContent = t('bk_err', { e: j.error === 'busy' ? t('bk_busy') : (j.error || '') }); return; }
    pv.hidden = true; bkPoll(msg, reset);
  };
}
async function bkPoll(msg, done) {
  let r = {};
  try { r = await (await fetch('backup_status', { cache: 'no-store' })).json(); } catch (e) { }
  if (r.state === 'running') { msg.textContent = t('bk_run', { d: r.done || 0, t: r.total || '…' }); return setTimeout(() => bkPoll(msg, done), 1000); }
  done();
  if (r.state === 'error') { msg.textContent = t('bk_err', { e: r.msg || '' }); return; }
  const s = r.stats || {};
  msg.textContent = t('bk_done', { a: s.new || 0, b: s.same || 0, r: s.rows || 0, l: s.lists || 0 });
  const nm = id => viewName(id), dd = x => x.slice(8, 10) + '.' + x.slice(5, 7) + '.';
  const rep = [];                                    // ausführlicher Bericht, bleibt stehen
  if ((s.days_repaired || []).length) rep.push('✔ ' + t('bk_r_repaired', { l: s.days_repaired.map(x => dd(x[0]) + ' ' + nm(x[1])).join(', ') }));
  if ((s.days_merged || []).length) rep.push('✔ ' + t('bk_r_merged', { l: s.days_merged.map(x => dd(x[0]) + ' ' + nm(x[1]) + ' (+' + x[2] + ' min)').join(', ') }));
  if ((s.days_skipped || []).length) rep.push('⚠ ' + t('bk_r_skipped', { l: s.days_skipped.map(x => dd(x[0]) + ' ' + nm(x[1])).join(', ') }));
  if (s.devices) rep.push('✔ ' + t('bk_r_devs', { n: s.devices.length }) + (s.devices_off && s.devices_off.length ? ' · ' + t('bk_r_off', { n: s.devices_off.length }) : ''));
  if (s.mic_kept) rep.push('⚠ ' + t('bk_r_mic', { d: s.mic_kept }));
  let box = $('bkrep'); if (!box) { box = el('div', { id: 'bkrep', className: 'bkrep' }); msg.parentNode.after(box); }
  box.innerHTML = rep.map(x => `<div>${esc(x)}</div>`).join(''); box.hidden = !rep.length;
  if (r.restart) { msg.textContent += ' ' + t('bk_reload'); setTimeout(() => location.reload(), rep.length ? 8000 : 2500); return; }
  EVSIG = ''; loadEvents(); plFetch();
}
function buildSources() {
  const body = $('sbody');
  const old = $('srcbox'); if (old) old.remove();
  const fs = el('fieldset', { id: 'srcbox' }); if (DEV) fs.dataset.sec = 'srcbox1';   // beim Gerät: nur seine Karte, standardmäßig offen
  fs.appendChild(el('legend', { textContent: t(DEV ? 'st_dev1' : 's_sources') }));
  const note = el('div', { className: 'srcnote' }); fs.appendChild(note);
  if (!PHONE.tls) note.textContent = t('tls_missing', { e: PHONE.tls_error || '' });
  else if (!PHONE.port) note.textContent = t('port_missing');
  const list = el('div', { id: 'srclist' }); fs.appendChild(list);
  for (const s of SOURCES) if (!DEV || s.id === DEV) list.appendChild(sourceRow(s));
  const add = el('div', { className: 'srcadd' }); add.hidden = !!DEV;
  const b1 = el('button', { textContent: '+ ' + t('add_phone'), className: 'pri' });
  const b2 = el('button', { textContent: '+ ' + t('add_url') });
  b1.onclick = async () => { try { const r = await srcPost({ action: 'add', type: 'phone' }); refreshDevBox(); buildSources(); showQR(r.id); } catch (e) { alert(t('saveerr') + ' ' + e.message); } };
  b2.onclick = async () => { try { await srcPost({ action: 'add', type: 'url' }); refreshDevBox(); buildSources(); } catch (e) { alert(t('saveerr') + ' ' + e.message); } };
  add.appendChild(b1); add.appendChild(b2);
  if (SOURCES.length >= 9) { b1.disabled = b2.disabled = true; }
  if (!PRO.ok) { b1.onclick = b2.onclick = () => proGate('dev'); b1.appendChild(proLockTag()); b2.appendChild(proLockTag()); }
  fs.appendChild(add);
  fs.appendChild(el('small', { className: 'srchelp', textContent: t('src_help') }));
  body.insertBefore(fs, body.firstChild);
  const oc = $('calbox'); if (oc) oc.remove(); if (!DEV) fs.after(calBox());
  makeCollapsible();
}
function sourceRow(s) {
  const row = el('div', { className: 'src' }); row.dataset.id = s.id;
  const top = el('div', { className: 'srctop' });
  const dot = el('i', { className: 'dot' });
  const name = el('input', { type: 'text', value: s.name, maxLength: 40, className: 'srcname', title: t('src_name') });
  const kind = el('span', { className: 'srctype', textContent: t('type_' + s.type) });
  const en = el('label', { className: 'srcen' }); const cb = el('input', { type: 'checkbox', checked: !!s.enabled }); en.appendChild(cb); en.appendChild(document.createTextNode(t('src_on')));
  top.append(dot, name, kind, en);
  row.appendChild(top);
  if (s.check) row.appendChild(el('div', { className: 'srccheck', textContent: '⚠ ' + t('src_check') }));   // aus einer Sicherung, war nicht erreichbar
  const sub = el('div', { className: 'srcsub' });
  const gain = el('input', { type: 'number', min: -20, max: 40, step: 0.5, value: s.gain_db || 0, className: 'n', title: t('gain_db') });
  const gl = el('label', { textContent: t('gain_db') + ' ' }); gl.appendChild(gain); sub.appendChild(gl);
  const cs = s.cal_state || {};                   // Stand des Einpegelns
  sub.appendChild(el('small', { className: 'calbadge' + (cs.ok ? ' ok' : cs.changed ? ' warn' : ''), textContent: cs.ok ? t('cal_ok_at', { d: fmtStamp(cs.at) }) : cs.changed ? t('cal_changed') : t('cal_none') }));
  const hum = el('select', { className: 'humsel', title: t('t_hum') });
  option(hum, '0', t('hum_off')); option(hum, '50', t('hum_50')); option(hum, '60', t('hum_60'));
  hum.value = String(s.hum || 0);
  const hl = el('label', { textContent: t('hum') + ' ' }); hl.appendChild(hum); const hti = tipIcon('t_hum'); if (hti) hl.appendChild(hti); sub.appendChild(hl);
  if (s.hum && s.hum_ok === false) sub.appendChild(el('small', { textContent: t('hum_na') }));
  hum.addEventListener('change', () => upd({ hum: hum.value }));
  let url = null, user = null, pass = null;
  if (s.type === 'url') {
    url = el('input', { type: 'url', value: s.url || '', placeholder: 'http://192.168.178.50:8080/audio.wav', className: 'srcurl' });
    sub.appendChild(url);
    if (!PHONE.ffmpeg) sub.appendChild(el('small', { textContent: t('no_ffmpeg') }));
  }
  if (s.type === 'phone') { const q = el('button', { textContent: t('connect_phone') }); q.onclick = () => showQR(s.id); sub.appendChild(q); }
  if (s.type === 'phone') {                       // Handy als Bewegungsmelder (Erschütterung, Bewegung im Kamerabild)
    const mb = el('div', { className: 'srcmot' }), M = s.motion || {};
    mb.appendChild(el('b', { textContent: t('mot_title') }));
    const mk = (key, kind) => { const l = el('label'), c = el('input', { type: 'checkbox', checked: !!(M[kind] && M[kind].on) }); l.append(c, ' ' + t(key)); c.onchange = () => upd({ ['motion_' + kind]: c.checked }); return l; };
    mb.append(mk('mot_vib', 'vib'), mk('mot_cam', 'cam'));
    const sens = el('select', { className: 'motsens' }); option(sens, 'high', t('mot_s_high')); option(sens, 'mid', t('mot_s_mid')); option(sens, 'low', t('mot_s_low'));
    sens.value = s.motion_sens || 'mid'; sens.onchange = () => upd({ motion_sens: sens.value });
    const sl = el('label', { textContent: t('mot_sens') + ' ' }); sl.appendChild(sens); mb.appendChild(sl);
    mb.appendChild(el('small', { textContent: t('h_mot') }));
    sub.appendChild(mb);
  }
  const ds = el('button', { textContent: '⚙ ' + t('dev_settings') }); ds.onclick = () => { if (DEV !== s.id) setDev(s.id, true); setSTab('det'); }; sub.appendChild(ds);
  if (s.id !== 'main') {
    const del = el('button', { textContent: t('delete'), className: 'danger' });
    del.onclick = async () => { if (!confirm(t('confirm_del', { n: s.name }))) return; try { await srcPost({ action: 'delete', id: s.id }); if (DEV === s.id) { formDirty = false; DEV = ''; } refreshDevBox(); buildSources(); } catch (e) { alert(e.message); } };
    sub.appendChild(del);
  }
  row.appendChild(sub);
  row.appendChild(refEditor(s));
  if (s.type === 'url') {                    // Zugangsdaten (z. B. IP Webcam mit Login)
    const lg = el('div', { className: 'srcsub srclogin' });
    user = el('input', { type: 'text', value: s.user || '', placeholder: t('src_user'), autocomplete: 'off', className: 'srcuser', title: t('src_user') });
    pass = el('input', { type: 'password', value: '', placeholder: s.has_password ? t('src_pass_saved') : t('src_pass'), autocomplete: 'new-password', className: 'srcpass', title: t('src_pass') });
    const eye = el('button', { type: 'button', textContent: '👁', className: 'eye', title: t('src_show') });
    eye.onclick = () => { pass.type = pass.type === 'password' ? 'text' : 'password'; };
    const l1 = el('label', { textContent: t('src_login') + ' ' });
    const pw = el('span', { className: 'srcpw' }); pw.append(pass, eye);   // Auge bleibt immer neben dem Passwortfeld
    lg.append(l1, user, pw);
    row.appendChild(lg);
  }
  let vcb = null, vvw = null, vrot = null, vurl = null, vdir = null, vdelay = null;
  if (s.type === 'url') {                    // Video (z. B. IP Webcam): pro Geraet ein/aus, eigener Pfad
    const vb = el('div', { className: 'srcsub srcvideo' });
    vcb = el('input', { type: 'checkbox', checked: !!s.video });
    const vl = el('label', { className: 'srcen' }); vl.append(vcb, document.createTextNode('🎥 ' + t('vid_rec'))); const vti = tipIcon('t_vid_rec'); if (vti) vl.appendChild(vti);
    vvw = el('input', { type: 'checkbox', checked: s.video_view == null ? !!s.video : !!s.video_view });
    const vw = el('label', { className: 'srcen' }); vw.append(vvw, document.createTextNode('📺 ' + t('vid_view'))); const wti = tipIcon('t_vid_view'); if (wti) vw.appendChild(wti);
    vrot = el('select', { title: t('vid_rot') });
    for (const a of [0, 90, 180, 270]) vrot.appendChild(el('option', { value: a, textContent: a + '°', selected: (s.video_rot || 0) === a }));
    const rl = el('label', { textContent: '⟳ ' + t('vid_rot') + ' ' }); rl.appendChild(vrot);
    vurl = el('input', { type: 'url', value: s.video_url || '', placeholder: t('vid_url_ph'), className: 'srcurl', title: t('vid_url') });
    vdir = el('input', { type: 'text', value: s.video_dir || '', placeholder: t('vid_dir_ph'), className: 'srcurl', title: t('vid_dir') });
    vdelay = el('input', { type: 'number', min: -3000, max: 3000, step: 50, value: s.video_delay_ms || 0, className: 'n', title: t('vid_delay') });
    const dl = el('label', { textContent: t('vid_delay') + ' ' }); dl.appendChild(vdelay); dl.append(' ms'); const dti = tipIcon('t_vid_delay'); if (dti) dl.appendChild(dti);
    vb.append(vw, vl, rl, vurl, vdir, dl);
    row.appendChild(vb);
  }
  // Protokolllisten: in welche Listen dieses Geraet eintraegt, je mit Uhrzeit (leer = immer)
  const plb = el('div', { className: 'srcsub srcpl' });
  const plRules = () => [...plb.querySelectorAll('.plrule')].map(r => ({ id: r.querySelector('select').value, from: r.querySelector('.plf').value, to: r.querySelector('.plt').value })).filter(x => x.id);
  const plDraw = rules => {
    plb.innerHTML = '';
    const lab = el('span', { className: 'srcpll', textContent: t('pl_dev') }); const ti = tipIcon('t_pl_dev'); if (ti) lab.appendChild(ti); plb.appendChild(lab);
    if (!PV.lists.length) { plb.appendChild(el('small', { textContent: t('pl_dev_none') })); return; }
    for (const r of rules) {
      const line = el('span', { className: 'plrule' });
      const sel = el('select', { title: t('pl_list') }); for (const l of PV.lists) sel.appendChild(el('option', { value: l.id, textContent: l.name, selected: l.id === r.id }));
      const f = el('input', { type: 'time', value: r.from || '', className: 'plf', title: t('pl_from') }), to = el('input', { type: 'time', value: r.to || '', className: 'plt', title: t('pl_to') });
      const x = el('button', { type: 'button', className: 'hadel', textContent: '✕', title: t('pl_rule_del') }); x.setAttribute('aria-label', t('pl_rule_del'));
      line.append(sel, f, el('span', { textContent: '–' }), to, x); plb.appendChild(line);
      [sel, f, to].forEach(e => e.addEventListener('change', () => upd({ plists: plRules() })));
      x.onclick = () => { line.remove(); upd({ plists: plRules() }); };
    }
    const add = el('button', { type: 'button', className: 'chip', textContent: '＋ ' + t('pl_rule_add') });
    add.onclick = () => { plDraw(plRules().concat({ id: PV.lists[0].id, from: '', to: '' })); upd({ plists: plRules() }); };
    plb.appendChild(add);
  };
  plDraw(s.plists || []); row.appendChild(plb);
  const stat = el('small', { className: 'srcstat' }); row.appendChild(stat);
  const upd = async (patch) => {
    try {
      const r = await srcPost(Object.assign({ action: 'update', id: s.id }, patch)); flash(row);
      const ns = (r.sources || []).find(x => x.id === s.id);
      if (url && ns && 'url' in patch) url.value = ns.url || '';      // vom Server korrigierte Adresse anzeigen
      if (user && ns && 'user' in patch) user.value = ns.user || '';
      if (pass && ns && ('password' in patch || 'user' in patch || 'url' in patch)) {
        if ('password' in patch) pass.value = '';
        pass.placeholder = ns.has_password ? t('src_pass_saved') : t('src_pass');
      }
    } catch (e) { alert(t('saveerr') + ' ' + e.message); }
  };
  name.addEventListener('change', () => upd({ name: name.value }));
  cb.addEventListener('change', () => upd({ enabled: cb.checked }));
  gain.addEventListener('change', () => upd({ gain_db: gain.value }));
  if (url) url.addEventListener('change', () => upd({ url: url.value }));
  if (vcb) { vcb.addEventListener('change', () => upd({ video: vcb.checked })); vvw.addEventListener('change', () => upd({ video_view: vvw.checked })); vrot.addEventListener('change', () => upd({ video_rot: +vrot.value })); vurl.addEventListener('change', () => upd({ video_url: vurl.value })); vdir.addEventListener('change', () => upd({ video_dir: vdir.value })); vdelay.addEventListener('change', () => upd({ video_delay_ms: vdelay.value })); }
  if (user) user.addEventListener('change', () => upd({ user: user.value }));
  if (pass) pass.addEventListener('change', () => { if (pass.value !== '') upd({ password: pass.value }); });
  paintRow(row, s);
  return row;
}
function refEditor(s) {
  const box = el('details', { className: 'refs' });
  const sum = el('summary', { textContent: '📏 ' + t('refs_title') + ((s.refs || []).length ? ' (' + s.refs.length + ')' : '') });
  const ti = tipIcon('t_refs'); if (ti) sum.appendChild(ti);
  box.appendChild(sum);
  const list = el('div', { className: 'reflist' }); box.appendChild(list);
  let refs = JSON.parse(JSON.stringify(s.refs || []));
  const save = async () => {
    try { const r = await srcPost({ action: 'update', id: s.id, refs }); const ns = (r.sources || []).find(x => x.id === s.id); refs = JSON.parse(JSON.stringify((ns && ns.refs) || [])); render(); markDirty(); }
    catch (e) { alert(t('saveerr') + ' ' + e.message); }
  };
  const render = () => {
    list.innerHTML = '';
    sum.firstChild.textContent = '📏 ' + t('refs_title') + (refs.length ? ' (' + refs.length + ')' : '');
    refs.forEach((r, i) => {
      const rw = el('div', { className: 'refrow' });
      const lab = el('input', { type: 'text', value: r.label, placeholder: t('refs_label'), maxLength: 30, className: 'reflab' });
      const db = el('input', { type: 'number', value: r.db, step: 0.5, min: -130, max: 0, className: 'n' });
      const col = el('select', { className: 'refcol' });
      REF_COLORS.forEach((cc, k) => { const o = option(col, cc, '●'); o.style.color = cc; });
      col.value = r.color; col.style.color = r.color;
      const del = el('button', { type: 'button', className: 'danger', textContent: '✕', title: t('delete') });
      lab.onchange = () => { r.label = lab.value; save(); };
      db.onchange = () => { r.db = parseFloat(db.value); save(); };
      col.onchange = () => { r.color = col.value; col.style.color = col.value; save(); };
      del.onclick = () => { refs.splice(i, 1); save(); };
      rw.append(lab, db, el('span', { textContent: 'dB' }), col, del); list.appendChild(rw);
    });
    const add = el('div', { className: 'refadd' });
    const b1 = el('button', { type: 'button', textContent: '+ ' + t('refs_add') });
    const b2 = el('button', { type: 'button', textContent: '+ ' + t('refs_add_now'), title: t('refs_add_now_tip') });
    b1.onclick = () => { if (refs.length >= 8) return; refs.push({ label: '', db: -50, color: REF_COLORS[refs.length % REF_COLORS.length] }); save(); };
    b2.onclick = () => {
      if (refs.length >= 8) return;
      const lv = (srcById(s.id) || {}).level; if (lv == null) { alert(t('refs_nolevel')); return; }
      refs.push({ label: t('refs_now_label'), db: Math.round(lv * 2) / 2, color: REF_COLORS[refs.length % REF_COLORS.length] }); save();
    };
    if (refs.length >= 8) b1.disabled = b2.disabled = true;
    add.append(b1, b2); list.appendChild(add);
  };
  render();
  return box;
}
function paintRow(row, s) {
  const [cls, txt] = srcState(s);
  row.querySelector('.dot').className = 'dot ' + cls;
  const lv = s.online && s.level != null ? ' · ' + t('level') + ' ' + f1(s.level) + ' dBFS' : '';
  row.querySelector('.srcstat').textContent = txt + lv + ' · ' + t('src_counts', { d: s.count_today || 0, n: s.count_total || 0 }) + (s.own ? ' · ' + t('own_tag') : '') + (s.video_on ? ' · 🎥 ' + (s.video_sending ? t('vid_sending', { f: s.video_fps }) : (s.video_error || t('vid_wait'))) : '');
}
function refreshSourceRows() {
  for (const s of SOURCES) { const r = document.querySelector(`#srclist .src[data-id="${CSS.escape(s.id)}"]`); if (r) paintRow(r, s); }
}
function flash(row) { row.classList.add('saved'); setTimeout(() => row.classList.remove('saved'), 900); }
async function showQR(id) {
  try {
    const j = await (await fetch('phonelink?id=' + encodeURIComponent(id), { cache: 'no-store' })).json();
    const host = j.ip || location.hostname;
    const box = $('qrbody');
    if (!j.port) { box.innerHTML = `<p class="qwarn">${esc(t('port_missing'))}</p>`; $('qrdlg').showModal(); return; }
    const link = `https://${host}:${j.port}/m/${j.token}`;
    const qr = qrcode(0, 'M'); qr.addData(link); qr.make();
    box.innerHTML = `<h4>${esc(j.name)}</h4><div class="qr">${qr.createSvgTag({ cellSize: 6, margin: 2, scalable: true })}</div>
      <div class="qlink"><input readonly value="${esc(link)}"><button id="qcopy">${esc(t('copy'))}</button></div>
      ${/\.local$/.test(host) ? `<p class="qwarn">${esc(t('mdns_hint'))}</p>` : ''}
      <ol class="qsteps">${t('qr_steps').split('|').map(s => `<li>${esc(s)}</li>`).join('')}</ol>
      <p class="qsmall">${esc(t('qr_secret'))} <button id="qrot">${esc(t('new_link'))}</button></p>`;
    $('qcopy').onclick = () => { const i = box.querySelector('input'); i.select(); try { navigator.clipboard.writeText(link); } catch (e) { document.execCommand('copy'); } $('qcopy').textContent = '✓'; };
    $('qrot').onclick = async () => { if (!confirm(t('confirm_rot'))) return; await srcPost({ action: 'token', id }); showQR(id); };
    if (!$('qrdlg').open) $('qrdlg').showModal();
  } catch (e) { alert(t('saveerr')); }
}

let diagT = 0;
async function loadDiag() {
  if ($('diagbox').hidden || !$('diagbox').open || Date.now() - diagT < 5000) return; diagT = Date.now();
  try { const j = await (await fetch('diag', { cache: 'no-store' })).json(); $('diag').textContent = 'v' + j.version + '  ·  ' + t('device') + ': ' + j.settings.device + '  ·  ' + j.settings.sample_rate + ' Hz\n\n' + j.text; } catch (e) { }
}

/* ================= GasLighter Pro: Lizenz, Sperren, „Pro kaufen“ ================= */
let PRO = { ok: false, state: 'none', free_import: true, buy: 'https://www.gsimulations.de/gaslighter/#buypro' };
async function proLoad() { try { const j = await (await fetch('pro', { cache: 'no-store' })).json(); if (j && j.state) PRO = j; } catch (e) { } proBanner(); return PRO; }
function proDate(d) { try { return new Date(d + 'T12:00:00').toLocaleDateString(locale()); } catch (e) { return d; } }
function proBuyLink(cls) { const a = el('a', { className: cls || 'chip pri', href: PRO.buy, target: '_blank', rel: 'noopener', textContent: '🛒 ' + t('pro_buy') }); return a; }
/* Hinweis kurz vor Ablauf (14 Tage) bzw. nach Ablauf – einmal je Ablaufdatum wegklickbar */
function proBanner() {
  const b = $('b_pro'); if (!b) return;
  let key = '', html = '';
  if (PRO.ok && PRO.days_left != null && PRO.days_left <= 14) { key = 'soon_' + PRO.until; html = t('pro_soon', { d: esc(proDate(PRO.until)), n: PRO.days_left }); }
  else if (PRO.state === 'expired') { key = 'exp_' + PRO.until; html = t('pro_expired_ban', { d: esc(proDate(PRO.until)) }); }
  let gone = false; try { gone = localStorage.getItem('laerm_proban') === key; } catch (e) { }
  if (!key || gone) { b.style.display = 'none'; return; }
  b.innerHTML = html + ` <a href="${esc(PRO.buy)}" target="_blank" rel="noopener">${esc(t('pro_renew'))}</a> ${BX()}`;
  b.style.display = 'block';
  b.querySelector('.bclose').onclick = () => { try { localStorage.setItem('laerm_proban', key); } catch (e) { } b.style.display = 'none'; };
}
/* Kleines Fenster an gesperrten Stellen: was die Funktion kann, „Pro kaufen“, „Schlüssel eintragen“ */
function proGate(feat) {
  let d = $('prognd');
  if (!d) { d = el('dialog', { id: 'prognd', className: 'evdlg prognd' }); document.body.appendChild(d); }
  d.innerHTML = `<h3>🔒 ${esc(t('pro_title'))}</h3><p><b>${esc(t('pro_f_' + feat))}</b></p><p>${esc(t('pro_g_' + feat))}</p><p class="mut">${esc(t('pro_gate_free'))}</p>
    <div class="ntedbtns"><button type="button" class="pgx">${esc(t('a_close'))}</button><button type="button" class="pgkey">🔑 ${esc(t('pro_enter'))}</button></div>`;
  d.querySelector('.ntedbtns').insertBefore(proBuyLink('chip pri'), d.querySelector('.pgkey').nextSibling);
  d.querySelector('.pgx').onclick = () => d.close();
  d.querySelector('.pgkey').onclick = async () => { d.close(); if (!$('dlg').open) await openSettings(); openSec('s_pro'); const k = $('prokey'); if (k) { k.scrollIntoView({ block: 'center' }); k.focus(); } };
  d.showModal();
}
function proLockTag() { const s = el('span', { className: 'protag', textContent: '🔒 Pro' }); s.title = t('pro_title'); return s; }
/* Einstellungen → Allgemein → Pro */
function proBox() {
  const fs = el('fieldset', { id: 'probox' }); fs.dataset.sec = 's_pro';
  fs.appendChild(el('legend', { textContent: t('s_pro') }));
  const st = el('div', { className: 'prost' }); fs.appendChild(st);
  const P = PRO;
  if (P.ok) st.innerHTML = `<b class="prook">✔ ${esc(t('pro_active', { d: proDate(P.until) }))}</b>` + (P.order ? `<small>${esc(t('pro_order', { o: P.order }))}${P.key_hint ? ' · ' + esc(P.key_hint) : ''}</small>` : '');
  else if (P.state === 'expired') st.innerHTML = `<b class="proexp">⚠ ${esc(t('pro_expired', { d: proDate(P.until) }))}</b>`;
  else st.innerHTML = `<b>${esc(t('pro_free'))}</b>`;
  const ul = el('ul', { className: 'prolist' });
  for (const f of ['imp', 'thr', 'dev']) ul.appendChild(el('li', { textContent: (P.ok ? '✔ ' : '🔒 ') + t('pro_f_' + f) }));
  fs.appendChild(ul);
  fs.appendChild(el('small', { className: 'prohelp', textContent: t('h_pro') + (!P.ok && P.free_import ? ' ' + t('pro_free_import') : '') }));
  const row = el('div', { className: 'bkrow prorow' });
  if (P.ok) {
    const del = el('button', { type: 'button', className: 'chip', textContent: t('pro_remove') });
    del.onclick = async () => { if (!confirm(t('pro_remove_q'))) return; try { const j = await (await fetch('pro', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{"action":"del"}' })).json(); PRO = j.pro || PRO; } catch (e) { } proRefresh(); };
    row.append(del, proBuyLink('chip'));
    fs.appendChild(row);
  } else {
    const ta = el('textarea', { id: 'prokey', className: 'prokey', rows: 3, placeholder: 'GL1-XXXXX-XXXXX-…', spellcheck: false });
    ta.setAttribute('autocomplete', 'off');
    const go = el('button', { type: 'button', className: 'pri', textContent: '🔑 ' + t('pro_activate') });
    const msg = el('span', { className: 'bkmsg', id: 'promsg' }); msg.setAttribute('aria-live', 'polite');
    go.onclick = async () => {
      const key = ta.value.trim(); if (!key) { ta.focus(); return; }
      go.disabled = true; msg.textContent = '';
      try {
        const j = await (await fetch('pro', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ key }) })).json();
        if (j.ok) { PRO = j.pro; proRefresh(); return; }
        msg.textContent = '⚠ ' + t('pro_err_' + (['expired', 'signature', 'product', 'format', 'empty'].includes(j.error) ? j.error : 'format'));
      } catch (e) { msg.textContent = '⚠ ' + t('saveerr'); }
      go.disabled = false;
    };
    fs.appendChild(ta);
    row.append(go, proBuyLink('chip'), msg); fs.appendChild(row);
  }
  return fs;
}
/* Nach Eintragen/Entfernen: Formular neu aufbauen (Sperren an/aus), Pro-Bereich offen lassen */
function proRefresh() {
  proBanner();
  if (!$('dlg').open) return;
  const body = $('sbody'), sc = body.scrollTop;
  buildForm(CUR); buildSources(); applySTab(); openSec('s_pro'); body.scrollTop = sc;
}
/* Ohne Pro: Erweiterte Einstellungen der Erkennung nur ansehen */
function proApplyForm() {
  const fs = $('sbody').querySelector('fieldset[data-sec="s_thr"]'); if (!fs) return;
  fs.classList.toggle('prolocked', !PRO.ok);
  const old = fs.querySelector('.proban'); if (old) old.remove();
  if (PRO.ok) return;
  fs.querySelectorAll('input,select,textarea').forEach(x => { x.disabled = true; });
  const ban = el('div', { className: 'proban' });
  ban.append(proLockTag(), el('span', { textContent: ' ' + t('pro_thr_ban') + ' ' }));
  const more = el('button', { type: 'button', className: 'chip', textContent: t('pro_more') }); more.onclick = () => proGate('thr');
  ban.append(more);
  const lg = fs.querySelector(':scope > legend'); if (lg) lg.after(ban); else fs.prepend(ban);
  if (lg && !lg.querySelector('.protag')) lg.appendChild(proLockTag());
}
/* ================= Einstellungen ================= */
const BG_STATS = ['quiet', 'median', 'min', 'mean', 'max'];   // So wird „normal“ berechnet
const FORM = [
  ['s_time', [['active_from', 'time'], ['active_to', 'time']]],
  ['s_audio', [['device', 'device'], ['mic_port', 'port'], ['mic_volume', 'range', 0, 400, 1], ['sample_rate', 'sel', [16000, 22050, 44100, 48000]]]],
  ['s_thr', [
    ['thr_mode', 'sel', ['bounded', 'dynamic', 'fixed'], { bounded: 'o_bounded', dynamic: 'o_dynamic', fixed: 'o_fixed' }],
    ['thr_fixed_db', 'num', -120, 0, 0.1, null, ['fixed']],
    ['offset_db', 'num', 0.5, 40, 0.1, null, ['dynamic', 'bounded']],
    ['min_db', 'num', -120, -10, 0.1, null, ['bounded']],
    ['thr_max_db', 'num', -120, 0, 0.1, null, ['bounded']],
    ['bg_window', 'window', 1, 3600, 1, null, ['dynamic', 'bounded']],
    ['bg_stat', 'sel', BG_STATS, { quiet: 'o_quiet', median: 'o_median', min: 'o_min', mean: 'o_mean', max: 'o_max' }, null, null, ['dynamic', 'bounded']],
    ['rise_s', 'num', 0.5, 3600, 0.5, null, ['dynamic', 'bounded']],
    ['fall_s', 'num', 0.5, 3600, 0.5, null, ['dynamic', 'bounded']],
    ['min_event_ms', 'num', 0, 2000, 20]]],
  ['s_rec', [['ctx_s', 'num', 0, 120, 1], ['day_layers', 'chk'], ['day_spec', 'chk'], ['fp_store', 'chk'], ['auto_delete', 'chk'], ['retention_days', 'num', 1, 3650, 1]]],
  ['s_wav', [['save_audio', 'chk'], ['audio_novoice', 'chk', 'save_audio'], ['pre_roll_s', 'num', 0, 30, 0.1, 'save_audio'], ['post_roll_s', 'num', 0.1, 60, 0.1, 'save_audio'], ['max_clip_s', 'num', 1, 300, 0.5, 'save_audio'], ['co_record', 'chk', 'save_audio']]],
  ['s_video', [['clip_dir', 'text'], ['video_width', 'num', 0, 3840, 10], ['video_fps', 'num', 1, 30, 1], ['video_crf', 'num', 18, 40, 1]]],
  ['s_notes', [['quiet_from', 'time'], ['quiet_to', 'time'], ['quiet_sunday', 'chk']]],
  ['s_misc', [['classify', 'chk'], ['ki_embed', 'chk'], ['group_pause_s', 'num', 10, 3600, 10], ['fn_assign_min', 'num', 0, 60, 1], ['language', 'sel', ['auto', 'de', 'en'], { auto: 'lauto', de: '#Deutsch', en: '#English' }]]],
];
let SRC = [], SRC_DET = [], DEF_SRC = '';
function portsFor(dev) {
  const name = !dev || dev === 'default' || dev === 'pulse' ? DEF_SRC : dev;
  const d = SRC_DET.find(x => x.name === name);
  return d ? d.ports : [];
}
function fillPorts(sel, dev, val) {
  sel.innerHTML = ''; option(sel, '', t('port_auto'));
  const ps = portsFor(dev);
  for (const p of ps) option(sel, p.name, p.desc + (p.avail ? '' : ' (' + t('port_na') + ')'));
  if (val && !ps.some(p => p.name === val)) option(sel, val, val);
  sel.value = val || '';
  const row = sel.closest('.f'); if (row) row.classList.toggle('hide', ps.length < 2 && !val);
}
/* Pro Geraet einstellbare Werte (wie PER_KEYS im Server) */
const PER = ['thr_mode', 'offset_db', 'thr_fixed_db', 'min_db', 'thr_max_db', 'bg_window', 'bg_unit', 'bg_stat', 'rise_s', 'fall_s',
  'min_event_ms', 'pre_roll_s', 'post_roll_s', 'max_clip_s', 'active_from', 'active_to', 'save_audio', 'audio_novoice', 'day_track', 'day_layers', 'day_spec', 'fp_store'];
const GLOBAL_ONLY = ['retention_days', 'auto_delete', 'classify', 'ki_embed', 'ctx_s', 'co_record', 'group_pause_s', 'fn_assign_min', 'clip_dir', 'video_width', 'video_fps', 'video_crf', 'quiet_from', 'quiet_to', 'quiet_sunday'];
let DEV = '';                                  // '' = Alle Geraete (Standard), sonst Quellen-ID
function srcById(id) { return SOURCES.find(s => s.id === id); }
/* Geräte zum Ansehen: eingerichtete und ehemalige (Daten vorhanden, Gerät nicht mehr eingerichtet, z. B. nach dem Einspielen) */
let FORMER = [];
function viewSources() { return SOURCES.concat(FORMER); }
function viewName(id) { const s = viewSources().find(x => x.id === id); return s ? s.name + (s.former ? ' (' + t('src_former') + ')' : '') : id; }
function effCfg(id) { const s = id && srcById(id); return s && s.own && s.cfg ? Object.assign({}, CUR || {}, s.cfg) : (CUR || {}); }
let formDirty = false;
function liveCfg(id) {                           // gerade gueltige Werte inkl. aktivem Zeitprofil (fuer die Statuskarte)
  const s = id && srcById(id), base = effCfg(id), slots = s && s.own ? (s.sched || []) : SCHED;
  const hit = slots.find(slotActive);
  return hit ? Object.assign({}, base, hit.cfg) : base;
}
function setDev(id, scroll) {
  if (formDirty && (id || '') !== DEV && !confirm(t('dev_discard'))) return;
  formDirty = false;
  DEV = id || '';
  const body = $('sbody'), sc = body.scrollTop;
  buildForm(CUR); buildSources();
  if (DEV && selSrc !== DEV && srcById(DEV)) selectSource(DEV);   // Live-Pegel oben zeigt dieses Geraet
  if (scroll) body.scrollTop = 0; else body.scrollTop = sc;
}
/* Oben in den Einstellungen: Auswahl „Allgemein (alle Geräte)“ oder ein Gerät; darunter die Reiter dafür */
function devBox() {
  const bar = $('sdev'); bar.innerHTML = '';
  const chips = el('div', { className: 'sdevchips', id: 'devsel' }); chips.setAttribute('role', 'tablist');
  const chip = (id, label) => { const b = el('button', { type: 'button', className: 'chip sdevc' + (DEV === id ? ' cur' : ''), textContent: label }); b.setAttribute('aria-selected', String(DEV === id)); b.onclick = () => { if (DEV !== id) setDev(id); }; chips.appendChild(b); };
  chip('', '⚙ ' + t('dev_gen'));
  for (const s of SOURCES) chip(s.id, (SRC_ICON[s.type] || '') + ' ' + s.name + (s.own ? ' · ' + t('own_short') : ''));
  const ti = tipIcon('t_dev'); if (ti) chips.appendChild(ti);
  bar.appendChild(chips);
  requestAnimationFrame(() => { const c = chips.querySelector('.cur'); if (c && chips.scrollWidth > chips.clientWidth) chips.scrollLeft = c.offsetLeft - chips.offsetLeft - 8; });   // Handy: gewähltes Gerät sichtbar
  if (DEV) {
    const s = srcById(DEV), r2 = el('div', { className: 'sdevown' });
    const cb = el('input', { type: 'checkbox', id: 'devown', checked: !!(s && s.own) });
    const ol = el('label', { htmlFor: 'devown', textContent: ' ' + t('f_devown') }); ol.prepend(cb); const oti = tipIcon('t_devown'); if (oti) ol.appendChild(oti);
    const hint = el('small', { id: 'devhint', textContent: t(cb.checked ? 'h_devown_on' : 'h_devown_off') });
    r2.append(ol, hint); bar.appendChild(r2);
    cb.onchange = () => {
      formDirty = true;
      hint.textContent = t(cb.checked ? 'h_devown_on' : 'h_devown_off');
      const sd = srcById(DEV);
      if (!cb.checked) setVals(CUR);                 // zeigt wieder die allgemeinen Werte
      else if (sd && sd.cfg) setVals(Object.assign({}, CUR, sd.cfg));   // gespeicherte Geraete-Werte zurueckholen
      renderSched();
      applyDevState();
    };
  } else bar.appendChild(el('small', { className: 'sdevhint', textContent: t('h_dev') }));
  syncSTabs();
}
/* Reiter je Auswahl: beim Gerät ohne „Allgemein“, „Geräte“ heißt dann „Gerät“ */
function syncSTabs() {
  const b = $('stabs'); if (!b) return;
  b.querySelectorAll('.stab').forEach(x => { if (x.dataset.tab === 'gen') x.hidden = !!DEV; if (x.dataset.tab === 'dev') x.textContent = t(DEV ? 'st_dev1' : 'st_dev'); });
  if (DEV && STAB === 'gen') setSTab('dev', true);
}
/* KI einlernen: Profile aufnehmen und verwalten (öffnet das Fenster „Profile“) */
function profBox() {
  const fs = el('fieldset', { id: 'pfbox' }); fs.dataset.sec = 's_prof';
  const lg = el('legend', { textContent: t('s_prof') }); const ti = tipIcon('t_prof'); if (ti) lg.appendChild(ti); fs.appendChild(lg);
  fs.appendChild(el('small', { className: 'calhelp', textContent: t('h_prof') }));
  const r = el('div', { className: 'calrow' });
  const b1 = el('button', { type: 'button', className: 'pri', textContent: '🧩 ' + t('pf_teach_btn') }), b2 = el('button', { type: 'button', textContent: t('s_prof_list') });
  b1.onclick = () => pfOpen('teach'); b2.onclick = () => pfOpen('list');
  r.append(b1, b2); fs.appendChild(r);
  return fs;
}
/* ---------- Zeitprofile ---------- */
let SCHED = [];                                  // allgemeine Zeitprofile (vom Server)
const SLOT_FIELDS = [['offset_db', 0.5, 40, 0.1, ['dynamic', 'bounded']], ['min_db', -120, -10, 0.1, ['bounded']], ['thr_max_db', -120, 0, 0.1, ['bounded']],
  ['thr_fixed_db', -120, 0, 0.1, ['fixed']], ['min_event_ms', 0, 2000, 20, null]];
function slotActive(sl) {
  const p = x => { const m = /^(\d{1,2}):(\d{2})$/.exec(x || ''); return m ? (+m[1]) * 60 + (+m[2]) : null; };
  const a = p(sl.from), b = p(sl.to), n = new Date(), m = n.getHours() * 60 + n.getMinutes();
  if (a == null || b == null || a === b) return false;
  return a < b ? (a <= m && m < b) : (m >= a || m < b);
}
function scopeSlots() {
  if (!DEV) return SCHED;
  const s = srcById(DEV), own = $('devown') ? $('devown').checked : !!(s && s.own);
  if (!own) return SCHED;
  return (s && s.own && s.sched) ? s.sched : (s && s.sched && s.sched.length ? s.sched : JSON.parse(JSON.stringify(SCHED)));
}
function slotRow(sl) {
  const box = el('div', { className: 'slot' });
  const r1 = el('div', { className: 'slotrow' });
  const fr = el('input', { type: 'time', value: sl.from || '22:00' }); fr.dataset.k = 'from';
  const to = el('input', { type: 'time', value: sl.to || '06:00' }); to.dataset.k = 'to';
  const md = el('select'); md.dataset.k = 'thr_mode';
  for (const m of ['bounded', 'dynamic', 'fixed']) option(md, m, t('o_' + m));
  const base = Object.assign({}, DEV ? effCfg(DEV) : CUR, sl.cfg || {});
  md.value = base.thr_mode;
  const del = el('button', { type: 'button', className: 'danger', textContent: '✕', title: t('delete') });
  del.onclick = () => { box.remove(); formDirty = true; markSlots(); };
  const act = el('span', { className: 'slotnow', textContent: t('slot_now') });
  r1.append(el('span', { textContent: t('from') }), fr, el('span', { textContent: t('to') }), to, md, act, del);
  const r2 = el('div', { className: 'slotrow' });
  for (const [k, lo, hi, step, modes] of SLOT_FIELDS) {
    const lab = el('label', { className: 'slotf' }); if (modes) lab.dataset.modes = modes.join(',');
    const inp = el('input', { type: 'number', min: lo, max: hi, step, value: base[k], className: 'n' }); inp.dataset.k = k;
    lab.append(el('small', { textContent: t('f_' + k) }), inp); r2.appendChild(lab);
  }
  const bl = el('label', { className: 'slotf' }); bl.dataset.modes = 'dynamic,bounded';   // So wird „normal“ berechnet (auch je Uhrzeit)
  const bs = el('select'); bs.dataset.k = 'bg_stat';
  for (const m of BG_STATS) option(bs, m, t('o_' + m));
  bs.value = base.bg_stat || 'quiet';
  bl.append(el('small', { textContent: t('f_bg_stat') }), bs); r2.appendChild(bl);
  box.append(r1, r2);
  const sync = () => { const m = md.value; r2.querySelectorAll('.slotf[data-modes]').forEach(l => l.classList.toggle('hide', !l.dataset.modes.split(',').includes(m))); markSlots(); };
  md.addEventListener('change', sync); fr.addEventListener('change', markSlots); to.addEventListener('change', markSlots);
  box.querySelectorAll('input,select').forEach(e => { e.addEventListener('input', () => { formDirty = true; }); e.addEventListener('change', () => { formDirty = true; }); });
  sync();
  return box;
}
function readSlots() {
  return [...document.querySelectorAll('#slotlist .slot')].map(b => {
    const g = k => b.querySelector(`[data-k="${k}"]`).value, cfg = { thr_mode: g('thr_mode') };
    for (const [k] of SLOT_FIELDS) cfg[k] = g(k);
    cfg.bg_stat = g('bg_stat');
    return { from: g('from'), to: g('to'), cfg };
  });
}
function markSlots() {                           // "jetzt aktiv" am ersten passenden Profil
  let found = false;
  document.querySelectorAll('#slotlist .slot').forEach(b => {
    const on = !found && slotActive({ from: b.querySelector('[data-k=from]').value, to: b.querySelector('[data-k=to]').value });
    if (on) found = true; b.classList.toggle('now', on);
  });
}
function schedBox() {
  const fs = el('fieldset', { id: 'schedbox', className: 'ff' }); fs.dataset.sec = 's_sched';
  const lg = el('legend', { textContent: t('s_sched') }); const sti = tipIcon('t_sched'); if (sti) lg.appendChild(sti); fs.appendChild(lg);
  fs.appendChild(el('small', { className: 'schedhelp', textContent: t('h_sched') }));
  const list = el('div', { id: 'slotlist' }); fs.appendChild(list);
  for (const sl of scopeSlots()) list.appendChild(slotRow(sl));
  const add = el('button', { type: 'button', id: 'slotadd', textContent: '+ ' + t('slot_add') });
  add.onclick = () => {
    if (list.children.length >= 12) return;
    const v = formValues(), cfg = {}; cfg.thr_mode = v.thr_mode; for (const [k] of SLOT_FIELDS) cfg[k] = v[k]; cfg.bg_stat = v.bg_stat;
    list.appendChild(slotRow({ from: '22:00', to: '06:00', cfg })); formDirty = true; markSlots();
  };
  fs.appendChild(add);
  setTimeout(markSlots, 0);
  return fs;
}
function renderSched() {
  const old = $('schedbox'); if (!old) return;
  const nb = schedBox(); old.replaceWith(nb); applyDevState();
}
function refreshDevBox() {                       // Geraeteliste neu (nach Hinzufuegen/Loeschen), Formular bleibt
  if (!$('sdev')) return;
  if (DEV && !srcById(DEV)) { setDev(''); return; }
  devBox();
}
function setVals(obj) {
  for (const k of PER) {
    const e = $('in_' + k); if (!e || obj[k] === undefined) continue;
    if (e.type === 'checkbox') e.checked = !!obj[k]; else e.value = obj[k];
    e.dispatchEvent(new Event('input'));
  }
  syncModeRows(); syncAudioRows();
}
/* Echter Ton: Stimm-Sicherung bleibt immer sichtbar (wie „Löschen nach (Tagen)“), der Hinweis sagt, wann sie wirkt */
function syncAudioRows() {                       // Vor-/Nachlauf, Länge, Mitspeichern und Stimm-Sicherung nur bei echtem Ton
  document.querySelectorAll('#sbody .f[data-need]').forEach(r => { const c = $('in_' + r.dataset.need); r.classList.toggle('needhide', !!c && !c.checked); });
}
function applyDevState() {
  const own = !!(DEV && $('devown') && $('devown').checked);
  document.querySelectorAll('#sbody fieldset.ff').forEach(fs => {
    const sec = fs.dataset.sec;
    fs.classList.toggle('devhide', !!DEV && (sec === 's_misc' || sec === 's_video' || sec === 's_notes' || (sec === 's_audio' && DEV !== 'main')));
    fs.querySelectorAll('.f[data-key]').forEach(r => {
      const k = r.dataset.key, per = PER.includes(k);
      r.classList.toggle('devhide', !!DEV && GLOBAL_ONLY.includes(k));
      r.classList.toggle('inherit', !!DEV && per && !own);
      r.querySelectorAll('input,select').forEach(i => { i.disabled = !!DEV && per && !own; });
    });
  });
  const sb = $('schedbox');
  if (sb) { const inh = !!DEV && !own; sb.classList.toggle('inherit', inh); sb.querySelectorAll('input,select,button').forEach(i => { i.disabled = inh; }); }
}
/* Hilfe: ⓘ-Hinweise mit Erklaerung (Maus drueber, antippen oder Tab). Abschaltbar, gilt pro Browser. */
function tipIcon(key) {
  const txt = t(key); if (!txt || txt === key) return null;
  const i = el('span', { className: 'tipi', textContent: 'ⓘ', tabIndex: 0 }); i.setAttribute('role', 'button'); i.setAttribute('aria-label', txt);
  i.dataset.tip = txt;
  return i;
}
function showTip(i) {
  const b = $('tipbox'), dlg = $('dlg'); b.textContent = i.dataset.tip; b.classList.add('on');
  const r = i.getBoundingClientRect(), dr = dlg.getBoundingClientRect(), w = Math.min(340, dr.width - 24);
  b.style.width = w + 'px';
  let x = r.left - dr.left - 20; x = Math.max(12, Math.min(x, dr.width - w - 12));
  let y = r.bottom - dr.top + 6; if (y + b.offsetHeight > dr.height - 8) y = r.top - dr.top - b.offsetHeight - 6;
  b.style.left = x + 'px'; b.style.top = Math.max(8, y) + 'px'; if (TIP !== i) TIP_T = Date.now(); TIP = i;
}
let TIP = null, TIP_T = 0;
function hideTip() { $('tipbox').classList.remove('on'); TIP = null; }
function initHelp() {
  let on = true; try { on = localStorage.getItem('laerm_help') !== '0'; } catch (e) { }
  const cb = $('helpon'); cb.checked = on; $('dlg').classList.toggle('nohelp', !on);
  cb.addEventListener('change', () => { $('dlg').classList.toggle('nohelp', !cb.checked); hideTip(); try { localStorage.setItem('laerm_help', cb.checked ? '1' : '0'); } catch (e) { } });
  $('helptg').title = t('help_tip');
  const dlg = $('dlg');
  dlg.addEventListener('pointerover', e => { if (e.pointerType !== 'mouse') return; const i = e.target.closest && e.target.closest('.tipi'); if (i) showTip(i); });
  dlg.addEventListener('pointerout', e => { if (e.pointerType !== 'mouse') return; const i = e.target.closest && e.target.closest('.tipi'); if (i && TIP === i) hideTip(); });
  dlg.addEventListener('click', e => { const i = e.target.closest && e.target.closest('.tipi'); if (i) { e.preventDefault(); if (TIP === i && Date.now() - TIP_T > 500) hideTip(); else showTip(i); } else if (TIP) hideTip(); });   // Antippen: erst zeigen, zweites Tippen schliesst
  dlg.addEventListener('focusin', e => { if (e.target.classList && e.target.classList.contains('tipi')) showTip(e.target); });
  dlg.addEventListener('focusout', e => { if (e.target.classList && e.target.classList.contains('tipi')) hideTip(); });
  $('sbody').addEventListener('scroll', hideTip);
}
function el(tag, props) { const e = document.createElement(tag); Object.assign(e, props || {}); return e; }
function option(sel, v, label) { const o = el('option', { value: String(v), textContent: label }); sel.appendChild(o); return o; }
function buildForm(base) {
  const body = $('sbody'); body.innerHTML = '';
  if (DEV && !srcById(DEV)) DEV = '';
  const cur = DEV ? effCfg(DEV) : base;
  devBox();
  for (const [sec, fields] of FORM) {
    const fs = el('fieldset', { className: 'ff' }); fs.dataset.sec = sec; fs.appendChild(el('legend', { textContent: t(sec) }));
    if (sec === 's_wav') fs.appendChild(el('div', { className: 'wavwarn', textContent: t('h_wav') }));   // warum man das ausgeschaltet lassen sollte
    for (const fd of fields) {
      const [k, type] = fd, row = el('div', { className: 'f' }), ctl = el('div', { className: 'ctl' });
      row.dataset.key = k;
      const modes = type === 'sel' ? fd[6] : fd[6];
      if (modes) row.dataset.modes = modes.join(',');
      const need = type === 'chk' ? fd[2] : type === 'num' ? fd[5] : null;      // nur sichtbar, wenn dieser Schalter an ist (z. B. echter Ton)
      if (typeof need === 'string') row.dataset.need = need;
      let inp;
      if (type === 'device') {
        inp = el('select');
        option(inp, 'default', t('dflt'));
        SRC.forEach(s => option(inp, s.name, s.name + (s.state ? ' (' + s.state + ')' : '')));
        if (![...inp.options].some(o => o.value === cur[k])) option(inp, cur[k], cur[k]);
        option(inp, '__custom', t('custom'));
        inp.value = cur[k];
        inp.addEventListener('change', () => {
          if (inp.value !== '__custom') return;
          const v = prompt(t('custom_prompt'), cur[k]);
          if (v && v.trim()) { const o = el('option', { value: v.trim(), textContent: v.trim() }); inp.insertBefore(o, inp.lastChild); inp.value = v.trim(); }
          else inp.value = cur[k];
        });
        ctl.appendChild(inp);
      } else if (type === 'port') {             // Buchse der Soundkarte (nur wenn es mehrere gibt)
        inp = el('select'); ctl.appendChild(inp);
        fillPorts(inp, cur.device, cur[k]);
      } else if (type === 'range') {
        const rg = el('input', { type: 'range', min: fd[2], max: fd[3], step: fd[4], value: cur[k] });
        inp = el('input', { type: 'number', min: fd[2], max: fd[3], step: fd[4], value: cur[k], className: 'n' });
        rg.addEventListener('input', () => { inp.value = rg.value; });
        inp.addEventListener('input', () => { rg.value = inp.value; });
        ctl.appendChild(rg); ctl.appendChild(inp); ctl.appendChild(el('span', { textContent: '%' }));
      } else if (type === 'sel') {
        inp = el('select');
        for (const v of fd[2]) { const lk = fd[3] && fd[3][v]; option(inp, v, lk ? (lk[0] === '#' ? lk.slice(1) : t(lk)) : v); }
        inp.value = String(cur[k]);
        ctl.appendChild(inp);
      } else if (type === 'chk') {
        inp = el('input', { type: 'checkbox', checked: !!cur[k] }); ctl.appendChild(inp);
      } else if (type === 'text') {
        inp = el('input', { type: 'text', value: cur[k] || '', placeholder: t('ph_' + k), className: 'wide' }); ctl.appendChild(inp);
      } else if (type === 'time') {
        inp = el('input', { type: 'time', value: cur[k] || '' }); ctl.appendChild(inp);
        const clr = el('button', { type: 'button', className: 'chip tclr', textContent: '✕', title: t('time_clear') });   // Uhrzeit mit einem Klick leeren
        clr.setAttribute('aria-label', t('time_clear'));
        const syncClr = () => { clr.disabled = !inp.value; };
        clr.onclick = () => { inp.value = ''; inp.dispatchEvent(new Event('input', { bubbles: true })); inp.dispatchEvent(new Event('change', { bubbles: true })); syncClr(); };
        inp.addEventListener('input', syncClr); inp.addEventListener('change', syncClr); syncClr();
        ctl.appendChild(clr);
      } else if (type === 'window') {
        inp = el('input', { type: 'number', min: fd[2], max: fd[3], step: fd[4], value: cur[k], className: 'n' });
        const u = el('select', { name: 'bg_unit', id: 'in_bg_unit' });
        option(u, 's', t('u_s')); option(u, 'min', t('u_min')); u.value = cur.bg_unit;
        ctl.appendChild(inp); ctl.appendChild(u);
      } else {
        inp = el('input', { type: 'number', min: fd[2], max: fd[3], step: fd[4], value: cur[k] }); ctl.appendChild(inp);
      }
      inp.name = k; inp.id = 'in_' + k;
      const lab = el('label', { htmlFor: inp.id, textContent: t('f_' + k) });
      const ti = tipIcon('t_' + k); if (ti) lab.appendChild(ti);
      row.appendChild(lab); row.appendChild(ctl);
      const help = ('h_' + k) in I18N.de ? t('h_' + k) : ''; if (help) row.appendChild(el('small', { textContent: help }));
      if (k === 'fp_store') { row.appendChild(el('small', { id: 'fpstat', className: 'fpstat' })); fpStat(); }
      fs.appendChild(row);
    }
    body.appendChild(fs);
  }
  const thrFs = body.querySelector('fieldset[data-sec="s_thr"]'); if (thrFs) { thrFs.after(schedBox()); thrFs.after(profBox()); }
  const timeFs = body.querySelector('fieldset[data-sec="s_time"]'); if (timeFs) timeFs.after(haBox());
  $('in_thr_mode').addEventListener('change', syncModeRows);
  if ($('in_save_audio')) $('in_save_audio').addEventListener('change', e => {   // Einschalten nur nach Bestaetigung des Hinweises
    if (e.target.checked && !confirm(t('audio_confirm'))) e.target.checked = false;
    syncAudioRows();
  });
  syncAudioRows();
  if ($('in_device') && $('in_mic_port')) { $('in_device').addEventListener('change', () => fillPorts($('in_mic_port'), $('in_device').value, '')); fillPorts($('in_mic_port'), $('in_device').value, $('in_mic_port').value); }
  syncModeRows();
  applyDevState();
  body.appendChild(bkBox()); body.appendChild(rsBox()); body.appendChild(diagBox());
  { const misc = body.querySelector('fieldset[data-sec="s_misc"]'); const pb = proBox(); if (misc) misc.before(pb); else body.appendChild(pb); }
  proApplyForm();
  formDirty = false; makeCollapsible();
  body.querySelectorAll('fieldset.ff [name], #devown').forEach(e => { e.addEventListener('input', () => { formDirty = true; }); e.addEventListener('change', () => { formDirty = true; }); });
}
function syncModeRows() {
  const m = $('in_thr_mode').value;
  document.querySelectorAll('#sbody .f[data-modes]').forEach(r => r.classList.toggle('hide', !r.dataset.modes.split(',').includes(m)));
}
function formValues() {
  const data = {};
  $('sbody').querySelectorAll('[name]').forEach(e => { data[e.name] = e.type === 'checkbox' ? e.checked : e.value; });
  return data;
}
function previewThr(base) {
  const box = $('sbody'); if (!box.childElementCount) return null;
  const v = formValues(), m = v.thr_mode, num = k => parseFloat(v[k]);
  if (m === 'fixed') return num('thr_fixed_db');
  if (base == null) return null;
  let x = base + num('offset_db');
  if (m === 'bounded') x = clamp(x, num('min_db'), Math.max(num('min_db') + 1, num('thr_max_db')));
  return x;
}
async function openSettings() {
  $('smsg').textContent = ''; $('calmsg').textContent = t('calhint');
  try {
    const r = await (await fetch('settings', { cache: 'no-store' })).json();
    if (r.pro && r.pro.state) { PRO = r.pro; proBanner(); }
    SRC = r.sources || []; CUR = r.settings; SCHED = r.schedule || []; SRC_DET = r.src_details || []; DEF_SRC = r.default_source || ''; initSTabs(); buildForm(CUR); await loadSources(); await plFetch(); buildSources(); applySTab(); $('dlg').showModal();
  } catch (e) { $('smsg').textContent = t('saveerr'); }
}
async function saveSettings() {
  $('smsg').textContent = t('saving'); $('ssave').disabled = true;
  try {
    const v = formValues();
    let devChanged = false;
    if (DEV) {                                  // Geraete-Werte gehen an die Quelle, nicht in die allgemeinen Einstellungen
      const s = srcById(DEV), own = !!($('devown') && $('devown').checked), per = {};
      for (const k of PER) if (k in v) { per[k] = v[k]; delete v[k]; }
      const before = JSON.stringify([!!(s && s.own), (s && s.own && s.cfg) || null, (s && s.own && s.sched) || null]);
      const rs = await srcPost(Object.assign({ action: 'update', id: DEV, own }, own ? { cfg: per, sched: readSlots() } : {}));
      const ns = srcById(DEV);
      devChanged = before !== JSON.stringify([!!(ns && ns.own), (ns && ns.own && ns.cfg) || null, (ns && ns.own && ns.sched) || null]);
    } else {                                    // allgemeine Zeitprofile
      const rr = await (await fetch('schedule', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ slots: readSlots() }) })).json();
      if (!rr.ok) throw new Error(rr.error || 'error');
      SCHED = rr.slots; devChanged = rr.changed;
    }
    const r = await (await fetch('settings', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(v) })).json();
    if (!r.ok) throw new Error(r.error || 'error');
    CUR = r.settings; renderEvents();
    if (r.changed.includes('language')) { pickLang(CUR.language); tr(); setLive(view.live); renderEvents(); }
    if (r.changed.length || devChanged) { const sc = $('sbody').scrollTop; buildForm(CUR); buildSources(); $('sbody').scrollTop = sc; }
    if (devChanged || r.changed.some(k => ['bg_window', 'bg_unit', 'bg_stat', 'thr_mode'].includes(k))) yv.auto = true;
    $('smsg').textContent = !r.changed.length && !devChanged ? t('nochange') : !r.changed.length ? (DEV ? t('saved_dev', { n: (srcById(DEV) || {}).name || '' }) : t('saved')) :
      (t(r.restart ? 'savedr' : 'saved') + (r.supervisor ? ' ' + t('sup') : (r.supervisor_available ? ' ' + t('nosup') : '')));
    formDirty = false; updateStatus();
  } catch (e) { $('smsg').textContent = t('saveerr'); }
  $('ssave').disabled = false;
}
/* Live-Pegel im Dialog */
function drawMeter() {
  const cv = $('meter'); fit(cv);
  const d = DPR(), c = cv.getContext('2d'), w = cv.width, h = cv.height, L = 6 * d, R = 6 * d, pw = w - L - R, by = 6 * d, bh = 20 * d;
  c.clearRect(0, 0, w, h);
  const leg = $('mleg');
  if (!st) { leg.textContent = ''; return; }
  const last = recs.length ? recs[recs.length - 1] : null;
  let pk = null;
  if (last) { const i3 = lowerBound(last.ts - 3000); for (let i = i3; i < recs.length; i++) if (recs[i].l > -125) pk = Math.max(pk == null ? -200 : pk, recs[i].l); }
  const pv = previewThr(st.base);
  const vals = [st.level, st.base, st.thr, pv, pk].filter(v => v != null && isFinite(v) && v > -125);
  let lo = -100, hi = -20;
  if (vals.length) {
    lo = Math.floor((Math.min(...vals) - 10) / 10) * 10; hi = Math.ceil((Math.max(...vals) + 10) / 10) * 10;
    if (hi - lo < 40) hi = lo + 40;
  }
  const X = v => L + pw * clamp((v - lo) / (hi - lo), 0, 1);
  c.fillStyle = C.grid; c.fillRect(L, by, pw, bh);
  if (st.level != null && st.level > -125) { c.fillStyle = st.active ? C.red : C.acc; c.fillRect(L, by, X(st.level) - L, bh); }
  if (pk != null) { c.fillStyle = C.tx; c.fillRect(X(pk) - d, by, 2 * d, bh); }
  const mark = (v, col, dash) => { if (v == null || !isFinite(v)) return; const x = X(v); c.strokeStyle = col; c.lineWidth = 3 * d; c.setLineDash(dash ? [4 * d, 3 * d] : []); c.beginPath(); c.moveTo(x, by - 4 * d); c.lineTo(x, by + bh + 4 * d); c.stroke(); c.setLineDash([]); };
  mark(st.base, C.bgl); mark(st.thr, C.thr); mark(pv, C.pv, true);
  for (const r of curRefs()) if (r.db >= lo && r.db <= hi) { c.fillStyle = r.color; c.fillRect(X(r.db) - d, by - 4 * d, 2 * d, bh + 8 * d); }
  c.font = (11 * d) + 'px system-ui'; c.fillStyle = C.mut; c.textAlign = 'center';
  const mg = dbTicks(lo, hi, pw, 42);
  c.fillStyle = C.mut;
  for (const k of mg.ticks) {
    const x = Math.round(X(k.v)) + .5; c.fillRect(x - .5, by + bh + 1 * d, 1, (k.major ? 5 : 2.5) * d);
    if (k.major) c.fillText(mg.fmt(k.v), clamp(x, L + 12 * d, L + pw - 12 * d), h - 3 * d);
  }
  const html = [[t('level'), st.silent ? null : st.level, st.active ? C.red : C.acc], [t('background'), st.base, C.bgl], [t('threshold'), st.thr, C.thr], [t('preview'), pv, C.pv]]
    .map(([n, v, col]) => `<b style="color:${col}">${esc(n)} ${f1(v == null || !isFinite(v) ? null : v)}</b>`).join(' ');
  if (leg.innerHTML !== html) leg.innerHTML = html;
}
let calTimer = null;
function calibrate() {
  if (calTimer) return;
  const t0 = nowServer(), dur = 15;
  $('calbtn').disabled = true;
  let left = dur; $('calmsg').textContent = t('calrun', { s: left });
  calTimer = setInterval(() => {
    left--; if (left > 0) { $('calmsg').textContent = t('calrun', { s: left }); return; }
    clearInterval(calTimer); calTimer = null; $('calbtn').disabled = false;
    const v = recs.filter(r => r.ts >= t0 && r.l > -125).map(r => r.l).sort((a, b) => a - b);
    if (v.length < 50) { $('calmsg').textContent = t('calfail'); return; }
    const q = p => v[Math.min(v.length - 1, Math.floor(p * v.length))];
    const p10 = q(0.10), p50 = q(0.5), p95 = q(0.95);
    if (DEV && $('devown') && !$('devown').checked) { $('devown').checked = true; $('devown').dispatchEvent(new Event('change')); }   // Kalibrieren gilt dann fuer dieses Geraet
    const set = (k, x) => { const e = $('in_' + k); if (e) { e.value = x; e.dispatchEvent(new Event('input')); } };
    const r5 = x => Math.round(x * 2) / 2;
    set('offset_db', clamp(r5(p95 - p10 + 4), 6, 20));
    set('min_db', clamp(r5(p10 + 3), -120, -10));
    set('thr_max_db', clamp(r5(p50 + 40), r5(p10 + 10), 0));
    set('thr_fixed_db', clamp(r5(p95 + 6), -120, 0));
    $('calmsg').textContent = t('calres', { q: p10.toFixed(1), m: p50.toFixed(1), p: p95.toFixed(1) });
  }, 1000);
}

/* ================= Start ================= */
let animating = false, dirty = true, lastFrame = performance.now(), frameDt = 16, lastT1 = 0, lastSeqDrawn = -1, lastMeter = 0;
const smoothK = tau => 1 - Math.exp(-frameDt / tau);
function markDirty() { dirty = true; }
function frame(now) {
  frameDt = Math.min(100, now - lastFrame); lastFrame = now;
  if (!document.hidden) {
    try {
      playAdapt(frameDt);
      let [t0, t1] = viewRange();
      if (view.live) { const pxm = (t1 - t0) / Math.max(100, ($('main').clientWidth - AXL() - 14) * DPR()); t1 = Math.floor(t1 / pxm) * pxm; t0 = t1 - view.span * 1000; }   // in ganzen Pixeln weiter
      const hist = histOn();                         // zurückgespult: Tagesverlauf statt Live-Grafik
      if (!hist && recs.length && t0 < recs[0].ts) loadOlder();
      const pxMs = view.span * 1000 / Math.max(100, $('main').clientWidth - AXL() - 14);
      const seq = recs.length ? recs[recs.length - 1].s : -1;
      if (Math.abs(t1 - lastT1) >= pxMs * 0.5 || seq !== lastSeqDrawn || animating || hoverX != null) dirty = true;
      if (dirty && !NV.open && !PV.open && !hist) {
        dirty = false; animating = false; lastT1 = t1; lastSeqDrawn = seq;
        if (view.mode === 'level') drawLevel($('main'), t0, t1); else drawWave($('main'), t0, t1);
        drawFnLive($('main'), t0, t1);                // freie Notizen an ihrer Stelle
        drawSpec($('spec'), t0, t1);
      }
      if ($('dlg').open && now - lastMeter > 90) { lastMeter = now; drawMeter(); }
      loadDiag();
    } catch (e) { console.error(e); }
  }
  requestAnimationFrame(frame);
}
window.addEventListener('resize', markDirty);
['click', 'change', 'wheel', 'pointerup'].forEach(ev => document.addEventListener(ev, markDirty, true));

/* ================= Nachtbericht (Schlaf-App-Stil) ================= */
const NV = { per: 'win', art: '', from: null, to: null, date: null, src: 'all', data: null, week: null, hover: null, playing: null, hits: [], timer: null, open: false };
const isoDay = d => d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate());
const parseDay = s => { const [y, m, d] = s.split('-').map(Number); return new Date(y, m - 1, d); };
/* Tages-Kreise: liegt der gewählte Tag in den letzten 7 Tagen, endet die Leiste bei der neuesten Nacht (nichts verschwindet);
   ältere Tage stehen in der Mitte (3 davor, 3 danach, nie über die neueste hinaus) */
function weekEnd(ds) {
  const last = nightDefault(), d = parseDay(ds), l = parseDay(last), diff = Math.round((l - d) / 864e5);
  if (diff <= 6) return last;
  const e = new Date(d); e.setDate(e.getDate() + 3); return isoDay(e);
}
function nightDefault() {
  // die zuletzt begonnene Nacht: vor Beginn der heutigen Nacht (Erfassung ab, sonst 20:00) ist es die von gestern
  const n = new Date(), d = new Date(n), m = /^(\d{1,2}):(\d{2})$/.exec((CUR && CUR.active_from) || '');
  if (!(m && CUR.active_to && CUR.active_from !== CUR.active_to)) return isoDay(d);   // keine Erfassungszeit: der heutige Tag
  const a = (+m[1]) * 60 + (+m[2]);
  if (n.getHours() * 60 + n.getMinutes() < a) d.setDate(d.getDate() - 1);
  return isoDay(d);
}
const NC = { bg: '', acc: '#38d9c4', accL: '#38d9c4', mut: '#888', grid: '#8883', warn: '#ff922b', red: '#ff6b6b', tx: '#fff', l1: '#8881', l2: '#8883', l3: '#888a' };
function ca(col, a) { if (/^hsl\(/.test(col || '')) return col.replace(')', ` / ${a})`); const m = /^#([0-9a-f]{6})/i.exec(col || ''); if (!m) return col; const v = parseInt(m[1], 16); return `rgba(${v >> 16},${(v >> 8) & 255},${v & 255},${a})`; }
function readNC() {
  const cs = getComputedStyle($('nightview')), g = n => cs.getPropertyValue(n).trim();
  Object.assign(NC, { bg: g('--card'), acc: g('--nacc') || NC.acc, accL: g('--nacc') || NC.accL, mut: g('--mut'), warn: g('--thr'), red: g('--red'), tx: g('--tx'), l1: g('--nl1'), l2: g('--nl2'), l3: g('--nl3'), grid: g('--nl1') });
}
function locale() { return lang === 'en' ? 'en-GB' : 'de-DE'; }
function showTab(mode) {
  if (mode === true || mode === 'night') mode = 'prot'; else if (mode === false || !mode) mode = 'live';   // Nachtbericht ist jetzt Teil von Protokolle
  const prot = mode === 'prot', live = !prot;
  NV.open = prot; PV.open = prot;
  $('liveview').hidden = !live; $('nightview').hidden = !prot;
  $('tab_live').classList.toggle('on', live); $('tab_prot').classList.toggle('on', prot);
  try { localStorage.setItem('laerm_tab', mode); } catch (e) { }
  if (prot) { if (!NV.date) perSet(NV.per, true); plFetch().then(plRefresh); loadNight(); } else { markDirty(); levLoad(true); }
  setTimeout(dashRefresh, 50);
}
/* Reiter Protokolle: ein Datensatz für Zeitraum + Filter (Gerät, Art, Liste); Kopfzahlen, Verlauf, Diagramme und Tabelle nutzen ihn alle */
function perRange() {
  const d0 = parseDay(NV.date), add = (d, n) => { const x = new Date(d); x.setDate(x.getDate() + n); return x; }, iso = d => isoDay(d) + 'T00:00';
  if (NV.per === 'win') return null;                 // Erfassungszeit: der Server kennt sie
  if (NV.per === 'free') { const a = parseDay(NV.from || NV.date), b = parseDay(NV.to || NV.date); return [iso(a <= b ? a : b), iso(add(a <= b ? b : a, 1))]; }
  const n = NV.per === '7' ? 7 : NV.per === '30' ? 30 : 1;
  return [iso(add(d0, 1 - n)), iso(add(d0, 1))];
}
function perQuery() {                                // gemeinsame Filter für alle Anfragen des Reiters
  const r = perRange(), d = NV.data;
  let q = 'src=' + encodeURIComponent(NV.src || 'all') + '&list=' + encodeURIComponent(PV.cur || '') + '&art=' + encodeURIComponent(NV.art || '');
  if (r) q += '&from=' + r[0] + '&to=' + r[1];
  else if (d && d.start && d.date === NV.date) q += '&from=' + encodeURIComponent(d.start.slice(0, 16)) + '&to=' + encodeURIComponent(d.end.slice(0, 16));
  else return null;
  return q;
}
function perSet(p, quiet) {
  NV.per = p; try { localStorage.setItem('laerm_per', p); } catch (e) { }
  const today = isoDay(new Date());
  if (p === 'win') NV.date = nightDefault();
  else if (p === 'yest') { const d = new Date(); d.setDate(d.getDate() - 1); NV.date = isoDay(d); }
  else NV.date = today;
  if (p === 'free' && !NV.from) { const d = new Date(); d.setDate(d.getDate() - 6); NV.from = isoDay(d); NV.to = today; }
  if (!quiet) loadNight();
}
async function loadNight() {
  const ds = NV.date, src = NV.src, rg = perRange(), key = JSON.stringify([ds, src, rg, NV.per, PV.cur, NV.art]);
  const fq = '&src=' + encodeURIComponent(src) + '&list=' + encodeURIComponent(PV.cur || '') + '&art=' + encodeURIComponent(NV.art || '') + (rg ? '&from=' + rg[0] + '&to=' + rg[1] : '');
  try {
    const [n, w] = await Promise.all([
      fetch('night?date=' + ds + fq, { cache: 'no-store' }).then(r => r.json()),
      NV.per === 'win' ? fetch('nights?date=' + weekEnd(ds) + '&src=' + encodeURIComponent(src), { cache: 'no-store' }).then(r => r.json()) : Promise.resolve({ nights: [] })]);
    if (key !== JSON.stringify([NV.date, NV.src, perRange(), NV.per, PV.cur, NV.art])) return;
    const rk = n.start + '|' + n.end + '|' + src;      // anderer Zeitraum: Verlauf wieder ganz zeigen
    if (DT.rk !== rk) { DT.rk = rk; DT.from = DT.to = null; DT.mark = null; }
    DT.src = src;
    NV.data = n; NV.dkey = key; NV.week = w.nights; renderNight(); dtLoad(DT, true); EVSIG = ''; loadEvents(); loadRun();
  } catch (e) { }
  clearTimeout(NV.timer);
  if (NV.open && NV.data && new Date(NV.data.end) > new Date()) NV.timer = setTimeout(loadNight, 60000);   // laufende Nacht aktualisieren
}
/* Aufzeichnung & Datenkette: Unterbrechungen/Updates im Zeitraum und ob die Tagesaufzeichnung unverändert ist */
async function loadRun() {
  const d = NV.data; if (!d || !d.start) return;
  let j; try { j = await (await fetch('runtime?from=' + new Date(d.start).getTime() + '&to=' + new Date(d.end).getTime(), { cache: 'no-store' })).json(); } catch (e) { return; }
  const box = $('nrun'), L = locale(), fm = iso => { const x = new Date(iso); return isNaN(x) ? '' : x.toLocaleString(L, { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit' }); };
  const ch = j.chains || [], bad = ch.filter(c => c.ok === false), none = ch.filter(c => c.ok == null || c.none);
  const evs = (j.events || []).filter(e => ['down', 'update', 'fallback', 'crash', 'import'].includes(e.kind));
  NV.down = evs.filter(e => e.kind === 'down').map(e => [new Date(e.from).getTime(), new Date(e.to).getTime(), e.note || '', e.key || e.from, e.cause, e]).filter(g => g[1] > g[0]);
  for (const sub of DT.subs || []) if (sub.data) dtDraw(sub);
  if (typeof LDT !== 'undefined' && histOn()) dtDraw(LDT);
  const chainTxt = !ch.length ? '' : bad.length
    ? '⚠ ' + t('run_chain_bad', { l: bad.map(c => c.name + ' ' + c.day.slice(8, 10) + '.' + c.day.slice(5, 7) + '. ' + (c.bad ? new Date(c.bad).toLocaleTimeString(L, { hour: '2-digit', minute: '2-digit' }) : '')).join(', ') })
    : '🛡 ' + t(none.length === ch.length ? 'run_chain_none' : 'run_chain_ok', { n: ch.filter(c => c.ok).length });
  const evTxt = evs.map(e => e.kind === 'down' && e.cause === 'gap' ? t('run_gap', { a: fm(e.from), b: fm(e.to), s: e.name || viewName(e.sid) }) : e.kind === 'down' ? t('run_down', { a: fm(e.from), b: fm(e.to), v: e.version_new || '', r: t(e.reason === 'update' ? 'run_r_update' : e.cause === 'lost' ? 'run_r_lost' : 'run_r_restart') })
    : e.kind === 'import' ? t('run_import', { a: fm(e.at), s: viewName(e.sid), n: e.minutes })
    : e.kind === 'update' ? t('run_update', { a: fm(e.at), o: e.version_old, n: e.version_new }) : e.kind === 'fallback' ? t('run_fallback', { a: fm(e.at), v: e.version, b: e.to }) : t('run_crash', { a: fm(e.at), v: e.version }));
  box.hidden = !chainTxt && !evTxt.length;
  box.innerHTML = (chainTxt ? `<div class="${bad.length ? 'bad' : ''}">${esc(chainTxt)}</div>` : '') + evTxt.map((x, i) => {
    const e = evs[i]; if (e.kind !== 'down') return `<div class="ev">${esc(x)}</div>`;
    return `<div class="ev rdown" data-key="${esc(e.key || e.from)}">${esc(x)}${e.note ? ` <b class="rnote">📝 ${esc(e.note)}</b>` : ''} <button type="button" class="chip rnbtn">${esc(t(e.note ? 'run_note_edit' : 'run_note_add'))}</button></div>`;
  }).join('');
  box.querySelectorAll('.rdown .rnbtn').forEach(b => b.onclick = () => runNoteEdit(b.closest('.rdown'), evs.find(e => (e.key || e.from) === b.closest('.rdown').dataset.key)));
}
/* Kommentar zu einer Unterbrechung (z. B. „Stromausfall“) – ändert nichts an der Aufzeichnung */
function runNoteEdit(row, e) {
  if (!row || !e || row.querySelector('.rnform')) return;
  const f = el('span', { className: 'rnform' }), inp = el('input', { type: 'text', value: e.note || '', maxLength: 300, placeholder: t('run_note_ph') });
  const ok = el('button', { type: 'button', className: 'chip pri', textContent: t('save') }), no = el('button', { type: 'button', className: 'chip', textContent: '✕' });
  no.setAttribute('aria-label', t('cancel'));
  const save = async () => {
    try { const r = await (await fetch('run_note', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ key: e.key || e.from, text: inp.value }) })).json(); if (!r.ok) throw new Error(r.error || 'error'); }
    catch (er) { alert(t('saveerr') + ' ' + er.message); return; }
    loadRun();
  };
  ok.onclick = save; no.onclick = () => loadRun();
  inp.addEventListener('keydown', ev => { if (ev.key === 'Enter') { ev.preventDefault(); save(); } if (ev.key === 'Escape') loadRun(); });
  const b = row.querySelector('.rnbtn'); if (b) b.hidden = true;
  f.append(inp, ok, no); row.appendChild(f); inp.focus();
}
function ringSVG(pct, size, stroke, color, inner) {
  const r = (size - stroke) / 2, c = 2 * Math.PI * r, p = Math.max(0, Math.min(100, pct));
  return `<svg viewBox="0 0 ${size} ${size}"><circle cx="${size / 2}" cy="${size / 2}" r="${r}" fill="none" stroke="${NC.l2}" stroke-width="${stroke}"/>
    <circle cx="${size / 2}" cy="${size / 2}" r="${r}" fill="none" stroke="${color}" stroke-width="${stroke}" stroke-linecap="round"
      stroke-dasharray="${(c * p / 100).toFixed(1)} ${c.toFixed(1)}" transform="rotate(-90 ${size / 2} ${size / 2})"/>${inner || ''}</svg>`;
}
const scoreColor = p => p >= 95 ? NC.acc : p >= 85 ? NC.warn : NC.red;
function renderNight() {
  const d = NV.data; if (!d) return;
  const s = new Date(d.start), e = new Date(d.end), L = locale();
  document.querySelectorAll('#nper button').forEach(b => b.classList.toggle('on', b.dataset.p === NV.per));
  $('ndate').hidden = NV.per === 'free'; $('nfree').hidden = NV.per !== 'free';
  if (NV.per === 'free') { $('nfrom').value = NV.from || ''; $('nto').value = NV.to || ''; }
  const rg = perRange(), qs = perQuery() || '';
  $('nday').textContent = NV.per === 'win' || NV.per === 'today' || NV.per === 'yest' ? s.toLocaleDateString(L, { weekday: 'long' }) : t('per_' + NV.per);
  const e1 = new Date(e.getTime() - 1);
  const whole = !s.getHours() && !s.getMinutes() && !e.getHours() && !e.getMinutes() && e - s >= 86e6;   // ohne Erfassungszeit: ganzer Tag
  if (rg) $('nrange').textContent = (isoDay(s) === isoDay(e1) ? s.toLocaleDateString(L, { day: 'numeric', month: 'long', year: 'numeric' }) :
    s.toLocaleDateString(L, { day: 'numeric', month: 'long' }) + ' – ' + e1.toLocaleDateString(L, { day: 'numeric', month: 'long', year: 'numeric' })) + (e > new Date() ? ' · ' + t('n_running') : '');
  else $('nrange').textContent = (whole ? s.toLocaleDateString(L, { day: 'numeric', month: 'long', year: 'numeric' }) + ' · ' + t('n_wholeday') :
    s.toLocaleDateString(L, { day: 'numeric', month: 'long' }) + ' – ' + e.toLocaleDateString(L, { day: 'numeric', month: 'long', year: 'numeric' }) +
    ' · ' + pad(s.getHours()) + ':' + pad(s.getMinutes()) + '\u2060–\u2060' + pad(e.getHours()) + ':' + pad(e.getMinutes())) + (e > new Date() ? ' · ' + t('n_running') : '');
  $('ndate').value = d.date;
  $('nnext').disabled = e > new Date();
  $('nsvg').href = 'night.svg?date=' + d.date + '&' + qs;
  $('nsvg').setAttribute('download', 'laerm_' + (rg ? rg[0].slice(0, 10) + '_' + isoDay(e1) : d.date) + '.svg');
  { let pr = {}; try { pr = JSON.parse(localStorage.getItem('laerm_proto') || '{}'); } catch (x) { }   // Lärmprotokoll für genau diese Auswahl
    const pp = { from: isoDay(s), to: isoDay(e1), src: NV.src || 'all', list: PV.cur || '', all: '1', name: pr.name || '', addr: pr.addr || '', flat: pr.flat || '' };
    $('plproto').href = 'protokoll.html?' + new URLSearchParams(Object.fromEntries(Object.entries(pp).filter(([, v]) => v))).toString(); }
  $('nweek').hidden = NV.per !== 'win';
  // Quellen-Auswahl
  const sel = $('nsrc'), opts = [['all', t('all_sources')]].concat(viewSources().map(x => [x.id, viewName(x.id)])), key = JSON.stringify(opts);
  if (sel.dataset.k !== key) { sel.dataset.k = key; sel.innerHTML = opts.map(([v, l]) => `<option value="${esc(v)}">${esc(l)}</option>`).join(''); }
  if (!opts.some(o => o[0] === NV.src)) NV.src = 'all';
  sel.value = NV.src; sel.closest('label').style.display = SOURCES.length > 1 ? '' : 'none';
  // Wochenleiste
  $('nweek').innerHTML = (NV.week || []).map(n => {
    const wd = parseDay(n.date).toLocaleDateString(L, { weekday: 'short' }).replace('.', '').slice(0, 2);
    const ok = n.data && n.quiet_pct != null, col = ok ? scoreColor(n.quiet_pct) : NC.l3;
    return `<button class="nwd${n.date === d.date ? ' sel' : ''}${n.data ? '' : ' nod'}" data-d="${n.date}" title="${esc(n.date)} · ${n.count} ${esc(t('n_count'))}">
      ${ringSVG(ok ? n.quiet_pct : 0, 44, 5, col, `<text x="22" y="26" text-anchor="middle" font-size="12" font-weight="700" fill="${n.date === d.date ? NC.tx : NC.mut}">${esc(wd)}</text>${n.date === d.date ? '<circle cx="22" cy="22" r="20.5" fill="none" stroke="${NC.tx}" stroke-width="1"/>' : ''}`)}
      <span>${n.count}</span></button>`;
  }).join('');
  $('nweek').querySelectorAll('.nwd').forEach(b => b.onclick = () => { NV.date = b.dataset.d; loadNight(); });
  // Zusammenfassung
  const sm = d.summary, has = d.levels.length || d.events.length, hasQ = sm.quiet_pct != null;
  $('nring').innerHTML = ringSVG(hasQ ? sm.quiet_pct : 0, 150, 14, hasQ ? scoreColor(sm.quiet_pct) : NC.l3,
    `<text x="75" y="76" text-anchor="middle" font-size="34" font-weight="800" fill="${NC.tx}">${hasQ ? Math.round(sm.quiet_pct) : '–'}<tspan font-size="16">${hasQ ? ' %' : ''}</tspan></text>
     <text x="75" y="100" text-anchor="middle" font-size="13" fill="${NC.mut}">${esc(t('n_quiet'))}</text>`);
  const fm = m => m >= 60 ? Math.floor(m / 60) + 'h ' + pad(Math.round(m % 60)) + 'm' : Math.round(m) + ' min';
  const nd = !has;                                  // leere Nacht: keine Nullwerte vortaeuschen
  $('nstats').innerHTML = [[nd ? '–' : sm.count, t('n_count')], [nd ? '–' : fm(sm.disturbed_min), t('n_dist')], [sm.longest_quiet_min != null ? fm(sm.longest_quiet_min) : '–', t('n_longest')],
    [t('n_rec_of', { a: numTxt((sm.recorded_min / 60).toFixed(1).replace(/\.0$/, '')), b: Math.round(sm.minutes / 60) }), t('n_recorded')],
    [sm.loudest != null ? sm.loudest.toFixed(0) + ' dBFS' : '–', t('n_loudest') + (sm.loudest_at ? ' · ' + sm.loudest_at : '')],
    [nd ? '–' : sm.event_s >= 60 ? fm(sm.event_s / 60) : sm.event_s.toFixed(1) + ' s', t('n_evtime')]]
    .map(([v, l], i) => `<div><b style="color:${i === 0 && v > 0 ? NC.warn : NC.tx}">${esc(v)}</b><span>${esc(l)}</span></div>`).join('') +
    (sm.arts && Object.keys(sm.arts).length ? `<div class="narts">${Object.entries(sm.arts).sort((a, b) => b[1] - a[1]).map(([g, n]) => `<span class="art a-${g}">${ART_ICON[g] || '❓'} ${esc(artName(g))} <small>${n}×</small></span>`).join('')}</div>` : '');
  // Die Störungen stehen in der Tabelle unten (gleicher Datensatz)
  const nn = d.events.flatMap(ev => (ev.notes || []).map(n => [ev, n])), fl = d.fnotes || [];
  $('nnotes').hidden = !nn.length && !fl.length;
  $('nnotes').innerHTML = nn.length ? `<h3>${esc(t('nt_night', { n: nn.length }))}</h3>` + nn.map(([ev, n], i) => `<div class="ntrow" data-i="${i}" tabindex="0"><span class="ntnum" style="background:${noteCol(n)}">📝</span><span class="ntoff" data-clk=" · ${esc(ev.name)}">${esc(n.clock)}</span><span class="ntclk">${esc(ev.name)}</span><span class="nttx">${(n.tags || []).map(ntTag).join('')}${n.text ? `<span class="ntt">${esc(n.text)}</span>` : ''}${n.witness ? `<span class="ntw">👤 ${esc(n.witness)}</span>` : ''}</span><span class="ntact">▶</span></div>`).join('') : '';
  $('nnotes').querySelectorAll('.ntrow').forEach(r => { const [ev, n] = nn[+r.dataset.i]; r.onclick = () => { if (ev.k) openEvent(ev.k, n.off); }; });
  if (fl.length) {                                   // freie Notizen: Klick springt im Verlauf hin, ✎ bearbeitet
    const nm = id => id === 'all' ? t('all_sources') : viewName(id);
    const h3 = `<h3>📝 ${esc(t('fn_list', { n: fl.length }))}</h3>`, box = el('div'); box.innerHTML = h3 + fl.map((n, i) => `<div class="ntrow fnr" data-i="${i}" tabindex="0"><span class="ntnum" style="background:#7048e8">📝</span><span class="ntoff">${esc(fmtDay(n.date))}</span><span class="ntclk">${esc(n.clock)}${n.to ? '–' + esc(n.clock_to) : ''}${n.rz ? ' 🌙' : ''} · ${esc(nm(n.src || 'all'))}</span><span class="nttx">${(n.tags || []).map(ntTag).join('')}${n.text ? `<span class="ntt">${esc(n.text)}</span>` : ''}${n.witness ? `<span class="ntw">👤 ${esc(n.witness)}</span>` : ''}</span><span class="ntact fned" title="${esc(t('nt_edit'))}">✎</span></div>`).join('');
    $('nnotes').prepend(...box.childNodes);
    $('nnotes').querySelectorAll('.fnr').forEach(r => { const n = fl[+r.dataset.i]; r.onclick = e => { if (e.target.closest('.fned')) { fnOpen(n); return; }
      DT.mark = [n.a, Math.max(n.b, n.a + 1000)]; DT.from = n.a - 120000; DT.to = Math.max(n.b, n.a) + 120000; dtLoad(DT, true); $('ndaybox').scrollIntoView({ behavior: 'smooth', block: 'start' }); }; });
  }
  const mo = (d.motion || []).filter(m => !SHIDE.has(m.kind));                        // Handys als Bewegungsmelder: Erschütterung / Bewegung im Bild
  if (mo.length) {
    const nm = id => viewName(id), box = el('div');
    box.innerHTML = `<h3>🫨 ${esc(t('mot_list', { n: mo.length }))}</h3>` + mo.map((m, i) => { const a = new Date(m.a), b = new Date(m.b), L = locale();
      return `<div class="ntrow mor" data-i="${i}" tabindex="0"><span class="ntnum" style="background:${m.kind === 'vib' ? '#e8590c' : '#1c7ed6'}">${m.kind === 'vib' ? '🫨' : '🏃'}</span><span class="ntoff">${esc(a.toLocaleDateString(L, { day: '2-digit', month: '2-digit' }))}</span><span class="ntclk">${esc(a.toLocaleTimeString(L))}–${esc(b.toLocaleTimeString(L))} · ${esc(nm(m.src))}</span><span class="nttx"><span class="ntt">${esc(t(m.kind === 'vib' ? 'mot_vib' : 'mot_cam'))} · ${esc(fmtDur(Math.max(0, (m.b - m.a) / 1000)))} · ${esc(t('mot_peak'))} ${esc(m.kind === 'vib' ? f2(m.peak) + ' m/s²' : f1(m.peak) + ' %')}${m.open ? ' · ' + esc(t('mot_open')) : ''}</span></span></div>`; }).join('');
    $('nnotes').hidden = false; $('nnotes').append(...box.childNodes);
    $('nnotes').querySelectorAll('.mor').forEach(r => { const m = mo[+r.dataset.i]; r.onclick = () => { DT.mark = [m.a, Math.max(m.b, m.a + 1000)]; DT.from = m.a - 120000; DT.to = Math.max(m.b, m.a) + 120000; dtLoad(DT, true); $('ndaybox').scrollIntoView({ behavior: 'smooth', block: 'start' }); }; });
  }
  haListRender();
  drawNight();
}
/* Liste „Sensoren aus Home Assistant im Zeitraum“ – eigenes Panel, standardmäßig ausgeblendet; optional nur sichtbarer Bereich */
function haListRender() {
  const d = NV.data || {}, box0 = $('nhalist'); if (!box0) return; box0.innerHTML = '';
  const hl = (d.ha || []).filter(x => !SHIDE.has('ha:' + x[2]) && (!dashVis('ha') || (x[1] >= DT.from && x[0] <= DT.to)));                             // Sensoren aus Home Assistant (Regeln „nur festhalten“)
  if (hl.length) {
    const box = el('div'), L = locale();
    box.innerHTML = `<h3>📡 ${esc(t('ha_list', { n: hl.length }))}</h3>` + hl.map((x, i) => { const dur = Math.max(0, (x[1] - x[0]) / 1000);
      return `<div class="ntrow har" data-i="${i}" data-a="${x[0]}" tabindex="0"><span class="ntnum" style="background:#1c7ed6">📡</span><span class="ntoff">${esc(new Date(x[0]).toLocaleDateString(L, { day: '2-digit', month: '2-digit' }))}</span><span class="ntclk">${esc(hms(x[0]))}–${esc(hms(x[1]))}</span><span class="nttx"><span class="ntt"><b>${esc(x[2])}</b> ${esc(t('ha_on'))} · ${esc(dur < 120 ? Math.round(dur) + ' s' : dur < 7200 ? Math.round(dur / 60) + ' min' : Math.floor(dur / 3600) + ' h ' + Math.round(dur % 3600 / 60) + ' min')}</span>${x[4] ? `<span class="ntt hant">📝 ${esc(x[4])}</span>` : ''}</span><span class="ntact hanote" title="${esc(t('ha_note'))}">✎</span></div>`; }).join('');
    box0.append(...box.childNodes);
    box0.querySelectorAll('.har').forEach(r => { const x = hl[+r.dataset.i]; r.onclick = e => {
      if (e.target.closest('.hanote')) { haPop({ a: x[0], b: x[1], name: x[2], rid: x[3], note: x[4] || '' }); return; }
      DT.mark = [x[0], Math.max(x[1], x[0] + 1000)]; DT.from = x[0] - 120000; DT.to = Math.max(x[1], x[0]) + 120000; dtLoad(DT, true); $('ndaybox').scrollIntoView({ behavior: 'smooth', block: 'start' }); }; });
  }
}
function nightGeom(cv) {
  fit(cv);
  const d = DPR(), w = cv.width, h = cv.height, L = 58 * d, R = 14 * d;
  return { d, w, h, L, R, pw: w - L - R };
}
function smoothLevels(lv) {
  const out = [];
  for (let i = 0; i < lv.length; i++) {
    let s = 0, n = 0;
    for (let k = Math.max(0, i - 2); k <= Math.min(lv.length - 1, i + 2); k++) if (lv[k][1] != null && Math.abs(lv[k][0] - lv[i][0]) <= 2) { s += lv[k][1]; n++; }
    out.push([lv[i][0], n ? s / n : null, lv[i][2], lv[i][3]]);
  }
  return out;
}
function curve(c, pts) {                      // weiche Kurve (Catmull-Rom -> Bezier)
  c.moveTo(pts[0][0], pts[0][1]);
  for (let i = 0; i < pts.length - 1; i++) {
    const p0 = pts[Math.max(0, i - 1)], p1 = pts[i], p2 = pts[i + 1], p3 = pts[Math.min(pts.length - 1, i + 2)];
    c.bezierCurveTo(p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6, p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6, p2[0], p2[1]);
  }
}
function drawNight() {
  if (!$('ncv').offsetParent) return;                // Minutenkurve ist im Reiter Protokolle durch den Verlauf ersetzt
  const nd = NV.data; if (!nd || !NV.open) return;
  const cv = $('ncv'), g = nightGeom(cv), c = cv.getContext('2d'), { d, w, h, L, pw } = g, T = 26 * d, B = 8 * d, ph = h - T - B;
  const total = Math.max(1, nd.minutes), X = m => L + pw * m / total;
  const lv = smoothLevels(nd.levels);
  const vals = []; lv.forEach(r => { if (r[1] != null) vals.push(r[1]); if (r[2] != null) vals.push(r[2]); }); nd.events.forEach(e => { if (e.peak != null) vals.push(e.peak); });
  let lo = vals.length ? Math.floor((Math.min(...vals) - 5) / 10) * 10 : -100, hi = vals.length ? Math.ceil((Math.max(...vals) + 5) / 10) * 10 : -20;
  if (hi - lo < 30) hi = lo + 30;
  const Y = v => T + ph * (1 - (v - lo) / (hi - lo));
  c.clearRect(0, 0, w, h);
  c.font = (11 * d) + 'px system-ui'; c.textAlign = 'right'; c.lineWidth = 1;
  const ng = dbTicks(lo, hi, ph, 22);
  drawDbGrid(c, ng.ticks.map(k => { const y = Y(k.v); return { y, major: k.major, text: (y < T + 12 * d || y > T + ph - 12 * d) ? null : ng.fmt(k.v) }; }), L, pw, d, true, NC.l2, NC.mut);   // Platz fuer laut/ruhig
  c.textAlign = 'left'; c.fillStyle = NC.mut; c.font = '600 ' + (11 * d) + 'px system-ui';
  c.fillText(t('n_loud'), 4 * d, T + 4 * d); c.fillText(t('n_calm'), 4 * d, T + ph - 2 * d);
  // Stundenlinien
  const s0 = new Date(nd.start);
  const qMin = pw / d / (total / 60) > 90 ? 15 : 30;          // Zwischenlinien je nach Breite alle 15 bzw. 30 min
  c.strokeStyle = NC.l1;
  for (const m of hourMarks(s0, total, qMin)) { const x = Math.round(X(m)) + .5; c.beginPath(); c.moveTo(x, T); c.lineTo(x, T + ph); c.stroke(); }
  c.strokeStyle = NC.l2;
  for (const m of hourMarks(s0, total)) { const x = Math.round(X(m)) + .5; c.beginPath(); c.moveTo(x, T); c.lineTo(x, T + ph); c.stroke(); }
  // Segmente ohne Luecken > 3 min
  const segs = []; let seg = null, last = null;
  for (const r of lv) { if (r[1] == null) continue; if (last != null && r[0] - last > 3) seg = null; if (!seg) { seg = []; segs.push(seg); } seg.push([X(r[0]), Y(r[1])]); last = r[0]; }
  const grad = c.createLinearGradient(0, T, 0, T + ph); grad.addColorStop(0, ca(NC.acc, .5)); grad.addColorStop(1, ca(NC.acc, .02));
  for (const sg of segs) {
    if (sg.length < 2) continue;
    c.beginPath(); curve(c, sg); c.lineTo(sg[sg.length - 1][0], T + ph); c.lineTo(sg[0][0], T + ph); c.closePath(); c.fillStyle = grad; c.fill();
    c.beginPath(); curve(c, sg); c.strokeStyle = NC.acc; c.lineWidth = 2.4 * d; c.lineJoin = 'round'; c.stroke();
  }
  // Spitzen (duenn)
  c.beginPath(); last = null;
  for (const r of nd.levels) { if (r[2] == null) { last = null; continue; } const x = X(r[0]), y = Y(r[2]); if (last == null || r[0] - last > 3) c.moveTo(x, y); else c.lineTo(x, y); last = r[0]; }
  c.strokeStyle = ca(NC.acc, .35); c.lineWidth = 1 * d; c.stroke();
  // Schwelle
  const thr = nd.levels.map(r => r[3]).filter(v => v != null).sort((a, b) => a - b);
  if (thr.length) { const tv = thr[thr.length >> 1], y = Y(tv); c.setLineDash([8 * d, 5 * d]); c.strokeStyle = NC.warn; c.lineWidth = 1.6 * d; c.beginPath(); c.moveTo(L, y); c.lineTo(L + pw, y); c.stroke(); c.setLineDash([]);
    c.textAlign = 'left'; lblBox(c, t('threshold') + ' ' + tv.toFixed(1), L + 6 * d, y - 6 * d, NC.warn, d); }
  if (NV.src && NV.src !== 'all') drawRefs(c, curRefs(NV.src), v => [Y(v)], lo, hi, L, pw, T, ph, d);
  // Ereignis-Markierungen in der Kurve
  for (const e of nd.events) { const x = X(e.o); c.strokeStyle = ca(NC.red, .35); c.lineWidth = 1 * d; c.beginPath(); c.moveTo(x, T); c.lineTo(x, T + ph); c.stroke(); }
  // Hover
  const hv = NV.hover;
  if (hv != null) {
    const m = (hv * d - L) / pw * total;
    if (m >= 0 && m <= total) {
      const x = X(m); c.strokeStyle = NC.l3; c.lineWidth = 1 * d; c.beginPath(); c.moveTo(x, T - 6 * d); c.lineTo(x, T + ph); c.stroke();
      let best = null; for (const r of lv) if (r[1] != null && (!best || Math.abs(r[0] - m) < Math.abs(best[0] - m))) best = r;
      if (best && Math.abs(best[0] - m) < 4) { c.fillStyle = NC.tx; c.beginPath(); c.arc(X(best[0]), Y(best[1]), 4 * d, 0, 7); c.fill(); }
      const tm = new Date(s0.getTime() + m * 60000), near = nearEvent(m, 6 * total / (pw / d));
      const b = $('nbubble'); b.style.display = 'block';
      b.innerHTML = `<b>${pad(tm.getHours())}:${pad(tm.getMinutes())}</b> · ${best && best[1] != null ? best[1].toFixed(1) + ' dBFS' : '–'}` +
        (near ? ` · <span style="color:${NC.red}">${esc(near.name)} ${esc(fmtDur(near.dur))}${near.file ? ' ▶' : ''}</span>` : '');
      const bw = b.offsetWidth, cw = cv.clientWidth; b.style.left = clamp(hv, bw / 2 + 2, Math.max(bw / 2 + 2, cw - bw / 2 - 2)) + 'px';
    }
  } else $('nbubble').style.display = 'none';
  drawTrack(total, s0);
}
function hourMarks(s0, total, stepMin) {   // volle Stunden (bzw. Viertelstunden) in echter Zeit (bei Zeitumstellung doppelt bzw. ausgelassen)
  const ms = (stepMin || 60) * 60000, out = [], t0 = s0.getTime(); let h = Math.ceil(t0 / ms) * ms;
  for (; (h - t0) / 60000 <= total; h += ms) out.push((h - t0) / 60000);
  return out;
}
function nearEvent(m, tol) { let best = null; for (const e of NV.data.events) { const dm = Math.abs(e.o - m); if (dm <= tol && (!best || dm < Math.abs(best.o - m))) best = e; } return best; }
function drawTrack(total, s0) {
  const cv = $('ntrack'), g = nightGeom(cv), c = cv.getContext('2d'), { d, w, h, L, pw } = g, mid = 30 * d;
  const X = m => L + pw * m / total;
  c.clearRect(0, 0, w, h);
  c.fillStyle = NC.mut; c.font = '600 ' + (11 * d) + 'px system-ui'; c.textAlign = 'left'; { const lt = t('n_events'), fits = 4 * d + c.measureText(lt).width + 6 * d <= L; c.fillText(lt, 4 * d, fits ? mid + 4 * d : mid - 12 * d); }   // passt der Text nicht vor die Linie (Handy), steht er darueber
  c.strokeStyle = NC.l2; c.lineWidth = 1 * d; c.beginPath(); c.moveTo(L, mid); c.lineTo(L + pw, mid); c.stroke();
  NV.hits = [];
  const peaks = NV.data.events.map(e => e.peak).filter(v => v != null), plo = peaks.length ? Math.min(...peaks) - 3 : -90, phi = peaks.length ? Math.max(...peaks) : -20;
  NV.data.events.forEach((e, i) => {
    const x = X(e.o), wd = Math.max(4 * d, X(e.o + (e.dur || 0.02) / 60) - x), hh = (7 + 14 * Math.max(0, Math.min(1, ((e.peak ?? plo) - plo) / Math.max(1, phi - plo)))) * d;
    c.fillStyle = NC.red;
    c.beginPath(); if (c.roundRect) c.roundRect(x - wd / 2, mid - hh, wd, hh * 2, 2 * d); else c.rect(x - wd / 2, mid - hh, wd, hh * 2); c.fill();
    NV.hits.push({ x0: (x - wd / 2 - 6 * d) / d, x1: (x + wd / 2 + 6 * d) / d, i });
  });
  // Stunden
  c.fillStyle = NC.mut; c.font = (12 * d) + 'px system-ui'; c.textAlign = 'center';
  const perH = pw / d / (total / 60), ty = h - 26 * d;
  c.fillStyle = NC.l3;
  for (const m of hourMarks(s0, total, perH > 90 ? 15 : 30)) c.fillRect(Math.round(X(m)), ty, 1 * d, 3 * d);
  c.fillStyle = NC.mut;
  for (const m of hourMarks(s0, total)) {
    const tm = new Date(s0.getTime() + m * 60000), x = X(m);
    c.fillRect(Math.round(x), ty, 1 * d, 6 * d); c.fillText(pad(tm.getHours()) + (perH > 70 || tm.getMinutes() ? ':' + pad(tm.getMinutes()) : ''), x, h - 10 * d);
  }
}
function playEvent(i) {                                // Stoerung im Nachtbericht: Ansicht mit Ablauf oeffnen
  const e = NV.data.events[i];
  if (e && e.k) openEvent(e.k, null, true);
}
function initNight() {
  $('tab_live').onclick = () => showTab('live'); $('tab_prot').onclick = () => showTab('prot');
  try { const p = localStorage.getItem('laerm_per'); if (['win', 'today', 'yest', '7', '30', 'free'].includes(p)) NV.per = p; } catch (e) { }
  const step = k => {                               // ‹ ›: um einen ganzen Zeitraum weiter
    const n = NV.per === '7' ? 7 : NV.per === '30' ? 30 : NV.per === 'free' ? Math.round((parseDay(NV.to) - parseDay(NV.from)) / 864e5) + 1 : 1;
    const mv = ds => { const dd = parseDay(ds); dd.setDate(dd.getDate() + k * n); return isoDay(dd); };
    const lim = NV.per === 'win' ? nightDefault() : isoDay(new Date());
    if (NV.per === 'free') { const nt = mv(NV.to); if (nt > lim) return; NV.from = mv(NV.from); NV.to = nt; }
    else { const nd = mv(NV.date); if (nd > lim) return; NV.date = nd; }
    loadNight();
  };
  $('nprev').onclick = () => step(-1); $('nnext').onclick = () => step(1);
  $('ndate').onchange = e => { if (e.target.value) { const lim = NV.per === 'win' ? nightDefault() : isoDay(new Date()); NV.date = e.target.value > lim ? lim : e.target.value; loadNight(); } };
  $('nfrom').onchange = e => { if (e.target.value) { NV.from = e.target.value; loadNight(); } };
  $('nto').onchange = e => { if (e.target.value) { NV.to = e.target.value; loadNight(); } };
  document.querySelectorAll('#nper button').forEach(b => b.onclick = () => perSet(b.dataset.p));
  $('nsrc').onchange = e => { NV.src = e.target.value; loadNight(); };
  const cv = $('ncv');
  cv.addEventListener('pointermove', e => { NV.hover = e.clientX - cv.getBoundingClientRect().left; drawNight(); });
  cv.addEventListener('pointerleave', () => { NV.hover = null; drawNight(); });
  const pick = (cvx, e) => {
    const x = e.clientX - cvx.getBoundingClientRect().left;
    let hit = NV.hits.find(hh => x >= hh.x0 && x <= hh.x1);
    if (!hit && cvx === cv && NV.data) { const g = nightGeom(cv); const m = (x * g.d - g.L) / g.pw * NV.data.minutes; const ne = nearEvent(m, 6 * NV.data.minutes / (g.pw / g.d)); if (ne) hit = { i: NV.data.events.indexOf(ne) }; }
    if (hit) playEvent(hit.i);
  };
  $('ntrack').addEventListener('click', e => pick($('ntrack'), e)); cv.addEventListener('click', e => pick(cv, e));
  window.addEventListener('resize', () => { if (NV.open) drawNight(); });
  perSet(NV.per, true);                              // gemerkter Zeitraum (z. B. Gestern) gilt auch beim Öffnen
  let tab = 'live'; try { tab = localStorage.getItem('laerm_tab') || 'live'; } catch (e) { }
  if (tab === 'night' || tab === 'prot') showTab(tab);
}

async function init() {
  applyTheme(); readColors(); buildLUT();
  try { const r = await (await fetch('settings', { cache: 'no-store' })).json(); CUR = r.settings; SRC = r.sources || []; SCHED = r.schedule || []; if (r.pro && r.pro.state) PRO = r.pro; } catch (e) { }
  pickLang(CUR && CUR.language); dashInit(); tr(); setLive(true); syncRec(null); initHelp();
  proBanner(); setInterval(proLoad, 6 * 3600 * 1000);
  bindCanvas($('main'), false); bindCanvas($('spec'), true);
  $('livebtn').addEventListener('click', () => setLive(!view.live));
  $('vidrot').onclick = vidRotate; $('vidsz').onclick = vidSize; $('vidfs').onclick = vidFull; $('vidframe').onclick = vidFull;
  for (const [id, k] of [['vidrot', 'vid_rot_tip'], ['vidsz', 'vid_size_tip'], ['vidfs', 'vid_full_tip']]) { $(id).title = t(k); $(id).setAttribute('aria-label', t(k)); }
  document.addEventListener('fullscreenchange', vidLayout); addEventListener('resize', () => { if (!$('vidlive').hidden) vidLayout(); });
  $('golive').addEventListener('click', goLive);
  $('themebtn').onclick = () => { THEME = THEME === 'auto' ? 'light' : THEME === 'light' ? 'dark' : 'auto'; try { localStorage.setItem('laerm_theme', THEME); } catch (e) { } applyTheme(); readColors(); if (NV.open) drawNight(); };
  setInterval(() => { if (THEME === 'auto') applyTheme(); }, 4000);
  $('laybtn').onclick = e => buildLayerPop(e.currentTarget); $('evlay').onclick = e => buildLayerPop(e.currentTarget);
  $('classrange').addEventListener('click', classifyRange);
  $('chkopen').onclick = () => $('chkdlg').showModal(); $('chkx').onclick = () => $('chkdlg').close();
  $('chkdlg').addEventListener('close', () => { $('chkaudio').pause(); });
  $('chkfile').onchange = e => { checkFile(e.target.files[0]); e.target.value = ''; };
  { const af = $('artflt'); for (const [v, l] of [['', t('art_all')], ['_notes', '📝 ' + t('nt_with')], ...ART_ORDER.map(g => [g, ART_ICON[g] + ' ' + artName(g)]), ['_none', t('art_none')]]) option(af, v, l); af.onchange = () => { ARTSEL.clear(); if (af.value) ARTSEL.add(af.value); artApply(); }; artMsBuild(); }
  $('notesopen').onclick = openAllNotes; ntaBind();
  $('recbtn').addEventListener('click', e => { e.stopPropagation(); toggleRec(); });
  $('tileplay').onclick = () => {
    if (rotActive()) { TILE.on = false; } else { TILE.on = true; TILE.manual = false; }
    try { localStorage.setItem('laerm_tileshow', TILE.on ? '1' : '0'); } catch (e) { }
    TILE.at = Date.now(); tileBar(); evFollow();
  };
  $('tileset').onclick = e => { e.stopPropagation(); tileSetPop(); };
  setInterval(tileTick, 1000);
  $('hbbtn').onclick = () => hbOpen('');
  $('hmore').onclick = toggleHMenu; placeHeader(); MOBILE.addEventListener('change', placeHeader);
  $('evx').onclick = () => $('evdlg').close();
  $('enote').addEventListener('blur', enoteSave);
  $('evdlg').addEventListener('close', () => { if (NV.open) setTimeout(loadNight, 300); });   // Notizen/Listen geaendert: Protokolle auffrischen
  $('evdlg').addEventListener('close', () => { enoteSave(); if (EVV.a) EVV.a.pause(); $('evvid').pause(); $('evaudio').pause(); cancelAnimationFrame(EVV.raf); lbPopClose(); $('sgpop').hidden = true; EVV.sel = null; });
  $('evvid').addEventListener('click', () => $('evplay').click());
  $('evplay').onclick = () => { if (!EVV.a) return; if (EVV.a.paused) { if (EVV.snd && EVV.a.currentTime < 0.05) EVV.a.currentTime = EVV.aOff || 0; EVV.a.play(); } else EVV.a.pause(); };   // mit Ton: am Anfang der Aufnahme beginnen, nicht im stillen Umfeld
  $('evcv').addEventListener('click', evSeek); $('evsp').addEventListener('click', evSeek); ntBind(); lbBind();
  $('lbsave').onclick = lbSave; $('lbcancel').onclick = () => { lbPopClose(); EVV.sel = null; evDraw(); };
  $('lbname').onkeydown = e => { if (e.key === 'Enter') { e.preventDefault(); lbSave(); } if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); $('lbcancel').click(); } };
  $('sgpop').addEventListener('keydown', e => { if (e.key === 'Escape') { e.stopPropagation(); $('sgpop').hidden = true; } });
  document.addEventListener('pointerdown', e => { if (!e.target.closest('#sgpop,#evcv')) $('sgpop').hidden = true; });
  $('simx').onclick = () => $('simdlg').close();
  window.addEventListener('resize', () => { if ($('evdlg').open) evDraw(); });
  document.addEventListener('keydown', e => {            // Taste Ende oder L = zurueck zu Live
    if (e.target.closest && e.target.closest('input,select,textarea,dialog')) return;
    if ((e.key === 'End' || e.key === 'l' || e.key === 'L') && !NV.open && !e.ctrlKey && !e.metaKey && !e.altKey) { goLive(); e.preventDefault(); }
  });
  $('m_level').onclick = () => { setMode('level'); if (histOn()) dtLoad(LDT, true); }; $('m_wave').onclick = () => { setMode('wave'); if (histOn()) dtLoad(LDT, true); };
  $('span').onchange = e => { const v = parseFloat(e.target.value); if (!e.target.selectedOptions[0].dataset.cus) view.preset = v; setSpan(v); };
  $('zin').onclick = () => zoomY(1 / 1.3);
  $('zout').onclick = () => zoomY(1.3);
  $('zauto').onclick = () => { yv.auto = !yv.auto; syncAutoBtn(); };
  $('sbtn').onclick = openSettings; $('ssave').onclick = saveSettings; $('calbtn').onclick = calibrate;
  // Schliessen mit ungespeicherten Aenderungen: nachfragen (auch bei Escape)
  const closeSettings = () => { if (formDirty && !confirm(t('unsaved_q'))) return; formDirty = false; $('dlg').close(); };
  $('scancel').onclick = closeSettings; $('sx').onclick = closeSettings;
  $('dlg').addEventListener('keydown', e => { if (e.key === 'Escape' && formDirty) { e.preventDefault(); e.stopPropagation(); closeSettings(); } });
  $('dlg').addEventListener('cancel', e => { if (formDirty) e.preventDefault(); });
  $('diagbox').addEventListener('toggle', () => { diagT = 0; loadDiag(); });
  document.addEventListener('keydown', e => { if (e.key === ' ' && !$('dlg').open && e.target === document.body) { e.preventDefault(); setLive(!view.live); } });
  setSpan(60); setMode('level');
  { // Anzahl: feste Werte oder eigene Zahl (1-5000)
    const sel = $('evn'), inp = $('evnc');
    const setN = n => { EVN = n; try { localStorage.setItem('laerm_evn', EVN); } catch (e) { } loadEvents(); };
    const show = () => { sel.value = String(EVN); const fixed = sel.value === String(EVN); if (!fixed) sel.value = 'c'; inp.hidden = sel.value !== 'c'; inp.value = EVN || ''; };
    show();
    sel.onchange = () => { if (sel.value === 'c') { inp.hidden = false; inp.value = EVN || 200; inp.focus(); inp.select(); } else { inp.hidden = true; setN(+sel.value); } };
    const take = () => { const n = Math.round(+inp.value); if (!(n >= 1)) { inp.value = EVN || ''; return; } const v = Math.min(5000, n); inp.value = v; if (v !== EVN) setN(v); };
    inp.onchange = take; inp.onkeydown = e => { if (e.key === 'Enter') { e.preventDefault(); take(); inp.blur(); } };
  }
  $('plmove').onchange = async e => { const id = e.target.value; e.target.value = ''; if (!id) return; const keys = selectedKeys(); if (!keys.length) return;
    try { await plPost('plist_mem', { id, keys, add: true }); $('artstat').textContent = t('pl_added', { n: keys.length, l: plName(id) }); } catch (x) { alert(t('saveerr')); } };
  $('pladd').onclick = () => plFormOpen('add'); $('plren').onclick = () => plFormOpen('ren'); $('plok').onclick = plFormOk; $('plcancel').onclick = () => { $('plform').hidden = true; };
  $('plname').onkeydown = e => { if (e.key === 'Enter') plFormOk(); else if (e.key === 'Escape') $('plform').hidden = true; };
  $('nplist').onchange = () => { PV.cur = $('nplist').value; try { localStorage.setItem('laerm_plist', PV.cur); } catch (e) { } plRefresh(); loadNight(); };
  $('pldel').onclick = async () => { if (!PV.cur || !confirm(t('pl_del_q', { n: plName(PV.cur) }))) return; try { await plPost('plist_del', { id: PV.cur }); PV.cur = ''; plRefresh(); loadNight(); } catch (e) { alert(t('saveerr')); } };
  $('plrmsel').onclick = async () => { const keys = selectedKeys(); if (!PV.cur || !keys.length) return; try { await plPost('plist_mem', { id: PV.cur, keys, add: false }); loadNight(); } catch (e) { alert(t('saveerr')); } };
  $('plnote').addEventListener('blur', plNoteSave);
  plFetch();
  $('artsel').onclick = () => recheckEvents([...SEL].map(k => (EV.events.find(r => ek(r) === k) || {}).datei).filter(Boolean));
  $('delsel').onclick = () => deleteEvents(selectedKeys()); $('delnone').onclick = () => { SEL.clear(); evSelToggle([], false); }; $('srcadd').onclick = () => { openSettings().then(() => { const b = openSec('srcbox'); if (b) b.scrollIntoView(); }); };
  $('qx').onclick = () => $('qrdlg').close();
  await loadSources(); setInterval(() => { if (!document.hidden) loadSources(); }, 2000);
  setInterval(() => { if (NV.open && !document.hidden) { loadEvents(); if (DT.from == null && !DT.drag && NV.data && new Date(NV.data.end).getTime() > nowServer()) dtLoad(DT, true); } }, 60000);   // laufender Tag: Verlauf wächst rechts mit
  initNight(); initDayTrack(); initFn(); initLev(); diagApply();
  poll(); requestAnimationFrame(t0 => { lastFrame = t0; frame(t0); });
}
/* ================= Einpegeln der Geräte ================= */
const fmtStamp = iso => { if (!iso) return ''; const d = new Date(iso); return isNaN(d) ? iso : d.toLocaleDateString(locale(), { day: '2-digit', month: '2-digit', year: 'numeric' }) + ' ' + pad(d.getHours()) + ':' + pad(d.getMinutes()); };
const CALV = { timer: null, last: null };
function calBox() {
  const fs = el('fieldset', { id: 'calbox' }); fs.dataset.sec = 's_cal';
  const lg = el('legend', { textContent: t('s_cal') }); const ti = tipIcon('t_cal'); if (ti) lg.appendChild(ti); fs.appendChild(lg);
  fs.appendChild(el('small', { className: 'calhelp', textContent: t('h_cal') }));
  const r1 = el('div', { className: 'calrow' });
  let off = new Set(); try { off = new Set(JSON.parse(localStorage.getItem('laerm_caloff') || '[]')); } catch (e) { }   // abgewählte Geräte (pro Browser)
  const devs = el('div', { id: 'caldevs', className: 'caldevs' });
  devs.appendChild(el('span', { className: 'caldl', textContent: t('cal_devs') }));
  SOURCES.forEach(s => { const l = el('label', { className: 'chip' }), c = el('input', { type: 'checkbox', checked: !off.has(s.id) }); c.dataset.id = s.id;
    c.onchange = () => { c.checked ? off.delete(s.id) : off.add(s.id); try { localStorage.setItem('laerm_caloff', JSON.stringify([...off])); } catch (e) { } go.disabled = calIds().length < 2; };
    l.append(c, document.createTextNode(' ' + s.name)); devs.appendChild(l); });
  const calIds = () => [...devs.querySelectorAll('input:checked')].map(c => c.dataset.id);
  fs.appendChild(devs);
  const secs = el('select', { id: 'calsecs', title: t('cal_secs') }); for (const v of [10, 15, 30]) option(secs, v, v + ' s'); secs.value = '15';
  const go = el('button', { type: 'button', className: 'pri', id: 'calgo', textContent: t('cal_start') });
  const L = (txt, e) => { const l = el('label'); l.append(txt + ' ', e); return l; };
  r1.append(L(t('cal_secs'), secs), go); fs.appendChild(r1); go.disabled = calIds().length < 2;
  fs.appendChild(el('div', { id: 'calst', className: 'calst' }));
  fs.appendChild(el('div', { id: 'calres', className: 'calres' }));
  const r2 = el('div', { className: 'calrow', id: 'calact' }); r2.hidden = true;
  const note = el('input', { type: 'text', id: 'calnote', maxLength: 300, placeholder: t('cal_note_ph'), className: 'wide' });
  const ap = el('button', { type: 'button', className: 'pri', textContent: t('cal_apply') });
  const ck = el('button', { type: 'button', textContent: t('cal_check') });
  const ds = el('button', { type: 'button', textContent: t('cal_discard') });
  r2.append(note, ap, ck, ds); fs.appendChild(r2);
  fs.appendChild(el('div', { id: 'callog', className: 'callog' }));
  go.onclick = async () => {
    try { const r = await (await fetch('cal_start', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ secs: +secs.value, ids: calIds() }) })).json(); if (!r.ok) throw new Error(r.error); calPoll(); }
    catch (e) { $('calst').textContent = t('saveerr') + ' ' + e.message; }
  };
  const fin = async apply => {
    try {
      const r = await (await fetch('cal_apply', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ apply, note: note.value }) })).json();
      if (!r.ok) throw new Error(r.error);
      if (r.sources) SOURCES = r.sources;
      note.value = ''; buildSources(); $('calst').textContent = t(apply ? 'cal_done_apply' : 'cal_done_check');
    } catch (e) { $('calst').textContent = t('saveerr') + ' ' + e.message; }
  };
  ap.onclick = () => fin(true); ck.onclick = () => fin(false);
  ds.onclick = async () => { try { await fetch('cal_cancel', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' }); } catch (e) { } calPoll(); };
  setTimeout(calPoll, 0);
  return fs;
}
async function calPoll() {
  clearTimeout(CALV.timer);
  let c; try { c = await (await fetch('cal_status', { cache: 'no-store' })).json(); } catch (e) { return; }
  if (!$('calbox')) return;
  CALV.last = c;
  const st = $('calst'), go = $('calgo'), act = $('calact'), res = $('calres');
  const sec = x => Math.max(0, Math.ceil((x - c.now) / 1000));
  go.disabled = c.state === 'running' || document.querySelectorAll('#caldevs input:checked').length < 2; act.hidden = c.state !== 'done';
  if (c.state === 'running') {
    st.textContent = c.now < c.q1 ? t('cal_q', { s: sec(c.q1) }) : c.now < c.t0 ? t('cal_on', { s: sec(c.t0) }) : c.now < c.t1 ? t('cal_meas', { s: sec(c.t1) }) : t('cal_eval');
    st.className = 'calst run' + (c.now >= c.q1 && c.now < c.t0 ? ' go' : '');
    res.innerHTML = '';
    if ($('dlg').open) CALV.timer = setTimeout(calPoll, 400);
  } else if (c.state === 'done') {
    st.className = 'calst'; st.textContent = c.msg === 'few' ? t('cal_few') : t('cal_result') + (c.target != null ? ' ' + t('cal_target', { v: c.target.toFixed(1) }) : '');
    const nm = id => viewName(id);
    res.innerHTML = `<table class="caltab"><thead><tr><th>${esc(t('cmp_dev'))}</th><th>${esc(t('cal_th_quiet'))}</th><th>${esc(t('cal_th_lvl'))}</th><th>${esc(t('cal_th_dev'))}</th><th>${esc(t('cal_th_gain'))}</th></tr></thead><tbody>` +
      c.res.map(e => `<tr class="${e.ok ? '' : 'bad'}"><td>${esc(e.name || nm(e.id))}</td><td>${e.quiet != null ? e.quiet.toFixed(1) : '–'}</td><td>${e.level != null ? e.level.toFixed(1) : '–'}${e.std != null ? ' <small>±' + e.std.toFixed(1) + '</small>' : ''}</td>` +
        `<td>${e.ok ? (e.delta >= 0 ? '+' : '') + e.delta.toFixed(1) + ' dB' : esc(t('cal_bad_' + (e.why || 'nodata')))}</td><td>${e.ok && e.gain_new != null ? esc(String(e.gain_old)) + ' → <b>' + esc(String(e.gain_new)) + '</b> dB' : '–'}</td></tr>`).join('') + '</tbody></table>';
    act.querySelectorAll('button')[0].disabled = act.querySelectorAll('button')[1].disabled = c.msg === 'few';
  } else { st.className = 'calst'; if (!/✓|festgehalten|recorded/.test(st.textContent)) st.textContent = ''; res.innerHTML = ''; }
  const lg = $('callog');
  lg.innerHTML = c.log && c.log.length ? `<b>${esc(t('cal_log_head'))}</b>` + c.log.map(e => `<div>${esc(fmtStamp(e.at))} · ${esc(t(e.kind === 'apply' ? 'cal_kind_apply' : 'cal_kind_check'))} · ` +
    (e.res || []).map(x => esc(x.name) + ' ' + (x.ok ? (x.level != null ? x.level.toFixed(1) : '') + (e.kind === 'apply' && x.gain_new != null ? ' (' + x.gain_old + '→' + x.gain_new + ' dB)' : '') : '–')).join(' · ') + (e.note ? ' · ' + esc(e.note) : '') + '</div>').join('') : '';
}

/* ================= Vergleich der Geräte im Ereignis ================= */
function renderCmp(j) {
  const box = $('evcmp'); const c = j.cmp || []; EVV.cmp = null;
  if (c.length < 2) { box.hidden = true; box.innerHTML = ''; return; }
  const v = c.filter(x => x.peak != null).sort((a, b) => b.peak - a.peak), top = v.length ? v[0].peak : null;
  const lead = v.filter(x => top - x.peak < 1).map(x => x.name);
  box.hidden = false;
  box.innerHTML = `<h4 class="nthead">${esc(t('cmp_head'))}</h4><div class="cmplead">${esc(lead.length === 1 ? t('cmp_loudest', { n: lead[0] }) : t('cmp_equal', { n: lead.join(', ') }))}</div>` +
    `<table class="cmptab"><thead><tr><th>${esc(t('cmp_dev'))}</th><th>${esc(t('cmp_peak'))}</th><th>${esc(t('cmp_diff'))}</th><th>${esc(t('cmp_cal'))}</th></tr></thead><tbody>` +
    v.concat(c.filter(x => x.peak == null)).map(x => `<tr${x.peak === top ? ' class="top"' : ''}><td>${esc(x.name)}${x.own ? ' <small>(' + esc(t('cmp_trig')) + ')</small>' : ''}</td><td>${x.peak != null ? x.peak.toFixed(1) + ' dBFS' : '–'}</td>` +
      `<td>${x.peak != null ? (x.peak === top ? '–' : (x.peak - top).toFixed(1) + ' dB') : '–'}</td><td>${x.cal.ok ? '✓ ' + esc(fmtStamp(x.cal.at)) : x.cal.changed ? '⚠ ' + esc(t('cal_changed')) : esc(t('cal_none'))}</td></tr>`).join('') +
    `</tbody></table><div class="cmpcvs" id="cmpcvs"></div><small class="cmphint">${esc(t('cmp_hint'))}</small>`;
  const rows = c.map(x => ({ name: x.name, own: x.own, g: x.own ? EVV.g : x.graph })).filter(x => x.g && x.g.recs && x.g.recs.length);
  const wrap = $('cmpcvs');
  rows.forEach(x => { x.R = x.own ? EVV.d : evDecode(x.g); x.cv = el('canvas', { className: 'cmpcv' }); const lab = el('div', { className: 'cmplab', textContent: x.name }); wrap.append(lab, x.cv); });
  let hist = new Uint32Array(256), n = 0;                  // gemeinsame Farbskala: Lautstärken sind zwischen den Geräten vergleichbar
  rows.forEach(x => { const nb = x.R.nb || NB; for (const r of x.R) for (let k = 0; k < nb; k++) { hist[r.sp[k]]++; n++; } });
  const pct = q => { let a = 0; for (let v2 = 0; v2 < 256; v2++) { a += hist[v2]; if (a >= q * n) return v2; } return 255; };
  const lo = pct(0.05), hi = Math.max(pct(0.997), lo + 40);
  rows.forEach(x => {
    const R = x.R, nb = R.nb || NB, tc = document.createElement('canvas'); tc.width = R.length; tc.height = nb;
    const img = tc.getContext('2d').createImageData(R.length, nb), px = img.data;
    R.forEach((r, xx) => { for (let k = 0; k < nb; k++) { const cc = cmap((r.sp[k] - lo) / (hi - lo)), o = 4 * ((nb - 1 - k) * R.length + xx); px[o] = cc[0]; px[o + 1] = cc[1]; px[o + 2] = cc[2]; px[o + 3] = 255; } });
    tc.getContext('2d').putImageData(img, 0, 0); x.tc = tc; x.off = (x.g.t0 || 0) - (EVV.g.t0 || 0);
  });
  EVV.cmp = rows; drawCmp();
}
function drawCmp() {
  const rows = EVV.cmp, g = EVV.g, R = EVV.d; if (!rows || !g || !R || !R.length) return;
  const total = Math.max(500, (g.clip_s || 0) * 1000, R[R.length - 1].o), d = DPR();
  for (const x of rows) {
    const cv = x.cv; fit(cv); const c = cv.getContext('2d'), w = cv.width, h = cv.height, L = 52 * d, Rr = 14 * d, pw = w - L - Rr;
    const X = o => L + pw * o / total, stp = x.R.step || 125;
    c.clearRect(0, 0, w, h); c.fillStyle = C.grid; c.fillRect(L, 0, pw, h);
    c.save(); c.beginPath(); c.rect(L, 0, pw, h); c.clip();
    c.imageSmoothingEnabled = true; c.drawImage(x.tc, X(x.R[0].o - stp + x.off), 0, X(x.R[x.R.length - 1].o + x.off) - X(x.R[0].o - stp + x.off), h);
    if (g.core) { c.strokeStyle = '#ffffffaa'; c.lineWidth = 1.5 * d; c.setLineDash([4 * d, 3 * d]); for (const o of g.core) { c.beginPath(); c.moveTo(X(o), 0); c.lineTo(X(o), h); c.stroke(); } c.setLineDash([]); }
    if (EVV.a && (EVV.a.currentTime > 0 || !EVV.a.paused)) { const xx = X(EVV.a.currentTime * 1000); c.strokeStyle = '#fff'; c.lineWidth = 2 * d; c.beginPath(); c.moveTo(xx, 0); c.lineTo(xx, h); c.stroke(); }
    c.restore();
  }
}
function haInfo(g) {
  return ((g && g.ha) || []).map(x => [x.label, (x.on ? t('ha_on') : x.on === false ? t('ha_off') : t('ha_unk')) + (x.state && !['on', 'off', 'unknown', 'unavailable'].includes(String(x.state).toLowerCase()) ? ' · ' + x.state : '')   // „aus · off“ doppelt: Rohzustand nur, wenn er mehr sagt (z. B. playing)
    + (x.on && x.mute ? ' · 🔇 ' + t('ha_mute') : x.on && x.vol != null ? ' · 🔊 ' + x.vol + ' %' : ''), x.entity]);
}

/* ================= Ganzer Tag (Tagesspur): im Nachtbericht und in der Live-Ansicht ================= */
const DT = { el: { cv: 'ndcv', hover: 'ndhover', none: 'ndnone', range: 'ndrange', reset: 'ndreset' }, hide: (() => { try { return new Set(JSON.parse(localStorage.getItem('laerm_dthide') || '[]')); } catch (e) { return new Set(); } })(), src: '', date: '', from: null, to: null, data: null, drag: null, req: 0 };
const LDT = { el: { cv: 'ldcv', hover: 'ldhover', none: 'ldnone', range: 'ldrange' }, live: true, src: '', date: '', from: null, to: null, data: null, drag: null, req: 0, timer: null };
const LONG_SPAN = s => s > 600;                     // Live-Ansicht: ab 1 h aus der Tagesaufzeichnung
async function dtLoad(S, keep) {
  if (S === true || S === undefined) { keep = S; S = DT; }
  if (S === DT) visChanged();
  let q;
  if (S === LDT) {                                  // Live: letzte 1 h / 6 h oder heute, laufend
    const now = nowServer(), today = isoDay(new Date(now));
    S.src = selSrc; S.date = today;
    if (S.from == null) S.zoom = false;
    if (!S.zoom) {
      if (view.span >= 86400) { S.from = parseDay(today).getTime(); S.to = S.from + 86400000; }
      else { S.to = now; S.from = now - view.span * 1000; }
    }
    q = 'daytrack?src=' + encodeURIComponent(S.src) + '&date=' + today + '&free=1&from=' + Math.round(S.from) + '&to=' + Math.round(S.to);
  } else {
    const date = NV.date; if (!date) return;
    if (!keep || S.date !== date) { S.from = S.to = null; }
    S.date = date;
    if (!S.src) S.src = NV.src || 'all';
    if (S === DT) {
      if (!nvReady()) return;                        // Bericht für diesen Tag noch nicht geladen: der Verlauf kommt gleich mit dem Bericht
      $('ndcv').hidden = true; $('ndmulti').hidden = false; return dtLoadAll(S);
    }   // Verlauf: eingestellte Zeilen untereinander, gemeinsame Zeitachse
    const [wf, wt] = dtWin(S);
    q = 'daytrack?src=' + encodeURIComponent(S.src) + '&date=' + date + '&free=1&from=' + wf + '&to=' + wt;
  }
  const cv = $(S.el.cv); if (!cv) return;
  q += '&n=' + Math.max(100, Math.round((cv.clientWidth || 800) / (S === LDT && view.mode === 'wave' ? 3 : 1)));
  if (S.busy) { S.pend = true; return; }             // nur eine Abfrage gleichzeitig, danach sofort die neueste
  S.busy = true; S.pend = false; dtBusy(S, true);
  const id = ++S.req, f0 = S.from, t0_ = S.to;
  try {
    const r = await (await fetch(q, { cache: 'no-store' })).json();
    if (id === S.req) { if (S.zoom && (S.from !== f0 || S.to !== t0_) && r && r.has) { r.from = S.from; r.to = S.to; } S.data = r; dtRender(S); }
  } catch (e) { }
  finally { S.busy = false; if (S.pend) { S.pend = false; dtLoad(S, true); } else dtBusy(S, false); }
}
function dtRangeTxt(r) {                             // „Mo., 05.10. 21:55–21:57“ bzw. über mehrere Tage „29.09. – 05.10.“
  const L = locale(), f = new Date(r.from), tt = new Date(r.to), e1 = new Date(r.to - 1), hm = d => pad(d.getHours()) + ':' + pad(d.getMinutes());
  if (isoDay(f) !== isoDay(e1)) return f.toLocaleDateString(L, { day: '2-digit', month: '2-digit' }) + ' ' + hm(f) + ' – ' + e1.toLocaleDateString(L, { day: '2-digit', month: '2-digit' }) + ' ' + (hm(tt) === '00:00' ? '24:00' : hm(tt));
  return f.toLocaleDateString(L, { weekday: 'short', day: '2-digit', month: '2-digit' }) + ' ' + hm(f) + '–' + (hm(tt) === '00:00' ? '24:00' : hm(tt));
}
function dtRender(S) {
  S = S || DT; const r = S.data; if (!r) return;
  if (S.el.sel && $(S.el.sel)) {
    const sel = $(S.el.sel), ids = new Set(r.srcs.concat([S.src]));
    sel.innerHTML = ''; option(sel, 'all', t('all_sources')); SOURCES.filter(s => ids.has(s.id)).forEach(s => option(sel, s.id, s.name)); if (![...sel.options].some(o => o.value === S.src)) option(sel, S.src, S.src); sel.value = S.src;
  }
  if (S.el.none && $(S.el.none)) $(S.el.none).hidden = r.has;
  if (S.el.reset) $(S.el.reset).disabled = S.from == null;
  if (S.el.range && $(S.el.range)) $(S.el.range).textContent = (S === LDT ? (S.zoom ? '⏪ ' : '● ') : '') + dtRangeTxt(r);
  dtDraw(S); if (S === LDT) dtSpec(S);
}
/* Gespeichertes Spektrum (ganzer Tag) als Bild: Spalten je Abschnitt, feste Farbskala -110 … -30 dBFS */
function specCols(r) {
  if (!r || !r.spec || !r.spec.b || !r.spec.b.length) return null;
  if (r._sc) return r._sc;
  const nb = r.spec.bands.length, lo = 2 * (-110 + 130), hi = 2 * (-30 + 130);
  const cols = r.spec.b.map(([t2, b]) => { const sb = atob(b), px = new Uint8ClampedArray(nb * 4);
    for (let k = 0; k < nb; k++) { const cc = cmap(((sb.charCodeAt(k) || 0) - lo) / (hi - lo)), o = 4 * (nb - 1 - k); px[o] = cc[0]; px[o + 1] = cc[1]; px[o + 2] = cc[2]; px[o + 3] = 255; }
    return [t2, px]; });
  return (r._sc = { nb, cols });
}
function drawSpecInto(c, r, X, y0, hgt, L, pw, d) {
  const sc = specCols(r); if (!sc) return false;
  const step = r.step || (r.to - r.from) / 1200, w1 = Math.max(1, X(r.from + step) - X(r.from)) + 0.6;
  const tc = document.createElement('canvas'); tc.width = 1; tc.height = sc.nb; const tx = tc.getContext('2d'), img = tx.createImageData(1, sc.nb);
  c.save(); c.beginPath(); c.rect(L, y0, pw, hgt); c.clip(); c.imageSmoothingEnabled = true;
  const cols = sc.cols, mw = Math.max(w1, X(r.from + 125) - X(r.from) + 0.6);   // höchstens bis zur nächsten Spalte (Lücke nur bei echter Pause)
  cols.forEach(([t2, px], i) => { const nx = i + 1 < cols.length ? X(cols[i + 1][0]) - X(t2) + 0.6 : w1; img.data.set(px); tx.putImageData(img, 0, 0); c.drawImage(tc, X(t2), y0, Math.max(w1, Math.min(nx, mw * 2.5)), hgt); });
  c.restore(); return true;
}
function dtDraw(S, hoverX) {
  S = S || DT; const r = S.data, cv = $(S.el.cv); if (!r || !cv || !cv.offsetParent) return;
  fit(cv); readNC();
  const art = (r.art || []).length || (r.subs || []).length || (r.pa || []).length;          // Zeile für die KI-Arten (Muster über den Tag)
  const d = DPR(), c = cv.getContext('2d'), w = cv.width, h = cv.height, L = 44 * d, Rr = 10 * d, T = (art ? 40 : 18) * d, B = 20 * d, pw = w - L - Rr, ph = h - T - B;
  const span = r.to - r.from, X = t2 => L + pw * (t2 - r.from) / span;
  let lo = 1e9, hi = -1e9; for (const p of r.pts) for (const v of [p[1], p[2], p[3]]) if (v != null && v > -125) { lo = Math.min(lo, v); hi = Math.max(hi, v); }
  if (lo > hi) { lo = -90; hi = -30; }               // unten bündig am tiefsten Wert (Schwelle zählt nicht), zu wenig Spanne nur nach oben ergänzen
  { const pad = Math.max(0.5, (hi - lo) * 0.04); lo = Math.floor((lo - pad) * 2) / 2; hi = Math.ceil((hi + pad) * 2) / 2; if (hi - lo < 6) hi = lo + 6; }
  { const yk = (S.parent || S).yk || 1; if (yk < 1) hi = lo + Math.max(1, (hi - lo) * yk); }   // Umschalt + Mausrad: Höhe gezoomt, unten bündig
  const ystep = [0.5, 1, 2, 5, 10, 20].find(q => (hi - lo) / q <= 8) || 20;
  const Y = v => T + ph * (1 - clamp((v - lo) / (hi - lo), 0, 1));
  c.clearRect(0, 0, w, h); c.font = (10.5 * d) + 'px system-ui'; c.fillStyle = NC.mut; c.strokeStyle = NC.grid; c.lineWidth = 1;
  c.textAlign = 'right'; const waveM = S.mode ? S.mode === 'wave' : S === LDT && view.mode === 'wave';
  const specM = S.mode === 'spec';                  // Zeile als Spektrogramm (gespeichertes Spektrum des ganzen Tages)
  if (specM) {                                      // Spektrogramm bleibt unser eigenes Bild (Raster und Zeitachse selbst)
    upHide(cv);
    for (let v = Math.ceil(lo / ystep) * ystep; v <= hi; v += ystep) { const y = Y(v); c.beginPath(); c.moveTo(L, y); c.lineTo(L + pw, y); c.stroke(); }
    const maxT = Math.max(3, Math.min(12, Math.floor(pw / d / 64))), steps = [10e3, 30e3, 60e3, 300e3, 900e3, 1800e3, 3600e3, 7200e3, 10800e3, 21600e3, 43200e3, 864e5, 1728e5, 6048e5], st = steps.find(s2 => span / s2 <= maxT) || 6048e5;
    c.textAlign = 'center';
    const tz = new Date(r.from).getTimezoneOffset() * 60000;     // Raster auf volle Ortszeit
    for (let t2 = Math.ceil((r.from - tz) / st) * st + tz; t2 < r.to - span * 0.015; t2 += st) { const x = X(t2), dd = new Date(t2); c.beginPath(); c.moveTo(x, T); c.lineTo(x, T + ph); c.stroke(); c.fillText(st >= 864e5 || (st >= 43200e3 && !dd.getHours()) ? pad(dd.getDate()) + '.' + pad(dd.getMonth() + 1) + '.' : pad(dd.getHours()) + ':' + pad(dd.getMinutes()) + (st < 60e3 ? ':' + pad(dd.getSeconds()) : ''), x, h - 5 * d); }
  } else {                                          // Pegelspur bzw. Balken: uPlot (Raster, Achsen, Kurven)
    const up = upGet(cv, { kind: waveM ? 'wave' : 'lvl', L: 44, R: 10, T: art ? 40 : 18, B: 20, pal: dayPal, day: true, act: !waveM });
    const pid = r.pts._uid || (r.pts._uid = ++UPID);
    if (waveM) {
      const F = v => clamp((v - lo) / (hi - lo), 0, 1), tk = dbTicks(lo, hi, ph / 2, 18);
      up.u._wv = { ticks: tk.ticks.filter(k => k.major), F, fmt: tk.fmt };
      upDraw(up, pid + '|' + lo + '|' + hi, () => dayData(r, true, F), r.from, r.to, -1, 1);
    } else upDraw(up, pid + '', () => dayData(r, false), r.from, r.to, lo, hi);
  }
  if (specM) {
    c.clearRect(L - 44 * d, T - 2 * d, pw + 44 * d, ph + 4 * d); c.fillStyle = C.grid; c.fillRect(L, T, pw, ph);
    if (!drawSpecInto(c, r, X, T, ph, L, pw, d)) { c.fillStyle = NC.mut; c.textAlign = 'left'; c.font = (11 * d) + 'px system-ui'; c.fillText(t('dt_spec_nodata'), L + 8 * d, T + ph / 2); }
    c.fillStyle = NC.mut; c.textAlign = 'right'; c.font = (10 * d) + 'px system-ui';
    const bands = (r.spec && r.spec.bands) || []; for (const f of bands.length ? [100, 500, 2000, 8000] : []) { const k = bands.findIndex(x => x >= f); if (k < 0) continue; const y = T + ph * (1 - (k + 0.5) / bands.length); c.fillText(f >= 1000 ? f / 1000 + 'k' : f + '', L - 4 * d, y + 3 * d); }
  }
  S.downHit = [];
  for (const g of NV.down || []) {                  // Nicht aufgezeichnet (Add-on aus / Neustart): schraffiert, damit es nicht wie Stille aussieht
    if (g[5] && g[5].sid && S.src && S.src !== 'all' && g[5].sid !== S.src) continue;   // Lücke nur eines Geräts: nur in dessen Zeile
    const x0 = X(Math.max(g[0], r.from)), x1 = X(Math.min(g[1], r.to)); if (x1 - x0 < 1) continue;
    const hov = hoverX != null && !MK.on && hoverX * d >= x0 && hoverX * d <= x1;   // darüber: etwas heller (anklickbar)
    c.save(); c.beginPath(); c.rect(x0, T, x1 - x0, ph); c.clip(); c.fillStyle = ca(NC.mut, hov ? 0.16 : 0.07); c.fillRect(x0, T, x1 - x0, ph);
    c.strokeStyle = ca(NC.mut, 0.22); c.lineWidth = 1 * d; c.beginPath(); for (let x = x0 - ph; x < x1; x += 8 * d) { c.moveTo(x, T + ph); c.lineTo(x + ph, T); } c.stroke();
    if (x1 - x0 > 40 * d) {                        // Beschriftung passend zur Breite: zweizeilig, notfalls gekürzt (voller Text als Tooltip)
      c.fillStyle = NC.mut; c.font = (10 * d) + 'px system-ui'; c.textAlign = 'center';
      const mw = x1 - x0 - 8 * d, fitT = s0 => { if (c.measureText(s0).width <= mw) return s0; let a0 = 0, b0 = s0.length; while (a0 < b0) { const m = (a0 + b0 + 1) >> 1; if (c.measureText(s0.slice(0, m) + '…').width <= mw) a0 = m; else b0 = m - 1; } return a0 ? s0.slice(0, a0) + '…' : ''; };
      const lh = 13 * d, maxL = Math.max(1, Math.floor((ph - 6 * d) / lh)), ls = [fitT(t('dt_norec'))];
      if (g[2] && maxL > 1) {                        // Kommentar in Wörtern umbrechen, so viele Zeilen wie Platz ist
        c.font = '600 ' + (10 * d) + 'px system-ui'; let cur = '';
        for (const w of ('📝 ' + g[2]).split(/\s+/)) { const tr = cur ? cur + ' ' + w : w; if (c.measureText(tr).width <= mw || !cur) cur = tr; else { ls.push(cur); cur = w; } }
        if (cur) ls.push(cur);
        if (ls.length > maxL) { ls.length = maxL; ls[maxL - 1] += '…'; }
        for (let i = 1; i < ls.length; i++) ls[i] = fitT(ls[i]);
      }
      const y0 = T + ph / 2 - (ls.length - 1) * lh / 2 + 3 * d;
      ls.forEach((l, i) => { c.font = (i ? '600 ' : '') + (10 * d) + 'px system-ui'; c.fillStyle = i ? NC.tx : NC.mut; c.fillText(l, (x0 + x1) / 2, y0 + i * lh); });
    }
    c.restore();
    (S.downHit || (S.downHit = [])).push([x0 / d, x1 / d, (g[2] ? '📝 ' + g[2] + '\n' : '') + t(g[2] ? 'run_click_edit' : 'run_click_add'), g]);
  }
  const haV = (r.ha || []).filter(a => !SHIDE.has('ha:' + a[2])), haLane = haLanes(haV);
  for (const a of haV) { const x0 = X(Math.max(a[0], r.from)), x1 = Math.max(X(Math.min(a[1], r.to)), X(Math.max(a[0], r.from)) + 3 * d); if (x1 <= x0 || x1 < L || x0 > L + pw) continue;
    const md = a[5] || 'note', col = md === 'event' ? sensCol(a) : '#1c7ed6', ly = T + haLane.get(a[2]) * 6 * d;
    if (md === 'pause') { c.fillStyle = ca(col, specM ? 0.0 : a[4] ? 0.26 : 0.18); c.fillRect(x0, T, x1 - x0, ph); }   // nur „pausieren“ füllt die ganze Höhe (dort wurde nicht ausgewertet)
    c.fillStyle = col; c.fillRect(x0, ly, x1 - x0, (a[4] ? 5 : 4) * d);   // „nur festhalten“/„als Ereignis“: schmaler Streifen oben, je Sensor eine Spur
    if (md === 'event') { c.fillRect(x0, ly, 2 * d, 12 * d); }
    if (a[4] && x1 - x0 > 30 * d) {                  // Notiz zum Sensor-Zeitraum gut sichtbar unter dem Streifen (gekürzt, ganzer Text im Tooltip)
      c.save(); c.beginPath(); c.rect(Math.max(x0, L), T, Math.min(x1, L + pw) - Math.max(x0, L), ph); c.clip();
      c.font = '600 ' + (11 * d) + 'px system-ui'; c.textAlign = 'left'; const tx = '📝 ' + a[4], mw = Math.min(x1, L + pw) - Math.max(x0, L) - 8 * d;
      let s0 = tx; while (s0.length > 4 && c.measureText(s0).width > mw) s0 = s0.slice(0, -2); if (s0 !== tx) s0 = s0.slice(0, -1) + '…';
      const tw = c.measureText(s0).width, xx = Math.max(x0, L) + 4 * d, yy = T + haLane.size * 6 * d + 12 * d + haLane.get(a[2]) * 15 * d;   // Notizen unter allen Spuren, je Sensor eine Zeile
      c.fillStyle = ca(NC.bg || '#000', 0.7); c.fillRect(xx - 2 * d, yy - 11 * d, tw + 4 * d, 15 * d); c.fillStyle = md === 'event' ? '#ff922b' : (typeof darkUI === 'function' && !darkUI()) ? '#1864ab' : '#74c0fc'; c.fillText(s0, xx, yy); c.restore();
    } }
  if ((r.hav || []).length && span <= 6 * 3600000) {   // Lautstärke des Fernsehers an den Wechseln
    c.save(); c.beginPath(); c.rect(L, 0, pw, T + ph); c.clip(); c.font = (9.5 * d) + 'px system-ui'; c.textAlign = 'left'; c.fillStyle = '#1c7ed6'; let lastX = -1e9;
    for (const v of r.hav) { const x = X(Math.max(v[0], r.from)); if (x < L - 1 || x > L + pw) continue; if (!(r.ha || []).some(a => v[0] >= a[0] - 6000 && v[0] <= a[1])) continue;
      const tx = v[3] ? '🔇' : '🔊' + (v[2] != null ? v[2] + '%' : ''); if (x - lastX < c.measureText(tx).width + 6 * d) continue;
      c.fillRect(x, T, 1 * d, 6 * d); c.fillText(tx, x + 2 * d, T + 9 * d + (art ? 0 : 0)); lastX = x + c.measureText(tx).width; }
    c.restore();
  }
  if (haV.length) { c.textAlign = 'left'; let lx = L + 4 * d; for (const [nm] of haLane) { const ea = haV.find(a => a[2] === nm && a[5] === 'event'), ev = !!ea; c.fillStyle = ev ? sensCol(ea) : '#1c7ed6'; const tx = (ev ? '◆ ' : '▬ ') + nm; c.fillText(tx, lx, 15 * d); lx += c.measureText(tx).width + 10 * d; } }
  const bw = Math.max(1, pw * (r.step || span / 1200) / span);
  // Spitze als Fläche mit Linie; Lücken (keine Werte, z. B. gestoppt) bleiben offen; Störung rot
  const gapMs = Math.max(400, 3 * (r.step || 0)), segs = []; let cur = null, prevT = null;
  for (const p of r.pts) { if (p[1] == null || (prevT != null && p[0] - prevT > gapMs)) { cur = null; } if (p[1] == null) { prevT = null; continue; } if (!cur) { cur = []; segs.push(cur); } cur.push(p); prevT = p[0]; }
  if (specM) segs.length = 0;
  const wave = waveM, LY = S.lay || LAY, lyOn = LY.lo || LY.mid || LY.hi || LY.dom || LY.cen;   // Zeile: eigene Darstellung und Ebenen
  if (wave && false) {                                // Lautstärke-Balken: jetzt uPlot
    const mid = T + ph / 2, F = v => clamp((v - lo) / (hi - lo), 0, 1), bwB = Math.max(2 * d, bw - 1 * d);
    for (const p of r.pts) { if (p[1] == null) continue; const hh = Math.max(1.5 * d, F(p[1]) * ph / 2), tv = p[4];
      c.fillStyle = tv == null ? NC.acc : p[1] >= tv ? NC.red : p[1] >= tv - 3 ? NC.warn : NC.acc; c.globalAlpha = tv != null && p[1] >= tv - 3 ? 1 : 0.75;
      c.fillRect(X(p[0]), mid - hh, bwB, hh * 2); }
    c.globalAlpha = 1; segs.length = 0;
  }
  segs.length = 0;                                  // Kurve zeichnet uPlot
  for (const sg of segs) {
    c.beginPath(); c.moveTo(X(sg[0][0]) + bw / 2, T + ph); for (const p of sg) c.lineTo(X(p[0]) + bw / 2, Y(p[1])); c.lineTo(X(sg[sg.length - 1][0]) + bw / 2, T + ph); c.closePath();
    c.fillStyle = ca(NC.acc, 0.22); c.fill();
    c.lineWidth = 1.2 * d; c.strokeStyle = NC.acc; c.beginPath(); sg.forEach((p, k) => { const x = X(p[0]) + bw / 2, y = Y(p[1]); if (k) c.lineTo(x, y); else c.moveTo(x, y); }); c.stroke();
    c.strokeStyle = NC.red; c.lineWidth = 1.6 * d; c.beginPath(); let on = false;
    sg.forEach(p => { const x = X(p[0]) + bw / 2, y = Y(p[1]); if (p[5]) { if (on) c.lineTo(x, y); else c.moveTo(x, y); on = true; } else on = false; }); c.stroke();
  }
  const line = (k, col, dash) => { c.strokeStyle = col; c.lineWidth = 1.5 * d; c.setLineDash(dash ? [4 * d, 3 * d] : []); c.beginPath(); let on = false; for (const p of r.pts) { if (p[k] == null) { on = false; continue; } const x = X(p[0]) + bw / 2, y = Y(p[k]); if (on) c.lineTo(x, y); else c.moveTo(x, y); on = true; } c.stroke(); c.setLineDash([]); };
  if (PT.v != null && S.parent === DT && !specM) ptDraw(c, r, X, Y, lo, hi, L, T, pw, ph, d, wave, bw);   // Prüf-Schwelle (nur Anzeige)
  // Hintergrund und Schwelle zeichnet uPlot; liegt die Schwelle außerhalb der Skala: gestrichelt am Rand mit Beschriftung und Pfeil
  if (!wave && !specM) {
    const tp = []; let prev = null; for (const p of r.pts) { if (prev != null && p[0] - prev > gapMs) tp.push([X(prev) + bw, null]); tp.push([X(p[0]) + bw / 2, p[4]]); prev = p[0]; }
    if (thrEdge(c, tp, lo, hi, L, T, pw, ph, d, NC.warn, 1.5)) {
      const lt = [...r.pts].reverse().find(p => p[4] != null && (p[4] > hi || p[4] < lo));
      if (lt) { c.font = '600 ' + (10.5 * d) + 'px system-ui'; c.textAlign = 'right'; lblBox(c, thrTxt(lt[4], lo, hi), L + pw - 4 * d, lt[4] > hi ? T + 15 * d : T + ph - 5 * d, NC.warn, d); }
    }
  }
  if (!wave && !specM && lyOn && r.pts.some(p => p.length > 6)) {   // Ebenen: tief/mittel/hoch (dB), dominante Frequenz und Klangschwerpunkt (50 Hz – 8 kHz)
    const F0 = Math.log(50), F1 = Math.log(8000), Yf = f => T + ph * (1 - (Math.log(clamp(f, 50, 8000)) - F0) / (F1 - F0));
    const snd = p => p[1] != null && (p[5] || (p[3] != null && p[1] >= p[3] + 6));
    for (const [id, k] of [['lo', 6], ['mid', 7], ['hi', 8]]) if (LY[id]) line(k, LCOL[id]);
    if (LY.cen) { c.strokeStyle = LCOL.cen; c.lineWidth = 1.6 * d; c.beginPath(); let on = false; for (const p of r.pts) { if (!snd(p) || p[10] == null) { on = false; continue; } const x = X(p[0]) + bw / 2, y = Yf(p[10]); if (on) c.lineTo(x, y); else c.moveTo(x, y); on = true; } c.stroke(); }
    if (LY.dom) { c.fillStyle = LCOL.dom; c.globalAlpha = .75; for (const p of r.pts) { if (!snd(p) || p[9] == null) continue; c.beginPath(); c.arc(X(p[0]) + bw / 2, Yf(p[9]), 1.8 * d, 0, 7); c.fill(); } c.globalAlpha = 1; }
    c.font = '600 ' + (10 * d) + 'px system-ui'; let lx = L + pw; c.textAlign = 'right';
    for (const id of ['cen', 'dom', 'hi', 'mid', 'lo']) if (LY[id]) { c.fillStyle = LCOL[id]; const tx = '■ ' + t('lay_s_' + id); c.fillText(tx, lx, 15 * d); lx -= c.measureText(tx).width + 10 * d; }
  }
  if (art) {                                          // KI: je Störung die erkannte Art, beim Hineinzoomen jedes Einzelereignis mit Symbol
    const y0 = T - 20 * d, fine = r.fine || {}; c.textAlign = 'center'; c.font = (12 * d) + 'px system-ui'; let lastX = -1e9;
    if ((r.subs || []).length) {
      for (const x of r.subs) { const xx = X(x[0]); if (xx < L || xx > L + pw) continue; const f = fine[x[1]] || { icon: '❓', group: 'other', name: x[1] };
        c.fillStyle = ART_HEX[f.group] || NC.mut; c.fillRect(xx - 0.75 * d, y0 + 15 * d, 1.5 * d, T - y0 - 15 * d);
        if (xx - lastX > 16 * d) { c.fillText(f.icon, xx, y0 + 12 * d); lastX = xx;
          if (span <= 20 * 60000) { c.font = '600 ' + (9.5 * d) + 'px system-ui'; c.textAlign = 'left'; c.fillText(f.name, xx + 8 * d, y0 + 11 * d); c.textAlign = 'center'; c.font = (12 * d) + 'px system-ui'; lastX = xx + c.measureText(f.name).width; } } }
    } else {
      for (const a of r.art) { const xx = X(a[0]); if (xx < L || xx > L + pw) continue; c.fillStyle = a[4] ? '#adb5bd' : a[3] ? lbCol(a[3]) : (ART_HEX[a[1]] || NC.mut); c.fillRect(xx - 1 * d, y0 + 4 * d, 2.5 * d, 14 * d);
        if (xx - lastX > 22 * d && span <= 6 * 3600000) { c.fillText(a[3] ? '🧩' : (ART_ICON[a[1]] || ''), xx, y0 + 2 * d); lastX = xx; } }
    }
  }
  if ((r.pa || []).length) {                         // Bereiche aus „Neu untersuchen“ (Profile, auch unter der Schwelle)
    c.save(); c.beginPath(); c.rect(L, 0, pw, T + ph); c.clip(); let lastX = -1e9;
    for (const a of r.pa) { const x0 = X(Math.max(a[0], r.from)), x1 = Math.max(x0 + 2 * d, X(Math.min(a[1], r.to))); if (x1 < L || x0 > L + pw) continue;
      const col = a[4] ? '#868e96' : lbCol(a[2]); c.fillStyle = ca(col, a[4] ? 0.10 : 0.14); c.fillRect(x0, T, x1 - x0, ph); c.fillStyle = col; c.fillRect(x0, T, x1 - x0, 3 * d);
      if (x1 - x0 > 30 * d || (x0 - lastX > 60 * d && span <= 2 * 3600000)) { c.font = '600 ' + (9.5 * d) + 'px system-ui'; c.textAlign = 'left'; c.fillText('🧩 ' + a[2], x0 + 2 * d, T + 13 * d); lastX = x0 + c.measureText('🧩 ' + a[2]).width; } }
    c.restore();
  }
  c.fillStyle = ca(NC.red, 0.35); for (const e of r.evx || []) { const x = X(e[0]); if (x >= L && x <= L + pw) c.fillRect(x - 1 * d, T + ph + 2 * d, Math.max(2 * d, X(e[0] + e[1]) - x), 2.5 * d); }   // Störung an einem anderen Gerät
  c.fillStyle = NC.red; for (const e of r.ev || []) { const x = X(e[0]); if (x >= L && x <= L + pw) c.fillRect(x - 1 * d, T + ph + 1 * d, Math.max(2 * d, X(e[0] + e[1]) - x), 4 * d); }
  {                                                  // Sensor-Ereignisse (Regel „als Ereignis“, z. B. Türsensor): rote Marker wie bei Störungen, dazu eine dünne Linie über die ganze Höhe
    c.save(); c.beginPath(); c.rect(L, 0, pw, T + ph + 8 * d); c.clip();
    for (const a of (r.ha || []).filter(a => a[5] === 'event' && !SHIDE.has('ha:' + a[2]))) {
      const x0 = X(Math.max(a[0], r.from)), x1 = Math.max(x0 + 2 * d, X(Math.min(a[1], r.to))); if (x1 < L || x0 > L + pw) continue;
      c.fillStyle = ca(NC.red, 0.10); c.fillRect(x0, T, x1 - x0, ph);
      c.strokeStyle = ca(NC.red, 0.75); c.lineWidth = 1 * d; c.setLineDash([3 * d, 3 * d]); c.beginPath(); c.moveTo(x0 + 0.5 * d, T); c.lineTo(x0 + 0.5 * d, T + ph); c.stroke(); c.setLineDash([]);
      c.fillStyle = NC.red; c.fillRect(x0 - 1 * d, T + ph + 1 * d, Math.max(3 * d, x1 - x0), 4 * d);
    }
    c.restore();
  }
  if (S === LDT && !S.zoom) { const x = X(nowServer()); if (x > L && x < L + pw) { c.strokeStyle = NC.tx; c.globalAlpha = 0.4; c.lineWidth = 1 * d; c.beginPath(); c.moveTo(x, T); c.lineTo(x, T + ph); c.stroke(); c.globalAlpha = 1; } }
  fnMarks(c, r.fn, X, T, ph, L, pw, d, span <= 30 * 60000);    // freie Notizen („Notiz jetzt“)
  {                                                  // Notizen und Home-Assistant-Sensoren anklickbar – Klickfläche breiter als die (oft schmale) Fläche
    const pad = (matchMedia('(pointer:coarse)').matches ? 16 : 8), hits = [];
    for (const n of r.fn || []) { const x0 = X(Math.max(n[0], r.from)) / d, x1 = Math.max(x0, X(Math.min(n[1], r.to)) / d); if (x1 < L / d - pad || x0 > (L + pw) / d + pad) continue;
      hits.push([x0 - pad, x1 + pad, '📝 ' + (n[2] || t('fn_btn')) + '\n' + t('fn_click_edit'), { kind: 'fn', a: n[0], b: n[1], id: n[3] }]); }
    const haV2 = (r.ha || []).filter(a => !SHIDE.has('ha:' + a[2])), lanes2 = haLanes(haV2), nl = lanes2.size;
    for (const a of haV2) { const x0 = X(Math.max(a[0], r.from)) / d, x1 = Math.max(x0, X(Math.min(a[1], r.to)) / d); if (x1 < L / d - pad || x0 > (L + pw) / d + pad) continue;
      // Sensoren können gleichzeitig an sein (Fernseher + Türsensor): jede Spur hat ihre eigene Klickfläche, darunter bleibt Ziehen frei
      const ln = lanes2.get(a[2]), ly = T / d + ln * 6, solo = nl === 1 && x1 - x0 <= 40;
      const ymax = solo ? null : a[4] ? T / d + nl * 6 + 16 + ln * 15 : ly + 8, ymin = solo ? null : ln === 0 ? null : ly - 2;   // breiter Balken: nur oben anklickbar (Leiste + Notiz), darunter bleibt Ziehen/Markieren frei
      hits.push([x0 - pad, x1 + pad, '📡 ' + a[2] + ' ' + t('ha_on') + ' · ' + hms(a[0]) + '–' + hms(a[1]) + (a[4] ? '\n📝 ' + a[4] : '') + '\n' + t('ha_click'), { kind: 'ha', a: a[0], b: a[1], name: a[2], rid: a[3], note: a[4] || '', S }, ymax, ymin]); }
    S.downHit = hits.concat(S.downHit || []);
  }
  const mk = S.parent ? S.parent.mark : S.mark;        // in der Tabelle gewähltes Ereignis
  if (mk) { const x0 = X(mk[0]), x1 = Math.max(x0 + 2 * d, X(mk[1])); c.fillStyle = ca(NC.warn, 0.22); c.fillRect(x0, T, x1 - x0, ph); c.fillStyle = NC.warn; c.fillRect(x0 - 1 * d, T, 2 * d, ph); }
  if (S.drag) { const a = Math.min(S.drag.a, S.drag.b), b = Math.max(S.drag.a, S.drag.b); c.fillStyle = S.drag.del ? 'rgba(224,49,49,0.25)' : ca(NC.acc, S.drag.mk ? 0.28 : 0.2); c.fillRect(a * d, T, (b - a) * d, ph); }
  if (MK.sel && MK.sel.day === S) drawMk(c, X, T, ph, d, false);
  S.geo = { L: L / d, pw: pw / d, T: T / d, ph: ph / d, lo, hi, wave: !!wave, spec: !!specM };
  if (hoverX != null) {
    const tq = r.from + span * clamp((hoverX - S.geo.L) / S.geo.pw, 0, 1); let best = null;
    for (const p of r.pts) if (best == null || Math.abs(p[0] - tq) < Math.abs(best[0] - tq)) best = p;
    if (best) { const x = X(best[0]); c.strokeStyle = NC.tx; c.lineWidth = 1 * d; c.beginPath(); c.moveTo(x, T); c.lineTo(x, T + ph); c.stroke();
      const dd = new Date(best[0]); $(S.el.hover).textContent = (S.name ? S.name + ' · ' : '') + t('dt_at', { t: pad(dd.getHours()) + ':' + pad(dd.getMinutes()) + ':' + pad(dd.getSeconds()), p: best[1] != null ? best[1].toFixed(1) : '–', b: best[3] != null ? best[3].toFixed(1) : '–' }); }
    const tol = span / S.geo.pw * 4, on = e => tq >= e[0] - tol && tq <= e[0] + Math.max(e[1], 0) + tol;   // ±4 px, damit auch kurze Störungen zu treffen sind
    const hit = (r.ev || []).find(on), hx = hit ? null : (r.evx || []).find(on), e = hit || hx;
    if (e && !S.drag && !(MK.sel && MK.sel.day === S)) {
      const o = e[3] && typeof e[3] === 'object' ? e[3] : {}, sid = S.src || r.src || selSrc;
      const tip = hit ? { src: sid, from: e[0], to: e[0] + e[1], pk: e[2], th: o.th, bg: o.bg, art: o.a, ac: o.ac, am: o.am, prof: o.p, pc: o.pc, pbg: o.pbg, nt: o.nt,
        also: (r.evx || []).filter(x => x[0] <= e[0] + e[1] + 1500 && x[0] + x[1] >= e[0] - 1500).map(x => x[3]) } : { other: true, src: e[3], from: e[0], to: e[0] + e[1], pk: e[2] };
      const rc = cv.getBoundingClientRect();
      tipShow('day', tipHtml(tip), rc.left + hoverX, rc.top + T / d, hoverX > rc.width * 0.6);
    } else tipHide('day');
  }
}
/* Zeitraum im Nachtbericht: wie der Bericht (eingestellte Erfassungszeit, sonst ganzer Tag), nach dem Hineinzoomen der gewählte Ausschnitt */
function dtWin(S) {
  if (S.from != null) return [Math.round(S.from), Math.round(S.to)];
  const d = NV.data; if (d && d.start) return nvSpan(d);
  const a = parseDay(S.date).getTime(); return [a, a + 86400000];
}
/* Verlauf: Zeilen frei einstellbar (wie „Zeile hinzufügen“): je Zeile Gerät, Darstellung und Ebenen; pro Browser gemerkt */
function dtRows(have) {
  let rows = null; try { rows = JSON.parse(localStorage.getItem('laerm_dtrows') || 'null'); } catch (e) { }
  if (!Array.isArray(rows) || !rows.length) rows = (have.length ? have.map(([s]) => s.id) : SOURCES.map(s => s.id)).map(src => ({ src, mode: 'level', lay: {} }));
  return rows.filter(r => r && r.src).slice(0, 12);
}
function dtRowsSave(rows) { try { localStorage.setItem('laerm_dtrows', JSON.stringify(rows)); } catch (e) { } }
/* Ladesymbol über den Grafik-Zeilen, solange Daten geladen werden (erscheint erst nach kurzer Zeit, damit es bei schnellen Antworten nicht flackert) */
function spinEl() { const d = el('div', { className: 'ldspin' }); d.innerHTML = '<i></i><span>' + esc(t('loading')) + '</span>'; return d; }
function dtBusy(S, on) {
  if (S === LDT) { const b = $('ldaybox'); if (b) b.classList.toggle('loading', on); return; }
  const box = $('ndmulti'); if (!box) return;
  if (on && !box.querySelector('canvas') && !box.querySelector('.ndph')) { const ph = el('div', { className: 'ndph ndcvw' }); ph.appendChild(spinEl()); box.appendChild(ph); }
  if (!on) { const ph = box.querySelector('.ndph'); if (ph) ph.remove(); }
  box.classList.toggle('loading', on);
}
/* Nur eine Abfrage gleichzeitig: Antworten werden immer gezeigt (auch während weiter gezoomt wird), danach sofort der neueste Ausschnitt */
async function dtLoadAll(S) {
  if (S.busy) { S.pend = true; return; }
  S.busy = true; S.pend = false; dtBusy(S, true);
  try { await dtLoadAll1(S); } finally { S.busy = false; if (S.pend) { S.pend = false; dtLoadAll(S); } else dtBusy(S, false); }
}
/* ================= Prüf-Schwelle (Protokolle → Verlauf): frei wählbarer Wert; zeigt, welche Spitzen darüber liegen.
   Nur Anzeige – gespeicherte Daten, Störungen und Prüfsummen bleiben unverändert. Gezählt wird auf dem Server aus den 125-ms-Werten,
   je Spitze mit nachträglicher KI-Zuordnung (aus der Störung bzw. dem gespeicherten KI-Fingerabdruck). ================= */
const PTCOL = '#be4bdb';
const PT = (() => { let v = null; try { const x = parseFloat(localStorage.getItem('laerm_pthr')); if (isFinite(x)) v = x; } catch (e) { } return { v, list: false, res: {}, req: 0, t: 0 }; })();
function ptSet(v, load) {
  PT.v = v == null || !isFinite(v) ? null : Math.round(clamp(v, -130, 0) * 2) / 2;
  try { if (PT.v == null) localStorage.removeItem('laerm_pthr'); else localStorage.setItem('laerm_pthr', String(PT.v)); } catch (e) { }
  $('ndptbar').hidden = PT.v == null; $('ndpt').classList.toggle('on', PT.v != null); $('ndpt').setAttribute('aria-pressed', String(PT.v != null));
  if (document.activeElement !== $('ndptv')) $('ndptv').value = PT.v == null ? '' : PT.v;
  for (const sub of DT.subs || []) if (sub.data) dtDraw(sub);
  if (PT.v == null) { PT.res = {}; $('ndptlist').hidden = true; $('ndptsum').innerHTML = ''; return; }
  if (load) ptLoadSoon();
}
function ptLoadSoon() { clearTimeout(PT.t); PT.t = setTimeout(ptLoad, 250); }
async function ptLoad() {
  if (PT.v == null || !DT.rows || !NV.open) return;
  const [a, b] = dtWin(DT), srcs = [...new Set(DT.rows.map(r => r.src))], id = ++PT.req, v = PT.v;
  $('ndptsum').innerHTML = '<small>' + esc(t('loading')) + '</small>';
  const res = await Promise.all(srcs.map(sid => fetch('exceed?src=' + encodeURIComponent(sid) + '&from=' + Math.round(a) + '&to=' + Math.round(b) + '&thr=' + v, { cache: 'no-store' }).then(x => x.json()).catch(() => null)));
  if (id !== PT.req) return;
  PT.res = {}; srcs.forEach((sid, i) => { PT.res[sid] = res[i]; }); ptRender();
}
const ptDur = s2 => { s2 = Math.round(s2); return s2 < 60 ? s2 + ' s' : Math.floor(s2 / 60) + ':' + pad(s2 % 60) + ' min'; };
function ptRender() {
  const nm = id => viewName(id);
  const ids = Object.keys(PT.res);
  $('ndptsum').innerHTML = ids.map(id => { const r = PT.res[id]; if (!r || !r.ok) return ''; return '<span>' + (r.n ? esc(t('pt_sum', { d: nm(id), n: r.n, t: ptDur(r.dur_s) })).replace(/^([^:]+):/, '<b>$1:</b>') : esc(t('pt_none', { d: nm(id) }))) + '</span>'; }).join('')
    + ((w => w ? `<span class="ptwarn">⚠ ${esc(t(w.ki_why === 'model' ? 'pt_kimodel' : 'pt_kioff'))}</span>` : '')(ids.map(id => PT.res[id]).find(r => r && r.ok && r.ki === false)));
  $('ndptl').textContent = t(PT.list ? 'pt_list_hide' : 'pt_list');
  const box = $('ndptlist'); box.hidden = !PT.list; if (!PT.list) return;
  const rows = []; let cut = false;
  for (const id of ids) { const r = PT.res[id]; if (!r || !r.ok) continue; if (r.cut) cut = true; for (const x of r.list) rows.push([id, x]); }
  rows.sort((p, q) => p[1][0] - q[1][0]);
  if (!rows.length) { box.innerHTML = `<div class="ndptcut">${esc(t('pt_none', { d: t('pt_col_dev') + ' –' }).replace(/^.*?: /, ''))}</div>`; return; }
  const show = rows.slice(0, 1000); if (rows.length > show.length) cut = true;
  const kiCell = k => {
    if (!k || k.src !== 'ev' && k.src !== 'fp') { const w = !k ? 'pt_nc' : k.src === 'nc' ? 'pt_nc' : k.src === 'day' ? 'pt_noday' : 'pt_nogap'; return `<td colspan="2" title="${esc(t(w + '_tip'))}"><small>${esc(t(w))}</small></td>`; }
    const tip = esc(t(k.src === 'ev' ? 'pt_ev' : 'pt_fp'));
    return `<td title="${tip}">${k.art ? artChip(k.art, k.pct, k.man) : ''}${k.src === 'fp' ? ' <small>ⓕ</small>' : ''}</td><td title="${tip}">${k.prof ? `<span class="art prof${k.pbg ? ' bgp' : ''}">🧩 ${esc(k.prof)}${k.ppct != null ? ` <small>${k.ppct} %</small>` : ''}</span>` : ''}</td>`;
  };
  box.innerHTML = `<table><tr><th>${esc(t('pt_col_dev'))}</th><th>${esc(t('pt_col_t'))}</th><th>${esc(t('pt_col_dur'))}</th><th>${esc(t('pt_col_pk'))}</th><th>${esc(t('pt_col_over'))}</th><th>${esc(t('pt_col_art'))}</th><th>${esc(t('pt_col_prof'))}</th></tr>`
    + show.map(([id, x]) => `<tr data-a="${x[0]}" data-b="${x[1]}"><td>${esc(nm(id))}</td><td>${hms(x[0])}</td><td>${(Math.max(0.125, (x[1] - x[0]) / 1000)).toFixed(1).replace('.', lang === 'de' ? ',' : '.')} s</td><td>${f1(x[2])} dBFS</td><td>+${f1(x[2] - PT.v)} dB</td>${kiCell(x[3])}</tr>`).join('')
    + '</table>' + (cut ? `<div class="ptcut ndptcut">${esc(t('pt_cut', { n: show.length }))}</div>` : '');
  box.querySelectorAll('tr[data-a]').forEach(tr => tr.onclick = () => { const a = +tr.dataset.a, b = +tr.dataset.b, padv = Math.max(15000, (b - a) * 3); DT.mark = [a, b]; dtSetWin(DT, a - padv, b + padv, 'now'); $('ndaybox').scrollIntoView({ behavior: 'smooth', block: 'start' }); });
}
function ptDraw(c, r, X, Y, lo, hi, L, T, pw, ph, d, wave, bw) {
  const v = PT.v, col = PTCOL;
  c.save(); c.beginPath(); c.rect(L, T, pw, ph); c.clip();
  if (wave) {                                         // Balken: gespiegelt; Teil über der Prüf-Schwelle hervorheben
    const mid = T + ph / 2, F = x => clamp((x - lo) / (hi - lo), 0, 1), fv = F(v);
    c.fillStyle = ca(col, 0.75);
    for (const p of r.pts) if (p[1] != null && p[1] > v) { const x = X(p[0]), hh = F(p[1]) * ph / 2, h0 = fv * ph / 2; c.fillRect(x, mid - hh, Math.max(1.5 * d, bw - 1 * d), hh - h0); c.fillRect(x, mid + h0, Math.max(1.5 * d, bw - 1 * d), hh - h0); }
    c.strokeStyle = col; c.lineWidth = 1.6 * d; c.beginPath(); for (const y of [mid - fv * ph / 2, mid + fv * ph / 2]) { c.moveTo(L, y); c.lineTo(L + pw, y); } c.stroke();
  } else {
    const yv0 = v > hi ? T : v < lo ? T + ph : Y(v);
    c.fillStyle = ca(col, 0.6);
    for (const p of r.pts) if (p[1] != null && p[1] > v) { const y = Y(p[1]); if (yv0 - y > 0.5) c.fillRect(X(p[0]), y, Math.max(1.2 * d, bw), yv0 - y); }
    c.strokeStyle = col; c.lineWidth = 1.8 * d; c.setLineDash(v > hi || v < lo ? [7 * d, 4 * d] : []); c.beginPath(); c.moveTo(L, yv0 + (v > hi ? 1 * d : v < lo ? -1 * d : 0)); c.lineTo(L + pw, yv0 + (v > hi ? 1 * d : v < lo ? -1 * d : 0)); c.stroke(); c.setLineDash([]);
  }
  c.restore();
  c.font = '600 ' + (10.5 * d) + 'px system-ui'; c.textAlign = 'left';
  const ty = wave ? T + ph / 2 - clamp((v - lo) / (hi - lo), 0, 1) * ph / 2 - 5 * d : v > hi ? T + 15 * d : v < lo ? T + ph - 5 * d : Y(v) - 5 * d;
  lblBox(c, t('pt_line', { v: f1(v) }) + (v > hi ? ' ↑' : v < lo ? ' ↓' : ''), L + 6 * d, Math.max(T + 12 * d, ty), col, d);
}
function ptNear(S, y) {                              // Maus nahe an der Linie (CSS-Pixel)?
  const g = S.geo; if (PT.v == null || S.parent !== DT || !g || g.spec || !S.data) return false;
  if (g.wave) { const mid = g.T + g.ph / 2, off = clamp((PT.v - g.lo) / (g.hi - g.lo), 0, 1) * g.ph / 2; return Math.abs(y - (mid - off)) < 7 || Math.abs(y - (mid + off)) < 7; }
  const yy = g.T + g.ph * (1 - clamp((PT.v - g.lo) / (g.hi - g.lo), 0, 1)); return Math.abs(y - yy) < 7;
}
function ptVal(S, y) {
  const g = S.geo; if (!g) return null;
  if (g.wave) { const f = clamp(Math.abs(y - (g.T + g.ph / 2)) / (g.ph / 2), 0, 1); return g.lo + f * (g.hi - g.lo); }
  return g.lo + (1 - clamp((y - g.T) / g.ph, 0, 1)) * (g.hi - g.lo);
}
function initPt() {
  if (!$('ndpt')) return;
  $('ndmore').onclick = () => { const o = $('ndtools').classList.toggle('open'); $('ndmore').setAttribute('aria-expanded', String(o)); };
  $('ndpt').onclick = () => {
    if (PT.v != null) return ptSet(null);
    let tv = null; const sub = (DT.subs || []).find(x => x.data && x.data.pts.length);   // Start: knapp über der gespeicherten Schwelle
    if (sub) { const th = sub.data.pts.map(p => p[4]).filter(x => x != null).sort((a, b) => a - b); if (th.length) tv = th[th.length >> 1] + 10; else { const pk = sub.data.pts.map(p => p[1]).filter(x => x != null).sort((a, b) => a - b); if (pk.length) tv = pk[Math.floor(pk.length * 0.9)]; } }
    ptSet(tv != null ? tv : -60, true);
  };
  $('ndptx').onclick = () => ptSet(null);
  $('ndptv').addEventListener('change', () => { const v = parseFloat(String($('ndptv').value).replace(',', '.')); if (isFinite(v)) ptSet(v, true); });
  $('ndptl').onclick = () => { PT.list = !PT.list; ptRender(); };
  if (PT.v != null) { $('ndptbar').hidden = false; $('ndpt').classList.add('on'); $('ndptv').value = PT.v; $('ndptl').textContent = t('pt_list'); }
}
function nvReady() { return NV.dkey === JSON.stringify([NV.date, NV.src, perRange(), NV.per, PV.cur, NV.art]); }
async function dtLoadAll1(S) {
  if (!nvReady()) return;
  const box = $('ndmulti'), date = S.date, id = ++S.req, dkey = NV.dkey;
  const w = Math.max(300, Math.round(box.clientWidth || $('ndaybox').clientWidth || 800));
  const [wf, wt] = dtWin(S);
  const spec = new Set((S.rows || dtRows([])).filter(r => r.mode === 'spec').map(r => r.src));      // Spektrum nur, wo eine Zeile es zeigt
  const q = sid => 'daytrack?src=' + encodeURIComponent(sid) + '&date=' + date + '&n=' + w + '&free=1&from=' + wf + '&to=' + wt + (spec.has(sid) ? '' : '&nospec=1');
  let res;
  const LS = SOURCES.concat(FORMER.filter(f => (S.rows || dtRows([])).some(r => r.src === f.id)));   // ehemalige Geräte nur, wenn eine Zeile sie zeigt
  try { res = await Promise.all(LS.map(s => fetch(q(s.id), { cache: 'no-store' }).then(x => x.json()).catch(() => null))); } catch (e) { return; }
  if (id !== S.req || date !== S.date || dkey !== NV.dkey) return;   // inzwischen anderer Tag/Zeitraum: verwerfen (der neue lädt schon)
  const [cf, ct] = dtWin(S);
  if (cf !== wf || ct !== wt) res.forEach(r => { if (r && r.has) { r.from = cf; r.to = ct; } });   // inzwischen weiter gezoomt: im aktuellen Ausschnitt zeigen, genauer kommt gleich
  const by = {}; LS.forEach((s, i) => { by[s.id] = res[i]; });
  const have = LS.map((s, i) => [s, res[i]]).filter(([s, r]) => r && r.has && !s.former);
  $('ndnone').hidden = have.length > 0; $('ndchips').innerHTML = '';
  S.rows = S.rows && S.rows.length ? S.rows : dtRows(have); S.byData = by;   // Zeilen behalten (Änderungen an Gerät, Darstellung, Höhe gehen sonst verloren)
  const sig = JSON.stringify(S.rows.map(r => [r.src, !!(by[r.src] && by[r.src].has)]));
  const ssig = JSON.stringify(S.rows.map(r => r.src));
  if (S.subs && S.subs.length === S.rows.length && S._ssig === ssig && (S._rsig === sig || S.from != null) && box.querySelector('canvas')) {   // nur neue Daten (Zoomen/Scrollen): Zeilen bleiben stehen, nur neu zeichnen (auch ohne Daten im Ausschnitt, damit nichts verrutscht)
    S.subs.forEach(sub => { const r = by[sub.src]; sub.data = r && r.has ? r : null; if (sub.data) dtDraw(sub); else dtEmpty(sub); });
  } else { S._rsig = sig; S._ssig = ssig; dtRowsRender(S); }
  if (PT.v != null) ptLoadSoon();
  dtBar(S);
  if (have.length) {                                  // Kopfzeile
    S.data = have[0][1]; const r = S.data;
    $('ndrange').textContent = dtRangeTxt(r) + (r.coarse ? ' · ' + t('dt_coarse') : '');
    $('ndreset').disabled = $('ndreset').hidden = S.from == null;
  }
}
function dtEmpty(S) {                               // Zeile ohne Daten im gezoomten Ausschnitt: Fläche bleibt gleich hoch, nur Hinweis
  const cv = $(S.el.cv); if (!cv || !cv.offsetParent) return; fit(cv); readNC(); upHide(cv);
  const d = DPR(), c = cv.getContext('2d'); c.clearRect(0, 0, cv.width, cv.height);
  c.fillStyle = C.grid; c.fillRect(44 * d, 18 * d, cv.width - 54 * d, cv.height - 38 * d);
  c.fillStyle = NC.mut; c.font = (11 * d) + 'px system-ui'; c.textAlign = 'left'; c.fillText(t('dt_none_row'), 52 * d, cv.height / 2);
}
const DT_LAYOPEN = new Set();
function dtRowsRender(S) {
  const box = $('ndmulti'); box.innerHTML = ''; S.subs = [];
  const name = id => viewName(id);
  S.rows.forEach((row, i) => {
    const hd = el('div', { className: 'ndrow' });
    const ss = el('select', { className: 'ndrsrc', title: t('src_col') }); viewSources().forEach(s => option(ss, s.id, viewName(s.id))); if (!viewSources().some(s => s.id === row.src)) option(ss, row.src, row.src); ss.value = row.src;
    const ms = el('select', { className: 'ndrmode', title: t('dt_view') }); option(ms, 'level', t('v_level')); option(ms, 'wave', t('v_wave')); option(ms, 'spec', t('dt_mode_spec')); ms.value = row.mode || 'level';
    const lb = el('span', { className: 'ndrlay' });
    for (const k of ['lo', 'mid', 'hi', 'dom', 'cen']) { const l = el('label', { className: 'chip ndchip', title: t('lay_' + k) }); const c = el('input', { type: 'checkbox', checked: !!(row.lay || {})[k] }); l.append(c, el('i', { className: 'ndsw' }), document.createTextNode(t('lay_s_' + k))); l.querySelector('i').style.background = LCOL[k]; c.onchange = () => { row.lay = Object.assign({}, row.lay, { [k]: c.checked }); dtRowsSave(S.rows); dtRowsRender(S); }; lb.appendChild(l); }
    lb.hidden = ms.value !== 'level';
    let lt = null;                                    // Handy: Ebenen hinter einem Knopf, damit der Graph Platz hat
    if (innerWidth < 600 && ms.value === 'level') {
      const n = Object.values(row.lay || {}).filter(Boolean).length, op = DT_LAYOPEN.has(i);
      lt = el('button', { type: 'button', className: 'chip ndrlt' + (n ? ' on' : ''), textContent: '🗂 ' + t('lay_btn') + (n ? ' (' + n + ')' : '') + (op ? ' ▴' : ' ▾') });
      lt.setAttribute('aria-expanded', String(op)); lb.hidden = !op;
      lt.onclick = () => { op ? DT_LAYOPEN.delete(i) : DT_LAYOPEN.add(i); dtRowsRender(S); };
    }
    const up = el('button', { type: 'button', className: 'chip', textContent: '↑', title: t('dt_up') }), dn = el('button', { type: 'button', className: 'chip', textContent: '↓', title: t('dt_down') }), rm = el('button', { type: 'button', className: 'chip danger', textContent: '✕', title: t('dt_rm') });
    up.disabled = i === 0; dn.disabled = i === S.rows.length - 1; rm.disabled = S.rows.length < 2;
    const mv = k => { const r2 = S.rows.splice(i, 1)[0]; S.rows.splice(i + k, 0, r2); dtRowsSave(S.rows); dtRowsRender(S); };
    up.onclick = () => mv(-1); dn.onclick = () => mv(1); rm.onclick = () => { S.rows.splice(i, 1); dtRowsSave(S.rows); dtRowsRender(S); };
    ss.onchange = () => { row.src = ss.value; dtRowsSave(S.rows); dtRowsRender(S); };
    ms.onchange = () => { row.mode = ms.value; dtRowsSave(S.rows); dtRowsRender(S); };
    hd.append(ss, ms, ...(lt ? [lt] : []), el('span', { className: 'ndrgap' }), up, dn, rm, lb);
    const cv = el('canvas', { id: 'ndcv_r' + i, className: 'ndcvm' });
    if (row.h) cv.style.height = row.h + 'px';
    const rz = el('div', { className: 'ndrz', title: t('dt_resize') }); rz.setAttribute('role', 'separator'); rz.setAttribute('aria-orientation', 'horizontal');
    const cw = el('div', { className: 'ndcvw' }); cw.append(cv, spinEl());
    box.append(hd, cw, rz);
    const r = S.byData && S.byData[row.src];
    const sub = { el: { cv: cv.id, hover: 'ndhover' }, src: row.src, name: name(row.src), parent: S, req: 0, mode: row.mode || 'level', lay: Object.assign({ lo: false, mid: false, hi: false, dom: false, cen: false }, row.lay || {}), data: r && r.has ? r : null };
    if (!sub.data) { cv.hidden = true; hd.appendChild(el('small', { className: 'ndrnone', textContent: t('dt_none_row') })); }
    bindDay(sub, () => { S.from = S.to = null; S.yk = 1; dtLoad(S, true); });
    S.subs.push(sub);
    let rzd = null;                                   // Höhe der Zeile ziehen (Doppelklick = Standard), pro Browser gemerkt
    rz.addEventListener('pointerdown', e => { rzd = { y: e.clientY, h: cv.getBoundingClientRect().height }; rz.setPointerCapture(e.pointerId); rz.classList.add('on'); e.preventDefault(); });
    rz.addEventListener('pointermove', e => { if (!rzd) return; const h = clamp(Math.round(rzd.h + e.clientY - rzd.y), 70, 900); cv.style.height = h + 'px'; if (sub.data) dtDraw(sub); else dtEmpty(sub); });
    const rzUp = () => { if (!rzd) return; rzd = null; rz.classList.remove('on'); const r2 = S.rows[i] || row; r2.h = Math.round(cv.getBoundingClientRect().height); dtRowsSave(S.rows); };   // S.rows wird beim Laden neu erzeugt: dort speichern
    rz.addEventListener('pointerup', rzUp); rz.addEventListener('pointercancel', rzUp);
    rz.addEventListener('dblclick', () => { delete (S.rows[i] || row).h; cv.style.height = ''; dtRowsSave(S.rows); if (sub.data) dtDraw(sub); });
  });
  const add = el('button', { type: 'button', className: 'chip ndradd', textContent: '＋ ' + t('dt_add') });
  add.disabled = S.rows.length >= 12;
  add.onclick = () => { const used = new Set(S.rows.map(r => r.src)), nx = SOURCES.find(s => !used.has(s.id)) || SOURCES[0]; if (!nx) return; S.rows.push({ src: nx.id, mode: 'level', lay: {} }); dtRowsSave(S.rows); dtRowsRender(S); };
  box.appendChild(add);
  for (const sub of S.subs) if (sub.data) dtDraw(sub);
  requestAnimationFrame(() => { for (const sub of S.subs) if (sub.data) dtDraw(sub); });   // nach dem Layout noch einmal in voller Breite
}
function dtJump(k, tr) {                             // Ereignis in der Tabelle gewählt: Verlauf aller Geräte springt dorthin
  const r = EV && EV.events.find(x => (x.k || '') === k); if (!r) return;
  const t0 = new Date(r.start).getTime(), dur = Math.max(+r.dauer_s || 0, 1) * 1000, span = Math.max(+r.clip_s || 0, +r.dauer_s || 0, 10) * 1000;
  DT.mark = [t0, t0 + dur]; DT.from = t0 - Math.max(60000, span * 0.5); DT.to = t0 + span + 60000;   // Störung markiert, mit Umfeld
  const es = r.quelle_id || 'main';                // nur eine Zeile und anderes Gerät: die Zeile schaltet auf das Gerät der Störung um
  if (DT.rows && DT.rows.length === 1 && DT.rows[0].src !== es) { DT.rows[0].src = es; dtRowsSave(DT.rows); }
  document.querySelectorAll('#events .cur').forEach(x => x.classList.remove('cur')); if (tr) tr.classList.add('cur');
  dtLoad(DT, true); $('ndaybox').scrollIntoView({ behavior: 'smooth', block: 'start' });
}
/* Grenzen des Berichts (gewählter Zeitraum): weiter als hier wird nicht gescrollt bzw. herausgezoomt */
function nvSpan(d) {                                 // Zeitraum des Berichts; läuft er noch, endet er bei „jetzt“ (Neuestes rechts bündig)
  const a = new Date(d.start).getTime(), b = new Date(d.end).getTime(), now = nowServer();
  return b > now && now > a ? [a, Math.min(b, Math.ceil((now + clamp((now - a) * 0.015, 60000, 600000)) / 60000) * 60000)] : [a, b];
}
function dtBase(S) { const d = NV.data; if (d && d.start) return nvSpan(d); const a = parseDay(S.date).getTime(); return [a, a + 86400000]; }
/* Neuen Ausschnitt für alle Zeilen setzen: sofort verschoben zeichnen, Daten gedrosselt nachladen */
function dtSetWin(S, f, t2, load) {
  const [b0, b1] = dtBase(S), sp = Math.min(t2 - f, b1 - b0);
  if (sp >= b1 - b0 - 1000) { S.from = S.to = null; S.zoom = false; }
  else { f = clamp(f, b0, b1 - sp); S.from = f; S.to = f + sp; S.zoom = true; }
  const [wf, wt] = dtWin(S);
  for (const sub of S.subs || []) if (sub.data) { sub.data = Object.assign({}, sub.data, { from: wf, to: wt }); dtDraw(sub); }
  if (S.data) $('ndrange').textContent = dtRangeTxt({ from: wf, to: wt }); $('ndreset').disabled = $('ndreset').hidden = S.from == null;
  dtBar(S);
  clearTimeout(S._lt); S._lt = setTimeout(() => dtLoad(S, true), load === 'now' ? 0 : 60);   // kurz sammeln; läuft schon eine Abfrage, folgt die nächste direkt danach
}
function dtZoom(S, k, fx) {                          // k < 1 hinein, > 1 heraus; fx = Stelle (0…1), die stehen bleibt
  const [wf, wt] = dtWin(S), sp = wt - wf, ns = Math.max(30000, sp * k), c0 = wf + fx * sp;
  dtSetWin(S, c0 - fx * ns, c0 - fx * ns + ns);
}
/* Bildlaufleiste unter den Zeilen: zeigt den Ausschnitt im ganzen Zeitraum, ziehen = scrollen, Klick = dorthin */
function dtBar(S) {
  const bar = $('ndbar'); if (!bar) return;
  const [b0, b1] = dtBase(S), [wf, wt] = dtWin(S), on = S.from != null;
  bar.hidden = !on || !(S.subs || []).some(x => x.data); if (bar.hidden) return;
  const th = $('ndthumb'), a = clamp((wf - b0) / (b1 - b0), 0, 1), w = clamp((wt - wf) / (b1 - b0), 0, 1);
  th.style.left = (a * 100) + '%'; th.style.width = Math.max(w * 100, 2) + '%';
}
function initDtBar(S) {
  const bar = $('ndbar'), tr = $('ndtrack'), th = $('ndthumb'); if (!bar) return;
  let dg = null;
  const pos = e => { const r = tr.getBoundingClientRect(); return (e.clientX - r.left) / Math.max(1, r.width); };
  tr.addEventListener('pointerdown', e => {
    const [b0, b1] = dtBase(S), [wf, wt] = dtWin(S), sp = wt - wf;
    if (e.target !== th) { const c = b0 + pos(e) * (b1 - b0); dtSetWin(S, c - sp / 2, c + sp / 2, 'now'); }   // Klick daneben: Ausschnitt dorthin
    const [f2] = dtWin(S); dg = { x: pos(e), f: f2, sp }; tr.setPointerCapture(e.pointerId); e.preventDefault();
  });
  tr.addEventListener('pointermove', e => { if (!dg) return; const [b0, b1] = dtBase(S), f = dg.f + (pos(e) - dg.x) * (b1 - b0); dtSetWin(S, f, f + dg.sp); });
  const up = () => { if (dg) { dg = null; dtLoad(S, true); } };
  tr.addEventListener('pointerup', up); tr.addEventListener('pointercancel', up);
  $('ndzin').onclick = () => dtZoom(S, 0.5, 0.5); $('ndzout').onclick = () => dtZoom(S, 2, 0.5);
  $('ndleft').onclick = () => { const [wf, wt] = dtWin(S), sp = wt - wf; dtSetWin(S, wf - sp * 0.8, wt - sp * 0.8, 'now'); };
  $('ndright').onclick = () => { const [wf, wt] = dtWin(S), sp = wt - wf; dtSetWin(S, wf + sp * 0.8, wt + sp * 0.8, 'now'); };
}
/* Mausrad / Touchpad: Weg in Pixel; Zoomfaktor nach Weg (Mausrad-Raster ≈ 100 px ≈ 25 %, Touchpad-Schritte fein, Touchpad-Zwei-Finger-Spreizen = Strg + Rad) */
function wheelPx(e) { return e.deltaMode === 1 ? 16 : e.deltaMode === 2 ? 400 : 1; }
function wheelK(px, pinch) { return Math.exp(clamp(px, -300, 300) * (pinch ? 0.01 : 0.0022)); }
/* Zwei Finger auf Touch-Geräten: zoomen und gleichzeitig verschieben. Läuft über Touch-Ereignisse, damit der Browser
   dabei nicht die Seite scrollt; ein Finger bleibt für Seite scrollen (senkrecht) bzw. Ziehen (waagerecht). */
function bindPinch(cv, win, fxAt, set, cancel, done) {
  let p = null;
  const mx = e => { const r = cv.getBoundingClientRect(), a = e.touches[0], b = e.touches[1]; return { x1: a.clientX - r.left, x2: b.clientX - r.left, w: r.width }; };
  cv.addEventListener('touchstart', e => {
    if (e.touches.length !== 2) return; const w0 = win(); if (!w0) return;
    e.preventDefault(); cancel(); const m = mx(e);
    p = { d: Math.max(20, Math.abs(m.x2 - m.x1)), fx: fxAt((m.x1 + m.x2) / 2), wf: w0[0], wt: w0[1] };
  }, { passive: false });
  cv.addEventListener('touchmove', e => {
    if (!p) return; e.preventDefault(); if (e.touches.length !== 2) return;
    const m = mx(e), sp = p.wt - p.wf, ns = Math.max(30000, sp * p.d / Math.max(20, Math.abs(m.x2 - m.x1))), c0 = p.wf + p.fx * sp, fx = fxAt((m.x1 + m.x2) / 2);
    set(c0 - fx * ns, c0 - fx * ns + ns);           // Stelle unter den Fingern bleibt unter den Fingern (auch beim Verschieben)
  }, { passive: false });
  const end = e => { if (p && e.touches.length < 2) { p = null; done(); } };
  cv.addEventListener('touchend', end); cv.addEventListener('touchcancel', end);
}
/* Verlauf: Mausrad (mit Strg) oder zwei Finger = zoomen, Ziehen = scrollen (wenn hineingezoomt), sonst bzw. mit Umschalt = Bereich aufziehen */
function bindDay(S, reset) {
  const cv = $(S.el.cv); if (!cv) return;
  const tg = S.parent || S;                          // alle Geräte: Zoom und Scrollen gelten für alle Zeilen
  const xAt = e => e.clientX - cv.getBoundingClientRect().left;
  const fxAt = x => S.geo ? clamp((x - S.geo.L) / S.geo.pw, 0, 1) : 0.5;
  const pts = new Map(); let pinch = null, pan = null;
  cv.style.touchAction = 'pan-y';
  let ptd = null;
  const yAt = e => e.clientY - cv.getBoundingClientRect().top;
  cv.addEventListener('pointerdown', e => {
    if (!e.button && ptNear(S, yAt(e))) { ptd = { id: e.pointerId }; cv.setPointerCapture(e.pointerId); e.preventDefault(); return; }   // Prüf-Schwelle ziehen
    if (DR.on && !e.button && S.data && S.geo) { pts.clear(); pinch = null; pan = null; S.drag = { a: xAt(e), b: xAt(e), mk: true, del: true }; cv.setPointerCapture(e.pointerId); dtDraw(S); return; }
    if (MK.on && !e.button && S.data && S.geo) { mkClose(); pts.clear(); pinch = null; pan = null; S.drag = { a: xAt(e), b: xAt(e), mk: true }; cv.setPointerCapture(e.pointerId); dtDraw(S); return; }
    pts.set(e.pointerId, xAt(e)); cv.setPointerCapture(e.pointerId);
    if (pts.size === 2 && e.pointerType === 'touch') { S.drag = null; pan = null; return; }   // zwei Finger: bindPinch
    if (pts.size === 2 && S.parent) {                // zwei Finger: zoomen
      const [x1, x2] = [...pts.values()], [wf, wt] = dtWin(tg); S.drag = null; pan = null;
      pinch = { d: Math.max(20, Math.abs(x2 - x1)), fx: fxAt((x1 + x2) / 2), wf, wt }; return;
    }
    if (pts.size > 1) return;
    if (S.parent && tg.from != null && !e.shiftKey) { const [wf, wt] = dtWin(tg); pan = { x: xAt(e), wf, wt, moved: false }; return; }
    S.drag = { a: xAt(e), b: xAt(e) };
  });
  cv.addEventListener('pointermove', e => {
    if (ptd) { const v = ptVal(S, yAt(e)); if (v != null) ptSet(v, false); return; }
    const dh = !MK.on && !DR.on && hitAt(S, xAt(e), yAt(e));   // anklickbar: Unterbrechung, Notiz, Sensor (breite Sensor-Balken nur oben)
    cv.style.cursor = ptNear(S, yAt(e)) ? 'ns-resize' : dh && !S.drag && !pan ? 'pointer' : '';
    cv.title = dh ? dh[2] : '';
    if (pts.has(e.pointerId)) pts.set(e.pointerId, xAt(e));
    if (pts.size > 1 && e.pointerType === 'touch') return;
    if (pinch && pts.size === 2) {
      const [x1, x2] = [...pts.values()], k = pinch.d / Math.max(20, Math.abs(x2 - x1)), sp = pinch.wt - pinch.wf, ns = Math.max(30000, sp * k), c0 = pinch.wf + pinch.fx * sp;
      dtSetWin(tg, c0 - pinch.fx * ns, c0 - pinch.fx * ns + ns); return;
    }
    if (pan) {
      const dx = xAt(e) - pan.x; if (Math.abs(dx) > 3) pan.moved = true; if (!pan.moved || !S.geo) return;
      const sh = -dx / S.geo.pw * (pan.wt - pan.wf); cv.style.cursor = 'grabbing'; dtSetWin(tg, pan.wf + sh, pan.wt + sh); return;
    }
    if (S.drag) { S.drag.b = xAt(e); dtDraw(S); } else dtDraw(S, xAt(e));
  });
  cv.addEventListener('pointerleave', e => { if (e.pointerType === 'mouse') tipHide('day'); if (!S.drag && !pan) { $(S.el.hover).textContent = ''; dtDraw(S); } });
  let dcT = 0;                                       // Klick auf eine Unterbrechung: Kommentar (kurz warten, ein Doppelklick hat Vorrang)
  const downClick = (x, e) => {
    if (MK.on || DR.on || e.type !== 'pointerup') return false;
    const y = yAt(e), h = hitAt(S, x, y); if (!h) return false;
    clearTimeout(dcT); const cx = e.clientX, cy = e.clientY; dcT = setTimeout(() => h[3] && h[3].kind === 'fn' ? fnOpenId(h[3]) : h[3] && h[3].kind === 'ha' ? haPop(h[3]) : rnOpen(h[3], cx, cy), 260); return true;
  };
  const up = e => {
    if (ptd) { ptd = null; ptSet(PT.v, true); return; }
    pts.delete(e.pointerId); cv.style.cursor = '';
    if (pinch) { if (pts.size < 2) { pinch = null; dtLoad(tg, true); } return; }
    const tap = e.pointerType !== 'mouse';             // Finger/Stift: Tippen zeigt die Werte an der Stelle (statt Maus darüber)
    if (pan) { const m = pan.moved, x0 = pan.x; pan = null; if (m) dtLoad(tg, true); else if (!downClick(x0, e)) { if (tap) dtDraw(S, x0); } return; }
    const g = S.geo, r = S.data, dr = S.drag; S.drag = null; if (!g || !r || !dr) return;
    const a = Math.min(dr.a, dr.b), b = Math.max(dr.a, dr.b);
    if (dr.mk) {                                     // markierter Bereich: benennen
      if (b - a < 4 || e.type !== 'pointerup') { dtDraw(S); return; }
      const tq2 = x => r.from + (r.to - r.from) * clamp((x - g.L) / g.pw, 0, 1), ta = tq2(a), tb = tq2(b);
      mkOpen(S.src || selSrc, ta, tb, e.clientX, e.clientY, () => dtDraw(S), { day: S }); dtDraw(S); return;
    }
    if (b - a < 6) { if (downClick(dr.a, e)) { dtDraw(S); return; } if (tap) dtDraw(S, dr.a); else dtDraw(S); return; }
    const tq = x => r.from + (r.to - r.from) * clamp((x - g.L) / g.pw, 0, 1);
    tg.from = tq(a); tg.to = Math.max(tq(b), tg.from + 30000); tg.zoom = true; dtLoad(tg, true);
  };
  cv.addEventListener('pointerup', up); cv.addEventListener('pointercancel', up);
  cv.addEventListener('wheel', e => {                 // Mausrad / Touchpad = zoomen, Umschalt + Rad oder seitlich wischen = scrollen
    e.preventDefault();
    if (!S.parent || !S.data || !S.geo) return;
    const u = wheelPx(e), dx = u * e.deltaX, dy = u * e.deltaY, side = Math.abs(dx) > Math.abs(dy) ? dx : 0;
    if (!side && (e.shiftKey || xAt(e) < S.geo.L)) {  // Umschalt + Mausrad oder über der dB-Beschriftung: Höhe (alle Zeilen), unten bündig
      tg.yk = clamp((tg.yk || 1) * wheelK(dy, e.ctrlKey), 0.02, 1); for (const sub of tg.subs || [tg]) if (sub.data) dtDraw(sub); return;
    }
    if (side && tg.from != null) { const [wf, wt] = dtWin(tg), sh = side / S.geo.pw * (wt - wf); dtSetWin(tg, wf + sh, wt + sh); return; }
    const z = side || dy; if (!z) return;
    dtZoom(tg, wheelK(z, e.ctrlKey), fxAt(xAt(e)));  // Stärke nach Weg: ein Mausrad-Raster ≈ 25 %, Touchpad fein
  }, { passive: false });
  bindPinch(cv, () => S.parent && S.data && S.geo ? dtWin(tg) : null, fxAt, (f, t2) => dtSetWin(tg, f, t2), () => { pts.clear(); pinch = null; pan = null; S.drag = null; }, () => dtLoad(tg, true));
  cv.addEventListener('dblclick', e => { clearTimeout(dcT); reset(e); });
}
/* Kommentar zu einer Unterbrechung direkt im Verlauf: kleines Fenster an der Klickstelle (gleiche Daten wie die Liste in Protokolle) */
const RN = { pop: null, g: null };
function rnClose() { if (RN.pop) RN.pop.hidden = true; RN.g = null; }
function rnOpen(g, cx, cy) {
  if (!g) return; tipHide(); mkClose(); RN.g = g;
  let p = RN.pop;
  if (!p) {
    p = RN.pop = el('div', { id: 'rnpop', className: 'lbpop mkpop rnpop' }); p.setAttribute('role', 'dialog'); p.hidden = true;
    p.innerHTML = `<b id="rntitle"></b><div id="rnsub" class="mksub"></div><input id="rntext" type="text" maxlength="300" autocomplete="off">
      <div class="ntedbtns"><button type="button" id="rndel" class="danger"></button><span class="rngap"></span><button type="button" id="rncancel"></button><button type="button" id="rnsave" class="pri"></button></div>`;
    document.body.appendChild(p);
    const save = async txt => {
      const g2 = RN.g; if (!g2) return;
      try { const r = await (await fetch('run_note', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ key: g2[3], text: txt }) })).json(); if (!r.ok) throw new Error(r.error || 'error'); }
      catch (er) { alert(t('saveerr') + ' ' + er.message); return; }
      rnClose(); loadRun();
    };
    $('rnsave').onclick = () => save($('rntext').value); $('rndel').onclick = () => save(''); $('rncancel').onclick = rnClose;
    $('rntext').addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); save($('rntext').value); } else if (e.key === 'Escape') rnClose(); });
    document.addEventListener('pointerdown', e => { if (!p.hidden && !p.contains(e.target) && !e.target.closest('canvas')) rnClose(); }, true);
  }
  const L = locale(), fm = ms => new Date(ms).toLocaleString(L, { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
  $('rntitle').textContent = '📝 ' + (x => x.charAt(0).toUpperCase() + x.slice(1))(t('dt_norec')) + ' ' + fm(g[0]) + ' – ' + fm(g[1]);
  const ev = g[5] || {}; $('rnsub').textContent = t(ev.reason === 'update' ? 'run_r_update' : g[4] === 'lost' ? 'run_r_lost' : 'run_r_restart');
  $('rntext').value = g[2] || ''; $('rntext').placeholder = t('run_note_ph');
  $('rnsave').textContent = t('save'); $('rncancel').textContent = t('cancel'); $('rndel').textContent = t('run_note_del'); $('rndel').hidden = !g[2];
  p.hidden = false;
  const w = p.offsetWidth, h = p.offsetHeight, vw = document.documentElement.clientWidth, vh = window.innerHeight;
  p.style.left = clamp(cx - w / 2, 8, Math.max(8, vw - w - 8)) + 'px'; p.style.top = (cy + 14 + h > vh - 8 ? Math.max(8, cy - 14 - h) : cy + 14) + 'px';
  $('rntext').focus(); $('rntext').select();
}
/* ================= Verlauf drucken („Notenblatt“): Zeitraum, Zeit je Zeile, Geräte, Inhalt, Format -> Vorschau-Seite ================= */
const PR = (() => { let c = null; try { c = JSON.parse(localStorage.getItem('laerm_pr') || 'null'); } catch (e) { } return Object.assign({ line: 10, lvl: true, spec: false, info: true, skip: true, scale: 'same', o: 'l' }, c && typeof c === 'object' ? c : {}); })();
const prDtl = ms => { const d = new Date(ms); return isoDay(d) + 'T' + pad(d.getHours()) + ':' + pad(d.getMinutes()); };
function prSet(a, b) { $("prfrom").value = prDtl(a); $("prto").value = prDtl(b); prEst(); }
function prVals() {
  const a = new Date($('prfrom').value).getTime(), b = new Date($('prto').value).getTime();
  const devs = [...$('prdevs').querySelectorAll('input:checked')].map(x => x.value);
  return { a, b, devs, line: +$('prline').value, lvl: $('prlvl').checked, spec: $('prspec').checked, info: $('prinfo').checked, skip: $('prskip').checked, scale: $('prscale').value, o: PR.o };
}
function prEst() {
  const v = prVals(), el_ = $('prest');
  if (!(v.b > v.a)) { el_.textContent = t('pr_bad'); el_.className = 'prest warn'; $('prgo').disabled = true; return; }
  if (!v.devs.length || !(v.lvl || v.spec || v.info)) { el_.textContent = t('pr_none'); el_.className = 'prest warn'; $('prgo').disabled = true; return; }
  const lines = Math.ceil((v.b - v.a) / (v.line * 60000));
  const per = (v.lvl ? 22 : 0) + (v.spec ? 14 : 0) + (v.info ? 5 : 0) + (v.devs.length > 1 ? 3 : 0), blk = 6 + per * v.devs.length;
  const pages = Math.max(1, Math.ceil(lines * blk / (v.o === 'p' ? 262 : 175)));
  el_.textContent = t(v.skip ? 'pr_est_max' : 'pr_est', { l: lines, p: pages }) + (PT.v != null ? ' · ' + t('pt_line', { v: f1(PT.v) }) : '') + (pages > 150 ? ' – ' + t('pr_many') : ''); el_.className = 'prest' + (pages > 10 ? ' warn' : '');
  $('prgo').disabled = false;
}
function prOpen() {
  const [wf, wt] = dtWin(DT);
  const rows = new Set((DT.rows || []).map(r => r.src));
  $('prdevs').innerHTML = '';
  for (const s2 of viewSources()) { const l = el('label', { className: 'chip' }), c = el('input', { type: 'checkbox', value: s2.id, checked: rows.size ? rows.has(s2.id) : true }); c.onchange = prEst; l.append(c, document.createTextNode(' ' + s2.name)); $('prdevs').appendChild(l); }
  $('prline').value = String(PR.line); $('prlvl').checked = PR.lvl; $('prspec').checked = PR.spec; $('prinfo').checked = PR.info; $('prskip').checked = PR.skip !== false; $('prscale').value = PR.scale;
  $('prorient').querySelectorAll('button').forEach(b => b.classList.toggle('on', b.dataset.o === PR.o));
  prSet(wf, wt); $('prdlg').showModal();
}
function initPrint() {
  if (!$('prdlg')) return;
  $('ndprint').onclick = prOpen; $('prx').onclick = $('prcancel').onclick = () => $('prdlg').close();
  ['prfrom', 'prto', 'prline', 'prlvl', 'prspec', 'prinfo', 'prskip', 'prscale'].forEach(id => { $(id).addEventListener('input', prEst); $(id).addEventListener('change', prEst); });
  $('prorient').querySelectorAll('button').forEach(b => b.onclick = () => { PR.o = b.dataset.o; $('prorient').querySelectorAll('button').forEach(x => x.classList.toggle('on', x === b)); prEst(); });
  $('prq_view').onclick = () => { const [a, b] = dtWin(DT); prSet(a, b); };
  $('prq_per').onclick = () => { const [a, b] = dtBase(DT); prSet(a, b); };
  $('prq_all').onclick = async () => {
    try { const j = await (await fetch('trackdays', { cache: 'no-store' })).json(); if (j.days && j.days.length) prSet(parseDay(j.days[0]).getTime(), Math.ceil(nowServer() / 60000) * 60000); } catch (e) { }
  };
  $('prgo').onclick = () => {
    const v = prVals(); if (!(v.b > v.a) || !v.devs.length) return;
    Object.assign(PR, { line: v.line, lvl: v.lvl, spec: v.spec, info: v.info, skip: v.skip, scale: v.scale }); try { localStorage.setItem('laerm_pr', JSON.stringify(PR)); } catch (e) { }
    const srcs = v.devs.map(id => [id, viewName(id)]);
    const u = 'druck.html?from=' + v.a + '&to=' + v.b + '&line=' + v.line + '&lvl=' + (v.lvl ? 1 : 0) + '&spec=' + (v.spec ? 1 : 0) + '&info=' + (v.info ? 1 : 0) + '&skip=' + (v.skip ? 1 : 0)
      + '&scale=' + v.scale + '&o=' + v.o + '&pt=' + (PT.v != null ? PT.v : '') + '&lang=' + lang + '&ver=' + encodeURIComponent(((document.querySelector('script[src^="app.js"]') || {}).src || '').split('v=')[1] || '') + '&srcs=' + encodeURIComponent(JSON.stringify(srcs));
    const w = window.open(u, '_blank'); if (!w) alert(t('pr_popup')); else $('prdlg').close();
  };
}
function initDayTrack() {
  initPrint(); initPt();
  if (!$('ndcv')) return;
  bindDay(DT, () => { DT.from = DT.to = null; DT.yk = 1; dtLoad(DT, true); });
  initDtBar(DT);
  $('ndreset').onclick = () => { DT.from = DT.to = null; DT.yk = 1; dtLoad(DT, true); };
  bindLive();
  document.querySelectorAll('.mkbtn').forEach(b => b.onclick = () => mkSet(!MK.on));
  document.querySelectorAll('.drbtn').forEach(b => b.onclick = () => drSet(!DR.on));
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && DR.on) drSet(false); });
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && MK.on && (!MK.pop || MK.pop.hidden)) mkSet(false); });
  window.addEventListener('resize', () => { if (NV.open) dtLoad(DT, true); if (histOn()) { dtDraw(LDT); dtSpec(LDT); } });
}
/* Live-Ansicht zurückspulen: über die Arbeitsspeicher-Grenze (10 min) hinaus oder mit 1 h / 6 h / Heute zeigt die Grafik
   den Tagesverlauf; das Spektrogramm darunter gibt es nur bei Störungen (aus deren Lärmspuren). Ziehen = spulen, Mausrad = Zeitraum, Doppelklick = Live. */
const SPC = {};                                     // Lärmspur-Cache für das Spektrogramm: Datei -> Promise(R)
function histOn() { return LONG_SPAN(view.span) || LDT.hist; }
function syncLongSpan() {
  const on = histOn();
  $('ldaybox').hidden = !on;
  document.querySelectorAll('.cvwrap').forEach(e => e.classList.toggle('longhide', on));
  clearInterval(LDT.timer); LDT.timer = null;
  if (on) {
    dtLoad(LDT, LDT.zoom);
    LDT.timer = setInterval(() => { if (!document.hidden && !NV.open && !PV.open && !LDT.zoom && !LDT.drag) dtLoad(LDT, true); }, 10000);
  }
  markDirty();
}
function histEnter(from, to) {                      // aus dem Live-Bild weiter zurückgespult als der Arbeitsspeicher reicht
  LDT.hist = true; LDT.zoom = true; LDT.from = from; LDT.to = to;
  TILE.manual = true; TILE.at = Date.now();          // Rundlauf steht, solange zurückgespult ist
  syncLongSpan();
}
function histExit() {
  if (!LDT.hist && !LDT.zoom) return;
  LDT.hist = false; LDT.zoom = false;
  if (LONG_SPAN(view.span)) dtLoad(LDT, false); else syncLongSpan();
}
function dtSpec(S) {
  const cv = $('ldsp'), r = S.data; if (!cv || !r || !cv.offsetParent) return;
  fit(cv); const d = DPR(), c = cv.getContext('2d'), w = cv.width, h = cv.height, L = 44 * d, Rr = 10 * d, pw = w - L - Rr;
  const span = r.to - r.from, X = t2 => L + pw * (t2 - r.from) / span;
  c.clearRect(0, 0, w, h); c.fillStyle = C.grid; c.fillRect(L, 0, pw, h);
  c.fillStyle = NC.mut; c.font = (10 * d) + 'px system-ui'; c.textAlign = 'left';
  if (drawSpecInto(c, r, X, 0, h, L, pw, d)) return;  // Spektrum des ganzen Tages gespeichert: durchgehend zeigen
  if (span > 3 * 3600000) { c.fillText(t('dt_spec_zoom'), L + 6 * d, h / 2 + 3 * d); return; }
  if (!(r.sp || []).length) { c.fillText(t('dt_spec_none'), L + 6 * d, h / 2 + 3 * d); return; }
  let vis = r.sp.filter(x => x[1] >= r.from && x[0] <= r.to);
  if (vis.length > 60) { const k = vis.length / 60; vis = Array.from({ length: 60 }, (_, i) => vis[Math.floor(i * k)]); }   // gleichmäßig verteilt, nicht nur die ersten
  for (const x of vis) {
    if (!SPC[x[2]]) {
      const e = SPC[x[2]] = { v: undefined };
      fetch('spur?f=' + encodeURIComponent(x[2]), { cache: 'force-cache' }).then(q => q.ok ? q.json() : null).then(g => g && g.recs && g.recs.length ? { g, R: evDecode(g) } : null)
        .catch(() => null).then(v2 => { e.v = v2; if (v2) dtSpec(S); });
    }
    const v = SPC[x[2]].v; if (!v) continue;
    if (!v.tc) {                                    // Bild der Spur einmal berechnen (feste Farbskala 0,5 dB ab -130 dBFS)
      const R = v.R, nb = R.nb || NB, tc = document.createElement('canvas'); tc.width = R.length; tc.height = nb;
      const img = tc.getContext('2d').createImageData(R.length, nb), px = img.data, lo = 2 * (-110 + 130), hi = 2 * (-30 + 130);
      R.forEach((q, xx) => { for (let k = 0; k < nb; k++) { const cc = cmap((q.sp[k] - lo) / (hi - lo)), o = 4 * ((nb - 1 - k) * R.length + xx); px[o] = cc[0]; px[o + 1] = cc[1]; px[o + 2] = cc[2]; px[o + 3] = 255; } });
      tc.getContext('2d').putImageData(img, 0, 0); v.tc = tc;
    }
    const R = v.R, stp = R.step || 125, a = v.g.t0 + R[0].o - stp, b = v.g.t0 + R[R.length - 1].o;
    c.save(); c.beginPath(); c.rect(L, 0, pw, h); c.clip(); c.imageSmoothingEnabled = true; c.drawImage(v.tc, X(a), 0, Math.max(1, X(b) - X(a)), h); c.restore();
  }
}
function bindLive() {
  const cv = $('ldcv'), S = LDT; if (!cv) return;
  const xAt = e => e.clientX - cv.getBoundingClientRect().left;
  let lastLoad = 0;
  cv.addEventListener('pointerdown', e => {
    if (!S.data) return;
    if (MK.on && !e.button && S.geo) { mkClose(); S.drag = { a: xAt(e), b: xAt(e), mk: true }; cv.setPointerCapture(e.pointerId); dtDraw(S); return; }
    S.drag = { x: xAt(e), from: S.data.from, to: S.data.to, moved: false }; cv.setPointerCapture(e.pointerId);
  });
  cv.addEventListener('pointermove', e => {
    if (!S.drag) { dtDraw(S, xAt(e)); return; }
    if (S.drag.mk) { S.drag.b = xAt(e); dtDraw(S); return; }
    const g = S.geo; if (!g) return;
    const dx = xAt(e) - S.drag.x; if (Math.abs(dx) > 3) S.drag.moved = true; if (!S.drag.moved) return;
    const span = S.drag.to - S.drag.from, sh = -dx / g.pw * span, now = nowServer();
    let f = S.drag.from + sh, t2 = S.drag.to + sh; if (t2 > now) { t2 = now; f = now - span; }
    S.from = f; S.to = t2; S.zoom = true;
    S.data = Object.assign({}, S.data, { from: f, to: t2 }); dtDraw(S); dtSpec(S);
    if (Date.now() - lastLoad > 300) { lastLoad = Date.now(); dtLoad(S, true); }
  });
  const up = e => {
    if (S.drag && S.drag.mk) {
      const dr = S.drag, g = S.geo, r = S.data; S.drag = null; const a = Math.min(dr.a, dr.b), b = Math.max(dr.a, dr.b);
      if (!g || !r || b - a < 4 || e.type !== 'pointerup') { dtDraw(S); return; }
      const tq2 = x => r.from + (r.to - r.from) * clamp((x - g.L) / g.pw, 0, 1);
      if (dr.del) { drOpen(S.src || NV.src || 'all', tq2(a), tq2(b)); dtDraw(S); return; }
      mkOpen(selSrc, tq2(a), tq2(b), e.clientX, e.clientY, () => dtDraw(S), { day: S }); dtDraw(S); return;
    }
    if (S.drag && S.drag.moved) {
      if (S.to >= nowServer() - 2000) { S.drag = null; if (!LONG_SPAN(view.span)) { goLive(); return; } S.zoom = false; }   // bis jetzt gespult: wieder live
      S.drag = null; dtLoad(S, true); return;
    }
    S.drag = null;
  };
  cv.addEventListener('pointerup', up); cv.addEventListener('pointercancel', up);
  cv.addEventListener('pointerleave', e => { if (e.pointerType === 'mouse') tipHide('day'); if (!S.drag) { $(S.el.hover).textContent = ''; dtDraw(S); } });
  cv.addEventListener('wheel', e => {
    e.preventDefault(); if (!S.data || !S.geo) return;
    const u = wheelPx(e), side = Math.abs(e.deltaX) > Math.abs(e.deltaY), z = side ? u * e.deltaX : u * e.deltaY; if (!z) return;
    if (!side && (e.shiftKey || xAt(e) < S.geo.L)) { S.yk = clamp((S.yk || 1) * wheelK(z, e.ctrlKey), 0.02, 1); dtDraw(S); return; }   // Höhe
    if (side) { const sh = z / S.geo.pw * (S.data.to - S.data.from); setWin(S.data.from + sh, S.data.to + sh); return; }   // seitlich wischen: verschieben
    if (!LDT.hist && (!S.zoom || S.data.to >= nowServer() - 3000)) {   // läuft bis „jetzt“: Zeitfenster zoomen, rechter Rand bleibt jetzt (unter 10 min wieder das normale Live-Bild)
      setSpan(clamp(Math.round(view.span * wheelK(z, e.ctrlKey)), 5, 86400)); return;
    }
    const r = S.data, span = r.to - r.from, ns = clamp(span * wheelK(z, e.ctrlKey), 60000, 2 * 86400000);
    const fx = clamp((xAt(e) - S.geo.L) / S.geo.pw, 0, 1), c0 = r.from + fx * span;
    setWin(c0 - fx * ns, c0 - fx * ns + ns);
  }, { passive: false });
  const setWin = (f, t2) => {                          // nicht über „jetzt“ hinaus; Daten gedrosselt nachladen
    const ns = clamp(t2 - f, 60000, 2 * 86400000), now = nowServer(); t2 = f + ns; if (t2 > now) { t2 = now; f = now - ns; }
    S.from = f; S.to = t2; S.zoom = true; S.data = Object.assign({}, S.data, { from: f, to: t2 }); dtDraw(S); dtSpec(S);
    if (Date.now() - lastLoad > 300) { lastLoad = Date.now(); dtLoad(S, true); }
  };
  bindPinch(cv, () => S.data && S.geo ? [S.data.from, S.data.to] : null, x => S.geo ? clamp((x - S.geo.L) / S.geo.pw, 0, 1) : 0.5, setWin, () => { S.drag = null; }, () => dtLoad(S, true));
  const back = () => { S.yk = 1; if (LONG_SPAN(view.span)) setSpan(view.preset && !LONG_SPAN(view.preset) ? view.preset : 60); goLive(); };     // ● Live: zurück zum normalen Live-Bild
  cv.addEventListener('dblclick', back);
  $('ldlive').onclick = back;
}
/* ================= Dashboard: Ereignisse des Tages als einfache Liste (Spalten und Gerät einstellbar, pro Browser gemerkt) ================= */
const LEV_COLS = ['tm', 'src', 'art', 'kinds', 'devs', 'dur', 'pk', 'thr', 'bg', 'nt'];
const LEV = (() => { let c = null; try { c = JSON.parse(localStorage.getItem('laerm_lev') || 'null'); } catch (e) { } c = c && typeof c === 'object' ? c : {};
  return { cols: Array.isArray(c.cols) ? c.cols.filter(x => LEV_COLS.includes(x)) : ['tm', 'src', 'art', 'devs', 'dur', 'pk', 'bg', 'nt'], src: c.src === 'sel' ? 'sel' : 'all', key: '', data: null, req: 0 }; })();
function levSave() { try { localStorage.setItem('laerm_lev', JSON.stringify({ cols: LEV.cols, src: LEV.src })); } catch (e) { } }
function levHead(c) { return { tm: t('start'), src: t('src_col'), art: t('art_col'), kinds: t('kinds_col'), devs: t('devs_col'), dur: t('dur'), pk: t('peak'), thr: t('thr_col'), bg: t('bg_col'), nt: '📝' }[c]; }
async function levLoad(force) {
  if (NV.open || !$('ldev')) return;                 // nur im Live-Reiter
  const now = new Date(nowServer()), day = isoDay(now), nx = new Date(now); nx.setDate(nx.getDate() + 1);
  const src = LEV.src === 'sel' ? selSrc : 'all', key = [lastCount, src, day].join('|');
  if (!force && key === LEV.key) return; LEV.key = key;
  const id = ++LEV.req;
  try { const j = await (await fetch('events?src=' + encodeURIComponent(src) + '&n=150&from=' + day + 'T00:00&to=' + isoDay(nx) + 'T00:00', { cache: 'no-store' })).json(); if (id !== LEV.req) return; LEV.data = j; levRender(); } catch (e) { LEV.key = ''; }
}
function levRender() {
  const j = LEV.data, tb = $('ldev'); if (!j) return;
  const evs = (j.events || []).filter(r => r.lead !== false);          // je Störung eine Zeile (lautestes Gerät), wie in Protokolle
  const multi = evs.some(r => (r.devs || []).length > 1);              // Spalte „Geräte (Spitze)“ nur, wenn sie etwas zeigt
  const useArt = !CUR || CUR.classify !== false, cols = LEV.cols.filter(c => (useArt || (c !== 'art' && c !== 'kinds')) && (c !== 'devs' || multi));
  $('ldevn').textContent = t('lev_n', { n: j.total != null ? j.total : evs.length });
  const hm = iso => { const d = new Date(iso); return isNaN(d) ? String(iso || '') : pad(d.getHours()) + ':' + pad(d.getMinutes()) + ':' + pad(d.getSeconds()); };
  const cell = (c, r) => c === 'tm' ? `<td class="tm">${esc(hm(r.start))}</td>` : c === 'src' ? srcCell(r)
    : c === 'art' ? `<td class="artc">${r.prof ? `<span class="art prof${r.bg ? ' bgp' : ''}">🧩 ${esc(r.prof)}${r.prof_ok ? ' ✓' : r.prof_c != null ? ` <small>${r.prof_c} %</small>` : ''}</span>` : ''}${(r.labels || []).map(n => `<span class="art lbl">🏷 ${esc(n)}</span>`).join('')}${r.art ? artChip(r.art, r.art_c, r.art_man) : r.prof ? '' : '<span class="noclip">–</span>'}</td>`
    : c === 'devs' ? `<td class="devc">${(r.devs || []).length > 1 ? r.devs.map((x, i) => `<span class="dvp${i === 0 ? ' top' : ''}">${esc(shortName(x[1]))} ${x[2] != null ? x[2].toFixed(0) : '–'}</span>`).join('') : '<span class="noclip">–</span>'}</td>`
    : c === 'kinds' ? `<td class="kinds">${kindsHTML(r.kinds, j.fine)}</td>` : c === 'dur' ? `<td class="dur">${esc(fmtDur(r.dauer_s))}</td>`
    : c === 'pk' ? `<td class="pk">${esc(fdb(r.spitze_dbfs))} <small>dBFS</small></td>` : c === 'thr' ? `<td class="thr">${esc(fdb(r.schwelle_dbfs))}</td>`
    : c === 'bg' ? `<td class="bgc">${esc(fdb(r.hintergrund_dbfs))}</td>` : `<td class="ntcol">${r.notes ? '📝 ' + r.notes : ''}</td>`;
  tb.innerHTML = `<thead><tr>${cols.map(c => `<th>${esc(levHead(c))}</th>`).join('')}</tr></thead><tbody>` +
    (evs.length ? evs.map(r => `<tr data-k="${esc(r.k || '')}"${r.bg || r.inc_bg ? ' class="bgrow"' : ''}>${cols.map(c => cell(c, r)).join('')}</tr>`).join('') : `<tr><td colspan="${cols.length || 1}" class="empty">${esc(t('lev_none'))}</td></tr>`) + '</tbody>';
  tb.querySelectorAll('tr[data-k]').forEach(tr => tr.onclick = () => { if (tr.dataset.k) openEvent(tr.dataset.k); });
}
function levCols() {
  const box = $('ldevcols');
  box.innerHTML = LEV_COLS.map(c => `<label class="chip"><input type="checkbox" data-c="${c}"${LEV.cols.includes(c) ? ' checked' : ''}> ${esc(levHead(c))}</label>`).join('');
  box.querySelectorAll('input').forEach(i => i.onchange = () => { LEV.cols = LEV_COLS.filter(c => box.querySelector(`input[data-c="${c}"]`).checked); levSave(); levRender(); });
}
function initLev() {
  if (!$('ldev')) return;
  $('ldevsrc').value = LEV.src;
  $('ldevsrc').onchange = () => { LEV.src = $('ldevsrc').value; levSave(); levLoad(true); };
  $('ldevcfg').onclick = () => { const b = $('ldevcols'); b.hidden = !b.hidden; if (!b.hidden) levCols(); };
}
/* ================= Freie Notiz („📝 Notiz jetzt“): einmal gespeichert, mit Zeitraum, an allen Aufzeichnungen dieser Zeit sichtbar ================= */
const FN = { list: [], edit: null, tags: new Set(), t: 0 };
const dtl = d => isoDay(d) + 'T' + pad(d.getHours()) + ':' + pad(d.getMinutes()) + ':' + pad(d.getSeconds());
async function fnOpenId(h) {                        // Notiz aus dem Verlauf öffnen (vollständig vom Server holen)
  try { const j = await (await fetch('fnotes?from=' + (h.a - 1000) + '&to=' + (h.b + 1000) + '&src=all', { cache: 'no-store' })).json(); const n = (j.notes || []).find(x => x.id === h.id); if (n) return fnOpen(n); } catch (e) { }
  toast(t('saveerr'));
}
function haPop(h) {                                  // Sensor aus Home Assistant angeklickt: Notiz zu diesem Zeitraum schreiben/ändern
  let d = $('hapop'); if (!d) { d = el('dialog', { id: 'hapop', className: 'evdlg prognd' }); document.body.appendChild(d); }
  const L = locale(), dur = Math.max(0, (h.b - h.a) / 1000), fdur = dur < 120 ? Math.round(dur) + ' s' : dur < 7200 ? Math.round(dur / 60) + ' min' : Math.floor(dur / 3600) + ' h ' + Math.round(dur % 3600 / 60) + ' min';
  d.innerHTML = `<h3>📡 ${esc(h.name)}</h3><p><b>${esc(new Date(h.a).toLocaleDateString(L))} · ${esc(hms(h.a))}–${esc(hms(h.b))}</b> · ${esc(fdur)} · ${esc(t('ha_on'))}</p>
    <label class="drl">${esc(t('ha_note'))}<textarea id="hanote" rows="2" maxlength="300" placeholder="${esc(t('ha_note_ph'))}"></textarea></label>
    <p class="mut">${esc(t('ha_pop_hint'))}</p>
    <div class="ntedbtns"><button type="button" class="hpl">${esc(t('ha_to_list'))}</button><span style="flex:1"></span>${h.note ? `<button type="button" class="danger hpd">${esc(t('run_note_del'))}</button>` : ''}<button type="button" class="hpx">${esc(t('cancel'))}</button><button type="button" class="pri hps">${esc(t('save'))}</button></div>`;
  const ta = d.querySelector('#hanote'); ta.value = h.note || '';
  const save = async txt => {
    try { const j = await (await fetch('ha_note', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ key: h.key || h.rid + '|' + h.a, text: txt }) })).json(); if (!j.ok) throw new Error(j.error); }
    catch (e) { alert(t('saveerr') + ' ' + e.message); return; }
    d.close(); if (NV.open) loadNight(); dtLoad(DT, true); EVSIG = ''; loadEvents();
  };
  d.querySelector('.hps').onclick = () => save(ta.value.trim());
  if (d.querySelector('.hpd')) d.querySelector('.hpd').onclick = () => save('');
  d.querySelector('.hpx').onclick = () => d.close();
  d.querySelector('.hpl').onclick = () => { d.close(); const row = document.querySelector(`.har[data-a="${h.a}"]`); if (row) { row.scrollIntoView({ behavior: 'smooth', block: 'center' }); row.classList.add('flash'); setTimeout(() => row.classList.remove('flash'), 1500); } };
  ta.onkeydown = e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); save(ta.value.trim()); } };
  d.showModal(); setTimeout(() => ta.focus(), 50);
}
function fnOpen(n) {
  FN.fromPanel = false; FN.edit = n && n.id ? n : null; FN.tags = new Set((n && n.tags) || []);
  $('fnfrom').value = n && n.from ? dtl(new Date(n.from)) : dtl(new Date(nowServer()));     // „von“ = Zeitpunkt des Öffnens
  $('fnto').value = n && n.to ? dtl(new Date(n.to)) : '';
  const sel = $('fnsrc'); sel.innerHTML = ''; option(sel, 'all', t('all_sources')); SOURCES.forEach(x => option(sel, x.id, x.name));
  let last = 'all'; try { last = localStorage.getItem('laerm_fnsrc') || 'all'; } catch (e) { }
  sel.value = n && n.src ? n.src : (SOURCES.some(x => x.id === last) ? last : 'all');
  $('fntext').value = (n && n.text) || ''; $('fnwit').value = (n && n.witness) || '';
  $('fntags').innerHTML = Object.keys(NOTE_TAGS).map(g => NOTE_TAGS[g].map(tg => `<button type="button" class="chip ntchip g-${g}${FN.tags.has(tg) ? ' on' : ''}" data-t="${tg}">${esc(t('nt_' + tg))}</button>`).join('')).join('');
  $('fntags').querySelectorAll('.ntchip').forEach(b => b.onclick = () => { const tg = b.dataset.t; FN.tags.has(tg) ? FN.tags.delete(tg) : FN.tags.add(tg); b.classList.toggle('on'); $('fnwit').hidden = !FN.tags.has('zeuge'); });
  $('fnwit').hidden = !FN.tags.has('zeuge'); $('fndel').hidden = !FN.edit; $('fnmsg').textContent = '';
  $('fndlg').showModal(); setTimeout(() => $('fntext').focus(), 50);
}
async function fnSave(del) {
  const body = del ? { action: 'del', id: FN.edit.id } : { action: FN.edit ? 'edit' : 'add', id: FN.edit ? FN.edit.id : '', from: $('fnfrom').value, to: $('fnto').value, src: $('fnsrc').value, text: $('fntext').value, tags: [...FN.tags], witness: $('fnwit').value };
  if (del && !confirm(t('fn_del_q'))) return;
  try {
    const r = await (await fetch('fnote', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })).json();
    if (!r.ok) { $('fnmsg').textContent = t(r.error === 'empty' ? 'fn_empty' : r.error === 'to' ? 'fn_bad_to' : 'saveerr'); return; }
    try { localStorage.setItem('laerm_fnsrc', $('fnsrc').value); } catch (e) { }
    $('fndlg').close(); fnRefresh(); if (FN.fromPanel && !del) fnpReset(); FN.fromPanel = false;
    if (NV.open) loadNight(); if (histOn()) dtLoad(LDT, true);
    if ($('evdlg').open && EVV.k) openEvent(EVV.k);
  } catch (e) { $('fnmsg').textContent = t('saveerr'); }
}
async function fnRefresh() {                         // Notizen der letzten Minuten fürs Live-Bild
  const now = nowServer(); FN.t = Date.now();
  try { FN.list = (await (await fetch('fnotes?from=' + (now - 3600000) + '&to=' + (now + 60000) + '&src=' + encodeURIComponent(selSrc), { cache: 'no-store' })).json()).notes || []; } catch (e) { }
  markDirty();
}
/* Markierung einer freien Notiz in einer Grafik: Band von–bis, gestrichelte Linie, 📝 und (wenn Platz) der Text */
function fnMarks(c, list, X, T, ph, L, pw, d, wide) {
  c.save(); c.beginPath(); c.rect(L, 0, pw, T + ph); c.clip();
  let lastX = -1e9;
  for (const n of list || []) {
    const a = Array.isArray(n) ? n[0] : n.a, b = Array.isArray(n) ? n[1] : n.b, tx = Array.isArray(n) ? n[2] : n.text;
    const x0 = X(a), x1 = Math.max(x0 + 2 * d, X(b)); if (x1 < L || x0 > L + pw) continue;
    c.fillStyle = 'rgba(112,72,232,0.12)'; c.fillRect(x0, T, x1 - x0, ph);
    c.strokeStyle = '#7048e8'; c.lineWidth = 1.5 * d; c.setLineDash([3 * d, 3 * d]); c.beginPath(); c.moveTo(x0, T); c.lineTo(x0, T + ph); c.stroke(); c.setLineDash([]);
    c.font = '600 ' + (11 * d) + 'px system-ui'; c.textAlign = 'left'; c.fillStyle = '#7048e8';
    const lab = '📝' + (wide && tx ? ' ' + (tx.length > 28 ? tx.slice(0, 27) + '…' : tx) : '');
    if (x0 - lastX > 20 * d) { c.fillText(lab, x0 + 3 * d, T + 13 * d); lastX = x0 + c.measureText(lab).width; }
  }
  c.restore();
}
function drawFnLive(cv, t0, t1) {
  if (!FN.list.length) return;
  const d = DPR(), c = cv.getContext('2d'), w = cv.width, h = cv.height, L = AXL() * d, R = 14 * d, T = 10 * d, B = 22 * d, pw = w - L - R, ph = h - T - B;
  const src = selSrc; fnMarks(c, FN.list.filter(n => (n.src || 'all') === 'all' || n.src === src), ts => L + pw * (ts - t0) / (t1 - t0), T, ph, L, pw, d, (t1 - t0) <= 20 * 60000);
}
function renderEvFn(list) {
  const box = $('evfnbox'); list = list || []; box.hidden = !list.length; if (!list.length) return;
  $('evfnhead').textContent = t('fn_in_ev', { n: list.length });
  $('evfnlist').innerHTML = list.map((n, i) => `<div class="ntrow" data-i="${i}"><span class="ntnum" style="background:#7048e8">📝</span><span class="ntoff">${esc(n.clock)}${n.to ? '–' + esc(n.clock_to) : ''}</span><span class="nttx">${(n.tags || []).map(ntTag).join('')}${n.text ? `<span class="ntt">${esc(n.text)}</span>` : ''}${n.witness ? `<span class="ntw">👤 ${esc(n.witness)}</span>` : ''}</span><span class="ntact">✎</span></div>`).join('');
  $('evfnlist').querySelectorAll('.ntrow').forEach(r => r.onclick = () => fnOpen(list[+r.dataset.i]));
}
/* Notiz-Leiste oben im Live-Bild: einklappbar, sofort tippbar; „von“ = Moment der ersten Eingabe */
const FNP = { from: null, tags: new Set(), tick: null };
function fnpTags() {
  const few = innerWidth < 700 && !FNP.more;               // Handy: nur die ersten Merkmale (und gewählte), Rest über „Mehr …“
  let k = 0;
  $('fnptags').innerHTML = Object.keys(NOTE_TAGS).map(g => NOTE_TAGS[g].map(tg => (few && k++ >= 6 && !FNP.tags.has(tg)) ? '' : `<button type="button" class="chip ntchip g-${g}${FNP.tags.has(tg) ? ' on' : ''}" data-t="${tg}">${esc(t('nt_' + tg))}</button>`).join('')).join('')
    + (innerWidth < 700 ? `<button type="button" class="chip fnpmoretags">${esc(t(few ? 'fnp_tags_more' : 'fnp_tags_less'))}</button>` : '');
  const mb = $('fnptags').querySelector('.fnpmoretags'); if (mb) mb.onclick = () => { FNP.more = !FNP.more; fnpTags(); };
  $('fnptags').querySelectorAll('.ntchip').forEach(b => b.onclick = () => { fnpStart(); const tg = b.dataset.t; FNP.tags.has(tg) ? FNP.tags.delete(tg) : FNP.tags.add(tg); b.classList.toggle('on'); $('fnpwit').hidden = !FNP.tags.has('zeuge'); });
}
function fnpSrc() {
  const sel = $('fnpsrc'), cur = sel.value; sel.innerHTML = ''; option(sel, 'all', t('all_sources')); SOURCES.forEach(x => option(sel, x.id, x.name));
  let last = cur || 'all'; if (!cur) try { last = localStorage.getItem('laerm_fnsrc') || 'all'; } catch (e) { }
  sel.value = [...sel.options].some(o => o.value === last) ? last : 'all';
}
function fnpStart() { if (FNP.from == null) { FNP.from = nowServer(); fnpShow(); fnpTarget(); } }
async function fnpTarget() {                           // Vorschau: welcher Störung die Notiz zugeordnet wird
  if (FNP.from == null) { FNP.tgt = null; return; }
  try { const j = await (await fetch('fnote_target?at=' + Math.round(FNP.from) + '&src=' + encodeURIComponent($('fnpsrc').value), { cache: 'no-store' })).json(); FNP.tgt = j.target; } catch (e) { FNP.tgt = null; }
  fnpShow();
}
function fnpShow() {
  const hm = ts => { const d = new Date(ts); return pad(d.getHours()) + ':' + pad(d.getMinutes()) + ':' + pad(d.getSeconds()); };
  const tg = !$('fnprun').checked && FNP.tgt;           // ohne eigene Zeit: wird der letzten Störung zugeordnet
  $('fnpfrom').textContent = FNP.from == null ? t(matchMedia('(pointer:coarse)').matches ? 'fnp_wait_m' : 'fnp_wait')
    : tg ? t('fnp_to_ev', { t: tg.clock, d: tg.devs.map(d => d[0] + (d[1] != null ? ' ' + d[1].toFixed(0) : '')).join(', '), k: tg.prof ? tg.kind : (tg.kind && tg.kind !== '?' ? artName(tg.kind) : '') })
    : t('fnp_from', { t: hm(FNP.from) }) + ($('fnprun').checked ? ' – ' + hm(nowServer()) : '');
  $('fnpfrom').classList.toggle('on', FNP.from != null);
}
function fnpReset() { FNP.from = null; FNP.tgt = null; FNP.tags = new Set(); $('fnptext').value = ''; $('fnpwit').value = ''; $('fnpwit').hidden = true; $('fnprun').checked = false; fnpTags(); fnpShow(); }
function fnpFold(open) {
  $('fnpbody').hidden = !open; $('fnptog').setAttribute('aria-expanded', open ? 'true' : 'false'); $('fnpanel').classList.toggle('shut', !open);
  try { localStorage.setItem('laerm_fnp', open ? '1' : '0'); } catch (e) { }
}
async function fnpSave() {
  const from = FNP.from == null ? nowServer() : FNP.from;
  const run = $('fnprun').checked;
  const body = { action: 'add', id: '', from: dtl(new Date(from)), to: run ? dtl(new Date(nowServer())) : '', src: $('fnpsrc').value, text: $('fnptext').value, tags: [...FNP.tags], witness: $('fnpwit').value, auto: !run };
  const msg = $('fnpmsg'); msg.className = 'fnpmsg';
  try {
    const r = await (await fetch('fnote', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })).json();
    if (!r.ok) { msg.textContent = t(r.error === 'empty' ? 'fn_empty' : r.error === 'to' ? 'fn_bad_to' : 'saveerr'); msg.classList.add('err'); return; }
    try { localStorage.setItem('laerm_fnsrc', $('fnpsrc').value); } catch (e) { }
    fnpReset(); msg.textContent = '✓ ' + (r.target ? t('fnp_saved_ev', { t: r.target.clock }) : t('fnp_saved')); setTimeout(() => { if (msg.textContent.startsWith('✓')) msg.textContent = ''; }, 4000);
    fnRefresh(); if (histOn()) dtLoad(LDT, true);
  } catch (e) { msg.textContent = t('saveerr'); msg.classList.add('err'); }
}
function initFnp() {
  if (!$('fnpanel')) return;
  let open = innerWidth >= 700; try { const v = localStorage.getItem('laerm_fnp'); if (v != null) open = v !== '0'; } catch (e) { }   // Handy: zu, damit das Live-Bild oben steht
  fnpFold(open); fnpTags(); fnpSrc(); fnpShow();
  $('fnptog').onclick = () => { const o = $('fnpbody').hidden; fnpFold(o); if (o) $('fnptext').focus(); };
  $('fnptext').addEventListener('input', () => { if ($('fnptext').value.trim()) fnpStart(); });
  $('fnprun').onchange = () => { fnpStart(); fnpShow(); };
  $('fnpsrc').addEventListener('change', fnpTarget);
  $('fnpsave').onclick = fnpSave;
  $('fnptext').addEventListener('keydown', e => { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) { e.preventDefault(); fnpSave(); } });
  $('fnpmore').onclick = () => {                     // ausführlich: Dialog mit von/bis, Inhalt wird mitgenommen
    const from = FNP.from == null ? nowServer() : FNP.from;
    fnOpen({ from, to: $('fnprun').checked ? nowServer() : null, src: $('fnpsrc').value, text: $('fnptext').value, tags: [...FNP.tags], witness: $('fnpwit').value });
    FN.fromPanel = true;
  };
  FNP.tick = setInterval(() => { if ($('fnprun').checked && !document.hidden) fnpShow(); }, 1000);
  if (open && !matchMedia('(pointer:coarse)').matches) setTimeout(() => { if (!document.activeElement || document.activeElement === document.body) $('fnptext').focus({ preventScroll: true }); }, 300);   // am PC sofort lostippen
}
/* ================= Profile: aufnehmen (Ruhepegel, dann jeder Ausschlag je Gerät), verwalten, neu untersuchen ================= */
const PF = { list: [], timer: 0, st: null, skip: new Set() };
async function pfLoad() {
  try { const j = await (await fetch('profiles', { cache: 'no-store' })).json(); PF.list = j.profiles || []; PF.st = j.teach; PF.scan = j.scan; } catch (e) { }
  pfRender(); pfTeachRender(); scanRender();
}
function pfScanRange() {                             // Zeitraum: im Reiter Protokolle der gewählte, sonst heute
  if (NV.open) {
    const r = perRange();
    if (r) return [new Date(r[0]).getTime(), new Date(r[1]).getTime()];
    const d = NV.data; if (d && d.start) return [new Date(d.start).getTime(), new Date(d.end).getTime()];
  }
  const a = parseDay(isoDay(new Date(nowServer()))).getTime(); return [a, a + 86400000];
}
function pfOpen(sec) {
  pfLoad();
  const [a, b] = pfScanRange(); $('scanper').textContent = t('scan_per', { r: dtRangeTxt({ from: a, to: b }) });
  const dv = $('pfdevs'); dv.innerHTML = '';
  dv.appendChild(el('span', { className: 'caldl', textContent: t('cal_devs') }));
  SOURCES.forEach(x => { const l = el('label', { className: 'chip' }), c = el('input', { type: 'checkbox', checked: true }); c.dataset.id = x.id; l.append(c, document.createTextNode(' ' + x.name)); dv.appendChild(l); });
  if (!$('profdlg').open) $('profdlg').showModal();
  if (sec === 'teach') setTimeout(() => $('pfname').focus(), 60);
  if (sec === 'scan') setTimeout(() => $('pfscan').scrollIntoView({ block: 'start' }), 60);
  if (sec === 'list') setTimeout(() => $('pflist').scrollIntoView({ block: 'start' }), 60);
}
function pfRender() {
  { const sel = $('scanname'), cur = sel.value; sel.innerHTML = ''; option(sel, '', t('scan_all')); PF.list.forEach(p => option(sel, p.name, p.name)); sel.value = PF.list.some(p => p.name === cur) ? cur : ''; }
  $('pfnames').innerHTML = PF.list.map(p => `<option value="${esc(p.name)}">`).join('');
  const nm = id => viewName(id);
  $('pflist').innerHTML = PF.list.length ? PF.list.map((p, i) => `<div class="pfitem${p.bg ? ' bg' : ''}" data-i="${i}">
      <b class="pfn">🧩 ${esc(p.name)}</b>
      <span class="pfc">${esc(t('pf_n', { n: p.n }))}${Object.keys(p.dev).length ? ' · ' + Object.entries(p.dev).map(([k, v]) => esc(nm(k)) + ' ' + v).join(' · ') : ''}${p.lb ? ' · 🏷 ' + p.lb : ''}</span>
      <label class="chip pfbg" title="${esc(t('pf_bg_tip'))}"><input type="checkbox" class="pfbgc"${p.bg ? ' checked' : ''}> ${esc(t('pf_bg'))}</label>
      <button type="button" class="chip pfmore">＋</button><button type="button" class="chip pfren">✎</button><button type="button" class="chip danger pfdel">🗑</button></div>`).join('')
    : `<div class="ntnone">${esc(t('pf_none'))}</div>`;
  $('pflist').querySelectorAll('.pfitem').forEach(it => {
    const p = PF.list[+it.dataset.i];
    it.querySelector('.pfbgc').onchange = e => pfPost({ action: 'bg', name: p.name, on: e.target.checked });
    it.querySelector('.pfmore').onclick = () => { $('pfname').value = p.name; $('pfname').focus(); $('pfteach').scrollIntoView({ block: 'start' }); };
    it.querySelector('.pfren').onclick = () => { const to = prompt(t('pf_ren_q'), p.name); if (to && to.trim() && to.trim() !== p.name) pfPost({ action: 'rename', name: p.name, to: to.trim() }); };
    it.querySelector('.pfdel').onclick = () => { if (confirm(t('pf_del_q', { n: p.name }))) pfPost({ action: 'delete', name: p.name }); };
  });
}
async function pfPost(body) {
  try { const r = await (await fetch('profile', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })).json();
    if (r.profiles) PF.list = r.profiles; pfRender(); EVSIG = ''; if (NV.open) loadEvents(); } catch (e) { alert(t('saveerr')); }
}
function pfTeachRender() {
  const st = PF.st || { state: 'idle' }, box = $('pfstate'), act = $('pfact'), res = $('pfres');
  const run = st.state === 'quiet' || st.state === 'armed', done = st.state === 'done';
  $('pfstart').hidden = run || done; $('pfdevs').hidden = run || done; box.hidden = !(run || done); act.hidden = !(run || done);
  $('pfstop').hidden = !run;
  if (!(run || done)) { res.innerHTML = ''; return; }
  const n = (st.groups || []).length;
  box.className = 'pfstate calst run' + (st.state === 'armed' ? ' go' : '');
  box.textContent = st.state === 'quiet' ? t('pf_quiet', { s: Math.max(0, Math.ceil((st.q1 - st.now) / 1000)) })
    : st.state === 'armed' ? t('pf_armed', { n, s: st.left_s }) : t('pf_done', { n });
  if (done) box.className = 'pfstate calst';
  const nm = id => (st.names || {})[id] || id;
  res.innerHTML = n ? `<div class="pfscroll"><table class="caltab"><thead><tr><th></th><th>#</th><th>${esc(t('start'))}</th>${(st.ids || []).map(id => `<th>${esc(nm(id))}</th>`).join('')}</tr></thead><tbody>` +
    st.groups.map((g, i) => `<tr><td><input type="checkbox" class="pfsk" data-i="${i}"${PF.skip.has(i) ? '' : ' checked'}></td><td>${i + 1}</td><td>${esc(g.at)}</td>${(st.ids || []).map(id => { const d = g.dev[id];
      return `<td>${d ? '✓ ' + esc(t('pf_heard', { d: (d.over >= 0 ? '+' : '') + d.over.toFixed(0) })) : '<span class="noclip">' + esc(t('pf_not_heard')) + '</span>'}</td>`; }).join('')}</tr>`).join('') + '</tbody></table></div>' : '';
  res.querySelectorAll('.pfsk').forEach(c => c.onchange = () => { const i = +c.dataset.i; c.checked ? PF.skip.delete(i) : PF.skip.add(i); });
  $('pfok').disabled = !n;
  clearTimeout(PF.timer); if (run && $('profdlg').open) PF.timer = setTimeout(pfTeachPoll, 500);
}
async function pfTeachPoll() { try { PF.st = await (await fetch('teach_status', { cache: 'no-store' })).json(); } catch (e) { } pfTeachRender(); }
async function pfTeach(action) {
  const body = { action };
  if (action === 'start') { body.name = $('pfname').value.trim(); if (!body.name) { $('pfname').focus(); return; } body.ids = [...$('pfdevs').querySelectorAll('input:checked')].map(c => c.dataset.id); PF.skip = new Set(); }
  if (action === 'finish') body.skip = [...PF.skip];
  try {
    const r = await (await fetch('teach', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })).json();
    if (action === 'stop') PF.st = r;
    else if (action === 'start' && !r.ok) { alert(t(r.error === 'busy' ? 'pf_busy' : 'saveerr')); }
    else if (action === 'finish' || action === 'cancel') { PF.st = { state: 'idle' }; if (r.profiles) PF.list = r.profiles; if (action === 'finish') $('pfstate').hidden = false;
      if (action === 'finish' && r.ok) { pfRender(); pfTeachRender(); const b = $('pfres'); b.innerHTML = `<div class="calst">✓ ${esc(t('pf_saved', { n: r.n }))}</div>`; return; } }
  } catch (e) { alert(t('saveerr')); }
  if (action === 'start') await pfTeachPoll(); else { pfRender(); pfTeachRender(); }
}
function scanRender() {
  const sc = PF.scan || { state: 'idle' }, st = $('scanst');
  $('scango').disabled = sc.state === 'running'; $('scanstop').hidden = sc.state !== 'running';
  st.className = 'calst' + (sc.state === 'running' ? ' run' : '');
  st.textContent = sc.state === 'running' ? t('scan_run', { p: sc.total ? Math.round(100 * sc.done / sc.total) : 0, e: sc.events || 0, a: sc.areas || 0 })
    : sc.state === 'done' ? (sc.msg === 'no_profiles' ? t('scan_noprof') : /^error/.test(sc.msg || '') ? t('saveerr') + ' ' + sc.msg : '✓ ' + t('scan_done', { e: sc.events || 0, a: sc.areas || 0 })) : '';
  clearTimeout(PF.stimer);
  if (sc.state === 'running') PF.stimer = setTimeout(async () => { try { PF.scan = await (await fetch('scan_status', { cache: 'no-store' })).json(); } catch (e) { } scanRender();
    if (PF.scan && PF.scan.state === 'done') { EVSIG = ''; if (NV.open) { loadEvents(); dtLoad(DT, true); } } }, 800);
}
async function scanGo() {
  const [a, b] = pfScanRange();
  try { const r = await (await fetch('scan', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ from: a, to: b, name: $('scanname').value, events: $('scanev').checked, areas: $('scanar').checked }) })).json();
    if (!r.ok) { alert(t(r.error === 'busy' ? 'pf_busy' : 'saveerr')); return; } PF.scan = { state: 'running', done: 0, total: 1 }; scanRender(); } catch (e) { alert(t('saveerr')); }
}
function initProf() {
  if (!$('profdlg')) return;
  $('pfx').onclick = () => $('profdlg').close();
  $('pfopen').onclick = () => pfOpen('teach');
  if ($('scanopen')) $('scanopen').onclick = () => pfOpen('scan');
  $('pfgo').onclick = () => pfTeach('start');
  $('pfname').onkeydown = e => { if (e.key === 'Enter') { e.preventDefault(); pfTeach('start'); } };
  $('pfstop').onclick = () => pfTeach('stop');
  $('pfok').onclick = () => pfTeach('finish');
  $('pfdrop').onclick = () => { if (confirm(t('pf_drop_q'))) pfTeach('cancel'); };
  $('scango').onclick = scanGo;
  $('scanstop').onclick = async () => { try { await fetch('scan', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{"action":"cancel"}' }); } catch (e) { } };
}
function initEvView() {
  const box = $('evview'); if (!box) return;
  const sync = () => box.querySelectorAll('button').forEach(b => b.classList.toggle('on', b.dataset.v === EVVIEW));
  box.querySelectorAll('button').forEach(b => b.onclick = () => { EVVIEW = b.dataset.v; try { localStorage.setItem('laerm_evview', EVVIEW); } catch (e) { } sync(); EVSIG = ''; renderEvents(); });
  sync();
}
function initFn() {
  initFnp(); initEvView(); initProf();
  $('fnx').onclick = $('fncancel').onclick = () => $('fndlg').close();
  $('fnsave').onclick = () => fnSave(false); $('fndel').onclick = () => fnSave(true);
  $('fnfnow').onclick = () => { $('fnfrom').value = dtl(new Date(nowServer())); };
  $('fntnow').onclick = () => { $('fnto').value = dtl(new Date(nowServer())); };
  $('fntclr').onclick = () => { $('fnto').value = ''; };
  fnRefresh(); setInterval(() => { if (!document.hidden && !NV.open) fnRefresh(); }, 15000);
}
init();
})();
