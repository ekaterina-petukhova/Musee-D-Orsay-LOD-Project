/* ===== HAMBURGER MENU ===== */
(function () {
  const btn = document.querySelector('.hamburger');
  const menu = document.querySelector('.mobile-menu');
  if (!btn || !menu) return;
  let open = false;
  btn.addEventListener('click', () => {
    open = !open;
    menu.classList.toggle('open', open);
    btn.innerHTML = open
      ? `<svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>`
      : `<svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>`;
  });
  menu.querySelectorAll('a').forEach(a => a.addEventListener('click', () => {
    open = false; menu.classList.remove('open');
  }));
})();

/* ===== SCROLL REVEAL ===== */
(function () {
  const els = document.querySelectorAll('.reveal');
  if (!els.length) return;
  const io = new IntersectionObserver(entries => {
    entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('is-visible'); io.unobserve(e.target); } });
  }, { threshold: 0.12, rootMargin: '0px 0px -8% 0px' });
  els.forEach(el => io.observe(el));
})();

/* ===== TABS ===== */
(function () {
  document.querySelectorAll('.tabs-scope').forEach(scope => {
    const btns = scope.querySelectorAll('.tab-btn');
    const contents = scope.querySelectorAll('.tab-content');
    btns.forEach((btn, i) => {
      btn.addEventListener('click', () => {
        btns.forEach(b => b.classList.remove('active'));
        contents.forEach(c => c.classList.remove('active'));
        btn.classList.add('active');
        contents[i].classList.add('active');
        // Trigger panzoom refit inside newly active tab
        const vp = contents[i].querySelector('.pz-viewport');
        if (vp && vp._panzoom) vp._panzoom.fit();
      });
    });
  });
})();

/* ===== ENTITY CARD FILTER ===== */
(function () {
  const filterBtns = document.querySelectorAll('.filter-btn');
  if (!filterBtns.length) return;
  filterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      filterBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const cat = btn.dataset.cat;
      document.querySelectorAll('.frame-tile').forEach(tile => {
        tile.style.display = (cat === 'All' || tile.dataset.type === cat) ? '' : 'none';
      });
    });
  });
})();

/* ===== HERO SCROLL ===== */
(function () {
  const section = document.getElementById('hero-scroll');
  if (!section) return;

  const layer1 = section.querySelector('.layer1');
  const layer2 = section.querySelector('.layer2');
  const layer3 = section.querySelector('.layer3');
  const captionEl = document.getElementById('hero-caption');
  const tagline1 = document.getElementById('tagline-1');
  const tagline2 = document.getElementById('tagline-2');

  const CAPTIONS = [
    [0.0, ''],
    [0.4, "1939 · Gare d'Orsay"],
    [0.75, '1986 · Musée d\'Orsay'],
    [1.0, 'Today'],
  ];

  const HOLD_1_END = 0.14, T1_END = 0.36, HOLD_2_END = 0.54, T2_END = 0.76;

  function ease(t) { return t < 0.5 ? 4*t*t*t : 1 - Math.pow(-2*t+2,3)/2; }

  function getCaption(p) {
    let text = '';
    for (const [thr, label] of CAPTIONS) { if (p >= thr) text = label; }
    return text;
  }

  let ticking = false;
  let lockUntil = 0, locked1 = false, locked2 = false;

  function update() {
    ticking = false;
    const rect = section.getBoundingClientRect();
    const range = rect.height - window.innerHeight;
    let p = range > 0 ? -rect.top / range : 0;
    p = Math.max(0, Math.min(1, p));

    const inside = rect.top <= 0 && rect.bottom > window.innerHeight;
    if (inside && p >= T1_END && !locked1) { locked1 = true; lockUntil = Date.now() + 700; }
    if (p < T1_END) locked1 = false;
    if (inside && p >= T2_END && !locked2) { locked2 = true; lockUntil = Date.now() + 900; }
    if (p < T2_END) locked2 = false;

    let o1 = 0, o2 = 0, o3 = 0;
    if (p <= HOLD_1_END) { o1 = 1; }
    else if (p <= T1_END) { const t = ease((p - HOLD_1_END) / (T1_END - HOLD_1_END)); o1 = 1-t; o2 = t; }
    else if (p <= HOLD_2_END) { o2 = 1; }
    else if (p <= T2_END) { const t = ease((p - HOLD_2_END) / (T2_END - HOLD_2_END)); o2 = 1-t; o3 = t; }
    else { o3 = 1; }

    if (layer1) layer1.style.opacity = o1;
    if (layer2) layer2.style.opacity = o2;
    if (layer3) layer3.style.opacity = o3;
    if (captionEl) captionEl.textContent = getCaption(p);

    if (tagline1) tagline1.classList.toggle('visible', p >= HOLD_2_END);
    if (tagline2) tagline2.classList.toggle('visible', p >= T2_END);
  }

  window.addEventListener('scroll', () => { if (!ticking) { requestAnimationFrame(update); ticking = true; } }, { passive: true });
  window.addEventListener('resize', update);
  window.addEventListener('wheel', e => { if (Date.now() < lockUntil) e.preventDefault(); }, { passive: false });
  window.addEventListener('touchmove', e => { if (Date.now() < lockUntil) e.preventDefault(); }, { passive: false });
  update();
})();

