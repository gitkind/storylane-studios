/* Storylane Studios — interactions */
(() => {
  const doc = document.documentElement;
  if (!/[?&]static(?![a-z])/.test(location.search)) doc.classList.add('js');

  const header = document.querySelector('.site-header');
  const toggle = document.querySelector('.nav-toggle');
  const nav = document.getElementById('main-nav');
  const navLinks = [...document.querySelectorAll('.main-nav ul a')];

  /* Header background once the page scrolls */
  const onScroll = () => header.classList.toggle('is-scrolled', window.scrollY > 40);
  onScroll();
  window.addEventListener('scroll', onScroll, { passive: true });

  /* Mobile menu */
  const setMenu = (open) => {
    document.body.classList.toggle('nav-open', open);
    toggle.setAttribute('aria-expanded', String(open));
    toggle.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
  };
  toggle.addEventListener('click', () => setMenu(!document.body.classList.contains('nav-open')));
  nav.addEventListener('click', (e) => { if (e.target.closest('a')) setMenu(false); });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') setMenu(false); });
  window.matchMedia('(min-width: 1101px)').addEventListener('change', (m) => { if (m.matches) setMenu(false); });

  /* Active nav link follows the section in view */
  const sectionFor = { home: 'home', 'our-story': 'our-story', work: 'work', services: 'services', founder: 'services', process: 'process', faq: 'process', contact: 'process' };
  const setActive = (id) => navLinks.forEach((a) => a.classList.toggle('is-active', a.getAttribute('href') === '#' + id));
  const spy = new IntersectionObserver((entries) => {
    entries.forEach((en) => { if (en.isIntersecting) setActive(sectionFor[en.target.id] || 'home'); });
  }, { rootMargin: '-45% 0px -50% 0px' });
  Object.keys(sectionFor).forEach((id) => { const el = document.getElementById(id); if (el) spy.observe(el); });

  /* Generic accordion helper */
  const accordion = (items, headSel, { single }) => {
    const open = (item, state) => {
      item.classList.toggle('is-open', state);
      item.querySelector(headSel).setAttribute('aria-expanded', String(state));
    };
    items.forEach((item) => {
      item.querySelector(headSel).addEventListener('click', () => {
        const next = !item.classList.contains('is-open');
        if (single) items.forEach((i) => i !== item && open(i, false));
        open(item, single ? true : next);
        if (single && !next) open(item, false);
      });
    });
    return open;
  };

  /* Services — one open at a time */
  const svcItems = [...document.querySelectorAll('.svc')];
  const openSvc = accordion(svcItems, '.svc-head', { single: true });

  /* Footer service links open the matching service */
  document.querySelectorAll('[data-svc]').forEach((a) => {
    a.addEventListener('click', () => {
      const idx = Number(a.dataset.svc);
      svcItems.forEach((it, i) => openSvc(it, i === idx));
    });
  });

  /* FAQ — independent toggles */
  accordion([...document.querySelectorAll('.faq-item')], '.faq-q', { single: false });

  /* Reveal on scroll */
  const reveals = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((en) => { if (en.isIntersecting) { en.target.classList.add('is-in'); io.unobserve(en.target); } });
    }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
    reveals.forEach((el) => io.observe(el));
  } else {
    reveals.forEach((el) => el.classList.add('is-in'));
  }

  /* Story dial — amber arc grows as the chapter scrolls through */
  const chapters = document.getElementById('chapters');
  const ring = document.querySelector('.dial-ring');
  if (chapters && ring && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    let ticking = false;
    const update = () => {
      const r = chapters.getBoundingClientRect();
      const vh = window.innerHeight;
      const p = Math.min(1, Math.max(0, (vh - r.top) / (vh + r.height)));
      ring.style.setProperty('--p', p.toFixed(3));
      ticking = false;
    };
    window.addEventListener('scroll', () => { if (!ticking) { ticking = true; requestAnimationFrame(update); } }, { passive: true });
    update();
  }
})();
