#!/usr/bin/env python3
"""Generate 'brightest-stars.svg' (top repos) and 'elements.svg' (from elements.json).
Pure standard library. Usage: python scripts/generate_panels.py [username]
Run from the repo root. Needs scripts/generate_galaxy.py next to it."""
import html, json, math, os, random, sys
from datetime import datetime, timezone
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import generate_galaxy as gg

USER = gg.USER
MAX_PROJECTS = 4          # how many repos in "Brightest stars"
MONO = "'SFMono-Regular',Consolas,'Liberation Mono',Menlo,monospace"
esc = html.escape

def trunc(s, n):
    s = s or ""
    return s if len(s) <= n else s[: n - 1] + "…"

def ago(iso):
    if not iso: return ""
    d = datetime.now(timezone.utc) - datetime.fromisoformat(iso.replace("Z", "+00:00"))
    days = d.days
    if days < 1: return "today"
    if days < 30: return f"{days}d ago"
    if days < 365: return f"{days // 30}mo ago"
    return f"{days // 365}y ago"

def top_lang_pct(name, lang):
    try:
        data = gg.api(f"/repos/{USER}/{name}/languages")
        total = sum(data.values())
        if total and lang in data: return round(100 * data[lang] / total)
    except Exception:
        pass
    return 100

DEFS = '''<defs>
<linearGradient id="pbg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0a0e26"/><stop offset=".55" stop-color="#0d1033"/><stop offset="1" stop-color="#140d2e"/></linearGradient>
<radialGradient id="b1"><stop offset="0" stop-color="#4f56d6" stop-opacity=".45"/><stop offset="1" stop-color="#4f56d6" stop-opacity="0"/></radialGradient>
<radialGradient id="b2"><stop offset="0" stop-color="#a855f7" stop-opacity=".30"/><stop offset="1" stop-color="#a855f7" stop-opacity="0"/></radialGradient>
<radialGradient id="b3"><stop offset="0" stop-color="#14b8a6" stop-opacity=".28"/><stop offset="1" stop-color="#14b8a6" stop-opacity="0"/></radialGradient>
<filter id="glw" x="-10%" y="-40%" width="120%" height="180%"><feGaussianBlur stdDeviation="1.6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<linearGradient id="trail" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#e0e7ff" stop-opacity="0"/><stop offset="1" stop-color="#e0e7ff" stop-opacity="1"/></linearGradient>
<linearGradient id="scan" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#818cf8" stop-opacity="0"/><stop offset="1" stop-color="#818cf8" stop-opacity=".16"/></linearGradient>
</defs>'''

def backdrop(W, H):
    """Animated background: drifting aurora, 3-layer parallax starfield, rare shooting stars."""
    rnd = random.Random(11)
    def glow(grad, cx, cy, rx, ry, dx, dy, dur):
        return (f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="url(#{grad})">'
                f'<animateTransform attributeName="transform" type="translate" values="0 0;{dx} {dy};0 0" dur="{dur}s" repeatCount="indefinite" calcMode="spline" keySplines=".45 0 .55 1;.45 0 .55 1" keyTimes="0;.5;1"/></ellipse>')
    def layer(n, radii, dur, opacity, twinkle):
        pts = [(rnd.uniform(4, W - 4), rnd.uniform(6, H - 6), rnd.choice(radii),
                rnd.choice(["#cbd5ff", "#cbd5ff", "#a5b4fc", "#fdba74", "#7dd3fc"]),
                rnd.uniform(3, 8), rnd.uniform(0, 8)) for _ in range(n)]
        out = []
        for shift in (0, W):                      # duplicate so the loop is seamless
            for x, y, r, c, d, b in pts:
                tw = (f'<animate attributeName="opacity" values="0.25;1;0.25" dur="{d:.1f}s" begin="-{b:.1f}s" repeatCount="indefinite"/>' if twinkle else "")
                out.append(f'<circle cx="{x + shift:.0f}" cy="{y:.0f}" r="{r}" fill="{c}">{tw}</circle>')
        return (f'<g opacity="{opacity}"><animateTransform attributeName="transform" type="translate" from="0 0" to="{-W} 0" dur="{dur}s" repeatCount="indefinite"/>'
                + "".join(out) + '</g>')
    def shooting(x0, y0, x1, y1, dur, beg):
        dx, dy = x1 - x0, y1 - y0
        L = math.hypot(dx, dy)
        tx, ty = -dx / L * 36, -dy / L * 36
        return (f'<g opacity="0"><line x1="{tx:.1f}" y1="{ty:.1f}" x2="0" y2="0" stroke="url(#trail)" stroke-width="1.4" stroke-linecap="round"/><circle r="1.7" fill="#fff"/>'
                f'<animateMotion dur="{dur}s" begin="{beg}s" repeatCount="indefinite" path="M {x0:.0f},{y0:.0f} L {x1:.0f},{y1:.0f}" keyPoints="0;1;1" keyTimes="0;0.08;1" calcMode="linear"/>'
                f'<animate attributeName="opacity" dur="{dur}s" begin="{beg}s" repeatCount="indefinite" values="0;1;1;0;0" keyTimes="0;.01;.06;.08;1"/></g>')
    area = W * H
    return "\n".join([
        glow("b1", 120, 40, 260, 150, 140, 40, 16),
        glow("b2", W - 80, int(H * 0.55), 260, 170, -150, -30, 20),
        glow("b3", int(W * 0.5), H, 300, 110, 120, -25, 18),
        layer(int(area / 9000), [0.5, 0.6], 170, 0.55, False),   # far: tiny, slow
        layer(int(area / 14000), [0.8, 1.0], 105, 0.8, True),     # mid
        layer(int(area / 30000), [1.3, 1.6], 62, 1.0, True),      # near: bigger, faster
        shooting(W * 0.08, H * 0.10, W * 0.34, H * 0.55, 13, 4),
        shooting(W * 0.92, H * 0.06, W * 0.66, H * 0.50, 19, 11),
    ])

