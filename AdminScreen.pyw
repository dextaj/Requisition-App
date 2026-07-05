import os
import sys
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog

import pyodbc  # kept only so existing "except pyodbc.Error" lines below still resolve
import branding
import appconfig
import applog

import admin_db
from admin_db import Database, KeywordChanges
from pathlib import Path

log = applog.get_logger("admin")


# ─────────────────────────────────────────────
#  CONFIGURATION
# ─────────────────────────────────────────────
def _resource_base():
    """Bundle dir when packaged by PyInstaller, else this file's folder."""
    if getattr(sys, "frozen", False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))
    
    
class Config:
    BASE_PATH = os.environ.get("CTC_APP_PATH", _resource_base())
    USER_APP        = os.path.join(BASE_PATH, "User.pyw")
    REQUISITION_APP = os.path.join(BASE_PATH, "RequisitionScreen.pyw")


# Membership in this group is required to open the Administration screen.
ADMIN_GROUP = "Administration"


class AdminAccessDenied(Exception):
    """Raised when the logged-in user may not open the Administration screen."""


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
C_ROW_ALT    = "#F7F5F2"
C_ROW_NEW    = "#EFF6FF"

FONT_TITLE   = ("Georgia",  22, "bold")
FONT_SECTION = ("Georgia",  13, "bold")
FONT_LABEL   = ("Verdana",  11, "bold")
FONT_ENTRY   = ("Verdana",  11)
FONT_BUTTON  = ("Verdana",  11, "bold")
FONT_SMALL   = ("Verdana",   9)
FONT_CAPTION = ("Verdana",  10)


def launch(path: str, *args) -> None:
    """Launch a screen, passing the admin's auth token via the environment so
    the launched screen authenticates as the same user.

    From source: run the .pyw with Python. When packaged (PyInstaller): run the
    sibling .exe in the same folder, since the .pyw files aren't runnable then.
    """
    env = {**os.environ, "CTC_AUTH_TOKEN": admin_db.token() or ""}
    try:
        if getattr(sys, "frozen", False):
            exe_dir = os.path.dirname(sys.executable)
            target = os.path.join(exe_dir, Path(str(path)).stem + ".exe")
            subprocess.Popen([target, *map(str, args)], env=env)
        else:
            subprocess.Popen([sys.executable, path, *map(str, args)], env=env)
    except FileNotFoundError:
        messagebox.showerror("Not Found", f"Could not find:\n{path}")

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


