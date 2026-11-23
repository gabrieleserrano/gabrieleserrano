#!/usr/bin/env python3
"""Genera le card SVG animate del profilo GitHub di Gabriele Serrano.

  python3 gen.py              → usa i dati reali (serve GH_TOKEN con scope read:user)
  DEMO=1 python3 gen.py       → dati finti, per provare il layout
  STATIC=1 python3 gen.py     → nessuna animazione (per gli screenshot)

Unica dipendenza: fonttools (pip install fonttools).
"""
import base64, io, json, os, random, urllib.request
from datetime import date, timedelta
from html import escape
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont

# ───────────────────────── CONFIG ─────────────────────────
LOGIN = os.environ.get("GH_LOGIN", "gabrieleserrano")
FIRST, LAST = "Gabriele", "Serrano"
KICKER = "VP of Technology · Palella Holdings"
TAGLINE = ["CTO at La Sicilia & PalComm.",
           "I build tech products from Sicily to the world."]
LINK = "palella.com/team/gabrieleserrano"
LINKS = [  # (etichetta, testo, file)
    ("WEBSITE", "palella.com/team/gabrieleserrano", "link-website.svg"),
    ("LINKEDIN", "in/gabriele-serrano", "link-linkedin.svg"),
]
TITLE, TITLE_ACCENT = "Fuelled by", "Etna"
# ──────────────────────────────────────────────────────────

ROOT = Path(__file__).parent
OUT = Path(os.environ.get("OUT", ROOT / "cards"))
STATIC = os.environ.get("STATIC") == "1"
DEMO = os.environ.get("DEMO") == "1"

W = 1000  # larghezza di tutte le card

PALETTE = """
:root{--card:#f4efe8;--line:#e4dbd0;--ink:#1b1714;--mut:#6f6359;--acc:#d9480f;--acc2:#f59f00;
--h0:#e6ddd2;--h1:#ffd3b4;--h2:#ffa56b;--h3:#ee6420;--h4:#b23d08}
@media (prefers-color-scheme: dark){:root{--card:#171310;--line:#2c241f;--ink:#f3ece4;--mut:#9c8f84;--acc:#ff7a2f;--acc2:#ffc04d;
--h0:#28201b;--h1:#552410;--h2:#933812;--h3:#e5560d;--h4:#ffa25c}}
"""

# ───────────── font: sottoinsieme incorporato in base64 ─────────────
def font_face(family, file, text, style="normal", weight=400):
    f = TTFont(ROOT / "fonts" / file)
    opts = subset.Options(); opts.flavor = "woff"; opts.layout_features = ["kern", "liga"]
    s = subset.Subsetter(opts); s.populate(text=text + " "); s.subset(f)
    buf = io.BytesIO(); f.flavor = "woff"; f.save(buf)
    b64 = base64.b64encode(buf.getvalue()).decode()
    return (f"@font-face{{font-family:'{family}';font-style:{style};font-weight:{weight};"
            f"src:url(data:font/woff;base64,{b64}) format('woff')}}")


SERIF = "'Fraunces',Georgia,serif"
MONO = "'JBMono',ui-monospace,Menlo,monospace"
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"

BASE = """
.card{fill:var(--card)}
.ink{fill:var(--ink)} .mut{fill:var(--mut)} .acc{fill:var(--acc)}
.in{opacity:0;animation:in .9s cubic-bezier(.2,.7,.2,1) forwards}
@keyframes in{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}
.fade{opacity:0;animation:fade .5s ease-out forwards}
@keyframes fade{to{opacity:1}}
@media (prefers-reduced-motion: reduce){.in,.fade{animation:none;opacity:1}}
"""
STATIC_CSS = ".in,.fade,.pop{animation:none!important;opacity:1!important;transform:none!important}"


def svg(h, body, css, fonts, w=None):
    w = w or W
    st = PALETTE + "".join(fonts) + BASE + css + (STATIC_CSS if STATIC else "")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            f"<style>{st}</style>"
            f'<rect class="card" width="{w}" height="{h}" rx="18"/>{body}</svg>')


def dl(s):
    return f'style="animation-delay:{s:.2f}s"'


# ───────────────────────── ritratto ASCII ─────────────────────────
RAMP = " .,:;-=+*cxo%#@"


def portrait_rows():
    raw = (ROOT / "assets" / "portrait_raw.txt").read_text().split()
    vals = [(ord(ch) - 97) / 25 for row in raw for ch in row if ch != "."]
    lo, hi = sorted(vals)[int(len(vals) * .02)], sorted(vals)[int(len(vals) * .98)]
    n = len(raw)
    light, dark = [], []
    for r, row in enumerate(raw):
        fade = min(1, (n - r) / 10)  # sfuma le ultime righe (spalle)
        lr, dr = "", ""
        for ch in row:
            if ch == ".":
                lr += " "; dr += " "; continue
            v = min(1, max(0, ((ord(ch) - 97) / 25 - lo) / (hi - lo)))
            ink_l = (1 - v) * fade          # tema chiaro: inchiostro = scuro
            ink_d = (0.15 + 0.85 * v) * fade  # tema scuro: inchiostro = chiaro
            lr += RAMP[round(ink_l * (len(RAMP) - 1))]
            dr += RAMP[round(ink_d * (len(RAMP) - 1))]
        light.append(lr.rstrip().replace(" ", "\u00a0")); dark.append(dr.rstrip().replace(" ", "\u00a0"))
    return light, dark


