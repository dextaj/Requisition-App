import tkinter as tk
from tkinter import ttk
import pyodbc
import os
import sys
import subprocess

# ── Database ─────────────────────────────────────────────────────────────────

DB_CONN = (
    r"Driver=ODBC Driver 18 for SQL Server;"
    r"Server=Chris;"
    r"Database=ChurchTeachersCollegeDB;"
    r"Trusted_Connection=yes;"
    r"encrypt=Optional;"
)

REQUISITION_FORM = (
    r"C:\Users\chris\AppData\Local\Programs\Python\Python314"
    r"\ChurchTeachersCollege\PythonApplication1\RequisitionForm.pyw"
)

def get_connection():
    return pyodbc.connect(DB_CONN)


# ── Logged-in user ────────────────────────────────────────────────────────────

def resolve_logged_in_user():
    os_user = os.getlogin()
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                "SELECT UserID, FirstName + ' ' + LastName "
                "FROM Administration.Users "
                "WHERE OSuser = ?",
                (os_user,)
            )
            user_row = cursor.fetchone()
            if user_row is None:
                print(f"No user found for OSuser={os_user}")
                return None, None

            user_id   = user_row[0]
            user_name = user_row[1]

            # Register in LogOnUser
            cursor.execute(
                "SELECT Logon_ID FROM Administration.LogOnUser "
                "WHERE OSuser = ?",
                (os_user,)
            )
            existing = cursor.fetchone()

            if existing:
                cursor.execute(
                    "UPDATE Administration.LogOnUser "
                    "SET UserID=?, UserName=?, DocNumber=NULL "
                    "WHERE OSuser=?",
                    (user_id, user_name, os_user)
                )
            else:
                cursor.execute(
                    "INSERT INTO Administration.LogOnUser "
                    "(UserID, UserName, OSuser, DocNumber) "
                    "VALUES (?, ?, ?, NULL)",
                    (user_id, user_name, os_user)
                )
            conn.commit()
            return user_id, user_name

    except pyodbc.Error as exc:
        print(f"resolve_logged_in_user error: {exc}")
    return None, None


def log_document_open(user_id, user_name, doc_number):
    os_user = os.getlogin()
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE Administration.LogOnUser "
                "SET DocNumber = ? "
                "WHERE OSuser = ?",
                (doc_number, os_user)
            )
            conn.commit()
            #print(f"log_document_open: DocNumber={doc_number} set for OSuser={os_user}")
    except pyodbc.Error as exc:
        print(f"log_document_open error: {exc}")


# ── Requisition data ──────────────────────────────────────────────────────────

def fetch_requisitions(user_name, view_all=False):
    if view_all:
        query = "SELECT * FROM REQUISITION.REQUISITION_TABLE"
        params = ()
    else:
        query = (
            "SELECT * FROM REQUISITION.REQUISITION_TABLE "
            "WHERE Assign_To = ?"
        )
        params = (user_name,)
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
    except pyodbc.Error as exc:
        print(f"fetch_requisitions error: {exc}")
        return []


