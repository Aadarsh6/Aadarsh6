#!/usr/bin/env python3
"""
Generates every animated SVG used by the profile README.

    python3 tools/generate.py            -> writes ./assets/*.svg   (animated, what you ship)
    python3 tools/generate.py --static   -> writes ./assets_static (final-frame previews, for checking layout)

Edit the CONTENT block below (roles, projects, stack), re-run, commit.
No dependencies. Uses SMIL animation, which GitHub renders inside <img> tags.
"""
import json
import math
import os
import sys
import xml.etree.ElementTree as ET

STATIC = "--static" in sys.argv
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "assets_static" if STATIC else "assets")
os.makedirs(OUT, exist_ok=True)

# ───────────────────────────── CONTENT ─────────────────────────────
NAME = "Aadarsh Mishra"
ROLES = [
    "Full-stack developer",
    "4th-year BTech, AI/ML",
    "Building Terminal-Talk",
    "Frontend, backend, auth, deploys",
]
STATUS_PILLS = [
    ("Open to internships and teams that ship", "#5eead4"),
    ("Deep in Terminal-Talk", "#fbbf24"),
]
CONTACT_SITE = "aadarshm.me"
CONTACT_MAIL = "aadarshakmishra16@gmail.com"

PROJECTS = [
    dict(
        file="card-revive.svg", uid="rv", accent="#5eead4", motif="pipeline",
        tag="razorpay buildathon", live=False,
        title="Revive AI",
        tagline="Autonomous revenue recovery for Razorpay",
        body=[
            "AI only recommends. A deterministic policy",
            "engine decides, and every execution is gated",
            "by a live Razorpay re-check. A 5-webhook storm",
            "exposed a race condition, fixed before shipping.",
        ],
        chips=["Razorpay", "Webhooks", "Policy engine"],
    ),
    dict(
        file="card-terminal-talk.svg", uid="tt", accent="#fbbf24", motif="p2p",
        tag="in progress", live=True,
        title="Terminal-Talk",
        tagline="Peer-to-peer encrypted chat on raw TCP sockets",
        body=[
            "No WebRTC, no framework hiding the network layer.",
            "Custom framing, persistent identities, encrypted",
            "history. And a real NAT-traversal experiment that",
            "failed predictably, and got measured, not hidden.",
        ],
        chips=["Raw TCP", "Encrypted", "NAT traversal"],
    ),
    dict(
        file="card-focuszen.svg", uid="fz", accent="#818cf8", motif="ring",
        tag="on the chrome web store", live=True,
        title="FocusZen",
        tagline="Focus-tracking Chrome extension",
        body=[
            "Published on the Chrome Web Store, paired with a",
            "React dashboard for session analytics.",
        ],
        chips=["Chrome extension", "React", "Analytics"],
    ),
    dict(
        file="card-xcraft.svg", uid="xc", accent="#fb7185", motif="thread",
        tag="web app", live=False,
        title="Xc Craft",
        tagline="From idea to a ready-to-post X thread",
        body=[
            "Six tone profiles, three formats, and one-click",
            "publishing through the Twitter API.",
        ],
        chips=["Twitter API", "6 tones", "3 formats"],
    ),
]

STACK_ROW_1 = ["TypeScript", "JavaScript", "Python", "React", "Node.js", "Express"]
STACK_ROW_2 = ["PostgreSQL", "Docker", "Prisma", "OAuth", "WebSockets", "WebRTC"]
# ───────────────────────────────────────────────────────────────────

INK = "#0a0f1c"
TEXT = "#e6edf7"
SOFT = "#cbd5e1"
MUTED = "#8b9bb4"
TEAL, AMBER, INDIGO, CORAL = "#5eead4", "#fbbf24", "#818cf8", "#fb7185"
MONO = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', 'DejaVu Sans Mono', monospace"
SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"

with open(os.path.join(HERE, "icons.json")) as fh:
    ICONS = json.load(fh)


# ───────────────────────────── helpers ─────────────────────────────
def fnum(x, places=2):
    s = f"{x:.{places}f}".rstrip("0").rstrip(".")
    return s if s not in ("", "-0") else "0"


def A(s):
    """Animation markup only exists in the shipped version."""
    return "" if STATIC else s


