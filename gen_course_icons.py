# -*- coding: utf-8 -*-
"""Generate 16 course icons as PNG (pure-Python, no external deps)."""
import zlib, struct, os

os.makedirs('/tmp/icons', exist_ok=True)

COURSES = [
    ("P1",  (46,109,183), "code"),
    ("P2",  (36,140,90),  "code"),
    ("P3",  (40,110,140), "tree"),
    ("P4",  (70,130,60),  "globe"),
    ("P5",  (180,110,50), "plot"),
    ("P6",  (190,70,70),  "rocket"),
    ("B1",  (108,74,182), "brain"),
    ("B2",  (200,90,40),  "chart"),
    ("B3",  (170,50,90),  "net"),
    ("B4",  (30,120,150), "chat"),
    ("B5",  (120,50,160), "game"),
    ("B6",  (60,100,120), "cloud"),
    ("A1",  (90,90,100),  "eye"),
    ("A2",  (140,110,30), "db"),
    ("A3",  (60,80,180),  "robot"),
    ("A4",  (100,60,60),  "shield"),
]

S = 480
FG = (255, 255, 255)


def make_png(w, h, pixels):
    def chunk(typ, data):
        c = struct.pack('>I', len(data)) + typ + data
        return c + struct.pack('>I', zlib.crc32(typ + data) & 0xffffffff)
    sig = b'\x89PNG\r\n\x1a\n'
    ihdr = chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
    raw = b''
    for y in range(h):
        raw += b'\x00' + bytes(v for x in range(w) for v in pixels[x, y])
    idat = chunk(b'DAT' + b'', zlib.compress(raw, 9)) if False else chunk(b'IDAT', zlib.compress(raw, 9))
    iend = chunk(b'IEND', b'')
    return sig + ihdr + idat + iend


