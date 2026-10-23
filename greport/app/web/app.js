'use strict';
/* GReport – Notizen zu Störungen. Bedienung wie der Notiz-Teil von GLighter, eigenes Erscheinungsbild. */
let FNPOP = null;                                    // Fenster, in das „Notiz jetzt“ abgedockt ist
const $ = id => document.getElementById(id) || (FNPOP && !FNPOP.closed ? FNPOP.document.getElementById(id) : null);
const pad = n => String(n).padStart(2, '0');
const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const el = (tag, props) => { const e = document.createElement(tag); Object.assign(e, props || {}); return e; };
const option = (sel, v, label) => { const o = el('option', { value: String(v), textContent: label }); sel.appendChild(o); return o; };
const isoDay = d => d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate());
const dtl = d => isoDay(d) + 'T' + pad(d.getHours()) + ':' + pad(d.getMinutes()) + ':' + pad(d.getSeconds());
// Zeit fürs Speichern immer mit Offset des Browsers (z. B. +01:00), damit der Zeitpunkt eindeutig ist – auch in der doppelten Stunde
// bei der Zeitumstellung und wenn Home Assistant in einer anderen Zeitzone läuft.
const tzo = d => { const m = -d.getTimezoneOffset(), a = Math.abs(m); return (m < 0 ? '-' : '+') + pad(Math.floor(a / 60)) + ':' + pad(a % 60); };
const dto = d => dtl(d) + tzo(d);
// Eingabefeld (Ortszeit ohne Offset) -> ISO mit Offset; unverändertes Feld behält den gespeicherten Zeitpunkt (orig)
const inIso = (v, orig) => !v ? '' : orig && dtl(new Date(orig)) === v ? orig : isNaN(new Date(v).getTime()) ? v : dto(new Date(v));
const nowMs = () => Date.now();
const post = (url, body) => fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body || {}) }).then(r => r.json());
let lang = (navigator.language || 'de').toLowerCase().startsWith('de') ? 'de' : 'en';
function t(k, v) {
  let s = (I18N[lang] || I18N.de)[k];
  if (s === undefined) s = I18N.de[k];
  if (s === undefined) return k;
  if (v) for (const x in v) s = s.split('{' + x + '}').join(v[x]);
  return s;
}
function tr() {
  document.documentElement.lang = lang; document.title = t('title');
  document.querySelectorAll('[data-i]').forEach(e => { e.textContent = t(e.dataset.i); });
  document.querySelectorAll('[data-ia]').forEach(e => { e.title = t(e.dataset.ia); e.setAttribute('aria-label', t(e.dataset.ia)); });
  document.querySelectorAll('[data-iph]').forEach(e => { e.placeholder = t(e.dataset.iph); });
}
function toast(msg, ms) {
  let e = document.getElementById('toast'); if (!e) { e = el('div', { id: 'toast', className: 'toast' }); e.setAttribute('role', 'status'); document.body.appendChild(e); }
  e.textContent = msg; e.classList.add('on'); clearTimeout(e._t); e._t = setTimeout(() => e.classList.remove('on'), ms || 3500);
}
/* ---------- Datum und Uhrzeit (einstellbar) ---------- */
let PF = { date: 'dmy4', time: 'hms', rel: true, wd: false };
const MON = { de: ['Jan.', 'Feb.', 'März', 'Apr.', 'Mai', 'Juni', 'Juli', 'Aug.', 'Sep.', 'Okt.', 'Nov.', 'Dez.'], en: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'] };
const WD = { de: ['So.', 'Mo.', 'Di.', 'Mi.', 'Do.', 'Fr.', 'Sa.'], en: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'] };
function fDate(ms, p) {
  p = p || PF; const d = new Date(ms), y = d.getFullYear(), m = d.getMonth(), dd = d.getDate(), wd = WD[lang][d.getDay()];
  let s;
  if (p.date === 'dmy2') s = pad(dd) + '.' + pad(m + 1) + '.' + String(y).slice(2);
  else if (p.date === 'wdm') s = wd + ' ' + pad(dd) + '.' + pad(m + 1) + '.';
  else if (p.date === 'iso') s = y + '-' + pad(m + 1) + '-' + pad(dd);
  else if (p.date === 'long') s = lang === 'en' ? dd + ' ' + MON.en[m] + ' ' + y : dd + '. ' + MON.de[m] + ' ' + y;
  else s = pad(dd) + '.' + pad(m + 1) + '.' + y;
  return p.wd && p.date !== 'wdm' ? wd + ' ' + s : s;
}
function fTime(ms, p) {
  p = p || PF; const d = new Date(ms), h = d.getHours();
  if (p.time === 'hm') return pad(h) + ':' + pad(d.getMinutes());
  if (p.time === 'h12') return ((h % 12) || 12) + ':' + pad(d.getMinutes()) + ':' + pad(d.getSeconds()) + (h < 12 ? ' AM' : ' PM');
  return pad(h) + ':' + pad(d.getMinutes()) + ':' + pad(d.getSeconds());
}
function fDay(ms) {                                  // Überschrift in der Liste: „Heute“, „Gestern“ oder das Datum
  if (PF.rel) { const a = new Date(ms), n = new Date(); const d0 = new Date(n.getFullYear(), n.getMonth(), n.getDate()).getTime(), dd = new Date(a.getFullYear(), a.getMonth(), a.getDate()).getTime();
    if (dd === d0) return t('gr_today'); if (dd === d0 - 86400000) return t('gr_yesterday'); }
  return fDate(ms);
}
/* ---------- Design (hell/dunkel/wie Home Assistant) ---------- */
const THEME_SVG = { auto: '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="8" fill="none" stroke="currentColor" stroke-width="2"/><path d="M12 4a8 8 0 0 1 0 16z" fill="currentColor"/></svg>',
  light: '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4.5" fill="currentColor"/><g stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M12 2v2.5M12 19.5V22M2 12h2.5M19.5 12H22M4.9 4.9l1.8 1.8M17.3 17.3l1.8 1.8M4.9 19.1l1.8-1.8M17.3 6.7l1.8-1.8"/></g></svg>',
  dark: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 14.5A8.5 8.5 0 0 1 9.5 4 8.5 8.5 0 1 0 20 14.5z" fill="currentColor"/></svg>' };
let THEME = 'auto'; try { THEME = localStorage.getItem('gr_theme') || 'auto'; } catch (e) { }
function haDark() { try { const p = window.parent; if (!p || p === window) return null; const ha = p.document.querySelector('home-assistant'), d = ha && ha.hass && ha.hass.themes && ha.hass.themes.darkMode; return typeof d === 'boolean' ? d : null; } catch (e) { return null; } }
function applyTheme() {
  let res = THEME === 'light' || THEME === 'dark' ? THEME : null;
  if (!res) { const h = haDark(); if (h !== null) res = h ? 'dark' : 'light'; }
  for (const doc of [document, FNPOP && !FNPOP.closed ? FNPOP.document : null]) if (doc) { const r = doc.documentElement; if (res) r.setAttribute('data-theme', res); else r.removeAttribute('data-theme'); }
  const b = document.getElementById('themebtn'); if (b) { b.innerHTML = THEME_SVG[THEME]; b.title = t('th_' + THEME) + ' – ' + t('th_tip'); b.setAttribute('aria-label', b.title); }
}
/* ---------- Zustand (Pro, GLighter, Home Assistant) ---------- */
let ST = { pro: { ok: false }, glighter: {}, ha: {}, persons: [] };
const PRO = () => !!(ST.pro && ST.pro.ok);
async function stLoad() {
  try { ST = await (await fetch('state', { cache: 'no-store' })).json(); } catch (e) { }
  if (ST.lang === 'de' || ST.lang === 'en') lang = ST.lang;
  if (ST.prefs) PF = ST.prefs;
  widthApply(); tipModeApply();
  stShow(); witList();
}
function stShow() {
  const b = $('grstat'); if (!b) return; b.innerHTML = '';
  const dot = (txt, on, tip) => { const c = el('span', { textContent: txt, className: on ? 'on' : '' }); c.title = tip; c.setAttribute('role', 'img'); c.setAttribute('aria-label', tip); b.appendChild(c); };
  const g = ST.glighter || {};
  if (g.found && ST.prefs && ST.prefs.gl === false) dot('🔗', false, t('gr_gl_off'));
  else if (g.linked) dot('🔗', true, t('gr_gl_linked') + ' – ' + t('gr_gl_linked_tip'));
  else if (g.found) dot('🔗', false, 'GLighter ' + t('gr_gl_found') + ' – ' + t('gr_gl_found_tip'));
  if (ST.mqtt) dot('🏠', true, t('gr_ha_ok_tip'));
  else if (ST.ha && ST.ha.api) dot('🏠', false, t('gr_ha_log_tip'));
}
/* ---------- Schnellwahl: Wörter, Gruppen, Reihenfolge ---------- */
let NOTE_TAGS = { src: ['oben', 'unten', 'nebenan', 'treppenhaus', 'draussen', 'unklar'], kind: ['klopfen', 'schritte', 'musik', 'stimmen', 'tuer', 'moebel', 'bohren', 'hund'],
  lvl: ['leicht', 'deutlich', 'stark'], eff: ['aufgewacht', 'kind_geweckt', 'kein_schlaf', 'gestoert'], act: ['geklingelt', 'angesprochen', 'verwaltung', 'polizei'], misc: ['zeuge', 'serie'] };
const GROUPS = ['src', 'kind', 'lvl', 'eff', 'act', 'misc', 'own'];          // eingebaute Wort-Rubriken
const NTS = { own: {}, del: new Set(), hide: new Set(), use: {}, sug: [], max: 5, ren: {}, grp: {}, order: [], mode: 'use', gall: [], when: [] };
const WHEN = new Map();                                // Zeitpunkt-Tasten: Schlüssel -> {l, m | at, day | none, own, hide}
function ntGroup(tag) { if (WHEN.has(tag)) return 'when'; if (NTS.grp[tag]) return NTS.grp[tag]; for (const g in NOTE_TAGS) if (NOTE_TAGS[g].includes(tag)) return g; return 'own'; }
function ntLabel(tg) { const w = WHEN.get(tg); if (w && w.own) return w.l; return NTS.own[tg] != null ? NTS.own[tg] : NTS.ren[tg] || t('nt_' + tg); }
/* Rubriken: eingebaute, „Zeitpunkt“ und eigene (g_…), in der eingestellten Reihenfolge */
const gInfo = g => (NTS.gall || []).find(x => x.g === g);
const gIds = () => NTS.gall && NTS.gall.length ? NTS.gall.map(x => x.g) : GROUPS.slice(0, -1).concat('when', 'own');
const wordGroups = () => gIds().filter(g => g !== 'when');
const gCustom = g => /^g_/.test(g);
function gLabel(g) { const i = gInfo(g); return i && (i.custom || i.renamed) ? i.l : t('gr_g_' + g); }
const G_PAL = ['#2f9e44', '#1098ad', '#7048e8', '#e8590c', '#c2255c', '#5c7cfa', '#868e96'];
function gColor(g) { const c = (NTS.gcol || {})[g]; if (c) return c; if (G_DEF[g]) return null; let h = 0; for (const ch of g) h = (h * 31 + ch.charCodeAt(0)) >>> 0; return G_PAL[h % G_PAL.length]; }
// Klasse und (bei eigenen Rubriken) Farbe für Tasten und Markierungen
function gAttr(g) { if (!gCustom(g)) return `g-${g}"`; const c = gColor(g); return `g-cu" style="--uc:${c};--udc:color-mix(in srgb, ${c} 72%, #fff)"`; }
function ntsApply(j) {
  if (!j || !j.ok) return;
  if (j.tags) NOTE_TAGS = j.tags;
  NTS.own = {}; NTS.del = new Set(); for (const o of j.own || []) { NTS.own[o.k] = o.l; if (o.del) NTS.del.add(o.k); }
  Object.assign(NTS, { hide: new Set(j.hide || []), use: j.use || {}, sug: j.suggest || [], max: j.own_max || 5, ren: j.ren || {}, grp: j.grp || {}, order: j.order || [], mode: j.mode || 'use', gcol: j.gcol || {}, req: new Set(j.req || []), limit: j.limit || 5, show: j.show || 0, proMax: j.pro_max || 200,
    gall: j.gall || [], when: j.when || [], whenMax: j.when_max || 30 });
  WHEN.clear(); for (const w of NTS.when) WHEN.set(w.k, w);
  gcolApply();
}
const G_DEF = { src: '#0c8a6a', kind: '#d6336c', lvl: '#e67700', eff: '#6741d9', act: '#1c6fd6', misc: '#5f6b78', own: '#a61e4d', when: '#0b7285' };
function gcolApply() {                                 // eigene Gruppenfarben als CSS-Variablen (auch im abgedockten Fenster)
  for (const doc of [document, FNPOP && !FNPOP.closed ? FNPOP.document : null]) {
    if (!doc) continue; const r = doc.documentElement.style;
    for (const g of GROUPS.concat('when')) { const c = (NTS.gcol || {})[g]; if (c) { r.setProperty('--u-' + g, c); r.setProperty('--ud-' + g, `color-mix(in srgb, ${c} 72%, #fff)`); } else { r.removeProperty('--u-' + g); r.removeProperty('--ud-' + g); } }
  }
}
async function ntsLoad() { try { ntsApply(await (await fetch('notetags', { cache: 'no-store' })).json()); } catch (e) { } fnpTags(); }
async function ntsPost(body) {
  const j = await post('notetags', body);
  if (!j.ok) throw new Error(j.error === 'limit_free' ? t('gr_qt_limit_free', { n: NTS.max }) : j.error === 'limit' ? t('qt_limit') : j.error === 'empty' ? t('qt_empty') : (j.error || 'error'));
  ntsApply(j); fnpTags(); listDraw(); return j;
}
function ntAll() {                                     // alle Wörter (auch ausgeblendete), Standard-Reihenfolge
  const out = []; for (const g in NOTE_TAGS) out.push(...NOTE_TAGS[g]);
  for (const k in NTS.own) if (!NTS.del.has(k)) out.push(k);
  return out;
}
function ntOrdered(list) {                             // fest angeordnet oder nach Gebrauch
  const base = new Map(ntAll().map((x, i) => [x, i]));
  if (NTS.mode === 'fixed') { const pos = new Map(NTS.order.map((x, i) => [x, i])); return list.sort((a, b) => (pos.has(a) ? pos.get(a) : 1e6 + base.get(a)) - (pos.has(b) ? pos.get(b) : 1e6 + base.get(b))); }
  return list.sort((a, b) => ((NTS.use[b] || 0) - (NTS.use[a] || 0)) || (base.get(a) - base.get(b)));
}
function ntVisible(sel) { return ntOrdered(ntAll().filter(k => !NTS.hide.has(k) || (sel && sel.has(k)))); }
const tagBtn = (tg, on) => `<button type="button" class="tag ${gAttr(ntGroup(tg)).replace('"', on ? ' on"' : '"')} data-t="${esc(tg)}" aria-pressed="${!!on}">${esc(ntLabel(tg))}</button>`;
const tagMk = tg => `<span class="mk ${gAttr(ntGroup(tg))}>${esc(ntLabel(tg))}</span>`;
/* ---------- Tipps (aus der Rechtsprechung abgeleitet, keine Rechtsberatung): einzeln wegklickbar, global abschaltbar ---------- */
let TIPX = new Set(); try { TIPX = new Set(JSON.parse(localStorage.getItem('gr_tipx') || '[]')); } catch (e) { }
const tipMode = () => PF.tipmode || (PF.tips === false ? 'off' : 'hover');
const tipsOn = () => tipMode() !== 'off';
function tipModeApply() { document.body.classList.toggle('tipshover', tipMode() === 'hover'); }
function tipsDraw(root) {
  (root || document).querySelectorAll('.tipslot').forEach(sl => {
    const want = sl.dataset.tips === 'cap' ? (FNP.edit ? ['8'] : ['1', '2', '7']) : sl.dataset.tips.split(',');
    const n = tipsOn() ? want.find(x => !TIPX.has(x)) : null;
    if (sl.dataset.cur === String(n || '') && sl.dataset.lang === lang) return;
    sl.dataset.cur = n || ''; sl.dataset.lang = lang;
    if (!n) { sl.innerHTML = ''; return; }
    sl.innerHTML = `<div class="tip" role="note"><button type="button" class="tipi" aria-expanded="false" aria-label="${esc(t('gr_tip_show'))}" title="${esc(t('gr_tip_' + n))}">💡</button><span class="tipt">${esc(t('gr_tip_' + n))}</span><details class="why"><summary>${esc(t('gr_tip_why'))}</summary><small>${esc(t('gr_tip_src', { s: t('gr_tip_' + n + '_s') }))}</small></details><button type="button" class="tipx" aria-label="${esc(t('gr_tip_x'))}" title="${esc(t('gr_tip_x'))}">✕</button></div>`;
    const tb = sl.querySelector('.tipi'); tb.onclick = () => { const o = tb.closest('.tip').classList.toggle('open'); tb.setAttribute('aria-expanded', String(o)); };
    sl.querySelector('.tipx').onclick = () => { TIPX.add(n); try { localStorage.setItem('gr_tipx', JSON.stringify([...TIPX])); } catch (e) { } tipsDraw(); };
  });
}
/* ---------- Weitere Angaben (Mehr): Häufigkeit, Polizei, Meldung, Folgen, Attest, Drohung/Gewalt; Rolle/Erreichbarkeit des Zeugen ---------- */
const ROLES = ['mitbewohner', 'nachbar', 'hausverwaltung', 'vermieter', 'polizei', 'sonstige'];
function extInit() {
  const r = $('fnpwrole'); r.innerHTML = ''; option(r, '', t('gr_w_role_none')); for (const k of ROLES) option(r, k, t('gr_role_' + k));
  const p = $('xrepto'); p.innerHTML = ''; option(p, '', t('gr_x_rep_none')); for (const k of ['hv', 'verm', 'sonst']) option(p, k, t('gr_rep_' + k));
  $('fnpwit').addEventListener('input', witX); $('fnpwit').addEventListener('change', witFill);
  $('xpolnr').addEventListener('input', () => { if ($('xpolnr').value.trim()) $('xpol').checked = true; });
  for (const id of ['xfreq', 'xpolnr', 'xhealth', 'xattest', 'fnpwcon']) $(id).addEventListener('input', () => { if ($(id).value.trim()) fnpStart(); });
}
function witX() { $('fnpwitx').hidden = !$('fnpwit').value.trim(); }
function witFill() {                                   // bekannte Person: Rolle und Erreichbarkeit aus der Personenliste vorschlagen
  const n = $('fnpwit').value.split(',')[0].trim(), i = (ST.persons_info || {})[n];
  if (i) { if (!$('fnpwrole').value && i.r) $('fnpwrole').value = i.r; if (!$('fnpwcon').value && i.c) $('fnpwcon').value = i.c; }
  witX();
}
function extRead() {
  const v = id => $(id).value.trim(), x = {};
  if (v('xfreq')) x.freq = v('xfreq');
  if ($('xpol').checked || v('xpolnr')) { x.pol = true; if (v('xpolnr')) x.pol_nr = v('xpolnr'); }
  if (v('xrepto')) x.rep_to = v('xrepto'); if (v('xrepdate')) x.rep_date = v('xrepdate');
  if (v('xhealth')) x.health = v('xhealth'); if (v('xattest')) x.attest = v('xattest');
  if ($('xthreat').checked) x.threat = true;
  if ($('fnpwit').value.trim()) { if (v('fnpwrole')) x.wrole = v('fnpwrole'); if (v('fnpwcon')) x.wcontact = v('fnpwcon'); }
  return x;
}
function extFill(x) {
  x = x || {};
  $('xfreq').value = x.freq || ''; $('xpol').checked = !!x.pol; $('xpolnr').value = x.pol_nr || ''; $('xrepto').value = x.rep_to || ''; $('xrepdate').value = x.rep_date || '';
  $('xhealth').value = x.health || ''; $('xattest').value = x.attest || ''; $('xthreat').checked = !!x.threat;
  $('fnpwrole').value = x.wrole || ''; $('fnpwcon').value = x.wcontact || '';
  $('secmore').open = ['freq', 'pol', 'rep_to', 'rep_date', 'health', 'attest', 'threat'].some(k => x[k]);
  witX();
}
function extTxt(n) {                                   // kurze Anzeige in Zeitleiste und Tabelle
  const x = n.ext || {}, p = [];
  if (x.threat) p.push('⚠ ' + t('gr_x_threat_s'));
  if (x.pol) p.push('🚓 ' + t('gr_x_pol_s') + (x.pol_nr ? ' ' + x.pol_nr : ''));
  if (x.rep_to || x.rep_date) p.push('📨 ' + (x.rep_to ? t('gr_rep_' + x.rep_to) : t('gr_x_rep_s')) + (x.rep_date ? ' ' + fDate(Date.parse(x.rep_date + 'T12:00:00')) : ''));
  if (x.freq) p.push('↻ ' + x.freq);
  if (x.health) p.push('⚕ ' + x.health);
  if (x.attest) p.push('📄 ' + t('gr_x_attest_s') + ': ' + x.attest);
  if (n.src_doc) p.push('🔎 ' + t('gr_from_doc', { n: n.src_doc.name || n.src_doc.id, p: n.src_doc.page || '–', l: n.src_doc.line || '–' }));
  return p;
}
const witTxt = n => { const x = n.ext || {}, r = x.wrole ? t('gr_role_' + x.wrole) : ''; return n.witness + (r || x.wcontact ? ' (' + [r, x.wcontact].filter(Boolean).join(', ') + ')' : ''); };
/* ---------- Notiz jetzt ---------- */
const FNP = { from: null, tags: new Set(), edit: null, fixed: false, open: new Set(), notime: false, when: null, approx: false, cap: null, manual: false, pend: null };
function fnpTags() {
  const box = $('fnptags'); if (!box) return;
  if (LAY.on) { layDraw(); return; }
  const vis = ntVisible(FNP.tags), by = {}; for (const k of vis) (by[ntGroup(k)] = by[ntGroup(k)] || []).push(k);
  let h = '';
  const w = NTS.sug[0];
  if (w) h += `<div class="sugline">💡 ${esc(t('qt_sug', { w: w.w, n: w.n }))} <button type="button" class="sugy">＋ ${esc(t('qt_create'))}</button><button type="button" class="sugn" aria-label="${esc(t('qt_sug_no'))}">✕</button></div>`;
  for (const g of gIds()) {
    const gi = gInfo(g) || {};
    if (g === 'when') {                                 // Rubrik „Zeitpunkt“: Tasten setzen die Zeit (kein Wort in der Notiz)
      const ws = whenOrdered().filter(k => !WHEN.get(k).hide || FNP.when === k);
      if (!ws.length || (gi.hide && !FNP.when)) continue;
      h += `<div class="grp" data-g="when"><span>${esc(gLabel(g))}</span><div>${ws.map(k => `<button type="button" class="tag ${gAttr('when').replace('"', FNP.when === k ? ' on"' : '"')} data-w="${esc(k)}" aria-pressed="${FNP.when === k}">${esc(ntLabel(k))}</button>`).join('')}</div></div>`;
      continue;
    }
    const ks = by[g] || []; if (!ks.length && g !== 'own') continue;
    if (gi.hide && !ks.some(k => FNP.tags.has(k))) continue;        // ausgeblendete Rubrik (gewählte Wörter bleiben sichtbar)
    const lim = NTS.show > 0 && !FNP.open.has(g) ? NTS.show : 0, shown = lim ? ks.filter((k, i) => i < lim || FNP.tags.has(k)) : ks, hid = ks.length - shown.length;   // Pro: nur die ersten N je Gruppe
    h += `<div class="grp${NTS.req && NTS.req.has(g) ? ' req' : ''}" data-g="${g}"><span>${esc(gLabel(g))}${NTS.req && NTS.req.has(g) ? '<i class="reqm" title="' + esc(t('gr_req_tip')) + '"> *</i>' : ''}</span><div>${shown.map(k => tagBtn(k, FNP.tags.has(k))).join('')}${hid > 0 ? `<button type="button" class="tag more" data-g="${g}">${esc(t('gr_more', { n: hid }))}</button>` : FNP.open.has(g) && NTS.show > 0 && ks.length > NTS.show ? `<button type="button" class="tag more less" data-g="${g}">${esc(t('gr_less'))}</button>` : ''}${g === 'own' ? `<button type="button" class="tag add">＋ ${esc(t('qt_add'))}</button>` : ''}</div></div>`;
  }
  box.innerHTML = h;
  box.querySelectorAll('.grp>div').forEach(row => {          // Handy: Hinweis rechts, solange die Zeile weitergeht
    const upd = () => row.parentNode.classList.toggle('ovf', row.scrollWidth - row.scrollLeft - row.clientWidth > 4);
    row.addEventListener('scroll', upd, { passive: true }); requestAnimationFrame(upd);
  });
  box.querySelectorAll('.tag[data-t]').forEach(b => {
    b.onclick = () => { const k = b.dataset.t; FNP.tags.has(k) ? FNP.tags.delete(k) : FNP.tags.add(k); b.classList.toggle('on', FNP.tags.has(k)); b.setAttribute('aria-pressed', FNP.tags.has(k)); fnpStart(); reqCheck(); if (SECHIDE.size) secDraw(); };
    b.oncontextmenu = e => { e.preventDefault(); qtOpen(b.dataset.t); };
    let lp = 0; b.addEventListener('touchstart', () => { lp = setTimeout(() => { lp = -1; qtOpen(b.dataset.t); }, 600); }, { passive: true });
    b.addEventListener('touchend', e => { if (lp === -1) e.preventDefault(); clearTimeout(lp); });
    b.addEventListener('touchmove', () => clearTimeout(lp), { passive: true });
  });
  box.querySelectorAll('.tag[data-w]').forEach(b => b.onclick = () => whenPick(b.dataset.w));
  const wg = box.querySelector('.grp[data-g="when"]'); if (wg) { const sl = el('div', { className: 'tipslot' }); sl.dataset.tips = '3'; wg.after(sl); tipsDraw(box); }
  box.querySelectorAll('.tag.more').forEach(b => b.onclick = () => { const g = b.dataset.g; FNP.open.has(g) ? FNP.open.delete(g) : FNP.open.add(g); fnpTags(); });
  const ad = box.querySelector('.tag.add'); if (ad) ad.onclick = () => qtOpen();
  reqCheck();
  const sy = box.querySelector('.sugy'); if (sy) sy.onclick = async () => { try { const j = await ntsPost({ action: 'add', l: w.w }); if (j.k) { FNP.tags.add(j.k); fnpTags(); } } catch (e) { alert(e.message); } };
  const sn = box.querySelector('.sugn'); if (sn) sn.onclick = () => ntsPost({ action: 'nope', w: w.k }).catch(e => alert(e.message));
}
function whenOrdered() {
  const ks = [...WHEN.keys()];
  if (NTS.mode !== 'fixed') return ks;
  const pos = new Map(NTS.order.map((x, i) => [x, i])); return ks.sort((a, b) => (pos.has(a) ? pos.get(a) : 1e6 + ks.indexOf(a)) - (pos.has(b) ? pos.get(b) : 1e6 + ks.indexOf(b)));
}
function hmAt(hm, base, back) { const [hh, mm] = hm.split(':').map(Number); return new Date(base.getFullYear(), base.getMonth(), base.getDate() - (back || 0), hh, mm, 0); }
function whenRange(w, base) {                         // wie im Server: [von, bis] in ms; bis = '' wenn ohne
  base = new Date(base);
  if (w.rng) {                                          // ungefährer Zeitraum, z. B. 22:00–06:00 (höchstens bis Erfassungsbeginn)
    const a = hmAt(w.rng[0], base, w.day); if (!w.day && a > base) a.setDate(a.getDate() - 1);
    const b = hmAt(w.rng[1], a); if (b <= a) b.setDate(b.getDate() + 1);
    const e = Math.min(b.getTime(), base.getTime()); return [a.getTime(), e > a.getTime() ? e : null];
  }
  if (w.at) { const d = hmAt(w.at, base, w.day); if (!w.day && d > base) d.setDate(d.getDate() - 1); return [d.getTime(), null]; }
  return [base.getTime() - (w.m || 0) * 60000, null];
}
function whenPick(k) {
  // Zeitpunkt-Taste: rechnet immer vom Beginn der Erfassung (erstes Tippen), nicht von der vorigen Taste und nicht vom Speichern.
  // Von Hand gesetzte Zeit hat Vorrang: erst nach Hinweis und zweitem Tippen ersetzen.
  const w = WHEN.get(k); if (!w) return;
  const msg = $('fnpmsg');
  if (FNP.when === k) { FNP.when = null; FNP.notime = false; FNP.approx = false; FNP.fixed = false; $('fnpfromi').value = ''; $('fnptoi').value = ''; }
  else {
    if (FNP.manual && FNP.pend !== k) { FNP.pend = k; msg.className = 'msg warn'; msg.textContent = t('gr_w_manual', { k: ntLabel(k) }); return; }
    FNP.pend = null; FNP.manual = false; if (msg.classList.contains('warn')) { msg.textContent = ''; msg.className = 'msg'; }
    if (FNP.cap == null) FNP.cap = FNP.edit ? (FNP.edit.cap || FNP.edit.a) : nowMs();
    FNP.when = k; FNP.approx = !!w.rng; FNP.notime = !!w.none;
    if (w.none) FNP.fixed = false;
    else { const [a, b] = whenRange(w, FNP.cap); FNP.fixed = true; FNP.from = a; $('fnpfromi').value = dtl(new Date(a)); $('fnptoi').value = b ? dtl(new Date(b)) : ''; $('fnprun').checked = false; }
  }
  if (FNP.from == null) FNP.from = nowMs();
  if (FNP.when) timeEdit(true);
  notimeShow(); fnpTags(); fnpShow();
}
function notimeShow() {                                // „ohne Zeitpunkt“: Zeitfelder sind dann aus
  const nt = !!FNP.notime; $('fnpnotime').checked = nt;
  for (const id of ['fnpfromi', 'fnptoi', 'fnpfnow', 'fnptnow', 'fnptclr', 'fnprun']) { const e = $(id); if (e) e.disabled = nt; }
}
function reqCheck() {                                 // alle Pflicht-Gruppen gewählt: gewählte Tasten und „Speichern“ leuchten pulsierend auf (gespeichert wird immer)
  const req = [...(NTS.req || [])], pn = $('fnpanel'); if (!pn) return;
  const have = new Set([...FNP.tags].map(ntGroup));
  pn.querySelectorAll('.grp.req').forEach(r => r.classList.toggle('done', have.has(r.dataset.g)));
  const all = req.length > 0 && req.every(g => have.has(g)), was = pn.classList.contains('alldone');
  pn.classList.toggle('alldone', all);
  if (all && !was) { const m = $('fnpmsg'); if (m && !m.textContent) { m.className = 'msg'; m.textContent = '✓ ' + t('gr_req_done'); setTimeout(() => { if (m.textContent === '✓ ' + t('gr_req_done')) m.textContent = ''; }, 3000); } }
}
function witList() {                                   // Pro: gespeicherte Personen zum Antippen (mehrere Zeugen)
  const box = $('fnpwitl'); if (!box) return; box.innerHTML = '';
  if (!PRO()) return;
  for (const p of ST.persons || []) {
    const b = el('button', { type: 'button', className: 'chip', textContent: p });
    b.onclick = () => { const w = $('fnpwit'), cur = w.value.split(',').map(x => x.trim()).filter(Boolean); if (!cur.includes(p)) cur.push(p); w.value = cur.join(', '); fnpStart(); };
    box.appendChild(b);
  }
}
function fnpStart() { if (FNP.from == null) FNP.from = nowMs(); if (FNP.cap == null && !FNP.edit) FNP.cap = FNP.from; fnpShow(); }
function fnpAt() { return FNP.fixed && FNP.from != null ? FNP.from : nowMs(); }
function fnpShow() {
  const at = FNP.edit && !FNP.fixed ? FNP.edit.a : fnpAt();
  $('capclock').textContent = fTime(at); $('capdate').textContent = fDate(at);
  const to = $('fnptoi').value, run = $('fnprun').checked;
  if (!LAY.on) {                                       // im Bearbeiten-Modus sind Überschrift und Hinweis editierbar – nicht überschreiben
    // eigener Hinweis ersetzt nur den Ruhezustand; Zustandsmeldungen (ändern, Zeit gesetzt, läuft) bleiben
    $('fnpfrom').textContent = FNP.edit ? t('gr_editing_s') : FNP.notime ? t('gr_notime') : FNP.fixed ? (FNP.when && FNP.cap ? t('gr_capinfo', { t: fTime(FNP.cap), k: ntLabel(FNP.when) }) : t('gr_t_fixed')) : FNP.from == null ? (PF.cap_sub || t(matchMedia('(pointer:coarse)').matches ? 'gr_wait_m' : 'gr_wait')) : t('gr_t_live');
    $('capttl').textContent = FNP.edit ? t('gr_change_ttl') : (PF.cap_title || t('fn_btn'));
  }
  $('fnptimetxt').textContent = FNP.notime ? t('gr_notime') + ' · ' + t('gr_t_change') : (FNP.approx ? '≈ ' : '') + (FNP.fixed || FNP.edit ? t('gr_t_at', { t: fTime(at) }) : t('gr_t_now')) + (to ? ' – ' + fTime(new Date(to).getTime()) : run ? ' – ' + t('gr_t_run') : '') + ' · ' + t('gr_t_change');
}
function fnpReset() {
  FNP.from = null; FNP.tags = new Set(); FNP.edit = null; FNP.fixed = false; Object.assign(FNP, { notime: false, when: null, approx: false, cap: null, manual: false, pend: null });
  $('fnptext').value = ''; $('fnpwit').value = ''; $('fnpfromi').value = ''; $('fnptoi').value = ''; $('fnprun').checked = false;
  $('fnpcancel').hidden = true; $('fnpsave').textContent = t('save'); $('fnpanel').classList.remove('editing');
  ATT.pend = []; attPendDraw();
  extFill(null); timeEdit(false); notimeShow(); fnpTags(); fnpShow(); listDraw(); reqCheck(); secDraw(); tipsDraw();
}
function timeEdit(open) {
  $('fnpext').hidden = !open; $('fnptimebtn').setAttribute('aria-expanded', String(open));
  if (open && !$('fnpfromi').value) $('fnpfromi').value = dtl(new Date(fnpAt()));
}
async function fnpSave() {
  const fixed = FNP.fixed && $('fnpfromi').value, tv = $('fnptoi').value, run = $('fnprun').checked, ed = FNP.edit;
  const body = { action: ed ? 'edit' : 'add', id: ed ? ed.id : '', from: fixed ? inIso($('fnpfromi').value, ed && ed.from) : ed ? (ed.from || dto(new Date(ed.a))) : dto(new Date(nowMs())), to: tv ? inIso(tv, ed && ed.to) : run ? dto(new Date(nowMs())) : '',
    src: ed ? (ed.src || 'all') : 'all', text: autoText($('fnptext').value, FNP.tags) || (ATT.pend.length ? t('gr_att_only', { n: ATT.pend.map(p => p.f.name).join(', ') }) : ''), typed: !!$('fnptext').value.trim(), tags: [...FNP.tags], witness: $('fnpwit').value,
    notime: !!FNP.notime, ext: extRead() };
  if (FNP.when) Object.assign(body, { wk: FNP.when, wl: ntLabel(FNP.when), approx: !!FNP.approx, cap: FNP.cap || nowMs() });   // erfasst um … (Taste: …)
  else if (ed && ed.wk && !FNP.timeTouched) Object.assign(body, { wk: ed.wk, wl: ed.wl, approx: !!ed.approx, cap: ed.cap });
  else if (ed && ed.cap) body.cap = ed.cap;                                    // Erfassungszeit bleibt beim Ändern
  else if (!ed && fixed) body.cap = FNP.cap || nowMs();                      // Zeit von Hand gesetzt: wann notiert wurde, getrennt festhalten
  const msg = $('fnpmsg'); msg.className = 'msg';
  try {
    const r = await post('note', body);
    if (!r.ok) { msg.textContent = t(r.error === 'empty' ? 'fn_empty' : r.error === 'to' ? 'fn_bad_to' : 'saveerr'); msg.classList.add('err'); return; }
    const at = r.note && r.note.a, pend = ATT.pend.slice(); fnpReset(); ntsLoad();
    if (pend.length) await attUploadAll(pend, [r.note.id], msg);            // Anlagen an die gerade gespeicherte Notiz
    msg.className = 'msg'; msg.textContent = '✓ ' + t(ed ? 'gr_changed_at' : 'gr_saved_at', { t: at ? fTime(at) : '' }); setTimeout(() => { if (msg.textContent.startsWith('✓')) msg.textContent = ''; }, 5000);
    listLoad();
  } catch (e) { msg.textContent = t('saveerr'); msg.classList.add('err'); }
}
function fnpEdit(n) {
  FNP.edit = n; FNP.tags = new Set(n.tags || []); FNP.fixed = false; FNP.from = n.a;
  Object.assign(FNP, { notime: !!n.notime, when: null, approx: !!n.approx, cap: n.cap || null, manual: false, pend: null, timeTouched: false });
  $('fnptext').value = n.text || ''; $('fnpwit').value = n.witness || '';
  $('fnpfromi').value = n.from ? dtl(new Date(n.from)) : ''; $('fnptoi').value = n.to ? dtl(new Date(n.to)) : ''; $('fnprun').checked = false;
  $('fnpcancel').hidden = false; $('fnpsave').textContent = t('gr_change'); $('fnpanel').classList.add('editing');
  extFill(n.ext); attPendDraw(); notimeShow(); fnpTags(); fnpShow(); listDraw(); tipsDraw(); $('fnpanel').scrollIntoView({ block: 'start', behavior: 'smooth' }); $('fnptext').focus({ preventScroll: true });
}
/* Aus den Markierungen einen Satz bilden (nur ohne eigenen Text), z. B. „Deutliche Schritte von oben“ */
const TS_DE = {
  kind: { klopfen: ['Klopfen', 'n'], schritte: ['Schritte', 'p'], musik: ['Musik/Bass', 'p'], stimmen: ['Stimmen', 'p'], tuer: ['Türgeräusch', 'n'], moebel: ['Möbelrücken', 'n'], bohren: ['Bohren', 'n'], hund: ['Hundegebell', 'n'] },
  lvl: { leicht: ['Leichtes', 'Leichte', 'leicht'], deutlich: ['Deutliches', 'Deutliche', 'deutlich'], stark: ['Starkes', 'Starke', 'stark'] },
  src: { oben: 'von oben', unten: 'von unten', nebenan: 'von nebenan', treppenhaus: 'im Treppenhaus', draussen: 'von draußen', unklar: 'Herkunft unklar' },
  rest: { aufgewacht: 'aufgewacht', kind_geweckt: 'Kind geweckt', kein_schlaf: 'kein Einschlafen', gestoert: 'gestört', geklingelt: 'geklingelt', angesprochen: 'Nachbarn angesprochen', verwaltung: 'Hausverwaltung informiert', polizei: 'Polizei/Ordnungsamt informiert', zeuge: 'Zeuge anwesend', serie: 'wiederholt' }, noise: 'Geräusche', and: ' und ' };
const TS_EN = {
  kind: { klopfen: ['knocking', 'n'], schritte: ['footsteps', 'p'], musik: ['music/bass', 'n'], stimmen: ['voices', 'p'], tuer: ['door noise', 'n'], moebel: ['moving furniture', 'n'], bohren: ['drilling', 'n'], hund: ['dog barking', 'n'] },
  lvl: { leicht: ['Slight', 'Slight', 'slight'], deutlich: ['Clear', 'Clear', 'clear'], stark: ['Strong', 'Strong', 'strong'] },
  src: { oben: 'from above', unten: 'from below', nebenan: 'from next door', treppenhaus: 'in the stairwell', draussen: 'from outside', unklar: 'origin unclear' },
  rest: { aufgewacht: 'woke up', kind_geweckt: 'child woken', kein_schlaf: 'could not sleep', gestoert: 'disturbed', geklingelt: 'rang the bell', angesprochen: 'talked to them', verwaltung: 'informed management', polizei: 'police/authority informed', zeuge: 'witness present', serie: 'repeated' }, noise: 'noise', and: ' and ' };
function tagSentence(tags) {
  const tg = [...(tags || [])]; if (!tg.length) return '';
  const D = lang === 'en' ? TS_EN : TS_DE, de = lang !== 'en';
  const isRen = x => NTS.ren[x];                       // umbenannte Wörter: so wie benannt verwenden
  const kinds = tg.filter(x => D.kind[x] && !isRen(x)), lvl = tg.find(x => D.lvl[x] && !isRen(x)), src = tg.find(x => D.src[x] && !isRen(x));
  const rest = tg.filter(x => D.rest[x] && !isRen(x)).map(x => D.rest[x]).concat(tg.filter(x => NTS.own[x] != null || isRen(x)).map(ntLabel));
  let main = '';
  if (kinds.length === 1) { const [nm, g] = D.kind[kinds[0]]; main = lvl ? (de ? D.lvl[lvl][g === 'n' ? 0 : 1] + ' ' + nm : D.lvl[lvl][0] + ' ' + nm) : nm; }
  else if (kinds.length > 1) main = kinds.map(x => D.kind[x][0]).join(', ').replace(/, ([^,]*)$/, D.and + '$1') + (lvl ? ' (' + D.lvl[lvl][2] + ')' : '');
  else if (lvl) main = de ? D.lvl[lvl][1] + ' ' + D.noise : D.lvl[lvl][0] + ' ' + D.noise;
  else if (src && src !== 'unklar') main = D.noise;
  if (src) main = main ? main + ' ' + D.src[src] : D.src[src];
  const out = [main, ...rest].filter(Boolean).join(', ');
  return out ? out.charAt(0).toUpperCase() + out.slice(1) : '';
}
const autoText = (text, tags) => (text || '').trim() ? text : tagSentence(tags);
function enterSave(ta, save) {                         // Enter speichert, Alt+Enter (oder Umschalt+Enter) = neue Zeile
  ta.addEventListener('keydown', e => {
    if (e.key !== 'Enter' || e.isComposing) return;
    if (e.altKey || e.shiftKey) { e.preventDefault(); const s = ta.selectionStart, en = ta.selectionEnd; ta.setRangeText('\n', s, en, 'end'); ta.dispatchEvent(new Event('input', { bubbles: true })); return; }
    e.preventDefault(); save();
  });
}
/* Abdocken: „Notiz jetzt“ als eigenes kleines Fenster über anderen Programmen */
async function fnPop() {
  if (FNPOP && !FNPOP.closed) { try { FNPOP.focus(); } catch (e) { } return; }
  const panel = document.getElementById('fnpanel'); if (!panel) return;
  let w = null;
  try { if (window.documentPictureInPicture) w = await documentPictureInPicture.requestWindow({ width: 480, height: 560 }); } catch (e) { w = null; }
  if (!w) { try { w = window.open('', 'gr_note', 'popup=yes,width=500,height=600'); } catch (e) { w = null; } }
  if (!w) { alert(t('pop_fail')); return; }
  const doc = w.document; doc.title = 'GReport – ' + t('fn_btn');
  const vp = doc.createElement('meta'); vp.name = 'viewport'; vp.content = 'width=device-width,initial-scale=1'; doc.head.appendChild(vp);
  for (const l of document.querySelectorAll('link[rel=stylesheet]')) { const n = doc.createElement('link'); n.rel = 'stylesheet'; n.href = l.href; doc.head.appendChild(n); }
  for (const at of document.documentElement.attributes) if (at.name.startsWith('data-')) doc.documentElement.setAttribute(at.name, at.value);
  doc.body.className = 'pop';
  const parent = panel.parentNode, next = panel.nextSibling;
  const ph = el('div', { className: 'popph' }); const pb = el('button', { type: 'button', className: 'btn', textContent: t('pop_back') });
  ph.append(el('span', { textContent: '📝 ' + t('pop_open'), className: 'grow' }), pb); parent.insertBefore(ph, panel);
  doc.body.appendChild(panel); FNPOP = w; gcolApply();
  const back = () => { if (FNPOP !== w) return; FNPOP = null; ph.remove(); try { parent.insertBefore(panel, next && next.parentNode === parent ? next : null); } catch (e) { parent.appendChild(panel); } };
  pb.onclick = () => { try { w.close(); } catch (e) { } back(); };
  w.addEventListener('pagehide', back);
  addEventListener('pagehide', () => { try { w.close(); } catch (e) { } });
  setTimeout(() => { const tx = doc.getElementById('fnptext'); if (tx) tx.focus(); }, 100);
}
/* Abschnitte von „Notiz jetzt“ ein- und ausblenden (auch abgedockt), gemerkt pro Browser */
const SECS = [['txt', 'fnptext', 'fnp_p_txt'], ['tags', 'fnptags', 'fnp_p_tags'], ['wit', 'secwit', 'fnp_p_wit'], ['more', 'secmore', 'gr_more_p'], ['time', 'sectime', 'gr_p_ext']];
let SECHIDE = new Set(); try { SECHIDE = new Set(JSON.parse(localStorage.getItem('gr_sechide') || '[]')); } catch (e) { }
function secDraw() {
  const bar = $('secbar'); if (!bar) return; bar.innerHTML = '';
  for (const [k, id, l] of capOrder().map(x => SECS.find(s => s[0] === x))) {
    const off = SECHIDE.has(k), e = $(id); if (e) e.hidden = off;
    const n = off && k === 'tags' && FNP.tags.size ? ' · ' + FNP.tags.size : off && k === 'wit' && $('fnpwit').value.trim() ? ' · 1' : '';
    const b = el('button', { type: 'button', className: 'secb' + (off ? '' : ' on'), textContent: t(l) + n });
    b.setAttribute('aria-pressed', String(!off)); b.title = t(off ? 'gr_sec_show' : 'gr_sec_hide', { s: t(l) });
    b.onclick = () => { off ? SECHIDE.delete(k) : SECHIDE.add(k); try { localStorage.setItem('gr_sechide', JSON.stringify([...SECHIDE])); } catch (x) { } secDraw(); };
    bar.appendChild(b);
  }
}
function initFnp() {
  fnpTags(); fnpShow(); secDraw();
  $('fnppop').onclick = fnPop;
  $('fnptext').addEventListener('input', () => { if ($('fnptext').value.trim()) fnpStart(); });
  $('fnpwit').addEventListener('input', () => { if ($('fnpwit').value.trim()) fnpStart(); });
  $('fnprun').onchange = () => { fnpStart(); fnpShow(); };
  $('fnpsave').onclick = fnpSave; $('fnpcancel').onclick = fnpReset;
  enterSave($('fnptext'), fnpSave);
  $('fnptimebtn').onclick = () => timeEdit($('fnpext').hidden);
  const manual = () => { FNP.manual = true; FNP.timeTouched = true; FNP.approx = false; FNP.pend = null; };   // von Hand gesetzt: hat Vorrang vor Zeit-Tasten
  $('fnpfnow').onclick = () => { FNP.fixed = false; manual(); $('fnpfromi').value = dtl(new Date(nowMs())); fnpShow(); };
  $('fnpfromi').addEventListener('input', () => { const v = new Date($('fnpfromi').value).getTime(); if (!isNaN(v)) { FNP.fixed = true; FNP.from = v; } manual(); fnpShow(); });
  $('fnptoi').addEventListener('input', () => { manual(); fnpShow(); });
  $('fnpnotime').onchange = () => { FNP.notime = $('fnpnotime').checked; FNP.when = FNP.notime ? [...WHEN.keys()].find(k => WHEN.get(k).none) || null : null; FNP.timeTouched = true; fnpStart(); notimeShow(); fnpTags(); fnpShow(); };
  $('fnptnow').onclick = () => { $('fnptoi').value = dtl(new Date(nowMs())); fnpShow(); };
  $('fnptclr').onclick = () => { $('fnptoi').value = ''; fnpShow(); };
  setInterval(() => {                                 // die Uhr läuft mit, bis gespeichert wird (oder die Zeit von Hand gesetzt ist)
    if (document.hidden && !(FNPOP && !FNPOP.closed)) return;
    if (!FNP.fixed && !FNP.edit) { const fi = $('fnpfromi'); if (fi && !$('fnpext').hidden && fi.ownerDocument.activeElement !== fi) fi.value = dtl(new Date(nowMs())); }
    fnpShow();
  }, 1000);
  if (!matchMedia('(pointer:coarse)').matches) setTimeout(() => $('fnptext').focus({ preventScroll: true }), 300);
}
/* ---------- Liste: Zeitleiste nach Tagen oder Tabelle (nur Anzeige – gespeichert wird nichts anders) ---------- */
const cnt = n => t(n === 1 ? 'gr_count_1' : 'gr_count', { n });
const LST = { all: [], notes: [], q: '', tag: '', range: 'all', from: '', to: '', view: 'tl' };
try { LST.view = localStorage.getItem('gr_view') === 'tb' ? 'tb' : 'tl'; } catch (e) { }
const NOTIME = '__notime';                             // Filter „ohne Zeitpunkt“ in der Zeitleiste
const RANGES = ['all', 'today', 'd7', 'd30', 'custom'];
const dayStart = s => { const d = new Date(s + 'T00:00:00'); return isNaN(d.getTime()) ? null : d; };
function rangeMs() {                                   // gewählter Zeitraum als [von, bis] in ms (null = offen)
  const n = new Date(), back = k => new Date(n.getFullYear(), n.getMonth(), n.getDate() - k).getTime();
  if (LST.range === 'today') return [back(0), null];
  if (LST.range === 'd7') return [back(6), null];
  if (LST.range === 'd30') return [back(29), null];
  if (LST.range === 'custom') {
    const f = dayStart(LST.from), e = dayStart(LST.to);
    return [f ? f.getTime() : null, e ? new Date(e.getFullYear(), e.getMonth(), e.getDate() + 1).getTime() - 1 : null];
  }
  return [null, null];
}
function rangeTitle() {
  if (LST.range === 'custom') {
    const f = dayStart(LST.from), e = dayStart(LST.to), a = f ? fDate(f.getTime()) : '', b = e ? fDate(e.getTime()) : '';
    return a && b ? t('gr_ttl_ft', { a, b }) : a ? t('gr_ttl_f', { a }) : b ? t('gr_ttl_t', { b }) : t('gr_list');
  }
  return t({ today: 'gr_ttl_today', d7: 'gr_ttl_d7', d30: 'gr_ttl_d30' }[LST.range] || 'gr_list');
}
async function listLoad() {
  const [f, e] = rangeMs(); let u = 'notes?limit=5000';
  if (f != null) u += '&from=' + f; if (e != null) u += '&to=' + e;
  try {
    const fresh = (await (await fetch(u, { cache: 'no-store' })).json()).notes || [];
    const old = new Map(LST.all.map(n => [n.id, n]));     // unveränderte Notizen behalten (Tabelle zeichnet dann nichts neu)
    LST.all = fresh.map(n => { const o = old.get(n.id); return o && JSON.stringify(o) === JSON.stringify(n) ? o : n; });
  } catch (x) { }
  listDraw();
}
// „erfasst 14:32:10, Taste: vor 5 Min.“ – Erfassungszeit und gewählter Zeitpunkt getrennt; ≈ = ungefähr
function metaTxt(n) {
  const p = [];
  if (n.notime) return '';
  if (n.cap && !n.wk && Math.abs(n.cap - n.a) > 60000) p.push(t('gr_capinfo_only', { t: fTime(n.cap) + (isoDay(new Date(n.cap)) !== isoDay(new Date(n.a)) ? ' (' + fDate(n.cap) + ')' : '') }));
  if (n.wk) p.push(t('gr_capinfo', { t: n.cap ? fTime(n.cap) + (isoDay(new Date(n.cap)) !== isoDay(new Date(n.a)) ? ' (' + fDate(n.cap) + ')' : '') : '–', k: n.wl || ntLabel(n.wk) }));
  if (n.approx) p.push(t('gr_approx'));
  return p.join(' · ');
}
const qMatch = (n, q) => ([n.text || '', n.witness || ''].concat(n.tagl || [], (n.tags || []).map(ntLabel)).join(' ')).toLowerCase().includes(q);
function countShow(n, m, f) {
  const c = document.getElementById('grcount'), s = f ? t('gr_cnt_f', { n, m }) : cnt(m);
  if (c.textContent !== s) c.textContent = s;
  document.getElementById('grclr').hidden = !f;
}
function filtDraw() {
  const box = document.getElementById('grfilt'); if (!box) return;
  const cnt = {}; for (const n of LST.notes) for (const k of n.tags || []) cnt[k] = (cnt[k] || 0) + 1;
  const top = Object.keys(cnt).sort((a, b) => cnt[b] - cnt[a]).slice(0, 10);
  const nn = LST.notes.filter(n => n.notime).length;
  box.innerHTML = (top.length > 1 ? top.map(k => `<button type="button" class="tag ${gAttr(ntGroup(k)).replace('"', LST.tag === k ? ' on"' : '"')} data-t="${esc(k)}" aria-pressed="${LST.tag === k}">${esc(ntLabel(k))} <small>${cnt[k]}</small></button>`).join('') : '')
    + (nn ? `<button type="button" class="tag ${gAttr('when').replace('"', LST.tag === NOTIME ? ' on"' : '"')} data-t="${NOTIME}" aria-pressed="${LST.tag === NOTIME}">${esc(t('gr_notime'))} <small>${nn}</small></button>` : '');
  box.querySelectorAll('.tag').forEach(b => b.onclick = () => { LST.tag = LST.tag === b.dataset.t ? '' : b.dataset.t; listDraw(); });
}
/* Breite: ganze Breite (Standard, wie die Tabelle) oder schmale Spalte; die Tabelle ist immer breit */
function widthApply(w) { document.body.classList.toggle('grwide', (w || (PF && PF.width) || 'wide') === 'wide'); }
function viewShow() {
  const tb = LST.view === 'tb';
  document.getElementById('grnotes').hidden = tb; document.getElementById('grgrid').hidden = !tb;
  document.getElementById('grfilt').hidden = tb; document.getElementById('grcols').hidden = !tb;
  if (!tb) colMenuClose();
  document.getElementById('logsec').classList.toggle('tbl', tb);
  widthApply();
  document.querySelectorAll('#grview button').forEach(b => { const on = b.dataset.v === LST.view; b.classList.toggle('on', on); b.setAttribute('aria-pressed', String(on)); });
}
async function noteDel(n) {
  if (!confirm(t('fn_del_q'))) return;
  try { await post('note', { action: 'del', id: n.id }); } catch (e) { }
  if (FNP.edit && FNP.edit.id === n.id) fnpReset(); listLoad();
}
function listDraw() {
  const q = LST.q.trim().toLowerCase().slice(0, 80);
  LST.notes = q ? LST.all.filter(n => qMatch(n, q)) : LST.all;
  const ttl = document.getElementById('logttl'), tt = rangeTitle(); if (ttl.textContent !== tt) ttl.textContent = tt;
  viewShow();
  if (LST.view === 'tb' && window.agGrid) { tblDraw(); return; }
  const box = document.getElementById('grnotes'); if (!box) return; box.innerHTML = ''; box.hidden = false;
  filtDraw();
  const list = LST.tag === NOTIME ? LST.notes.filter(n => n.notime) : LST.tag ? LST.notes.filter(n => (n.tags || []).includes(LST.tag)) : LST.notes;
  countShow(list.length, LST.all.length, !!(q || LST.tag));
  if (!list.length) { box.appendChild(el('div', { className: 'empty', textContent: t(q || LST.tag || LST.range !== 'all' ? 'gr_none_q' : 'gr_none') })); return; }
  const days = new Map(); for (const n of list) { const k = isoDay(new Date(n.a)); if (!days.has(k)) days.set(k, []); days.get(k).push(n); }
  for (const [, ns] of days) {
    const h = el('div', { className: 'day' }); h.innerHTML = `<span>${esc(fDay(ns[0].a))}</span><small>${esc(cnt(ns.length))}</small>`; box.appendChild(h);
    for (const n of ns) {
      const r = el('div', { className: 'note' + (FNP.edit && FNP.edit.id === n.id ? ' cur' : '') });
      const by = n.by === 'homeassistant' ? '🏠 Home Assistant' : n.by === 'import' ? t('gr_imported') : '';
      r.innerHTML = `<div class="t">${n.notime ? `<small class="nt">${esc(t('gr_notime'))}</small>` : esc((n.approx ? '≈ ' : '') + fTime(n.a))}${n.to ? `<small>${esc(t('gr_until', { t: fTime(n.b) }))}</small>` : ''}</div>
        <div class="c">${(n.tags || []).filter(k => k !== 'zeuge' || !n.witness).map(tagMk).join('')}${n.text ? `<span class="tx">${esc(n.text)}</span>` : ''}${n.witness ? `<span class="who">👤 ${esc(witTxt(n))}</span>` : ''}${extTxt(n).map(x => `<span class="by ext">${esc(x)}</span>`).join('')}${(n.att || []).length ? `<button type="button" class="by attb" aria-label="${esc(t('gr_att_open') + ': ' + n.att.map(a => a.name).join(', '))}" title="${esc(n.att.map(a => a.name).join(', '))}">📎 ${n.att.length}</button>` : ''}${by ? `<span class="by">${esc(by)}</span>` : ''}${metaTxt(n) ? `<span class="by meta">${esc(metaTxt(n))}</span>` : ''}${n.edited ? `<button type="button" class="by histb" data-h="${esc(n.id)}">${esc(t('gr_edited_at', { t: fDate(Date.parse(n.edited)) + ' ' + fTime(Date.parse(n.edited)) }))}</button>` : ''}</div>
        <div class="a"><button type="button" class="e" aria-label="${esc(t('nt_edit'))}" title="${esc(t('nt_edit'))}">✎</button><button type="button" class="d" aria-label="${esc(t('nt_del'))}" title="${esc(t('nt_del'))}">🗑</button></div>`;
      r.querySelector('.e').onclick = () => fnpEdit(n);
      r.querySelector('.d').onclick = () => noteDel(n);
      const hb = r.querySelector('.histb'); if (hb) hb.onclick = () => histOpen(n);
      const ab = r.querySelector('.attb'); if (ab) ab.onclick = () => attOpen(n.id);
      box.appendChild(r);
    }
  }
}
/* Tabelle (AG Grid Community, MIT – liegt der App bei, kein Internet nötig). Farben kommen aus den CSS-Variablen von GReport,
   dadurch folgen hell, dunkel und der Design-Knopf automatisch. */
let GRID = null, GRID_FMT = '', GRID_EDIT = null;
const NARROW = () => matchMedia('(max-width:600px)').matches;
const COLS = 'day time text tags witness'.split(' ');
const colKey = () => 'gr_cols' + (NARROW() ? '_n' : '');
function colVisible() {
  const v = NARROW() ? { day: true, time: false, text: true, tags: false, witness: false } : { day: true, time: true, text: true, tags: true, witness: true };
  try { Object.assign(v, JSON.parse(localStorage.getItem(colKey()) || '{}')); } catch (e) { }
  return v;
}
function colApply() {
  if (!GRID) return; const v = colVisible();
  GRID.setColumnsVisible(COLS.filter(c => v[c]), true); GRID.setColumnsVisible(COLS.filter(c => !v[c]), false);
  GRID.setColumnWidths([{ key: 'act', newWidth: NARROW() ? 80 : 104 }]); GRID.refreshHeader();   // schmal: Aktionen ohne Überschrift
  GRID.refreshCells({ columns: ['day'], force: true });   // ohne Spalte „Uhrzeit“ steht die Uhrzeit unter dem Datum
}
const gridTheme = () => agGrid.themeQuartz.withParams({
  backgroundColor: 'var(--card)', foregroundColor: 'var(--ink)', textColor: 'var(--ink)', subtleTextColor: 'var(--mut)',
  chromeBackgroundColor: 'var(--soft)', headerBackgroundColor: 'var(--soft)', headerTextColor: 'var(--ink)', headerFontWeight: 650,
  borderColor: 'var(--line)', rowBorder: { color: 'var(--line)' }, accentColor: 'var(--acc)', rangeSelectionBorderColor: 'var(--acc)',
  rowHoverColor: 'color-mix(in srgb, var(--acc) 7%, transparent)', selectedRowBackgroundColor: 'color-mix(in srgb, var(--acc) 12%, transparent)',
  inputBackgroundColor: 'var(--card)', inputBorder: { color: 'var(--line)' }, inputTextColor: 'var(--ink)', inputPlaceholderTextColor: 'var(--mut)',
  inputFocusBorder: { color: 'var(--acc)', width: 2 }, focusShadow: '0 0 0 2px var(--acc)', menuBackgroundColor: 'var(--card)', menuTextColor: 'var(--ink)',
  fontFamily: 'inherit', fontSize: 14, headerFontSize: 13.5, wrapperBorderRadius: 10, borderRadius: 8, spacing: 7, browserColorScheme: 'inherit',
  iconColor: 'var(--mut)'
});
const agText = p => {                                  // Texte der Tabelle selbst (Filter, Hinweise für Screenreader)
  let s = (I18N[lang] || I18N.de)['ag_' + p.key]; if (s == null) return p.defaultValue;
  for (const v of p.variableValues || []) s = s.replace('${variable}', v);
  return s;
};
class TagFilter {                                      // Mehrfachauswahl: Notizen mit mindestens einem der gewählten Wörter
  init(p) { this.p = p; this.sel = new Set(); this.gui = el('div', { className: 'tagf' }); this.draw(); }
  words() { const c = {}; for (const n of LST.notes) for (const k of n.tags || []) c[k] = (c[k] || 0) + 1; for (const k of this.sel) c[k] = c[k] || 0; return Object.keys(c).sort((a, b) => c[b] - c[a] || ntLabel(a).localeCompare(ntLabel(b))).map(k => [k, c[k]]); }
  draw() {
    const ws = this.words();
    this.gui.innerHTML = `<fieldset><legend>${esc(t('gr_f_words'))}</legend>${ws.length ? ws.map(([k, n]) => `<label class="check"><input type="checkbox" value="${esc(k)}"${this.sel.has(k) ? ' checked' : ''}><span class="mk ${gAttr(ntGroup(k))}>${esc(ntLabel(k))}</span><small>${n}</small></label>`).join('') : `<p class="hint">${esc(t('gr_none_q'))}</p>`}</fieldset>
      <div class="tagfb"><button type="button" class="btn"${this.sel.size ? '' : ' disabled'}>${esc(t('gr_f_none'))}</button></div>`;
    this.gui.querySelectorAll('input').forEach(i => i.onchange = () => { i.checked ? this.sel.add(i.value) : this.sel.delete(i.value); this.gui.querySelector('.tagfb button').disabled = !this.sel.size; this.p.filterChangedCallback(); });
    this.gui.querySelector('.tagfb button').onclick = () => { this.sel.clear(); this.draw(); this.p.filterChangedCallback(); const f = this.gui.querySelector('input'); if (f) f.focus(); };
  }
  getGui() { return this.gui; }
  afterGuiAttached() { this.draw(); const f = this.gui.querySelector('input'); if (f) f.focus(); }
  isFilterActive() { return this.sel.size > 0; }
  doesFilterPass(p) { const tg = p.data.tags || []; for (const k of this.sel) if (tg.includes(k)) return true; return false; }
  getModel() { return this.sel.size ? { values: [...this.sel] } : null; }
  setModel(m) { this.sel = new Set((m && m.values) || []); this.draw(); }
}
class TagFloat {                                       // Kopfzeile: zeigt „Alle“ oder „2 gewählt“, öffnet die Auswahl
  init(p) { this.b = el('button', { type: 'button', className: 'tagff tagw' }); this.b.onclick = () => p.showParentFilter(); this.onParentModelChanged(null); }
  onParentModelChanged(m) { const n = m && m.values ? m.values.length : 0; this.b.textContent = n ? t('gr_f_n', { n }) : t('gr_f_all'); this.b.setAttribute('aria-label', t('gr_c_tags') + ': ' + this.b.textContent); }
  getGui() { return this.b; }
}
class DateFloat {                                     // Kopfzeile Datum: zeigt den gewählten Zeitraum, öffnet den Datumsfilter
  init(p) { this.b = el('button', { type: 'button', className: 'tagff datef' }); this.b.onclick = () => p.showParentFilter(); this.onParentModelChanged(null); }
  onParentModelChanged(m) {
    const d = s => s ? fDate(new Date(String(s).slice(0, 10) + 'T12:00:00').getTime()) : '';
    const v = !m ? t('gr_f_all') : m.type === 'inRange' ? d(m.dateFrom) + ' – ' + d(m.dateTo) : m.type === 'lessThan' ? t('gr_f_before', { d: d(m.dateFrom) }) : m.type === 'greaterThan' ? t('gr_f_after', { d: d(m.dateFrom) }) : d(m.dateFrom);
    this.b.textContent = v; this.b.setAttribute('aria-label', t('gr_c_day') + ': ' + v);
  }
  getGui() { return this.b; }
}
class TimeFilter {                                     // Uhrzeit: mit Zeitpunkt / ohne Zeitpunkt / per Taste / ungefähr
  init(p) { this.p = p; this.sel = new Set(); this.gui = el('div', { className: 'tagf' }); this.draw(); }
  draw() {
    const o = ['with', 'none', 'key', 'approx'];
    this.gui.innerHTML = `<fieldset><legend>${esc(t('gr_c_time'))}</legend>${o.map(x => `<label class="check"><input type="checkbox" value="${x}"${this.sel.has(x) ? ' checked' : ''}> ${esc(t('gr_tf_' + x))}</label>`).join('')}</fieldset>`;
    this.gui.querySelectorAll('input').forEach(i => i.onchange = () => { i.checked ? this.sel.add(i.value) : this.sel.delete(i.value); this.p.filterChangedCallback(); });
  }
  getGui() { return this.gui; }
  afterGuiAttached() { const f = this.gui.querySelector('input'); if (f) f.focus(); }
  isFilterActive() { return this.sel.size > 0; }
  doesFilterPass(p) { const n = p.data; return (this.sel.has('with') && !n.notime) || (this.sel.has('none') && n.notime) || (this.sel.has('key') && !!n.wk) || (this.sel.has('approx') && !!n.approx); }
  getModel() { return this.sel.size ? { values: [...this.sel] } : null; }
  setModel(m) { this.sel = new Set((m && m.values) || []); this.draw(); }
}
class TimeFloat {
  init(p) { this.b = el('button', { type: 'button', className: 'tagff timef' }); this.b.onclick = () => p.showParentFilter(); this.onParentModelChanged(null); }
  onParentModelChanged(m) { const v = m && m.values && m.values.length ? m.values.map(x => t('gr_tf_' + x)).join(', ') : t('gr_f_all'); this.b.textContent = v; this.b.setAttribute('aria-label', t('gr_c_time') + ': ' + v); }
  getGui() { return this.b; }
}
const dayOf = ms => { const d = new Date(ms); return new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime(); };
const secOfDay = ms => { const d = new Date(ms); return d.getHours() * 3600 + d.getMinutes() * 60 + d.getSeconds(); };
const timeTxt = n => n.notime ? t('gr_notime') : (n.approx ? '≈ ' : '') + fTime(n.a) + (n.to ? ' – ' + fTime(n.b) : '');
function actCell(p) {
  const w = el('div', { className: 'acts' });
  w.innerHTML = `<button type="button" class="e" tabindex="-1" aria-label="${esc(t('nt_edit'))}" title="${esc(t('nt_edit'))}">✎</button><button type="button" class="d" tabindex="-1" aria-label="${esc(t('nt_del'))}" title="${esc(t('nt_del'))}">🗑</button>`;
  w.querySelector('.e').onclick = () => fnpEdit(p.data); w.querySelector('.d').onclick = () => noteDel(p.data);
  w.addEventListener('keydown', e => {                 // in der Zelle: ←/→ und Tab wechseln zwischen ✎ und 🗑, Esc zurück zur Zelle
    const bs = [...w.querySelectorAll('button')], i = bs.indexOf(document.activeElement); if (i < 0) return;
    if (e.key === 'ArrowRight' || e.key === 'ArrowLeft' || (e.key === 'Tab' && (e.shiftKey ? i === 1 : i === 0))) { e.preventDefault(); bs[1 - i].focus(); }
    else if (e.key === 'Escape') { e.preventDefault(); p.api.setFocusedCell(p.node.rowIndex, 'act'); }
  });
  return w;
}
function gridOpts() {
  const tf = { maxNumConditions: 1, buttons: ['reset'], filterOptions: ['contains', 'notContains', 'equals', 'startsWith', 'blank', 'notBlank'] };
  return {
    theme: gridTheme(), getLocaleText: agText, rowData: [], getRowId: p => String(p.data.id),
    defaultColDef: { sortable: true, resizable: true, suppressHeaderMenuButton: true, floatingFilter: true, filter: false },
    columnDefs: [
      { colId: 'day', field: 'a', headerName: t('gr_c_day'), sort: 'desc', flex: 1.1, minWidth: 96, filter: 'agDateColumnFilter',
        filterParams: { comparator: (fd, v) => { const d = dayOf(v); return d < fd.getTime() ? -1 : d > fd.getTime() ? 1 : 0; }, filterOptions: ['inRange', 'equals', 'lessThan', 'greaterThan'], defaultOption: 'inRange', inRangeInclusive: true, maxNumConditions: 1, buttons: ['reset'] },
        floatingFilterComponent: DateFloat, cellRenderer: p => `<span>${esc(fDay(p.data.a))}</span>${GRID && !GRID.getColumn('time').isVisible() ? `<small class="tm">${esc(timeTxt(p.data))}</small>` : ''}`,
        getQuickFilterText: () => '' },
      { colId: 'time', headerName: t('gr_c_time'), valueGetter: p => p.data.notime ? -1 : secOfDay(p.data.a), flex: 1.2, minWidth: 124, wrapText: true, autoHeight: true, cellClass: 'num',
        cellRenderer: p => `<span>${esc(timeTxt(p.data))}</span>${metaTxt(p.data) ? `<small class="tm">${esc(metaTxt(p.data))}</small>` : ''}${p.data.edited ? `<small class="tm">${esc(t('gr_edited'))}</small>` : ''}`,
        filter: TimeFilter, floatingFilterComponent: TimeFloat, getQuickFilterText: p => timeTxt(p.data) },
      { colId: 'text', field: 'text', headerName: t('gr_c_text'), flex: 3, minWidth: 100, wrapText: true, autoHeight: true, filter: 'agTextColumnFilter', filterParams: tf,
        cellRenderer: p => `<span>${esc(p.data.text || '')}</span>${(p.data.att || []).length ? ` <button type="button" class="attb linkbtn" tabindex="-1" aria-label="${esc(t('gr_att_open'))}">📎 ${p.data.att.length}</button>` : ''}${extTxt(p.data).map(x => `<small class="tm">${esc(x)}</small>`).join('')}`, getQuickFilterText: p => (p.data.text || '') + ' ' + extTxt(p.data).join(' ') },
      { colId: 'tags', field: 'tags', headerName: t('gr_c_tags'), cellDataType: false, flex: 2.2, minWidth: 150, sortable: false, wrapText: true, autoHeight: true, filter: TagFilter, floatingFilterComponent: TagFloat,
        cellRenderer: p => `<div class="mks">${(p.data.tags || []).filter(k => k !== 'zeuge' || !p.data.witness).map(tagMk).join('')}</div>` },
      { colId: 'witness', field: 'witness', headerName: t('gr_c_witness'), flex: 1.2, minWidth: 100, wrapText: true, autoHeight: true, filter: 'agTextColumnFilter', filterParams: tf,
        valueFormatter: p => p.data.witness ? witTxt(p.data) : '' },
      { colId: 'act', headerName: t('gr_c_act'), headerValueGetter: () => NARROW() ? '' : t('gr_c_act'), headerTooltip: t('gr_act_tip'), width: NARROW() ? 80 : 104, minWidth: 80, maxWidth: 104, sortable: false, resizable: false, floatingFilter: false, cellClass: 'actc', cellRenderer: actCell,
        suppressKeyboardEvent: p => !!(p.event.target && p.event.target.closest && p.event.target.closest('.acts button')) }
    ],
    rowClassRules: { cur: p => !!(FNP.edit && p.data && FNP.edit.id === p.data.id) },
    tabToNextCell: () => false,                        // Tab verlässt die Tabelle (Pfeiltasten bewegen sich darin)
    tooltipShowDelay: 400, suppressCellFocus: false, animateRows: false, enableCellTextSelection: true, ensureDomOrder: true,
    onCellKeyDown: p => { if (p.column.getColId() === 'act' && (p.event.key === 'Enter' || p.event.key === 'F2') && !p.event.target.closest('.acts button')) { const c = p.event.target.querySelector && p.event.target.querySelector('.acts button'); if (c) { p.event.preventDefault(); c.focus(); } } },
    onFilterChanged: tblCount, onModelUpdated: tblCount,
    onCellClicked: p => { const b = p.event && p.event.target && p.event.target.closest && p.event.target.closest('.attb'); if (b) attOpen(p.data.id); },
    overlayNoRowsTemplate: `<span class="empty">${esc(t('gr_none_q'))}</span>`
  };
}
function tblCount() { if (GRID) countShow(GRID.getDisplayedRowCount(), LST.all.length, GRID.isAnyFilterPresent() || !!LST.q.trim()); }
function tblDraw() {
  if (!GRID) { GRID = agGrid.createGrid(document.getElementById('grgrid'), gridOpts()); colApply(); }
  const fk = JSON.stringify([PF, lang, NTS.ren, NTS.own, NTS.grp]);
  GRID.setGridOption('rowData', LST.notes);
  if (fk !== GRID_FMT) { GRID_FMT = fk; GRID.refreshCells({ force: true }); }
  const ed = FNP.edit ? FNP.edit.id : null; if (ed !== GRID_EDIT) { GRID_EDIT = ed; GRID.redrawRows(); }
  tblCount();
}
function colMenuClose() { const m = document.getElementById('grcolm'); if (m && !m.hidden) { m.hidden = true; document.getElementById('grcols').setAttribute('aria-expanded', 'false'); } }
function colMenu() {
  const m = document.getElementById('grcolm'), b = document.getElementById('grcols');
  if (!m.hidden) { colMenuClose(); return; }
  const v = colVisible();
  m.innerHTML = `<b class="colttl">${esc(t('gr_cols'))}</b>` + COLS.map(c => `<label class="check"><input type="checkbox" data-c="${c}"${v[c] ? ' checked' : ''}> ${esc(t('gr_c_' + c))}</label>`).join('');
  const boxes = [...m.querySelectorAll('input')];
  const lock = () => { const on = boxes.filter(x => x.checked); boxes.forEach(x => { x.disabled = on.length === 1 && x.checked; }); };   // mindestens eine Spalte bleibt
  boxes.forEach(x => x.onchange = () => { const nv = colVisible(); nv[x.dataset.c] = x.checked; try { localStorage.setItem(colKey(), JSON.stringify(nv)); } catch (e) { } colApply(); lock(); });
  lock(); m.hidden = false; b.setAttribute('aria-expanded', 'true'); boxes[0].focus();
  m.onkeydown = e => { if (e.key === 'Escape') { e.preventDefault(); colMenuClose(); b.focus(); } };
}
function initList() {
  const rs = document.getElementById('grrange'); rs.innerHTML = ''; for (const r of RANGES) option(rs, r, t('gr_r_' + r));
  rs.value = LST.range;
  const cust = () => { const c = LST.range === 'custom'; document.getElementById('grcust').hidden = !c; };
  rs.onchange = () => {
    LST.range = rs.value; cust();
    if (LST.range === 'custom' && !LST.from && !LST.to) { const d = new Date(); LST.to = isoDay(d); LST.from = isoDay(new Date(d.getFullYear(), d.getMonth() - 1, d.getDate())); document.getElementById('grfrom').value = LST.from; document.getElementById('grto').value = LST.to; }
    listLoad();
  };
  for (const id of ['grfrom', 'grto']) document.getElementById(id).addEventListener('change', e => { LST[id === 'grfrom' ? 'from' : 'to'] = e.target.value; listLoad(); });
  cust();
  document.querySelectorAll('#grview button').forEach(b => b.onclick = () => { LST.view = b.dataset.v; try { localStorage.setItem('gr_view', LST.view); } catch (e) { } listDraw(); });
  document.getElementById('grclr').onclick = () => {
    LST.q = ''; LST.tag = ''; document.getElementById('grq').value = ''; if (GRID) GRID.setFilterModel(null);
    listDraw(); document.getElementById('grq').focus();
  };
  document.getElementById('grcols').onclick = e => { e.stopPropagation(); colMenu(); };
  document.addEventListener('click', e => { if (!e.target.closest('#grcolm,#grcols')) colMenuClose(); });
  matchMedia('(max-width:600px)').addEventListener('change', () => { colMenuClose(); colApply(); });
  viewShow();
}
/* ---------- Schnellwahl bearbeiten (Dialog): umbenennen, Gruppe, Reihenfolge, ausblenden, zurücksetzen ---------- */
function qtOpen(focus) {
  const d = document.getElementById('qtdlg');
  const gsel = document.getElementById('qtnewg'); gsel.innerHTML = ''; for (const g of wordGroups()) option(gsel, g, gLabel(g)); gsel.value = 'own';
  qtDraw(focus); if (!d.open) d.showModal();
  if (!focus) setTimeout(() => document.getElementById('qtnew').focus(), 50);
}
function qtDraw(focus) {
  const box = document.getElementById('qtlist'); box.innerHTML = '';
  document.querySelectorAll('#qtdlg .seg button').forEach(b => { const on = b.dataset.mode === NTS.mode; b.classList.toggle('on', on); b.setAttribute('aria-checked', String(on)); b.setAttribute('role', 'radio'); });
  const ownN = Object.keys(NTS.own).filter(k => !NTS.del.has(k)).length;
  document.getElementById('qtinfo').textContent = (PRO() ? t('gr_qt_pro', { n: ownN, m: NTS.max }) + ' ' : t('gr_qt_free', { n: ownN, m: NTS.max }) + ' ') + t(NTS.mode === 'fixed' ? 'gr_mode_fixed_h' : 'gr_mode_use_h');
  const lim = document.getElementById('qtlim');
  lim.innerHTML = `<label>${esc(t('gr_lim_own'))} <input type="number" id="qtlimn" min="5" max="${NTS.proMax}" value="${NTS.limit}"${PRO() ? '' : ' disabled'}></label><label>${esc(t('gr_lim_show'))} <input type="number" id="qtshown" min="0" max="50" value="${NTS.show}"${PRO() ? '' : ' disabled'}></label>${PRO() ? '' : '<span>🔒 Pro</span>'}`;
  if (PRO()) {
    document.getElementById('qtlimn').onchange = e => ntsPost({ action: 'limit', n: +e.target.value }).then(() => qtDraw()).catch(x => alert(x.message));
    document.getElementById('qtshown').onchange = e => ntsPost({ action: 'show', n: +e.target.value }).then(() => qtDraw()).catch(x => alert(x.message));
  }
  const sg = document.getElementById('qtsug'); sg.innerHTML = NTS.sug.map(w => `<button type="button" class="chip" data-w="${esc(w.w)}">💡 ${esc(w.w)} (${w.n}×) ＋</button>`).join('');
  sg.querySelectorAll('button').forEach(b => b.onclick = () => ntsPost({ action: 'add', l: b.dataset.w }).then(() => qtDraw()).catch(e => alert(e.message)));
  const all = ntOrdered(ntAll()), by = {}; for (const k of all) (by[ntGroup(k)] = by[ntGroup(k)] || []).push(k);
  for (const g of wordGroups()) {
    const ks = by[g] || []; if (!ks.length) continue;
    const sec = el('div', { className: 'qtg ' + (gCustom(g) ? 'g-cu' : 'g-' + g) }); if (gCustom(g)) { sec.style.setProperty('--uc', gColor(g)); sec.style.setProperty('--udc', gColor(g)); } const gc = (NTS.gcol || {})[g];
 const rq = NTS.req && NTS.req.has(g);
    sec.innerHTML = `<h4>${esc(gLabel(g))}<label class="reqc" title="${esc(t('gr_req_tip'))}"><input type="checkbox"${rq ? ' checked' : ''}> ${esc(t('gr_req'))}</label><input type="color" value="${esc(gc || G_DEF[g] || gColor(g))}" aria-label="${esc(t('gr_gcol', { g: gLabel(g) }))}" title="${esc(t('gr_gcol', { g: gLabel(g) }))}">${gc ? `<button type="button" class="gcr" title="${esc(t('gr_gcol_reset'))}" aria-label="${esc(t('gr_gcol_reset'))}">↺</button>` : ''}</h4>`;
    sec.querySelector('.reqc input').onchange = e => ntsPost({ action: 'req', g, on: e.target.checked }).then(() => qtDraw()).catch(x => alert(x.message));
    const ci = sec.querySelector('input[type=color]');
    ci.addEventListener('input', () => { NTS.gcol = Object.assign({}, NTS.gcol, { [g]: ci.value }); gcolApply(); });
    ci.addEventListener('change', () => ntsPost({ action: 'gcol', g, c: ci.value }).then(() => qtDraw()).catch(e => alert(e.message)));
    const cr = sec.querySelector('.gcr'); if (cr) cr.onclick = () => ntsPost({ action: 'gcol', g, c: '' }).then(() => qtDraw());
    const rows = el('div', { className: 'qtrows' });
    for (const k of ks) {
      const own = NTS.own[k] != null, off = NTS.hide.has(k);
      const r = el('div', { className: 'qtr' + (off ? ' off' : '') }); r.dataset.k = k; r.draggable = true;
      r.innerHTML = `<span class="hd" title="${esc(t('gr_drag'))}" aria-hidden="true">⠿</span><input type="text" maxlength="30" value="${esc(ntLabel(k))}" aria-label="${esc(t('qt_ren'))}"><select aria-label="${esc(t('gr_group'))}">${wordGroups().map(x => `<option value="${x}"${x === g ? ' selected' : ''}>${esc(gLabel(x))}</option>`).join('')}</select>
        <span class="b"><button type="button" class="up" aria-label="${esc(t('gr_up'))}" title="${esc(t('gr_up'))}">▲</button><button type="button" class="dn" aria-label="${esc(t('gr_down'))}" title="${esc(t('gr_down'))}">▼</button>${own ? `<button type="button" class="del" aria-label="${esc(t('nt_del'))}" title="${esc(t('nt_del'))}">🗑</button>` : `<label class="vis" title="${esc(t('gr_shown_tip'))}"><input type="checkbox"${off ? '' : ' checked'}> ${esc(t('gr_shown'))}</label>`}</span>`;
      const inp = r.querySelector('input');
      const ren = () => { const v = inp.value.trim(); if (v && v !== ntLabel(k)) ntsPost({ action: 'ren', k, l: v }).then(() => qtDraw()).catch(e => alert(e.message)); };
      inp.addEventListener('change', ren); inp.addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); inp.blur(); } });
      r.querySelector('select').onchange = e => ntsPost({ action: 'grp', k, g: e.target.value }).then(() => qtDraw()).catch(x => alert(x.message));
      r.querySelector('.up').onclick = () => qtMove(k, -1); r.querySelector('.dn').onclick = () => qtMove(k, 1);
      const vb = r.querySelector('.vis input'); if (vb) vb.onchange = () => ntsPost({ action: 'hide', k, on: !vb.checked }).then(() => qtDraw());
      const db = r.querySelector('.del'); if (db) db.onclick = () => { if (confirm(t('qt_del_q', { n: ntLabel(k) }))) ntsPost({ action: 'del', k }).then(() => qtDraw()); };
      r.addEventListener('dragstart', e => { r.classList.add('drag'); e.dataTransfer.setData('text/plain', k); e.dataTransfer.effectAllowed = 'move'; });
      r.addEventListener('dragend', () => r.classList.remove('drag'));
      r.addEventListener('dragover', e => { e.preventDefault(); r.classList.add('over'); });
      r.addEventListener('dragleave', () => r.classList.remove('over'));
      r.addEventListener('drop', e => { e.preventDefault(); r.classList.remove('over'); const from = e.dataTransfer.getData('text/plain'); if (from && from !== k) qtPlace(from, k); });
      rows.appendChild(r);
      if (focus === k) setTimeout(() => { inp.focus(); inp.select(); r.scrollIntoView({ block: 'center' }); }, 60);
    }
    sec.appendChild(rows); box.appendChild(sec);
  }
}
function qtSaveOrder(list) { return ntsPost({ action: 'order', keys: list }).then(() => qtDraw()).catch(e => alert(e.message)); }
function qtMove(k, dir) {                              // ▲▼ innerhalb der Gruppe
  const all = ntOrdered(ntAll()), g = ntGroup(k), same = all.filter(x => ntGroup(x) === g), i = same.indexOf(k), j = i + dir;
  if (j < 0 || j >= same.length) return;
  const a = all.indexOf(k), b = all.indexOf(same[j]); [all[a], all[b]] = [all[b], all[a]]; qtSaveOrder(all);
}
function qtPlace(from, before) {                        // Ziehen: vor das Ziel setzen (Gruppe des Ziels übernehmen)
  const all = ntOrdered(ntAll()).filter(x => x !== from); all.splice(all.indexOf(before), 0, from);
  const g = ntGroup(before);
  (ntGroup(from) !== g ? ntsPost({ action: 'grp', k: from, g }) : Promise.resolve()).then(() => qtSaveOrder(all));
}
function initQt() {
  document.querySelectorAll('#qtdlg .seg button').forEach(b => b.onclick = () => ntsPost(b.dataset.mode === 'fixed' ? { action: 'order', keys: ntOrdered(ntAll()) } : { action: 'mode', mode: 'use' }).then(() => qtDraw()));
  document.getElementById('qtreset').onclick = () => { if (confirm(t('gr_reset_q'))) ntsPost({ action: 'reset' }).then(() => qtDraw()); };
  const add = () => { const v = document.getElementById('qtnew').value.trim(); if (!v) return; ntsPost({ action: 'add', l: v, g: document.getElementById('qtnewg').value }).then(() => { document.getElementById('qtnew').value = ''; qtDraw(); }).catch(e => alert(e.message)); };
  document.getElementById('qtaddok').onclick = add;
  document.getElementById('qtnew').addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); add(); } });
}
/* ---------- Anzeige: Datum und Uhrzeit ---------- */
function prefOpen() {
  const ds = document.getElementById('pfdate'), ts = document.getElementById('pftime'), ex = Date.now();
  ds.innerHTML = ''; for (const f of ['dmy4', 'dmy2', 'wdm', 'iso', 'long']) option(ds, f, fDate(ex, Object.assign({}, PF, { date: f, wd: false })));
  ts.innerHTML = ''; for (const f of ['hms', 'hm', 'h12']) option(ts, f, fTime(ex, Object.assign({}, PF, { time: f })));
  ds.value = PF.date; ts.value = PF.time; document.getElementById('pfrel').checked = PF.rel; document.getElementById('pfwd').checked = PF.wd;
  document.getElementById('pftipmode').value = tipMode();
  document.getElementById('pftipsr').onclick = () => { TIPX.clear(); try { localStorage.removeItem('gr_tipx'); } catch (e) { } tipsDraw(); toast('✓ ' + t('gr_p_tips_done')); };
  const upd = () => { const p = prefRead(); document.getElementById('pfex').textContent = fDate(ex, p) + ', ' + fTime(ex, p); };
  for (const x of [ds, ts, document.getElementById('pfrel'), document.getElementById('pfwd')]) x.onchange = upd;
  upd(); document.getElementById('prefdlg').showModal();
}
const prefRead = () => ({ date: document.getElementById('pfdate').value, time: document.getElementById('pftime').value, rel: document.getElementById('pfrel').checked, wd: document.getElementById('pfwd').checked, tipmode: document.getElementById('pftipmode').value, tips: document.getElementById('pftipmode').value !== 'off' });
/* ---------- Textdatei & Import/Export (Pro) ---------- */
const TXT = { st: null, content: null };
const txtErr = e => { const k = 'gr_err_' + String(e || 'x').replace(/\W/g, '_'); const v = t(k); return v === k ? t('gr_err_x') + (e ? ' (' + e + ')' : '') : v; };
async function txtOpen() {
  const d = document.getElementById('txtdlg');
  try { TXT.st = await (await fetch('textfile', { cache: 'no-store' })).json(); } catch (e) { TXT.st = {}; }
  const s = TXT.st || {};
  document.getElementById('txton').checked = !!s.on; document.getElementById('txtmon').checked = !!s.monthly;
  document.getElementById('txtfmt').value = s.fmt || 'txt';
  const pth = document.getElementById('txtpath'); pth.value = s.path || ''; pth.placeholder = s.default || '/share/greport/export/greport_tagebuch.txt';
  txtStatus();
  const lk = document.getElementById('txtpro'); lk.hidden = PRO(); lk.textContent = '🔒 ' + t('gr_txt_pro');
  if (PRO()) d.removeAttribute('data-locked'); else d.setAttribute('data-locked', '');
  d.querySelectorAll('.blk').forEach(b => { b.inert = !PRO(); });     // ohne Pro: gesperrt, auch für Tastatur und Screenreader
  expPath(); tipsDraw(d); document.getElementById('impres').hidden = true; document.getElementById('impgo').disabled = true; TXT.content = null;
  document.getElementById('imppath').value = '';
  d.showModal();
}
function txtStatus() {
  const s = TXT.st || {}, el_ = document.getElementById('txtst');
  el_.textContent = (s.moved ? '⚠ ' + t('gr_txt_moved', { o: s.moved, n: s.default || '' }) + ' ' : '') + (s.error ? '⚠ ' + txtErr(s.error) : s.last ? '✓ ' + t('gr_txt_last', { t: fDate(new Date(s.last).getTime()) + ' ' + fTime(new Date(s.last).getTime()), f: (s.files || []).slice(-1)[0] || '' }) : t('gr_txt_roots', { r: (s.roots || ['/share/greport/export', '/media/greport']).join(', ') }));
}
function expPath() {
  const f = document.getElementById('expfmt').value, p = document.getElementById('exppath');
  p.placeholder = '/share/greport/export/greport_export_' + isoDay(new Date()) + '.' + f;
}
function impShow(r) {
  const box = document.getElementById('impres'); box.hidden = false;
  if (!r.ok) { box.textContent = '⚠ ' + txtErr(r.error); document.getElementById('impgo').disabled = true; return; }
  box.innerHTML = r.applied != null ? `✓ ${esc(t('gr_imp_done', { n: r.applied, w: r.words_made || 0 }))}`
    : `${esc(t('gr_imp_found', { n: r.new, d: r.dup, b: r.bad }))}${r.words && r.words.length ? `<br>${esc(t('gr_imp_words', { w: r.words.join(', ') }))}` : ''}${r.sample && r.sample.length ? `<ul>${r.sample.map(x => `<li>${esc(fDate(new Date(x.from).getTime()) + ' ' + fTime(new Date(x.from).getTime()))} – ${esc(x.text || '…')}</li>`).join('')}</ul>` : ''}`;
  document.getElementById('impgo').disabled = r.applied != null || !r.new;
}
function impBody(apply) {
  const p = document.getElementById('imppath').value.trim();
  return TXT.content != null && !p ? { content: TXT.content, apply } : { path: p, apply };
}
function initTxt() {
  document.getElementById('txtsave').onclick = async () => {
    const j = await post('textfile', { on: document.getElementById('txton').checked, monthly: document.getElementById('txtmon').checked, fmt: document.getElementById('txtfmt').value, path: document.getElementById('txtpath').value.trim() }).catch(() => ({ ok: false }));
    if (!j.ok) { document.getElementById('txtst').textContent = '⚠ ' + txtErr(j.error); return; }
    TXT.st = j; txtStatus(); toast('✓ ' + t('gr_txt_saved'));
  };
  document.getElementById('txtnow').onclick = async () => { const j = await post('textfile', { action: 'write' }).catch(() => ({ ok: false })); TXT.st = Object.assign(TXT.st || {}, j); if (!j.ok) TXT.st.error = j.error; txtStatus(); };
  document.getElementById('expfmt').onchange = expPath;
  document.getElementById('expdl').onclick = () => { location.href = 'export?fmt=' + document.getElementById('expfmt').value; };
  document.getElementById('expgo').onclick = async () => {
    const j = await post('export_file', { fmt: document.getElementById('expfmt').value, path: document.getElementById('exppath').value.trim() }).catch(() => ({ ok: false }));
    document.getElementById('expst').textContent = j.ok ? '✓ ' + t('gr_exp_done', { n: j.n, p: j.path }) : '⚠ ' + txtErr(j.error);
  };
  document.getElementById('impfile').onclick = () => document.getElementById('impf').click();
  document.getElementById('impf').onchange = async e => {
    const f = e.target.files[0]; e.target.value = ''; if (!f) return;
    TXT.content = await f.text(); document.getElementById('imppath').value = ''; document.getElementById('imppath').placeholder = '📎 ' + f.name;
    impShow(await post('import', impBody(false)).catch(() => ({ ok: false })));
  };
  document.getElementById('imppath').addEventListener('input', () => { TXT.content = null; document.getElementById('impgo').disabled = true; });
  document.getElementById('impprev').onclick = async () => impShow(await post('import', impBody(false)).catch(() => ({ ok: false })));
  document.getElementById('impgo').onclick = async () => { const r = await post('import', impBody(true)).catch(() => ({ ok: false })); impShow(r); if (r.ok) { ntsLoad(); listLoad(); } };
}
/* ---------- Nachweis: Kette prüfen, Verlauf einer Notiz, Papierkorb ---------- */
const OPS = { start: 'gr_op_start', add: 'gr_op_add', edit: 'gr_op_edit', del: 'gr_op_del', restore: 'gr_op_restore', extern: 'gr_op_extern', extern_del: 'gr_op_extern' };
const fIso = s => { const v = Date.parse(s); return isNaN(v) ? String(s || '–') : fDate(v) + ' ' + fTime(v); };
async function verOpen() {
  const d = document.getElementById('verdlg'), box = document.getElementById('verbox'); box.textContent = '…';
  const [rf, rt] = rangeMs(), q = (rf != null ? '&from=' + rf : '') + (rt != null ? '&to=' + rt : '');     // Bericht für den angezeigten Zeitraum
  document.getElementById('repdl').href = 'bericht?gs=0' + q; document.getElementById('repgs').href = 'bericht?gs=1' + q; tipsDraw(d);
  if (!d.open) d.showModal();
  let v; try { v = await (await fetch('verify', { cache: 'no-store' })).json(); } catch (e) { box.textContent = t('saveerr'); return; }
  const head = v.empty ? t('gr_ver_empty') : v.ok ? t('gr_ver_ok', { t: fIso(v.since) }) : t('gr_ver_bad', { n: v.problems.length });
  box.innerHTML = `<p class="verhead ${v.ok ? 'ok' : 'bad'}">${v.ok ? '✓' : '⚠'} ${esc(head)}</p>
    ${v.problems.length ? `<ul class="verlist">${v.problems.map(p => `<li>${esc(p.what)}</li>`).join('')}</ul>` : ''}
    ${v.warnings.length ? `<p class="hint">${esc(t('gr_ver_warn'))}</p><ul class="verlist">${v.warnings.map(p => `<li>${esc(p.what)}</li>`).join('')}</ul>` : ''}
    <dl class="verdl"><dt>${esc(t('gr_ver_n'))}</dt><dd>${v.n} · ${esc(t('gr_ver_notes', { n: v.notes }))}</dd>
      <dt>${esc(t('gr_ver_first'))}</dt><dd><code>${esc(v.first_hash || '–')}</code></dd><dt>${esc(t('gr_ver_last'))}</dt><dd><code>${esc(v.last_hash || '–')}</code> (${esc(fIso(v.last))})</dd>
      <dt>${esc(t('gr_ver_keyed'))}</dt><dd>${v.keyed} / ${v.n}</dd><dt>${esc(t('gr_ver_files'))}</dt><dd>${esc(t('gr_ver_files_n', { n: v.files || 0, a: v.files_active || 0 }))}</dd><dt>${esc(t('gr_ver_clock'))}</dt><dd>${esc(v.clock)}${v.tz ? ' · ' + esc(v.tz) : ''}</dd></dl>
    <p class="hint">${esc(t('gr_ver_h'))}</p>`;
  trashDraw();
}
async function trashDraw() {
  const box = document.getElementById('trashbox');
  let j; try { j = await (await fetch('trash', { cache: 'no-store' })).json(); } catch (e) { return; }
  const ns = (j.notes || []).slice().reverse();
  box.innerHTML = ns.length ? ns.map(n => `<div class="histrow"><span>${esc(fDate(n.a) + ' ' + (n.notime ? t('gr_notime') : fTime(n.a)))} – ${esc(n.text || (n.tagl || []).join(', '))}<small>${esc(t('gr_deleted_at', { t: fIso(n.deleted) }))}</small></span><button type="button" class="btn" data-r="${esc(n.id)}">${esc(t('gr_restore'))}</button></div>`).join('') : `<p class="hint">${esc(t('gr_trash_empty'))}</p>`;
  box.querySelectorAll('[data-r]').forEach(b => b.onclick = async () => { const r = await post('note', { action: 'restore', id: b.dataset.r }).catch(() => ({})); if (r.ok) { toast('✓ ' + t('gr_restored')); trashDraw(); listLoad(); } });
}
async function histOpen(n) {
  const d = document.getElementById('histdlg'), box = document.getElementById('histbox'); box.textContent = '…'; d.showModal(); tipsDraw(d);
  let j; try { j = await (await fetch('history?id=' + encodeURIComponent(n.id), { cache: 'no-store' })).json(); } catch (e) { box.textContent = t('saveerr'); return; }
  const ver = x => { if (!x) return ''; const p = Object.assign({ a: Date.parse(x.from) || Date.parse(x.at || x.ts) }, x); return `${esc(fDate(p.a) + ' ' + (p.notime ? t('gr_notime') : fTime(p.a)))}${p.to ? ' – ' + esc(fTime(Date.parse(p.to))) : ''} · ${esc(p.text || '')}${(p.tags || []).length ? ' · ' + esc(p.tags.map(ntLabel).join(', ')) : ''}${p.witness ? ' · 👤 ' + esc(p.witness) : ''}`; };
  box.innerHTML = (j.items || []).map(e => {
    const x = e.op === 'start' ? (e.note || null) : e.note;
    return `<div class="histrow"><span><b>${esc(t(OPS[e.op] || 'gr_op_edit'))}</b> · ${esc(fIso(e.iso))}${x ? `<small>${ver(x)}</small>` : ''}${e.prev && e.op !== 'start' ? `<small class="old">${esc(t('gr_hist_before'))}: ${ver(e.prev)}</small>` : ''}</span></div>`;
  }).join('') || `<p class="hint">${esc(t('gr_hist_none'))}</p>`;
}
/* ---------- Kleine Hilfe ---------- */
const HELP = ['now', 'tags', 'req', 'time', 'when', 'more', 'att', 'scan', 'lay', 'list', 'ver', 'doc', 'ha', 'gl', 'txt', 'pro'];
function helpOpen() {
  document.getElementById('helpbody').innerHTML = HELP.map(k => `<details${k === 'now' ? ' open' : ''}><summary>${esc(t('gr_h_' + k))}</summary><p>${esc(t('gr_h_' + k + '_t'))}</p></details>`).join('');
  document.getElementById('helpdlg').showModal();
}
/* ---------- Menü ---------- */
function menu() {
  const m = document.getElementById('grmenul');
  if (!m.hidden) { m.hidden = true; return; }
  const lock = PRO() ? '' : '🔒 Pro';
  const items = [['✎', t('qt_title'), () => qtOpen()], ['🕒', t('gr_prefs'), prefOpen], ['▦', t('gr_lay'), layOpen], ['🔗', t('gr_gl_title'), glOpen], ['🏠', t('gr_dash'), dashOpen], null,
    ['📎', t('gr_att_title'), () => attOpen()], ['⤓', t('gr_backup'), () => { location.href = 'backup'; }], ['✔', t('gr_ver_title'), verOpen],
    ['📄', t('gr_txt_title'), txtOpen, lock],
    ['👤', t('gr_persons'), () => PRO() ? perOpen() : proOpen(), lock], null,
    ['?', t('gr_help'), helpOpen], ['⭐', PRO() ? t('gr_pro_on') : t('gr_pro_get'), proOpen]];
  m.innerHTML = '';
  for (const it of items) {
    if (!it) { m.appendChild(el('hr')); continue; }
    const b = el('button', { type: 'button' }); b.setAttribute('role', 'menuitem');
    b.append(el('span', { textContent: it[0], className: 'mi' }), el('span', { textContent: it[1] })); if (it[3]) b.appendChild(el('span', { className: 'lock', textContent: it[3] }));
    b.onclick = () => { m.hidden = true; it[2](); }; m.appendChild(b);
  }
  m.hidden = false; m.querySelector('button').focus();
  m.onkeydown = e => {                                  // Pfeiltasten im Menü
    const bs = [...m.querySelectorAll('button')], i = bs.indexOf(document.activeElement);
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { e.preventDefault(); bs[(i + (e.key === 'ArrowDown' ? 1 : bs.length - 1)) % bs.length].focus(); }
    else if (e.key === 'Home' || e.key === 'End') { e.preventDefault(); bs[e.key === 'Home' ? 0 : bs.length - 1].focus(); }
    else if (e.key === 'Escape' || e.key === 'Tab') { m.hidden = true; document.getElementById('grmenu').focus(); }
  };
}
/* Dashboard-Vorlage für Home Assistant */
let DASH_ON = false;
function dashOpen() {
  const d = document.getElementById('dashdlg');
  if (!DASH_ON && window.HADash) { DASH_ON = true; HADash.mount(document.getElementById('dashbox'), { lang, get: 'hadash', post: 'hadash_apply', preview: 'hadash',
    parts: { karte: t('hd_karte'), felder: t('hd_felder'), letzte: t('hd_letzte'), heute: t('hd_heute'), oeffnen: t('hd_oeffnen') } }); }
  d.showModal();
}
function proOpen() {
  const p = ST.pro || {};
  document.getElementById('prost').textContent = p.ok ? t('pro_active', { d: p.until || '' }) : p.state === 'expired' ? t('gr_pro_expired', { d: p.until || '' }) : t('gr_pro_none');
  document.getElementById('probuy').href = p.buy || 'https://www.gsimulations.de/greport/#buypro';
  document.getElementById('prodel').hidden = !(p.ok || p.state === 'expired'); document.getElementById('promsg').textContent = '';
  document.getElementById('prodlg').showModal();
}
/* GLighter: Notizen weitergeben (an/aus) */
function glOpen() {
  const g = ST.glighter || {}, on = !(ST.prefs && ST.prefs.gl === false);
  document.getElementById('glshare').checked = on;
  document.getElementById('glst').textContent = !g.found ? t('gr_gl_none') : g.linked ? t('gr_gl_linked') : 'GLighter ' + t('gr_gl_found') + ' – ' + t('gr_gl_found_tip');
  document.getElementById('gldlg').showModal();
}
function perOpen() {                                   // Zeilen „Name; Rolle; Erreichbarkeit“
  const inf = ST.persons_info || {};
  document.getElementById('perlist').value = (ST.persons || []).map(p => { const i = inf[p]; return i && (i.r || i.c) ? [p, i.r ? t('gr_role_' + i.r) : '', i.c || ''].join('; ') : p; }).join('\n');
  document.getElementById('perdlg').showModal();
}
function initDialogs() {
  document.querySelectorAll('dialog .dlgx').forEach(b => b.onclick = () => b.closest('dialog').close());
  document.querySelectorAll('dialog').forEach((d, i) => { const h = d.querySelector('h3'); if (h && !d.hasAttribute('aria-labelledby')) { h.id = h.id || 'dlgh' + i; d.setAttribute('aria-labelledby', h.id); } });
  document.getElementById('prosave').onclick = async () => {
    const k = document.getElementById('prokey').value.trim(); if (!k) return;
    const j = await post('pro', { key: k }).catch(() => ({ ok: false }));
    const m = document.getElementById('promsg'); m.className = 'msg' + (j.ok ? '' : ' err'); m.textContent = j.ok ? '✓ ' + t('gr_pro_ok') : t(j.error === 'offline' ? 'gr_pro_offline' : 'gr_pro_bad');
    if (j.ok) { document.getElementById('prokey').value = ''; await stLoad(); ntsLoad(); setTimeout(() => document.getElementById('prodlg').close(), 900); }
  };
  document.getElementById('prodel').onclick = async () => { if (!confirm(t('pro_remove_q'))) return; await post('pro', { action: 'del' }).catch(() => { }); await stLoad(); proOpen(); };
  document.getElementById('persave').onclick = async () => {
    const lst = document.getElementById('perlist').value.split('\n').map(x => x.trim()).filter(Boolean);
    const j = await post('persons', { list: lst }).catch(() => ({ ok: false }));
    if (j.ok) { ST.persons = j.list; ST.persons_info = j.info || {}; witList(); document.getElementById('perdlg').close(); } else alert(t('saveerr'));
  };
  document.getElementById('pfsave').onclick = async () => {
    const j = await post('prefs', prefRead()).catch(() => ({ ok: false }));
    if (j.ok) { delete j.ok; PF = j; widthApply(); tipModeApply(); tipsDraw(); document.getElementById('prefdlg').close(); fnpShow(); listDraw(); } else alert(t('saveerr'));
  };
  document.getElementById('glsave').onclick = async () => {
    const j = await post('prefs', { gl: document.getElementById('glshare').checked }).catch(() => ({ ok: false }));
    if (j.ok) { ST.prefs = Object.assign(ST.prefs || {}, { gl: j.gl }); PF = Object.assign(PF || {}, { gl: j.gl }); stShow(); document.getElementById('gldlg').close(); toast(t(j.gl ? 'gr_gl_on_ok' : 'gr_gl_off_ok')); } else alert(t('saveerr'));
  };
  document.getElementById('grimpf').onchange = async e => {
    const f = e.target.files[0]; e.target.value = ''; if (!f) return;
    try { const j = await (await fetch('import', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: await f.text() })).json(); toast(j.ok ? t('gr_imported_n', { n: j.n }) : t('gr_import_bad')); listLoad(); } catch (x) { toast(t('gr_import_bad')); }
  };
  document.getElementById('veragain').onclick = verOpen;
  initQt(); initTxt();
}
/* ---------- Layout anpassen: direkt auf dem Erfassen-Bildschirm (Ziehen mit Maus/Finger oder Pfeiltasten) ----------
   Änderungen sammeln sich in einem Entwurf; „Fertig“ schickt sie in einem Rutsch (notetags: batch) und die
   Überschrift/Reihenfolge der Bereiche an die Einstellungen. „Abbrechen“ verwirft alles. */
const LAY = { on: false, d: null, focus: null };
const SEC_EL = { txt: 'fnptext', tags: 'fnptags', wit: 'secwit', more: 'secmore', time: 'sectime' };
const SEC_L = { txt: 'fnp_p_txt', tags: 'fnp_p_tags', wit: 'fnp_p_wit', more: 'gr_more_p', time: 'gr_p_ext' };
function capOrder() { const o = (PF.cap_order || []).filter(x => SEC_EL[x]); return o.concat(Object.keys(SEC_EL).filter(x => !o.includes(x))); }
function secApply(order) {
  const body = $('fnpbody'); if (!body) return;
  for (const k of order || capOrder()) { const e = $(SEC_EL[k]); if (e) body.appendChild(e); }
}
const hex6 = () => Array.from(crypto.getRandomValues(new Uint8Array(3)), b => b.toString(16).padStart(2, '0')).join('');
const layFlat = gs => gs.filter(g => !g.del).flatMap(g => g.keys);
function layBuild() {
  const groups = gIds().map(g => {
    const gi = gInfo(g) || {}, col = (NTS.gcol || {})[g] || '';
    return { g, l: gLabel(g), l0: gLabel(g), custom: gCustom(g), hide: !!gi.hide, hide0: !!gi.hide, col, col0: col, isNew: false, del: false,
      keys: g === 'when' ? whenOrdered() : ntOrdered(ntAll().filter(k => ntGroup(k) === g)) };
  });
  const keys = {};
  for (const gr of groups) for (const k of gr.keys) {
    const w = WHEN.get(k);
    keys[k] = { k, l: ntLabel(k), l0: ntLabel(k), kind: w ? 'when' : 'tag', own: w ? !!w.own : NTS.own[k] != null, hide: w ? !!w.hide : NTS.hide.has(k), hide0: w ? !!w.hide : NTS.hide.has(k), g0: gr.g, isNew: false, del: false };
  }
  const secs = capOrder();
  LAY.d = { groups, keys, order0: layFlat(groups).join(), gorder0: groups.map(g => g.g).join(), secs, secs0: secs.join(), title: PF.cap_title || '', sub: PF.cap_sub || '', width: PF.width || 'wide', width0: PF.width || 'wide' };
}
function laySay(msg) { const e = $('laylive'); if (e) { e.textContent = ''; setTimeout(() => { e.textContent = msg; }, 30); } }
function layOpen() {
  if (LAY.on) return;
  LAY.on = true; layBuild();
  const pn = $('fnpanel'); pn.classList.add('lay'); $('laybtn').setAttribute('aria-pressed', 'true');
  const ce = 'plaintext-only';
  for (const [id, key, def] of [['capttl', 'title', t('fn_btn')], ['fnpfrom', 'sub', t(matchMedia('(pointer:coarse)').matches ? 'gr_wait_m' : 'gr_wait')]]) {
    const e = $(id); e.textContent = LAY.d[key] || def; try { e.contentEditable = ce; } catch (x) { e.contentEditable = 'true'; }
    if (e.contentEditable !== ce) e.contentEditable = 'true';
    e.setAttribute('role', 'textbox'); e.setAttribute('aria-label', t(id === 'capttl' ? 'gr_lay_title' : 'gr_lay_sub')); e.tabIndex = 0; e.dataset.def = def;
    e.onkeydown = ev => { if (ev.key === 'Enter') { ev.preventDefault(); e.blur(); } };
  }
  layBar(); fnpTags(); $('laybar').querySelector('.laysec').focus();
}
function layClose() {
  LAY.on = false; LAY.d = null; widthApply();   // Abbrechen: gespeicherte Breite
  for (const id of ['capttl', 'fnpfrom']) { const e = $(id); e.removeAttribute('contenteditable'); e.removeAttribute('role'); e.removeAttribute('aria-label'); e.removeAttribute('tabindex'); e.onkeydown = null; }
  const pn = $('fnpanel'); pn.classList.remove('lay'); $('laybtn').setAttribute('aria-pressed', 'false'); $('laybar').hidden = true; $('laybar').innerHTML = '';
  secApply(); secDraw(); fnpTags(); fnpShow(); $('laybtn').focus();
}
function layBar() {
  const bar = $('laybar'), d = LAY.d; bar.hidden = false;
  bar.innerHTML = `<p class="layhint">${esc(t('gr_lay_hint'))}</p>
    <div class="laysecs"><span class="laysl" id="laysl">${esc(t('gr_lay_secs'))}</span><div class="laysbox" role="group" aria-labelledby="laysl">${d.secs.map((k, i) => `<button type="button" class="laysec" data-sec="${k}" data-drag="sec" aria-label="${esc(t('gr_lay_sec_a', { s: t(SEC_L[k]), i: i + 1, n: d.secs.length }))}"><span aria-hidden="true">⠿</span> ${esc(t(SEC_L[k]))}</button>`).join('')}</div></div>
    <div class="laywid"><span class="laysl" id="laywl">${esc(t('gr_p_width'))}</span><div class="seg" role="group" aria-labelledby="laywl">${['wide', 'narrow'].map(w => `<button type="button" class="laywb${d.width === w ? ' on' : ''}" data-w="${w}" aria-pressed="${d.width === w}">${esc(t(w === 'wide' ? 'gr_p_wide' : 'gr_p_narrow'))}</button>`).join('')}</div></div>
    <div class="laybtns"><button type="button" class="btn" id="layreset">${esc(t('gr_reset'))}</button><span class="grow"></span><button type="button" class="btn" id="laycancel">${esc(t('cancel'))}</button><button type="button" class="btn primary" id="laydone">${esc(t('gr_lay_done'))}</button></div>
    <span class="sr" id="laylive" aria-live="polite"></span>`;
  bar.querySelectorAll('.laysec').forEach(b => b.onkeydown = e => {
    const i = d.secs.indexOf(b.dataset.sec), j = e.key === 'ArrowLeft' || e.key === 'ArrowUp' ? i - 1 : e.key === 'ArrowRight' || e.key === 'ArrowDown' ? i + 1 : -2;
    if (j === -2) return; e.preventDefault(); if (j < 0 || j >= d.secs.length) return;
    d.secs.splice(j, 0, d.secs.splice(i, 1)[0]); secApply(d.secs); layBar(); bar.querySelector(`.laysec[data-sec="${b.dataset.sec}"]`).focus();
    laySay(t('gr_lay_moved', { s: t(SEC_L[b.dataset.sec]), i: j + 1, n: d.secs.length }));
  });
  bar.querySelectorAll('.laywb').forEach(b => b.onclick = () => { d.width = b.dataset.w; widthApply(d.width); layBar(); bar.querySelector(`.laywb[data-w="${d.width}"]`).focus(); });   // Vorschau sofort
  $('layreset').onclick = layReset; $('laycancel').onclick = layClose; $('laydone').onclick = laySave;
}
function layFind(k) { return LAY.d.groups.find(g => g.keys.includes(k)); }
function layDraw() {
  const box = $('fnptags'), d = LAY.d; if (!box || !d) return;
  const cnt = d.groups.filter(g => !g.del).length;
  let h = '<div class="laygs">';
  d.groups.filter(g => !g.del).forEach((gr, gi) => {
    const kind = gr.g === 'when' ? 'when' : 'tag', col = gr.col || gColor(gr.g) || G_DEF[gr.g] || '#5f6b78';
    h += `<div class="layg${gr.hide ? ' off' : ''}" data-g="${esc(gr.g)}" style="--gc:${esc(col)}">
      <div class="laygh"><button type="button" class="hd" data-drag="grp" aria-label="${esc(t('gr_lay_grp_a', { g: gr.l, i: gi + 1, n: cnt }))}" title="${esc(t('gr_drag'))}">⠿</button>
        <input type="text" class="lgn" maxlength="30" value="${esc(gr.l)}" aria-label="${esc(t('gr_lay_gname'))}">
        <input type="color" class="lgc" value="${esc(/^#[0-9a-f]{6}$/i.test(col) ? col : '#5f6b78')}" aria-label="${esc(t('gr_gcol', { g: gr.l }))}" title="${esc(t('gr_gcol', { g: gr.l }))}">
        <label class="check"><input type="checkbox" class="lgh"${gr.hide ? '' : ' checked'}> ${esc(t('gr_shown'))}</label>
        ${gr.custom ? `<button type="button" class="lgd" aria-label="${esc(t('gr_lay_gdel', { g: gr.l }))}" title="${esc(t('gr_lay_gdel', { g: gr.l }))}">🗑</button>` : ''}</div>
      <div class="laykeys" data-kind="${kind}">${gr.keys.map(k => d.keys[k]).filter(x => x && !x.del).map(x => `<span class="layk tag ${gAttr(kind === 'when' ? 'when' : gr.g).replace('"', x.hide ? ' off"' : '"')} data-k="${esc(x.k)}"><button type="button" class="lkn" data-drag="key" aria-label="${esc(t('gr_lay_key_a', { k: x.l, g: gr.l }) + (x.hide ? ', ' + t('gr_lay_hidden') : ''))}">${esc(x.l)}</button><button type="button" class="lkx" aria-label="${esc(t(x.own ? 'gr_lay_kdel' : x.hide ? 'gr_lay_kshow' : 'gr_lay_khide', { k: x.l }))}" title="${esc(t(x.own ? 'gr_lay_kdel' : x.hide ? 'gr_lay_kshow' : 'gr_lay_khide', { k: x.l }))}">${x.own ? '✕' : x.hide ? '○' : '●'}</button></span>`).join('')}<button type="button" class="tag add lka">＋ ${esc(t(kind === 'when' ? 'gr_lay_wadd' : 'gr_lay_kadd'))}</button></div>
    </div>`;
  });
  h += `<button type="button" class="btn lga">＋ ${esc(t('gr_lay_gadd'))}</button></div>`;
  box.innerHTML = h;
  box.querySelectorAll('.layg').forEach(row => {
    const gr = d.groups.find(g => g.g === row.dataset.g);
    row.querySelector('.lgn').onchange = e => { const v = e.target.value.trim(); if (v) gr.l = v; else e.target.value = gr.l; };
    row.querySelector('.lgc').oninput = e => { gr.col = e.target.value; row.style.setProperty('--gc', gr.col); };
    row.querySelector('.lgh').onchange = e => { gr.hide = !e.target.checked; row.classList.toggle('off', gr.hide); };
    const del = row.querySelector('.lgd'); if (del) del.onclick = () => {
      if (!confirm(t('gr_lay_gdel_q', { g: gr.l }))) return;
      const own = d.groups.find(g => g.g === 'own'); own.keys.push(...gr.keys); gr.keys = []; gr.del = true; layDraw(); laySay(t('gr_lay_gdeleted', { g: gr.l }));
    };
    row.querySelector('.hd').onkeydown = e => layMoveGroup(e, gr);
    row.querySelector('.lka').onclick = () => layAddKey(row, gr);
  });
  box.querySelectorAll('.layk').forEach(chip => {
    const k = chip.dataset.k, x = d.keys[k];
    const nb = chip.querySelector('.lkn');
    nb.onclick = () => { if (!LAY.dragged) layRename(chip, x); };
    nb.onkeydown = e => { if (e.key === 'Delete' || e.key === 'Backspace') { e.preventDefault(); layKeyX(x); } else layMoveKey(e, x); };
    chip.querySelector('.lkx').onclick = () => layKeyX(x);
  });
  box.querySelector('.lga').onclick = () => {
    const l = prompt(t('gr_lay_gname')); if (!l || !l.trim()) return;
    const g = 'g_' + hex6(); d.groups.splice(d.groups.findIndex(x => x.g === 'own'), 0, { g, l: l.trim().slice(0, 30), l0: '', custom: true, hide: false, hide0: false, col: '', col0: '', isNew: true, del: false, keys: [] });
    LAY.focus = `.layg[data-g="${g}"] .lgn`; layDraw();
  };
  if (LAY.focus) { const f = box.querySelector(LAY.focus); LAY.focus = null; if (f) f.focus(); }
}
function layKeyX(x) {                                  // eigene Taste löschen, eingebaute ein-/ausblenden
  const d = LAY.d;
  if (x.own) { if (!confirm(t('qt_del_q', { n: x.l }))) return; x.del = true; const g = layFind(x.k); if (g) g.keys = g.keys.filter(k => k !== x.k); laySay(t('gr_lay_kdeleted', { k: x.l })); }
  else { x.hide = !x.hide; LAY.focus = `.layk[data-k="${x.k}"] .lkx`; laySay(t(x.hide ? 'gr_lay_khidden' : 'gr_lay_kshown', { k: x.l })); }
  layDraw();
}
function layRename(chip, x) {
  const nb = chip.querySelector('.lkn'), inp = el('input', { type: 'text', className: 'lkin', value: x.l, maxLength: 30 });
  inp.setAttribute('aria-label', t('qt_ren')); nb.replaceWith(inp); inp.focus(); inp.select();
  let done = false;
  const fin = ok => { if (done) return; done = true; const v = inp.value.trim(); if (ok && v) x.l = v; LAY.focus = `.layk[data-k="${x.k}"] .lkn`; layDraw(); };
  inp.onkeydown = e => { if (e.key === 'Enter') { e.preventDefault(); fin(true); } else if (e.key === 'Escape') { e.preventDefault(); fin(false); } };
  inp.onblur = () => fin(true);
}
function layAddKey(row, gr) {
  const keysBox = row.querySelector('.laykeys'), add = keysBox.querySelector('.lka'), when = gr.g === 'when';
  const f = el('span', { className: 'lkform' });
  f.innerHTML = `<input type="text" class="lkin" maxlength="30" aria-label="${esc(t('gr_lay_kname'))}" placeholder="${esc(t('gr_lay_kname'))}">${when ? `<input type="text" class="lkin lkt" maxlength="5" aria-label="${esc(t('gr_lay_wspec'))}" placeholder="${esc(t('gr_lay_wspec_ph'))}">` : ''}<button type="button" class="chip">${esc(t('qt_create'))}</button>`;
  add.replaceWith(f); const [n, sp] = f.querySelectorAll('input'); n.focus();
  const go = () => {
    const l = n.value.trim(); if (!l) { layDraw(); return; }
    const k = (when ? 't_' : 'c_') + hex6(), x = { k, l, l0: l, kind: when ? 'when' : 'tag', own: true, hide: false, g0: gr.g, isNew: true, del: false };
    if (when) { const v = (sp.value || '').trim(); if (/^\d{1,2}:\d\d$/.test(v)) x.at = v; else if (/^\d+$/.test(v)) x.m = +v; else { sp.focus(); sp.setAttribute('aria-invalid', 'true'); toast(t('gr_lay_wspec_bad')); return; } }
    LAY.d.keys[k] = x; gr.keys.push(k); LAY.focus = `.layg[data-g="${gr.g}"] .lka`; layDraw(); laySay(t('gr_lay_kadded', { k: l }));
  };
  f.querySelector('button').onclick = go;
  f.querySelectorAll('input').forEach(i => i.onkeydown = e => { if (e.key === 'Enter') { e.preventDefault(); go(); } else if (e.key === 'Escape') { e.preventDefault(); layDraw(); } });
}
function layMoveKey(e, x) {                            // ←/→ innerhalb der Rubrik, ↑/↓ in die vorige/nächste Rubrik (gleiche Art)
  const d = LAY.d, gr = layFind(x.k); if (!gr) return;
  const vis = gr.keys.filter(k => !d.keys[k].del), i = vis.indexOf(x.k);
  if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
    e.preventDefault(); const j = i + (e.key === 'ArrowLeft' ? -1 : 1); if (j < 0 || j >= vis.length) return;
    const a = gr.keys.indexOf(x.k), b = gr.keys.indexOf(vis[j]); [gr.keys[a], gr.keys[b]] = [gr.keys[b], gr.keys[a]];
    laySay(t('gr_lay_moved', { s: x.l, i: j + 1, n: vis.length }));
  } else if (e.key === 'ArrowUp' || e.key === 'ArrowDown') {
    e.preventDefault(); if (x.kind === 'when') return;
    const gs = d.groups.filter(g => !g.del && g.g !== 'when'), gi = gs.indexOf(gr), ng = gs[gi + (e.key === 'ArrowUp' ? -1 : 1)]; if (!ng) return;
    gr.keys = gr.keys.filter(k => k !== x.k); ng.keys.splice(Math.min(i, ng.keys.length), 0, x.k);
    laySay(t('gr_lay_moved_g', { k: x.l, g: ng.l }));
  } else return;
  LAY.focus = `.layk[data-k="${x.k}"] .lkn`; layDraw();
}
function layMoveGroup(e, gr) {
  if (e.key !== 'ArrowUp' && e.key !== 'ArrowDown') return; e.preventDefault();
  const gs = LAY.d.groups, i = gs.indexOf(gr); let j = i;
  do { j += e.key === 'ArrowUp' ? -1 : 1; } while (gs[j] && gs[j].del);
  if (j < 0 || j >= gs.length) return;
  gs.splice(i, 1); gs.splice(j, 0, gr);
  const vis = gs.filter(g => !g.del); laySay(t('gr_lay_moved', { s: gr.l, i: vis.indexOf(gr) + 1, n: vis.length }));
  LAY.focus = `.layg[data-g="${gr.g}"] .hd`; layDraw();
}
function layFromDom() {                                // nach dem Ziehen: Reihenfolge aus dem Bildschirm übernehmen
  const d = LAY.d, box = $('fnptags');
  const order = [...box.querySelectorAll('.layg')].map(r => r.dataset.g);
  d.groups.sort((a, b) => (order.indexOf(a.g) < 0 ? 1e6 : order.indexOf(a.g)) - (order.indexOf(b.g) < 0 ? 1e6 : order.indexOf(b.g)));
  for (const r of box.querySelectorAll('.layg')) {
    const gr = d.groups.find(g => g.g === r.dataset.g), seen = [...r.querySelectorAll('.layk')].map(c => c.dataset.k);
    gr.keys = seen.concat(gr.keys.filter(k => d.keys[k].del && !seen.includes(k)));
  }
  const bs = [...$('laybar').querySelectorAll('.laysec')].map(b => b.dataset.sec); if (bs.length) d.secs = bs;
}
function layPointer(e) {                               // Ziehen mit Maus, Stift oder Finger
  if (!LAY.on || e.button !== 0) return;
  const h = e.target.closest('[data-drag]'); if (!h) return;
  const kind = h.dataset.drag, item = kind === 'key' ? h.closest('.layk') : kind === 'grp' ? h.closest('.layg') : h;
  const x0 = e.clientX, y0 = e.clientY; let on = false;
  const move = ev => {
    if (!on) { if (Math.hypot(ev.clientX - x0, ev.clientY - y0) < 6) return; on = true; item.classList.add('dragging'); }
    ev.preventDefault();
    const u = document.elementFromPoint(ev.clientX, ev.clientY); if (!u) return;
    if (kind === 'key') {
      const box = u.closest('.laykeys'); if (!box || box.dataset.kind !== item.parentNode.dataset.kind) return;
      const tg = u.closest('.layk');
      if (tg && tg !== item) { const r = tg.getBoundingClientRect(); box.insertBefore(item, ev.clientX > r.left + r.width / 2 ? tg.nextSibling : tg); }
      else if (!tg && item.parentNode !== box) box.insertBefore(item, box.querySelector('.lka, .lkform'));
    } else if (kind === 'grp') {
      const tg = u.closest('.layg'); if (tg && tg !== item) { const r = tg.getBoundingClientRect(); tg.parentNode.insertBefore(item, ev.clientY > r.top + r.height / 2 ? tg.nextSibling : tg); }
    } else {
      const tg = u.closest('.laysec'); if (tg && tg !== item) { const r = tg.getBoundingClientRect(); tg.parentNode.insertBefore(item, ev.clientX > r.left + r.width / 2 ? tg.nextSibling : tg); }
    }
  };
  const end = () => {
    removeEventListener('pointermove', move); removeEventListener('pointerup', end); removeEventListener('pointercancel', end);
    if (!on) return;
    item.classList.remove('dragging'); layFromDom(); LAY.dragged = true; setTimeout(() => { LAY.dragged = false; }, 0);
    if (kind === 'sec') { secApply(LAY.d.secs); layBar(); } else layDraw();
  };
  addEventListener('pointermove', move, { passive: false }); addEventListener('pointerup', end); addEventListener('pointercancel', end);
}
async function laySave() {
  const d = LAY.d, ops = [];
  layFromDom();
  const where = {}; for (const gr of d.groups) for (const k of gr.keys) where[k] = gr.g;
  for (const gr of d.groups) if (gr.isNew && !gr.del) ops.push({ action: 'gadd', g: gr.g, l: gr.l });
  for (const x of Object.values(d.keys)) {
    if (x.isNew) { if (x.del) continue; ops.push(x.kind === 'when' ? Object.assign({ action: 'wadd', k: x.k, l: x.l }, x.at ? { at: x.at } : { m: x.m || 0 }) : { action: 'add', k: x.k, l: x.l, g: where[x.k] }); continue; }
    if (x.del) { ops.push({ action: 'del', k: x.k }); continue; }
    if (x.l !== x.l0) ops.push({ action: 'ren', k: x.k, l: x.l });
    if (x.hide !== x.hide0 && !x.own) ops.push({ action: 'hide', k: x.k, on: x.hide });
    if (x.kind === 'tag' && where[x.k] && where[x.k] !== x.g0) ops.push({ action: 'grp', k: x.k, g: where[x.k] });
  }
  for (const gr of d.groups) {
    if (gr.isNew) { if (!gr.del && gr.hide) ops.push({ action: 'ghide', g: gr.g, on: true }); if (!gr.del && gr.col) ops.push({ action: 'gcol', g: gr.g, c: gr.col }); continue; }
    if (gr.del) { ops.push({ action: 'gdel', g: gr.g }); continue; }
    if (gr.l !== gr.l0) ops.push({ action: 'gren', g: gr.g, l: gr.l });
    if (gr.hide !== gr.hide0) ops.push({ action: 'ghide', g: gr.g, on: gr.hide });
    if (gr.col !== gr.col0) ops.push({ action: 'gcol', g: gr.g, c: gr.col });
  }
  if (layFlat(d.groups).filter(k => !d.keys[k].del).join() !== d.order0.split(',').filter(k => d.keys[k] && !d.keys[k].del).join()) ops.push({ action: 'order', keys: layFlat(d.groups).filter(k => !d.keys[k].del) });
  const gs = d.groups.filter(g => !g.del).map(g => g.g); if (gs.join() !== d.gorder0) ops.push({ action: 'gorder', groups: gs });
  const tt = $('capttl').textContent.trim(), ts = $('fnpfrom').textContent.trim();
  const pf = { cap_title: tt === $('capttl').dataset.def ? '' : tt.slice(0, 60), cap_sub: ts === $('fnpfrom').dataset.def ? '' : ts.slice(0, 160) };
  if (d.secs.join() !== d.secs0) pf.cap_order = d.secs;
  if (d.width !== d.width0) pf.width = d.width;
  try {
    if (ops.length) {
      const j = await post('notetags', { action: 'batch', ops });
      if (j.ok) ntsApply(j);
      if (j.errors && j.errors.length) toast(t('gr_lay_errs', { n: j.errors.length }) + (j.errors.some(x => x.error === 'limit_free') ? ' ' + t('gr_qt_limit_free', { n: NTS.max }) : ''), 6000);
    }
    if (pf.cap_title !== (PF.cap_title || '') || pf.cap_sub !== (PF.cap_sub || '') || pf.cap_order || pf.width) {
      const j = await post('prefs', pf); if (j.ok) { delete j.ok; PF = j; }
    }
    toast('✓ ' + t('gr_lay_saved'));
  } catch (x) { toast(t('saveerr')); return; }
  layClose(); listDraw();
}
async function layReset() {
  if (!confirm(t('gr_lay_reset_q'))) return;
  try {
    const j = await post('notetags', { action: 'reset' }); if (j.ok) ntsApply(j);
    const p = await post('prefs', { cap_title: '', cap_sub: '', cap_order: [], width: 'wide' }); if (p.ok) { delete p.ok; PF = p; }
  } catch (x) { toast(t('saveerr')); return; }
  secApply(); layBuild(); widthApply();
  for (const [id, def] of [['capttl', $('capttl').dataset.def], ['fnpfrom', $('fnpfrom').dataset.def]]) $(id).textContent = def;
  layBar(); layDraw(); laySay(t('gr_lay_reset_done'));
}
function initLay() {
  $('laybtn').onclick = () => LAY.on ? layClose() : layOpen();
  $('fnpanel').addEventListener('pointerdown', layPointer);
  secApply();
}
/* ---------- Anlagen (frei): an Notizen hängen, ansehen, herunterladen; Papierkorb statt Löschen ---------- */
const ATT = { pend: [], st: null, note: null };
const ATT_KINDS = ['pdf', 'txt', 'text', 'log', 'jpg', 'jpeg', 'png', 'heic', 'heif', 'docx', 'odt', 'eml'];
const fSize = n => n >= 1048576 ? (n / 1048576).toFixed(1).replace('.', lang === 'de' ? ',' : '.') + ' MB' : Math.max(1, Math.round((n || 0) / 1024)) + ' KB';
const attIcon = k => ({ pdf: '📄', jpg: '🖼', png: '🖼', heic: '🖼', txt: '📝', eml: '✉', docx: '📃', odt: '📃' }[k] || '📎');
const attExt = n => (String(n || '').split('.').pop() || '').toLowerCase();
function attErr(r, name) {
  const e = (r && r.error) || 'x', m = fSize((r && r.max) || ((ST.att || {}).max_file) || 0);
  return t({ kind: 'gr_att_err_kind', 'too big': 'gr_att_err_big', full: 'gr_att_err_full', type: 'gr_att_err_type' }[e] || 'gr_att_err_x', { n: name, m });
}
function attPick(files) {                               // im Erfassen-Bereich vormerken, hochgeladen wird beim Speichern
  const max = (ST.att || {}).max_file || 25 * 1048576;
  for (const f of files) {
    if (!ATT_KINDS.includes(attExt(f.name))) { toast(attErr({ error: 'kind' }, f.name), 6000); continue; }
    if (f.size > max) { toast(attErr({ error: 'too big', max }, f.name), 6000); continue; }
    ATT.pend.push({ f, desc: '' });
  }
  fnpStart(); attPendDraw();
}
function attPendDraw() {
  const box = $('fnpatts'); if (!box) return;
  const cur = (FNP.edit && FNP.edit.att) || [];
  box.hidden = !ATT.pend.length && !cur.length;
  box.innerHTML = cur.map(a => `<div class="attp"><button type="button" class="linkbtn" data-v="${esc(a.id)}">${attIcon(a.kind)} ${esc(a.name)}</button><small>${esc(fSize(a.size))}</small><span class="grow"></span><button type="button" class="icon sm" data-x="${esc(a.id)}" aria-label="${esc(t('gr_att_rm', { n: a.name }))}" title="${esc(t('gr_att_rm', { n: a.name }))}">🗑</button></div>`).join('')
    + ATT.pend.map((p, i) => `<div class="attp pend"><span>${attIcon(attExt(p.f.name).replace('jpeg', 'jpg'))} ${esc(p.f.name)}</span><small>${esc(fSize(p.f.size))} · ${esc(t('gr_att_pend'))}</small><input type="text" maxlength="300" data-d="${i}" value="${esc(p.desc)}" placeholder="${esc(t('gr_att_desc_ph'))}" aria-label="${esc(t('gr_att_desc') + ': ' + p.f.name)}"><button type="button" class="icon sm" data-r="${i}" aria-label="${esc(t('gr_att_x'))}" title="${esc(t('gr_att_x'))}">✕</button></div>`).join('');
  box.querySelectorAll('[data-d]').forEach(x => x.oninput = () => { ATT.pend[+x.dataset.d].desc = x.value; });
  box.querySelectorAll('[data-r]').forEach(x => x.onclick = () => { ATT.pend.splice(+x.dataset.r, 1); attPendDraw(); });
  box.querySelectorAll('[data-v]').forEach(x => x.onclick = () => { const a = cur.find(y => y.id === x.dataset.v); if (a) prevOpen(a); });
  box.querySelectorAll('[data-x]').forEach(x => x.onclick = async () => {
    const a = cur.find(y => y.id === x.dataset.x); if (!a || !confirm(t('gr_att_del_q', { n: a.name }))) return;
    const r = await post('file', { action: 'del', id: a.id }).catch(() => ({}));
    if (r.ok) { FNP.edit.att = cur.filter(y => y.id !== a.id); attPendDraw(); listLoad(); }
  });
}
async function attUpload(f, desc, notes) {
  const u = 'upload?name=' + encodeURIComponent(f.name) + '&desc=' + encodeURIComponent(desc || '') + '&note=' + encodeURIComponent((notes || []).join(',')) + '&mtime=' + (f.lastModified || '');
  try { return await (await fetch(u, { method: 'POST', body: f })).json(); } catch (e) { return { ok: false, error: 'x' }; }
}
async function attUploadAll(items, notes, msgEl) {      // nacheinander hochladen, Fehler je Datei melden
  let ok = 0;
  for (const p of items) {
    if (msgEl) { msgEl.className = 'msg'; msgEl.textContent = t('gr_att_upl', { n: p.f.name }); }
    const r = await attUpload(p.f, p.desc, notes);
    if (r.ok) ok++; else toast(attErr(r, p.f.name), 7000);
  }
  return ok;
}
async function attOpen(noteId) {
  ATT.note = noteId || null;
  const d = document.getElementById('attdlg'); if (!d.open) d.showModal();
  await attLoad();
}
async function attLoad() {
  try { ATT.st = await (await fetch('files', { cache: 'no-store' })).json(); } catch (e) { ATT.st = { files: [], trash: [] }; }
  attDraw();
}
function attNotesTxt(a) { const n = (a.notes || []).length; return n === 0 ? t('gr_att_n0') : n === 1 ? t('gr_att_n1') : t('gr_att_nn', { n }); }
function attRow(a, trash) {
  const info = t('gr_att_info', { s: fSize(a.size), t: fIso(a.up), n: attNotesTxt(a) }) + (a.txt ? ' · ' + t('gr_att_txt') : '');
  return `<div class="histrow attrow" data-id="${esc(a.id)}"><span class="grow"><b>${attIcon(a.kind)} ${esc(a.name)}</b><small>${esc(info)}</small><small class="hash">${esc(t('gr_att_hash', { h: a.sha256 }))}</small>
    ${trash ? `<small>${esc(t('gr_deleted_at', { t: fIso(a.del) }))}</small>` : `<input type="text" class="attdesc" maxlength="300" value="${esc(a.desc || '')}" placeholder="${esc(t('gr_att_desc_ph'))}" aria-label="${esc(t('gr_att_desc') + ': ' + a.name)}">`}</span>
    <span class="attacts">${trash ? `<button type="button" class="btn" data-a="restore">${esc(t('gr_restore'))}</button>` : `<button type="button" class="btn" data-a="view">${esc(t('gr_att_view'))}</button><button type="button" class="btn" data-a="scan">${esc(t('gr_att_scan'))}</button><button type="button" class="icon sm" data-a="del" aria-label="${esc(t('gr_att_del') + ': ' + a.name)}" title="${esc(t('gr_att_del'))}">🗑</button>`}</span></div>`;
}
function attDraw() {
  const s = ATT.st || {}, n = ATT.note, note = n ? LST.all.find(x => x.id === n) : null;
  const fs = (s.files || []).filter(a => !n || (a.notes || []).includes(n));
  document.getElementById('attuse').textContent = t('gr_att_use', { u: fSize(s.used || 0), m: fSize(s.max_total || 0) });
  const fo = document.getElementById('attfor'); fo.hidden = !n;
  fo.innerHTML = n ? `${esc(t('gr_att_for', { t: note ? fDate(note.a) + (note.notime ? '' : ' ' + fTime(note.a)) : '–' }))} <button type="button" class="linkbtn" id="attallb">${esc(t('gr_att_all'))}</button>` : '';
  const ab = document.getElementById('attallb'); if (ab) ab.onclick = () => { ATT.note = null; attDraw(); };
  const box = document.getElementById('attlist');
  box.innerHTML = fs.length ? fs.map(a => attRow(a)).join('') : `<p class="hint">${esc(t('gr_att_none'))}</p>`;
  const tr = document.getElementById('atttrash'), tl = s.trash || [];
  tr.innerHTML = tl.length ? tl.map(a => attRow(a, true)).join('') : `<p class="hint">${esc(t('gr_att_trash_empty'))}</p>`;
  const tl_ = s.tools || {}, hint = [];
  if (!tl_.pdftotext) hint.push(t('gr_att_nopdf'));
  if (!tl_.tesseract) hint.push(t('gr_att_noocr')); else hint.push(t('gr_att_ocr_ok', { l: (tl_.langs || []).join(', ') || '–' }));
  document.getElementById('atttools').textContent = hint.join(' ');
  for (const root of [box, tr]) root.querySelectorAll('.attrow').forEach(r => {
    const a = (s.files || []).concat(s.trash || []).find(x => x.id === r.dataset.id); if (!a) return;
    const de = r.querySelector('.attdesc'); if (de) de.onchange = () => post('file', { action: 'desc', id: a.id, desc: de.value }).then(j => { if (j.ok) a.desc = j.file.desc; });
    r.querySelectorAll('[data-a]').forEach(b => b.onclick = async () => {
      const act = b.dataset.a;
      if (act === 'view') return prevOpen(a);
      if (act === 'scan') return docOpen(a);
      if (act === 'del' && !confirm(t('gr_att_del_q', { n: a.name }))) return;
      const j = await post('file', { action: act, id: a.id }).catch(() => ({}));
      if (j.ok) { await attLoad(); listLoad(); }
    });
  });
}
function prevOpen(a) {
  const d = document.getElementById('prevdlg'), box = document.getElementById('prevbox'), u = 'file?id=' + encodeURIComponent(a.id);
  document.getElementById('prevttl').textContent = a.name;
  box.innerHTML = a.kind === 'jpg' || a.kind === 'png' ? `<img src="${u}&inline=1" alt="${esc(a.desc || a.name)}">`
    : a.kind === 'pdf' || a.kind === 'txt' || a.kind === 'eml' ? `<iframe src="${u}&inline=1" title="${esc(a.name)}"></iframe>` : `<p class="hint">${esc(t('gr_att_noprev'))}</p>`;
  document.getElementById('previnfo').textContent = [fSize(a.size), a.desc || '', t('gr_att_hash', { h: a.sha256 || '' })].filter(Boolean).join(' · ');
  const dl = document.getElementById('prevdl'); dl.href = u; dl.setAttribute('download', a.name);
  const tx = document.getElementById('prevtxt'); tx.hidden = !a.txt; tx.href = u + '&txt=1';
  if (!d.open) d.showModal();
}
function initAtt() {
  const coarse = matchMedia('(pointer:coarse)').matches;
  $('fnpatt').onclick = () => document.getElementById('attf').click();
  $('fnpcam').hidden = !coarse; $('fnpcam').onclick = () => { ATT.camFor = 'fnp'; document.getElementById('attcam').click(); };
  document.getElementById('attupcam').hidden = !coarse;
  document.getElementById('attupcam').onclick = () => { ATT.camFor = 'dlg'; document.getElementById('attcam').click(); };
  document.getElementById('attup').onclick = () => { ATT.upDlg = true; document.getElementById('attf').click(); };
  const take = async (files, toDlg) => {
    if (!toDlg) { attPick(files); return; }
    const m = document.getElementById('attmsg'), n = await attUploadAll(files.map(f => ({ f, desc: '' })), ATT.note ? [ATT.note] : [], m);
    m.textContent = n ? '✓ ' + t('gr_att_upok', { n }) : ''; await attLoad(); listLoad();
  };
  document.getElementById('attf').onchange = e => { const fs = [...e.target.files]; e.target.value = ''; const dlg = !!ATT.upDlg; ATT.upDlg = false; if (fs.length) take(fs, dlg); };
  document.getElementById('attcam').onchange = e => { const fs = [...e.target.files]; e.target.value = ''; if (fs.length) take(fs, ATT.camFor === 'dlg'); };
}
/* ---------- Notizen aus einem Dokument vorschlagen: erkennen (offline), prüfen, ändern, übernehmen ---------- */
const DOC = { a: null, res: null, timer: 0 };
const docErr = e => { const k = 'gr_doc_e_' + String(e || 'x').replace(/\W/g, '_'), v = t(k); return v === k ? t('gr_doc_e_x') : v; };
async function docOpen(a, again) {
  DOC.a = a; DOC.res = null; clearTimeout(DOC.timer);
  const d = document.getElementById('docdlg'); if (!d.open) d.showModal();
  document.getElementById('docinfo').textContent = a.name; document.getElementById('doclist').innerHTML = ''; document.getElementById('docbar').hidden = true;
  document.getElementById('docgo').disabled = true; document.getElementById('docagain').hidden = true;
  const st = document.getElementById('docst'); st.className = 'msg'; st.textContent = t('gr_doc_run');
  const r = await post('scan', { id: a.id, again: !!again }).catch(() => ({ ok: false }));
  if (!r.ok) { st.className = 'msg err'; st.textContent = t('gr_doc_err', { e: docErr(r.error) }); return; }
  docPoll(r);
}
async function docPoll(r) {
  const st = document.getElementById('docst'), d = document.getElementById('docdlg');
  if (!d.open) return;
  if (!r || r.state === 'run' || r.state === undefined) {
    DOC.timer = setTimeout(async () => { let j; try { j = await (await fetch('scan?id=' + encodeURIComponent(DOC.a.id), { cache: 'no-store' })).json(); } catch (e) { j = null; } docPoll(j); }, 1500);
    return;
  }
  document.getElementById('docagain').hidden = false;
  if (r.state === 'err' || !r.ok) { st.className = 'msg err'; st.textContent = t('gr_doc_err', { e: docErr(r.error) + (r.error === 'tool' && r.detail ? ' ' + r.detail : '') }); return; }
  if (r.state === 'none') { st.textContent = ''; return; }
  DOC.res = r; docDraw();
}
function docDraw() {
  const r = DOC.res, st = document.getElementById('docst'), box = document.getElementById('doclist');
  const m = t('gr_m_' + String(r.method || 'text').replace('+', '')) + (r.pages > 1 ? ', ' + t('gr_m_pages', { n: r.pages }) : '');
  document.getElementById('docinfo').textContent = t(r.doc_date_known ? 'gr_doc_info' : 'gr_doc_info_u', { n: r.name, m, d: fDate(Date.parse(r.doc_date)) });
  const sg = r.suggestions || [];
  if (!sg.length) { st.className = 'msg'; st.textContent = t('gr_doc_empty'); box.innerHTML = ''; return; }
  document.getElementById('docbar').hidden = false;
  box.innerHTML = sg.map(s => {
    const on = !s.dup && s.dup_of == null && s.conf !== 'unklar', pos = t('gr_doc_pos', { p: s.page, l: s.line });
    return `<div class="docrow${on ? ' on' : ''}" data-i="${s.i}">
      <div class="dochead"><label class="check"><input type="checkbox" class="dsel"${on ? ' checked' : ''} aria-label="${esc(t('gr_doc_pick', { p: pos }))}"> <b>${esc(pos)}</b></label>
        <span class="conf c-${s.conf}">${esc(t('gr_doc_c_' + s.conf))}</span>${s.date_only ? `<span class="conf c-day">${esc(t('gr_doc_day'))}</span>` : ''}${s.dup ? `<span class="conf c-dup">${esc(t('gr_doc_dup'))}</span>` : s.dup_of != null ? `<span class="conf c-dup">${esc(t('gr_doc_dup2'))}</span>` : ''}</div>
      <div class="row wrap"><label class="field inl"><span>${esc(t('per_from'))}</span><input type="datetime-local" step="1" class="dfrom" value="${esc(dtl(new Date(s.from)))}"></label>
        <label class="field inl"><span>${esc(t('per_to'))}</span><input type="datetime-local" step="1" class="dto" value="${s.to ? esc(dtl(new Date(s.to))) : ''}"></label></div>
      <textarea rows="2" maxlength="500" class="dtext" aria-label="${esc(t('gr_doc_text'))}">${esc(s.text)}</textarea>
      <div class="mks dtags">${(s.tags || []).map(k => `<button type="button" class="tag ${gAttr(ntGroup(k)).replace('"', ' on"')} data-t="${esc(k)}" aria-pressed="true">${esc(ntLabel(k))}</button>`).join('')}</div>
      <input type="text" class="dwit" maxlength="200" value="${esc(s.witness || '')}" placeholder="${esc(t('fn_wit'))}" aria-label="${esc(t('gr_doc_wit'))}">
      <small class="ctx">${esc(t('gr_doc_ctx'))}: „${esc(s.sentence)}“</small></div>`;
  }).join('') + (r.more ? `<p class="hint">${esc(t('gr_doc_more', { n: r.more }))}</p>` : '');
  box.querySelectorAll('.docrow').forEach(row => {
    row.querySelector('.dsel').onchange = e => { row.classList.toggle('on', e.target.checked); docCount(); };
    row.querySelectorAll('.dtags .tag').forEach(b => b.onclick = () => { const on = b.getAttribute('aria-pressed') !== 'true'; b.setAttribute('aria-pressed', String(on)); b.classList.toggle('on', on); });
  });
  const go = document.getElementById('docgo'); go.textContent = PRO() ? t('gr_doc_go') : t('gr_doc_go_pro'); go.title = PRO() ? '' : t('gr_doc_pro');
  docCount();
}
function docCount() {
  const rows = [...document.querySelectorAll('#doclist .docrow')], k = rows.filter(r => r.querySelector('.dsel').checked).length;
  document.getElementById('docst').className = 'msg'; document.getElementById('docst').textContent = t('gr_doc_found', { n: rows.length, k }) + (PRO() ? '' : ' ' + t('gr_doc_pro'));
  document.getElementById('doccnt').textContent = k + ' / ' + rows.length;
  document.getElementById('docgo').disabled = !k;
}
async function docApply() {
  if (!PRO()) { proOpen(); return; }
  const sg = new Map((DOC.res.suggestions || []).map(s => [String(s.i), s])), items = [];
  for (const row of document.querySelectorAll('#doclist .docrow')) {
    if (!row.querySelector('.dsel').checked) continue;
    const s = sg.get(row.dataset.i), f = row.querySelector('.dfrom').value, to = row.querySelector('.dto').value;
    items.push({ i: s.i, from: f ? inIso(f, s.from) : s.from, to: to ? inIso(to, s.to) : '', text: row.querySelector('.dtext').value, witness: row.querySelector('.dwit').value,
      tags: [...row.querySelectorAll('.dtags .tag[aria-pressed="true"]')].map(b => b.dataset.t), page: s.page, line: s.line, conf: s.conf, date_only: !!s.date_only && f === dtl(new Date(s.from)) });
  }
  const r = await post('doc_apply', { id: DOC.a.id, items }).catch(() => ({ ok: false }));
  if (!r.ok) { const st = document.getElementById('docst'); st.className = 'msg err'; st.textContent = r.error === 'pro' ? t('gr_doc_pro') : t('saveerr'); return; }
  toast('✓ ' + t('gr_doc_done', { n: r.n }), 5000); document.getElementById('docdlg').close(); listLoad(); if (document.getElementById('attdlg').open) attLoad();
}
function initDoc() {
  const sel = on => { document.querySelectorAll('#doclist .docrow').forEach(r => { r.querySelector('.dsel').checked = on; r.classList.toggle('on', on); }); docCount(); };
  document.getElementById('docall').onclick = () => sel(true); document.getElementById('docnone').onclick = () => sel(false);
  document.getElementById('docgo').onclick = docApply;
  document.getElementById('docagain').onclick = () => DOC.a && docOpen(DOC.a, true);
  document.getElementById('docdlg').addEventListener('close', () => clearTimeout(DOC.timer));
}
/* ---------- Start ---------- */
async function init() {
  await stLoad(); tr(); applyTheme();
  document.getElementById('themebtn').onclick = () => { THEME = THEME === 'auto' ? 'light' : THEME === 'light' ? 'dark' : 'auto'; try { localStorage.setItem('gr_theme', THEME); } catch (e) { } applyTheme(); };
  setInterval(() => { if (THEME === 'auto') applyTheme(); }, 4000);
  document.getElementById('grmenu').onclick = e => { e.stopPropagation(); menu(); };
  document.getElementById('helpbtn').onclick = helpOpen;
  document.addEventListener('click', e => { const m = document.getElementById('grmenul'); if (!m.hidden && !e.target.closest('#grmenul')) m.hidden = true; });
  document.addEventListener('keydown', e => { if (e.key === 'Escape') document.getElementById('grmenul').hidden = true; });
  let qt = 0; document.getElementById('grq').addEventListener('input', e => { clearTimeout(qt); qt = setTimeout(() => { LST.q = e.target.value; listDraw(); }, 200); });
  initDialogs(); initFnp(); extInit(); initAtt(); initDoc(); initList(); initLay(); await ntsLoad(); listLoad(); tipsDraw();
  setInterval(() => { if (!document.hidden) { stLoad(); if (!FNP.edit) listLoad(); } }, 30000);   // z. B. neue Notiz aus Home Assistant
}
init();
