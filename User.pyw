import tkinter as tk
from tkinter import ttk, messagebox
import os

import requests
from user_db import fetch_all_users, fetch_user, save_user

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

FONT_TITLE   = ("Georgia",  22, "bold")
FONT_SECTION = ("Georgia",  13, "bold")
FONT_LABEL   = ("Verdana",  11, "bold")
FONT_ENTRY   = ("Verdana",  11)
FONT_BUTTON  = ("Verdana",  11, "bold")
FONT_SMALL   = ("Verdana",   9)
FONT_CAPTION = ("Verdana",  10)

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


def make_entry(parent, width=30, show=None, state="normal"):
    opts = dict(
        master=parent,
        font=FONT_ENTRY,
        relief="flat", bd=4,
        bg=C_PANEL, fg=C_TEXT,
        insertbackground=C_PRIMARY,
        width=width,
        highlightbackground=C_BORDER,
        highlightthickness=1,
        state=state,
    )
    if show:
        opts["show"] = show
    return tk.Entry(**opts)


def field_row(parent, label, row, col=0, show=None, state="normal", width=28):
    """Create a label+entry pair and return the entry widget."""
    make_label(parent, label, bg=C_PANEL).grid(
        row=row, column=col, sticky="e", padx=(12, 6), pady=8)
    entry = make_entry(parent, width=width, show=show, state=state)
    entry.grid(row=row, column=col + 1, sticky="ew", padx=(0, 12), pady=8)
    return entry


