#!/usr/bin/env python3
"""Generate 'brightest-stars.svg' (top repos) and 'elements.svg' (from elements.json).
Pure standard library. Usage: python scripts/generate_panels.py [username]
Run from the repo root. Needs scripts/generate_galaxy.py next to it."""
import html, json, math, os, sys
from datetime import datetime, timezone
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scripts import generate_galaxy as gg

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
</defs>'''

def frame(W, H, body):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
{DEFS}
<clipPath id="pc"><rect width="{W}" height="{H}" rx="18"/></clipPath>
<g clip-path="url(#pc)">
<rect width="{W}" height="{H}" fill="url(#pbg)"/>
<ellipse cx="120" cy="40" rx="260" ry="150" fill="url(#b1)"/>
<ellipse cx="{W-80}" cy="{H*0.55:.0f}" rx="260" ry="170" fill="url(#b2)"/>
<ellipse cx="{W*0.5:.0f}" cy="{H}" rx="300" ry="110" fill="url(#b3)"/>
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
        desc = trunc(r.get("description") or "No description provided.", 44)
        pw = len(lang) * 6.4 + 22
        b.append(f'''<g transform="translate({x} {y})">
<rect width="{CW}" height="{CH}" rx="12" fill="#0a0d2a" fill-opacity=".85" stroke="#3b4290"><animate attributeName="stroke-opacity" values=".6;1;.6" dur="{4+i}s" repeatCount="indefinite"/></rect>
<text x="16" y="24" font-size="9" fill="#8089d6">• {esc(trunc(r["name"], 40))}</text>
<text x="16" y="56" font-size="17" font-weight="700" fill="#eef0ff">{esc(trunc(r["name"], 24))}<tspan fill="#818cf8"><animate attributeName="opacity" values="1;0;1" dur="1.2s" repeatCount="indefinite"/> _</tspan></text>
<text x="16" y="78" font-size="10" fill="#aab2f0">{esc(desc)}</text>
<rect x="16" y="90" width="{pw:.0f}" height="18" rx="9" fill="#1b2150" stroke="#4f56b8" stroke-opacity=".7"/>
<text x="{16+pw/2:.0f}" y="102" font-size="9" fill="#c7cdfa" text-anchor="middle">{esc(lang)}</text>
<text x="16" y="126" font-size="10" fill="#c7cdfa"><tspan fill="{c}">★</tspan> {r["stargazers_count"]}   <tspan fill="#6b74b8">updated {ago(r["pushed_at"])}</tspan></text>
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
            b.append(f'<g transform="translate({x:.0f} {line_y})"><rect width="{w:.0f}" height="26" rx="13" fill="#12173d" fill-opacity=".9" stroke="{col}" stroke-opacity=".55"/>'
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
    open("../brightest-stars.svg", "w", encoding="utf-8").write(build_projects(repos, pcts))
    with open("../elements.json", encoding="utf-8") as f:
        open("../elements.svg", "w", encoding="utf-8").write(build_elements(json.load(f)))
    print("Wrote brightest-stars.svg and elements.svg")
