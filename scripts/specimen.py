# -*- coding: utf-8 -*-
"""Vulpes Ferrea specimen and web test page. Called by export_fonts.py.
樣張全部內嵌 SVG（不需安裝字型），排字時套用字偶。測試頁內嵌 WOFF2，用瀏覽器真實排版。"""
import html

TOP, BOTTOM = 900, -260

CSS = """
:root{--bg:#0a0b0e;--panel:#11131a;--line:#232733;--ink:#d9dde3;--dim:#7d8594;--hot:#ff2e7e;--cold:#3fe0ff}
:root[data-theme=light]{--bg:#ece9e2;--panel:#f6f4ef;--line:#d5d1c7;--ink:#121317;--dim:#5d6270;--hot:#c8155e;--cold:#0a7f99}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.7 "Noto Sans TC","Microsoft JhengHei","PingFang TC",system-ui,sans-serif}
main{max-width:1180px;margin:0 auto;padding:40px 24px 80px}
header{border-bottom:1px solid var(--line);padding-bottom:20px;margin-bottom:8px}
.tag{font:12px/1 ui-monospace,Consolas,monospace;letter-spacing:.14em;color:var(--hot);text-transform:uppercase}
h1{font-size:22px;margin:10px 0 4px;font-weight:600}
h2{font-size:13px;font-weight:600;color:var(--dim);letter-spacing:.12em;margin:56px 0 14px;border-top:1px solid var(--line);padding-top:14px}
h3{font-size:12px;font-weight:600;color:var(--dim);margin:22px 0 8px}
p{margin:0;color:var(--dim);max-width:68ch}
.note{font-size:13px;margin-top:10px}
"""


