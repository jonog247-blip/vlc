#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_skin.py -- Validate and preview the "VLC Next" skins2 skin.

    python3 tools/test_skin.py             # validate + render previews
    python3 tools/test_skin.py --check     # validation only (exit 1 on error)

What it verifies
----------------
1.  theme.xml validates against VLC's own DTD (share/skins2/skin.dtd) -- the
    same grammar the skins2 parser enforces.
2.  Every bitmap reference resolves to a declared <Bitmap>/<SubBitmap>, and
    every referenced file exists inside the skin.
3.  Every action string is real.  The valid set is extracted from VLC's own
    interpreter.cpp (REGISTER_CMD) plus the "<id>.show()/hide()/setLayout()"
    family handled by Interpreter::parseAction, and the built-in image
    actions (move / resizeE / resizeS / resizeSE).
4.  Every variable used in value=, state= and visible= exists.  The list is
    extracted from vlcproc.cpp / interpreter.cpp at run time.
5.  Slider geometry: the sprite strip must be exactly divisible by nbhoriz /
    nbvert, and one frame must be exactly as wide as the Bezier curve --
    otherwise the fill would be misaligned (see ctrl_slider.cpp).
6.  Layout geometry: every control sits inside its layout, and two controls
    that both take the mouse may not overlap.
7.  Renders a PNG preview of every layout, compositing the real bitmaps and
    the real fonts, so the result can be eyeballed without running VLC.
"""

import os
import re
import sys
import xml.etree.ElementTree as ET

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SKIN = os.path.dirname(HERE)
REPO = os.path.normpath(os.path.join(SKIN, "..", "..", ".."))
SKINS2 = os.path.join(REPO, "modules", "gui", "skins2")
DTD = os.path.join(REPO, "share", "skins2", "skin.dtd")
THEME = os.path.join(SKIN, "theme.xml")
PREVIEW_DIR = os.path.join(HERE, "preview")


# ---------------------------------------------------------------------------
# Engine facts, extracted from the VLC source tree (no hard-coded lists)
# ---------------------------------------------------------------------------

def engine_actions():
    """Action names registered in skins2's command interpreter."""
    src = open(os.path.join(SKINS2, "parser", "interpreter.cpp")).read()
    actions = set(re.findall(r'REGISTER_CMD1?\(\s*"([^"]+)"', src))
    return actions


def engine_variables():
    """Variable names registered by VlcProc / Interpreter."""
    names = set()
    vlcproc = open(os.path.join(SKINS2, "src", "vlcproc.cpp")).read()
    names |= set(re.findall(r'REGISTER_VAR\(\s*[^,]+,\s*[^,]+,\s*"([^"]+)"',
                            vlcproc))
    names |= set(re.findall(r'registerVar\(\s*[^,]+,\s*"([^"]+)"', vlcproc))
    interp = open(os.path.join(SKINS2, "parser", "interpreter.cpp")).read()
    names |= set(re.findall(r'registerVar\(\s*[^,]+,\s*"([^"]+)"', interp))
    names |= {"true", "false"}
    return names


BUILTIN_ACTIONS = {"none", "move", "resizeE", "resizeS", "resizeSE",
                   "resizeW", "resizeN", "resizeNE", "resizeNW", "resizeSW"}
MACROS = set("HTtLlDdVNFBSR")


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------

class Node(object):
    """An element together with its resolved rectangle."""

    def __init__(self, tag, attrs, rect, parent=None):
        self.tag = tag
        self.attrs = attrs
        self.rect = rect            # (x, y, w, h) absolute in the layout
        self.parent = parent
        self.children = []
        self.local = None           # rect relative to the parent control

    @property
    def id(self):
        return self.attrs.get("id", "")

    def __repr__(self):
        return "<%s %s %s>" % (self.tag, self.id, self.rect)


def parse_points(text):
    """points="(0,3),(733,3)" -> list of (x, y)."""
    pts = []
    for m in re.finditer(r"\(([^)]*)\)", text or ""):
        parts = m.group(1).split(",")
        if len(parts) == 2:
            pts.append((int(parts[0]), int(parts[1])))
    return pts


