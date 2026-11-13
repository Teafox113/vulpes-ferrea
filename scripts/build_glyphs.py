#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vulpes Ferrea — glyph generator (design source)
================================================
This script IS the design source of the typeface. Every outline is computed from the
module grid and the parts defined in documentation/design/03-spec.md; nothing is drawn by
hand or traced from another font.

Output: sources/glyphs.json, then calls export_fonts.py to build every deliverable.

    pip install -r requirements.txt
    python scripts/build_glyphs.py

字形產生器（設計原始檔）。所有輪廓都依 documentation/design/03-spec.md 的模組格線與零件計算而來，
沒有手繪，也沒有描摹任何既有字型。
"""
import json
import os
import sys

from shapely import affinity
from shapely.geometry import Polygon
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

# ───────────── 規範常數（docs/03-spec.md §2–§3、§7）─────────────
M = 30
STEM = 3 * M        # 直畫 90
BAR = 2 * M         # 橫畫 60
HAIR = 1 * M        # 細線 30
DW = STEM           # 斜畫水平寬度 90
CAP = 24 * M        # 720
XH = 18 * M         # 540
ASC = 26 * M        # 780
DESC = -7 * M       # -210
MATH = 285          # 數學符號中線（+ = ~ < > 的中心）
W = 9 * M           # 小寫字身 270（90+90+90）
WC = 11 * M         # 大寫字身 330（90+150+90）
FIG_ADV = 450       # 數字等寬字寬
C_LC = 3 * M        # 小寫主切角 90
C_UC = 4 * M        # 大寫主切角 120
C_MIN = 1 * M       # 副切角 30
BLADE = 2 * M       # 刃切 60
SB = 45             # 小寫直邊字腔（SB*2 = 小寫字腔 90）
SB_UC = 60          # 大寫直邊字腔
SB_PT = 30          # 尖端、斜邊、開口字腔
DOT = 60            # 標點菱形半徑
IDOT = 54           # i j 的點
UPM = 1000
SPACE = 210

FAMILY = "Vulpes Ferrea"
REVISION = "r3"   # 設計版次（對應 FONTLOG）

# §6 允許非 45° 斜線的字（布林交點可離格點，原始端點不可）
DIAG = {"k", "v", "w", "x", "z", "K", "M", "N", "R", "V", "W", "X", "Y", "Z", "Q",
        "seven", "slash", "backslash", "percent", "ampersand"}


# ───────────── 零件（§4）─────────────
def R(x0, y0, x1, y1, tl=0, tr=0, bl=0, br=0):
    pts = []
    pts += [(x0, y0 + bl), (x0 + bl, y0)] if bl else [(x0, y0)]
    pts += [(x1 - br, y0), (x1, y0 + br)] if br else [(x1, y0)]
    pts += [(x1, y1 - tr), (x1 - tr, y1)] if tr else [(x1, y1)]
    pts += [(x0 + tl, y1), (x0, y1 - tl)] if tl else [(x0, y1)]
    return Polygon(pts)


def tri(kind, x, y, c):
    """直角頂點在 (x,y) 的 45° 三角形。減 = 外角切角；加 = 內角補角。"""
    dx = c if kind in ("tl", "bl") else -c
    dy = -c if kind in ("tl", "tr") else c
    return Polygon([(x, y), (x + dx, y), (x, y + dy)])


def P(*pts):
    return Polygon(pts)


def diamond(cx, cy, r):
    return Polygon([(cx - r, cy), (cx, cy - r), (cx + r, cy), (cx, cy + r)])


def U(*s):
    return unary_union(list(s))


def cut(shape, *cutters):
    return shape.difference(unary_union(list(cutters)))


def stem(x, y0, y1, top="flat", bot="flat", w=STEM):
    """直畫。top: flat｜blade（尖在右上）｜fork（狐耳）；bot: flat｜blade（尖在左下）。"""
    s = R(x, y0, x + w, y1, tl=BLADE if top == "blade" else 0, br=BLADE if bot == "blade" else 0)
    if top == "fork":
        s = s.difference(P((x, y1), (x + w, y1), (x + w / 2, y1 - w / 2)))
    return s


def diag(xb, yb, xt, yt, w=DW):
    """斜畫：底端 (xb..xb+w, yb)、頂端 (xt..xt+w, yt)，兩端水平切。"""
    return P((xb, yb), (xb + w, yb), (xt + w, yt), (xt, yt))


def bowl(x0, y0, x1, y1, c, major=("tl", "br"), minor=("tr", "bl")):
    o = {k: c for k in major}
    o.update({k: C_MIN for k in minor})
    i = {k: c - 2 * M for k in major}
    return R(x0, y0, x1, y1, **o).difference(R(x0 + STEM, y0 + BAR, x1 - STEM, y1 - BAR, **i))


def hook(xs, x0, y_top, c=C_LC):
    """回勾降部（g j y 共用）：直畫在 xs，降到 DESC 後橫畫回勾到 x0；
    外角主切角 c，內角補 c−2M；回勾的自由端刃切。"""
    s = U(R(xs, DESC, xs + STEM, y_top), R(x0, DESC, xs + STEM, DESC + BAR), tri("br", xs, DESC + BAR, c - 2 * M))
    return cut(s, tri("br", xs + STEM, DESC, c), tri("tl", x0, DESC + BAR, BLADE))


def rot180(shape, w, h):
    return affinity.rotate(shape, 180, origin=(w / 2, h / 2))


def mirror(shape, w):
    return affinity.scale(shape, xfact=-1, yfact=1, origin=(w / 2, 0))


def s_shape(w, h, c, mid):
    s = U(R(0, h - BAR, w, h), R(0, mid, STEM, h), R(0, mid, w, mid + BAR),
          R(w - STEM, 0, w, mid + BAR), R(0, 0, w, BAR),
          tri("tl", STEM, h - BAR, c - 2 * M), tri("br", w - STEM, BAR, c - 2 * M))
    return cut(s, tri("tl", 0, h, c), tri("br", w, 0, c),
               tri("br", w, h - BAR, BLADE), tri("tl", 0, BAR, BLADE),
               tri("tr", w, mid + BAR, C_MIN), tri("bl", 0, mid, C_MIN))


def chevron():
    """< 的骨架：兩條 45° 斜畫，尖端在左，水平切口。字身 0..270，y 105..465。"""
    up = P((180, 465), (270, 465), (90, 285), (0, 285))
    lo = P((0, 285), (90, 285), (270, 105), (180, 105))
    return U(up, lo)


# ───────────── 字形表 ─────────────
G = {}


GRID_EXEMPT = set()   # 縮放字（上標、分數、序數）：格點以 7.5 為單位，登記豁免


def glyph(name, uni, shape, w, lsb=SB, rsb=SB, note="", adv=None):
    """uni：int、int 清單（一字多碼位，如 hyphen + 軟連字號）或 None（替換字，只能經 OpenType 叫出）。"""
    unis = [] if uni is None else ([uni] if isinstance(uni, int) else list(uni))
    G[name] = dict(shape=shape, w=w, lsb=lsb, rsb=rsb, unis=unis, note=note, adv=adv)


def build():
    # ════════ 小寫 ════════
    def n_body(width=W, stems=(0, 180)):
        s = R(0, 0, width, XH, tl=BLADE, tr=C_MIN)
        for a, b in zip(stems[:-1], stems[1:]):
            s = s.difference(R(a + STEM, -10, b, XH - BAR))
        return cut(s, *[tri("br", x + STEM, 0, BLADE) for x in stems])

    n = n_body()
    glyph("n", 0x6E, n, W, note="小寫節奏基準：直畫 90／字腔 90／直畫 90")
    glyph("m", 0x6D, n_body(450, (0, 180, 360)), 450)
    glyph("u", 0x75, rot180(n, W, XH), W, note="n 旋轉 180°")
    h = cut(U(n, R(0, 0, STEM, ASC)), P((0, ASC), (STEM, ASC), (45, ASC - 45)), tri("br", STEM, 0, BLADE))
    glyph("h", 0x68, h, W, note="狐耳叉頂")
    r = cut(U(stem(0, 0, XH, "blade", "blade"), R(0, XH - BAR, 210, XH)),
            tri("br", 210, XH - BAR, BLADE), tri("tl", 0, XH, BLADE))
    glyph("r", 0x72, r, 210, rsb=SB_PT)
    glyph("i", 0x69, U(stem(0, 0, XH, "blade", "blade"), diamond(45, 684, IDOT)), STEM)
    glyph("j", 0x6A, U(hook(90, 0, XH), diamond(135, 684, IDOT)) .difference(tri("tl", 90, XH, BLADE)), 180,
          lsb=SB_PT, note="回勾降部")
    glyph("l", 0x6C, stem(0, 0, ASC, "fork", "blade"), STEM)

    o = bowl(0, 0, W, XH, C_LC)
    glyph("o", 0x6F, o, W, note="小寫字碗：主切 3M、副切 1M、內切 1M")
    glyph("c", 0x63, cut(o, R(180, 120, 280, 420)), W, rsb=SB_PT)
    glyph("e", 0x65, cut(U(o, R(90, 240, 180, 300)), R(180, 60, 280, 240), tri("br", 180, 60, M)), W, rsb=SB_PT)

    a = U(stem(180, 0, XH, "flat", "blade"),
          R(0, XH - BAR, W, XH, tl=BLADE, tr=C_MIN),
          R(0, 0, W, 300, tl=C_LC, bl=C_MIN).difference(R(90, 60, 180, 240, tl=M)))
    glyph("a", 0x61, cut(a, tri("br", W, 0, BLADE)), W,
          note="雙層 a：上下字腔同高 180，字碗頂橫與 e 的腰同高")

    d = U(R(0, 0, W, XH, tl=C_LC, bl=C_MIN).difference(R(90, 60, 180, XH - BAR, tl=M)), R(180, 0, W, ASC))
    glyph("d", 0x64, cut(d, P((180, ASC), (W, ASC), (225, ASC - 45)), tri("br", W, 0, BLADE)), W)
    b = U(R(0, 0, W, XH, tr=C_MIN, br=C_LC, bl=C_MIN).difference(R(90, 60, 180, XH - BAR, br=M)),
          R(0, C_MIN, STEM, ASC).union(R(0, 0, STEM, ASC, bl=C_MIN)))
    glyph("b", 0x62, cut(b, P((0, ASC), (STEM, ASC), (45, ASC - 45))), W, note="d 的筆軸對應，不是鏡射")
    p = U(R(0, 0, W, XH, tr=C_MIN, br=C_LC).difference(R(90, 60, 180, XH - BAR, br=M)),
          stem(0, DESC, XH, "blade", "blade"))
    glyph("p", 0x70, cut(p, tri("tl", 0, XH, BLADE)), W)
    q = U(R(0, 0, W, XH, tl=C_LC, bl=C_MIN).difference(R(90, 60, 180, XH - BAR, tl=M)),
          stem(180, DESC, XH, "flat", "blade"))
    glyph("q", 0x71, cut(q, tri("tr", W, XH, C_MIN)), W, note="直降：自由端刃切")
    g = U(R(0, 0, W, XH, tl=C_LC, bl=C_MIN).difference(R(90, 60, 180, XH - BAR, tl=M)), hook(180, 0, XH))
    glyph("g", 0x67, cut(g, tri("tr", W, XH, C_MIN)), W, note="回勾降部：與 q 只差尾端")
    y = U(R(0, 0, W, XH, bl=C_MIN).difference(R(90, 60, 180, XH + 10)), hook(180, 0, XH))
    glyph("y", 0x79, cut(y, tri("tl", 0, XH, BLADE), tri("tl", 180, XH, BLADE)), W,
          note="織體式 y：u 加回勾降部")

    k_loop = R(0, 300, W, XH, tr=C_MIN, br=C_LC).difference(R(90, 360, 180, XH - BAR, br=M))
    glyph("k", 0x6B, U(stem(0, 0, ASC, "fork", "blade"), k_loop, diag(180, 0, 90, 300)), W, rsb=SB_PT,
          note="r3：織體式閉口 k，上方小碗 + 斜腳，取代 r2 的交叉臂")
    glyph("v", 0x76, U(diag(90, 0, 0, XH), diag(90, 0, 180, XH)), W, lsb=SB_PT, rsb=SB_PT)
    glyph("w", 0x77, U(diag(90, 0, 0, XH), diag(90, 0, 180, XH), diag(270, 0, 180, XH), diag(270, 0, 360, XH)),
          450, lsb=SB_PT, rsb=SB_PT)
    glyph("x", 0x78, U(diag(0, 0, 180, XH), diag(180, 0, 0, XH)), W, lsb=SB_PT, rsb=SB_PT)
    z = U(R(0, XH - BAR, W, XH, tl=BLADE), R(0, 0, W, BAR, br=BLADE), diag(0, BAR, 180, XH - BAR))
    glyph("z", 0x7A, z, W, lsb=SB_PT, rsb=SB_PT)

    glyph("s", 0x73, s_shape(W, XH, C_LC, 240), W, lsb=SB_PT, rsb=SB_PT)
    t = U(R(45, 0, 135, 660, tl=BLADE), R(0, XH - BAR, 210, XH, tl=BLADE, br=BLADE), R(45, 0, 210, BAR, br=BLADE))
    glyph("t", 0x74, cut(t, tri("bl", 45, 0, C_MIN)), 210, lsb=SB_PT, rsb=SB_PT)
    f = U(R(45, 0, 135, ASC, br=BLADE), R(45, ASC - BAR, 240, ASC), R(0, XH - BAR, 210, XH, tl=BLADE, br=BLADE))
    glyph("f", 0x66, cut(f, tri("tl", 45, ASC, BLADE), tri("br", 240, ASC - BAR, BLADE)), 240,
          lsb=SB_PT, rsb=SB_PT)

    # ════════ 大寫 ════════
    X1 = WC - STEM  # 240
    glyph("H", 0x48, U(stem(0, 0, CAP, "blade", "blade"), stem(X1, 0, CAP, "blade", "blade"), R(0, 330, WC, 390)),
          WC, SB_UC, SB_UC, note="大寫節奏基準：直畫 90／字腔 150／直畫 90")
    glyph("I", 0x49, U(R(0, CAP - BAR, 210, CAP, tl=BLADE, br=BLADE), R(60, 0, 150, CAP),
                       R(0, 0, 210, BAR, tl=BLADE, br=BLADE)), 210, SB_PT, SB_PT, note="上下橫畫，與 l 1 區分")
    L = cut(U(stem(0, 0, CAP, "blade"), R(0, 0, WC, BAR, br=BLADE)), tri("bl", 0, 0, C_MIN))
    glyph("L", 0x4C, L, WC - 30, SB_UC, SB_PT)
    E = U(R(0, 0, STEM, CAP), R(0, CAP - BAR, WC, CAP), R(0, 330, 270, 390), R(0, 0, WC, BAR))
    E = cut(E, tri("tl", 0, CAP, BLADE), tri("br", WC, CAP - BAR, BLADE), tri("br", 270, 330, BLADE),
            tri("br", WC, 0, BLADE), tri("bl", 0, 0, C_MIN))
    glyph("E", 0x45, E, WC, SB_UC, SB_PT)
    F = U(stem(0, 0, CAP, "flat", "blade"), R(0, CAP - BAR, WC, CAP), R(0, 330, 270, 390))
    F = cut(F, tri("tl", 0, CAP, BLADE), tri("br", WC, CAP - BAR, BLADE), tri("br", 270, 330, BLADE))
    glyph("F", 0x46, F, WC, SB_UC, SB_PT)
    T = U(R(0, CAP - BAR, WC, CAP, tl=BLADE, br=BLADE), stem(120, 0, CAP, "flat", "blade"))
    glyph("T", 0x54, T, WC, SB_PT, SB_PT)

    A = U(R(0, 0, WC, CAP, tl=C_UC, tr=C_MIN).difference(R(90, -10, X1, CAP - BAR, tl=2 * M)), R(0, 270, WC, 330))
    glyph("A", 0x41, cut(A, tri("br", STEM, 0, BLADE), tri("br", WC, 0, BLADE)), WC, SB_UC, SB_UC,
          note="不對稱 A：主切角取代尖頂")
    O = bowl(0, 0, WC, CAP, C_UC)
    glyph("O", 0x4F, O, WC, SB_UC, SB_UC, note="大寫字碗：主切 4M、副切 1M、內切 2M")
    glyph("C", 0x43, cut(O, R(X1, 180, WC + 10, 540)), WC, SB_UC, SB_PT)
    G_ = U(cut(O, R(X1, 390, WC + 10, 540)), R(165, 330, WC, 390))
    glyph("G", 0x47, cut(G_, tri("tl", 165, 390, BLADE)), WC, SB_UC, SB_UC, note="C 的下半封口，加內橫")
    Q = U(O, P((150, 60), (240, 60), (360, -60), (270, -60)))
    glyph("Q", 0x51, Q, WC, SB_UC, SB_PT, note="r3：45° 尾巴從底橫向右下穿出，與筆軸同向")
    D = R(0, 0, WC, CAP, tr=C_MIN, br=C_UC, bl=C_MIN).difference(R(90, 60, X1, CAP - BAR, br=2 * M))
    glyph("D", 0x44, cut(D, tri("tl", 0, CAP, BLADE)), WC, SB_UC, SB_UC)
    U_ = R(0, 0, WC, CAP, br=C_UC, bl=C_MIN).difference(R(90, 60, X1, CAP + 10, br=2 * M))
    glyph("U", 0x55, cut(U_, tri("tl", 0, CAP, BLADE), tri("tl", X1, CAP, BLADE)), WC, SB_UC, SB_UC)
    J = cut(U_, R(-10, 240, 90, CAP + 10), tri("tl", 0, 240, BLADE), tri("tl", X1, CAP, BLADE))
    glyph("J", 0x4A, J, WC, SB_PT, SB_UC, note="U 的左臂截短")
    bowlP = R(0, 330, WC, CAP, tr=C_MIN, br=C_UC).difference(R(90, 390, X1, CAP - BAR, br=2 * M))
    glyph("P", 0x50, cut(U(stem(0, 0, CAP, "flat", "blade"), bowlP), tri("tl", 0, CAP, BLADE)), WC, SB_UC, SB_PT)
    Rr = cut(U(stem(0, 0, CAP, "flat", "blade"), bowlP, diag(240, 0, 150, 360)), tri("tl", 0, CAP, BLADE))
    glyph("R", 0x52, Rr, WC, SB_UC, SB_PT)
    B = U(R(0, 330, 300, CAP, tr=C_MIN, br=C_LC).difference(R(90, 390, 210, CAP - BAR, br=M)),
          R(0, 0, WC, 390, bl=C_MIN, br=C_UC).difference(R(90, 60, X1, 330, br=2 * M)))
    glyph("B", 0x42, cut(B, tri("tl", 0, CAP, BLADE)), WC, SB_UC, SB_UC,
          note="上碗窄 30，右腰留出缺口，與 8 區分")
    glyph("S", 0x53, s_shape(WC, CAP, C_UC, 330), WC, SB_PT, SB_PT)

    K = U(stem(0, 0, CAP, "blade", "blade"), diag(60, 330, 240, CAP), diag(240, 0, 60, 390))
    glyph("K", 0x4B, K, WC, SB_UC, SB_PT)
    Mm = U(stem(0, 0, CAP, "flat", "blade"), stem(360, 0, CAP, "flat", "blade"),
           diag(180, 240, 0, CAP), diag(180, 240, 360, CAP))
    glyph("M", 0x4D, cut(Mm, tri("tl", 0, CAP, BLADE), tri("tr", 450, CAP, C_MIN)), 450, SB_UC, SB_UC,
          note="中央 V 停在 240，不落地")
    N = U(stem(0, 0, CAP, "flat", "blade"), stem(X1, 0, CAP, "blade", "flat"), diag(X1, 0, 0, CAP))
    glyph("N", 0x4E, N, WC, SB_UC, SB_UC)
    glyph("V", 0x56, U(diag(120, 0, 0, CAP), diag(120, 0, 240, CAP)), WC, SB_PT, SB_PT)
    glyph("W", 0x57, U(diag(120, 0, 0, CAP), diag(120, 0, 240, CAP), diag(360, 0, 240, CAP), diag(360, 0, 480, CAP)),
          570, SB_PT, SB_PT)
    glyph("X", 0x58, U(diag(0, 0, 240, CAP), diag(240, 0, 0, CAP)), WC, SB_PT, SB_PT)
    glyph("Y", 0x59, U(diag(120, 330, 0, CAP), diag(120, 330, 240, CAP), stem(120, 0, 360, "flat", "blade")), WC,
          SB_PT, SB_PT)
    Z = U(R(0, CAP - BAR, WC, CAP, tl=BLADE), R(0, 0, WC, BAR, br=BLADE), diag(0, BAR, 240, CAP - BAR))
    glyph("Z", 0x5A, Z, WC, SB_PT, SB_PT)

    # ════════ 數字（等寬 450）════════
    def fig(name, uni, shape, note=""):
        glyph(name, uni, shape, WC, 60, 60, note=note, adv=FIG_ADV)

    fig("zero", 0x30, U(O, diamond(165, 360, 60)), "菱形零")
    fig("one", 0x31, U(R(120, 0, 210, CAP), P((120, CAP), (15, 615), (15, 525), (120, 630)),
                       R(30, 0, 300, BAR, tl=BLADE, br=BLADE)))
    two = U(R(0, CAP - BAR, WC, CAP), R(X1, 420, WC, CAP), diag(0, 180, X1, 420), R(0, 0, STEM, 180), R(0, 0, WC, BAR))
    fig("two", 0x32, cut(two, tri("tl", 0, CAP, BLADE), tri("tr", WC, CAP, C_MIN), tri("br", WC, 0, BLADE),
                         tri("bl", 0, 0, C_MIN)), "45° 斜腰，取代 r1 的切角腰")
    three = U(R(0, CAP - BAR, WC, CAP), R(90, 330, WC, 390), R(0, 0, WC, BAR), R(X1, 0, WC, CAP),
              tri("br", X1, BAR, 2 * M))
    fig("three", 0x33, cut(three, tri("tl", 0, CAP, BLADE), tri("tl", 90, 390, BLADE), tri("tl", 0, BAR, BLADE),
                           tri("tr", WC, CAP, C_MIN), tri("br", WC, 0, C_UC)))
    four = U(R(0, 270, STEM, CAP, tl=BLADE), R(0, 270, WC, 330), stem(X1, 0, CAP, "blade", "blade"))
    fig("four", 0x34, cut(four, tri("bl", 0, 270, C_MIN)))
    five = U(R(0, CAP - BAR, WC, CAP), R(0, 390, STEM, CAP), R(0, 390, WC, 450), R(X1, 0, WC, 450),
             R(0, 0, WC, BAR), tri("br", X1, BAR, 2 * M), tri("tr", X1, 390, 2 * M))
    fig("five", 0x35, cut(five, tri("br", WC, CAP - BAR, BLADE), tri("tl", 0, BAR, BLADE), tri("br", WC, 0, C_UC),
                          tri("tr", WC, 450, C_UC)),
        "直角肩、腰抬高到 390、碗的右上用主切：三處與 S 區分")
    six = U(R(0, 0, STEM, CAP), R(0, CAP - BAR, WC, CAP), tri("tl", STEM, CAP - BAR, 2 * M),
            R(0, 0, WC, 390, tr=C_MIN, br=C_UC, bl=C_MIN).difference(R(90, 60, X1, 330, br=2 * M)))
    six = cut(six, tri("tl", 0, CAP, C_UC), tri("br", WC, CAP - BAR, BLADE))
    fig("six", 0x36, six)
    seven = cut(U(R(0, CAP - BAR, WC, CAP), diag(60, 0, X1, CAP - BAR)), tri("tl", 0, CAP, BLADE),
                tri("tr", WC, CAP, C_MIN))
    fig("seven", 0x37, seven)
    eight = R(0, 0, WC, CAP, tl=C_UC, tr=C_MIN, bl=C_MIN, br=C_UC).difference(
        U(R(90, 390, X1, CAP - BAR, tl=2 * M), R(90, 60, X1, 330, br=2 * M)))
    fig("eight", 0x38, cut(eight, diamond(0, 360, M), diamond(WC, 360, M)), "腰部菱形缺口")
    fig("nine", 0x39, rot180(six, WC, CAP), "six 旋轉 180°")

    # ════════ 標點與符號 ════════
    pt = dict(lsb=SB_PT, rsb=SB_PT)
    dot = diamond(DOT, DOT, DOT)
    tail = P((120, 60), (120, -30), (0, -150), (0, -60), (60, 0))
    glyph("period", 0x2E, dot, 120, **pt)
    glyph("comma", 0x2C, U(dot, tail), 120, **pt)
    glyph("colon", 0x3A, U(dot, diamond(DOT, XH - DOT, DOT)), 120, **pt)
    glyph("semicolon", 0x3B, U(dot, tail, diamond(DOT, XH - DOT, DOT)), 120, **pt)
    glyph("exclam", 0x21, U(R(15, 210, 105, CAP, tl=BLADE, br=BLADE), dot), 120, **pt)
    q_ = U(R(0, CAP - BAR, W, CAP, tl=BLADE, tr=C_MIN), R(180, 390, W, CAP),
           R(90, 330, W, 390), tri("br", 180, 390, C_LC - 2 * M), stem(90, 180, 390, "flat", "blade"),
           diamond(135, DOT, DOT))
    q_ = cut(q_, tri("br", W, 330, C_LC))
    glyph("question", 0x3F, q_, W, **pt)
    glyph("quotesingle", 0x27, R(0, 510, STEM, CAP), STEM, SB, SB, note="r3：直引號改成無切角的直條，與彎引號的楔形區分")
    glyph("quotedbl", 0x22, U(R(0, 510, STEM, CAP), R(150, 510, 240, CAP)), 240, SB, SB)
    glyph("grave", 0x60, P((0, 750), (90, 750), (210, 630), (120, 630)), 210, **pt)
    glyph("hyphen", 0x2D, R(0, 255, 210, 315, tl=BLADE, br=BLADE), 210, **pt)
    glyph("underscore", 0x5F, R(0, -150, WC, -90), WC, 0, 0)
    glyph("plus", 0x2B, U(R(0, 255, WC, 315), R(120, 120, 210, 450)), WC, **pt)
    glyph("equal", 0x3D, U(R(0, 180, WC, 240), R(0, 330, WC, 390)), WC, **pt)
    tilde = P((0, 225), (150, 225), (240, 315), (360, 315), (360, 375), (210, 375), (120, 285), (0, 285))
    glyph("asciitilde", 0x7E, cut(tilde, tri("tl", 0, 285, BLADE), tri("br", 360, 315, BLADE)), 360, **pt)
    glyph("less", 0x3C, chevron(), 270, **pt)
    glyph("greater", 0x3E, mirror(chevron(), 270), 270, **pt)
    caret = affinity.translate(affinity.rotate(chevron(), -90, origin=(135, 285)), 45, 300)
    glyph("asciicircum", 0x5E, caret, 360, **pt)
    glyph("slash", 0x2F, diag(0, -120, 240, ASC), WC, **pt)
    glyph("backslash", 0x5C, mirror(diag(0, -120, 240, ASC), WC), WC, **pt)
    glyph("bar", 0x7C, R(0, DESC, STEM, ASC), STEM, SB_UC, SB_UC)
    brk = R(0, -150, 180, ASC).difference(R(90, -90, 190, ASC - BAR))
    glyph("bracketleft", 0x5B, brk, 180, SB_UC, SB_PT)
    glyph("bracketright", 0x5D, mirror(brk, 180), 180, SB_PT, SB_UC)
    par = R(0, -150, 180, ASC, tl=C_UC, bl=C_UC).difference(R(90, -90, 190, ASC - BAR, tl=2 * M, bl=2 * M))
    glyph("parenleft", 0x28, par, 180, SB_UC, SB_PT, note="括號成對，切角上下對稱（筆軸例外）")
    glyph("parenright", 0x29, mirror(par, 180), 180, SB_PT, SB_UC)
    brace = U(R(60, -150, 240, ASC, tl=C_MIN, bl=C_MIN).difference(R(150, -90, 250, ASC - BAR)),
              P((60, 405), (0, 345), (0, 285), (60, 225)))
    glyph("braceleft", 0x7B, brace, 240, SB_PT, SB_PT, note="方括號加中央 45° 尖角")
    glyph("braceright", 0x7D, mirror(brace, 240), 240, SB_PT, SB_PT)

    def x45(cx, cy, d, sign):
        if sign > 0:
            return P((cx - 45 - d, cy - d), (cx + 45 - d, cy - d), (cx + 45 + d, cy + d), (cx - 45 + d, cy + d))
        return P((cx - 45 + d, cy - d), (cx + 45 + d, cy - d), (cx + 45 - d, cy + d), (cx - 45 - d, cy + d))

    ast = U(R(120, 420, 210, CAP), x45(165, 570, 120, 1), x45(165, 570, 120, -1))
    glyph("asterisk", 0x2A, ast, WC, **pt)
    hsh = U(stem(30, 30, 630, "blade", "blade"), stem(210, 30, 630, "blade", "blade"),
            R(0, 180, WC, 240, tl=BLADE, br=BLADE), R(0, 420, WC, 480, tl=BLADE, br=BLADE))
    glyph("numbersign", 0x23, hsh, WC, **pt)
    glyph("dollar", 0x24, U(s_shape(WC, CAP, C_UC, 330), R(120, CAP, 210, 810), R(120, -90, 210, 0)), WC, **pt)
    glyph("percent", 0x25, U(diamond(75, 570, 75), diamond(255, 150, 75), diag(30, 0, 210, CAP)), WC, **pt)

    # & （r3 重畫）：上方窄迴圈 + 下方左開 C 形 + 斜腳穿過下字腔 + 右側短臂
    amp = U(R(45, 450, 315, CAP, tl=C_LC, tr=C_MIN).difference(R(135, 510, 225, CAP - BAR, tl=M)),
            R(0, 0, 135, 510, bl=C_MIN), R(0, 0, 270, BAR, bl=C_MIN),
            diag(330, 0, 225, 450), R(270, 240, 420, 300, br=BLADE))
    amp = cut(amp, tri("tl", 0, 510, BLADE))
    glyph("ampersand", 0x26, amp, 420, **pt, note="r3：上迴圈加寬到 90，斜腳改由上迴圈右下直落")

    # @ （r3 重畫）：外框八角環在右下斷開，內 a 放大，a 的直畫接回外框底部
    ring = R(0, -120, 600, 630, tl=C_UC, tr=C_MIN, bl=C_MIN).difference(R(90, -60, 510, 570, tl=2 * M))
    ring = cut(ring, R(450, -130, 610, 150))
    inner = R(150, 60, 450, 450, tl=C_LC, bl=C_MIN).difference(R(240, 120, 360, 390, tl=M))
    at = U(ring, inner, R(360, -60, 450, 450), R(360, -120, 450, -60))
    glyph("at", 0x40, cut(at, tri("br", 600, 150, BLADE)), 600, **pt, note="r3：內 a 放大到 300×390")


# ───────────── 輸出 ─────────────
def contours(shape):
    polys = [shape] if shape.geom_type == "Polygon" else list(shape.geoms)
    out = []
    for p in polys:
        p = orient(p, sign=-1.0)
        for ring in [p.exterior] + list(p.interiors):
            out.append([(round(x, 2), round(y, 2)) for x, y in list(ring.coords)[:-1]])
    return out


def num(v):
    return int(v) if float(v).is_integer() else v




# ═════════════ r3 擴充：第二期排版符號、第三期歐文字母、替換字 ═════════════
def S(name):
    """已建字形的原始形狀（未加左字腔）。"""
    return G[name]["shape"]


def T(shape, dx=0, dy=0):
    return affinity.translate(shape, dx, dy)


def scaled(shape, f, dx=0, dy=0):
    return T(affinity.scale(shape, f, f, origin=(0, 0)), dx, dy)


def r15(v):
    return int(round(v / 15.0)) * 15


# ── 重音零件（§4.1）。每個零件的左下角在 (0,0)。h = 高度 ──
def acc_acute(h):
    return P((0, 0), (90, 0), (90 + h, h), (h, h))


def acc_grave(h):
    return P((h, 0), (h + 90, 0), (90, h), (0, h))


def acc_circ():
    return P((0, 0), (90, 0), (135, 45), (180, 0), (270, 0), (165, 105), (105, 105))


def acc_caron():
    return affinity.scale(acc_circ(), 1, -1, origin=(0, 52.5))


def acc_dier(r=45, gap=90):
    return U(diamond(r, r, r), diamond(3 * r + gap, r, r))


def acc_ring():
    return R(0, 0, 180, 180, tl=60, br=60).difference(R(60, 60, 120, 120))


def acc_tilde(d):
    return P((0, 0), (105, 0), (105 + d, d), (270, d), (270, d + 60), (165, d + 60), (165 - d, 60), (0, 60))


def acc_macron():
    return R(0, 0, 270, BAR, tl=BLADE, br=BLADE)


def acc_cedilla():
    return cut(U(R(60, -150, 120, 0), R(0, -150, 120, -90)), tri("tl", 0, -90, M))


ACC_LC_Y = XH + 60      # 小寫重音底線 600
ACC_UC_Y = CAP + 45     # 大寫重音底線 765


def accent(kind, cap):
    """回傳 (形狀, 底端 y)。大寫版本較矮，頂端不超過 900。"""
    h = 90 if cap else 120
    return {
        "acute": acc_acute(h), "grave": acc_grave(h), "circumflex": acc_circ(), "caron": acc_caron(),
        "dieresis": acc_dier(), "ring": acc_ring(), "tilde": acc_tilde(45 if cap else 60),
        "macron": acc_macron(), "cedilla": acc_cedilla(),
    }[kind]


def compose(name, uni, base, kind, cap=None, note=""):
    """基本字母 + 重音零件。重音以基本字母的外框中心對齊，位移取 15 的倍數；
    重音若超出字身，字腔自動加寬到至少留 15，避免碰到鄰字。"""
    b = G[base]
    if cap is None:
        cap = base[0].isupper()
    bs = b["shape"]
    minx, miny, maxx, maxy = bs.bounds
    if base in ("dotlessi",):
        minx, maxx = 0, STEM
    a = accent(kind, cap)
    aw = a.bounds[2] - a.bounds[0]
    dx = r15((minx + maxx) / 2 - aw / 2)
    if kind == "cedilla":
        dy = 0
    elif kind == "ring" and cap:
        dy = CAP - 30        # Å：環與 A 的頂橫熔接（北歐常見寫法），頂端 870
    else:
        dy = ACC_UC_Y if cap else ACC_LC_Y
    shape = U(bs, T(a, dx, dy))
    lsb, rsb, w = b["lsb"], b["rsb"], b["w"]
    over_l = max(0, -dx)
    over_r = max(0, dx + aw - w)
    if over_l:
        shape = T(shape, over_l)
    w2 = w + over_l + over_r
    lsb2 = max(15, lsb - over_l)
    rsb2 = max(15, rsb - over_r)
    glyph(name, uni, shape, w2, lsb2, rsb2, note=note or f"{base} + {kind}", adv=b["adv"])
    BASE_OF[name] = base


BASE_OF = {}


def build_ext():
    pt = dict(lsb=SB_PT, rsb=SB_PT)

    # ── 一字多碼位 ──
    G["hyphen"]["unis"].append(0x00AD)        # 軟連字號

    # ── 引號：楔形。’ 是直畫底端切 90（3M）的 45° 楔，尖端朝左下；‘ 是 ’ 轉 180°。
    #    r2 的「菱形 + 斜尾」放到大寫高會被看成 ‹ ›，所以彎引號不沿用逗號造形。──
    qr = R(0, 510, STEM, CAP, br=STEM)
    ql = affinity.rotate(qr, 180, origin=(45, (510 + CAP) / 2))
    glyph("quoteright", 0x2019, qr, STEM, **pt)
    glyph("quoteleft", 0x2018, ql, STEM, **pt)
    glyph("quotedblright", 0x201D, U(qr, T(qr, 150)), 240, **pt)
    glyph("quotedblleft", 0x201C, U(ql, T(ql, 150)), 240, **pt)
    qb = T(qr, 0, -600)                       # 底線引號：y −90..120
    glyph("quotesinglbase", 0x201A, qb, STEM, **pt)
    glyph("quotedblbase", 0x201E, U(qb, T(qb, 150)), 240, **pt)

    # ── 破折號、減號 ──
    glyph("endash", 0x2013, R(0, 255, 450, 315, tl=BLADE, br=BLADE), 450, 0, 0, note="寬 = 數字寬，可接成連續線")
    glyph("emdash", 0x2014, R(0, 255, 900, 315, tl=BLADE, br=BLADE), 900, 0, 0)
    glyph("minus", 0x2212, R(0, 255, WC, 315), WC, **pt)
    glyph("figuredash", 0x2012, R(0, 255, 390, 315, tl=BLADE, br=BLADE), 390, 30, 30, adv=FIG_ADV)

    # ── 刪節號、間隔號、項目符號 ──
    dot = S("period")
    glyph("ellipsis", 0x2026, U(dot, T(dot, 210), T(dot, 420)), 540, **pt)
    glyph("periodcentered", 0x00B7, diamond(DOT, MATH, DOT), 120, **pt)
    glyph("bullet", 0x2022, diamond(105, MATH, 105), 210, 45, 45)

    # ── 數學 ──
    def xcross(cx, cy, d):
        a = P((cx - 45 - d, cy - d), (cx + 45 - d, cy - d), (cx + 45 + d, cy + d), (cx - 45 + d, cy + d))
        return U(a, mirror(a, 2 * cx))

    glyph("multiply", 0x00D7, xcross(165, MATH, 120), WC, **pt)
    glyph("divide", 0x00F7, U(R(0, 255, WC, 315), diamond(165, MATH + 135, 45), diamond(165, MATH - 135, 45)), WC, **pt)
    glyph("plusminus", 0x00B1, U(R(0, 345, WC, 405), R(120, 225, 210, 525), R(0, 90, WC, 150)), WC, **pt)
    glyph("logicalnot", 0x00AC, U(R(0, 315, WC, 375), R(240, 165, WC, 375)), WC, **pt)
    glyph("degree", 0x00B0, R(0, 540, 180, CAP, tl=60, br=60).difference(R(60, 600, 120, 660)), 180, **pt)

    # ── 角引號 ──
    def chev(half, c=MATH):
        up = P((half, c + half), (half + 90, c + half), (90, c), (0, c))
        lo = P((0, c), (90, c), (half + 90, c - half), (half, c - half))
        return U(up, lo)

    sg = chev(120)
    glyph("guilsinglleft", 0x2039, sg, 210, **pt)
    glyph("guilsinglright", 0x203A, mirror(sg, 210), 210, **pt)
    glyph("guillemotleft", 0x00AB, U(sg, T(sg, 150)), 360, **pt)
    glyph("guillemotright", 0x00BB, mirror(U(sg, T(sg, 150)), 360), 360, **pt)

    # ── 倒置標點 ──
    ex = S("exclam")
    glyph("exclamdown", 0x00A1, T(affinity.rotate(ex, 180, origin=(60, 360)), 0, XH - CAP), 120, **pt)
    qu = S("question")
    glyph("questiondown", 0x00BF, T(affinity.rotate(qu, 180, origin=(W / 2, 360)), 0, XH - CAP), W, **pt)

    # ── 貨幣 ──
    C_ = S("C")
    glyph("Euro", 0x20AC, U(T(C_, 60), R(0, 270, 270, 330, tl=BLADE, br=BLADE), R(0, 390, 270, 450, tl=BLADE, br=BLADE)),
          390, **pt, note="C + 兩條刃切橫畫")
    glyph("sterling", 0x00A3, cut(U(stem(60, 0, CAP - BAR), R(60, CAP - BAR, WC, CAP, tl=C_UC - 60),
                                    R(0, 300, 270, 360, tl=BLADE, br=BLADE), R(0, 0, WC, BAR)),
                                  tri("tl", 60, CAP, C_UC), tri("br", WC, CAP - BAR, BLADE), tri("br", WC, 0, BLADE),
                                  tri("bl", 0, 0, C_MIN)), WC, **pt)
    Y_ = S("Y")
    glyph("yen", 0x00A5, U(Y_, R(15, 120, 315, 180, tl=BLADE, br=BLADE), R(15, 240, 315, 300, tl=BLADE, br=BLADE)), WC,
          **pt)
    c_ = S("c")
    glyph("cent", 0x00A2, U(c_, R(90, XH, 180, XH + 90), R(90, -90, 180, 0)), W, **pt)
    cur = R(75, 135, 345, 405, tl=60, br=60, tr=30, bl=30).difference(R(150, 210, 270, 330))
    glyph("currency", 0x00A4, U(cur, diamond(75, 405, 45), diamond(345, 405, 45), diamond(75, 135, 45),
                                diamond(345, 135, 45)), 420, **pt)
    f_ = S("f")
    flor = U(T(f_, 45), R(90, DESC, 180, 0), R(0, DESC, 180, DESC + BAR))
    glyph("florin", 0x0192, cut(flor, tri("tl", 0, DESC + BAR, BLADE)), 285, **pt)

    # ── 段落、劍號、分隔號 ──
    s_lo = s_shape(W, 450, C_LC, 195)
    glyph("section", 0x00A7, U(T(s_lo, 0, 270), s_lo), W, **pt, note="兩個 s 交疊")
    glyph("paragraph", 0x00B6, U(R(0, 360, 150, CAP, tl=C_UC, bl=C_MIN), stem(120, 0, CAP, "flat", "blade"),
                                 stem(270, 0, CAP, "flat", "blade"), R(120, CAP - BAR, 360, CAP)), 360, **pt)
    glyph("dagger", 0x2020, U(stem(120, -150, CAP, "flat", "blade"), R(0, 450, WC, 510, tl=BLADE, br=BLADE)), WC, **pt)
    glyph("daggerdbl", 0x2021, U(stem(120, -150, CAP), R(0, 450, WC, 510, tl=BLADE, br=BLADE),
                                 R(0, 60, WC, 120, tl=BLADE, br=BLADE)), WC, **pt)
    glyph("brokenbar", 0x00A6, U(R(0, DESC, STEM, 225), R(0, 345, STEM, ASC)), STEM, SB_UC, SB_UC)

    # ── 版權、註冊、商標 ──
    def badge(inner):
        ring = R(0, 60, 600, 660, tl=150, tr=150, bl=150, br=150).difference(
            R(60, 120, 540, 600, tl=120, tr=120, bl=120, br=120))
        return U(ring, inner)

    smallC = R(180, 210, 420, 510, tl=90, bl=30).difference(R(240, 270, 430, 450, tl=30))
    glyph("copyright", 0x00A9, badge(smallC), 600, **pt)
    smallR = U(R(180, 210, 240, 510), R(180, 360, 420, 510, tr=30, br=90).difference(R(240, 420, 360, 450)),
               P((285, 360), (345, 360), (420, 210), (360, 210)))
    glyph("registered", 0x00AE, badge(smallR), 600, **pt)
    tm = U(R(0, 660, 240, 720), R(90, 420, 150, 660),
           R(300, 420, 360, 720), R(540, 420, 600, 720), P((360, 720), (420, 720), (450, 630), (480, 720), (540, 720),
                                                             (480, 540), (420, 540)))
    glyph("trademark", 0x2122, tm, 600, **pt, note="上標尺寸，筆畫 60")

    # ── 重音零件（獨立字元）──
    for name, uni, kind in [("acute", 0x00B4, "acute"), ("dieresis", 0x00A8, "dieresis"), ("macron", 0x00AF, "macron"),
                            ("cedilla", 0x00B8, "cedilla"), ("circumflex", 0x02C6, "circumflex"),
                            ("tilde", 0x02DC, "tilde"), ("caron", 0x02C7, "caron"), ("ring", 0x02DA, "ring")]:
        a = accent(kind, False)
        glyph(name, uni, a if kind == "cedilla" else T(a, 0, ACC_LC_Y), a.bounds[2], **pt)

    # ── 上標、分子、分母、分數（縮放 0.5，登記格點豁免）──
    figs = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
    for f in figs:
        raw = G[f]["shape"]
        glyph(f + ".numr", None, scaled(raw, 0.5, 0, 360), 165, 30, 30)
        glyph(f + ".dnom", None, scaled(raw, 0.5, 0, 0), 165, 30, 30)
        GRID_EXEMPT.update({f + ".numr", f + ".dnom"})
    for f, uni in [("one", 0x00B9), ("two", 0x00B2), ("three", 0x00B3)]:
        glyph(f + "superior", uni, scaled(G[f]["shape"], 0.5, 0, 360), 165, 30, 30)
        GRID_EXEMPT.add(f + "superior")
    frac = diag(0, 0, 210, CAP, w=60)
    glyph("fraction", 0x2044, frac, 270, -60, -60)
    for name, uni, a, b in [("onequarter", 0x00BC, "one", "four"), ("onehalf", 0x00BD, "one", "two"),
                            ("threequarters", 0x00BE, "three", "four")]:
        sh = U(scaled(G[a]["shape"], 0.5, 0, 360), T(frac, 90), scaled(G[b]["shape"], 0.5, 285, 0))
        glyph(name, uni, sh, 450, **pt)
        GRID_EXEMPT.add(name)
    glyph("perthousand", 0x2030, U(S("percent"), diamond(435, 150, 75)), 510, **pt)

    # ── 序數 ──
    glyph("ordfeminine", 0x00AA, U(scaled(S("a"), 0.5, 0, 450), R(0, 360, 135, 390)), 135, **pt)
    glyph("ordmasculine", 0x00BA, U(scaled(S("o"), 0.5, 0, 450), R(0, 360, 135, 390)), 135, **pt)
    GRID_EXEMPT.update({"ordfeminine", "ordmasculine"})

    # ── 獨立歐文字母 ──
    glyph("dotlessi", 0x0131, stem(0, 0, XH, "blade", "blade"), STEM)
    mu = U(S("u"), stem(0, DESC, XH, "blade", "blade"))
    glyph("mu", 0x00B5, mu, W)
    X1 = WC - STEM
    AE = U(R(0, 0, STEM, CAP), R(0, CAP - BAR, 480, CAP), R(210, 0, 300, CAP), R(0, 330, 450, 390), R(210, 0, 480, BAR),
           tri("tl", STEM, CAP - BAR, 2 * M))
    AE = cut(AE, tri("tl", 0, CAP, C_UC), tri("br", STEM, 0, BLADE), tri("br", 480, CAP - BAR, BLADE),
             tri("br", 450, 330, BLADE), tri("br", 480, 0, BLADE), tri("bl", 210, 0, C_MIN))
    glyph("AE", 0x00C6, AE, 480, SB_UC, SB_PT)
    OE = U(R(0, 0, 300, CAP, tl=C_UC, bl=C_MIN).difference(R(90, 60, 210, CAP - BAR, tl=2 * M)),
           R(210, CAP - BAR, 480, CAP), R(210, 330, 450, 390), R(210, 0, 480, BAR))
    OE = cut(OE, tri("br", 480, CAP - BAR, BLADE), tri("br", 450, 330, BLADE), tri("br", 480, 0, BLADE))
    glyph("OE", 0x0152, OE, 480, SB_UC, SB_PT)
    glyph("ae", 0x00E6, U(S("a"), T(S("e"), 180)), 450, SB, SB_PT)
    glyph("oe", 0x0153, U(S("o"), T(S("e"), 180)), 450, SB, SB_PT)
    glyph("Oslash", 0x00D8, U(S("O"), diag(0, -45, 240, CAP + 45)), WC, SB_UC - 15, SB_UC - 15)
    glyph("oslash", 0x00F8, U(S("o"), diag(0, -45, 180, XH + 45)), W, SB - 15, SB - 15)
    glyph("Eth", 0x00D0, U(T(S("D"), 60), R(0, 330, 210, 390, tl=BLADE, br=BLADE)), WC + 60, SB_PT, SB_UC)
    eth = U(R(0, 0, W, 450, tl=C_LC, bl=C_MIN, br=C_LC).difference(R(90, 60, 180, 390, tl=M, br=M)),
            diag(180, 360, 60, ASC - 60), R(60, 600, 270, 660, tl=BLADE, br=BLADE))
    glyph("eth", 0x00F0, eth, W, SB, SB_PT)
    Thorn = U(stem(0, 0, CAP, "blade", "blade"),
              R(0, 150, WC, 570, tr=C_MIN, br=C_UC).difference(R(90, 210, X1, 510, br=2 * M)))
    glyph("Thorn", 0x00DE, Thorn, WC, SB_UC, SB_UC)
    thorn = U(stem(0, DESC, ASC, "fork", "blade"),
              R(0, 0, W, XH, tr=C_MIN, br=C_LC).difference(R(90, 60, 180, XH - BAR, br=M)))
    glyph("thorn", 0x00FE, thorn, W)
    # ß（織體 ſʒ 寫法）：長 s 的直畫 + 頂橫 + 右上短直畫 → 45° 斜畫回到腰部 → ʒ 形下碗，底橫在左側斷開
    ss = U(stem(0, 0, ASC - BAR, "flat", "blade"), R(0, ASC - BAR, W, ASC), R(180, 600, W, ASC),
           P((90, 510), (180, 510), (270, 600), (180, 600)),
           R(90, 450, 300, 510), R(210, 0, 300, 510), R(150, 0, 300, BAR),
           tri("tl", STEM, ASC - BAR, M), tri("br", 210, BAR, M))
    ss = cut(ss, tri("tl", 0, ASC, C_LC), tri("tr", W, ASC, C_MIN), tri("tl", 150, BAR, C_MIN),
             tri("tr", 300, 510, C_MIN), tri("br", 300, 0, C_LC))
    glyph("germandbls", 0x00DF, ss, 300, note="織體 ſʒ 寫法：斜畫腰部與 ʒ 形下碗，與 B、A 區分")

    # ── 重音字 ──
    acc_map = {"grave": "grave", "acute": "acute", "circumflex": "circumflex", "tilde": "tilde",
               "dieresis": "dieresis", "ring": "ring", "cedilla": "cedilla", "caron": "caron"}
    table = [
        ("A", 0x00C0, "grave"), ("A", 0x00C1, "acute"), ("A", 0x00C2, "circumflex"), ("A", 0x00C3, "tilde"),
        ("A", 0x00C4, "dieresis"), ("A", 0x00C5, "ring"), ("C", 0x00C7, "cedilla"),
        ("E", 0x00C8, "grave"), ("E", 0x00C9, "acute"), ("E", 0x00CA, "circumflex"), ("E", 0x00CB, "dieresis"),
        ("I", 0x00CC, "grave"), ("I", 0x00CD, "acute"), ("I", 0x00CE, "circumflex"), ("I", 0x00CF, "dieresis"),
        ("N", 0x00D1, "tilde"),
        ("O", 0x00D2, "grave"), ("O", 0x00D3, "acute"), ("O", 0x00D4, "circumflex"), ("O", 0x00D5, "tilde"),
        ("O", 0x00D6, "dieresis"),
        ("U", 0x00D9, "grave"), ("U", 0x00DA, "acute"), ("U", 0x00DB, "circumflex"), ("U", 0x00DC, "dieresis"),
        ("Y", 0x00DD, "acute"), ("Y", 0x0178, "dieresis"), ("S", 0x0160, "caron"), ("Z", 0x017D, "caron"),
        ("a", 0x00E0, "grave"), ("a", 0x00E1, "acute"), ("a", 0x00E2, "circumflex"), ("a", 0x00E3, "tilde"),
        ("a", 0x00E4, "dieresis"), ("a", 0x00E5, "ring"), ("c", 0x00E7, "cedilla"),
        ("e", 0x00E8, "grave"), ("e", 0x00E9, "acute"), ("e", 0x00EA, "circumflex"), ("e", 0x00EB, "dieresis"),
        ("dotlessi", 0x00EC, "grave"), ("dotlessi", 0x00ED, "acute"), ("dotlessi", 0x00EE, "circumflex"),
        ("dotlessi", 0x00EF, "dieresis"), ("n", 0x00F1, "tilde"),
        ("o", 0x00F2, "grave"), ("o", 0x00F3, "acute"), ("o", 0x00F4, "circumflex"), ("o", 0x00F5, "tilde"),
        ("o", 0x00F6, "dieresis"),
        ("u", 0x00F9, "grave"), ("u", 0x00FA, "acute"), ("u", 0x00FB, "circumflex"), ("u", 0x00FC, "dieresis"),
        ("y", 0x00FD, "acute"), ("y", 0x00FF, "dieresis"), ("s", 0x0161, "caron"), ("z", 0x017E, "caron"),
    ]
    for base, uni, kind in table:
        nm = {"dotlessi": "i"}.get(base, base) + acc_map[kind]
        if uni == 0x0178:
            nm = "Ydieresis"
        compose(nm, uni, base, kind, cap=base[0].isupper())

    # ── 替換字（OpenType）──
    for f in figs:
        sh = G[f]["shape"]
        mnx, _, mxx, _ = sh.bounds
        glyph(f + ".pnum", None, T(sh, -mnx), mxx - mnx, 45, 45)
    glyph("zero.slash", None, U(S("O"), diag(90, 60, 150, CAP - BAR)), WC, 60, 60, adv=FIG_ADV,
          note="斜線零（zero 功能）")
    DIAG.add("zero.slash")
    case = {"hyphen": 75, "endash": 75, "emdash": 75, "guilsinglleft": 75, "guilsinglright": 75,
            "guillemotleft": 75, "guillemotright": 75, "parenleft": 45, "parenright": 45, "bracketleft": 45,
            "bracketright": 45, "braceleft": 45, "braceright": 45, "exclamdown": CAP - XH, "questiondown": CAP - XH,
            "periodcentered": 75, "bullet": 75}
    for n, dy in case.items():
        g = G[n]
        glyph(n + ".case", None, T(g["shape"], 0, dy), g["w"], g["lsb"], g["rsb"], adv=g["adv"])

    # §6 斜線字登記：新字與「基本字母已登記」的衍生字
    DIAG.update({"registered", "trademark", "fraction", "perthousand", "Oslash", "oslash", "eth", "yen"})
    DIAG.update(n for n, b in BASE_OF.items() if b in DIAG)
    DIAG.update(f + ".pnum" for f in figs if f in DIAG)
    return case, figs


def finalize():
    data = {}
    for name, g in G.items():
        shape = affinity.translate(g["shape"], xoff=g["lsb"]).simplify(0.01)
        if g["adv"] and name in FIGS_TNUM:  # 等寬數字：置中
            minx, _, maxx, _ = shape.bounds
            shape = affinity.translate(shape, xoff=(g["adv"] - (maxx - minx)) / 2 - minx)
            shape = affinity.translate(shape, xoff=-(shape.bounds[0] % 15))
        adv = g["adv"] or g["lsb"] + g["w"] + g["rsb"]
        u = g["unis"]
        data[name] = dict(unicode=u[0] if u else None, unicodes=u, char=chr(u[0]) if u else "",
                          advance=int(adv), lsb=num(shape.bounds[0]), rsb=num(adv - shape.bounds[2]),
                          note=g["note"], contours=[[[num(x), num(y)] for x, y in c] for c in contours(shape)])
    return data


FIGS_TNUM = {"zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "zero.slash", "figuredash"}


# ═════════════ OpenType 功能（§8）═════════════
# 字偶：以字形外側輪廓分類。左類看字形「右側」，右類看字形「左側」。重音字自動跟隨基本字母。
KERN_LEFT = {
    "L_T": ["T"], "L_V": ["V", "W"], "L_Y": ["Y"], "L_L": ["L"], "L_FP": ["F", "P"], "L_KX": ["K", "X"],
    "L_A": ["A"], "L_r": ["r"], "L_vwy": ["v", "w", "y"], "L_kx": ["k", "x"], "L_f": ["f"],
    "L_quote": ["quotesingle", "quotedbl", "quoteright", "quotedblright", "quoteleft", "quotedblleft"],
    "L_comma": ["period", "comma", "ellipsis", "quotesinglbase", "quotedblbase"],
    "L_hyph": ["hyphen", "endash", "emdash"],
}
KERN_RIGHT = {
    "R_O": ["C", "G", "O", "Q", "Oslash", "OE"], "R_A": ["A", "AE"], "R_J": ["J"], "R_T": ["T"], "R_V": ["V", "W"],
    "R_Y": ["Y"],
    "R_lr": ["a", "c", "d", "e", "g", "o", "q", "s", "ae", "oe", "oslash", "eth"],
    "R_lx": ["m", "n", "p", "r", "u", "dotlessi", "mu"], "R_lv": ["v", "w", "y"], "R_lz": ["x", "z"],
    "R_quote": ["quotesingle", "quotedbl", "quoteright", "quotedblright", "quoteleft", "quotedblleft"],
    "R_comma": ["period", "comma", "ellipsis", "quotesinglbase", "quotedblbase"],
    "R_hyph": ["hyphen", "endash", "emdash"],
}
KERN_PAIRS = [
    ("L_T", "R_lr", -75), ("L_T", "R_lx", -60), ("L_T", "R_lv", -45), ("L_T", "R_lz", -45), ("L_T", "R_comma", -75),
    ("L_T", "R_hyph", -60), ("L_T", "R_A", -30), ("L_T", "R_O", -15), ("L_T", "R_J", -60),
    ("L_V", "R_lr", -45), ("L_V", "R_lx", -30), ("L_V", "R_comma", -60), ("L_V", "R_hyph", -30), ("L_V", "R_A", -30),
    ("L_V", "R_O", -15), ("L_V", "R_J", -45),
    ("L_Y", "R_lr", -60), ("L_Y", "R_lx", -45), ("L_Y", "R_comma", -75), ("L_Y", "R_hyph", -45), ("L_Y", "R_A", -30),
    ("L_Y", "R_O", -15), ("L_Y", "R_J", -60),
    ("L_L", "R_T", -75), ("L_L", "R_V", -60), ("L_L", "R_Y", -75), ("L_L", "R_quote", -90), ("L_L", "R_hyph", -45),
    ("L_L", "R_O", -15),
    ("L_FP", "R_comma", -75), ("L_FP", "R_A", -30), ("L_FP", "R_lr", -30), ("L_FP", "R_J", -45),
    ("L_KX", "R_O", -30), ("L_KX", "R_lr", -30), ("L_KX", "R_hyph", -45),
    ("L_A", "R_T", -30), ("L_A", "R_V", -30), ("L_A", "R_Y", -30), ("L_A", "R_quote", -45),
    ("L_r", "R_comma", -60), ("L_r", "R_hyph", -30),
    ("L_vwy", "R_comma", -45), ("L_vwy", "R_lr", -15),
    ("L_kx", "R_lr", -30), ("L_kx", "R_hyph", -30),
    ("L_f", "R_quote", 30), ("L_f", "R_comma", -30),
    ("L_quote", "R_A", -45), ("L_quote", "R_J", -60), ("L_quote", "R_lr", -30),
    ("L_comma", "R_T", -75), ("L_comma", "R_V", -60), ("L_comma", "R_Y", -75), ("L_comma", "R_quote", -90),
    ("L_hyph", "R_T", -60), ("L_hyph", "R_V", -30), ("L_hyph", "R_Y", -45),
]


def kern_classes(names):
    def expand(cls):
        out = {}
        for k, members in cls.items():
            ms = [m for m in members if m in names]
            ms += [n for n, b in BASE_OF.items() if b in members and n in names and n not in ms]
            out[k] = ms
        return out
    return expand(KERN_LEFT), expand(KERN_RIGHT)


def features(names, case, figs):
    left, right = kern_classes(names)
    fea = ["languagesystem DFLT dflt;", "languagesystem latn dflt;", ""]
    fea += [f"@{k} = [{' '.join(v)}];" for k, v in {**left, **right}.items() if v]
    tn = [f for f in figs]
    fea += [f"@figs = [{' '.join(tn)}];", f"@pnum = [{' '.join(f + '.pnum' for f in figs)}];",
            f"@numr = [{' '.join(f + '.numr' for f in figs)}];", f"@dnom = [{' '.join(f + '.dnom' for f in figs)}];",
            f"@case_in = [{' '.join(case)}];", f"@case_out = [{' '.join(n + '.case' for n in case)}];", ""]
    fea += ["feature kern {"] + [f"  pos @{a} @{b} {v};" for a, b, v in KERN_PAIRS if left.get(a) and right.get(b)] + \
           ["} kern;", ""]
    fea += ["feature pnum { sub @figs by @pnum; } pnum;", "feature tnum { sub @pnum by @figs; } tnum;",
            "feature zero { sub zero by zero.slash; } zero;",
            "feature case { sub @case_in by @case_out; } case;",
            "feature frac {",
            "  lookup FRAC_N { sub @figs by @numr; } FRAC_N;",
            "  lookup FRAC_S { sub slash by fraction; } FRAC_S;",
            "  lookup FRAC_D { sub [fraction @dnom] @numr' by @dnom; } FRAC_D;",
            "} frac;",
            "feature numr { sub @figs by @numr; } numr;", "feature dnom { sub @figs by @dnom; } dnom;", ""]
    flat = {}
    for a, b, v in KERN_PAIRS:
        for x in left.get(a, []):
            for y in right.get(b, []):
                flat[f"{x} {y}"] = v
    return "\n".join(fea), flat


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.normpath(os.path.join(here, ".."))
    build()
    case, figs = build_ext()
    data = finalize()
    fea, flat = features(set(data), case, figs)
    meta = dict(family=FAMILY, revision=REVISION, upm=UPM, space=SPACE, diag_glyphs=sorted(DIAG),
                grid_exempt=sorted(GRID_EXEMPT), base_of=BASE_OF,
                metrics=dict(M=M, stem=STEM, bar=BAR, hair=HAIR, diag_width=DW, cap=CAP, xheight=XH,
                             ascender=ASC, descender=DESC, math_axis=MATH, width_lc=W, width_uc=WC,
                             figure_advance=FIG_ADV, sidebearing=SB, sidebearing_uc=SB_UC, sidebearing_point=SB_PT,
                             chamfer_lc=C_LC, chamfer_uc=C_UC, chamfer_minor=C_MIN, blade=BLADE,
                             accent_lc_base=ACC_LC_Y, accent_uc_base=ACC_UC_Y),
                kern=flat, features=fea)
    os.makedirs(os.path.join(root, "sources"), exist_ok=True)
    with open(os.path.join(root, "sources", "glyphs.json"), "w", encoding="utf-8") as fh:
        json.dump(dict(meta=meta, glyphs=data), fh, ensure_ascii=False, separators=(",", ":"))
    sys.path.insert(0, here)
    import export_fonts
    sys.exit(1 if export_fonts.export(root) else 0)


if __name__ == "__main__":
    main()
