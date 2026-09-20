#!/usr/bin/env python3
"""
Generates the SVG assets for the profile README ("engineer's notebook" edition).

    pip install fonttools brotli
    python3 tools/generate.py             -> ./assets/*-light.svg and *-dark.svg
    python3 tools/generate.py --static    -> ./assets_static (no animation, for layout previews)

Everything is transparent so it sits directly on GitHub's page. Each graphic is built
twice (light and dark); the README picks one with <picture>. Fonts are subset and embedded
as data URIs, so they render without any network request.

Edit the CONTENT block, re-run, commit.
"""
import base64
import io
import math
import os
import sys
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

from fontTools import subset
from fontTools.ttLib import TTFont

STATIC = "--static" in sys.argv
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "assets_static" if STATIC else "assets")
FONT_DIR = os.path.join(HERE, "fonts")
os.makedirs(OUT, exist_ok=True)

# ───────────────────────────── CONTENT ─────────────────────────────
NAME = "Aadarsh Mishra"
GREETING = "hi, I'm"
TAGLINE = "Full-stack developer."
SUBLINE = "Building full products end to end."
STATUS_OPEN = "open to internships and teams that ship"
STATUS_NOW = "currently deep in Terminal-Talk"
PIPELINE = ["frontend", "backend", "auth", "deploys"]
PIPELINE_NOTE = "start to finish"

PROJECTS = [
    dict(
        key="revive", motif="revive", status="buildathon project", live=False,
        title="Revive AI",
        tagline="Autonomous revenue recovery for Razorpay.",
        body="The AI only recommends. A deterministic policy engine decides, and every execution "
             "is gated by a live Razorpay re-check. A deliberate 5-webhook concurrency storm "
             "exposed a real race condition; the root cause was found and fixed before shipping.",
        url="github.com/Aadarsh6/Revenue-Recover-Razorpay-AI",
    ),
    dict(
        key="terminal-talk", motif="tt", status="in progress", live=True,
        title="Terminal-Talk",
        tagline="Peer-to-peer encrypted chat on raw TCP sockets.",
        body="No WebRTC, no framework hiding the network layer. Custom framing, persistent "
             "identities, encrypted history, and a real NAT-traversal experiment that failed "
             "predictably and got measured instead of hidden.",
        url="github.com/Aadarsh6/Terminal-Talk",
    ),
    dict(
        key="focuszen", motif="focus", status="live", live=True,
        title="FocusZen",
        tagline="A focus-tracking Chrome extension.",
        body="Published on the Chrome Web Store, paired with a React dashboard for session analytics.",
        url="focuszen.aadarshm.me",
    ),
    dict(
        key="xcraft", motif="xc", status="web app", live=False,
        title="Xc Craft",
        tagline="Turns an idea into a ready-to-post X thread.",
        body="Structured threads with six tone profiles and three formats, published in one click "
             "through the Twitter API.",
        url="xcraft.aadarshm.me",
    ),
]

STACK = [
    ("languages", ["TypeScript", "JavaScript", "Python"]),
    ("frontend", ["React"]),
    ("backend", ["Node.js", "Express", "PostgreSQL", "Prisma"]),
    ("auth + realtime", ["OAuth", "WebSockets", "WebRTC"]),
    ("ship", ["Docker"]),
]

CONTACT_HEADLINE = ["Open to internships", "and teams that ship."]
EMAIL = "aadarshakmishra16@gmail.com"
CONTACT_NOTE = "4th-year BTech"
# ───────────────────────────────────────────────────────────────────

THEMES = {
    "light": dict(ink="#16181d", body="#3b414d", dim="#697080", rule="#d3d8df", faint="#b9c0cc", accent="#2b40e0"),
    "dark": dict(ink="#eceef3", body="#c2c8d3", dim="#8b94a4", rule="#30363d", faint="#4b5363", accent="#8fa1ff"),
}

FACES = {
    "d800": ("bricolage-grotesque-latin-800-normal.woff", 800),
    "d700": ("bricolage-grotesque-latin-700-normal.woff", 700),
    "d500": ("bricolage-grotesque-latin-500-normal.woff", 500),
    "d400": ("bricolage-grotesque-latin-400-normal.woff", 400),
    "mono": ("jetbrains-mono-latin-400-normal.woff", 400),
    "hand": ("just-another-hand-latin-400-normal.woff", 400),
}
FALLBACK = {
    "d": "'Bricolage Grotesque',-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif",
    "mono": "'JetBrains Mono',ui-monospace,SFMono-Regular,Menlo,Consolas,monospace",
    "hand": "'Just Another Hand','Segoe Print','Bradley Hand',cursive",
}

