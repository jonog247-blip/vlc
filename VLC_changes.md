
VLC Media Player UI/UX Redesign — Complete Technical Specification
Based on the redesign concept by Juxtopposed (Figma Community File[1] / Video Walkthrough[2]).
1. Design System & Style Tokens
1.1 Color Palette & Theme Tokens
code
Code
DARK THEME (DEFAULT)
┌───────────────────────┬──────────────┬─────────────────────────────────────┐
│ Token Name            │ Hex Value    │ Usage                               │
├───────────────────────┼──────────────┼─────────────────────────────────────┤
│ bg-primary            │ #121212      │ Base application canvas             │
│ bg-secondary          │ #1A1A1A      │ Drawers, sidebars, modals           │
│ bg-surface            │ #242424      │ Card backgrounds, input fields      │
│ bg-surface-hover      │ #2F2F2F      │ Hover states, active list items     │
│ border-subtle         │ #333333      │ Component dividers, input borders   │
│ text-primary          │ #FFFFFF      │ Headers, active titles, timestamps  │
│ text-secondary        │ #888888      │ Inactive labels, metadata, shortcuts│
│ accent-orange (Main)  │ #E07A1E      │ Primary play button, active toggles │
│ accent-orange-hover   │ #F58B2C      │ Hover state on primary buttons      │
└───────────────────────┴──────────────┴─────────────────────────────────────┘

                             ACCENT COLOR CHOICES
   [Orange #E07A1E] [Red #DC2626] [Green #16A34A] [Cyan #06B6D4] [Blue #2563EB]
   [Purple #7C3AED] [Magenta #DB2777] [Amber #D97706] [Gray #4B5563]
1.2 Shape Language & Button Geometry
Border Radius: 4px to 6px on buttons, popups, and input bars [01:27–01:31].
Philosophy: Avoid circular buttons (retaining VLC's distinct utilitarian identity); utilize rounded rectangular pills for all action triggers [01:25–01:32].
Transitions: Smooth 150ms ease-out on all hover and active states.
1.3 Iconography System
Two-Tone Decorative Icons: Muted gray stroke (#888888) with orange fill accent (#E07A1E) used for static section headers and non-clickable visual indicators [01:10].
Monochrome Clickable Icons: Clean 1.5px stroke outline icons in off-white (#E0E0E0) for interactive controls [01:13].
2. In-Player Playback Layout & Behavior
2.1 Full Playback Window Overview
Screenshot Reference: Video Timestamp [04:07], [11:39], [20:13]
code
Code
+-------------------------------------------------------------------------------+
| (▲) [···] [|] 📁 S01 > The Wand S01E04            The Wand S01E04    —  □  ⛶  ✕| <- Top Bar
|-------------------------------------------------------------------------------|
|                                                                               |
|                                                                               |
|                                [ VIDEO CANVAS ]                               |
|                                                                               |
|                                                                               |
|-------------------------------------------------------------------------------|
| [⏮] [  ▶  ] [⏭]  00:06:34 [========●==============================] 00:25:40   |
|                             (Seekbar / Subtitle Timeline)                     |
|                                                  [45% ◄▓▓▒░] [💬] [⚙] [☰] [⛶] | <- Bottom Bar
+-------------------------------------------------------------------------------+
2.2 Top Header Bar
Screenshot Reference: Video Timestamp [03:36], [05:07], [11:36]
code
Code
+-------------------------------------------------------------------------------+
| (▲) [···] [|] 📁 S01 > The Wand S01E04            The Wand S01E04    —  □  ⛶  ✕|
+-------------------------------------------------------------------------------+
   ^    ^    ^   ^                                         ^           ^  ^  ^  ^
   │    │    │   │                                         │           Window Controls
   │    │    │   Media directory breadcrumb (clickable)    Center title
   │    │    In-player library drawer toggle
   │    Consolidated menu trigger (replaces legacy MenuBar)
   VLC Traffic Cone Logo
Behavior & State:
Auto-Hide: Automatically slides out of view during playback; slides down when the mouse enters the top 40px zone [03:48–03:54].
Breadcrumb Navigation: Clicking 📁 S01 navigates back to the parent directory inside the library drawer without interrupting video playback [10:25, 11:36].
Unified ··· Menu: Replaces traditional top menu headers (Media, Playback, Audio, Video, Subtitle, Tools, View, Help) with a single dropdown [05:06–05:12].
2.3 Bottom Control Bar & Seekbar
Screenshot Reference: Video Timestamp [02:14], [02:47], [03:08], [03:25]
code
Code
+-------------------------------------------------------------------------------+
| [⏮] [  ▶  ] [⏭]  00:06:34  [====================================]  00:25:40   |
|                             |░░░░|    |░░░░░░░░|         |░░░░░|              |
|                             (Interactive Subtitle Dialogue Blocks)            |
|                                            [🔊 ◄█████▒░░░]  [💬]  [⚙]  [☰]  [⛶]|
+-------------------------------------------------------------------------------+
  (1)   (2)   (3)    (4)                       (5)            (6)   (7)  (8)  (9)
Control Breakdown:
Previous Track (⏮): Skips to the prior item in the queue [02:14].
Play/Pause Button (▶ / ⏸): Left-aligned rounded rectangle pill in accent orange (#E07A1E) [02:14].
Next Track (⏭): Skips to next item in the queue.
Time Indicators: Clickable format toggles (Elapsed vs Remaining) [02:48].
Cone/Wedge Volume Slider (◄█████▒░░░):
Tapered geometric cone shape [03:07].
Fill level changes dynamically: Green (0–100%) 
→
→
 Yellow (100–150%) 
→
→
 Red (150–200%) [02:59, 03:08].
Quick Track Selector (💬): Opens track flyout [04:30].
Quick Settings Gear (⚙): Opens right-side adjustment drawer [06:34].
Queue Toggle (☰): Opens queue/chapters/bookmarks sidebar [02:46].
Fullscreen Toggle (⛶): Enters/exits true fullscreen [02:22].
2.4 Seekbar Thumbnail Hover Preview & Visual Subtitle Strip
Screenshot Reference: Video Timestamp [03:29], [06:55], [20:31]
code
Code
+-----------------------+
                       |   [Video Frame Img]   |
                       |       00:02:10        |
                       +-----------▼-----------+
[==================================●============================================]
      [████]       [████████]              [█████]       [████████████]
   (Sub block)    (Sub block)            (Sub block)       (Sub block)
Thumbnail Hover: Displays frame snapshot + timestamp at mouse cursor location [03:29].
Subtitle Track Timeline: Renders small horizontal rectangles reflecting dialogue start/end timestamps directly on the seekbar [06:55, 20:31].
Interactive Drag-to-Sync: Scrubbing or dragging an individual subtitle block offsets subtitle delay in real time [07:02].
2.5 Resume Playback Toast (Bottom Center)
Screenshot Reference: Video Timestamp [14:06]
code
Code
+---------------------------------------------+
                     |  You already watched till 00:08:02          |
                     |  [ Continue Watching ]                      |
                     +---------------------------------------------+
[⏮] [  ▶  ] [⏭]  00:06:34 [====================================]  00:25:40 ...
Location: Floats bottom-center above the control bar (instead of legacy top-right corner) [14:04].
Timeout: Automatically dismisses after 8 seconds if ignored.
3. Flyout Panels & Drawers (In-Playback)
3.1 Quick Track Switcher Flyout
Screenshot Reference: Video Timestamp [04:33], [04:37], [04:45]
Triggered by clicking the Track Selector icon (💬):
code
Code
+-----------------------------------------------------+
|    [ Video ]          [ Audio ]       [• Subtitles] |
+-----------------------------------------------------+
| Embedded Tracks                                     |
|   ( ) None                                          |
|   (•) Track 1 - English (SRT)                       |
|                                                     |
| External Tracks                                 [+] |
|   • The_Wand_S01E04 [English]           [✎]     [🗑] |
|                                                     |
| ─────────────────────────────────────────────────── |
| [ Show Preferences ]                                |
+-----------------------------------------------------+
Audio Tab Mode: Adds Output Device section listing connected audio sinks (Speakers, Headphones, Bluetooth) with a refresh icon (↻) [04:37].
3.2 Right Sidebar: Subtitle Sync & Appearance Panel
Screenshot Reference: Video Timestamp [07:16], [07:23], [07:44], [08:00]
code
Code
+------------------------------------------------------------------+
|  [Queue]     [Bookmarks]     [Chapters]     [• Subtitles]    [✕] |
+------------------------------------------------------------------+
| Synchronization                                                  |
|   Subtitle Track Delay                            -2.000 s       |
|   [-10 s] [─────────────●─────────────] [+10 s]                  |
|                                                                  |
|   Subtitle Speed                                 1.000 fps       |
|   [─────────────●─────────────────────]                          |
|                                                                  |
|   Subtitle Duration Factor                       0.000           |
|   [──────●────────────────────────────]                          |
|                                                                  |
| Appearance                                                       |
|   Embedded Sub Format                           [ OFF ]          |
|   Subtitle Font                                 [ Helvetica   ▼] |
|   Text Color                                    [ #B8B8B8 ] [■]  |
|   Outline Color                                 [ #0C0C0C ] [■]  |
|   Subtitle Offset                               0px              |
|   Size Values                     [ Relative ]  [• Pixels ]      |
|   Font Size                                     18px             |
|   [──────────────────●────────────────]                          |
|   Outline Thickness                             2px              |
|   Background Opacity                            0%               |
|                                                                  |
| Presets                                                          |
|   [ The Wand Subtitle Preset                              ▼]     |
|   ├── + New Custom Preset                                        |
|   ├── Default Preset                                             |
|   ├── Anime (Top positioned, yellow text)                        |
|   └── Loud and then Quiet Movies (Boosted duration)              |
|                                                                  |
| [ Open Advanced Settings ]                                       |
+------------------------------------------------------------------+
3.3 Right Sidebar: Audio & Video Filters Panels
Screenshot Reference: Video Timestamp [08:42], [08:49], [08:57]
code
Code
+------------------------------------------------------------------+
|  [Playback]       [Video]       [• Audio]       [Subtitles]  [✕] |
+------------------------------------------------------------------+
| Defaults                                                         |
|   Audio Track                                   [ Track 1     ▼] |
|   Audio Language                                [ English     ▼] |
|   Stereo Mode                                   [ Stereo  ][Test]|
|                                                                  |
| Equalizer                                                [ ON ]  |
|   Preset: [ Full Bass & Treble                            ▼]     |
|   Preamp: +12.0 dB  [──────●──────────────────────]              |
|                                                                  |
|   60Hz   170Hz  310Hz  600Hz   1kHz   3kHz   6kHz  12kHz  16kHz  |
|    |      |      |      |      |      |      |      |      |     |
|   [■]     |      |      |     [■]    [■]     |      |     [■]    |
|    |     [■]    [■]     |      |      |     [■]     |      |     |
|    |      |      |     [■]     |      |      |     [■]     |     |
|                                                                  |
| [>] Compressor                                          [ OFF ]  |
| [>] Spatializer                                         [ OFF ]  |
| [>] Stereo Widener                                      [ OFF ]  |
+------------------------------------------------------------------+
3.4 Right Sidebar: Queue, Bookmarks & Chapters
Screenshot Reference: Video Timestamp [02:49], [15:12], [15:15]
code
Code
+------------------------------------------------------------------+
|  [• Queue]            [Bookmarks]           [Chapters]       [✕] |
+------------------------------------------------------------------+
|  2 Items • 48m                              [↓↑] [↻] [⤮] [-] [+] |
|                                                                  |
|  :: The_Wand_S01E03.mp4                                23:06     |
|  :: The_Wand_S01E04.mp4 (Playing)                      25:40     |
|                                                                  |
|  (Drag and drop new media files here to queue)                   |
+------------------------------------------------------------------+

CHAPTERS TAB VIEW:
|  01  Winter (00:02:15)                                           |
|  02  Spring (00:29:45)                                           |
|  03  Summer (00:51:30)                                           |
|  04  Fall   (01:13:50)                                           |
3.5 Bulk Subtitle Matcher Dialog
Screenshot Reference: Video Timestamp [06:04], [06:14], [06:19]
Invoked via Add Subtitles button:
code
Code
+-----------------------------------------------------------------------------------+
| Add Subtitles                                                                 [✕] |
+-----------------------------------------------------------------------------------+
| Target: [ To This Folder   ▼]   Source: [ From Computer ▼]   Query: [ The Wand S01]
|-----------------------------------------------------------------------------------|
| Video File                          Matched Subtitle File                Action   |
|-----------------------------------------------------------------------------------|
| 📄 The_Wand_S01E01.mp4   ───────►   📄 The_Wand_S01E01.srt               [ ⇄ ]    |
| 📄 The_Wand_S01E02.mp4   ───────►   📄 The_Wand_S01E02.srt               [ ⇄ ]    |
| 📄 The_Wand_S01E03.mp4   ───────►   📄 The_Wand_S01E03.srt               [ ⇄ ]    |
| 📄 The_Wand_S01E04.mp4   ───────►   📄 The_Wand_S01E04.srt               [ ⇄ ]    |
| 📄 The_Wand_S01E05.mp4   ───────►   📄 The_Wand_S01E05.srt               [ ⇄ ]    |
|-----------------------------------------------------------------------------------|
| [ Cancel ]                                                        [ Save & Sync ] |
+-----------------------------------------------------------------------------------+
4. Media Library & Management Views
4.1 In-Playback Overlay Library Drawer
Screenshot Reference: Video Timestamp [11:39], [11:45]
Allows file browsing without exiting the video view:
code
Code
+-------------------------------------------------------------------------------+
| [🏠] [📁 Videos > The Wand > S01] [↓↑] [⊞] [🔍 Search]             —  □  ⛶  ✕|
+-------------------+-----------------------------------------------------------+
| 📁 Videos         |                                                           |
| 🎵 Music          |   [ CURRENT VIDEO PLAYBACK PERSISTS HERE ]                |
| 📶 Network        |                                                           |
| 📑 Playlists      |   (Drawer overlays on the left; video is not stopped)     |
| ───────────────── |                                                           |
| 📄 S01E01.mp4     |                                                           |
| 📄 S01E02.mp4     |                                                           |
| 📄 S01E03.mp4     |                                                           |
| 📄 S01E04.mp4     |                                                           |
| 📄 S01E05.mp4     |                                                           |
+-------------------+-----------------------------------------------------------+
4.2 Full Library Mode with Corner Mini-Player
Screenshot Reference: Video Timestamp [11:48], [11:52], [20:15]
When navigating away to the full library while playback is active:
code
Code
+-------------------------------------------------------------------------------+
| (▲) [···] [🏠 Home]   [🔍 Search library...]                       —  □  ⛶  ✕|
+------------+------------------------------------------------------------------+
| 🏠 Home    |  Videos > Shows > The Wand > S01           15 Items  [↓↑] [⊞] [🔍]|
| 🎬 Videos  |  +-------------------------------------------------------------+ |
| 🎵 Music   |  | [Thumbnail]   [Thumbnail]   [Thumbnail]   [Thumbnail]       | |
| 📶 Network |  |  S01E01        S01E02        S01E03        S01E04           | |
| 📑 Playlists| |                                                             | |
| 🕒 Recent  |  | [Thumbnail]   [Thumbnail]   [Thumbnail]   [Thumbnail]       | |
|            |  |  S01E05        S01E06        S01E07        S01E08           | |
| 📌 PINNED  |  +-------------------------------------------------------------+ |
| • CoolSongs|                                                                  |
| • Anime    |                                      +-------------------------+ |
|            |                                      | [Mini Player Window]    | |
| [+] Add    |                                      | S01E05 (Playing)        | |
|            |                                      | [⏮] [ ⏸ ] [⏭]  [—] [⛶]| |
+------------+--------------------------------------+-------------------------+-+
4.3 Music Player View
Screenshot Reference: Video Timestamp [12:15], [12:20]
code
Code
+-------------------------------------------------------------------------------+
| (▲) [···] [🎵 Music > Songs > My Songs]                            —  □  ⛶  ✕|
+------------+------------------------------------------------------------------+
| 🏠 Home    |                                                                  |
| 🎬 Videos  |                    +------------------------+                    |
| 🎵 Music   |                    |                        |                    |
| 📶 Network |                    |   ALBUM ART DISPLAY    |                    |
| 📑 Playlists|                   |      (Square 1:1)      |                    |
| 🕒 Recent  |                    |                        |                    |
|            |                    +------------------------+                    |
| 📌 PINNED  |                                                                  |
| • My Songs |                         untangle - juxtopposed                   |
|            |                              Single (2024)                       |
+------------+------------------------------------------------------------------+
| [⏮] [  ▶  ] [⏭]  00:00:10  [|||||||||||||||·····················]  00:03:40   |
|                             (Audio Amplitude Waveform Scrub Bar)              |
+-------------------------------------------------------------------------------+
5. Global Settings Architecture
Screenshot Reference: Video Timestamp [17:39], [17:43], [17:50], [18:09], [18:48]
code
Code
+-------------------------------------------------------------------------------+
| Settings                                                                  [✕] |
+--------------------+----------------------------------------------------------+
| 🔍 Search settings | Appearance                                               |
|                    |   Interface language                     [ English    ▼] |
| APP                |   Theme                  [• Dark ]   [ Light ]  [ System ]|
| • General          |   Accent color           [■][■][■][■][■][■][■][■][■]     |
|   Interface        |                                                          |
|   Privacy          | Startup                                                  |
|   Controls         |   Show confirmation and error dialogs            [ OFF ] |
|                    |   Check for updates automatically                [  ON ] |
| MEDIA              |                                                          |
|   Playback         | Diagnostics                                              |
|   Video            |   Developer mode                                 [ OFF ] |
|   Audio            |   Save a log                                     [ OFF ] |
|   Subtitles        |                                                          |
|   Library          | ──────────────────────────────────────────────────────── |
|                    | [v] Advanced Options                                     |
| SYSTEM             |     Show minor warnings                          [ OFF ] |
|   Network          |     Log format                               [ Plain text ]|
|   Performance      |     Collect playback statistics                  [  ON ] |
|   Recording        |                                                          |
|   Extensions       | [ Reset all settings ]                                   |
+--------------------+----------------------------------------------------------+
5.1 Replaced Obscure Numeric Settings
Legacy Subtitle Fuzziness: Replaced numeric 0–4 with human-readable dropdown options:
Off
Any title
Contains title
Title with extra characters (Default)
Exact title match [17:29–17:34]
Contextual Documentation: Every item has an ⓘ tooltip hover explaining the underlying flag [18:51].
5.2 Dedicated Keyboard Shortcuts Manager & OSD Feedback
Screenshot Reference: Video Timestamp [15:26], [15:59]
code
Code
+-------------------------------------------------------------------------------+
| Keyboard Shortcuts                                                        [✕] |
+-------------------------------------------------------------------------------+
| 🔍 Search Action or Shortcut...                                               |
|                                                                               |
| Action                      Shortcut             Global Hotkey                |
|-------------------------------------------------------------------------------|
| Toggle Fullscreen           F                    [ None ]                     |
| Exit Fullscreen             Esc                  [ None ]                     |
| Play / Pause                Space                Media Play/Pause             |
| Next Frame                  E                    [ None ]                     |
| Subtitle Track Cycle        V                    [ None ]                     |
| Audio Track Cycle           B                    [ None ]                     |
| Subtitle Delay Up           G                    [ None ]                     |
| Subtitle Delay Down         H                    [ None ]                     |
| Aspect Ratio Cycle          A                    [ None ]                     |
| Crop Ratio Cycle            C                    [ None ]                     |
+-------------------------------------------------------------------------------+
On-Screen Display Feedback: Triggering a shortcut displays a temporary status badge in the upper right quadrant:
code
Code
+──────────────────────+
|  Crop: 2.35:1        |
|  Pressed 'C'         |
+──────────────────────+
6. Player Toolbar Customizer & Profile Switcher
Screenshot Reference: Video Timestamp [19:12], [19:22], [19:31]
code
Code
+-------------------------------------------------------------------------------+
| Customize Player Toolbar                                                  [✕] |
+-------------------------------------------------------------------------------+
| Drag items in and out of the toolbar bar below to reorder them:               |
|                                                                               |
|  [ Spacer ]       [ Divider ]      [ Speed 1x ]    [ Backward 10s ]           |
|  [ Forward 10s ]  [ Backward 15s ] [ Forward 15s ] [ Stop ]                   |
|  [ Repeat ]       [ Shuffle ]      [ Record ]      [ Snapshot ]               |
|  [ Picture-in-Pic][ HDR ]          [ Zoom ]        [ Right Sidebar ]          |
|  [ Chapters ]     [ Favorite ]     [ Bookmarks ]   [ Media Info ]             |
|                                                                               |
| ACTIVE TOOLBAR PREVIEW:                                                       |
| +---------------------------------------------------------------------------+ |
| | [⏮] [ ▶ ] [⏭] [Time] [====== Seekbar ======] [Vol] [💬] [⚙] [☰] [⛶]      | |
| +---------------------------------------------------------------------------+ |
|                                                                               |
| Active Layout Profile: [ Shows ▼ ]  (Profiles: Movies, Shows, Music, Work)    |
|                                                                               |
| [ Cancel ]                                                    [ Save Layout ] |
+-------------------------------------------------------------------------------+
7. First-Run Onboarding Flow
Screenshot Reference: Video Timestamp [19:47], [19:49], [19:50]
code
Code
STEP 1: WELCOME & MEDIA FOLDER
+---------------------------------------------------------+
|                        (▲)                              |
|                   Welcome to VLC!                       |
|   Choose a default media folder to get started with:    |
|   [ ~/Videos                               ] [Browse]   |
|                                                         |
|                                              [ Next ► ] |
+---------------------------------------------------------+

STEP 2: THEME & ACCENT
+---------------------------------------------------------+
|            Select your preferred theme & color          |
|                                                         |
|       [ Light ]          [• Dark ]          [ System ]  |
|                                                         |
|    (•) Orange   ( ) Red    ( ) Green   ( ) Blue   ( ) Cyan|
|                                                         |
| [ ◄ Back ]                                   [ Next ► ] |
+---------------------------------------------------------+

STEP 3: ESSENTIAL KEYBOARD SHORTCUTS
+---------------------------------------------------------+
|            Learn the basic keyboard shortcuts           |
|                                                         |
|   Play / Pause          [ Space ]                       |
|   Toggle Fullscreen     [   F   ]                       |
|   Seek Back / Forward   [ ◄ ] [ ► ]                     |
|   Volume Up / Down      [ ▲ ] [ ▼ ]                     |
|   Cycle Subtitles       [   V   ]                       |
|   Cycle Audio           [   B   ]                       |
|                                                         |
| [ ◄ Back ]                                 [ Finish ✓ ] |
+---------------------------------------------------------+
8. Implementation Checklist for Skin / Frontend Developers

Layout Engine: Implement left-aligned playback controls ([Prev] [Play Pill] [Next] [Time]) [02:14].

Cone Volume Slider: Custom vector shape widget mapping audio volume from 
0
%
0%
 to 
200
%
200%
 with green-yellow-red threshold coloring [03:07].

Unified Top Bar: Remove native OS menu bar text entries; substitute with (▲) [···] icon dropdown and directory breadcrumb [05:07, 11:36].

Subtitle Alignment Drawer: Right-hand sliding drawer with timing offset sliders and preset persistence keyed per TV show / movie title [07:16, 08:00].

Visual Subtitle Seekbar Strip: Canvas layer on top of the seekbar rendering dialogue time spans as interactive blocks [06:55, 20:31].

In-Playback Overlay File Browser: Overlay drawer that opens over active playback without scaling or stopping the video [11:39].

Floating Mini-Player: Window-in-window mode triggered when navigating into the full media library during playback [11:48].

Plain-Text Settings: Refactored preferences dialog replacing numeric flags with human-readable dropdowns and search indexing [17:29, 17:40].