def doc(w, h, title, defs, body):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{title}">
<title>{title}</title>
<defs>
<style>.m{{font-family:{MONO};}} .s{{font-family:{SANS};}}</style>
{defs}
</defs>
{body}
</svg>
"""


def validate(name, s):
    root = ET.fromstring(s)  # raises if not well-formed
    for el in root.iter():
        tag = el.tag.split("}")[-1]
        if tag in ("animate", "animateTransform"):
            v, k = el.get("values"), el.get("keyTimes")
            if v and k:
                vs, ks = v.split(";"), [float(x) for x in k.split(";")]
                assert len(vs) == len(ks), f"{name}: values/keyTimes length mismatch"
                assert ks[0] == 0, f"{name}: keyTimes must start at 0"
                assert all(b > a for a, b in zip(ks, ks[1:])), f"{name}: keyTimes not strictly increasing"
                if el.get("calcMode") != "discrete":
                    assert ks[-1] == 1, f"{name}: linear keyTimes must end at 1"


def write(name, s):
    validate(name, s)
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as fh:
        fh.write(s)
    print(f"  {name:28s} {len(s)/1024:5.1f} KB")


def blink():
    return A('<animate attributeName="opacity" values="1;0" keyTimes="0;0.5" calcMode="discrete" dur="1.1s" repeatCount="indefinite"/>')


def typing_steps(n, cw, x0=0.0):
    """Discrete stepping for typing n characters once. Returns (values, keyTimes)."""
    vals = ";".join(fnum(x0 + i * cw) for i in range(n + 1))
    kts = ";".join(fnum(i / (n + 1), 5) for i in range(n + 1))
    return vals, kts


def role_cycle(roles, type_dt=0.055, hold=1.9, del_dt=0.025, gap=0.3):
    """Timeline of (time, visible_chars) for every role. Returns per-role events, cursor events, cycle length."""
    t, per, cur = 0.0, [], []
    for r in roles:
        n = len(r)
        ev = [(t, 0)] + [(t + i * type_dt, i) for i in range(1, n + 1)]
        t_del = t + n * type_dt + hold
        ev += [(t_del + j * del_dt, n - j) for j in range(1, n + 1)]
        per.append(ev)
        cur.extend(ev)
        t = t_del + n * del_dt + gap
    return per, cur, t


# ───────────────────────────── header ──────────────────────────────
def header():
    W, H = 900, 320
    cw1, cw2 = 10.8, 13.2  # monospace advance at 18px / 22px

    # network graph on the right: the peer-to-peer motif
    N = {1: (668, 118), 2: (770, 88), 3: (852, 152), 4: (744, 192), 5: (836, 248), 6: (676, 250), 7: (764, 292)}
    E = [(1, 2), (2, 3), (1, 4), (2, 4), (3, 4), (4, 5), (4, 6), (6, 7), (5, 7), (4, 7), (3, 5), (1, 6)]
    lines = "".join(
        f'<line x1="{N[a][0]}" y1="{N[a][1]}" x2="{N[b][0]}" y2="{N[b][1]}" stroke="{TEAL}" stroke-opacity="{.42 if 4 in (a, b) else .2}" stroke-width="1.2"/>'
        for a, b in E
    )
    nodes = ""
    for i, (x, y) in N.items():
        if i == 4:
            continue
        nodes += f'<circle cx="{x}" cy="{y}" r="5" fill="{INK}" stroke="{TEAL}" stroke-width="1.5"/><circle cx="{x}" cy="{y}" r="1.8" fill="{TEAL}"/>'
    hx, hy = N[4]
    hub = (
        f'<circle cx="{hx}" cy="{hy}" r="14" fill="{TEAL}" opacity=".35" filter="url(#glow)"/>'
        + A(f'<circle cx="{hx}" cy="{hy}" r="8" fill="none" stroke="{TEAL}" stroke-width="1.2"><animate attributeName="r" values="8;30" dur="3s" repeatCount="indefinite"/><animate attributeName="opacity" values=".7;0" dur="3s" repeatCount="indefinite"/></circle>')
        + f'<circle cx="{hx}" cy="{hy}" r="7" fill="{TEAL}"/><circle cx="{hx}" cy="{hy}" r="2.6" fill="{INK}"/>'
    )
    flights = [(1, 4, 2.6), (4, 3, 2.2), (2, 4, 3.0), (4, 6, 2.4), (5, 4, 2.8), (4, 7, 2.0), (1, 2, 2.5), (3, 5, 3.2), (7, 6, 2.7)]
    packets = ""
    for k, (a, b, dur) in enumerate(flights):
        (x1, y1), (x2, y2) = N[a], N[b]
        if STATIC:
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            if k % 2 == 0:
                packets += f'<circle cx="{fnum(mx)}" cy="{fnum(my)}" r="7" fill="{AMBER}" opacity=".25"/><circle cx="{fnum(mx)}" cy="{fnum(my)}" r="2.6" fill="{AMBER}"/>'
        else:
            begin = fnum(2.3 + k * 0.47)
            packets += (
                f'<g opacity="0"><circle r="7" fill="{AMBER}" opacity=".25"/><circle r="2.6" fill="{AMBER}"/>'
                f'<animateMotion path="M{x1} {y1} L{x2} {y2}" dur="{dur}s" begin="{begin}s" repeatCount="indefinite"/>'
                f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.12;0.88;1" dur="{dur}s" begin="{begin}s" repeatCount="indefinite"/></g>'
            )
    graph = (
        f'<g opacity="{1 if STATIC else 0}">' + lines + nodes + hub + packets
        + A('<animate attributeName="opacity" from="0" to="1" begin="1.8s" dur="1s" fill="freeze"/>')
        + "</g>"
    )

    # line 1: $ whoami (prompt is static, the command is typed once)
    cmd = "whoami"
    n1, x1 = len(cmd), 48 + 2 * cw1
    v1, k1 = typing_steps(n1, cw1, x1)
    vw, _ = typing_steps(n1, cw1, 0)
    line1 = (
        f'<clipPath id="c1"><rect x="{fnum(x1)}" y="72" width="{fnum(n1 * cw1) if STATIC else 0}" height="28">'
        + A(f'<animate attributeName="width" values="{vw}" keyTimes="{k1}" calcMode="discrete" dur="0.7s" begin="0.5s" fill="freeze"/>')
        + "</rect></clipPath>"
        f'<text class="m" x="48" y="94" font-size="18" fill="{TEAL}">$</text>'
        f'<text class="m" x="{fnum(x1)}" y="94" font-size="18" fill="{TEXT}" textLength="{fnum(n1 * cw1)}" lengthAdjust="spacing" clip-path="url(#c1)">{cmd}</text>'
    )
    cursor1 = "" if STATIC else (
        f'<g><rect x="{fnum(x1)}" y="75" width="10" height="21" fill="{AMBER}"><animate attributeName="x" values="{v1}" keyTimes="{k1}" calcMode="discrete" dur="0.7s" begin="0.5s" fill="freeze"/>'
        f"{blink()}</rect>"
        '<set attributeName="opacity" to="0" begin="1.4s" fill="freeze"/></g>'
    )

    # the name is printed as command output; a sheen crosses it now and then
    name_w = len(NAME) * 33.6
    name = (
        f'<text class="m" x="48" y="170" font-size="56" font-weight="700" fill="url(#sheen)" textLength="{fnum(name_w)}" lengthAdjust="spacing" opacity="{1 if STATIC else 0}">{NAME}'
        + A('<set attributeName="opacity" to="1" begin="1.4s" fill="freeze"/>')
        + "</text>"
    )

    # rotating roles: each has its own reveal clip, all driven by one timeline
    per, cur, D = role_cycle(ROLES)
    rx0, ry = 74.4, 214
    role_defs, role_texts = "", ""
    for i, r in enumerate(ROLES):
        ev = per[i] if per[i][0][0] == 0 else [(0, 0)] + per[i]
        vals = ";".join(fnum(c * cw2) for _, c in ev)
        kts = ";".join(fnum(t / D, 5) for t, _ in ev)
        w0 = len(r) * cw2 if (STATIC and i == 0) else 0
        role_defs += (
            f'<clipPath id="rc{i}"><rect x="{rx0}" y="188" width="{fnum(w0)}" height="34">'
            + A(f'<animate attributeName="width" values="{vals}" keyTimes="{kts}" calcMode="discrete" dur="{fnum(D)}s" begin="2s" repeatCount="indefinite"/>')
            + "</rect></clipPath>"
        )
        role_texts += f'<text class="m" x="{rx0}" y="{ry}" font-size="22" fill="{TEAL}" textLength="{fnum(len(r) * cw2)}" lengthAdjust="spacing" clip-path="url(#rc{i})">{r}</text>'
    cvals = ";".join(fnum(rx0 + c * cw2) for _, c in cur)
    ckts = ";".join(fnum(t / D, 5) for t, _ in cur)
    role_line = (
        f'<g opacity="{1 if STATIC else 0}"><text class="m" x="48" y="{ry}" font-size="22" fill="{MUTED}">&gt;</text>'
        + A('<set attributeName="opacity" to="1" begin="2s" fill="freeze"/>')
        + "</g>"
        + role_texts
        + (
            f'<g opacity="0"><rect x="{rx0}" y="{ry - 19}" width="11" height="25" fill="{AMBER}">'
            f'<animate attributeName="x" values="{cvals}" keyTimes="{ckts}" calcMode="discrete" dur="{fnum(D)}s" begin="2s" repeatCount="indefinite"/>{blink()}</rect>'
            '<set attributeName="opacity" to="1" begin="2s" fill="freeze"/></g>'
            if not STATIC
            else f'<rect x="{fnum(rx0 + len(ROLES[0]) * cw2)}" y="{ry - 19}" width="11" height="25" fill="{AMBER}"/>'
        )
    )

    # status pills
    pills, px = "", 48
    for k, (label, colour) in enumerate(STATUS_PILLS):
        tw = len(label) * 7.8
        pw = 36 + tw + 18
        cx = px + 20
        ring = A(f'<circle cx="{cx}" cy="261" r="4" fill="none" stroke="{colour}" stroke-width="1.2"><animate attributeName="r" values="4;12" dur="2.2s" repeatCount="indefinite"/><animate attributeName="opacity" values=".7;0" dur="2.2s" repeatCount="indefinite"/></circle>')
        pills += (
            f'<g opacity="{1 if STATIC else 0}">'
            f'<rect x="{px}" y="244" width="{fnum(pw)}" height="34" rx="17" fill="#ffffff" fill-opacity=".04" stroke="#94a3b8" stroke-opacity=".28"/>'
            f'<circle cx="{cx}" cy="261" r="4" fill="{colour}"/>{ring}'
            f'<text class="m" x="{px + 36}" y="265.5" font-size="13" fill="{SOFT}" textLength="{fnum(tw)}" lengthAdjust="spacing">{label}</text>'
            + A(f'<animate attributeName="opacity" from="0" to="1" begin="{2.1 + k * 0.25}s" dur="0.5s" fill="freeze"/>')
            + "</g>"
        )
        px += pw + 12

    defs = f"""
