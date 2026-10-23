/* Lärmprotokoll – Verlauf drucken („Notenblatt“): Zeile für Zeile (z. B. 10 min) Pegelspur, Spektrogramm, Störungen und Notizen,
   für den gewählten Zeitraum und die gewählten Geräte. Die Seite lädt die Daten selbst und wird dann über den Browser gedruckt. */
(function () {
'use strict';
const $ = id => document.getElementById(id);
const pad = n => String(n).padStart(2, '0');
const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const Q = new URLSearchParams(location.search);
const lang = Q.get('lang') === 'en' ? 'en' : 'de';
function t(k, v) { let s = (I18N[lang] || I18N.de)[k]; if (s === undefined) s = I18N.de[k]; if (s === undefined) return k; if (v) for (const x in v) s = s.split('{' + x + '}').join(v[x]); return s; }
const num = v => v == null || v === '' || !isFinite(+v) ? null : +v;
const f1 = v => num(v) == null ? '–' : (lang === 'de' ? (+v).toFixed(1).replace('.', ',') : (+v).toFixed(1));
const hm = ms => { const d = new Date(ms); return pad(d.getHours()) + ':' + pad(d.getMinutes()); };
const hms = ms => { const d = new Date(ms); return hm(ms) + ':' + pad(d.getSeconds()); };
const day = ms => new Date(ms).toLocaleDateString(lang === 'en' ? 'en-GB' : 'de-DE', { weekday: 'short', day: '2-digit', month: '2-digit', year: 'numeric' });
const isoDay = ms => { const d = new Date(ms); return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()); };
const ART_ICON = { knock: '🔨', door: '🚪', steps: '👣', voice: '🗣', tv: '📺', scrape: '🔩', signal: '🔔', animal: '🐾', noise: '〰', other: '❓' };

/* ---------- Einstellungen aus dem Aufruf ---------- */
const FROM = +Q.get('from'), TO = +Q.get('to'), LINE = Math.max(1, +Q.get('line') || 10) * 60000;
let SRCS = []; try { SRCS = JSON.parse(Q.get('srcs') || '[]'); } catch (e) { }
const SHOW = { lvl: Q.get('lvl') !== '0', spec: Q.get('spec') === '1', info: Q.get('info') !== '0', ev: Q.get('ev') !== '0' };
const MFO = Q.get('mfo') === '1';                     // nach Muster ausgefilterte weglassen (mit Vermerk oben)
let EVD = null;                                       // Belegdaten: Zusammenfassung, Zeitachse, Prüfsummen, Musterfilter
const SAME = Q.get('scale') !== 'line', PORT = Q.get('o') === 'p';
const SKIP = Q.get('skip') !== '0';                    // Zeilen ohne Aufzeichnung zu einer Zeile zusammenfassen
const PTV = Q.get('pt') !== null && Q.get('pt') !== '' && isFinite(+Q.get('pt')) ? +Q.get('pt') : null;   // Prüf-Schwelle (nur Anzeige)
const W = PORT ? 900 : 1200;                          // Datenpunkte je Zeile (feiner als die Druckauflösung nötig)
const L = 34, H = 84, AX = 12;                         // linker Rand (dB), Höhe der Pegelspur, Zeitachse

document.body.className = PORT ? 'port' : 'land';
$('pgsize').textContent = '@page{size:A4 ' + (PORT ? 'portrait' : 'landscape') + ';margin:9mm 9mm 11mm;@bottom-right{content:counter(page) " / " counter(pages);font:9px system-ui;color:#6b7280}}';
document.title = t('pr_title'); $('ttl').textContent = t('pr_title');
$('bprint').textContent = '🖨 ' + t('pr_print'); $('bclose').textContent = t('pr_close');
$('bprint').onclick = () => window.print(); $('bclose').onclick = () => window.close();

/* ---------- Farben Spektrogramm (wie in der App) ---------- */
const STOPS = [[0, 0, 4], [31, 12, 72], [85, 15, 109], [136, 34, 106], [186, 54, 85], [227, 89, 51], [249, 140, 10], [249, 201, 50], [252, 255, 164]];
function cmap(x) { const p = Math.max(0, Math.min(1, x)) * (STOPS.length - 1), i = Math.floor(p), f = p - i, a = STOPS[i], b = STOPS[Math.min(i + 1, STOPS.length - 1)]; return [a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, a[2] + (b[2] - a[2]) * f]; }

/* ---------- Zeilen ---------- */
const NL = Math.max(1, Math.ceil((TO - FROM) / LINE));
const lines = Array.from({ length: NL }, (_, i) => ({ a: FROM + i * LINE, b: Math.min(TO, FROM + (i + 1) * LINE), dev: {}, notes: [] }));
const lineOf = ts => Math.floor((ts - FROM) / LINE);

function prog(a, b) { $('prog').innerHTML = esc(t('pr_load', { a, b })) + '<i><i style="width:' + Math.round(100 * a / Math.max(1, b)) + '%"></i></i>'; }

async function getJSON(u) { for (let k = 0; k < 3; k++) { try { const r = await fetch(u, { cache: 'no-store' }); if (r.ok) return await r.json(); } catch (e) { } await new Promise(r => setTimeout(r, 500 * (k + 1))); } return null; }

async function load() {
  if (!SRCS.length || !(TO > FROM)) { $('paper').innerHTML = '<p>' + esc(t('pr_none')) + '</p>'; return; }
  const k = Math.max(1, Math.min(Math.floor(16000 / W), Math.floor(12 * 3600000 / LINE)));   // mehrere Zeilen je Abfrage
  const jobs = [];
  for (const [sid] of SRCS) for (let i = 0; i < NL; i += k) jobs.push({ sid, i0: i, i1: Math.min(NL, i + k) });
  let done = 0; const total = jobs.length + (SHOW.info ? 1 : 0); prog(0, total);
  if (SHOW.info) {                                      // Notizen (an Störungen und freie) im Zeitraum
    const j = await getJSON('notes?from=' + isoDay(FROM) + '&to=' + isoDay(TO - 1) + '&src=all');
    for (const n of (j && j.notes) || []) { const ts = num(n.t); if (ts == null || ts < FROM || ts >= TO) continue; const li = lines[lineOf(ts)]; if (li) li.notes.push(n); }
    prog(++done, total);
  }
  const run = async job => {
    const a = FROM + job.i0 * LINE, b = FROM + job.i1 * LINE, n = (job.i1 - job.i0) * W;
    const r = await getJSON('daytrack?src=' + encodeURIComponent(job.sid) + '&date=' + isoDay(a) + '&free=1&from=' + a + '&to=' + b + '&n=' + n + (SHOW.spec ? '' : '&nospec=1'));
    for (let i = job.i0; i < job.i1; i++) lines[i].dev[job.sid] = { pts: [], spec: [], ev: [], has: !!(r && r.has) };
    if (r && r.has) {
      for (const p of r.pts || []) { const li = lines[lineOf(p[0])]; if (li && li.dev[job.sid]) li.dev[job.sid].pts.push(p); }
      for (const s of (r.spec && r.spec.b) || []) { const li = lines[lineOf(s[0])]; if (li && li.dev[job.sid]) li.dev[job.sid].spec.push(s); }
      for (const e of r.ev || []) { for (let i = Math.max(job.i0, lineOf(e[0])); i <= Math.min(job.i1 - 1, lineOf(e[0] + Math.max(0, e[1]))); i++) lines[i].dev[job.sid].ev.push(e); }
      if (r.spec && r.spec.bands) NB = r.spec.bands.length;
    }
    prog(++done, total);
  };
  try { const rt = await getJSON('runtime?from=' + FROM + '&to=' + TO); DOWN = ((rt && rt.events) || []).filter(e => e.kind === 'down').map(e => [new Date(e.from).getTime(), new Date(e.to).getTime(), e.note || '', e.cause]); } catch (e) { }
  const evP = (SHOW.ev || MFO) ? getJSON('beleg?from=' + FROM + '&to=' + TO + '&srcs=' + encodeURIComponent(SRCS.map(s => s[0]).join(',')) + (MFO ? '&mfo=1' : '')) : Promise.resolve(null);
  let q = 0; const workers = Array.from({ length: 3 }, async () => { while (q < jobs.length) await run(jobs[q++]); });
  await Promise.all(workers);
  EVD = await evP; if (EVD && !EVD.ok) EVD = null;
  mfMark();
  render();
  if (SHOW.ev && EVD) evidTop();
  if (SHOW.info) await methodBlock();
  if (SHOW.ev && EVD) evidBottom();
}
/* Musterfilter: Störungen kennzeichnen („nach Muster … ausgefiltert“) bzw. mit „weglassen“ entfernen */
function mfMark() {
  if (!EVD || !(EVD.mf_ev || []).length) return;
  const hit = (sid, t0) => EVD.mf_ev.find(x => x[1] === sid && Math.abs(x[0] - t0) < 1500);
  for (const li of lines) for (const sid in li.dev) {
    const d = li.dev[sid];
    d.ev = d.ev.filter(e => { const m = hit(sid, e[0]); if (!m) return true; if (MFO) return false; if (e[3] && typeof e[3] === 'object') e[3].mf = m[2]; else e[3] = { mf: m[2] }; return true; });
  }
}
const fd1 = v => lang === 'de' ? String(v).replace('.', ',') : String(v);
function durTxt(s) { s = +s || 0; if (s < 60) return fd1(Math.round(s * 10) / 10) + ' s'; if (s < 3600) return Math.floor(s / 60) + ' min ' + pad(Math.round(s % 60)) + ' s'; return Math.floor(s / 3600) + ' h ' + pad(Math.floor(s % 3600 / 60)) + ' min'; }
/* Oben: Vermerk Musterfilter und Zusammenfassung nach Zeitpunkt, Art, Intensität, Dauer, Häufigkeit */
function evidTop() {
  const s = EVD.summary, mf = EVD.muster, wdn = lang === 'en' ? ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'] : ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'];
  const d = document.createElement('div'); d.className = 'evid';
  const row = (k, v) => `<tr><th>${esc(k)}</th><td>${v}</td></tr>`;
  let h = '';
  if (mf && mf.used && mf.used.length) h += `<p class="evmf">${esc(t(mf.omit ? 'ev_mf_omit' : 'ev_mf_in', { l: mf.used.map(([a, c]) => '„' + a + '“ ' + c + '×').join('; ') }))}</p>`;
  h += `<h3>${esc(t('ev_sum'))}</h3><table class="evt">`;
  h += row(t('ev_n'), esc(String(s.n)) + (s.bg_n ? ' · ' + esc(t('ev_bg', { n: s.bg_n })) : ''));
  h += row(t('ev_time'), esc(t('ev_night', { n: s.night_n, r: s.rz_n })) + (s.top_hours.length ? ' · ' + esc(t('ev_top_h')) + ': ' + s.top_hours.map(([hh, c]) => pad(hh) + '–' + pad((hh + 1) % 24) + ' (' + c + '×)').join(', ') : '') + '<br>' + s.wd.map((c, i) => esc(wdn[i]) + ' ' + c).join(' · '));
  if (s.arts.length) h += row(t('ev_kind'), esc(s.arts.map(([a, c]) => a + ' ' + c + '×').join(', ')));
  if (s.peak) h += row(t('ev_int'), esc(t('ev_pk_t', { a: f1(s.peak.min), b: f1(s.peak.med), c: f1(s.peak.max) })) + '<br>' + esc(s.over.map(([a, c]) => a + ': ' + c).join(' · ')));
  if (s.dur) h += row(t('ev_dur'), esc(t('ev_dur_t', { a: durTxt(s.dur.sum), b: durTxt(s.dur.med), c: durTxt(s.dur.max) })) + '<br>' + esc(s.dur_b.map(([a, c]) => a + ': ' + c).join(' · '))
    + (s.impulses ? '<br>' + esc(t('ev_imp_t', { n: s.impulses.sum, e: s.impulses.events })) : ''));
  h += row(t('ev_freq'), esc(t('ev_freq_t', { d: s.days_with, t: s.days, a: fd1(s.per_day_avg), m: s.per_day_max })) + '<br>' + esc(t('ev_rec_t', { r: s.days_rec, q: s.days_quiet_rec })));
  h += '</table>';
  d.innerHTML = h;
  const paper = $('paper'), after = paper.querySelector('.leg') || paper.firstChild; if (after && after.nextSibling) paper.insertBefore(d, after.nextSibling); else paper.appendChild(d);
}
/* Unten: lückenlose Zeitachse, Prüfsummen mit Erklärung, Rohdaten, was die Aufzeichnung belegt */
function evidBottom() {
  const d = document.createElement('div'); d.className = 'evid';
  const mx = Math.max(1, ...EVD.timeline.map(x => x.n));
  let h = `<h3>${esc(t('ev_tl'))}</h3><div class="evtl">` + EVD.timeline.map(x => `<div class="evd${x.rec.length ? '' : ' norec'}"><span>${esc(day(new Date(x.day + 'T12:00:00').getTime()))}</span><b>${x.n ? x.n : esc(t('ev_none_day'))}</b>`
    + `<i style="width:${x.n ? Math.max(3, Math.round(60 * x.n / mx)) : 0}px"></i><small>${esc(t(x.rec.length ? 'ev_rec' : 'ev_norec'))}</small></div>`).join('') + '</div>';
  if (EVD.chains.length) h += `<h3>${esc(t('ev_chain'))}</h3><p class="evs">${esc(EVD.howto)}</p><table class="evt"><tr><th>${esc(t('ev_c_day'))}</th><th>${esc(t('ev_c_dev'))}</th><th>${esc(t('ev_c_res'))}</th><th>${esc(t('ev_c_head'))}</th></tr>`
    + EVD.chains.map(c => `<tr><td>${esc(day(new Date(c.day + 'T12:00:00').getTime()))}</td><td>${esc(c.name)}</td><td>${esc(c.res)}</td><td class="mono">${esc(c.head || '–')}</td></tr>`).join('') + '</table>';
  const p = new URLSearchParams({ from: isoDay(FROM), to: isoDay(TO - 1) }); if (SRCS.length === 1) p.set('src', SRCS[0][0]); if (MFO) p.set('mfo', '1');
  h += `<h3>${esc(t('ev_raw'))}</h3><p class="evs">${esc(t('ev_raw_t'))} <a href="ereignisse.csv?${p}">ereignisse.csv?${esc(p.toString())}</a></p>`;
  h += `<h3>${esc(t('ev_limits'))}</h3><p class="evs">${esc(EVD.limits)}</p>`;
  d.innerHTML = h; $('paper').appendChild(d);
}
/* Messmethode unter dem Ausdruck: Programm, Geräte, Messort, Fenster, Kalibrierung, Ton (zum Nachvollziehen für Dritte) */
async function methodBlock() {
  const j = EVD ? { ok: true, info: EVD.method } : await getJSON('methode'); if (!j || !j.ok) return;
  const m = j.info, d = document.createElement('div'); d.className = 'meth';
  d.innerHTML = `<h3>${esc(t('pr_meth'))}</h3><p>GLighter ${esc(m.version)}</p><ul>${m.devices.filter(x => SRCS.some(([sid]) => sid === x.id)).map(x => `<li><b>${esc(x.name)}</b> · ${esc(x.type)}${x.mic ? ' · ' + esc(x.mic) : ''} · ${esc(t('meas_place'))}: ${esc(x.place || t('meas_win_na'))} · ${esc(t('meas_win'))}: ${esc(x.window || t('meas_win_na'))}</li>`).join('')}</ul>
    <p>${esc(m.calib)}</p><p>${esc(m.audio_txt)}</p><p>${esc(m.art_txt)}</p>`;
  $('paper').appendChild(d);
}
let NB = 23, DOWN = [];             // Unterbrechungen des Add-ons (mit eigenem Kommentar)

