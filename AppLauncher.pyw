"""
Church Teachers College — Requisition Management System
Entry point. Run this file to start the application.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import sys
import os
from pathlib import Path

# ─────────────────────────────────────────────
#  PATHS
# ─────────────────────────────────────────────
BASE_DIR = Path(r"C:\Users\chris\AppData\Local\Programs\Python\Python314"
                r"\ChurchTeachersCollege\PythonApplication1")

SCREENS = {
    "login":        BASE_DIR / "Login.pyw",
    "admin":        BASE_DIR / "AdminScreen.pyw",
    "requisitions": BASE_DIR / "RequisitionScreen.pyw",
    "users":        BASE_DIR / "User.pyw",
}

# ─────────────────────────────────────────────
#  DESIGN TOKENS
# ─────────────────────────────────────────────
C_BG         = "#F7F3EE"
C_PANEL      = "#FFFFFF"
C_HEADER_BG  = "#1A2B4A"
C_HEADER_ACC = "#C8A96E"
C_PRIMARY    = "#2563EB"
C_PRIMARY_DK = "#1D4ED8"
C_BORDER     = "#D8D0C8"
C_TEXT       = "#1C1917"
C_TEXT_MUTED = "#78716C"
C_SUCCESS    = "#16A34A"
C_DANGER     = "#DC2626"

FONT_TITLE   = ("Georgia",  28, "bold")
FONT_SUB     = ("Georgia",  13, "italic")
FONT_SECTION = ("Georgia",  13, "bold")
FONT_LABEL   = ("Verdana",  11, "bold")
FONT_BODY    = ("Verdana",  10)
FONT_SMALL   = ("Verdana",   9)
FONT_BUTTON  = ("Verdana",  11, "bold")

# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────
def launch(path):
    """Launch a Python script as a non-blocking subprocess."""
    try:
        subprocess.Popen([sys.executable, str(path)])
    except FileNotFoundError:
        messagebox.showerror("Not Found", f"Could not find:\n{path}")


def make_button(parent, text, command, variant="primary", width=18):
    palette = {
        "primary": (C_PRIMARY,  C_PRIMARY_DK, "white"),
        "success": (C_SUCCESS,  "#15803D",    "white"),
        "danger":  (C_DANGER,   "#B91C1C",    "white"),
        "ghost":   (C_BORDER,   "#C0BAB2",    C_TEXT),
        "gold":    (C_HEADER_ACC, "#B8996E",  C_HEADER_BG),
    }
    bg, hover_bg, fg = palette.get(variant, palette["primary"])
    btn = tk.Button(
        parent, text=text, command=command,
        bg=bg, fg=fg, font=FONT_BUTTON,
        relief="flat", bd=0, padx=20, pady=12,
        width=width, cursor="hand2",
        activebackground=hover_bg, activeforeground=fg,
    )
    btn.bind("<Enter>", lambda e: btn.config(bg=hover_bg))
    btn.bind("<Leave>", lambda e: btn.config(bg=bg))
    return btn


# ─────────────────────────────────────────────
#  LAUNCHER APP
# ─────────────────────────────────────────────
class AppLauncher(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Church Teachers College — RMS")
        self.geometry("700x520")
        self.resizable(False, False)
        self.configure(bg=C_BG)

        self._build_ui()

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        self._build_header()
        self._build_body()
        self._build_footer()

    def _build_header(self):
        hdr = tk.Frame(self, bg=C_HEADER_BG)
        hdr.pack(fill="x")

        # Gold accent bar at very top
        tk.Frame(hdr, bg=C_HEADER_ACC, height=4).pack(fill="x")

        inner = tk.Frame(hdr, bg=C_HEADER_BG, pady=24)
        inner.pack(fill="x", padx=40)

        tk.Label(inner, text="Church Teachers College",
                 font=FONT_TITLE, bg=C_HEADER_BG, fg="white").pack(anchor="w")
        tk.Label(inner, text="Requisition Management System",
                 font=FONT_SUB, bg=C_HEADER_BG, fg=C_HEADER_ACC).pack(anchor="w")

        # Divider
        tk.Frame(hdr, bg=C_HEADER_ACC, height=2).pack(fill="x")

    def _build_body(self):
        body = tk.Frame(self, bg=C_BG)
        body.pack(fill="both", expand=True, padx=40, pady=30)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)

        # ── Left column — primary entry point
        left = tk.Frame(body, bg=C_BG)
        left.grid(row=0, column=0, sticky="NSEW", padx=(0, 16))

        tk.Label(left, text="Get Started",
                 font=FONT_SECTION, bg=C_BG, fg=C_HEADER_BG,
                 anchor="w").pack(fill="x", pady=(0, 8))
        tk.Frame(left, bg=C_HEADER_ACC, height=2).pack(fill="x", pady=(0, 16))

        # Login card
        login_card = tk.Frame(left, bg=C_PANEL,
                              highlightthickness=1,
                              highlightbackground=C_BORDER)
        login_card.pack(fill="x", pady=(0, 12))

        card_inner = tk.Frame(login_card, bg=C_PANEL, padx=16, pady=16)
        card_inner.pack(fill="x")

        tk.Label(card_inner, text="Sign In",
                 font=("Verdana", 12, "bold"),
                 bg=C_PANEL, fg=C_HEADER_BG).pack(anchor="w")
        tk.Label(card_inner,
                 text="Sign in to access your requisitions,\n"
                      "approvals and account settings.",
                 font=FONT_BODY, bg=C_PANEL, fg=C_TEXT_MUTED,
                 justify="left").pack(anchor="w", pady=(4, 12))
        make_button(card_inner, "Sign In",
                    lambda: self._launch_and_minimize("login"),
                    "gold", 16).pack(anchor="w")

        # ── Right column — quick access
        right = tk.Frame(body, bg=C_BG)
        right.grid(row=0, column=1, sticky="NSEW", padx=(16, 0))

        tk.Label(right, text="Quick Access",
                 font=FONT_SECTION, bg=C_BG, fg=C_HEADER_BG,
                 anchor="w").pack(fill="x", pady=(0, 8))
        tk.Frame(right, bg=C_HEADER_ACC, height=2).pack(fill="x", pady=(0, 16))

        quick_items = [
            ("Requisitions",  "View and manage requisitions",
             "requisitions", "primary"),
            ("Administration", "Users, keywords and settings",
             "admin",        "primary"),
            ("User Management", "Add or edit user accounts",
             "users",        "primary"),
        ]

        for label, desc, key, variant in quick_items:
            card = tk.Frame(right, bg=C_PANEL,
                            highlightthickness=1,
                            highlightbackground=C_BORDER)
            card.pack(fill="x", pady=(0, 8))

            card_inner = tk.Frame(card, bg=C_PANEL, padx=14, pady=10)
            card_inner.pack(fill="x")
            card_inner.columnconfigure(0, weight=1)

            tk.Label(card_inner, text=label,
                     font=("Verdana", 10, "bold"),
                     bg=C_PANEL, fg=C_HEADER_BG,
                     anchor="w").grid(row=0, column=0, sticky="w")
            tk.Label(card_inner, text=desc,
                     font=FONT_SMALL, bg=C_PANEL, fg=C_TEXT_MUTED,
                     anchor="w").grid(row=1, column=0, sticky="w", pady=(2, 4))
            tk.Button(
                card_inner, text="Open",
                command=lambda k=key: self._launch_and_minimize(k),
                bg=C_BG, fg=C_PRIMARY,
                font=("Verdana", 9, "bold"),
                relief="flat", bd=0, cursor="hand2",
                activebackground=C_BG, activeforeground=C_PRIMARY_DK,
            ).grid(row=0, column=1, rowspan=2, sticky="e")

        # ── Version / info strip
        info = tk.Frame(body, bg=C_BG)
        info.grid(row=1, column=0, columnspan=2, sticky="EW", pady=(16, 0))

        tk.Label(info,
                 text="Note: Quick Access screens open without requiring login. "
                      "Use Sign In for full access control.",
                 font=FONT_SMALL, bg=C_BG, fg=C_TEXT_MUTED,
                 wraplength=580, justify="left").pack(anchor="w")

    def _build_footer(self):
        tk.Frame(self, bg=C_BORDER, height=1).pack(fill="x")
        footer = tk.Frame(self, bg=C_PANEL, padx=40, pady=10)
        footer.pack(fill="x")
        footer.columnconfigure(0, weight=1)

        tk.Label(footer,
                 text="Church Teachers College  |  Requisition Management System  |  v1.0",
                 font=FONT_SMALL, bg=C_PANEL, fg=C_TEXT_MUTED).grid(
            row=0, column=0, sticky="w")

        make_button(footer, "Exit", self.destroy, "danger", 8).grid(
            row=0, column=1, sticky="e")

    # ── Actions ───────────────────────────────────────────────────────────────

    def _launch_and_minimize(self, key):
        path = SCREENS.get(key)
        if path and path.exists():
            launch(path)
            self.iconify()   # minimise launcher while app is open
        else:
            messagebox.showerror(
                "Not Found",
                f"Could not find screen file:\n{path}"
            )


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    app = AppLauncher()
    app.mainloop()