<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{INK}"/><stop offset="1" stop-color="#0f1a33"/></linearGradient>
<clipPath id="card"><rect width="{W}" height="{H}" rx="20"/></clipPath>
<filter id="blur" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="52"/></filter>
<filter id="glow" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="4"/></filter>
<pattern id="dots" width="24" height="24" patternUnits="userSpaceOnUse"><circle cx="1.5" cy="1.5" r="1" fill="{MUTED}" opacity=".16"/></pattern>
<linearGradient id="sheen" gradientUnits="userSpaceOnUse" x1="48" y1="0" x2="{fnum(48 + name_w)}" y2="0" gradientTransform="translate(-560 0)">
  <stop offset="0" stop-color="#f1f5f9"/><stop offset=".36" stop-color="#f1f5f9"/><stop offset=".5" stop-color="{TEAL}"/><stop offset=".64" stop-color="#f1f5f9"/><stop offset="1" stop-color="#f1f5f9"/>
  {A('<animateTransform attributeName="gradientTransform" type="translate" values="-560 0;560 0;560 0" keyTimes="0;0.32;1" dur="8s" begin="1.9s" repeatCount="indefinite"/>')}
</linearGradient>
{line1[: line1.index('<text')]}
{role_defs}
"""
    drift = lambda cx, cy, dx, dy, d: A(
        f'<animate attributeName="cx" values="{cx};{cx + dx};{cx}" dur="{d}s" repeatCount="indefinite"/>'
        f'<animate attributeName="cy" values="{cy};{cy + dy};{cy}" dur="{d}s" repeatCount="indefinite"/>'
    )
    body = f"""
