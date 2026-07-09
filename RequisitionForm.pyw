import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog, font
import os
import io
from datetime import date

import requests
import branding

from reqform_db import (
    load_lists, fetch_users, generate_doc_number, load_session,
    fetch_requisition, fetch_items, fetch_history, fetch_attachments,
    fetch_approvers, save_requisition, submit_requisition,
    upload_attachment, delete_attachment, download_attachment,
)

# ---------------------------------------------
#  DESIGN TOKENS
# ---------------------------------------------
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

# ---------------------------------------------
#  LIST / LAYOUT CONSTANTS
# ---------------------------------------------
DOC_PREFIXES = {
    "Transport":      "TRAN-",
    "Infrastructure": "INFR-",
    "Household":      "HSLD-",
    "Kitchen":        "KTCN-",
}

TRIP_CATEGORIES = ("Transport",)
ITEMS_CATEGORIES = ("Kitchen", "Household", "Stationery")
FARM_SITES = ("Farm",)

ITEM_COLUMNS_DEFAULT = [
    ("Item_Name",          "Items to be purchased",                    "text", 5),
    ("Amt_In_Stock",       "Amt. In Stock",                            "text", 2),
    ("Quantity_Requested", "Quantity Requested",                       "text", 2),
    ("Comments",           "Comments (Ex: Special Occasion or Usage)", "text", 5),
]
ITEM_COLUMNS_FARM = [
    ("Item_Name",          "Items to be purchased", "text",  6),
    ("Amt_In_Stock",       "Amt. In Stock",         "text",  2),
    ("Quantity_Requested", "Quantity Requested",    "text",  2),
    ("Broiler",            "Broiler",               "check", 1),
    ("Layer",              "Layer",                 "check", 1),
    ("Pigs",               "Pigs",                  "check", 1),
    ("Gen_Supply",         "Gen. Sup/main",         "check", 1),
]

# ---------------------------------------------
#  PHASES
# ---------------------------------------------
PHASES_STANDARD    = ["Draft", "HOD Review", "VP Review",
                      "Principal Approval", "Procurement", "Accounts", "Completed"]
PHASES_MAINTENANCE = ["Draft", "HOD Review", "VP Review", "Maintenance Unit",
                      "VP Approval", "Principal Approval", "Procurement", "Accounts", "Completed"]
PHASES_TRANSPORT   = ["Draft", "HOD Review", "VP Approval", "Accounts", "Completed"]

def get_phases(category, via_maintenance=False):
    if category == "Transport":
        return PHASES_TRANSPORT
    if via_maintenance:
        return PHASES_MAINTENANCE
    return PHASES_STANDARD

# ---------------------------------------------
#  WIDGET FACTORIES
# ---------------------------------------------
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

# ---------------------------------------------
#  PHASE TRACKER
# ---------------------------------------------
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

