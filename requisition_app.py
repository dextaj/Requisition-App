import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog, font
import pyodbc
import os
import re
import shutil
from datetime import date
import branding

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


def row_to_dict(cursor, row):
    """Convert a pyodbc row into a dict keyed by column name.

    Uses cursor.description, so it reflects the columns of the most recently
    executed query. Call it (and consume the result) before running another
    query on the same cursor. Returns None when row is None.
    """
    if row is None:
        return None
    return {col[0]: value for col, value in zip(cursor.description, row)}

# ─────────────────────────────────────────────
#  ATTACHMENTS FOLDER
# ─────────────────────────────────────────────
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
#  KEYWORD / LIST HELPERS
# ─────────────────────────────────────────────
def get_keywords_data(table_name):
    """Fetch active keyword names from a Keywords schema table."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT KeywordName FROM Keywords.{table_name} "
                f"WHERE isActive = 0 ORDER BY KeywordName"
            )
            return [row[0] for row in cursor.fetchall()]
    except pyodbc.Error as exc:
        print(f"get_keywords_data({table_name}) error: {exc}")
        return []


def load_lists():
    """Load all dropdown lists from the database. Called once at startup."""
    return {
        "site":        get_keywords_data("Site"),
        "category":    get_keywords_data("Category"),
        "maintenance": get_keywords_data("Maintenance"),
        "department":  get_keywords_data("Department"),
        "academic":    get_keywords_data("Academic"),
    }


DOC_PREFIXES = {
    "Transport":      "TRAN-",
    "Infrastructure": "INFR-",
    "Household":      "HSLD-",
    "Kitchen":        "KTCN-",
}

# ─────────────────────────────────────────────
#  PHASES
# ─────────────────────────────────────────────
PHASES_STANDARD    = ["Draft", "HOD Review", "VP Review",
                      "Principal Approval", "Procurement", "Accounts"]
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
#  HISTORY LOGGER
# ─────────────────────────────────────────────
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


# ─────────────────────────────────────────────
#  PHASE TRACKER
# ─────────────────────────────────────────────
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
            bg, fg, border, symbol = C_ACTIVE_BG, C_ACTIVE_FG, C_ACTIVE_BD, str(i + 1)
        else:
            bg, fg, border, symbol = C_PENDING_BG, C_PENDING_FG, C_PENDING_BD, str(i + 1)

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
                row=0, column=col + 1, sticky="EW")


# ─────────────────────────────────────────────
#  DOCUMENT NUMBER GENERATOR
# ─────────────────────────────────────────────
def generate_doc_number(category):
    prefix = DOC_PREFIXES.get(category, "OFFS-") if category else ""
    if not prefix:
        return ""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT MAX(Document_Number) FROM REQUISITION.REQUISITION_TABLE "
                "WHERE Document_Number LIKE ?",
                (f"%{prefix}%",)
            )
            row = cursor.fetchone()
            counter = 0
            if row and row[0]:
                nums = re.findall(r"\d+", row[0])
                counter = int(nums[-1]) if nums else 0
        return f"{prefix}{counter + 1:05d}"
    except pyodbc.Error as exc:
        print(f"generate_doc_number error: {exc}")
        return ""


# ─────────────────────────────────────────────
#  SESSION / DATA HELPERS
# ─────────────────────────────────────────────
def load_session():
    os_user     = os.getlogin()
    user_name   = ""
    doc_number  = ""
    req_row     = None
    assigned_to = ""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT UserID, UserName, OSuser, DocNumber "
                "FROM Administration.LogOnUser WHERE OSuser = ?",
                (os_user,)
            )
            log_row = row_to_dict(cursor, cursor.fetchone())
            if log_row is not None:
                user_name  = log_row.get("UserName") or ""
                doc_number = log_row.get("DocNumber") or ""
                if doc_number:
                    cursor.execute(
                        "SELECT * FROM REQUISITION.REQUISITION_TABLE "
                        "WHERE Document_Number = ?",
                        (doc_number,)
                    )
                    req_row = row_to_dict(cursor, cursor.fetchone())
                    if req_row is not None:
                        assigned_to = req_row.get("Assign_To") or ""
    except pyodbc.Error as exc:
        print(f"load_session error: {exc}")
    return user_name, doc_number, req_row, assigned_to


def fetch_users():
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT FirstName, LastName FROM Administration.Users")
            return [f"{r[0]} {r[1]}" for r in cursor.fetchall()]
    except pyodbc.Error as exc:
        print(f"fetch_users error: {exc}")
        return []


def fetch_attachments(doc_number):
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT Attachment_ID, File_Name, File_Path, "
                "Uploaded_By, Upload_Date "
                "FROM REQUISITION.REQUISITION_ATTACHMENTS "
                "WHERE Document_Number = ? "
                "ORDER BY Upload_Date ASC",
                (doc_number,)
            )
            return cursor.fetchall()
    except pyodbc.Error as exc:
        print(f"fetch_attachments error: {exc}")
        return []


def save_attachment(doc_number, file_name, file_path, uploaded_by):
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO REQUISITION.REQUISITION_ATTACHMENTS "
                "(Document_Number, File_Name, File_Path, Uploaded_By, Upload_Date) "
                "VALUES (?, ?, ?, ?, ?)",
                (doc_number, file_name, file_path,
                 uploaded_by, str(date.today()))
            )
            conn.commit()
    except pyodbc.Error as exc:
        print(f"save_attachment error: {exc}")
        raise


def delete_attachment(attachment_id):
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM REQUISITION.REQUISITION_ATTACHMENTS "
                "WHERE Attachment_ID = ?",
                (attachment_id,)
            )
            conn.commit()
    except pyodbc.Error as exc:
        print(f"delete_attachment error: {exc}")
        raise


# ─────────────────────────────────────────────
#  MAIN APPLICATION
# ─────────────────────────────────────────────
class RequisitionForm(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Requisition Management")
        self.geometry("1400x900")
        self.minsize(1100, 700)
        self.configure(bg=C_BG)

        self.today = date.today()

        # Load dropdown lists from DB
        lists = load_lists()
        self.SITE_LIST        = lists["site"]
        self.CATEGORY_LIST    = lists["category"]
        self.MAINTENANCE_LIST = lists["maintenance"]
        self.DEPT_LIST        = lists["department"]
        self.ACADEMIC_LIST    = lists["academic"]

        self.status_var      = tk.StringVar(value="Ready")
        self.doc_var         = tk.StringVar()
        self.mvar            = tk.BooleanVar()
        self.request_option  = tk.StringVar(value="Material Only")
        self.site_var        = tk.StringVar(value="")
        self.category_var    = tk.StringVar(value="")
        self.maintenance_var = tk.StringVar(
            value=self.MAINTENANCE_LIST[0] if self.MAINTENANCE_LIST else "")
        self.dept_var        = tk.StringVar(
            value=self.DEPT_LIST[0] if self.DEPT_LIST else "")
        self.academic_var    = tk.StringVar(
            value=self.ACADEMIC_LIST[0] if self.ACADEMIC_LIST else "")
        self.logon_user_var  = tk.StringVar(value="")
        self.current_phase   = ""
        self.assigned_to     = ""

        self._apply_styles()
        self._build_ui()

        user_name, doc_number, req_row, assigned_to = load_session()
        if user_name:
            self.logon_user_var.set(f"  {user_name}  ")
        self.assigned_to = assigned_to if assigned_to is not None else ""

        if doc_number:
            self.docNumber_entry.config(state="normal")
            self.doc_var.set(doc_number)
            self.docNumber_entry.config(state="readonly")

        if req_row:
            self._populate_fields(req_row)

        self.after(100, self._reload_phase_from_db)

    # ── Styles ────────────────────────────────────────────────────────────────

    def _apply_styles(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("TNotebook", background=C_BG, borderwidth=0,
                    tabmargins=[0, 0, 0, 0])
        s.configure("TNotebook.Tab", font=FONT_CAPTION, padding=[18, 10],
                    background=C_BORDER, foreground=C_TEXT_MUTED)
        s.map("TNotebook.Tab",
              background=[("selected", C_PANEL)],
              foreground=[("selected", C_PRIMARY)])
        s.configure("Treeview",
                    background=C_PANEL, foreground=C_TEXT,
                    rowheight=32, fieldbackground=C_PANEL,
                    font=FONT_CAPTION, borderwidth=0)
        s.configure("Treeview.Heading",
                    background=C_HEADER_BG, foreground="white",
                    font=("Verdana", 10, "bold"), relief="flat", padding=[8, 6])
        s.map("Treeview",
              background=[("selected", C_PRIMARY)],
              foreground=[("selected", "white")])
        s.configure("TCombobox",
                    fieldbackground=C_PANEL, background=C_PANEL,
                    foreground=C_TEXT, arrowcolor=C_PRIMARY,
                    bordercolor=C_BORDER, lightcolor=C_BORDER,
                    darkcolor=C_BORDER, insertcolor=C_PRIMARY)
        big_font = font.Font(family="Verdana", size=11)
        self.option_add("*TCombobox*Listbox*Font", big_font)
        self.option_add("*TCombobox*Listbox*Background", C_PANEL)
        self.option_add("*TCombobox*Listbox*Foreground", C_TEXT)
        self.option_add("*TCombobox*Listbox*selectBackground", C_PRIMARY)

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        self._build_header()
        self._build_phase_band()
        self._build_body()
        self._build_button_bar()
        self._build_status_bar()
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

    def _build_header(self):
        hdr = tk.Frame(self, bg=C_HEADER_BG, height=70)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        branding.add_logo(hdr, self, bg=C_HEADER_BG)

        tk.Label(hdr, text="Requisition Management",
                 font=FONT_TITLE, bg=C_HEADER_BG, fg="white").pack(
            side="left", padx=(0, 0) if branding.has_logo(self) else 24,
            pady=14)
        tk.Label(hdr, text="Church Teachers College",
                 font=("Georgia", 11, "italic"),
                 bg=C_HEADER_BG, fg=C_HEADER_ACC).pack(side="left", padx=12)
        tk.Label(hdr, textvariable=self.logon_user_var,
                 font=FONT_SMALL, bg=C_HEADER_BG,
                 fg="#94A3B8").pack(side="right", padx=24)

    def _build_phase_band(self):
        self.process_frame = tk.Frame(self, bg=C_PANEL, relief="flat", bd=0)
        self.process_frame.pack(fill="x")
        tk.Frame(self, bg=C_BORDER, height=1).pack(fill="x")

    def _build_body(self):
        body = tk.Frame(self, bg=C_BG)
        body.pack(fill="both", expand=True)
        self.notebook = ttk.Notebook(body, height=640)
        self.tab1 = ttk.Frame(self.notebook)
        self.tab2 = ttk.Frame(self.notebook)
        self.tab3 = ttk.Frame(self.notebook)
        self.notebook.add(self.tab1, text="  Requisition Request  ")
        self.notebook.add(self.tab3, text="  Approval History  ")
        self.notebook.pack(fill="both", expand=True)
        self._build_tab1()
        self._build_tab2()
        self._build_tab3()

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

    def _build_scrollable_tab(self, tab):
        canvas = tk.Canvas(tab, bg=C_BG, highlightthickness=0)
        vsb = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        frame = tk.Frame(canvas, bg=C_BG)
        frame.columnconfigure(0, weight=1)
        win_id = canvas.create_window((0, 0), window=frame, anchor="nw")
        def on_canvas_resize(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(win_id, width=event.width)
        frame.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", on_canvas_resize)
        canvas.configure(yscrollcommand=vsb.set)
        canvas.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        return frame

    # ── Tab 1 ─────────────────────────────────────────────────────────────────

    def _build_tab1(self):
        sf = self._build_scrollable_tab(self.tab1)

        self.details_outer, info = card(sf, "Requisition Details", row=0, col=0, pady=16)
        info.columnconfigure(1, weight=1)
        info.columnconfigure(3, weight=1)
        info.columnconfigure(5, weight=1)

        make_label(info, "Number", bg=C_PANEL).grid(
            row=0, column=0, sticky="e", padx=(0, 6), pady=6)
        self.docNumber_entry = tk.Entry(
            info, textvariable=self.doc_var, font=FONT_ENTRY,
            state="readonly", bg="#F0F0F0", relief="flat", bd=4, width=16)
        self.docNumber_entry.grid(row=0, column=1, sticky="ew", pady=6)

        make_label(info, "Created By", bg=C_PANEL).grid(
            row=0, column=2, sticky="e", padx=(12, 6), pady=6)
        self.createdBy_entry = tk.Entry(
            info, font=FONT_ENTRY, relief="flat", bd=4,
            bg=C_PANEL, fg=C_TEXT, width=22,
            highlightbackground=C_BORDER, highlightthickness=1)
        self.createdBy_entry.grid(row=0, column=3, sticky="ew", pady=6)

        make_label(info, "Site", bg=C_PANEL).grid(
            row=0, column=4, sticky="e", padx=(12, 6), pady=6)
        self.site_entry = make_combo(info, self.SITE_LIST, self.site_var, width=16)
        self.site_entry.grid(row=0, column=5, sticky="ew", pady=6)

        make_label(info, "Category", bg=C_PANEL).grid(
            row=1, column=0, sticky="e", padx=(0, 6), pady=6)
        self.category_entry = make_combo(
            info, self.CATEGORY_LIST, self.category_var, width=14)
        self.category_entry.grid(row=1, column=1, sticky="ew", pady=6)
        self.category_entry.bind("<<ComboboxSelected>>", self._on_category_selected)

        make_label(info, "Dept & Units", bg=C_PANEL).grid(
            row=1, column=2, sticky="e", padx=(12, 6), pady=6)
        self.dept_entry = make_combo(info, self.DEPT_LIST, self.dept_var, width=14)
        self.dept_entry.grid(row=1, column=3, sticky="ew", pady=6)
        self.dept_entry.bind("<<ComboboxSelected>>", self._on_department_selected)

        self.maintenance_label = make_label(info, "Maintenance Area", bg=C_PANEL)
        self.maintenance_label.grid(row=1, column=4, sticky="e", padx=(12, 6), pady=6)
        self.maintenance_entry = make_combo(
            info, self.MAINTENANCE_LIST, self.maintenance_var, width=18)
        self.maintenance_entry.grid(row=1, column=5, sticky="ew", pady=6)
        self.maintenance_label.grid_remove()
        self.maintenance_entry.grid_remove()

        self.academic_label = make_label(info, "Academic Department", bg=C_PANEL)
        self.academic_label.grid(row=2, column=0, sticky="e", padx=(0, 6), pady=6)
        self.academic_entry = make_combo(
            info, self.ACADEMIC_LIST, self.academic_var, width=36)
        self.academic_entry.grid(row=2, column=1, columnspan=3, sticky="ew", pady=6)
        self.academic_label.grid_remove()
        self.academic_entry.grid_remove()

        # Transport-only fields (shown when Category == "Transport")
        self.tripDate_label = make_label(info, "Date of Trip", bg=C_PANEL)
        self.tripDate_label.grid(row=6, column=0, sticky="e", padx=(0, 6), pady=6)
        self.tripDateEntry = tk.Entry(
            info, font=FONT_ENTRY, relief="flat", bd=4,
            bg=C_PANEL, fg=C_TEXT,
            highlightbackground=C_BORDER, highlightthickness=1)
        self.tripDateEntry.grid(row=6, column=1, sticky="ew", pady=6)

        self.destination_label = make_label(info, "Destination", bg=C_PANEL)
        self.destination_label.grid(row=6, column=2, sticky="e", padx=(12, 6), pady=6)
        self.destinationEntry = tk.Entry(
            info, font=FONT_ENTRY, relief="flat", bd=4,
            bg=C_PANEL, fg=C_TEXT,
            highlightbackground=C_BORDER, highlightthickness=1)
        self.destinationEntry.grid(row=6, column=3, sticky="ew", pady=6)

        self.departure_label = make_label(info, "Time of Departure", bg=C_PANEL)
        self.departure_label.grid(row=6, column=4, sticky="e", padx=(12, 6), pady=6)
        self.departureTimeEntry = tk.Entry(
            info, font=FONT_ENTRY, relief="flat", bd=4,
            bg=C_PANEL, fg=C_TEXT,
            highlightbackground=C_BORDER, highlightthickness=1)
        self.departureTimeEntry.grid(row=6, column=5, sticky="ew", pady=6)

        for _w in (self.tripDate_label, self.tripDateEntry,
                   self.destination_label, self.destinationEntry,
                   self.departure_label, self.departureTimeEntry):
            _w.grid_remove()

        make_label(info, "Purchased At", bg=C_PANEL).grid(
            row=3, column=0, sticky="e", padx=(0, 6), pady=6)
        self.supplierEntry = tk.Entry(
            info, font=FONT_ENTRY, relief="flat", bd=4,
            bg=C_PANEL, fg=C_TEXT,
            highlightbackground=C_BORDER, highlightthickness=1)
        self.supplierEntry.grid(row=3, column=1, columnspan=3, sticky="ew", pady=6)

        make_label(info, "Purpose", bg=C_PANEL).grid(
            row=4, column=0, sticky="e", padx=(0, 6), pady=6)
        self.purposeEntry = tk.Entry(
            info, font=FONT_ENTRY, relief="flat", bd=4,
            bg=C_PANEL, fg=C_TEXT,
            highlightbackground=C_BORDER, highlightthickness=1)
        self.purposeEntry.grid(row=4, column=1, columnspan=3, sticky="ew", pady=6)

        self.mcheck = tk.Checkbutton(
            info, text="Route through Maintenance Unit",
            variable=self.mvar, command=self._on_maintenance_toggle,
            font=FONT_CAPTION, bg=C_PANEL, fg=C_TEXT,
            activebackground=C_PANEL, selectcolor=C_PANEL, cursor="hand2")
        self.mcheck.grid(row=5, column=0, columnspan=3, sticky="w", pady=6)

        # Items Requested
        self.req_outer, req_inner = card(sf, "Items Requested", row=1, col=0, pady=0)
        make_label(req_inner, "List all items being requested:",
                   f=FONT_SMALL, fg=C_TEXT_MUTED, bg=C_PANEL).pack(
            anchor="w", pady=(0, 4))
        self.requestingText = make_scrolled(req_inner, height=12)
        self.requestingText.pack(fill="both", expand=True)        

        # Attachments
        self.att_outer, att_inner = card(sf, "Attachments", row=5, col=0, pady=8)

        att_tree_frame = tk.Frame(att_inner, bg=C_PANEL)
        att_tree_frame.pack(fill="x", pady=(0, 6))
        att_tree_frame.columnconfigure(0, weight=1)

        att_cols = ("att_id", "file_name", "uploaded_by", "upload_date")
        self.att_tree = ttk.Treeview(
            att_tree_frame, columns=att_cols,
            show="headings", height=4, selectmode="browse"
        )
        for col_id, heading, width, stretch in [
            ("att_id",      "ID",          0,   False),
            ("file_name",   "File Name",   0,   True),
            ("uploaded_by", "Uploaded By", 160, False),
            ("upload_date", "Date",        100, False),
        ]:
            self.att_tree.heading(col_id, text=heading)
            self.att_tree.column(col_id, width=width, stretch=stretch)

        att_vsb = ttk.Scrollbar(att_tree_frame, orient="vertical",
                                command=self.att_tree.yview)
        self.att_tree.configure(yscrollcommand=att_vsb.set)
        self.att_tree.grid(row=0, column=0, sticky="EW")
        att_vsb.grid(row=0, column=1, sticky="NS")

        att_btn_row = tk.Frame(att_inner, bg=C_PANEL)
        att_btn_row.pack(fill="x")
        make_button(att_btn_row, "Add",    self._browse_attachment, "ghost",  10
                    ).pack(side="left", padx=(0, 4))
        make_button(att_btn_row, "Open",   self._open_attachment,   "ghost",  10
                    ).pack(side="left", padx=(0, 4))
        make_button(att_btn_row, "Remove", self._remove_attachment, "danger", 10
                    ).pack(side="left")

        # HOD Comment
        self.hod_outer, hod_inner = card(sf, "HOD Comment", row=2, col=0, pady=8)
        self.HODcomment_entry = make_scrolled(hod_inner, height=4)
        self.HODcomment_entry.pack(fill="both", expand=True)

        # VP Reviewer Notes
        self.vp_outer, vp_inner = card(sf, "VP Reviewer Notes", row=3, col=0, pady=0)
        self.vpReviewerText = make_scrolled(vp_inner, height=4)
        self.vpReviewerText.pack(fill="both", expand=True)

        # Principal Comments
        self.prin_outer, prin_inner = card(sf, "Principal Comments", row=4, col=0, pady=8)
        self.principalText = make_scrolled(prin_inner, height=5)
        self.principalText.pack(fill="both", expand=True)
    # ── Tab 2 ─────────────────────────────────────────────────────────────────

    def _build_tab2(self):
        sf = self._build_scrollable_tab(self.tab2)

        self.rt_outer, rt_inner = card(sf, "Request Type", row=0, col=0, pady=16)
        rt_row = tk.Frame(rt_inner, bg=C_PANEL)
        rt_row.pack(fill="x")
        self._request_type_radios = []
        for val, lbl in [("Material Only",  "Material Only"),
                         ("Labor Only",     "Labor Only"),
                         ("Material/Labor", "Material & Labor")]:
            rb = tk.Radiobutton(
                rt_row, text=lbl, variable=self.request_option, value=val,
                font=FONT_CAPTION, bg=C_PANEL, fg=C_TEXT,
                activebackground=C_PANEL, selectcolor=C_PANEL, cursor="hand2")
            rb.pack(side="left", padx=16)
            self._request_type_radios.append(rb)

        self.sw_outer,   sw_inner   = card(sf, "Scope of Work",        row=1, col=0, pady=0)
        self.scopeText = make_scrolled(sw_inner, height=6)
        self.scopeText.pack(fill="both", expand=True)

        self.con_outer,  con_inner  = card(sf, "Contractor(s)",        row=2, col=0, pady=8)
        self.contractorEntry = tk.Entry(
            con_inner, font=FONT_ENTRY, relief="flat", bd=4,
            bg=C_PANEL, fg=C_TEXT,
            highlightbackground=C_BORDER, highlightthickness=1)
        self.contractorEntry.pack(fill="x")

        self.mat_outer,  mat_inner  = card(sf, "List of Materials",    row=3, col=0, pady=0)
        self.materialText = make_scrolled(mat_inner, height=6)
        self.materialText.pack(fill="both", expand=True)

        self.vpa_outer,  vpa_inner  = card(sf, "VP Approver Comments", row=4, col=0, pady=8)
        self.vpApproverText = make_scrolled(vpa_inner, height=5)
        self.vpApproverText.pack(fill="both", expand=True)


    # ── Tab 3 ─────────────────────────────────────────────────────────────────

    def _build_tab3(self):
        sf = self._build_scrollable_tab(self.tab3)
        self.hist_outer, hist_inner = card(sf, "Approval History", row=0, col=0, pady=16)

        summary = tk.Frame(hist_inner, bg=C_PANEL)
        summary.pack(fill="x", pady=(0, 10))
        self.history_doc_label = tk.Label(
            summary, text="", font=FONT_CAPTION, bg=C_PANEL, fg=C_TEXT_MUTED)
        self.history_doc_label.pack(side="left")
        self.history_phase_label = tk.Label(
            summary, text="", font=("Verdana", 10, "bold"),
            bg=C_PANEL, fg=C_PRIMARY)
        self.history_phase_label.pack(side="right")

        col_config = [
            ("Phase",       "Phase",       150, True),
            ("Action",      "Action",      100, True),
            ("Action_Date", "Date",        110, True),
            ("Action_By",   "By",          160, True),
            ("Assigned_To", "Assigned To", 160, True),
            ("Comments",    "Comments",      0, True),
        ]
        col_ids = tuple(c[0] for c in col_config)
        self.historyTree = ttk.Treeview(
            hist_inner, columns=col_ids, show="headings", height=12)
        for col_id, heading, width, stretch in col_config:
            self.historyTree.heading(col_id, text=heading)
            self.historyTree.column(col_id, width=width, stretch=stretch)
        vsb = ttk.Scrollbar(hist_inner, orient="vertical",
                            command=self.historyTree.yview)
        self.historyTree.configure(yscrollcommand=vsb.set)
        self.historyTree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

    # ── Button bar & status ───────────────────────────────────────────────────

    def _build_button_bar(self):
        tk.Frame(self, bg=C_BORDER, height=1).pack(fill="x")
        bar = tk.Frame(self, bg=C_PANEL, padx=20, pady=12)
        bar.pack(fill="x", side="bottom")
        make_button(bar, "Close",  self.destroy,             "danger",  10).pack(side="right", padx=6)
        make_button(bar, "Submit", self._open_submit_window, "success", 10).pack(side="right", padx=6)
        make_button(bar, "Save",   self._save_draft,         "primary", 10).pack(side="right", padx=6)

    def _build_status_bar(self):
        bar = tk.Frame(self, bg=C_HEADER_BG, height=32)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)
        tk.Label(bar, textvariable=self.status_var,
                 font=("Verdana", 9), bg=C_HEADER_BG, fg="#94A3B8").pack(
            side="left", padx=16, pady=6)

    # ── Populate from DB row ──────────────────────────────────────────────────

    def _populate_fields(self, row):
        def safe(name, default=""):
            value = row.get(name)
            return value if value is not None else default

        self.createdBy_entry.insert(0, safe("Created_By"))
        self.docNumber_entry.config(state="normal")
        self.doc_var.set(safe("Document_Number"))
        self.docNumber_entry.config(state="readonly")

        if safe("Site") in self.SITE_LIST:
            self.site_entry.current(self.SITE_LIST.index(safe("Site")))
        if safe("Category") in self.CATEGORY_LIST:
            self.category_entry.current(self.CATEGORY_LIST.index(safe("Category")))
        if safe("Maintenance") in self.MAINTENANCE_LIST:
            self.maintenance_entry.current(self.MAINTENANCE_LIST.index(safe("Maintenance")))
        if safe("Department") in self.DEPT_LIST:
            self.dept_entry.current(self.DEPT_LIST.index(safe("Department")))
        if safe("Academic") in self.ACADEMIC_LIST:
            self.academic_entry.current(self.ACADEMIC_LIST.index(safe("Academic")))

        self.supplierEntry.insert(0, safe("Supplier"))
        self.purposeEntry.insert(0, safe("Purpose"))
        st_set(self.requestingText,   safe("Requesting"))
        st_set(self.HODcomment_entry, safe("HOD_Comment"))
        st_set(self.vpReviewerText,   safe("VP_Comment"))
        self.request_option.set(safe("Request_Type", "Material Only"))
        st_set(self.scopeText,        safe("Scope"))
        self.contractorEntry.insert(0, safe("Contractor"))
        st_set(self.materialText,     safe("Material"))
        st_set(self.vpApproverText,   safe("VP_Approval"))
        st_set(self.principalText,    safe("Principal_Comment"))
        self.tripDateEntry.insert(0, safe("Trip_Date"))
        self.destinationEntry.insert(0, safe("Destination"))
        self.departureTimeEntry.insert(0, safe("Departure_Time"))

        if safe("Category") == "Infrastructure":
            self.maintenance_label.grid()
            self.maintenance_entry.grid()
        if safe("Category") == "Transport":
            self._show_transport_fields()
        if safe("Department") == "Academic":
            self.academic_label.grid()
            self.academic_entry.grid()

    def _populate_history(self, doc_number):
        for item in self.historyTree.get_children():
            self.historyTree.delete(item)
        if not doc_number:
            return
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT Phase, Action, Action_Date, Action_By, "
                    "Assigned_To, Comments "
                    "FROM REQUISITION.REQUISITION_HISTORY "
                    "WHERE Document_Number = ? "
                    "ORDER BY History_ID ASC",
                    (doc_number,)
                )
                for i, hr in enumerate(cursor.fetchall()):
                    self.historyTree.insert(
                        "", "end", iid=i, text="",
                        values=(hr[0], hr[1], hr[2], hr[3], hr[4], hr[5]))
        except pyodbc.Error as exc:
            print(f"_populate_history error: {exc}")
        self.history_doc_label.config(text=f"Document: {doc_number}")
        self.history_phase_label.config(
            text=f"Current phase: {self.current_phase}")

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
                    "FROM REQUISITION.REQUISITION_TABLE "
                    "WHERE Document_Number = ?",
                    (doc_number,)
                )
                row = row_to_dict(cursor, cursor.fetchone())
                if row is not None:
                    self.current_phase = row.get("Phase") or ""
                    self.assigned_to   = row.get("Assign_To") or ""
                    if row.get("Category") and self.category_var.get() == "":
                        self.category_var.set(row["Category"])
                    if row.get("Maintenance_Unit") is not None:
                        self.mvar.set(bool(row["Maintenance_Unit"]))
        except pyodbc.Error as exc:
            print(f"_reload_phase_from_db error: {exc}")

        self._refresh_tracker()
        self._update_mcheck_visibility()
        self._update_field_editability()
        if hasattr(self, "_request_type_radios"):
            self._update_tab_visibility()
            self._update_tab2_editability()
        self._populate_history(doc_number)
        self._load_attachments()

    # ── Field event handlers ──────────────────────────────────────────────────

    def _show_transport_fields(self):
        for w in (self.tripDate_label, self.tripDateEntry,
                  self.destination_label, self.destinationEntry,
                  self.departure_label, self.departureTimeEntry):
            w.grid()

    def _hide_transport_fields(self, clear=False):
        if clear:
            for w in (self.tripDateEntry, self.destinationEntry,
                      self.departureTimeEntry):
                state = w.cget("state")
                if state != "normal":
                    w.config(state="normal")
                w.delete(0, "end")
                if state != "normal":
                    w.config(state=state)
        for w in (self.tripDate_label, self.tripDateEntry,
                  self.destination_label, self.destinationEntry,
                  self.departure_label, self.departureTimeEntry):
            w.grid_remove()

    def _on_category_selected(self, event=None):
        selected = self.category_entry.get()
        if selected == "Infrastructure":
            self.maintenance_label.grid()
            self.maintenance_entry.grid()
        else:
            self.maintenance_entry.set("")
            self.maintenance_label.grid_remove()
            self.maintenance_entry.grid_remove()
        if selected == "Transport":
            self._show_transport_fields()
        else:
            self._hide_transport_fields(clear=True)
        self._assign_doc_number()
        self._refresh_tracker()

    def _on_department_selected(self, event=None):
        if self.dept_entry.get() == "Academic":
            self.academic_label.grid()
            self.academic_entry.grid()
        else:
            self.academic_entry.set("")
            self.academic_label.grid_remove()
            self.academic_entry.grid_remove()

    def _on_maintenance_toggle(self):
        self._refresh_tracker()
        self._update_tab_visibility()

    def _refresh_tracker(self):
        build_phase_tracker(
            self.process_frame,
            self.current_phase,
            self.category_entry.get(),
            self.mvar.get(),
        )

    def _update_mcheck_visibility(self):
        if self.current_phase == "VP Review":
            self.mcheck.grid()
        else:
            self.mcheck.grid_remove()

    def _update_tab2_editability(self):
        is_maintenance_phase = self.current_phase == "Maintenance Unit"
        logged_in   = (self.logon_user_var.get() or "").strip()
        assigned_to = (self.assigned_to or "").strip()
        is_assignee = bool(assigned_to) and logged_in == assigned_to
        editable    = is_maintenance_phase and is_assignee
        state_text  = "normal"  if editable else "disabled"
        bg_text     = "#FAFAF9" if editable else "#F0F0F0"
        bg_entry    = C_PANEL   if editable else "#F0F0F0"
        for widget in (self.scopeText, self.materialText,
                       self.vpApproverText):
            widget.config(state=state_text, bg=bg_text)
        self.contractorEntry.config(state=state_text, bg=bg_entry)
        for rb in self._request_type_radios:
            rb.config(state="normal" if editable else "disabled")

    def _update_field_editability(self):
        phase    = self.current_phase
        is_draft = phase in ("", "Draft")

        def show(f): f.grid()
        def hide(f): f.grid_remove()
        def lock(w):
            try: w.config(state="disabled", bg="#F0F0F0")
            except tk.TclError: pass
        def unlock(w):
            try: w.config(state="normal", bg="#FAFAF9")
            except tk.TclError: pass
        def lock_entry(w):   w.config(state="readonly", bg="#F0F0F0")
        def unlock_entry(w): w.config(state="normal",   bg=C_PANEL)

        # Details card — editable in Draft only
        if is_draft:
            unlock_entry(self.createdBy_entry)
            unlock_entry(self.supplierEntry)
            unlock_entry(self.purposeEntry)
            unlock_entry(self.tripDateEntry)
            unlock_entry(self.destinationEntry)
            unlock_entry(self.departureTimeEntry)
            self.site_entry.config(state="readonly")
            self.category_entry.config(state="readonly")
            self.dept_entry.config(state="readonly")
            self.maintenance_entry.config(state="readonly")
            self.academic_entry.config(state="readonly")
        else:
            lock_entry(self.createdBy_entry)
            lock_entry(self.supplierEntry)
            lock_entry(self.purposeEntry)
            lock_entry(self.tripDateEntry)
            lock_entry(self.destinationEntry)
            lock_entry(self.departureTimeEntry)
            self.site_entry.config(state="disabled")
            self.category_entry.config(state="disabled")
            self.dept_entry.config(state="disabled")
            self.maintenance_entry.config(state="disabled")
            self.academic_entry.config(state="disabled")

        # Items Requested — Draft only
        show(self.req_outer)
        unlock(self.requestingText) if is_draft else lock(self.requestingText)

        # HOD Comment — visible from HOD Review onwards
        if is_draft:
            hide(self.hod_outer)
        else:
            show(self.hod_outer)
            unlock(self.HODcomment_entry) if phase == "HOD Review" \
                else lock(self.HODcomment_entry)

        # VP Reviewer Notes — visible from VP Review onwards
        if phase in ("", "Draft", "HOD Review"):
            hide(self.vp_outer)
        else:
            show(self.vp_outer)
            unlock(self.vpReviewerText) if phase == "VP Review" \
                else lock(self.vpReviewerText)

        # Principal Comments — visible from Principal Approval onwards
        if phase in ("", "Draft", "HOD Review", "VP Review",
                     "Maintenance Unit", "VP Approval"):
            hide(self.prin_outer)
        else:
            show(self.prin_outer)
            unlock(self.principalText) if phase == "Principal Approval" \
                else lock(self.principalText)

        # Attachments — always visible
        show(self.att_outer)

    def _assign_doc_number(self):
        if self.doc_var.get():
            return
        number = generate_doc_number(self.category_entry.get())
        if number:
            self.docNumber_entry.config(state="normal")
            self.doc_var.set(number)
            self.docNumber_entry.config(state="readonly")
            self.status_var.set(f"Document number assigned: {number}")

    # ── Attachments ───────────────────────────────────────────────────────────

    def _load_attachments(self):
        for item in self.att_tree.get_children():
            self.att_tree.delete(item)
        doc_number = self.doc_var.get().strip()
        if not doc_number:
            return
        for row in fetch_attachments(doc_number):
            self.att_tree.insert(
                "", "end", iid=str(row[0]),
                values=(row[0], row[1], row[2], row[3]))

    def _browse_attachment(self):
        doc_number = self.doc_var.get().strip()
        if not doc_number:
            messagebox.showwarning(
                "Save First",
                "Please save the requisition before adding attachments.")
            return
        file_paths = filedialog.askopenfilenames(
            title="Select Attachments",
            filetypes=[("All Files", "*.*"), ("PDF", "*.pdf"),
                       ("Word", "*.docx"), ("Images", "*.png *.jpg *.jpeg")])
        if not file_paths:
            return
        doc_folder = os.path.join(ATTACHMENTS_FOLDER, doc_number)
        try:
            os.makedirs(doc_folder, exist_ok=True)
        except Exception as exc:
            messagebox.showerror("Error", f"Could not create folder:\n{exc}")
            return
        added = 0
        for file_path in file_paths:
            file_name = os.path.basename(file_path)
            dest_path = os.path.join(doc_folder, file_name)
            try:
                shutil.copy2(file_path, dest_path)
                save_attachment(
                    doc_number  = doc_number,
                    file_name   = file_name,
                    file_path   = dest_path,
                    uploaded_by = self.logon_user_var.get().strip(),
                )
                added += 1
            except Exception as exc:
                messagebox.showerror("Error",
                                     f"Failed to save '{file_name}':\n{exc}")
        if added:
            self._load_attachments()
            self.status_var.set(
                f"{added} attachment{'s' if added != 1 else ''} added.")

    def _open_attachment(self):
        selected = self.att_tree.focus()
        if not selected:
            messagebox.showwarning("No Selection", "Select an attachment to open.")
            return
        values = self.att_tree.item(selected, "values")
        if not values:
            return
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT File_Path FROM REQUISITION.REQUISITION_ATTACHMENTS "
                    "WHERE Attachment_ID = ?",
                    (int(values[0]),))
                row = cursor.fetchone()
        except pyodbc.Error as exc:
            messagebox.showerror("Error", str(exc))
            return
        if row is None or not os.path.exists(row[0]):
            messagebox.showerror(
                "Not Found",
                f"File not found on disk:\n{row[0] if row else ''}")
            return
        try:
            os.startfile(row[0])
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def _remove_attachment(self):
        selected = self.att_tree.focus()
        if not selected:
            messagebox.showwarning("No Selection", "Select an attachment to remove.")
            return
        values = self.att_tree.item(selected, "values")
        file_name = values[1] if values else "this file"
        if not messagebox.askyesno(
            "Remove Attachment",
            f"Remove '{file_name}' from this requisition?\n\n"
            f"The file will remain on disk."
        ):
            return
        try:
            delete_attachment(int(values[0]))
            self._load_attachments()
            self.status_var.set(f"Removed: {file_name}")
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    # ── Common args ───────────────────────────────────────────────────────────

    def _build_args_common(self):
        return (
            self.site_entry.get(),
            self.category_entry.get(),
            self.maintenance_var.get(),
            self.dept_entry.get(),
            self.academic_entry.get(),
            self.supplierEntry.get(),
            self.purposeEntry.get(),
            st_get(self.requestingText),
            st_get(self.HODcomment_entry),
            st_get(self.vpReviewerText),
            self.request_option.get(),
            st_get(self.scopeText),
            self.contractorEntry.get(),
            st_get(self.materialText),
            st_get(self.vpApproverText),
            st_get(self.principalText),
            1 if self.mvar.get() else 0,
            self.tripDateEntry.get(),
            self.destinationEntry.get(),
            self.departureTimeEntry.get(),
        )

    # ── Save draft ────────────────────────────────────────────────────────────

    def _save_draft(self):
        doc_number = self.doc_var.get().strip()
        if not doc_number:
            messagebox.showwarning("Missing",
                                   "A document number is required before saving.")
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
                        "VP_Approval=?,Principal_Comment=?,Maintenance_Unit=?,"
                        "Trip_Date=?,Destination=?,Departure_Time=? "
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
                        "Trip_Date,Destination,Departure_Time,"
                        "Phase,Submit_Date,Assign_To) "
                        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (self.createdBy_entry.get(), doc_number, *args_common,
                         "Draft", str(self.today), self.createdBy_entry.get()))
                    msg, popup = "Draft saved.", "Requisition saved as Draft."
                log_history(cursor, doc_number,
                            phase     = self.current_phase or "Draft",
                            action    = "Updated" if exists else "Saved",
                            action_by = self.logon_user_var.get().strip())
                conn.commit()
            self.status_var.set(msg)
            messagebox.showinfo("Saved", popup)
            self.after(300, self._reload_phase_from_db)
        except Exception as exc:
            messagebox.showerror("Database Error", str(exc))

    # ── Submit window ─────────────────────────────────────────────────────────

    def _open_submit_window(self):
        doc_number = self.doc_var.get().strip()
        if not doc_number:
            messagebox.showwarning("Missing",
                                   "A document number is required before submitting.")
            return
        phases = get_phases(self.category_entry.get(), self.mvar.get())
        current_idx = phases.index(self.current_phase) \
            if self.current_phase in phases else 0
        if current_idx + 1 >= len(phases):
            messagebox.showwarning(
                "Complete", "This requisition has already reached the final phase.")
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
        tk.Label(hdr, text="Assignment Details",
                 font=("Georgia", 15, "bold"),
                 bg=C_HEADER_BG, fg="white").pack(side="left", padx=20, pady=12)

        body = tk.Frame(win, bg=C_BG, padx=28, pady=16)
        body.pack(fill="both", expand=True)
        body.columnconfigure(1, weight=1)

        def frow(label, widget, r):
            tk.Label(body, text=label, font=FONT_LABEL, bg=C_BG,
                     fg=C_TEXT_MUTED, anchor="w").grid(
                row=r, column=0, sticky="w", pady=6)
            widget.grid(row=r, column=1, sticky="ew", padx=(12, 0), pady=6)

        phase_var = tk.StringVar(value=next_phase)
        frow("Next Phase",
             tk.Entry(body, textvariable=phase_var, font=FONT_ENTRY,
                      state="readonly", bg="#F0F0F0", relief="flat", bd=4), 0)
        frow("Date Assigned",
             tk.Entry(body, textvariable=tk.StringVar(value=str(self.today)),
                      font=FONT_ENTRY, state="readonly",
                      bg="#F0F0F0", relief="flat", bd=4), 1)
        assignee_combo = ttk.Combobox(body, values=user_list,
                                      state="readonly", font=FONT_ENTRY)
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
                        messagebox.showerror(
                            "Not Found",
                            "Save the requisition before submitting.")
                        return
                    cursor.execute(
                        "UPDATE REQUISITION.REQUISITION_TABLE SET "
                        "Site=?,Category=?,Maintenance=?,Department=?,Academic=?,"
                        "Supplier=?,Purpose=?,Requesting=?,HOD_Comment=?,VP_Comment=?,"
                        "Request_Type=?,Scope=?,Contractor=?,Material=?,"
                        "VP_Approval=?,Principal_Comment=?,Maintenance_Unit=?,"
                        "Trip_Date=?,Destination=?,Departure_Time=?,"
                        "Phase=?,Assign_To=?,Submit_Date=?,Complete_Date=? "
                        "WHERE Document_Number=?",
                        (*args_common, phase_var.get(), assignee_combo.get(),
                         str(self.today), str(self.today), doc_number))
                    log_history(cursor, doc_number,
                                phase       = completed_phase,
                                action      = "Submitted",
                                action_by   = self.logon_user_var.get().strip(),
                                assigned_to = assignee_combo.get(),
                                comments    = st_get(self.HODcomment_entry))
                    conn.commit()
                self.status_var.set("Submitted successfully.")
                win.destroy()
                self.after(300, self._reload_phase_from_db)
            except Exception as exc:
                messagebox.showerror("Error", str(exc))

        make_button(bf, "Save & Submit", do_submit,  "success", 14
                    ).pack(side="right", padx=4)
        make_button(bf, "Cancel",        win.destroy, "danger",  10
                    ).pack(side="right", padx=4)


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    app = RequisitionForm()
    app.mainloop()