def hero():
    h = 440
    light, dark = portrait_rows()
    cols = max(len(r) for r in light + dark)
    pw = 372                       # larghezza del ritratto
    fs = pw / cols / 0.6           # JetBrains Mono: larghezza carattere = 0.6em
    lh = fs * 0.6 * 1.85           # proporzione delle celle campionate
    px, py = W - pw - 40, (h - lh * len(light)) / 2 + fs * 0.8

    def block(rows, cls):
        out = [f'<g class="{cls}" font-family="{MONO}" font-size="{fs:.2f}" xml:space="preserve">']
        for i, r in enumerate(rows):
            if r.replace("\u00a0", ""):
                out.append(f'<text class="fade ink" {dl(.5 + i * .022)} x="{px:.1f}" y="{py + i * lh:.1f}">{escape(r)}</text>')
        return "".join(out) + "</g>"

    css = """
.pd{display:none} @media (prefers-color-scheme: dark){.pl{display:none}.pd{display:inline}}
.sq{animation:blink 2.4s ease-in-out infinite} @keyframes blink{50%{opacity:.35}}
"""
    fonts = [
        font_face("Fraunces", "fraunces-latin-400-normal.woff", FIRST + TITLE),
        font_face("Fraunces", "fraunces-latin-400-italic.woff", LAST + TITLE_ACCENT, "italic"),
        font_face("JBMono", "jetbrains-mono-latin-400-normal.woff",
                  KICKER.upper() + RAMP + "\u00a0"),
    ]
    body = f'''
<defs><linearGradient id="lava" x1="0" x2="1">
<stop offset="0" stop-color="var(--acc)"/><stop offset=".42" stop-color="var(--acc)"/>
<stop offset=".5" stop-color="var(--acc2)"/><stop offset=".58" stop-color="var(--acc)"/><stop offset="1" stop-color="var(--acc)"/>
{"" if STATIC else '<animateTransform attributeName="gradientTransform" type="translate" values="-1 0;1 0" dur="3.5s" begin="1.4s" repeatCount="indefinite"/>'}
</linearGradient></defs>
<g class="in" {dl(0)}><rect class="acc sq" x="48" y="52" width="9" height="9" rx="1.5"/>
<text class="mut" x="68" y="61" font-family="{MONO}" font-size="13" letter-spacing="1.6">{escape(KICKER.upper())}</text></g>
<text class="ink in" {dl(.15)} x="42" y="168" font-family="{SERIF}" font-size="104" letter-spacing="-3">{escape(FIRST)}</text>
<text class="in" {dl(.35)} x="40" y="268" font-family="{SERIF}" font-style="italic" font-size="104" letter-spacing="-3" fill="url(#lava)">{escape(LAST)}</text>
<g class="in" {dl(.6)} font-family="{SANS}" font-size="19">
<text class="ink" x="48" y="346">{escape(TAGLINE[0])}</text>
<text class="ink" x="48" y="372">{escape(TAGLINE[1])}</text></g>
{block(light, "pl")}{block(dark, "pd")}
'''
    return svg(h, body, css, fonts)


# ───────────────────────── dati contributi ─────────────────────────
def fetch_calendar():
    if DEMO:
        rnd = random.Random(7)
        end = date.today(); start = end - timedelta(days=364 + (end.weekday() + 1) % 7)
        since = date(2026, 5, 13)
        days, d = [], start
        while d <= end:
            if d < since: n = 0
            else:
                base = 6 if d.weekday() < 5 else 1.5
                n = max(0, int(rnd.gauss(base, 4))) if rnd.random() > .12 else 0
            days.append((d, n)); d += timedelta(days=1)
        return days
    q = """query($l:String!){user(login:$l){contributionsCollection{contributionCalendar{
          weeks{contributionDays{date contributionCount}}}}}}"""
    req = urllib.request.Request("https://api.github.com/graphql",
        data=json.dumps({"query": q, "variables": {"l": LOGIN}}).encode(),
        headers={"Authorization": f"bearer {os.environ['GH_TOKEN']}", "Content-Type": "application/json"})
    data = json.load(urllib.request.urlopen(req))
    weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    return [(date.fromisoformat(x["date"]), x["contributionCount"]) for w in weeks for x in w["contributionDays"]]