class Theme(object):
    def __init__(self, path):
        tree = ET.parse(path)
        self.root = tree.getroot()
        self.bitmaps = {}        # id -> (file, x, y, w, h)
        self.fonts = {}          # id -> (file, size)
        self.windows = []        # (id, attrs, [layouts])
        self.popups = {}
        self._scan()

    def _scan(self):
        for bmp in self.root.findall("Bitmap"):
            a = bmp.attrib
            for sub in bmp.findall("SubBitmap"):
                s = sub.attrib
                self.bitmaps[s["id"]] = (a["file"], int(s["x"]), int(s["y"]),
                                         int(s["width"]), int(s["height"]))
            else:
                if "file" in a and not bmp.findall("SubBitmap"):
                    self.bitmaps[a["id"]] = (a["file"], 0, 0, None, None)
        for f in self.root.findall("Font"):
            a = f.attrib
            self.fonts[a["id"]] = (a["file"], int(a.get("size", 12)))
        for p in self.root.findall("PopupMenu"):
            self.popups[p.attrib["id"]] = [c.attrib for c in p]
        for w in self.root.findall("Window"):
            layouts = []
            for l in w.findall("Layout"):
                layouts.append(self._layout(l))
            self.windows.append((w.attrib["id"], w.attrib, layouts))

    def _layout(self, layout_el):
        a = layout_el.attrib
        W, H = int(a["width"]), int(a["height"])
        root = Node("Layout", a, (0, 0, W, H))
        self._walk(layout_el, root, (0, 0, W, H))
        return root

    def _walk(self, el, parent, box):
        bx, by, bw, bh = box
        for child in el:
            if child.tag in ("SliderBackground", "MenuItem", "MenuSeparator"):
                continue
            a = child.attrib
            x = int(a.get("x", 0))
            y = int(a.get("y", 0))
            w = int(a.get("width", -1))
            h = int(a.get("height", -1))
            # At natural size skins2 resolves left/top to x/y for every
            # anchoring mode (see Builder::makePosition + Position::getLeft).
            # A width/height of 0 means "stretch to the parent's far edge".
            if child.tag == "Image" and (w <= 0 or h <= 0):
                bw_, bh_ = self.bitmap_size(a.get("image"))
                if w <= 0:
                    w = bw_ if w == -1 else (bw - x)
                if h <= 0:
                    h = bh_ if h == -1 else (bh - y)
            elif child.tag in ("Button", "Checkbox"):
                key = "up" if child.tag == "Button" else "up1"
                w, h = self.bitmap_size(a.get(key))
            elif child.tag == "Slider":
                pts = parse_points(a.get("points"))
                w = max(p[0] for p in pts) + 1 if pts else 0
                h = max(p[1] for p in pts) + 1 if pts else 0
            elif child.tag == "Text":
                if w <= 0:
                    w = bw - x
                h = self.fonts.get(a.get("font"), ("", 12))[1] + 4
            elif child.tag == "Video":
                w = w if w > 0 else bw
                h = h if h > 0 else bh
            else:
                if w <= 0:
                    w = bw - x
                if h <= 0:
                    h = bh - y

            node = Node(child.tag, a, (bx + x, by + y, w, h), parent)
            node.local = (x, y, w, h)
            parent.children.append(node)
            if child.tag in ("Panel", "Group"):
                self._walk(child, node, (node.rect[0], node.rect[1], w, h))

    def bitmap_size(self, ident):
        info = self.bitmaps.get(ident)
        if not info:
            return (0, 0)
        f, sx, sy, w, h = info
        if w is not None:
            return (w, h)
        path = os.path.join(SKIN, f)
        if not os.path.exists(path):
            return (0, 0)
        with Image.open(path) as im:
            return im.size

    def all_nodes(self):
        out = []
        for _, _, layouts in self.windows:
            for l in layouts:
                stack = [l]
                while stack:
                    n = stack.pop()
                    out.append((l, n))
                    stack.extend(n.children)
        return out


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

