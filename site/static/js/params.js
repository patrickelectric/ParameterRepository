import MiniSearch from './vendor/minisearch.js';

const idx = JSON.parse(document.getElementById('idx').textContent);
const $ = id => document.getElementById(id);
const table = $('params'), tbody = table.querySelector('tbody');
const cache = new Map();
let rows = [], ms, hits = [], shown = 0, group = '', gen = 0;

const fmtMap = m => Object.entries(m).map(([k, v]) => `${k}: ${v}`).join(', ');
const td = (text, cls) => { const e = document.createElement('td'); e.textContent = text; if (cls) e.className = cls; return e; };

function load(file) {
  if (!cache.has(file)) cache.set(file, fetch(`${table.dataset.base}/${file}.json`).then(r => {
    if (!r.ok) throw new Error(`${file}: ${r.status}`);
    return r.json();
  }));
  return cache.get(file);
}

function fillVersions() {
  $('version').innerHTML = idx[$('vehicle').value].map((v, i) => `<option value="${v}">${v}${i ? '' : ' (latest)'}</option>`).join('');
}

function fillChips() {
  const groups = new Set(rows.map(r => r.n.split('_')[0]));
  $('chips').innerHTML = [...groups].sort().map(g => `<button class="${g === group ? 'on' : ''}" data-g="${g}">${g}</button>`).join('');
}

function search() {
  const q = $('q').value.trim();
  hits = q ? ms.search(q, { prefix: true, fuzzy: 0.2, boost: { n: 3 } }) : rows.slice();
  // equal scores: shorter name first, so ATC_RAT_RLL_P outranks ATC_RAT_RLL_FLTD
  if (q) hits.sort((a, b) => b.score - a.score || a.n.length - b.n.length);
  const i = hits.findIndex(h => h.n === q.toUpperCase().replace(/\s+/g, '_'));
  if (i > 0) hits.unshift(...hits.splice(i, 1));
  if (group) hits = hits.filter(h => h.n.split('_')[0] === group);
  $('count').textContent = `${hits.length} parameters`;
  tbody.textContent = ''; shown = 0; more();
  history.replaceState(null, '', '#' + new URLSearchParams({ v: $('vehicle').value, r: $('version').value, q, g: group }));
}

function more() {
  const frag = document.createDocumentFragment();
  for (const h of hits.slice(shown, shown + 300)) {
    const tr = document.createElement('tr');
    tr.className = 'p';
    const desc = td(h.d); desc.prepend(Object.assign(document.createElement('b'), { textContent: h.t + ' ' }));
    tr.append(td(h.n, 'n'), desc, td(h.r ? h.r.join(' to ') : ''), td(h.u || ''));
    tr.onclick = () => {
      const next = tr.nextElementSibling;
      if (next?.classList.contains('x')) return next.remove();
      const x = document.createElement('tr'); x.className = 'x';
      const cell = td([h.v && 'Values: ' + fmtMap(h.v), h.b && 'Bitmask: ' + fmtMap(h.b)].filter(Boolean).join('\n') || 'No values or bitmask');
      cell.colSpan = 4; x.append(cell); tr.after(x);
    };
    frag.append(tr);
  }
  shown += 300; tbody.append(frag); $('more').hidden = shown >= hits.length;
}

async function reload() {
  const file = `${$('vehicle').value}-${$('version').value}`, my = ++gen;
  rows = await load(file);
  if (my !== gen) return; // a newer selection won
  ms = new MiniSearch({ fields: ['n', 'd'], storeFields: ['n', 't', 'd', 'r', 'u', 'v', 'b'], idField: 'n' });
  ms.addAll(rows);
  fillChips(); search();
  table.dataset.loaded = file;
}

$('vehicle').onchange = () => { fillVersions(); reload(); };
$('version').onchange = reload;
$('q').oninput = search;
$('more').onclick = more;
$('chips').onclick = e => {
  const g = e.target.dataset.g;
  if (g === undefined) return;
  group = group === g ? '' : g;
  fillChips(); search();
};

const h = new URLSearchParams(location.hash.slice(1));
if (idx[h.get('v')]) $('vehicle').value = h.get('v');
fillVersions();
$('version').value = h.get('r');
if (!$('version').value) $('version').selectedIndex = 0;
$('q').value = h.get('q') || '';
group = h.get('g') || '';
reload();