<g clip-path="url(#card)">
  <rect width="{W}" height="{H}" fill="url(#bg)"/>
  <rect width="{W}" height="{H}" fill="url(#dots)"/>
  <g filter="url(#blur)">
    <circle cx="790" cy="70" r="130" fill="{TEAL}" opacity=".15">{drift(790, 70, -50, 40, 14)}</circle>
    <circle cx="80" cy="320" r="150" fill="{INDIGO}" opacity=".17">{drift(80, 320, 70, -30, 18)}</circle>
  </g>
  <rect width="{W}" height="42" fill="#fff" opacity=".035"/>
  <line x1="0" y1="42" x2="{W}" y2="42" stroke="#fff" stroke-opacity=".07"/>
</g>
<circle cx="26" cy="21" r="5.5" fill="{CORAL}" opacity=".85"/><circle cx="46" cy="21" r="5.5" fill="{AMBER}" opacity=".85"/><circle cx="66" cy="21" r="5.5" fill="{TEAL}" opacity=".85"/>
<text class="m" x="450" y="25" font-size="12" text-anchor="middle" fill="{MUTED}">aadarsh@dev: ~</text>
{line1[line1.index('<text'):]}
{cursor1}
{name}
{role_line}
{pills}
{graph}
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="19.5" fill="none" stroke="#94a3b8" stroke-opacity=".22"/>
"""
    # the c1 clipPath is defined in <defs>; the visible <text> for line 1 is in the body
    return doc(W, H, f"{NAME}, full-stack developer. Animated terminal intro.", defs, body)


# ───────────────────────────── project cards ────────────────────────
def motif_pipeline(c):
    xs, y = [292, 346, 400], 50
    lit = [("1;.15;.15", "0;0.25;1"), (".15;.15;1;.15;.15", "0;0.3;0.45;0.62;1"), (".15;.15;1;.15", "0;0.72;0.9;1")]
    s = f'<line x1="302" y1="{y}" x2="336" y2="{y}" stroke="{c}" stroke-opacity=".35"/><line x1="356" y1="{y}" x2="390" y2="{y}" stroke="{c}" stroke-opacity=".35"/>'
    for i, x in enumerate(xs):
        fo = ".9" if STATIC else "1"
        s += f'<circle cx="{x}" cy="{y}" r="10" fill="{c}" fill-opacity="{.85 if STATIC else .15}" stroke="{c}" stroke-width="1.5">'
        s += A(f'<animate attributeName="fill-opacity" values="{lit[i][0]}" keyTimes="{lit[i][1]}" dur="3.6s" repeatCount="indefinite"/>')
        s += "</circle>"
    s += f'<path d="M395 50.5 l3.4 3.4 l6.6 -7" fill="none" stroke="#fff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>'
    s += f'<text class="m" x="292" y="55" font-size="9.5" font-weight="700" text-anchor="middle" fill="#fff">AI</text>'
    for x, lab in zip(xs, ["recommend", "decide", "verify"]):
        s += f'<text class="m" x="{x}" y="80" font-size="10" text-anchor="middle" fill="{MUTED}">{lab}</text>'
    if STATIC:
        s += f'<circle cx="320" cy="{y}" r="2.6" fill="#fff"/>'
    else:
        s += (f'<g opacity="0"><circle r="6" fill="#fff" opacity=".25"/><circle r="2.6" fill="#fff"/>'
              f'<animateMotion path="M292 {y} L400 {y}" dur="3.6s" keyPoints="0;1;1" keyTimes="0;0.9;1" calcMode="linear" repeatCount="indefinite"/>'
              f'<animate attributeName="opacity" values="0;1;1;0;0" keyTimes="0;0.05;0.85;0.9;1" dur="3.6s" repeatCount="indefinite"/></g>')
    return s


def motif_p2p(c):
    y = 50
    s = f'<line x1="300" y1="{y}" x2="390" y2="{y}" stroke="{c}" stroke-opacity=".4" stroke-dasharray="3 4"/>'
    for x, lab in ((290, "you"), (400, "peer")):
        s += f'<circle cx="{x}" cy="{y}" r="9" fill="{INK}" stroke="{c}" stroke-width="1.6"/><circle cx="{x}" cy="{y}" r="3" fill="{c}"/>'
        s += f'<text class="m" x="{x}" y="80" font-size="10" text-anchor="middle" fill="{MUTED}">{lab}</text>'
    s += f'<rect x="340" y="{y - 1}" width="11" height="9" rx="2" fill="{c}"/><path d="M342 {y - 1} v-3 a3.5 3.5 0 0 1 7 0 v3" fill="none" stroke="{c}" stroke-width="1.6"/>'
    if STATIC:
        s += f'<circle cx="316" cy="{y}" r="2.4" fill="#fff"/><circle cx="374" cy="{y}" r="2.4" fill="#fff"/>'
    else:
        for k, (a, b, d, beg) in enumerate([(300, 390, 2.4, 0), (300, 390, 2.4, 1.2), (390, 300, 2.4, 0.6), (390, 300, 2.4, 1.8)]):
            s += (f'<g opacity="0"><circle r="5.5" fill="#fff" opacity=".22"/><circle r="2.4" fill="#fff"/>'
                  f'<animateMotion path="M{a} {y} L{b} {y}" dur="{d}s" begin="{beg}s" repeatCount="indefinite"/>'
                  f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.1;0.9;1" dur="{d}s" begin="{beg}s" repeatCount="indefinite"/></g>')
    return s


def motif_ring(c):
    cx, cy, r = 388, 52, 24
    circ = 2 * math.pi * r
    off = circ * (0.35 if STATIC else 1)
    s = f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#fff" stroke-opacity=".1" stroke-width="5"/>'
    s += (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{c}" stroke-width="5" stroke-linecap="round" '
          f'stroke-dasharray="{fnum(circ)}" stroke-dashoffset="{fnum(off)}" transform="rotate(-90 {cx} {cy})">'
          + A(f'<animate attributeName="stroke-dashoffset" values="{fnum(circ)};0;0;{fnum(circ)}" keyTimes="0;0.8;0.93;1" dur="7s" repeatCount="indefinite"/>')
          + "</circle>")
    s += f'<text class="m" x="{cx}" y="{cy + 3.5}" font-size="10" text-anchor="middle" fill="{MUTED}">focus</text>'
    return s


def motif_thread(c):
    x = 288
    s = f'<line x1="{x}" y1="36" x2="{x}" y2="76" stroke="{c}" stroke-opacity=".35"/>'
    for i, (w, op) in enumerate([(104, .9), (78, .62), (112, .42)]):
        y = 30 + i * 20
        s += f'<circle cx="{x}" cy="{y + 6}" r="4" fill="{INK}" stroke="{c}" stroke-width="1.5"/>'
        s += f'<rect x="{x + 14}" y="{y + 2}" width="{w if STATIC else 0}" height="8" rx="4" fill="{c}" fill-opacity="{op}">'
        s += A(f'<animate attributeName="width" values="0;{w};{w};0" keyTimes="0;0.25;0.85;1" dur="4.6s" begin="{i * 0.45}s" repeatCount="indefinite"/>')
        s += "</rect>"
    return s


MOTIFS = dict(pipeline=motif_pipeline, p2p=motif_p2p, ring=motif_ring, thread=motif_thread)


def card(p):
    w, c, u = 440, p["accent"], p["uid"]
    last = 146 + 20 * (len(p["body"]) - 1)
    chips_y = last + 22
    h = chips_y + 26 + 24

    chips, cx = "", 32
    for label in p["chips"]:
        tw = len(label) * 6.9
        cwid = tw + 22
        chips += (f'<rect x="{cx}" y="{chips_y}" width="{fnum(cwid)}" height="26" rx="13" fill="{c}" fill-opacity=".09" stroke="{c}" stroke-opacity=".38"/>'
                  f'<text class="m" x="{cx + 11}" y="{chips_y + 17}" font-size="11.5" fill="{c}" textLength="{fnum(tw)}" lengthAdjust="spacing">{label}</text>')
        cx += cwid + 8

    body = "".join(f'<text class="s" x="32" y="{146 + 20 * i}" font-size="13.5" fill="#a9b6cc">{line}</text>' for i, line in enumerate(p["body"]))
    ring = A(f'<circle cx="34" cy="34" r="4" fill="none" stroke="{c}" stroke-width="1.2"><animate attributeName="r" values="4;11" dur="2.2s" repeatCount="indefinite"/><animate attributeName="opacity" values=".7;0" dur="2.2s" repeatCount="indefinite"/></circle>') if p["live"] else ""

    defs = f"""
