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
  stShow(); witList();
}
function stShow() {
  const b = $('grstat'); if (!b) return; b.innerHTML = '';
  const dot = (txt, on, tip) => { const c = el('span', { textContent: txt, className: on ? 'on' : '' }); c.title = tip; c.setAttribute('aria-label', tip); b.appendChild(c); };
  const g = ST.glighter || {};
  if (g.linked) dot('🔗', true, t('gr_gl_linked') + ' – ' + t('gr_gl_linked_tip'));
  else if (g.found) dot('🔗', false, 'GLighter ' + t('gr_gl_found') + ' – ' + t('gr_gl_found_tip'));
  if (ST.mqtt) dot('🏠', true, t('gr_ha_ok_tip'));
  else if (ST.ha && ST.ha.api) dot('🏠', false, t('gr_ha_log_tip'));
}
/* ---------- Schnellwahl: Wörter, Gruppen, Reihenfolge ---------- */
let NOTE_TAGS = { src: ['oben', 'unten', 'nebenan', 'treppenhaus', 'draussen', 'unklar'], kind: ['klopfen', 'schritte', 'musik', 'stimmen', 'tuer', 'moebel', 'bohren', 'hund'],
  lvl: ['leicht', 'deutlich', 'stark'], eff: ['aufgewacht', 'kind_geweckt', 'kein_schlaf', 'gestoert'], act: ['geklingelt', 'angesprochen', 'verwaltung', 'polizei'], misc: ['zeuge', 'serie'] };