def frame(W, H, body):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
{DEFS}
<clipPath id="pc"><rect width="{W}" height="{H}" rx="18"/></clipPath>
<g clip-path="url(#pc)">
<rect width="{W}" height="{H}" fill="url(#pbg)"/>
{backdrop(W, H)}
<g font-family="{MONO}">
{body}
</g>
<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="18" fill="none" stroke="#4f56b8" stroke-opacity=".6"/>
</g>
</svg>'''

def build_projects(repos, pcts):
    ranked = sorted(repos, key=lambda r: (r["stargazers_count"], r["pushed_at"] or ""), reverse=True)[:MAX_PROJECTS]
    W, CW, CH, GAP, X0, Y0 = 900, 414, 142, 16, 28, 82
    rows = math.ceil(len(ranked) / 2) or 1
    H = Y0 + rows * (CH + GAP) + 14
    b = [f'<text x="{X0}" y="46" font-size="11" letter-spacing="3" fill="#818cf8">PROJECTS.LIST</text>',
         f'<text x="170" y="46" font-size="11" fill="#6b74b8">./projects.sh --all</text>',
         f'<text x="{W-X0}" y="46" font-size="11" fill="#818cf8" text-anchor="end">{len(ranked)} projects</text>',
         f'<line x1="{X0}" y1="58" x2="{W-X0}" y2="58" stroke="#4f56b8" stroke-opacity=".6"/>']
    for i, r in enumerate(ranked):
        x = X0 + (i % 2) * (CW + GAP)
        y = Y0 + (i // 2) * (CH + GAP)
        c = gg.color_for(r["language"])
        lang = r["language"] or "No language"
        pct = pcts.get(r["name"], 100)
        circ = 2 * math.pi * 26
        end = circ * (1 - pct / 100)
        fs = max(10.5, min(17, 280 / (0.61 * max(len(r["name"]), 1))))   # shrink long names to fit
        desc = trunc(r.get("description") or "No description provided.", 44)
        pw = len(lang) * 6.4 + 22
        per = 2 * (CW + CH - 4 * 12) + 2 * math.pi * 12          # card border length
        pd = (per * 0.11, per * 0.89, per)
        b.append(f'''<g transform="translate({x} {y})">
