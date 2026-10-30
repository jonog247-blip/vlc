# VLC Next — a skins2 skin

A reskin of VLC implementing the redesign described in
[`VLC_changes.md`](../../../VLC_changes.md) (itself taken from the Juxtopposed
redesign walkthrough): dark surfaces, a single accent colour, left aligned
transport controls with an accent orange play pill, a tapered cone volume
slider, a unified `···` menu instead of the menu bar, and right hand drawers
for the queue and the equalizer.

It is a **skins2 skin**, so it loads into an existing VLC installation:
**no compiling, no patching, no rebuilding VLC.**


## Install

1. Grab `vlcnext.vlt` (or rebuild it, see below).
2. VLC → *Tools* → *Preferences* → *Interface*.
3. Under *Look and feel*, pick **Use custom skin**, browse to `vlcnext.vlt`.
4. Save and restart VLC.

To go back: same place, choose *Native* (or *System's default*).

skins2 is built into VLC 3.x and is still built by this tree
(`modules/gui/skins2`, `meson` option `skins2`, default `auto`).


## What the skin gives you

| Spec | Feature | Where |
|---|---|---|
| §1.1 | Dark palette (`#121212` / `#1A1A1A` / `#242424` / `#2F2F2F` / `#333333`), orange accent `#E07A1E` | `tools/design.py` |
| §1.2 | 4–6px radii, rounded-rectangular pills, no circular buttons | `tools/art.py` |
| §1.3 | Two-tone cone mark, monochrome off-white `#E0E0E0` icon set, orange for active toggles | `tools/art.py` |
| §2.1 | Video canvas + top bar + two row control bar | layout `normal` |
| §2.2 | Unified `···` menu replacing the whole menu bar, folder breadcrumb, technical readout, window controls | `PopupMenu id="main_menu"` |
| §2.3 | Left aligned `[prev][play pill][next]`, elapsed/total time, seek bar, live `85%` readout, cone/wedge volume slider (green → yellow → red), track flyout, audio drawer, queue drawer, fullscreen | layout `normal` |
| §2.4 | Seek bar with a filled progress track and a scrub handle | `seek.strip` sprite sheet |
| §3.3 | Audio drawer: equalizer on/off, preamp and all 10 bands, bitrate / sample rate | layout `sidebar_audio` |
| §3.4 | Queue drawer: live playlist, add / remove / sort | layout `sidebar_queue` |
| §4.2 | Floating mini player | window `miniwin` |
| §2.2 | Auto-hiding controls in fullscreen (VLC's `FscWindow` fades them out) | window `fullscreenController` |

The drawers are **inside** the window: opening one takes its 320px out of the
video column instead of widening the window, so the window keeps whatever size
you gave it. That works because all three main layouts declare the same
original size and the same min/max (skins2 only carries a resize across a
layout switch when it considers the layouts one window:
`GenericLayout::isTightlyCoupledWith`), and because the control bar and the
video area are anchored to the drawer's left edge rather than to the window's
right edge.

Extras that come free with skins2: window resizing and drag by the bars,
album art behind the video, tooltips on every control, and VLC's own
preferences / open / playlist dialogs behind the `···` menu (the gear opens
the audio drawer, as in `§2.3`).

### Window size and 4K screens

The window opens at **1280×800**, centred for a 1920×1080 desktop
(`<Window id="main" x="320" y="140">`), and every layout is freely resizable:

```
min 1000×520   max unbounded   default 1280×800
```

Everything is anchored, so the header, the control bar, the seek bar, the
drawers and the resize grips follow the window edge at any size — up to 4K and
beyond. The size you drag the window to is stored by VLC in `skins2-config`
and reused on the next start.

skins2 has **no screen query and no DPI awareness**: a theme cannot ask how
big the desktop is or how the compositor scales it, and the bitmaps are blitted
1:1 in physical pixels. That is why the default is a compromise between a
1080p laptop and a 4K desktop rather than a proportional size, and why on a 4K
panel (or on a HiDPI display scaled below 100%) the window has to be dragged
open once — VLC then remembers it. If a stale `skins2-config` entry ever wins
(e.g. after the layout ids changed between versions) VLC falls back to the
default above.


## What skins2 cannot do

These need changes to the skins2 C++ module (new variables and controls), so
they are **not** in the skin. They are listed in `VLC_changes.md` but cannot be
reached from a `.vlt` file:

* Resume-playback toast (`§2.5`) — a skin cannot show timed pop-ups.
* Auto-hiding top bar (`§2.2`) — skins2 hides windows, not parts of a layout,
  so the header is always visible. The header and the control bar *are* drag
  handles, which is how the window is moved.
* Clicking the folder breadcrumb to walk up a directory (`§2.2`) — there is no
  library in skins2, so it opens VLC's playlist instead.
* Screen-relative window sizing (`§4.1` "responsive up to 4K") — a skin
  cannot query the screen size or the DPI, so the window opens at a fixed
  default size and is resized by hand (VLC remembers it).
* Elapsed ⇄ remaining time toggle on click (`§2.3`) — `$T` / `$D` are fixed
  macros and no command switches them; both are shown at once instead.
* The centre title of the header (`§2.2`) — skins2 has no way to ellipsize or
  centre a string over a variable width, and the media name is already the
  breadcrumb, so that slot carries the bitrate / sample-rate readout.
* Subtitle sync panel (delay / speed / duration sliders) — skins2 has no
  subtitle variables; only `time`, `volume` and the equalizer are exposed.
* Subtitle appearance settings and per-show presets.
* Subtitle dialogue blocks drawn on the seek bar, and drag-to-sync.
* Thumbnail hover previews on the seek bar.
* Bulk subtitle matcher dialog.
* Bookmarks and chapters tabs (no chapter/bookmark list control exists).
* Library / music browsing views and the corner mini-player-over-library.
* Rewritten settings, keyboard shortcut manager, toolbar customizer and
  first-run onboarding — those live in VLC's own dialogs, not in a skin.

Everything above would be a change to `modules/gui/skins2` (C++) or to the Qt
interface (`modules/gui/qt`), which needs a full VLC build.


## Seek bar accuracy (a one-file engine fix, shipped in this tree)

The seek bar is driven by the `time` variable, i.e. by the *position* VLC's
demuxer reports (`DEMUX_GET_POSITION`).  VLC computes that as
`i_pcr / i_duration`, which is only meaningful when the container starts at
timestamp 0.  For files that start far from zero (many MKVs, remuxes,
broadcast captures) a stream that has just started reports a position close to
1.0: the bar shows "nearly finished", and a click seeks with the same skewed
scale, so scrubbing appears not to work either.  The elapsed/duration readouts
next to the bar (`$T`/`$D`) query the player directly and are correct, which is
why the two disagree.

`modules/gui/skins2` now derives the variable from the player's own time and
length, and seeks by time:

* `src/vlcproc.cpp` — `VlcProc::on_position_changed()` recomputes the position
  as `vlc_player_GetTime() / vlc_player_GetLength()` instead of trusting the
  value handed over by the demuxer;
* `vars/time.cpp` — `StreamTime::set()` seeks with `vlc_player_SetTime(pct *
  length)`, falling back to `vlc_player_SetPosition()` when the length is
  unknown (live streams).

This fixes the slider, the scrub target and the "at the end when just
starting" symptom for **every** skins2 theme, not just this one.  It is a
change to `modules/gui/skins2`, so it only takes effect in a VLC built from
this tree; a stock VLC binary fed this `.vlt` still gets the old (demux)
position and can therefore show an early "full" bar on such files.


## Rebuilding

The skin is generated from source — the artwork is drawn with vectors, not
hand-edited bitmaps:

```sh
pip install Pillow lxml          # build + test dependencies
python3 tools/build.py           # -> theme.xml, vlcnext/*.png, vlcnext.vlt
python3 tools/test_skin.py       # validate + render previews
python3 tools/test_skin.py --check   # validation only (non-zero exit on error)

python3 tools/package.py         # re-pack vlcnext.vlt, stdlib only, no Pillow
```

`*.vlt` is in VLC's `.gitignore` (it is a build product, exactly like
`skins2/default.vlt`), but `vlcnext.vlt` is force-added here so that a fresh
clone contains a ready-to-install skin. After rebuilding, refresh it with
`git add -f share/skins2/vlcnext/vlcnext.vlt`.
`tools/package.py` re-creates it from `theme.xml` + the PNGs using nothing but
`tarfile`, so you never need Pillow just to repack the skin.

Editing workflow:

* **Colours, sizes, spacing, menu contents** → `tools/design.py`
* **Icons, buttons, sliders, chrome** → `tools/art.py`
* **Layout, controls, actions** → `tools/build.py`

`tools/test_skin.py` is the interesting part. It does not just parse the XML:

1. validates `theme.xml` against VLC's own `share/skins2/skin.dtd`;
2. checks every bitmap reference resolves and every file exists;
3. checks every action against the commands actually registered in
   `modules/gui/skins2/parser/interpreter.cpp` (read from the source at test
   time), plus the `<id>.show()/hide()/setLayout()` family;
4. checks every variable in `value=`, `state=` and `visible=` against the
   variables registered in `vlcproc.cpp`;
5. checks slider sprite strips tile exactly and that one frame is exactly as
   wide as the slider's Bezier curve — get this wrong and the fill silently
   stops lining up with the handle;
6. checks every control sits inside its layout and that no two mouse targets
   overlap;
7. renders a preview PNG per layout (plus `tools/preview/contact_sheet.png`)
   over a coloured desktop, exactly the way skins2 composites — every control
   clipped to its own rectangle, images resized with `mosaic` / `scale` /
   `scale2` semantics, sliders placed on the Bezier curve, `$` macros filled
   with sample values — and asserts on pixels: the play pill is orange, the
   seek fill is orange up to the playhead and grey after it, the cone volume
   is green below 100%, the drawers really draw on the right;
8. asserts that **every pixel of every layout is opaque**, because skins2
   shapes the window from the painted alpha channel: one unpainted pixel is a
   see-through hole to the desktop. This is what catches a stretched 8×8
   swatch whose last row was left semi-transparent by the resampler;
9. re-runs `Position` for every control (`relayout()`) at a window 320×180
   larger *and* at the layout's own minimum size, then re-checks containment,
   click target overlap, the drawer's width and edge, and that the seek bar
   absorbed the width delta. An anchor that is wrong is invisible at the
   design size and only shows up when the user drags the window corner — this
   is what caught the queue list and its footer buttons not following the
   bottom of the drawer;
10. asserts that **every control id is unique across the whole theme**, not
   just inside one layout.  skins2 keeps controls in one map keyed by id while
   each layout keeps *raw* pointers to them, so two layouts sharing an id (the
   same `seek` in `normal` and in both drawers) makes the builder destroy the
   first control and leave that layout pointing at freed memory — the widget
   then paints nothing, paints stale pixels or eats clicks, depending on
   allocation order.  Control ids are therefore prefixed with their layout id
   (`normal.seek`, `sidebar_audio.volume`, `fsc.fsc.seek`) by
   `tools/build.py`, and this check keeps them that way.

## Files

```
theme.xml               generated skin definition (skins2 DTD 2.0)
vlcnext.vlt             packaged skin  (tar.gz, like skins2/default.vlt)
vlcnext/*.png           generated artwork
tools/design.py         tokens + geometry
tools/art.py            vector drawing (Pillow, 4x supersampled)
tools/build.py          assembles theme.xml, renders PNGs, packages the .vlt
tools/test_skin.py      validation + preview rendering
tools/preview/          rendered previews (regenerated by the test)
```

The skin can also be opened in the **VLC Skin Editor** (`File` → `Open` → pick
`theme.xml`); `tools/build.py` writes plain, hand-editable XML.
