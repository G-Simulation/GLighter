'use strict';
/* GReport – der Notiz-Teil von GLighter als eigene App. Aussehen und Bedienung wie in GLighter. */
let FNPOP = null;                                    // Fenster, in das der Notizbereich abgedockt ist
const $ = id => document.getElementById(id) || (FNPOP && !FNPOP.closed ? FNPOP.document.getElementById(id) : null);
const pad = n => String(n).padStart(2, '0');
const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const el = (tag, props) => { const e = document.createElement(tag); Object.assign(e, props || {}); return e; };
const option = (sel, v, label) => { const o = el('option', { value: String(v), textContent: label }); sel.appendChild(o); return o; };
const isoDay = d => d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate());
const dtl = d => isoDay(d) + 'T' + pad(d.getHours()) + ':' + pad(d.getMinutes()) + ':' + pad(d.getSeconds());
const nowServer = () => Date.now();
let lang = (navigator.language || 'de').toLowerCase().startsWith('de') ? 'de' : 'en';
function t(k, v) {
  let s = (I18N[lang] || I18N.de)[k];
  if (s === undefined) s = I18N.de[k];
  if (s === undefined) return k;
  if (v) for (const x in v) s = s.split('{' + x + '}').join(v[x]);
  return s;
}
const locale = () => lang === 'en' ? 'en-GB' : 'de-DE';
function tr() {
  document.documentElement.lang = lang; document.title = t('title');
  document.querySelectorAll('[data-i]').forEach(e => { e.textContent = t(e.dataset.i); });
  document.querySelectorAll('[data-ia]').forEach(e => { e.title = t(e.dataset.ia); e.setAttribute('aria-label', t(e.dataset.ia)); });
  document.querySelectorAll('[data-iph]').forEach(e => { e.placeholder = t(e.dataset.iph); });
}
function toast(msg, ms) {
  let e = document.getElementById('toast'); if (!e) { e = el('div', { id: 'toast', className: 'toast' }); e.setAttribute('role', 'status'); document.body.appendChild(e); }
  e.textContent = msg; e.classList.add('on'); clearTimeout(e._t); e._t = setTimeout(() => e.classList.remove('on'), ms || 4000);
}
/* ---------- Design (hell/dunkel/wie Home Assistant) ---------- */
let THEME = 'auto'; try { THEME = localStorage.getItem('gr_theme') || 'auto'; } catch (e) { }
function haDark() { try { const p = window.parent; if (!p || p === window) return null; const ha = p.document.querySelector('home-assistant'), d = ha && ha.hass && ha.hass.themes && ha.hass.themes.darkMode; return typeof d === 'boolean' ? d : null; } catch (e) { return null; } }
function applyTheme() {
  let res = THEME === 'light' || THEME === 'dark' ? THEME : null;
  if (!res) { const h = haDark(); if (h !== null) res = h ? 'dark' : 'light'; }
  const r = document.documentElement; if (res) r.setAttribute('data-theme', res); else r.removeAttribute('data-theme');
  const b = document.getElementById('themebtn'); if (b) { b.textContent = (THEME === 'auto' ? '🌓 ' : THEME === 'dark' ? '🌙 ' : '☀ ') + t('th_' + THEME); b.title = t('th_tip'); }
}
/* ---------- Zustand (Pro, GLighter, Home Assistant) ---------- */
let ST = { pro: { ok: false }, glighter: {}, ha: {}, persons: [] };
const PRO = () => !!(ST.pro && ST.pro.ok);
async function stLoad() {
  try { ST = await (await fetch('state', { cache: 'no-store' })).json(); } catch (e) { }
  if (ST.lang === 'de' || ST.lang === 'en') lang = ST.lang;
  stShow(); witList();
}
function stShow() {
  const b = $('grstat'); if (!b) return; b.innerHTML = '';
  const chip = (txt, cls, tip) => { const c = el('span', { className: 'chip ' + (cls || ''), textContent: txt }); if (tip) c.title = tip; b.appendChild(c); };
  const g = ST.glighter || {};
  if (g.linked) chip('🔗 ' + t('gr_gl_linked'), 'ok', t('gr_gl_linked_tip'));
  else if (g.found) chip('GLighter: ' + t('gr_gl_found'), 'warn', t('gr_gl_found_tip'));
  if (ST.mqtt) chip('🏠 ' + t('gr_ha_ok'), 'ok', t('gr_ha_ok_tip'));
  else if (ST.ha && ST.ha.api) chip('🏠 ' + t('gr_ha_log'), '', t('gr_ha_log_tip'));
  chip(PRO() ? '⭐ Pro' : t('gr_free'), PRO() ? 'ok' : '', PRO() ? t('pro_active', { d: ST.pro.until || '' }) : t('gr_free_tip'));
}
/* ---------- Schnellwahl (wie in GLighter) ---------- */
let NOTE_TAGS = { src: ['oben', 'unten', 'nebenan', 'treppenhaus', 'draussen', 'unklar'], kind: ['klopfen', 'schritte', 'musik', 'stimmen', 'tuer', 'moebel', 'bohren', 'hund'],
  lvl: ['leicht', 'deutlich', 'stark'], eff: ['aufgewacht', 'kind_geweckt', 'kein_schlaf', 'gestoert'], act: ['geklingelt', 'angesprochen', 'verwaltung', 'polizei'], misc: ['zeuge', 'serie'] };
