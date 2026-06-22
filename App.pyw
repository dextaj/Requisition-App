"""
Church Teachers College — Requisition Management System
Single-process application. Run this file to start.
Package with: pyinstaller --onefile --windowed App.pyw
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog, font as tkfont
import pyodbc
import hashlib
import os
import re
import shutil
from datetime import date
from pathlib import Path

# ─────────────────────────────────────────────
#  DATABASE
# ─────────────────────────────────────────────
DB_CONN = (
    r"Driver=ODBC Driver 18 for SQL Server;"
    r"Server=Chris;"
    r"Database=ChurchTeachersCollegeDB;"
    r"Trusted_Connection=yes;"
    r"encrypt=Optional;"
)

def get_connection():
    return pyodbc.connect(DB_CONN)

# ─────────────────────────────────────────────
#  PATHS
# ─────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
ATTACHMENTS_FOLDER = os.path.join(
    os.environ.get("USERPROFILE", "C:\\"),
    "ChurchTeachersCollege", "Attachments"
)

# ─────────────────────────────────────────────
#  DESIGN TOKENS
# ─────────────────────────────────────────────
C_BG         = "#F7F3EE"
C_PANEL      = "#FFFFFF"
C_HEADER_BG  = "#1A2B4A"
C_HEADER_ACC = "#C8A96E"
C_PRIMARY    = "#2563EB"
C_PRIMARY_DK = "#1D4ED8"
C_SUCCESS    = "#16A34A"
C_DANGER     = "#DC2626"
C_BORDER     = "#D8D0C8"
C_TEXT       = "#1C1917"
C_TEXT_MUTED = "#78716C"
C_DONE       = "#15803D"
C_ACTIVE_BG  = "#EFF6FF"
C_ACTIVE_FG  = "#1D4ED8"
C_ACTIVE_BD  = "#3B82F6"
C_PENDING_BG = "#F5F5F4"
C_PENDING_FG = "#A8A29E"
C_PENDING_BD = "#D6D3D1"

FONT_TITLE   = ("Georgia",  22, "bold")
FONT_SECTION = ("Georgia",  13, "bold")
FONT_LABEL   = ("Verdana",  11, "bold")
FONT_ENTRY   = ("Verdana",  11)
FONT_BUTTON  = ("Verdana",  11, "bold")
FONT_SMALL   = ("Verdana",   9)
FONT_CAPTION = ("Verdana",  10)

# ─────────────────────────────────────────────
#  DATA LISTS
# ─────────────────────────────────────────────
SITE_LIST = ["", "Main campus", "Brownstown", "Farm"]
CATEGORY_LIST = ["", "Transport", "Infrastructure", "Household", "Kitchen", "Office Supplies"]
MAINTENANCE_LIST = ["Residential Facility", "Classroom/ Lecture Space", "Offices, Grounds"]
DEPT_LIST = [
    "IT", "Quality Assurance", "Kitchen", "Practicum", "Data Protection",
    "Research & Development", "Student Services", "Household", "Library",
    "Guidance & Counselling", "Assessment & Intervention", "Maintenance", "Academic",
]
ACADEMIC_LIST = [
    "Language & Literatures", "General Education & Professional Studies",
    "Technology", "Natural Sciences",
    "Inclusive Education & Childhood Studies", "Humanities",
]
DOC_PREFIXES = {
    "Transport":      "TRAN-",
    "Infrastructure": "INFR-",
    "Household":      "HSLD-",
    "Kitchen":        "KTCN-",
}

# ─────────────────────────────────────────────
#  PHASES
# ─────────────────────────────────────────────
PHASES_STANDARD    = ["Draft", "HOD Review", "VP Review", "Principal Approval", "Procurement", "Accounts"]
PHASES_MAINTENANCE = ["Draft", "HOD Review", "VP Review", "Maintenance Unit",
                      "VP Approval", "Principal Approval", "Procurement", "Accounts"]
PHASES_TRANSPORT   = ["Draft", "HOD Review", "VP Approval", "Accounts"]

def get_phases(category, via_maintenance=False):
    if category == "Transport":
        return PHASES_TRANSPORT
    if via_maintenance:
        return PHASES_MAINTENANCE
    return PHASES_STANDARD

# ─────────────────────────────────────────────
#  WIDGET FACTORIES
# ─────────────────────────────────────────────
def make_button(parent, text, command, variant="primary", width=12):
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
        relief="flat", bd=0, padx=18, pady=9,
        width=width, cursor="hand2",
        activebackground=hover_bg, activeforeground=fg,
    )
    btn.bind("<Enter>", lambda e: btn.config(bg=hover_bg))
    btn.bind("<Leave>", lambda e: btn.config(bg=bg))
    return btn


def make_label(parent, text, f=FONT_LABEL, fg=C_TEXT, bg=C_PANEL, **kw):
    return tk.Label(parent, text=text, font=f, fg=fg, bg=bg, **kw)


def make_combo(parent, values, textvariable=None, width=15, state="readonly"):
    opts = dict(master=parent, values=values, state=state,
                font=FONT_ENTRY, width=width)
    if textvariable:
        opts["textvariable"] = textvariable
    return ttk.Combobox(**opts)


def make_scrolled(parent, height=4):
    return scrolledtext.ScrolledText(
        parent, font=FONT_ENTRY, height=height,
        relief="flat", bd=0, bg="#FAFAF9", fg=C_TEXT,
    )


def st_get(widget):
    try:
        return widget.get("1.0", "end-1c")
    except TypeError:
        return widget.get()
    except tk.TclError:
        return ""


def st_set(widget, value):
    try:
        widget.delete("1.0", "end")
        widget.insert("1.0", value or "")
    except TypeError:
        widget.delete(0, "end")
        widget.insert(0, value or "")
    except tk.TclError:
        pass


def card(parent, title, row=0, col=0, padx=16, pady=10, colspan=1):
    outer = tk.Frame(parent, bg=C_PANEL, bd=0,
                     highlightbackground=C_BORDER, highlightthickness=1)
    outer.grid(row=row, column=col, columnspan=colspan,
               padx=padx, pady=pady, sticky="nsew")
    outer.columnconfigure(0, weight=1)
    if title:
        tk.Label(outer, text=title, font=FONT_SECTION,
                 bg=C_PANEL, fg=C_HEADER_BG,
                 anchor="w", padx=14, pady=8).pack(fill="x")
        tk.Frame(outer, bg=C_HEADER_ACC, height=2).pack(fill="x", padx=14)
    inner = tk.Frame(outer, bg=C_PANEL, padx=14, pady=10)
    inner.pack(fill="both", expand=True)
    inner.columnconfigure(0, weight=1)
    return outer, inner

# ─────────────────────────────────────────────
#  SHARED HELPERS
# ─────────────────────────────────────────────
def verify_password(plain, stored_hash):
    plain = (plain or "").strip()
    stored_hash_s = stored_hash.strip() if isinstance(stored_hash, str) else stored_hash
    try:
        import bcrypt
        stored_bytes = stored_hash.encode() if isinstance(stored_hash, str) else stored_hash
        return bcrypt.checkpw(plain.encode(), stored_bytes)
    except (ImportError, ValueError):
        pass
    if hashlib.sha256(plain.encode()).hexdigest() == stored_hash_s:
        return True
    return plain == stored_hash_s


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def register_logon(user_id, user_name):
    os_user = os.getlogin()
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT Logon_ID FROM Administration.LogOnUser WHERE OSuser = ?",
                (os_user,)
            )
            if cursor.fetchone():
                cursor.execute(
                    "UPDATE Administration.LogOnUser "
                    "SET UserID=?, UserName=?, DocNumber=NULL WHERE OSuser=?",
                    (user_id, user_name, os_user)
                )
            else:
                cursor.execute(
                    "INSERT INTO Administration.LogOnUser "
                    "(UserID, UserName, OSuser, DocNumber) VALUES (?, ?, ?, NULL)",
                    (user_id, user_name, os_user)
                )
            conn.commit()
    except pyodbc.Error as exc:
        print(f"register_logon error: {exc}")


def log_history(cursor, doc_number, phase, action, action_by,
                assigned_to="", comments=""):
    cursor.execute(
        "INSERT INTO REQUISITION.REQUISITION_HISTORY "
        "(Document_Number, Phase, Action, Action_Date, "
        "Action_By, Assigned_To, Comments) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (doc_number, phase, action, str(date.today()),
         action_by, assigned_to, comments)
    )


def build_phase_tracker(parent, current_phase, category="", via_maintenance=False):
    for w in parent.winfo_children():
        w.destroy()
    phases = get_phases(category, via_maintenance)
    idx = phases.index(current_phase) if current_phase in phases else 0
    outer = tk.Frame(parent, bg=C_PANEL, pady=12)
    outer.pack(fill="x", padx=20)
    for i, phase in enumerate(phases):
        col = i * 2
        if i < idx:
            bg, fg, border, symbol = C_DONE, "white", C_DONE, "+"
        elif i == idx:
            bg, fg, border, symbol = C_ACTIVE_BG, C_ACTIVE_FG, C_ACTIVE_BD, str(i+1)
        else:
            bg, fg, border, symbol = C_PENDING_BG, C_PENDING_FG, C_PENDING_BD, str(i+1)
        c = tk.Canvas(outer, width=38, height=38, bg=C_PANEL, highlightthickness=0)
        c.grid(row=0, column=col, padx=2)
        c.create_oval(2, 2, 36, 36, fill=bg, outline=border, width=2)
        c.create_text(19, 19, text=symbol, fill=fg, font=("Verdana", 11, "bold"))
        lbl_fg = C_DONE if i < idx else C_ACTIVE_FG if i == idx else C_PENDING_FG
        tk.Label(outer, text=phase, bg=C_PANEL, fg=lbl_fg,
                 font=FONT_SMALL, wraplength=72, justify="center").grid(row=1, column=col)
        if i < len(phases) - 1:
            line_color = C_DONE if i < idx else C_PENDING_BD
            tk.Frame(outer, bg=line_color, height=2, width=44).grid(
                row=0, column=col+1, sticky="EW")


def generate_doc_number(category):
    prefix = DOC_PREFIXES.get(category, "OFFS-") if category else ""
    if not prefix:
        return ""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT MAX(Document_Number) FROM REQUISITION.REQUISITION_TABLE "
                "WHERE Document_Number LIKE ?", (f"%{prefix}%",))
            row = cursor.fetchone()
            counter = 0
            if row and row[0]:
                nums = re.findall(r"\d+", row[0])
                counter = int(nums[-1]) if nums else 0
        return f"{prefix}{counter + 1:05d}"
    except pyodbc.Error as exc:
        print(f"generate_doc_number error: {exc}")
        return ""


def fetch_users():
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT FirstName, LastName FROM Administration.Users")
            return [f"{r[0]} {r[1]}" for r in cursor.fetchall()]
    except pyodbc.Error as exc:
        print(f"fetch_users error: {exc}")
        return []


# ─────────────────────────────────────────────
#  BASE SCREEN  (all screens inherit this)
# ─────────────────────────────────────────────
class BaseScreen(tk.Frame):
    """
    All screens are Frames. They receive a reference to the App
    so they can call self.app.show(ScreenClass) to navigate.
    """
    def __init__(self, parent, app):
        super().__init__(parent, bg=C_BG)
        self.app = app
        self.grid(row=0, column=0, sticky="NSEW")

    def on_show(self):
        """Called every time this screen is raised. Override to refresh data."""
        pass


# ═════════════════════════════════════════════
#  SCREEN 1 — LOGIN
# ═════════════════════════════════════════════
class LoginScreen(BaseScreen):

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self._build_ui()
        app.bind("<Return>", lambda e: self._login())

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        center = tk.Frame(self, bg=C_BG)
        center.place(relx=0.5, rely=0.5, anchor="center")

        # Header card
        hdr = tk.Frame(center, bg=C_HEADER_BG, width=460)
        hdr.pack(fill="x")
        tk.Frame(hdr, bg=C_HEADER_ACC, height=4).pack(fill="x")
        inner_hdr = tk.Frame(hdr, bg=C_HEADER_BG, pady=20)
        inner_hdr.pack(fill="x", padx=30)
        tk.Label(inner_hdr, text="Church Teachers College",
                 font=FONT_TITLE, bg=C_HEADER_BG, fg="white").pack(anchor="w")
        tk.Label(inner_hdr, text="Requisition Management System",
                 font=("Georgia", 11, "italic"),
                 bg=C_HEADER_BG, fg=C_HEADER_ACC).pack(anchor="w")

        # Form card
        form_card = tk.Frame(center, bg=C_PANEL, width=460,
                             highlightthickness=1, highlightbackground=C_BORDER)
        form_card.pack(fill="x")
        form = tk.Frame(form_card, bg=C_PANEL, padx=30, pady=24)
        form.pack(fill="x")
        form.columnconfigure(1, weight=1)

        tk.Label(form, text="Sign in to your account",
                 font=FONT_SECTION, bg=C_PANEL, fg=C_HEADER_BG).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 16))

        make_label(form, "Username", bg=C_PANEL).grid(
            row=1, column=0, sticky="e", padx=(0, 10), pady=8)
        self.username_entry = tk.Entry(
            form, font=FONT_ENTRY, relief="flat", bd=4,
            bg="#F7F5F2", fg=C_TEXT, highlightbackground=C_BORDER,
            highlightthickness=1, width=28)
        self.username_entry.grid(row=1, column=1, sticky="ew", pady=8)
        self.username_entry.focus_set()

        make_label(form, "Password", bg=C_PANEL).grid(
            row=2, column=0, sticky="e", padx=(0, 10), pady=8)
        self.password_entry = tk.Entry(
            form, font=FONT_ENTRY, relief="flat", bd=4,
            bg="#F7F5F2", fg=C_TEXT, highlightbackground=C_BORDER,
            highlightthickness=1, width=28, show="*")
        self.password_entry.grid(row=2, column=1, sticky="ew", pady=8)

        btn_row = tk.Frame(form, bg=C_PANEL)
        btn_row.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(16, 0))
        make_button(btn_row, "Sign In", self._login, "gold", 12).pack(side="left")
        make_button(btn_row, "Clear",   self._clear, "ghost", 10).pack(side="left", padx=8)

        # Status
        self.status_var = tk.StringVar()
        tk.Label(form_card, textvariable=self.status_var,
                 font=FONT_SMALL, bg=C_PANEL, fg=C_DANGER).pack(pady=(0, 8))

    def _login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        if not username or not password:
            self.status_var.set("Please enter your username and password.")
            return
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT UserID, FirstName, LastName, UserName, Password_hash "
                    "FROM Administration.Users WHERE UserName = ?", (username,))
                result = cursor.fetchone()
        except pyodbc.Error as exc:
            messagebox.showerror("Database Error", str(exc))
            return

        if result is None or not verify_password(password, result[4]):
            self.status_var.set("Incorrect username or password.")
            self.password_entry.delete(0, "end")
            return

        user_id, first, last = result[0], result[1], result[2]
        full_name = f"{first} {last}"
        register_logon(user_id, full_name)

        # Store session on app
        self.app.current_user_id   = user_id
        self.app.current_user_name = full_name

        self.status_var.set("")
        self._clear()
        self.app.show(HomeScreen)

    def _clear(self):
        self.username_entry.delete(0, "end")
        self.password_entry.delete(0, "end")
        self.status_var.set("")
        self.username_entry.focus_set()


# ═════════════════════════════════════════════
#  SCREEN 2 — HOME / LAUNCHER
# ═════════════════════════════════════════════
class HomeScreen(BaseScreen):

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self._build_ui()

    def on_show(self):
        self.user_label.config(
            text=f"Welcome, {self.app.current_user_name}")

    def _build_ui(self):
        self._build_header()
        body = tk.Frame(self, bg=C_BG)
        body.pack(fill="both", expand=True, padx=40, pady=30)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)
        self._build_nav(body)
        self._build_footer()

    def _build_header(self):
        hdr = tk.Frame(self, bg=C_HEADER_BG)
        hdr.pack(fill="x")
        tk.Frame(hdr, bg=C_HEADER_ACC, height=4).pack(fill="x")
        inner = tk.Frame(hdr, bg=C_HEADER_BG, pady=16)
        inner.pack(fill="x", padx=24)
        inner.columnconfigure(1, weight=1)
        tk.Label(inner, text="Church Teachers College",
                 font=FONT_TITLE, bg=C_HEADER_BG, fg="white").grid(
            row=0, column=0, sticky="w")
        tk.Label(inner, text="Requisition Management System",
                 font=("Georgia", 11, "italic"),
                 bg=C_HEADER_BG, fg=C_HEADER_ACC).grid(row=1, column=0, sticky="w")
        self.user_label = tk.Label(inner, text="", font=FONT_SMALL,
                                   bg=C_HEADER_BG, fg="#94A3B8")
        self.user_label.grid(row=0, column=1, sticky="e")

    def _build_nav(self, body):
        modules = [
            ("Requisitions",   "Create, view and manage requisitions.",
             RequisitionListScreen, "primary", 0, 0),
            ("Administration", "Manage users, keywords and settings.",
             AdminScreen,           "primary", 0, 1),
        ]
        for label, desc, screen, variant, r, c in modules:
            card_frame = tk.Frame(body, bg=C_PANEL,
                                  highlightthickness=1,
                                  highlightbackground=C_BORDER)
            card_frame.grid(row=r, column=c, sticky="NSEW",
                            padx=8, pady=8)
            inner = tk.Frame(card_frame, bg=C_PANEL, padx=20, pady=20)
            inner.pack(fill="both", expand=True)
            tk.Label(inner, text=label, font=("Georgia", 16, "bold"),
                     bg=C_PANEL, fg=C_HEADER_BG).pack(anchor="w")
            tk.Frame(inner, bg=C_HEADER_ACC, height=2).pack(fill="x", pady=8)
            tk.Label(inner, text=desc, font=FONT_BODY if hasattr(self, 'FONT_BODY')
                     else FONT_CAPTION,
                     bg=C_PANEL, fg=C_TEXT_MUTED, wraplength=240,
                     justify="left").pack(anchor="w", pady=(0, 16))
            make_button(inner, f"Open {label}",
                        lambda s=screen: self.app.show(s),
                        variant, 16).pack(anchor="w")

    def _build_footer(self):
        tk.Frame(self, bg=C_BORDER, height=1).pack(fill="x")
        footer = tk.Frame(self, bg=C_PANEL, padx=24, pady=10)
        footer.pack(fill="x")
        footer.columnconfigure(0, weight=1)
        tk.Label(footer, text="Church Teachers College  |  RMS v1.0",
                 font=FONT_SMALL, bg=C_PANEL, fg=C_TEXT_MUTED).grid(
            row=0, column=0, sticky="w")
        make_button(footer, "Sign Out",
                    lambda: self.app.show(LoginScreen),
                    "danger", 10).grid(row=0, column=1, sticky="e")


# ═════════════════════════════════════════════
#  SCREEN 3 — REQUISITION LIST
# ═════════════════════════════════════════════
class RequisitionListScreen(BaseScreen):

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self._all_rows = []
        self.view_all  = False
        self._build_ui()

    def on_show(self):
        self._load_data()

    def _build_ui(self):
        self._build_header()
        self._build_stats()
        self._build_toolbar()
        self._build_table()
        self._build_footer()
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)

    def _build_header(self):
        hdr = tk.Frame(self, bg=C_HEADER_BG, height=60)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="Requisitions", font=FONT_TITLE,
                 bg=C_HEADER_BG, fg="white").pack(side="left", padx=24, pady=10)
        make_button(hdr, "Home",
                    lambda: self.app.show(HomeScreen),
                    "ghost", 8).pack(side="right", padx=16, pady=10)

    def _build_stats(self):
        bar = tk.Frame(self, bg="#f0eeea",
                       highlightthickness=1, highlightbackground="#ddddd5")
        bar.pack(fill="x")
        self.stat_open    = self._stat_cell(bar, "0", "My open",       0)
        self.stat_pending = self._stat_cell(bar, "0", "Pending",        1)
        self.stat_total   = self._stat_cell(bar, "0", "Total this month", 2)
        bar.columnconfigure(0, weight=1)
        bar.columnconfigure(1, weight=1)
        bar.columnconfigure(2, weight=1)

    def _stat_cell(self, parent, val, label, col):
        cell = tk.Frame(parent, bg="#ffffff",
                        highlightthickness=1, highlightbackground="#e0deda")
        cell.grid(row=0, column=col, sticky="NSEW",
                  padx=(0 if col == 0 else 1, 0))
        v = tk.Label(cell, text=val, bg="#ffffff",
                     font=("Segoe UI", 20, "bold"), fg="#1a1a1a",
                     pady=6, padx=14)
        v.grid(row=0, column=0, sticky="W")
        tk.Label(cell, text=label, bg="#ffffff",
                 font=("Segoe UI", 10), fg="#888780",
                 padx=14, pady=0).grid(row=1, column=0, sticky="W")
        tk.Frame(cell, bg="#ffffff", height=8).grid(row=2, column=0)
        return v

    def _build_toolbar(self):
        bar = tk.Frame(self, bg="#ffffff",
                       highlightthickness=1, highlightbackground="#ddddd5")
        bar.pack(fill="x")
        make_button(bar, "+ New Requisition",
                    self._new_requisition, "primary", 16).pack(
            side="left", padx=10, pady=8)

        self.toggle_mine = tk.Button(
            bar, text="Mine", command=lambda: self._set_view(False),
            bg="#1e40af", fg="#ffffff", font=("Segoe UI", 10, "bold"),
            relief="flat", bd=0, padx=12, pady=5, cursor="hand2")
        self.toggle_mine.pack(side="left", pady=8)

        self.toggle_all = tk.Button(
            bar, text="All", command=lambda: self._set_view(True),
            bg="#f0eeea", fg="#555550", font=("Segoe UI", 10),
            relief="flat", bd=0, padx=12, pady=5, cursor="hand2")
        self.toggle_all.pack(side="left", pady=8)

        tk.Frame(bar, bg="#ffffff").pack(side="left", fill="x", expand=True)

        tk.Label(bar, text="Search:", bg="#ffffff",
                 font=("Segoe UI", 10), fg="#888780").pack(
            side="left", padx=(0, 4), pady=8)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._on_search)
        se = tk.Entry(bar, textvariable=self.search_var,
                      font=("Segoe UI", 11), relief="solid", bd=1,
                      width=24, fg="#1a1a1a", bg="#ffffff")
        se.pack(side="left", padx=(0, 10), pady=8, ipady=4)

    def _build_table(self):
        frame = tk.Frame(self, bg="#ffffff",
                         highlightthickness=1, highlightbackground="#ddddd5")
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        cols = ("doc_number", "site", "category", "department", "description", "phase")
        self.tree = ttk.Treeview(frame, columns=cols,
                                 show="headings", selectmode="browse")
        col_cfg = [
            ("doc_number",  "Doc #",       100, tk.W,      False),
            ("site",        "Site",        130, tk.W,      False),
            ("category",    "Category",    120, tk.W,      False),
            ("department",  "Department",  130, tk.W,      False),
            ("description", "Description", 0,   tk.W,      True),
            ("phase",       "Phase",       110, tk.CENTER, False),
        ]
        for col_id, heading, width, anchor, stretch in col_cfg:
            self.tree.heading(col_id, text=heading)
            if width:
                self.tree.column(col_id, width=width, anchor=anchor, stretch=stretch)
            else:
                self.tree.column(col_id, anchor=anchor, stretch=True)

        self.tree.tag_configure("draft",    foreground="#92400e", background="#fffbeb")
        self.tree.tag_configure("review",   foreground="#1e3a8a", background="#eff6ff")
        self.tree.tag_configure("approved", foreground="#14532d", background="#f0fdf4")
        self.tree.tag_configure("closed",   foreground="#6b7280", background="#f9fafb")

        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="NSEW")
        vsb.grid(row=0, column=1, sticky="NS")
        hsb.grid(row=1, column=0, sticky="EW")
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

    def _build_footer(self):
        footer = tk.Frame(self, bg="#ffffff",
                          highlightthickness=1, highlightbackground="#ddddd5")
        footer.pack(fill="x")
        footer.columnconfigure(0, weight=1)
        self.count_label = tk.Label(footer, text="", bg="#ffffff",
                                    font=("Segoe UI", 10), fg="#888780",
                                    padx=14, pady=8)
        self.count_label.grid(row=0, column=0, sticky="W")

    def _load_data(self):
        user_name = self.app.current_user_name
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                if self.view_all:
                    cursor.execute("SELECT * FROM REQUISITION.REQUISITION_TABLE")
                else:
                    cursor.execute(
                        "SELECT * FROM REQUISITION.REQUISITION_TABLE "
                        "WHERE Assign_To = ?", (user_name,))
                self._all_rows = cursor.fetchall()

                # Stats
                cursor.execute(
                    "SELECT COUNT(*) FROM REQUISITION.REQUISITION_TABLE "
                    "WHERE Assign_To = ? AND Phase != 'Accounts'", (user_name,))
                open_count = cursor.fetchone()[0]
                cursor.execute(
                    "SELECT COUNT(*) FROM REQUISITION.REQUISITION_TABLE "
                    "WHERE Assign_To = ? AND Phase = 'Draft'", (user_name,))
                pending = cursor.fetchone()[0]
                cursor.execute(
                    "SELECT COUNT(*) FROM REQUISITION.REQUISITION_TABLE "
                    "WHERE MONTH(Submit_Date)=MONTH(GETDATE()) "
                    "AND YEAR(Submit_Date)=YEAR(GETDATE())")
                total = cursor.fetchone()[0]
        except pyodbc.Error as exc:
            print(f"RequisitionListScreen load error: {exc}")
            self._all_rows = []
            open_count = pending = total = 0

        self.stat_open.config(text=str(open_count))
        self.stat_pending.config(text=str(pending))
        self.stat_total.config(text=str(total))
        self._refresh_table(self._all_rows)

    def _refresh_table(self, rows):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for row in rows:
            doc  = row[2]  if len(row) > 2  else ""
            site = row[3]  if len(row) > 3  else ""
            cat  = row[4]  if len(row) > 4  else ""
            dept = row[6]  if len(row) > 6  else ""
            desc = row[15] if len(row) > 15 else ""
            phase = row[10] if len(row) > 10 else ""
            tag = self._phase_tag(phase)
            self.tree.insert("", "end", iid=str(row[0]),
                             values=(doc, site, cat, dept, desc, phase),
                             tags=(tag,))
        count = len(rows)
        self.count_label.config(
            text=f"{count} requisition{'s' if count != 1 else ''} shown")

    def _phase_tag(self, phase):
        if not phase: return ""
        p = phase.strip().lower()
        if p == "draft": return "draft"
        if p in ("hod review", "vp review"): return "review"
        if p in ("vp approval", "principal approval",
                 "procurement", "maintenance unit"): return "approved"
        if p == "accounts": return "closed"
        return ""

    def _set_view(self, all_reqs):
        self.view_all = all_reqs
        if all_reqs:
            self.toggle_all.config(bg="#1e40af", fg="#ffffff",
                                   font=("Segoe UI", 10, "bold"))
            self.toggle_mine.config(bg="#f0eeea", fg="#555550",
                                    font=("Segoe UI", 10))
        else:
            self.toggle_mine.config(bg="#1e40af", fg="#ffffff",
                                    font=("Segoe UI", 10, "bold"))
            self.toggle_all.config(bg="#f0eeea", fg="#555550",
                                   font=("Segoe UI", 10))
        self._load_data()

    def _on_search(self, *_):
        if not hasattr(self, "tree"): return
        term = self.search_var.get().strip().lower()
        if not term:
            self._refresh_table(self._all_rows)
            return
        filtered = [r for r in self._all_rows
                    if any(term in str(cell).lower() for cell in r)]
        self._refresh_table(filtered)

    def _on_select(self, _event):
        selected = self.tree.focus()
        if not selected: return
        values = self.tree.item(selected, "values")
        if not values: return
        doc_number = values[0]
        # Store selected doc on app then navigate to form
        self.app.selected_doc_number = doc_number
        self.app.show(RequisitionFormScreen)

    def _new_requisition(self):
        self.app.selected_doc_number = None
        self.app.show(RequisitionFormScreen)


# ═════════════════════════════════════════════
#  SCREEN 4 — REQUISITION FORM
# ═════════════════════════════════════════════
class RequisitionFormScreen(BaseScreen):

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.today         = date.today()
        self.current_phase = ""
        self.assigned_to   = ""

        # StringVars
        self.doc_var         = tk.StringVar()
        self.mvar            = tk.BooleanVar()
        self.request_option  = tk.StringVar(value="Material Only")
        self.site_var        = tk.StringVar(value="")
        self.category_var    = tk.StringVar(value="")
        self.maintenance_var = tk.StringVar(value=MAINTENANCE_LIST[0])
        self.dept_var        = tk.StringVar(value=DEPT_LIST[0])
        self.academic_var    = tk.StringVar(value=ACADEMIC_LIST[0])
        self.status_var      = tk.StringVar(value="Ready")

        self._build_ui()

    def on_show(self):
        self._reset_form()
        doc_number = self.app.selected_doc_number
        if doc_number:
            self._load_document(doc_number)
        else:
            self._reload_phase_from_db()

    def _reset_form(self):
        self.current_phase = ""
        self.assigned_to   = ""
        self.doc_var.set("")
        self.mvar.set(False)
        self.request_option.set("Material Only")
        self.site_var.set("")
        self.category_var.set("")
        self.maintenance_var.set(MAINTENANCE_LIST[0])
        self.dept_var.set(DEPT_LIST[0])
        self.academic_var.set(ACADEMIC_LIST[0])
        self.status_var.set("Ready")

        for entry in (self.createdBy_entry, self.supplierEntry, self.purposeEntry,
                      self.contractorEntry):
            entry.delete(0, "end")
        for st in (self.requestingText, self.HODcomment_entry, self.vpReviewerText,
                   self.scopeText, self.materialText, self.vpApproverText,
                   self.principalText):
            st_set(st, "")

        self.maintenance_label.grid_remove()
        self.maintenance_entry.grid_remove()
        self.academic_label.grid_remove()
        self.academic_entry.grid_remove()

    def _load_document(self, doc_number):
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM REQUISITION.REQUISITION_TABLE "
                    "WHERE Document_Number = ?", (doc_number,))
                row = cursor.fetchone()
        except pyodbc.Error as exc:
            messagebox.showerror("Error", str(exc))
            return
        if row:
            self._populate_fields(row)
        self._reload_phase_from_db()

    def _build_ui(self):
        # Header
        hdr = tk.Frame(self, bg=C_HEADER_BG, height=60)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="Requisition", font=FONT_TITLE,
                 bg=C_HEADER_BG, fg="white").pack(side="left", padx=24, pady=10)
        make_button(hdr, "Back to List",
                    lambda: self.app.show(RequisitionListScreen),
                    "ghost", 12).pack(side="right", padx=16, pady=10)

        # Phase tracker band
        self.process_frame = tk.Frame(self, bg=C_PANEL)
        self.process_frame.pack(fill="x")
        tk.Frame(self, bg=C_BORDER, height=1).pack(fill="x")

        # Notebook
        body = tk.Frame(self, bg=C_BG)
        body.pack(fill="both", expand=True)
        self.notebook = ttk.Notebook(body)
        self.tab1 = ttk.Frame(self.notebook)
        self.tab2 = ttk.Frame(self.notebook)
        self.tab3 = ttk.Frame(self.notebook)
        self.notebook.add(self.tab1, text="  Requisition Request  ")
        self.notebook.add(self.tab3, text="  Approval History  ")
        self.notebook.pack(fill="both", expand=True)

        self._build_tab1()
        self._build_tab2()
        self._build_tab3()

        # Button bar
        tk.Frame(self, bg=C_BORDER, height=1).pack(fill="x")
        bar = tk.Frame(self, bg=C_PANEL, padx=20, pady=12)
        bar.pack(fill="x")
        make_button(bar, "Back",   lambda: self.app.show(RequisitionListScreen),
                    "ghost",   10).pack(side="right", padx=6)
        make_button(bar, "Submit", self._open_submit_window,
                    "success", 10).pack(side="right", padx=6)
        make_button(bar, "Save",   self._save_draft,
                    "primary", 10).pack(side="right", padx=6)

        # Status bar
        sbar = tk.Frame(self, bg=C_HEADER_BG, height=32)
        sbar.pack(fill="x")
        sbar.pack_propagate(False)
        tk.Label(sbar, textvariable=self.status_var,
                 font=("Verdana", 9), bg=C_HEADER_BG, fg="#94A3B8").pack(
            side="left", padx=16, pady=6)

    def _build_scrollable_tab(self, tab):
        canvas = tk.Canvas(tab, bg=C_BG, highlightthickness=0)
        vsb = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        frame = tk.Frame(canvas, bg=C_BG)
        frame.columnconfigure(0, weight=1)
        win_id = canvas.create_window((0, 0), window=frame, anchor="nw")
        def on_resize(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(win_id, width=event.width)
        frame.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", on_resize)
        canvas.configure(yscrollcommand=vsb.set)
        canvas.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        return frame

    def _build_tab1(self):
        sf = self._build_scrollable_tab(self.tab1)
        self.details_outer, info = card(sf, "Requisition Details", row=0, col=0, pady=16)
        info.columnconfigure(1, weight=1)
        info.columnconfigure(3, weight=1)
        info.columnconfigure(5, weight=1)

        make_label(info, "Number", bg=C_PANEL).grid(row=0, column=0, sticky="e", padx=(0,6), pady=6)
        self.docNumber_entry = tk.Entry(info, textvariable=self.doc_var, font=FONT_ENTRY,
                                        state="readonly", bg="#F0F0F0", relief="flat", bd=4, width=16)
        self.docNumber_entry.grid(row=0, column=1, sticky="ew", pady=6)

        make_label(info, "Created By", bg=C_PANEL).grid(row=0, column=2, sticky="e", padx=(12,6), pady=6)
        self.createdBy_entry = tk.Entry(info, font=FONT_ENTRY, relief="flat", bd=4,
                                         bg=C_PANEL, fg=C_TEXT, width=22,
                                         highlightbackground=C_BORDER, highlightthickness=1)
        self.createdBy_entry.grid(row=0, column=3, sticky="ew", pady=6)

        make_label(info, "Site", bg=C_PANEL).grid(row=0, column=4, sticky="e", padx=(12,6), pady=6)
        self.site_entry = make_combo(info, SITE_LIST, self.site_var, width=16)
        self.site_entry.grid(row=0, column=5, sticky="ew", pady=6)

        make_label(info, "Category", bg=C_PANEL).grid(row=1, column=0, sticky="e", padx=(0,6), pady=6)
        self.category_entry = make_combo(info, CATEGORY_LIST, self.category_var, width=14)
        self.category_entry.grid(row=1, column=1, sticky="ew", pady=6)
        self.category_entry.bind("<<ComboboxSelected>>", self._on_category_selected)

        make_label(info, "Dept & Units", bg=C_PANEL).grid(row=1, column=2, sticky="e", padx=(12,6), pady=6)
        self.dept_entry = make_combo(info, DEPT_LIST, self.dept_var, width=14)
        self.dept_entry.grid(row=1, column=3, sticky="ew", pady=6)
        self.dept_entry.bind("<<ComboboxSelected>>", self._on_department_selected)

        self.maintenance_label = make_label(info, "Maintenance Area", bg=C_PANEL)
        self.maintenance_label.grid(row=1, column=4, sticky="e", padx=(12,6), pady=6)
        self.maintenance_entry = make_combo(info, MAINTENANCE_LIST, self.maintenance_var, width=18)
        self.maintenance_entry.grid(row=1, column=5, sticky="ew", pady=6)
        self.maintenance_label.grid_remove()
        self.maintenance_entry.grid_remove()

        self.academic_label = make_label(info, "Academic Department", bg=C_PANEL)
        self.academic_label.grid(row=2, column=0, sticky="e", padx=(0,6), pady=6)
        self.academic_entry = make_combo(info, ACADEMIC_LIST, self.academic_var, width=36)
        self.academic_entry.grid(row=2, column=1, columnspan=3, sticky="ew", pady=6)
        self.academic_label.grid_remove()
        self.academic_entry.grid_remove()

        make_label(info, "Purchased At", bg=C_PANEL).grid(row=3, column=0, sticky="e", padx=(0,6), pady=6)
        self.supplierEntry = tk.Entry(info, font=FONT_ENTRY, relief="flat", bd=4,
                                       bg=C_PANEL, fg=C_TEXT,
                                       highlightbackground=C_BORDER, highlightthickness=1)
        self.supplierEntry.grid(row=3, column=1, columnspan=3, sticky="ew", pady=6)

        make_label(info, "Purpose", bg=C_PANEL).grid(row=4, column=0, sticky="e", padx=(0,6), pady=6)
        self.purposeEntry = tk.Entry(info, font=FONT_ENTRY, relief="flat", bd=4,
                                      bg=C_PANEL, fg=C_TEXT,
                                      highlightbackground=C_BORDER, highlightthickness=1)
        self.purposeEntry.grid(row=4, column=1, columnspan=3, sticky="ew", pady=6)

        self.mcheck = tk.Checkbutton(info, text="Route through Maintenance Unit",
                                      variable=self.mvar, command=self._on_maintenance_toggle,
                                      font=FONT_CAPTION, bg=C_PANEL, fg=C_TEXT,
                                      activebackground=C_PANEL, selectcolor=C_PANEL, cursor="hand2")
        self.mcheck.grid(row=5, column=0, columnspan=3, sticky="w", pady=6)

        self.req_outer, req_inner = card(sf, "Items Requested", row=1, col=0, pady=0)
        make_label(req_inner, "List all items being requested:",
                   f=FONT_SMALL, fg=C_TEXT_MUTED, bg=C_PANEL).pack(anchor="w", pady=(0,4))
        self.requestingText = make_scrolled(req_inner, height=10)
        self.requestingText.pack(fill="both", expand=True)

        self.hod_outer, hod_inner = card(sf, "HOD Comment", row=2, col=0, pady=8)
        self.HODcomment_entry = make_scrolled(hod_inner, height=4)
        self.HODcomment_entry.pack(fill="both", expand=True)

        self.vp_outer, vp_inner = card(sf, "VP Reviewer Notes", row=3, col=0, pady=0)
        self.vpReviewerText = make_scrolled(vp_inner, height=4)
        self.vpReviewerText.pack(fill="both", expand=True)

        self.att_outer, att_inner = card(sf, "Attachments", row=4, col=0, pady=8)
        att_row = tk.Frame(att_inner, bg=C_PANEL)
        att_row.pack(fill="x")
        self.attachments_entry = tk.Entry(att_row, font=FONT_ENTRY, relief="flat", bd=4,
                                           bg="#F0F0F0", fg=C_TEXT, state="readonly")
        self.attachments_entry.pack(side="left", fill="x", expand=True, padx=(0,8))
        make_button(att_row, "Browse", self._browse_attachment, "ghost", 10).pack(side="left", padx=4)
        make_button(att_row, "Open",   self._open_attachment,   "ghost", 10).pack(side="left")

    def _build_tab2(self):
        sf = self._build_scrollable_tab(self.tab2)
        self.rt_outer, rt_inner = card(sf, "Request Type", row=0, col=0, pady=16)
        rt_row = tk.Frame(rt_inner, bg=C_PANEL)
        rt_row.pack(fill="x")
        self._request_type_radios = []
        for val, lbl in [("Material Only","Material Only"),("Labor Only","Labor Only"),("Material/Labor","Material & Labor")]:
            rb = tk.Radiobutton(rt_row, text=lbl, variable=self.request_option, value=val,
                                font=FONT_CAPTION, bg=C_PANEL, fg=C_TEXT,
                                activebackground=C_PANEL, selectcolor=C_PANEL, cursor="hand2")
            rb.pack(side="left", padx=16)
            self._request_type_radios.append(rb)

        self.sw_outer,   sw_inner   = card(sf, "Scope of Work",        row=1, col=0, pady=0)
        self.scopeText = make_scrolled(sw_inner, height=6)
        self.scopeText.pack(fill="both", expand=True)

        self.con_outer,  con_inner  = card(sf, "Contractor(s)",        row=2, col=0, pady=8)
        self.contractorEntry = tk.Entry(con_inner, font=FONT_ENTRY, relief="flat", bd=4,
                                         bg=C_PANEL, fg=C_TEXT,
                                         highlightbackground=C_BORDER, highlightthickness=1)
        self.contractorEntry.pack(fill="x")

        self.mat_outer,  mat_inner  = card(sf, "List of Materials",    row=3, col=0, pady=0)
        self.materialText = make_scrolled(mat_inner, height=6)
        self.materialText.pack(fill="both", expand=True)

        self.vpa_outer,  vpa_inner  = card(sf, "VP Approver Comments", row=4, col=0, pady=8)
        self.vpApproverText = make_scrolled(vpa_inner, height=5)
        self.vpApproverText.pack(fill="both", expand=True)

        self.prin_outer, prin_inner = card(sf, "Principal Comments",   row=5, col=0, pady=0)
        self.principalText = make_scrolled(prin_inner, height=5)
        self.principalText.pack(fill="both", expand=True)

    def _build_tab3(self):
        sf = self._build_scrollable_tab(self.tab3)
        self.hist_outer, hist_inner = card(sf, "Approval History", row=0, col=0, pady=16)
        summary = tk.Frame(hist_inner, bg=C_PANEL)
        summary.pack(fill="x", pady=(0,10))
        self.history_doc_label = tk.Label(summary, text="", font=FONT_CAPTION,
                                           bg=C_PANEL, fg=C_TEXT_MUTED)
        self.history_doc_label.pack(side="left")
        self.history_phase_label = tk.Label(summary, text="", font=("Verdana",10,"bold"),
                                             bg=C_PANEL, fg=C_PRIMARY)
        self.history_phase_label.pack(side="right")

        col_config = [
            ("Phase",       "Phase",       150, True),
            ("Action",      "Action",      100, True),
            ("Action_Date", "Date",        110, True),
            ("Action_By",   "By",          160, True),
            ("Assigned_To", "Assigned To", 160, True),
            ("Comments",    "Comments",    0,   True),
        ]
        col_ids = tuple(c[0] for c in col_config)
        self.historyTree = ttk.Treeview(hist_inner, columns=col_ids,
                                         show="headings", height=12)
        for col_id, heading, width, stretch in col_config:
            self.historyTree.heading(col_id, text=heading)
            self.historyTree.column(col_id, width=width, stretch=stretch)
        vsb = ttk.Scrollbar(hist_inner, orient="vertical", command=self.historyTree.yview)
        self.historyTree.configure(yscrollcommand=vsb.set)
        self.historyTree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

    # ── Populate ──────────────────────────────────────────────────────────────

    def _populate_fields(self, row):
        def safe(idx, default=""):
            return row[idx] if len(row) > idx and row[idx] is not None else default
        self.createdBy_entry.insert(0, safe(1))
        self.docNumber_entry.config(state="normal")
        self.doc_var.set(safe(2))
        self.docNumber_entry.config(state="readonly")
        if safe(3) in SITE_LIST: self.site_entry.current(SITE_LIST.index(safe(3)))
        if safe(4) in CATEGORY_LIST: self.category_entry.current(CATEGORY_LIST.index(safe(4)))
        if safe(5) in MAINTENANCE_LIST: self.maintenance_entry.current(MAINTENANCE_LIST.index(safe(5)))
        if safe(6) in DEPT_LIST: self.dept_entry.current(DEPT_LIST.index(safe(6)))
        if safe(7) in ACADEMIC_LIST: self.academic_entry.current(ACADEMIC_LIST.index(safe(7)))
        self.supplierEntry.insert(0, safe(14))
        self.purposeEntry.insert(0, safe(15))
        st_set(self.requestingText,   safe(16))
        st_set(self.HODcomment_entry, safe(17))
        st_set(self.vpReviewerText,   safe(18))
        self.request_option.set(safe(19, "Material Only"))
        st_set(self.scopeText,        safe(20))
        self.contractorEntry.insert(0, safe(21))
        st_set(self.materialText,     safe(22))
        st_set(self.vpApproverText,   safe(23))
        st_set(self.principalText,    safe(24))
        if safe(4) == "Infrastructure":
            self.maintenance_label.grid(); self.maintenance_entry.grid()
        if safe(6) == "Academic":
            self.academic_label.grid(); self.academic_entry.grid()

    def _populate_history(self, doc_number):
        for item in self.historyTree.get_children():
            self.historyTree.delete(item)
        if not doc_number: return
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT Phase, Action, Action_Date, Action_By, Assigned_To, Comments "
                    "FROM REQUISITION.REQUISITION_HISTORY "
                    "WHERE Document_Number = ? ORDER BY History_ID ASC", (doc_number,))
                for i, hr in enumerate(cursor.fetchall()):
                    self.historyTree.insert("", "end", iid=i, text="",
                                            values=(hr[0],hr[1],hr[2],hr[3],hr[4],hr[5]))
        except pyodbc.Error as exc:
            print(f"_populate_history error: {exc}")
        self.history_doc_label.config(text=f"Document: {doc_number}")
        self.history_phase_label.config(text=f"Current phase: {self.current_phase}")

    def _reload_phase_from_db(self):
        doc_number = self.doc_var.get().strip()
        if not doc_number:
            self._refresh_tracker()
            self._update_mcheck_visibility()
            if hasattr(self, "_request_type_radios"):
                self._update_tab_visibility()
                self._update_tab2_editability()
            self._update_field_editability()
            return
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT Phase, Assign_To, Category, Maintenance_Unit "
                    "FROM REQUISITION.REQUISITION_TABLE WHERE Document_Number = ?",
                    (doc_number,))
                row = cursor.fetchone()
                if row is not None:
                    self.current_phase = row[0] if row[0] is not None else ""
                    self.assigned_to   = row[1] if row[1] is not None else ""
                    if row[2] and self.category_var.get() == "":
                        self.category_var.set(row[2])
                    if row[3] is not None:
                        self.mvar.set(bool(row[3]))
        except pyodbc.Error as exc:
            print(f"_reload_phase_from_db error: {exc}")
        self._refresh_tracker()
        self._update_mcheck_visibility()
        self._update_field_editability()
        if hasattr(self, "_request_type_radios"):
            self._update_tab_visibility()
            self._update_tab2_editability()
        self._populate_history(doc_number)

    # ── Event handlers ────────────────────────────────────────────────────────

    def _on_category_selected(self, event=None):
        selected = self.category_entry.get()
        if selected == "Infrastructure":
            self.maintenance_label.grid(); self.maintenance_entry.grid()
        else:
            self.maintenance_entry.set("")
            self.maintenance_label.grid_remove(); self.maintenance_entry.grid_remove()
        self._assign_doc_number()
        self._refresh_tracker()

    def _on_department_selected(self, event=None):
        if self.dept_entry.get() == "Academic":
            self.academic_label.grid(); self.academic_entry.grid()
        else:
            self.academic_entry.set("")
            self.academic_label.grid_remove(); self.academic_entry.grid_remove()

    def _on_maintenance_toggle(self):
        self._refresh_tracker()
        self._update_tab_visibility()

    def _refresh_tracker(self):
        build_phase_tracker(self.process_frame, self.current_phase,
                            self.category_entry.get(), self.mvar.get())

    def _update_mcheck_visibility(self):
        if self.current_phase == "VP Review":
            self.mcheck.grid()
        else:
            self.mcheck.grid_remove()

    def _update_tab_visibility(self):
        via_maintenance = self.mvar.get()
        current_tabs = self.notebook.tabs()
        tab2_id = str(self.tab2)
        tab3_id = str(self.tab3)
        if via_maintenance:
            if tab2_id not in current_tabs:
                self.notebook.insert(1, self.tab2, text="  Maintenance Unit  ")
        else:
            if tab2_id in current_tabs:
                self.notebook.hide(self.tab2)
        if tab3_id not in current_tabs:
            self.notebook.add(self.tab3, text="  Approval History  ")
        self._update_tab2_editability()

    def _update_tab2_editability(self):
        is_maint = self.current_phase == "Maintenance Unit"
        logged_in   = self.app.current_user_name.strip()
        assigned_to = (self.assigned_to or "").strip()
        editable    = is_maint and bool(assigned_to) and logged_in == assigned_to
        state_text  = "normal"  if editable else "disabled"
        bg_text     = "#FAFAF9" if editable else "#F0F0F0"
        bg_entry    = C_PANEL   if editable else "#F0F0F0"
        for w in (self.scopeText, self.materialText,
                  self.vpApproverText, self.principalText):
            w.config(state=state_text, bg=bg_text)
        self.contractorEntry.config(state=state_text, bg=bg_entry)
        for rb in self._request_type_radios:
            rb.config(state="normal" if editable else "disabled")

    def _update_field_editability(self):
        phase = self.current_phase
        def show(f): f.grid()
        def hide(f): f.grid_remove()
        def lock(w):
            try: w.config(state="disabled", bg="#F0F0F0")
            except tk.TclError: pass
        def unlock(w):
            try: w.config(state="normal", bg="#FAFAF9")
            except tk.TclError: pass

        is_draft = phase in ("", "Draft")
        show(self.req_outer)
        unlock(self.requestingText) if is_draft else lock(self.requestingText)
        hide(self.hod_outer) if is_draft else show(self.hod_outer)
        if not is_draft:
            unlock(self.HODcomment_entry) if phase == "HOD Review" else lock(self.HODcomment_entry)
        hide(self.vp_outer) if phase in ("", "Draft", "HOD Review") else show(self.vp_outer)
        if phase not in ("", "Draft", "HOD Review"):
            unlock(self.vpReviewerText) if phase == "VP Review" else lock(self.vpReviewerText)
        show(self.att_outer)

    def _assign_doc_number(self):
        if self.doc_var.get(): return
        number = generate_doc_number(self.category_entry.get())
        if number:
            self.docNumber_entry.config(state="normal")
            self.doc_var.set(number)
            self.docNumber_entry.config(state="readonly")
            self.status_var.set(f"Document number assigned: {number}")

    def _build_args_common(self):
        return (
            self.site_entry.get(), self.category_entry.get(),
            self.maintenance_var.get(), self.dept_entry.get(),
            self.academic_entry.get(), self.supplierEntry.get(),
            self.purposeEntry.get(), st_get(self.requestingText),
            st_get(self.HODcomment_entry), st_get(self.vpReviewerText),
            self.request_option.get(), st_get(self.scopeText),
            self.contractorEntry.get(), st_get(self.materialText),
            st_get(self.vpApproverText), st_get(self.principalText),
            1 if self.mvar.get() else 0,
        )

    # ── Attachments ───────────────────────────────────────────────────────────

    def _browse_attachment(self):
        file_path = filedialog.askopenfilename(
            title="Select Attachment",
            filetypes=[("All Files","*.*"),("PDF","*.pdf"),
                       ("Word","*.docx"),("Images","*.png *.jpg")])
        if not file_path: return
        try:
            os.makedirs(ATTACHMENTS_FOLDER, exist_ok=True)
            file_name = os.path.basename(file_path)
            shutil.copy2(file_path, os.path.join(ATTACHMENTS_FOLDER, file_name))
            self.attachments_entry.config(state="normal")
            self.attachments_entry.delete(0, "end")
            self.attachments_entry.insert(0, file_name)
            self.attachments_entry.config(state="readonly")
            self.status_var.set(f"Attachment saved: {file_name}")
        except Exception as exc:
            messagebox.showerror("Error", f"Failed to save attachment:\n{exc}")

    def _open_attachment(self):
        file_name = self.attachments_entry.get().strip()
        if not file_name:
            messagebox.showwarning("No Attachment", "No attachment selected.")
            return
        file_path = os.path.join(ATTACHMENTS_FOLDER, file_name)
        if not os.path.exists(file_path):
            messagebox.showerror("Not Found", f"Attachment not found:\n{file_path}")
            return
        try:
            os.startfile(file_path)
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    # ── Save / Submit ─────────────────────────────────────────────────────────

    def _save_draft(self):
        doc_number = self.doc_var.get().strip()
        if not doc_number:
            messagebox.showwarning("Missing", "A document number is required before saving.")
            return
        args_common = self._build_args_common()
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT COUNT(*) FROM REQUISITION.REQUISITION_TABLE "
                    "WHERE Document_Number = ?", (doc_number,))
                exists = cursor.fetchone()[0] > 0
                if exists:
                    cursor.execute(
                        "UPDATE REQUISITION.REQUISITION_TABLE SET "
                        "Site=?,Category=?,Maintenance=?,Department=?,Academic=?,"
                        "Supplier=?,Purpose=?,Requesting=?,HOD_Comment=?,VP_Comment=?,"
                        "Request_Type=?,Scope=?,Contractor=?,Material=?,"
                        "VP_Approval=?,Principal_Comment=?,Maintenance_Unit=? "
                        "WHERE Document_Number=?",
                        (*args_common, doc_number))
                    msg, popup = "Requisition updated.", "Requisition updated."
                else:
                    cursor.execute(
                        "INSERT INTO REQUISITION.REQUISITION_TABLE "
                        "(Created_By,Document_Number,Site,Category,Maintenance,"
                        "Department,Academic,Supplier,Purpose,Requesting,"
                        "HOD_Comment,VP_Comment,Request_Type,Scope,Contractor,"
                        "Material,VP_Approval,Principal_Comment,Maintenance_Unit,"
                        "Phase,Submit_Date,Assign_To) "
                        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (self.createdBy_entry.get(), doc_number, *args_common,
                         "Draft", str(self.today), self.createdBy_entry.get()))
                    msg, popup = "Draft saved.", "Requisition saved as Draft."
                log_history(cursor, doc_number,
                            phase=self.current_phase or "Draft",
                            action="Updated" if exists else "Saved",
                            action_by=self.app.current_user_name)
                conn.commit()
            self.status_var.set(msg)
            messagebox.showinfo("Saved", popup)
            self.after(300, self._reload_phase_from_db)
        except Exception as exc:
            messagebox.showerror("Database Error", str(exc))

    def _open_submit_window(self):
        doc_number = self.doc_var.get().strip()
        if not doc_number:
            messagebox.showwarning("Missing", "Save the requisition before submitting.")
            return
        phases = get_phases(self.category_entry.get(), self.mvar.get())
        current_idx = phases.index(self.current_phase) if self.current_phase in phases else 0
        if current_idx + 1 >= len(phases):
            messagebox.showwarning("Complete", "This requisition has reached the final phase.")
            return
        next_phase = phases[current_idx + 1]
        user_list  = fetch_users()

        win = tk.Toplevel(self)
        win.title("Submit Requisition")
        win.geometry("520x300")
        win.configure(bg=C_BG)
        win.resizable(False, False)
        win.grab_set()

        hdr = tk.Frame(win, bg=C_HEADER_BG, height=56)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        tk.Label(hdr, text="Assignment Details", font=("Georgia",15,"bold"),
                 bg=C_HEADER_BG, fg="white").pack(side="left", padx=20, pady=12)

        body = tk.Frame(win, bg=C_BG, padx=28, pady=16)
        body.pack(fill="both", expand=True)
        body.columnconfigure(1, weight=1)

        def frow(label, widget, r):
            tk.Label(body, text=label, font=FONT_LABEL, bg=C_BG,
                     fg=C_TEXT_MUTED, anchor="w").grid(row=r, column=0, sticky="w", pady=6)
            widget.grid(row=r, column=1, sticky="ew", padx=(12,0), pady=6)

        phase_var = tk.StringVar(value=next_phase)
        frow("Next Phase",    tk.Entry(body, textvariable=phase_var, font=FONT_ENTRY,
                                       state="readonly", bg="#F0F0F0", relief="flat", bd=4), 0)
        frow("Date Assigned", tk.Entry(body, textvariable=tk.StringVar(value=str(self.today)),
                                       font=FONT_ENTRY, state="readonly",
                                       bg="#F0F0F0", relief="flat", bd=4), 1)
        assignee_combo = ttk.Combobox(body, values=user_list, state="readonly", font=FONT_ENTRY)
        frow("Assigned To", assignee_combo, 2)

        bf = tk.Frame(win, bg=C_BG, padx=28, pady=10)
        bf.pack(fill="x")

        def do_submit():
            if not assignee_combo.get():
                messagebox.showwarning("Required", "Please select an assignee.")
                return
            args_common     = self._build_args_common()
            completed_phase = self.current_phase
            try:
                with get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT COUNT(*) FROM REQUISITION.REQUISITION_TABLE "
                        "WHERE Document_Number = ?", (doc_number,))
                    if cursor.fetchone()[0] == 0:
                        messagebox.showerror("Not Found", "Save the requisition first.")
                        return
                    cursor.execute(
                        "UPDATE REQUISITION.REQUISITION_TABLE SET "
                        "Site=?,Category=?,Maintenance=?,Department=?,Academic=?,"
                        "Supplier=?,Purpose=?,Requesting=?,HOD_Comment=?,VP_Comment=?,"
                        "Request_Type=?,Scope=?,Contractor=?,Material=?,"
                        "VP_Approval=?,Principal_Comment=?,Maintenance_Unit=?,"
                        "Phase=?,Assign_To=?,Submit_Date=?,Complete_Date=? "
                        "WHERE Document_Number=?",
                        (*args_common, phase_var.get(), assignee_combo.get(),
                         str(self.today), str(self.today), doc_number))
                    log_history(cursor, doc_number,
                                phase=completed_phase, action="Submitted",
                                action_by=self.app.current_user_name,
                                assigned_to=assignee_combo.get(),
                                comments=st_get(self.HODcomment_entry))
                    conn.commit()
                self.status_var.set("Submitted successfully.")
                win.destroy()
                self.after(300, self._reload_phase_from_db)
            except Exception as exc:
                messagebox.showerror("Error", str(exc))

        make_button(bf, "Save & Submit", do_submit,   "success", 14).pack(side="right", padx=4)
        make_button(bf, "Cancel",        win.destroy,  "danger",  10).pack(side="right", padx=4)


# ═════════════════════════════════════════════
#  SCREEN 5 — ADMIN
# ═════════════════════════════════════════════
class AdminScreen(BaseScreen):

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self._build_ui()

    def on_show(self):
        self._load_users()
        self._load_keywords()

    def _build_ui(self):
        hdr = tk.Frame(self, bg=C_HEADER_BG, height=60)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        tk.Label(hdr, text="Administration", font=FONT_TITLE,
                 bg=C_HEADER_BG, fg="white").pack(side="left", padx=24, pady=10)
        make_button(hdr, "Home",
                    lambda: self.app.show(HomeScreen),
                    "ghost", 8).pack(side="right", padx=16, pady=10)

        body = tk.Frame(self, bg=C_BG)
        body.pack(fill="both", expand=True, padx=12, pady=12)
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        self._build_users_panel(body)
        self._build_right_panel(body)

        tk.Frame(self, bg=C_BORDER, height=1).pack(fill="x")
        footer = tk.Frame(self, bg=C_PANEL, padx=20, pady=10)
        footer.pack(fill="x")
        make_button(footer, "Close", lambda: self.app.show(HomeScreen),
                    "danger", 10).pack(side="right")

    def _build_users_panel(self, parent):
        outer = tk.Frame(parent, bg=C_PANEL,
                         highlightthickness=1, highlightbackground=C_BORDER)
        outer.grid(row=0, column=0, sticky="NSEW", padx=(0,6))
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(1, weight=1)

        ph = tk.Frame(outer, bg=C_HEADER_BG)
        ph.grid(row=0, column=0, sticky="EW")
        tk.Label(ph, text="Users", font=FONT_SECTION,
                 bg=C_HEADER_BG, fg="white", padx=14, pady=8).pack(side="left")
        make_button(ph, "+ New User",
                    lambda: self.app.show(UserScreen),
                    "primary", 10).pack(side="right", padx=10, pady=6)

        tree_frame = tk.Frame(outer, bg=C_PANEL)
        tree_frame.grid(row=1, column=0, sticky="NSEW", padx=6, pady=6)
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        cols = ("userid","name","username","email")
        self.user_tree = ttk.Treeview(tree_frame, columns=cols,
                                       show="headings", selectmode="browse")
        for col_id, heading, width, stretch in [
            ("userid",   "ID",       0,   False),
            ("name",     "Name",     180, True),
            ("username", "Username", 130, True),
            ("email",    "Email",    0,   True),
        ]:
            self.user_tree.heading(col_id, text=heading)
            self.user_tree.column(col_id, width=width, stretch=stretch)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.user_tree.yview)
        self.user_tree.configure(yscrollcommand=vsb.set)
        self.user_tree.grid(row=0, column=0, sticky="NSEW")
        vsb.grid(row=0, column=1, sticky="NS")
        self.user_tree.bind("<<TreeviewSelect>>", self._on_user_select)

        self.user_count = tk.Label(outer, text="", bg=C_PANEL,
                                    font=FONT_SMALL, fg=C_TEXT_MUTED, padx=10, pady=4)
        self.user_count.grid(row=2, column=0, sticky="W")

    def _build_right_panel(self, parent):
        right = tk.Frame(parent, bg=C_BG)
        right.grid(row=0, column=1, sticky="NSEW")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)

        kw_frame = tk.Frame(right, bg=C_PANEL,
                             highlightthickness=1, highlightbackground=C_BORDER)
        kw_frame.grid(row=0, column=0, sticky="NSEW")
        kw_frame.columnconfigure(0, weight=1)
        kw_frame.rowconfigure(1, weight=1)

        tk.Label(kw_frame, text="Keywords", font=FONT_SECTION,
                 bg=C_PANEL, fg=C_HEADER_BG, padx=14, pady=8).pack(fill="x")
        tk.Frame(kw_frame, bg=C_HEADER_ACC, height=2).pack(fill="x", padx=14)
        tk.Label(kw_frame, text="Select a table to manage its values",
                 font=FONT_SMALL, fg=C_TEXT_MUTED, bg=C_PANEL,
                 padx=14, pady=4).pack(anchor="w")

        lb_frame = tk.Frame(kw_frame, bg=C_PANEL, padx=14, pady=6)
        lb_frame.pack(fill="both", expand=True)
        lb_frame.columnconfigure(0, weight=1)
        lb_frame.rowconfigure(0, weight=1)

        self.keyword_listbox = tk.Listbox(lb_frame, font=FONT_ENTRY, relief="flat", bd=0,
                                           bg="#F7F5F2", fg=C_TEXT,
                                           selectbackground=C_PRIMARY, selectforeground="white",
                                           activestyle="none")
        kw_vsb = ttk.Scrollbar(lb_frame, orient="vertical",
                                command=self.keyword_listbox.yview)
        self.keyword_listbox.configure(yscrollcommand=kw_vsb.set)
        self.keyword_listbox.grid(row=0, column=0, sticky="NSEW")
        kw_vsb.grid(row=0, column=1, sticky="NS")
        self.keyword_listbox.bind("<<ListboxSelect>>", self._on_keyword_select)

    def _load_users(self):
        for item in self.user_tree.get_children():
            self.user_tree.delete(item)
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT UserID, FirstName, LastName, UserName, Email "
                    "FROM Administration.Users ORDER BY LastName, FirstName")
                rows = cursor.fetchall()
        except pyodbc.Error:
            rows = []
        for row in rows:
            self.user_tree.insert("", "end", iid=str(row[0]),
                                   values=(row[0], f"{row[1]} {row[2]}", row[3], row[4]))
        self.user_count.config(text=f"{len(rows)} user{'s' if len(rows)!=1 else ''}")

    def _load_keywords(self):
        self.keyword_listbox.delete(0, "end")
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES "
                    "WHERE TABLE_SCHEMA='Keywords' AND TABLE_TYPE='BASE TABLE' "
                    "ORDER BY TABLE_NAME")
                for row in cursor.fetchall():
                    self.keyword_listbox.insert("end", row[0])
        except pyodbc.Error as exc:
            print(f"_load_keywords error: {exc}")

    def _on_user_select(self, _event):
        selected = self.user_tree.focus()
        if not selected: return
        self.app.selected_user_id = int(selected)
        self.app.show(UserScreen)

    def _on_keyword_select(self, _event):
        sel = self.keyword_listbox.curselection()
        if not sel: return
        table_name = self.keyword_listbox.get(sel[0])
        KeywordWindow(self, table_name)


# ═════════════════════════════════════════════
#  SCREEN 6 — USER FORM
# ═════════════════════════════════════════════
class UserScreen(BaseScreen):

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self._selected_user_id = None
        self._build_ui()

    def on_show(self):
        self._load_users()
        user_id = getattr(self.app, "selected_user_id", None)
        if user_id:
            self.app.selected_user_id = None
            self._load_user(user_id)
        else:
            self._new_user()

    def _build_ui(self):
        hdr = tk.Frame(self, bg=C_HEADER_BG, height=60)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        tk.Label(hdr, text="User Management", font=FONT_TITLE,
                 bg=C_HEADER_BG, fg="white").pack(side="left", padx=24, pady=10)
        make_button(hdr, "Back",
                    lambda: self.app.show(AdminScreen),
                    "ghost", 8).pack(side="right", padx=16, pady=10)

        body = tk.Frame(self, bg=C_BG)
        body.pack(fill="both", expand=True, padx=12, pady=12)
        body.columnconfigure(0, weight=2)
        body.columnconfigure(1, weight=3)
        body.rowconfigure(0, weight=1)

        self._build_list(body)
        self._build_form(body)

        tk.Frame(self, bg=C_BORDER, height=1).pack(fill="x")
        bar = tk.Frame(self, bg=C_PANEL, padx=20, pady=12)
        bar.pack(fill="x")
        make_button(bar, "Back",  lambda: self.app.show(AdminScreen), "ghost",   10).pack(side="right", padx=6)
        make_button(bar, "Save",  self._save_user,                    "success", 10).pack(side="right", padx=6)
        make_button(bar, "Clear", self._new_user,                     "ghost",   10).pack(side="right", padx=6)

        self.status_var = tk.StringVar(value="Ready")
        sbar = tk.Frame(self, bg=C_HEADER_BG, height=32)
        sbar.pack(fill="x"); sbar.pack_propagate(False)
        tk.Label(sbar, textvariable=self.status_var, font=FONT_SMALL,
                 bg=C_HEADER_BG, fg="#94A3B8").pack(side="left", padx=16, pady=6)

    def _build_list(self, parent):
        outer = tk.Frame(parent, bg=C_PANEL,
                         highlightthickness=1, highlightbackground=C_BORDER)
        outer.grid(row=0, column=0, sticky="NSEW", padx=(0,6))
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(1, weight=1)

        ph = tk.Frame(outer, bg=C_HEADER_BG)
        ph.grid(row=0, column=0, sticky="EW")
        tk.Label(ph, text="All Users", font=FONT_SECTION,
                 bg=C_HEADER_BG, fg="white", padx=14, pady=8).pack(side="left")
        make_button(ph, "+ New", self._new_user, "primary", 8
                    ).pack(side="right", padx=10, pady=6)

        tf = tk.Frame(outer, bg=C_PANEL)
        tf.grid(row=1, column=0, sticky="NSEW", padx=6, pady=6)
        tf.columnconfigure(0, weight=1); tf.rowconfigure(0, weight=1)

        cols = ("userid","name","username","email")
        self.user_tree = ttk.Treeview(tf, columns=cols, show="headings", selectmode="browse")
        for col_id, heading, width, stretch in [
            ("userid",   "ID",       0,   False),
            ("name",     "Name",     160, True),
            ("username", "Username", 110, True),
            ("email",    "Email",    0,   True),
        ]:
            self.user_tree.heading(col_id, text=heading)
            self.user_tree.column(col_id, width=width, stretch=stretch)
        vsb = ttk.Scrollbar(tf, orient="vertical", command=self.user_tree.yview)
        self.user_tree.configure(yscrollcommand=vsb.set)
        self.user_tree.grid(row=0, column=0, sticky="NSEW")
        vsb.grid(row=0, column=1, sticky="NS")
        self.user_tree.bind("<<TreeviewSelect>>", lambda e: self._on_select())

        self.user_count = tk.Label(outer, text="", bg=C_PANEL,
                                    font=FONT_SMALL, fg=C_TEXT_MUTED, padx=10, pady=4)
        self.user_count.grid(row=2, column=0, sticky="W")

    def _build_form(self, parent):
        outer = tk.Frame(parent, bg=C_PANEL,
                         highlightthickness=1, highlightbackground=C_BORDER)
        outer.grid(row=0, column=1, sticky="NSEW")
        outer.columnconfigure(0, weight=1)

        self.form_title_var = tk.StringVar(value="New User")
        ph = tk.Frame(outer, bg=C_HEADER_BG)
        ph.pack(fill="x")
        tk.Label(ph, textvariable=self.form_title_var, font=FONT_SECTION,
                 bg=C_HEADER_BG, fg="white", padx=14, pady=8).pack(side="left")
        tk.Frame(outer, bg=C_HEADER_ACC, height=2).pack(fill="x")

        form = tk.Frame(outer, bg=C_PANEL, padx=10, pady=10)
        form.pack(fill="both", expand=True)
        form.columnconfigure(1, weight=1)
        form.columnconfigure(3, weight=1)

        def frow(label, row, col=0, show=None, state="normal"):
            make_label(form, label, bg=C_PANEL).grid(
                row=row, column=col, sticky="e", padx=(12,6), pady=8)
            e = tk.Entry(form, font=FONT_ENTRY, relief="flat", bd=4,
                         bg=C_PANEL, fg=C_TEXT, width=22,
                         highlightbackground=C_BORDER, highlightthickness=1,
                         state=state, **({"show": show} if show else {}))
            e.grid(row=row, column=col+1, sticky="ew", padx=(0,12), pady=8)
            return e

        self.firstName_entry = frow("First Name", 0, 0)
        self.lastName_entry  = frow("Last Name",  0, 2)
        self.email_entry     = frow("Email",      1, 0)
        self.userName_entry  = frow("Username",   1, 2)
        self.osuser_entry    = frow("OS Username", 2, 0)
        make_label(form, "(Windows login)", f=FONT_SMALL,
                   fg=C_TEXT_MUTED, bg=C_PANEL).grid(row=2, column=3, sticky="w")
        self.password_entry  = frow("Password",         3, 0, show="*")
        self.password2_entry = frow("Confirm Password", 3, 2, show="*")

        tog = tk.Frame(form, bg=C_PANEL)
        tog.grid(row=4, column=0, columnspan=4, sticky="w", padx=12, pady=12)
        self.enabled_var = tk.BooleanVar(value=True)
        self.reset_var   = tk.BooleanVar(value=False)
        tk.Checkbutton(tog, text="Account Enabled", variable=self.enabled_var,
                       font=FONT_CAPTION, bg=C_PANEL, fg=C_TEXT,
                       activebackground=C_PANEL, selectcolor=C_PANEL,
                       cursor="hand2").pack(side="left", padx=(0,20))
        tk.Checkbutton(tog, text="Reset Password on Next Login", variable=self.reset_var,
                       font=FONT_CAPTION, bg=C_PANEL, fg=C_TEXT,
                       activebackground=C_PANEL, selectcolor=C_PANEL,
                       cursor="hand2").pack(side="left")

        tk.Frame(form, bg=C_BORDER, height=1).grid(
            row=5, column=0, columnspan=4, sticky="EW", padx=12, pady=(4,0))
        make_label(form, "Leave password blank to keep existing password.",
                   f=FONT_SMALL, fg=C_TEXT_MUTED, bg=C_PANEL).grid(
            row=6, column=0, columnspan=4, sticky="w", padx=12, pady=4)

    def _load_users(self):
        for item in self.user_tree.get_children():
            self.user_tree.delete(item)
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT UserID, FirstName, LastName, UserName, Email "
                    "FROM Administration.Users ORDER BY LastName, FirstName")
                rows = cursor.fetchall()
        except pyodbc.Error:
            rows = []
        for row in rows:
            self.user_tree.insert("", "end", iid=str(row[0]),
                                   values=(row[0], f"{row[1]} {row[2]}", row[3], row[4]))
        self.user_count.config(text=f"{len(rows)} user{'s' if len(rows)!=1 else ''}")

    def _load_user(self, user_id):
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT UserID, FirstName, LastName, UserName, Email, OSuser "
                    "FROM Administration.Users WHERE UserID = ?", (user_id,))
                row = cursor.fetchone()
        except pyodbc.Error as exc:
            messagebox.showerror("Error", str(exc)); return
        if not row: return
        self._new_user()
        self._selected_user_id = user_id
        self.form_title_var.set(f"Edit — {row[1]} {row[2]}")
        for entry, val in [(self.firstName_entry, row[1]),
                           (self.lastName_entry,  row[2]),
                           (self.userName_entry,  row[3]),
                           (self.email_entry,     row[4]),
                           (self.osuser_entry,    row[5] or "")]:
            entry.insert(0, val or "")

    def _on_select(self):
        selected = self.user_tree.focus()
        if selected:
            self._load_user(int(selected))

    def _new_user(self):
        self._selected_user_id = None
        self.form_title_var.set("New User")
        for e in (self.firstName_entry, self.lastName_entry,
                  self.email_entry, self.userName_entry,
                  self.osuser_entry, self.password_entry, self.password2_entry):
            e.delete(0, "end")
        self.enabled_var.set(True)
        self.reset_var.set(False)
        self.status_var.set("Ready to add new user")

    def _save_user(self):
        first = self.firstName_entry.get().strip()
        last  = self.lastName_entry.get().strip()
        email = self.email_entry.get().strip()
        uname = self.userName_entry.get().strip()
        osuser = self.osuser_entry.get().strip()
        pw    = self.password_entry.get()
        pw2   = self.password2_entry.get()
        if not first or not last or not uname or not email:
            messagebox.showwarning("Required", "First name, last name, username and email are required.")
            return
        if pw or pw2:
            if pw != pw2:
                messagebox.showwarning("Password", "Passwords do not match."); return
            if len(pw) < 6:
                messagebox.showwarning("Password", "Password must be at least 6 characters."); return
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                if self._selected_user_id is None:
                    if not pw:
                        messagebox.showwarning("Required", "Password required for new users."); return
                    cursor.execute(
                        "INSERT INTO Administration.Users "
                        "(FirstName,LastName,Email,UserName,Password_hash,OSuser) "
                        "VALUES (?,?,?,?,?,?)",
                        (first, last, email, uname, hash_password(pw), osuser or None))
                    msg = f"User '{first} {last}' created."
                else:
                    if pw:
                        cursor.execute(
                            "UPDATE Administration.Users SET "
                            "FirstName=?,LastName=?,Email=?,UserName=?,Password_hash=?,OSuser=? "
                            "WHERE UserID=?",
                            (first, last, email, uname, hash_password(pw), osuser or None,
                             self._selected_user_id))
                    else:
                        cursor.execute(
                            "UPDATE Administration.Users SET "
                            "FirstName=?,LastName=?,Email=?,UserName=?,OSuser=? "
                            "WHERE UserID=?",
                            (first, last, email, uname, osuser or None,
                             self._selected_user_id))
                    msg = f"User '{first} {last}' updated."
                conn.commit()
            self.status_var.set(msg)
            messagebox.showinfo("Saved", msg)
            self._load_users()
            self._new_user()
        except pyodbc.Error as exc:
            messagebox.showerror("Database Error", str(exc))


# ═════════════════════════════════════════════
#  KEYWORD WINDOW  (Toplevel — stays as popup)
# ═════════════════════════════════════════════
class KeywordWindow(tk.Toplevel):

    def __init__(self, parent, table_name):
        super().__init__(parent)
        self.table_name = table_name
        self.title(f"Keywords — {table_name}")
        self.geometry("720x520")
        self.configure(bg=C_BG)
        self.grab_set()
        self._rows     = []
        self._new_rows = []
        self._build_ui()
        self._load_rows()

    def _build_ui(self):
        hdr = tk.Frame(self, bg=C_HEADER_BG, height=56)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        tk.Label(hdr, text=f"Keywords — {self.table_name}",
                 font=("Georgia",14,"bold"), bg=C_HEADER_BG, fg="white"
                 ).pack(side="left", padx=20, pady=12)

        col_hdr = tk.Frame(self, bg=C_HEADER_BG)
        col_hdr.pack(fill="x", padx=20, pady=(8,0))
        for text, width in [("ID",8),("Description",36),("Active",8),("Delete",8)]:
            tk.Label(col_hdr, text=text, width=width, bg=C_HEADER_BG,
                     fg="white", font=FONT_CAPTION).pack(side="left")

        outer = tk.Frame(self, bg=C_BG)
        outer.pack(fill="both", expand=True, padx=20, pady=8)
        canvas = tk.Canvas(outer, bg=C_BG, highlightthickness=0)
        vsb = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        self.rows_frame = tk.Frame(canvas, bg=C_BG)
        win_id = canvas.create_window((0,0), window=self.rows_frame, anchor="nw")
        def on_resize(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(win_id, width=e.width)
        self.rows_frame.bind("<Configure>",
                             lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", on_resize)
        canvas.configure(yscrollcommand=vsb.set)
        canvas.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        tk.Frame(self, bg=C_BORDER, height=1).pack(fill="x")
        footer = tk.Frame(self, bg=C_PANEL, padx=16, pady=10)
        footer.pack(fill="x")
        make_button(footer, "Close",     self.destroy,      "danger",  10).pack(side="right", padx=4)
        make_button(footer, "Save",      self._save,        "success", 10).pack(side="right", padx=4)
        make_button(footer, "+ Add Row", self._add_new_row, "primary", 10).pack(side="left",  padx=4)

    def _load_rows(self):
        for w in self.rows_frame.winfo_children():
            w.destroy()
        self._rows.clear()
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES "
                    "WHERE TABLE_SCHEMA='Keywords' AND TABLE_NAME=?", (self.table_name,))
                if cursor.fetchone()[0] == 0: return
                cursor.execute(f"SELECT Id, keywordName, isActive FROM Keywords.[{self.table_name}]")
                data = cursor.fetchall()
        except pyodbc.Error as exc:
            print(f"KeywordWindow load error: {exc}"); return
        for i, row in enumerate(data):
            self._add_existing_row(i, row[0], row[1], bool(row[2]))

    def _add_existing_row(self, r, row_id, name, is_active):
        bg = C_PANEL if r % 2 == 0 else "#F7F5F2"
        name_var   = tk.StringVar(value=name)
        active_var = tk.BooleanVar(value=is_active)
        del_var    = tk.BooleanVar(value=False)
        row_frame = tk.Frame(self.rows_frame, bg=bg)
        row_frame.pack(fill="x", pady=1)
        tk.Label(row_frame, text=str(row_id), width=8, bg=bg,
                 font=FONT_CAPTION, fg=C_TEXT_MUTED).pack(side="left")
        tk.Entry(row_frame, textvariable=name_var, width=36, font=FONT_ENTRY,
                 relief="flat", bd=2, bg=bg, fg=C_TEXT).pack(side="left", padx=4)
        tk.Checkbutton(row_frame, variable=active_var,
                       bg=bg, activebackground=bg).pack(side="left", padx=4)
        tk.Checkbutton(row_frame, variable=del_var, fg=C_DANGER,
                       bg=bg, activebackground=bg, selectcolor=bg).pack(side="left", padx=4)
        self._rows.append((row_id, name_var, active_var, del_var))

    def _add_new_row(self):
        name_var   = tk.StringVar()
        active_var = tk.BooleanVar(value=True)
        r = len(self._rows) + len(self._new_rows)
        bg = C_PANEL if r % 2 == 0 else "#F7F5F2"
        row_frame = tk.Frame(self.rows_frame, bg=bg)
        row_frame.pack(fill="x", pady=1)
        tk.Label(row_frame, text="NEW", width=8, bg=bg,
                 font=FONT_CAPTION, fg=C_PRIMARY).pack(side="left")
        tk.Entry(row_frame, textvariable=name_var, width=36, font=FONT_ENTRY,
                 relief="flat", bd=2, bg="#EFF6FF", fg=C_TEXT).pack(side="left", padx=4)
        tk.Checkbutton(row_frame, variable=active_var,
                       bg=bg, activebackground=bg).pack(side="left", padx=4)
        self._new_rows.append((name_var, active_var))

    def _save(self):
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                for row_id, name_var, active_var, del_var in self._rows:
                    if del_var.get():
                        cursor.execute(
                            f"DELETE FROM Keywords.[{self.table_name}] WHERE Id=?", (row_id,))
                    else:
                        cursor.execute(
                            f"UPDATE Keywords.[{self.table_name}] "
                            f"SET keywordName=?, isActive=? WHERE Id=?",
                            (name_var.get(), 1 if active_var.get() else 0, row_id))
                for name_var, active_var in self._new_rows:
                    name = name_var.get().strip()
                    if name:
                        cursor.execute(
                            f"INSERT INTO Keywords.[{self.table_name}] "
                            f"(keywordName, isActive) VALUES (?,?)",
                            (name, 1 if active_var.get() else 0))
                conn.commit()
            messagebox.showinfo("Saved", "Keywords saved successfully.")
            self._new_rows.clear()
            self._load_rows()
        except Exception as exc:
            messagebox.showerror("Error", str(exc))


# ═════════════════════════════════════════════
#  MAIN APPLICATION CONTROLLER
# ═════════════════════════════════════════════
class App(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Church Teachers College — RMS")
        self.geometry("1400x900")
        self.minsize(1100, 700)
        self.configure(bg=C_BG)

        # Session state
        self.current_user_id   = None
        self.current_user_name = ""
        self.selected_doc_number = None
        self.selected_user_id    = None

        self._apply_styles()

        # Container
        container = tk.Frame(self)
        container.pack(fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # Build all screens
        self.screens = {}
        for ScreenClass in (LoginScreen, HomeScreen, RequisitionListScreen,
                            RequisitionFormScreen, AdminScreen, UserScreen):
            screen = ScreenClass(container, self)
            self.screens[ScreenClass] = screen

        # Start on login
        self.show(LoginScreen)

    def show(self, screen_class):
        """Raise a screen and call its on_show hook."""
        screen = self.screens[screen_class]
        screen.tkraise()
        screen.on_show()
        # Resize window to suit the screen
        sizes = {
            LoginScreen:           "600x500",
            HomeScreen:            "900x600",
            RequisitionListScreen: "1300x750",
            RequisitionFormScreen: "1400x900",
            AdminScreen:           "1200x750",
            UserScreen:            "1200x750",
        }
        self.geometry(sizes.get(screen_class, "1400x900"))

    def _apply_styles(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("TNotebook", background=C_BG, borderwidth=0, tabmargins=[0,0,0,0])
        s.configure("TNotebook.Tab", font=FONT_CAPTION, padding=[18,10],
                    background=C_BORDER, foreground=C_TEXT_MUTED)
        s.map("TNotebook.Tab",
              background=[("selected", C_PANEL)], foreground=[("selected", C_PRIMARY)])
        s.configure("Treeview",
                    background=C_PANEL, foreground=C_TEXT, rowheight=28,
                    fieldbackground=C_PANEL, font=FONT_CAPTION, borderwidth=0)
        s.configure("Treeview.Heading",
                    background=C_HEADER_BG, foreground="white",
                    font=("Verdana",10,"bold"), relief="flat", padding=[8,6])
        s.map("Treeview",
              background=[("selected", C_PRIMARY)], foreground=[("selected","white")])
        s.configure("TCombobox",
                    fieldbackground=C_PANEL, background=C_PANEL, foreground=C_TEXT,
                    arrowcolor=C_PRIMARY, bordercolor=C_BORDER,
                    lightcolor=C_BORDER, darkcolor=C_BORDER)
        big_font = tkfont.Font(family="Verdana", size=11)
        self.option_add("*TCombobox*Listbox*Font", big_font)
        self.option_add("*TCombobox*Listbox*Background", C_PANEL)
        self.option_add("*TCombobox*Listbox*Foreground", C_TEXT)
        self.option_add("*TCombobox*Listbox*selectBackground", C_PRIMARY)


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    app = App()
    app.mainloop()
