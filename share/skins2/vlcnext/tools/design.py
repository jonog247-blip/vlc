#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
design.py -- Design tokens and geometry for the "VLC Next" skins2 skin.

This module is the single source of truth for the skin.  Every colour,
radius, icon size and coordinate used by the generated theme.xml and by the
generated bitmaps is defined here, so that the UI, the artwork and the
automated tests can never drift apart.

The design follows VLC_changes.md ("VLC Media Player UI/UX Redesign"), which
is itself derived from the Juxtopposed redesign walkthrough.

 colours ......... VLC_changes.md section 1.1
 shapes .......... section 1.2 (4-6px radii, no circular buttons)
 iconography ..... section 1.3 (two-tone decorative / monochrome clickable)
 player layout ... section 2
 drawers ......... section 3
"""

# ---------------------------------------------------------------------------
# 1.1 Colour palette & theme tokens (dark theme, the default)
# ---------------------------------------------------------------------------

BG_PRIMARY = (0x12, 0x12, 0x12)   # base application canvas
BG_SECONDARY = (0x1A, 0x1A, 0x1A)  # drawers, sidebars, modals
BG_SURFACE = (0x24, 0x24, 0x24)   # card backgrounds, input fields
BG_HOVER = (0x2F, 0x2F, 0x2F)    # hover states, active list items
BORDER = (0x33, 0x33, 0x33)    # component dividers, input borders

TEXT_PRIMARY = (0xFF, 0xFF, 0xFF)   # headers, active titles, timestamps
TEXT_SECOND = (0x88, 0x88, 0x88)   # inactive labels, metadata, shortcuts

ACCENT = (0xE0, 0x7A, 0x1E)   # primary play button, active toggles
ACCENT_HOVER = (0xF5, 0x8B, 0x2C)   # hover state on primary buttons
ACCENT_SOFT = (0x3A, 0x24, 0x10)   # accent tint used for "pressed" surfaces

ICON = (0xE0, 0xE0, 0xE0)   # monochrome clickable icons (1.5px stroke)
ICON_MUTED = (0x88, 0x88, 0x88)   # two-tone decorative icon stroke

# Cone / wedge volume slider thresholds (section 2.3):
#   green 0-100%, yellow 100-150%, red 150-200%
VOL_GREEN = (0x16, 0xA3, 0x4A)
VOL_YELLOW = (0xEA, 0xB3, 0x08)
VOL_RED = (0xDC, 0x26, 0x26)

# Colour keyed out by the skins2 bitmap loader.  We never paint with it: the
# PNG alpha channel already carries the transparency (file_bitmap.cpp honours
# it), and the attribute is mandatory in skin.dtd.
ALPHA_COLOR = "#FF00FF"

# Hex helpers (XML wants strings such as "#FFFFFF")
def hexc(rgb):
    return "#%02X%02X%02X" % rgb


# ---------------------------------------------------------------------------
# 1.2 Shape language
# ---------------------------------------------------------------------------

RADIUS_SMALL = 4      # buttons, popups
RADIUS_MEDIUM = 6      # primary play pill, panels
STROKE = 1            # 1.5px stroke outline icons, rounded to 1px at 20px
TRANSITION_MS = 150     # documented in the spec; skins2 swaps bitmaps instantly


# ---------------------------------------------------------------------------
# Geometry
# ---------------------------------------------------------------------------

TOPBAR_H = 40        # section 2.2 -- auto-hiding header
BAR_H = 96         # section 2.3 -- two row control bar
SIDEBAR_W = 320        # section 3.2 -- right hand drawer
TAB_H = 56         # drawer tab strip

MAIN_W = 1280        # main window, "normal" layout
MAIN_H = 800
SIDE_W = MAIN_W + SIDEBAR_W      # kept for reference: the drawer is 320 wide
SIDE_H = MAIN_H


MIN_W = 1000       # resizing limits (the control bar needs >= 1000px)
MIN_H = 520
MAX_W = 99999
MAX_H = 99999

# Bottom control bar, local coordinates (bar height 96)
ROW1_CY = 34        # transport + seek row centre
ROW2_CY = 72        # title + utility row centre

TRANSPORT_X = 24        # left margin of [prev][play][next]
PREV_X = TRANSPORT_X
PLAY_X = 64
NEXT_X = 144

PREV_SIZE = 32
NEXT_SIZE = 32
PLAY_W = 64        # the accent orange pill (section 2.3)
PLAY_H = 40

SEEK_X = 266        # seekbar starts after the elapsed time readout
SEEK_RIGHT_GAP = 100      # gap between the seekbar and the window edge

# The seek strip is a sprite sheet whose frames must be exactly as wide
# as the slider's Bezier curve at the design size; the drawer layouts have
# a 320px narrower video column, so they need their own strip.
SEEK_W = MAIN_W - SEEK_X - SEEK_RIGHT_GAP
SEEK_W_DRAWER = MAIN_W - SIDEBAR_W - SEEK_X - SEEK_RIGHT_GAP
TIME_W = 70
TOTAL_TIME_W = 68

VOL_ICON_D = 400       # distance from the right edge to the speaker icon
VOL_TEXT_D = 360       # ... to the "85%" readout (section 2.3)
VOL_TEXT_W = 32
VOL_SLIDER_D = 320
VOL_SLIDER_W = 120
VOL_SLIDER_H = 16

BTN = 32          # square hit area of the utility icon buttons
GAP = 8           # gap between utility buttons
RIGHT_MARGIN = 24

# Distances from the right edge of the window to each utility button
D_TRACKS = 176
D_GEAR = 136
D_QUEUE = 96
D_FULLSCREEN = 56
D_PIP = 440       # mini player (section 4.2)

# Top bar
LOGO_X = 16
LOGO_SIZE = 22
MENU_X = 48
MENU_SIZE = 32
CRUMB_X = 88
CRUMB_W = 320
INFO_W = 220
INFO_D = 372        # distance from the right edge to the technical readout
WIN_BTN_W = 44
WIN_BTN_H = 40
WIN_BTN_D = 132       # distance from the right edge to the window button block

# Drawer (sidebar), local coordinates
SB_PAD = 16
TAB_W = 88
TAB_H_BTN = 36
CLOSE_D = 40        # distance from the drawer's right edge to the close button

# Equalizer (section 3.3)
EQ_TOP = 112
EQ_BOTTOM = 280
EQ_TRACK_H = EQ_BOTTOM - EQ_TOP        # travel of the band sliders
EQ_KNOB_W = 22
EQ_KNOB_H = 10
EQ_BAND_X0 = 70
EQ_BAND_STEP = 24
EQ_PREAMP_X = 34
EQ_BANDS = ["60", "170", "310", "600", "1k", "3k", "6k", "12k", "14k", "16k"]

# Mini player (section 4.2)
MINI_W = 340
MINI_H = 236
MINI_VIDEO_H = 166

# Fullscreen controller (FscWindow, fades out automatically).  Fixed size, so
# every coordinate below is an absolute left/top offset.
FSC_W = 1020
FSC_H = 88
FSC_MARGIN = 24
FSC_ROW_CY = 44        # vertical centre of the control row (88px tall)
FSC_TIME_X = 188
FSC_TIME_W = 60
FSC_SEEK_X = 256
FSC_SEEK_W = 420       # its own sprite strip: see SEEK_FRAMES
FSC_TOTAL_X = 684
FSC_MUTE_X = 756
FSC_VOL_X = 796
FSC_EXIT_X = 924
FSC_CLOSE_X = 964

# ---------------------------------------------------------------------------
# Bitmap slices
# ---------------------------------------------------------------------------
# Every sheet is generated by build.py; the tables below say where each
# control lives inside it.  Cell order is always: normal, hover, down
# (and for checkboxes: state 1 normal/hover/down, state 2 normal/hover/down).

STATE_NAMES = ("normal", "hover", "down")

# skins2 spells the hover state "over" (DTD attribute over=""), so the emitted
# bitmap ids use that spelling while the drawing code keeps the natural one.
XML_STATE = {"normal": "normal", "hover": "over", "down": "down"}

# Small monochrome icon buttons drawn at ICON_GLYPH size inside a BTN hit area
ICON_GLYPH = 18

# Names of the icons rendered into btn_icons.png, in sheet order.
# (key, kind)  kind: "button" (3 cells) or "checkbox" (6 cells)
ICON_BUTTONS = [
    # key              kind        glyph
    ("tracks", "button", "bubble"),
    ("gear", "checkbox", "gear"),
    ("queue", "checkbox", "queue"),
    ("fullscreen", "button", "fullscreen"),
    ("mute", "checkbox", "speaker"),
    ("stop", "button", "stop"),
    ("snapshot", "button", "snapshot"),
    ("record", "button", "record"),
    ("ontop", "checkbox", "ontop"),
    ("faster", "button", "faster"),
    ("slower", "button", "slower"),
    ("pip", "button", "pip"),
    ("pl", "button", "playlist"),
    ("expand", "button", "expand"),
    ("close", "button", "close"),
    ("menu", "button", "menu"),
    ("folder", "button", "folder"),
    ("win_min", "button", "win_min"),
    ("win_max", "button", "win_max"),
    ("win_unmax", "button", "win_unmax"),
    ("win_close", "button", "win_close"),
]

# ---------------------------------------------------------------------------
# Slider strips
# ---------------------------------------------------------------------------
# The skins2 SliderBackground is a sprite sheet: the frame whose index is
# round(value * (nbImages - 1)) is blitted at the control's position, scaled
# by the layout factor (see ctrl_slider.cpp).  Each frame must therefore be
# exactly as wide as the slider's Bezier curve.

SEEK_FRAMES = 61       # ~1.6% steps
SEEK_TRACK_H = 6
VOL_FRAMES = 41       # ~2.5% steps
VOL_CONE_H = 16

# ---------------------------------------------------------------------------
# Menu definitions (section 2.2: one "..." menu replaces the whole menu bar)
# ---------------------------------------------------------------------------

MAIN_MENU = [
    ("Open File...", "dialogs.file()", None),
    ("Open Folder...", "dialogs.directory()", None),
    ("Open Disc...", "dialogs.disc()", None),
    ("Open Network Stream...", "dialogs.net()", None),
    (None, None, "sep"),
    ("Play", "vlc.play()", None),
    ("Pause", "vlc.pause()", None),
    ("Stop", "vlc.stop()", None),
    ("Previous", "playlist.previous()", None),
    ("Next", "playlist.next()", None),
    (None, None, "sep"),
    ("Faster", "vlc.faster()", None),
    ("Slower", "vlc.slower()", None),
    ("Next Frame", "vlc.nextFrame()", None),
    (None, None, "sep"),
    ("Previous Chapter", "dvd.previousChapter()", None),
    ("Next Chapter", "dvd.nextChapter()", None),
    (None, None, "sep"),
    ("Toggle Fullscreen", "vlc.fullscreen()", None),
    ("Always On Top", "vlc.onTop()", None),
    ("Take Snapshot", "vlc.snapshot()", None),
    ("Record", "vlc.toggleRecord()", None),
    (None, None, "sep"),
    ("Queue", "main.setLayout(sidebar_queue)", None),
    ("Audio / Equalizer", "main.setLayout(sidebar_audio)", None),
    ("Mini Player", "miniwin.show()", None),
    ("VLC Playlist", "dialogs.playlist()", None),
    (None, None, "sep"),
    ("Media Information", "dialogs.fileInfo()", None),
    ("Messages", "dialogs.messages()", None),
    ("Preferences...", "dialogs.prefs()", None),
    (None, None, "sep"),
    ("Quit", "vlc.quit()", None),
]

TRACKS_MENU = [
    ("Audio Menu", "dialogs.audioPopup()", None),
    ("Video Menu", "dialogs.videoPopup()", None),
    ("Tools Menu", "dialogs.miscPopup()", None),
    (None, None, "sep"),
    ("Faster", "vlc.faster()", None),
    ("Slower", "vlc.slower()", None),
    ("Next Frame", "vlc.nextFrame()", None),
    (None, None, "sep"),
    ("Toggle Fullscreen", "vlc.fullscreen()", None),
]