# ---------------------------------------------
#  PDF EXPORT
# ---------------------------------------------
def build_requisition_pdf(path, data):
    """Render a requisition to a PDF at `path`. Requires 'reportlab'."""
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.lib.utils import ImageReader
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                     Table, TableStyle, Image as RLImage)

    NAVY = colors.HexColor("#1A2B4A")
    styles = getSampleStyleSheet()
    title = ParagraphStyle("t", parent=styles["Title"], fontSize=16, spaceAfter=2)
    sub = ParagraphStyle("s", parent=styles["Heading2"], fontSize=12,
                         textColor=NAVY, spaceAfter=8)
    head = ParagraphStyle("h", parent=styles["Heading4"], textColor=NAVY,
                          spaceBefore=10, spaceAfter=3)
    body = styles["BodyText"]

    def para(text):
        return Paragraph(str(text or "").replace("\n", "<br/>"), body)

    doc = SimpleDocTemplate(
        path, pagesize=letter, title=f"Requisition {data.get('document_number','')}",
        leftMargin=0.7 * inch, rightMargin=0.7 * inch,
        topMargin=0.7 * inch, bottomMargin=0.7 * inch)
    elems = [Paragraph("Church Teachers College", title),
             Paragraph("Requisition", sub)]

    def info_block(pairs):
        rows = [[Paragraph(f"<b>{k}</b>", body), para(v)]
                for k, v in pairs if v not in (None, "")]
        if not rows:
            return
        t = Table(rows, colWidths=[1.7 * inch, 5.0 * inch])
        t.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))
        elems.append(t)

    summary = [
        ("Document #", data.get("document_number")),
        ("Created By", data.get("created_by")),
        ("Site", data.get("site")),
        ("Category", data.get("category")),
        ("Dept & Units", data.get("department")),
        ("Maintenance Area", data.get("maintenance")),
        ("Academic Dept", data.get("academic")),
        ("Purchased At", data.get("supplier")),
        ("Purpose", data.get("purpose")),
        ("Cost", data.get("cost")),
        ("Current Phase", data.get("phase")),
    ]
    if data.get("category") == "Transport":
        summary += [("Date of Trip", data.get("trip_date")),
                    ("Destination", data.get("destination")),
                    ("Time of Departure", data.get("departure_time"))]
    info_block(summary)

    def items_table(header, rows, weights):
        avail = 7.0 * inch
        widths = [avail * w / sum(weights) for w in weights]
        tdata = [[Paragraph(f"<b>{h}</b>", body) for h in header]]
        tdata += rows
        t = Table(tdata, colWidths=widths, repeatRows=1)
        t.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D8D0C8")),
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (1, 1), (-1, -1), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        elems.append(t)

    mode = data.get("items_mode")
    items = data.get("items") or []
    if mode == "farm":
        elems.append(Paragraph("Items", head))
        rows = [[para(it.get("Item_Name")), it.get("Amt_In_Stock", ""),
                 it.get("Quantity_Requested", ""),
                 "X" if it.get("Broiler") else "", "X" if it.get("Layer") else "",
                 "X" if it.get("Pigs") else "", "X" if it.get("Gen_Supply") else ""]
                for it in items]
        items_table(["Items to be purchased", "Amt. In Stock", "Quantity Requested",
                     "Broiler", "Layer", "Pigs", "Gen. Sup/main"],
                    rows, [6, 2, 2, 1, 1, 1, 1.5])
    elif mode == "comments":
        elems.append(Paragraph("Items", head))
        rows = [[para(it.get("Item_Name")), it.get("Amt_In_Stock", ""),
                 it.get("Quantity_Requested", ""), para(it.get("Comments"))]
                for it in items]
        items_table(["Items to be purchased", "Amt. In Stock",
                     "Quantity Requested", "Comments"], rows, [5, 2, 2, 5])
    elif data.get("requesting"):
        elems.append(Paragraph("Items Requested", head))
        elems.append(para(data.get("requesting")))

    for label, key in [("Scope of Work", "scope"), ("Contractor(s)", "contractor"),
                       ("List of Materials", "material"),
                       ("HOD Comment", "hod_comment"),
                       ("VP Reviewer Notes", "vp_comment"),
                       ("VP Approver Comments", "vp_approval"),
                       ("Principal Comments", "principal_comment")]:
        if data.get(key):
            elems.append(Paragraph(label, head))
            elems.append(para(data.get(key)))

    elems.append(Spacer(1, 16))
    elems.append(Paragraph("Approvals & Accounts", head))

    approvers = data.get("approvers") or {}

    def sig_flowable(info):
        if info and info.get("image"):
            try:
                bio = io.BytesIO(info["image"])
                iw, ih = ImageReader(bio).getSize()
                h = 0.5 * inch
                w = min(2.0 * inch, h * iw / ih) if ih else 1.5 * inch
                bio.seek(0)
                return RLImage(bio, width=w, height=h)
            except Exception:
                pass
        return Spacer(1, 0.5 * inch)

    sig_imgs, sig_caps = [], []
    for key, label in (("hod", "HOD"), ("vp", "VP"), ("principal", "Principal")):
        info = approvers.get(key)
        sig_imgs.append(sig_flowable(info))
        name = (info or {}).get("name") or ""
        sig_caps.append(Paragraph(f"<b>{label}</b><br/>{name}", body))

    sig_table = Table([sig_imgs, sig_caps], colWidths=[2.33 * inch] * 3)
    sig_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, 0), "BOTTOM"),
        ("VALIGN", (0, 1), (-1, 1), "TOP"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("LINEABOVE", (0, 1), (-1, 1), 0.5, NAVY),
        ("TOPPADDING", (0, 1), (-1, 1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
    ]))
    elems.append(sig_table)
    elems.append(Spacer(1, 8))

    info_block([
        ("Receipt Acknowledged (Accounts)",
         "Yes" if data.get("accounts_acknowledged") else "No"),
    ])
    doc.build(elems)
    return path