<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0d1424"/><stop offset="1" stop-color="{INK}"/></linearGradient>
<radialGradient id="gl" cx="{w - 10}" cy="0" r="240" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="{c}" stop-opacity=".2"/><stop offset="1" stop-color="{c}" stop-opacity="0"/></radialGradient>
<clipPath id="cp"><rect width="{w}" height="{h}" rx="18"/></clipPath>
"""
    svg_body = f"""
<g clip-path="url(#cp)"><rect width="{w}" height="{h}" fill="url(#bg)"/><rect width="{w}" height="{h}" fill="url(#gl)"/></g>
<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="17.5" fill="none" stroke="#94a3b8" stroke-opacity=".2"/>
<circle cx="34" cy="34" r="3.5" fill="{c}"/>{ring}
<text class="m" x="46" y="38.5" font-size="12" fill="{MUTED}">{p['tag']}</text>
<text class="s" x="32" y="90" font-size="27" font-weight="700" fill="#f1f5f9">{p['title']}</text>
<text class="s" x="32" y="115" font-size="14.5" fill="{c}">{p['tagline']}</text>
{body}
{chips}
{MOTIFS[p['motif']](c)}
"""
    return doc(w, h, f"{p['title']}: {p['tagline']}", defs, svg_body)


# ───────────────────────────── section bars ─────────────────────────
def section(cmd, right):
    W, H, cw = 900, 52, 9.6
    n = 2 + len(cmd)
    x_end = 24 + n * cw
    rl = len(right) * 7.2
    line = ""
    if x_end + 60 < 876 - rl - 24:
        line = f'<line x1="{fnum(x_end + 44)}" y1="26" x2="{fnum(876 - rl - 20)}" y2="26" stroke="#94a3b8" stroke-opacity=".22" stroke-dasharray="2 6" stroke-linecap="round"/>'
    body = f"""
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="12" fill="#0d1424" stroke="#94a3b8" stroke-opacity=".2"/>
<text class="m" x="24" y="32" font-size="16" fill="{TEAL}">$</text>
<text class="m" x="{fnum(24 + 2 * cw)}" y="32" font-size="16" fill="{TEXT}" textLength="{fnum(len(cmd) * cw)}" lengthAdjust="spacing">{cmd}</text>
<rect x="{fnum(x_end + 6)}" y="14" width="9" height="20" fill="{AMBER}">{blink()}</rect>
{line}
<text class="m" x="876" y="31" font-size="12" text-anchor="end" fill="{MUTED}">{right}</text>
"""
    return doc(W, H, f"{cmd}", "", body)


# ───────────────────────────── stack marquee ────────────────────────
def lum(hexc):
    r, g, b = (int(hexc[i:i + 2], 16) / 255 for i in (0, 2, 4))
    lin = lambda v: v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def icon_markup(name, x, y):
    s = 20 / 24
    if name in ICONS:
        col = "#" + ICONS[name]["hex"]
        if lum(col[1:]) < 0.1:
            col = "#cbd5e1"
        return f'<path transform="translate({x} {y}) scale({fnum(s, 4)})" d="{ICONS[name]["path"]}" fill="{col}"/>'
    g = f'transform="translate({x} {y}) scale({fnum(s, 4)})" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"'
    if name == "OAuth":
        return f'<g {g} stroke="{INDIGO}"><rect x="5" y="11" width="14" height="9" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/></g>'
    if name == "WebSockets":
        return f'<g {g} stroke="{TEAL}"><path d="M4 8h14m-4-4 4 4-4 4"/><path d="M20 16H6m4-4-4 4 4 4"/></g>'
    raise KeyError(name)


def marquee_row(names, y, direction):
    gap, cw = 14, 8.4
    x, parts = 0, []
    for n in names:
        pw = 64 + len(n) * cw
        parts.append(
            f'<g><rect x="{fnum(x)}" y="{y}" width="{fnum(pw)}" height="44" rx="22" fill="#fff" fill-opacity=".045" stroke="#94a3b8" stroke-opacity=".25"/>'
            f'{icon_markup(n, fnum(x + 18), y + 12)}'
            f'<text class="m" x="{fnum(x + 48)}" y="{y + 27.5}" font-size="14" fill="{TEXT}" textLength="{fnum(len(n) * cw)}" lengthAdjust="spacing">{n}</text></g>'
        )
        x += pw + gap
    G = x
    copies = math.ceil(900 / G) + 1
    strip = "".join(f'<g transform="translate({fnum(i * G)} 0)">{"".join(parts)}</g>' for i in range(copies))
    dur = G / 34
    vals = f"0 0;{fnum(-G)} 0" if direction < 0 else f"{fnum(-G)} 0;0 0"
    off = 30 if STATIC else 0
    return f'<g transform="translate({-off if direction<0 else -G + off} 0)">' + A(
        f'<animateTransform attributeName="transform" type="translate" values="{vals}" dur="{fnum(dur)}s" repeatCount="indefinite"/>'
    ) + strip + "</g>"


def stack():
    W, H = 900, 148
    defs = """
