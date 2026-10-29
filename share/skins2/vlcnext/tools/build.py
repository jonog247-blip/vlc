#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build.py -- Generate the "VLC Next" skins2 skin.

    python3 tools/build.py            # writes theme.xml, PNGs and vlcnext.vlt

Outputs (all inside the skin directory):

    theme.xml           the skin definition (skins2 DTD 2.0)
    vlcnext/*.png       the artwork, generated from vectors in art.py
    vlcnext.vlt         the packaged skin (tar.gz, like skins2/default.vlt)

Nothing here is hand-edited: design.py holds the tokens, art.py the drawing
routines, this file the layout assembly.  test_skin.py validates the result.
"""

import os
import shutil
import sys
import package

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SKIN = os.path.dirname(HERE)
ASSET_DIR = os.path.join(SKIN, "vlcnext")
FONTS = os.path.join(SKIN, "..", "fonts")

sys.path.insert(0, HERE)

import art                                            # noqa: E402
import design as D                                    # noqa: E402

SKIN_NAME = "VLC Next"
SKIN_ID = "vlcnext"


# ---------------------------------------------------------------------------
# Sprite sheets
# ---------------------------------------------------------------------------

class Sheet(object):
    """Packs many small bitmaps into one PNG with SubBitmap definitions."""

    def __init__(self, name, max_width=4096):
        self.name = name
        self.max_width = max_width
        self.items = []          # (id, image)

    def add(self, ident, image):
        self.items.append((ident, image))

    def build(self):
        # Shelf packing, tallest first.
        order = sorted(self.items, key=lambda kv: -kv[1].height)
        rows = []
        cur = []
        cur_w = 0
        for ident, img in order:
            if cur and cur_w + img.width > self.max_width:
                rows.append((cur, cur_w))
                cur, cur_w = [], 0
            cur.append((ident, img))
            cur_w += img.width
        if cur:
            rows.append((cur, cur_w))

        width = max(r[1] for r in rows)
        height = sum(max(i.height for _, i in row) for row, _ in rows)
        sheet = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        rects = {}
        y = 0
        for row, _ in rows:
            x = 0
            row_h = max(i.height for _, i in row)
            for ident, img in row:
                sheet.paste(img, (x, y))
                rects[ident] = (x, y, img.width, img.height)
                x += img.width
            y += row_h
        return sheet, rects


class Bitmaps(object):
    """Registry of every bitmap (or sub-bitmap) id available to theme.xml."""

    def __init__(self):
        self.sheets = []         # (filename, sheet, rects)
        self.ids = {}            # id -> (file, x, y, w, h, is_sub)

    def add_sheet(self, filename, sheet):
        img, rects = sheet.build()
        self.sheets.append((filename, img))
        for ident, (x, y, w, h) in sorted(rects.items()):
            self.ids[ident] = (filename, x, y, w, h, True)
        return img

    def add_file(self, ident, filename, image):
        """A whole-file bitmap (no slicing)."""
        self.sheets.append((filename, image))
        self.ids[ident] = (filename, 0, 0, image.width, image.height, False)

    def size(self, ident):
        return self.ids[ident][3], self.ids[ident][4]

    def xml(self):
        # group sub-bitmaps by file
        files = {}
        for ident, (f, x, y, w, h, is_sub) in sorted(self.ids.items()):
            files.setdefault(f, []).append((ident, x, y, w, h, is_sub))
        out = []
        for f, entries in sorted(files.items()):
            whole = [e for e in entries if not e[5]]
            subs = [e for e in entries if e[5]]
            for ident, x, y, w, h, _ in whole:
                out.append('  <Bitmap id="%s" file="%s/%s" alphacolor="%s"/>'
                           % (ident, SKIN_ID, f, D.ALPHA_COLOR))
            if not subs:
                continue
            out.append('  <Bitmap id="%s" file="%s/%s" alphacolor="%s">'
                       % (subs[0][0].rsplit(".", 1)[0] + ".sheet", SKIN_ID, f,
                          D.ALPHA_COLOR))
            for ident, x, y, w, h, _ in subs:
                out.append('    <SubBitmap id="%s" x="%d" y="%d" '
                           'width="%d" height="%d"/>'
                           % (ident, x, y, w, h))
            out.append("  </Bitmap>")
        return "\n".join(out)


# ---------------------------------------------------------------------------
# XML emitter
# ---------------------------------------------------------------------------

def esc(value):
    return (str(value).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


class El(object):
    """Builds one XML element with stable attribute ordering."""

    ORDER = ["id", "x", "y", "width", "height", "lefttop", "rightbottom",
             "xkeepratio", "ykeepratio", "visible", "image", "resize",
             "art", "up", "down", "over", "up1", "down1", "over1", "up2",
             "down2", "over2", "state", "action", "action1", "action2",
             "text", "font", "color", "scrolling", "alignment",
             "focus", "value", "points", "thickness", "tooltiptext",
             "tooltiptext1", "tooltiptext2", "help", "bgimage", "fgcolor",
             "playcolor", "bgcolor1", "bgcolor2", "selcolor"]

    def __init__(self, tag, **attrs):
        self.tag = tag
        self.attrs = attrs
        self.children = []

    def child(self, el):
        self.children.append(el)
        return self

    def render(self, indent=4):
        pad = " " * indent
        keys = [k for k in self.ORDER if k in self.attrs]
        keys += [k for k in self.attrs if k not in self.ORDER]
        parts = ['%s="%s"' % (k, esc(self.attrs[k])) for k in keys]
        line = "%s<%s %s" % (pad, self.tag, " ".join(parts))
        if not self.children:
            return line + "/>"
        out = [line + ">"]
        for c in self.children:
            out.append(c.render(indent + 2))
        out.append("%s</%s>" % (pad, self.tag))
        return "\n".join(out)


def Image_(ident, x, y, w=None, h=None, bitmap=None, **kw):
    a = {}
    a["id"] = ident
    a["image"] = bitmap
    a["x"] = x
    a["y"] = y
    if w is not None:
        a["width"] = w
    if h is not None:
        a["height"] = h
    a.update(kw)
    return El("Image", **a)


def Button(ident, up, down, over, action, x, y, **kw):
    a = dict(id=ident, up=up, down=down, over=over, action=action, x=x, y=y)
    a.update(kw)
    return El("Button", **a)


def Checkbox(ident, up1, down1, over1, up2, down2, over2, state,
             action1, action2, x, y, **kw):
    a = dict(id=ident, up1=up1, down1=down1, over1=over1, up2=up2,
             down2=down2, over2=over2, state=state, action1=action1,
             action2=action2, x=x, y=y)
    a.update(kw)
    return El("Checkbox", **a)


def Text(ident, text, x, y, width, font="defaultfont", **kw):
    a = dict(id=ident, text=text, x=x, y=y, width=width, font=font)
    a.update(kw)
    return El("Text", **a)


def Slider(ident, x, y, points, up, value, down=None, over=None,
           background=None, nbimages=1, **kw):
    a = dict(id=ident, x=x, y=y, points=points, up=up, value=value)
    if down:
        a["down"] = down
    if over:
        a["over"] = over
    a.update(kw)
    el = El("Slider", **a)
    if background:
        el.child(El("SliderBackground", id=ident + ".bg", image=background,
                    nbhoriz=nbimages))
    return el


def Playlist(ident, x, y, w, h, font="defaultfont", **kw):
    a = dict(id=ident, x=x, y=y, width=w, height=h, font=font)
    a.update(kw)
    return El("Playlist", **a)


def Video(ident, x, y, w, h, **kw):
    return El("Video", id=ident, x=x, y=y, width=w, height=h, **kw)


def Panel(ident, x, y, w, h, **kw):
    return El("Panel", id=ident, x=x, y=y, width=w, height=h, **kw)


# ---------------------------------------------------------------------------
# Artwork
# ---------------------------------------------------------------------------

def build_bitmaps():
    bm = Bitmaps()

    # --- chrome -----------------------------------------------------------
    ui = Sheet("ui.png", max_width=2048)
    ui.add("solid.primary", art.solid(8, 8, D.BG_PRIMARY))
    ui.add("solid.secondary", art.solid(8, 8, D.BG_SECONDARY))
    ui.add("solid.surface", art.solid(8, 8, D.BG_SURFACE))
    ui.add("solid.hover", art.solid(8, 8, D.BG_HOVER))
    ui.add("solid.accent", art.solid(8, 8, D.ACCENT))
    ui.add("blank", art.canvas(8, 8) if False else
           Image.new("RGBA", (8, 8), (0, 0, 0, 0)))
    ui.add("border.h", art.bar(8, 1, D.BORDER))
    ui.add("border.v", art.bar(1, 8, D.BORDER))
    ui.add("logo", art.draw_cone(D.LOGO_SIZE))
    ui.add("tab.over", art.tab_bg(D.TAB_W, D.TAB_H_BTN, "hover"))
    ui.add("tab.active", art.tab_bg(D.TAB_W, D.TAB_H_BTN, "active"))
    ui.add("eq.track", art.eq_track(6, D.EQ_TRACK_H))

    # rectangular button surfaces (88x28) used for the drawer footer
    for i, st in enumerate(D.STATE_NAMES):
        if st == "normal":
            fill = D.BG_SURFACE
        elif st == "hover":
            fill = D.BG_HOVER
        else:
            fill = D.ACCENT_SOFT
        ui.add("btn.rect." + D.XML_STATE[st], art.solid(88, 28, fill, radius=D.RADIUS_SMALL))

    # switch (equalizer on/off)
    for st in D.STATE_NAMES:
        ui.add("toggle.on." + D.XML_STATE[st], switch(st, True))
        ui.add("toggle.off." + D.XML_STATE[st], switch(st, False))

    # grips for window resizing
    ui.add("grip.e", grip_e(6, 40))
    ui.add("grip.s", grip_s(40, 6))
    ui.add("grip.se", grip_se(14, 14))

    # cursors / knobs
    ui.add("seek.cursor.normal", art.seek_cursor(14, "normal"))
    ui.add("seek.cursor.over", art.seek_cursor(14, "hover"))
    ui.add("seek.cursor.down", art.seek_cursor(14, "down"))
    ui.add("vol.cursor.normal", art.volume_cursor(12, D.VOL_CONE_H, "normal"))
    ui.add("vol.cursor.over", art.volume_cursor(12, D.VOL_CONE_H, "hover"))
    ui.add("vol.cursor.down", art.volume_cursor(12, D.VOL_CONE_H, "down"))
    ui.add("eq.knob.normal", art.eq_knob(D.EQ_KNOB_W, D.EQ_KNOB_H, "normal"))
    ui.add("eq.knob.over", art.eq_knob(D.EQ_KNOB_W, D.EQ_KNOB_H, "hover"))
    ui.add("eq.knob.down", art.eq_knob(D.EQ_KNOB_W, D.EQ_KNOB_H, "down"))

    bm.add_sheet("ui.png", ui)

    # --- icon buttons -----------------------------------------------------
    icons = Sheet("icons.png", max_width=1024)
    for key, kind, glyph in D.ICON_BUTTONS:
        cells = 6 if kind == "checkbox" else 3
        for i, st in enumerate(D.STATE_NAMES):
            icons.add("icons.%s.%s" % (key, D.XML_STATE[st]),
                      art.icon_cell(D.BTN, glyph, st, active=False))
        if kind == "checkbox":
            for i, st in enumerate(D.STATE_NAMES):
                icons.add("icons.%s.on.%s" % (key, D.XML_STATE[st]),
                          art.icon_cell(D.BTN, glyph, st, active=True))
    bm.add_sheet("icons.png", icons)

    # --- transport --------------------------------------------------------
    prev = Sheet("prev.png")
    for st in D.STATE_NAMES:
        prev.add("btn.prev." + D.XML_STATE[st], art.transport_cell(D.PREV_SIZE, "prev", st))
    bm.add_sheet("prev.png", prev)

    nxt = Sheet("next.png")
    for st in D.STATE_NAMES:
        nxt.add("btn.next." + D.XML_STATE[st], art.transport_cell(D.NEXT_SIZE, "next", st))
    bm.add_sheet("next.png", nxt)

    play = Sheet("play.png")
    for st in D.STATE_NAMES:
        play.add("btn.play." + D.XML_STATE[st], art.play_pill(D.PLAY_W, D.PLAY_H, st,
                                                 paused=False))
    bm.add_sheet("play.png", play)

    pause = Sheet("pause.png")
    for st in D.STATE_NAMES:
        pause.add("btn.pause." + D.XML_STATE[st], art.play_pill(D.PLAY_W, D.PLAY_H, st,
                                                   paused=True))
    bm.add_sheet("pause.png", pause)

    # --- slider strips ----------------------------------------------------
    seek_w = D.MAIN_W - D.SEEK_X - D.SEEK_RIGHT_GAP
    bm.add_file("seek.strip", "seek_strip.png",
                art.seek_strip(seek_w, D.SEEK_TRACK_H, D.SEEK_FRAMES))
    bm.add_file("seek.strip.fsc", "seek_strip_fsc.png",
                art.seek_strip(D.FSC_SEEK_W, D.SEEK_TRACK_H, D.SEEK_FRAMES))
    bm.add_file("vol.strip", "vol_strip.png",
                art.volume_strip(D.VOL_SLIDER_W, D.VOL_CONE_H, D.VOL_FRAMES))

    return bm, seek_w


def switch(state, on):
    """A small toggle switch for the equalizer."""
    w, h = 44, 24
    img = art.canvas(w, h)
    d = __import__("PIL.ImageDraw", fromlist=["ImageDraw"]).Draw(img)
    if on:
        fill = D.ACCENT if state == "normal" else (
            D.ACCENT_HOVER if state == "hover" else D.ACCENT_SOFT)
        art.rrect(d, (0, 0, w - 1, h - 1), h / 2.0, fill=fill)
        art.ellipse(d, (w - h + 2, 2, w - 3, h - 3), fill=D.TEXT_PRIMARY)
    else:
        fill = D.BG_SURFACE if state == "normal" else (
            D.BG_HOVER if state == "hover" else D.ACCENT_SOFT)
        art.rrect(d, (0, 0, w - 1, h - 1), h / 2.0, fill=fill)
        art.ellipse(d, (2, 2, h - 3, h - 3), fill=D.TEXT_SECOND)
    return art.finish(img, w, h)


def grip_e(w, h):
    img = art.canvas(w, h)
    d = __import__("PIL.ImageDraw", fromlist=["ImageDraw"]).Draw(img)
    art.rrect(d, (w - 3, h * 0.25, w - 1, h * 0.75), 1, fill=D.BORDER)
    return art.finish(img, w, h)


def grip_s(w, h):
    img = art.canvas(w, h)
    d = __import__("PIL.ImageDraw", fromlist=["ImageDraw"]).Draw(img)
    art.rrect(d, (w * 0.25, h - 3, w * 0.75, h - 1), 1, fill=D.BORDER)
    return art.finish(img, w, h)


def grip_se(w, h):
    img = art.canvas(w, h)
    d = __import__("PIL.ImageDraw", fromlist=["ImageDraw"]).Draw(img)
    for i in range(3):
        o = i * 4
        art.line(d, [(w - 3 - o, h - 1), (w - 1, h - 3 - o)], D.BORDER, 1)
    return art.finish(img, w, h)


# ---------------------------------------------------------------------------
# Layout assembly
# ---------------------------------------------------------------------------

def top_bar(W, with_close=True):
    """Section 2.2: cone, unified "..." menu, breadcrumb, window controls."""
    p = Panel("topbar", 0, 0, 0, D.TOPBAR_H, rightbottom="righttop")
    p.child(Image_("topbar.bg", 0, 0, 0, D.TOPBAR_H,
                   bitmap="solid.secondary", resize="scale",
                   rightbottom="righttop", action="move"))
    p.child(Image_("topbar.edge", 0, D.TOPBAR_H - 1, 0, 1, bitmap="border.h",
                   resize="scale", rightbottom="righttop"))
    p.child(Image_("topbar.logo", D.LOGO_X,
                   (D.TOPBAR_H - D.LOGO_SIZE) // 2, D.LOGO_SIZE, D.LOGO_SIZE,
                   bitmap="logo"))
    p.child(Button("topbar.menu", "icons.menu.normal", "icons.menu.down",
                   "icons.menu.over", "main_menu.show()",
                   D.MENU_X, (D.TOPBAR_H - D.MENU_SIZE) // 2,
                   tooltiptext="Main menu"))
    # breadcrumb: folder glyph + media name (section 2.2)
    p.child(Image_("topbar.folder", D.CRUMB_X, 12, 16, 16,
                   bitmap="icons.folder.normal", resize="scale"))
    p.child(Text("topbar.crumb", "$N", D.CRUMB_X + 22, 13, D.CRUMB_W,
                 color=D.hexc(D.TEXT_SECOND), scrolling="auto",
                 focus="false"))
    # technical readout, right aligned
    p.child(Text("topbar.info", "$B kb/s   $S Hz", W - D.INFO_D, 13,
                 D.INFO_W, color=D.hexc(D.TEXT_SECOND), alignment="right",
                 lefttop="righttop", rightbottom="righttop", focus="false"))

    # window controls
    bx = W - D.WIN_BTN_D
    p.child(Button("win.min", "icons.win_min.normal", "icons.win_min.down",
                   "icons.win_min.over", "vlc.minimize()", bx, 0,
                   lefttop="righttop", rightbottom="righttop",
                   tooltiptext="Minimise"))
    bx += D.WIN_BTN_W
    p.child(Checkbox("win.max",
                     "icons.win_unmax.normal", "icons.win_unmax.down",
                     "icons.win_unmax.over",
                     "icons.win_max.normal", "icons.win_max.down",
                     "icons.win_max.over", "main.isMaximized()",
                     "main.unmaximize()", "main.maximize()", bx, 0,
                     lefttop="righttop", rightbottom="righttop",
                     tooltiptext1="Restore", tooltiptext2="Maximise"))
    bx += D.WIN_BTN_W
    p.child(Button("win.close", "icons.win_close.normal",
                   "icons.win_close.down", "icons.win_close.over",
                   "vlc.quit()", bx, 0,
                   lefttop="righttop", rightbottom="righttop",
                   tooltiptext="Quit VLC"))
    return p


def control_bar(W, H, seek_w, layout_id):
    """Section 2.3: transport, seek bar, cone volume, utility buttons."""
    bar_y = H - D.BAR_H
    p = Panel("bar", 0, bar_y, W, D.BAR_H,
              lefttop="leftbottom", rightbottom="leftbottom")
    p.child(Image_("bar.bg", 0, 0, W, D.BAR_H, bitmap="solid.primary",
                   resize="scale", rightbottom="rightbottom", action="move"))
    p.child(Image_("bar.edge", 0, 0, 0, 1, bitmap="border.h", resize="scale",
                   rightbottom="righttop"))

    # ---- row 1: transport + time + seek -------------------------------
    y1 = D.ROW1_CY - D.PREV_SIZE // 2
    p.child(Button("btn.prev", "btn.prev.normal", "btn.prev.down",
                   "btn.prev.over", "playlist.previous()", D.PREV_X, y1,
                   tooltiptext="Previous"))
    p.child(Checkbox("btn.play",
                     "btn.pause.normal", "btn.pause.down", "btn.pause.over",
                     "btn.play.normal", "btn.play.down", "btn.play.over",
                     "vlc.isPlaying", "vlc.pause()", "vlc.play()",
                     D.PLAY_X, D.ROW1_CY - D.PLAY_H // 2,
                     tooltiptext1="Pause", tooltiptext2="Play"))
    p.child(Button("btn.next", "btn.next.normal", "btn.next.down",
                   "btn.next.over", "playlist.next()", D.NEXT_X, y1,
                   tooltiptext="Next"))

    p.child(Text("time.elapsed", "$T", D.NEXT_X + D.NEXT_SIZE + 20,
                 D.ROW1_CY - 7, D.TIME_W, color=D.hexc(D.TEXT_PRIMARY),
                 focus="false"))

    # seek bar -- the strip frame width equals the Bezier width
    p.child(Slider("seek", D.SEEK_X, D.ROW1_CY - 3,
                   "(0,3),(%d,3)" % (seek_w - 1),
                   "seek.cursor.normal", "time",
                   down="seek.cursor.down", over="seek.cursor.over",
                   background="seek.strip", nbimages=D.SEEK_FRAMES,
                   rightbottom="righttop",
                   tooltiptext="Seek: $T / $D"))
    total_x = W - D.SEEK_RIGHT_GAP + 8
    p.child(Text("time.total", "$D", total_x, D.ROW1_CY - 7, D.TOTAL_TIME_W,
                 color=D.hexc(D.TEXT_SECOND), alignment="right",
                 lefttop="righttop", rightbottom="righttop", focus="false"))

    # ---- row 2: title + volume + utility buttons ----------------------
    p.child(Text("bar.title", "$N", D.TRANSPORT_X, D.ROW2_CY - 8, 620,
                 font="font.large", color=D.hexc(D.TEXT_PRIMARY),
                 scrolling="auto", rightbottom="righttop", focus="false"))

    y2 = D.ROW2_CY - D.BTN // 2
    # mini player (section 4.2)
    p.child(Button("btn.pip", "icons.pip.normal", "icons.pip.down",
                   "icons.pip.over", "miniwin.show()", W - D.D_PIP, y2,
                   lefttop="righttop", rightbottom="righttop",
                   tooltiptext="Mini player"))
    p.child(Checkbox("btn.mute",
                     "icons.mute.on.normal", "icons.mute.on.down",
                     "icons.mute.on.over",
                     "icons.mute.normal", "icons.mute.down",
                     "icons.mute.over", "vlc.isMute", "vlc.mute()",
                     "vlc.mute()", W - D.VOL_ICON_D, y2,
                     lefttop="righttop", rightbottom="righttop",
                     tooltiptext1="Unmute", tooltiptext2="Mute"))
    # live volume readout, "$V" is substituted by skins2 (section 2.3)
    p.child(Text("volume.label", "$V%", W - D.VOL_TEXT_D, D.ROW2_CY - 7,
                 D.VOL_TEXT_W, color=D.hexc(D.TEXT_SECOND),
                 alignment="right", lefttop="righttop",
                 rightbottom="righttop", focus="false"))
    p.child(Slider("volume", W - D.VOL_SLIDER_D, D.ROW2_CY - D.VOL_CONE_H // 2,
                   "(0,%d),(%d,%d)" % (D.VOL_CONE_H // 2, D.VOL_SLIDER_W - 1,
                                       D.VOL_CONE_H // 2),
                   "vol.cursor.normal", "volume",
                   down="vol.cursor.down", over="vol.cursor.over",
                   background="vol.strip", nbimages=D.VOL_FRAMES,
                   lefttop="righttop", rightbottom="righttop",
                   tooltiptext="Volume: $V%"))
    p.child(Button("btn.tracks", "icons.tracks.normal", "icons.tracks.down",
                   "icons.tracks.over", "tracks_menu.show()",
                   W - D.D_TRACKS, y2,
                   lefttop="righttop", rightbottom="righttop",
                   tooltiptext="Tracks"))
    p.child(Button("btn.prefs", "icons.gear.normal", "icons.gear.down",
                   "icons.gear.over", "dialogs.prefs()",
                   W - D.D_GEAR, y2,
                   lefttop="righttop", rightbottom="righttop",
                   tooltiptext="Settings"))
    p.child(Checkbox("btn.queue",
                     "icons.queue.on.normal", "icons.queue.on.down",
                     "icons.queue.on.over",
                     "icons.queue.normal", "icons.queue.down",
                     "icons.queue.over",
                     "sidebar_queue.isActive",
                     "main.setLayout(normal)", "main.setLayout(sidebar_queue)",
                     W - D.D_QUEUE, y2,
                     lefttop="righttop", rightbottom="righttop",
                     tooltiptext1="Hide queue", tooltiptext2="Queue"))
    p.child(Button("btn.fullscreen", "icons.fullscreen.normal",
                   "icons.fullscreen.down", "icons.fullscreen.over",
                   "vlc.fullscreen()", W - D.D_FULLSCREEN, y2,
                   lefttop="righttop", rightbottom="righttop",
                   tooltiptext="Fullscreen"))
    return p


def drawer_tabs(W, active):
    """Queue / Audio tabs at the top of the right hand drawer."""
    out = []
    # Queue tab
    out.append(Checkbox("tab.queue",
                        "tab.active", "tab.active", "tab.active",
                        "blank", "tab.active", "tab.over",
                        "sidebar_queue.isActive",
                        "main.setLayout(sidebar_queue)",
                        "main.setLayout(sidebar_queue)",
                        D.SB_PAD, 12))
    out.append(Text("tab.queue.label.on", "Queue", D.SB_PAD, 22, D.TAB_W,
                    font="font.bold", color=D.hexc(D.TEXT_PRIMARY),
                    alignment="center",
                    focus="false", visible="sidebar_queue.isActive"))
    out.append(Text("tab.queue.label.off", "Queue", D.SB_PAD, 22, D.TAB_W,
                    font="font.bold", color=D.hexc(D.TEXT_SECOND),
                    alignment="center",
                    focus="false", visible="not sidebar_queue.isActive"))
    # Audio tab
    ax = D.SB_PAD + D.TAB_W + 12
    out.append(Checkbox("tab.audio",
                        "tab.active", "tab.active", "tab.active",
                        "blank", "tab.active", "tab.over",
                        "sidebar_audio.isActive",
                        "main.setLayout(sidebar_audio)",
                        "main.setLayout(sidebar_audio)",
                        ax, 12))
    out.append(Text("tab.audio.label.on", "Audio", ax, 22, D.TAB_W,
                    font="font.bold", color=D.hexc(D.TEXT_PRIMARY),
                    alignment="center",
                    focus="false", visible="sidebar_audio.isActive"))
    out.append(Text("tab.audio.label.off", "Audio", ax, 22, D.TAB_W,
                    font="font.bold", color=D.hexc(D.TEXT_SECOND),
                    alignment="center",
                    focus="false", visible="not sidebar_audio.isActive"))
    # close
    out.append(Button("drawer.close", "icons.close.normal",
                      "icons.close.down", "icons.close.over",
                      "main.setLayout(normal)",
                      D.SIDEBAR_W - D.CLOSE_D, 12,
                      lefttop="righttop", rightbottom="righttop",
                      tooltiptext="Close panel"))
    out.append(Image_("drawer.divider", 0, D.TAB_H, 0, 1, bitmap="border.h",
                      resize="scale", rightbottom="righttop"))
    return out


def drawer(kind, W, H):
    """The right hand drawer: Queue (3.4) or Audio/equalizer (3.3)."""
    x = W - D.SIDEBAR_W
    p = Panel("drawer", x, D.TOPBAR_H, D.SIDEBAR_W,
              H - D.TOPBAR_H - D.BAR_H,
              lefttop="righttop", rightbottom="rightbottom")
    p.child(Image_("drawer.bg", 0, 0, 0, 0, bitmap="solid.secondary",
                   resize="scale", rightbottom="rightbottom"))
    p.child(Image_("drawer.edge", 0, 0, 1, 0, bitmap="border.v",
                   resize="scale", rightbottom="rightbottom"))
    for el in drawer_tabs(D.SIDEBAR_W, kind):
        p.child(el)

    if kind == "queue":
        p.child(Playlist("queue.list", 8, D.TAB_H + 12, D.SIDEBAR_W - 16,
                         H - D.TOPBAR_H - D.BAR_H - D.TAB_H - 100,
                         fgcolor=D.hexc(D.TEXT_PRIMARY),
                         playcolor=D.hexc(D.ACCENT),
                         bgcolor1=D.hexc(D.BG_SECONDARY),
                         bgcolor2=D.hexc(D.BG_SECONDARY),
                         selcolor=D.hexc(D.BG_HOVER)))
        fy = H - D.TOPBAR_H - D.BAR_H - 56
        for i, (label, action) in enumerate(
                [("Add", "dialogs.file()"),
                 ("Remove", "playlist.del()"),
                 ("Sort", "playlist.sort()")]):
            bx = D.SB_PAD + i * 100
            p.child(Button("queue.%s" % label.lower(),
                           "btn.rect.normal", "btn.rect.down",
                           "btn.rect.over", action, bx, fy))
            p.child(Text("queue.%s.label" % label.lower(), label, bx, fy + 7,
                         88, color=D.hexc(D.TEXT_PRIMARY),
                         alignment="center", focus="false"))
    else:
        # ---- equalizer (section 3.3) ---------------------------------
        p.child(Text("eq.title", "Equalizer", D.SB_PAD, D.TAB_H + 14, 200,
                     font="font.bold.large", color=D.hexc(D.TEXT_PRIMARY),
                     focus="false"))
        p.child(Checkbox("eq.toggle",
                         "toggle.on.normal", "toggle.on.down",
                         "toggle.on.over",
                         "toggle.off.normal", "toggle.off.down",
                         "toggle.off.over",
                         "equalizer.isEnabled",
                         "equalizer.disable()", "equalizer.enable()",
                         D.SIDEBAR_W - 60, D.TAB_H + 12,
                         lefttop="righttop", rightbottom="righttop",
                         tooltiptext1="Disable equalizer",
                         tooltiptext2="Enable equalizer"))
        y0 = D.EQ_TOP
        y1 = D.EQ_BOTTOM
        # preamp
        p.child(Image_("eq.track.preamp", D.EQ_PREAMP_X - 2, y0, 6,
                       D.EQ_TRACK_H, bitmap="eq.track"))
        p.child(Slider("eq.preamp", D.EQ_PREAMP_X, 0,
                       "(0,%d),(0,%d)" % (y1 - 1, y0),
                       "eq.knob.normal", "equalizer.preamp",
                       down="eq.knob.down", over="eq.knob.over",
                       tooltiptext="Preamp"))
        p.child(Text("eq.preamp.label", "pre", D.EQ_PREAMP_X - 16, y1 + 8, 32,
                     font="font.small", color=D.hexc(D.TEXT_SECOND),
                     alignment="center", focus="false"))
        # bands
        for i, name in enumerate(D.EQ_BANDS):
            bx = D.EQ_BAND_X0 + i * D.EQ_BAND_STEP
            p.child(Image_("eq.track.b%d" % i, bx - 2, y0, 6, D.EQ_TRACK_H,
                           bitmap="eq.track"))
            p.child(Slider("eq.band%d" % i, bx, 0,
                           "(0,%d),(0,%d)" % (y1 - 1, y0),
                           "eq.knob.normal", "equalizer.band(%d)" % i,
                           down="eq.knob.down", over="eq.knob.over",
                           tooltiptext="%s Hz" % name))
            p.child(Text("eq.band%d.label" % i, name, bx - 16, y1 + 8, 32,
                         font="font.small", color=D.hexc(D.TEXT_SECOND),
                         alignment="center", focus="false"))
        p.child(Text("eq.info.bitrate", "Bitrate: $B kb/s", D.SB_PAD,
                     y1 + 48, D.SIDEBAR_W - 32,
                     color=D.hexc(D.TEXT_SECOND), focus="false"))
        p.child(Text("eq.info.rate", "Sample rate: $S Hz", D.SB_PAD,
                     y1 + 66, D.SIDEBAR_W - 32,
                     color=D.hexc(D.TEXT_SECOND), focus="false"))
    return p


def video_area(W, H, right_inset=0):
    """Background, album art and the video canvas (section 2.1)."""
    out = []
    out.append(Image_("bg", 0, 0, 0, 0, bitmap="solid.primary",
                      resize="scale", rightbottom="rightbottom"))
    vw = W - right_inset
    out.append(Image_("art", 0, D.TOPBAR_H, vw, H - D.TOPBAR_H - D.BAR_H,
                      bitmap="solid.primary", resize="scale2", art="true",
                      rightbottom="rightbottom"))
    out.append(Video("video", 0, D.TOPBAR_H, vw, H - D.TOPBAR_H - D.BAR_H,
                     rightbottom="rightbottom", visible="vlc.hasVout"))
    return out


def resize_grips(W, H):
    out = []
    out.append(Image_("grip.e", W - 6, D.TOPBAR_H, 6,
                      H - D.TOPBAR_H - D.BAR_H, bitmap="grip.e",
                      resize="scale", action="resizeE",
                      lefttop="righttop", rightbottom="righttop"))
    out.append(Image_("grip.s", 0, H - 6, W - 14, 6, bitmap="grip.s",
                      resize="scale", action="resizeS",
                      lefttop="leftbottom", rightbottom="rightbottom"))
    out.append(Image_("grip.se", W - 14, H - 14, 14, 14, bitmap="grip.se",
                      action="resizeSE",
                      lefttop="rightbottom", rightbottom="rightbottom"))
    return out


def layout(ident, W, H, seek_w, drawer_kind=None, resizable=True):
    el = El("Layout", id=ident, width=W, height=H)
    if resizable:
        el.attrs["minwidth"] = D.MIN_W
        el.attrs["maxwidth"] = D.MAX_W
        el.attrs["minheight"] = D.MIN_H
        el.attrs["maxheight"] = D.MAX_H
    else:
        el.attrs["minwidth"] = W
        el.attrs["maxwidth"] = W
        el.attrs["minheight"] = H
        el.attrs["maxheight"] = H

    inset = D.SIDEBAR_W if drawer_kind else 0
    for c in video_area(W, H, inset):
        el.child(c)
    # the control bar spans the video area, not the drawer
    el.child(control_bar(W - inset, H, seek_w, ident))
    if drawer_kind:
        el.child(drawer(drawer_kind, W, H))
    el.child(top_bar(W))
    for c in resize_grips(W, H):
        el.child(c)
    return el


def mini_window(seek_w):
    """Section 4.2: floating mini player."""
    w = El("Window", id="miniwin", visible="false", x="240", y="160")
    l = El("Layout", id="mini", width=D.MINI_W, height=D.MINI_H,
           minwidth=D.MINI_W, maxwidth=D.MINI_W,
           minheight=D.MINI_H, maxheight=D.MINI_H)
    l.child(Image_("mini.bg", 0, 0, D.MINI_W, D.MINI_H,
                   bitmap="solid.primary", resize="scale",
                   rightbottom="rightbottom", action="move"))
    l.child(Video("mini.video", 0, 0, D.MINI_W, D.MINI_VIDEO_H,
                  visible="vlc.hasVout"))
    cy = D.MINI_VIDEO_H + 28
    l.child(Button("mini.prev", "btn.prev.normal", "btn.prev.down",
                   "btn.prev.over", "playlist.previous()", 16, cy - 16))
    l.child(Checkbox("mini.play",
                     "btn.pause.normal", "btn.pause.down", "btn.pause.over",
                     "btn.play.normal", "btn.play.down", "btn.play.over",
                     "vlc.isPlaying", "vlc.pause()", "vlc.play()",
                     56, cy - 20, tooltiptext1="Pause", tooltiptext2="Play"))
    l.child(Button("mini.next", "btn.next.normal", "btn.next.down",
                   "btn.next.over", "playlist.next()", 128, cy - 16))
    l.child(Button("mini.fs", "icons.fullscreen.normal",
                   "icons.fullscreen.down", "icons.fullscreen.over",
                   "vlc.fullscreen()", D.MINI_W - 88, cy - 16,
                   lefttop="righttop", rightbottom="righttop",
                   tooltiptext="Fullscreen"))
    l.child(Button("mini.close", "icons.close.normal", "icons.close.down",
                   "icons.close.over", "miniwin.hide()",
                   D.MINI_W - 40, cy - 16,
                   lefttop="righttop", rightbottom="righttop",
                   tooltiptext="Close mini player"))
    l.child(Text("mini.title", "$N", 16, D.MINI_VIDEO_H + 4,
                 D.MINI_W - 32, color=D.hexc(D.TEXT_PRIMARY),
                 scrolling="auto", focus="false"))
    w.child(l)
    return w


def fsc_window():
    """Fullscreen controller: the FscWindow fades out by itself."""
    w = El("Window", id="fullscreenController", position="South",
           ymargin="3%")
    l = El("Layout", id="fsc", width=D.FSC_W, height=D.FSC_H,
           minwidth=D.FSC_W, maxwidth=D.FSC_W,
           minheight=D.FSC_H, maxheight=D.FSC_H)
    cy = D.FSC_ROW_CY
    y1 = cy - D.PREV_SIZE // 2
    l.child(Image_("fsc.bg", 0, 0, D.FSC_W, D.FSC_H, bitmap="solid.secondary",
                   resize="scale", rightbottom="rightbottom", action="move"))
    l.child(Image_("fsc.edge", 0, 0, 0, 1, bitmap="border.h",
                   resize="scale", rightbottom="righttop"))
    l.child(Button("fsc.prev", "btn.prev.normal", "btn.prev.down",
                   "btn.prev.over", "playlist.previous()", D.FSC_MARGIN, y1))
    l.child(Checkbox("fsc.play",
                     "btn.pause.normal", "btn.pause.down", "btn.pause.over",
                     "btn.play.normal", "btn.play.down", "btn.play.over",
                     "vlc.isPlaying", "vlc.pause()", "vlc.play()",
                     D.PLAY_X, cy - D.PLAY_H // 2))
    l.child(Button("fsc.next", "btn.next.normal", "btn.next.down",
                   "btn.next.over", "playlist.next()", D.NEXT_X, y1))
    l.child(Text("fsc.time", "$T", D.FSC_TIME_X, cy - 7, D.FSC_TIME_W,
                 color=D.hexc(D.TEXT_PRIMARY), focus="false"))
    l.child(Slider("fsc.seek", D.FSC_SEEK_X, cy - 3,
                   "(0,3),(%d,3)" % (D.FSC_SEEK_W - 1), "seek.cursor.normal",
                   "time", down="seek.cursor.down", over="seek.cursor.over",
                   background="seek.strip.fsc", nbimages=D.SEEK_FRAMES))
    l.child(Text("fsc.total", "$D", D.FSC_TOTAL_X, cy - 7, D.FSC_TIME_W,
                 color=D.hexc(D.TEXT_SECOND), alignment="right",
                 focus="false"))
    l.child(Checkbox("fsc.mute",
                     "icons.mute.on.normal", "icons.mute.on.down",
                     "icons.mute.on.over",
                     "icons.mute.normal", "icons.mute.down",
                     "icons.mute.over", "vlc.isMute", "vlc.mute()",
                     "vlc.mute()", D.FSC_MUTE_X, y1))
    l.child(Slider("fsc.volume", D.FSC_VOL_X, cy - D.VOL_CONE_H // 2,
                   "(0,%d),(%d,%d)" % (D.VOL_CONE_H // 2,
                                       D.VOL_SLIDER_W - 1,
                                       D.VOL_CONE_H // 2),
                   "vol.cursor.normal", "volume", down="vol.cursor.down",
                   over="vol.cursor.over", background="vol.strip",
                   nbimages=D.VOL_FRAMES))
    l.child(Button("fsc.exit", "icons.fullscreen.normal",
                   "icons.fullscreen.down", "icons.fullscreen.over",
                   "vlc.fullscreen()", D.FSC_EXIT_X, y1,
                   tooltiptext="Exit fullscreen"))
    l.child(Button("fsc.close", "icons.close.normal", "icons.close.down",
                   "icons.close.over",
                   "fullscreenController.setLayout(fsc)",
                   D.FSC_CLOSE_X, y1, tooltiptext="Hide controls"))
    w.child(l)
    return w


def popup_menu(ident, entries):
    el = El("PopupMenu", id=ident)
    for label, action, sep in entries:
        if sep:
            el.child(El("MenuSeparator"))
        else:
            el.child(El("MenuItem", label=label, action=action))
    return el


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    bm, seek_w = build_bitmaps()

    # --- write the artwork -------------------------------------------
    if os.path.isdir(ASSET_DIR):
        shutil.rmtree(ASSET_DIR)
    os.makedirs(ASSET_DIR)
    for filename, img in bm.sheets:
        img.save(os.path.join(ASSET_DIR, filename), optimize=True)
    # fonts: give the skin real typographic sizes instead of only the
    # built-in 12px defaultfont.
    for f in ("FreeSans.ttf", "FreeSansBold.ttf"):
        src = os.path.normpath(os.path.join(FONTS, f))
        if os.path.exists(src):
            shutil.copy(src, os.path.join(ASSET_DIR, f))

    # --- theme.xml ----------------------------------------------------
    out = []
    out.append('<?xml version="1.0" encoding="UTF-8"?>')
    out.append('<!DOCTYPE Theme PUBLIC "-//VideoLAN//DTD VLC Skins V2.0//EN" '
               '"skin.dtd">')
    out.append('<Theme version="2.0" alpha="255" movealpha="200" '
               'tooltipfont="defaultfont">')
    out.append('  <ThemeInfo name="%s" author="VLC Next skin" email="" '
               'webpage="https://www.videolan.org/vlc/"/>' % SKIN_NAME)
    out.append("")
    out.append("  <!-- Artwork: generated by tools/build.py from art.py -->")
    out.append(bm.xml())
    for f, size in (("font", 12), ("font.small", 11), ("font.large", 14),
                    ("font.title", 16)):
        out.append('  <Font id="%s" file="%s/FreeSans.ttf" size="%d"/>'
                   % (f, SKIN_ID, size))
    for f, size in (("font.bold", 12), ("font.bold.large", 14)):
        out.append('  <Font id="%s" file="%s/FreeSansBold.ttf" size="%d"/>'
                   % (f, SKIN_ID, size))
    out.append("")
    out.append("  <!-- Section 2.2: one menu replaces the whole menu bar -->")
    out.append(popup_menu("main_menu", D.MAIN_MENU).render(2))
    out.append(popup_menu("tracks_menu", D.TRACKS_MENU).render(2))
    out.append("")
    out.append('  <Window id="main" visible="true" x="140" y="90">')
    out.append(layout("normal", D.MAIN_W, D.MAIN_H, seek_w).render(4))
    out.append(layout("sidebar_queue", D.SIDE_W, D.SIDE_H, seek_w,
                      drawer_kind="queue", resizable=False).render(4))
    out.append(layout("sidebar_audio", D.SIDE_W, D.SIDE_H, seek_w,
                      drawer_kind="audio", resizable=False).render(4))
    out.append("  </Window>")
    out.append(mini_window(seek_w).render(2))
    out.append(fsc_window().render(2))
    out.append("</Theme>")

    theme_path = os.path.join(SKIN, "theme.xml")
    with open(theme_path, "w") as fh:
        fh.write("\n".join(out) + "\n")

    # --- vlcnext.vlt ---------------------------------------------------
    print("wrote %s" % theme_path)
    for f in sorted(os.listdir(ASSET_DIR)):
        p = os.path.join(ASSET_DIR, f)
        print("   %-18s %6.1f KB" % (f, os.path.getsize(p) / 1024.0))
    package.main()


if __name__ == "__main__":
    main()
