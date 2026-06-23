import tkinter as tk
from tkinter import messagebox
import subprocess
import sys
import os
from pathlib import Path
import api_client
import appconfig
import applog

log = applog.get_logger("login")

# ─────────────────────────────────────────────
#  PATHS
# ─────────────────────────────────────────────
BASE_DIR   = Path(r"C:\Users\chris\AppData\Local\Programs\Python\Python314"
                  r"\ChurchTeachersCollege\PythonApplication1")
ASSETS_DIR = BASE_DIR / "assets"
ADMIN_SCREEN       = BASE_DIR / "AdminScreen.pyw"
REQUISITION_SCREEN = BASE_DIR / "RequisitionScreen.pyw"

# ─────────────────────────────────────────────
#  DESIGN TOKENS
# ─────────────────────────────────────────────
C_BG         = "#F7F3EE"
C_PANEL      = "#FFFFFF"
C_HEADER_BG  = "#1A2B4A"
C_HEADER_ACC = "#C8A96E"
C_PRIMARY    = "#2563EB"
C_PRIMARY_DK = "#1D4ED8"
C_DANGER     = "#DC2626"
C_BORDER     = "#D8D0C8"
C_TEXT       = "#1C1917"
C_TEXT_MUTED = "#78716C"

FONT_TITLE   = ("Georgia",  22, "bold")
FONT_LABEL   = ("Verdana",  11, "bold")
FONT_ENTRY   = ("Verdana",  11)
FONT_BUTTON  = ("Verdana",  11, "bold")
FONT_SMALL   = ("Verdana",   9)

# ─────────────────────────────────────────────
#  WIDGET FACTORIES
# ─────────────────────────────────────────────
def make_button(parent, text, command, variant="primary", width=12):
    palette = {
        "primary": (C_PRIMARY,  C_PRIMARY_DK, "white"),
        "danger":  (C_DANGER,   "#B91C1C",    "white"),
        "ghost":   (C_BORDER,   "#C0BAB2",    C_TEXT),
    }
    bg, hover_bg, fg = palette.get(variant, palette["primary"])
    btn = tk.Button(
        parent, text=text, command=command,
        bg=bg, fg=fg, font=FONT_BUTTON,
        relief="flat", bd=0, padx=18, pady=9,
        width=width, cursor="hand2",
        activebackground=hover_bg, activeforeground=fg,
    )
    btn.bind("<Enter>", lambda e: btn.config(bg=hover_bg))
    btn.bind("<Leave>", lambda e: btn.config(bg=bg))
    return btn


def launch(path, *args):
    """Launch a Python script as a non-blocking subprocess.

    Extra args are passed on the command line - used to hand the
    authenticated UserID to the screen being opened.
    """
    try:
        subprocess.Popen([sys.executable, str(path), *map(str, args)])
    except FileNotFoundError:
        messagebox.showerror("Not Found", f"Could not find:\n{path}")

