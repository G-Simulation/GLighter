/* GasLighter – Handbuch: Kapitel aus hb_inhalt.js (Markdown, erzeugt aus handbuch/<Sprache>/*.md),
   Inhaltsverzeichnis, Suche, Verweise #kapitel/anker. Läuft ohne Internet. */
(function () {
'use strict';
const $ = id => document.getElementById(id);
const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const Q = new URLSearchParams(location.search);
let lang = (Q.get('lang') || (navigator.language || 'de')).toLowerCase().startsWith('en') ? 'en' : 'de';
const th = Q.get('theme'); if (th === 'dark' || th === 'light') document.documentElement.setAttribute('data-theme', th);
const UI = {
  de: { title: 'Handbuch', search: 'Im Handbuch suchen …', print: '🖨 Drucken', other: 'English', prev: '← ', next: ' →', none: 'Nichts gefunden.', hits: '{n} Treffer für „{q}“', toc: 'Inhalt' },
  en: { title: 'Manual', search: 'Search the manual …', print: '🖨 Print', other: 'Deutsch', prev: '← ', next: ' →', none: 'Nothing found.', hits: '{n} results for “{q}”', toc: 'Contents' }
};
const u = (k, v) => { let s = UI[lang][k]; if (v) for (const x in v) s = s.split('{' + x + '}').join(v[x]); return s; };
const slugify = s => s.toLowerCase().replace(/[äöüß]/g, c => ({ 'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'ß': 'ss' }[c])).replace(/<[^>]+>/g, '').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
function chapters() { return (window.HB && window.HB[lang]) || []; }

/* ---------- kleines Markdown ---------- */
function inline(s) {
  let o = esc(s);
  o = o.replace(/`([^`]+)`/g, (m, c) => '<code>' + c + '</code>');
  o = o.replace(/!\[([^\]]*)\]\(([^)\s]+)\)/g, (m, a, src) => '<img src="hb/' + src.replace(/^.*\//, '').replace('{lang}', lang) + '" alt="' + a + '" loading="lazy">' + (a ? '<div class="cap">' + a + '</div>' : ''));
  o = o.replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, (m, t, h) => '<a href="' + h + '"' + (/^https?:/.test(h) ? ' target="_blank" rel="noopener"' : '') + '>' + t + '</a>');
  o = o.replace(/\*\*([^*]+)\*\*/g, '<b>$1</b>').replace(/(^|[^*])\*([^*\s][^*]*)\*/g, '$1<i>$2</i>');
  o = o.replace(/\[\[([^\]]+)\]\]/g, '<kbd>$1</kbd>');
  o = o.replace(/\s*\{#([a-z0-9_-]+)\}/g, '<span id="$1"></span>');   // Anker mitten im Text (z. B. in Listen)
  return o;
}
function md(src) {
  const L = src.replace(/\r/g, '').split('\n'), out = [], heads = [];
  let i = 0;
  const para = [];
  const flush = () => { if (para.length) { out.push('<p>' + inline(para.join(' ')) + '</p>'); para.length = 0; } };
  while (i < L.length) {
    const l = L[i];
    if (/^```/.test(l)) { flush(); const b = []; i++; while (i < L.length && !/^```/.test(L[i])) b.push(L[i++]); i++; out.push('<pre><code>' + esc(b.join('\n')) + '</code></pre>'); continue; }
    let m = /^(#{1,3})\s+(.*?)(?:\s*\{#([a-z0-9_-]+)\})?\s*$/.exec(l);
    if (m) { flush(); const n = m[1].length, id = m[3] || slugify(m[2]); heads.push({ n, id, t: m[2] }); out.push(`<h${n} id="${id}">${inline(m[2])}</h${n}>`); i++; continue; }
    if (/^\s*$/.test(l)) { flush(); i++; continue; }
    if (/^>\s?/.test(l)) { flush(); const b = []; while (i < L.length && /^>\s?/.test(L[i])) b.push(L[i++].replace(/^>\s?/, '')); const w = /^\s*(⚠|\*\*Achtung|\*\*Wichtig|\*\*Warning|\*\*Important)/.test(b[0]); out.push('<blockquote' + (w ? ' class="warn"' : '') + '>' + b.map(x => '<p>' + inline(x) + '</p>').join('') + '</blockquote>'); continue; }
    if (/^\|/.test(l)) { flush(); const rows = []; while (i < L.length && /^\|/.test(L[i])) rows.push(L[i++]); const cells = r => r.replace(/^\||\|$/g, '').split('|').map(c => c.trim());
      const hd = cells(rows[0]), body = rows.slice(/^\|\s*:?-/.test(rows[1] || '') ? 2 : 1);
      out.push('<table><tr>' + hd.map(c => '<th>' + inline(c) + '</th>').join('') + '</tr>' + body.map(r => '<tr>' + cells(r).map(c => '<td>' + inline(c) + '</td>').join('') + '</tr>').join('') + '</table>'); continue; }
    if (/^\s*([-*]|\d+\.)\s+/.test(l)) { flush(); const ol = /^\s*\d+\./.test(l), items = [];
      while (i < L.length && (/^\s*([-*]|\d+\.)\s+/.test(L[i]) || (/^\s{2,}\S/.test(L[i]) && items.length))) { if (/^\s*([-*]|\d+\.)\s+/.test(L[i])) items.push(L[i].replace(/^\s*([-*]|\d+\.)\s+/, '')); else items[items.length - 1] += ' ' + L[i].trim(); i++; }
      out.push((ol ? '<ol>' : '<ul>') + items.map(x => '<li>' + inline(x) + '</li>').join('') + (ol ? '</ol>' : '</ul>')); continue; }
    para.push(l.trim()); i++;
  }
  flush();
  return { html: out.join('\n'), heads };
}

/* ---------- Anzeige ---------- */
let CUR = null;
function toc(curSlug, heads) {
  $('toc').innerHTML = chapters().map((c, k) => {
    const on = c.slug === curSlug;
    const sub = on ? '<div class="sub">' + heads.filter(h => h.n === 2).map(h => `<a href="#${c.slug}/${h.id}">${inline(h.t)}</a>`).join('') + '</div>' : '';
    return `<a href="#${c.slug}" class="${on ? 'cur' : ''}">${k + 1}. ${esc(c.title)}</a>${sub}`;
  }).join('');
}
function show(slug, anchor) {
  const L = chapters(); if (!L.length) { $('out').textContent = '–'; return; }
  const k = Math.max(0, L.findIndex(c => c.slug === slug)), c = L[k];
  const r = md(c.md);
  CUR = c.slug;
  const prev = L[k - 1], next = L[k + 1];
  $('out').innerHTML = `<article>${r.html.replace(/^<h1 id="([^"]*)">/, `<h1 id="$1"><span class="no">${k + 1}.</span>`)}
    <div class="nav2"><span>${prev ? `<a href="#${prev.slug}">${u('prev')}${esc(prev.title)}</a>` : ''}</span><span>${next ? `<a href="#${next.slug}">${esc(next.title)}${u('next')}</a>` : ''}</span></div></article>`;
  toc(c.slug, r.heads);
  document.title = c.title + ' – ' + u('title');
  $('toc').classList.remove('open');
  requestAnimationFrame(() => { const t = anchor && document.getElementById(anchor); if (t) t.scrollIntoView({ block: 'start' }); else window.scrollTo(0, 0); });
}
function route() {
  const h = decodeURIComponent(location.hash.slice(1));
  if (h.startsWith('suche=')) return search(h.slice(6));
  const [s, a] = h.split('/');
  show(s || (chapters()[0] || {}).slug, a);
}
function search(q) {
  q = q.trim(); if (!q) return route();
  const words = q.toLowerCase().split(/\s+/).filter(Boolean), hits = [];
  for (const c of chapters()) {
    let sec = { id: '', t: c.title, txt: [] }; const secs = [sec];
    for (const l of c.md.split('\n')) { const m = /^(#{2,3})\s+(.*?)(?:\s*\{#([a-z0-9_-]+)\})?\s*$/.exec(l); if (m) { sec = { id: m[3] || slugify(m[2]), t: m[2], txt: [] }; secs.push(sec); } else sec.txt.push(l); }
    for (const s of secs) {
      const all = (s.t + ' ' + s.txt.join(' ')).toLowerCase();
      if (words.every(w => all.includes(w))) {
        const plain = s.txt.join(' ').replace(/\]\([^)]*\)/g, ']').replace(/\{#[a-z0-9_-]+\}/g, '').replace(/[#*`>|!\[\]()]/g, ' ').replace(/\s+/g, ' ');
        const p = Math.max(0, plain.toLowerCase().indexOf(words[0]) - 60);
        hits.push({ c, s, snip: plain.slice(p, p + 200), score: (s.t.toLowerCase().includes(words[0]) ? 2 : 0) + words.length });
      }
    }
  }
  hits.sort((a, b) => b.score - a.score);
  const hl = x => { let o = esc(x); for (const w of words) o = o.replace(new RegExp('(' + w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ')', 'gi'), '<mark>$1</mark>'); return o; };
  $('out').innerHTML = `<div class="res"><h1>${esc(u('hits', { n: hits.length, q }))}</h1>` + (hits.length ? hits.slice(0, 60).map(h =>
    `<div class="hit" data-h="${esc(h.c.slug + (h.s.id ? '/' + h.s.id : ''))}"><b>${esc(h.c.title)}${h.s.id ? ' › ' + hl(h.s.t) : ''}</b><small>… ${hl(h.snip)} …</small></div>`).join('') : `<p>${esc(u('none'))}</p>`) + '</div>';
  $('out').querySelectorAll('.hit').forEach(d => d.onclick = () => { location.hash = d.dataset.h; });
  toc(CUR, []);
}
function ui() {
  document.documentElement.lang = lang;
  $('ttl').textContent = '📖 ' + u('title'); $('q').placeholder = u('search'); $('bprint').textContent = u('print'); $('blang').textContent = u('other');
  $('tocbtn').title = u('toc');
}
let qt = 0;
$('q').addEventListener('input', () => { clearTimeout(qt); qt = setTimeout(() => { const v = $('q').value.trim(); if (v.length >= 2) history.replaceState(null, '', '#suche=' + encodeURIComponent(v)), search(v); else if (!v) route(); }, 200); });
$('q').addEventListener('keydown', e => { if (e.key === 'Escape') { $('q').value = ''; route(); } });
$('bprint').onclick = () => window.print();
$('blang').onclick = () => { lang = lang === 'de' ? 'en' : 'de'; ui(); show(CUR); };   // gleiche Kapitel-Kennung in beiden Sprachen
$('tocbtn').onclick = () => $('toc').classList.toggle('open');
window.addEventListener('hashchange', route);
ui(); route();
})();