# ---------------------------------------------
#  MAIN APPLICATION
# ---------------------------------------------
class RequisitionForm(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Requisition Management")
        self.geometry("1400x900")
        self.minsize(1100, 700)
        self.configure(bg=C_BG)
        self.state("zoomed")

        self.today = date.today()

        # Load dropdown lists from the API
        lists = load_lists()
        self.SITE_LIST        = lists["site"]
        self.CATEGORY_LIST    = lists["category"]
        self.MAINTENANCE_LIST = lists["maintenance"]
        self.DEPT_LIST        = lists["department"]
        self.ACADEMIC_LIST    = lists["academic"]

        self.status_var      = tk.StringVar(value="Ready")
        self.doc_var         = tk.StringVar()
        self.mvar            = tk.BooleanVar()
        self.accounts_ack_var = tk.BooleanVar()
        self.send_kitchen_var     = tk.BooleanVar()
        self.send_household_var   = tk.BooleanVar()
        self.send_it_var          = tk.BooleanVar()
        self.send_maintenance_var = tk.BooleanVar()
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
        self.current_user_id = None
        self.current_phase   = ""
        self.assigned_to     = ""

        self._apply_styles()
        self._build_ui()

        (self.current_user_id, user_name,
         doc_number, req_row, assigned_to) = load_session()
        self.current_user_name = user_name or ""
        if user_name:
            self.logon_user_var.set(f"  {user_name}  ")
        self.assigned_to = assigned_to if assigned_to is not None else ""

        # New requisition (no existing row loaded): default Created By to the
        # logged-in user. Existing requisitions keep their saved Created By.
        if not req_row and user_name:
            self.createdBy_entry.insert(0, user_name)

        if doc_number:
            self.docNumber_entry.config(state="normal")
            self.doc_var.set(doc_number)
            self.docNumber_entry.config(state="readonly")

        if req_row:
            self._populate_fields(req_row)

        self.after(100, self._reload_phase_from_db)

    # -- Styles ----------------------------------------------------------------

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

    # -- UI construction -------------------------------------------------------

    def _build_ui(self):
        self._build_header()
        self._build_phase_band()
        self._build_status_bar()    # bottom-anchored, packed first
        self._build_button_bar()    # bottom-anchored, packed before body
        self._build_body()          # fills the remaining space
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

    # -- Tab 1 -----------------------------------------------------------------

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
        self.site_entry.bind("<<ComboboxSelected>>", self._on_site_selected)

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

        # Trip fields (shown when Category is in TRIP_CATEGORIES)
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
        
        # Send to Department(s) — shown/editable at VP Review
        self.send_dept_frame = tk.Frame(info, bg=C_PANEL)
        self.send_dept_frame.grid(row=7, column=0, columnspan=6,
                                  sticky="w", pady=(4, 6))
        tk.Label(self.send_dept_frame, text="Send to Department(s):",
                 font=FONT_LABEL, bg=C_PANEL, fg=C_HEADER_BG).pack(
            side="left", padx=(0, 12))
        self.send_kitchen_check = tk.Checkbutton(
            self.send_dept_frame, text="Kitchen", variable=self.send_kitchen_var,
            font=FONT_CAPTION, bg=C_PANEL, fg=C_TEXT,
            activebackground=C_PANEL, selectcolor=C_PANEL, cursor="hand2")
        self.send_kitchen_check.pack(side="left", padx=6)
        self.send_household_check = tk.Checkbutton(
            self.send_dept_frame, text="Household", variable=self.send_household_var,
            font=FONT_CAPTION, bg=C_PANEL, fg=C_TEXT,
            activebackground=C_PANEL, selectcolor=C_PANEL, cursor="hand2")
        self.send_household_check.pack(side="left", padx=6)
        self.send_it_check = tk.Checkbutton(
            self.send_dept_frame, text="IT", variable=self.send_it_var,
            font=FONT_CAPTION, bg=C_PANEL, fg=C_TEXT,
            activebackground=C_PANEL, selectcolor=C_PANEL, cursor="hand2")
        self.send_it_check.pack(side="left", padx=6)
        self.send_maintenance_check = tk.Checkbutton(
            self.send_dept_frame, text="Maintenance", variable=self.send_maintenance_var,
            font=FONT_CAPTION, bg=C_PANEL, fg=C_TEXT,
            activebackground=C_PANEL, selectcolor=C_PANEL, cursor="hand2")
        self.send_maintenance_check.pack(side="left", padx=6)
        self.send_dept_frame.grid_remove()   # hidden until VP Review

        # Items Requested
        self.req_outer, req_inner = card(sf, "Items Requested", row=1, col=0, pady=0)
        make_label(req_inner, "List all items being requested:",
                   f=FONT_SMALL, fg=C_TEXT_MUTED, bg=C_PANEL).pack(
            anchor="w", pady=(0, 4))
        self.requestingText = make_scrolled(req_inner, height=12)
        self.requestingText.pack(fill="both", expand=True)

        # Items to be Purchased - structured table.
        self.item_rows = []
        self._item_cols = ITEM_COLUMNS_DEFAULT
        self._items_built_mode = "comments"
        self._item_data_start = 2
        self._next_item_grid_row = 2
        self.items_outer, items_inner = card(
            sf, "Items to be Purchased", row=1, col=0, pady=0)

        self.items_grid = tk.Frame(items_inner, bg=C_PANEL)
        self.items_grid.pack(fill="x")

        items_btn_row = tk.Frame(items_inner, bg=C_PANEL)
        items_btn_row.pack(fill="x", pady=(8, 0))
        self.add_item_btn = make_button(
            items_btn_row, "Add Row", self._add_item_row, "ghost", 10)
        self.add_item_btn.pack(side="left")

        self._build_items_header()
        self.items_outer.grid_remove()

        # Attachments
        self.att_outer, att_inner = card(sf, "Attachments", row=3, col=0, pady=8)

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
        self.hod_outer, hod_inner = card(sf, "HOD Comment", row=4, col=0, pady=8)
        self.HODcomment_entry = make_scrolled(hod_inner, height=4)
        self.HODcomment_entry.pack(fill="both", expand=True)

        # VP Reviewer Notes
        self.vp_outer, vp_inner = card(sf, "VP Reviewer Notes", row=5, col=0, pady=0)
        self.vpReviewerText = make_scrolled(vp_inner, height=4)
        self.vpReviewerText.pack(fill="both", expand=True)

        # Principal Comments
        self.prin_outer, prin_inner = card(sf, "Principal Comments", row=6, col=0, pady=8)
        self.principalText = make_scrolled(prin_inner, height=5)
        self.principalText.pack(fill="both", expand=True)

        # Cost
        self.cost_outer, cost_inner = card(sf, "Cost", row=2, col=0, pady=8)
        cost_inner.columnconfigure(1, weight=1)
        make_label(cost_inner, "Cost", bg=C_PANEL).grid(
            row=0, column=0, sticky="e", padx=(0, 6), pady=6)
        self.costEntry = tk.Entry(
            cost_inner, font=FONT_ENTRY, relief="flat", bd=4, bg=C_PANEL, fg=C_TEXT,
            highlightbackground=C_BORDER, highlightthickness=1)
        self.costEntry.grid(row=0, column=1, sticky="ew", pady=6)

        # Approvals & Accounts
        self.acct_outer, acct_inner = card(
            sf, "Approvals & Accounts", row=7, col=0, pady=8)
        acct_inner.columnconfigure(1, weight=1)

        make_label(acct_inner, "VP Signature", bg=C_PANEL).grid(
            row=0, column=0, sticky="e", padx=(0, 6), pady=6)
        vp_sig_row = tk.Frame(acct_inner, bg=C_PANEL)
        vp_sig_row.grid(row=0, column=1, sticky="ew", pady=6)
        vp_sig_row.columnconfigure(0, weight=1)
        self.vpSignatureEntry = tk.Entry(
            vp_sig_row, font=FONT_ENTRY, relief="flat", bd=4, bg=C_PANEL, fg=C_TEXT,
            highlightbackground=C_BORDER, highlightthickness=1)
        self.vpSignatureEntry.grid(row=0, column=0, sticky="ew")

        make_label(acct_inner, "Principal Signature", bg=C_PANEL).grid(
            row=1, column=0, sticky="e", padx=(0, 6), pady=6)
        prin_sig_row = tk.Frame(acct_inner, bg=C_PANEL)
        prin_sig_row.grid(row=1, column=1, sticky="ew", pady=6)
        prin_sig_row.columnconfigure(0, weight=1)
        self.principalSignatureEntry = tk.Entry(
            prin_sig_row, font=FONT_ENTRY, relief="flat", bd=4, bg=C_PANEL, fg=C_TEXT,
            highlightbackground=C_BORDER, highlightthickness=1)
        self.principalSignatureEntry.grid(row=0, column=0, sticky="ew")

        self.acctAckCheck = tk.Checkbutton(
            acct_inner, text="Acknowledge receipt of the requisition (Accounts)",
            variable=self.accounts_ack_var, font=FONT_CAPTION, bg=C_PANEL,
            fg=C_TEXT, activebackground=C_PANEL, selectcolor=C_PANEL, cursor="hand2")
        self.acctAckCheck.grid(row=2, column=0, columnspan=2, sticky="w", pady=6)

    # -- Tab 2 -----------------------------------------------------------------

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

    # -- Tab 3 -----------------------------------------------------------------

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

    # -- Button bar & status ---------------------------------------------------

    def _build_button_bar(self):
        tk.Frame(self, bg=C_BORDER, height=1).pack(fill="x")
        bar = tk.Frame(self, bg=C_PANEL, padx=20, pady=12)
        bar.pack(fill="x", side="bottom")
        make_button(bar, "Close",  self.destroy,             "danger",  10).pack(side="right", padx=6)
        make_button(bar, "Submit", self._open_submit_window, "success", 10).pack(side="right", padx=6)
        make_button(bar, "Save",   self._save_draft,         "primary", 10).pack(side="right", padx=6)
        make_button(bar, "Print PDF", self._print_pdf,       "ghost",   10).pack(side="right", padx=6)

    def _build_status_bar(self):
        bar = tk.Frame(self, bg=C_HEADER_BG, height=32)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)
        tk.Label(bar, textvariable=self.status_var,
                 font=("Verdana", 9), bg=C_HEADER_BG, fg="#94A3B8").pack(
            side="left", padx=16, pady=6)

    # -- Populate from DB row --------------------------------------------------

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
        self.costEntry.insert(0, safe("Cost"))
        self.vpSignatureEntry.insert(0, safe("VP_Signature"))
        self.principalSignatureEntry.insert(0, safe("Principal_Signature"))
        self.accounts_ack_var.set(bool(safe("Accounts_Acknowledged")))
        self.send_kitchen_var.set(bool(safe("Send_Kitchen")))
        self.send_household_var.set(bool(safe("Send_Household")))
        self.send_it_var.set(bool(safe("Send_IT")))
        self.send_maintenance_var.set(bool(safe("Send_Maintenance")))

        if safe("Category") == "Infrastructure":
            self.maintenance_label.grid()
            self.maintenance_entry.grid()
        if safe("Category") in TRIP_CATEGORIES:
            self._show_transport_fields()
        if safe("Department") == "Academic":
            self.academic_label.grid()
            self.academic_entry.grid()

    def _populate_history(self, doc_number):
        for item in self.historyTree.get_children():
            self.historyTree.delete(item)
        if not doc_number:
            return
        for i, hr in enumerate(fetch_history(doc_number)):
            self.historyTree.insert(
                "", "end", iid=i, text="",
                values=(hr[0], hr[1], hr[2], hr[3], hr[4], hr[5]))
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

        row = fetch_requisition(doc_number)
        if row is not None:
            self.current_phase = row.get("Phase") or ""
            self.assigned_to   = row.get("Assign_To") or ""
            if row.get("Category") and self.category_var.get() == "":
                self.category_var.set(row["Category"])
            if row.get("Maintenance_Unit") is not None:
                self.mvar.set(bool(row["Maintenance_Unit"]))

        self._refresh_tracker()
        self._update_mcheck_visibility()
        self._load_items()
        self._update_field_editability()
        if hasattr(self, "_request_type_radios"):
            self._update_tab_visibility()
            self._update_tab2_editability()
        self._populate_history(doc_number)
        self._load_attachments()

    def _config_item_columns(self, frame):
        for i in range(12):
            frame.columnconfigure(i, weight=0, minsize=0)
        cols = getattr(self, "_item_cols", ITEM_COLUMNS_DEFAULT)
        for i, (key, label, kind, weight) in enumerate(cols):
            frame.columnconfigure(
                i, weight=weight, minsize=(60 if kind == "check" else 0))
        frame.columnconfigure(len(cols), weight=0, minsize=34)

    def _items_mode(self):
        if self.site_entry.get() in FARM_SITES:
            return "farm"
        if self.category_entry.get() in ITEMS_CATEGORIES:
            return "comments"
        return None

    def _build_items_header(self):
        for w in self.items_grid.winfo_children():
            w.destroy()
        self._config_item_columns(self.items_grid)
        cols = self._item_cols
        check_idx = [i for i, c in enumerate(cols) if c[2] == "check"]
        hdr_row = 0
        if check_idx:
            first, last = check_idx[0], check_idx[-1]
            tk.Label(self.items_grid, text="Tick the appropriate unit",
                     font=("Verdana", 10, "bold"), bg=C_PANEL, fg=C_HEADER_BG,
                     anchor="center").grid(
                row=0, column=first, columnspan=last - first + 1,
                sticky="ew", pady=(0, 2))
            hdr_row = 1
        for i, (key, label, kind, weight) in enumerate(cols):
            tk.Label(self.items_grid, text=label, font=("Verdana", 10, "bold"),
                     bg=C_PANEL, fg=C_HEADER_BG, anchor="center",
                     justify="center",
                     wraplength=(70 if kind == "check" else 200)).grid(
                row=hdr_row, column=i, sticky="ew", padx=(0, 6), pady=(0, 2))
        sep_row = hdr_row + 1
        tk.Frame(self.items_grid, bg=C_HEADER_ACC, height=1).grid(
            row=sep_row, column=0, columnspan=len(cols) + 1,
            sticky="ew", pady=(0, 4))
        self._item_data_start = sep_row + 1
        self._next_item_grid_row = self._item_data_start

    def _ensure_items_mode(self, mode):
        if getattr(self, "_items_built_mode", None) == mode:
            return
        snapshot = self._snapshot_items()
        self._items_built_mode = mode
        self._item_cols = ITEM_COLUMNS_FARM if mode == "farm" \
            else ITEM_COLUMNS_DEFAULT
        self._clear_item_rows()
        self._build_items_header()
        for data in snapshot:
            self._add_item_row(data)

    def _add_item_row(self, values=None):
        r = self._next_item_grid_row
        self._next_item_grid_row += 1
        ref = {"row": r, "fields": {}, "widgets": [], "button": None}
        for i, (key, label, kind, weight) in enumerate(self._item_cols):
            if kind == "text":
                e = tk.Entry(self.items_grid, font=FONT_ENTRY, relief="flat", bd=4,
                             bg=C_PANEL, fg=C_TEXT,
                             highlightbackground=C_BORDER, highlightthickness=1)
                if values:
                    e.insert(0, str(values.get(key, "") or ""))
                e.grid(row=r, column=i, sticky="ew", padx=(0, 6), pady=2)
                ref["fields"][key] = ("text", e)
                ref["widgets"].append(e)
            else:  # check
                var = tk.BooleanVar(
                    value=bool(values.get(key)) if values else False)
                cb = tk.Checkbutton(
                    self.items_grid, variable=var, bg=C_PANEL,
                    activebackground=C_PANEL, selectcolor=C_PANEL, cursor="hand2")
                cb.grid(row=r, column=i, pady=2)
                ref["fields"][key] = ("check", var, cb)
                ref["widgets"].append(cb)
        btn = tk.Button(self.items_grid, text="\u2715",
                        command=lambda: self._remove_item_row(ref),
                        bg=C_DANGER, fg="white", font=("Verdana", 9, "bold"),
                        relief="flat", bd=0, width=2, cursor="hand2",
                        activebackground="#B91C1C", activeforeground="white")
        btn.grid(row=r, column=len(self._item_cols), pady=2)
        ref["button"] = btn
        ref["widgets"].append(btn)
        self.item_rows.append(ref)
        return ref

    def _remove_item_row(self, ref):
        if ref in self.item_rows:
            for w in ref["widgets"]:
                w.destroy()
            self.item_rows.remove(ref)
        if not self.item_rows:
            self._add_item_row()

    def _clear_item_rows(self):
        for ref in self.item_rows:
            for w in ref["widgets"]:
                w.destroy()
        self.item_rows = []
        self._next_item_grid_row = getattr(self, "_item_data_start", 2)

    def _row_data(self, ref):
        data = {"Item_Name": "", "Amt_In_Stock": "",
                "Quantity_Requested": "", "Comments": "",
                "Broiler": 0, "Layer": 0, "Pigs": 0, "Gen_Supply": 0}
        for key, field in ref["fields"].items():
            if field[0] == "text":
                data[key] = field[1].get()
            else:
                data[key] = 1 if field[1].get() else 0
        return data

    def _snapshot_items(self):
        return [self._row_data(ref) for ref in self.item_rows]

    def _collect_items(self):
        items = []
        for ref in self.item_rows:
            data = self._row_data(ref)
            if any(str(data[k]).strip() for k in
                   ("Item_Name", "Amt_In_Stock", "Quantity_Requested", "Comments")):
                items.append(data)
        return items

    def _load_items(self):
        mode = self._items_mode()
        if mode is None:
            self._clear_item_rows()
            return
        self._ensure_items_mode(mode)
        self._clear_item_rows()
        doc_number = self.doc_var.get().strip()
        if doc_number:
            for item in fetch_items(doc_number):
                self._add_item_row(item)
        if not self.item_rows:
            self._add_item_row()

    def _set_items_editable(self, editable):
        for ref in self.item_rows:
            for key, field in ref["fields"].items():
                if field[0] == "text":
                    field[1].config(state="normal" if editable else "readonly",
                                    bg=C_PANEL if editable else "#F0F0F0")
                else:
                    field[2].config(state="normal" if editable else "disabled")
            ref["button"].config(state="normal" if editable else "disabled")
        self.add_item_btn.config(state="normal" if editable else "disabled")

    def _update_items_visibility(self):
        mode = self._items_mode()
        if mode is None:
            self.items_outer.grid_remove()
            self.req_outer.grid()
        else:
            self._ensure_items_mode(mode)
            self.req_outer.grid_remove()
            self.items_outer.grid()
            if not self.item_rows:
                self._add_item_row()

    # -- Field event handlers --------------------------------------------------

    def _on_site_selected(self, event=None):
        self._update_items_visibility()
        self._set_items_editable(self.current_phase in ("", "Draft"))

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
        if selected in TRIP_CATEGORIES:
            self._show_transport_fields()
        else:
            self._hide_transport_fields(clear=True)
        self._update_items_visibility()
        self._set_items_editable(self.current_phase in ("", "Draft"))
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

        self._update_items_visibility()
        unlock(self.requestingText) if is_draft else lock(self.requestingText)
        self._set_items_editable(is_draft)

        if is_draft:
            hide(self.hod_outer)
        else:
            show(self.hod_outer)
            unlock(self.HODcomment_entry) if phase == "HOD Review" \
                else lock(self.HODcomment_entry)

        if phase in ("", "Draft", "HOD Review"):
            hide(self.vp_outer)
        else:
            show(self.vp_outer)
            unlock(self.vpReviewerText) if phase == "VP Review" \
                else lock(self.vpReviewerText)

        if phase in ("", "Draft", "HOD Review", "VP Review",
                     "Maintenance Unit", "VP Approval"):
            hide(self.prin_outer)
        else:
            show(self.prin_outer)
            unlock(self.principalText) if phase == "Principal Approval" \
                else lock(self.principalText)

        show(self.att_outer)

        (lock_entry if phase == "Accounts"
         else unlock_entry)(self.costEntry)

        if phase in ("", "Draft", "HOD Review"):
            hide(self.acct_outer)
        else:
            show(self.acct_outer)
            vp_ok = phase in ("VP Review", "VP Approval")
            (unlock_entry if vp_ok else lock_entry)(self.vpSignatureEntry)
            prin_ok = phase == "Principal Approval"
            (unlock_entry if prin_ok else lock_entry)(self.principalSignatureEntry)
            self.acctAckCheck.config(
                state="normal" if phase == "Accounts" else "disabled")
                
        # Send to Department(s): visible and editable only at VP Review
        if phase == "VP Review":
            self.send_dept_frame.grid()
            for cb in (self.send_kitchen_check, self.send_household_check,
                       self.send_it_check, self.send_maintenance_check):
                cb.config(state="normal")
        else:
            for cb in (self.send_kitchen_check, self.send_household_check,
                       self.send_it_check, self.send_maintenance_check):
                cb.config(state="disabled")
            # keep visible (read-only) if any are already set, else hide
            if any(v.get() for v in (self.send_kitchen_var, self.send_household_var,
                                     self.send_it_var, self.send_maintenance_var)):
                self.send_dept_frame.grid()
            else:
                self.send_dept_frame.grid_remove()

    def _assign_doc_number(self):
        if self.doc_var.get():
            return
        number = generate_doc_number(self.category_entry.get())
        if number:
            self.docNumber_entry.config(state="normal")
            self.doc_var.set(number)
            self.docNumber_entry.config(state="readonly")
            self.status_var.set(f"Document number assigned: {number}")

    # -- Attachments -----------------------------------------------------------

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
        added = 0
        for file_path in file_paths:
            file_name = os.path.basename(file_path)
            try:
                upload_attachment(doc_number, file_path)
                added += 1
            except Exception as exc:
                messagebox.showerror("Error",
                                     f"Failed to upload '{file_name}':\n{exc}")
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
            path = download_attachment(int(values[0]), values[1])
        except Exception as exc:
            messagebox.showerror("Error", str(exc))
            return
        try:
            os.startfile(path)
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
            f"Remove '{file_name}' from this requisition?"
        ):
            return
        try:
            delete_attachment(int(values[0]))
            self._load_attachments()
            self.status_var.set(f"Removed: {file_name}")
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    # -- Field payload ---------------------------------------------------------

    def _build_fields(self):
        return {
            "Site": self.site_entry.get(),
            "Category": self.category_entry.get(),
            "Maintenance": self.maintenance_var.get(),
            "Department": self.dept_entry.get(),
            "Academic": self.academic_entry.get(),
            "Supplier": self.supplierEntry.get(),
            "Purpose": self.purposeEntry.get(),
            "Requesting": st_get(self.requestingText),
            "HOD_Comment": st_get(self.HODcomment_entry),
            "VP_Comment": st_get(self.vpReviewerText),
            "Request_Type": self.request_option.get(),
            "Scope": st_get(self.scopeText),
            "Contractor": self.contractorEntry.get(),
            "Material": st_get(self.materialText),
            "VP_Approval": st_get(self.vpApproverText),
            "Principal_Comment": st_get(self.principalText),
            "Maintenance_Unit": 1 if self.mvar.get() else 0,
            "Trip_Date": self.tripDateEntry.get(),
            "Destination": self.destinationEntry.get(),
            "Departure_Time": self.departureTimeEntry.get(),
            "Cost": self.costEntry.get(),
            "VP_Signature": self.vpSignatureEntry.get(),
            "Principal_Signature": self.principalSignatureEntry.get(),
            "Accounts_Acknowledged": 1 if self.accounts_ack_var.get() else 0,
            "Send_Kitchen":     1 if self.send_kitchen_var.get() else 0,
            "Send_Household":   1 if self.send_household_var.get() else 0,
            "Send_IT":          1 if self.send_it_var.get() else 0,
            "Send_Maintenance": 1 if self.send_maintenance_var.get() else 0,
        }

    # -- Signatures & PDF ------------------------------------------------------

    def _print_pdf(self):
        doc_number = self.doc_var.get().strip()
        if not doc_number:
            messagebox.showwarning(
                "Missing", "Save the requisition before printing a PDF.")
            return
        mode = self._items_mode()
        data = {
            "document_number": doc_number,
            "created_by":      self.createdBy_entry.get(),
            "site":            self.site_entry.get(),
            "category":        self.category_entry.get(),
            "department":      self.dept_entry.get(),
            "maintenance":     self.maintenance_entry.get(),
            "academic":        self.academic_entry.get(),
            "supplier":        self.supplierEntry.get(),
            "purpose":         self.purposeEntry.get(),
            "cost":            self.costEntry.get(),
            "phase":           self.current_phase,
            "trip_date":       self.tripDateEntry.get(),
            "destination":     self.destinationEntry.get(),
            "departure_time":  self.departureTimeEntry.get(),
            "items_mode":      mode,
            "items":           self._collect_items() if mode else [],
            "requesting":      st_get(self.requestingText) if mode is None else "",
            "scope":           st_get(self.scopeText),
            "contractor":      self.contractorEntry.get(),
            "material":        st_get(self.materialText),
            "hod_comment":     st_get(self.HODcomment_entry),
            "vp_comment":      st_get(self.vpReviewerText),
            "vp_approval":     st_get(self.vpApproverText),
            "principal_comment": st_get(self.principalText),
            "accounts_acknowledged": self.accounts_ack_var.get(),
            "approvers":       fetch_approvers(doc_number),
        }
        path = filedialog.asksaveasfilename(
            title="Save PDF", defaultextension=".pdf",
            initialfile=f"{doc_number}.pdf", filetypes=[("PDF", "*.pdf")])
        if not path:
            return
        try:
            build_requisition_pdf(path, data)
        except ImportError:
            messagebox.showerror(
                "Missing Library",
                "PDF export needs the 'reportlab' package.\n\n"
                "Install it once with:\n    pip install reportlab")
            return
        except Exception as exc:
            messagebox.showerror("PDF Error", str(exc))
            return
        self.status_var.set(f"PDF saved: {path}")
        if messagebox.askyesno("PDF Created", "PDF saved. Open it now?"):
            try:
                os.startfile(path)
            except Exception as exc:
                messagebox.showerror("Error", str(exc))

    # -- Save draft ------------------------------------------------------------

    def _save_draft(self):
        doc = self.doc_var.get().strip()
        if not doc:
            messagebox.showwarning("Missing",
                                   "A document number is required before saving.")
            return
        try:
            save_requisition(doc, self._build_fields(), self._collect_items())
        except requests.RequestException as exc:
            messagebox.showerror("Database Error", str(exc))
            return
        self.status_var.set("Saved.")
        messagebox.showinfo("Saved", "Requisition saved.")
        self.after(300, self._reload_phase_from_db)

    # -- Submit window ---------------------------------------------------------

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

        # Branch: at VP Review, if any department box is ticked, the requisition
        # is routed to those departments and skips the rest of the approval chain.
        any_dept = any(v.get() for v in (
            self.send_kitchen_var, self.send_household_var,
            self.send_it_var, self.send_maintenance_var))
        if self.current_phase == "VP Review" and any_dept:
            next_phase = "Completed"
        else:
            next_phase = phases[current_idx + 1]

        # Completed is terminal — no assignee is chosen.
        completing = (next_phase == "Completed")
        user_list  = fetch_users() if not completing else []

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
        if completing:
            assignee_combo = None
            tk.Label(body, text="(No assignee — this completes the requisition)",
                     font=FONT_CAPTION, bg=C_BG, fg=C_TEXT_MUTED).grid(
                row=2, column=0, columnspan=2, sticky="w", pady=6)
        else:
            assignee_combo = ttk.Combobox(body, values=user_list,
                                          state="readonly", font=FONT_ENTRY)
            frow("Assigned To", assignee_combo, 2)

        bf = tk.Frame(win, bg=C_BG, padx=28, pady=10)
        bf.pack(fill="x")

        def do_submit():
            if not completing and not assignee_combo.get():
                messagebox.showwarning("Required", "Please select an assignee.")
                return
            assignee = "" if completing else assignee_combo.get()
            try:
                submit_requisition(
                    doc_number, self._build_fields(), self._collect_items(),
                    assignee, self.current_phase,
                    comments=st_get(self.HODcomment_entry))
            except requests.HTTPError as exc:
                # 403 = not your assignment, 409 = phase changed / already final
                detail = (exc.response.json().get("detail")
                          if exc.response is not None else str(exc))
                messagebox.showerror("Submit", detail)
                return
            except requests.RequestException as exc:
                messagebox.showerror("Error", str(exc))
                return
            self.status_var.set("Submitted successfully.")
            win.destroy()
            self.after(300, self._reload_phase_from_db)

        make_button(bf, "Cancel", win.destroy, "ghost",   10).pack(side="right", padx=6)
        make_button(bf, "Submit", do_submit,   "success", 10).pack(side="right", padx=6)


# ---------------------------------------------
#  ENTRY POINT
# ---------------------------------------------
if __name__ == "__main__":
    app = RequisitionForm()
    app.mainloop()
