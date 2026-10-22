#!/usr/bin/env python3
"""Generate an animated 'Repo Galaxy' SVG from your real GitHub repositories.
Pure standard library. Usage: python scripts/generate_galaxy.py [username] [output.svg]
Set GITHUB_TOKEN to avoid API rate limits (the Action does this automatically)."""
import hashlib, html, json, math, os, random, sys, urllib.request
from collections import Counter

USER = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("GH_USER", "andremasalle")
OUT = sys.argv[2] if len(sys.argv) > 2 else "repo-galaxy.svg"
INCLUDE_FORKS = False
# Repos to leave out (case-insensitive). The profile repo itself is excluded by default.
EXCLUDE = {USER.lower()}   # add more, e.g. {USER.lower(), "some-private-notes"}
STATIC = bool(os.environ.get('GALAXY_STATIC'))
EXCLUDE = {USER.lower()}   # repos to hide, e.g. the profile repo; add more names in lowercase
MAX_LABELS = 5

LANG_COLORS = {
    "Jupyter Notebook": "#f97316", "Python": "#60a5fa", "JavaScript": "#facc15",
    "TypeScript": "#38bdf8", "HTML": "#fb7185", "CSS": "#a78bfa", "R": "#34d399",
    "Java": "#f59e0b", "C++": "#f472b6", "C": "#94a3b8", "Go": "#22d3ee",
    "Rust": "#fdba74", "PHP": "#818cf8", "Shell": "#86efac", "Dart": "#2dd4bf",
}
FALLBACK = ["#a78bfa", "#34d399", "#f472b6", "#22d3ee", "#fbbf24"]
def color_for(lang):
    if lang in LANG_COLORS: return LANG_COLORS[lang]
    if not lang: return "#94a3b8"
    return FALLBACK[int(hashlib.md5(lang.encode()).hexdigest(), 16) % len(FALLBACK)]