<linearGradient id="fade" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#000"/><stop offset=".07" stop-color="#fff"/><stop offset=".93" stop-color="#fff"/><stop offset="1" stop-color="#000"/></linearGradient>
<mask id="edge"><rect width="900" height="148" fill="url(#fade)"/></mask>
"""
    body = f"""
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="16" fill="#0d1424" stroke="#94a3b8" stroke-opacity=".2"/>
<g mask="url(#edge)">{marquee_row(STACK_ROW_1, 20, -1)}{marquee_row(STACK_ROW_2, 84, +1)}</g>
"""
    return doc(W, H, "Tech stack: " + ", ".join(STACK_ROW_1 + STACK_ROW_2), defs, body)


# ───────────────────────────── footer ──────────────────────────────
def footer():
    W, H, cw = 900, 138, 9.6
    cmd = "echo $CONTACT"
    n1, x1 = len(cmd), 24 + 2 * 9.6
    vw, kt = typing_steps(n1, cw, 0)
    vx, _ = typing_steps(n1, cw, x1)
    clip = (f'<clipPath id="fc"><rect x="{fnum(x1)}" y="24" width="{fnum(n1 * cw) if STATIC else 0}" height="28">'
            + A(f'<animate attributeName="width" values="{vw}" keyTimes="{kt}" calcMode="discrete" dur="0.9s" begin="0.4s" fill="freeze"/>')
            + "</rect></clipPath>")
    cur1 = "" if STATIC else (f'<g><rect x="{fnum(x1)}" y="28" width="9" height="20" fill="{AMBER}"><animate attributeName="x" values="{vx}" keyTimes="{kt}" calcMode="discrete" dur="0.9s" begin="0.4s" fill="freeze"/>{blink()}</rect>'
                              '<set attributeName="opacity" to="0" begin="1.5s" fill="freeze"/></g>')
    body = f"""
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="16" fill="#0d1424" stroke="#94a3b8" stroke-opacity=".2"/>
<text class="m" x="24" y="44" font-size="16" fill="{TEAL}">$</text>
<text class="m" x="{fnum(x1)}" y="44" font-size="16" fill="{TEXT}" textLength="{fnum(n1 * cw)}" lengthAdjust="spacing" clip-path="url(#fc)">{cmd}</text>
{cur1}
<g opacity="{1 if STATIC else 0}"><text class="m" x="24" y="76" font-size="16" fill="{TEAL}" textLength="{fnum(len(CONTACT_SITE) * cw)}" lengthAdjust="spacing">{CONTACT_SITE}</text>
<text class="m" x="{fnum(24 + (len(CONTACT_SITE) + 3) * cw)}" y="76" font-size="16" fill="{SOFT}" textLength="{fnum(len(CONTACT_MAIL) * cw)}" lengthAdjust="spacing">{CONTACT_MAIL}</text>
{A('<animate attributeName="opacity" from="0" to="1" begin="1.6s" dur="0.4s" fill="freeze"/>')}</g>
<g opacity="{1 if STATIC else 0}"><text class="m" x="24" y="110" font-size="16" fill="{TEAL}">$</text>
<rect x="{fnum(x1)}" y="95" width="9" height="20" fill="{AMBER}">{blink()}</rect>{A('<animate attributeName="opacity" from="0" to="1" begin="2s" dur="0.1s" fill="freeze"/>')}</g>
"""
    return doc(W, H, f"Contact: {CONTACT_SITE}, {CONTACT_MAIL}", clip, body)


# ───────────────────────────── build ───────────────────────────────
if __name__ == "__main__":
    print(("Static previews" if STATIC else "Animated assets") + f" -> {os.path.normpath(OUT)}")
    write("header.svg", header())
    for p in PROJECTS:
        write(p["file"], card(p))
    write("section-projects.svg", section("ls ~/projects", f"{len(PROJECTS)} items"))
    write("section-stack.svg", section("cat stack.txt", f"{len(STACK_ROW_1) + len(STACK_ROW_2)} tools"))
    write("stack.svg", stack())
    write("footer.svg", footer())