class Report(object):
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.info = []

    def error(self, msg):
        self.errors.append(msg)

    def warn(self, msg):
        self.warnings.append(msg)

    def note(self, msg):
        self.info.append(msg)


CLICKABLE = ("Button", "Checkbox", "Slider", "Playlist", "Playtree")


def dtd_validate(report):
    from lxml import etree
    if not os.path.exists(DTD):
        report.warn("skin.dtd not found at %s -- skipped DTD validation" % DTD)
        return
    dtd = etree.DTD(DTD)
    doc = etree.parse(THEME)
    if dtd.validate(doc):
        report.note("DTD validation against share/skins2/skin.dtd: OK")
    else:
        for e in dtd.error_log:
            report.error("DTD: %s" % e.message)


def check_bitmaps(theme, report):
    refs = []
    for layout, node in theme.all_nodes():
        a = node.attrs
        for key in ("image", "up", "down", "over", "up1", "down1", "over1",
                    "up2", "down2", "over2", "bgimage"):
            if a.get(key) and a[key] != "none":
                refs.append((node, key, a[key]))
        # SliderBackground images live as children in the XML tree
    for el in theme.root.iter("SliderBackground"):
        refs.append((None, "image", el.attrib.get("image")))

    missing = 0
    for node, key, ident in refs:
        if ident not in theme.bitmaps:
            where = node.id if node else "SliderBackground"
            report.error("undeclared bitmap %r (%s of %s)" % (ident, key,
                                                              where))
            missing += 1
    files = set()
    for ident, (f, _, _, _, _) in theme.bitmaps.items():
        path = os.path.join(SKIN, f)
        if not os.path.exists(path):
            report.error("bitmap %s: missing file %s" % (ident, f))
        files.add(f)
    report.note("bitmaps: %d ids, %d files, %d references"
                % (len(theme.bitmaps), len(files), len(refs)))


def check_actions(theme, report):
    valid = engine_actions() | BUILTIN_ACTIONS
    windows = {w[0] for w in theme.windows}
    layouts = set()
    for _, _, ls in theme.windows:
        for l in ls:
            layouts.add(l.attrs["id"])
    popups = set(theme.popups)
    bad = 0
    count = 0
    for el in theme.root.iter():
        for key in ("action", "action1", "action2", "action"):
            val = el.attrib.get(key)
            if not val or val == "none":
                continue
            count += 1
            for one in val.split(";"):
                one = one.strip()
                ok = one in valid
                m = re.match(r"^([A-Za-z0-9_]+)\.(show|hide|maximize|unmaximize)"
                             r"\(\)$", one)
                if m and (m.group(1) in windows or m.group(1) in popups):
                    ok = True
                m = re.match(r"^([A-Za-z0-9_]+)\.setLayout\(([A-Za-z0-9_]+)\)$",
                             one)
                if m and m.group(1) in windows and m.group(2) in layouts:
                    ok = True
                if not ok:
                    report.error("unknown action %r (%s of %s)"
                                 % (one, key, el.attrib.get("id", el.tag)))
                    bad += 1
    report.note("actions: %d checked, %d registered commands in interpreter.cpp"
                % (count, len(engine_actions())))


def check_variables(theme, report):
    vars_ = engine_variables()

    def known(token):
        token = token[:-2] if token.endswith("()") else token
        if token in vars_:
            return True
        if re.match(r"^equalizer\.band\(\d+\)$", token):
            return True
        if token.endswith(".isActive") or token.endswith(".isVisible") \
                or token.endswith(".isMaximized"):
            base = token.rsplit(".", 1)[0]
            for _, _, ls in theme.windows:
                for l in ls:
                    if l.attrs["id"] == base:
                        return True
            for w in theme.windows:
                if w[0] == base:
                    return True
        return False

    count = 0
    for el in theme.root.iter():
        a = el.attrib
        for key in ("visible", "state"):
            expr = a.get(key)
            if not expr or expr in ("true", "false"):
                continue
            for token in re.findall(r"[A-Za-z_][A-Za-z0-9_.]*(?:\(\d*\))?",
                                    expr):
                token = token.rstrip()
                if token in ("not", "and", "or"):
                    continue
                count += 1
                if not known(token):
                    report.error("unknown variable %r in %s=\"%s\" (%s)"
                                 % (token, key, expr,
                                    a.get("id", el.tag)))
        if el.tag == "Slider" and a.get("value"):
            count += 1
            if not known(a["value"]):
                report.error("unknown slider value %r (%s)"
                             % (a["value"], a.get("id")))
    report.note("variables: %d references, %d known"
                % (count, len(vars_)))