def draw(glyph, bg):
    px = {}
    bg2 = tuple(min(255, int(c * 0.78)) for c in bg)
    for y in range(S):
        t = y / S
        row = tuple(int(bg[i] * (1 - t) + bg2[i] * t) for i in range(3))
        for x in range(S):
            px[x, y] = row
    m = 14
    border = tuple(int(bg[i] * 0.55) for i in range(3))
    for y in range(S):
        for x in range(S):
            if x < m or x >= S - m or y < m or y >= S - m:
                px[x, y] = border
    cx, cy = S // 2, S // 2 - 20
    f = FG

    def rect(x0, y0, x1, y1, col):
        for y in range(max(0, y0), min(S, y1)):
            for x in range(max(0, x0), min(S, x1)):
                px[x, y] = col

    def line(x0, y0, x1, y1, col, w=18):
        steps = max(abs(x1 - x0), abs(y1 - y0), 1)
        r2 = (w // 2) ** 2
        for i in range(steps + 1):
            xx = x0 + (x1 - x0) * i // steps
            yy = y0 + (y1 - y0) * i // steps
            for dy in range(-w // 2, w // 2 + 1):
                for dx in range(-w // 2, w // 2 + 1):
                    if dx * dx + dy * dy <= r2:
                        x2, y2 = xx + dx, yy + dy
                        if 0 <= x2 < S and 0 <= y2 < S:
                            px[x2, y2] = col

    def circle(cx0, cy0, r, col, fill=False, w=10):
        for y in range(max(0, cy0 - r - 2), min(S, cy0 + r + 3)):
            for x in range(max(0, cx0 - r - 2), min(S, cx0 + r + 3)):
                d2 = (x - cx0) ** 2 + (y - cy0) ** 2
                if fill and d2 <= r * r:
                    px[x, y] = col
                elif not fill and abs(d2 - r * r) <= r * w:
                    px[x, y] = col

    if glyph == "code":
        line(cx - 90, cy - 45, cx - 150, cy + 15, f)
        line(cx - 150, cy + 15, cx - 90, cy + 75, f)
        line(cx + 90, cy - 45, cx + 150, cy + 15, f)
        line(cx + 150, cy + 15, cx + 90, cy + 75, f)
        line(cx - 20, cy + 95, cx + 20, cy - 65, f)
    elif glyph == "brain":
        circle(cx - 55, cy - 20, 62, f, w=14)
        circle(cx + 55, cy - 20, 62, f, w=14)
        line(cx, cy - 80, cx, cy + 60, f)
        line(cx - 45, cy + 75, cx, cy + 95, f)
        line(cx + 45, cy + 75, cx, cy + 95, f)
    elif glyph == "chart":
        line(cx - 140, cy + 95, cx + 140, cy + 95, f, w=10)
        for i, bh in enumerate([60, 110, 160]):
            x0 = cx - 100 + i * 80
            rect(x0, cy + 85 - bh, x0 + 55, cy + 85, f)
    elif glyph == "net":
        nodes = [(cx, cy - 90), (cx - 120, cy + 40), (cx + 120, cy + 40),
                 (cx - 60, cy - 30), (cx + 60, cy - 30)]
        dim = tuple(int(c * 0.6) for c in f)
        for a in nodes:
            for b in nodes:
                if a != b:
                    d2 = (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2
                    if d2 < 20000:
                        line(a[0], a[1], b[0], b[1], dim, w=5)
        for n in nodes:
            circle(n[0], n[1], 26, f, fill=True)
    elif glyph == "chat":
        rect(cx - 130, cy - 90, cx + 130, cy + 40, f)
        rect(cx - 80, cy + 40, cx - 20, cy + 95, f)
        circle(cx - 55, cy - 25, 12, bg, fill=True)
        circle(cx + 55, cy - 25, 12, bg, fill=True)
        line(cx - 40, cy + 5, cx + 40, cy + 5, bg, w=12)
    elif glyph == "eye":
        circle(cx, cy, 140, f, w=14)
        circle(cx, cy, 60, f, fill=True)
        circle(cx, cy, 26, bg, fill=True)
    elif glyph == "db":
        for yy in [-70, 0, 70]:
            rect(cx - 110, cy + yy - 18, cx + 110, cy + yy + 18, f)
    elif glyph == "robot":
        rect(cx - 100, cy - 60, cx + 100, cy + 70, f)
        rect(cx - 30, cy - 130, cx + 30, cy - 60, f)
        circle(cx - 45, cy + 5, 16, bg, fill=True)
        circle(cx + 45, cy + 5, 16, bg, fill=True)
        rect(cx - 40, cy + 40, cx + 40, cy + 52, bg)
        line(cx - 100, cy - 10, cx - 140, cy - 10, f)
        line(cx + 100, cy - 10, cx + 140, cy - 10, f)
    elif glyph == "shield":
        line(cx - 110, cy - 90, cx + 110, cy - 90, f)
        line(cx - 110, cy - 90, cx - 110, cy + 30, f)
        line(cx + 110, cy - 90, cx + 110, cy + 30, f)
        line(cx - 110, cy + 30, cx, cy + 120, f)
        line(cx + 110, cy + 30, cx, cy + 120, f)
        line(cx - 45, cy + 5, cx - 10, cy + 45, f, w=14)
        line(cx - 10, cy + 45, cx + 55, cy - 40, f, w=14)
    elif glyph == "tree":
        line(cx, cy - 110, cx, cy + 100, f, w=10)
        for dy in [-90, -20, 50]:
            line(cx, cy + dy + 40, cx - 90, cy + dy + 110, f, w=9)
            line(cx, cy + dy + 40, cx + 90, cy + dy + 110, f, w=9)
            circle(cx - 90, cy + dy + 110, 24, f, fill=True)
            circle(cx + 90, cy + dy + 110, 24, f, fill=True)
    elif glyph == "globe":
        circle(cx, cy, 135, f, w=12)
        circle(cx, cy, 60, f, w=10)
        line(cx - 135, cy, cx + 135, cy, f, w=8)
        line(cx, cy - 135, cx, cy + 135, f, w=8)
        line(cx - 105, cy - 75, cx + 105, cy - 75, f, w=6)
        line(cx - 105, cy + 75, cx + 105, cy + 75, f, w=6)
    elif glyph == "plot":
        line(cx - 140, cy + 95, cx + 140, cy + 95, f, w=10)
        line(cx - 140, cy + 95, cx - 140, cy - 95, f, w=10)
        prev = None
        vals = [20, 55, 35, 80, 60, 110, 90, 130, 120]
        for i in range(9):
            xx = cx - 110 + i * 33
            yy = cy + 70 - vals[i]
            circle(xx, yy, 12, f, fill=True)
            if prev:
                line(prev[0], prev[1], xx, yy, f, w=7)
            prev = (xx, yy)
    elif glyph == "game":
        rect(cx - 140, cy - 80, cx + 140, cy + 80, f)
        rect(cx - 100, cy - 15, cx - 45, cy + 15, bg)
        rect(cx - 80, cy - 35, cx - 65, cy + 35, bg)
        circle(cx + 75, cy + 30, 22, bg, fill=True)
        circle(cx + 35, cy + 30, 22, bg, fill=True)
    elif glyph == "cloud":
        circle(cx - 70, cy + 20, 65, f, fill=True)
        circle(cx + 20, cy + 5, 85, f, fill=True)
        circle(cx + 95, cy + 35, 55, f, fill=True)
        rect(cx - 125, cy + 40, cx + 145, cy + 95, f)
    elif glyph == "rocket":
        for y in range(-120, 100):
            t = abs(y) / 110.0
            halfw = int(50 * (1 - t * t * 0.85))
            rect(cx - halfw, cy + y, cx + halfw, cy + y + 1, f)
        circle(cx, cy - 45, 24, bg, fill=True)
        line(cx - 50, cy + 80, cx - 85, cy + 130, f, w=13)
        line(cx + 50, cy + 80, cx + 85, cy + 130, f, w=13)
        circle(cx, cy + 130, 22, f, fill=True)
    return px


for code, bg, glyph in COURSES:
    px = draw(glyph, bg)
    png = make_png(S, S, px)
    out = '/tmp/icons/%s.png' % code
    open(out, 'wb').write(png)
    print(out, len(png) // 1024, 'KB')
print("DONE: 16 icons generated")