/* ===== PAN/ZOOM ===== */
(function () {
  document.querySelectorAll('.pz-viewport').forEach(vp => {
    const inner = vp.querySelector('.pz-inner');
    if (!inner) return;

    let scale = 1, tx = 0, ty = 0;
    let dragging = false, lastX = 0, lastY = 0;

    function apply() {
      inner.style.transform = `translate(${tx}px,${ty}px) scale(${scale})`;
    }

    function fit() {
      const iw = inner.scrollWidth, ih = inner.scrollHeight;
      const vw = vp.clientWidth, vh = vp.clientHeight;
      scale = Math.min(vw / iw, vh / ih, 1);
      tx = (vw - iw * scale) / 2;
      ty = (vh - ih * scale) / 2;
      apply();
    }

    // expose fit for tab switching
    vp._panzoom = { fit };

    // Wait for image to load before fitting
    const img = inner.querySelector('img');
    if (img && !img.complete) img.addEventListener('load', fit);
    else setTimeout(fit, 50);

    // Reset button
    const toolbar = vp.closest('.panel')?.querySelector('.panel-toolbar button');
    if (toolbar) toolbar.addEventListener('click', fit);

    // Mouse drag
    vp.addEventListener('mousedown', e => {
      dragging = true; lastX = e.clientX; lastY = e.clientY;
      vp.classList.add('grabbing');
    });
    window.addEventListener('mousemove', e => {
      if (!dragging) return;
      tx += e.clientX - lastX; ty += e.clientY - lastY;
      lastX = e.clientX; lastY = e.clientY;
      apply();
    });
    window.addEventListener('mouseup', () => { dragging = false; vp.classList.remove('grabbing'); });

    // Touch drag
    let lastTX = 0, lastTY = 0, lastDist = 0;
    vp.addEventListener('touchstart', e => {
      if (e.touches.length === 1) { lastTX = e.touches[0].clientX; lastTY = e.touches[0].clientY; }
      if (e.touches.length === 2) {
        const dx = e.touches[0].clientX - e.touches[1].clientX;
        const dy = e.touches[0].clientY - e.touches[1].clientY;
        lastDist = Math.sqrt(dx*dx + dy*dy);
      }
    }, { passive: true });
    vp.addEventListener('touchmove', e => {
      e.preventDefault();
      if (e.touches.length === 1) {
        tx += e.touches[0].clientX - lastTX; ty += e.touches[0].clientY - lastTY;
        lastTX = e.touches[0].clientX; lastTY = e.touches[0].clientY; apply();
      }
      if (e.touches.length === 2) {
        const dx = e.touches[0].clientX - e.touches[1].clientX;
        const dy = e.touches[0].clientY - e.touches[1].clientY;
        const dist = Math.sqrt(dx*dx + dy*dy);
        const factor = dist / lastDist;
        scale = Math.max(0.2, Math.min(8, scale * factor));
        lastDist = dist; apply();
      }
    }, { passive: false });

    // Wheel zoom
    vp.addEventListener('wheel', e => {
      e.preventDefault();
      const rect = vp.getBoundingClientRect();
      const mx = e.clientX - rect.left, my = e.clientY - rect.top;
      const factor = e.deltaY < 0 ? 1.1 : 0.91;
      const newScale = Math.max(0.1, Math.min(10, scale * factor));
      tx = mx - (mx - tx) * (newScale / scale);
      ty = my - (my - ty) * (newScale / scale);
      scale = newScale; apply();
    }, { passive: false });
  });
})();