# ─────────────────────────────────────────────
#  MAIN APPLICATION
# ─────────────────────────────────────────────
class UserScreen(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("User Information")
        self.geometry("1100x750")
        self.minsize(900, 600)
        self.configure(bg=C_BG)

        self._selected_user_id = None

        self._apply_styles()
        self._build_ui()
        self._load_users()

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

    # ── Styles ────────────────────────────────────────────────────────────────

    def _apply_styles(self):
        s = ttk.Style(self)
        s.theme_use("clam")

        s.configure("Treeview",
                    background=C_PANEL, foreground=C_TEXT,
                    rowheight=28, fieldbackground=C_PANEL,
                    font=FONT_CAPTION, borderwidth=0)
        s.configure("Treeview.Heading",
                    background=C_HEADER_BG, foreground="white",
                    font=("Verdana", 10, "bold"), relief="flat", padding=[8, 6])
        s.map("Treeview",
              background=[("selected", C_PRIMARY)],
              foreground=[("selected", "white")])

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        self._build_header()

        body = tk.Frame(self, bg=C_BG)
        body.pack(fill="both", expand=True, padx=12, pady=12)
        body.columnconfigure(0, weight=2)
        body.columnconfigure(1, weight=3)
        body.rowconfigure(0, weight=1)

        self._build_user_list(body)
        self._build_user_form(body)
        self._build_button_bar()
        self._build_status_bar()

    def _build_header(self):
        hdr = tk.Frame(self, bg=C_HEADER_BG, height=70)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        tk.Label(hdr, text="User Information",
                 font=FONT_TITLE, bg=C_HEADER_BG, fg="white").pack(
            side="left", padx=24, pady=14)
        tk.Label(hdr, text="Church Teachers College",
                 font=("Georgia", 11, "italic"),
                 bg=C_HEADER_BG, fg=C_HEADER_ACC).pack(side="left")

    def _build_user_list(self, parent):
        outer = tk.Frame(parent, bg=C_PANEL,
                         highlightthickness=1, highlightbackground=C_BORDER)
        outer.grid(row=0, column=0, sticky="NSEW", padx=(0, 6))
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(1, weight=1)

        # Panel header
        ph = tk.Frame(outer, bg=C_HEADER_BG)
        ph.grid(row=0, column=0, sticky="EW")
        tk.Label(ph, text="All Users", font=FONT_SECTION,
                 bg=C_HEADER_BG, fg="white",
                 padx=14, pady=8).pack(side="left")
        make_button(ph, "+ New",
                    self._new_user, "primary", 8
                    ).pack(side="right", padx=10, pady=6)

        # Treeview
        tree_frame = tk.Frame(outer, bg=C_PANEL)
        tree_frame.grid(row=1, column=0, sticky="NSEW", padx=6, pady=6)
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        cols = ("userid", "name", "username", "email")
        self.user_tree = ttk.Treeview(tree_frame, columns=cols,
                                      show="headings", selectmode="browse")

        col_cfg = [
            ("userid",   "ID",       0,   False),
            ("name",     "Name",     180, True),
            ("username", "Username", 130, True),
            ("email",    "Email",    0,   True),
        ]
        for col_id, heading, width, stretch in col_cfg:
            self.user_tree.heading(col_id, text=heading)
            if width:
                self.user_tree.column(col_id, width=width, stretch=stretch)
            else:
                self.user_tree.column(col_id, width=0, stretch=stretch)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical",
                            command=self.user_tree.yview)
        self.user_tree.configure(yscrollcommand=vsb.set)
        self.user_tree.grid(row=0, column=0, sticky="NSEW")
        vsb.grid(row=0, column=1, sticky="NS")

        self.user_tree.bind("<<TreeviewSelect>>", self._on_user_select)

        self.user_count_label = tk.Label(outer, text="", bg=C_PANEL,
                                         font=FONT_SMALL, fg=C_TEXT_MUTED,
                                         padx=10, pady=4)
        self.user_count_label.grid(row=2, column=0, sticky="W")

    def _build_user_form(self, parent):
        outer = tk.Frame(parent, bg=C_PANEL,
                         highlightthickness=1, highlightbackground=C_BORDER)
        outer.grid(row=0, column=1, sticky="NSEW")
        outer.columnconfigure(0, weight=1)

        # Form header
        self.form_title_var = tk.StringVar(value="New User")
        ph = tk.Frame(outer, bg=C_HEADER_BG)
        ph.pack(fill="x")
        tk.Label(ph, textvariable=self.form_title_var, font=FONT_SECTION,
                 bg=C_HEADER_BG, fg="white",
                 padx=14, pady=8).pack(side="left")

        tk.Frame(outer, bg=C_HEADER_ACC, height=2).pack(fill="x")

        form = tk.Frame(outer, bg=C_PANEL, padx=10, pady=10)
        form.pack(fill="both", expand=True)
        form.columnconfigure(1, weight=1)
        form.columnconfigure(3, weight=1)

        # Row 0 — First / Last name
        self.firstName_entry = field_row(form, "First Name", row=0, col=0)
        self.lastName_entry  = field_row(form, "Last Name",  row=0, col=2)

        # Row 1 — Email / Username
        self.email_entry    = field_row(form, "Email",     row=1, col=0)
        self.userName_entry = field_row(form, "Username",  row=1, col=2)

        # Row 2 — OS User
        self.osuser_entry = field_row(form, "OS Username", row=2, col=0)
        make_label(form, "(Windows login name)", f=FONT_SMALL,
                   fg=C_TEXT_MUTED, bg=C_PANEL).grid(
            row=2, column=3, sticky="w", padx=(0, 12))

        # Row 3 — Password
        self.password_entry  = field_row(form, "Password",        row=3, col=0, show="*")
        self.password2_entry = field_row(form, "Confirm Password", row=3, col=2, show="*")

        # Row 4 — Status toggles
        toggle_frame = tk.Frame(form, bg=C_PANEL)
        toggle_frame.grid(row=4, column=0, columnspan=4,
                          sticky="w", padx=12, pady=12)

        self.enabled_var = tk.BooleanVar(value=True)
        self.reset_var   = tk.BooleanVar(value=False)

        tk.Checkbutton(
            toggle_frame, text="Account Enabled",
            variable=self.enabled_var,
            font=FONT_CAPTION, bg=C_PANEL, fg=C_TEXT,
            activebackground=C_PANEL, selectcolor=C_PANEL,
            cursor="hand2",
        ).pack(side="left", padx=(0, 20))

        tk.Checkbutton(
            toggle_frame, text="Reset Password on Next Login",
            variable=self.reset_var,
            font=FONT_CAPTION, bg=C_PANEL, fg=C_TEXT,
            activebackground=C_PANEL, selectcolor=C_PANEL,
            cursor="hand2",
        ).pack(side="left")

        # Row 5 — divider + password note
        tk.Frame(form, bg=C_BORDER, height=1).grid(
            row=5, column=0, columnspan=4, sticky="EW", padx=12, pady=(4, 0))
        make_label(form, "Leave password blank to keep existing password (edit mode).",
                   f=FONT_SMALL, fg=C_TEXT_MUTED, bg=C_PANEL).grid(
            row=6, column=0, columnspan=4, sticky="w", padx=12, pady=4)

    def _build_button_bar(self):
        tk.Frame(self, bg=C_BORDER, height=1).pack(fill="x")
        bar = tk.Frame(self, bg=C_PANEL, padx=20, pady=12)
        bar.pack(fill="x", side="bottom")

        make_button(bar, "Close",  self.destroy,    "danger",  10
                    ).pack(side="right", padx=6)
        make_button(bar, "Save",   self._save_user, "success", 10
                    ).pack(side="right", padx=6)
        make_button(bar, "Clear",  self._new_user,  "ghost",   10
                    ).pack(side="right", padx=6)

    def _build_status_bar(self):
        self.status_var = tk.StringVar(value="Ready")
        bar = tk.Frame(self, bg=C_HEADER_BG, height=32)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)
        tk.Label(bar, textvariable=self.status_var,
                 font=("Verdana", 9), bg=C_HEADER_BG, fg="#94A3B8").pack(
            side="left", padx=16, pady=6)

    # ── Data loading ──────────────────────────────────────────────────────────

    def _load_users(self):
        for item in self.user_tree.get_children():
            self.user_tree.delete(item)

        rows = fetch_all_users()
        for row in rows:
            full_name = f"{row[1]} {row[2]}"
            self.user_tree.insert("", "end",
                                  iid=str(row[0]),
                                  values=(row[0], full_name, row[3], row[4]))

        count = len(rows)
        self.user_count_label.config(
            text=f"{count} user{'s' if count != 1 else ''}"
        )

    # ── Interactions ──────────────────────────────────────────────────────────

    def _on_user_select(self, _event):
        selected = self.user_tree.focus()
        if not selected:
            return
        user_id = int(selected)
        self._selected_user_id = user_id

        try:
            row = fetch_user(user_id)
        except requests.RequestException as exc:
            messagebox.showerror("Error", str(exc))
            return

        if row is None:
            return

        self._clear_form()
        self.form_title_var.set(f"Edit User — {row[1]} {row[2]}")
        self.firstName_entry.insert(0, row[1] or "")
        self.lastName_entry.insert(0, row[2] or "")
        self.userName_entry.insert(0, row[3] or "")
        self.email_entry.insert(0, row[4] or "")
        self.osuser_entry.insert(0, row[5] or "")

        self.status_var.set(f"Editing user: {row[1]} {row[2]}")

    def _new_user(self):
        self._selected_user_id = None
        self._clear_form()
        self.form_title_var.set("New User")
        self.status_var.set("Ready to add new user")

    def _clear_form(self):
        for entry in (self.firstName_entry, self.lastName_entry,
                      self.email_entry, self.userName_entry,
                      self.osuser_entry, self.password_entry,
                      self.password2_entry):
            entry.delete(0, "end")
        self.enabled_var.set(True)
        self.reset_var.set(False)

    def _save_user(self):
        first    = self.firstName_entry.get().strip()
        last     = self.lastName_entry.get().strip()
        email    = self.email_entry.get().strip()
        username = self.userName_entry.get().strip()
        osuser   = self.osuser_entry.get().strip()
        pw       = self.password_entry.get()
        pw2      = self.password2_entry.get()

        # Validation
        if not first or not last:
            messagebox.showwarning("Required", "First and last name are required.")
            return
        if not username:
            messagebox.showwarning("Required", "Username is required.")
            return
        if not email:
            messagebox.showwarning("Required", "Email is required.")
            return

        # Password validation
        if pw or pw2:
            if pw != pw2:
                messagebox.showwarning("Password", "Passwords do not match.")
                return
            if len(pw) < 6:
                messagebox.showwarning("Password",
                                       "Password must be at least 6 characters.")
                return

        if self._selected_user_id is None and not pw:
            messagebox.showwarning("Required",
                                   "Password is required for new users.")
            return

        try:
            save_user(self._selected_user_id, first, last, email, username,
                      osuser, password=pw or None)
        except requests.HTTPError as exc:
            detail = (exc.response.json().get("detail")
                      if exc.response is not None else str(exc))
            messagebox.showerror("Save", detail)
            return
        except requests.RequestException as exc:
            messagebox.showerror("Database Error", str(exc))
            return

        verb = "updated" if self._selected_user_id else "created"
        msg = f"User '{first} {last}' {verb} successfully."
        self.status_var.set(msg)
        messagebox.showinfo("Saved", msg)
        self._load_users()
        self._new_user()


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    app = UserScreen()
    app.mainloop()
