"""Generate Storylane Studios inner pages and keep the shared header/footer in sync.

Run from the repo root:  python tools/build_pages.py

Writes the Work category pages, the Story DNA service page and the Contact page,
and rewrites the <!-- @header --> / <!-- @footer --> blocks inside index.html so
every page shares one header and footer. Output is plain static HTML for GitHub Pages
(all links are relative, so the /storylane-studios/ sub-path keeps working).
"""
from __future__ import annotations

import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CONTACT = {
    "email": "connect.storylanestudios@gmail.com",
    "phone": "+91 8218527215",
    "tel": "+918218527215",
    "wa": "https://wa.me/918218527215",
    "ig": "https://www.instagram.com/storylane.studios/",
    "ig_handle": "@storylane.studios",
}

ARROW = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 17 17 7M8 7h9v9"/></svg>'
DOC = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/>'
       '<path d="M14 3v5h5M9 13h6M9 17h4"/></svg>')
CHECK = '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="m8 12 3 3 5-6"/></svg>'

# Work categories: slug, file, title (outlined), chip label
WORK = [
    ("commercial", "work-commercial.html", "Commercial Brands &amp; Ads Films", "Commercial Brands &amp; Ads Films"),
    ("product", "work-product-photography.html", "Product Photography", "Product Photography"),
    ("websites", "work-websites.html", "Websites &amp; Digital Experiences", "Websites &amp; Digital Experiences"),
    ("reels", "work-short-form.html", "Short - Form Content &amp; Reels", "Short-Form Content &amp; Reels"),
    ("brand", "work-brand-integration.html", "Brand Integration Campaigns", "Brand Integration Campaigns"),
    ("social", "work-social-media.html", "Social Media Management", "Social Media Management"),
]
WORK_FILE = {slug: f for slug, f, _, _ in WORK}

# Footer "Services" column -> best matching page
FOOTER_SERVICES = [
    ("Brand Identity &amp; Positioning", "story-dna.html"),
    ("Websites &amp; Digital Experiences", WORK_FILE["websites"]),
    ("Commercial Ads &amp; Brand Films", WORK_FILE["commercial"]),
    ("Product Photography", WORK_FILE["product"]),
    ("Short-Form Content &amp; Reels", WORK_FILE["reels"]),
    ("Social Media Management &amp; Content Strategy", WORK_FILE["social"]),
    ("Brand Integration Campaigns", WORK_FILE["brand"]),
    ("Performance Marketing", "index.html#services"),
    ("Film Production", "index.html#services"),
]

SERVICE_OPTIONS = [
    "Brand Identity & Positioning", "Websites & Digital Experiences", "Commercial Ads & Brand Films",
    "Product Photography", "Short-Form Content & Reels", "Social Media Management & Content Strategy",
    "Brand Integration Campaigns", "Performance Marketing", "Film Production", "Not sure yet",
]

ICONS = {
    "web": '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="4" width="18" height="14" rx="2"/><path d="M3 8h18M8 21h8"/></svg>',
    "film": '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="4" y="7" width="16" height="12" rx="1"/><path d="M4 11h16M8 7l-1 4M13 7l-1 4M18 7l-1 4"/></svg>',
    "camera": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 8h3l2-3h6l2 3h3v11H4z"/><circle cx="12" cy="13" r="3.5"/></svg>',
    "reel": '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="6" y="3" width="12" height="18" rx="2"/><path d="M6 7h12M6 17h12M10 10.5v3l3-1.5z"/></svg>',
    "phone": '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="7" y="3" width="10" height="18" rx="2"/><path d="M10 7h4M10 11h4M10 15h2"/></svg>',
    "tag": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 12V4h8l10 10-8 8z"/><circle cx="7.5" cy="8.5" r="1.4"/></svg>',
    "chart": '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="4" width="18" height="16" rx="2"/><path d="m7 15 3-3 3 2 4-5"/></svg>',
    "clap": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 10h16v9H4zM4 10l2-5 14 0-2 5M9 5l-1.5 5M14 5l-1.5 5"/></svg>',
    "mail": '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/></svg>',
    "call": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 4h3l2 5-2 1a11 11 0 0 0 6 6l1-2 5 2v3a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2z"/></svg>',
    "whatsapp": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 20l1.3-4A8 8 0 1 1 8 18.7z"/><path d="M9 9c0 3 2.5 6 6 6l1-1.5-2-1-1 1c-1-.5-2-1.5-2.5-2.5l1-1-1-2z"/></svg>',
    "insta": '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="4" y="4" width="16" height="16" rx="5"/><circle cx="12" cy="12" r="3.6"/><circle cx="17" cy="7" r=".9"/></svg>',
    "pin": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 21s-6-5.6-6-11a6 6 0 0 1 12 0c0 5.4-6 11-6 11z"/><circle cx="12" cy="10" r="2.3"/></svg>',
}