_measure_cache = {}


def _face(key):
    if key not in _measure_cache:
        f = TTFont(os.path.join(FONT_DIR, FACES[key][0]))
        _measure_cache[key] = (f.getBestCmap(), f["hmtx"], f["head"].unitsPerEm)
    return _measure_cache[key]


def width(key, size, text):
    cmap, hmtx, upem = _face(key)
    total = 0
    for ch in text:
        g = cmap.get(ord(ch))
        total += hmtx[g][0] if g else upem * 0.5
    return total * size / upem


def wrap(key, size, text, max_w):
    lines, cur = [], ""
    for word in text.split():
        trial = (cur + " " + word).strip()
        if width(key, size, trial) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    lines.append(cur)
    return lines


def subset_b64(key, chars):
    font = TTFont(os.path.join(FONT_DIR, FACES[key][0]))
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.layout_features = ["kern"]
    opts.name_IDs = []
    opts.notdef_outline = True
    sub = subset.Subsetter(opts)
    sub.populate(text="".join(sorted(set(chars))) + " ")
    sub.subset(font)
    font.flavor = "woff2"
    buf = io.BytesIO()
    font.save(buf)
    return base64.b64encode(buf.getvalue()).decode()


def fnum(x, places=2):
    s = f"{x:.{places}f}".rstrip("0").rstrip(".")
    return s if s not in ("", "-0") else "0"


def A(s):
    return "" if STATIC else s


def blink():
    return A('<animate attributeName="opacity" values="1;0" keyTimes="0;0.5" calcMode="discrete" dur="1.1s" repeatCount="indefinite"/>')


class Doc:
    def __init__(self, w, h, title, T):
        self.w, self.h, self.title, self.T = w, h, title, T
        self.used = {}

    def txt(self, face, size, x, y, s, fill, anchor="start", rot=None, extra=""):
        self.used.setdefault(face, set()).update(s)
        tr = f' transform="rotate({rot} {fnum(x)} {fnum(y)})"' if rot else ""
        an = f' text-anchor="{anchor}"' if anchor != "start" else ""
        return f'<text class="{face}" x="{fnum(x)}" y="{fnum(y)}" font-size="{size}" fill="{fill}"{an}{tr}{extra}>{escape(s)}</text>'

    def render(self, body):
        css = []
        for face, chars in self.used.items():
            wt = FACES[face][1]
            fb = FALLBACK["d" if face.startswith("d") else face]
            css.append(f"@font-face{{font-family:'f-{face}';src:url(data:font/woff2;base64,{subset_b64(face, chars)}) format('woff2');font-weight:{wt};}}")
            css.append(f".{face}{{font-family:'f-{face}',{fb};font-weight:{wt};}}")
        label = escape(self.title, {'"': "&quot;"})
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}" role="img" aria-label="{label}">\n'
            f"<title>{escape(self.title)}</title>\n<style>{''.join(css)}</style>\n{body}\n</svg>\n"
        )


def validate(name, s):
    root = ET.fromstring(s)
    for el in root.iter():
        if el.tag.split("}")[-1] in ("animate", "animateTransform"):
            v, k = el.get("values"), el.get("keyTimes")
            if v and k:
                vs, ks = v.split(";"), [float(x) for x in k.split(";")]
                assert len(vs) == len(ks), f"{name}: values/keyTimes mismatch"
                assert ks[0] == 0 and all(b > a for a, b in zip(ks, ks[1:])), f"{name}: bad keyTimes"
                if el.get("calcMode") != "discrete":
                    assert ks[-1] == 1, f"{name}: linear keyTimes must end at 1"


def write(name, s):
    validate(name, s)
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as fh:
        fh.write(s)
    print(f"  {name:34s} {len(s) / 1024:5.1f} KB")


