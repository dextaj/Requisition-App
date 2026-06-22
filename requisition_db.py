"""
requisition_db.py - client data layer for the Requisition screen (local dev).

Same function names and return shapes as the old pyodbc versions, so the
RequisitionScreen UI is unchanged. Each call now goes to the API.

Auth token: prefers CTC_AUTH_TOKEN if set; otherwise, in dev, it derives a
"dev:<id>" token from the UserID the login screen passes on the command line.
It also publishes the token into the environment so the Requisition FORM,
which this screen launches, inherits it.
"""

import os
import sys

import requests
import applog

log = applog.get_logger("requisition")

_BASE = os.environ.get("CTC_API_BASE", "http://localhost:8000").rstrip("/")
_session = requests.Session()

_token = os.environ.get("CTC_AUTH_TOKEN")
if not _token and len(sys.argv) > 1 and sys.argv[1].strip().isdigit():
    _token = f"dev:{sys.argv[1].strip()}"      # DEV fallback, from login's argv
if _token:
    _session.headers["Authorization"] = f"Bearer {_token}"
    os.environ["CTC_AUTH_TOKEN"] = _token       # so the launched form inherits it


def _get(path, **kw):
    r = _session.get(_BASE + path, timeout=30, **kw)
    r.raise_for_status()
    return r.json()


def _send(method, path, **kw):
    r = _session.request(method, _BASE + path, timeout=30, **kw)
    r.raise_for_status()
    return r.json() if r.content else None


def resolve_logged_in_user(user_id=None):
    try:
        me = _get("/auth/me")
    except requests.RequestException as exc:
        log.error("resolve_logged_in_user failed: %s", exc)
        return None, None
    try:
        _send("POST", "/session", json={"os_user": os.getlogin()})
    except requests.RequestException as exc:
        log.warning("session register failed: %s", exc)
    return me["user_id"], me["full_name"]


def user_in_any_group(user_id, group_names):
    if user_id is None or not group_names:
        return False
    try:
        r = _get("/auth/in-any-group", params=[("group", g) for g in group_names])
        return r["in_any"]
    except requests.RequestException as exc:
        log.error("user_in_any_group failed: %s", exc)
        return False


def fetch_requisitions(user_id, user_name, view_all=False):
    try:
        return _get("/requisitions", params={"scope": "all" if view_all else "mine"})
    except requests.RequestException as exc:
        log.error("fetch_requisitions failed: %s", exc)
        return []


def fetch_summary_counts(user_name):
    try:
        d = _get("/requisitions/summary")
        return d["my_open"], d["pending"], d["total_month"]
    except requests.RequestException:
        return 0, 0, 0


def log_document_open(user_id, user_name, doc_number):
    try:
        _send("PUT", "/session/document",
              json={"os_user": os.getlogin(), "doc_number": doc_number})
    except requests.RequestException as exc:
        log.error("log_document_open failed: %s", exc)