def api(path):
    req = urllib.request.Request("https://api.github.com" + path,
        headers={"Accept": "application/vnd.github+json", "User-Agent": "repo-galaxy"})
    tok = os.environ.get("GITHUB_TOKEN")
    if tok: req.add_header("Authorization", f"Bearer {tok}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def fetch_repos():
    repos, page = [], 1
    while True:
        batch = api(f"/users/{USER}/repos?per_page=100&type=owner&sort=pushed&page={page}")
        repos += batch
        if len(batch) < 100: break
        page += 1
    if not INCLUDE_FORKS: repos = [r for r in repos if not r["fork"]]
    repos = [r for r in repos if r["name"].lower() not in EXCLUDE]
    repos = [r for r in repos if r["name"].lower() not in EXCLUDE]
    return repos

def build(repos):
    W, H, CX, CY = 900, 400, 590, 205
    n = len(repos)
    stars = sum(r["stargazers_count"] for r in repos)
    langs = Counter(r["language"] or "Other" for r in repos)
    top_langs = langs.most_common(3)
    total = sum(langs.values()) or 1
    seed = int(hashlib.md5(USER.encode()).hexdigest()[:8], 16)
    rnd = random.Random(seed)
    lang_order = [l for l, _ in langs.most_common()]

    # galaxy-space -> screen-space (same tilt as the rotating dust)
    tilt, sy = math.radians(-14), 0.42
    def to_screen(x, y):
        y *= sy
        return (CX + x * math.cos(tilt) - y * math.sin(tilt),
                CY + x * math.sin(tilt) + y * math.cos(tilt))

    # background twinkling stars
    bg = []
    for _ in range(90):
        d, b = rnd.uniform(3, 9), rnd.uniform(0, 9)
        bg.append(f'<circle cx="{rnd.uniform(10,W-10):.0f}" cy="{rnd.uniform(10,H-10):.0f}" r="{rnd.choice([.5,.7,.9])}" fill="#cbd5ff"><animate attributeName="opacity" values="0.1;0.8;0.1" dur="{d:.1f}s" begin="-{b:.1f}s" repeatCount="indefinite"/></circle>')

    # rotating dust (decorative), coloured by your language mix
    palette = [color_for(l) for l, c in langs.items() for _ in range(max(1, round(10 * c / total)))] or ["#60a5fa"]
    groups = [[], [], []]
    for arm in (0, 1):
        for i in range(130):
            t = (i / 130) ** 0.9
            r = 28 + t * 330
            a = arm * math.pi + t * 3.4 + rnd.gauss(0, 0.22 + 0.25 * t)
            rad = rnd.choice([0.8, 1, 1.2, 1.5, 1.8, 2.2])
            d, b, lo = rnd.uniform(2.5, 7), rnd.uniform(0, 6), rnd.uniform(.15, .4)
            groups[i % 3].append(f'<circle cx="{r*math.cos(a):.1f}" cy="{r*math.sin(a):.1f}" r="{rad}" fill="{rnd.choice(palette)}"><animate attributeName="opacity" values="{lo:.2f};1;{lo:.2f}" dur="{d:.1f}s" begin="-{b:.1f}s" repeatCount="indefinite"/></circle>')
    dust = "\n".join(
        f'<g><animateTransform attributeName="transform" type="rotate" from="0" to="{360*s}" dur="{dur}s" repeatCount="indefinite"/>{"".join(g)}</g>'
        for g, dur, s in zip(groups, (110, 75, 55), (1, -1, 1)))

    # one bright star per real repo; each orbits the core, its label travels with it
    ranked = sorted(repos, key=lambda r: (r["stargazers_count"], r["pushed_at"] or ""), reverse=True)
    label_names = {r["name"] for r in ranked[:MAX_LABELS]}
    repo_svg = []
    for idx, r in enumerate(ranked):
        h = int(hashlib.md5(r["name"].encode()).hexdigest(), 16)
        t = (idx + 0.5) / max(n, 1)
        if r["name"] in label_names:         # labelled stars stay inside the canvas
            li = [x["name"] for x in ranked[:MAX_LABELS]].index(r["name"])
            a = 80 + li * (150 / max(1, min(MAX_LABELS, n) - 1)) + (h % 10)
            a = min(a, (290 - min(len(r["name"]), 40) * 3.1) / 0.97)   # keep the whole label inside the canvas
        else:
            a = 70 + t * 250 + (h % 24)      # orbit half-width
        b = a * sy                            # orbit half-height (flattened)
        size = 3.2 + math.sqrt(r["stargazers_count"]) * 1.6
        c = color_for(r["language"])
        orbit = 70 + (h % 60) + t * 90        # seconds per lap: inner = faster
        phase = (h >> 6) % int(orbit)
        tw, tb = 2 + (h % 30) / 10, (h >> 4) % 6
        path = f"M {a:.1f},0 A {a:.1f},{b:.1f} 0 1,1 {-a:.1f},0 A {a:.1f},{b:.1f} 0 1,1 {a:.1f},0 Z"
        label = ""
        if r["name"] in label_names:
            full = r["name"]
            nm = html.escape(full if len(full) <= 40 else full[:39] + "…")
            label = f'<text transform="rotate(14)" x="0" y="{-(size+7):.1f}" text-anchor="middle" font-size="10" fill="#e0e7ff" font-weight="600">{nm}</text>'
        if STATIC:  # debug preview only (renderers without SMIL)
            ang = 2 * math.pi * phase / orbit
            move = f' transform="translate({a*math.cos(ang):.1f} {b*math.sin(ang):.1f})"'
            anim = ""
        else:
            move = ""
            anim = f'<animateMotion dur="{orbit}s" begin="-{phase}s" repeatCount="indefinite" path="{path}"/>'
        repo_svg.append(f'<g{move}>{anim}<circle r="{size:.1f}" fill="{c}" filter="url(#g)"><animate attributeName="opacity" values="0.55;1;0.55" dur="{tw:.1f}s" begin="-{tb}s" repeatCount="indefinite"/></circle>{label}</g>')

    # shooting stars + core pulse rings
    shoot = []
    for i, (x0, y0, x1, y1, dur, beg) in enumerate([(120, 40, 330, 120, 11, 3), (840, 70, 660, 160, 17, 9), (300, 360, 470, 300, 23, 15)]):
        shoot.append(f'<g opacity="0"><line x1="-26" y1="-9" x2="0" y2="0" stroke="#e0e7ff" stroke-width="1.3" stroke-linecap="round"/><circle r="1.6" fill="#fff"/>'
                     f'<animateMotion dur="{dur}s" begin="{beg}s" repeatCount="indefinite" path="M {x0},{y0} L {x1},{y1}" keyPoints="0;1;1" keyTimes="0;0.09;1" calcMode="linear"/>'
                     f'<animate attributeName="opacity" dur="{dur}s" begin="{beg}s" repeatCount="indefinite" values="0;1;0;0" keyTimes="0;0.02;0.09;1"/></g>')
    pulses = "".join(
        f'<circle r="6" fill="none" stroke="#a5b4fc" stroke-width="1.2"><animate attributeName="r" values="6;80" dur="6s" begin="{d}s" repeatCount="indefinite"/><animate attributeName="opacity" values="0.6;0" dur="6s" begin="{d}s" repeatCount="indefinite"/></circle>'
        for d in (0, 3))

    legend = ""
    for i, (l, c) in enumerate(top_langs):
        y = 295 + i * 24
        legend += f'<circle cx="45" cy="{y-4}" r="5" fill="{color_for(l)}"/><text x="58" y="{y}" font-size="12" fill="#e0e7ff">{html.escape(l)}</text><text x="190" y="{y}" font-size="12" fill="#a5b4fc">{round(100*c/total)}%</text>'

    ok = "'SFMono-Regular',Consolas,'Liberation Mono',Menlo,monospace"
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Repo Galaxy for @{USER}">
<defs>
<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#050816"/><stop offset=".6" stop-color="#0a0f2c"/><stop offset="1" stop-color="#0b1236"/></linearGradient>
<radialGradient id="core"><stop offset="0" stop-color="#fff" stop-opacity=".95"/><stop offset=".15" stop-color="#a5b4fc" stop-opacity=".8"/><stop offset=".5" stop-color="#4f46e5" stop-opacity=".25"/><stop offset="1" stop-color="#4f46e5" stop-opacity="0"/></radialGradient>
<radialGradient id="halo"><stop offset="0" stop-color="#6366f1" stop-opacity=".28"/><stop offset="1" stop-color="#6366f1" stop-opacity="0"/></radialGradient>
<filter id="g" x="-200%" y="-200%" width="500%" height="500%"><feGaussianBlur stdDeviation="2.2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<filter id="t" x="-20%" y="-50%" width="140%" height="200%"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<clipPath id="r"><rect width="{W}" height="{H}" rx="18"/></clipPath>
</defs>
<g clip-path="url(#r)">
<rect width="{W}" height="{H}" fill="url(#bg)"/>
<ellipse cx="{CX}" cy="{CY}" rx="380" ry="170" fill="url(#halo)"/>
{"".join(bg)}
<g transform="translate({CX} {CY}) rotate(-14) scale(1 .42)">
<circle r="120" fill="none" stroke="#6366f1" stroke-opacity=".12" stroke-dasharray="2 6"/>
<circle r="230" fill="none" stroke="#6366f1" stroke-opacity=".1" stroke-dasharray="2 8"/>
<circle r="340" fill="none" stroke="#6366f1" stroke-opacity=".08" stroke-dasharray="2 10"/>
{dust}</g>
<g transform="translate({CX} {CY}) rotate(-14) scale(1 .42)">{pulses}</g>
<g transform="translate({CX} {CY})"><ellipse rx="70" ry="36" fill="url(#core)"><animate attributeName="opacity" values=".7;1;.7" dur="4s" repeatCount="indefinite"/></ellipse><circle r="5" fill="#fff" filter="url(#g)"/></g>
<g transform="translate({CX} {CY}) rotate(-14)" font-family="{ok}">{"".join(repo_svg)}</g>
{"".join(shoot)}
<g font-family="{ok}">
<text x="40" y="58" font-size="11" letter-spacing="4" fill="#818cf8">REPO GALAXY</text>
<text x="40" y="92" font-size="28" font-weight="700" fill="#e0e7ff" filter="url(#t)">@{USER}<tspan fill="#818cf8"><animate attributeName="opacity" values="1;0;1" dur="1.1s" repeatCount="indefinite"/>_</tspan></text>
<text x="40" y="118" font-size="13" fill="#a5b4fc">{n} repositories</text>
<text x="40" y="140" font-size="10" fill="#6b74b8">Each star is a repository.</text>
<text x="40" y="272" font-size="10" letter-spacing="3" fill="#6b74b8">ARMS</text>
{legend}
<text x="860" y="382" font-size="9" fill="#4b5399" text-anchor="end">./repo-galaxy --live</text>
</g>
<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="18" fill="none" stroke="#4f56b8" stroke-opacity=".6"/>
</g>
</svg>'''

if __name__ == "__main__":
    repos = fetch_repos()
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(build(repos))
    print(f"Wrote {OUT}: {len(repos)} repos for @{USER}")