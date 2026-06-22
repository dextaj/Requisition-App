"""
branding.py — shared logo / branding helpers for all screens.

Drop this file in the same folder as your other .pyw screens
(PythonApplication1) so every screen can `import branding`.

Usage in any screen's _build_header:

    import branding

    def _build_header(self):
        hdr = tk.Frame(self, bg=C_HEADER_BG, height=70)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        branding.add_logo(hdr, self, bg=C_HEADER_BG)   # <-- one line

        tk.Label(hdr, text="Administration", ...).pack(...)
        ...
"""

import os
from PIL import Image, ImageTk

# ─────────────────────────────────────────────
#  PATHS
# ─────────────────────────────────────────────
# Resolve the assets folder relative to THIS file, so it keeps working
# even if the app is moved to another machine or folder.
_BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR  = os.path.join(_BASE_DIR, "assets")
LOGO_PATH   = os.path.join(ASSETS_DIR, "image.png")


# ─────────────────────────────────────────────
#  LOGO LOADER
# ─────────────────────────────────────────────
def add_logo(header_frame, owner, height=50, bg="#1A2B4A",
             side="left", padx=(24, 12), pady=10, path=None):
    """
    Load the logo, scale it to `height` px tall (keeping aspect ratio),
    and pack it into `header_frame`.

    The PhotoImage is stashed on `owner` (e.g. the window/`self`) so Tk
    doesn't garbage-collect it and blank the logo. Returns the Label on
    success, or None if the image couldn't be loaded (a message is printed
    and the header simply renders without a logo).
    """
    try:
        img = Image.open(path or LOGO_PATH)
        ratio = height / img.height
        img = img.resize((int(img.width * ratio), height), Image.LANCZOS)

        photo = ImageTk.PhotoImage(img)
        owner._logo_photo = photo  # keep a reference on the window!

        import tkinter as tk
        label = tk.Label(header_frame, image=photo, bg=bg)
        label.pack(side=side, padx=padx, pady=pady)
        return label
    except Exception as exc:
        print(f"branding.add_logo: could not load logo: {exc}")
        return None


def has_logo(owner):
    """True if a logo was successfully attached to `owner`."""
    return getattr(owner, "_logo_photo", None) is not None