e = html.escape


# ---------------------------------------------------------------------------
# Shared chrome
# ---------------------------------------------------------------------------
def header(home: str, active: str = "") -> str:
    """home = '' on index.html (in-page anchors) or 'index.html' elsewhere."""
    def item(anchor: str, label: str) -> str:
        cls = ' class="is-active"' if active == anchor else ""
        return f'          <li><a href="{home}#{anchor}"{cls}>{label}</a></li>'
    items = "\n".join(item(a, l) for a, l in [("home", "Home"), ("our-story", "Our Story"), ("work", "Work"),
                                                ("services", "Services"), ("process", "Process")])
    return f"""<!-- @header -->
  <header class="site-header" id="top">
    <div class="container header-inner">
      <a href="{home}#home" class="brand" aria-label="Storylane Studios — home">
        <img src="assets/img/logo.png" alt="Storylane Studios" width="140" height="65">
      </a>
      <nav class="main-nav" id="main-nav" aria-label="Primary">
        <ul>
{items}
        </ul>
        <a href="contact.html" class="btn-outline nav-cta-mobile">Start Your Story {ARROW}</a>
      </nav>
      <a href="contact.html" class="btn-outline nav-cta">Start Your Story {ARROW}</a>
      <button class="nav-toggle" aria-controls="main-nav" aria-expanded="false" aria-label="Open menu"><span></span><span></span></button>
    </div>
  </header>
  <!-- /@header -->"""


def footer(home: str, extra_class: str = "") -> str:
    quick = [("Home", f"{home}#home"), ("Our Story", f"{home}#our-story"), ("Work", f"{home}#work"),
             ("Service", f"{home}#services"), ("Founder", f"{home}#founder"), ("Process", f"{home}#process"),
             ("FAQ", f"{home}#faq"), ("Contact", "contact.html")]
    quick_html = "\n".join(f'            <li><a href="{h}">{l}</a></li>' for l, h in quick)
    svc_html = "\n".join(f'            <li><a href="{h}">{l}</a></li>' for l, h in FOOTER_SERVICES)
    cls = "site-footer" + (f" {extra_class}" if extra_class else "")
    return f"""<!-- @footer -->
  <footer class="{cls}">
    <div class="container">
      <div class="footer-grid">
        <div class="footer-brand">
          <a href="{home}#home" class="brand"><img src="assets/img/logo.png" alt="Storylane Studios" width="140" height="65" loading="lazy"></a>
          <p>Turning brands into stories<br>worth remembering.</p>
          <p class="founded">Founded by <a href="{home}#founder">Ayush Jain</a></p>
          <ul class="socials">
            <li><a href="mailto:{CONTACT['email']}" aria-label="Email {CONTACT['email']}"><img src="assets/img/icon-mail.png" alt="" width="58" height="58" loading="lazy"></a></li>
            <li><a href="tel:{CONTACT['tel']}" aria-label="Call {CONTACT['phone']}"><img src="assets/img/icon-phone.png" alt="" width="58" height="58" loading="lazy"></a></li>
            <li><a href="{CONTACT['ig']}" target="_blank" rel="noopener" aria-label="Instagram {CONTACT['ig_handle']}"><img src="assets/img/icon-instagram.png" alt="" width="58" height="58" loading="lazy"></a></li>
            <li><a href="{CONTACT['wa']}" target="_blank" rel="noopener" aria-label="WhatsApp {CONTACT['phone']}"><img src="assets/img/icon-whatsapp.png" alt="" width="58" height="58" loading="lazy"></a></li>
          </ul>
        </div>
        <nav class="footer-col" aria-label="Quick links">
          <h2>Quick Links</h2>
          <ul>
{quick_html}
          </ul>
        </nav>
        <div class="footer-col">
          <h2>Services</h2>
          <ul>
{svc_html}
          </ul>
        </div>
      </div>
      <div class="footer-bottom">
        <p><span class="copy" aria-hidden="true">©</span> 2026 Storylane Studios. All rights reserved.</p>
        <ul>
          <li><a href="#">Privacy Policy</a></li>
          <li><a href="#">Terms of Service</a></li>
        </ul>
      </div>
    </div>
  </footer>
  <!-- /@footer -->"""


