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
| §2.3 | Left aligned `[prev][play pill][next]`, elapsed/total time, seek bar, live `85%` readout, cone/wedge volume slider (green → yellow → red), track flyout, settings, queue, fullscreen | layout `normal` |
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
preferences / open / playlist dialogs behind the gear button.


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
* Elapsed ⇄ remaining time toggle on click (`§2.3`) — `$T` / `$D` are fixed
  macros and no command switches them; both are shown at once instead.
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
9. re-runs `Position` for every control at a window 320×180 larger
   (`relayout()`) and re-checks containment, overlap and the drawer edge,
   because an anchor that is wrong is invisible at the design size and only
   shows up when the user drags the window corner.

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