const NTS = { own: {}, del: new Set(), hide: new Set(), use: {}, sug: [], max: 5 };
function ntGroup(tag) { for (const g in NOTE_TAGS) if (NOTE_TAGS[g].includes(tag)) return g; return 'own'; }
function ntLabel(tg) { return NTS.own[tg] != null ? NTS.own[tg] : t('nt_' + tg); }
function ntsApply(j) {
  if (!j || !j.ok) return;
  if (j.tags) NOTE_TAGS = j.tags;
  NTS.own = {}; NTS.del = new Set(); for (const o of j.own || []) { NTS.own[o.k] = o.l; if (o.del) NTS.del.add(o.k); }
  NTS.hide = new Set(j.hide || []); NTS.use = j.use || {}; NTS.sug = j.suggest || []; NTS.max = j.own_max || 5;
}
async function ntsLoad() { try { ntsApply(await (await fetch('notetags', { cache: 'no-store' })).json()); } catch (e) { } fnpTags(); }
async function ntsPost(body) {
  const j = await (await fetch('notetags', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })).json();
  if (!j.ok) throw new Error(j.error === 'limit_free' ? t('gr_qt_limit_free', { n: NTS.max }) : j.error === 'limit' ? t('qt_limit') : j.error === 'empty' ? t('qt_empty') : (j.error || 'error'));
  ntsApply(j); fnpTags(); return j;
}
function ntList(sel) {
  const out = [], seen = new Set(), add = tg => { if (!seen.has(tg)) { seen.add(tg); out.push(tg); } };
  for (const g in NOTE_TAGS) for (const tg of NOTE_TAGS[g]) if (!NTS.hide.has(tg) || (sel && sel.has(tg))) add(tg);
  for (const k in NTS.own) if (!NTS.del.has(k) || (sel && sel.has(k))) add(k);
  const pos = new Map(out.map((x, i) => [x, i]));
  return out.sort((a, b) => ((NTS.use[b] || 0) - (NTS.use[a] || 0)) || (pos.get(a) - pos.get(b)));
}
const ntChip = (tg, on) => `<button type="button" class="chip ntchip g-${ntGroup(tg)}${on ? ' on' : ''}" data-t="${esc(tg)}" aria-pressed="${!!on}" title="${esc(t('qt_tip'))}">${NTS.own[tg] != null ? '★ ' : ''}${esc(ntLabel(tg))}</button>`;
const ntAddBtn = () => `<button type="button" class="chip ntadd" title="${esc(t('qt_add_tip'))}">＋ ${esc(t('qt_add'))}</button>`;
const ntTag = tg => `<span class="ntag g-${ntGroup(tg)}">${esc(ntLabel(tg))}</span>`;
function ntSugHtml() {
  const w = NTS.sug[0]; if (!w) return '';
  return `<span class="ntsug" data-w="${esc(w.w)}" data-k="${esc(w.k)}">💡 ${esc(t('qt_sug', { w: w.w, n: w.n }))} <button type="button" class="chip ntsugy">＋</button><button type="button" class="chip ntsugn" title="${esc(t('qt_sug_no'))}">✕</button></span>`;
}
function ntChipBind(box, sel, onTog) {                   // Klick = wählen, Rechtsklick/lange drücken = verwalten, ＋ = eigene anlegen
  box.querySelectorAll('.ntchip').forEach(b => {
    b.onclick = () => { const tg = b.dataset.t; sel.has(tg) ? sel.delete(tg) : sel.add(tg); b.classList.toggle('on', sel.has(tg)); b.setAttribute('aria-pressed', sel.has(tg)); if (onTog) onTog(tg); };
    b.oncontextmenu = e => { e.preventDefault(); ntManage(box, b.dataset.t); };
  });
  const a = box.querySelector('.ntadd'); if (a) a.onclick = () => ntManage(box);
  const sg = box.querySelector('.ntsug');
  if (sg) {
    sg.querySelector('.ntsugy').onclick = async () => { try { const j = await ntsPost({ action: 'add', l: sg.dataset.w }); if (j.k) { sel.add(j.k); if (onTog) onTog(j.k); fnpTags(); } } catch (e) { alert(e.message); } };
    sg.querySelector('.ntsugn').onclick = () => ntsPost({ action: 'nope', w: sg.dataset.k }).catch(e => alert(e.message));
  }
}
function ntManage(box, focus) {                        // Verwalten direkt unter den Tasten: welche Wörter in der Liste stehen (auch die Auswahl in Home Assistant)
  const doc = box.ownerDocument; let m = doc.getElementById(box.id + '_qt');
  if (m && !focus) { m.remove(); return; }
  if (!m) { m = doc.createElement('div'); m.id = box.id + '_qt'; m.className = 'qtman'; m.style.cssText = 'border:1px solid #8884;border-radius:8px;padding:8px;margin:6px 0;display:flex;flex-direction:column;gap:6px'; box.after(m); }
  const draw = () => {
    const own = Object.keys(NTS.own).filter(k => !NTS.del.has(k)), built = []; for (const g in NOTE_TAGS) built.push(...NOTE_TAGS[g]);
    m.innerHTML = `<div style="display:flex;gap:6px;align-items:center;flex-wrap:wrap"><b style="flex:1">${esc(t('qt_title'))}</b><button type="button" class="chip qtx">✕</button></div>
      <small>${esc(t('gr_qt_ha'))}</small>
      <div style="display:flex;gap:6px"><input type="text" class="qtnew" maxlength="30" placeholder="${esc(t('qt_new_ph'))}" style="flex:1;min-width:0"><button type="button" class="pri qtaddok">${esc(t('qt_create'))}</button></div>
      ${!PRO() ? `<small>${esc(t('gr_qt_free', { n: own.length, m: NTS.max }))}</small>` : ''}
      ${NTS.sug.length ? `<small>${esc(t('qt_sug_h'))}</small><div style="display:flex;gap:5px;flex-wrap:wrap">${NTS.sug.map(w => `<span class="chip qtsg" data-w="${esc(w.w)}" data-k="${esc(w.k)}">💡 ${esc(w.w)} (${w.n}×) <a href="#" class="qtsy">＋</a> <a href="#" class="qtsn">✕</a></span>`).join('')}</div>` : `<small>${esc(t('qt_learn_h'))}</small>`}
      ${own.length ? `<small>${esc(t('qt_own_h'))}</small>` + own.map(k => `<div class="qtrow" data-k="${esc(k)}" style="display:flex;gap:6px"><input type="text" maxlength="30" value="${esc(NTS.own[k])}" style="flex:1;min-width:0"><button type="button" class="chip qtren">${esc(t('qt_ren'))}</button><button type="button" class="chip qtdel">🗑</button></div>`).join('') : ''}
      <small>${esc(t('qt_built_h'))}</small><div style="display:flex;gap:5px;flex-wrap:wrap">${built.map(k => `<button type="button" class="chip qtb${NTS.hide.has(k) ? '' : ' on'}" data-k="${esc(k)}" style="${NTS.hide.has(k) ? 'opacity:.5;text-decoration:line-through' : ''}">${esc(ntLabel(k))}</button>`).join('')}</div>`;
    const go = p => ntsPost(p).then(draw).catch(e => alert(e.message));
    m.querySelector('.qtx').onclick = () => m.remove();
    const nw = m.querySelector('.qtnew'), addIt = () => { const v = nw.value.trim(); if (v) go({ action: 'add', l: v }); };
    m.querySelector('.qtaddok').onclick = addIt; nw.onkeydown = e => { if (e.key === 'Enter') { e.preventDefault(); addIt(); } };
    m.querySelectorAll('.qtsg').forEach(x => { x.querySelector('.qtsy').onclick = e => { e.preventDefault(); go({ action: 'add', l: x.dataset.w }); }; x.querySelector('.qtsn').onclick = e => { e.preventDefault(); go({ action: 'nope', w: x.dataset.k }); }; });
    m.querySelectorAll('.qtrow').forEach(r => {
      const k = r.dataset.k, inp = r.querySelector('input');
      r.querySelector('.qtren').onclick = () => go({ action: 'ren', k, l: inp.value });
      inp.onkeydown = e => { if (e.key === 'Enter') { e.preventDefault(); go({ action: 'ren', k, l: inp.value }); } };
      r.querySelector('.qtdel').onclick = () => { if (confirm(t('qt_del_q', { n: NTS.own[k] }))) go({ action: 'del', k }); };
    });
    m.querySelectorAll('.qtb').forEach(b => b.onclick = () => go({ action: 'hide', k: b.dataset.k, on: !NTS.hide.has(b.dataset.k) }));
    if (focus) { const r = m.querySelector(`.qtrow[data-k="${CSS.escape(focus)}"] input`), b = m.querySelector(`.qtb[data-k="${CSS.escape(focus)}"]`); (r || b || nw).focus(); if (r) r.select(); focus = null; }
    else nw.focus();
  };
  draw();
}
/* Aus den Markierungen einen Satz bilden (nur wenn kein eigener Text da ist), z. B. „Deutliche Schritte im Treppenhaus“ */
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
  const kinds = tg.filter(x => D.kind[x]), lvl = tg.find(x => D.lvl[x]), src = tg.find(x => D.src[x]);
  const rest = tg.filter(x => D.rest[x]).map(x => D.rest[x]).concat(tg.filter(x => NTS.own[x] != null).map(x => NTS.own[x]));
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
/* ---------- Notiz jetzt (wie die Notiz-Leiste in GLighter) ---------- */
const FNP = { from: null, tags: new Set(), tick: null, edit: null };
function fnpTags() {
  const box = $('fnptags'); if (!box) return;
  const W = ((box.ownerDocument || document).defaultView || window).innerWidth, few = W < 700 && !FNP.more;
  let k = 0;
  box.innerHTML = ntSugHtml() + ntList(FNP.tags).map(tg => (few && k++ >= 6 && !FNP.tags.has(tg)) ? '' : ntChip(tg, FNP.tags.has(tg))).join('')
    + (few ? '' : ntAddBtn()) + (W < 700 ? `<button type="button" class="chip fnpmoretags">${esc(t(few ? 'fnp_tags_more' : 'fnp_tags_less'))}</button>` : '');
  const mb = box.querySelector('.fnpmoretags'); if (mb) mb.onclick = () => { FNP.more = !FNP.more; fnpTags(); };
  ntChipBind(box, FNP.tags, () => fnpStart());
}
function witList() {                                   // Pro: gespeicherte Personen zum Antippen (mehrere Zeugen)
  const box = $('fnpwitl'); if (!box) return; box.innerHTML = '';
  if (!PRO()) return;
  for (const p of ST.persons || []) {
    const b = el('button', { type: 'button', className: 'chip', textContent: '👤 ' + p });
    b.onclick = () => { const w = $('fnpwit'), cur = w.value.split(',').map(x => x.trim()).filter(Boolean); if (!cur.includes(p)) cur.push(p); w.value = cur.join(', '); fnpStart(); };
    box.appendChild(b);
  }
}
function fnpStart() { if (FNP.from == null) { FNP.from = nowServer(); fnpShow(); } }
function fnpShow() {
  const hm = ts => { const d = new Date(ts); return pad(d.getHours()) + ':' + pad(d.getMinutes()) + ':' + pad(d.getSeconds()); };
  const f = $('fnpfrom');
  f.textContent = FNP.edit ? t('gr_editing', { t: new Date(FNP.edit.a).toLocaleString(locale()) }) : FNP.from == null ? t(matchMedia('(pointer:coarse)').matches ? 'gr_wait_m' : 'gr_wait')
    : t('fnp_from', { t: hm(FNP.from) });
  f.classList.toggle('on', FNP.from != null || !!FNP.edit);
}
function fnpReset() {
  FNP.from = null; FNP.tags = new Set(); FNP.edit = null; FNP.fixed = false;
  $('fnptext').value = ''; $('fnpwit').value = ''; $('fnpfromi').value = ''; $('fnptoi').value = '';
  $('fnpcancel').hidden = true; $('fnpsave').textContent = t('save'); $('fnpanel').classList.remove('editing');
  fnpTags(); fnpShow(); listDraw();
}
function fnpFold(open) {
  $('fnpbody').hidden = !open; $('fnptog').setAttribute('aria-expanded', open ? 'true' : 'false'); $('fnpanel').classList.toggle('shut', !open);
  try { localStorage.setItem('gr_fnp', open ? '1' : '0'); } catch (e) { }
}
async function fnpSave() {
  const fixed = FNP.fixed && $('fnpfromi').value, tv = $('fnptoi').value;
  const ed = FNP.edit;
  const body = { action: ed ? 'edit' : 'add', id: ed ? ed.id : '', from: fixed ? $('fnpfromi').value : ed ? ed.from : dtl(new Date(nowServer())), to: tv,
    src: ed ? (ed.src || 'all') : 'all', text: autoText($('fnptext').value, FNP.tags), typed: !!$('fnptext').value.trim(), tags: [...FNP.tags], witness: $('fnpwit').value };
  const msg = $('fnpmsg'); msg.className = 'fnpmsg';
  try {
    const r = await (await fetch('note', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })).json();
    if (!r.ok) { msg.textContent = t(r.error === 'empty' ? 'fn_empty' : r.error === 'to' ? 'fn_bad_to' : 'saveerr'); msg.classList.add('err'); return; }
    fnpReset(); ntsLoad(); msg.textContent = '✓ ' + t(ed ? 'gr_changed' : 'fnp_saved'); setTimeout(() => { if (msg.textContent.startsWith('✓')) msg.textContent = ''; }, 4000);
    listLoad();
  } catch (e) { msg.textContent = t('saveerr'); msg.classList.add('err'); }
}
function fnpEdit(n) {                                  // gespeicherte Notiz in der Leiste ändern
  FNP.edit = n; FNP.tags = new Set(n.tags || []); FNP.fixed = true; FNP.from = n.a;
  $('fnptext').value = n.text || ''; $('fnpwit').value = n.witness || '';
  $('fnpfromi').value = n.from ? dtl(new Date(n.from)) : ''; $('fnptoi').value = n.to ? dtl(new Date(n.to)) : '';
  $('fnpcancel').hidden = false; $('fnpsave').textContent = t('gr_change'); $('fnpanel').classList.add('editing');
  fnpFold(true); fnpTags(); fnpShow(); listDraw(); $('fnpanel').scrollIntoView({ block: 'nearest', behavior: 'smooth' }); $('fnptext').focus();
}
/* Notizbereich abdocken: eigenes Fenster über anderen Programmen (Chrome/Edge: Bild-im-Bild, sonst kleines Zusatzfenster) */
async function fnPop() {
  if (FNPOP && !FNPOP.closed) { try { FNPOP.focus(); } catch (e) { } return; }
  const panel = $('fnpanel'); if (!panel) return;
  let w = null;
  try { if (window.documentPictureInPicture) w = await documentPictureInPicture.requestWindow({ width: 460, height: 380 }); } catch (e) { w = null; }
  if (!w) { try { w = window.open('', 'gr_note', 'popup=yes,width=480,height=400'); } catch (e) { w = null; } }
  if (!w) { alert(t('pop_fail')); return; }
  const doc = w.document; doc.title = 'GReport – ' + t('fn_btn');
  const vp = doc.createElement('meta'); vp.name = 'viewport'; vp.content = 'width=device-width,initial-scale=1'; doc.head.appendChild(vp);
  for (const l of document.querySelectorAll('link[rel=stylesheet]')) { const n = doc.createElement('link'); n.rel = 'stylesheet'; n.href = l.href; doc.head.appendChild(n); }
  for (const at of document.documentElement.attributes) if (at.name.startsWith('data-')) doc.documentElement.setAttribute(at.name, at.value);
  doc.body.className = 'gr fnpopbody';
  const parent = panel.parentNode, next = panel.nextSibling;
  const ph = el('div', { className: 'card fnpph' }); const pb = el('button', { type: 'button', className: 'chip', textContent: t('pop_back') });
  ph.append(document.createTextNode('📝 ' + t('pop_open') + ' '), pb); parent.insertBefore(ph, panel);
  doc.body.appendChild(panel); panel.classList.add('inpop'); FNPOP = w;
  const back = () => { if (FNPOP !== w) return; FNPOP = null; ph.remove(); try { parent.insertBefore(panel, next && next.parentNode === parent ? next : null); } catch (e) { parent.appendChild(panel); } panel.classList.remove('inpop'); };
  pb.onclick = () => { try { w.close(); } catch (e) { } back(); };
  w.addEventListener('pagehide', back);
  let rz = 0; w.addEventListener('resize', () => { clearTimeout(rz); rz = setTimeout(() => { if (FNPOP === w) fnpTags(); }, 150); });
  addEventListener('pagehide', () => { try { w.close(); } catch (e) { } });
  setTimeout(() => { const tx = doc.getElementById('fnptext'); if (tx) tx.focus(); }, 100);
}
function initFnp() {
  let open = true; try { const v = localStorage.getItem('gr_fnp'); if (v != null) open = v !== '0'; } catch (e) { }
  fnpFold(open); fnpTags(); fnpShow();
  $('fnppop').onclick = fnPop;
  $('fnptog').onclick = () => { const o = $('fnpbody').hidden; fnpFold(o); if (o) $('fnptext').focus(); };
  $('fnptext').addEventListener('input', () => { if ($('fnptext').value.trim()) fnpStart(); });
  $('fnpwit').addEventListener('input', () => { if ($('fnpwit').value.trim()) fnpStart(); });
  $('fnpsave').onclick = fnpSave; $('fnpcancel').onclick = fnpReset;
  enterSave($('fnptext'), fnpSave);
  {                                                   // jeder Teil einzeln einklappbar (Textfeld, Schnellwahl, Zeuge, Zeitraum) – gemerkt pro Browser
    const pn = $('fnpanel');
    const PARTS = [['txt', 'fnp_p_txt'], ['tags', 'fnp_p_tags'], ['wit', 'fnp_p_wit'], ['ext', 'gr_p_ext']];
    let hid = new Set(); try { hid = new Set(JSON.parse(localStorage.getItem('gr_fnphide') || '[]')); } catch (e) { }
    let bar = $('fnpsec'); if (!bar) { bar = el('div', { id: 'fnpsec', className: 'fnpsec' }); $('fnpbody').prepend(bar); }
    const sync = () => {
      for (const [k] of PARTS) pn.classList.toggle('fh-' + k, hid.has(k));
      const els = { txt: [$('fnptext')], tags: [$('fnptags'), $('fnptags_qt')], wit: [$('fnpwit'), $('fnpwitl')], ext: [$('fnpext')] };
      for (const [k] of PARTS) for (const e of els[k]) if (e) e.style.display = hid.has(k) ? 'none' : '';
      bar.innerHTML = '';
      for (const [k, l] of PARTS) {
        const n = k === 'tags' && hid.has(k) && FNP.tags.size ? ' (' + FNP.tags.size + ')' : k === 'wit' && hid.has(k) && $('fnpwit').value.trim() ? ' (1)' : '';
        const b = el('button', { type: 'button', className: 'chip fnpsb' + (hid.has(k) ? '' : ' on'), textContent: (hid.has(k) ? '▸ ' : '▾ ') + t(l) + n });
        b.setAttribute('aria-expanded', String(!hid.has(k)));
        b.onclick = () => { hid.has(k) ? hid.delete(k) : hid.add(k); try { localStorage.setItem('gr_fnphide', JSON.stringify([...hid])); } catch (e) { } sync(); };
        bar.appendChild(b);
      }
    };
    $('fnptags').addEventListener('click', () => setTimeout(sync, 0)); $('fnpwit').addEventListener('input', sync);
    sync();
  }
  $('fnpfnow').onclick = () => { FNP.fixed = false; $('fnpfromi').value = dtl(new Date(nowServer())); };
  $('fnpfromi').addEventListener('input', () => { FNP.fixed = true; const v = new Date($('fnpfromi').value).getTime(); if (!isNaN(v)) FNP.from = v; fnpShow(); });
  $('fnptnow').onclick = () => { $('fnptoi').value = dtl(new Date(nowServer())); };
  $('fnptclr').onclick = () => { $('fnptoi').value = ''; };
  FNP.tick = setInterval(() => {                    // die Uhrzeit läuft mit, bis sie beim Speichern gesetzt wird (oder von Hand geändert ist)
    if (document.hidden && !(FNPOP && !FNPOP.closed)) return;
    const now = nowServer();
    if (!FNP.fixed) {
      if (FNP.from != null) FNP.from = now;
      const fi = $('fnpfromi'); if (fi && fi.ownerDocument.activeElement !== fi) fi.value = dtl(new Date(now));
    }
    if (FNP.from != null && !FNP.fixed) fnpShow();
  }, 1000);
  if (!matchMedia('(pointer:coarse)').matches) setTimeout(() => $('fnptext').focus({ preventScroll: true }), 300);
}
/* ---------- Liste der Notizen ---------- */
const LST = { notes: [], q: '' };
async function listLoad() {
  try { LST.notes = (await (await fetch('notes?limit=1000&q=' + encodeURIComponent(LST.q), { cache: 'no-store' })).json()).notes || []; } catch (e) { }
  listDraw();
}
function listDraw() {
  const box = document.getElementById('grnotes'); if (!box) return; box.innerHTML = '';
  document.getElementById('grcount').textContent = t('gr_count', { n: LST.notes.length });
  if (!LST.notes.length) { box.appendChild(el('div', { className: 'ntnone', textContent: t(LST.q ? 'gr_none_q' : 'gr_none') })); return; }
  let day = '';
  for (const n of LST.notes) {
    const a = new Date(n.a), d = a.toLocaleDateString(locale(), { weekday: 'short', day: '2-digit', month: '2-digit', year: 'numeric' });
    if (d !== day) { day = d; box.appendChild(el('div', { className: 'grday', textContent: d })); }
    const r = el('div', { className: 'grn' + (FNP.edit && FNP.edit.id === n.id ? ' edit' : '') });
    const tt = pad(a.getHours()) + ':' + pad(a.getMinutes()) + ':' + pad(a.getSeconds()), tb = n.to ? new Date(n.b) : null;
    const by = n.by === 'homeassistant' ? '🏠 Home Assistant' : n.by === 'import' ? '⤓ ' + t('gr_imported') : '';
    r.innerHTML = `<div class="grt"><b>${esc(tt)}</b>${tb ? '– ' + esc(pad(tb.getHours()) + ':' + pad(tb.getMinutes()) + ':' + pad(tb.getSeconds())) : ''}</div>
      <div class="grb">${(n.tags || []).map(ntTag).join('')}${n.text ? `<span class="ntt">${esc(n.text)}</span>` : ''}${n.witness ? `<span class="ntw">👤 ${esc(n.witness)}</span>` : ''}${by ? `<span class="grby">${esc(by)}</span>` : ''}</div>
      <div class="gra"><button type="button" class="chip gre" title="${esc(t('nt_edit'))}">✎</button><button type="button" class="chip grd" title="${esc(t('nt_del'))}">🗑</button></div>`;
    r.querySelector('.gre').onclick = () => fnpEdit(n);
    r.querySelector('.grd').onclick = async () => { if (!confirm(t('fn_del_q'))) return; try { await fetch('note', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ action: 'del', id: n.id }) }); } catch (e) { } if (FNP.edit && FNP.edit.id === n.id) fnpReset(); listLoad(); };
    box.appendChild(r);
  }
}
/* ---------- Menü: Sicherung (frei), Export/Import, Personen (Pro), Pro-Schlüssel ---------- */
function menu() {
  const m = document.getElementById('grmenul');
  if (!m.hidden) { m.hidden = true; return; }
  const lock = PRO() ? '' : ' 🔒';
  const items = [['⤓ ' + t('gr_backup'), () => { location.href = 'backup'; }],
    ['📄 ' + t('gr_export_csv') + lock, () => PRO() ? (location.href = 'export?fmt=csv') : proOpen()],
    ['🗂 ' + t('gr_export_json') + lock, () => PRO() ? (location.href = 'export?fmt=json') : proOpen()],
    ['⤒ ' + t('gr_import') + lock, () => PRO() ? document.getElementById('grimpf').click() : proOpen()],
    ['👤 ' + t('gr_persons') + lock, () => PRO() ? perOpen() : proOpen()],
    ['⭐ ' + t('pro_title'), proOpen]];
  m.innerHTML = '';
  for (const [l, f] of items) { const b = el('button', { type: 'button', textContent: l }); b.onclick = () => { m.hidden = true; f(); }; m.appendChild(b); }
  m.hidden = false;
}
function proOpen() {
  const d = document.getElementById('prodlg'), p = ST.pro || {};
  document.getElementById('prost').textContent = p.ok ? t('pro_active', { d: p.until || '' }) : p.state === 'expired' ? t('gr_pro_expired', { d: p.until || '' }) : t('gr_pro_none');
  document.getElementById('probuy').href = p.buy || 'https://www.gsimulations.de/greport/#buypro';
  document.getElementById('prodel').hidden = !(p.ok || p.state === 'expired'); document.getElementById('promsg').textContent = '';
  d.showModal();
}
function perOpen() { document.getElementById('perlist').value = (ST.persons || []).join('\n'); document.getElementById('perdlg').showModal(); }
function initDialogs() {
  document.querySelectorAll('dialog .dlgx').forEach(b => b.onclick = () => b.closest('dialog').close());
  document.getElementById('prosave').onclick = async () => {
    const k = document.getElementById('prokey').value.trim(); if (!k) return;
    const j = await (await fetch('pro', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ key: k }) })).json().catch(() => ({ ok: false }));
    const m = document.getElementById('promsg'); m.className = 'fnpmsg' + (j.ok ? '' : ' err'); m.textContent = j.ok ? '✓ ' + t('gr_pro_ok') : '⚠ ' + t('gr_pro_bad');
    if (j.ok) { document.getElementById('prokey').value = ''; await stLoad(); ntsLoad(); setTimeout(() => document.getElementById('prodlg').close(), 900); }
  };
  document.getElementById('prodel').onclick = async () => { if (!confirm(t('pro_remove_q'))) return; await fetch('pro', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{"action":"del"}' }).catch(() => { }); await stLoad(); proOpen(); };
  document.getElementById('persave').onclick = async () => {
    const lst = document.getElementById('perlist').value.split('\n').map(x => x.trim()).filter(Boolean);
    const j = await (await fetch('persons', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ list: lst }) })).json().catch(() => ({ ok: false }));
    if (j.ok) { ST.persons = j.list; witList(); document.getElementById('perdlg').close(); } else alert(t('saveerr'));
  };
  document.getElementById('grimpf').onchange = async e => {
    const f = e.target.files[0]; e.target.value = ''; if (!f) return;
    try { const j = await (await fetch('import', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: await f.text() })).json(); toast(j.ok ? t('gr_imported_n', { n: j.n }) : t('gr_import_bad')); listLoad(); } catch (x) { toast(t('gr_import_bad')); }
  };
}
/* ---------- Start ---------- */
async function init() {
  await stLoad(); tr(); applyTheme();
  document.getElementById('themebtn').onclick = () => { THEME = THEME === 'auto' ? 'light' : THEME === 'light' ? 'dark' : 'auto'; try { localStorage.setItem('gr_theme', THEME); } catch (e) { } applyTheme(); };
  setInterval(() => { if (THEME === 'auto') applyTheme(); }, 4000);
  document.getElementById('grmenu').onclick = e => { e.stopPropagation(); menu(); };
  document.addEventListener('click', e => { const m = document.getElementById('grmenul'); if (!m.hidden && !e.target.closest('#grmenul')) m.hidden = true; });
  let qt = 0; document.getElementById('grq').addEventListener('input', e => { clearTimeout(qt); qt = setTimeout(() => { LST.q = e.target.value; listLoad(); }, 250); });
  initDialogs(); initFnp(); await ntsLoad(); listLoad();
  let rz = 0; addEventListener('resize', () => { clearTimeout(rz); rz = setTimeout(fnpTags, 150); });
  setInterval(() => { if (!document.hidden) { stLoad(); if (!FNP.edit) listLoad(); } }, 30000);   // z. B. neue Notiz aus Home Assistant
}
init();