def check_slider_geometry(theme, report):
    """The strip must tile exactly and one frame must match the curve."""
    for el in theme.root.iter("Slider"):
        bg = el.find("SliderBackground")
        if bg is None:
            continue
        a = el.attrib
        ident = bg.attrib["image"]
        nbh = int(bg.attrib.get("nbhoriz", 1))
        nbv = int(bg.attrib.get("nbvert", 1))
        padh = int(bg.attrib.get("padhoriz", 0))
        padv = int(bg.attrib.get("padvert", 0))
        W, H = theme.bitmap_size(ident)
        if W == 0:
            continue
        if (W + padh) % nbh or (H + padv) % nbv:
            report.error("slider %s: strip %dx%d does not divide into "
                         "%dx%d frames" % (a["id"], W, H, nbh, nbv))
            continue
        fw = (W + padh) // nbh - padh
        fh = (H + padv) // nbv - padv
        pts = parse_points(a.get("points"))
        cw = max(p[0] for p in pts) + 1
        if fw != cw:
            report.error("slider %s: frame width %d != curve width %d "
                         "(the fill would not line up)" % (a["id"], fw, cw))
        report.note("slider %-12s %2dx%-2d frames of %dx%d, curve %dx%d"
                    % (a["id"], nbh, nbv, fw, fh, cw,
                       max(p[1] for p in pts) + 1))


def check_geometry(theme, report):
    for wid, wattr, layouts in theme.windows:
        for l in layouts:
            LW, LH = int(l.attrs["width"]), int(l.attrs["height"])
            nodes = []
            stack = list(l.children)
            while stack:
                n = stack.pop()
                nodes.append(n)
                stack.extend(n.children)
            for n in nodes:
                x, y, w, h = n.rect
                if x < 0 or y < 0 or x + w > LW + 1 or y + h > LH + 1:
                    report.error("layout %s: %s %s sticks out of "
                                 "%dx%d (rect %s)"
                                 % (l.attrs["id"], n.tag, n.id, LW, LH,
                                    n.rect))
            # mouse targets must not overlap.  For a Slider only the curve
            # (grown by its cursor bitmap) is clickable, not the whole rect.
            click = [n for n in nodes if n.tag in CLICKABLE and
                     n.attrs.get("visible") in (None, "true")]
            for i in range(len(click)):
                for j in range(i + 1, len(click)):
                    a, b = click[i], click[j]
                    ra = hit_rect(theme, a)
                    rb = hit_rect(theme, b)
                    if overlaps(ra, rb):
                        report.error("layout %s: %s %s overlaps %s %s "
                                     "(%s vs %s)" % (l.attrs["id"], a.tag,
                                                     a.id, b.tag, b.id,
                                                     ra, rb))


def walk(node):
    yield node
    for c in node.children:
        for x in walk(c):
            yield x


def hit_rect(theme, node):
    """The area of a control that actually takes the mouse."""
    if node.tag != "Slider":
        return node.rect
    pts = parse_points(node.attrs.get("points"))
    if not pts:
        return node.rect
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    kw, kh = theme.bitmap_size(node.attrs.get("up"))
    x, y, _, _ = node.rect
    return (x + min(xs) - kw // 2, y + min(ys) - kh // 2,
            (max(xs) - min(xs)) + kw, (max(ys) - min(ys)) + kh)


def overlaps(r1, r2, slack=0):
    x1, y1, w1, h1 = r1
    x2, y2, w2, h2 = r2
    return not (x1 + w1 <= x2 + slack or x2 + w2 <= x1 + slack or
                y1 + h1 <= y2 + slack or y2 + h2 <= y1 + slack)


