(function () {
  'use strict';
  var doc = document, root = doc.documentElement;
  var base = root.getAttribute('data-root') || './';

  /* ---- theme ---- */
  var toggle = doc.getElementById('theme-toggle');
  if (toggle) toggle.addEventListener('click', function () {
    var dark = !root.classList.contains('dark');
    root.classList.toggle('dark', dark);
    try { localStorage.setItem('theme', dark ? 'dark' : 'light'); } catch (e) {}
  });

  /* ---- mobile menu ---- */
  var menu = doc.getElementById('menu-btn');
  if (menu) menu.addEventListener('click', function () {
    var open = doc.body.classList.toggle('nav-open');
    menu.setAttribute('aria-expanded', open ? 'true' : 'false');
  });
  doc.querySelectorAll('.sidebar a').forEach(function (a) {
    a.addEventListener('click', function () { doc.body.classList.remove('nav-open'); });
  });

  /* ---- code blocks: label and copy button ---- */
  var copyIcon = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="14" height="14" x="8" y="8" rx="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/></svg>';
  var okIcon = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>';
  doc.querySelectorAll('.prose pre, .demo pre').forEach(function (pre) {
    if (pre.parentNode.classList.contains('code-block')) return;
    var holder = pre.parentNode.classList.contains('sourceCode') ? pre.parentNode : pre;
    var lang = '';
    (pre.className + ' ' + (pre.firstElementChild ? pre.firstElementChild.className : '')).split(/\s+/).forEach(function (c) {
      if (c && c !== 'sourceCode' && c !== 'default') lang = lang || c.replace(/^language-/, '');
    });
    if (lang === 'text' || lang === 'plaintext') lang = '';
    var wrap = doc.createElement('div');
    wrap.className = 'code-block' + (lang ? '' : ' no-head');
    holder.parentNode.insertBefore(wrap, holder);
    if (lang) {
      var head = doc.createElement('div');
      head.className = 'code-head';
      head.innerHTML = '<span>' + lang + '</span>';
      wrap.appendChild(head);
      var btn = doc.createElement('button');
      btn.className = 'copy'; btn.type = 'button'; btn.setAttribute('aria-label', 'Copy code'); btn.innerHTML = copyIcon;
      head.appendChild(btn);
      wrap.appendChild(holder);
      wire(btn, pre);
    } else {
      wrap.appendChild(holder);
      var b2 = doc.createElement('button');
      b2.className = 'copy'; b2.type = 'button'; b2.setAttribute('aria-label', 'Copy code'); b2.innerHTML = copyIcon;
      wrap.appendChild(b2);
      wire(b2, pre);
    }
  });
  function wire(btn, pre) {
    btn.addEventListener('click', function () {
      var text = pre.innerText.replace(/\n$/, '');
      var done = function () {
        btn.innerHTML = okIcon; btn.setAttribute('data-done', '1');
        setTimeout(function () { btn.innerHTML = copyIcon; btn.removeAttribute('data-done'); }, 1600);
      };
      if (navigator.clipboard) navigator.clipboard.writeText(text).then(done, function () {});
    });
  }

  /* ---- on this page: highlight the section in view ---- */
  var links = doc.querySelectorAll('.toc a');
  if (links.length && 'IntersectionObserver' in window) {
    var map = {};
    links.forEach(function (a) { map[a.getAttribute('href').slice(1)] = a; });
    var heads = Array.prototype.slice.call(doc.querySelectorAll('.prose h2[id], .prose h3[id]'));
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting && map[e.target.id]) {
          links.forEach(function (l) { l.classList.remove('active'); });
          map[e.target.id].classList.add('active');
        }
      });
    }, { rootMargin: '-80px 0px -70% 0px' });
    heads.forEach(function (h) { io.observe(h); });
  }

  /* ---- search (Ctrl/Cmd+K or /) ---- */
  var dlg = doc.getElementById('search-dialog');
  if (!dlg) return;
  var input = doc.getElementById('search-input'), list = doc.getElementById('search-list');
  var index = null, current = [], sel = 0;

  function load(cb) {
    if (index) return cb();
    fetch(base + 'search.json').then(function (r) { return r.json(); }).then(function (j) { index = j; cb(); }).catch(function () { index = []; cb(); });
  }
  function score(item, terms) {
    var s = 0, t = item.title.toLowerCase(), h = item.headings.toLowerCase(), d = item.description.toLowerCase();
    for (var i = 0; i < terms.length; i++) {
      var w = terms[i], hit = 0;
      if (t.indexOf(w) > -1) hit += 6;
      if (h.indexOf(w) > -1) hit += 3;
      if (d.indexOf(w) > -1) hit += 1;
      if (item.url.indexOf(w) > -1) hit += 1;
      if (!hit) return 0;
      s += hit;
    }
    return s;
  }
  function render() {
    var q = input.value.trim().toLowerCase(), terms = q.split(/\s+/).filter(Boolean);
    var results = (index || []).map(function (it) { return { it: it, s: terms.length ? score(it, terms) : 1 }; })
      .filter(function (r) { return r.s > 0; }).sort(function (a, b) { return b.s - a.s; }).slice(0, 12);
    current = results; sel = 0;
    if (!results.length) { list.innerHTML = '<li class="search-empty">No results for "' + q.replace(/[<>&]/g, '') + '".</li>'; return; }
    list.innerHTML = results.map(function (r, i) {
      return '<li><a href="' + base + r.it.url + '" role="option" aria-selected="' + (i === 0) + '"><b>' + esc(r.it.title) + '</b><small>' + esc(r.it.section + ' · ' + r.it.description).slice(0, 140) + '</small></a></li>';
    }).join('');
  }
  function esc(s) { return s.replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function mark() {
    var items = list.querySelectorAll('a');
    items.forEach(function (a, i) { a.setAttribute('aria-selected', i === sel ? 'true' : 'false'); });
    if (items[sel]) items[sel].scrollIntoView({ block: 'nearest' });
  }
  function open() { load(function () { if (!dlg.open) dlg.showModal(); input.value = ''; render(); input.focus(); }); }
  doc.querySelectorAll('[data-search]').forEach(function (b) { b.addEventListener('click', open); });
  doc.addEventListener('keydown', function (e) {
    var tag = (e.target.tagName || '').toLowerCase();
    if ((e.key === 'k' && (e.metaKey || e.ctrlKey)) || (e.key === '/' && tag !== 'input' && tag !== 'textarea')) { e.preventDefault(); open(); }
  });
  input.addEventListener('input', render);
  input.addEventListener('keydown', function (e) {
    var n = list.querySelectorAll('a').length;
    if (e.key === 'ArrowDown') { e.preventDefault(); sel = Math.min(sel + 1, n - 1); mark(); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); sel = Math.max(sel - 1, 0); mark(); }
    else if (e.key === 'Enter' && current[sel]) { location.href = base + current[sel].it.url; }
  });
  dlg.addEventListener('click', function (e) { if (e.target === dlg) dlg.close(); });
})();