def render(meta, data, path_d):
    by_char = {}
    for n, g in data.items():
        for u in g["unicodes"]:
            by_char.setdefault(chr(u), n)
    kern = meta["kern"]
    m = meta["metrics"]
    space = meta["space"]

    def line(text, px, cls="ink", use_kern=True):
        x, d, prev = 0.0, [], None
        for ch in text:
            if ch in (" ", " "):
                x += space
                prev = None
                continue
            n = by_char[ch]  # 缺字直接報錯，不靜默略過
            if use_kern and prev:
                x += kern.get(f"{prev} {n}", 0)
            d.append(path_d(data[n], x))
            x += data[n]["advance"]
            prev = n
        h = TOP - BOTTOM
        return (f'<svg class="ln {cls}" role="img" aria-label="{html.escape(text)}" viewBox="0 {-TOP} {max(x, 1):g} {h}" '
                f'style="height:{px * h / 1000:.1f}px"><path transform="scale(1,-1)" d="{"".join(d)}"/></svg>')

    def names_line(names, px):
        x, d = 0.0, []
        for n in names:
            d.append(path_d(data[n], x))
            x += data[n]["advance"] + 40
        h = TOP - BOTTOM
        return (f'<svg class="ln ink" viewBox="0 {-TOP} {x:g} {h}" style="height:{px * h / 1000:.1f}px">'
                f'<path transform="scale(1,-1)" d="{"".join(d)}"/></svg>')

    def construction(text, px):
        x, parts, nodes = 0.0, [], []
        for ch in text:
            if ch == " ":
                x += space
                continue
            g = data[by_char[ch]]
            parts.append(path_d(g, x))
            for c in g["contours"]:
                nodes += [f'<rect x="{px_ + x - 5:g}" y="{py - 5:g}" width="10" height="10"/>' for px_, py in c]
            nodes.append(f'<line class="adv" x1="{x:g}" x2="{x:g}" y1="{BOTTOM}" y2="{TOP}"/>')
            x += g["advance"]
        nodes.append(f'<line class="adv" x1="{x:g}" x2="{x:g}" y1="{BOTTOM}" y2="{TOP}"/>')
        guides = "".join(
            f'<line class="guide" x1="-150" x2="{x + 20:g}" y1="{v}" y2="{v}"/>'
            f'<text class="glabel" x="-150" y="{-v - 10}" transform="scale(1,-1)">{lab} {v}</text>'
            for lab, v in [("升部", m["ascender"]), ("大寫高", m["cap"]), ("x 高", m["xheight"]), ("基線", 0),
                           ("降部", m["descender"])])
        h = TOP - BOTTOM
        return (f'<svg class="cons" viewBox="-160 {-TOP} {x + 190:g} {h}">'
                f'<defs><pattern id="grid" width="{m["M"]}" height="{m["M"]}" patternUnits="userSpaceOnUse">'
                f'<path d="M{m["M"]} 0H0V{m["M"]}" class="gridline"/></pattern></defs>'
                f'<g transform="scale(1,-1)"><rect x="0" y="{BOTTOM}" width="{x:g}" height="{h}" fill="url(#grid)"/>'
                f'{guides}<path class="shape" d="{"".join(parts)}"/><g class="nodes">{"".join(nodes)}</g></g></svg>')

    def cell(n):
        g = data[n]
        lab = html.escape(g["char"]) if g["char"] else "·"
        code = f'U+{g["unicode"]:04X}' if g["unicode"] is not None else "替換字"
        return f'<figure>{names_line([n], 64)}<figcaption><b>{lab}</b> {n}<br>{code} · {g["advance"]}</figcaption></figure>'

    def group(title, chars):
        ns = [by_char[c] for c in chars]
        return f'<h3>{title}（{len(ns)}）</h3><div class="grid">{"".join(cell(n) for n in ns)}</div>'

    groups = "".join([
        group("大寫", "ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
        group("小寫", "abcdefghijklmnopqrstuvwxyz"),
        group("數字", "0123456789"),
        group("ASCII 符號", "!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"),
        group("排版符號", "‘’“”‚„–—‒…·•‹›«»¡¿§¶†‡¦°×÷±−¬"),
        group("貨幣、商標、上標", "€£¥¢¤ƒ©®™¹²³¼½¾‰⁄ªºµ"),
        group("獨立重音", "´¨¯¸ˆ˜ˇ˚"),
        group("歐文大寫", "ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞŒŠŽŸ"),
        group("歐文小寫", "àáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿœšžßı"),
    ])
    alts = [n for n, g in data.items() if not g["unicodes"]]
    alt_grid = f'<h3>OpenType 替換字（{len(alts)}）</h3><div class="grid">{"".join(cell(n) for n in alts)}</div>'

    confus = ["O0o", "S5s", "Il1|", "B8ß", "Z2z", "G6", "gq9", "uny", "vVwW", "([{", "rn m", "cl d", "kK", "&@Q"]
    conf = "".join(f'<div class="pair">{line(t, 72)}</div>' for t in confus)
    kpairs = ["AVATAR", "Tower", "Yacht", "LT'Y'", "“To,”", "F.P.", "WAVY", "-T-"]
    kerncmp = "".join(f'<div class="pair">{line(t, 56, use_kern=False)}{line(t, 56, "hot")}</div>' for t in kpairs)
    water = "".join(f'<div class="wf"><span>{s}px</span>{line("Hamburgevons 0123 minimum", s)}</div>'
                    for s in [96, 64, 40, 28, 20, 14])
    sentences = [("Sphinx of black quartz, judge my vow.", 56, "ink"),
                 ("THE QUICK BROWN FOX JUMPS OVER THE LAZY DOG", 44, "ink"),
                 ("the quick brown fox jumps over the lazy dog", 44, "cold"),
                 ("“Wrath of the Iron Vixen” — Requiem No. 9", 44, "ink"),
                 ("Glyph #42: [ok] {yes} <no> 50% @fox & co. ~/vault_01", 40, "ink"),
                 ("Straße · Ørsted · Ça va? · Œuvre · Björk · Señor · Façade", 44, "hot"),
                 ("€ 1.299 · £ 48 · ¥ 3.600 · ½ off · 37 °C · ± 0,5 · © 2026 FOX™", 40, "cold"),
                 ("¿Qué pasó? ¡Ahora! «Déjà vu» ‹ ok › … § 4.2 ¶ † ‡", 40, "ink")]
    sent = '<div class="stack">' + "".join(line(t, px, c) for t, px, c in sentences) + "</div>"

    return f"""<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>鐵狐體 {meta["revision"]} 樣張</title>
<style>{CSS}
svg.ln{{display:block;max-width:100%;width:auto}} .ink path{{fill:var(--ink)}} .hot path{{fill:var(--hot)}} .cold path{{fill:var(--cold)}}
.hero{{padding:28px 0 4px;overflow:hidden}} .stack>*+*{{margin-top:6px}}
svg.cons{{display:block;width:100%;height:auto;background:var(--panel);border:1px solid var(--line)}}
.gridline{{fill:none;stroke:var(--line);stroke-width:1}} .guide{{stroke:var(--hot);stroke-width:1.5;opacity:.7}}
.adv{{stroke:var(--cold);stroke-width:1.5;opacity:.45;stroke-dasharray:8 8}}
.glabel{{font:26px ui-monospace,Consolas,monospace;fill:var(--hot)}} .shape{{fill:color-mix(in srgb,var(--ink) 20%,transparent);stroke:var(--ink);stroke-width:3}} .nodes rect{{fill:var(--cold)}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(92px,1fr));gap:1px;background:var(--panel);border:1px solid var(--line)}}
figure{{margin:0;background:var(--panel);outline:1px solid var(--line);padding:10px 6px 8px;display:flex;flex-direction:column;align-items:center;overflow:hidden}}
figure svg{{max-width:100%}}
figcaption{{font:10.5px/1.5 ui-monospace,Consolas,monospace;color:var(--dim);text-align:center;margin-top:4px;word-break:break-all}} figcaption b{{color:var(--ink)}}
.pairs{{display:flex;flex-wrap:wrap;gap:12px}} .pair{{background:var(--panel);border:1px solid var(--line);padding:10px 16px;max-width:100%;overflow:hidden}}
.wf{{display:flex;align-items:center;gap:16px}} .wf span{{font:11px ui-monospace,Consolas,monospace;color:var(--dim);width:40px;flex:none}}
.light{{background:#ece9e2;padding:24px;margin-top:12px}} .light .ink path{{fill:#121317}}
@media (max-width:600px){{main{{padding:24px 16px 60px}}}}
</style></head><body><main>
<header><div class="tag">Vulpes Ferrea · {meta["revision"]} · {len(data) + 2} glyphs · SIL OFL 1.1</div>
<h1>Vulpes Ferrea 鐵狐體 樣張</h1>
<p>中文以外的字集完成：ASCII、排版符號、Windows-1252／Latin-1 全部歐文字母，加上 OpenType 替換字。本頁排字已套用字偶。要在瀏覽器裡用真正的字型檔測試，請開同資料夾的 webtest.html。</p></header>

<section class="hero stack">{line("FOX", 190)}{line("No fear, no saints.", 78, "hot")}{line("Œuvre noire — 2026", 78)}</section>

<h2>01 ｜ 構造：模組格線與基準線</h2>
{construction("ÅkQ& @ß", 400)}
<p class="note">格線一格 = 1 模組（{m["M"]}）。粉紅線是五條基準線，青色虛線是字寬邊界，青色方點是輪廓節點。</p>

<h2>02 ｜ 節奏：柵欄測試</h2>
<div class="stack">{line("minimum", 96)}{line("lumen dominion immune", 56)}{line("HIMMELHUNDE", 56)}</div>

<h2>03 ｜ 全字集</h2>
{groups}{alt_grid}

<h2>04 ｜ 字句</h2>
{sent}
<div class="light stack">{line("Black steel, white page. 1234567890", 48)}{line("jagged gospel — quiet engine", 36)}</div>

<h2>05 ｜ 字偶：上為未調，下為已調（粉紅）</h2>
<div class="pairs">{kerncmp}</div>

<h2>06 ｜ 易混字比對</h2>
<div class="pairs">{conf}</div>

<h2>07 ｜ 字級</h2>
<div class="stack">{water}</div>
<p class="note">窄而密的字不耐小字級，14px 以下僅供確認極限。</p>
</main></body></html>
"""


def webtest(meta, woff2_b64):
    fam = meta["family"]
    feats = [("kern", "字偶", True), ("pnum", "比例數字", False), ("zero", "斜線零", False),
             ("case", "大寫標點", False), ("frac", "分數", False)]
    boxes = "".join(f'<label><input type="checkbox" data-f="{t}" {"checked" if on else ""}> {t} {lab}</label>'
                    for t, lab, on in feats)
    return f"""<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>鐵狐體 網頁測試</title>
<style>{CSS}
@font-face{{font-family:"{fam}";src:url(data:font/woff2;base64,{woff2_b64}) format("woff2");font-display:block}}
.ctl{{display:flex;flex-wrap:wrap;gap:12px 20px;align-items:center;margin:20px 0;font-size:13px;color:var(--dim)}}
.ctl input[type=range]{{width:200px}} .ctl label{{display:flex;gap:6px;align-items:center;cursor:pointer}}
textarea{{width:100%;min-height:80px;background:var(--panel);color:var(--ink);border:1px solid var(--line);padding:12px;font:15px/1.5 ui-monospace,Consolas,monospace;resize:vertical}}
#out{{font-family:"{fam}",monospace;line-height:1.16;margin-top:24px;word-break:break-word;color:var(--ink)}}
.samples{{margin-top:48px;font-family:"{fam}";display:grid;gap:18px}}
.samples div{{border-top:1px solid var(--line);padding-top:12px}} .samples small{{display:block;font:11px ui-monospace,Consolas,monospace;color:var(--dim);margin-bottom:6px}}
.ui{{display:flex;gap:12px;flex-wrap:wrap}} .btn{{font-family:"{fam}";font-size:20px;letter-spacing:.06em;padding:10px 22px;border:2px solid var(--hot);color:var(--hot);background:none;clip-path:polygon(12px 0,100% 0,100% calc(100% - 12px),calc(100% - 12px) 100%,0 100%,0 12px)}}
</style></head><body><main>
<header><div class="tag">{fam} · {meta["revision"]} · WOFF2 實機排版</div>
<h1>鐵狐體 網頁測試</h1>
<p>這一頁用瀏覽器真正載入字型檔（內嵌 WOFF2）排字，可以檢查 hinting、字偶與 OpenType 功能。輸入框可以打任何字；字型裡沒有的字（例如中文）會改用系統字型顯示。</p></header>
<div class="ctl">
<label>字級 <input id="size" type="range" min="12" max="200" value="72"> <span id="sv">72</span>px</label>
<label>字距 <input id="track" type="range" min="-50" max="200" value="0"> <span id="tv">0</span></label>
{boxes}
<label><input type="checkbox" id="theme"> 淺色底</label>
</div>
<textarea id="txt">The Iron Fox — “No fear, no saints.” 0123456789 ½ € 1.299 Œuvre Straße</textarea>
<div id="out"></div>
<div class="samples">
<div><small>介面標題 48px</small><span style="font-size:48px">SYSTEM OVERRIDE / 04</span></div>
<div><small>按鈕 20px</small><div class="ui"><button class="btn">LAUNCH</button><button class="btn">ABORT</button></div></div>
<div><small>數據 tnum 36px</small><span style="font-size:36px;font-feature-settings:'tnum'">1,048,576 · 00:42:17.09</span></div>
<div><small>分數 frac 36px</small><span style="font-size:36px;font-feature-settings:'frac'">1/2 3/4 15/16 7/8</span></div>
<div><small>全大寫 case 36px</small><span style="font-size:36px;font-feature-settings:'case'">«ALPHA» — (BETA) [GAMMA] {{DELTA}} ¿OK?</span></div>
<div><small>小字 16px</small><span style="font-size:16px">Small text check: the quick brown fox jumps over the lazy dog 1234567890.</span></div>
</div>
</main>
<script>
const $=id=>document.getElementById(id);
function upd(){{
  const out=$("out"); out.textContent=$("txt").value;
  out.style.fontSize=$("size").value+"px"; $("sv").textContent=$("size").value;
  out.style.letterSpacing=($("track").value/1000)+"em"; $("tv").textContent=$("track").value;
  const fs=[...document.querySelectorAll("[data-f]")].map(b=>`"${{b.dataset.f}}" ${{b.checked?1:0}}`).join(",");
  out.style.fontFeatureSettings=fs;
  document.documentElement.dataset.theme=$("theme").checked?"light":"";
}}
document.querySelectorAll("input,textarea").forEach(e=>e.addEventListener("input",upd));
upd();
</script></body></html>
"""