# ─────────────────────────────────────────────
#  MAIN APPLICATION
# ─────────────────────────────────────────────
class LoginScreen(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Login")
        self.geometry("520x400")
        self.resizable(False, False)
        self.configure(bg=C_BG)

        self._target_screen = None   # set on successful login

        self._load_assets()
        self._build_ui()

        # Bind Enter key to login
        self.bind("<Return>", lambda e: self._login())

    # ── Asset loading ─────────────────────────────────────────────────────────

    def _load_assets(self):
        """Load icon images - gracefully skip if files are missing."""
        self._icon_img    = self._load_image("image.png",    subsample=2)
        self._user_img    = self._load_image("userIcon.png",     subsample=50)
        self._password_img = self._load_image("passwordIcon.png", subsample=10)

    def _load_image(self, filename, subsample=1):
        path = ASSETS_DIR / filename
        if not path.exists():
            return None
        try:
            img = tk.PhotoImage(file=str(path))
            if subsample > 1:
                img = img.subsample(subsample, subsample)
            return img
        except tk.TclError:
            return None

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        self._build_header()
        self._build_form()
        self._build_status_bar()

    def _build_header(self):
        hdr = tk.Frame(self, bg=C_HEADER_BG, height=80)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        # Logo icon
        if self._icon_img:
            tk.Label(hdr, image=self._icon_img,
                     bg=C_HEADER_BG).pack(side="left", padx=16, pady=10)

        text_frame = tk.Frame(hdr, bg=C_HEADER_BG)
        text_frame.pack(side="left", pady=10)

        tk.Label(text_frame, text=appconfig.active_config().display_name,
                 font=FONT_TITLE, bg=C_HEADER_BG, fg="white").pack(anchor="w")
        tk.Label(text_frame, text="Requisition Management System",
                 font=("Georgia", 11, "italic"),
                 bg=C_HEADER_BG, fg=C_HEADER_ACC).pack(anchor="w")

    def _build_form(self):
        # Outer card
        card = tk.Frame(self, bg=C_PANEL,
                        highlightthickness=1, highlightbackground=C_BORDER)
        card.pack(fill="both", expand=True, padx=40, pady=24)
        card.columnconfigure(1, weight=1)

        tk.Label(card, text="Sign in to your account",
                 font=("Georgia", 13, "bold"),
                 bg=C_PANEL, fg=C_HEADER_BG,
                 padx=20, pady=12).grid(row=0, column=0, columnspan=2, sticky="w")

        tk.Frame(card, bg=C_HEADER_ACC, height=2).grid(
            row=1, column=0, columnspan=2, sticky="EW", padx=20)

        # Username row
        user_row = tk.Frame(card, bg=C_PANEL)
        user_row.grid(row=2, column=0, columnspan=2, sticky="EW",
                      padx=20, pady=(16, 6))
        user_row.columnconfigure(1, weight=1)

        if self._user_img:
            tk.Label(user_row, image=self._user_img,
                     bg=C_PANEL).grid(row=0, column=0, padx=(0, 8))

        tk.Label(user_row, text="Username", font=FONT_LABEL,
                 bg=C_PANEL, fg=C_TEXT_MUTED,
                 width=10, anchor="w").grid(row=0, column=1, sticky="w")

        self.username_entry = tk.Entry(
            user_row, font=FONT_ENTRY, relief="flat", bd=4,
            bg="#F7F5F2", fg=C_TEXT, insertbackground=C_PRIMARY,
            highlightbackground=C_BORDER, highlightthickness=1,
        )
        self.username_entry.grid(row=0, column=2, sticky="ew", padx=(8, 0))
        self.username_entry.focus_set()

        # Password row
        pw_row = tk.Frame(card, bg=C_PANEL)
        pw_row.grid(row=3, column=0, columnspan=2, sticky="EW",
                    padx=20, pady=6)
        pw_row.columnconfigure(1, weight=1)

        if self._password_img:
            tk.Label(pw_row, image=self._password_img,
                     bg=C_PANEL).grid(row=0, column=0, padx=(0, 8))

        tk.Label(pw_row, text="Password", font=FONT_LABEL,
                 bg=C_PANEL, fg=C_TEXT_MUTED,
                 width=10, anchor="w").grid(row=0, column=1, sticky="w")

        self.password_entry = tk.Entry(
            pw_row, font=FONT_ENTRY, relief="flat", bd=4,
            bg="#F7F5F2", fg=C_TEXT, insertbackground=C_PRIMARY,
            highlightbackground=C_BORDER, highlightthickness=1,
            show="*",
        )
        self.password_entry.grid(row=0, column=2, sticky="ew", padx=(8, 0))

        # Button row
        btn_row = tk.Frame(card, bg=C_PANEL)
        btn_row.grid(row=4, column=0, columnspan=2, sticky="EW",
                     padx=20, pady=(16, 16))

        make_button(btn_row, "Sign In", self._login,  "primary", 12
                    ).pack(side="left", padx=(0, 8))
        make_button(btn_row, "Clear",   self._clear,  "ghost",   10
                    ).pack(side="left")

    def _build_status_bar(self):
        self.status_var = tk.StringVar(value="")
        bar = tk.Frame(self, bg=C_HEADER_BG, height=30)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)
        tk.Label(bar, textvariable=self.status_var,
                 font=FONT_SMALL, bg=C_HEADER_BG, fg="#94A3B8").pack(
            side="left", padx=16, pady=6)

    # ── Actions ───────────────────────────────────────────────────────────────

    def _login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()

        if not username or not password:
            messagebox.showwarning("Required", "Please enter your username and password.")
            return

        self.status_var.set("Signing in...")
        self.update()

        try:
            result = api_client.login(username, password, os_user=os.getlogin())
        except Exception as exc:
            log.error("login request failed for username=%r: %s", username, exc)
            messagebox.showerror("Connection Error",
                                 "Could not reach the server. Is the API running?")
            self.status_var.set("")
            return

        if result is None:
            log.info("login failed for username=%r", username)
            messagebox.showwarning("Login Failed", "Incorrect username or password.")
            self.password_entry.delete(0, "end")
            self.status_var.set("")
            return

        self.user_id = result["user_id"]
        self.auth_token = result["token"]
        self._target_screen = ADMIN_SCREEN if result["is_admin"] else REQUISITION_SCREEN
        log.info("login ok: user_id=%s admin=%s", self.user_id, result["is_admin"])
        self.status_var.set(f"Welcome, {result['full_name']}")
        self.after(300, self._open_main)

    def _open_main(self):
        target = self._target_screen or REQUISITION_SCREEN
        user_id = getattr(self, "user_id", None)
        token = getattr(self, "auth_token", None)
        # Publish the real signed token so the launched screen (and everything
        # it launches in turn) authenticates as this user. Each screen's _db
        # module reads CTC_AUTH_TOKEN from the environment.
        if token:
            os.environ["CTC_AUTH_TOKEN"] = token
        self.destroy()
        # The UserID is still passed on the command line as a dev-mode fallback;
        # when a real token is present, that's what actually authenticates.
        if user_id is not None:
            launch(target, user_id)
        else:
            launch(target)

    def _clear(self):
        self.username_entry.delete(0, "end")
        self.password_entry.delete(0, "end")
        self.username_entry.focus_set()
        self.status_var.set("")


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    # Resolve the active customer up front so a misconfiguration shows a clear
    # message instead of failing on the first query.
    try:
        appconfig.active_config()
    except appconfig.ConfigError as exc:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Configuration error", str(exc))
        root.destroy()
        sys.exit(1)
    app = LoginScreen()
    app.mainloop()