const GROUPS = ['src', 'kind', 'lvl', 'eff', 'act', 'misc', 'own'];
const NTS = { own: {}, del: new Set(), hide: new Set(), use: {}, sug: [], max: 5, ren: {}, grp: {}, order: [], mode: 'use' };
function ntGroup(tag) { if (NTS.grp[tag]) return NTS.grp[tag]; for (const g in NOTE_TAGS) if (NOTE_TAGS[g].includes(tag)) return g; return 'own'; }
function ntLabel(tg) { return NTS.own[tg] != null ? NTS.own[tg] : NTS.ren[tg] || t('nt_' + tg); }
function ntsApply(j) {
  if (!j || !j.ok) return;
  if (j.tags) NOTE_TAGS = j.tags;
  NTS.own = {}; NTS.del = new Set(); for (const o of j.own || []) { NTS.own[o.k] = o.l; if (o.del) NTS.del.add(o.k); }
  Object.assign(NTS, { hide: new Set(j.hide || []), use: j.use || {}, sug: j.suggest || [], max: j.own_max || 5, ren: j.ren || {}, grp: j.grp || {}, order: j.order || [], mode: j.mode || 'use' });
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
const tagBtn = (tg, on) => `<button type="button" class="tag g-${ntGroup(tg)}${on ? ' on' : ''}" data-t="${esc(tg)}" aria-pressed="${!!on}">${esc(ntLabel(tg))}</button>`;
const tagMk = tg => `<span class="mk g-${ntGroup(tg)}">${esc(ntLabel(tg))}</span>`;
/* ---------- Notiz jetzt ---------- */
const FNP = { from: null, tags: new Set(), edit: null, fixed: false };
function fnpTags() {
  const box = $('fnptags'); if (!box) return;
  const vis = ntVisible(FNP.tags), by = {}; for (const k of vis) (by[ntGroup(k)] = by[ntGroup(k)] || []).push(k);
  let h = '';
  const w = NTS.sug[0];
  if (w) h += `<div class="sugline">💡 ${esc(t('qt_sug', { w: w.w, n: w.n }))} <button type="button" class="sugy">＋ ${esc(t('qt_create'))}</button><button type="button" class="sugn" aria-label="${esc(t('qt_sug_no'))}">✕</button></div>`;
  for (const g of GROUPS) {
    const ks = by[g] || []; if (!ks.length && g !== 'own') continue;
    h += `<div class="grp"><span>${esc(t('gr_g_' + g))}</span><div>${ks.map(k => tagBtn(k, FNP.tags.has(k))).join('')}${g === 'own' ? `<button type="button" class="tag add">＋ ${esc(t('qt_add'))}</button>` : ''}</div></div>`;
  }
  box.innerHTML = h;
  box.querySelectorAll('.tag[data-t]').forEach(b => {
    b.onclick = () => { const k = b.dataset.t; FNP.tags.has(k) ? FNP.tags.delete(k) : FNP.tags.add(k); b.classList.toggle('on', FNP.tags.has(k)); b.setAttribute('aria-pressed', FNP.tags.has(k)); fnpStart(); };
    b.oncontextmenu = e => { e.preventDefault(); qtOpen(b.dataset.t); };
    let lp = 0; b.addEventListener('touchstart', () => { lp = setTimeout(() => { lp = -1; qtOpen(b.dataset.t); }, 600); }, { passive: true });
    b.addEventListener('touchend', e => { if (lp === -1) e.preventDefault(); clearTimeout(lp); });
    b.addEventListener('touchmove', () => clearTimeout(lp), { passive: true });
  });
  const ad = box.querySelector('.tag.add'); if (ad) ad.onclick = () => qtOpen();
  const sy = box.querySelector('.sugy'); if (sy) sy.onclick = async () => { try { const j = await ntsPost({ action: 'add', l: w.w }); if (j.k) { FNP.tags.add(j.k); fnpTags(); } } catch (e) { alert(e.message); } };
  const sn = box.querySelector('.sugn'); if (sn) sn.onclick = () => ntsPost({ action: 'nope', w: w.k }).catch(e => alert(e.message));
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
function fnpStart() { if (FNP.from == null) FNP.from = nowMs(); fnpShow(); }
function fnpAt() { return FNP.fixed && FNP.from != null ? FNP.from : nowMs(); }
function fnpShow() {
  const at = FNP.edit && !FNP.fixed ? FNP.edit.a : fnpAt();
  $('capclock').textContent = fTime(at); $('capdate').textContent = fDate(at);
  const to = $('fnptoi').value, run = $('fnprun').checked;
  $('fnpfrom').textContent = FNP.edit ? t('gr_editing_s') : FNP.fixed ? t('gr_t_fixed') : FNP.from == null ? t(matchMedia('(pointer:coarse)').matches ? 'gr_wait_m' : 'gr_wait') : t('gr_t_live');
  $('fnptimetxt').textContent = (FNP.fixed || FNP.edit ? t('gr_t_at', { t: fTime(at) }) : t('gr_t_now')) + (to ? ' – ' + fTime(new Date(to).getTime()) : run ? ' – ' + t('gr_t_run') : '') + ' · ' + t('gr_t_change');
  $('capttl').textContent = FNP.edit ? t('gr_change_ttl') : t('fn_btn');
}
function fnpReset() {
  FNP.from = null; FNP.tags = new Set(); FNP.edit = null; FNP.fixed = false;
  $('fnptext').value = ''; $('fnpwit').value = ''; $('fnpfromi').value = ''; $('fnptoi').value = ''; $('fnprun').checked = false;
  $('fnpcancel').hidden = true; $('fnpsave').textContent = t('save'); $('fnpanel').classList.remove('editing');
  timeEdit(false); fnpTags(); fnpShow(); listDraw();
}
function timeEdit(open) {
  $('fnpext').hidden = !open; $('fnptimebtn').setAttribute('aria-expanded', String(open));
  if (open && !$('fnpfromi').value) $('fnpfromi').value = dtl(new Date(fnpAt()));
}
async function fnpSave() {
  const fixed = FNP.fixed && $('fnpfromi').value, tv = $('fnptoi').value, run = $('fnprun').checked, ed = FNP.edit;
  const body = { action: ed ? 'edit' : 'add', id: ed ? ed.id : '', from: fixed ? $('fnpfromi').value : ed ? ed.from : dtl(new Date(nowMs())), to: tv || (run ? dtl(new Date(nowMs())) : ''),
    src: ed ? (ed.src || 'all') : 'all', text: autoText($('fnptext').value, FNP.tags), typed: !!$('fnptext').value.trim(), tags: [...FNP.tags], witness: $('fnpwit').value };
  const msg = $('fnpmsg'); msg.className = 'msg';
  try {
    const r = await post('note', body);
    if (!r.ok) { msg.textContent = t(r.error === 'empty' ? 'fn_empty' : r.error === 'to' ? 'fn_bad_to' : 'saveerr'); msg.classList.add('err'); return; }
    const at = r.note && r.note.a; fnpReset(); ntsLoad();
    msg.textContent = '✓ ' + t(ed ? 'gr_changed_at' : 'gr_saved_at', { t: at ? fTime(at) : '' }); setTimeout(() => { if (msg.textContent.startsWith('✓')) msg.textContent = ''; }, 5000);
    listLoad();
  } catch (e) { msg.textContent = t('saveerr'); msg.classList.add('err'); }
}
function fnpEdit(n) {
  FNP.edit = n; FNP.tags = new Set(n.tags || []); FNP.fixed = false; FNP.from = n.a;
  $('fnptext').value = n.text || ''; $('fnpwit').value = n.witness || '';
  $('fnpfromi').value = n.from ? dtl(new Date(n.from)) : ''; $('fnptoi').value = n.to ? dtl(new Date(n.to)) : ''; $('fnprun').checked = false;
  $('fnpcancel').hidden = false; $('fnpsave').textContent = t('gr_change'); $('fnpanel').classList.add('editing');
  fnpTags(); fnpShow(); listDraw(); $('fnpanel').scrollIntoView({ block: 'start', behavior: 'smooth' }); $('fnptext').focus({ preventScroll: true });
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
  doc.body.appendChild(panel); FNPOP = w;
  const back = () => { if (FNPOP !== w) return; FNPOP = null; ph.remove(); try { parent.insertBefore(panel, next && next.parentNode === parent ? next : null); } catch (e) { parent.appendChild(panel); } };
  pb.onclick = () => { try { w.close(); } catch (e) { } back(); };
  w.addEventListener('pagehide', back);
  addEventListener('pagehide', () => { try { w.close(); } catch (e) { } });
  setTimeout(() => { const tx = doc.getElementById('fnptext'); if (tx) tx.focus(); }, 100);
}
function initFnp() {
  fnpTags(); fnpShow();
  $('fnppop').onclick = fnPop;
  $('fnptext').addEventListener('input', () => { if ($('fnptext').value.trim()) fnpStart(); });
  $('fnpwit').addEventListener('input', () => { if ($('fnpwit').value.trim()) fnpStart(); });
  $('fnprun').onchange = () => { fnpStart(); fnpShow(); };
  $('fnpsave').onclick = fnpSave; $('fnpcancel').onclick = fnpReset;
  enterSave($('fnptext'), fnpSave);
  $('fnptimebtn').onclick = () => timeEdit($('fnpext').hidden);
  $('fnpfnow').onclick = () => { FNP.fixed = false; $('fnpfromi').value = dtl(new Date(nowMs())); fnpShow(); };
  $('fnpfromi').addEventListener('input', () => { const v = new Date($('fnpfromi').value).getTime(); if (!isNaN(v)) { FNP.fixed = true; FNP.from = v; } fnpShow(); });
  $('fnptoi').addEventListener('input', fnpShow);
  $('fnptnow').onclick = () => { $('fnptoi').value = dtl(new Date(nowMs())); fnpShow(); };
  $('fnptclr').onclick = () => { $('fnptoi').value = ''; fnpShow(); };
  setInterval(() => {                                 // die Uhr läuft mit, bis gespeichert wird (oder die Zeit von Hand gesetzt ist)
    if (document.hidden && !(FNPOP && !FNPOP.closed)) return;
    if (!FNP.fixed && !FNP.edit) { const fi = $('fnpfromi'); if (fi && !$('fnpext').hidden && fi.ownerDocument.activeElement !== fi) fi.value = dtl(new Date(nowMs())); }
    fnpShow();
  }, 1000);
  if (!matchMedia('(pointer:coarse)').matches) setTimeout(() => $('fnptext').focus({ preventScroll: true }), 300);
}
/* ---------- Liste: Zeitleiste nach Tagen ---------- */
const cnt = n => t(n === 1 ? 'gr_count_1' : 'gr_count', { n });
const LST = { notes: [], q: '', tag: '' };
async function listLoad() {
  try { LST.notes = (await (await fetch('notes?limit=2000&q=' + encodeURIComponent(LST.q), { cache: 'no-store' })).json()).notes || []; } catch (e) { }
  listDraw();
}
function filtDraw() {
  const box = document.getElementById('grfilt'); if (!box) return;
  const cnt = {}; for (const n of LST.notes) for (const k of n.tags || []) cnt[k] = (cnt[k] || 0) + 1;
  const top = Object.keys(cnt).sort((a, b) => cnt[b] - cnt[a]).slice(0, 10);
  box.innerHTML = top.length > 1 ? top.map(k => `<button type="button" class="tag g-${ntGroup(k)}${LST.tag === k ? ' on' : ''}" data-t="${esc(k)}" aria-pressed="${LST.tag === k}">${esc(ntLabel(k))} <small>${cnt[k]}</small></button>`).join('') : '';
  box.querySelectorAll('.tag').forEach(b => b.onclick = () => { LST.tag = LST.tag === b.dataset.t ? '' : b.dataset.t; listDraw(); });
}
function listDraw() {
  const box = document.getElementById('grnotes'); if (!box) return; box.innerHTML = '';
  filtDraw();
  const list = LST.tag ? LST.notes.filter(n => (n.tags || []).includes(LST.tag)) : LST.notes;
  document.getElementById('grcount').textContent = cnt(list.length);
  if (!list.length) { box.appendChild(el('div', { className: 'empty', textContent: t(LST.q || LST.tag ? 'gr_none_q' : 'gr_none') })); return; }
  const days = new Map(); for (const n of list) { const k = isoDay(new Date(n.a)); if (!days.has(k)) days.set(k, []); days.get(k).push(n); }
  for (const [, ns] of days) {
    const h = el('div', { className: 'day' }); h.innerHTML = `<span>${esc(fDay(ns[0].a))}</span><small>${esc(cnt(ns.length))}</small>`; box.appendChild(h);
    for (const n of ns) {
      const r = el('div', { className: 'note' + (FNP.edit && FNP.edit.id === n.id ? ' cur' : '') });
      const by = n.by === 'homeassistant' ? '🏠 Home Assistant' : n.by === 'import' ? t('gr_imported') : '';
      r.innerHTML = `<div class="t">${esc(fTime(n.a))}${n.to ? `<small>${esc(t('gr_until', { t: fTime(n.b) }))}</small>` : ''}</div>
        <div class="c">${(n.tags || []).filter(k => k !== 'zeuge' || !n.witness).map(tagMk).join('')}${n.text ? `<span class="tx">${esc(n.text)}</span>` : ''}${n.witness ? `<span class="who">👤 ${esc(n.witness)}</span>` : ''}${by ? `<span class="by">${esc(by)}</span>` : ''}</div>
        <div class="a"><button type="button" class="e" aria-label="${esc(t('nt_edit'))}" title="${esc(t('nt_edit'))}">✎</button><button type="button" class="d" aria-label="${esc(t('nt_del'))}" title="${esc(t('nt_del'))}">🗑</button></div>`;
      r.querySelector('.e').onclick = () => fnpEdit(n);
      r.querySelector('.d').onclick = async () => { if (!confirm(t('fn_del_q'))) return; try { await post('note', { action: 'del', id: n.id }); } catch (e) { } if (FNP.edit && FNP.edit.id === n.id) fnpReset(); listLoad(); };
      box.appendChild(r);
    }
  }
}
/* ---------- Schnellwahl bearbeiten (Dialog): umbenennen, Gruppe, Reihenfolge, ausblenden, zurücksetzen ---------- */
function qtOpen(focus) {
  const d = document.getElementById('qtdlg');
  const gsel = document.getElementById('qtnewg'); gsel.innerHTML = ''; for (const g of GROUPS) option(gsel, g, t('gr_g_' + g)); gsel.value = 'own';
  qtDraw(focus); if (!d.open) d.showModal();
  if (!focus) setTimeout(() => document.getElementById('qtnew').focus(), 50);
}
function qtDraw(focus) {
  const box = document.getElementById('qtlist'); box.innerHTML = '';
  document.querySelectorAll('#qtdlg .seg button').forEach(b => { const on = b.dataset.mode === NTS.mode; b.classList.toggle('on', on); b.setAttribute('aria-checked', String(on)); b.setAttribute('role', 'radio'); });
  const ownN = Object.keys(NTS.own).filter(k => !NTS.del.has(k)).length;
  document.getElementById('qtinfo').textContent = (PRO() ? '' : t('gr_qt_free', { n: ownN, m: NTS.max }) + ' ') + t(NTS.mode === 'fixed' ? 'gr_mode_fixed_h' : 'gr_mode_use_h');
  const sg = document.getElementById('qtsug'); sg.innerHTML = NTS.sug.map(w => `<button type="button" class="chip" data-w="${esc(w.w)}">💡 ${esc(w.w)} (${w.n}×) ＋</button>`).join('');
  sg.querySelectorAll('button').forEach(b => b.onclick = () => ntsPost({ action: 'add', l: b.dataset.w }).then(() => qtDraw()).catch(e => alert(e.message)));
  const all = ntOrdered(ntAll()), by = {}; for (const k of all) (by[ntGroup(k)] = by[ntGroup(k)] || []).push(k);
  for (const g of GROUPS) {
    const ks = by[g] || []; if (!ks.length) continue;
    const sec = el('div', { className: 'qtg g-' + g }); sec.innerHTML = `<h4>${esc(t('gr_g_' + g))}</h4>`;
    const rows = el('div', { className: 'qtrows' });
    for (const k of ks) {
      const own = NTS.own[k] != null, off = NTS.hide.has(k);
      const r = el('div', { className: 'qtr' + (off ? ' off' : '') }); r.dataset.k = k; r.draggable = true;
      r.innerHTML = `<span class="hd" title="${esc(t('gr_drag'))}" aria-hidden="true">⠿</span><input type="text" maxlength="30" value="${esc(ntLabel(k))}" aria-label="${esc(t('qt_ren'))}"><select aria-label="${esc(t('gr_group'))}">${GROUPS.map(x => `<option value="${x}"${x === g ? ' selected' : ''}>${esc(t('gr_g_' + x))}</option>`).join('')}</select>
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
  const upd = () => { const p = prefRead(); document.getElementById('pfex').textContent = fDate(ex, p) + ', ' + fTime(ex, p); };
  for (const x of [ds, ts, document.getElementById('pfrel'), document.getElementById('pfwd')]) x.onchange = upd;
  upd(); document.getElementById('prefdlg').showModal();
}
const prefRead = () => ({ date: document.getElementById('pfdate').value, time: document.getElementById('pftime').value, rel: document.getElementById('pfrel').checked, wd: document.getElementById('pfwd').checked });
/* ---------- Menü ---------- */
function menu() {
  const m = document.getElementById('grmenul');
  if (!m.hidden) { m.hidden = true; return; }
  const lock = PRO() ? '' : '🔒 Pro';
  const items = [['✎', t('qt_title'), () => qtOpen()], ['🕒', t('gr_prefs'), prefOpen], null,
    ['⤓', t('gr_backup'), () => { location.href = 'backup'; }],
    ['📄', t('gr_export_csv'), () => PRO() ? (location.href = 'export?fmt=csv') : proOpen(), lock],
    ['🗂', t('gr_export_json'), () => PRO() ? (location.href = 'export?fmt=json') : proOpen(), lock],
    ['⤒', t('gr_import'), () => PRO() ? document.getElementById('grimpf').click() : proOpen(), lock],
    ['👤', t('gr_persons'), () => PRO() ? perOpen() : proOpen(), lock], null,
    ['⭐', PRO() ? t('gr_pro_on') : t('gr_pro_get'), proOpen]];
  m.innerHTML = '';
  for (const it of items) {
    if (!it) { m.appendChild(el('hr')); continue; }
    const b = el('button', { type: 'button' }); b.setAttribute('role', 'menuitem');
    b.append(el('span', { textContent: it[0], className: 'mi' }), el('span', { textContent: it[1] })); if (it[3]) b.appendChild(el('span', { className: 'lock', textContent: it[3] }));
    b.onclick = () => { m.hidden = true; it[2](); }; m.appendChild(b);
  }
  m.hidden = false; m.querySelector('button').focus();
}
function proOpen() {
  const p = ST.pro || {};
  document.getElementById('prost').textContent = p.ok ? t('pro_active', { d: p.until || '' }) : p.state === 'expired' ? t('gr_pro_expired', { d: p.until || '' }) : t('gr_pro_none');
  document.getElementById('probuy').href = p.buy || 'https://www.gsimulations.de/greport/#buypro';
  document.getElementById('prodel').hidden = !(p.ok || p.state === 'expired'); document.getElementById('promsg').textContent = '';
  document.getElementById('prodlg').showModal();
}
function perOpen() { document.getElementById('perlist').value = (ST.persons || []).join('\n'); document.getElementById('perdlg').showModal(); }
function initDialogs() {
  document.querySelectorAll('dialog .dlgx').forEach(b => b.onclick = () => b.closest('dialog').close());
  document.getElementById('prosave').onclick = async () => {
    const k = document.getElementById('prokey').value.trim(); if (!k) return;
    const j = await post('pro', { key: k }).catch(() => ({ ok: false }));
    const m = document.getElementById('promsg'); m.className = 'msg' + (j.ok ? '' : ' err'); m.textContent = j.ok ? '✓ ' + t('gr_pro_ok') : t('gr_pro_bad');
    if (j.ok) { document.getElementById('prokey').value = ''; await stLoad(); ntsLoad(); setTimeout(() => document.getElementById('prodlg').close(), 900); }
  };
  document.getElementById('prodel').onclick = async () => { if (!confirm(t('pro_remove_q'))) return; await post('pro', { action: 'del' }).catch(() => { }); await stLoad(); proOpen(); };
  document.getElementById('persave').onclick = async () => {
    const lst = document.getElementById('perlist').value.split('\n').map(x => x.trim()).filter(Boolean);
    const j = await post('persons', { list: lst }).catch(() => ({ ok: false }));
    if (j.ok) { ST.persons = j.list; witList(); document.getElementById('perdlg').close(); } else alert(t('saveerr'));
  };
  document.getElementById('pfsave').onclick = async () => {
    const j = await post('prefs', prefRead()).catch(() => ({ ok: false }));
    if (j.ok) { PF = { date: j.date, time: j.time, rel: j.rel, wd: j.wd }; document.getElementById('prefdlg').close(); fnpShow(); listDraw(); } else alert(t('saveerr'));
  };
  document.getElementById('grimpf').onchange = async e => {
    const f = e.target.files[0]; e.target.value = ''; if (!f) return;
    try { const j = await (await fetch('import', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: await f.text() })).json(); toast(j.ok ? t('gr_imported_n', { n: j.n }) : t('gr_import_bad')); listLoad(); } catch (x) { toast(t('gr_import_bad')); }
  };
  initQt();
}
/* ---------- Start ---------- */
async function init() {
  await stLoad(); tr(); applyTheme();
  document.getElementById('themebtn').onclick = () => { THEME = THEME === 'auto' ? 'light' : THEME === 'light' ? 'dark' : 'auto'; try { localStorage.setItem('gr_theme', THEME); } catch (e) { } applyTheme(); };
  setInterval(() => { if (THEME === 'auto') applyTheme(); }, 4000);
  document.getElementById('grmenu').onclick = e => { e.stopPropagation(); menu(); };
  document.addEventListener('click', e => { const m = document.getElementById('grmenul'); if (!m.hidden && !e.target.closest('#grmenul')) m.hidden = true; });
  document.addEventListener('keydown', e => { if (e.key === 'Escape') document.getElementById('grmenul').hidden = true; });
  let qt = 0; document.getElementById('grq').addEventListener('input', e => { clearTimeout(qt); qt = setTimeout(() => { LST.q = e.target.value; listLoad(); }, 250); });
  initDialogs(); initFnp(); await ntsLoad(); listLoad();
  setInterval(() => { if (!document.hidden) { stLoad(); if (!FNP.edit) listLoad(); } }, 30000);   // z. B. neue Notiz aus Home Assistant
}
init();
