'use strict';
/* Eigene Felder („Bausteine“) der Notiz-Erfassung – gleiche Datei in GReport und GLighter.
   Arten: Textfeld, Zähler, Zahl, Ja/Nein, Auswahlliste, Skala, Dauer, Datum/Uhrzeit, Ort, Person/Zeuge.
   Werte je Notiz in „fields“ {Kennung: Wert}. Pillen-Rubriken bleiben die Rubriken der Schnellwahl (Werte in „tags“).
   Die App gibt Texte (t), Maskieren (esc) und Zeitformate über Felder.setup() mit. */
window.Felder = (() => {
  const TYPES = ['text', 'counter', 'number', 'yesno', 'select', 'scale', 'duration', 'datetime', 'place', 'person'];
  const ROLES = ['mitbewohner', 'nachbar', 'hausverwaltung', 'vermieter', 'polizei', 'sonstige'];
  const H = { t: k => k, esc: s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c])),
    lang: () => 'de', fmtDT: ms => new Date(ms).toLocaleString(), dtl: d => d.toISOString().slice(0, 16), dto: d => d.toISOString(), nowMs: () => Date.now() };
  function t(k, v) { return H.t(k, v); }
  const e = s => H.esc(s);
  const S = { defs: [], sec: {}, counts: {}, daily: {}, sug: {}, tpl: null, first: false, max: 20, tpls: ['laerm', 'allg', 'zaehler'] };
  function setup(o) { Object.assign(H, o || {}); }
  function load(j) {
    if (!j || !j.ok) return;
    for (const k of ['sec', 'counts', 'daily', 'sug']) S[k] = j[k] || {};
    S.defs = j.blocks || []; S.tpl = j.tpl || null; S.first = !!j.first; S.max = j.max || 20; if (j.tpls) S.tpls = j.tpls;
  }
  const isId = id => /^b_[0-9a-f]{6}$/.test(String(id || ''));
  const byId = id => S.defs.find(b => b.id === id);
  const active = () => S.defs.filter(b => !b.del);
  const visible = () => active().filter(b => !b.hide);
  const isEmpty = v => v == null || v === '' || (Array.isArray(v) && !v.length) || (typeof v === 'object' && !Array.isArray(v) && !String(v.n || '').trim());
  const hex6 = () => Array.from(crypto.getRandomValues(new Uint8Array(3)), x => x.toString(16).padStart(2, '0')).join('');
  const newId = () => { let i; do { i = 'b_' + hex6(); } while (byId(i)); return i; };
  const numTxt = n => H.lang() === 'de' ? String(n).replace('.', ',') : String(n);
  const readNum = s => { s = String(s == null ? '' : s).trim().replace(',', '.'); if (!s) return null; const n = Number(s); return isFinite(n) ? n : NaN; };
  const durTxt = m => { m = Math.round(m || 0); return m < 60 ? m + ' min' : Math.floor(m / 60) + ' h' + (m % 60 ? ' ' + String(m % 60).padStart(2, '0') + ' min' : ''); };
  const txtMax = b => Math.max(10, Math.min(500, +b.max || 500));
  const dtKind = b => b.kind === 'date' || b.kind === 'time' ? b.kind : 'dt';
  const p2 = n => String(n).padStart(2, '0'), ymd = d => d.getFullYear() + '-' + p2(d.getMonth() + 1) + '-' + p2(d.getDate());
  const dtNow = b => { const d = new Date(H.nowMs()), k = dtKind(b); return k === 'date' ? ymd(d) : k === 'time' ? p2(d.getHours()) + ':' + p2(d.getMinutes()) + (b.sec ? ':' + p2(d.getSeconds()) : '') : H.dtl(d); };
  const dtIn = (b, v) => { if (!v) return ''; const k = dtKind(b), s = String(v);
    if (/^\d{2}:\d{2}/.test(s)) return k === 'time' ? s : '';
    if (/^\d{4}-\d{2}-\d{2}$/.test(s)) return k === 'date' ? s : k === 'dt' ? s + 'T00:00' : '';
    const d = new Date(s); if (isNaN(d)) return ''; return k === 'date' ? ymd(d) : k === 'time' ? p2(d.getHours()) + ':' + p2(d.getMinutes()) : H.dtl(d); };
  const scaleMax = b => b.rng === '10' ? 10 : 5, scaleMin = b => b.rng === '10' ? 0 : 1;
  const roleTxt = r => r ? t('fb_role_' + r) : '';
  /* Wert lesbar */
  function fmt(b, v) {
    if (v == null || v === '') return '';
    switch (b.type) {
      case 'counter': return b.mode === 'add' ? String(v) : (v > 0 ? '+' : v < 0 ? '−' : '') + Math.abs(v);
      case 'number': return numTxt(v) + (b.unit ? ' ' + b.unit : '');
      case 'yesno': return v ? t('fb_yes') : t('fb_no');
      case 'scale': return v + '/' + scaleMax(b);
      case 'duration': return durTxt(v);
      case 'datetime': {
        if (/^\d{2}:\d{2}$/.test(String(v))) return String(v);                                   // nur Uhrzeit
        if (/^\d{4}-\d{2}-\d{2}$/.test(String(v))) { const [y, m, d] = String(v).split('-').map(Number); return new Date(y, m - 1, d).toLocaleDateString(H.lang() === 'en' ? 'en-GB' : 'de-DE'); }   // nur Datum
        const ms = Date.parse(v); return isNaN(ms) ? String(v) : H.fmtDT(ms);
      }
      case 'person': { if (typeof v !== 'object') return String(v); const x = [roleTxt(v.r), v.c].filter(Boolean); return (v.n || '') + (x.length ? ' (' + x.join(', ') + ')' : ''); }
      default: return Array.isArray(v) ? v.join(', ') : String(v);
    }
  }
  /* kurz „Name: Wert“ in der Reihenfolge der Definitionen (auch gelöschte – alte Werte bleiben sichtbar) */
  function compact(fields) {
    if (!fields || typeof fields !== 'object') return [];
    const out = [];
    for (const b of S.defs) if (b.id in fields) { const s = fmt(b, fields[b.id]); if (s !== '') out.push((b.l || b.id) + ': ' + s); }
    return out;
  }
  const label = b => e(b.l || t('fb_type_' + b.type));
  const reqMark = req => req ? `<i class="reqm" aria-hidden="true"> *</i><span class="sr"> ${e(t('fb_req_sr'))}</span>` : '';
  const helpHtml = b => b.h ? `<small class="fbhelp" id="fbh_${b.id}">${e(b.h)}</small>` : '';
  const desc = b => b.h ? ` aria-describedby="fbh_${b.id}"` : '';
  /* ---------- Erfassung: ein Feld zeichnen; hk.set(id, Wert), hk.start(), hk.count(b, ±1) ---------- */
  function countTxt(b, v) { const n = S.counts[b.id] || 0; return b.mode === 'add' ? t('fb_c_note', { n: v || 0 }) + ' · ' + t('fb_c_today', { n }) : t('fb_c_today', { n }); }
  function render(box, b, v, hk) {
    const id = b.id, req = !!b.req, ar = req ? ' aria-required="true"' : '';
    box.dataset.b = id; box.classList.add('fbblk', 'fbt-' + b.type); box.classList.toggle('req', req);
    if (b.col) box.style.setProperty('--fbc', b.col); else box.style.removeProperty('--fbc');
    const lab = `<label class="fbl" for="fbi_${id}">${label(b)}${reqMark(req)}</label>`, grp = `<span class="fbl" id="fbl_${id}">${label(b)}${reqMark(req)}</span>`;
    let h = '';
    switch (b.type) {
      case 'text': { const mx = txtMax(b), ph = b.ph ? ` placeholder="${e(b.ph)}"` : '', sg = !b.ml && b.sug && (S.sug[id] || []).length;
        h = lab + (b.ml ? `<textarea id="fbi_${id}" rows="${b.rows || 2}" maxlength="${mx}"${ph}${ar}${desc(b)}>${e(v || '')}</textarea>`
          : `<input type="text" id="fbi_${id}" maxlength="${mx}" autocomplete="off"${sg ? ` list="fbd_${id}"` : ''} value="${e(v || '')}"${ph}${ar}${desc(b)}>${sg ? `<datalist id="fbd_${id}">${S.sug[id].map(x => `<option value="${e(x)}"></option>`).join('')}</datalist>` : ''}`); break; }
      case 'place': h = lab + `<input type="text" id="fbi_${id}" maxlength="120" list="fbd_${id}" autocomplete="off" value="${e(v || '')}"${b.ph ? ` placeholder="${e(b.ph)}"` : ''}${ar}${desc(b)}><datalist id="fbd_${id}">${(S.sug[id] || []).map(x => `<option value="${e(x)}"></option>`).join('')}</datalist>`; break;
      case 'number': h = lab + `<span class="fbrow"><input type="text" class="fbnumi" inputmode="decimal" autocomplete="off" id="fbi_${id}" value="${v == null ? '' : e(numTxt(v))}"${ar}${desc(b)}>${b.unit ? `<span class="fbunit">${e(b.unit)}</span>` : ''}${b.min != null || b.max != null ? `<small class="fbunit">${e(t('fb_range', { a: b.min != null ? numTxt(b.min) : '…', b: b.max != null ? numTxt(b.max) : '…' }))}</small>` : ''}</span>`; break;
      case 'counter': h = grp + `<span class="fbrow fbcnt"><button type="button" class="fbplus" aria-label="${e(t('fb_c_plus', { l: b.l }))}" aria-describedby="fbc_${id}">＋1</button>${b.minus ? `<button type="button" class="fbminus" aria-label="${e(t('fb_c_minus', { l: b.l }))}" aria-describedby="fbc_${id}">−1</button>` : ''}<span class="fbcount" id="fbc_${id}" aria-live="polite">${e(countTxt(b, v))}</span></span>`; break;
      case 'yesno': h = grp + `<span class="fbrow" role="group" aria-labelledby="fbl_${id}"${desc(b)}><button type="button" class="fbchip" data-v="1" aria-pressed="${v === true}">${e(t('fb_yes'))}</button><button type="button" class="fbchip" data-v="0" aria-pressed="${v === false}">${e(t('fb_no'))}</button></span>`; break;
      case 'select': {
        const opts = (b.opts || []).slice(); for (const x of (Array.isArray(v) ? v : v ? [v] : [])) if (!opts.includes(x)) opts.push(x);   // alter Wert bleibt wählbar
        h = b.multi ? grp + `<span class="fbrow" role="group" aria-labelledby="fbl_${id}"${desc(b)}>${opts.map(o => `<button type="button" class="fbchip" data-o="${e(o)}" aria-pressed="${(v || []).includes(o)}">${e(o)}</button>`).join('') || `<small class="fbhelp">${e(t('fb_sel_empty'))}</small>`}</span>`
          : lab + `<select id="fbi_${id}"${ar}${desc(b)}><option value="">${e(t('fb_sel_none'))}</option>${opts.map(o => `<option${o === v ? ' selected' : ''}>${e(o)}</option>`).join('')}</select>`;
        break;
      }
      case 'scale': {
        const lo = scaleMin(b), hi = scaleMax(b), ns = []; for (let i = lo; i <= hi; i++) ns.push(i);
        h = grp + `<span class="fbrow fbscale" role="group" aria-labelledby="fbl_${id}"${desc(b)}>${b.lo ? `<small class="fbend">${e(b.lo)}</small>` : ''}${ns.map(i => `<button type="button" class="fbchip fbnum" data-v="${i}" aria-pressed="${v === i}" aria-label="${e(t('fb_scale_v', { v: i, m: hi }) + (i === lo && b.lo ? ' – ' + b.lo : i === hi && b.hi ? ' – ' + b.hi : ''))}">${i}</button>`).join('')}${b.hi ? `<small class="fbend">${e(b.hi)}</small>` : ''}</span>`;
        break;
      }
      case 'duration': { const hh = v == null ? '' : Math.floor(v / 60), mm = v == null ? '' : v % 60;
        h = grp + `<span class="fbrow" role="group" aria-labelledby="fbl_${id}"${desc(b)}><input type="number" class="fbdh" min="0" max="1666" inputmode="numeric" value="${hh}" aria-label="${e(b.l + ': ' + t('fb_hours'))}"><span>${e(t('fb_h'))}</span><input type="number" class="fbdm" min="0" max="59" inputmode="numeric" value="${mm}" aria-label="${e(b.l + ': ' + t('fb_minutes'))}"><span>${e(t('fb_min'))}</span></span>`; break; }
      case 'datetime': { const k = dtKind(b), ty = k === 'date' ? 'date' : k === 'time' ? 'time' : 'datetime-local';
        h = lab + `<span class="fbrow"><input type="${ty}" id="fbi_${id}"${k === 'date' ? '' : ` step="${b.sec ? 1 : 60}"`} value="${e(dtIn(b, v))}"${ar}${desc(b)}>${b.nonow ? '' : `<button type="button" class="chip fbnow">${e(t(k === 'date' ? 'fb_today' : 'fb_now'))}</button>`}</span>`; break; }
      case 'person': { const p = v && typeof v === 'object' ? v : {};
        h = grp + `<span class="fbrow fbper" role="group" aria-labelledby="fbl_${id}"${desc(b)}><input type="text" class="fbpn" maxlength="80" value="${e(p.n || '')}" placeholder="${e(t('fb_p_name'))}" aria-label="${e(b.l + ': ' + t('fb_p_name'))}"${ar}><select class="fbpr" aria-label="${e(b.l + ': ' + t('fb_p_role'))}"><option value="">${e(t('fb_role_none'))}</option>${ROLES.map(r => `<option value="${r}"${p.r === r ? ' selected' : ''}>${e(roleTxt(r))}</option>`).join('')}</select><input type="text" class="fbpc" maxlength="120" value="${e(p.c || '')}" placeholder="${e(t('fb_p_contact'))}" aria-label="${e(b.l + ': ' + t('fb_p_contact'))}"></span>`; break; }
    }
    box.innerHTML = h + helpHtml(b);
    bind(box, b, v, hk);
  }
  function bind(box, b, v, hk) {
    const id = b.id, set = x => { hk.set(id, isEmpty(x) ? undefined : x); if (!isEmpty(x)) hk.start(); }, q = s => box.querySelector(s);
    const i = q('#fbi_' + id);
    if (b.type === 'text' || b.type === 'place') i.addEventListener('input', () => set(i.value.trim() ? i.value : ''));
    else if (b.type === 'number') i.addEventListener('input', () => { const n = readNum(i.value); const bad = Number.isNaN(n) || (n != null && ((b.min != null && n < b.min) || (b.max != null && n > b.max))); i.setAttribute('aria-invalid', String(bad)); set(bad ? '' : n); box.dataset.bad = bad ? '1' : ''; });
    else if (b.type === 'select' && !b.multi) i.addEventListener('change', () => set(i.value));
    else if (b.type === 'datetime') {
      const k = dtKind(b), val = () => !i.value ? '' : k === 'dt' ? H.dto(new Date(i.value)) : k === 'time' ? i.value.slice(0, b.sec ? 8 : 5) : i.value;
      i.addEventListener('input', () => set(val()));
      const nb = q('.fbnow'); if (nb) nb.onclick = () => { i.value = dtNow(b); i.dispatchEvent(new Event('input')); };
      if (isEmpty(v) && b.def === 'now') { i.value = dtNow(b); hk.set(id, val()); }          // vorbelegt mit „jetzt“ (startet die Notiz nicht)
    }
    else if (b.type === 'yesno') box.querySelectorAll('.fbchip').forEach(c => c.onclick = () => { const on = c.getAttribute('aria-pressed') !== 'true'; box.querySelectorAll('.fbchip').forEach(x => x.setAttribute('aria-pressed', 'false')); c.setAttribute('aria-pressed', String(on)); set(on ? c.dataset.v === '1' : ''); });
    else if (b.type === 'scale') box.querySelectorAll('.fbchip').forEach(c => c.onclick = () => { const on = c.getAttribute('aria-pressed') !== 'true'; box.querySelectorAll('.fbchip').forEach(x => x.setAttribute('aria-pressed', 'false')); c.setAttribute('aria-pressed', String(on)); set(on ? +c.dataset.v : ''); });
    else if (b.type === 'select') box.querySelectorAll('.fbchip').forEach(c => c.onclick = () => { c.setAttribute('aria-pressed', String(c.getAttribute('aria-pressed') !== 'true')); set([...box.querySelectorAll('.fbchip[aria-pressed="true"]')].map(x => x.dataset.o)); });
    else if (b.type === 'duration') { const f = () => { const hh = readNum(q('.fbdh').value), mm = readNum(q('.fbdm').value); const bad = Number.isNaN(hh) || Number.isNaN(mm) || (mm != null && (mm < 0 || mm > 59)) || (hh != null && hh < 0); box.dataset.bad = bad ? '1' : ''; set(bad || (hh == null && mm == null) ? '' : Math.round((hh || 0) * 60 + (mm || 0))); }; q('.fbdh').addEventListener('input', f); q('.fbdm').addEventListener('input', f); }
    else if (b.type === 'person') { const f = () => set({ n: q('.fbpn').value.trim(), r: q('.fbpr').value, c: q('.fbpc').value.trim() }); for (const s of ['.fbpn', '.fbpc']) q(s).addEventListener('input', f); q('.fbpr').addEventListener('change', f); }
    else if (b.type === 'counter') {
      const press = d => {
        if (b.mode === 'add') { const n = Math.max(0, (hk.get(id) || 0) + d); hk.set(id, n || undefined); if (n) hk.start(); q('.fbcount').textContent = countTxt(b, n); return; }
        hk.count(b, d);
      };
      q('.fbplus').onclick = () => press(1); const m = q('.fbminus'); if (m) m.onclick = () => press(-1);
    }
  }
  function countShow(root, b) { const c = root && root.querySelector(`.fbblk[data-b="${b.id}"] .fbcount`); if (c) c.textContent = countTxt(b, undefined); }
  /* Pflicht und Eingaben prüfen → {miss: [Namen], bad: [Namen]} */
  function check(fv, root, only) {
    const miss = [], bad = [];
    for (const b of (only || visible())) {
      if (b.req && b.type !== 'counter' && isEmpty((fv || {})[b.id])) miss.push(b.l);
      const box = root && root.querySelector(`.fbblk[data-b="${b.id}"]`); if (box && box.dataset.bad === '1') bad.push(b.l);
    }
    return { miss, bad };
  }
  /* ---------- Statistik: Zähler je Tag (letzte 14 Tage) als kleine Balken ---------- */
  function chart(b) {
    const d = S.daily[b.id] || [], mx = Math.max(1, ...d.map(x => x[1])), sum = d.reduce((a, x) => a + x[1], 0), n = d.length || 1, w = 100 / n;
    const bars = d.map((x, i) => { const hh = Math.max(x[1] > 0 ? 6 : 1.5, 36 * Math.max(0, x[1]) / mx); return `<rect x="${(i * w + w * 0.15).toFixed(2)}" y="${(38 - hh).toFixed(2)}" width="${(w * 0.7).toFixed(2)}" height="${hh.toFixed(2)}" rx="1"${i === n - 1 ? ' class="now"' : ''}></rect>`; }).join('');
    const a = t('fb_st_a', { l: b.l, n: S.counts[b.id] || 0, s: sum, d: d.map(x => x[0].slice(8, 10) + '.' + x[0].slice(5, 7) + '. ' + x[1]).join(', ') });
    return `<figure class="fbst"><figcaption><b>${e(b.l)}</b> <span>${e(t('fb_c_today', { n: S.counts[b.id] || 0 }))} · ${e(t('fb_st_14', { s: sum }))}</span></figcaption><svg viewBox="0 0 100 40" preserveAspectRatio="none" role="img" aria-label="${e(a)}">${bars}</svg></figure>`;
  }
  /* ---------- Layout anpassen: Einstellungen je Feld (Entwurf d = {blocks, sec}) ---------- */
  function newDef(type) {
    const b = { id: newId(), type, l: t('fb_type_' + type), isNew: true };
    if (type === 'counter') Object.assign(b, { mode: 'entry', minus: true });
    if (type === 'select') b.opts = [];
    if (type === 'scale') b.rng = '5';
    return b;
  }
  const cb = (cls, on, txt, extra) => `<label class="check fbck"><input type="checkbox" class="${cls}"${on ? ' checked' : ''}${extra || ''}> ${e(txt)}</label>`;
  const inp = (cls, txt, val, max, extra) => `<label class="fbf"><span>${e(txt)}</span><input type="text" class="${cls}" maxlength="${max}" value="${e(val == null ? '' : val)}"${extra || ''}></label>`;
  /* Zeile für ein eingebautes Bereich (k) oder ein Feld (b). bi = {k, l (Standardname), req (erlaubt), help (erlaubt)} */
  function edRow(it, d) {
    const b = it.b, s = it.k ? (d.sec[it.k] = d.sec[it.k] || {}) : null, nm = b ? b.l : (s.l || it.l), hid = b ? !!b.hide : !!s.hide;
    let x = '';
    if (b) {
      if (b.type === 'text') x += inp('fe_ph', t('fb_ed_ph'), b.ph, 80) + inp('fe_tmax', t('fb_ed_maxlen'), b.max, 3, ' inputmode="numeric"') + cb('fe_ml', b.ml, t('fb_ed_ml'))
        + `<label class="fbf fe_mlon"${b.ml ? '' : ' hidden'}><span>${e(t('fb_ed_rows'))}</span><select class="fe_rows">${[2, 3, 4, 6, 8].map(n => `<option value="${n}"${(b.rows || 2) === n ? ' selected' : ''}>${n}</option>`).join('')}</select></label>`
        + `<span class="fe_mloff"${b.ml ? ' hidden' : ''}>${cb('fe_sug', b.sug, t('fb_ed_sug'))}</span>`;
      if (b.type === 'place') x += inp('fe_ph', t('fb_ed_ph'), b.ph, 80);
      if (b.type === 'datetime') x += `<label class="fbf"><span>${e(t('fb_ed_kind'))}</span><select class="fe_kind">${[['dt', 'fb_ed_k_dt'], ['date', 'fb_ed_k_date'], ['time', 'fb_ed_k_time']].map(([v, k]) => `<option value="${v}"${dtKind(b) === v ? ' selected' : ''}>${e(t(k))}</option>`).join('')}</select></label>`
        + `<label class="fbf"><span>${e(t('fb_ed_def'))}</span><select class="fe_def"><option value=""${b.def !== 'now' ? ' selected' : ''}>${e(t('fb_ed_def_empty'))}</option><option value="now"${b.def === 'now' ? ' selected' : ''}>${e(t('fb_ed_def_now'))}</option></select></label>`
        + cb('fe_nonow', !b.nonow, t('fb_ed_nowbtn')) + `<span class="fe_secw"${dtKind(b) === 'date' ? ' hidden' : ''}>${cb('fe_sec', b.sec, t('fb_ed_sec'))}</span>`;
      if (b.type === 'counter') x += `<label class="fbf"><span>${e(t('fb_ed_mode'))}</span><select class="fe_mode"><option value="entry"${b.mode !== 'add' ? ' selected' : ''}>${e(t('fb_ed_mode_entry'))}</option><option value="add"${b.mode === 'add' ? ' selected' : ''}>${e(t('fb_ed_mode_add'))}</option></select></label>` + cb('fe_minus', b.minus, t('fb_ed_minus'));
      if (b.type === 'number') x += inp('fe_unit', t('fb_ed_unit'), b.unit, 12) + inp('fe_min', t('fb_ed_min'), b.min, 16, ' inputmode="decimal"') + inp('fe_max', t('fb_ed_max'), b.max, 16, ' inputmode="decimal"');
      if (b.type === 'select') x += `<label class="fbf fbwide"><span>${e(t('fb_ed_opts'))}</span><textarea class="fe_opts" rows="3">${e((b.opts || []).join('\n'))}</textarea></label>` + cb('fe_multi', b.multi, t('fb_ed_multi'));
      if (b.type === 'scale') x += `<label class="fbf"><span>${e(t('fb_ed_rng'))}</span><select class="fe_rng"><option value="5"${b.rng !== '10' ? ' selected' : ''}>${e(t('fb_ed_rng5'))}</option><option value="10"${b.rng === '10' ? ' selected' : ''}>${e(t('fb_ed_rng10'))}</option></select></label>` + inp('fe_lo', t('fb_ed_lo'), b.lo, 24) + inp('fe_hi', t('fb_ed_hi'), b.hi, 24);
    }
    const kind = b ? t('fb_type_' + b.type) : t('fb_ed_builtin');
    return `<details class="fbed${hid ? ' off' : ''}" data-id="${e(b ? b.id : it.k)}"${b && b.isNew ? ' open' : ''}><summary><span class="fbedn">${e(nm)}</span> <small>${e(kind)}${hid ? ' · ' + e(t('fb_ed_hidden')) : ''}${(b ? b.req : s.req) ? ' · ' + e(t('fb_ed_req')) : ''}</small></summary>
      <div class="fbedg">${inp('fe_l', t('fb_ed_name'), nm, b ? 40 : 40)}${(b || it.help) ? inp('fe_h', t('fb_ed_help'), b ? b.h : s.h, 160) : ''}
        ${(b ? b.type !== 'counter' : it.req) ? cb('fe_req', b ? b.req : s.req, t('fb_ed_req')) : ''}${cb('fe_show', !hid, t('fb_ed_shown'))}${x}
        ${b ? `<button type="button" class="btn fe_del">🗑 ${e(t('fb_ed_del', { l: b.l }))}</button>` : ''}</div></details>`;
  }
  /* d = {blocks, sec}, items = [{k, l, req, help} | {b}] in Anzeige-Reihenfolge; hk.change(), hk.say(msg), hk.add(type) */
  function editor(box, d, items, hk) {
    const addable = TYPES.map(x => `<option value="${x}">${e(t('fb_type_' + x))}</option>`).join('');
    box.innerHTML = `<div class="fbeds"><span class="laysl" id="fbedl">${e(t('fb_ed_title'))}</span><p class="hint fbhint">${e(t('fb_ed_hint'))}</p>
      <div class="fbedl" role="list" aria-labelledby="fbedl">${items.map(it => `<div role="listitem">${edRow(it, d)}</div>`).join('')}</div>
      <div class="fbadd"><select class="fe_type" aria-label="${e(t('fb_ed_type'))}"><option value="pills">${e(t('fb_type_pills'))}</option>${addable}</select><button type="button" class="btn fe_add">＋ ${e(t('fb_ed_add'))}</button></div></div>`;
    box.querySelectorAll('.fbed').forEach(row => {
      const id = row.dataset.id, b = d.blocks.find(x => x.id === id), s = b ? null : (d.sec[id] = d.sec[id] || {}), q = c => row.querySelector('.' + c);
      const upd = () => { const sm = row.querySelector('summary .fbedn'); sm.textContent = (b ? b.l : s.l) || (items.find(x => x.k === id) || {}).l || ''; row.classList.toggle('off', b ? !!b.hide : !!s.hide); hk.change(id); };
      q('fe_l').addEventListener('input', ev => { const v = ev.target.value.trim().slice(0, 40); if (b) { if (v) b.l = v; } else s.l = v && v !== (items.find(x => x.k === id) || {}).l ? v : ''; upd(); });
      const hh = q('fe_h'); if (hh) hh.addEventListener('input', () => { if (b) b.h = hh.value.trim(); else s.h = hh.value.trim(); hk.change(id); });
      const rq = q('fe_req'); if (rq) rq.onchange = () => { if (b) b.req = rq.checked; else s.req = rq.checked; hk.change(id); };
      q('fe_show').onchange = ev => { if (b) b.hide = !ev.target.checked; else s.hide = !ev.target.checked; upd(); hk.say(t(ev.target.checked ? 'fb_ed_shown_s' : 'fb_ed_hidden_s', { l: b ? b.l : (s.l || id) })); };
      if (!b) return;
      const on = (c, f) => { const x = q(c); if (x) x.addEventListener(x.tagName === 'SELECT' || x.type === 'checkbox' ? 'change' : 'input', () => { f(x); hk.change(id); }); };
      on('fe_ml', x => { b.ml = x.checked; row.querySelector('.fe_mlon').hidden = !b.ml; row.querySelector('.fe_mloff').hidden = b.ml; }); on('fe_ph', x => { b.ph = x.value.trim().slice(0, 80); }); on('fe_rows', x => { b.rows = +x.value; }); on('fe_sug', x => { b.sug = x.checked; });
      on('fe_kind', x => { b.kind = x.value === 'dt' ? undefined : x.value; row.querySelector('.fe_secw').hidden = x.value === 'date'; }); on('fe_def', x => { b.def = x.value || undefined; }); on('fe_nonow', x => { b.nonow = !x.checked; }); on('fe_sec', x => { b.sec = x.checked; }); on('fe_mode', x => { b.mode = x.value; }); on('fe_minus', x => { b.minus = x.checked; });
      on('fe_unit', x => { b.unit = x.value.trim(); });
      on('fe_tmax', x => { const n = readNum(x.value), bad = Number.isNaN(n) || (n != null && (n < 10 || n > 500)); x.setAttribute('aria-invalid', String(bad)); if (!bad) b.max = n == null ? undefined : Math.round(n); });
      for (const k of ['min', 'max']) on('fe_' + k, x => { const n = readNum(x.value); x.setAttribute('aria-invalid', String(Number.isNaN(n))); b[k] = n == null || Number.isNaN(n) ? null : n; });
      on('fe_opts', x => { b.opts = [...new Set(x.value.split('\n').map(y => y.trim()).filter(Boolean))].slice(0, 30); }); on('fe_multi', x => { b.multi = x.checked; });
      on('fe_rng', x => { b.rng = x.value; }); on('fe_lo', x => { b.lo = x.value.trim(); }); on('fe_hi', x => { b.hi = x.value.trim(); });
      q('fe_del').onclick = () => { if (!confirm(t('fb_ed_del_q', { l: b.l }))) return; b.del = true; hk.say(t('fb_ed_deleted', { l: b.l })); hk.change(id, true); };
    });
    box.querySelector('.fe_add').onclick = () => {
      const ty = box.querySelector('.fe_type').value;
      if (ty === 'pills') { hk.add('pills'); return; }
      if (d.blocks.filter(x => !x.del).length >= S.max) { alert(t('fb_ed_limit', { n: S.max })); return; }
      const b = newDef(ty); d.blocks.push(b); hk.say(t('fb_ed_added', { l: b.l })); hk.add(ty, b);
    };
  }
  /* Entwurf → zum Speichern (ohne Hilfsfelder) */
  const strip = d => ({ blocks: d.blocks.filter(b => !(b.isNew && b.del)).map(b => { const o = Object.assign({}, b); delete o.isNew; return o; }), sec: d.sec });
  /* ---------- Vorlagen ---------- */
  function tplBox(box, cur, onPick, later) {
    box.innerHTML = `<p class="fbtplh"><b>${e(t('fb_tpl_title'))}</b> ${e(t('fb_tpl_h'))}</p><div class="fbtpls">${S.tpls.map(x => `<button type="button" class="fbtpl${cur === x ? ' on' : ''}" data-tpl="${x}" aria-pressed="${cur === x}"><b>${e(t('fb_tpl_' + x))}</b><small>${e(t('fb_tpl_' + x + '_h'))}</small></button>`).join('')}</div>${later ? `<button type="button" class="linkbtn fbtpll">${e(t('fb_tpl_later'))}</button>` : ''}`;
    box.querySelectorAll('.fbtpl').forEach(x => x.onclick = () => onPick(x.dataset.tpl));
    const l = box.querySelector('.fbtpll'); if (l && later) l.onclick = later;
  }
  return { TYPES, ROLES, S, setup, load, isId, byId, active, visible, isEmpty, fmt, compact, render, countShow, check, chart, editor, strip, newDef, tplBox, readNum };
})();