def check_ids(theme, report):
    seen = {}
    for layout, node in theme.all_nodes():
        ident = node.id
        if not ident or ident == "none":
            continue
        key = (layout.attrs["id"], ident)
        if key in seen:
            report.error("duplicate id %r in layout %s"
                         % (ident, layout.attrs["id"]))
        seen[key] = node
    for ident in theme.bitmaps:
        if ident in seen:
            report.error("bitmap id %r collides with a control id" % ident)


def check_artwork(theme, report):
    """Every icon must actually have ink on it (catches blank/broken cells)."""
    cache = {}
    for ident, (f, x, y, w, h) in sorted(theme.bitmaps.items()):
        if f not in cache:
            path = os.path.join(SKIN, f)
            if not os.path.exists(path):
                continue
            cache[f] = Image.open(path).convert("RGBA")
        img = cache[f]
        if w is None:
            crop = img
        else:
            crop = img.crop((x, y, x + w, y + h))
        px = crop.tobytes()
        n = len(px) // 4
        opaque = sum(1 for i in range(3, len(px), 4) if px[i] > 30)
        ink = opaque / float(n) if n else 0.0
        if ident == "blank":
            continue                       # deliberately empty
        if ink < 0.02:
            report.error("artwork %s is empty (%.2f%% ink)" % (ident,
                                                               100 * ink))
        elif ink > 0.995 and ident.startswith(("icons.", "btn.")) \
                and not ident.endswith((".down", ".over")):
            report.error("artwork %s is a solid block (%.1f%% ink)"
                         % (ident, 100 * ink))
    report.note("artwork: %d bitmaps have ink" % (len(theme.bitmaps) - 1))


def check_macros(theme, report):
    for el in theme.root.iter("Text"):
        text = el.attrib.get("text", "")
        for m in re.findall(r"\$([A-Za-z])", text):
            if m not in MACROS:
                report.error("text %s: unknown macro $%s"
                             % (el.attrib.get("id"), m))
    for el in theme.root.iter():
        tt = el.attrib.get("tooltiptext", "")
        for m in re.findall(r"\$([A-Za-z])", tt):
            if m not in MACROS:
                report.error("tooltip of %s: unknown macro $%s"
                             % (el.attrib.get("id"), m))


# ---------------------------------------------------------------------------
# Preview renderer
# ---------------------------------------------------------------------------

SAMPLE = {"N": "The.Wand.S01E04.1080p.mkv", "T": "00:06:34",
          "D": "00:25:40", "V": "85", "B": "2768", "S": "48000",
          "R": "1.00", "F": "file:///home/vlc/The.Wand.S01E04.mkv",
          "L": "-00:19:06", "l": "-19:06", "H": "", "t": "6:34", "d": "25:40"}

STATE = {"vlc.hasVout": True, "vlc.isPlaying": True, "vlc.isStopped": False,
         "vlc.isPaused": False, "vlc.isMute": False, "vlc.isFullscreen": False,
         "vlc.hasAudio": True, "dvd.isActive": False,
         "equalizer.isEnabled": True, "vlc.isOnTop": False,
         "vlc.canRecord": True, "vlc.isRecording": False}


def visible(expr, layout_id):
    if expr is None or expr == "true":
        return True
    if expr.endswith(".isActive"):
        return expr.rsplit(".", 1)[0] == layout_id
    if expr.startswith("not "):
        return not visible(expr[4:], layout_id)
    return STATE.get(expr, True)


def load_bitmap(theme, ident):
    info = theme.bitmaps.get(ident)
    if not info:
        return None
    f, x, y, w, h = info
    path = os.path.join(SKIN, f)
    if not os.path.exists(path):
        return None
    im = Image.open(path).convert("RGBA")
    if w is not None:
        im = im.crop((x, y, x + w, y + h))
    return im


def frame_of(img, index, nbh):
    w = img.width // nbh
    return img.crop((index * w, 0, index * w + w, img.height))