def fetch_summary_counts(user_name):
    """Return (my_open, pending, total_month) counts."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                "SELECT COUNT(*) FROM REQUISITION.REQUISITION_TABLE "
                "WHERE Assign_To = ? AND Phase != 'Accounts'",
                (user_name,)
            )
            my_open = cursor.fetchone()[0]

            cursor.execute(
                "SELECT COUNT(*) FROM REQUISITION.REQUISITION_TABLE "
                "WHERE Assign_To = ? AND Phase = 'Draft'",
                (user_name,)
            )
            pending = cursor.fetchone()[0]

            cursor.execute(
                "SELECT COUNT(*) FROM REQUISITION.REQUISITION_TABLE "
                "WHERE MONTH(Submit_Date) = MONTH(GETDATE()) "
                "AND YEAR(Submit_Date) = YEAR(GETDATE())"
            )
            total_month = cursor.fetchone()[0]

            return my_open, pending, total_month
    except pyodbc.Error:
        return 0, 0, 0

# ── Main application window ───────────────────────────────────────────────────

class RequisitionScreen(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Requisitions")
        self.geometry("1200x700")
        self.minsize(900, 500)
        self.configure(bg="#f5f5f0")

        self.user_id, self.user_name = resolve_logged_in_user()
        self.view_all = False
        self._all_rows = []

        self._apply_styles()
        self._build_ui()
        self._load_data()

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

    # ── Styles ────────────────────────────────────────────────────────────────

    def _apply_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure(
            "Treeview",
            background="#ffffff",
            fieldbackground="#ffffff",
            foreground="#1a1a1a",
            font=("Segoe UI", 11),
            rowheight=28,
        )
        style.configure(
            "Treeview.Heading",
            background="#f0eeea",
            foreground="#555550",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
        )
        style.map("Treeview", background=[("selected", "#dbeafe")])
        style.map("Treeview.Heading", background=[("active", "#e4e2dc")])

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        outer = tk.Frame(self, bg="#f5f5f0")
        outer.grid(row=0, column=0, sticky="NSEW", padx=10, pady=10)
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(3, weight=1)

        self._build_header(outer)
        self._build_stats_bar(outer)
        self._build_toolbar(outer)
        self._build_table(outer)
        self._build_footer(outer)

    def _build_header(self, parent):
        hdr = tk.Frame(parent, bg="#ffffff", relief="flat",
                       highlightthickness=1, highlightbackground="#ddddd5")
        hdr.grid(row=0, column=0, sticky="EW", pady=(0, 1))
        hdr.columnconfigure(1, weight=1)

        tk.Label(hdr, text="Requisitions", bg="#ffffff",
                 font=("Segoe UI", 14, "bold"), fg="#1a1a1a",
                 pady=10, padx=14).grid(row=0, column=0, sticky="W")

        user_display = self.user_name or os.getlogin()
        tk.Label(hdr, text=f"  {user_display}  ", bg="#dbeafe",
                 fg="#1e40af", font=("Segoe UI", 10),
                 relief="flat", pady=4, padx=2,
                 bd=0).grid(row=0, column=2, sticky="E", padx=14)

    def _build_stats_bar(self, parent):
        bar = tk.Frame(parent, bg="#f0eeea",
                       highlightthickness=1, highlightbackground="#ddddd5")
        bar.grid(row=1, column=0, sticky="EW", pady=(0, 1))

        self.stat_my_open = self._stat_cell(bar, "0", "My open requisitions", 0)
        self.stat_pending = self._stat_cell(bar, "0", "Pending approval",     1)
        self.stat_total   = self._stat_cell(bar, "0", "Total this month",     2)

        bar.columnconfigure(0, weight=1)
        bar.columnconfigure(1, weight=1)
        bar.columnconfigure(2, weight=1)

    def _stat_cell(self, parent, value, label, col):
        cell = tk.Frame(parent, bg="#ffffff",
                        highlightthickness=1, highlightbackground="#e0deda")
        cell.grid(row=0, column=col, sticky="NSEW",
                  padx=(0 if col == 0 else 1, 0), pady=0)
        val_lbl = tk.Label(cell, text=value, bg="#ffffff",
                           font=("Segoe UI", 20, "bold"), fg="#1a1a1a",
                           pady=6, padx=14)
        val_lbl.grid(row=0, column=0, sticky="W")
        tk.Label(cell, text=label, bg="#ffffff",
                 font=("Segoe UI", 10), fg="#888780",
                 padx=14, pady=(0)).grid(row=1, column=0, sticky="W")
        tk.Frame(cell, bg="#ffffff", height=8).grid(row=2, column=0)
        return val_lbl

    def _build_toolbar(self, parent):
        bar = tk.Frame(parent, bg="#ffffff",
                       highlightthickness=1, highlightbackground="#ddddd5")
        bar.grid(row=2, column=0, sticky="EW", pady=(0, 1))

        new_btn = tk.Button(
            bar, text="+ New requisition",
            command=self._open_new_requisition,
            bg="#dbeafe", fg="#1e40af",
            font=("Segoe UI", 11, "bold"),
            relief="flat", bd=0,
            padx=14, pady=7, cursor="hand2",
            activebackground="#bfdbfe", activeforeground="#1e3a8a",
        )
        new_btn.grid(row=0, column=0, padx=(10), pady=8)

        self.toggle_mine = tk.Button(
            bar, text="Mine",
            command=lambda: self._set_view(False),
            bg="#1e40af", fg="#ffffff",
            font=("Segoe UI", 10, "bold"),
            relief="flat", bd=0,
            padx=12, pady=5, cursor="hand2",
        )
        self.toggle_mine.grid(row=0, column=1, pady=8)

        self.toggle_all = tk.Button(
            bar, text="All",
            command=lambda: self._set_view(True),
            bg="#f0eeea", fg="#555550",
            font=("Segoe UI", 10),
            relief="flat", bd=0,
            padx=12, pady=5, cursor="hand2",
        )
        self.toggle_all.grid(row=0, column=2, padx=(12), pady=8)

        tk.Frame(bar, bg="#ffffff").grid(row=0, column=3, sticky="EW")
        bar.columnconfigure(3, weight=1)

        tk.Label(bar, text="Search:", bg="#ffffff",
                 font=("Segoe UI", 10), fg="#888780"
                 ).grid(row=0, column=4, padx=(4), pady=8)

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._on_search)
        search_entry = tk.Entry(
            bar, textvariable=self.search_var,
            font=("Segoe UI", 11), relief="solid", bd=1,
            width=24, fg="#1a1a1a", bg="#ffffff",
        )
        search_entry.grid(row=0, column=5, padx=(10), pady=8, ipady=4)
        search_entry.insert(0, "Search requisitions...")
        search_entry.bind("<FocusIn>",  lambda e: self._clear_placeholder(search_entry))
        search_entry.bind("<FocusOut>", lambda e: self._restore_placeholder(search_entry))

    def _build_table(self, parent):
        frame = tk.Frame(parent, bg="#ffffff",
                         highlightthickness=1, highlightbackground="#ddddd5")
        frame.grid(row=3, column=0, sticky="NSEW", pady=(0, 1))
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        parent.rowconfigure(3, weight=1)

        columns = ("doc_number", "site", "category", "department", "description", "status")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings",
                                 selectmode="browse")

        col_config = [
            ("doc_number",  "Doc #",       100, tk.W),
            ("site",        "Site",        130, tk.W),
            ("category",    "Category",    120, tk.W),
            ("department",  "Department",  130, tk.W),
            ("description", "Description", 0,   tk.W),
            ("status", "Phase", 110, tk.CENTER),
        ]
        for col_id, heading, width, anchor in col_config:
            self.tree.heading(col_id, text=heading,
                              command=lambda c=col_id: self._sort_column(c))
            if width:
                self.tree.column(col_id, width=width, anchor=anchor, stretch=False)
            else:
                self.tree.column(col_id, anchor=anchor, stretch=True)

        self.tree.tag_configure("pending",  foreground="#92400e", background="#fffbeb")
        self.tree.tag_configure("approved", foreground="#14532d", background="#f0fdf4")
        self.tree.tag_configure("review",   foreground="#1e3a8a", background="#eff6ff")
        self.tree.tag_configure("closed",   foreground="#6b7280", background="#f9fafb")

        vsb = ttk.Scrollbar(frame, orient="vertical",   command=self.tree.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="NSEW")
        vsb.grid(row=0, column=1, sticky="NS")
        hsb.grid(row=1, column=0, sticky="EW")

        self.tree.bind("<<TreeviewSelect>>", self._on_row_select)

    def _build_footer(self, parent):
        footer = tk.Frame(parent, bg="#ffffff",
                          highlightthickness=1, highlightbackground="#ddddd5")
        footer.grid(row=4, column=0, sticky="EW")
        footer.columnconfigure(0, weight=1)

        self.row_count_label = tk.Label(
            footer, text="", bg="#ffffff",
            font=("Segoe UI", 10), fg="#888780",
            padx=14, pady=8,
        )
        self.row_count_label.grid(row=0, column=0, sticky="W")

        tk.Button(
            footer, text="Close",
            command=self.destroy,
            bg="#f5f5f0", fg="#444441",
            font=("Segoe UI", 10),
            relief="flat", bd=0,
            padx=14, pady=6, cursor="hand2",
            activebackground="#e4e2dc",
        ).grid(row=0, column=1, padx=10, pady=6, sticky="E")

    # ── Data loading ──────────────────────────────────────────────────────────

    def _load_data(self):
        self._all_rows = fetch_requisitions(self.user_name, view_all=self.view_all)
        self._refresh_table(self._all_rows)
        self._refresh_stats()

    def _refresh_stats(self):
        if not self.user_name:
            return
        my_open, pending, total = fetch_summary_counts(self.user_name)
        self.stat_my_open.config(text=str(my_open))
        self.stat_pending.config(text=str(pending))
        self.stat_total.config(text=str(total))

    def _refresh_table(self, rows):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for row in rows:
            # 0=Requisition_ID, 1=Created_By, 2=Document_Number, 3=Site,
            # 4=Category, 5=Maintenance, 6=Department, 7=Academic,
            # 8=Requesting, 9=HOD_Comment, 10=Phase, 11=Submit_Date,
            # 12=Assign_To, 13=Complete_Date, 14=Supplier, 15=Purpose
            doc_number  = row[2]  if len(row) > 2  else ""
            site        = row[3]  if len(row) > 3  else ""
            category    = row[4]  if len(row) > 4  else ""
            department  = row[6]  if len(row) > 6  else ""
            description = row[15] if len(row) > 15 else ""  # Purpose
            phase       = row[10] if len(row) > 10 else ""  # Phase not Status

            tag = self._status_tag(phase)
            self.tree.insert(
                "", "end",
                iid=str(row[0]),
                values=(doc_number, site, category, department, description, phase),
                tags=(tag,),
            )

        count = len(rows)
        self.row_count_label.config(
            text=f"{count} requisition{'s' if count != 1 else ''} shown"
        )
        
    def _status_tag(self, phase):
        if not phase:
            return ""
        p = phase.strip().lower()
        if p == "draft":                        return "pending"
        if p in ("hod review", "vp review"):    return "review"
        if p in ("vp approval", "principal approval",
             "procurement", "maintenance unit"): return "approved"
        if p == "accounts":                     return "closed"
        return ""

    # ── Interactions ──────────────────────────────────────────────────────────

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
        if not hasattr(self, "tree"):
            return
        term = self.search_var.get().strip().lower()
        if not term or term == "search requisitions...":
            self._refresh_table(self._all_rows)
            return
        filtered = [
            r for r in self._all_rows
            if any(term in str(cell).lower() for cell in r)
        ]
        self._refresh_table(filtered)

    def _on_row_select(self, _event):
        selected = self.tree.focus()
        if not selected:
            return
        values = self.tree.item(selected, "values")
        if not values:
            return
        doc_number = values[0]
        if self.user_id and self.user_name:
            log_document_open(self.user_id, self.user_name, doc_number)
        self.after(300, self._open_requisition_form)  # wait 300ms for DB commit

    def _open_requisition_form(self):
        try:
            subprocess.Popen([sys.executable, REQUISITION_FORM])
        except FileNotFoundError:
            tk.messagebox.showerror(
                "Not found",
                f"Could not find requisition form:\n{REQUISITION_FORM}"
            )

    def _open_new_requisition(self):
        self._open_requisition_form()

    def _sort_column(self, col):
        data = [
            (self.tree.set(k, col), k)
            for k in self.tree.get_children("")
        ]
        data.sort(reverse=getattr(self, "_sort_reverse", False))
        for index, (_, k) in enumerate(data):
            self.tree.move(k, "", index)
        self._sort_reverse = not getattr(self, "_sort_reverse", False)

    def _clear_placeholder(self, entry):
        if entry.get() == "Search requisitions...":
            entry.delete(0, tk.END)
            entry.config(fg="#1a1a1a")

    def _restore_placeholder(self, entry):
        if not entry.get():
            entry.insert(0, "Search requisitions...")
            entry.config(fg="#aaaaaa")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import tkinter.messagebox
    app = RequisitionScreen()
    app.mainloop()