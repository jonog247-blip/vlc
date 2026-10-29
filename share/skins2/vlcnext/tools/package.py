#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
package.py -- Build vlcnext.vlt from the checked-in sources.

    python3 tools/package.py

Uses only the Python standard library (tarfile), so it works even without
Pillow: the artwork is committed as PNGs, this only re-creates the archive.
tools/build.py regenerates the artwork and then calls this.

The .vlt is a gzip'ed ustar archive, the same shape as skins2/default.vlt.
VLC's ThemeLoader extracts it and searches it recursively for theme.xml, so
the layout inside is simply:

    theme.xml
    vlcnext/*.png
    vlcnext/FreeSans*.ttf
"""

import os
import sys
import tarfile

HERE = os.path.dirname(os.path.abspath(__file__))
SKIN = os.path.dirname(HERE)
ASSETS = os.path.join(SKIN, "vlcnext")
NAME = "vlcnext"


def main():
    theme = os.path.join(SKIN, "theme.xml")
    if not os.path.exists(theme):
        sys.exit("missing %s -- run tools/build.py first" % theme)
    if not os.path.isdir(ASSETS):
        sys.exit("missing %s -- run tools/build.py first" % ASSETS)

    vlt = os.path.join(SKIN, NAME + ".vlt")
    tmp = vlt + ".tmp"
    with tarfile.open(tmp, "w:gz", format=tarfile.USTAR_FORMAT) as tar:
        tar.add(theme, arcname="theme.xml")
        for name in sorted(os.listdir(ASSETS)):
            tar.add(os.path.join(ASSETS, name),
                    arcname="%s/%s" % (NAME, name))
    os.replace(tmp, vlt)

    print("wrote %s (%d files, %.1f KB)"
          % (vlt, len(os.listdir(ASSETS)) + 1,
             os.path.getsize(vlt) / 1024.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
