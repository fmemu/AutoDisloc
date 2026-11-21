# SPDX-License-Identifier: MIT
# AutoDisloc 2 - Copyright (c) 2026 Firat Memu
"""Draw the program icon (a broadened diffraction peak over a sharp one)."""
import os
import sys

import numpy as np
from matplotlib.figure import Figure

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = os.path.join(ROOT, "assets")
os.makedirs(out, exist_ok=True)
fig = Figure(figsize=(4, 4), dpi=256)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")
from matplotlib.patches import FancyBboxPatch
ax.add_patch(FancyBboxPatch((0.04, 0.04), 0.92, 0.92, boxstyle="round,pad=0,rounding_size=0.2",
                            fc="#16324f", ec="none"))
x = np.linspace(0.1, 0.9, 600)
sharp = 0.2 + 0.62 * np.exp(-((x - 0.5) / 0.018) ** 2)
broad = 0.2 + 0.42 / (1 + ((x - 0.5) / 0.07) ** 2)
ax.fill_between(x, 0.2, broad, color="#2a78d6", alpha=0.55, lw=0)
ax.plot(x, broad, color="#86b6ef", lw=7, solid_capstyle="round")
ax.plot(x, sharp, color="white", lw=5, solid_capstyle="round")
ax.plot([0.1, 0.9], [0.2, 0.2], color="#86b6ef", lw=4, solid_capstyle="round")
png = os.path.join(out, "icon.png")
fig.savefig(png, transparent=True)
from PIL import Image
im = Image.open(png).convert("RGBA")
im.save(os.path.join(out, "icon.ico"), sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
if sys.platform == "darwin":
    iconset = os.path.join(out, "icon.iconset")
    os.makedirs(iconset, exist_ok=True)
    for s in (16, 32, 128, 256, 512):
        im.resize((s, s), Image.LANCZOS).save(os.path.join(iconset, f"icon_{s}x{s}.png"))
        im.resize((2 * s, 2 * s), Image.LANCZOS).save(os.path.join(iconset, f"icon_{s}x{s}@2x.png"))
    os.system(f'iconutil -c icns "{iconset}" -o "{os.path.join(out, "icon.icns")}"')
print("icon ok")