# ───────────────────────────── drawing helpers ─────────────────────
def line(x1, y1, x2, y2, col, w=1.3, dash=None, op=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    o = f' stroke-opacity="{op}"' if op else ""
    return f'<line x1="{fnum(x1)}" y1="{fnum(y1)}" x2="{fnum(x2)}" y2="{fnum(y2)}" stroke="{col}" stroke-width="{w}" stroke-linecap="round"{d}{o}/>'


def circle(x, y, r, stroke=None, fill="none", w=1.4, dash=None):
    st = f' stroke="{stroke}" stroke-width="{w}"' if stroke else ""
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<circle cx="{fnum(x)}" cy="{fnum(y)}" r="{r}" fill="{fill}"{st}{d}/>'


def cross(x, y, s, col, w=1.6):
    return line(x - s, y - s, x + s, y + s, col, w) + line(x - s, y + s, x + s, y - s, col, w)


def harrow(T, p0, c1, c2, p1, head=7):
    ang = math.atan2(p1[1] - c2[1], p1[0] - c2[0])
    a1 = (p1[0] + head * math.cos(ang + math.radians(150)), p1[1] + head * math.sin(ang + math.radians(150)))
    a2 = (p1[0] + head * math.cos(ang - math.radians(150)), p1[1] + head * math.sin(ang - math.radians(150)))
    return (f'<path d="M{p0[0]} {p0[1]} C{c1[0]} {c1[1]} {c2[0]} {c2[1]} {p1[0]} {p1[1]} '
            f'M{a1[0]:.1f} {a1[1]:.1f} L{p1[0]} {p1[1]} L{a2[0]:.1f} {a2[1]:.1f}" fill="none" '
            f'stroke="{T["accent"]}" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>')


def traveller(T, path, dur, static_pt, begin=0, r=3.5):
    col = T["accent"]
    if STATIC:
        return f'<circle cx="{static_pt[0]}" cy="{static_pt[1]}" r="{r}" fill="{col}"/>'
    return (f'<g opacity="0"><circle r="{r + 3.5}" fill="{col}" opacity=".18"/><circle r="{r}" fill="{col}"/>'
            f'<animateMotion path="{path}" dur="{dur}s" begin="{begin}s" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.1;0.9;1" dur="{dur}s" begin="{begin}s" repeatCount="indefinite"/></g>')


def pulse(T, x, y, r=3.5):
    col = T["accent"]
    ring = A(f'<circle cx="{x}" cy="{y}" r="{r}" fill="none" stroke="{col}" stroke-width="1.2">'
             f'<animate attributeName="r" values="{r};{r * 3.2}" dur="2.4s" repeatCount="indefinite"/>'
             f'<animate attributeName="opacity" values=".7;0" dur="2.4s" repeatCount="indefinite"/></circle>')
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{col}"/>{ring}'


# ───────────────────────────── header ──────────────────────────────
def header(T):
    W, H = 900, 404
    d = Doc(W, H, f"{NAME}. {TAGLINE} {SUBLINE} {STATUS_OPEN}.", T)
    p = []
    p.append(d.txt("hand", 40, 2, 48, GREETING, T["accent"], rot=-4))
    p.append(d.txt("d800", 100, -3, 144, NAME, T["ink"]))
    p.append(d.txt("d500", 34, 0, 204, TAGLINE, T["ink"]))
    p.append(d.txt("d400", 20, 0, 240, SUBLINE, T["body"]))

    # status: what is true right now
    p.append(pulse(T, 5, 292, 3.5))
    p.append(d.txt("mono", 13, 18, 297, STATUS_OPEN, T["dim"]))
    p.append(d.txt("mono", 13, 0, 321, ">", T["dim"]))
    p.append(d.txt("mono", 13, 18, 321, STATUS_NOW, T["dim"]))
    cx = 18 + width("mono", 13, STATUS_NOW) + 5
    p.append(f'<rect x="{fnum(cx)}" y="310" width="8" height="15" fill="{T["accent"]}">{blink()}</rect>')

    # the through-line: what "end to end" means
    y = 362
    xs = [6 + i * (888 / (len(PIPELINE) - 1)) for i in range(len(PIPELINE))]
    for a, b in zip(xs, xs[1:]):
        p.append(line(a + 9, y, b - 9, y, T["dim"], 1.3, op=".55"))
    for i, (x, lab) in enumerate(zip(xs, PIPELINE)):
        last = i == len(xs) - 1
        p.append(circle(x, y, 5, stroke=T["accent"] if last else T["dim"], fill=T["accent"] if last else "none"))
        anchor = "start" if i == 0 else ("end" if last else "middle")
        lx = 0 if i == 0 else (900 if last else x)
        p.append(d.txt("mono", 12, lx, y + 27, lab, T["dim"], anchor=anchor))
    p.append(traveller(T, f"M{xs[0]} {y} L{xs[-1]} {y}", 9, (int(xs[1]), y)))
    p.append(d.txt("hand", 27, xs[1] + 60, y - 14, PIPELINE_NOTE, T["accent"], rot=-2))
    return d.render("\n".join(p))


# ───────────────────────────── section label ───────────────────────
def label(T, text):
    d = Doc(900, 34, text, T)
    return d.render(d.txt("mono", 12, 0, 22, text, T["dim"]))


# ───────────────────────────── diagrams ────────────────────────────
def diag_tt(d, T):
    ink, ac, y = T["dim"], T["accent"], 76
    s = [circle(24, y, 6, stroke=ink), circle(306, y, 6, stroke=ink)]
    s.append(line(31, y, 163, y, ink, 1.4))
    s.append(line(178, y, 299, y, T["faint"], 1.4, dash="2 6"))
    s.append(line(170, 34, 170, 118, ac, 1.4, dash="2 5"))
    s.append(cross(170, y, 5, ac))
    s.append(d.txt("mono", 11, 24, 100, "you", ink, anchor="middle"))
    s.append(d.txt("mono", 11, 306, 100, "peer", ink, anchor="middle"))
    s.append(d.txt("mono", 11, 170, 24, "NAT", ac, anchor="middle"))
    s.append(traveller(T, f"M31 {y} L163 {y}", 2.6, (96, y)))
    s.append(d.txt("hand", 27, 188, 126, "failed as predicted.", ac, rot=-2))
    s.append(d.txt("hand", 27, 188, 148, "measured it anyway.", ac, rot=-2))
    s.append(harrow(T, (198, 110), (190, 104), (182, 98), (176, 90)))
    return "".join(s)


def diag_revive(d, T):
    ink, ac, y = T["dim"], T["accent"], 88
    nx = [84, 160, 236, 312]
    s = []
    for off in (-40, -20, 0, 20, 40):
        s.append(line(0, y + off, 75, y, ink, 1.1, op=".7"))
    s.append(circle(nx[0], y, 8, stroke=ink, dash="3 3"))
    s.append(circle(nx[1], y, 8, stroke=ink))
    s.append(circle(nx[2], y, 8, stroke=ink))
    s.append(f'<path d="M{nx[2] - 3.5} {y + .5} l2.6 2.8 l4.6 -5.6" fill="none" stroke="{ac}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>')
    s.append(circle(nx[3], y, 5, stroke=ac, fill=ac))
    for a, b in zip(nx, nx[1:]):
        s.append(line(a + 10, y, b - (10 if b != nx[3] else 7), y, ink, 1.3, op=".8"))
    for x, lab in zip(nx, ["AI", "policy", "live check", "execute"]):
        s.append(d.txt("mono", 11, x, y + 28, lab, ink, anchor="middle"))
    s.append(traveller(T, f"M0 {y} L{nx[3]} {y}", 4.4, (120, y)))
    s.append(d.txt("hand", 27, 100, 34, "5 webhooks at once.", ac, rot=-2))
    s.append(d.txt("hand", 27, 100, 56, "found the race.", ac, rot=-2))
    s.append(harrow(T, (94, 48), (82, 54), (68, 60), (56, 68)))
    return "".join(s)


def diag_focus(d, T):
    ink, ac = T["dim"], T["accent"]
    pts = [(6, 104), (44, 92), (82, 100), (120, 66), (158, 78), (196, 46), (234, 60), (272, 30), (322, 40)]
    path = "M" + " L".join(f"{x} {y}" for x, y in pts)
    s = [line(0, 124, 330, 124, T["rule"], 1.2)]
    s.append(f'<path d="{path}" fill="none" stroke="{ink}" stroke-width="1.6" stroke-linejoin="round" stroke-linecap="round"/>')
    for x, y in pts[:-1]:
        s.append(circle(x, y, 2.6, stroke=ink, fill="none", w=1.3))
    s.append(circle(*pts[-1], 4.5, stroke=ac, fill=ac))
    s.append(d.txt("mono", 11, 0, 14, "focus sessions", ink))
    s.append(traveller(T, path, 6, (158, 78), r=3))
    s.append(d.txt("hand", 27, 118, 150, "live on the chrome web store", ac, rot=-1.5))
    s.append(harrow(T, (250, 134), (284, 128), (312, 100), (321, 52)))
    return "".join(s)


def diag_xc(d, T):
    ink, ac = T["dim"], T["accent"]
    s = [circle(10, 34, 5, stroke=ac, w=1.6)]
    s.append(f'<path d="M16 34 C 56 34, 66 30, 102 30" fill="none" stroke="{ac}" stroke-width="1.3" stroke-dasharray="2 5" stroke-linecap="round"/>')
    s.append(d.txt("mono", 11, 10, 58, "idea", ink, anchor="middle"))
    s.append(line(110, 34, 110, 126, ink, 1.3, op=".8"))
    posts = [(30, 176, 122), (78, 132, 92), (126, 188, 138)]
    for y, w1, w2 in posts:
        s.append(circle(110, y, 4.5, stroke=ink))
        s.append(line(126, y - 5, 126 + w1, y - 5, ink, 1.5))
        s.append(line(126, y + 6, 126 + w2, y + 6, ink, 1.5, op=".6"))
    s.append(traveller(T, "M110 34 L110 126", 3.8, (110, 78), r=3))
    s.append(d.txt("hand", 27, 0, 108, "idea in,", ac, rot=-2))
    s.append(d.txt("hand", 27, 0, 130, "thread out.", ac, rot=-2))
    return "".join(s)


DIAGRAMS = dict(tt=diag_tt, revive=diag_revive, focus=diag_focus, xc=diag_xc)


# ───────────────────────────── project rows ────────────────────────
def project_row(P, T):
    W = 900
    body_lines = wrap("d400", 15.5, P["body"], 492)
    last_y = 140 + 24 * (len(body_lines) - 1)
    url_y = last_y + 40
    H = max(url_y + 30, 232)
    d = Doc(W, H, f"{P['title']}. {P['tagline']} {P['body']} {P['url']}", T)
    s = [line(0, 0.5, W, 0.5, T["rule"], 1)]
    s.append(pulse(T, 5, 33, 3.5) if P["live"] else circle(5, 33, 3.5, fill=T["dim"]))
    s.append(d.txt("mono", 12, 18, 37, P["status"], T["dim"]))
    s.append(d.txt("d700", 36, -1, 82, P["title"], T["ink"]))
    s.append(d.txt("d500", 18, 0, 110, P["tagline"], T["ink"]))
    for i, ln in enumerate(body_lines):
        s.append(d.txt("d400", 15.5, 0, 140 + 24 * i, ln, T["body"]))
    s.append(d.txt("mono", 12, 0, url_y, P["url"], T["accent"]))
    oy = (H - 150) / 2 + 6
    s.append(f'<g transform="translate(560 {fnum(oy)})">{DIAGRAMS[P["motif"]](d, T)}</g>')
    return d.render("\n".join(s))


# ───────────────────────────── stack ───────────────────────────────
def stack(T):
    W, row_h, top = 900, 54, 44
    H = top + row_h * len(STACK) + 6
    d = Doc(W, H, "Stack: " + "; ".join(f"{k}: {', '.join(v)}" for k, v in STACK), T)
    s = [d.txt("mono", 12, 0, 22, "stack", T["dim"])]
    for i, (lab, items) in enumerate(STACK):
        y0 = top + i * row_h
        s.append(line(0, y0 + 0.5, W, y0 + 0.5, T["rule"], 1))
        s.append(d.txt("mono", 12, 0, y0 + 33, lab, T["dim"]))
        x = 230
        for it in items:
            s.append(d.txt("d500", 22, x, y0 + 35, it, T["ink"]))
            x += width("d500", 22, it) + 34
    return d.render("\n".join(s))


# ───────────────────────────── contact ─────────────────────────────
def contact(T):
    W, H = 900, 318
    d = Doc(W, H, f"{' '.join(CONTACT_HEADLINE)} {EMAIL}. {CONTACT_NOTE}.", T)
    s = [line(0, 0.5, W, 0.5, T["rule"], 1)]
    s.append(d.txt("d800", 60, -2, 104, CONTACT_HEADLINE[0], T["ink"]))
    s.append(d.txt("d800", 60, -2, 168, CONTACT_HEADLINE[1], T["ink"]))
    ew = width("d500", 30, EMAIL)
    s.append(d.txt("d500", 30, 0, 236, EMAIL, T["accent"]))
    s.append(line(0, 246, ew * 0.99, 246, T["accent"], 1.6))
    s.append(d.txt("mono", 12, 0, 284, CONTACT_NOTE, T["dim"]))
    return d.render("\n".join(s))


# ───────────────────────────── build ───────────────────────────────
if __name__ == "__main__":
    print(("Static previews" if STATIC else "Assets") + f" -> {os.path.normpath(OUT)}")
    for theme, T in THEMES.items():
        write(f"header-{theme}.svg", header(T))
        write(f"label-projects-{theme}.svg", label(T, "projects"))
        for P in PROJECTS:
            write(f"project-{P['key']}-{theme}.svg", project_row(P, T))
        write(f"stack-{theme}.svg", stack(T))
        write(f"contact-{theme}.svg", contact(T))