def font_for(theme, ident):
    info = theme.fonts.get(ident)
    if not info:
        return ImageFont.load_default()
    path = os.path.join(SKIN, info[0])
    if not os.path.exists(path):
        return ImageFont.load_default()
    return ImageFont.truetype(path, info[1])


def render_layout(theme, wid, layout):
    W = int(layout.attrs["width"])
    H = int(layout.attrs["height"])
    img = Image.new("RGB", (W, H), (0x12, 0x12, 0x12))
    d = ImageDraw.Draw(img)
    lid = layout.attrs["id"]

    def draw_node(node, ox, oy):
        a = node.attrs
        x, y, w, h = node.rect
        x -= ox
        y -= oy
        if not visible(a.get("visible"), lid):
            return
        if node.tag == "Image":
            bmp = load_bitmap(theme, a.get("image"))
            if bmp is None:
                return
            if a.get("resize") == "scale" and (bmp.width != w or
                                               bmp.height != h):
                bmp = bmp.resize((max(1, w), max(1, h)), Image.LANCZOS)
            img.paste(bmp, (x, y), bmp)
        elif node.tag == "Button":
            bmp = load_bitmap(theme, a.get("up"))
            if bmp:
                img.paste(bmp, (x, y), bmp)
        elif node.tag == "Checkbox":
            state = a.get("state", "true")
            on = visible(state, lid)
            key = "up1" if on else "up2"
            bmp = load_bitmap(theme, a.get(key))
            if bmp:
                img.paste(bmp, (x, y), bmp)
        elif node.tag == "Text":
            text = a.get("text", "")
            text = re.sub(r"\$([A-Za-z])",
                          lambda m: SAMPLE.get(m.group(1), m.group(0)), text)
            fnt = font_for(theme, a.get("font", "defaultfont"))
            color = a.get("color", "#FFFFFF")
            tw = d.textlength(text, font=fnt)
            align = a.get("alignment", "left")
            if align == "center":
                tx = x + (w - tw) / 2
            elif align == "right":
                tx = x + w - tw
            else:
                tx = x
            d.text((tx, y), text, font=fnt, fill=color)
        elif node.tag == "Slider":
            bg = None
            for c in node.raw_children:
                if c.tag == "SliderBackground":
                    bg = c.attrib
            if bg:
                bmp = load_bitmap(theme, bg["image"])
                if bmp:
                    nbh = int(bg.get("nbhoriz", 1))
                    idx = int(round(0.42 * (nbh - 1)))
                    frame = frame_of(bmp, idx, nbh)
                    frame = frame.resize((w, frame.height), Image.LANCZOS)
                    img.paste(frame, (x, y), frame)
            cur = load_bitmap(theme, a.get("up"))
            if cur:
                pts = parse_points(a.get("points"))
                if pts:
                    (x0, y0), (x1, y1) = pts[0], pts[-1]
                    px = x + x0 + (x1 - x0) * 0.42
                    py = y + y0 + (y1 - y0) * 0.42
                    img.paste(cur, (int(px - cur.width / 2),
                                    int(py - cur.height / 2)), cur)
        elif node.tag == "Video":
            for i in range(h):
                v = 0x1A + int(0x10 * (1 - i / float(max(1, h))))
                d.line([(x, y + i), (x + w, y + i)],
                       fill=(v, v, v))
            label = "VIDEO"
            d.text((x + w / 2 - 18, y + h / 2 - 6), label,
                   fill=(0x55, 0x55, 0x55))
        elif node.tag == "Playlist":
            d.rectangle([x, y, x + w, y + h], fill=(0x1A, 0x1A, 0x1A))
            fnt = font_for(theme, a.get("font", "defaultfont"))
            for i, name in enumerate(["The.Wand.S01E03.mkv",
                                      "The.Wand.S01E04.mkv",
                                      "The.Wand.S01E05.mkv"]):
                ry = y + 6 + i * 22
                col = (0xE0, 0x7A, 0x1E) if i == 1 else (0xFF, 0xFF, 0xFF)
                if i == 1:
                    d.rectangle([x, ry - 3, x + w, ry + 17],
                                fill=(0x2F, 0x2F, 0x2F))
                d.text((x + 8, ry), "%d. %s" % (i + 1, name), font=fnt,
                       fill=col)
        for c in node.children:
            draw_node(c, ox, oy)

    for c in layout.children:
        draw_node(c, 0, 0)
    return img


