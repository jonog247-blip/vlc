#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
art.py -- Vector artwork for the "VLC Next" skins2 skin.

Everything is drawn programmatically with Pillow so the skin stays editable
(no binary blobs checked in without a recipe).  Icons are rasterised at
SUPERSAMPLE x and down-sampled with LANCZOS, which gives the smooth 1.5px
stroke outlines described in VLC_changes.md section 1.3.
"""

from PIL import Image, ImageDraw

from design import (
    ACCENT, ACCENT_HOVER, ACCENT_SOFT, BG_HOVER, BG_PRIMARY, BG_SECONDARY,
    BG_SURFACE, BORDER, ICON, ICON_MUTED, RADIUS_MEDIUM, RADIUS_SMALL,
    TEXT_PRIMARY, TEXT_SECOND, VOL_GREEN, VOL_RED, VOL_YELLOW,
)

SUPERSAMPLE = 4


# ---------------------------------------------------------------------------
# Canvas helpers
# ---------------------------------------------------------------------------

def canvas(w, h):
    """Transparent canvas, supersampled."""
    return Image.new("RGBA", (w * SUPERSAMPLE, h * SUPERSAMPLE), (0, 0, 0, 0))


def finish(img, w, h):
    """Down-sample a supersampled canvas to its real size."""
    return img.resize((w, h), Image.LANCZOS)


def S(v):
    """Scale a coordinate into supersample space."""
    return v * SUPERSAMPLE


def rrect(d, box, radius, fill=None, outline=None, width=1):
    """Rounded rectangle; box is (x0, y0, x1, y1) in real (unscaled) pixels."""
    x0, y0, x1, y1 = [S(v) for v in box]
    r = S(radius)
    if fill is not None:
        d.rounded_rectangle([x0, y0, x1, y1], radius=r, fill=fill)
    if outline is not None:
        d.rounded_rectangle([x0, y0, x1, y1], radius=r, outline=outline,
                            width=max(1, int(S(width))))


def line(d, pts, color, width=1.5):
    d.line([(S(x), S(y)) for x, y in pts], fill=color,
           width=max(1, int(round(S(width)))), joint="curve")


def poly(d, pts, color):
    d.polygon([(S(x), S(y)) for x, y in pts], fill=color)


def ellipse(d, box, fill=None, outline=None, width=1):
    x0, y0, x1, y1 = [S(v) for v in box]
    if fill is not None:
        d.ellipse([x0, y0, x1, y1], fill=fill)
    if outline is not None:
        d.ellipse([x0, y0, x1, y1], outline=outline,
                  width=max(1, int(round(S(width)))))


def arc(d, box, start, end, color, width=1.5):
    x0, y0, x1, y1 = [S(v) for v in box]
    d.arc([x0, y0, x1, y1], start, end, fill=color,
          width=max(1, int(round(S(width)))))


# ---------------------------------------------------------------------------
# Icon glyphs
#
# Each glyph is drawn centred on (cx, cy) inside a box of `s` pixels.
# ---------------------------------------------------------------------------

def g_play(d, cx, cy, s, c):
    h = s * 0.42
    w = s * 0.36
    poly(d, [(cx - w * 0.55, cy - h), (cx - w * 0.55, cy + h),
             (cx + w * 0.95, cy)], c)


def g_pause(d, cx, cy, s, c):
    h = s * 0.40
    w = s * 0.13
    gap = s * 0.16
    rrect(d, (cx - gap - w, cy - h, cx - gap + w, cy + h), w * 0.5,
          fill=c)
    rrect(d, (cx + gap - w, cy - h, cx + gap + w, cy + h), w * 0.5,
          fill=c)


def _tri(d, cx, cy, s, c, direction):
    h = s * 0.34
    w = s * 0.26
    if direction > 0:
        poly(d, [(cx - w, cy - h), (cx - w, cy + h), (cx + w, cy)], c)
    else:
        poly(d, [(cx + w, cy - h), (cx + w, cy + h), (cx - w, cy)], c)


def g_prev(d, cx, cy, s, c):
    _tri(d, cx - s * 0.16, cy, s * 0.95, c, -1)
    _tri(d, cx + s * 0.20, cy, s * 0.95, c, -1)
    rrect(d, (cx - s * 0.44, cy - s * 0.34, cx - s * 0.36, cy + s * 0.34),
          s * 0.04, fill=c)


def g_next(d, cx, cy, s, c):
    _tri(d, cx - s * 0.20, cy, s * 0.95, c, 1)
    _tri(d, cx + s * 0.16, cy, s * 0.95, c, 1)
    rrect(d, (cx + s * 0.36, cy - s * 0.34, cx + s * 0.44, cy + s * 0.34),
          s * 0.04, fill=c)


def g_stop(d, cx, cy, s, c):
    r = s * 0.30
    rrect(d, (cx - r, cy - r, cx + r, cy + r), s * 0.06, fill=c)


def g_faster(d, cx, cy, s, c):
    _tri(d, cx - s * 0.12, cy, s * 0.9, c, 1)
    _tri(d, cx + s * 0.22, cy, s * 0.9, c, 1)


def g_slower(d, cx, cy, s, c):
    _tri(d, cx + s * 0.12, cy, s * 0.9, c, -1)
    _tri(d, cx - s * 0.22, cy, s * 0.9, c, -1)


def g_bubble(d, cx, cy, s, c):
    """Quick track switcher (section 3.1)."""
    w, h = s * 0.88, s * 0.62
    x0, y0 = cx - w / 2, cy - h / 2 - s * 0.06
    rrect(d, (x0, y0, x0 + w, y0 + h), s * 0.16, fill=c)
    poly(d, [(x0 + w * 0.22, y0 + h - 1), (x0 + w * 0.34, y0 + h - 1),
             (x0 + w * 0.22, y0 + h + s * 0.18)], c)
    dot = s * 0.07
    for i in (-1, 0, 1):
        ellipse(d, (cx + i * s * 0.22 - dot, cy - s * 0.10 - dot,
                    cx + i * s * 0.22 + dot, cy - s * 0.10 + dot),
                fill=BG_SECONDARY)


def g_gear(d, cx, cy, s, c):
    """Quick settings (section 2.3)."""
    r_out = s * 0.42
    r_in = s * 0.20
    ellipse(d, (cx - r_out, cy - r_out, cx + r_out, cy + r_out),
            outline=c, width=s * 0.11)
    for i in range(6):
        a = i * 60.0
        import math
        dx = math.cos(math.radians(a))
        dy = math.sin(math.radians(a))
        line(d, [(cx + dx * r_out * 0.92, cy + dy * r_out * 0.92),
                 (cx + dx * (r_out + s * 0.14), cy + dy * (r_out + s * 0.14))],
             c, width=s * 0.12)
    ellipse(d, (cx - r_in, cy - r_in, cx + r_in, cy + r_in),
            outline=c, width=s * 0.10)


def g_queue(d, cx, cy, s, c):
    """Queue / playlist drawer toggle (section 3.4)."""
    w = s * 0.78
    h = s * 0.10
    for i in (-1, 0, 1):
        y = cy + i * s * 0.28
        rrect(d, (cx - w / 2, y - h / 2, cx + w / 2, y + h / 2), h / 2, fill=c)
    # a small accent dot marks the "currently playing" row
    ellipse(d, (cx + w / 2 - s * 0.06, cy - s * 0.28 - s * 0.10,
                cx + w / 2 + s * 0.06, cy - s * 0.28 + s * 0.02),
            fill=ACCENT)


def g_fullscreen(d, cx, cy, s, c):
    r = s * 0.40
    k = s * 0.26
    w = s * 0.14
    for sx, sy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        px = cx + sx * r
        py = cy + sy * r
        line(d, [(px - sx * k, py), (px, py)], c, width=w * 0.9)
        line(d, [(px, py - sy * k), (px, py)], c, width=w * 0.9)


def g_expand(d, cx, cy, s, c):
    r = s * 0.36
    line(d, [(cx - r, cy + r * 0.2), (cx - r * 0.1, cy - r * 0.7),
             (cx + r, cy - r * 0.7)], c, width=s * 0.12)
    line(d, [(cx + r, cy - r * 0.2), (cx + r * 0.1, cy + r * 0.7),
             (cx - r, cy + r * 0.7)], c, width=s * 0.12)


def g_speaker(d, cx, cy, s, c, waves=2, crossed=False):
    """Volume: tapered speaker cone with two-tone waves (section 2.3)."""
    body_w = s * 0.20
    body_h = s * 0.30
    bx = cx - s * 0.24
    poly(d, [(bx, cy - body_h / 2), (bx + body_w, cy - s * 0.30),
             (bx + body_w, cy + s * 0.30), (bx, cy + body_h / 2)], c)
    rrect(d, (bx - s * 0.10, cy - s * 0.16, bx, cy + s * 0.16), s * 0.04,
          fill=c)
    for i in range(waves):
        rr = s * (0.22 + 0.17 * (i + 1))
        arc(d, (bx + body_w - s * 0.04 - rr, cy - rr,
                bx + body_w - s * 0.04 + rr, cy + rr),
            -55, 55, c, width=s * 0.10)
    if crossed:
        r = s * 0.16
        ex = cx + s * 0.42
        line(d, [(ex - r, cy - r), (ex + r, cy + r)], VOL_RED, width=s * 0.11)
        line(d, [(ex + r, cy - r), (ex - r, cy + r)], VOL_RED, width=s * 0.11)


def g_snapshot(d, cx, cy, s, c):
    w, h = s * 0.84, s * 0.60
    x0, y0 = cx - w / 2, cy - h / 2 + s * 0.06
    rrect(d, (x0, y0, x0 + w, y0 + h), s * 0.10, outline=c, width=s * 0.11)
    rrect(d, (cx - w * 0.14, y0 - s * 0.14, cx + w * 0.14, y0 + s * 0.02),
          s * 0.05, fill=c)
    ellipse(d, (cx - s * 0.16, cy - s * 0.06, cx + s * 0.16, cy + s * 0.26),
            outline=c, width=s * 0.11)


def g_record(d, cx, cy, s, c, active=False):
    r = s * 0.34
    ellipse(d, (cx - r, cy - r, cx + r, cy + r), outline=c, width=s * 0.12)
    r2 = s * 0.20
    ellipse(d, (cx - r2, cy - r2, cx + r2, cy + r2),
            fill=VOL_RED if active else c)


def g_ontop(d, cx, cy, s, c, active=False):
    """Always on top push-pin."""
    line(d, [(cx, cy - s * 0.40), (cx, cy + s * 0.34)], c, width=s * 0.11)
    poly(d, [(cx, cy - s * 0.42), (cx - s * 0.14, cy - s * 0.20),
             (cx + s * 0.14, cy - s * 0.20)], c)
    line(d, [(cx - s * 0.26, cy + s * 0.34), (cx + s * 0.26, cy + s * 0.34)],
         ACCENT if active else c, width=s * 0.12)


def g_pip(d, cx, cy, s, c):
    x0, y0 = cx - s * 0.42, cy - s * 0.32
    x1, y1 = cx + s * 0.42, cy + s * 0.32
    rrect(d, (x0, y0, x1, y1), s * 0.08, outline=c, width=s * 0.11)
    rrect(d, (x1 - s * 0.34, y1 - s * 0.26, x1 - s * 0.04, y1 - s * 0.04),
          s * 0.04, fill=c)


def g_playlist(d, cx, cy, s, c):
    w = s * 0.66
    x0 = cx - w / 2 + s * 0.14
    for i in (-1, 0, 1):
        y = cy + i * s * 0.28
        rrect(d, (x0, y - s * 0.05, x0 + w, y + s * 0.05), s * 0.05, fill=c)
    _tri(d, cx - w / 2 - s * 0.06, cy, s * 0.55, c, 1)


def g_close(d, cx, cy, s, c):
    r = s * 0.28
    line(d, [(cx - r, cy - r), (cx + r, cy + r)], c, width=s * 0.13)
    line(d, [(cx + r, cy - r), (cx - r, cy + r)], c, width=s * 0.13)


def g_menu(d, cx, cy, s, c):
    """The unified "..." menu trigger (section 2.2)."""
    r = s * 0.10
    for i in (-1, 0, 1):
        ellipse(d, (cx + i * s * 0.30 - r, cy - r, cx + i * s * 0.30 + r, cy + r),
                fill=c)


def g_folder(d, cx, cy, s, c):
    w, h = s * 0.80, s * 0.58
    x0, y0 = cx - w / 2, cy - h / 2 + s * 0.10
    rrect(d, (x0, y0 + s * 0.10, x0 + w * 0.42, y0 + s * 0.22), s * 0.05,
          fill=c)
    rrect(d, (x0, y0 + s * 0.14, x0 + w, y0 + h), s * 0.08, fill=c)


def g_win_min(d, cx, cy, s, c):
    line(d, [(cx - s * 0.26, cy + s * 0.26), (cx + s * 0.26, cy + s * 0.26)],
         c, width=s * 0.11)


def g_win_max(d, cx, cy, s, c):
    r = s * 0.28
    rrect(d, (cx - r, cy - r, cx + r, cy + r), s * 0.05, outline=c,
          width=s * 0.11)


def g_win_unmax(d, cx, cy, s, c):
    r = s * 0.26
    rrect(d, (cx - r - s * 0.10, cy - r + s * 0.10,
              cx + r - s * 0.10, cy + r + s * 0.10), s * 0.04, outline=c,
          width=s * 0.10)
    rrect(d, (cx - r + s * 0.10, cy - r - s * 0.10,
              cx + r + s * 0.10, cy + r - s * 0.10), s * 0.04, fill=BG_SECONDARY,
          outline=c, width=s * 0.10)


def g_win_close(d, cx, cy, s, c):
    r = s * 0.26
    line(d, [(cx - r, cy - r), (cx + r, cy + r)], c, width=s * 0.12)
    line(d, [(cx + r, cy - r), (cx - r, cy + r)], c, width=s * 0.12)


# ---------------------------------------------------------------------------
# The VLC traffic cone (section 2.2), drawn two-tone: muted stroke + accent
# ---------------------------------------------------------------------------

def draw_cone(size):
    img = canvas(size, size)
    d = ImageDraw.Draw(img)
    cx = size / 2.0
    apex_y = size * 0.10
    base_y = size * 0.80
    half = size * 0.26
    # cone body
    poly(d, [(cx, apex_y), (cx + half, base_y), (cx - half, base_y)], ACCENT)
    # decorative band (two-tone: muted stroke over accent fill)
    band_y0 = base_y - size * 0.20
    band_y1 = base_y - size * 0.10
    k0 = (band_y0 - apex_y) / (base_y - apex_y)
    k1 = (band_y1 - apex_y) / (base_y - apex_y)
    poly(d, [(cx + half * k0, band_y0), (cx + half * k1, band_y1),
             (cx - half * k1, band_y1), (cx - half * k0, band_y0)],
         ICON_MUTED)
    # road / base
    rrect(d, (cx - half - size * 0.06, base_y,
              cx + half + size * 0.06, base_y + size * 0.10),
          size * 0.05, fill=ICON)
    ellipse(d, (cx - half, base_y - size * 0.04, cx + half,
                base_y + size * 0.04), fill=ACCENT)
    return finish(img, size, size)


# ---------------------------------------------------------------------------
# Icon button cells
# ---------------------------------------------------------------------------

GLYPHS = {
    "bubble": g_bubble,
    "gear": g_gear,
    "queue": g_queue,
    "fullscreen": g_fullscreen,
    "stop": g_stop,
    "snapshot": g_snapshot,
    "faster": g_faster,
    "slower": g_slower,
    "pip": g_pip,
    "playlist": g_playlist,
    "expand": g_expand,
    "close": g_close,
    "menu": g_menu,
    "folder": g_folder,
    "win_min": g_win_min,
    "win_max": g_win_max,
    "win_unmax": g_win_unmax,
    "win_close": g_win_close,
}


def icon_cell(size, glyph, state, active=False):
    """One state of a square icon button.

    state: normal | hover | down
    active: the "on" state of a toggle (accent coloured glyph)
    """
    img = canvas(size, size)
    d = ImageDraw.Draw(img)
    cx = cy = size / 2.0

    # Surface (section 1.2: rounded rectangular pills, never circles)
    if state == "hover":
        rrect(d, (1, 1, size - 2, size - 2), RADIUS_SMALL, fill=BG_HOVER)
    elif state == "down":
        rrect(d, (1, 1, size - 2, size - 2), RADIUS_SMALL, fill=ACCENT_SOFT)

    if state == "down":
        color = ACCENT
    elif active:
        color = ACCENT
    elif state == "hover":
        color = TEXT_PRIMARY
    else:
        color = ICON

    s = size * 0.78          # glyph box
    if glyph == "speaker":
        g_speaker(d, cx, cy, s, color,
                  waves=0 if active else 2, crossed=active)
    elif glyph == "record":
        g_record(d, cx, cy, s, color, active=active)
    elif glyph == "ontop":
        g_ontop(d, cx, cy, s, color, active=active)
    else:
        GLYPHS[glyph](d, cx, cy, s, color)

    return finish(img, size, size)


def play_pill(w, h, state, paused=False):
    """The accent orange play/pause pill (section 2.3)."""
    img = canvas(w, h)
    d = ImageDraw.Draw(img)
    if state == "hover":
        fill = ACCENT_HOVER
    elif state == "down":
        fill = ACCENT_SOFT
    else:
        fill = ACCENT
    rrect(d, (0, 0, w - 1, h - 1), RADIUS_MEDIUM, fill=fill)
    if state == "down":
        rrect(d, (0, 0, w - 1, h - 1), RADIUS_MEDIUM, outline=ACCENT, width=1)
    cx, cy = w / 2.0, h / 2.0
    s = h * 0.86
    if paused:
        g_pause(d, cx, cy, s, TEXT_PRIMARY)
    else:
        g_play(d, cx, cy, s, TEXT_PRIMARY)
    return finish(img, w, h)


def transport_cell(size, glyph, state):
    """prev / next buttons."""
    img = canvas(size, size)
    d = ImageDraw.Draw(img)
    cx = cy = size / 2.0
    if state == "hover":
        rrect(d, (1, 1, size - 2, size - 2), RADIUS_SMALL, fill=BG_HOVER)
    elif state == "down":
        rrect(d, (1, 1, size - 2, size - 2), RADIUS_SMALL, fill=ACCENT_SOFT)
    color = ACCENT if state == "down" else (TEXT_PRIMARY if state == "hover"
                                            else ICON)
    (g_prev if glyph == "prev" else g_next)(d, cx, cy, size * 0.80, color)
    return finish(img, size, size)


# ---------------------------------------------------------------------------
# Chrome
# ---------------------------------------------------------------------------

def solid(w, h, color, radius=0, border=None):
    img = canvas(w, h)
    d = ImageDraw.Draw(img)
    rrect(d, (0, 0, w - 1, h - 1), radius, fill=color)
    if border:
        rrect(d, (0, 0, w - 1, h - 1), radius, outline=border, width=1)
    return finish(img, w, h)


def bar(w, h, color, edge=None, edge_side="bottom"):
    """A flat bar with an optional 1px divider on one side."""
    img = canvas(w, h)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S(w) - 1, S(h) - 1], fill=color)
    if edge:
        if edge_side == "bottom":
            d.rectangle([0, S(h - 1), S(w) - 1, S(h) - 1], fill=edge)
        elif edge_side == "top":
            d.rectangle([0, 0, S(w) - 1, 1], fill=edge)
        elif edge_side == "left":
            d.rectangle([0, 0, 1, S(h) - 1], fill=edge)
    return finish(img, w, h)


def tab_bg(w, h, state):
    """Drawer tab: plain / hover / active (accent underline)."""
    img = canvas(w, h)
    d = ImageDraw.Draw(img)
    if state == "hover":
        rrect(d, (0, 0, w - 1, h - 1), RADIUS_SMALL, fill=BG_HOVER)
    elif state == "active":
        rrect(d, (0, 0, w - 1, h - 1), RADIUS_SMALL, fill=BG_HOVER)
        rrect(d, (w * 0.25, h - 4, w * 0.75, h - 2), 1, fill=ACCENT)
    return finish(img, w, h)


# ---------------------------------------------------------------------------
# Seek bar (section 2.4) -- sprite strip, one frame per progress step
# ---------------------------------------------------------------------------

def seek_strip(width, height, frames):
    """Horizontal sprite strip: the filled progress bar at N positions."""
    img = canvas(width * frames, height)
    d = ImageDraw.Draw(img)
    for i in range(frames):
        x0 = i * width
        t = i / float(frames - 1)
        # track
        rrect(d, (x0, 0, x0 + width - 1, height - 1), height / 2.0,
              fill=BG_SURFACE)
        # progress
        fill_w = max(height, int(round(width * t)))
        if fill_w > 0:
            rrect(d, (x0, 0, x0 + fill_w - 1, height - 1), height / 2.0,
                  fill=ACCENT)
    return finish(img, width * frames, height)


def seek_cursor(size, state):
    """The scrub handle: a small accent dot with a halo on hover."""
    img = canvas(size, size)
    d = ImageDraw.Draw(img)
    r = size / 2.0
    if state == "hover":
        ellipse(d, (0, 0, size - 1, size - 1), fill=ACCENT_HOVER)
    elif state == "down":
        ellipse(d, (0, 0, size - 1, size - 1), fill=TEXT_PRIMARY)
    else:
        ellipse(d, (1, 1, size - 2, size - 2), fill=ACCENT)
        ellipse(d, (r - r * 0.35, r - r * 0.35, r + r * 0.35, r + r * 0.35),
                fill=TEXT_PRIMARY)
    return finish(img, size, size)


# ---------------------------------------------------------------------------
# Cone / wedge volume slider (section 2.3)
#
# A tapered geometric cone: narrow at the left, opening to the right.  The
# fill level drives the colour: green (0-100%), yellow (100-150%),
# red (150-200%) -- the skins2 volume variable maps [0,1] to [0,200]%.
# ---------------------------------------------------------------------------

def volume_strip(width, height, frames):
    img = canvas(width * frames, height)
    d = ImageDraw.Draw(img)
    for i in range(frames):
        x0 = i * width
        t = i / float(frames - 1)          # 0 .. 1  (1 == 200%)
        if t <= 0.5:
            color = VOL_GREEN
        elif t <= 0.75:
            color = VOL_YELLOW
        else:
            color = VOL_RED
        # wedge: 4px tall at the left, full height at the right
        h0 = height * 0.28
        h1 = height
        cy = height / 2.0
        # outline (unfilled wedge)
        poly(d, [(x0, cy - h0 / 2), (x0 + width - 1, cy - h1 / 2),
                 (x0 + width - 1, cy + h1 / 2), (x0, cy + h0 / 2)], BG_SURFACE)
        # fill
        fw = int(round((width - 1) * t))
        if fw > 0:
            fh0 = h0
            fh1 = h0 + (h1 - h0) * t
            poly(d, [(x0, cy - fh0 / 2), (x0 + fw, cy - fh1 / 2),
                     (x0 + fw, cy + fh1 / 2), (x0, cy + fh0 / 2)], color)
    return finish(img, width * frames, height)


def volume_cursor(w, h, state):
    img = canvas(w, h)
    d = ImageDraw.Draw(img)
    color = ACCENT_HOVER if state == "hover" else (
        TEXT_PRIMARY if state == "down" else ICON)
    rrect(d, (w * 0.30, 0, w * 0.70, h - 1), w * 0.2, fill=color)
    return finish(img, w, h)


def eq_knob(w, h, state):
    img = canvas(w, h)
    d = ImageDraw.Draw(img)
    color = ACCENT_HOVER if state == "hover" else (
        TEXT_PRIMARY if state == "down" else ICON)
    rrect(d, (0, 0, w - 1, h - 1), h / 2.0, fill=color)
    return finish(img, w, h)


def eq_track(w, h):
    """Vertical slider track for the equalizer bands."""
    img = canvas(w, h)
    d = ImageDraw.Draw(img)
    rrect(d, (0, 0, w - 1, h - 1), w / 2.0, fill=BG_SURFACE)
    return finish(img, w, h)
