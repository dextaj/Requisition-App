import tkinter as tk
from tkinter import ttk
import os
import sys
import subprocess
import branding
import appconfig
import applog

from requisition_db import (
    resolve_logged_in_user, user_in_any_group,
    fetch_requisitions, fetch_summary_counts, log_document_open,
)

log = applog.get_logger("requisition")

def _resource_base():
    """Bundle dir when packaged by PyInstaller, else this file's folder."""
    if getattr(sys, "frozen", False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

REQUISITION_FORM = os.path.join(_resource_base(), "RequisitionForm.pyw")


def _launch_form():
    """Open the Requisition form: the sibling .exe when packaged, else the
    .pyw via Python when running from source."""
    if getattr(sys, "frozen", False):
        exe_dir = os.path.dirname(sys.executable)
        subprocess.Popen([os.path.join(exe_dir, "RequisitionForm.exe")])
    else:
        subprocess.Popen([sys.executable, REQUISITION_FORM])
        
# Groups whose members may view ALL requisitions (not just their own).
VIEW_ALL_GROUPS = ("VP", "Principal")

# ── Header design tokens (match other screens) ────────────────────────────────
C_HEADER_BG  = "#1A2B4A"
C_HEADER_ACC = "#C8A96E"
FONT_TITLE   = ("Georgia", 22, "bold")
FONT_SMALL   = ("Verdana",  9)

# ── Main application window ───────────────────────────────────────────────────

class RequisitionScreen(tk.Tk):
    def __init__(self, login_user_id=None):
        super().__init__()
        self.title("Requisitions")
        self.geometry("1200x700")
        self.minsize(900, 500)
        self.configure(bg="#f5f5f0")

        self.user_id, self.user_name = resolve_logged_in_user(login_user_id)
        # Only VP / Principal members may switch to the "All" view.
        self.can_view_all = user_in_any_group(self.user_id, VIEW_ALL_GROUPS)
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
        hdr = tk.Frame(parent, bg=C_HEADER_BG, height=70)
        hdr.grid(row=0, column=0, sticky="EW", pady=(0, 1))
        hdr.pack_propagate(False)

        branding.add_logo(hdr, self, bg=C_HEADER_BG)

        tk.Label(hdr, text="Requisitions",
                 font=FONT_TITLE, bg=C_HEADER_BG, fg="white").pack(
            side="left", padx=(0, 0) if branding.has_logo(self) else 24,
            pady=14)
        tk.Label(hdr, text=appconfig.active_config().display_name,
                 font=("Georgia", 11, "italic"),
                 bg=C_HEADER_BG, fg=C_HEADER_ACC).pack(side="left", padx=12)

        user_display = self.user_name or os.getlogin()
        tk.Label(hdr, text=f"  {user_display}  ",
                 font=FONT_SMALL, bg=C_HEADER_BG,
                 fg="#94A3B8").pack(side="right", padx=24)

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

        # Mine / All toggle — only shown to VP / Principal members. For everyone
        # else the view is fixed to their own requisitions, so the toggle pair
        # would be meaningless and is omitted entirely.
        self.toggle_mine = None
        self.toggle_all = None
        if self.can_view_all:
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

        close_btn = tk.Button(
            footer, text="Close",
            command=self.destroy,
            bg="#DC2626", fg="white",
            font=("Verdana", 11, "bold"),
            relief="flat", bd=0,
            padx=18, pady=9, width=10, cursor="hand2",
            activebackground="#B91C1C", activeforeground="white",
        )
        close_btn.bind("<Enter>", lambda e: close_btn.config(bg="#B91C1C"))
        close_btn.bind("<Leave>", lambda e: close_btn.config(bg="#DC2626"))
        close_btn.grid(row=0, column=1, padx=10, pady=6, sticky="E")

    # ── Data loading ──────────────────────────────────────────────────────────

    def _load_data(self):
        self._all_rows = fetch_requisitions(
            self.user_id, self.user_name, view_all=self.view_all)
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
        # Guard: a non-privileged user can never reach the "All" view, even if
        # this were called programmatically.
        if all_reqs and not self.can_view_all:
            return

        self.view_all = all_reqs
        active   = ("Segoe UI", 10, "bold")
        inactive = ("Segoe UI", 10)

        if self.toggle_mine is not None:
            self.toggle_mine.config(
                bg="#1e40af" if not all_reqs else "#f0eeea",
                fg="#ffffff" if not all_reqs else "#555550",
                font=active if not all_reqs else inactive)
        if self.toggle_all is not None:
            self.toggle_all.config(
                bg="#1e40af" if all_reqs else "#f0eeea",
                fg="#ffffff" if all_reqs else "#555550",
                font=active if all_reqs else inactive)

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
            _launch_form()
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

def _parse_user_id_arg():
    """First CLI arg is the authenticated UserID passed by the login screen."""
    if len(sys.argv) > 1:
        try:
            return int(sys.argv[1])
        except ValueError:
            log.warning("ignoring non-numeric user id arg: %r", sys.argv[1])
    return None


if __name__ == "__main__":
    import tkinter.messagebox
    try:
        appconfig.active_config()
    except appconfig.ConfigError as exc:
        root = tk.Tk()
        root.withdraw()
        tkinter.messagebox.showerror("Configuration error", str(exc))
        root.destroy()
        sys.exit(1)
    app = RequisitionScreen(login_user_id=_parse_user_id_arg())
    app.mainloop()