def contact_sheet(theme):
    """One labelled image showing every layout, for review."""
    tiles = []
    for wid, wattr, layouts in theme.windows:
        for l in layouts:
            img = render_layout(theme, wid, l)
            tiles.append(("%s / %s" % (wid, l.attrs["id"]), img))
    pad = 24
    label_h = 26
    scale = 0.62
    tw = int(max(t[1].width for t in tiles) * scale)
    total_h = sum(int(t[1].height * scale) + label_h + pad for t in tiles)
    sheet = Image.new("RGB", (tw + pad * 2, total_h + pad),
                      (0x08, 0x08, 0x08))
    d = ImageDraw.Draw(sheet)
    fnt = None
    for f in ("FreeSansBold.ttf", "FreeSans.ttf"):
        p = os.path.join(SKIN, "vlcnext", f)
        if os.path.exists(p):
            fnt = ImageFont.truetype(p, 15)
            break
    if fnt is None:
        fnt = ImageFont.load_default()
    y = pad
    for title, img in tiles:
        d.text((pad, y), title, font=fnt, fill=(0xE0, 0x7A, 0x1E))
        y += label_h
        small = img.resize((int(img.width * scale), int(img.height * scale)),
                           Image.LANCZOS)
        sheet.paste(small, (pad, y))
        d.rectangle([pad - 1, y - 1, pad + small.width, y + small.height],
                    outline=(0x33, 0x33, 0x33))
        y += small.height + pad
    path = os.path.join(PREVIEW_DIR, "contact_sheet.png")
    sheet.save(path)
    return path


def render_all(theme):
    if not os.path.isdir(PREVIEW_DIR):
        os.makedirs(PREVIEW_DIR)
    out = []
    for wid, wattr, layouts in theme.windows:
        for l in layouts:
            img = render_layout(theme, wid, l)
            path = os.path.join(PREVIEW_DIR, "%s_%s.png"
                                % (wid, l.attrs["id"]))
            img.save(path)
            out.append(path)
    return out


# ---------------------------------------------------------------------------
# Pixel checks on the rendered previews
#
# These assert that the artwork really lands where the layout says it should:
# the accent pill is orange and sits at the left of the control bar, the seek
# bar fill is orange up to the playhead and surface grey after it, the cone
# volume is green below 100%, and so on.  This is what catches "valid XML that
# looks wrong".
# ---------------------------------------------------------------------------

def near(px, colour, tol=10):
    return all(abs(px[i] - colour[i]) <= tol for i in range(3))


def region_has(img, box, colour, tol=12):
    x0, y0, x1, y1 = box
    crop = img.crop((max(0, x0), max(0, y0), min(img.width, x1),
                     min(img.height, y1)))
    for px in (crop.get_flattened_data() if hasattr(crop, "get_flattened_data") else crop.getdata()):
        if near(px, colour, tol):
            return True
    return False


def pixel_is(img, x, y, colour, tol=12):
    return near(img.getpixel((x, y))[:3], colour, tol)