def page(file: str, title: str, desc: str, body: str, active: str = "", preload: str = "") -> None:
    pre = f'\n  <link rel="preload" as="image" href="{preload}">' if preload else ""
    doc = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} — Storylane Studios</title>
  <meta name="description" content="{desc}">
  <meta name="theme-color" content="#0a0a0c">
  <meta property="og:type" content="website">
  <meta property="og:title" content="{title} — Storylane Studios">
  <meta property="og:description" content="{desc}">
  <meta property="og:image" content="assets/img/studio-still.jpg">
  <meta name="twitter:card" content="summary_large_image">
  <link rel="icon" type="image/png" href="assets/img/logo.png">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Anton&family=Inter:wght@400;500&family=Manrope:wght@300;400;500;600&display=swap" rel="stylesheet">{pre}
  <link rel="stylesheet" href="assets/css/styles.css">
  <link rel="stylesheet" href="assets/css/pages.css">
</head>
<body>
  <a class="skip-link" href="#main">Skip to content</a>

  {header("index.html", active)}

  <main id="main" class="page-main">
{body}
  </main>

  {footer("index.html", "site-footer--page")}

  <script src="assets/js/main.js" defer></script>
</body>
</html>
"""
    (ROOT / file).write_text(doc, encoding="utf-8", newline="\n")
    print("wrote", file)


# ---------------------------------------------------------------------------
# Work category pages
# ---------------------------------------------------------------------------
def cat_hero(title: str) -> str:
    return f"""    <section class="cat-hero" aria-labelledby="page-title">
      <div class="container">
        <h1 id="page-title" class="outline-title">{title}<span class="sweep" aria-hidden="true">{title}</span></h1>
      </div>
    </section>"""


def tiles(items, extra="") -> str:
    out = []
    for i, (src, alt) in enumerate(items):
        out.append(f'          <figure class="media-tile tile-in" style="--i:{i}"{extra}><img src="assets/img/work/{src}.webp" alt="{alt}" loading="lazy"></figure>')
    return "\n".join(out)


def block(label: str, inner: str, grid_class: str, hint: str = "") -> str:
    hint_html = f'\n          <p class="cat-hint">{hint}</p>' if hint else ""
    return f"""    <section class="cat-block">
      <div class="container">
        <div class="cat-head">
          <p class="eyebrow eyebrow--auto"><span>{label}</span></p>{hint_html}
        </div>
        <div class="{grid_class}">
{inner}
        </div>
      </div>
    </section>"""


def next_cta(service: str) -> str:
    return f"""    <section class="cta cta--next" aria-labelledby="cta-title">
      <div class="container">
        <h2 id="cta-title" class="display">Ready to Make Your Story the Next One?</h2>
        <p>Every great project starts with an idea. Let’s talk about<br class="br-lg"> yours and explore what we can create together.</p>
        <div class="cta-actions">
          <a class="btn-dark" href="contact.html?service={e(service)}">Get Quotation {DOC}</a>
          <a class="btn-amber" href="contact.html">Let’s Talk</a>
        </div>
      </div>
    </section>"""


def explore(current: str) -> str:
    chips = "\n".join(f'          <a class="chip" href="{f}">{label}</a>' for slug, f, _, label in WORK if slug != current)
    return f"""    <section class="explore" aria-label="Explore other work">
      <div class="container">
        <p class="eyebrow eyebrow--auto"><span>Explore Other Work</span></p>
        <div class="chips">
{chips}
        </div>
      </div>
    </section>"""


def work_pages() -> None:
    # 1. Commercial (prototype 777-10379 — "Our Work animation")
    body = "\n".join([
        cat_hero("Commercial Brands &amp; Ads Films"),
        block("Our Selected Work", tiles([
            ("commercial-chings", "Ching’s Secret product ad film"),
            ("commercial-silk", "Cadbury Silk commercial with a home cook"),
            ("commercial-roar", "ROAR energy drink ad film — Power-up and Roar"),
            ("commercial-meraki", "Meraki brand film logo reveal"),
        ]), "grid-wide"),
        next_cta("Commercial Ads & Brand Films"), explore("commercial")])
    page(WORK_FILE["commercial"], "Commercial Brands & Ads Films",
         "Commercial ads and brand films by Storylane Studios, Mumbai — cinematic product and brand storytelling.",
         body, "work")

    # 2. Product photography (794-12022) — mosaic + lightbox
    mosaic = [("pp-glasses-peach", "Eyeglasses on a peach backdrop", 2, 2), ("pp-perfume-red", "Red perfume bottle under studio light", 3, 2),
              ("pp-mic", "Studio microphone with blue sound waves", 2, 2), ("pp-glasses-redlight", "Eyeglasses lit in red", 5, 2),
              ("pp-glasses-orange", "Clear frames on an orange backdrop", 4, 4), ("pp-headphones", "Headphones in blue light", 2, 2),
              ("pp-satan", "Satan perfume bottle product shot", 2, 4), ("pp-dark-red", "Moody red-lit product still", 2, 3),
              ("pp-sunglasses", "Two pairs of sunglasses on orange and cream", 2, 2), ("pp-glasses-drops", "Eyeglasses with water droplets", 2, 2),
              ("pp-glasses-teal", "Tortoise frames on teal", 2, 2), ("pp-watch", "Black chronograph watch on mesh", 2, 2),
              ("pp-glasses-tortoise", "Tortoise eyeglasses on a split backdrop", 6, 3), ("pp-drinks", "Three craft soda bottles", 2, 3),
              ("pp-glasses-purple", "Metal frames under purple light", 2, 2), ("pp-perfume-black", "Perfume bottle with dramatic shadow", 2, 2),
              ("pp-glasses-round", "Round tortoise frames on peach and violet", 3, 2), ("pp-glasses-white", "White frames on a blue backdrop", 3, 2)]
    items = "\n".join(
        f'          <button type="button" class="media-tile tile-in" style="--c:{c};--r:{r};--i:{i % 6}" data-full="assets/img/work/{s}.webp" aria-label="Open full image: {a}">'
        f'<img src="assets/img/work/{s}.webp" alt="{a}" loading="lazy"></button>'
        for i, (s, a, c, r) in enumerate(mosaic))
    hint = 'Click to open the full view image <svg viewBox="0 0 24 24" aria-hidden="true"><rect x="7" y="3" width="10" height="18" rx="5"/><path d="M12 7v4"/></svg>'
    body = "\n".join([cat_hero("Product Photography"), block("Our Selected Work", items, "mosaic", hint),
                      next_cta("Product Photography"), explore("product")])
    page(WORK_FILE["product"], "Product Photography",
         "Product photography by Storylane Studios — eyewear, fragrance, audio and beverage shoots that make products feel premium.",
         body, "work")

    # 3. Websites (827-7976)
    body = "\n".join([cat_hero("Websites &amp; Digital Experiences"),
                      block("Our Selected Work", tiles([("websites-eysta", "Eysta eyewear website — Frames Fresher Than the Rain")]), "grid-wide"),
                      next_cta("Websites & Digital Experiences"), explore("websites")])
    page(WORK_FILE["websites"], "Websites & Digital Experiences",
         "Websites and digital experiences designed and built by Storylane Studios.", body, "work")

    # 4. Short-form (830-8650)
    curve = tiles([("reel-eysta-group", "Eysta community reel"), ("reel-share", "When You Have Enough, Just Share It With Others reel"),
                   ("reel-sunglass-wall", "Eyewear store wall reel"), ("reel-sunset", "Couple watching the sunset reel"),
                   ("reel-two-friends", "Two friends sharing a snack by the sea reel")])
    ai = tiles([("reel-ai-ladders", "AI-generated reel of climbers on giant sunglasses"), ("reel-ai-diwali", "AI-assisted Diwali gifting reel")])
    body = "\n".join([cat_hero("Short - Form Content &amp; Reels"), block("Our Selected Work", curve, "curve-row"),
                      block("Storytelling Through AI", ai, "ai-reels"),
                      next_cta("Short-Form Content & Reels"), explore("reels")])
    page(WORK_FILE["reels"], "Short-Form Content & Reels",
         "Short-form content and reels by Storylane Studios — scroll-stopping stories, including AI-assisted storytelling.", body, "work")

    # 5. Brand integration (841-8555)
    body = "\n".join([cat_hero("Brand Integration Campaigns"),
                      block("Our Selected Work", tiles([("reel-pottery-group", "Brand integration reel at a pottery studio"),
                                                        ("reel-pottery-wheel", "Pottery wheel brand integration reel"),
                                                        ("reel-pottery-couple", "Couple at the pottery wheel reel"),
                                                        ("reel-flowers", "Couple with roses brand integration reel")]), "grid-reels"),
                      next_cta("Brand Integration Campaigns"), explore("brand")])
    page(WORK_FILE["brand"], "Brand Integration Campaigns",
         "Brand integration campaigns by Storylane Studios — brands woven naturally into stories audiences love.", body, "work")

    # 6. Social media (843-9171)
    phones = tiles([(f"ig-grid-{i}", f"Instagram grid managed by Storylane Studios ({n})") for i, n in
                    [(1, "eysta.eyewear"), (2, "eysta.eyewear"), (3, "eysta.eyewear"), (4, "powertrade_academy"), (5, "powertrade_academy")]])
    posters = tiles([("poster-worth-the-mess", "Worth the Mess film poster"), ("poster-perfect-time", "Perfect Time film poster"),
                     ("poster-trade-smarter", "Trade Smarter, Not Blindly social poster"), ("poster-option-trading", "Option Trading Signals social poster"),
                     ("poster-forex", "Forex Trading course poster")])
    body = "\n".join([cat_hero("Social Media Management"), block("Our Selected Instagram Grid Work", phones, "grid-five phones"),
                      block("Our Selected Poster Work", posters, "grid-five posters"),
                      next_cta("Social Media Management & Content Strategy"), explore("social")])
    page(WORK_FILE["social"], "Social Media Management",
         "Social media management by Storylane Studios — Instagram grids and poster design for growing brands.", body, "work")


# ---------------------------------------------------------------------------
# Story DNA service page (753-6944)
# ---------------------------------------------------------------------------
def story_dna() -> None:
    packages = [
        ("Presence", ["Logo suite", "Brand guidelines", "Social media kit<br>(Bio, highlights, etc.)", "Brand story and voice"], False),
        ("Identity", ["Logo design (3 concepts)", "Color palette", "Typography guide", "Business card design"], True),
        ("Legacy", ["Complete brand identity", "Brand strategy", "Brand voice &amp; tone", "Competitors analysis"], False),
    ]
    pk = []
    for name, feats, featured in packages:
        lis = "\n".join(f"              <li>{CHECK}<span>{f}</span></li>" for f in feats)
        badge = '\n            <span class="pkg-badge">Highly Recommended</span>' if featured else ""
        cls = "pkg pkg--featured" if featured else "pkg"
        pk.append(f"""          <article class="{cls}">{badge}
            <h3>{name}</h3>
            <ul>
{lis}
            </ul>
            <a class="btn-outline" href="contact.html?service=Brand%20Identity%20%26%20Positioning&amp;package={name}">Get Quotation {DOC}</a>
          </article>""")
    others = [("Story Destination", "Websites &amp; Digital Experiences", "web", WORK_FILE["websites"]),
              ("Story Creation", "Commercial Ads &amp; Brand Films", "film", WORK_FILE["commercial"]),
              ("Story In Every Frame", "Product Photography", "camera", WORK_FILE["product"]),
              ("Storytelling Reels", "Short-Form Content &amp; Reels", "reel", WORK_FILE["reels"]),
              ("Story Chapters", "Social Media Management &amp; Content Strategy", "phone", WORK_FILE["social"]),
              ("Stories That Sell", "Brand Integration Campaigns", "tag", WORK_FILE["brand"]),
              ("Story Reach", "Performance Marketing", "chart", "index.html#services"),
              ("Story Motion", "Film Production", "clap", "index.html#services")]
    mq = "\n".join(f'            <a class="mq-item" href="{h}"><span class="step-icon">{ICONS[ic]}</span><span><strong>{t}</strong><span class="sub">{s}</span></span></a>'
                   for t, s, ic, h in others)
    arrow_l = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M11 5 4 12l7 7v-4h9V9h-9z"/></svg>'
    arrow_r = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m13 5 7 7-7 7v-4H4V9h9z"/></svg>'
    who = ["New Businesses", "Startups", "Rebranding", "Growing Brands", "Established Businesses"]
    body = f"""    <section class="svc-hero" aria-labelledby="page-title">
      <img src="assets/img/pages/story-dna-hero.webp" alt="" width="1920" height="1440" fetchpriority="high">
      <div class="container">
        <p class="eyebrow eyebrow--auto"><span>Story DNA : Brand Identity &amp; Positioning</span></p>
        <h1 id="page-title" class="display">Every Great Story Starts<br> <span class="grad">with A Strong Identity.</span></h1>
        <p class="lead">Your brand is more than a logo. We help define the personality, voice, visuals, and positioning that make your business recognizable, memorable, and impossible to ignore.</p>
        <a class="btn-amber" href="contact.html?service=Brand%20Identity%20%26%20Positioning">Get Quotation {DOC}</a>
      </div>
    </section>

    <section class="svc-section" aria-label="Problem and solution">
      <div class="container">
        <div class="ps-panel reveal">
          <div>
            <h3>Without a Clear identity,<br>every marketing effort<br>feels disconnected.</h3>
            <p>Many businesses invest in content, websites, and advertising before defining who they are as a brand.</p>
          </div>
          <div class="ps-labels" aria-hidden="true"><span>{arrow_l} Problem</span><span>Solution {arrow_r}</span></div>
          <div>
            <h3>Give Your Brand a Clear<br>Identity to Build From.</h3>
            <p>Define what your brand stands for, how it sounds, how it looks, and how it wants to be remembered, creating a clear identity that brings consistency to everything you do.</p>
          </div>
        </div>
        <div class="handles reveal">
          <p class="eyebrow eyebrow--auto"><span>How Storylane Handles It</span></p>
          <h2>We Build Brands from the Story Within.</h2>
          <p>Instead of starting with colors, fonts, or logos, we start by understanding the business behind the brand. We uncover its story, ambition, audience, and personality. Then turn those insights into a brand identity that feels intentional, distinctive, and true to the business.</p>
        </div>
      </div>
    </section>

    <section class="svc-section" aria-labelledby="pkg-title">
      <div class="container">
        <p class="eyebrow eyebrow--auto" id="pkg-title"><span>Choose Your Package</span></p>
        <div class="packages" data-reveal>
{chr(10).join(pk)}
        </div>
      </div>
    </section>

    <section class="svc-section" aria-labelledby="who-title">
      <div class="container">
        <p class="eyebrow eyebrow--auto" id="who-title"><span>Who Is It For?</span></p>
        <ul class="chips">
{chr(10).join(f'          <li class="chip">{w}</li>' for w in who)}
        </ul>
      </div>
    </section>

    <section class="cta cta--next" style="margin-top:clamp(64px,6.9vw,100px)" aria-labelledby="cta-title">
      <div class="container">
        <h2 id="cta-title" class="display">Ready to Start Your Story?</h2>
        <p>No pressure. No obligation.<br>Just a conversation about what’s possible.</p>
        <a class="btn-amber" href="contact.html">Let’s Talk</a>
      </div>
    </section>

    <section class="explore" aria-labelledby="other-title">
      <div class="container">
        <p class="eyebrow eyebrow--auto" id="other-title"><span>Explore Other Services</span></p>
      </div>
      <div class="marquee">
        <div class="marquee-track">
{mq}
        </div>
      </div>
    </section>"""
    page("story-dna.html", "Story DNA: Brand Identity & Positioning",
         "Story DNA by Storylane Studios — brand identity and positioning packages: Presence, Identity and Legacy.",
         body, "services", "assets/img/pages/story-dna-hero.webp")


# ---------------------------------------------------------------------------
# Contact page (765-9991)
# ---------------------------------------------------------------------------
def contact() -> None:
    opts = "\n".join(f'                  <option>{e(o)}</option>' for o in SERVICE_OPTIONS)
    heart = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10z"/>'
             '<path d="m9 12 2 2 4-4"/></svg>')
    cards = [("Email", CONTACT["email"], f"mailto:{CONTACT['email']}", "mail", False),
             ("Phone", CONTACT["phone"], f"tel:{CONTACT['tel']}", "call", False),
             ("WhatsApp", CONTACT["phone"], CONTACT["wa"], "whatsapp", False),
             ("Instagram", CONTACT["ig_handle"], CONTACT["ig"], "insta", False),
             ("Location", "Based in Mumbai. Building stories for brands across India.", "", "pin", True)]
    card_html = []
    for title, val, href, ic, full in cards:
        cls = "contact-card" + (" contact-card--full" if full else "")
        ext = ' target="_blank" rel="noopener"' if href.startswith("http") else ""
        tag_open = f'<a class="{cls}" href="{href}"{ext}>' if href else f'<div class="{cls}">'
        tag_close = "</a>" if href else "</div>"
        card_html.append(f'          {tag_open}<div><h2>{title}</h2><p>{e(val)}</p></div><span class="step-icon">{ICONS[ic]}</span>{tag_close}')
    body = f"""    <section class="contact-hero" aria-labelledby="page-title">
      <div class="glow-stripes" aria-hidden="true"></div>
      <div class="container contact-grid">
        <div>
          <p class="eyebrow"><span>Contact</span></p>
          <h1 id="page-title" class="display">Every Great Story<br> Starts with A<br> <span class="grad">Conversation.</span></h1>
          <figure class="contact-photo reveal">
            <img src="assets/img/studio-still.webp" alt="Ayush Jain, founder of Storylane Studios" width="1600" height="900">
          </figure>
        </div>
        <div class="contact-side">
          <p class="lead underline">Tell us about your brand, your goals, and the challenges you’re facing. We’ll help you find the right path forward.</p>
          <form class="form-card" id="contact-form" novalidate data-to="{CONTACT['email']}">
            <div class="form-grid">
              <div class="field">
                <label for="f-name">Your Name*</label>
                <input id="f-name" name="name" type="text" autocomplete="name" placeholder="Enter Full Name" required>
                <span class="err">Please enter your name.</span>
              </div>
              <div class="field">
                <label for="f-email">Email*</label>
                <input id="f-email" name="email" type="email" autocomplete="email" placeholder="Enter Valid Email Address" required>
                <span class="err">Please enter a valid email address.</span>
              </div>
              <div class="field">
                <label for="f-phone">Phone*</label>
                <input id="f-phone" name="phone" type="tel" autocomplete="tel" placeholder="Enter Contact Number" required pattern="[0-9+()\\-\\s]{{7,}}">
                <span class="err">Please enter a contact number.</span>
              </div>
              <div class="field">
                <label for="f-brand">Brand / Company*</label>
                <input id="f-brand" name="brand" type="text" autocomplete="organization" placeholder="Enter Brand / Company Name" required>
                <span class="err">Please enter your brand or company.</span>
              </div>
              <div class="field field--full">
                <label for="f-service">What do you need help with?*</label>
                <select id="f-service" name="service" required>
                  <option value="" disabled selected>Select Service</option>
{opts}
                </select>
                <span class="err">Please choose a service.</span>
              </div>
              <div class="field field--full">
                <label for="f-msg">Tell us about your brand *</label>
                <textarea id="f-msg" name="message" placeholder="Your Brand, your goals, and the challenges you’re facing." required></textarea>
                <span class="err">Please tell us a little about your brand.</span>
              </div>
            </div>
            <button class="btn-amber" type="submit">Connect With Us {heart}</button>
            <p class="form-status" role="status" aria-live="polite"></p>
          </form>
        </div>
      </div>
      <div class="container contact-cards">
{chr(10).join(card_html)}
      </div>
    </section>"""
    page("contact.html", "Contact", "Contact Storylane Studios, Mumbai — tell us about your brand and start your story.", body)


# ---------------------------------------------------------------------------
# index.html: shared header/footer blocks
# ---------------------------------------------------------------------------
def sync_index() -> None:
    p = ROOT / "index.html"
    s = p.read_text(encoding="utf-8")
    s = re.sub(r"<!-- @header -->.*?<!-- /@header -->", lambda m: header("", "home"), s, flags=re.S)
    s = re.sub(r"<!-- @footer -->.*?<!-- /@footer -->", lambda m: footer(""), s, flags=re.S)
    p.write_text(s, encoding="utf-8", newline="\n")
    print("synced index.html header/footer")


if __name__ == "__main__":
    work_pages()
    story_dna()
    contact()
    sync_index()