/* ---------- Skala ---------- */
function range(pts) {
  let lo = 1e9, hi = -1e9;
  for (const p of pts) for (const v of [p[1], p[3]]) if (v != null && v > -125) { if (v < lo) lo = v; if (v > hi) hi = v; }
  return lo > hi ? null : [lo, hi];
}
function nice(r) {                                      // unten bündig am tiefsten Wert, oben etwas Luft
  if (!r) return [-90, -30];
  let [lo, hi] = r; const padv = Math.max(0.5, (hi - lo) * 0.04); lo = Math.floor(lo - padv); hi = Math.ceil(hi + padv); if (hi - lo < 6) hi = lo + 6; return [lo, hi];
}

/* ---------- Zeichnen ---------- */
function tickStep(ms) { const c = [10e3, 30e3, 60e3, 120e3, 300e3, 600e3, 900e3, 1800e3, 3600e3]; return c.find(s => ms / s <= 12) || 3600e3; }
function svgLine(li, d, sc) {
  const VW = L + W, pts = d.pts, span = li.b - li.a || LINE, X = ts => L + W * (ts - li.a) / LINE;
  const [lo, hi] = sc, Y = v => 2 + (H - 6) * (1 - Math.max(0, Math.min(1, (v - lo) / (hi - lo))));
  const o = [];
  o.push(`<rect x="${L}" y="0" width="${W * span / LINE}" height="${H}" fill="#fafbfc"/>`);
  const ys = [1, 2, 5, 10, 20].find(q => (hi - lo) / q <= 4) || 20;
  for (let v = Math.ceil(lo / ys) * ys; v <= hi; v += ys) { const y = Y(v).toFixed(1); o.push(`<line x1="${L}" x2="${VW}" y1="${y}" y2="${y}" stroke="#eceff2" stroke-width=".8"/><text x="${L - 3}" y="${(+y + 3).toFixed(1)}" font-size="8.5" text-anchor="end" fill="#6b7280">${v}</text>`); }
  const ts = tickStep(LINE);
  for (let x = Math.ceil(li.a / ts) * ts; x <= li.a + LINE; x += ts) { const xx = X(x).toFixed(1); o.push(`<line x1="${xx}" x2="${xx}" y1="0" y2="${H}" stroke="#eceff2" stroke-width=".8"/><line x1="${xx}" x2="${xx}" y1="${H}" y2="${H + 3}" stroke="#9aa1a9" stroke-width=".8"/><text x="${xx}" y="${H + AX - 1}" font-size="8.5" text-anchor="middle" fill="#6b7280">${ts < 60000 ? hms(x) : hm(x)}</text>`); }
  // Störungen (Zustand je Abschnitt) unten rot
  const bin = LINE / W; let act = '';
  for (const p of pts) if (p[5]) act += `M${X(p[0]).toFixed(1)} ${H - 2}h${Math.max(1, W * bin / LINE).toFixed(1)}`;
  if (act) o.push(`<path d="${act}" stroke="#e03131" stroke-width="3"/>`);
  // Spitze als Fläche, Hintergrund, Schwelle (Lücken bleiben leer)
  const segs = []; let cur = [];
  for (let i = 0; i < pts.length; i++) { const p = pts[i]; if (p[1] == null || (cur.length && p[0] - cur[cur.length - 1][0] > bin * 3)) { if (cur.length) segs.push(cur); cur = []; } if (p[1] != null) cur.push(p); }
  if (cur.length) segs.push(cur);
  for (const s of segs) {
    const top = s.map(p => `${X(p[0]).toFixed(1)} ${Y(p[1]).toFixed(1)}`).join('L');
    o.push(`<path d="M${X(s[0][0]).toFixed(1)} ${H}L${top}L${X(s[s.length - 1][0] + bin).toFixed(1)} ${Y(s[s.length - 1][1]).toFixed(1)}L${X(s[s.length - 1][0] + bin).toFixed(1)} ${H}Z" fill="#cfe3f7" stroke="#2f7fd1" stroke-width=".7" stroke-linejoin="round"/>`);
    const bgp = s.filter(p => p[3] != null).map(p => `${X(p[0]).toFixed(1)} ${Y(p[3]).toFixed(1)}`).join('L'); if (bgp) o.push(`<path d="M${bgp}" fill="none" stroke="#868e96" stroke-width="1"/>`);
    const thp = s.filter(p => p[4] != null && p[4] >= lo && p[4] <= hi).map(p => `${X(p[0]).toFixed(1)} ${Y(p[4]).toFixed(1)}`).join('L'); if (thp) o.push(`<path d="M${thp}" fill="none" stroke="#e8590c" stroke-width="1" stroke-dasharray="4 3"/>`);
  }
  if (!segs.length) o.push(`<text x="${L + 6}" y="${H / 2 + 3}" font-size="9" fill="#9aa1a9">${esc(t('pr_nodata'))}</text>`);
  if (PTV != null) {                                  // Prüf-Schwelle: Linie, Teil der Spitzen darüber hervorgehoben
    const yP = PTV > hi ? 1 : PTV < lo ? H - 1 : Y(PTV); let hl = '';
    for (const p of pts) if (p[1] != null && p[1] > PTV) { const y = Y(p[1]); if (yP - y > 0.3) hl += `M${X(p[0]).toFixed(1)} ${y.toFixed(1)}h${Math.max(0.8, W * bin / LINE).toFixed(1)}V${yP.toFixed(1)}h-${Math.max(0.8, W * bin / LINE).toFixed(1)}Z`; }
    if (hl) o.push(`<path d="${hl}" fill="#be4bdb" fill-opacity=".6"/>`);
    o.push(`<line x1="${L}" x2="${L + W}" y1="${yP.toFixed(1)}" y2="${yP.toFixed(1)}" stroke="#be4bdb" stroke-width="1.2"${PTV > hi || PTV < lo ? ' stroke-dasharray="4 3"' : ''}/>`);
  }
  // Nummern der Störungen (oben), Notizen (Dreieck)
  let lastX = -99;
  d.ev.forEach((e, k) => { const x = Math.max(L, X(e[0])); o.push(`<rect x="${x.toFixed(1)}" y="${H - 5}" width="${Math.max(1.5, W * e[1] / LINE).toFixed(1)}" height="5" fill="#e03131"/>`);
    if (x - lastX > 11) { o.push(`<text x="${x.toFixed(1)}" y="9" font-size="8.5" font-weight="700" fill="#e03131">${k + 1}</text>`); lastX = x; } });
  for (const [k, n] of d.notes || []) { const x = X(n.t); o.push(`<path d="M${(x - 3.5).toFixed(1)} 0h7l-3.5 6z" fill="#7048e8"/><text x="${(x + 4).toFixed(1)}" y="8" font-size="8" fill="#7048e8">${'N' + (k + 1)}</text>`); }
  o.push(`<rect x="${L}" y="0" width="${W}" height="${H}" fill="none" stroke="#d0d5db" stroke-width=".8"/>`);
  return `<svg viewBox="0 0 ${VW} ${H + AX}" preserveAspectRatio="none" style="aspect-ratio:${VW}/${H + AX}">${o.join('')}</svg>`;
}
function specCanvas(li, d) {
  const cv = document.createElement('canvas'); cv.width = W; cv.height = NB;
  const c = cv.getContext('2d'), img = c.createImageData(W, NB), px = img.data, lo = 2 * (-110 + 130), hi = 2 * (-30 + 130);
  for (let i = 0; i < px.length; i += 4) { px[i] = 245; px[i + 1] = 246; px[i + 2] = 248; px[i + 3] = 255; }
  const bin = LINE / W;
  for (const [ts, b64] of d.spec) {
    const x = Math.floor((ts - li.a) / bin); if (x < 0 || x >= W) continue; const sb = atob(b64);
    for (let k = 0; k < NB; k++) { const cc = cmap(((sb.charCodeAt(k) || 0) - lo) / (hi - lo)), o = 4 * ((NB - 1 - k) * W + x); px[o] = cc[0]; px[o + 1] = cc[1]; px[o + 2] = cc[2]; }
  }
  c.putImageData(img, 0, 0); return cv;
}
function ptCount(pts) {                              // Spitzen über der Prüf-Schwelle in einer Zeile (aus den Druck-Abschnitten)
  const bin = LINE / W; let n = 0, ms = 0, last = -1e15;
  for (const p of pts) if (p[1] != null && p[1] > PTV) { if (p[0] - last > Math.max(500, bin * 1.5)) n++; last = p[0]; ms += bin; }
  return { n, ms };
}
function evText(e, k) {
  const o = e[3] && typeof e[3] === 'object' ? e[3] : {}, dur = Math.max(0, e[1]) / 1000;
  const parts = [`<b>${k + 1}</b> ${hms(e[0])}`, (lang === 'de' ? (dur < 10 ? dur.toFixed(1) : Math.round(dur) + '').replace('.', ',') : (dur < 10 ? dur.toFixed(1) : Math.round(dur))) + ' s', f1(e[2]) + ' dBFS' + (num(o.th) != null && num(e[2]) != null ? ' (+' + f1(e[2] - o.th) + ')' : '')];
  if (o.a) parts.push((ART_ICON[o.a] || '') + ' ' + esc(t('art_' + o.a)) + (o.am ? ' (' + esc(t('ev_conf')) + ')' : ' – ' + esc(o.ac != null ? t('art_sugg', { c: o.ac }) : t('art_sugg0'))));
  if (o.p) parts.push('🧩 ' + esc(o.p) + (o.pc != null ? ' ' + o.pc + ' %' : ''));
  if (o.imp) parts.push(esc(t('ev_imp', { n: o.imp })));
  if (o.mf) parts.push('⊘ ' + esc(t('ev_mf_row', { l: o.mf.join(', ') })));
  if (o.nt) parts.push('📝 ' + o.nt);
  return '<div>' + parts.join(' · ') + '</div>';
}
function endTxt(ms) { return hm(ms) === '00:00' ? day(ms - 1) + ' 24:00' : day(ms) + ' ' + hm(ms); }   // Ende um Mitternacht: „24:00“ des Vortags
function emptyLine(li) { return !li.notes.length && SRCS.every(([sid]) => { const d = li.dev[sid]; return !d || (!d.ev.length && !d.pts.some(p => p[1] != null)); }); }
function render() {
  const paper = $('paper'), names = Object.fromEntries(SRCS);
  const scales = {};
  if (SAME) for (const [sid] of SRCS) { let lo = 1e9, hi = -1e9; for (const li of lines) { const r = li.dev[sid] && range(li.dev[sid].pts); if (r) { lo = Math.min(lo, r[0]); hi = Math.max(hi, r[1]); } } scales[sid] = nice(lo > hi ? null : [lo, hi]); }
  const made = new Date().toLocaleString(lang === 'en' ? 'en-GB' : 'de-DE');
  const h = [`<div class="hd"><div><h1>${esc(t('pr_head'))}: ${esc(day(FROM))} ${hm(FROM)} – ${esc(endTxt(TO))}</h1><div class="meta" style="text-align:left">${esc(SRCS.map(s => s[1]).join(', '))} · ${esc(t('pr_line'))}: ${LINE / 60000} min · ${esc(SAME ? t('pr_scale_same') : t('pr_scale_line'))}</div></div><div class="meta">${esc(t('title'))} v${esc(Q.get('ver') || '')}<br>${esc(t('pr_made', { t: made }))}</div></div>`,
    `<div class="leg"><span><i style="background:#cfe3f7;border:1px solid #2f7fd1"></i>${esc(t('peak'))} (dBFS)</span><span><i style="background:#868e96;height:2px"></i>${esc(t('background'))}</span><span><i style="border-top:2px dashed #e8590c;height:0"></i>${esc(t('threshold'))}</span><span><i style="background:#e03131"></i>${esc(t('pr_ev'))}</span><span><i style="background:#7048e8;width:8px"></i>${esc(t('pr_note'))}</span>${PTV != null ? `<span><i style="background:#be4bdb;height:3px"></i>${esc(t('pt_line', { v: f1(PTV) }))}</span>` : ''}</div>`];
  paper.innerHTML = h.join('');
  const frag = document.createDocumentFragment();
  let prevDay = '', gap = null, shown = 0;
  const flushGap = () => { if (!gap) return; const g = document.createElement('div'); g.className = 'blk gap';
    g.innerHTML = `<div class="bt"><span>${esc(day(gap.a))} ${hm(gap.a)} – ${esc(hm(gap.b) === '00:00' ? '24:00' : hm(gap.b))}</span><small>${esc(t('pr_gap', { n: gap.n }))}</small></div>`;
    const dn = DOWN.filter(x => x[0] < gap.b && x[1] > gap.a);
    if (dn.length) g.insertAdjacentHTML('beforeend', '<div class="inf">' + dn.map(x => `<div>${esc(t('dt_norec'))} ${hms(x[0])} – ${hms(x[1])} (${esc(t(x[3] === 'lost' ? 'run_r_lost' : 'run_r_restart'))})${x[2] ? ' · <b style="color:#333">📝 ' + esc(x[2]) + '</b>' : ''}</div>`).join('') + '</div>');
    frag.appendChild(g); gap = null; };
  for (const li of lines) {
    if (SKIP && emptyLine(li)) {                        // ohne Aufzeichnung: eine Zeile für den ganzen Abschnitt (je Tag)
      if (gap && day(gap.a) === day(li.a)) { gap.b = li.b; gap.n++; } else { flushGap(); gap = { a: li.a, b: li.b, n: 1 }; }
      continue;
    }
    flushGap(); shown++;
    const blk = document.createElement('div'); blk.className = 'blk';
    const dd = day(li.a), showDay = dd !== prevDay; prevDay = dd;
    let html = `<div class="bt"><span>${showDay ? esc(dd) + ' · ' : ''}${hm(li.a)} – ${hm(li.b)}</span><small>${showDay ? '' : esc(dd)}</small></div>`;
    const notesHere = li.notes;
    blk.innerHTML = html;
    for (const [sid] of SRCS) {
      const d = li.dev[sid] || { pts: [], spec: [], ev: [] }; d.notes = notesHere.map((n, k) => [k, n]).filter(([, n]) => !n.quelle_id || n.quelle_id === 'all' || n.quelle_id === sid);   // Nummer wie in der Liste darunter
      const dv = document.createElement('div'); dv.className = 'dv';
      if (SRCS.length > 1) dv.innerHTML = `<div class="dn">${esc(names[sid] || sid)}</div>`;
      if (SHOW.lvl) dv.insertAdjacentHTML('beforeend', svgLine(li, d, SAME ? scales[sid] : nice(range(d.pts))));
      if (SHOW.spec) dv.appendChild(specCanvas(li, d));
      if (SHOW.info && PTV != null) { const ex = ptCount(d.pts); dv.insertAdjacentHTML('beforeend', `<div class="inf pt">${esc(t('pt_line', { v: f1(PTV) }))}: ${ex.n ? esc(t('pt_sum', { d: '', n: ex.n, t: (lang === 'de' ? String(Math.round(ex.ms / 100) / 10).replace('.', ',') : Math.round(ex.ms / 100) / 10) + ' s' })).replace(/^: /, '') : '–'}</div>`); }
      if (SHOW.info && d.ev.length) dv.insertAdjacentHTML('beforeend', '<div class="inf">' + d.ev.map(evText).join('') + '</div>');
      blk.appendChild(dv);
    }
    if (SHOW.info && notesHere.length) blk.insertAdjacentHTML('beforeend', '<div class="inf">' + notesHere.map((n, k) => `<div class="nt">N${k + 1} ${hms(n.t)}${n.quelle_id && n.quelle_id !== 'all' ? ' · ' + esc(names[n.quelle_id] || n.quelle || '') : ''} · ${esc(n.text || '')}${(n.tags || []).length ? ' (' + esc(n.tags.join(', ')) + ')' : ''}${n.witness ? ' · ' + esc(t('pr_witness')) + ': ' + esc(n.witness) : ''}</div>`).join('') + '</div>');
    frag.appendChild(blk);
  }
  flushGap();
  paper.appendChild(frag);
  $('prog').textContent = t('pr_ready', { n: shown }); $('bprint').disabled = false;
}
load();
})();
