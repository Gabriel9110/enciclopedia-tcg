/* ---------- menu su telefono ---------- */
(function () {
  var side = document.getElementById('side'), btn = document.getElementById('menuBtn');
  if (!side || !btn) return;
  btn.addEventListener('click', function () { var o = side.classList.toggle('open'); btn.setAttribute('aria-expanded', o ? 'true' : 'false'); });
  var on = side.querySelector('a.on'); if (on && on.scrollIntoView) { try { on.scrollIntoView({ block: 'center' }); window.scrollTo(0, 0); } catch (e) {} }
})();
/* ---------- anteprima delle carte ---------- */
(function () {
  var data = {};
  try { data = JSON.parse(document.getElementById('cardsdata').textContent); } catch (e) { return; }
  var pop = document.getElementById('pop');
  var TN = { G: 'Erba', R: 'Fuoco', W: 'Acqua', L: 'Lampo', P: 'Psico', F: 'Lotta', C: 'Incolore', D: 'Buio', M: 'Metallo', N: 'Drago', '0': 'Nessuno' };
  var TC = { G: 't-grass', R: 't-fire', W: 't-water', L: 't-light', P: 't-psy', F: 't-fight', C: 't-col', D: 't-dark', M: 't-metal', N: 't-col', '0': 't-col' };
  var imgOK = null; // null = sconosciuto, true/false dopo il primo tentativo
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function dots(cost) {
    if (!cost) return '<span class="en t-col" title="Nessun costo">0</span>';
    return cost.split('').map(function (t) { return '<span class="en ' + (TC[t] || 't-col') + '" title="' + (TN[t] || '') + '"></span>'; }).join('');
  }
  function wr(s) {
    if (!s) return '–';
    return s.split(' ').map(function (x) { var t = x[0]; return '<span class="en ' + (TC[t] || 't-col') + '" title="' + (TN[t] || '') + '"></span>' + esc(x.slice(1)); }).join(' ');
  }
  function stage(c) {
    var s = c.sub || [];
    var m = { 'Basic': 'Base', 'Stage 1': 'Fase 1', 'Stage 2': 'Fase 2', 'Level-Up': 'LV.X', 'Supporter': 'Aiuto', 'Item': 'Allenatore', 'Stadium': 'Stadio', 'Pokémon Tool': 'Strumento', 'Special': 'Energia Speciale', 'Technical Machine': 'Macchina Tecnica', "Rocket's Secret Machine": "Rocket's Secret Machine" };
    var out = s.map(function (x) { return m[x] || x; });
    if (c.sup === 'T' && !out.length) out = ['Allenatore'];
    if (c.sup === 'E' && !out.length) out = ['Energia'];
    return out.join(' · ');
  }
  function render(id) {
    var c = data[id]; if (!c) return '';
    var t = (c.t || 'C')[0];
    var h = '<div class="pc ' + (c.sup === 'P' ? TC[t] : (c.sup === 'T' ? 't-tr' : 't-en')) + '">';
    h += '<div class="pc-img" hidden><img alt="' + esc(c.n) + '"></div>';
    h += '<div class="pc-mock"><div class="pc-top"><span class="pc-st">' + esc(stage(c)) + (c.ev ? ' · da ' + esc(c.ev) : '') + '</span>';
    h += '<div class="pc-nm"><b>' + esc(c.n) + '</b>' + (c.hp ? '<span class="pc-hp">' + esc(c.hp) + ' PS ' + (c.t || '').split('').map(function (x) { return '<span class="en ' + TC[x] + '" title="' + TN[x] + '"></span>'; }).join('') + '</span>' : '') + '</div></div>';
    h += '<div class="pc-body">';
    (c.ab || []).forEach(function (a) { h += '<div class="pc-ab"><span class="pc-abk">' + esc(a[0]) + '</span> <b>' + esc(a[1]) + '</b><p>' + esc(a[2]) + '</p></div>'; });
    (c.at || []).forEach(function (a) { h += '<div class="pc-at"><div class="pc-atl"><span class="pc-cost">' + dots(a[1]) + '</span><b>' + esc(a[0]) + '</b><span class="pc-dmg">' + esc(a[2]) + '</span></div>' + (a[3] ? '<p>' + esc(a[3]) + '</p>' : '') + '</div>'; });
    (c.ru || []).forEach(function (r) { h += '<p class="pc-ru">' + esc(r) + '</p>'; });
    h += '</div>';
    if (c.sup === 'P') h += '<div class="pc-wrr"><span>Debolezza ' + wr(c.w) + '</span><span>Resistenza ' + wr(c.r) + '</span><span>Ritirata ' + (c.rc ? dots('C'.repeat(c.rc)) : '0') + '</span></div>';
    h += '</div><div class="pc-foot"><span>' + esc(c.s) + ' · ' + esc(c.no) + (c.ra ? ' · ' + esc(c.ra) : '') + '</span>' + (c.big ? '<a href="' + esc(c.big) + '" target="_blank" rel="noopener">Immagine originale</a>' : '') + '</div></div>';
    return h;
  }
  var cur = null, pinned = false, hideT = null;
  function place(el) {
    var r = el.getBoundingClientRect(), pw = pop.offsetWidth, ph = pop.offsetHeight, vw = window.innerWidth, vh = window.innerHeight;
    var x = r.left + r.width / 2 - pw / 2; x = Math.max(8, Math.min(x, vw - pw - 8));
    var y = r.bottom + 8; if (y + ph > vh - 8) y = Math.max(8, r.top - ph - 8);
    pop.style.left = x + 'px'; pop.style.top = y + 'px';
  }
  function open(el, pin) {
    clearTimeout(hideT);
    var id = el.dataset.c; if (!data[id]) return;
    if (cur !== el) {
      pop.innerHTML = render(id); cur = el;
      var c = data[id], box = pop.querySelector('.pc-img'), img = box.querySelector('img');
      if (c.img && imgOK !== false) {
        img.onload = function () { imgOK = true; box.hidden = false; pop.querySelector('.pc-mock').hidden = true; place(el); };
        img.onerror = function () { imgOK = false; };
        img.src = c.img;
      }
    }
    pinned = !!pin; pop.hidden = false; place(el);
  }
  function close() { pop.hidden = true; cur = null; pinned = false; }
  var fine = window.matchMedia && window.matchMedia('(hover: hover)').matches;
  document.addEventListener('mouseover', function (e) {
    if (!fine) return; var el = e.target.closest('.cd'); if (el) open(el, false);
  });
  document.addEventListener('mouseout', function (e) {
    if (!fine || pinned) return; var el = e.target.closest('.cd');
    if (el && !(e.relatedTarget && (el.contains(e.relatedTarget) || pop.contains(e.relatedTarget)))) hideT = setTimeout(close, 180);
  });
  pop.addEventListener('mouseenter', function () { clearTimeout(hideT); });
  pop.addEventListener('mouseleave', function () { if (!pinned) hideT = setTimeout(close, 180); });
  document.addEventListener('click', function (e) {
    var el = e.target.closest('.cd');
    if (el) { e.preventDefault(); if (cur === el && pinned) close(); else open(el, true); return; }
    if (!pop.contains(e.target)) close();
  });
  document.addEventListener('focusin', function (e) { var el = e.target.closest && e.target.closest('.cd'); if (el) open(el, false); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') close(); if ((e.key === 'Enter' || e.key === ' ') && e.target.classList && e.target.classList.contains('cd')) { e.preventDefault(); open(e.target, true); } });
  window.addEventListener('scroll', function () { if (cur && !pop.hidden) place(cur); }, { passive: true });
})();
/* ---------- filtro famiglie nel catalogo dei mazzi ---------- */
(function () {
  var box = document.querySelector('.dk-filter'); if (!box) return;
  box.addEventListener('click', function (e) {
    var b = e.target.closest('button'); if (!b) return;
    var a = b.dataset.a;
    box.querySelectorAll('button').forEach(function (x) { x.classList.toggle('on', x === b); });
    document.querySelectorAll('.dkc').forEach(function (c) { c.hidden = !!a && c.dataset.a !== a; });
    document.querySelectorAll('.dk-era').forEach(function (s) { s.hidden = !s.querySelector('.dkc:not([hidden])'); });
  });
})();
