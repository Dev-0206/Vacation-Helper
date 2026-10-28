"""Generate one illustrated SVG scene per destination into static/scenes/.

The scenes are original, simple, layered silhouettes (sky, sun, ridges, skylines, palms and so on).
They are drawn from code, so they are small, sharp at any size, and free of any photo licensing.

Run from the project root:  python tools/make_scenes.py
"""
import math
import os
import random

W, H = 1600, 900
OUT = os.path.join(os.path.dirname(__file__), "..", "static", "scenes")


def n(v):
    return f"{v:.1f}"


def mix(c1, c2, t):
    """Blend two #rrggbb colors. t=0 gives c1, t=1 gives c2."""
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(a[i] + (b[i] - a[i]) * t):02x}" for i in range(3))


class Scene:
    def __init__(self, seed, sky, sun=None, stars=0):
        self.rng = random.Random(seed)
        self.defs = []
        self.parts = []
        self._gid = 0
        self.defs.append(
            '<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="{sky[0]}"/>'
            f'<stop offset="0.55" stop-color="{sky[1]}"/>'
            f'<stop offset="1" stop-color="{sky[2]}"/></linearGradient>'
        )
        self.defs.append('<filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="7"/></filter>')
        self.defs.append('<filter id="soft" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="22"/></filter>')
        self.parts.append(f'<rect width="{W}" height="{H}" fill="url(#sky)"/>')
        for _ in range(stars):
            x, y = self.rng.uniform(0, W), self.rng.uniform(0, H * 0.55)
            r = self.rng.choice([1, 1, 1.4, 2])
            o = self.rng.uniform(0.35, 0.95)
            self.parts.append(f'<circle cx="{n(x)}" cy="{n(y)}" r="{r}" fill="#fff" opacity="{n(o)}"/>')
        if sun:
            x, y, r, color = sun
            self.parts.append(f'<circle cx="{n(x)}" cy="{n(y)}" r="{n(r * 2.6)}" fill="{color}" opacity="0.28" filter="url(#soft)"/>')
            self.parts.append(f'<circle cx="{n(x)}" cy="{n(y)}" r="{n(r)}" fill="{color}"/>')

    def gid(self):
        self._gid += 1
        return f"g{self._gid}"

    def add(self, s):
        self.parts.append(s)

    def grad_fill(self, top, bottom):
        g = self.gid()
        self.defs.append(
            f'<linearGradient id="{g}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{top}"/><stop offset="1" stop-color="{bottom}"/></linearGradient>'
        )
        return f"url(#{g})"

    def ridge(self, base, amp, color, light=None, op=1.0, sharp=False, peak=None, seed=0):
        rng = random.Random(seed or self.rng.random())
        ph = [rng.uniform(0, 6.28) for _ in range(4)]
        pts = []
        x = -20
        while x <= W + 20:
            if peak:
                cx, wd, ht = peak
                h = max(0.0, 1 - abs(x - cx) / wd) ** 1.15 * ht
                h += 14 * math.sin(x * 0.03 + ph[0]) + 8 * math.sin(x * 0.09 + ph[1])
                y = base - max(0, h)
            elif sharp:
                v = 0.55 * abs(math.sin(x * 0.0045 + ph[0])) + 0.3 * abs(math.sin(x * 0.011 + ph[1])) + 0.15 * abs(math.sin(x * 0.027 + ph[2]))
                y = base - amp * v
            else:
                v = 0.5 + 0.28 * math.sin(x * 0.004 + ph[0]) + 0.16 * math.sin(x * 0.011 + ph[1]) + 0.06 * math.sin(x * 0.03 + ph[2])
                y = base - amp * v
            pts.append((x, y))
            x += 16
        d = "M-20 %d " % H + " ".join(f"L{n(px)} {n(py)}" for px, py in pts) + f" L{W + 20} {H} Z"
        fill = self.grad_fill(light or color, color) if light else color
        self.add(f'<path d="{d}" fill="{fill}" opacity="{op}"/>')

    def skyline(self, base, x0, x1, hmin, hmax, wmin, wmax, color, windows=None, op=1.0, tall=None):
        rng = self.rng
        x = x0
        out = []
        wins = []
        while x < x1:
            w = rng.uniform(wmin, wmax)
            h = rng.uniform(hmin, hmax)
            if tall and rng.random() < tall:
                h *= 1.6
            top = base - h
            out.append(f'<rect x="{n(x)}" y="{n(top)}" width="{n(w)}" height="{n(h + 2)}"/>')
            if rng.random() < 0.18:
                out.append(f'<rect x="{n(x + w * 0.3)}" y="{n(top - 16)}" width="{n(w * 0.4)}" height="18"/>')
            if rng.random() < 0.1:
                out.append(f'<rect x="{n(x + w * 0.47)}" y="{n(top - 46)}" width="2.4" height="48"/>')
            if windows:
                col, density = windows
                cols = max(1, int(w // 14))
                rows = max(1, int(h // 22))
                for cx in range(cols):
                    for cy in range(rows):
                        if rng.random() < density:
                            wins.append(f'<rect x="{n(x + 5 + cx * 14)}" y="{n(top + 8 + cy * 22)}" width="5" height="8"/>')
            x += w + rng.uniform(0, 5)
        self.add(f'<g fill="{color}" opacity="{op}">' + "".join(out) + "</g>")
        if wins:
            self.add(f'<g fill="{windows[0]}" opacity="0.85">' + "".join(wins) + "</g>")

    def neon_strip(self, base, x0, x1, palette, dark):
        rng = self.rng
        x = x0
        glows, solids = [], []
        while x < x1:
            w = rng.uniform(46, 120)
            h = rng.uniform(120, 420)
            top = base - h
            solids.append(f'<rect x="{n(x)}" y="{n(top)}" width="{n(w)}" height="{n(h + 2)}"/>')
            for band in range(rng.randint(1, 3)):
                col = rng.choice(palette)
                by = top + rng.uniform(10, h - 24)
                r = f'<rect x="{n(x + 4)}" y="{n(by)}" width="{n(w - 8)}" height="6" fill="{col}"/>'
                glows.append(r)
            if rng.random() < 0.5:
                col = rng.choice(palette)
                glows.append(f'<rect x="{n(x)}" y="{n(top)}" width="{n(w)}" height="4" fill="{col}"/>')
            x += w + rng.uniform(6, 26)
        self.add(f'<g fill="{dark}">' + "".join(solids) + "</g>")
        self.add('<g filter="url(#glow)" opacity="0.9">' + "".join(glows) + "</g>")
        self.add("<g>" + "".join(glows) + "</g>")

    def needle(self, x, base, h, color):
        self.add(
            f'<g fill="{color}"><rect x="{n(x - 3)}" y="{n(base - h)}" width="6" height="{n(h)}"/>'
            f'<path d="M{n(x - 58)} {n(base - h * 0.78)} Q{n(x)} {n(base - h * 0.9)} {n(x + 58)} {n(base - h * 0.78)} Q{n(x)} {n(base - h * 0.7)} {n(x - 58)} {n(base - h * 0.78)} Z"/>'
            f'<rect x="{n(x - 1.4)}" y="{n(base - h - 46)}" width="2.8" height="50"/>'
            f'<path d="M{n(x - 20)} {n(base)} L{n(x - 5)} {n(base - h * 0.7)} L{n(x + 5)} {n(base - h * 0.7)} L{n(x + 20)} {n(base)} Z"/></g>'
        )

    def spire_tower(self, x, base, h, w, color):
        s = []
        steps = [(1.0, 0.0), (0.78, 0.55), (0.56, 0.78), (0.34, 0.9)]
        for ww, hh in steps:
            top = base - h * (1 - hh * 0.0)
        # stepped tower from wide base to narrow top
        y = base
        parts = [(w, h * 0.55), (w * 0.78, h * 0.2), (w * 0.56, h * 0.15), (w * 0.34, h * 0.1)]
        for ww, hh in parts:
            s.append(f'<rect x="{n(x - ww / 2)}" y="{n(y - hh)}" width="{n(ww)}" height="{n(hh + 1)}"/>')
            y -= hh
        s.append(f'<rect x="{n(x - 1.6)}" y="{n(y - 70)}" width="3.2" height="72"/>')
        self.add(f'<g fill="{color}">' + "".join(s) + "</g>")

    def bridge(self, x0, x1, deck, tower_h, color, cable=None):
        cable = cable or color
        t1, t2 = x0 + (x1 - x0) * 0.24, x0 + (x1 - x0) * 0.76
        top = deck - tower_h
        parts = [f'<rect x="{n(x0)}" y="{n(deck)}" width="{n(x1 - x0)}" height="10" fill="{color}"/>']
        for t in (t1, t2):
            parts.append(f'<rect x="{n(t - 7)}" y="{n(top)}" width="14" height="{n(tower_h + 40)}" fill="{color}"/>')
            parts.append(f'<rect x="{n(t - 15)}" y="{n(top + tower_h * 0.28)}" width="30" height="7" fill="{color}"/>')
            parts.append(f'<rect x="{n(t - 15)}" y="{n(top + tower_h * 0.58)}" width="30" height="7" fill="{color}"/>')
        mid = (t1 + t2) / 2
        parts.append(f'<path d="M{n(x0)} {n(deck - 6)} Q{n((x0 + t1) / 2)} {n(deck + 20)} {n(t1)} {n(top)}" stroke="{cable}" stroke-width="4" fill="none"/>')
        parts.append(f'<path d="M{n(t1)} {n(top)} Q{n(mid)} {n(deck + 20)} {n(t2)} {n(top)}" stroke="{cable}" stroke-width="4" fill="none"/>')
        parts.append(f'<path d="M{n(t2)} {n(top)} Q{n((t2 + x1) / 2)} {n(deck + 20)} {n(x1)} {n(deck - 6)}" stroke="{cable}" stroke-width="4" fill="none"/>')
        x = t1
        while x < t2:
            cy = top + (deck - top) * (1 - 4 * ((x - t1) / (t2 - t1)) * (1 - (x - t1) / (t2 - t1)) * 0.0)
            sag = (deck + 20 - top) * 4 * ((x - t1) / (t2 - t1)) * (1 - (x - t1) / (t2 - t1))
            y_cable = top + sag * 0.78
            parts.append(f'<line x1="{n(x)}" y1="{n(y_cable)}" x2="{n(x)}" y2="{n(deck)}" stroke="{cable}" stroke-width="1.6"/>')
            x += 22
        self.add("<g>" + "".join(parts) + "</g>")

    def palm(self, x, base, h, lean, color):
        tx, ty = x + lean, base - h
        d = f"M{n(x - 5)} {n(base)} Q{n(x + lean * 0.2)} {n(base - h * 0.55)} {n(tx - 3)} {n(ty)} L{n(tx + 3)} {n(ty)} Q{n(x + lean * 0.3 + 6)} {n(base - h * 0.55)} {n(x + 5)} {n(base)} Z"
        leaves = []
        for ang in (-165, -140, -112, -80, -52, -25, -5):
            a = math.radians(ang)
            L = h * 0.5
            ex, ey = tx + math.cos(a) * L, ty + math.sin(a) * L * 0.62 + L * 0.28
            cx, cy = tx + math.cos(a) * L * 0.5, ty + math.sin(a) * L * 0.62 - L * 0.12
            leaves.append(f'<path d="M{n(tx)} {n(ty)} Q{n(cx)} {n(cy - 18)} {n(ex)} {n(ey)} Q{n(cx)} {n(cy + 8)} {n(tx)} {n(ty + 4)} Z"/>')
        self.add(f'<g fill="{color}"><path d="{d}"/>' + "".join(leaves) + "</g>")

    def fir(self, x, base, h, color):
        w = h * 0.42
        tiers = []
        for i in range(5):
            t = i / 5
            ty = base - h * (0.2 + t * 0.8)
            tw = w * (1 - t * 0.78)
            tiers.append(f"M{n(x - tw)} {n(ty + h * 0.2)} L{n(x)} {n(ty - h * 0.08)} L{n(x + tw)} {n(ty + h * 0.2)} Z")
        self.add(f'<g fill="{color}"><rect x="{n(x - 3)}" y="{n(base - h * 0.18)}" width="6" height="{n(h * 0.2)}"/><path d="{" ".join(tiers)}"/></g>')

    def forest(self, base, x0, x1, hmin, hmax, color, gap=(18, 40)):
        x = x0
        while x < x1:
            self.fir(x, base, self.rng.uniform(hmin, hmax), color)
            x += self.rng.uniform(*gap)

    def saguaro(self, x, base, h, color):
        w = h * 0.12
        self.add(
            f'<g fill="{color}"><rect x="{n(x - w / 2)}" y="{n(base - h)}" width="{n(w)}" height="{n(h)}" rx="{n(w / 2)}"/>'
            f'<path d="M{n(x - w / 2)} {n(base - h * 0.45)} h{n(-w * 1.4)} v{n(-h * 0.28)} h{n(w * 0.55)} v{n(h * 0.2)} h{n(w * 0.85)} Z"/>'
            f'<rect x="{n(x - w * 1.9)}" y="{n(base - h * 0.73)}" width="{n(w * 0.55)}" height="{n(h * 0.3)}" rx="{n(w * 0.27)}"/>'
            f'<path d="M{n(x + w / 2)} {n(base - h * 0.6)} h{n(w * 1.3)} v{n(-h * 0.22)} h{n(-w * 0.5)} v{n(h * 0.14)} h{n(-w * 0.8)} Z"/>'
            f'<rect x="{n(x + w * 1.3)}" y="{n(base - h * 0.84)}" width="{n(w * 0.55)}" height="{n(h * 0.26)}" rx="{n(w * 0.27)}"/></g>'
        )

    def water(self, top, color_top, color_bottom, streak=None, streak_x=None):
        fill = self.grad_fill(color_top, color_bottom)
        self.add(f'<rect x="0" y="{n(top)}" width="{W}" height="{n(H - top)}" fill="{fill}"/>')
        if streak:
            cx = streak_x or W / 2
            for i in range(9):
                y = top + 12 + i * ((H - top) / 10)
                w = 220 * (1 - i * 0.07) + self.rng.uniform(-20, 20)
                self.add(f'<rect x="{n(cx - w / 2)}" y="{n(y)}" width="{n(w)}" height="{3 + i * 0.5:.1f}" rx="2" fill="{streak}" opacity="{n(0.55 - i * 0.04)}"/>')
        for i in range(10):
            y = top + 20 + i * ((H - top) / 11)
            x = self.rng.uniform(0, W)
            w = self.rng.uniform(60, 190)
            self.add(f'<rect x="{n(x)}" y="{n(y)}" width="{n(w)}" height="2" rx="1" fill="#ffffff" opacity="0.1"/>')

    def waves(self, top, color, count=5):
        for i in range(count):
            y = top + i * 26
            d = f"M0 {n(y)} " + " ".join(
                f"Q{n(x + 60)} {n(y - 10 - i)} {n(x + 120)} {n(y)}" for x in range(0, W, 240)
            ) + " " + " ".join(f"Q{n(x + 60)} {n(y + 10 + i)} {n(x + 120)} {n(y)}" for x in range(120, W, 240))
            self.add(f'<path d="M0 {n(y)} ' + " ".join(f"q60 {-9 - i * 2} 120 0 t120 0" for _ in range(14)) + f'" stroke="{color}" stroke-width="2.2" fill="none" opacity="{n(0.55 - i * 0.08)}"/>')

    def ferris(self, x, y, r, color, light):
        parts = [f'<circle cx="{n(x)}" cy="{n(y)}" r="{n(r)}" fill="none" stroke="{color}" stroke-width="4"/>',
                 f'<circle cx="{n(x)}" cy="{n(y)}" r="{n(r * 0.62)}" fill="none" stroke="{color}" stroke-width="2"/>']
        for i in range(16):
            a = math.radians(i * 22.5)
            ex, ey = x + math.cos(a) * r, y + math.sin(a) * r
            parts.append(f'<line x1="{n(x)}" y1="{n(y)}" x2="{n(ex)}" y2="{n(ey)}" stroke="{color}" stroke-width="2"/>')
            parts.append(f'<circle cx="{n(ex)}" cy="{n(ey)}" r="6" fill="{light}"/>')
        parts.append(f'<path d="M{n(x - r * 0.55)} {n(y + r * 1.35)} L{n(x)} {n(y)} L{n(x + r * 0.55)} {n(y + r * 1.35)}" stroke="{color}" stroke-width="6" fill="none"/>')
        self.add("<g>" + "".join(parts) + "</g>")

    def fireworks(self, bursts):
        for x, y, r, color in bursts:
            parts = []
            for i in range(22):
                a = math.radians(i * (360 / 22))
                x1, y1 = x + math.cos(a) * r * 0.25, y + math.sin(a) * r * 0.25
                x2, y2 = x + math.cos(a) * r, y + math.sin(a) * r
                parts.append(f'<line x1="{n(x1)}" y1="{n(y1)}" x2="{n(x2)}" y2="{n(y2)}"/>')
                parts.append(f'<circle cx="{n(x2)}" cy="{n(y2)}" r="3.4" fill="{color}" stroke="none"/>')
            self.add(f'<g stroke="{color}" stroke-width="2.4" stroke-linecap="round" opacity="0.95">' + "".join(parts) + "</g>")
            self.add(f'<circle cx="{n(x)}" cy="{n(y)}" r="{n(r * 0.9)}" fill="{color}" opacity="0.14" filter="url(#soft)"/>')

    def string_lights(self, y, sag, color, x0=-20, x1=W + 20, count=26):
        d = f"M{x0} {n(y)} Q{n((x0 + x1) / 2)} {n(y + sag * 2)} {x1} {n(y)}"
        bulbs = []
        for i in range(count + 1):
            t = i / count
            bx = x0 + (x1 - x0) * t
            by = y + sag * 4 * t * (1 - t) * 1.0 * 1.0
            bulbs.append(f'<circle cx="{n(bx)}" cy="{n(by + 8)}" r="5" fill="{color}"/>')
        self.add(f'<path d="{d}" stroke="#1a1020" stroke-width="2" fill="none" opacity="0.7"/>')
        self.add('<g filter="url(#glow)" opacity="0.95">' + "".join(bulbs) + "</g>")
        self.add("<g>" + "".join(bulbs) + "</g>")

    def rowhouses(self, base, x0, x1, colors, window):
        rng = self.rng
        x = x0
        parts, wins = [], []
        while x < x1:
            w = rng.uniform(70, 120)
            h = rng.uniform(150, 260)
            col = rng.choice(colors)
            top = base - h
            parts.append(f'<rect x="{n(x)}" y="{n(top)}" width="{n(w)}" height="{n(h + 2)}" fill="{col}"/>')
            parts.append(f'<rect x="{n(x - 3)}" y="{n(top - 8)}" width="{n(w + 6)}" height="10" fill="{mix(col, "#000000", 0.25)}"/>')
            if rng.random() < 0.6:
                parts.append(f'<rect x="{n(x + w * 0.65)}" y="{n(top - 34)}" width="12" height="36" fill="{mix(col, "#000000", 0.15)}"/>')
            for rr in range(int(h // 46)):
                for cc in range(int(w // 34)):
                    wins.append(f'<rect x="{n(x + 10 + cc * 30)}" y="{n(top + 18 + rr * 44)}" width="14" height="22" rx="2"/>')
            x += w + 2
        self.add("<g>" + "".join(parts) + "</g>")
        self.add(f'<g fill="{window}" opacity="0.8">' + "".join(wins) + "</g>")

    def steeple(self, x, base, h, color):
        self.add(
            f'<g fill="{color}"><rect x="{n(x - 26)}" y="{n(base - h * 0.55)}" width="52" height="{n(h * 0.55)}"/>'
            f'<path d="M{n(x - 20)} {n(base - h * 0.55)} L{n(x)} {n(base - h)} L{n(x + 20)} {n(base - h * 0.55)} Z"/>'
            f'<rect x="{n(x - 1.5)}" y="{n(base - h - 30)}" width="3" height="32"/></g>'
        )

    def fog(self, y, h, color, op=0.5):
        g = self.gid()
        self.defs.append(
            f'<linearGradient id="{g}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{color}" stop-opacity="0"/>'
            f'<stop offset="0.5" stop-color="{color}" stop-opacity="{op}"/><stop offset="1" stop-color="{color}" stop-opacity="0"/></linearGradient>'
        )
        self.add(f'<rect x="0" y="{n(y)}" width="{W}" height="{n(h)}" fill="url(#{g})"/>')

    def beams(self, xs, color):
        for x in xs:
            self.add(f'<path d="M{n(x)} {H} L{n(x - 120)} 0 L{n(x + 120)} 0 Z" fill="{color}" opacity="0.09"/>')

    def dunes(self, base, amp, color, light=None, seed=0):
        rng = random.Random(seed or self.rng.random())
        ph = [rng.uniform(0, 6.28) for _ in range(3)]
        pts = []
        x = -20
        while x <= W + 20:
            v = 0.5 + 0.34 * math.sin(x * 0.0035 + ph[0]) + 0.16 * math.sin(x * 0.009 + ph[1])
            pts.append((x, base - amp * v))
            x += 16
        d = "M-20 %d " % H + " ".join(f"L{n(px)} {n(py)}" for px, py in pts) + f" L{W + 20} {H} Z"
        fill = self.grad_fill(light or color, color) if light else color
        self.add(f'<path d="{d}" fill="{fill}"/>')

    def save(self, name):
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid slice" aria-hidden="true">'
            f'<defs>{"".join(self.defs)}</defs>{"".join(self.parts)}</svg>'
        )
        os.makedirs(OUT, exist_ok=True)
        path = os.path.join(OUT, f"{name}.svg")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(svg)
        return len(svg)


def seattle():
    s = Scene(11, ("#1b2a4a", "#6377ad", "#f4a98c"), sun=(1180, 600, 66, "#ffd9b0"), stars=24)
    s.ridge(600, 0, "#7d8db8", light="#dfe6f5", op=0.9, peak=(520, 520, 330), seed=3)
    s.ridge(640, 120, "#4b5b86", light="#6f80ae", op=0.9, seed=5)
    s.skyline(690, 600, 1250, 50, 190, 28, 60, "#27324f", windows=("#ffd48a", 0.12))
    s.needle(900, 690, 300, "#1e2845")
    s.water(690, "#1d2b4d", "#0e1830", streak="#ffcf9a", streak_x=1180)
    s.forest(720, -20, 330, 150, 290, "#0c1630", gap=(24, 46))
    s.forest(735, 1380, 1640, 140, 250, "#0c1630", gap=(24, 46))
    return s


def miami():
    s = Scene(12, ("#2a1055", "#c2417f", "#ffb36b"), sun=(800, 580, 96, "#ffe1a8"), stars=18)
    s.water(600, "#3a2f78", "#1b1747", streak="#ffd7a0", streak_x=800)
    s.rowhouses(600, 1050, 1640, ["#f3b9c6", "#9ad6d1", "#f7d9a8", "#c5b4e8"], "#ffe9b8")
    s.rowhouses(600, -20, 360, ["#9ad6d1", "#f3b9c6", "#f7d9a8"], "#ffe9b8")
    s.add(f'<rect x="0" y="600" width="{W}" height="300" fill="#1d1030" opacity="0.18"/>')
    for x, h, l in ((120, 440, 30), (330, 360, -26), (1250, 470, 34), (1480, 380, -30)):
        s.palm(x, 760, h, l, "#1b0f2e")
    s.dunes(840, 70, "#2a1640", light="#3b2158")
    return s


def denver():
    s = Scene(13, ("#4f7fb5", "#9fc3dd", "#ffe0b0"), sun=(1230, 330, 60, "#fff3d1"))
    s.ridge(600, 330, "#6f8fb5", light="#e8f0f8", op=0.95, sharp=True, seed=4)
    s.ridge(660, 260, "#4a6890", light="#7c9bbd", sharp=True, seed=8)
    s.ridge(740, 170, "#2f4766", light="#42607f", sharp=True, seed=9)
    s.forest(800, -20, 1640, 90, 190, "#14263a", gap=(14, 30))
    s.dunes(900, 100, "#0f1e2e")
    return s


def san_diego():
    s = Scene(14, ("#3aa5d9", "#8dd3ee", "#fff1cf"), sun=(1230, 230, 72, "#fff7dc"))
    s.water(520, "#35a4cf", "#1b6e9c", streak="#ffffff", streak_x=1230)
    s.waves(600, "#ffffff", 5)
    s.ridge(560, 60, "#d6a272", light="#efc596", seed=2)
    s.dunes(900, 220, "#e8cd92", light="#f6e3b2", seed=6)
    s.dunes(900, 140, "#c98d58", light="#dba670", seed=7)
    for x, h, l in ((180, 470, 40), (420, 380, -28), (1380, 430, -34)):
        s.palm(x, 790, h, l, "#15382a")
    return s


def chicago():
    s = Scene(15, ("#14213d", "#3b5b92", "#f7b27a"), sun=(1000, 540, 56, "#ffe2b8"), stars=14)
    s.skyline(620, -20, 1640, 90, 250, 40, 90, "#2a3f6b", op=0.8, tall=0.2)
    s.skyline(640, -20, 1640, 130, 360, 46, 100, "#18233f", windows=("#ffd48a", 0.2), tall=0.3)
    s.spire_tower(640, 640, 460, 110, "#101a33")
    s.water(640, "#16264a", "#0a1228", streak="#ffd7a0", streak_x=1000)
    s.add(f'<rect x="0" y="640" width="{W}" height="6" fill="#0a1228"/>')
    return s


def boston():
    s = Scene(16, ("#3a2a52", "#c46a6a", "#ffc17a"), sun=(520, 560, 70, "#ffe6bd"), stars=12)
    s.water(640, "#3b2f5e", "#1d1838", streak="#ffd9a6", streak_x=520)
    s.skyline(640, 980, 1640, 120, 260, 44, 80, "#2d2142", windows=("#ffd48a", 0.2))
    s.rowhouses(660, -20, 900, ["#7a3a36", "#8b4a3e", "#6b3030", "#9a5a46"], "#ffd48a")
    s.steeple(980, 660, 330, "#2a1c3a")
    for x, sz in ((1180, 1.0), (1370, 0.7)):
        s.add(f'<g fill="#1a1230"><path d="M{x} 760 L{x} {n(760 - 110 * sz)} L{n(x + 50 * sz)} 760 Z"/><path d="M{x - 6} 764 L{n(x + 60 * sz)} 764 L{n(x + 48 * sz)} 774 L{x + 2} 774 Z"/></g>')
    s.dunes(900, 60, "#1d1838")
    return s


def las_vegas():
    s = Scene(17, ("#0b0620", "#2a0f55", "#c33a8f"), sun=(1280, 190, 40, "#f3e9ff"), stars=90)
    s.ridge(640, 130, "#26104a", seed=2)
    s.neon_strip(700, 120, 1500, ["#35f2ff", "#ff3fb0", "#ffd23f", "#9b6bff"], "#150a2e")
    s.add(f'<rect x="0" y="700" width="{W}" height="200" fill="#0a0518"/>')
    for i in range(14):
        x = 140 + i * 100
        s.add(f'<rect x="{x}" y="740" width="60" height="5" rx="2" fill="#ff3fb0" opacity="{n(0.15 + (i % 3) * 0.1)}"/>')
    return s


def phoenix():
    s = Scene(18, ("#ff7a3d", "#ffb05a", "#ffe0a3"), sun=(800, 520, 118, "#fff0b8"))
    s.ridge(640, 150, "#c0553a", light="#e68a5f", op=0.85, sharp=True, seed=5)
    s.dunes(780, 120, "#9a4430", light="#c0653f", seed=6)
    s.dunes(850, 120, "#6b2a22", light="#8b3b2c", seed=7)
    for x, h in ((220, 340), (1320, 400), (1480, 270), (110, 230)):
        s.saguaro(x, 880, h, "#2a1414")
    s.dunes(920, 70, "#2a1414")
    return s


def austin():
    s = Scene(19, ("#2a1b4d", "#a14a7a", "#ffb870"), sun=(1120, 590, 60, "#ffe2b8"), stars=12)
    s.skyline(660, 640, 1400, 60, 220, 34, 70, "#241a45", windows=("#ffd48a", 0.16))
    s.water(660, "#2a2050", "#150f30", streak="#ffd9a6", streak_x=1120)
    s.string_lights(150, 120, "#ffd98a")
    s.string_lights(250, 90, "#ff9fd0", x0=-20, x1=900, count=14)
    s.add(f'<g fill="#150f26"><rect x="150" y="470" width="30" height="300"/><circle cx="165" cy="400" r="150"/><circle cx="60" cy="470" r="110"/><circle cx="290" cy="470" r="120"/></g>')
    s.dunes(900, 80, "#150f26")
    return s


def new_york():
    s = Scene(20, ("#0d1b3a", "#32508c", "#f09a78"), sun=(1280, 560, 50, "#ffd9b8"), stars=18)
    s.skyline(640, -20, 1640, 120, 330, 38, 80, "#24386a", op=0.75, tall=0.25)
    s.skyline(660, -20, 1640, 170, 440, 44, 96, "#141f3d", windows=("#ffd48a", 0.22), tall=0.35)
    s.spire_tower(820, 660, 560, 120, "#0b1328")
    s.water(660, "#14234a", "#08102a", streak="#ffd0a0", streak_x=1280)
    return s


def orlando():
    s = Scene(21, ("#0a0a2e", "#3a1a6e", "#e5568a"), stars=70)
    s.fireworks([(420, 220, 120, "#ffd23f"), (860, 150, 150, "#ff6fb5"), (1250, 260, 110, "#35f2ff"), (1480, 140, 80, "#ffd23f")])
    s.water(660, "#2a1550", "#0f0826", streak="#ff6fb5", streak_x=860)
    s.ferris(1180, 520, 150, "#190c34", "#ffd98a")
    s.dunes(700, 40, "#140a2a")
    for x, h, l in ((130, 460, 34), (330, 360, -26), (1470, 420, -30)):
        s.palm(x, 780, h, l, "#0f0724")
    s.dunes(900, 70, "#0f0724")
    return s


def san_francisco():
    s = Scene(22, ("#4a4e7d", "#e8909a", "#ffd2a0"), sun=(1260, 520, 70, "#fff0d0"))
    s.ridge(560, 160, "#6a5a7e", light="#8a7690", op=0.9, seed=3)
    s.water(640, "#3a4672", "#1c2548", streak="#ffe0b8", streak_x=1260)
    s.bridge(120, 1500, 640, 330, "#c9442b", cable="#d9573a")
    s.fog(500, 240, "#ffe9e0", 0.55)
    s.ridge(900, 150, "#2d2a48", light="#3f3a5c", seed=9)
    s.fog(660, 160, "#ffe9e0", 0.35)
    return s


def nashville():
    s = Scene(23, ("#1c1033", "#5b2a6e", "#ff9a5a"), sun=(1260, 600, 54, "#ffd9b0"), stars=30)
    s.beams([300, 640, 1000], "#ffd9b0")
    s.skyline(660, 560, 1380, 60, 210, 30, 66, "#1a1030", windows=("#ffd48a", 0.18))
    s.add('<g fill="#1a1030"><path d="M890 660 L890 380 L910 340 L930 380 L930 660 Z"/><path d="M1010 660 L1010 430 L1028 400 L1046 430 L1046 660 Z"/></g>')
    s.water(660, "#271645", "#10081f", streak="#ffd0a0", streak_x=1260)
    s.string_lights(170, 100, "#ffb86b")
    s.string_lights(300, 80, "#ff7fb0", x0=700, x1=1620, count=16)
    s.dunes(900, 70, "#10081f")
    return s


def portland():
    s = Scene(24, ("#2f4a4a", "#7aa39a", "#ece4c4"), sun=(1280, 260, 52, "#fff6da"))
    s.ridge(620, 0, "#8ea9a4", light="#eef4f0", op=0.9, peak=(800, 520, 420), seed=3)
    s.fog(480, 200, "#f3f0e0", 0.6)
    s.forest(760, -20, 1640, 130, 250, "#274840", gap=(14, 26))
    s.fog(620, 200, "#f3f0e0", 0.45)
    s.forest(840, -20, 1640, 160, 300, "#14302a", gap=(16, 30))
    s.add('<path d="M860 840 Q1100 730 1340 840" stroke="#0c221d" stroke-width="12" fill="none"/>')
    s.dunes(920, 60, "#0c221d")
    return s


def salt_lake_city():
    s = Scene(25, ("#2b4a7a", "#7aa7d6", "#ffe6c2"), sun=(1290, 260, 60, "#ffffff"))
    s.ridge(560, 330, "#9db8da", light="#ffffff", op=0.95, sharp=True, seed=4)
    s.ridge(620, 250, "#5f7ba5", light="#a8bfdc", sharp=True, seed=11)
    s.water(640, "#e6eef8", "#b9cbe3", streak="#ffffff", streak_x=900)
    s.ridge(900, 0, "#7e98bb", op=0.0, seed=2)
    s.forest(660, -20, 400, 70, 150, "#1c3150", gap=(16, 30))
    s.forest(660, 1250, 1640, 70, 150, "#1c3150", gap=(16, 30))
    s.add(f'<rect x="0" y="640" width="{W}" height="4" fill="#ffffff" opacity="0.5"/>')
    return s


SCENES = {
    "seattle": seattle,
    "miami": miami,
    "denver": denver,
    "san-diego": san_diego,
    "chicago": chicago,
    "boston": boston,
    "las-vegas": las_vegas,
    "phoenix": phoenix,
    "austin": austin,
    "new-york": new_york,
    "orlando": orlando,
    "san-francisco": san_francisco,
    "nashville": nashville,
    "portland": portland,
    "salt-lake-city": salt_lake_city,
}

if __name__ == "__main__":
    for name, fn in SCENES.items():
        size = fn().save(name)
        print(f"{name:16} {size / 1024:5.1f} KB")