def activity(days):
    cell, gap = 14, 3
    weeks = []
    for d, n in days:
        if not weeks or d.weekday() == 6:  # le settimane GitHub iniziano di domenica
            weeks.append([])
        weeks[-1].append((d, n))
    weeks = weeks[-53:]
    nz = sorted(n for _, n in days if n)
    q = [nz[int(len(nz) * p)] for p in (.25, .5, .75)] if nz else [1, 2, 3]
    lvl = lambda n: 0 if n == 0 else 1 + sum(n > t for t in q)
    total = sum(n for _, n in days)

    gw = len(weeks) * (cell + gap) - gap
    x0, y0 = (W - gw) / 2, 128
    h = y0 + 7 * (cell + gap) + 64
    css = """.pop{opacity:0;animation:pop .5s cubic-bezier(.2,.8,.2,1.2) forwards;transform-box:fill-box;transform-origin:center}
@keyframes pop{from{opacity:0;transform:scale(.3)}to{opacity:1;transform:none}}
@media (prefers-reduced-motion: reduce){.pop{animation:none;opacity:1}}"""
    fonts = [
        font_face("Fraunces", "fraunces-latin-400-normal.woff", TITLE),
        font_face("Fraunces", "fraunces-latin-400-italic.woff", TITLE_ACCENT, "italic"),
        font_face("JBMono", "jetbrains-mono-latin-400-normal.woff",
                  "REFRESHED DAILYlessmore JanFebMarAprMayJunJulAugSepOctNovDec contributions in the last 12 months0123456789,·"),
    ]
    parts = [f'''
<g class="in"><text x="{x0 - 2:.0f}" y="74" font-family="{SERIF}" font-size="40" letter-spacing="-1"><tspan class="ink">{escape(TITLE)} </tspan><tspan class="acc" font-style="italic">{escape(TITLE_ACCENT)}</tspan></text>
<text class="mut" x="{x0:.0f}" y="100" font-family="{MONO}" font-size="12.5" letter-spacing="1">{total:,} contributions in the last 12 months</text>
<text class="mut" x="{x0 + gw:.0f}" y="72" font-family="{MONO}" font-size="12.5" letter-spacing="1.6" text-anchor="end">REFRESHED DAILY</text></g>''']
    last_month = None
    for i, wk in enumerate(weeks):
        x = x0 + i * (cell + gap)
        g = [f'<g class="pop" {dl(.25 + i * .022)}>']
        for d, n in wk:
            y = y0 + ((d.weekday() + 1) % 7) * (cell + gap)
            g.append(f'<rect x="{x:.1f}" y="{y}" width="{cell}" height="{cell}" rx="3" fill="var(--h{lvl(n)})"/>')
        parts.append("".join(g) + "</g>")
        m = wk[0][0].month
        lx = x0 + gw - 5 * (cell + gap) - 38
        if m != last_month and wk[0][0].day <= 7 and x < lx - 70:
            parts.append(f'<text class="mut fade" {dl(.4 + i * .022)} x="{x:.1f}" y="{y0 + 7 * (cell + gap) + 22}" font-family="{MONO}" font-size="12">{wk[0][0]:%b}</text>')
        last_month = m
    ly = y0 + 7 * (cell + gap) + 11
    lx = x0 + gw - 5 * (cell + gap) - 38
    leg = [f'<g class="fade" {dl(1.6)}><text class="mut" x="{lx - 8:.0f}" y="{ly + 11}" font-family="{MONO}" font-size="12" text-anchor="end">less</text>']
    for k in range(5):
        leg.append(f'<rect x="{lx + k * (cell + gap):.1f}" y="{ly}" width="{cell}" height="{cell}" rx="3" fill="var(--h{k})"/>')
    leg.append(f'<text class="mut" x="{lx + 5 * (cell + gap) + 5:.0f}" y="{ly + 11}" font-family="{MONO}" font-size="12">more</text></g>')
    return svg(h, "".join(parts) + "".join(leg), css, fonts)


def link_card(i, label, text):
    w, h = 494, 84
    fonts = [font_face("JBMono", "jetbrains-mono-latin-400-normal.woff", label + text + "↗")]
    css = ".arr{animation:nudge 2.4s ease-in-out infinite}@keyframes nudge{50%{transform:translate(3px,-3px)}}@media (prefers-reduced-motion: reduce){.arr{animation:none}}"
    body = f'''<g class="in" {dl(.2 + i * .15)} font-family="{MONO}">
<text class="mut" x="32" y="36" font-size="12" letter-spacing="1.6">{escape(label)}</text>
<text class="ink" x="32" y="61" font-size="16">{escape(text)}</text>
<text class="acc arr" x="{w - 32}" y="50" font-size="20" text-anchor="end">↗</text></g>'''
    return svg(h, body, css, fonts, w)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "hero.svg").write_text(hero())
    for i, (label, text, name) in enumerate(LINKS):
        (OUT / name).write_text(link_card(i, label, text))
    (OUT / "activity.svg").write_text(activity(fetch_calendar()))
    for p in sorted(OUT.glob("*.svg")):
        print(f"{p.name}: {p.stat().st_size // 1024} KB")