# ─────────────────────────────────────────────
#  KEYWORD WINDOW
# ─────────────────────────────────────────────
class KeywordWindow(tk.Toplevel):

    def __init__(self, parent, db: Database, table_name: str):
        super().__init__(parent)
        self.db = db
        self.table_name = table_name
        self.title(f"Keywords — {table_name}")
        self.geometry("720x600")
        self.configure(bg=C_BG)
        self.resizable(True, True)
        self.grab_set()

        self._rows = []       # (row_id, name_var, active_var, del_var)
        self._new_rows = []   # (name_var, active_var)

        self._build_ui()
        self._load_rows()

    def _build_ui(self):
        # Header — same dark bar as the Group window
        hdr = tk.Frame(self, bg=C_HEADER_BG, height=56)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        branding.add_logo(hdr, self, bg=C_HEADER_BG, height=36)
        tk.Label(hdr, text=f"Keyword — {self.table_name}",)

        # Bordered white panel (mirrors the Group window's list panels)
        panel = tk.Frame(self, bg=C_PANEL,
                         highlightthickness=1, highlightbackground=C_BORDER)
        panel.pack(fill="both", expand=True, padx=16, pady=12)
        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(2, weight=1)

        tk.Label(panel, text=f"Values in {self.table_name}", font=FONT_LABEL,
                 bg=C_PANEL, fg=C_HEADER_BG, padx=10, pady=6).grid(
            row=0, column=0, columnspan=2, sticky="W")

        # Body holds the header strip and the scrollable rows in the SAME grid
        # column, so they share an exact width; the scrollbar sits beside both.
        body = tk.Frame(panel, bg=C_PANEL)
        body.grid(row=2, column=0, columnspan=2, sticky="NSEW", padx=8, pady=(0, 8))
        body.columnconfigure(0, weight=1)
        body.rowconfigure(1, weight=1)

        # Column headers — light strip, gridded so columns line up with rows
        col_hdr = tk.Frame(body, bg=C_ROW_ALT)
        col_hdr.grid(row=0, column=0, sticky="EW")
        self._configure_columns(col_hdr)
        for i, (text, anchor) in enumerate(
                (("ID", "w"), ("Description", "w"), ("Active", ""), ("Delete", ""))):
            tk.Label(col_hdr, text=text, bg=C_ROW_ALT, fg=C_TEXT_MUTED,
                     font=FONT_CAPTION).grid(row=0, column=i, sticky=anchor,
                                             padx=8, pady=5)

        canvas = tk.Canvas(body, bg=C_PANEL, highlightthickness=0)
        vsb = ttk.Scrollbar(body, orient="vertical", command=canvas.yview)
        self.rows_frame = tk.Frame(canvas, bg=C_PANEL)

        win_id = canvas.create_window((0, 0), window=self.rows_frame, anchor="nw")

        def on_resize(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(win_id, width=event.width)

        self.rows_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", on_resize)
        canvas.configure(yscrollcommand=vsb.set)
        canvas.grid(row=1, column=0, sticky="NSEW")
        vsb.grid(row=1, column=1, sticky="NS")

        # Mouse-wheel scrolling (Windows / macOS delta convention)
        def on_wheel(event):
            canvas.yview_scroll(int(-event.delta / 120), "units")
        canvas.bind_all("<MouseWheel>", on_wheel)
        self.bind("<Destroy>",
                  lambda e: canvas.unbind_all("<MouseWheel>"), add="+")

        # Footer — status on the left, actions on the right (as in Group window)
        tk.Frame(self, bg=C_BORDER, height=1).pack(fill="x")
        footer = tk.Frame(self, bg=C_PANEL, padx=16, pady=10)
        footer.pack(fill="x")

        make_button(footer, "Close",     self.destroy,      "danger",  10
                    ).pack(side="right", padx=4)
        make_button(footer, "Save",      self._save,        "success", 10
                    ).pack(side="right", padx=4)
        make_button(footer, "+ Add Row", self._add_new_row, "primary", 10
                    ).pack(side="left",  padx=4)
        self.status_label = tk.Label(footer, text="", bg=C_PANEL,
                                     font=FONT_SMALL, fg=C_TEXT_MUTED)
        self.status_label.pack(side="left", padx=8)

    def _load_rows(self):
        for w in self.rows_frame.winfo_children():
            w.destroy()
        self._rows.clear()
        self._new_rows.clear()

        try:
            data = self.db.keyword_rows(self.table_name)
        except (pyodbc.Error, ValueError) as exc:
            log.exception("admin error")
            messagebox.showerror("Load Error", str(exc))
            return

        for i, row in enumerate(data):
            self._add_existing_row(i, row[0], row[1], bool(row[2]))
        self._update_status()

    # Shared column layout (minsize_px, weight) for ID / Description / Active /
    # Delete. The header strip and every row apply this, so columns align.
    _COLS = ((56, 0), (160, 1), (72, 0), (72, 0))

    def _configure_columns(self, frame):
        for i, (minsize, weight) in enumerate(self._COLS):
            frame.columnconfigure(i, minsize=minsize, weight=weight)

    def _row_bg(self, index: int) -> str:
        return C_PANEL if index % 2 == 0 else C_ROW_ALT

    def _add_existing_row(self, index, row_id, name, is_active):
        bg = self._row_bg(index)

        name_var   = tk.StringVar(value=name)
        active_var = tk.BooleanVar(value=is_active)
        del_var    = tk.BooleanVar(value=False)

        row_frame = tk.Frame(self.rows_frame, bg=bg)
        row_frame.pack(fill="x", pady=1)
        self._configure_columns(row_frame)

        tk.Label(row_frame, text=str(row_id), bg=bg, font=FONT_CAPTION,
                 fg=C_TEXT_MUTED, anchor="w").grid(
            row=0, column=0, sticky="w", padx=8, pady=2)
        tk.Entry(row_frame, textvariable=name_var, font=FONT_ENTRY,
                 relief="flat", bd=2, bg=bg, fg=C_TEXT).grid(
            row=0, column=1, sticky="ew", padx=8, pady=2)
        tk.Checkbutton(row_frame, variable=active_var, bg=bg,
                       activebackground=bg).grid(row=0, column=2, pady=2)
        tk.Checkbutton(row_frame, variable=del_var, bg=bg,
                       activebackground=bg, command=self._update_status,
                       fg=C_DANGER, selectcolor=bg).grid(row=0, column=3, pady=2)

        self._rows.append((row_id, name_var, active_var, del_var))

    def _add_new_row(self):
        name_var   = tk.StringVar()
        active_var = tk.BooleanVar(value=True)

        bg = self._row_bg(len(self._rows) + len(self._new_rows))

        row_frame = tk.Frame(self.rows_frame, bg=bg)
        row_frame.pack(fill="x", pady=1)
        self._configure_columns(row_frame)

        tk.Label(row_frame, text="NEW", bg=bg, font=FONT_CAPTION,
                 fg=C_PRIMARY, anchor="w").grid(
            row=0, column=0, sticky="w", padx=8, pady=2)
        tk.Entry(row_frame, textvariable=name_var, font=FONT_ENTRY,
                 relief="flat", bd=2, bg=C_ROW_NEW, fg=C_TEXT).grid(
            row=0, column=1, sticky="ew", padx=8, pady=2)
        tk.Checkbutton(row_frame, variable=active_var, bg=bg,
                       activebackground=bg).grid(row=0, column=2, pady=2)

        self._new_rows.append((name_var, active_var))
        self._update_status()

    def _update_status(self):
        deleting = sum(1 for *_, del_var in self._rows if del_var.get())
        existing = len(self._rows) - deleting
        new = len(self._new_rows)
        total = existing + new
        pending = deleting + new
        text = f"{total} value{'s' if total != 1 else ''}"
        if pending:
            text += f"  ·  {pending} unsaved change{'s' if pending != 1 else ''}"
        self.status_label.config(text=text)

    def _collect_changes(self) -> KeywordChanges:
        deleted, updated = [], []
        for row_id, name_var, active_var, del_var in self._rows:
            if del_var.get():
                deleted.append(row_id)
            else:
                updated.append((row_id, name_var.get().strip(), active_var.get()))

        inserted = [
            (name_var.get().strip(), active_var.get())
            for name_var, active_var in self._new_rows
            if name_var.get().strip()
        ]
        return KeywordChanges(updated=updated, deleted=deleted, inserted=inserted)

    def _save(self):
        try:
            self.db.save_keywords(self.table_name, self._collect_changes())
        except (pyodbc.Error, ValueError) as exc:
            log.exception("admin error")
            messagebox.showerror("Save Error", str(exc))
            return

        messagebox.showinfo("Saved", "Keywords saved successfully.")
        self._load_rows()


# ─────────────────────────────────────────────
#  GROUP MEMBERSHIP WINDOW
# ─────────────────────────────────────────────
class GroupWindow(tk.Toplevel):
    """Two-list shuttle for managing which users belong to a group.

    Left list  = users not in the group; right list = current members.
    Add/Remove move users between the in-memory sets; Save applies the
    difference against the original membership in one transaction.
    """

    def __init__(self, parent, db: Database, group_id: int, group_name: str):
        super().__init__(parent)
        self.db = db
        self.group_id = group_id
        self.group_name = group_name
        self.title(f"Group — {group_name}")
        self.geometry("760x560")
        self.configure(bg=C_BG)
        self.resizable(True, True)
        self.grab_set()

        self._labels: dict[int, str] = {}   # user_id -> "First Last (username)"
        self._original: set[int] = set()     # membership as loaded
        self._members: set[int] = set()      # membership as edited

        self._build_ui()
        self._load()

    # ── UI ────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        hdr = tk.Frame(self, bg=C_HEADER_BG, height=56)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        branding.add_logo(hdr, self, bg=C_HEADER_BG, height=36)
        tk.Label(hdr, text=f"Group — {self.group_name}",)

        body = tk.Frame(self, bg=C_BG)
        body.pack(fill="both", expand=True, padx=16, pady=12)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(2, weight=1)
        body.rowconfigure(0, weight=1)

        self.available_box = self._make_list_panel(
            body, 0, "Available users")
        self._make_shuttle_buttons(body, 1)
        self.member_box = self._make_list_panel(
            body, 2, f"Members of {self.group_name}")

        # Double-click shortcuts mirror the buttons.
        self.available_box.bind("<Double-1>", lambda e: self._add_selected())
        self.member_box.bind("<Double-1>", lambda e: self._remove_selected())

        tk.Frame(self, bg=C_BORDER, height=1).pack(fill="x")
        footer = tk.Frame(self, bg=C_PANEL, padx=16, pady=10)
        footer.pack(fill="x")
        make_button(footer, "Close", self.destroy, "danger",  10
                    ).pack(side="right", padx=4)
        make_button(footer, "Save",  self._save,   "success", 10
                    ).pack(side="right", padx=4)
        self.status_label = tk.Label(footer, text="", bg=C_PANEL,
                                     font=FONT_SMALL, fg=C_TEXT_MUTED)
        self.status_label.pack(side="left", padx=4)

    def _make_list_panel(self, parent, col, heading) -> tk.Listbox:
        frame = tk.Frame(parent, bg=C_PANEL,
                         highlightthickness=1, highlightbackground=C_BORDER)
        frame.grid(row=0, column=col, sticky="NSEW")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)

        tk.Label(frame, text=heading, font=FONT_LABEL,
                 bg=C_PANEL, fg=C_HEADER_BG, padx=10, pady=6).grid(
            row=0, column=0, columnspan=2, sticky="W")

        box = tk.Listbox(frame, font=FONT_ENTRY, relief="flat", bd=0,
                         bg=C_ROW_ALT, fg=C_TEXT,
                         selectbackground=C_PRIMARY, selectforeground="white",
                         selectmode="extended", activestyle="none")
        vsb = ttk.Scrollbar(frame, orient="vertical", command=box.yview)
        box.configure(yscrollcommand=vsb.set)
        box.grid(row=1, column=0, sticky="NSEW", padx=(8, 0), pady=(0, 8))
        vsb.grid(row=1, column=1, sticky="NS", pady=(0, 8))
        return box

    def _make_shuttle_buttons(self, parent, col):
        mid = tk.Frame(parent, bg=C_BG)
        mid.grid(row=0, column=col, padx=10)
        make_button(mid, "Add  \u2192", self._add_selected, "primary", 10
                    ).pack(pady=6)
        make_button(mid, "\u2190  Remove", self._remove_selected, "ghost", 10
                    ).pack(pady=6)

    # ── Data ────────────────────────────────────────────────────────────────────
    def _load(self):
        try:
            users = self.db.fetch_users()
            self._original = self.db.fetch_group_member_ids(self.group_id)
        except pyodbc.Error as exc:
            log.exception("admin error")
            messagebox.showerror("Load Error", str(exc))
            return

        self._labels = {
            row[0]: f"{row[1]} {row[2]} ({row[3]})" for row in users
        }
        self._members = set(self._original)
        self._refresh_lists()

    def _refresh_lists(self):
        def fill(box, ids):
            box.delete(0, "end")
            # Keep a parallel id list aligned with listbox indices.
            ordered = sorted(ids, key=lambda uid: self._labels.get(uid, "").lower())
            for uid in ordered:
                box.insert("end", self._labels.get(uid, f"User {uid}"))
            return ordered

        member_ids = self._members
        available_ids = set(self._labels) - self._members
        self._available_order = fill(self.available_box, available_ids)
        self._member_order = fill(self.member_box, member_ids)

        pending = (len(self._members - self._original)
                   + len(self._original - self._members))
        self.status_label.config(
            text=f"{len(self._members)} member"
                 f"{'s' if len(self._members) != 1 else ''}"
                 + (f"  ·  {pending} unsaved change"
                    f"{'s' if pending != 1 else ''}" if pending else "")
        )

    # ── Interactions ────────────────────────────────────────────────────────────
    def _add_selected(self):
        for i in self.available_box.curselection():
            self._members.add(self._available_order[i])
        self._refresh_lists()

    def _remove_selected(self):
        for i in self.member_box.curselection():
            self._members.discard(self._member_order[i])
        self._refresh_lists()

    def _save(self):
        to_add = self._members - self._original
        to_remove = self._original - self._members
        if not to_add and not to_remove:
            messagebox.showinfo("No changes", "Nothing to save.")
            return
        try:
            self.db.set_group_membership(self.group_id, to_add, to_remove)
        except pyodbc.Error as exc:
            log.exception("admin error")
            messagebox.showerror("Save Error", str(exc))
            return
        messagebox.showinfo("Saved", "Group membership updated.")
        self._original = set(self._members)
        self._refresh_lists()