<rect width="{CW}" height="{CH}" rx="12" fill="#0a0d2a" fill-opacity=".85" stroke="#3b4290"><animate attributeName="stroke-opacity" values=".6;1;.6" dur="{4+i}s" repeatCount="indefinite"/></rect>
<rect width="{CW}" height="{CH}" rx="12" fill="none" stroke="{c}" stroke-width="1.8" stroke-linecap="round" stroke-dasharray="{pd[0]:.1f} {pd[1]:.1f}" filter="url(#glw)"><animate attributeName="stroke-dashoffset" from="0" to="{-pd[2]:.1f}" dur="{7+i}s" begin="-{i*2.3:.1f}s" repeatCount="indefinite"/></rect>
<text x="16" y="24" font-size="9" fill="#8089d6">• {esc(trunc(r["name"], 50))}</text>
<text x="16" y="56" font-size="{fs:.1f}" font-weight="700" fill="#eef0ff">{esc(trunc(r["name"], 44))}<tspan fill="#818cf8"><animate attributeName="opacity" values="1;0;1" dur="1.2s" repeatCount="indefinite"/> _</tspan></text>
<text x="16" y="78" font-size="10" fill="#aab2f0">{esc(desc)}</text>
<rect x="16" y="90" width="{pw:.0f}" height="18" rx="9" fill="#1b2150" stroke="#4f56b8" stroke-opacity=".7"/>
<text x="{16+pw/2:.0f}" y="102" font-size="9" fill="#c7cdfa" text-anchor="middle">{esc(lang)}</text>
<text x="16" y="126" font-size="10" fill="#6b74b8">updated {ago(r["pushed_at"])}</text>
<g transform="translate({CW-60} {CH/2:.0f}) rotate(-90)">
<circle r="26" fill="none" stroke="#1e2350" stroke-width="7"/>
<circle r="26" fill="none" stroke="{c}" stroke-width="7" stroke-linecap="round" stroke-dasharray="{circ:.2f}" stroke-dashoffset="{end:.2f}"><animate attributeName="stroke-dashoffset" from="{circ:.2f}" to="{end:.2f}" dur="1.6s" fill="freeze"/></circle>
</g>
<text x="{CW-60}" y="{CH/2+3:.0f}" font-size="10" font-weight="700" fill="#fff" text-anchor="middle">{pct}%</text>
</g>''')
    return frame(W, H, "\n".join(b))

def build_elements(cfg):
    W, X0, LX, RIGHT, ROW = 900, 28, 28, 872, 36
    title, sub = esc(cfg.get("title", "Stack")), esc(cfg.get("subtitle", ""))
    b = [f'<text x="{X0}" y="46" font-size="20" font-weight="700" fill="#eef0ff">{title}</text>',
         f'<text x="{X0}" y="66" font-size="11" fill="#a5b4fc">{sub}</text>',
         f'<text x="{W-X0}" y="46" font-size="11" fill="#818cf8" text-anchor="end">&gt; stack.scan<tspan><animate attributeName="opacity" values="1;0;1" dur="1.1s" repeatCount="indefinite"/> _</tspan></text>',
         f'<line x1="{X0}" y1="82" x2="{W-X0}" y2="82" stroke="#4f56b8" stroke-opacity=".6"/>']
    y, n = 104, 0
    for g in cfg.get("groups", []):
        b.append(f'<text x="{LX}" y="{y+17}" font-size="10" letter-spacing="3" fill="#6b74b8">{esc(g.get("name","").upper())}</text>')
        x, line_y = 190, y
        for it in g.get("items", []):
            name = it["name"] if isinstance(it, dict) else str(it)
            col = (it.get("color") if isinstance(it, dict) else None) or gg.color_for(name)
            w = 40 + len(name) * 7.3
            if x + w > RIGHT:
                x, line_y = 190, line_y + ROW
            d, bgn = 2 + (n % 5) * 0.7, (n % 7) * 0.6
            cper = 2 * (w + 26 - 2 * 13) + 2 * math.pi * 13          # chip border length
            b.append(f'<g transform="translate({x:.0f} {line_y})"><rect width="{w:.0f}" height="26" rx="13" fill="#12173d" fill-opacity=".9" stroke="{col}" stroke-opacity=".55"/>'
                     f'<rect width="{w:.0f}" height="26" rx="13" fill="none" stroke="{col}" stroke-width="1.5" stroke-linecap="round" stroke-dasharray="{cper*0.16:.1f} {cper*0.84:.1f}" filter="url(#glw)"><animate attributeName="stroke-dashoffset" from="0" to="{-cper:.1f}" dur="{4+(n%4)}s" begin="-{(n*0.9)%6:.1f}s" repeatCount="indefinite"/></rect>'
                     f'<circle cx="15" cy="13" r="4" fill="{col}"><animate attributeName="opacity" values=".4;1;.4" dur="{d:.1f}s" begin="-{bgn:.1f}s" repeatCount="indefinite"/></circle>'
                     f'<text x="28" y="17" font-size="12" fill="#e0e7ff">{esc(name)}</text></g>')
            x += w + 10
            n += 1
        y = line_y + ROW + 12
    return frame(W, y + 10, "\n".join(b))

if __name__ == "__main__":
    repos = gg.fetch_repos()
    ranked = sorted(repos, key=lambda r: (r["stargazers_count"], r["pushed_at"] or ""), reverse=True)[:MAX_PROJECTS]
    pcts = {r["name"]: top_lang_pct(r["name"], r["language"]) for r in ranked if r["language"]}
    open("brightest-stars.svg", "w", encoding="utf-8").write(build_projects(repos, pcts))
    with open("elements.json", encoding="utf-8") as f:
        open("elements.svg", "w", encoding="utf-8").write(build_elements(json.load(f)))
    print("Wrote brightest-stars.svg and elements.svg")