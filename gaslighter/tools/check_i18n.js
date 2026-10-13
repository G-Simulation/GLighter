// Prüft, ob alle Texte der Oberfläche auf Deutsch und Englisch vorhanden sind. Aufruf im Ordner app/web: node ../../tools/check_i18n.js
const fs=require('fs'); const src=fs.readFileSync('i18n.js','utf8'); const I18N=new Function('window',src+';return window.I18N')({});
const app=fs.readFileSync('app.js','utf8'); const html=fs.readFileSync('index.html','utf8');
const de=I18N.de,en=I18N.en; const miss=new Set();
for(const m of app.matchAll(/\bt\('([a-z0-9_]+)'/g)) { if(m[1].endsWith('_')) continue; if(!(m[1] in de)) miss.add('de:'+m[1]); if(!(m[1] in en)) miss.add('en:'+m[1]); }
for(const m of html.matchAll(/data-i[a-z]*="([a-z0-9_]+)"/g)) { if(!(m[1] in de)) miss.add('de:'+m[1]); if(!(m[1] in en)) miss.add('en:'+m[1]); }
for(const m of app.matchAll(/\['([a-z_]+)', '(time|num|chk|sel|text|range|device|port|window)'/g)) for(const p of ['f_']) { const k=p+m[1]; if(!(k in de)) miss.add('de:'+k); if(!(k in en)) miss.add('en:'+k); }
console.log([...miss].sort().join('\n'));
const dk=Object.keys(de), ek=Object.keys(en); console.log('only de', dk.filter(k=>!(k in en))); console.log('only en', ek.filter(k=>!(k in de)));
if (miss.size || dk.some(k => !(k in en)) || ek.some(k => !(k in de))) process.exit(1);