# ─────────────────────────────────────────────
#  SIGNATURE WINDOW
# ─────────────────────────────────────────────
class SignatureWindow(tk.Toplevel):
    """View / upload / remove a single user's approval signature image."""

    MAX_PREVIEW = (380, 160)         # preview is scaled to fit within this
    _EXT_TO_TYPE = {
        ".png":  "image/png",
        ".jpg":  "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif":  "image/gif",
    }

    def __init__(self, parent, db: Database, user_id, user_name):
        super().__init__(parent)
        self.db = db
        self.user_id = user_id
        self.user_name = user_name
        self.title(f"Signature — {user_name}")
        self.geometry("540x440")
        self.configure(bg=C_BG)
        self.resizable(False, False)
        self.grab_set()

        self._preview_img = None       # keep a reference so Tk doesn't GC it
        self._pending_data = None      # bytes chosen but not yet saved
        self._pending_type = None

        self._build_ui()
        self._load()

    def _build_ui(self):
        hdr = tk.Frame(self, bg=C_HEADER_BG, height=56)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        branding.add_logo(hdr, self, bg=C_HEADER_BG, height=36)
        tk.Label(hdr, text=f"Signature — {self.user_name}",)

        panel = tk.Frame(self, bg=C_PANEL,
                         highlightthickness=1, highlightbackground=C_BORDER)
        panel.pack(fill="both", expand=True, padx=16, pady=12)

        tk.Label(panel, text="Signature image", font=FONT_LABEL,
                 bg=C_PANEL, fg=C_HEADER_BG, padx=10, pady=6).pack(anchor="w")
        tk.Frame(panel, bg=C_HEADER_ACC, height=2).pack(fill="x", padx=10)

        self.preview = tk.Label(panel, bg=C_ROW_ALT, fg=C_TEXT_MUTED,
                                font=FONT_SMALL, width=44, height=8,
                                relief="flat")
        self.preview.pack(fill="both", expand=True, padx=10, pady=10)

        tk.Label(panel, text="PNG or JPG; a transparent PNG looks best on documents.",
                 font=FONT_SMALL, fg=C_TEXT_MUTED, bg=C_PANEL,
                 padx=10).pack(anchor="w", pady=(0, 8))

        tk.Frame(self, bg=C_BORDER, height=1).pack(fill="x")
        footer = tk.Frame(self, bg=C_PANEL, padx=16, pady=10)
        footer.pack(fill="x")
        # Grid guarantees all four buttons get placed (pack was clipping Save
        # in the fixed-width window). Column 2 is an elastic spacer that pushes
        # Save / Close to the right.
        footer.columnconfigure(2, weight=1)
        make_button(footer, "Upload…", self._choose_file, "primary", 9
                    ).grid(row=0, column=0, padx=(0, 4))
        make_button(footer, "Remove",  self._remove,      "ghost",   9
                    ).grid(row=0, column=1, padx=4)
        make_button(footer, "Save",    self._save,        "success", 9
                    ).grid(row=0, column=3, padx=4)
        make_button(footer, "Close",   self.destroy,      "danger",  9
                    ).grid(row=0, column=4, padx=(4, 0))

    def _load(self):
        try:
            data, content_type = self.db.fetch_signature(self.user_id)
        except pyodbc.Error as exc:
            log.exception("admin error")
            messagebox.showerror("Load Error", str(exc))
            return
        if data:
            self._show_image(data)
        else:
            self._show_placeholder("No signature on file.")

    def _choose_file(self):
        path = filedialog.askopenfilename(
            parent=self,
            title="Choose signature image",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.gif"),
                       ("PNG", "*.png"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, "rb") as fh:
                data = fh.read()
        except OSError as exc:
            messagebox.showerror("Read Error", str(exc))
            return

        ext = os.path.splitext(path)[1].lower()
        self._pending_data = data
        self._pending_type = self._EXT_TO_TYPE.get(ext, "application/octet-stream")
        self._show_image(data, note="  (unsaved)")

    def _save(self):
        if self._pending_data is None:
            messagebox.showinfo("No change", "Choose an image first.")
            return
        try:
            self.db.save_signature(self.user_id, self._pending_data,
                                   self._pending_type,
                                   updated_by=getattr(self.master,
                                                      "current_user_id", None))
        except pyodbc.Error as exc:
            log.exception("admin error")
            messagebox.showerror("Save Error", str(exc))
            return
        self._pending_data = self._pending_type = None
        messagebox.showinfo("Saved", "Signature saved.")
        self._load()

    def _remove(self):
        if not messagebox.askyesno(
                "Remove signature",
                f"Remove the signature for {self.user_name}?"):
            return
        try:
            self.db.delete_signature(self.user_id)
        except pyodbc.Error as exc:
            log.exception("admin error")
            messagebox.showerror("Remove Error", str(exc))
            return
        self._pending_data = self._pending_type = None
        self._show_placeholder("No signature on file.")

    # ── Preview rendering ─────────────────────────────────────────────────────
    def _show_placeholder(self, text):
        self._preview_img = None
        self.preview.config(image="", text=text)

    def _show_image(self, data, note=""):
        img = self._build_photoimage(data)
        if img is None:
            self._show_placeholder(
                "(Preview unavailable — install Pillow for non-PNG formats)")
            return
        self._preview_img = img
        self.preview.config(image=img, text="")
        if note:
            self.title(f"Signature — {self.user_name}{note}")

    def _build_photoimage(self, data):
        # Pillow handles any format and scales cleanly; preferred when present.
        try:
            import io
            from PIL import Image, ImageTk
            img = Image.open(io.BytesIO(data))
            img.thumbnail(self.MAX_PREVIEW)
            return ImageTk.PhotoImage(img)
        except Exception:
            pass
        # Fallback: Tk's own PhotoImage (PNG/GIF only) via base64 data.
        try:
            import base64
            img = tk.PhotoImage(data=base64.b64encode(data).decode("ascii"))
            factor = max(1, img.width() // self.MAX_PREVIEW[0])
            if factor > 1:
                img = img.subsample(factor, factor)
            return img
        except tk.TclError:
            return None


# ─────────────────────────────────────────────
#  MAIN APPLICATION
# ─────────────────────────────────────────────
class AdminScreen(tk.Tk):

    def __init__(self, db: Database | None = None, login_user_id=None):
        super().__init__()
        self.db = db or Database()
        self.current_user_id = login_user_id

        # Only Administration members may open this screen. Identity comes from
        # the token; the server makes the call. Fails closed.
        if not self.db.user_in_group(login_user_id, ADMIN_GROUP):
            self.destroy()
            raise AdminAccessDenied(
                "You are not a member of the Administration group.")

        self.title("Administration")
        self.geometry("1400x800")
        self.minsize(1000, 600)
        self.configure(bg=C_BG)

        self._apply_styles()
        self._build_ui()
        self._load_users()
        self._load_keywords()
        self._load_groups()

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
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        self._build_users_panel(body)
        self._build_right_panel(body)
        self._build_footer()

    def _build_header(self):
        hdr = tk.Frame(self, bg=C_HEADER_BG, height=70)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        branding.add_logo(hdr, self, bg=C_HEADER_BG)

        tk.Label(hdr, text="Administration",
                 font=FONT_TITLE, bg=C_HEADER_BG, fg="white").pack(
            side="left", padx=(0, 0) if branding.has_logo(self) else 24,
            pady=14)
        tk.Label(hdr, text=appconfig.active_config().display_name,
                 font=("Georgia", 11, "italic"),
                 bg=C_HEADER_BG, fg=C_HEADER_ACC).pack(side="left", padx=12)

    def _build_users_panel(self, parent):
        outer = tk.Frame(parent, bg=C_PANEL,
                         highlightthickness=1, highlightbackground=C_BORDER)
        outer.grid(row=0, column=0, sticky="NSEW", padx=(0, 6))
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(1, weight=1)

        # Panel header
        ph = tk.Frame(outer, bg=C_HEADER_BG)
        ph.grid(row=0, column=0, sticky="EW")
        tk.Label(ph, text="Users", font=FONT_SECTION,
                 bg=C_HEADER_BG, fg="white",
                 padx=14, pady=8).pack(side="left")
        make_button(ph, "+ New User",
                    lambda: launch(Config.USER_APP),
                    "primary", 10).pack(side="right", padx=10, pady=6)
        make_button(ph, "Signature",
                    self._on_manage_signature,
                    "ghost", 10).pack(side="right", padx=0, pady=6)

        # Treeview
        tree_frame = tk.Frame(outer, bg=C_PANEL)
        tree_frame.grid(row=1, column=0, sticky="NSEW", padx=8, pady=8)
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        cols = ("userid", "firstname", "lastname", "username", "email")
        self.user_tree = ttk.Treeview(tree_frame, columns=cols,
                                       show="headings", selectmode="browse")

        col_config = [
            ("userid",    "ID",         0,   False),
            ("firstname", "First Name", 160, True),
            ("lastname",  "Last Name",  160, True),
            ("username",  "Username",   140, True),
            ("email",     "Email",      0,   True),
        ]
        for col_id, heading, width, stretch in col_config:
            self.user_tree.heading(col_id, text=heading)
            self.user_tree.column(col_id, width=width, stretch=stretch)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical",
                            command=self.user_tree.yview)
        self.user_tree.configure(yscrollcommand=vsb.set)
        self.user_tree.grid(row=0, column=0, sticky="NSEW")
        vsb.grid(row=0, column=1, sticky="NS")

        # Double-click to edit so plain selection / keyboard nav doesn't
        # spawn windows.
        self.user_tree.bind("<Double-1>", self._on_user_activate)

        # Row count label
        self.user_count_label = tk.Label(outer, text="", bg=C_PANEL,
                                         font=FONT_SMALL, fg=C_TEXT_MUTED,
                                         padx=10, pady=4)
        self.user_count_label.grid(row=2, column=0, sticky="W")

    def _build_right_panel(self, parent):
        right = tk.Frame(parent, bg=C_BG)
        right.grid(row=0, column=1, sticky="NSEW")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)
        right.rowconfigure(2, weight=1)

        # Applications
        req_frame = tk.Frame(right, bg=C_PANEL,
                             highlightthickness=1, highlightbackground=C_BORDER)
        req_frame.grid(row=0, column=0, sticky="EW", pady=(0, 6))

        tk.Label(req_frame, text="Applications", font=FONT_SECTION,
                 bg=C_PANEL, fg=C_HEADER_BG,
                 padx=14, pady=8).pack(fill="x")
        tk.Frame(req_frame, bg=C_HEADER_ACC, height=2).pack(fill="x", padx=14)

        btn_inner = tk.Frame(req_frame, bg=C_PANEL, padx=14, pady=10)
        btn_inner.pack(fill="x")
        make_button(btn_inner, "Requisitions",
                    lambda: launch(Config.REQUISITION_APP, self.current_user_id)
                            if self.current_user_id is not None
                            else launch(Config.REQUISITION_APP),
                    "primary", 14).pack(fill="x", pady=4)

        # Keywords panel
        kw_frame = tk.Frame(right, bg=C_PANEL,
                            highlightthickness=1, highlightbackground=C_BORDER)
        kw_frame.grid(row=1, column=0, sticky="NSEW", pady=(0, 0))
        kw_frame.columnconfigure(0, weight=1)
        kw_frame.rowconfigure(1, weight=1)

        tk.Label(kw_frame, text="Keywords", font=FONT_SECTION,
                 bg=C_PANEL, fg=C_HEADER_BG,
                 padx=14, pady=8).pack(fill="x")
        tk.Frame(kw_frame, bg=C_HEADER_ACC, height=2).pack(fill="x", padx=14)
        tk.Label(kw_frame, text="Select a table to manage its values",
                 font=FONT_SMALL, fg=C_TEXT_MUTED,
                 bg=C_PANEL, padx=14, pady=4).pack(anchor="w")

        lb_frame = tk.Frame(kw_frame, bg=C_PANEL, padx=14, pady=6)
        lb_frame.pack(fill="both", expand=True)
        lb_frame.columnconfigure(0, weight=1)
        lb_frame.rowconfigure(0, weight=1)

        self.keyword_listbox = tk.Listbox(
            lb_frame,
            font=FONT_ENTRY,
            relief="flat", bd=0,
            bg=C_ROW_ALT, fg=C_TEXT,
            selectbackground=C_PRIMARY, selectforeground="white",
            activestyle="none",
        )
        kw_vsb = ttk.Scrollbar(lb_frame, orient="vertical",
                               command=self.keyword_listbox.yview)
        self.keyword_listbox.configure(yscrollcommand=kw_vsb.set)
        self.keyword_listbox.grid(row=0, column=0, sticky="NSEW")
        kw_vsb.grid(row=0, column=1, sticky="NS")

        self.keyword_listbox.bind("<<ListboxSelect>>", self._on_keyword_select)

        # Groups panel
        grp_frame = tk.Frame(right, bg=C_PANEL,
                             highlightthickness=1, highlightbackground=C_BORDER)
        grp_frame.grid(row=2, column=0, sticky="NSEW", pady=(6, 0))
        grp_frame.columnconfigure(0, weight=1)
        grp_frame.rowconfigure(1, weight=1)

        grp_hdr = tk.Frame(grp_frame, bg=C_PANEL)
        grp_hdr.pack(fill="x")
        tk.Label(grp_hdr, text="Groups", font=FONT_SECTION,
                 bg=C_PANEL, fg=C_HEADER_BG,
                 padx=14, pady=8).pack(side="left")
        make_button(grp_hdr, "+ New Group", self._on_new_group,
                    "primary", 11).pack(side="right", padx=10, pady=6)
        tk.Frame(grp_frame, bg=C_HEADER_ACC, height=2).pack(fill="x", padx=14)
        tk.Label(grp_frame, text="Select a group to manage its members",
                 font=FONT_SMALL, fg=C_TEXT_MUTED,
                 bg=C_PANEL, padx=14, pady=4).pack(anchor="w")

        glb_frame = tk.Frame(grp_frame, bg=C_PANEL, padx=14, pady=6)
        glb_frame.pack(fill="both", expand=True)
        glb_frame.columnconfigure(0, weight=1)
        glb_frame.rowconfigure(0, weight=1)

        self.group_listbox = tk.Listbox(
            glb_frame,
            font=FONT_ENTRY,
            relief="flat", bd=0,
            bg=C_ROW_ALT, fg=C_TEXT,
            selectbackground=C_PRIMARY, selectforeground="white",
            activestyle="none",
        )
        grp_vsb = ttk.Scrollbar(glb_frame, orient="vertical",
                                command=self.group_listbox.yview)
        self.group_listbox.configure(yscrollcommand=grp_vsb.set)
        self.group_listbox.grid(row=0, column=0, sticky="NSEW")
        grp_vsb.grid(row=0, column=1, sticky="NS")

        self.group_listbox.bind("<<ListboxSelect>>", self._on_group_select)

        # Maps the listbox row index -> (GroupID, GroupName).
        self._group_index: list[tuple[int, str]] = []

    def _build_footer(self):
        tk.Frame(self, bg=C_BORDER, height=1).pack(fill="x")
        footer = tk.Frame(self, bg=C_PANEL, padx=20, pady=10)
        footer.pack(fill="x", side="bottom")
        make_button(footer, "Close", self.destroy, "danger", 10
                    ).pack(side="right", padx=4)

    # ── Data loading ──────────────────────────────────────────────────────────

    def _load_users(self):
        for item in self.user_tree.get_children():
            self.user_tree.delete(item)

        try:
            rows = self.db.fetch_users()
        except pyodbc.Error as exc:
            log.exception("admin error")
            messagebox.showerror("Load Error", str(exc))
            rows = []

        for row in rows:
            self.user_tree.insert("", "end",
                                  iid=str(row[0]),
                                  values=(row[0], row[1], row[2], row[3], row[4]))

        count = len(rows)
        self.user_count_label.config(
            text=f"{count} user{'s' if count != 1 else ''}"
        )

    def _load_keywords(self):
        self.keyword_listbox.delete(0, "end")
        try:
            names = self.db.keyword_tables(refresh=True)
        except pyodbc.Error as exc:
            log.exception("admin error")
            messagebox.showerror("Load Error", str(exc))
            names = []
        for name in names:
            self.keyword_listbox.insert("end", name)

    def _load_groups(self):
        self.group_listbox.delete(0, "end")
        self._group_index = []
        try:
            self.db.ensure_core_groups()      # make sure the four always exist
            groups = self.db.fetch_groups()
        except pyodbc.Error as exc:
            log.exception("admin error")
            messagebox.showerror(
                "Load Error",
                "Could not load groups. Has groups_schema.sql been run?\n\n"
                f"{exc}")
            return
        for group_id, name, member_count in groups:
            self.group_listbox.insert("end", f"{name}  ({member_count})")
            self._group_index.append((group_id, name))

    # ── Interactions ──────────────────────────────────────────────────────────

    def _on_user_activate(self, _event):
        user_id = self.user_tree.focus()
        if not user_id:
            return
        # Pass the selected ID along; User.pyw can read it from argv when ready.
        launch(Config.USER_APP, user_id)

    def _on_manage_signature(self):
        user_id = self.user_tree.focus()
        if not user_id:
            messagebox.showinfo(
                "Select a user",
                "Select a user in the list first, then click Signature.")
            return
        values = self.user_tree.item(user_id, "values")
        # values = (UserID, FirstName, LastName, Username, Email)
        name = f"{values[1]} {values[2]}" if values else user_id
        SignatureWindow(self, self.db, int(user_id), name)

    def _on_keyword_select(self, _event):
        selection = self.keyword_listbox.curselection()
        if not selection:
            return
        table_name = self.keyword_listbox.get(selection[0])
        KeywordWindow(self, self.db, table_name)

    def _on_group_select(self, _event):
        selection = self.group_listbox.curselection()
        if not selection:
            return
        group_id, group_name = self._group_index[selection[0]]
        win = GroupWindow(self, self.db, group_id, group_name)
        # Refresh member counts once the membership window is closed.
        win.bind("<Destroy>",
                 lambda e: self._load_groups() if e.widget is win else None)

    def _on_new_group(self):
        name = simpledialog.askstring(
            "New Group", "Group name:", parent=self)
        if not name or not name.strip():
            return
        try:
            self.db.create_group(name.strip())
        except pyodbc.Error as exc:
            log.exception("admin error")
            messagebox.showerror("Error", f"Could not create group:\n{exc}")
            return
        self._load_groups()


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    # First CLI arg is the authenticated UserID passed by the login screen.
    login_user_id = None
    if len(sys.argv) > 1:
        try:
            login_user_id = int(sys.argv[1])
        except ValueError:
            log.warning("ignoring non-numeric user id arg: %r", sys.argv[1])

    # Resolve the active customer before anything touches the database.
    try:
        appconfig.active_config()
    except appconfig.ConfigError as exc:
        warn = tk.Tk()
        warn.withdraw()
        messagebox.showerror("Configuration error", str(exc))
        warn.destroy()
        sys.exit(1)

    try:
        app = AdminScreen(login_user_id=login_user_id)
    except AdminAccessDenied as exc:
        # Need a fresh hidden root to host the dialog (the denied one is gone).
        warn = tk.Tk()
        warn.withdraw()
        messagebox.showerror("Access denied", str(exc))
        warn.destroy()
        sys.exit(1)

    app.mainloop()
