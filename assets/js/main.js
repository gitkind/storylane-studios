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
  const reveals = document.querySelectorAll('.reveal, .tile-in, [data-reveal]');
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

  /* Explore-other-services marquee: duplicate the track so it loops seamlessly */
  document.querySelectorAll('.marquee-track').forEach((track) => {
    [...track.children].forEach((node) => {
      const copy = node.cloneNode(true);
      copy.setAttribute('aria-hidden', 'true');
      copy.setAttribute('tabindex', '-1');
      track.appendChild(copy);
    });
  });

  /* Product photography lightbox */
  const shots = [...document.querySelectorAll('[data-full]')];
  if (shots.length) {
    const box = document.createElement('div');
    box.className = 'lightbox';
    box.setAttribute('role', 'dialog');
    box.setAttribute('aria-modal', 'true');
    box.setAttribute('aria-label', 'Full view image');
    box.innerHTML = '<img alt=""><button class="lightbox-close" type="button" aria-label="Close"></button>' +
      '<button class="lightbox-nav lightbox-prev" type="button" aria-label="Previous image">‹</button>' +
      '<button class="lightbox-nav lightbox-next" type="button" aria-label="Next image">›</button>';
    document.body.appendChild(box);
    const img = box.querySelector('img');
    let idx = 0;
    let opener = null;
    const show = (i) => {
      idx = (i + shots.length) % shots.length;
      img.src = shots[idx].dataset.full;
      img.alt = shots[idx].querySelector('img').alt;
    };
    const close = () => {
      box.classList.remove('is-open');
      document.body.style.overflow = '';
      if (opener) opener.focus();
    };
    shots.forEach((s, i) => s.addEventListener('click', () => {
      opener = s;
      show(i);
      box.classList.add('is-open');
      document.body.style.overflow = 'hidden';
      box.querySelector('.lightbox-close').focus();
    }));
    box.querySelector('.lightbox-close').addEventListener('click', close);
    box.querySelector('.lightbox-prev').addEventListener('click', () => show(idx - 1));
    box.querySelector('.lightbox-next').addEventListener('click', () => show(idx + 1));
    box.addEventListener('click', (e) => { if (e.target === box) close(); });
    document.addEventListener('keydown', (e) => {
      if (!box.classList.contains('is-open')) return;
      if (e.key === 'Escape') close();
      if (e.key === 'ArrowLeft') show(idx - 1);
      if (e.key === 'ArrowRight') show(idx + 1);
    });
  }

  /* Contact form — static hosting, so it opens a pre-filled email to the studio */
  const form = document.getElementById('contact-form');
  if (form) {
    const params = new URLSearchParams(location.search);
    const wanted = params.get('service');
    const select = form.querySelector('select[name="service"]');
    if (wanted && select) {
      const match = [...select.options].find((o) => o.text === wanted);
      if (match) match.selected = true;
    }
    const pkg = params.get('package');
    const msg = form.querySelector('textarea[name="message"]');
    if (pkg && msg && !msg.value) msg.value = `I'm interested in the ${pkg} package.`;

    const status = form.querySelector('.form-status');
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      let firstBad = null;
      form.querySelectorAll('.field').forEach((f) => {
        const input = f.querySelector('input, select, textarea');
        const ok = input.checkValidity() && input.value.trim() !== '';
        f.classList.toggle('is-invalid', !ok);
        input.setAttribute('aria-invalid', String(!ok));
        if (!ok && !firstBad) firstBad = input;
      });
      if (firstBad) {
        status.textContent = 'Please fill in the highlighted fields.';
        firstBad.focus();
        return;
      }
      const d = Object.fromEntries(new FormData(form));
      const subject = `New enquiry: ${d.service} — ${d.brand}`;
      const body = `Name: ${d.name}\nEmail: ${d.email}\nPhone: ${d.phone}\nBrand / Company: ${d.brand}\nService: ${d.service}\n\n${d.message}`;
      window.location.href = `mailto:${form.dataset.to}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
      status.textContent = 'Opening your email app with your details filled in…';
    });
    form.addEventListener('input', (e) => {
      const f = e.target.closest('.field');
      if (f && f.classList.contains('is-invalid') && e.target.checkValidity()) {
        f.classList.remove('is-invalid');
        e.target.setAttribute('aria-invalid', 'false');
      }
    });
  }
})();
