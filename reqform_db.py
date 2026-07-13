"""
reqform_db.py - client data layer for the Requisition form (local dev).

Same function names/return shapes the form expects, so the UI is unchanged.
Token comes from CTC_AUTH_TOKEN, which the requisition screen sets in the
environment before launching the form.
"""

import os
import base64
import tempfile

import requests
import applog

log = applog.get_logger("reqform")

_BASE = os.environ.get("CTC_API_BASE", "http://localhost:8000").rstrip("/")
_session = requests.Session()
_token = os.environ.get("CTC_AUTH_TOKEN")
if _token:
    _session.headers["Authorization"] = f"Bearer {_token}"


def _get(path, **kw):
    r = _session.get(_BASE + path, timeout=30, **kw)
    r.raise_for_status()
    return r.json()


def _send(method, path, **kw):
    r = _session.request(method, _BASE + path, timeout=30, **kw)
    r.raise_for_status()
    return r.json() if r.content else None


# ── Lookups ──
def load_lists():
    try:
        return _get("/lists")
    except requests.RequestException as exc:
        log.error("load_lists failed: %s", exc)
        return {"site": [], "category": [], "maintenance": [],
                "department": [], "academic": []}


def fetch_users():
    try:
        return _get("/user-names")
    except requests.RequestException as exc:
        log.error("fetch_users failed: %s", exc)
        return []


def generate_doc_number(category):
    try:
        return _get("/doc-number", params={"category": category})["doc_number"]
    except requests.RequestException as exc:
        log.error("generate_doc_number failed: %s", exc)
        return ""


# ── Session / requisition ──
def fetch_requisition(doc):
    if not doc:
        return None
    try:
        return _get(f"/requisitions/{doc}")
    except requests.RequestException as exc:
        log.error("fetch_requisition failed: %s", exc)
        return None


def load_session():
    # Identity from the token; the document number from the LogOnUser hand-off
    # row the requisition screen wrote (keyed by OS user).
    user_id, user_name, doc = None, "", ""
    try:
        me = _get("/auth/me")
        user_id, user_name = me["user_id"], me["full_name"]
    except requests.RequestException as exc:
        log.error("load_session (whoami) failed: %s", exc)
    try:
        doc = _get("/session", params={"os_user": os.getlogin()}).get("doc_number") or ""
    except requests.RequestException as exc:
        log.error("load_session (doc) failed: %s", exc)
    req_row = fetch_requisition(doc) if doc else None
    assigned_to = (req_row or {}).get("Assign_To") or ""
    return user_id, user_name, doc, req_row, assigned_to


def fetch_items(doc):
    try:
        return _get(f"/requisitions/{doc}/items")
    except requests.RequestException as exc:
        log.error("fetch_items failed: %s", exc)
        return []


def fetch_history(doc):
    try:
        return _get(f"/requisitions/{doc}/history")
    except requests.RequestException as exc:
        log.error("fetch_history failed: %s", exc)
        return []


def fetch_attachments(doc):
    try:
        return _get(f"/requisitions/{doc}/attachments")
    except requests.RequestException as exc:
        log.error("fetch_attachments failed: %s", exc)
        return []


def fetch_approvers(doc):
    result = {"hod": None, "vp": None, "principal": None}
    if not doc:
        return result
    try:
        data = _get(f"/requisitions/{doc}/approvers")
    except requests.RequestException as exc:
        log.error("fetch_approvers failed: %s", exc)
        return result
    for key, info in data.items():
        if info and info.get("image") is not None:
            info = dict(info)
            info["image"] = base64.b64decode(info["image"])  # bytes for the PDF
        result[key] = info
    return result

def fetch_unprocessed_for_department(dept):
    try:
        return _get(f"/requisitions/by-department/{dept}")
    except requests.RequestException as exc:
        log.error("fetch_unprocessed_for_department failed: %s", exc)
        return []


def mark_requisitions_processed(department, doc_numbers):
    try:
        return _send("POST", "/requisitions/mark-processed",
                     json={"department": department, "doc_numbers": doc_numbers})
    except requests.RequestException as exc:
        log.error("mark_requisitions_processed failed: %s", exc)
        return {"updated": 0}

# ── Writes ──
def save_requisition(doc, fields, items):
    _send("PUT", f"/requisitions/{doc}", json={"fields": fields, "items": items})


def submit_requisition(doc, fields, items, assignee, completed_phase,
                       comments="", next_phase=""):
    return _send("POST", f"/requisitions/{doc}/submit",
                 json={"fields": fields, "items": items, "assignee": assignee,
                       "completed_phase": completed_phase, "comments": comments,
                       "next_phase": next_phase})

# ── Attachments ──
def upload_attachment(doc, file_path):
    with open(file_path, "rb") as fh:
        r = _session.post(f"{_BASE}/requisitions/{doc}/attachments",
                          files={"file": (os.path.basename(file_path), fh)}, timeout=120)
    r.raise_for_status()


def delete_attachment(attachment_id):
    r = _session.delete(f"{_BASE}/attachments/{attachment_id}", timeout=30)
    r.raise_for_status()


def download_attachment(attachment_id, file_name):
    r = _session.get(f"{_BASE}/attachments/{attachment_id}/download", timeout=120)
    r.raise_for_status()
    tmp = os.path.join(tempfile.gettempdir(), file_name)
    with open(tmp, "wb") as fh:
        fh.write(r.content)
    return tmp