def check_render(theme, report):
    import design as D
    normal = Image.open(os.path.join(PREVIEW_DIR, "main_normal.png"))
    W, H = D.MAIN_W, D.MAIN_H
    bar_y = H - D.BAR_H

    checks = [
        ("top bar uses the secondary surface",
         pixel_is(normal, 550, 12, D.BG_SECONDARY)),
        ("canvas uses the base surface",
         pixel_is(normal, 5, H - 30, D.BG_PRIMARY)),
        ("top bar is separated by a 1px border",
         pixel_is(normal, 550, D.TOPBAR_H - 1, D.BORDER)),
        ("play pill is accent orange",
         region_has(normal, (D.PLAY_X, bar_y + D.ROW1_CY - 12,
                             D.PLAY_X + D.PLAY_W, bar_y + D.ROW1_CY + 12),
                    D.ACCENT)),
        ("seek bar fill is accent orange before the playhead",
         pixel_is(normal, D.SEEK_X + 120, bar_y + D.ROW1_CY, D.ACCENT)),
        ("seek bar is unfilled after the playhead",
         pixel_is(normal, D.SEEK_X + 600, bar_y + D.ROW1_CY, D.BG_SURFACE)),
        ("seek bar shows a handle",
         region_has(normal, (D.SEEK_X + 260, bar_y + D.ROW1_CY - 7,
                             D.SEEK_X + 340, bar_y + D.ROW1_CY + 7),
                    D.TEXT_PRIMARY)),
        ("cone volume is green under 100%",
         region_has(normal, (W - D.VOL_SLIDER_D, bar_y + D.ROW2_CY - 8,
                             W - D.VOL_SLIDER_D + 60,
                             bar_y + D.ROW2_CY + 8), D.VOL_GREEN)),
        ("cone volume is unfilled (surface grey) past the level",
         pixel_is(normal, W - D.VOL_SLIDER_D + 110, bar_y + D.ROW2_CY,
                  D.BG_SURFACE)),
        ("window controls sit in the top right",
         region_has(normal, (W - 60, 0, W - 20, D.TOPBAR_H), D.ICON)),
    ]
    for name, ok in checks:
        if not ok:
            report.error("render: %s" % name)

    # the drawer layouts must actually draw the drawer on the right
    for name, kind in (("main_sidebar_queue.png", "queue"),
                       ("main_sidebar_audio.png", "audio")):
        img = Image.open(os.path.join(PREVIEW_DIR, name))
        if not pixel_is(img, D.MAIN_W + 160, D.TOPBAR_H + 200,
                        D.BG_SECONDARY):
            report.error("render: %s has no drawer surface at x=%d"
                         % (name, D.MAIN_W + 160))
        if not pixel_is(img, D.MAIN_W, D.TOPBAR_H + 200, D.BORDER):
            report.error("render: %s is missing the drawer border" % name)
    report.note("render: %d pixel assertions on %d layouts"
                % (len(checks) + 4, 3))


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main():
    report = Report()
    theme = Theme(THEME)

    # keep the raw children of Slider elements for the renderer
    for el in theme.root.iter("Slider"):
        pass
    raw = {}
    for widx, (wid, wattr, layouts) in enumerate(theme.windows):
        w_el = [w for w in theme.root.findall("Window")
                if w.attrib["id"] == wid][0]
        for lidx, l in enumerate(layouts):
            l_el = w_el.findall("Layout")[lidx]
            stack = [(l_el, l)]
            while stack:
                src, node = stack.pop()
                node.raw_children = list(src)
                for s, n in zip([c for c in src if c.tag != "SliderBackground"],
                                node.children):
                    stack.append((s, n))

    dtd_validate(report)
    check_bitmaps(theme, report)
    check_actions(theme, report)
    check_variables(theme, report)
    check_slider_geometry(theme, report)
    check_artwork(theme, report)
    check_ids(theme, report)
    check_macros(theme, report)
    check_geometry(theme, report)

    if "--check" not in sys.argv:
        for p in render_all(theme):
            report.note("preview: %s" % os.path.relpath(p, SKIN))
        report.note("contact sheet: %s"
                    % os.path.relpath(contact_sheet(theme), SKIN))
        check_render(theme, report)

    if "--dump" in sys.argv:
        print("\n%-22s %-6s %-24s %s" % ("layout", "kind", "id", "rect"))
        for wid, wattr, layouts in theme.windows:
            for l in layouts:
                for _, n in [(0, c) for c in walk(l)]:
                    print("%-22s %-6s %-24s %s"
                          % (l.attrs["id"], n.tag, n.id, n.rect))

    for line in report.info:
        print("  .  %s" % line)
    for line in report.warnings:
        print("  !  %s" % line)
    for line in report.errors:
        print("  X  %s" % line)
    print("\n%d error(s), %d warning(s)" % (len(report.errors),
                                            len(report.warnings)))
    return 1 if report.errors else 0


if __name__ == "__main__":
    sys.exit(main())
