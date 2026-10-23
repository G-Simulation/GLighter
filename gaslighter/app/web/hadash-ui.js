/* Dashboard-Vorlage für Home Assistant – Bedienteil, in GLighter, GReport und GJarvis gleich.
   HADash.mount(box, { lang, get: 'hadash', post: 'hadash_apply', preview: 'hadash', parts: { key: 'Beschriftung' }, icon })
   Ändert in Home Assistant nur etwas nach „In Home Assistant anlegen“ (und bei vorhandenem Dashboard erst nach „Ersetzen“). */
(function () {
  const L = {
    de: {
      intro: 'Legt in Home Assistant ein fertiges Dashboard mit den Entitäten dieser App an. Du kannst es danach in Home Assistant frei weiter bearbeiten.',
      title: 'Name', url: 'Adresse', url_h: 'Kleinbuchstaben und mindestens ein Bindestrich; steht danach in der Adresszeile von Home Assistant', sidebar: 'In der Seitenleiste zeigen', admin: 'Nur für Administratoren',
      parts: 'Bereiche', create: 'In Home Assistant anlegen', update: 'Dashboard ersetzen', yaml: 'Als YAML anzeigen (zum Kopieren)', copy: 'Kopieren', copied: 'Kopiert',
      exists: 'Es gibt schon ein Dashboard mit dieser Adresse. Ersetzen überschreibt Änderungen, die du dort gemacht hast. Die bisherige Fassung wird vorher in der App gesichert.', foreign: 'Achtung: Dieses Dashboard hat nicht diese App angelegt. Ersetzen überschreibt seinen Inhalt (die bisherige Fassung wird vorher gesichert). Sichtbarkeit und Name bleiben, wie sie sind.', replace: 'Ja, ersetzen', cancel: 'Abbrechen',
      ok_new: 'Dashboard angelegt.', ok_rep: 'Dashboard ersetzt.', open: 'Dashboard öffnen', busy: 'Wird angelegt …', loading: 'Wird geladen …',
      bad_url: 'Die Adresse braucht Kleinbuchstaben, Ziffern und mindestens einen Bindestrich (z. B. gsim-notizen).', no_entities: 'Keine Entitäten dieser App gefunden. Ist MQTT eingeschaltet und die App mit Home Assistant verbunden?',
      no_ha: 'Home Assistant ist nicht erreichbar. Die YAML-Vorlage kannst du trotzdem kopieren und in Home Assistant unter Dashboard → Bearbeiten → Rohdaten-Editor einfügen.',
      err: 'Hat nicht geklappt: {e}', found: '{n} Entitäten gefunden', manual: 'Von Hand: In Home Assistant ein neues Dashboard anlegen, „Bearbeiten“ → ⋮ → „Rohdaten-Konfigurationseditor“ und die YAML einfügen.'
    },
    en: {
      intro: 'Creates a ready-made dashboard with this app’s entities in Home Assistant. You can keep editing it in Home Assistant afterwards.',
      title: 'Name', url: 'Address', url_h: 'Lower case with at least one hyphen; appears in the Home Assistant address bar', sidebar: 'Show in sidebar', admin: 'Administrators only',
      parts: 'Sections', create: 'Create in Home Assistant', update: 'Replace dashboard', yaml: 'Show as YAML (to copy)', copy: 'Copy', copied: 'Copied',
      exists: 'A dashboard with this address already exists. Replacing it overwrites changes you made there. The previous version is saved in the app first.', foreign: 'Note: this dashboard was not created by this app. Replacing overwrites its content (the previous version is saved first). Visibility and name stay as they are.', replace: 'Yes, replace', cancel: 'Cancel',
      ok_new: 'Dashboard created.', ok_rep: 'Dashboard replaced.', open: 'Open dashboard', busy: 'Creating …', loading: 'Loading …',
      bad_url: 'The address needs lower case letters, digits and at least one hyphen (e.g. gsim-notes).', no_entities: 'No entities of this app found. Is MQTT on and the app connected to Home Assistant?',
      no_ha: 'Home Assistant is not reachable. You can still copy the YAML and paste it in Home Assistant under Dashboard → Edit → Raw configuration editor.',
      err: 'Did not work: {e}', found: '{n} entities found', manual: 'By hand: create a new dashboard in Home Assistant, “Edit” → ⋮ → “Raw configuration editor” and paste the YAML.'
    }
  };
  let uid = 0;
  const CSS = `.hadash{display:grid;gap:10px}.hadash .hd-intro{margin:0}
.hadash .hd-grid{display:grid;grid-template-columns:max-content minmax(0,1fr);gap:8px 12px;align-items:center}
.hadash .hd-grid input{width:100%;box-sizing:border-box;min-height:40px}.hadash .hd-grid small{display:block;margin-top:2px;opacity:.85}
.hadash .hd-chk{display:flex;align-items:center;gap:10px;min-height:40px;cursor:pointer}
.hadash .hd-chk input{width:22px;height:22px;margin:0;flex:none}
.hadash .hd-parts{border:1px solid currentColor;border-color:color-mix(in srgb,currentColor 25%,transparent);border-radius:8px;padding:6px 12px;margin:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr))}
.hadash .hd-row{display:flex;gap:8px;flex-wrap:wrap}.hadash button{min-height:44px;padding:0 16px}
.hadash .hd-ask{border-left:4px solid #b8860b;padding:4px 12px}.hadash .hd-ask p{margin:4px 0 8px}
.hadash .hd-msg{margin:0;min-height:1.4em}.hadash .hd-msg.bad{color:#b42318}
.hadash pre{max-height:320px;overflow:auto;padding:10px;border-radius:8px;background:color-mix(in srgb,currentColor 7%,transparent);font-size:12px;white-space:pre;margin:8px 0 0}
.hadash summary{cursor:pointer;min-height:32px;display:flex;align-items:center}
@media (max-width:480px){.hadash .hd-grid{grid-template-columns:1fr}}
@media (prefers-color-scheme:dark){.hadash .hd-msg.bad{color:#ff8a80}}`;
  function style() {
    if (document.getElementById('hadash-css')) return;
    const s = document.createElement('style'); s.id = 'hadash-css'; s.textContent = CSS; document.head.appendChild(s);
  }
  function mount(box, o) {
    const T = L[o.lang === 'en' ? 'en' : 'de'], id = 'hd' + (++uid);
    const fmt = (s, v) => s.replace(/\{(\w+)\}/g, (_, k) => v[k] != null ? v[k] : '');
    const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
    style(); box.classList.add('hadash');
    box.innerHTML = `<p class="hd-intro">${esc(T.intro)}</p>
      <div class="hd-grid">
        <label for="${id}t">${esc(T.title)}</label><input id="${id}t" type="text" maxlength="60" autocomplete="off">
        <label for="${id}u">${esc(T.url)}</label><div><input id="${id}u" type="text" maxlength="40" autocomplete="off" spellcheck="false" aria-describedby="${id}uh"><small id="${id}uh">${esc(T.url_h)}</small></div>
      </div>
      <label class="hd-chk"><input type="checkbox" id="${id}s"> ${esc(T.sidebar)}</label>
      <label class="hd-chk"><input type="checkbox" id="${id}a"> ${esc(T.admin)}</label>
      <fieldset class="hd-parts"><legend>${esc(T.parts)}</legend>${Object.entries(o.parts).map(([k, v]) => `<label class="hd-chk"><input type="checkbox" value="${esc(k)}"> ${esc(v)}</label>`).join('')}</fieldset>
      <div class="hd-row"><button type="button" class="hd-go pri btn primary">${esc(T.create)}</button></div>
      <div class="hd-ask" hidden><p>${esc(T.exists)}</p><div class="hd-row"><button type="button" class="hd-rep btn danger">${esc(T.replace)}</button><button type="button" class="hd-no btn">${esc(T.cancel)}</button></div></div>
      <p class="hd-msg" role="status" aria-live="polite"></p>
      <details class="hd-yaml"><summary>${esc(T.yaml)}</summary><small>${esc(T.manual)}</small><div class="hd-row"><button type="button" class="hd-copy btn">${esc(T.copy)}</button></div><pre tabindex="0"></pre></details>`;
    const q = s => box.querySelector(s), ti = q('#' + id + 't'), ur = q('#' + id + 'u'), sb = q('#' + id + 's'), ad = q('#' + id + 'a');
    const msg = q('.hd-msg'), go = q('.hd-go'), ask = q('.hd-ask'), pre = q('pre');
    const say = (s, bad, link) => { msg.classList.toggle('bad', !!bad); msg.innerHTML = esc(s) + (link ? ` <a href="${esc(link)}" target="_top">${esc(T.open)}</a>` : ''); };
    const val = () => ({ title: ti.value, url: ur.value.trim().toLowerCase(), sidebar: sb.checked, admin: ad.checked,
      parts: [...box.querySelectorAll('.hd-parts input:checked')].map(x => x.value) });
    const post = (u, d) => fetch(u, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(d) }).then(r => r.json());
    let tm = 0;
    const preview = async () => {
      try {
        const j = await post(o.preview || o.get, val());
        pre.textContent = j.yaml || '';
        if (!j.available) say(T.no_ha, false); else if (j.error) say(fmt(T.err, { e: j.error }), true); else if (!j.n_entities) say(T.no_entities, true); else if (!msg.dataset.keep) say(fmt(T.found, { n: j.n_entities }));
        go.textContent = j.exists ? T.update : T.create; go.disabled = !j.available || !j.valid_url;
        if (!j.valid_url) say(T.bad_url, true);
      } catch (e) { say(fmt(T.err, { e: e.message || e }), true); }
    };
    const later = () => { clearTimeout(tm); delete msg.dataset.keep; tm = setTimeout(preview, 350); };
    box.addEventListener('input', later); box.addEventListener('change', later);
    const apply = async overwrite => {
      ask.hidden = true; go.disabled = true; say(T.busy);
      try {
        const r = await post(o.post, Object.assign(val(), { overwrite }));
        if (r.exists) { ask.querySelector('p').textContent = r.own === false ? T.foreign : T.exists; ask.hidden = false; q('.hd-rep').focus(); say(''); }
        else if (r.ok) { msg.dataset.keep = 1; say(r.created ? T.ok_new : T.ok_rep, false, r.url); }
        else say(T[r.error] || fmt(T.err, { e: r.error || '?' }), true);
      } catch (e) { say(fmt(T.err, { e: e.message || e }), true); }
      go.disabled = false; preview();
    };
    go.onclick = () => apply(false);
    q('.hd-rep').onclick = () => apply(true);
    q('.hd-no').onclick = () => { ask.hidden = true; go.focus(); };
    q('.hd-copy').onclick = async e => {
      try { await navigator.clipboard.writeText(pre.textContent); }
      catch (_) { const r = document.createRange(); r.selectNodeContents(pre); const s = getSelection(); s.removeAllRanges(); s.addRange(r); document.execCommand('copy'); }
      e.target.textContent = T.copied; setTimeout(() => { e.target.textContent = T.copy; }, 1500);
    };
    say(T.loading);
    fetch(o.get, { cache: 'no-store' }).then(r => r.json()).then(j => {
      const p = j.prefs || {};
      ti.value = p.title || ''; ur.value = p.url || ''; sb.checked = p.sidebar !== false; ad.checked = !!p.admin;
      box.querySelectorAll('.hd-parts input').forEach(x => { x.checked = (p.parts || Object.keys(o.parts)).includes(x.value); });
      preview();
    }).catch(e => say(fmt(T.err, { e: e.message || e }), true));
  }
  window.HADash = { mount };
})();
