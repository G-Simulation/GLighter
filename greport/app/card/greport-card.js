// GReport-Karte für Home Assistant.
// Das Add-on kopiert diese Datei beim Start nach /config/www/greport/ und trägt sie als Dashboard-Ressource ein.
// Danach steht „GReport“ unter „Karte hinzufügen“ → „Nach Karte“. Funktioniert für alle Benutzer, auch ohne Administratorrechte.
const GR_SKIP = ['select.greport_schnellwahl'];
const GR_ORDER = ['woher', 'was', 'wie_stark', 'folgen', 'massnahmen', 'sonstiges', 'eigene'];

class GReportCard extends HTMLElement {
  setConfig(c) { this._c = Object.assign({}, c || {}); this._sig = null; }
  static getStubConfig() { return {}; }
  getCardSize() { return 8; }
  getGridOptions() { return { columns: 12, rows: 'auto', min_columns: 6 }; }
  _de() { return String((this._hass && this._hass.language) || 'de').startsWith('de'); }
  _name(s) { return String(s.attributes.friendly_name || s.entity_id).replace(/^GReport\s+/i, ''); }
  _sel() {
    return Object.keys(this._hass.states)
      .filter(e => e.startsWith('select.greport_') && !GR_SKIP.includes(e))
      .sort((a, b) => GR_ORDER.indexOf(a.slice(15)) - GR_ORDER.indexOf(b.slice(15)));
  }
  _call(d, s, data) { return this._hass.callService(d, s, data); }

  _build(sel) {
    const h = this._hass, de = this._de(), st = e => h.states[e];
    const r = this.shadowRoot || this.attachShadow({ mode: 'open' });
    const esc = t => String(t).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
    const lab = (e, f) => esc(st(e) ? this._name(st(e)) : f);
    const title = esc(this._c.title || (de ? 'GReport – Notiz erfassen' : 'GReport – add note'));
    if (!st('text.greport_notiz')) {
      r.innerHTML = `<ha-card style="display:block;padding:16px">${de
        ? 'GReport wurde nicht gefunden. Läuft das Add-on GReport und ist MQTT eingeschaltet?'
        : 'GReport not found. Is the GReport add-on running with MQTT enabled?'}</ha-card>`;
      return;
    }
    r.innerHTML = `<style>
      ha-card{padding:16px;display:block}
      h2{margin:0 0 12px;font-size:1.2em;font-weight:500}
      label{display:block;font-size:.85em;color:var(--secondary-text-color);margin:10px 0 4px}
      textarea,input,select{width:100%;box-sizing:border-box;padding:10px;border-radius:8px;border:1px solid var(--divider-color);background:var(--card-background-color);color:var(--primary-text-color);font:inherit}
      textarea{min-height:80px;resize:vertical}
      .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:0 12px}
      button{margin-top:16px;width:100%;padding:12px;border:0;border-radius:8px;background:var(--primary-color);color:var(--text-primary-color,#fff);font-size:1em;cursor:pointer}
      .info{margin-top:10px;font-size:.85em;color:var(--secondary-text-color)}
      .ok{color:var(--success-color,green)}
    </style>
    <ha-card><h2>${title}</h2>
      <label>${lab('text.greport_notiz', de ? 'Notiz' : 'Note')}</label><textarea id="notiz"></textarea>
      <div class="grid">${sel.map(e => `<div><label>${lab(e, e)}</label><select data-e="${e}"></select></div>`).join('')}</div>
      <label>${lab('text.greport_zeuge', de ? 'Zeuge' : 'Witness')}</label><input id="zeuge">
      <button id="save">${lab('button.greport_speichern', de ? 'Speichern' : 'Save')}</button>
      <div class="info" id="info"></div>
    </ha-card>`;
    const q = id => r.getElementById(id);
    const setText = (e, v) => this._call('text', 'set_value', { entity_id: e, value: v });
    q('notiz').addEventListener('change', ev => setText('text.greport_notiz', ev.target.value));
    q('zeuge').addEventListener('change', ev => setText('text.greport_zeuge', ev.target.value));
    r.querySelectorAll('select').forEach(el => el.addEventListener('change', ev =>
      this._call('select', 'select_option', { entity_id: el.dataset.e, option: ev.target.value })));
    q('save').addEventListener('click', async () => {
      const n = q('notiz'), z = q('zeuge'), i = q('info');
      try {
        await setText('text.greport_notiz', n.value);
        await setText('text.greport_zeuge', z.value);
        await this._call('button', 'press', { entity_id: 'button.greport_speichern' });
        n.value = ''; z.value = '';
        i.className = 'info ok'; i.textContent = de ? 'Gespeichert ✓' : 'Saved ✓';
      } catch (err) {
        i.className = 'info'; i.textContent = (de ? 'Fehler: ' : 'Error: ') + (err && err.message || err);
      }
      setTimeout(() => { i.className = 'info'; this._upd(); }, 3000);
    });
  }

  _upd() {
    const h = this._hass, r = this.shadowRoot; if (!h || !r) return;
    const st = e => h.states[e], de = this._de();
    r.querySelectorAll('select').forEach(el => {
      const s = st(el.dataset.e); if (!s) return;
      const opts = s.attributes.options || [], sig = opts.join('|');
      if (el.dataset.o !== sig) {
        el.innerHTML = '';
        opts.forEach(o => { const op = document.createElement('option'); op.textContent = o; el.appendChild(op); });
        el.dataset.o = sig;
      }
      if (r.activeElement !== el) el.value = s.state;
    });
    const n = st('text.greport_notiz'), ta = r.getElementById('notiz');
    if (n && ta && n.attributes.max) ta.maxLength = n.attributes.max;
    const l = st('sensor.greport_letzte_notiz'), c = st('sensor.greport_notizen_heute'), i = r.getElementById('info');
    if (i && !i.classList.contains('ok'))
      i.textContent = `${de ? 'Heute' : 'Today'}: ${c ? c.state : '–'} · ${de ? 'Letzte' : 'Last'}: ${l ? l.state : '–'}`;
  }

  set hass(h) {
    this._hass = h;
    const sel = this._sel(), sig = sel.join(',') + '|' + !!h.states['text.greport_notiz'] + '|' + h.language;
    if (sig !== this._sig) { this._sig = sig; this._build(sel); }
    this._upd();
  }
}

customElements.get('greport-card') || customElements.define('greport-card', GReportCard);
window.customCards = window.customCards || [];
if (!window.customCards.some(c => c.type === 'greport-card')) {
  window.customCards.push({
    type: 'greport-card', name: 'GReport', preview: true,
    description: 'Notiz erfassen: Notiz, Woher, Was, Wie stark, Folgen, Maßnahmen, Zeuge, Speichern / Add a note',
  });
}
